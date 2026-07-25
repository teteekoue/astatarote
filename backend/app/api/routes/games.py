from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.app.core.database.session import get_db
from backend.app.models.models import Game, Level, GameState, User
from backend.app.schemas.schemas import GameCreate, GameResponse, LevelResponse, ValidateResponse, UserResponse, UserPreferences
from backend.app.api.routes.auth import get_current_user
from backend.app.core.ai.service import AIService
from backend.app.core.game.engine import GameEngine

router = APIRouter(tags=["games"])

# User settings and profile routes
@router.get("/users/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/users/me/preferences", response_model=UserResponse)
def update_preferences(
    prefs: UserPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.preferences = prefs.model_dump()
    db.commit()
    db.refresh(current_user)
    return current_user


# Game management routes
@router.get("/games", response_model=List[GameResponse])
def get_games(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    games = db.query(Game).filter(Game.user_id == current_user.id).all()
    return games

@router.post("/games", response_model=GameResponse)
def create_game(
    game_in: GameCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total_levels = 3  # We pre-generate 3 levels for an optimal learning curve
    
    # Create the game
    game = Game(
        user_id=current_user.id,
        name=game_in.name,
        description=game_in.description or f"Apprendre {game_in.domain} ({game_in.level})",
        domain=game_in.domain,
        level=game_in.level,
        status="active",
        current_level_index=0,
        total_levels=total_levels,
        progress=0.0
    )
    db.add(game)
    db.commit()
    db.refresh(game)

    # Pre-generate levels using the AI service
    for idx in range(total_levels):
        try:
            raw_level = AIService.generate_level(
                domain=game.domain,
                user_level=game.level,
                level_index=idx,
                custom_prompt=game_in.custom_prompt if idx == 0 else None,
                preferences=current_user.preferences or {}
            )
        except Exception as e:
            # Safe fallback if AI service fails
            raw_level = {
                "title": f"Défi {idx+1}",
                "description": "Scénario généré automatiquement.",
                "objective": "Compléter la configuration système.",
                "scenario": {
                    "type": "simulation",
                    "initial_state": {"cwd": "/home/user", "fs": {"/home/user": {}}},
                    "expected_state": {"files_checks": []}
                },
                "hints": ["Examinez le système", "Lisez les consignes"],
                "difficulty": 2,
                "points": 100,
                "time_limit": 600
            }

        # Save Level to database
        level = Level(
            game_id=game.id,
            level_index=idx,
            title=raw_level.get("title", f"Défi {idx+1}"),
            description=raw_level.get("description", ""),
            objective=raw_level.get("objective", ""),
            scenario=raw_level.get("scenario", {}),
            hints=raw_level.get("hints", []),
            difficulty=raw_level.get("difficulty", 3),
            points=raw_level.get("points", 100),
            time_limit=raw_level.get("time_limit", 600),
            status="available" if idx == 0 else "locked"
        )
        db.add(level)
        db.commit()
        db.refresh(level)

        # Initialize GameState with level initial state
        initial_state = level.scenario.get("initial_state", {})
        game_state = GameState(
            game_id=game.id,
            level_id=level.id,
            terminal_state=initial_state,
            chat_history=[],
            memory_summary="{}"
        )
        db.add(game_state)
        db.commit()

    return game

@router.get("/games/{game_id}/levels", response_model=List[LevelResponse])
def get_game_levels(
    game_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    game = db.query(Game).filter(Game.id == game_id, Game.user_id == current_user.id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Jeu introuvable")
    return game.levels

@router.get("/games/{game_id}/levels/{level_index}", response_model=LevelResponse)
def get_game_level(
    game_id: int,
    level_index: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    game = db.query(Game).filter(Game.id == game_id, Game.user_id == current_user.id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Jeu introuvable")
    
    level = db.query(Level).filter(Level.game_id == game_id, Level.level_index == level_index).first()
    if not level:
        raise HTTPException(status_code=404, detail="Niveau introuvable")
    return level

@router.post("/games/{game_id}/levels/{level_index}/validate", response_model=ValidateResponse)
def validate_game_level(
    game_id: int,
    level_index: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Ensure game ownership
    game = db.query(Game).filter(Game.id == game_id, Game.user_id == current_user.id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Jeu introuvable")

    result = GameEngine.validate_level(db, game_id, level_index)
    return result

@router.delete("/games/{game_id}")
def delete_game(
    game_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    game = db.query(Game).filter(Game.id == game_id, Game.user_id == current_user.id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Jeu introuvable")
    
    db.delete(game)
    db.commit()
    return {"status": "success", "message": f"Le jeu '{game.name}' a été supprimé avec succès."}
