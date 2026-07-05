"""
app/tasks/sync.py
──────────────────
Celery background tasks for automatic syncing.

Key design decision: Each task creates its own SQLAlchemy engine and
disposes it when done. This avoids asyncpg connection pool conflicts
that occur when Celery's prefork workers reuse processes with stale
async connections from previous event loops.
"""

import asyncio
import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
        asyncio.set_event_loop(None)


async def _sync_user_async(user_id: int) -> dict:
    """Core async sync logic for a single user."""

    # Import all models first so SQLAlchemy can resolve relationships
    import app.models.user      # noqa: F401
    import app.models.track     # noqa: F401
    import app.models.playlist  # noqa: F401

    import os
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.models.user import User
    from app.services.categorizer import mood_categorizer
    from app.services.playlist_service import playlist_service
    from app.services.track_service import track_service
    from sqlalchemy import select

    # Create a FRESH engine per task — avoids stale connection pool issues
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://moodify:moodify@postgres:5432/moodify"
    )
    engine = create_async_engine(database_url, pool_size=2, max_overflow=0)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    try:
        async with SessionLocal() as db:
            # Load user
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if user is None:
                logger.warning(f"User {user_id} not found, skipping sync")
                return {"status": "skipped", "reason": "user not found"}

            if not user.is_active:
                return {"status": "skipped", "reason": "user inactive"}

            logger.info(f"Starting sync for user {user_id} ({user.email})")

            try:
                # Step 1: Import recent tracks
                import_result = await track_service.import_recent_tracks(
                    user=user, db=db,
                )
                logger.info(f"User {user_id}: imported {import_result.new_tracks_saved} new tracks")

                # Step 2: Categorize uncategorized tracks
                categorize_result = await mood_categorizer.categorize_user_tracks(
                    user=user, db=db, only_uncategorized=True,
                )
                logger.info(f"User {user_id}: categorized {categorize_result['categorized']} tracks")

                # Step 3: Sync playlists only if there are new tracks
                if import_result.new_tracks_saved > 0 or categorize_result["categorized"] > 0:
                    playlist_result = await playlist_service.create_or_sync_all_playlists(
                        user=user, db=db,
                    )
                    logger.info(f"User {user_id}: {playlist_result['message']}")
                else:
                    playlist_result = {"message": "No new tracks, playlist sync skipped"}
                    logger.info(f"User {user_id}: no new tracks, skipping playlist sync")

                await db.commit()

                return {
                    "status": "success",
                    "user_id": user_id,
                    "import": {
                        "new_tracks": import_result.new_tracks_saved,
                        "duplicates_skipped": import_result.duplicates_skipped,
                    },
                    "categorization": {
                        "categorized": categorize_result["categorized"],
                        "by_mood": categorize_result.get("by_mood", {}),
                    },
                    "playlists": playlist_result.get("message", ""),
                }

            except Exception as e:
                await db.rollback()
                logger.error(f"Sync failed for user {user_id}: {e}")
                raise
    finally:
        # Always dispose the engine to release all connections
        await engine.dispose()


def _get_all_user_ids() -> list[int]:
    """Get all active user IDs using synchronous psycopg2 connection."""
    import os
    import psycopg2

    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://moodify:moodify@postgres:5432/moodify"
    )
    sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    conn = psycopg2.connect(sync_url)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE is_active = TRUE")
            return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


async def _sync_all_users_async() -> dict:
    """Load all active users and dispatch individual sync tasks."""
    user_ids = _get_all_user_ids()
    logger.info(f"Dispatching sync for {len(user_ids)} users")
    for user_id in user_ids:
        sync_user.delay(user_id)
    return {"status": "dispatched", "users_queued": len(user_ids)}


# ── Celery Tasks ───────────────────────────────────────────────────────────────

@celery_app.task(
    name="app.tasks.sync.sync_all_users",
    bind=True,
    max_retries=3,
)
def sync_all_users(self):
    """Scheduled task: sync all active users every 30 minutes."""
    try:
        logger.info("🔄 sync_all_users triggered by Celery Beat")
        return run_async(_sync_all_users_async())
    except Exception as exc:
        logger.error(f"sync_all_users failed: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(
    name="app.tasks.sync.sync_user",
    bind=True,
    max_retries=3,
)
def sync_user(self, user_id: int):
    """Sync a single user's listening history and playlists."""
    try:
        logger.info(f"🔄 sync_user triggered for user {user_id}")
        return run_async(_sync_user_async(user_id))
    except Exception as exc:
        logger.error(f"sync_user failed for user {user_id}: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))