import json
import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from backend.app.core.database.session import SessionLocal
from backend.app.core.ai.service import AIService
from backend.app.api.routes.auth import decode_token
from backend.app.models.models import Game, Level, GameState, User

logger = logging.getLogger("astarote.websockets.chat")
router = APIRouter()


@router.websocket("/ws/chat/{game_id}")
async def chat_websocket(websocket: WebSocket, game_id: int):
    token = websocket.query_params.get("token")
    await websocket.accept()

    db = SessionLocal()
    try:
        if not token or not decode_token(token):
            await websocket.send_text(json.dumps({
                "sender": "ai", "message": "[ERREUR] Authentification requise.",
                "timestamp": str(datetime.utcnow()),
            }))
            await websocket.close(code=4401)
            return

        username = decode_token(token)
        user = db.query(User).filter(User.username == username).first()
        game = db.query(Game).filter(Game.id == game_id).first()
        if not user or not game or game.user_id != user.id:
            await websocket.send_text(json.dumps({
                "sender": "ai", "message": "[ERREUR] Accès refusé à ce laboratoire.",
                "timestamp": str(datetime.utcnow()),
            }))
            await websocket.close(code=4403)
            return

        user_prefs = user.preferences if user else {"provider_ia": "fallback"}

        level_index = game.current_level_index
        level = db.query(Level).filter(
            Level.game_id == game_id, Level.level_index == level_index
        ).first()
        if not level:
            level = db.query(Level).filter(Level.game_id == game_id).first()

        if not level:
            await websocket.send_text(json.dumps({
                "sender": "ai", "message": "Aucun défi actif trouvé.",
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

        chat_history = state.chat_history or []

        welcome_message = (
            f"Salut ! Je suis **Nemesis**, ton coéquipier d'apprentissage.\n"
            f"Objectif du défi **'{level.title}'** : {level.objective}\n\n"
            "Je peux t'expliquer des concepts, te donner un indice progressif, "
            "ou vérifier ta démarche — sans jamais te donner la solution brute. "
            "Que veux-tu explorer ?"
        )
        await websocket.send_text(json.dumps({
            "sender": "ai", "message": welcome_message,
            "timestamp": str(datetime.utcnow()),
        }))

        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            user_msg = payload.get("message", "").strip()

            if not user_msg:
                continue

            user_chat_entry = {
                "sender": "user", "message": user_msg,
                "timestamp": str(datetime.utcnow()),
            }
            chat_history.append(user_chat_entry)

            ai_reply_text = AIService.assist_chat(
                game_id=game_id,
                level_title=level.title,
                level_objective=level.objective,
                level_consigne=level.consigne or level.objective,
                current_state={"level_index": level.level_index, "objective": level.objective},
                chat_history=chat_history,
                user_message=user_msg,
                preferences=user_prefs,
            )

            ai_chat_entry = {
                "sender": "ai", "message": ai_reply_text,
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
