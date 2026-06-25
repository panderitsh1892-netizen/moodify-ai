"""
app/services/spotify.py
────────────────────────
Spotify Web API client.

This service handles ALL communication with Spotify's API:
- Building the OAuth authorization URL
- Exchanging the authorization code for tokens
- Refreshing expired access tokens
- Fetching user profile data

Design decision: We use httpx (async HTTP client) instead of the requests
library because our FastAPI app is async. Using synchronous requests inside
an async route would block the entire event loop — meaning no other requests
could be processed while we wait for Spotify to respond.
"""

from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx

from app.core.config import settings

# ── Spotify API URLs ───────────────────────────────────────────────────────────
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"


class SpotifyService:
    """
    Client for the Spotify Web API.

    Instantiated once per request (or once globally for background tasks).
    All methods are async.
    """

    def __init__(self):
        self.client_id = settings.SPOTIFY_CLIENT_ID
        self.client_secret = settings.SPOTIFY_CLIENT_SECRET
        self.redirect_uri = settings.SPOTIFY_REDIRECT_URI

    # ── OAuth Step 1: Build Authorization URL ─────────────────────────────────
    def get_auth_url(self, state: str) -> str:
        """
        Build the Spotify authorization URL that we redirect the user to.

        The `state` parameter is a random string we generate and store.
        When Spotify redirects back to us, it includes the same state.
        We verify it matches — this prevents CSRF attacks where a malicious
        site tricks a user into connecting someone else's Spotify account.

        Args:
            state: Random CSRF protection string

        Returns:
            Full Spotify authorization URL
        """
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": settings.SPOTIFY_SCOPES,
            "state": state,
            "show_dialog": "false",   # Don't ask for approval every time
        }
        return f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"

    # ── OAuth Step 2: Exchange Code for Tokens ────────────────────────────────
    async def exchange_code(self, code: str) -> dict:
        """
        Exchange the authorization code (from Spotify's callback) for tokens.

        Spotify's OAuth flow:
        1. We redirect user to Spotify → they log in and approve
        2. Spotify redirects to our callback URL with ?code=XXXX
        3. We POST that code to Spotify's token endpoint
        4. Spotify returns access_token + refresh_token

        The code can only be used ONCE and expires in 10 minutes.

        Args:
            code: Authorization code from Spotify callback

        Returns:
            Dict containing access_token, refresh_token, expires_in
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                SPOTIFY_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
                # Spotify requires client credentials as HTTP Basic Auth
                auth=(self.client_id, self.client_secret),
            )
            response.raise_for_status()
            return response.json()

    # ── Token Refresh ─────────────────────────────────────────────────────────
    async def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Get a new access token using the refresh token.

        Access tokens expire after 1 hour. Instead of asking the user to
        log in again, we silently exchange the refresh token for a new one.

        Args:
            refresh_token: The long-lived refresh token stored in our DB

        Returns:
            Dict containing new access_token and expires_in
            (Spotify may also return a new refresh_token — we handle that)
        """
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

    # ── User Profile ──────────────────────────────────────────────────────────
    async def get_current_user_profile(self, access_token: str) -> dict:
        """
        Fetch the authenticated user's Spotify profile.

        Returns fields like: id, email, display_name, images

        Args:
            access_token: Valid Spotify access token

        Returns:
            Spotify user profile dict
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SPOTIFY_API_BASE}/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()

    # ── Token Expiry Helper ───────────────────────────────────────────────────
    @staticmethod
    def calculate_token_expiry(expires_in: int) -> datetime:
        """
        Calculate the exact UTC datetime when an access token expires.

        Spotify returns `expires_in` as seconds (usually 3600 = 1 hour).
        We subtract 5 minutes as a safety buffer so we refresh slightly
        before expiry rather than right when it expires.

        Args:
            expires_in: Seconds until token expires (from Spotify response)

        Returns:
            UTC datetime of token expiry
        """
        buffer_seconds = 300  # 5 minute buffer
        return datetime.now(UTC) + timedelta(seconds=expires_in - buffer_seconds)

    # ── Token Validity Check ──────────────────────────────────────────────────
    @staticmethod
    def is_token_expired(token_expiry: datetime | None) -> bool:
        """
        Check if an access token has expired.

        Args:
            token_expiry: UTC datetime when the token expires

        Returns:
            True if expired (needs refresh), False if still valid
        """
        if token_expiry is None:
            return True
        return datetime.now(UTC) >= token_expiry


# ── Singleton Instance ─────────────────────────────────────────────────────────
# One instance shared across the app.
# Safe because SpotifyService holds no mutable per-request state.
spotify_service = SpotifyService()
