import os
import sys

# Dynamic sys.path insertion to support running from any directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)         # backend/
grandparent_dir = os.path.dirname(parent_dir)     # root folder/

if grandparent_dir not in sys.path:
    sys.path.insert(0, grandparent_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.database.session import Base, engine
from backend.app.api.routes.auth import router as auth_router
from backend.app.api.routes.games import router as games_router
from backend.app.api.websockets.terminal import router as terminal_ws_router
from backend.app.api.websockets.chat import router as chat_ws_router

# Auto-create SQLite database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Astatarote API",
    description="Backend pour la plateforme d'apprentissage Linux et Cybersécurité Astatarote",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST Routes
app.include_router(auth_router, prefix="/api")
app.include_router(games_router, prefix="/api")

# WebSocket Routes
app.include_router(terminal_ws_router)
app.include_router(chat_ws_router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "project": "Astatarote",
        "description": "Plateforme d'apprentissage Linux et Cybersécurité",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main.py:app", host="0.0.0.0", port=8000, reload=True)
