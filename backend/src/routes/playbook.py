"""
Playbook Routes

Endpoints for tracking playbook progress and ROI scenarios.
"""

import logging
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.config.supabase_client import get_async_supabase

logger = logging.getLogger(__name__)


async def _validate_report_belongs_to_paid_session(report_id: str) -> None:
    """
    Verify a report exists and belongs to a paid quiz session.
    Raises HTTPException if not found or not paid.
    """
    supabase = await get_async_supabase()

    # Look up the report to get its quiz_session_id
    report_result = await supabase.table("reports").select(
        "id, quiz_session_id"
    ).eq("id", report_id).single().execute()

    if not report_result.data:
        logger.warning(f"Playbook endpoint called with invalid report_id={report_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    quiz_session_id = report_result.data.get("quiz_session_id")
    if quiz_session_id:
        session_result = await supabase.table("quiz_sessions").select(
            "id, status"
        ).eq("id", quiz_session_id).single().execute()

        if not session_result.data:
            logger.warning(
                f"Playbook endpoint: report {report_id} references missing session {quiz_session_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated session not found"
            )

        paid_statuses = [
            "paid", "workshop_started", "workshop_complete",
            "generating", "report_generating", "report_delivered",
            "completed", "qa_pending", "released",
        ]
        if session_result.data.get("status") not in paid_statuses:
            logger.warning(
                f"Playbook endpoint called with unpaid session status={session_result.data.get('status')} "
                f"for report_id={report_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session must be paid to access playbook data"
            )

router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================

class TaskCompletionRequest(BaseModel):
    """Request to mark a task as complete/incomplete."""
    playbook_id: str
    task_id: str
    completed: bool


class TaskCompletionResponse(BaseModel):
    """Response after updating task completion."""
    success: bool
    task_id: str
    completed: bool
    completed_at: Optional[datetime] = None


class PlaybookProgressResponse(BaseModel):
    """Response with playbook progress summary."""
    report_id: str
    playbook_id: str
    completed_tasks: List[str]
    total_completed: int


class ROIScenarioRequest(BaseModel):
    """Request to save an ROI scenario."""
    name: str
    inputs: dict = Field(..., description="ROI calculator inputs")
    results: dict = Field(..., description="Calculated results")


class ROIScenarioResponse(BaseModel):
    """Response with saved ROI scenario."""
    id: str
    name: str
    inputs: dict
    results: dict
    created_at: datetime


# ============================================================================
# Playbook Progress Endpoints
# ============================================================================

@router.post("/progress", response_model=TaskCompletionResponse)
async def save_task_completion(
    report_id: str,
    request: TaskCompletionRequest,
):
    """
    Save task completion status for a playbook task.

    This endpoint tracks user progress through implementation playbooks.
    """
    # Validate report belongs to a paid session
    await _validate_report_belongs_to_paid_session(report_id)

    supabase = await get_async_supabase()

    try:
        # Check if record exists
        existing = await supabase.table("playbook_progress").select("*").eq(
            "report_id", report_id
        ).eq(
            "playbook_id", request.playbook_id
        ).eq(
            "task_id", request.task_id
        ).execute()

        completed_at = datetime.utcnow().isoformat() if request.completed else None

        if existing.data:
            # Update existing record
            await supabase.table("playbook_progress").update({
                "completed": request.completed,
                "completed_at": completed_at,
            }).eq("id", existing.data[0]["id"]).execute()
        else:
            # Insert new record
            await supabase.table("playbook_progress").insert({
                "report_id": report_id,
                "playbook_id": request.playbook_id,
                "task_id": request.task_id,
                "completed": request.completed,
                "completed_at": completed_at,
            }).execute()

        return TaskCompletionResponse(
            success=True,
            task_id=request.task_id,
            completed=request.completed,
            completed_at=datetime.fromisoformat(completed_at) if completed_at else None,
        )

    except Exception as e:
        logger.error(f"Failed to save task completion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save task completion")


@router.get("/progress/{report_id}", response_model=List[PlaybookProgressResponse])
async def get_playbook_progress(report_id: str):
    """
    Get all playbook progress for a report.

    Returns completed tasks grouped by playbook.
    """
    # Handle sample report - return empty progress (demo mode)
    if report_id == "sample":
        return []

    # Validate report belongs to a paid session
    await _validate_report_belongs_to_paid_session(report_id)

    supabase = await get_async_supabase()

    try:
        result = await supabase.table("playbook_progress").select("*").eq(
            "report_id", report_id
        ).eq("completed", True).execute()

        # Group by playbook
        progress_by_playbook: dict[str, List[str]] = {}
        for record in result.data:
            playbook_id = record["playbook_id"]
            if playbook_id not in progress_by_playbook:
                progress_by_playbook[playbook_id] = []
            progress_by_playbook[playbook_id].append(record["task_id"])

        # Build response
        responses = []
        for playbook_id, task_ids in progress_by_playbook.items():
            responses.append(PlaybookProgressResponse(
                report_id=report_id,
                playbook_id=playbook_id,
                completed_tasks=task_ids,
                total_completed=len(task_ids),
            ))

        return responses

    except Exception as e:
        logger.error(f"Failed to get playbook progress: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get playbook progress")


# ============================================================================
# ROI Scenario Endpoints
# ============================================================================

@router.post("/scenarios", response_model=ROIScenarioResponse)
async def save_roi_scenario(
    report_id: str,
    request: ROIScenarioRequest,
):
    """
    Save an ROI scenario for comparison.

    Allows users to save different what-if scenarios from the ROI calculator.
    """
    # Validate report belongs to a paid session
    await _validate_report_belongs_to_paid_session(report_id)

    supabase = await get_async_supabase()

    try:
        result = await supabase.table("roi_scenarios").insert({
            "report_id": report_id,
            "name": request.name,
            "inputs": request.inputs,
            "results": request.results,
        }).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to save scenario")

        record = result.data[0]
        return ROIScenarioResponse(
            id=record["id"],
            name=record["name"],
            inputs=record["inputs"],
            results=record["results"],
            created_at=datetime.fromisoformat(record["created_at"].replace("Z", "+00:00")),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save ROI scenario: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save ROI scenario")


@router.get("/scenarios/{report_id}", response_model=List[ROIScenarioResponse])
async def list_roi_scenarios(report_id: str):
    """
    List all saved ROI scenarios for a report.
    """
    # Validate report belongs to a paid session
    await _validate_report_belongs_to_paid_session(report_id)

    supabase = await get_async_supabase()

    try:
        result = await supabase.table("roi_scenarios").select("*").eq(
            "report_id", report_id
        ).order("created_at", desc=True).execute()

        scenarios = []
        for record in result.data:
            scenarios.append(ROIScenarioResponse(
                id=record["id"],
                name=record["name"],
                inputs=record["inputs"],
                results=record["results"],
                created_at=datetime.fromisoformat(record["created_at"].replace("Z", "+00:00")),
            ))

        return scenarios

    except Exception as e:
        logger.error(f"Failed to list ROI scenarios: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list ROI scenarios")


@router.delete("/scenarios/{scenario_id}")
async def delete_roi_scenario(scenario_id: str):
    """
    Delete a saved ROI scenario.
    """
    supabase = await get_async_supabase()

    try:
        await supabase.table("roi_scenarios").delete().eq(
            "id", scenario_id
        ).execute()

        return {"success": True, "deleted_id": scenario_id}

    except Exception as e:
        logger.error(f"Failed to delete ROI scenario: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete ROI scenario")
