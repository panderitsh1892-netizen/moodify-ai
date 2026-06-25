"""
app/services/track_service.py
──────────────────────────────
Business logic for importing and managing tracks.

This service sits between the API router and the database.
It handles:
- Parsing Spotify's API response into our Track model format
- Deduplication (skip tracks we already have)
- Bulk database inserts for performance

Design decision: We use INSERT ... ON CONFLICT DO NOTHING for deduplication.
This is more efficient than SELECT first, then INSERT — it's a single database
round-trip instead of two.
"""

from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.track import Track
from app.models.user import User
from app.schemas.track import ImportResponse
from app.services.spotify import spotify_service


class TrackService:
    """Handles all track import and retrieval logic."""

    async def import_recent_tracks(
        self,
        user: User,
        db: AsyncSession,
        after_timestamp: int | None = None,
    ) -> ImportResponse:
        """
        Fetch recently played tracks from Spotify and save new ones to DB.

        Flow:
        1. Get a valid (non-expired) Spotify access token
        2. Call Spotify's recently-played endpoint
        3. Parse each play event into a Track row
        4. Bulk insert — skip duplicates via ON CONFLICT DO NOTHING
        5. Return a summary of what was imported

        Args:
            user            : The authenticated User ORM object
            db              : Async database session
            after_timestamp : Unix ms timestamp — only fetch tracks after this
                              (used for incremental syncs in Phase 7)

        Returns:
            ImportResponse with counts of fetched/saved/skipped tracks
        """
        # Step 1: Get valid token (auto-refreshes if expired)
        access_token = await spotify_service.get_valid_access_token(user)

        # Save token updates if refresh happened
        await db.flush()

        # Step 2: Fetch from Spotify
        response = await spotify_service.get_recently_played(
            access_token=access_token,
            limit=50,
            after=after_timestamp,
        )

        items = response.get("items", [])
        total_fetched = len(items)

        if total_fetched == 0:
            return ImportResponse(
                message="No new tracks found",
                total_fetched=0,
                new_tracks_saved=0,
                duplicates_skipped=0,
            )

        # Step 3: Parse Spotify response into row dicts
        track_rows = []
        for item in items:
            track_data = item.get("track", {})
            played_at_str = item.get("played_at", "")

            # Skip items with missing essential data
            if not track_data or not played_at_str:
                continue

            # Parse played_at from ISO 8601 string to datetime
            # Spotify format: "2024-01-15T14:30:00.000Z"
            played_at = datetime.fromisoformat(
                played_at_str.replace("Z", "+00:00")
            )

            # Extract artist names (a track can have multiple artists)
            artists = track_data.get("artists", [])
            artist_names = ", ".join(a.get("name", "") for a in artists)

            # Extract album art (Spotify returns multiple sizes — take the first)
            images = track_data.get("album", {}).get("images", [])
            album_art_url = images[0]["url"] if images else None

            track_rows.append({
                "user_id": user.id,
                "spotify_track_id": track_data.get("id", ""),
                "title": track_data.get("name", "Unknown"),
                "artist": artist_names or "Unknown Artist",
                "album": track_data.get("album", {}).get("name"),
                "album_art_url": album_art_url,
                "duration_ms": track_data.get("duration_ms"),
                "played_at": played_at,
                # Audio features and mood filled in Phase 5
                "valence": None,
                "energy": None,
                "tempo": None,
                "danceability": None,
                "speechiness": None,
                "track_key": None,
                "mood_category": None,
            })

        if not track_rows:
            return ImportResponse(
                message="No valid tracks to import",
                total_fetched=total_fetched,
                new_tracks_saved=0,
                duplicates_skipped=total_fetched,
            )

        # Step 4: Bulk insert with deduplication
        # ON CONFLICT DO NOTHING: if a row with the same
        # (user_id, spotify_track_id, played_at) already exists, skip it.
        # This is safe to run multiple times — idempotent.
        stmt = pg_insert(Track).values(track_rows)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=None,
            constraint="uq_user_track_played_at",
        )

        result = await db.execute(stmt)

        # rowcount tells us how many rows were actually inserted
        new_tracks_saved = result.rowcount
        duplicates_skipped = total_fetched - new_tracks_saved

        return ImportResponse(
            message=f"Import complete. {new_tracks_saved} new tracks saved.",
            total_fetched=total_fetched,
            new_tracks_saved=new_tracks_saved,
            duplicates_skipped=duplicates_skipped,
        )

    async def get_user_tracks(
        self,
        user_id: int,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        mood: str | None = None,
    ) -> tuple[list[Track], int]:
        """
        Retrieve a paginated list of tracks for a user.

        Args:
            user_id   : The user's internal ID
            db        : Async database session
            page      : Page number (1-based)
            page_size : Number of tracks per page
            mood      : Optional mood filter (e.g. "Romantic")

        Returns:
            Tuple of (list of Track objects, total count)
        """
        # Base query
        query = select(Track).where(Track.user_id == user_id)
        count_query = select(func.count()).select_from(Track).where(
            Track.user_id == user_id
        )

        # Optional mood filter
        if mood:
            query = query.where(Track.mood_category == mood)
            count_query = count_query.where(Track.mood_category == mood)

        # Order by most recently played first
        query = query.order_by(Track.played_at.desc())

        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute both queries
        result = await db.execute(query)
        tracks = result.scalars().all()

        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        return list(tracks), total


# Singleton instance
track_service = TrackService()
