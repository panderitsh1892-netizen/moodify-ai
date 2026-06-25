"""
app/models/track.py
────────────────────
SQLAlchemy ORM model for the tracks table.

Each row represents ONE listen event — one song played once at a specific time.
If the user listens to the same song 5 times, we store 5 rows.

Design decisions:

1. We store spotify_track_id separately from our internal id.
   Our id is the primary key for our database relationships.
   spotify_track_id is used to call Spotify's API for audio features.

2. audio features (valence, energy, tempo, danceability) are nullable
   because we fetch them in Phase 5 AFTER storing the track.
   Phase 4 stores the track. Phase 5 fills in the audio features.

3. mood_category is also nullable for the same reason —
   it gets set in Phase 5 after we analyze the audio features.

4. UniqueConstraint on (user_id, spotify_track_id, played_at) prevents
   duplicate listen events from being stored if the sync job runs twice.
"""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Track(Base):
    __tablename__ = "tracks"

    # Prevent duplicate listen events
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "spotify_track_id",
            "played_at",
            name="uq_user_track_played_at",
        ),
    )

    # ── Primary Key ───────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ── Foreign Key ───────────────────────────────────────────────────────────
    # Which user listened to this track
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Spotify Track Identity ────────────────────────────────────────────────
    spotify_track_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    artist: Mapped[str] = mapped_column(String(500), nullable=False)
    album: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Album art URL from Spotify
    album_art_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Track duration in milliseconds (as returned by Spotify)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # When the user listened to this track (UTC, from Spotify)
    played_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # ── Audio Features (filled in Phase 5) ───────────────────────────────────
    # Spotify's measure of musical positivity (0.0 = sad, 1.0 = happy)
    valence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Perceptual measure of intensity and activity (0.0 = calm, 1.0 = energetic)
    energy: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Overall estimated tempo in BPM
    tempo: Mapped[float | None] = mapped_column(Float, nullable=True)

    # How suitable the track is for dancing (0.0 = least, 1.0 = most)
    danceability: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Detects presence of spoken words (0.0 = music, 1.0 = speech)
    speechiness: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Musical key the track is in (0=C, 1=C#, 2=D, ..., 11=B)
    track_key: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Mood Category (filled in Phase 5) ────────────────────────────────────
    # e.g. "Romantic", "Energetic", "Melancholic", "Happy", "Chill", "Angry"
    mood_category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    # Allows: track.user → gets the User object
    user: Mapped["User"] = relationship("User", back_populates="tracks")  # type: ignore # noqa

    def __repr__(self) -> str:
        return f"<Track id={self.id} title={self.title!r} artist={self.artist!r}>"
