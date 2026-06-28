"""
app/models/playlist.py
───────────────────────
SQLAlchemy ORM model for the playlists table.

Each row represents one mood playlist created inside Spotify.
We store the spotify_playlist_id so we can:
- Add new tracks to it without recreating it
- Link to it directly from our frontend
- Avoid creating duplicate playlists for the same mood
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Playlist(Base):
    __tablename__ = "playlists"

    # ── Primary Key ───────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ── Foreign Key ───────────────────────────────────────────────────────────
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Spotify Identity ──────────────────────────────────────────────────────
    # The playlist ID inside Spotify — used to add tracks and generate links
    spotify_playlist_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )

    # Display name shown in Spotify e.g. "Romantic Vibes 🌹"
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Which mood this playlist represents e.g. "Romantic"
    mood_category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Spotify URL to open this playlist directly
    spotify_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Sync Tracking ─────────────────────────────────────────────────────────
    # How many tracks are currently in this playlist
    track_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # When we last synced this playlist with Spotify
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

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
    user: Mapped["User"] = relationship("User", back_populates="playlists")  # type: ignore # noqa

    def __repr__(self) -> str:
        return f"<Playlist id={self.id} name={self.name!r} mood={self.mood_category}>"
