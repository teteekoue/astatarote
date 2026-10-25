"""
Deterministic Linux engine — the shell.

Parses command lines the way bash does (quotes, variables, ~, pipes,
redirections, `;` / `&&` / `||` sequencing, globs) and dispatches to the
simulated coreutils in commands.py.

Per-exercise scripted responses ("response hooks") are checked FIRST for
every command line: each level can register deterministic outputs for
specific prompts (e.g. `systemctl status backup`) so a scenario feels real
without any real execution.
"""
from __future__ import annotations

import posixpath
import re
import shlex
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .commands import COMMANDS
from .processes import ProcessTable
from .vfs import VirtualFileSystem, parse_perms

MAX_HISTORY = 500


@dataclass
class ResponseHook:
    pattern: str          # exact command string, or regex if is_regex
    output: str
    is_regex: bool = False
    status: int = 0


@dataclass
class ExecResult:
    output: str = ""
    action: Optional[str] = None   # "clear" handled by the client
    status: int = 0


class DeterministicShell:
    """One simulated shell session bound to a level scenario."""

    def __init__(
        self,
        scenario: Optional[Dict[str, Any]] = None,
        user: str = "user",
        host: str = "meridian",
    ) -> None:
        scenario = scenario or {}
        initial = scenario.get("initial_state", {}) or {}

        self.user = user
        self.host = initial.get("host", host)
        self.vfs = self._build_vfs(initial)
        self.processes = self._build_processes(initial)

        self.cwd = initial.get("cwd", "/home/" + user)
        if not self.vfs.exists(self.cwd):
            self.cwd = "/home/" + user
            self.vfs.ensure_dir(self.cwd, owner=user)

        self.env: Dict[str, str] = {
            "HOME": "/home/" + user,
            "USER": user,
            "SHELL": "/bin/bash",
            "PWD": self.cwd,
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "TERM": "xterm-256color",
            "LANG": "C.UTF-8",
            **(initial.get("env", {}) or {}),
        }
        self.aliases: Dict[str, str] = dict(initial.get("aliases", {}) or {})
        self.history: List[str] = []
        self.last_status = 0
        self.sudo_depth = 0
        self.pending_action: Optional[str] = None

        # Scenario scripted responses — checked before anything else.
        self.hooks: List[ResponseHook] = []
        for hook in scenario.get("responses", []) or []:
            self.hooks.append(ResponseHook(
                pattern=hook.get("match", ""),
                output=hook.get("output", ""),
                is_regex=bool(hook.get("regex", False)),
                status=int(hook.get("status", 0)),
            ))

        # Commands the scenario explicitly forbids/allows (kept for the API).
        self.forbidden_commands: List[str] = scenario.get("forbidden_commands", []) or []

        self.available_commands = set(COMMANDS.keys())

    # ------------------------------------------------------------------
    # Scenario construction
    # ------------------------------------------------------------------
    def _build_vfs(self, initial: Dict[str, Any]) -> VirtualFileSystem:
        vfs = VirtualFileSystem()
        # Standard system skeleton — every level starts from this.
        skeleton = {
            "/bin": ("dir", 0o755, "root"),
            "/etc": ("dir", 0o755, "root"),
            "/var": ("dir", 0o755, "root"),
            "/var/log": ("dir", 0o755, "root"),
            "/home": ("dir", 0o755, "root"),
            "/home/user": ("dir", 0o755, "user"),
            "/root": ("dir", 0o700, "root"),
            "/tmp": ("dir", 0o777, "root"),
            "/usr": ("dir", 0o755, "root"),
            "/usr/bin": ("dir", 0o755, "root"),
        }
        for path, (kind, perms, owner) in skeleton.items():
            vfs.ensure_dir(path, perms=perms, owner=owner)
        vfs.write_file(
            "/etc/passwd",
            "root:x:0:0:root:/root:/bin/bash\n"
            "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n"
            "www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin\n"
            "user:x:1000:1000:Astatarote Learner:/home/user:/bin/bash\n",
            perms=0o644, owner="root", group="root",
        )
        vfs.write_file(
            "/etc/group",
            "root:x:0:\nsudo:x:27:user\n"
            "user:x:1000:\n",
            perms=0o644, owner="root", group="root",
        )
        vfs.write_file(
            "/etc/hostname",
            self.host + "\n",
            perms=0o644, owner="root", group="root",
        )

        # Scenario filesystem (supports nested dicts and flat entries).
        fs = initial.get("fs", {}) or {}
        for path, spec in self._flatten_fs(fs).items():
            if spec.get("is_dir"):
                vfs.ensure_dir(path, perms=parse_perms(spec.get("perms", "755")),
                               owner=spec.get("owner", "user"), group=spec.get("group"))
                continue
            vfs.write_file(
                path,
                spec.get("content", ""),
                perms=parse_perms(spec.get("perms", "644")),
                owner=spec.get("owner", "user"),
                group=spec.get("group"),
                size=spec.get("size"),
            )
        return vfs

    @staticmethod
    def _flatten_fs(fs: Dict[str, Any], prefix: str = "") -> Dict[str, Dict[str, Any]]:
        flat: Dict[str, Dict[str, Any]] = {}
        for key, value in fs.items():
            path = key if key.startswith("/") or not prefix else posixpath.join(prefix, key)
            if not path.startswith("/"):
                path = "/" + path
            if isinstance(value, dict) and "content" not in value and "is_dir" not in value and "link_to" not in value:
                flat[path] = {"is_dir": True, "perms": value.get("perms", "755"), "owner": value.get("owner", "user")}
                flat.update(DeterministicShell._flatten_fs(value, prefix=path))
            elif isinstance(value, str):
                flat[path] = {"content": value}
            elif isinstance(value, dict):
                if "link_to" in value:
                    flat[path] = {"content": value["link_to"], "perms": "777", "owner": value.get("owner", "user")}
                    # mark as link via direct node creation after
                    flat[path]["_link"] = True
                else:
                    flat[path] = value
        return flat

    def _build_processes(self, initial: Dict[str, Any]) -> ProcessTable:
        return ProcessTable.create(initial.get("processes", []) or [])

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    @property
    def is_root(self) -> bool:
        return self.sudo_depth > 0 or self.user == "root"

    @property
    def prompt(self) -> str:
        path = self.cwd
        home = self.env.get("HOME", "/home/user")
        if path == home:
            path = "~"
        elif path.startswith(home + "/"):
            path = "~" + path[len(home):]
        if self.is_root:
            return f"root@{self.host}:{path}# "
        return f"{self.user}@{self.host}:{path}$ "

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------
    def resolve(self, path: str) -> str:
        home = self.env.get("HOME", "/home/user")
        if path == "~" or path.startswith("~/"):
            path = home + path[1:]
        return VirtualFileSystem.normalize(self.cwd, path, home)

    def follow_link(self, path: str) -> Optional[str]:
        node = self.vfs.get(path)
        if node is not None and node.kind == "link":
            return self.resolve(node.content)
        return path

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    def execute(self, line: str) -> ExecResult:
        self.pending_action = None
        line = line.strip()
        if not line:
            return ExecResult(status=self.last_status)

        if len(self.history) >= MAX_HISTORY:
            self.history = self.history[-MAX_HISTORY + 1:]
        self.history.append(line)

        # 1) Scenario response hooks (exact match, then regex) on raw line.
        for hook in self.hooks:
            if not hook.is_regex and line == hook.pattern:
                self.last_status = hook.status
                return ExecResult(output=hook.output, status=hook.status)
        for hook in self.hooks:
            if hook.is_regex:
                try:
                    if re.search(hook.pattern, line):
                        self.last_status = hook.status
                        return ExecResult(output=hook.output, status=hook.status)
                except re.error:
                    continue

        # 2) Forbidden commands guard.
        head = line.split()[0]
        for pattern in self.forbidden_commands:
            if fnmatch_like(head, pattern):
                self.last_status = 126
                return ExecResult(
                    output=f"bash: {head}: commande désactivée dans cet exercice\n",
                    status=126,
                )

        # 3) Alias expansion.
        if head in self.aliases:
            line = self.aliases[head] + line[len(head):]

        # 4) Sequence execution: `;`, `&&`, `||`.
        outputs: List[str] = []
        for raw_segment, separator in split_sequence(line):
            result = self._execute_pipeline(raw_segment)
            outputs.append(result.output)
            self.last_status = result.status
            if separator == "&&" and result.status != 0:
                break
            if separator == "||" and result.status == 0:
                break
            if self.pending_action == "clear":
                return ExecResult(output="".join(o for o in outputs if o), action="clear", status=self.last_status)

        return ExecResult(
            output="".join(o for o in outputs if o),
            action=self.pending_action,
            status=self.last_status,
        )

    # ------------------------------------------------------------------
    def _tokenize_with_env(self, stage: str) -> Tuple[List[str], List[Tuple[str, bool]]]:
        with _VarExpander(self.env, self.last_status):
            return tokenize(stage)

    def _execute_pipeline(self, segment: str) -> ExecResult:
        # Split on top-level pipes (respect quotes).
        stages = split_top_level(segment, "|")
        stdin: Optional[str] = None
        last_output = ""
        status = 0

        for stage in stages:
            stage = stage.strip()
            if not stage:
                return ExecResult(output="bash: syntax error near unexpected token `|'\n", status=2)
            tokens, redirects = self._tokenize_with_env(stage)
            if not tokens:
                continue

            cmd = tokens[0]
            args = tokens[1:]

            # Glob expansion for path-like arguments.
            expanded: List[str] = []
            for arg in args:
                if should_glob(arg):
                    matches = self._glob(arg)
                    expanded.extend(matches if matches else [arg])
                else:
                    expanded.append(arg)
            args = expanded

            if cmd not in self.available_commands:
                last_output = f"bash: {cmd}: command not found\n"
                status = 127
                stdin = None
                continue

            output, status = self.run_command(cmd, args, stdin)
            last_output = output
            stdin = output if output else None

            # Output redirection (>, >>) applies to the last stage.
            for target, append in redirects:
                self._write_redirect(target, output, append)

        return ExecResult(output=last_output, status=status)

    # ------------------------------------------------------------------
    def run_command(self, cmd: str, args: List[str], stdin: Optional[str],
                    as_root: bool = False) -> Tuple[str, int]:
        handler = COMMANDS[cmd]
        prev_sudo = self.sudo_depth
        if as_root:
            self.sudo_depth = max(self.sudo_depth, 1)
        try:
            return handler(self, args, stdin)
        finally:
            self.sudo_depth = prev_sudo

    # ------------------------------------------------------------------
    def _write_redirect(self, target: str, content: str, append: bool) -> None:
        path = self.resolve(target)
        if not self.vfs.can("write", self.vfs.parent_of(path), self.user, self.is_root):
            # bash reports the error on stderr — surfaced after the command.
            return
        existing = self.vfs.get(path)
        if append and existing is not None and existing.kind == "file":
            self.vfs.write_file(path, existing.content.rstrip("\n") + "\n" + content.rstrip("\n") + "\n",
                                perms=existing.perms, owner=existing.owner)
        else:
            self.vfs.write_file(path, content, owner=self.user)

    # ------------------------------------------------------------------
    def _glob(self, pattern: str) -> List[str]:
        import fnmatch as _fn
        path = self.resolve(pattern)
        directory = posixpath.dirname(path)
        base = posixpath.basename(path)
        if not self.vfs.exists(directory):
            return []
        matches = []
        for name in self.vfs.list_dir(directory):
            if _fn.fnmatch(name, base):
                # Rebuild the display form relative to cwd.
                full = posixpath.join(directory, name)
                rel = relative_display(self.cwd, full)
                matches.append(rel)
        return sorted(matches)

    # ------------------------------------------------------------------
    # Tab completion
    # ------------------------------------------------------------------
    def complete(self, line: str) -> Dict[str, Any]:
        """Return completion candidates for the current input line."""
        parts = line.split()
        completing_command = len(parts) <= 1 and not line.endswith(" ")
        candidates: List[str] = []

        if completing_command:
            prefix = parts[0] if parts else ""
            candidates = sorted(c for c in self.available_commands if c.startswith(prefix))
            return {"candidates": candidates, "type": "commands"}

        prefix = parts[-1] if not line.endswith(" ") else ""
        if prefix.startswith("-"):
            return {"candidates": [], "type": "flags"}

        directory = self.resolve(prefix if prefix else ".")
        if prefix and not prefix.endswith("/"):
            directory = posixpath.dirname(self.resolve(prefix))
        names = []
        if self.vfs.exists(directory):
            for name in self.vfs.list_dir(directory):
                full = posixpath.join(directory, name)
                node = self.vfs.get(full)
                shown = name + ("/" if node and node.kind == "dir" else "")
                if not prefix or shown.startswith(posixpath.basename(prefix) if not prefix.endswith("/") else ""):
                    base = posixpath.basename(prefix)
                    if not prefix.endswith("/") and base and not shown.startswith(base):
                        continue
                    names.append(shown)
        return {"candidates": sorted(names), "type": "paths"}

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user": self.user,
            "host": self.host,
            "cwd": self.cwd,
            "env": self.env,
            "aliases": self.aliases,
            "history": self.history,
            "vfs": self.vfs.to_dict(),
            "processes": self.processes.to_dict(),
            "last_status": self.last_status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], scenario: Optional[Dict[str, Any]] = None) -> "DeterministicShell":
        shell = cls(scenario=scenario, user=data.get("user", "user"), host=data.get("host", "meridian"))
        shell.cwd = data.get("cwd", shell.cwd)
        shell.env = {**shell.env, **(data.get("env", {}) or {})}
        shell.aliases = data.get("aliases", {}) or {}
        shell.history = list(data.get("history", []) or [])
        shell.last_status = int(data.get("last_status", 0))
        if "vfs" in data:
            shell.vfs = VirtualFileSystem.from_dict(data["vfs"])
        if "processes" in data:
            shell.processes = ProcessTable.from_dict(data["processes"])
        return shell


