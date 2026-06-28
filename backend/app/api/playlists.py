"""
app/api/playlists.py
─────────────────────
Playlist management endpoints.

Endpoints:
    POST /api/playlists/sync  → Create or update all mood playlists in Spotify
    GET  /api/playlists/      → List all playlists in our database
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.playlist import (
    CreatePlaylistsResponse,
    PlaylistListResponse,
    PlaylistResponse,
)
from app.services.playlist_service import playlist_service

router = APIRouter()


# ── Sync All Playlists ─────────────────────────────────────────────────────────
@router.post("/sync", response_model=CreatePlaylistsResponse)
async def sync_playlists(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create or update all mood playlists in the user's Spotify account.

    For each mood category that has categorized tracks:
    - Creates a new Spotify playlist if one doesn't exist yet
    - Adds any new tracks not already in the playlist

    Run this after:
    1. POST /api/tracks/import    (import listening history)
    2. POST /api/tracks/categorize (assign moods)
    3. POST /api/playlists/sync   (create playlists) ← this endpoint
    """
    result = await playlist_service.create_or_sync_all_playlists(
        user=current_user,
        db=db,
    )

    return CreatePlaylistsResponse(
        message=result["message"],
        playlists_created=result["playlists_created"],
        playlists_updated=result["playlists_updated"],
        total_tracks_added=result["total_tracks_added"],
        playlists=[
            PlaylistResponse.model_validate(p)
            for p in result["playlists"]
        ],
    )


# ── List Playlists ─────────────────────────────────────────────────────────────
@router.get("/", response_model=PlaylistListResponse)
async def list_playlists(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return all mood playlists we've created for this user.

    Each playlist includes:
    - The Spotify URL to open it directly
    - How many tracks it contains
    - When it was last synced
    """
    playlists, total = await playlist_service.get_user_playlists(
        user_id=current_user.id,
        db=db,
    )

    return PlaylistListResponse(
        playlists=[PlaylistResponse.model_validate(p) for p in playlists],
        total=total,
    )
