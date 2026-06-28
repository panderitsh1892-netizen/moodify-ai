"""
app/schemas/playlist.py
────────────────────────
Pydantic schemas for Playlist serialization.
"""

from datetime import datetime

from pydantic import BaseModel


class PlaylistResponse(BaseModel):
    """Public schema for a single playlist."""
    id: int
    spotify_playlist_id: str
    name: str
    mood_category: str
    spotify_url: str | None
    track_count: int
    last_synced_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PlaylistListResponse(BaseModel):
    """List of playlists."""
    playlists: list[PlaylistResponse]
    total: int


class CreatePlaylistsResponse(BaseModel):
    """Summary returned after creating/syncing playlists."""
    message: str
    playlists_created: int
    playlists_updated: int
    total_tracks_added: int
    playlists: list[PlaylistResponse]