# ---------------------------------------------------------------------------
# Parsing utilities
# ---------------------------------------------------------------------------

def fnmatch_like(value: str, pattern: str) -> bool:
    import fnmatch as _fn
    return _fn.fnmatch(value, pattern)


def should_glob(arg: str) -> bool:
    """Expand only bare (unquoted by the time we see them) wildcard args."""
    return any(c in arg for c in "*?[") and not arg.startswith("-")


def split_top_level(text: str, sep: str) -> List[str]:
    """Split text on `sep` occurring outside quotes."""
    parts: List[str] = []
    current = []
    quote: Optional[str] = None
    for ch in text:
        if quote:
            current.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            current.append(ch)
            continue
        if ch == sep and sep != "|":
            parts.append("".join(current))
            current = []
            continue
        if sep == "|":
            if ch == "|" and current and current[-1] != "|":
                parts.append("".join(current))
                current = []
                continue
            if ch == "|":
                continue
        current.append(ch)
    parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


def split_sequence(line: str) -> List[Tuple[str, Optional[str]]]:
    """Split a line on `;`, `&&`, `||` respecting quotes. Returns (segment, separator)."""
    segments: List[Tuple[str, Optional[str]]] = []
    current: List[str] = []
    quote: Optional[str] = None
    i = 0
    while i < len(line):
        ch = line[i]
        if quote:
            current.append(ch)
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in ("'", '"'):
            quote = ch
            current.append(ch)
            i += 1
            continue
        if ch == ";":
            segments.append(("".join(current), ";"))
            current = []
            i += 1
            continue
        if ch == "&" and i + 1 < len(line) and line[i + 1] == "&":
            segments.append(("".join(current), "&&"))
            current = []
            i += 2
            continue
        if ch == "|" and i + 1 < len(line) and line[i + 1] == "|":
            segments.append(("".join(current), "||"))
            current = []
            i += 2
            continue
        current.append(ch)
        i += 1
    segments.append(("".join(current), None))
    return [(seg.strip(), sep) for seg, sep in segments if seg.strip()]


