"""
app/schemas/user.py
────────────────────
Pydantic schemas for User serialization.

Design decision: We have SEPARATE schemas for different purposes:

- UserBase       : shared fields
- UserCreate     : what we need to create a user (internal, not exposed via API)
- UserResponse   : what we return to the frontend (NEVER includes tokens)
- TokenResponse  : what we return after successful OAuth

Why separate? The User ORM model contains sensitive fields like access_token
and refresh_token. If we returned the model directly, we'd risk accidentally
exposing those tokens in API responses. Pydantic schemas act as a firewall —
only fields explicitly defined in the schema are ever serialized.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    display_name: str | None = None
    avatar_url: str | None = None


class UserCreate(UserBase):
    """Internal schema for creating a user. Never exposed via API."""
    spotify_id: str
    access_token: str
    refresh_token: str
    token_expiry: datetime | None = None


class UserUpdate(BaseModel):
    """Schema for updating user tokens after a refresh."""
    access_token: str
    refresh_token: str
    token_expiry: datetime | None = None


class UserResponse(UserBase):
    """
    Safe public schema — returned to the frontend.
    Notice: NO access_token, NO refresh_token, NO sensitive data.
    """
    id: int
    spotify_id: str
    is_active: bool
    created_at: datetime

    # from_attributes=True allows Pydantic to read from SQLAlchemy ORM objects
    # (previously called orm_mode=True in Pydantic v1)
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Returned to the frontend after successful OAuth login."""
    access_token: str        # Our JWT token (not Spotify's)
    token_type: str = "bearer"
    user: UserResponse
