"""
Chat WebSocket — the AI learning assistant ("Nemesis").

Authenticates the requesting user via token, scopes the conversation to
their own game, and feeds the assistant the level context plus the player's
recent terminal history (from the deterministic engine state) so hints are
relevant to what the player is actually doing.
"""
import json
import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from backend.app.core.database.session import SessionLocal
from backend.app.core.ai.service import AIService
from backend.app.models.models import Game, GameState, Level, User
from backend.app.api.routes.auth import decode_token

logger = logging.getLogger("astarote.websockets.chat")
router = APIRouter()


def _resolve_user(db: Session, websocket: WebSocket) -> User | None:
    token = websocket.query_params.get("token")
    if not token:
        return None
    username = decode_token(token)
    if not username:
        return None
    return db.query(User).filter(User.username == username).first()


@router.websocket("/ws/chat/{game_id}")
async def chat_websocket(websocket: WebSocket, game_id: int):
    await websocket.accept()

    db: Session = SessionLocal()
    try:
        user = _resolve_user(db, websocket)
        if not user:
            await websocket.send_text(json.dumps({
                "sender": "ai",
                "message": "Session expirée — rechargez la page pour retrouver l'assistant.",
                "timestamp": str(datetime.utcnow()),
            }))
            await websocket.close(code=4401)
            return

        game = db.query(Game).filter(Game.id == game_id, Game.user_id == user.id).first()
        if not game:
            await websocket.send_text(json.dumps({
                "sender": "ai",
                "message": "Laboratoire introuvable.",
                "timestamp": str(datetime.utcnow()),
            }))
            await websocket.close(code=4403)
            return

        user_prefs = user.preferences or {"provider_ia": "fallback"}

        raw_level = websocket.query_params.get("level")
        if raw_level is not None and raw_level.isdigit():
            level_index = int(raw_level)
        else:
            level_index = game.current_level_index
        level = db.query(Level).filter(
            Level.game_id == game_id, Level.level_index == level_index
        ).first()
        if not level:
            level = db.query(Level).filter(Level.game_id == game_id).first()
        if not level:
            await websocket.send_text(json.dumps({
                "sender": "ai",
                "message": "Aucun défi actif trouvé.",
                "timestamp": str(datetime.utcnow()),
            }))
            await websocket.close()
            return

        state = db.query(GameState).filter(
            GameState.game_id == game_id, GameState.level_id == level.id
        ).first()
        if not state:
            state = GameState(game_id=game_id, level_id=level.id, terminal_state={}, chat_history=[])
            db.add(state)
            db.commit()
            db.refresh(state)

        chat_history = list(state.chat_history or [])
        terminal_history = list((state.terminal_state or {}).get("history", []) or [])

        # Replay the persisted conversation (silent resume).
        for entry in chat_history[-30:]:
            await websocket.send_text(json.dumps(entry))

        if not chat_history:
            welcome_message = (
                f"Salut ! Je suis **Nemesis**, ton assistante d'apprentissage. 🤖\n\n"
                f"On attaque le défi **« {level.title} »**.\n\n"
                "Je peux t'expliquer un concept, décrypter une erreur ou te donner un "
                "indice progressif — mais jamais la solution toute faite. "
                "Comment puis-je t'aider ?"
            )
            welcome = {
                "sender": "ai",
                "message": welcome_message,
                "timestamp": str(datetime.utcnow()),
            }
            chat_history.append(welcome)
            state.chat_history = chat_history
            db.commit()
            await websocket.send_text(json.dumps(welcome))

        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            user_msg = payload.get("message", "").strip()

            if not user_msg:
                continue

            # Refresh terminal history on each message for relevant hints.
            db.refresh(state)
            terminal_history = list((state.terminal_state or {}).get("history", []) or [])

            user_chat_entry = {
                "sender": "user",
                "message": user_msg,
                "timestamp": str(datetime.utcnow()),
            }
            chat_history.append(user_chat_entry)

            ai_reply_text = AIService.assist_chat(
                game_name=game.name,
                level_title=level.title,
                level_objective=level.objective,
                level_consigne=level.consigne or level.objective,
                level_hints=level.hints or [],
                terminal_history=terminal_history,
                chat_history=chat_history,
                user_message=user_msg,
                preferences=user_prefs,
            )

            ai_chat_entry = {
                "sender": "ai",
                "message": ai_reply_text,
                "timestamp": str(datetime.utcnow()),
            }
            chat_history.append(ai_chat_entry)
            state.chat_history = chat_history
            db.commit()

            await websocket.send_text(json.dumps(ai_chat_entry))

    except WebSocketDisconnect:
        logger.info("Chat WebSocket disconnected for game %s", game_id)
    except Exception as e:
        logger.exception("Error in chat websocket: %s", e)
    finally:
        db.close()