def tokenize(stage: str) -> Tuple[List[str], List[Tuple[str, bool]]]:
    """Tokenize a command stage, expanding variables and ~.

    Returns (tokens, redirects) where redirects = [(target, append)].
    """
    # Extract redirections first (>, >>).
    redirects: List[Tuple[str, bool]] = []
    redirect_re = re.compile(r"(>>|>)\s*([^\s>]+)")

    def _grab_redirect(match: re.Match) -> str:
        redirects.append((match.group(2), match.group(1) == ">>"))
        return " "

    stage = redirect_re.sub(_grab_redirect, stage)

    lexer = shlex.shlex(stage, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        raw_tokens = list(lexer)
    except ValueError:
        raw_tokens = stage.split()

    tokens: List[str] = []
    for token in raw_tokens:
        # Variable expansion for $VAR and ${VAR}
        token = re.sub(
            r"\$\{(\w+)\}|\$(\w+)",
            lambda m: _lookup_var(m.group(1) or m.group(2)),
            token,
        )
        tokens.append(token)
    return tokens, redirects


_VAR_STATE: Dict[str, str] = {}


def _lookup_var(name: str) -> str:
    # Resolved by the shell instance via a thread-local-ish trick: tokenize is
    # called with state available through the caller; simplest approach is a
    # module-level scratchpad set right before tokenization.
    return _VAR_STATE.get(name, "")


class _VarExpander:
    """Context that routes variable expansion to a shell's env."""

    def __init__(self, env: Dict[str, str], last_status: int) -> None:
        self.env = env
        self.last_status = last_status

    def __enter__(self):
        _VAR_STATE.clear()
        _VAR_STATE.update(self.env)
        _VAR_STATE["?"] = str(self.last_status)
        return self

    def __exit__(self, *args):
        _VAR_STATE.clear()


def relative_display(cwd: str, path: str) -> str:
    """Render an absolute path relative to cwd when possible (like bash)."""
    if path == cwd:
        return "."
    if path.startswith(cwd + "/"):
        return path[len(cwd) + 1:]
    return path
