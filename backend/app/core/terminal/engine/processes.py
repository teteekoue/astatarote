"""
Deterministic Linux engine — simulated process table.

Provides a realistic `ps aux` / `top` view seeded from the level scenario.
Processes can be started and killed by commands (kill, systemctl scripts),
and the validation engine can assert whether a process is still running.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Deterministic pseudo-uptime baseline (seconds). Real elapsed time is not
# used so that outputs stay reproducible.
BASE_BOOT_OFFSET = 7380  # ~2h03m after boot


def _command_matches(command: str, name: str) -> bool:
    """Match a process by name: full command, first token, or basename."""
    if command == name:
        return True
    for token in command.split():
        if token == name or token.rsplit("/", 1)[-1] == name:
            return True
    return False


@dataclass
class SimProcess:
    pid: int
    user: str
    command: str
    cpu: float = 0.0
    mem: float = 0.4
    vsz: int = 2048
    rss: int = 980
    tty: str = "?"
    stat: str = "Ss"
    start: str = "08:00"
    time: str = "0:00"
    alive: bool = True
    system: bool = False   # system daemons cannot be killed by non-root
    exit_code: Optional[int] = None

    # ------------------------------------------------------------------
    def ps_aux_row(self) -> str:
        return (
            f"{self.user:<8} {self.pid:>5} {self.cpu:>4.1f} {self.mem:>4.1f} "
            f"{self.vsz:>7} {self.rss:>6} {self.tty:>3} {self.stat:<4} "
            f"{self.start:>5} {self.time:>4} {self.command}"
        )


# A small set of standard daemons every scenario starts from.
SYSTEM_PROCESSES: List[Dict[str, Any]] = [
    {"pid": 1, "user": "root", "command": "/sbin/init splash", "stat": "Ss", "cpu": 0.0, "mem": 0.3},
    {"pid": 2, "user": "root", "command": "[kthreadd]", "stat": "S", "cpu": 0.0, "mem": 0.0, "tty": "?"},
    {"pid": 288, "user": "root", "command": "/lib/systemd/systemd-journald", "stat": "Ssl", "cpu": 0.1, "mem": 0.8},
    {"pid": 342, "user": "root", "command": "/sbin/multipathd --daemon", "stat": "Ss", "cpu": 0.0, "mem": 0.2},
    {"pid": 411, "user": "root", "command": "/usr/sbin/sshd -D", "stat": "Ss", "cpu": 0.0, "mem": 0.3},
    {"pid": 445, "user": "root", "command": "/usr/sbin/cron -f", "stat": "Ss", "cpu": 0.0, "mem": 0.2},
    {"pid": 512, "user": "root", "command": "/lib/systemd/systemd --user", "stat": "Ss", "cpu": 0.0, "mem": 0.5},
    {"pid": 613, "user": "user", "command": "-bash", "stat": "Ss", "cpu": 0.0, "mem": 0.3, "tty": "pts/0", "system": False},
]


class ProcessTable:
    def __init__(self) -> None:
        self.processes: List[SimProcess] = []
        self._next_pid = 1000

    # ------------------------------------------------------------------
    @classmethod
    def create(cls, scenario_processes: Optional[List[Dict[str, Any]]] = None) -> "ProcessTable":
        table = cls()
        for spec in SYSTEM_PROCESSES:
            clean = {k: v for k, v in spec.items() if k != "system"}
            table.add(system=True, **clean)
        for spec in scenario_processes or []:
            table.add(
                pid=spec.get("pid"),
                system=bool(spec.get("system", False)),
                **{
                    "name": spec.get("name") or spec.get("command") or "process",
                    "user": spec.get("user", "user"),
                    "cpu": spec.get("cpu", 0.2),
                    "mem": spec.get("mem", 0.5),
                    "command": spec.get("command"),
                },
            )
        return table

    # ------------------------------------------------------------------
    def add(self, system: bool = False, name: Optional[str] = None, **kwargs: Any) -> SimProcess:
        command = kwargs.pop("command", None) or name or "process"
        proc = SimProcess(
            pid=kwargs.pop("pid", None) or self._next_pid,  # type: ignore[arg-type]
            user=kwargs.pop("user", "user"),
            command=command,
            cpu=kwargs.pop("cpu", 0.2),
            mem=kwargs.pop("mem", 0.5),
            vsz=kwargs.pop("vsz", 2048),
            rss=kwargs.pop("rss", 980),
            tty=kwargs.pop("tty", "?"),
            stat=kwargs.pop("stat", "Ss" if system else "S"),
            start=kwargs.pop("start", "08:00"),
            time=kwargs.pop("time", "0:00"),
            system=system,
        )
        self.processes.append(proc)
        self._next_pid = max(self._next_pid, proc.pid + 1, 1000)
        return proc

    # ------------------------------------------------------------------
    def alive(self) -> List[SimProcess]:
        return [p for p in self.processes if p.alive]

    def find(self, pid: Optional[int] = None, name: Optional[str] = None) -> Optional[SimProcess]:
        for proc in self.alive():
            if pid is not None and proc.pid == pid:
                return proc
            if name is not None and _command_matches(proc.command, name):
                return proc
        return None

    def find_all(self, name: str) -> List[SimProcess]:
        return [p for p in self.alive() if _command_matches(p.command, name)]

    def kill(self, proc: SimProcess) -> None:
        proc.alive = False

    # ------------------------------------------------------------------
    def ps_aux(self) -> str:
        lines = ["USER      PID  %CPU %MEM    VSZ   RSS TTY  STAT START  TIME COMMAND"]
        for proc in sorted(self.alive(), key=lambda p: p.pid):
            lines.append(proc.ps_aux_row())
        return "\n".join(lines)

    def top_snapshot(self, total_mem_mb: int = 3861) -> str:
        alive = sorted(self.alive(), key=lambda p: -p.cpu)
        used = sum(p.rss for p in alive) // 1024
        lines = [
            "top - 10:13:42 up 2:03,  1 user,  load average: 0.42, 0.35, 0.29",
            f"Tasks: {len(alive)} total,   1 running, {len(alive) - 1} sleeping,   0 stopped,   0 zombie",
            f"%Cpu(s):  {sum(p.cpu for p in alive):>4.1f} us,  1.2 sy,  0.0 ni, {max(0.0, 98.8 - sum(p.cpu for p in alive)):>4.1f} id",
            f"MiB Mem :   {total_mem_mb} total,   {max(0, total_mem_mb - used - 900)} free,    900 buff,   {used} MiB used",
            "",
            "  PID USER      PR  NI    VIRT    RES  %CPU  %MEM     TIME+ COMMAND",
        ]
        for proc in alive[:14]:
            lines.append(
                f"{proc.pid:>5} {proc.user:<9} 20   0  {proc.vsz * 1024:>6}  {proc.rss * 1024:>6}  {proc.cpu:>4.1f}  {proc.mem:>4.1f}   {proc.time:>6} {proc.command.split(' ')[0][:12]}"
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "next_pid": self._next_pid,
            "processes": [
                {
                    "pid": p.pid, "user": p.user, "command": p.command,
                    "cpu": p.cpu, "mem": p.mem, "vsz": p.vsz, "rss": p.rss,
                    "tty": p.tty, "stat": p.stat, "start": p.start,
                    "time": p.time, "alive": p.alive, "system": p.system,
                }
                for p in self.processes
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessTable":
        table = cls()
        table._next_pid = int(data.get("next_pid", 1000))
        for raw in data.get("processes", []):
            table.processes.append(SimProcess(
                pid=raw["pid"], user=raw.get("user", "user"), command=raw.get("command", "?"),
                cpu=raw.get("cpu", 0.0), mem=raw.get("mem", 0.5), vsz=raw.get("vsz", 2048),
                rss=raw.get("rss", 980), tty=raw.get("tty", "?"), stat=raw.get("stat", "S"),
                start=raw.get("start", "08:00"), time=raw.get("time", "0:00"),
                alive=raw.get("alive", True), system=raw.get("system", False),
            ))
        return table
