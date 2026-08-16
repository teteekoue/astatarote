import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from backend.app.core.database.session import SessionLocal
from backend.app.core.terminal.manager import TerminalManager, is_dangerous, GUARD_MESSAGE
from backend.app.core.terminal.sandbox import SandboxManager
from backend.app.models.models import Game, Level

logger = logging.getLogger("astarote.websockets.terminal")
router = APIRouter()


async def _forward_to_shell(session, websocket, text: str) -> None:
    """Forwards keystrokes to the PTY, blocking full lines that are dangerous.

    The shell runs in canonical mode: characters are buffered until Enter.
    We therefore detect dangerous commands on complete lines and, instead of
    submitting them, send SIGINT (Ctrl-C) to flush the pending input line.
    """
    output = bytearray()
    for ch in text:
        if ch in "\r\n":
            line = getattr(session, "pending_line", "")
            session.pending_line = ""
            if line.strip() and is_dangerous(line):
                session.write(b"\x03")  # Ctrl-C: discard buffered line + reprompt
                await websocket.send_text(json.dumps({"output": GUARD_MESSAGE}))
                continue
            output.extend(ch.encode("utf-8", errors="ignore"))
        elif ch == "\x7f":  # backspace edits the pending line
            session.pending_line = getattr(session, "pending_line", "")[:-1]
            output.extend(b"\x7f")
        elif ch in ("\x03", "\x04", "\x1a", "\x1b") or not ch.isprintable():
            # Control characters (Ctrl-C, EOF, escape, arrows...) pass through.
            session.pending_line = ""
            output.extend(ch.encode("utf-8", errors="ignore"))
        elif ch.isprintable() or ch == "\t":
            session.pending_line = getattr(session, "pending_line", "") + ch
            output.extend(ch.encode("utf-8", errors="ignore"))
        else:
            output.extend(ch.encode("utf-8", errors="ignore"))

    if output:
        session.write(bytes(output))


@router.websocket("/ws/terminal/{game_id}")
async def terminal_websocket(websocket: WebSocket, game_id: int):
    await websocket.accept()

    db = SessionLocal()
    session = None
    current_level_id = None
    try:
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            await websocket.send_text(json.dumps({"output": "\r\n[ERREUR] Laboratoire introuvable.\r\n"}))
            await websocket.close(code=4403)
            return

        # The terminal shell must match the level the user is currently viewing.
        # 'level' query param carries the selected level_index; fall back to the
        # game's current progress only when none is provided.
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
            await websocket.send_text(json.dumps({"output": "\r\n[ERREUR] Aucun niveau disponible.\r\n"}))
            await websocket.close()
            return

        # Prepare the real sandbox for this level
        workdir = SandboxManager.prepare(game_id, level.id, level.scenario)
        current_level_id = level.id

        # Open (or reuse) a real bash session inside the sandbox
        session = TerminalManager.get_or_create(game_id, level.id, workdir)

        # Send shell banner + any buffered output
        banner = (
            f"\r\n\x1b[1;32mAstatarote Terminal\x1b[0m — shell réel "
            f"dans la sandbox du défi {level_index + 1}.\r\n"
            f"Tapez \x1b[1;36mhelp\x1b[0m, \x1b[1;36mls\x1b[0m, \x1b[1;36mman\x1b[0m... Tous les outils Linux sont disponibles.\r\n\r\n"
        )
        await websocket.send_text(json.dumps({"output": banner}))
        initial = session.read()
        if initial:
            await websocket.send_text(json.dumps({"output": initial.decode("utf-8", errors="replace")}))

        loop = asyncio.get_running_loop()

        async def pump_output():
            while not session.closed:
                data = session.read()
                if data:
                    await websocket.send_text(
                        json.dumps({"output": data.decode("utf-8", errors="replace")})
                    )
                await asyncio.sleep(0.02)

        recv_task = asyncio.create_task(websocket.receive_text())
        pump_task = asyncio.create_task(pump_output())

        try:
            while not session.closed:
                done, pending = await asyncio.wait(
                    {recv_task, pump_task}, return_when=asyncio.FIRST_COMPLETED
                )
                if pump_task in done:
                    # shell exited
                    break

                if recv_task.done():
                    try:
                        payload = json.loads(recv_task.result())
                    except Exception:
                        break

                    # Viewport resize messages arrive as top-level {"type":"resize"}
                    if payload.get("type") == "resize":
                        session.set_size(payload.get("rows", 24), payload.get("cols", 80))
                        recv_task = asyncio.create_task(websocket.receive_text())
                        continue

                    message = payload.get("command", "")
                    if message:
                        await _forward_to_shell(session, websocket, message)
                    recv_task = asyncio.create_task(websocket.receive_text())
        except WebSocketDisconnect:
            pass
        finally:
            recv_task.cancel()
            pump_task.cancel()

    except WebSocketDisconnect:
        logger.info("Terminal WebSocket disconnected for game %s", game_id)
    except Exception as e:
        logger.exception("Error in terminal websocket: %s", e)
    finally:
        if session is not None:
            session.write(b"\x04")  # Send EOF to cleanly exit shell
        if current_level_id is not None:
            TerminalManager.close_session(game_id, current_level_id)
        db.close()
