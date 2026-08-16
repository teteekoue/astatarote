from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from backend.app.core.config import settings
from backend.app.core.database.session import get_db
from backend.app.core.terminal.sandbox import SandboxManager
from backend.app.models.models import Game, Level, GameState, User
from backend.app.schemas.schemas import (
    GameCreate,
    GameResponse,
    LevelResponse,
    ValidateResponse,
    UserResponse,
    UserPreferences,
    UserUpdate,
    UserPasswordUpdate,
)
from backend.app.api.routes.auth import get_current_user, verify_password, get_password_hash
from backend.app.core.ai.service import AIService
from backend.app.core.game.engine import GameEngine

router = APIRouter(tags=["games"])

TOTAL_LEVELS = 3


def _get_owned_game(db: Session, game_id: int, user: User) -> Game:
    game = (
        db.query(Game)
        .filter(Game.id == game_id, Game.user_id == user.id)
        .first()
    )
    if not game:
        raise HTTPException(status_code=404, detail="Jeu introuvable")
    return game


# ---------------------------------------------------------------------------
# User settings & profile routes
# ---------------------------------------------------------------------------

@router.get("/users/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/users/me", response_model=UserResponse)
def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = payload.model_dump(exclude_none=True)
    if "username" in data:
        existing = (
            db.query(User)
            .filter(User.username == data["username"], User.id != current_user.id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=400, detail="Nom d'utilisateur déjà utilisé"
            )
        current_user.username = data["username"]
    if "email" in data:
        current_user.email = data["email"]
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/users/me/password", response_model=UserResponse)
def update_my_password(
    payload: UserPasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=400, detail="Le mot de passe actuel est incorrect"
        )
    current_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/users/me/preferences", response_model=UserResponse)
def update_preferences(
    prefs: UserPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_data = prefs.model_dump(exclude_none=True)

    # Keep the existing key when the client sends an empty or masked value
    existing_key = (current_user.preferences or {}).get("api_key")
    new_key = new_data.get("api_key")
    if new_key in (None, "") or (new_key and "•" in new_key):
        new_data["api_key"] = existing_key or ""

    merged = dict(current_user.preferences or {})
    merged.update(new_data)
    current_user.preferences = merged
    db.commit()
    db.refresh(current_user)
    return current_user


# ---------------------------------------------------------------------------
# Game management routes
# ---------------------------------------------------------------------------

@router.get("/games", response_model=List[GameResponse])
def get_games(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Game)
        .filter(Game.user_id == current_user.id)
        .order_by(Game.created_at.desc())
        .all()
    )


@router.post("/games", response_model=GameResponse)
def create_game(
    game_in: GameCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    game = Game(
        user_id=current_user.id,
        name=game_in.name,
        description=game_in.description
        or f"Apprendre {game_in.domain} ({game_in.level})",
        domain=game_in.domain,
        level=game_in.level,
        status="active",
        current_level_index=0,
        total_levels=TOTAL_LEVELS,
        progress=0.0,
    )
    db.add(game)
    db.commit()
    db.refresh(game)

    for idx in range(TOTAL_LEVELS):
        try:
            raw_level = AIService.generate_level(
                domain=game.domain,
                user_level=game.level,
                level_index=idx,
                custom_prompt=game_in.custom_prompt,
                preferences=current_user.preferences or {},
            )
        except Exception as e:
            raw_level = None

        if not raw_level:
            # Ultra-safe fallback if even the template fails
            raw_level = AIService._generate_fallback_level(
                game.domain, game.level, idx, game_in.custom_prompt
            )

        level = Level(
            game_id=game.id,
            level_index=idx,
            title=raw_level.get("title", f"Défi {idx + 1}"),
            description=raw_level.get("situation_probleme") or raw_level.get("description", ""),
            objective=raw_level.get("objective", ""),
            situation_probleme=raw_level.get("situation_probleme"),
            consigne=raw_level.get("consigne"),
            support_technique=raw_level.get("support_technique"),
            scenario=raw_level.get("scenario", {}),
            hints=raw_level.get("hints", []),
            difficulty=raw_level.get("difficulty", 3),
            points=raw_level.get("points", 100),
            time_limit=raw_level.get("time_limit", 600),
            status="available" if idx == 0 else "locked",
        )
        db.add(level)
        db.commit()
        db.refresh(level)

        game_state = GameState(
            game_id=game.id,
            level_id=level.id,
            terminal_state={
                "level_index": idx,
                "sandbox_dir": SandboxManager.sandbox_dir(game.id, level.id),
            },
            chat_history=[],
            memory_summary="{}",
        )
        db.add(game_state)

    db.commit()
    db.refresh(game)
    return game


@router.get("/games/{game_id}/levels", response_model=List[LevelResponse])
def get_game_levels(
    game_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_owned_game(db, game_id, current_user)
    return (
        db.query(Level)
        .filter(Level.game_id == game_id)
        .order_by(Level.level_index.asc())
        .all()
    )


@router.get("/games/{game_id}/levels/{level_index}", response_model=LevelResponse)
def get_game_level(
    game_id: int,
    level_index: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_owned_game(db, game_id, current_user)
    level = (
        db.query(Level)
        .filter(Level.game_id == game_id, Level.level_index == level_index)
        .first()
    )
    if not level:
        raise HTTPException(status_code=404, detail="Niveau introuvable")
    return level


@router.post("/games/{game_id}/levels/{level_index}/validate", response_model=ValidateResponse)
def validate_game_level(
    game_id: int,
    level_index: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_owned_game(db, game_id, current_user)
    return GameEngine.validate_level(db, game_id, level_index)


@router.post("/games/{game_id}/levels/{level_index}/reset", response_model=ValidateResponse)
def reset_game_level(
    game_id: int,
    level_index: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Recreates the level sandbox from scratch (processes killed, files restored)."""
    _get_owned_game(db, game_id, current_user)
    level = (
        db.query(Level)
        .filter(Level.game_id == game_id, Level.level_index == level_index)
        .first()
    )
    if not level:
        raise HTTPException(status_code=404, detail="Niveau introuvable")

    SandboxManager.prepare(game_id, level.id, level.scenario)
    return {
        "success": True,
        "message": "Sandbox du niveau réinitialisée. L'environnement a été restauré à son état initial.",
        "points_earned": 0,
    }


@router.delete("/games/{game_id}")
def delete_game(
    game_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    game = _get_owned_game(db, game_id, current_user)
    SandboxManager.cleanup(game_id, 0)
    db.delete(game)
    db.commit()
    return {
        "status": "success",
        "message": f"Le jeu '{game.name}' a été supprimé avec succès.",
    }
