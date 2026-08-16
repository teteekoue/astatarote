import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.core.database.session import Base, engine
from backend.app.api.routes.auth import router as auth_router
from backend.app.api.routes.games import router as games_router
from backend.app.api.websockets.terminal import router as terminal_ws_router
from backend.app.api.websockets.chat import router as chat_ws_router

# Auto-create database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Astatarote API",
    description="Backend pour la plateforme d'apprentissage Linux et Cybersécurité Astatarote",
    version="2.0.0",
)

# CORS — restricted to configured origins (credentials are never sent with wildcard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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


@app.get("/api/health")
def health():
    return {"status": "ok", "project": "Astatarote", "version": "2.0.0"}


# Mount built frontend assets (self-contained production distribution)
frontend_dist_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
)
if os.path.exists(frontend_dist_dir):
    app.mount("/", StaticFiles(directory=frontend_dist_dir, html=True), name="frontend")
else:
    @app.get("/")
    def read_root():
        return {
            "status": "online",
            "project": "Astatarote",
            "description": "Plateforme d'apprentissage Linux et Cybersécurité (Mode Développement API)",
            "docs_url": "/docs",
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
