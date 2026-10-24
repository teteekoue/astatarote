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

    # First-run bootstrap admin (zero-config friendly). Disable in production.
    BOOTSTRAP_ADMIN: bool = os.getenv("ASTAROTE_BOOTSTRAP_ADMIN", "true").lower() in (
        "1",
        "true",
        "yes",
    )
    ADMIN_USERNAME: str = os.getenv("ASTAROTE_ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ASTAROTE_ADMIN_PASSWORD", "admin123")
    ADMIN_EMAIL: str = os.getenv("ASTAROTE_ADMIN_EMAIL", "admin@astarote.local")


settings = Settings()
