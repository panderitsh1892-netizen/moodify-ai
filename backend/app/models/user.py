"""
app/models/user.py
──────────────────
SQLAlchemy ORM model for the users table.

Design decisions:

1. We store both access_token and refresh_token encrypted in the database.
   The refresh_token is the most sensitive — it never expires unless revoked,
   so losing it means losing access to the user's Spotify account.

2. token_expiry stores when the access_token expires. Before every Spotify
   API call, we check if now > token_expiry and refresh if needed.

3. is_active flag lets us soft-disable accounts without deleting data.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    # ── Primary Key ───────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ── Spotify Identity ──────────────────────────────────────────────────────
    # Spotify's unique ID for this user (e.g. "31xample...")
    # unique=True prevents duplicate accounts for the same Spotify user.
    spotify_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Profile image URL from Spotify
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Spotify Tokens ────────────────────────────────────────────────────────
    # Access token: short-lived (1 hour), used for Spotify API calls
    access_token: Mapped[str] = mapped_column(Text, nullable=False)

    # Refresh token: long-lived, used to get new access tokens
    # Never expires unless user revokes access in Spotify settings
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)

    # When the access token expires (UTC)
    token_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Account State ─────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── Timestamps ────────────────────────────────────────────────────────────
    # server_default=func.now() sets the value at the DATABASE level,
    # meaning it works even if we forget to set it in Python.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} spotify_id={self.spotify_id} email={self.email}>"
