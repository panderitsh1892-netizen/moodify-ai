"""
app/api/tracks.py
──────────────────
Track management endpoints.

Endpoints:
    POST /api/tracks/import     → Trigger a listening history import
    GET  /api/tracks/           → List all imported tracks (paginated)
    GET  /api/tracks/stats      → Summary stats (total tracks, moods breakdown)
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.track import Track
from app.models.user import User
from app.schemas.track import ImportResponse, TrackListResponse, TrackResponse
from app.services.track_service import track_service

router = APIRouter()


# ── Import Listening History ───────────────────────────────────────────────────
@router.post("/import", response_model=ImportResponse)
async def import_tracks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch the user's recently played tracks from Spotify and save to database.

    - Fetches up to 50 most recent tracks
    - Skips tracks already in the database
    - Returns a summary of what was imported

    This endpoint is called:
    - Manually by the user from the dashboard
    - Automatically by the Celery sync job (Phase 7)
    """
    result = await track_service.import_recent_tracks(
        user=current_user,
        db=db,
    )
    return result


# ── List Tracks ────────────────────────────────────────────────────────────────
@router.get("/", response_model=TrackListResponse)
async def list_tracks(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Tracks per page"),
    mood: str | None = Query(default=None, description="Filter by mood category"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return a paginated list of the user's imported tracks.

    Optional filters:
    - mood: filter by mood category (e.g. "Romantic", "Energetic")

    Results are ordered by most recently played first.
    """
    tracks, total = await track_service.get_user_tracks(
        user_id=current_user.id,
        db=db,
        page=page,
        page_size=page_size,
        mood=mood,
    )

    return TrackListResponse(
        tracks=[TrackResponse.model_validate(t) for t in tracks],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── Track Stats ────────────────────────────────────────────────────────────────
@router.get("/stats")
async def get_track_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return summary statistics for the user's listening history.

    Returns:
    - Total number of tracks imported
    - Breakdown of tracks by mood category
    - Number of tracks not yet categorized
    """
    # Total tracks
    total_result = await db.execute(
        select(func.count()).select_from(Track).where(
            Track.user_id == current_user.id
        )
    )
    total = total_result.scalar_one()

    # Breakdown by mood
    mood_result = await db.execute(
        select(Track.mood_category, func.count(Track.id))
        .where(Track.user_id == current_user.id)
        .where(Track.mood_category.isnot(None))
        .group_by(Track.mood_category)
        .order_by(func.count(Track.id).desc())
    )
    mood_breakdown = {mood: count for mood, count in mood_result.all()}

    # Uncategorized tracks
    uncategorized_result = await db.execute(
        select(func.count()).select_from(Track).where(
            Track.user_id == current_user.id,
            Track.mood_category.is_(None),
        )
    )
    uncategorized = uncategorized_result.scalar_one()

    return {
        "total_tracks": total,
        "mood_breakdown": mood_breakdown,
        "uncategorized": uncategorized,
    }
