"""
app/core/database.py
────────────────────
Async database engine and session management.

Design decision: We use SQLAlchemy's async engine so that database queries
don't block FastAPI's event loop. Every query is awaited, meaning the server
can handle other requests while waiting for Postgres to respond.

The `get_db` dependency is injected into FastAPI route handlers via
`Depends(get_db)`. FastAPI calls it before the route runs and ensures the
session is closed after the response is sent, even if an exception occurs.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ── Engine ─────────────────────────────────────────────────────────────────────
# The engine manages the connection pool. `echo=True` logs all SQL statements
# in development — very useful for debugging, must be False in production.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    # Pool settings: keep up to 10 connections open, allow 20 overflow.
    pool_size=10,
    max_overflow=20,
    # Recycle connections every 30 minutes to avoid stale connection errors.
    pool_recycle=1800,
)

# ── Session Factory ────────────────────────────────────────────────────────────
# async_sessionmaker creates new AsyncSession objects on demand.
# expire_on_commit=False: keeps ORM objects usable after commit without
# re-querying the database. Important for returning data in API responses.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Base Model ─────────────────────────────────────────────────────────────────
# All SQLAlchemy ORM models will inherit from this class.
# Declaring it here (rather than in models/) avoids circular imports.
class Base(DeclarativeBase):
    pass


# ── FastAPI Dependency ─────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async database session for use in FastAPI route handlers.

    Usage in a route:
        @router.get("/tracks")
        async def get_tracks(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Track))
            ...

    The `async with` block guarantees the session is closed after the
    request completes, releasing the connection back to the pool.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
