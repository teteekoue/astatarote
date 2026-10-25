"""
Terminal WebSocket — deterministic engine edition.

Protocol (JSON messages):
  client → server : {"type": "input",     "line": "ls -la"}
                    {"type": "complete",  "line": "ch"}        (tab completion)
  server → client : {"type": "output",    "output": "..."}
                    {"type": "banner",    "output": "..."}
                    {"type": "completion", "candidates": [...], "type": "paths"}
                    {"type": "action",     "action": "clear"}
                    {"type": "error",      "message": "..."}

Each command line is executed by the deterministic Linux engine; the state
is persisted after every command so validation always sees the latest truth.
"""
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from backend.app.core.database.session import SessionLocal
from backend.app.core.terminal.engine import session as engine_sessions
from backend.app.core.terminal.engine.session import banner
from backend.app.models.models import Game, GameState, Level, User
from backend.app.api.routes.auth import resolve_user_from_token

logger = logging.getLogger("astarote.websockets.terminal")
router = APIRouter()


def _resolve_user(db: Session, websocket: WebSocket) -> User | None:
    return resolve_user_from_token(websocket.query_params.get("token"), db)


@router.websocket("/ws/terminal/{game_id}")
async def terminal_websocket(websocket: WebSocket, game_id: int):
    await websocket.accept()

    db: Session = SessionLocal()
    try:
        user = _resolve_user(db, websocket)
        if not user:
            await websocket.send_text(json.dumps({
                "type": "error", "message": "Session expirée — rechargez la page.",
            }))
            await websocket.close(code=4401)
            return

        game = db.query(Game).filter(Game.id == game_id, Game.user_id == user.id).first()
        if not game:
            await websocket.send_text(json.dumps({
                "type": "error", "message": "\r\n[ERREUR] Laboratoire introuvable.\r\n",
            }))
            await websocket.close(code=4403)
            return

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
                "type": "error", "message": "\r\n[ERREUR] Aucun niveau disponible.\r\n",
            }))
            await websocket.close()
            return

        # Load or rebuild the deterministic session for this level.
        state = (
            db.query(GameState)
            .filter(GameState.game_id == game_id, GameState.level_id == level.id)
            .first()
        )
        saved = (state.terminal_state if state else None) or None
        shell = engine_sessions.get_session(game.id, level.id, level.scenario, saved)

        await websocket.send_text(json.dumps({
            "type": "banner",
            "output": banner(shell, level.level_index),
        }))
        await websocket.send_text(json.dumps({"type": "output", "output": shell.prompt}))

        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                continue

            kind = payload.get("type")

            if kind == "input":
                line = payload.get("line", "")
                result = shell.execute(line)
                state = (
                    db.query(GameState)
                    .filter(GameState.game_id == game_id, GameState.level_id == level.id)
                    .first()
                )
                if not state:
                    state = GameState(
                        game_id=game_id, level_id=level.id,
                        terminal_state={}, chat_history=[],
                    )
                    db.add(state)
                state.terminal_state = engine_sessions.persist(shell)
                db.commit()

                if result.action == "clear":
                    await websocket.send_text(json.dumps({"type": "action", "action": "clear"}))
                elif result.output:
                    await websocket.send_text(json.dumps({
                        "type": "output", "output": result.output,
                    }))
                await websocket.send_text(json.dumps({
                    "type": "output", "output": shell.prompt,
                }))

            elif kind == "complete":
                completion = shell.complete(payload.get("line", ""))
                await websocket.send_text(json.dumps({
                    "type": "completion",
                    "candidates": completion.get("candidates", []),
                    "kind": completion.get("type", "paths"),
                }))

    except WebSocketDisconnect:
        logger.info("Terminal WebSocket disconnected for game %s", game_id)
    except Exception as e:
        logger.exception("Error in terminal websocket: %s", e)
    finally:
        db.close()
