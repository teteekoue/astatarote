import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.models.models import Game, Level, GameState, User

logger = logging.getLogger("astarote.game")

class GameEngine:
    @staticmethod
    def validate_level(db: Session, game_id: int, level_index: int) -> Dict[str, Any]:
        """
        Validates whether the objectives of a level are achieved by examining the virtual terminal state.
        Marks level as completed, increments game progress, assigns points, and awards badges.
        """
        # Find Game
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            return {"success": False, "message": "Jeu introuvable.", "points_earned": 0}

        # Find Level
        level = db.query(Level).filter(Level.game_id == game_id, Level.level_index == level_index).first()
        if not level:
            return {"success": False, "message": "Niveau introuvable.", "points_earned": 0}

        # Find GameState
        state = db.query(GameState).filter(GameState.game_id == game_id, GameState.level_id == level.id).first()
        if not state:
            return {"success": False, "message": "Aucun état de jeu enregistré pour ce niveau.", "points_earned": 0}

        terminal_state = state.terminal_state or {}
        fs = terminal_state.get("fs", {})
        processes = terminal_state.get("processes", [])

        # Retrieve validation checks from the level scenario config
        scenario = level.scenario or {}
        expected_state = scenario.get("expected_state", {})
        
        # Validation checks
        all_passed = True
        failed_reasons = []

        # 1. Check file properties
        files_checks = expected_state.get("files_checks", [])
        for check in files_checks:
            path = check.get("path")
            expected_perms = check.get("perms")
            content_contains = check.get("content_contains")
            
            if path not in fs:
                all_passed = False
                failed_reasons.append(f"Fichier manquant : '{path}'")
                continue
                
            file_info = fs[path]
            
            if expected_perms:
                actual_perms = str(file_info.get("perms", ""))
                # Handle leading 0s or standard representation
                if actual_perms != expected_perms and actual_perms.replace("0", "") != expected_perms.replace("0", ""):
                    all_passed = False
                    failed_reasons.append(f"Permissions incorrectes sur '{path}' : attendu '{expected_perms}', trouvé '{actual_perms}'")
            
            if content_contains:
                actual_content = str(file_info.get("content", ""))
                if content_contains not in actual_content:
                    all_passed = False
                    failed_reasons.append(f"Le contenu de '{path}' n'est pas tout à fait correct.")

        # 2. Check process state
        proc_not_running = expected_state.get("process_not_running")
        if proc_not_running:
            running_proc_names = [p.get("name") for p in processes]
            if proc_not_running in running_proc_names:
                all_passed = False
                failed_reasons.append(f"Le processus '{proc_not_running}' est toujours actif !")

        # 3. Check file deleted
        file_not_exists = expected_state.get("file_not_exists")
        if file_not_exists:
            if file_not_exists in fs:
                all_passed = False
                failed_reasons.append(f"Le fichier temporaire '{file_not_exists}' n'a pas été supprimé.")

        # Handle validation outcome
        if not all_passed:
            level.attempts += 1
            db.commit()
            return {
                "success": False,
                "message": "Validation échouée.\n" + "\n".join(failed_reasons),
                "points_earned": 0
            }

        # Level passed!
        level.status = "completed"
        level.completed_at = datetime.utcnow()
        level.attempts += 1
        
        # Calculate scores
        points_earned = level.points
        
        # Update user stats & preferences
        user = db.query(User).filter(User.id == game.user_id).first()
        if user:
            stats = user.stats or {}
            stats["points"] = stats.get("points", 0) + points_earned
            stats["levels_completed"] = stats.get("levels_completed", 0) + 1
            
            # Badges and Rank Calculations
            badge_unlocked = None
            unlocked_badges = stats.get("badges", [])
            
            # Badge checks
            if game.domain == "linux" and "Linux Ninja" not in unlocked_badges:
                unlocked_badges.append("Linux Ninja")
                badge_unlocked = "Linux Ninja"
            elif game.domain == "security" and "Defender" not in unlocked_badges:
                unlocked_badges.append("Defender")
                badge_unlocked = "Defender"
            elif game.domain == "network" and "Network Sentinel" not in unlocked_badges:
                unlocked_badges.append("Network Sentinel")
                badge_unlocked = "Network Sentinel"

            stats["badges"] = unlocked_badges

            # Rank upgrade based on points
            total_points = stats["points"]
            rank = "Novice"
            if total_points >= 500:
                rank = "Maître"
            elif total_points >= 350:
                rank = "Expert"
            elif total_points >= 200:
                rank = "Administrateur"
            elif total_points >= 100:
                rank = "Apprenti"
            stats["rank"] = rank
            
            user.stats = stats
            db.add(user)

        # Update Game progress
        levels = db.query(Level).filter(Level.game_id == game_id).all()
        completed_count = sum(1 for l in levels if l.status == "completed")
        game.progress = (completed_count / len(levels)) * 100.0 if levels else 0.0
        
        # Unlock next level
        next_level_index = level_index + 1
        next_level = db.query(Level).filter(Level.game_id == game_id, Level.level_index == next_level_index).first()
        if next_level:
            next_level.status = "available"
        else:
            # All levels completed, mark game as completed
            game.status = "completed"

        # Update active levels tracking
        game.current_level_index = next_level_index if next_level else level_index

        db.commit()

        # Generate a cool success message
        success_msg = f"Félicitations ! Vous avez validé le défi '{level.title}' avec succès !"
        if badge_unlocked:
            success_msg += f"\n🏆 Badge Débloqué : **{badge_unlocked}** !"

        return {
            "success": True,
            "message": success_msg,
            "points_earned": points_earned,
            "badge_unlocked": badge_unlocked,
            "next_level_index": next_level_index if next_level else None
        }
