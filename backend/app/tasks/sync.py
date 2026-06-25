"""
app/tasks/sync.py
─────────────────
Background sync tasks (placeholder).

This module is imported by celery_app.py via the `include` list.
It must exist now so Celery doesn't throw an import error on startup.

We'll implement the actual sync logic in Phase 7.
"""

from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.sync.sync_all_users")
def sync_all_users():
    """Placeholder: will sync listening history for all users."""
    print("🔄 sync_all_users task triggered (not yet implemented)")
    return {"status": "placeholder"}


@celery_app.task(name="app.tasks.sync.sync_user")
def sync_user(user_id: int):
    """Placeholder: will sync listening history for a single user."""
    print(f"🔄 sync_user task triggered for user {user_id} (not yet implemented)")
    return {"status": "placeholder", "user_id": user_id}
