"""
app/core/security.py
─────────────────────
JWT token utilities and FastAPI auth dependency.

How authentication works in Moodify AI:

1. User completes Spotify OAuth → we get their Spotify tokens
2. We create OUR OWN JWT token (separate from Spotify's)
3. Frontend stores our JWT and sends it in every request header:
       Authorization: Bearer <our_jwt_token>
4. Our `get_current_user` dependency decodes the JWT and loads the user

Why do we create our own JWT instead of using Spotify's access token directly?
- Spotify tokens expire in 1 hour and change on every refresh
- Our JWT is stable and only contains a user ID
- We control expiry, payload, and signing
- Decouples our auth from Spotify's token lifecycle
"""

from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

# ── JWT Config ─────────────────────────────────────────────────────────────────
ALGORITHM = "HS256"

# HTTPBearer extracts the token from the Authorization: Bearer <token> header
security_scheme = HTTPBearer()


# ── Token Creation ─────────────────────────────────────────────────────────────
def create_access_token(user_id: int) -> str:
    """
    Create a signed JWT token containing the user's ID.

    The token payload (called "claims") contains:
    - sub: subject (the user's ID as a string)
    - exp: expiry timestamp
    - iat: issued-at timestamp
    """
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),   # Subject: who this token belongs to
        "exp": expire,          # Expiry: when this token stops working
        "iat": now,             # Issued at: when this token was created
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int:
    """
    Decode and verify a JWT token. Returns the user ID.
    Raises HTTPException if the token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str | None = payload.get("sub")

        if user_id_str is None:
            raise credentials_exception

        return int(user_id_str)

    except JWTError:
        raise credentials_exception


# ── FastAPI Dependency ─────────────────────────────────────────────────────────
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency that:
    1. Extracts the JWT from the Authorization header
    2. Decodes it to get the user ID
    3. Loads and returns the User from the database

    Usage in a protected route:
        @router.get("/me")
        async def get_me(current_user: User = Depends(get_current_user)):
            return current_user
    """
    token = credentials.credentials
    user_id = decode_access_token(token)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    return user
