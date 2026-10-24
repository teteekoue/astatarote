from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
from typing import List, Optional

logger = logging.getLogger("astarote.api.games")

from backend.app.core.database.session import get_db
from backend.app.catalog import list_games, get_game
from backend.app.models.models import Game, Level, GameState, User
from backend.app.schemas.schemas import (
    GameStart,
    GameResponse,
    LevelResponse,
    ValidateResponse,
    UserResponse,
    UserPreferences,
    UserUpdate,
    UserPasswordUpdate,
    CatalogGameResponse,
)
from backend.app.api.routes.auth import (
    get_current_user,
    get_optional_user,
    verify_password,
    get_password_hash,
)
from backend.app.core.game.engine import GameEngine
from backend.app.core.terminal.engine import session as engine_sessions

router = APIRouter(tags=["games"])


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
# Catalog routes (frozen, hand-crafted courses)
# ---------------------------------------------------------------------------

@router.get("/catalog", response_model=List[CatalogGameResponse])
def get_catalog(
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """List the frozen course catalog, annotated with the user's enrollments."""
    enrollments = {}
    if current_user:
        for game in db.query(Game).filter(Game.user_id == current_user.id).all():
            enrollments[game.catalog_slug] = game

    result = []
    for meta in list_games():
        enrollment = enrollments.get(meta["slug"])
        result.append(CatalogGameResponse(
            **meta,
            enrolled=enrollment is not None,
            enrollment=GameResponse.model_validate(enrollment) if enrollment else None,
        ))
    return result


# ---------------------------------------------------------------------------
# Game (enrollment) management routes
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
def start_game(
    game_in: GameStart,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Instantiate a user's run of a frozen catalog course.

    No AI is involved: levels are copied verbatim from the hand-crafted
    catalog definition into the user's own progress rows.
    """
    catalog_game = get_game(game_in.catalog_slug)
    if not catalog_game:
        raise HTTPException(status_code=404, detail="Parcours introuvable dans le catalogue.")

    # Idempotent enrollment: resume an existing run instead of duplicating.
    existing = (
        db.query(Game)
        .filter(
            Game.user_id == current_user.id,
            Game.catalog_slug == catalog_game["slug"],
            Game.status == "active",
        )
        .first()
    )
    if existing:
        return existing

    game = Game(
        user_id=current_user.id,
        catalog_slug=catalog_game["slug"],
        catalog_version=catalog_game["version"],
        name=catalog_game["name"],
        description=catalog_game["description"],
        domain=catalog_game["domain"],
        level=catalog_game["level"],
        status="active",
        current_level_index=0,
        total_levels=len(catalog_game["levels"]),
        progress=0.0,
    )
    db.add(game)
    db.commit()
    db.refresh(game)

    for idx, level_data in enumerate(catalog_game["levels"]):
        level = Level(
            game_id=game.id,
            level_index=idx,
            title=level_data["title"],
            description=level_data.get("situation_probleme", ""),
            objective=level_data["objective"],
            situation_probleme=level_data.get("situation_probleme"),
            consigne="\n".join(f"- {step}" for step in level_data.get("consigne", []))
            if isinstance(level_data.get("consigne"), list)
            else level_data.get("consigne"),
            support_technique=level_data.get("support_technique"),
            scenario={
                "initial_state": level_data["scenario"].get("initial_state", {}),
                "responses": level_data["scenario"].get("responses", []),
                "forbidden_commands": level_data["scenario"].get("forbidden_commands", []),
                "expected_state": level_data.get("expected_state", {}),
            },
            hints=level_data.get("hints", []),
            difficulty=level_data.get("difficulty", 3),
            points=level_data.get("points", 100),
            time_limit=level_data.get("time_limit", 600),
            status="available" if idx == 0 else "locked",
        )
        db.add(level)
        db.commit()
        db.refresh(level)

        game_state = GameState(
            game_id=game.id,
            level_id=level.id,
            terminal_state={},
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
    """Recreate the level's virtual machine from its frozen scenario."""
    _get_owned_game(db, game_id, current_user)
    level = (
        db.query(Level)
        .filter(Level.game_id == game_id, Level.level_index == level_index)
        .first()
    )
    if not level:
        raise HTTPException(status_code=404, detail="Niveau introuvable")

    # Fresh deterministic session from the initial scenario.
    engine_sessions.reset_session(game_id, level.id, level.scenario)
    state = (
        db.query(GameState)
        .filter(GameState.game_id == game_id, GameState.level_id == level.id)
        .first()
    )
    shell = engine_sessions.get_session(game_id, level.id, level.scenario)
    if state:
        state.terminal_state = engine_sessions.persist(shell)
    db.commit()

    return {
        "success": True,
        "message": "Environnement virtuel réinitialisé — l'état de départ est restauré.",
        "points_earned": 0,
    }


@router.delete("/games/{game_id}")
def delete_game(
    game_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    game = _get_owned_game(db, game_id, current_user)

    # Drop every cached virtual machine for this game.
    for level in db.query(Level).filter(Level.game_id == game_id).all():
        engine_sessions.drop_session(game_id, level.id)

    db.delete(game)
    db.commit()
    return {
        "status": "success",
        "message": f"Le jeu '{game.name}' a été supprimé avec succès.",
    }
