"""
app/tasks/celery_app.py
───────────────────────
Celery application instance and beat schedule.
"""

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "moodify",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.sync"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Worker settings
    worker_prefetch_multiplier=1,   # Process one task at a time per worker
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (prevents memory leaks)
)

# ── Periodic Task Schedule (Celery Beat) ───────────────────────────────────────
celery_app.conf.beat_schedule = {
    "sync-all-users-every-30-min": {
        "task": "app.tasks.sync.sync_all_users",
        # Run every 30 minutes
        "schedule": settings.SYNC_INTERVAL_SECONDS,
        "options": {
            # Route to the default queue
            "queue": "celery",
        },
    },
}
