"""
Game validation engine — deterministic edition.

Each level is validated against the persisted virtual machine state
(GameState.terminal_state) produced by the deterministic Linux engine:
file existence, permissions, contents, simulated processes and the
commands the learner actually ran. No real filesystem is touched, which
makes validation instant, hermetic and impossible to spoof from the client.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.app.models.models import Game, Level, GameState, User
from backend.app.core.terminal.engine import session as engine_sessions
from backend.app.core.terminal.engine.shell import DeterministicShell

logger = logging.getLogger("astarote.game")

RANKS = [
    (500, "Maître"),
    (350, "Expert"),
    (200, "Administrateur"),
    (100, "Apprenti"),
]

BADGES = {
    "linux": "Linux Ninja",
    "network": "Network Sentinel",
    "security": "Defender",
}


def _load_shell(game: Game, level: Level) -> Optional[DeterministicShell]:
    """Rebuild the authoritative session state from the DB (never trusted from client)."""
    state = (
        level.game_states
        and level.game_states[0]
    )
    saved = (state.terminal_state if state else None) or None
    if saved and saved.get("_engine") == engine_sessions.STATE_VERSION:
        return DeterministicShell.from_dict(saved, scenario=level.scenario)
    # No session yet: the environment is still in its initial state.
    return engine_sessions.get_session(game.id, level.id, level.scenario, saved)


class GameEngine:
    @staticmethod
    def validate_level(db: Session, game_id: int, level_index: int) -> Dict[str, Any]:
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            return {"success": False, "message": "Jeu introuvable.", "points_earned": 0}

        level = db.query(Level).filter(
            Level.game_id == game_id, Level.level_index == level_index
        ).first()
        if not level:
            return {"success": False, "message": "Niveau introuvable.", "points_earned": 0}

        shell = _load_shell(game, level)
        if shell is None:
            return {
                "success": False,
                "message": "Aucune session de terminal trouvée pour ce défi. Ouvrez le terminal puis validez à nouveau.",
                "points_earned": 0,
            }

        expected_state = (level.scenario or {}).get("expected_state", {}) or {}
        failures: List[str] = []
        all_passed = True

        # 1. File checks ---------------------------------------------------
        for check in expected_state.get("files_checks", []) or []:
            path = check.get("path")
            if not path:
                continue
            node = shell.vfs.get(path)
            if node is None:
                all_passed = False
                failures.append(f"Élément manquant : '{path}'")
                continue

            expected_type = check.get("type")
            if expected_type == "dir" and node.kind != "dir":
                all_passed = False
                failures.append(f"'{path}' devrait être un dossier.")
                continue
            if expected_type == "file" and node.kind == "dir":
                all_passed = False
                failures.append(f"'{path}' devrait être un fichier.")
                continue

            expected_perms = check.get("perms")
            if expected_perms:
                actual_perms = oct(node.perms)[2:].zfill(3)
                if actual_perms != str(expected_perms):
                    all_passed = False
                    failures.append(
                        f"Permissions incorrectes sur '{path}' : attendu '{expected_perms}', trouvé '{actual_perms}'"
                    )

            content_contains = check.get("content_contains")
            if content_contains:
                content = node.content if node.kind == "file" else ""
                if str(content_contains).lower() not in content.lower():
                    all_passed = False
                    failures.append(f"Le contenu de '{path}' ne contient pas l'élément attendu.")

            content_not_contains = check.get("content_not_contains")
            if content_not_contains:
                content = node.content if node.kind == "file" else ""
                if str(content_not_contains).lower() in content.lower():
                    all_passed = False
                    failures.append(f"Le contenu de '{path}' ne doit pas contenir : '{content_not_contains}'")

        # 2. Deleted file checks -------------------------------------------
        for check in expected_state.get("files_not_exists", []) or []:
            path = check.get("path") if isinstance(check, dict) else check
            if not path:
                continue
            if shell.vfs.exists(path):
                all_passed = False
                failures.append(f"'{path}' devrait avoir été déplacé ou supprimé.")

        # 3. Process checks --------------------------------------------------
        proc_not_running = expected_state.get("process_not_running")
        if proc_not_running:
            if shell.processes.find(name=proc_not_running) is not None:
                all_passed = False
                failures.append(f"Le processus '{proc_not_running}' est toujours actif !")

        proc_running = expected_state.get("process_running")
        if proc_running:
            if shell.processes.find(name=proc_running) is None:
                all_passed = False
                failures.append(f"Le processus '{proc_running}' devrait toujours être actif.")

        # 4. Pedagogical command usage ---------------------------------------
        for required in expected_state.get("commands_used", []) or []:
            if not any(required in entry for entry in shell.history):
                all_passed = False
                failures.append(f"Commande attendue non utilisée : '{required}'")

        if not all_passed:
            level.attempts += 1
            db.commit()
            return {
                "success": False,
                "message": "Validation échouée.\n" + "\n".join(failures),
                "points_earned": 0,
            }

        # ---- Level passed! ------------------------------------------------
        level.status = "completed"
        level.completed_at = datetime.utcnow()
        level.attempts += 1
        points_earned = level.points

        user = db.query(User).filter(User.id == game.user_id).first()
        badge_unlocked = None
        if user:
            # Copy first: re-assigning the same dict object is a no-op for
            # SQLAlchemy's change detection on JSON columns.
            stats = dict(user.stats or {})
            stats["points"] = stats.get("points", 0) + points_earned
            stats["levels_completed"] = stats.get("levels_completed", 0) + 1

            unlocked_badges = stats.get("badges", [])
            badge_name = BADGES.get(game.domain)
            if badge_name and badge_name not in unlocked_badges:
                unlocked_badges.append(badge_name)
                badge_unlocked = badge_name
            stats["badges"] = unlocked_badges

            total_points = stats.get("points", 0)
            rank = "Novice"
            for threshold, label in RANKS:
                if total_points >= threshold:
                    rank = label
                    break
            stats["rank"] = rank
            user.stats = stats
            db.add(user)

        # Update game progress + unlock next level
        levels = db.query(Level).filter(Level.game_id == game_id).all()
        completed_count = sum(1 for lv in levels if lv.status == "completed")
        game.progress = (completed_count / len(levels)) * 100.0 if levels else 0.0

        next_level_index = level_index + 1
        next_level = db.query(Level).filter(
            Level.game_id == game_id, Level.level_index == next_level_index
        ).first()
        if next_level:
            next_level.status = "available"
        else:
            game.status = "completed"
        game.current_level_index = next_level_index if next_level else level_index

        db.commit()

        success_msg = (
            f"Félicitations ! Vous avez validé le défi '{level.title}' avec succès !"
        )
        if badge_unlocked:
            success_msg += f"\nBadge débloqué : {badge_unlocked} !"

        return {
            "success": True,
            "message": success_msg,
            "points_earned": points_earned,
            "badge_unlocked": badge_unlocked,
            "next_level_index": next_level_index if next_level else None,
        }
