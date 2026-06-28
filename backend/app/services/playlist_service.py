"""
app/services/playlist_service.py
──────────────────────────────────
Business logic for creating and syncing Spotify playlists.

This is the service that delivers Moodify AI's core promise:
"listen to music → playlists appear in Spotify automatically."

Flow per mood:
1. Check if playlist already exists in our DB
2. If not → create it in Spotify → save to DB
3. If yes → load existing playlist
4. Get tracks for this mood from DB
5. Check which tracks are already in the Spotify playlist
6. Add only the new ones → update track count in DB
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.playlist import Playlist
from app.models.track import Track
from app.models.user import User
from app.services.categorizer import Mood
from app.services.spotify import spotify_service

# ── Playlist Names Per Mood ────────────────────────────────────────────────────
MOOD_PLAYLIST_NAMES = {
    Mood.ROMANTIC:    "Romantic Vibes 🌹",
    Mood.HAPPY:       "Happy Vibes ⭐",
    Mood.ENERGETIC:   "Energetic Boost ⚡",
    Mood.MELANCHOLIC: "Melancholic Feels 🌧️",
    Mood.ANGRY:       "Angry Mode 🔥",
    Mood.CHILL:       "Chill Zone 😌",
}

MOOD_DESCRIPTIONS = {
    Mood.ROMANTIC:    "Love songs and soft ballads curated by Moodify AI 🌹",
    Mood.HAPPY:       "Upbeat feel-good tracks curated by Moodify AI ⭐",
    Mood.ENERGETIC:   "High energy workout and hype music by Moodify AI ⚡",
    Mood.MELANCHOLIC: "Sad and introspective music curated by Moodify AI 🌧️",
    Mood.ANGRY:       "Intense and aggressive tracks curated by Moodify AI 🔥",
    Mood.CHILL:       "Relaxed background music curated by Moodify AI 😌",
}


class PlaylistService:
    """Handles creation and syncing of Spotify mood playlists."""

    async def create_or_sync_all_playlists(
        self,
        user: User,
        db: AsyncSession,
    ) -> dict:
        """
        Create or update all mood playlists for a user.

        For each mood that has at least one track:
        - Creates the playlist in Spotify if it doesn't exist yet
        - Adds any new tracks not already in the playlist

        Args:
            user : User ORM object
            db   : Async database session

        Returns:
            Summary dict with counts of created/updated playlists
        """
        # Get valid Spotify token
        access_token = await spotify_service.get_valid_access_token(user)
        await db.flush()

        playlists_created = 0
        playlists_updated = 0
        total_tracks_added = 0
        result_playlists = []

        # Process each mood category
        for mood in Mood.ALL:
            playlist_name = MOOD_PLAYLIST_NAMES[mood]
            description = MOOD_DESCRIPTIONS[mood]

            # Get all tracks for this mood from our DB
            tracks_result = await db.execute(
                select(Track).where(
                    Track.user_id == user.id,
                    Track.mood_category == mood,
                )
            )
            mood_tracks = tracks_result.scalars().all()

            # Skip moods with no tracks
            if not mood_tracks:
                continue

            # Check if we already have a playlist for this mood
            playlist_result = await db.execute(
                select(Playlist).where(
                    Playlist.user_id == user.id,
                    Playlist.mood_category == mood,
                )
            )
            playlist = playlist_result.scalar_one_or_none()

            if playlist is None:
                # ── Create new playlist in Spotify ────────────────────────────
                spotify_playlist = await spotify_service.create_playlist(
                    access_token=access_token,
                    spotify_user_id=user.spotify_id,
                    name=playlist_name,
                    description=description,
                    public=False,
                )

                spotify_playlist_id = spotify_playlist["id"]
                spotify_url = spotify_playlist.get(
                    "external_urls", {}
                ).get("spotify", "")

                # Save playlist to our DB
                playlist = Playlist(
                    user_id=user.id,
                    spotify_playlist_id=spotify_playlist_id,
                    name=playlist_name,
                    mood_category=mood,
                    spotify_url=spotify_url,
                    track_count=0,
                )
                db.add(playlist)
                await db.flush()  # Get playlist.id assigned
                playlists_created += 1

                # Add all tracks to the new playlist
                tracks_to_add = mood_tracks
            else:
                # ── Update existing playlist ──────────────────────────────────
                # Get tracks already in the Spotify playlist
                existing_track_ids = await spotify_service.get_playlist_tracks(
                    access_token=access_token,
                    playlist_id=playlist.spotify_playlist_id,
                )

                # Only add tracks not already in the playlist
                existing_set = set(existing_track_ids)
                tracks_to_add = [
                    t for t in mood_tracks
                    if t.spotify_track_id not in existing_set
                ]
                playlists_updated += 1

            # ── Add tracks to Spotify playlist ────────────────────────────────
            if tracks_to_add:
                # Convert track IDs to Spotify URIs
                # Format: spotify:track:4iV5W9uYEdYUVa79Axb7Rh
                track_uris = [
                    f"spotify:track:{t.spotify_track_id}"
                    for t in tracks_to_add
                ]

                await spotify_service.add_tracks_to_playlist(
                    access_token=access_token,
                    playlist_id=playlist.spotify_playlist_id,
                    track_uris=track_uris,
                )

                total_tracks_added += len(tracks_to_add)

            # Update our DB record
            playlist.track_count = len(mood_tracks)
            playlist.last_synced_at = datetime.now(UTC)
            result_playlists.append(playlist)

        await db.flush()

        return {
            "message": f"Sync complete. {playlists_created} created, {playlists_updated} updated.",
            "playlists_created": playlists_created,
            "playlists_updated": playlists_updated,
            "total_tracks_added": total_tracks_added,
            "playlists": result_playlists,
        }

    async def get_user_playlists(
        self,
        user_id: int,
        db: AsyncSession,
    ) -> tuple[list[Playlist], int]:
        """
        Get all mood playlists for a user from our database.

        Returns:
            Tuple of (list of Playlist objects, total count)
        """
        result = await db.execute(
            select(Playlist)
            .where(Playlist.user_id == user_id)
            .order_by(Playlist.created_at.desc())
        )
        playlists = result.scalars().all()
        return list(playlists), len(playlists)


playlist_service = PlaylistService()
