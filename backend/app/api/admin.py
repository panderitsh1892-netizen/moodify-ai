"""
app/api/admin.py
─────────────────
Admin endpoints for manually triggering sync jobs.

These endpoints let you:
- Trigger a full sync for your own account immediately
- Check the status of background tasks
- Useful for testing without waiting 30 minutes

In production you'd protect these with an admin role check.
For now they're protected by normal JWT auth.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.tasks.sync import sync_all_users, sync_user

router = APIRouter()


@router.post("/sync/me")
async def trigger_my_sync(
    current_user: User = Depends(get_current_user),
):
    """
    Manually trigger a sync for the current user.

    Queues a Celery task that will:
    1. Import recent Spotify plays
    2. Categorize new tracks by mood
    3. Update Spotify playlists

    The task runs asynchronously — this endpoint returns immediately
    with a task ID. Use GET /api/admin/task/{task_id} to check status.
    """
    task = sync_user.delay(current_user.id)

    return {
        "message": f"Sync queued for user {current_user.id}",
        "task_id": task.id,
        "status": "queued",
        "check_status_at": f"/api/admin/task/{task.id}",
    }


@router.post("/sync/all")
async def trigger_all_sync(
    current_user: User = Depends(get_current_user),
):
    """
    Manually trigger sync for ALL active users.

    This is what Celery Beat calls automatically every 30 minutes.
    Calling it manually is useful for testing.
    """
    task = sync_all_users.delay()

    return {
        "message": "Full sync queued for all active users",
        "task_id": task.id,
        "status": "queued",
    }


@router.get("/task/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Check the status of a background task by its ID.

    Possible states:
    - PENDING  : Task is queued, not yet picked up by a worker
    - STARTED  : Worker is currently executing the task
    - SUCCESS  : Task completed successfully
    - FAILURE  : Task failed (check 'error' field)
    - RETRY    : Task failed and is being retried
    """
    from app.tasks.celery_app import celery_app

    task_result = celery_app.AsyncResult(task_id)

    response = {
        "task_id": task_id,
        "status": task_result.state,
    }

    if task_result.state == "SUCCESS":
        response["result"] = task_result.result
    elif task_result.state == "FAILURE":
        response["error"] = str(task_result.result)
    elif task_result.state == "PENDING":
        response["message"] = "Task is queued and waiting for a worker"

    return response
