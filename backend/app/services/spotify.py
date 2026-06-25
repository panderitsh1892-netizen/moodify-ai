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
        """
        Fetch the user's recently played tracks from Spotify.

        Args:
            access_token : Valid Spotify access token
            limit        : Number of tracks to fetch (max 50)
            after        : Unix timestamp in ms — fetch tracks played AFTER
                           this time. Used for incremental syncs.

        Returns:
            Spotify API response dict with "items" list of play events
        """
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

    async def get_valid_access_token(self, user) -> str:
        """
        Return a valid access token, refreshing if expired.

        Args:
            user: User ORM object

        Returns:
            Valid Spotify access token
        """
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