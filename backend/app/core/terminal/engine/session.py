"""
Deterministic Linux engine — session management.

Sessions live in memory while a WebSocket is open and are persisted into
GameState.terminal_state after every command. The validation endpoint always
reloads the authoritative state from the database, so progress checks can
never be spoofed from the client.
"""
from __future__ import annotations

import threading
from typing import Any, Dict, Optional, Tuple

from .shell import DeterministicShell

# In-memory cache: (game_id, level_id) -> DeterministicShell
_SESSIONS: Dict[Tuple[int, int], DeterministicShell] = {}
_LOCK = threading.Lock()

STATE_VERSION = 2


def session_key(game_id: int, level_id: int) -> Tuple[int, int]:
    return (game_id, level_id)


def get_session(
    game_id: int,
    level_id: int,
    scenario: Optional[Dict[str, Any]],
    saved_state: Optional[Dict[str, Any]] = None,
) -> DeterministicShell:
    """Return the cached session, or rebuild it (from saved state if any)."""
    key = session_key(game_id, level_id)
    with _LOCK:
        if key in _SESSIONS:
            return _SESSIONS[key]
        if saved_state and saved_state.get("_engine") == STATE_VERSION and "vfs" in saved_state:
            shell = DeterministicShell.from_dict(saved_state, scenario=scenario)
        else:
            shell = DeterministicShell(scenario=scenario or {})
        _SESSIONS[key] = shell
        return shell


def drop_session(game_id: int, level_id: int) -> None:
    with _LOCK:
        _SESSIONS.pop(session_key(game_id, level_id), None)


def reset_session(
    game_id: int,
    level_id: int,
    scenario: Optional[Dict[str, Any]],
) -> DeterministicShell:
    """Recreate a session from the level's initial scenario."""
    with _LOCK:
        shell = DeterministicShell(scenario=scenario or {})
        _SESSIONS[session_key(game_id, level_id)] = shell
        return shell


def persist(shell: DeterministicShell) -> Dict[str, Any]:
    """Serialize a session for GameState.terminal_state storage."""
    data = shell.to_dict()
    data["_engine"] = STATE_VERSION
    return data


def banner(shell: DeterministicShell, level_index: int) -> str:
    return (
        f"\x1b[1;32mAstatarote Lab\x1b[0m — shell simulé (moteur déterministe)\n"
        f"Environnement du défi {level_index + 1} chargé. Tapez \x1b[1mhelp\x1b[0m pour la liste des commandes.\n"
    )
