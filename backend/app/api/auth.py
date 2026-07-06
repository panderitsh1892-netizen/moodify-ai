"""
app/api/auth.py
────────────────
Spotify OAuth authentication endpoints.

Endpoints:
    GET  /api/auth/login      → Redirect user to Spotify login
    GET  /api/auth/callback   → Handle Spotify's redirect back to us
    GET  /api/auth/me         → Return current logged-in user
    POST /api/auth/refresh    → Refresh expired Spotify token
    POST /api/auth/logout     → Logout (client discards JWT)
"""

import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, get_current_user
from app.models.user import User
from app.schemas.user import TokenResponse, UserResponse
from app.services.spotify import spotify_service

router = APIRouter()


# ── Step 1: Login ──────────────────────────────────────────────────────────────
@router.get("/login")
async def spotify_login():
    """
    Redirect the user to Spotify's authorization page.

    We generate a random `state` string for CSRF protection.
    In production, we'd store this in Redis and verify it in the callback.
    For now, we include it in the redirect and verify it's present.
    """
    # Generate a cryptographically secure random state string
    state = secrets.token_urlsafe(16)

    # Build the Spotify auth URL with all required parameters
    auth_url = spotify_service.get_auth_url(state=state)

    # Redirect the user's browser to Spotify's login page
    return RedirectResponse(url=auth_url)


# ── Step 2: Callback ───────────────────────────────────────────────────────────
@router.get("/callback", response_model=TokenResponse)
async def spotify_callback(
    code: str = Query(..., description="Authorization code from Spotify"),
    state: str = Query(..., description="CSRF state parameter"),
    error: str | None = Query(None, description="Error from Spotify if user denied"),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Spotify's redirect after user authorization.

    Spotify redirects to this URL with either:
    - ?code=XXXX&state=YYYY  (success)
    - ?error=access_denied   (user denied access)

    On success:
    1. Exchange the code for Spotify tokens
    2. Fetch the user's Spotify profile
    3. Create or update the user in our database
    4. Issue our own JWT token
    5. Return JWT + user data to the frontend
    """
    # Handle user denying access
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Spotify authorization denied: {error}",
        )

    # Exchange authorization code for Spotify tokens
    try:
        token_data = await spotify_service.exchange_code(code)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange code with Spotify: {str(e)}",
        )

    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]
    expires_in = token_data["expires_in"]

    # Calculate when this access token expires
    token_expiry = spotify_service.calculate_token_expiry(expires_in)

    # Fetch user's Spotify profile using the new access token
    try:
        profile = await spotify_service.get_current_user_profile(access_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch Spotify profile: {str(e)}",
        )

    spotify_id = profile["id"]
    email = profile.get("email", "")
    display_name = profile.get("display_name", "")
    avatar_url = (
        profile["images"][0]["url"]
        if profile.get("images")
        else None
    )

    # Check if this Spotify user already has an account in our database
    result = await db.execute(
        select(User).where(User.spotify_id == spotify_id)
    )
    user = result.scalar_one_or_none()

    if user:
        # Existing user — update their tokens (tokens change on every login)
        user.access_token = access_token
        user.refresh_token = refresh_token
        user.token_expiry = token_expiry
        user.display_name = display_name
        user.avatar_url = avatar_url
    else:
        # New user — create their account
        user = User(
            spotify_id=spotify_id,
            email=email,
            display_name=display_name,
            avatar_url=avatar_url,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=token_expiry,
        )
        db.add(user)

    # Save to database
    await db.flush()   # Assigns user.id without committing yet
    await db.refresh(user)  # Reload to get server-generated values

    # Issue OUR JWT token (this is what the frontend will use)
    our_jwt = create_access_token(user_id=user.id)

    # Redirect to frontend with token in URL params
    # Frontend extracts token from URL and stores in localStorage
    import json
    from fastapi.responses import RedirectResponse
    from urllib.parse import quote

    user_data = UserResponse.model_validate(user).model_dump()
    user_data["created_at"] = user_data["created_at"].isoformat()
    user_json = quote(json.dumps(user_data))

    frontend_url = f"http://127.0.0.1:3000/?token={our_jwt}&user={user_json}"
    return RedirectResponse(url=frontend_url)


# ── Get Current User ───────────────────────────────────────────────────────────
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Return the currently authenticated user's profile.

    Protected endpoint — requires valid JWT in Authorization header.
    The `get_current_user` dependency handles token verification.
    """
    return UserResponse.model_validate(current_user)


# ── Refresh Spotify Token ──────────────────────────────────────────────────────
@router.post("/refresh")
async def refresh_spotify_token(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh the user's Spotify access token.

    Called automatically by the frontend or background tasks when
    the stored Spotify token has expired.
    """
    try:
        token_data = await spotify_service.refresh_access_token(
            current_user.refresh_token
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to refresh Spotify token: {str(e)}",
        )

    # Update tokens in database
    current_user.access_token = token_data["access_token"]
    current_user.token_expiry = spotify_service.calculate_token_expiry(
        token_data["expires_in"]
    )

    # Spotify sometimes issues a new refresh token — update if so
    if "refresh_token" in token_data:
        current_user.refresh_token = token_data["refresh_token"]

    return {"message": "Token refreshed successfully"}


# ── Logout ─────────────────────────────────────────────────────────────────────
@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout the current user.

    Since JWTs are stateless, true server-side invalidation would require
    a token blacklist in Redis. For now, we instruct the client to discard
    the token. We'll add Redis blacklisting in Phase 7.
    """
    return {
        "message": "Logged out successfully. Please discard your token.",
        "user_id": current_user.id,
    }