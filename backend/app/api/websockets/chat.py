import json
import logging
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from backend.app.core.database.session import SessionLocal
from backend.app.models.models import Game, Level, GameState, User
from backend.app.core.ai.service import AIService

logger = logging.getLogger("astarote.websockets.chat")
router = APIRouter()

@router.websocket("/ws/chat/{game_id}")
async def chat_websocket(websocket: WebSocket, game_id: int):
    await websocket.accept()
    db = SessionLocal()

    try:
        # Fetch current game and user to get AI settings
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            await websocket.send_text(json.dumps({"sender": "ai", "message": "Jeu introuvable.", "timestamp": str(datetime.utcnow())}))
            await websocket.close()
            return

        user = db.query(User).filter(User.id == game.user_id).first()
        user_prefs = user.preferences if user else {"provider_ia": "fallback"}

        level_index = game.current_level_index
        level = db.query(Level).filter(Level.game_id == game_id, Level.level_index == level_index).first()
        if not level:
            level = db.query(Level).filter(Level.game_id == game_id).first()

        if not level:
            await websocket.send_text(json.dumps({"sender": "ai", "message": "Aucun défi actif trouvé.", "timestamp": str(datetime.utcnow())}))
            await websocket.close()
            return

        # Fetch GameState for history
        state = db.query(GameState).filter(GameState.game_id == game_id, GameState.level_id == level.id).first()
        if not state:
            state = GameState(game_id=game_id, level_id=level.id, terminal_state={}, chat_history=[])
            db.add(state)
            db.commit()
            db.refresh(state)

        chat_history = state.chat_history or []

        # Send greeting message
        welcome_message = f"Salut ! Je suis ton coéquipier d'apprentissage pour le défi **'{level.title}'**. Comment puis-je t'aider aujourd'hui ?"
        await websocket.send_text(json.dumps({
            "sender": "ai",
            "message": welcome_message,
            "timestamp": str(datetime.utcnow())
        }))

        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            user_msg = payload.get("message", "").strip()

            if not user_msg:
                continue

            # Append user message to history
            user_chat_entry = {"sender": "user", "message": user_msg, "timestamp": str(datetime.utcnow())}
            chat_history.append(user_chat_entry)

            # Call AI Service for pedagogical help
            ai_reply_text = AIService.assist_chat(
                game_id=game_id,
                level_title=level.title,
                level_objective=level.objective,
                current_state=state.terminal_state or {},
                chat_history=chat_history,
                user_message=user_msg,
                preferences=user_prefs
            )

            # Append AI message to history
            ai_chat_entry = {"sender": "ai", "message": ai_reply_text, "timestamp": str(datetime.utcnow())}
            chat_history.append(ai_chat_entry)

            # Save updated history
            state.chat_history = chat_history
            db.commit()

            # Return response
            await websocket.send_text(json.dumps(ai_chat_entry))

    except WebSocketDisconnect:
        logger.info(f"Chat WebSocket disconnected for game {game_id}")
    except Exception as e:
        logger.error(f"Error in chat websocket: {str(e)}")
    finally:
        db.close()
