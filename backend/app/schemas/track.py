"""
app/schemas/track.py
─────────────────────
Pydantic schemas for Track serialization.

TrackResponse    — what we return to the frontend for a single track
ImportResponse   — summary returned after importing listening history
"""

from datetime import datetime

from pydantic import BaseModel


class TrackResponse(BaseModel):
    """
    Safe public schema for a track — returned to the frontend.
    Includes all fields the UI needs to display a track card.
    """
    id: int
    spotify_track_id: str
    title: str
    artist: str
    album: str | None
    album_art_url: str | None
    duration_ms: int | None
    played_at: datetime

    # Audio features (null until Phase 5 fills them in)
    valence: float | None
    energy: float | None
    tempo: float | None
    danceability: float | None

    # Mood (null until Phase 5 categorizes them)
    mood_category: str | None

    created_at: datetime

    model_config = {"from_attributes": True}


class ImportResponse(BaseModel):
    """Summary returned after running a listening history import."""
    message: str
    total_fetched: int       # How many tracks Spotify returned
    new_tracks_saved: int    # How many were actually new and saved
    duplicates_skipped: int  # How many were already in the database


class TrackListResponse(BaseModel):
    """Paginated list of tracks."""
    tracks: list[TrackResponse]
    total: int
    page: int
    page_size: int
