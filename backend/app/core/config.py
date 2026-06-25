"""
app/core/config.py
──────────────────
Single source of truth for all application configuration.

Design decision: pydantic-settings reads values from environment variables
(and .env files in development). Every setting is type-checked at startup —
if DATABASE_URL is missing, the app crashes immediately with a clear error,
not silently at runtime when the first DB query runs.

Usage:
    from app.core.config import settings
    print(settings.DATABASE_URL)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME: str = "Moodify AI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # The environment name ("development", "staging", "production").
    # Used to toggle behaviour (e.g. detailed error messages only in dev).
    ENVIRONMENT: str = "development"

    # ── Security ──────────────────────────────────────────────────────────────
    # SECRET_KEY signs JWT session tokens. Must be long, random, and secret.
    # Generate one with: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # ── Database ──────────────────────────────────────────────────────────────
    # asyncpg:// driver prefix is required for SQLAlchemy's async engine.
    DATABASE_URL: str = "postgresql+asyncpg://moodify:moodify@localhost:5432/moodify"

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Spotify OAuth ─────────────────────────────────────────────────────────
    # Get these from https://developer.spotify.com/dashboard
    SPOTIFY_CLIENT_ID: str = ""
    SPOTIFY_CLIENT_SECRET: str = ""
    SPOTIFY_REDIRECT_URI: str = "http://localhost:8000/api/auth/callback"

    # Scopes define what Moodify is allowed to do on behalf of the user.
    # - user-read-recently-played: read listening history
    # - playlist-modify-public:   create and edit public playlists
    # - playlist-modify-private:  create and edit private playlists
    # - user-read-email:          read user's email (for our user record)
    SPOTIFY_SCOPES: str = (
        "user-read-recently-played "
        "playlist-modify-public "
        "playlist-modify-private "
        "user-read-email "
        "user-read-private"
    )

    # ── Celery ────────────────────────────────────────────────────────────────
    # Celery uses Redis as both the message broker (where tasks are queued)
    # and the result backend (where task results are stored).
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # How often (in seconds) the sync job runs per user.
    SYNC_INTERVAL_SECONDS: int = 1800  # 30 minutes

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Origins allowed to make cross-origin requests to our API.
    # In production this would be your actual domain.
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:8000",  # FastAPI (for Swagger UI)
    ]

    # pydantic-settings config: look for a .env file in the project root.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Single shared instance — import this everywhere.
# Python's module system caches it, so it's effectively a singleton.
settings = Settings()
