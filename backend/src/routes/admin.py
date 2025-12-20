"""
Admin Routes

Administrative endpoints for system management and manual job triggers.
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from src.middleware.auth import require_workspace, CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Model Update Models
# ============================================================================

class ModelUpdateResponse(BaseModel):
    id: str
    model_slug: str
    change_type: str
    old_value: Optional[dict]
    new_value: Optional[dict]
    status: str
    created_at: str
    reviewed_at: Optional[str]


class ModelUpdateAction(BaseModel):
    action: str  # "approve" or "dismiss"


# ============================================================================
# Scheduler Job Triggers
# ============================================================================

@router.post("/jobs/follow-up-emails")
async def trigger_follow_up_emails(
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Manually trigger the follow-up email job.
    Sends 7-day follow-up emails to users who haven't received them.
    """
    try:
        from src.services.scheduler_service import trigger_follow_up_emails as run_job
        await run_job()
        return {"success": True, "message": "Follow-up email job completed"}
    except Exception as e:
        logger.error(f"Follow-up email job failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job failed: {str(e)}"
        )


@router.post("/jobs/storage-cleanup")
async def trigger_storage_cleanup(
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Manually trigger the storage cleanup job.
    Removes PDFs older than 30 days.
    """
    try:
        from src.services.scheduler_service import trigger_storage_cleanup as run_job
        await run_job()
        return {"success": True, "message": "Storage cleanup job completed"}
    except Exception as e:
        logger.error(f"Storage cleanup job failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job failed: {str(e)}"
        )


@router.post("/jobs/quiz-cleanup")
async def trigger_quiz_cleanup(
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Manually trigger the expired quiz session cleanup job.
    Removes unpaid quiz sessions older than 7 days.
    """
    try:
        from src.services.scheduler_service import trigger_quiz_cleanup as run_job
        await run_job()
        return {"success": True, "message": "Quiz cleanup job completed"}
    except Exception as e:
        logger.error(f"Quiz cleanup job failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job failed: {str(e)}"
        )


@router.get("/jobs/status")
async def get_scheduler_status(
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Get the status of all scheduled jobs.
    """
    try:
        from src.services.scheduler_service import get_scheduler

        scheduler = get_scheduler()
        jobs = []

        for job in scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            })

        return {
            "running": scheduler.running,
            "jobs": jobs,
        }
    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )


# ============================================================================
# System Health
# ============================================================================

@router.get("/system/storage-stats")
async def get_storage_stats(
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Get storage usage statistics.
    """
    try:
        from src.config.supabase_client import get_async_supabase

        supabase = await get_async_supabase()

        # List files in storage
        result = supabase.storage.from_("reports").list("pdfs")

        total_files = len(result) if result else 0
        total_size = sum(f.get("metadata", {}).get("size", 0) for f in result) if result else 0

        return {
            "bucket": "reports",
            "total_files": total_files,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }
    except Exception as e:
        logger.error(f"Failed to get storage stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.get("/system/email-stats")
async def get_email_stats(
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Get email sending statistics.
    """
    try:
        from src.config.supabase_client import get_async_supabase
        from datetime import timedelta

        supabase = await get_async_supabase()

        # Count reports by follow-up status
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        # Reports completed in last 30 days
        completed_result = await supabase.table("reports").select(
            "id", count="exact"
        ).gte(
            "generation_completed_at", thirty_days_ago.isoformat()
        ).eq("status", "completed").execute()

        # Reports with follow-up sent
        followup_result = await supabase.table("reports").select(
            "id", count="exact"
        ).not_.is_("follow_up_sent_at", "null").execute()

        return {
            "reports_completed_30d": completed_result.count or 0,
            "follow_ups_sent": followup_result.count or 0,
        }
    except Exception as e:
        logger.error(f"Failed to get email stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


# ============================================================================
# Model Freshness Management
# ============================================================================

@router.get("/model-updates")
async def list_model_updates(
    status_filter: str = "pending",
    limit: int = 50,
    current_user: CurrentUser = Depends(require_workspace),
):
    """List model updates pending review."""
    from src.config.supabase_client import get_async_supabase

    supabase = await get_async_supabase()

    query = supabase.table("model_updates").select("*")

    if status_filter != "all":
        query = query.eq("status", status_filter)

    result = await query.order("created_at", desc=True).limit(limit).execute()

    return {
        "updates": result.data,
        "count": len(result.data),
    }


@router.post("/model-updates/{update_id}/approve")
async def approve_model_update(
    update_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """Approve a model update and apply it to knowledge base."""
    from src.config.supabase_client import get_async_supabase

    supabase = await get_async_supabase()

    # Get the update
    result = await supabase.table("model_updates").select("*").eq("id", update_id).single().execute()

    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Update not found")

    update = result.data

    if update["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Update already {update['status']}"
        )

    # Mark as approved
    await supabase.table("model_updates").update({
        "status": "approved",
        "reviewed_at": datetime.utcnow().isoformat(),
    }).eq("id", update_id).execute()

    # TODO: Apply the change to knowledge base JSON files
    # This would update backend/src/knowledge/vendors/ai_assistants.json

    return {
        "success": True,
        "message": f"Approved update for {update['model_slug']}",
        "update_id": update_id,
    }


@router.post("/model-updates/{update_id}/dismiss")
async def dismiss_model_update(
    update_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """Dismiss a model update without applying."""
    from src.config.supabase_client import get_async_supabase

    supabase = await get_async_supabase()

    result = await supabase.table("model_updates").select("*").eq("id", update_id).single().execute()

    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Update not found")

    if result.data["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Update already {result.data['status']}"
        )

    await supabase.table("model_updates").update({
        "status": "dismissed",
        "reviewed_at": datetime.utcnow().isoformat(),
    }).eq("id", update_id).execute()

    return {
        "success": True,
        "message": "Update dismissed",
        "update_id": update_id,
    }


@router.post("/jobs/model-freshness")
async def trigger_freshness_check(
    current_user: CurrentUser = Depends(require_workspace),
):
    """Manually trigger a model freshness check."""
    try:
        from src.jobs.model_freshness import run_model_freshness_job

        result = await run_model_freshness_job()

        return {
            "success": True,
            "result": result,
        }
    except Exception as e:
        logger.error(f"Model freshness job failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job failed: {str(e)}"
        )
