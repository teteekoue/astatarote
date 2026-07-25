import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from backend.app.core.database.session import SessionLocal
from backend.app.models.models import Game, Level, GameState
from backend.app.core.terminal.manager import TerminalSimulator

logger = logging.getLogger("astarote.websockets.terminal")
router = APIRouter()

@router.websocket("/ws/terminal/{game_id}")
async def terminal_websocket(websocket: WebSocket, game_id: int):
    await websocket.accept()
    db = SessionLocal()
    
    try:
        # Fetch current active level of the game
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            await websocket.send_text(json.dumps({"output": "Erreur : Jeu introuvable.\r\n", "cwd": "/"}))
            await websocket.close()
            return

        level_index = game.current_level_index
        level = db.query(Level).filter(Level.game_id == game_id, Level.level_index == level_index).first()
        if not level:
            # Fall back to first level if current index is invalid
            level = db.query(Level).filter(Level.game_id == game_id).first()

        if not level:
            await websocket.send_text(json.dumps({"output": "Erreur : Aucun niveau disponible.\r\n", "cwd": "/"}))
            await websocket.close()
            return

        # Get or create GameState
        state = db.query(GameState).filter(GameState.game_id == game_id, GameState.level_id == level.id).first()
        if not state:
            # Create a basic fallback state
            state = GameState(
                game_id=game_id,
                level_id=level.id,
                terminal_state={
                    "cwd": "/home/user",
                    "fs": {
                        "/home/user": {"is_dir": True, "perms": "755", "owner": "user"}
                    },
                    "processes": [{"pid": 1, "name": "systemd"}]
                }
            )
            db.add(state)
            db.commit()
            db.refresh(state)

        terminal_state = state.terminal_state or {}
        cwd = terminal_state.get("cwd", "/home/user")

        # Send initial shell prompt
        welcome_msg = (
            f"--- Terminal Interactif Astatarote (Mode: {level.scenario.get('type', 'simulation')}) ---\r\n"
            f"Tapez 'help' pour la liste des commandes.\r\n\r\n"
            f"user@astatarote:{cwd}$ "
        )
        await websocket.send_text(json.dumps({
            "output": welcome_msg,
            "cwd": cwd
        }))

        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            command_line = payload.get("command", "").strip()

            # Execute command on simulator
            stdout, new_state_dict = TerminalSimulator.execute(command_line, terminal_state)
            
            # Save state back to DB
            state.terminal_state = new_state_dict
            db.commit()

            # Format terminal output with carriage returns for xterm.js
            formatted_output = stdout.replace("\n", "\r\n") if stdout else ""
            if formatted_output and not formatted_output.endswith("\r\n"):
                formatted_output += "\r\n"

            new_cwd = new_state_dict.get("cwd", "/home/user")
            prompt = f"user@astatarote:{new_cwd}$ "
            
            # Return result and updated working directory
            await websocket.send_text(json.dumps({
                "output": formatted_output + prompt,
                "cwd": new_cwd
            }))
            
            # Keep updated state in memory for next commands
            terminal_state = new_state_dict

    except WebSocketDisconnect:
        logger.info(f"Terminal WebSocket disconnected for game {game_id}")
    except Exception as e:
        logger.error(f"Error in terminal websocket: {str(e)}")
    finally:
        db.close()
