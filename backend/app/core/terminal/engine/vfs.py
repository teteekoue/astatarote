"""
Deterministic Linux engine — Virtual File System.

A lightweight in-memory POSIX-like filesystem that powers the simulated
terminal. Inspired by the architecture of browser terminal simulators
(bash-emulator, terminal4dummies, terminal_quest), ported server-side so
validation always runs against an authoritative, cheat-proof state.

Design goals:
  * Deterministic: same scenario + same commands => same output.
  * Realistic: GNU coreutils-like listings, permissions, error messages.
  * Serializable: the whole tree can be dumped to / loaded from JSON so a
    session survives server restarts and can be inspected by the validator.
"""
from __future__ import annotations

import posixpath
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Fixed reference clock: every node created through the scenario or through
# commands gets an mtime derived from the session clock, keeping outputs
# byte-for-byte reproducible (ls -l, stat, date...).
DEFAULT_EPOCH = 1767254400  # 2026-01-01 08:00:00 UTC


@dataclass
class FileNode:
    kind: str = "file"                 # "file" | "dir" | "link"
    content: str = ""                  # file payload (or link target)
    perms: int = 0o644
    owner: str = "user"
    group: str = "user"
    mtime: int = DEFAULT_EPOCH
    size: Optional[int] = None         # override reported size (None => len(content))
    extra: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    def permission_string(self) -> str:
        bits = "d" if self.kind == "dir" else ("l" if self.kind == "link" else "-")
        for shift in (6, 3, 0):
            for flag, char in ((4, "r"), (2, "w"), (1, "x")):
                bits += char if (self.perms >> shift) & flag else "-"
        return bits

    def reported_size(self) -> int:
        if self.size is not None:
            return self.size
        if self.kind == "dir":
            return 4096
        return len(self.content.encode("utf-8"))


class VirtualFileSystem:
    """POSIX-ish filesystem tree backed by a flat {abs_path: FileNode} dict."""

    def __init__(self, epoch: int = DEFAULT_EPOCH) -> None:
        self.epoch = epoch
        self.nodes: Dict[str, FileNode] = {}
        self._ensure_root()

    # ------------------------------------------------------------------
    # Basic tree construction
    # ------------------------------------------------------------------
    def _ensure_root(self) -> None:
        if "/" not in self.nodes:
            self.nodes["/"] = FileNode(kind="dir", perms=0o755, owner="root", group="root", mtime=self.epoch)

    def ensure_dir(self, path: str, perms: int = 0o755, owner: str = "user", group: Optional[str] = None) -> None:
        path = self.normalize("/", path)
        parts = [p for p in path.split("/") if p]
        current = ""
        for part in parts:
            current = f"{current}/{part}"
            if current not in self.nodes:
                self.nodes[current] = FileNode(
                    kind="dir", perms=perms, owner=owner,
                    group=group or owner, mtime=self.epoch,
                )

    def write_file(self, path: str, content: str, perms: int = 0o644,
                   owner: str = "user", group: Optional[str] = None, size: Optional[int] = None) -> None:
        path = self.normalize("/", path)
        parent = posixpath.dirname(path)
        if parent and parent not in self.nodes:
            self.ensure_dir(parent)
        self.nodes[path] = FileNode(
            kind="file", content=content, perms=perms, owner=owner,
            group=group or owner, mtime=self.epoch, size=size,
        )

    def write_link(self, path: str, target: str, owner: str = "user") -> None:
        path = self.normalize("/", path)
        parent = posixpath.dirname(path)
        if parent and parent not in self.nodes:
            self.ensure_dir(parent)
        self.nodes[path] = FileNode(kind="link", content=target, perms=0o777, owner=owner, mtime=self.epoch)

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------
    @staticmethod
    def normalize(cwd: str, path: str, home: str = "/home/user") -> str:
        """Resolve a user-supplied path against cwd (like a shell would)."""
        if not path or path == "~" or path.startswith("~/"):
            path = home + path[1:]
        if not path.startswith("/"):
            path = posixpath.join(cwd, path)
        parts: List[str] = []
        for part in path.split("/"):
            if part in ("", "."):
                continue
            if part == "..":
                if parts:
                    parts.pop()
                continue
            parts.append(part)
        return "/" + "/".join(parts) if parts else "/"

    def exists(self, path: str) -> bool:
        return self.normalize("/", path) in self.nodes

    def get(self, path: str) -> Optional[FileNode]:
        return self.nodes.get(self.normalize("/", path))

    def parent_of(self, path: str) -> str:
        return posixpath.dirname(self.normalize("/", path)) or "/"

    def list_dir(self, path: str) -> List[str]:
        """Immediate children names of a directory, sorted."""
        path = self.normalize("/", path)
        if path != "/" :
            path = path.rstrip("/") or "/"
        prefix = "" if path == "/" else path
        names = set()
        for node_path in self.nodes:
            if node_path == "/" or not node_path.startswith(prefix + "/"):
                continue
            rest = node_path[len(prefix) + 1:]
            if not rest:
                continue
            names.add(rest.split("/")[0])
        return sorted(names)

    # ------------------------------------------------------------------
    # Permission model (simplified but pedagogically faithful)
    # ------------------------------------------------------------------
    def can(self, action: str, path: str, user: str, is_root: bool = False) -> bool:
        """action in {'read','write','execute'}."""
        node = self.get(path)
        if node is None:
            return False
        if is_root or user == "root":
            return True
        shift = {"read": 4, "write": 2, "execute": 1}[action]
        if user == node.owner:
            perm = (node.perms >> 6) & shift
        elif user in (node.group,):
            perm = (node.perms >> 3) & shift
        else:
            perm = node.perms & shift
        return bool(perm)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "epoch": self.epoch,
            "nodes": {
                path: {
                    "kind": node.kind,
                    "content": node.content,
                    "perms": oct(node.perms),
                    "owner": node.owner,
                    "group": node.group,
                    "mtime": node.mtime,
                    **({"size": node.size} if node.size is not None else {}),
                }
                for path, node in self.nodes.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VirtualFileSystem":
        vfs = cls(epoch=int(data.get("epoch", DEFAULT_EPOCH)))
        vfs.nodes = {}
        for path, raw in (data.get("nodes") or {}).items():
            perms = raw.get("perms", "0o644")
            try:
                perms_int = int(str(perms), 8) if isinstance(perms, str) else int(perms)
            except ValueError:
                perms_int = 0o644
            vfs.nodes[path] = FileNode(
                kind=raw.get("kind", "file"),
                content=raw.get("content", ""),
                perms=perms_int,
                owner=raw.get("owner", "user"),
                group=raw.get("group", "user"),
                mtime=int(raw.get("mtime", DEFAULT_EPOCH)),
                size=raw.get("size"),
            )
        vfs._ensure_root()
        return vfs


def parse_perms(spec: Any, default: int = 0o644) -> int:
    """Parse '644' / 0o644 / 420 into an int mode."""
    try:
        if isinstance(spec, int):
            # Ambiguity: 644 means octal in our scenarios.
            return spec if spec < 0o10000 else int(str(spec), 8)
        text = str(spec).strip()
        if text.startswith("0o"):
            return int(text, 8)
        return int(text, 8)
    except (ValueError, TypeError):
        return default


def perms_to_str(perms: int) -> str:
    node = FileNode(perms=perms)
    return node.permission_string()[1:]
