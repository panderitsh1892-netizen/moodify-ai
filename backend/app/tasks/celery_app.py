"""
app/tasks/celery_app.py
───────────────────────
Celery application instance.

Design decision: We create the Celery app here, separate from FastAPI's
main.py. This matters because Celery workers run as a completely separate
process — they don't import or start FastAPI. Having a dedicated module
means both the FastAPI app and Celery workers can import this without
pulling in each other's dependencies.

Celery Beat (the scheduler) reads the `beat_schedule` to know which tasks
to run automatically and how often. We'll add the actual sync task in Phase 7.
"""

from celery import Celery

from app.core.config import settings

# ── Celery App Instance ─────────────────────────────────────────────────────────
celery_app = Celery(
    "moodify",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    # Where Celery looks for task definitions.
    # We'll add task modules here as we build them.
    include=["app.tasks.sync"],
)

# ── Celery Configuration ────────────────────────────────────────────────────────
celery_app.conf.update(
    # Serialize tasks as JSON (not pickle — pickle has security risks).
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Timezone for Celery Beat schedules.
    timezone="UTC",
    enable_utc=True,
    # Task result expiry: delete results from Redis after 1 hour.
    result_expires=3600,
    # Retry failed tasks up to 3 times with exponential backoff.
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# ── Periodic Task Schedule ─────────────────────────────────────────────────────
# Celery Beat will trigger these tasks automatically.
# We'll populate this in Phase 7 when we build the sync job.
celery_app.conf.beat_schedule = {
    # Example (Phase 7):
    # "sync-all-users-every-30-min": {
    #     "task": "app.tasks.sync.sync_all_users",
    #     "schedule": settings.SYNC_INTERVAL_SECONDS,
    # },
}
