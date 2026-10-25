import os

from dotenv import load_dotenv

# Load the project .env when present (local dev); in production the
# environment is provided by the container / orchestrator.
load_dotenv()


class Settings:
    """Central application settings, configurable through environment variables."""

    SECRET_KEY: str = os.getenv(
        "ASTAROTE_SECRET_KEY",
        "asta-change-me-in-production-2026",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ASTAROTE_TOKEN_EXPIRE_MINUTES", "1440")
    )

    CORS_ORIGINS: list = [
        origin.strip()
        for origin in os.getenv(
            "ASTAROTE_CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000",
        ).split(",")
        if origin.strip()
    ]

    # PHASE DE TEST — accès ouvert : sans token valide, les requêtes sont
    # rattachées au compte démo partagé (admin/admin) au lieu d'être rejetées.
    # Passer à "false" pour rétablir l'authentification SaaS stricte.
    OPEN_ACCESS: bool = os.getenv("ASTAROTE_OPEN_ACCESS", "true").lower() in (
        "1",
        "true",
        "yes",
    )

    # First-run bootstrap admin. During the open-access testing phase this is
    # the shared demo account (admin/admin) used by /api/auth/auto.
    BOOTSTRAP_ADMIN: bool = os.getenv("ASTAROTE_BOOTSTRAP_ADMIN", "true").lower() in (
        "1",
        "true",
        "yes",
    )
    ADMIN_USERNAME: str = os.getenv("ASTAROTE_ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ASTAROTE_ADMIN_PASSWORD", "admin")
    ADMIN_EMAIL: str = os.getenv("ASTAROTE_ADMIN_EMAIL", "admin@astarote.dev")


settings = Settings()
