"""
app/services/spotify.py
────────────────────────
Spotify Web API client.
"""

from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx

from app.core.config import settings

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"


class SpotifyService:

    def __init__(self):
        self.client_id = settings.SPOTIFY_CLIENT_ID
        self.client_secret = settings.SPOTIFY_CLIENT_SECRET
        self.redirect_uri = settings.SPOTIFY_REDIRECT_URI

    def get_auth_url(self, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": settings.SPOTIFY_SCOPES,
            "state": state,
            "show_dialog": "false",
        }
        return f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                SPOTIFY_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
                auth=(self.client_id, self.client_secret),
            )
            response.raise_for_status()
            return response.json()

    async def refresh_access_token(self, refresh_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                SPOTIFY_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                auth=(self.client_id, self.client_secret),
            )
            response.raise_for_status()
            return response.json()

    async def get_current_user_profile(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SPOTIFY_API_BASE}/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()

    async def get_recently_played(
        self,
        access_token: str,
        limit: int = 50,
        after: int | None = None,
    ) -> dict:
        """Fetch the user's recently played tracks from Spotify."""
        params: dict = {"limit": limit}
        if after is not None:
            params["after"] = after

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SPOTIFY_API_BASE}/me/player/recently-played",
                headers={"Authorization": f"Bearer {access_token}"},
                params=params,
            )
            response.raise_for_status()
            return response.json()

    async def get_audio_features(
        self,
        access_token: str,
        track_ids: list[str],
    ) -> list[dict]:
        """
        Fetch audio features for multiple tracks in one API call.

        Spotify's audio-features endpoint accepts up to 100 track IDs
        at once, making it efficient for batch processing.

        Audio features include:
        - valence     : musical positivity (0.0 sad → 1.0 happy)
        - energy      : intensity (0.0 calm → 1.0 intense)
        - danceability: dance suitability (0.0 → 1.0)
        - tempo       : BPM
        - speechiness : spoken words ratio (0.0 music → 1.0 speech)
        - key         : musical key (0=C, 1=C#, ... 11=B)

        Args:
            access_token : Valid Spotify access token
            track_ids    : List of Spotify track IDs (max 100 per call)

        Returns:
            List of audio feature dicts (one per track)
        """
        if not track_ids:
            return []

        # Spotify allows max 100 IDs per request
        # We'll chunk them in the categorizer service
        ids_param = ",".join(track_ids[:100])

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SPOTIFY_API_BASE}/audio-features",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"ids": ids_param},
            )
            response.raise_for_status()
            data = response.json()
            # Filter out None values (Spotify returns null for some tracks)
            return [f for f in data.get("audio_features", []) if f is not None]

    async def get_valid_access_token(self, user) -> str:
        """Return a valid access token, refreshing if expired."""
        if self.is_token_expired(user.token_expiry):
            token_data = await self.refresh_access_token(user.refresh_token)
            user.access_token = token_data["access_token"]
            user.token_expiry = self.calculate_token_expiry(
                token_data["expires_in"]
            )
            if "refresh_token" in token_data:
                user.refresh_token = token_data["refresh_token"]
        return user.access_token

    @staticmethod
    def calculate_token_expiry(expires_in: int) -> datetime:
        buffer_seconds = 300
        return datetime.now(UTC) + timedelta(seconds=expires_in - buffer_seconds)

    @staticmethod
    def is_token_expired(token_expiry: datetime | None) -> bool:
        if token_expiry is None:
            return True
        return datetime.now(UTC) >= token_expiry


spotify_service = SpotifyService()
