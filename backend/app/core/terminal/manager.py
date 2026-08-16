"""
Real Linux terminal sessions powered by a PTY.

Each session spawns an interactive /bin/bash inside the level sandbox.
Input from the WebSocket is written to the PTY master; output from the shell
is read from the PTY master and streamed back. A lightweight guard intercepts
obviously dangerous commands before they reach the shell.
"""
import fcntl
import logging
import os
import pty
import re
import signal
import struct
import termios
import threading
import time
from typing import Dict, Optional, Tuple

logger = logging.getLogger("astarote.terminal")

# --- Dangerous command guard -------------------------------------------------
DANGEROUS_PATTERNS = [
    re.compile(r"^\s*rm\s+(-[a-zA-Z]*[rR]f[a-zA-Z]*\s+)?[~/]*(/|\.|\*|etc|usr|bin|boot|var|lib|root|home)\s*$"),
    re.compile(r"^\s*rm\s+(-[a-zA-Z]*[rR]f[a-zA-Z]*\s+)?/\*"),
    re.compile(r"^\s*rm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+)?/(etc|usr|bin|boot|var|lib|lib64|sbin|opt)\b"),
    re.compile(r"^\s*(shutdown|reboot|poweroff|halt|init\s+\d|telinit)"),
    re.compile(r"^\s*(dd\s+.*(of=/(dev|tmp|boot|etc|home))|dd\s+if=/dev/(zero|sda|sdb))"),
    re.compile(r"^\s*mkfs(\s|$)|^\s*mkfs\.\w+(\s|$)|^\s*mkswap(\s|$)|^\s*fsck\s+-[a-z]*\s*/"),
    re.compile(r"^\s*(fdisk|parted|gdisk)\b"),
    re.compile(r"^\s*mount\b|^\s*umount\b"),
    re.compile(r"^\s*chmod\s+(-[a-zA-Z]*[Rr][a-zA-Z]*\s+)?-?0*777\s+/(\s|$)|^\s*chmod\s+777\s+/\*"),
    re.compile(r"^\s*:\(\)\s*\{.*\};:"),
    re.compile(r"^\s*>\s*/dev/"),
    re.compile(r"^\s*sudo\s+rm\b|^\s*sudo\s+shutdown\b|^\s*sudo\s+dd\b"),
    re.compile(r"^\s*(curl|wget)\s+.*\|\s*(ba)?sh\b"),
]

GUARD_MESSAGE = (
    "\r\n\033[1;31m[GARDIEN ASTATAROTE]\033[0m "
    "Commande bloquée : cette action est interdite dans le laboratoire "
    "pour enseigner de bonnes pratiques. Réessayez une action ciblée.\r\n"
)


def is_dangerous(command_line: str) -> bool:
    stripped = command_line.strip()
    if not stripped:
        return False
    return any(pattern.search(stripped) for pattern in DANGEROUS_PATTERNS)


# --- PTY session ------------------------------------------------------------
class TerminalSession:
    def __init__(self, key: str, workdir: str):
        self.key = key
        self.workdir = workdir
        self.pid: Optional[int] = None
        self.master_fd: Optional[int] = None
        self.closed = False
        self.pending_line: str = ""
        self._spawn()

    def _spawn(self) -> None:
        os.makedirs(self.workdir, exist_ok=True)
        pid, master_fd = pty.fork()
        if pid == 0:
            # ---- child process ----
            try:
                os.chdir(self.workdir)
            except OSError:
                pass
            os.environ["TERM"] = "xterm-256color"
            os.environ["COLORTERM"] = "truecolor"
            os.environ["HOME"] = os.path.join(self.workdir, "home", "user") if os.path.isdir(os.path.join(self.workdir, "home", "user")) else self.workdir
            os.environ["PS1"] = (
                r"\[\033[01;32m\]agent@astatarote\[\033[00m\]:"
                r"\[\033[01;34m\]\w\[\033[00m\]\$ "
            )
            os.environ["LANG"] = "en_US.UTF-8"
            try:
                os.execvp("/bin/bash", ["bash", "--norc", "-i"])
            except Exception:
                os.execvp("/bin/sh", ["/bin/sh", "-i"])
        # ---- parent process ----
        self.pid = pid
        self.master_fd = master_fd
        os.set_blocking(master_fd, False)

        # Disable bash history expansion so that '!' (e.g. in HTML echoed
        # content such as "<!DOCTYPE html>") is not treated as a history
        # command, which would break echo/cat commands in the sandbox.
        self.write(b"set +o histexpand\r")
        time.sleep(0.2)
        try:
            while True:
                chunk = os.read(self.master_fd, 65536)
                if not chunk:
                    break
        except (BlockingIOError, OSError):
            pass

    def write(self, data: bytes) -> None:
        if self.closed or self.master_fd is None:
            return
        try:
            os.write(self.master_fd, data)
        except OSError:
            self.closed = True

    def read(self) -> bytes:
        if self.closed or self.master_fd is None:
            return b""
        chunks = []
        try:
            while True:
                chunk = os.read(self.master_fd, 65536)
                if not chunk:
                    break
                chunks.append(chunk)
                if len(chunks) > 32:
                    break
        except BlockingIOError:
            pass
        except OSError:
            self.closed = True
        return b"".join(chunks)

    def set_size(self, rows: int, cols: int) -> None:
        if self.master_fd is None or self.closed:
            return
        try:
            rows = max(rows or 24, 1)
            cols = max(cols or 80, 1)
            fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        except OSError:
            pass

    def close(self) -> None:
        self.closed = True
        if self.pid:
            try:
                os.kill(self.pid, signal.SIGHUP)
            except ProcessLookupError:
                pass
            try:
                os.kill(self.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                os.waitpid(self.pid, os.WNOHANG)
            except (ChildProcessError, OSError):
                pass
        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
            self.master_fd = None


# --- Session manager ---------------------------------------------------------
class TerminalManager:
    _sessions: Dict[str, TerminalSession] = {}
    _lock = threading.Lock()

    @classmethod
    def session_key(cls, game_id: int, level_id: int) -> str:
        return f"{game_id}:{level_id}"

    @classmethod
    def get_or_create(cls, game_id: int, level_id: int, workdir: str) -> TerminalSession:
        key = cls.session_key(game_id, level_id)
        with cls._lock:
            session = cls._sessions.get(key)
            if session and not session.closed and os.path.isdir(workdir):
                return session
            if session:
                session.close()
            session = TerminalSession(key, workdir)
            cls._sessions[key] = session
            return session

    @classmethod
    def close_session(cls, game_id: int, level_id: int) -> None:
        key = cls.session_key(game_id, level_id)
        with cls._lock:
            session = cls._sessions.pop(key, None)
        if session:
            session.close()

    @classmethod
    def close_all(cls) -> None:
        with cls._lock:
            sessions = list(cls._sessions.values())
            cls._sessions.clear()
        for session in sessions:
            session.close()
