"""
Sandbox manager: materialises each level's scenario as a real directory tree
on the local filesystem, and can spawn/stop the background processes that the
scenario defines. The terminal connects to a real bash process running inside
this directory, and validation inspects the real filesystem state.
"""
import logging
import os
import shutil
import subprocess
import threading
from typing import Dict, Any, List, Optional, Tuple

from backend.app.core.config import settings

logger = logging.getLogger("astarote.sandbox")


class SandboxManager:
    BASE = settings.SANDBOX_BASE

    # (game_id, level_id) -> list of spawned Popen processes
    _processes: Dict[Tuple[int, int], List[subprocess.Popen]] = {}
    _lock = threading.Lock()

    # ------------------------------------------------------------------
    @classmethod
    def sandbox_dir(cls, game_id: int, level_id: int) -> str:
        return os.path.join(cls.BASE, f"game_{game_id}", f"level_{level_id}")

    # ------------------------------------------------------------------
    @classmethod
    def _normalize_fs(cls, node: Any) -> List[Tuple[str, Dict[str, Any]]]:
        """Converts both nested and flat fs dicts into a flat list of (abs_path, info)."""
        results: List[Tuple[str, Dict[str, Any]]] = []

        def walk(base_path: str, current: Any):
            if not isinstance(current, dict):
                return
            for key, value in current.items():
                if key.startswith("/"):
                    child_path = os.path.normpath(key)
                else:
                    child_path = os.path.normpath(os.path.join(base_path, key))

                # If the value looks like a nested directory dict (children have no is_dir/file marker),
                # treat it as a directory. Otherwise treat it as a file entry.
                if isinstance(value, dict) and "content" not in value and "is_dir" not in value:
                    results.append((child_path, {"is_dir": True, "perms": "755", "owner": "user"}))
                    walk(child_path, value)
                else:
                    info = dict(value) if isinstance(value, dict) else {"content": value}
                    results.append((child_path, info))

        walk("/", node)
        return results

    # ------------------------------------------------------------------
    @classmethod
    def prepare(cls, game_id: int, level_id: int, scenario: Optional[Dict[str, Any]]) -> str:
        """Creates (or recreates) the sandbox directory from a level scenario."""
        root = cls.sandbox_dir(game_id, level_id)
        cls.cleanup(game_id, level_id)

        home = os.path.join(root, "home", "user")
        os.makedirs(home, exist_ok=True)

        initial_state = (scenario or {}).get("initial_state", {}) or {}
        fs = initial_state.get("fs", {}) or {}

        entries = cls._normalize_fs(fs)
        for abs_path, info in entries:
            rel = os.path.normpath(abs_path).lstrip("/")
            target = os.path.join(root, rel) if rel else root
            # Prevent escaping the sandbox
            if os.path.commonpath([os.path.abspath(target), os.path.abspath(root)]) != os.path.abspath(root):
                logger.warning("Skipping sandbox path escaping root: %s", abs_path)
                continue

            if info.get("is_dir"):
                os.makedirs(target, exist_ok=True)
                os.chmod(target, cls._parse_perms(info.get("perms", "755")))
            else:
                parent = os.path.dirname(target)
                os.makedirs(parent, exist_ok=True)
                content = info.get("content", "")
                if isinstance(content, (dict, list)):
                    content = ""
                with open(target, "w", encoding="utf-8") as fh:
                    fh.write(str(content))
                os.chmod(target, cls._parse_perms(info.get("perms", "644")))

        # Spawn scenario background processes
        processes = initial_state.get("processes", []) or []
        cls._spawn_processes(game_id, level_id, processes, home)

        logger.info("Sandbox ready for game=%s level=%s at %s", game_id, level_id, root)
        return root

    # ------------------------------------------------------------------
    @classmethod
    def _parse_perms(cls, perms: Any) -> int:
        try:
            return int(str(perms).strip() or "644", 8)
        except ValueError:
            return 0o644

    # ------------------------------------------------------------------
    @classmethod
    def _spawn_processes(
        cls,
        game_id: int,
        level_id: int,
        processes: List[Dict[str, Any]],
        cwd: str,
    ) -> None:
        key = (game_id, level_id)
        with cls._lock:
            cls._processes.setdefault(key, [])

        for proc in processes:
            name = proc.get("name")
            pid = proc.get("pid")
            if not name:
                continue
            try:
                p = subprocess.Popen(
                    ["bash", "-c", f"exec -a {name} sleep 86400"],
                    cwd=cwd,
                    start_new_session=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                with cls._lock:
                    cls._processes.setdefault(key, []).append(p)
                logger.info(
                    "Spawned sandbox process %s (pid=%s) for game=%s level=%s",
                    name,
                    p.pid,
                    game_id,
                    level_id,
                )
            except Exception as e:
                logger.warning("Failed to spawn process %s: %s", name, e)

    # ------------------------------------------------------------------
    @classmethod
    def cleanup(cls, game_id: int, level_id: int) -> None:
        """Stops spawned processes and removes the sandbox directory."""
        key = (game_id, level_id)
        with cls._lock:
            procs = cls._processes.pop(key, [])
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
            try:
                p.kill()
            except Exception:
                pass

        root = cls.sandbox_dir(game_id, level_id)
        if os.path.isdir(root):
            try:
                shutil.rmtree(root, ignore_errors=True)
            except Exception as e:
                logger.warning("Sandbox cleanup warning: %s", e)

    # ------------------------------------------------------------------
    @classmethod
    def is_process_running(cls, game_id: int, level_id: int, name: str) -> bool:
        """True if a scenario process with the given name is still alive."""
        key = (game_id, level_id)
        with cls._lock:
            procs = list(cls._processes.get(key, []))
        for p in procs:
            if p.poll() is not None:
                continue
            # The process argv[0] was renamed via `exec -a <name>`.
            try:
                with open(f"/proc/{p.pid}/cmdline", "rb") as fh:
                    cmdline = fh.read().decode("utf-8", errors="ignore").replace("\x00", " ")
                if cmdline.split() and cmdline.split()[0] == name:
                    return True
            except OSError:
                continue
        return False

    # ------------------------------------------------------------------
    @classmethod
    def process_names(cls, game_id: int, level_id: int) -> List[str]:
        """Names of still-running scenario processes for a level."""
        key = (game_id, level_id)
        with cls._lock:
            procs = list(cls._processes.get(key, []))
        names = []
        for p in procs:
            if p.poll() is not None:
                continue
            try:
                with open(f"/proc/{p.pid}/cmdline", "rb") as fh:
                    cmdline = fh.read().decode("utf-8", errors="ignore").replace("\x00", " ")
                parts = cmdline.split()
                if parts:
                    names.append(parts[0])
            except OSError:
                continue
        return names

    # ------------------------------------------------------------------
    @classmethod
    def resolve_sandbox_path(cls, game_id: int, level_id: int, path: str) -> Optional[str]:
        """Maps a scenario path into the sandbox, guarding against escapes."""
        root = os.path.abspath(cls.sandbox_dir(game_id, level_id))
        norm_path = os.path.normpath(path)
        candidate = os.path.abspath(os.path.join(root, norm_path.lstrip("/")))
        if os.path.commonpath([candidate, root]) != root:
            return None
        return candidate


def resolve_path_in_sandbox(game_id: int, level_id: int, path: str) -> Optional[str]:
    return SandboxManager.resolve_sandbox_path(game_id, level_id, path)
