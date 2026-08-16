"""
Game validation engine.

Instead of inspecting a simulated in-memory state, this engine validates each
level against the REAL sandbox directory that the terminal operates on: file
existence, permissions (octal), contents, removed files and running processes.
"""
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.app.models.models import Game, Level, GameState, User
from backend.app.core.terminal.sandbox import SandboxManager

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

        scenario = level.scenario or {}
        expected_state = scenario.get("expected_state", {}) or {}

        # Materialise the sandbox on first access; NEVER recreate it here
        # (the terminal may have modified files that validation inspects).
        if not os.path.isdir(SandboxManager.sandbox_dir(game_id, level.id)):
            SandboxManager.prepare(game_id, level.id, scenario)

        failures: List[str] = []
        all_passed = True

        # 1. File checks -------------------------------------------------
        for check in expected_state.get("files_checks", []) or []:
            path = check.get("path")
            if not path:
                continue
            abs_path = SandboxManager.resolve_sandbox_path(game_id, level.id, path)
            if abs_path is None:
                failures.append(f"Chemin invalide : '{path}'")
                all_passed = False
                continue

            if not os.path.lexists(abs_path):
                all_passed = False
                failures.append(f"Fichier manquant : '{path}'")
                continue

            expected_perms = check.get("perms")
            if expected_perms:
                try:
                    actual_perms = oct(os.stat(abs_path).st_mode & 0o777)[2:]
                    if actual_perms != str(expected_perms):
                        all_passed = False
                        failures.append(
                            f"Permissions incorrectes sur '{path}' : "
                            f"attendu '{expected_perms}', trouvé '{actual_perms}'"
                        )
                except OSError:
                    all_passed = False
                    failures.append(f"Impossible de lire les permissions de '{path}'")

            content_contains = check.get("content_contains")
            if content_contains:
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as fh:
                        content = fh.read()
                    if content_contains not in content:
                        all_passed = False
                        failures.append(
                            f"Le contenu de '{path}' ne contient pas l'élément attendu."
                        )
                except OSError:
                    all_passed = False
                    failures.append(f"Impossible de lire '{path}'")

            content_not_contains = check.get("content_not_contains")
            if content_not_contains:
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as fh:
                        content = fh.read()
                    if content_not_contains in content:
                        all_passed = False
                        failures.append(
                            f"Le contenu de '{path}' ne doit pas contenir : "
                            f"'{content_not_contains}'"
                        )
                except OSError:
                    pass

        # 2. Process checks ----------------------------------------------
        proc_not_running = expected_state.get("process_not_running")
        if proc_not_running:
            if SandboxManager.is_process_running(game_id, level.id, proc_not_running):
                all_passed = False
                failures.append(f"Le processus '{proc_not_running}' est toujours actif !")

        proc_running = expected_state.get("process_running")
        if proc_running:
            if not SandboxManager.is_process_running(game_id, level.id, proc_running):
                all_passed = False
                failures.append(f"Le processus '{proc_running}' devrait être actif.")

        # 3. Deleted file checks ------------------------------------------
        file_not_exists = expected_state.get("file_not_exists")
        if file_not_exists:
            abs_path = SandboxManager.resolve_sandbox_path(game_id, level.id, file_not_exists)
            if abs_path and os.path.lexists(abs_path):
                all_passed = False
                failures.append(
                    f"Le fichier '{file_not_exists}' n'a pas été supprimé."
                )

        if not all_passed:
            level.attempts += 1
            db.commit()
            return {
                "success": False,
                "message": "Validation échouée.\n" + "\n".join(failures),
                "points_earned": 0,
            }

        # ---- Level passed! ---------------------------------------------
        level.status = "completed"
        level.completed_at = datetime.utcnow()
        level.attempts += 1
        points_earned = level.points

        user = db.query(User).filter(User.id == game.user_id).first()
        badge_unlocked = None
        if user:
            stats = user.stats or {}
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
