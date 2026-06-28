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
            "show_dialog": "true",
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
        """Fetch the user's recently played tracks."""
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

    async def create_playlist(
        self,
        access_token: str,
        spotify_user_id: str,
        name: str,
        description: str = "",
        public: bool = False,
    ) -> dict:
        """Create a new playlist in the user's Spotify account."""
        # POST /me/playlists is the new endpoint (Feb 2026 migration)
        # Old endpoint POST /users/{user_id}/playlists returns 403 in Dev mode
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SPOTIFY_API_BASE}/me/playlists",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "name": name,
                    "description": description,
                    "public": public,
                },
            )
            response.raise_for_status()
            return response.json()

    async def add_tracks_to_playlist(
        self,
        access_token: str,
        playlist_id: str,
        track_uris: list[str],
    ) -> dict:
        """Add tracks to an existing Spotify playlist."""
        if not track_uris:
            return {}

        last_response = {}
        chunk_size = 100
        for i in range(0, len(track_uris), chunk_size):
            chunk = track_uris[i : i + chunk_size]
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{SPOTIFY_API_BASE}/playlists/{playlist_id}/items",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                    json={"uris": chunk},
                )
                response.raise_for_status()
                last_response = response.json()

        return last_response

    async def get_playlist_tracks(
        self,
        access_token: str,
        playlist_id: str,
    ) -> list[str]:
        """Get all track IDs currently in a Spotify playlist."""
        track_ids = []
        url = f"{SPOTIFY_API_BASE}/playlists/{playlist_id}/items"
        params = {"fields": "items(track(id)),next", "limit": 100}

        async with httpx.AsyncClient() as client:
            while url:
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {access_token}"},
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

                for item in data.get("items", []):
                    track = item.get("track")
                    if track and track.get("id"):
                        track_ids.append(track["id"])

                url = data.get("next")
                params = {}

        return track_ids

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