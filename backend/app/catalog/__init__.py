"""
Static game catalog.

Games are authored by hand, reviewed and frozen: nothing is generated at
runtime. Each module in this package exposes a `GAME` dict following the
catalog schema below. The registry loads them all and exposes simple lookup
helpers used by the API routes.

Catalog schema
-------------
GAME = {
    "slug": str,                    # unique identifier
    "name": str,
    "tagline": str,
    "description": str,
    "domain": "linux" | "network" | "security",
    "level": "beginner" | "intermediate" | "advanced",
    "difficulty": int,              # 1-5 (display)
    "duration_minutes": int,
    "skills": [str, ...],
    "version": str,                 # frozen content version
    "levels": [LEVEL, ...],
}

LEVEL = {
    "title": str,
    "situation_probleme": str,      # narrative context (why this matters)
    "consigne": [str, ...],         # ordered list of instructions
    "support_technique": str,       # markdown cheat-sheet
    "objective": str,               # one-line goal
    "scenario": {
        "initial_state": {
            "cwd": str,
            "host": str,
            "fs": {path: {"content": str} | {"is_dir": True, "perms": "755", "owner": "user"}},
            "processes": [{"name": str, "user": str, "cpu": float, "command": str}],
            "env": {str: str},
        },
        "responses": [{"match": str, "output": str, "regex": False, "status": 0}],
        "forbidden_commands": [str],
    },
    "expected_state": {
        "files_checks": [{"path": str, "perms": str, "content_contains": str}],
        "files_not_exists": [{"path": str}],
        "process_not_running": str,
        "process_running": str,
        "commands_used": [str],
    },
    "hints": [str, ...],
    "difficulty": int,              # 1-10
    "points": int,
    "time_limit": int,              # seconds
}
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("astarote.catalog")

from backend.app.catalog.linux_essentials import GAME as LINUX_ESSENTIALS

_GAMES: List[Dict[str, Any]] = [
    LINUX_ESSENTIALS,
]

_BY_SLUG: Dict[str, Dict[str, Any]] = {game["slug"]: game for game in _GAMES}


def list_games() -> List[Dict[str, Any]]:
    """Catalog metadata (without level content) for public listing."""
    return [
        {
            "slug": g["slug"],
            "name": g["name"],
            "tagline": g["tagline"],
            "description": g["description"],
            "domain": g["domain"],
            "level": g["level"],
            "difficulty": g["difficulty"],
            "duration_minutes": g["duration_minutes"],
            "skills": g["skills"],
            "version": g["version"],
            "total_levels": len(g["levels"]),
            "total_points": sum(lv["points"] for lv in g["levels"]),
        }
        for g in _GAMES
    ]


def get_game(slug: str) -> Optional[Dict[str, Any]]:
    return _BY_SLUG.get(slug)


def get_level(slug: str, level_index: int) -> Optional[Dict[str, Any]]:
    game = get_game(slug)
    if not game:
        return None
    levels = game["levels"]
    if 0 <= level_index < len(levels):
        return levels[level_index]
    return None
