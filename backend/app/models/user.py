"""
app/models/user.py
──────────────────
SQLAlchemy ORM model for the users table.

Design decisions:

1. We store both access_token and refresh_token in the database.
   The refresh_token is the most sensitive — it never expires unless revoked,
   so losing it means losing access to the user's Spotify account.

2. token_expiry stores when the access_token expires. Before every Spotify
   API call, we check if now > token_expiry and refresh if needed.

3. is_active flag lets us soft-disable accounts without deleting data.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.track import Track


class User(Base):
    __tablename__ = "users"

    # ── Primary Key ───────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ── Spotify Identity ──────────────────────────────────────────────────────
    spotify_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Spotify Tokens ────────────────────────────────────────────────────────
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    token_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Account State ─────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── Timestamps ────────────────────────────────────────────────────────────
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

    # ── Relationships ─────────────────────────────────────────────────────────
    # Allows: user.tracks → gets list of Track objects
    # TYPE_CHECKING import above avoids circular imports at runtime
    tracks: Mapped[list[Track]] = relationship(
        "Track",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} spotify_id={self.spotify_id} email={self.email}>"
