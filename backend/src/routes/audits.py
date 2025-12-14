"""
Audit Routes

CRUD operations for audits (CRB analysis projects).
All routes require authentication and workspace context.
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse

from src.config.supabase_client import get_async_supabase
from src.middleware.auth import require_workspace, CurrentUser
from src.models.audit import (
    AuditCreate,
    AuditUpdate,
    AuditResponse,
    AuditListResponse,
    AuditWithClient,
    AUDIT_STATUSES,
    AUDIT_TIERS,
    ANALYSIS_PHASES,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=AuditListResponse)
async def list_audits(
    current_user: CurrentUser = Depends(require_workspace),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    client_id: Optional[str] = Query(default=None),
):
    """
    List all audits in the workspace.

    Supports pagination and filtering by status or client.
    """
    try:
        supabase = await get_async_supabase()

        # Build query
        query = supabase.table("audits").select(
            "*, clients(name, industry)", count="exact"
        ).eq("workspace_id", current_user.workspace_id)

        # Apply filters
        if status_filter:
            query = query.eq("status", status_filter)

        if client_id:
            query = query.eq("client_id", client_id)

        # Apply pagination and ordering
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

        result = await query.execute()

        # Map results with client info
        audits = []
        for audit_data in result.data:
            client_info = audit_data.pop("clients", None)
            audit = AuditResponse(**audit_data)
            audits.append(audit)

        return AuditListResponse(
            data=audits,
            total=result.count or len(audits)
        )

    except Exception as e:
        logger.error(f"List audits error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list audits"
        )


@router.post("", response_model=AuditResponse, status_code=status.HTTP_201_CREATED)
async def create_audit(
    request: AuditCreate,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Create a new audit.

    Requires a client_id. Creates intake_responses record automatically.
    """
    try:
        supabase = await get_async_supabase()

        # Verify client exists and belongs to workspace
        client_check = await supabase.table("clients").select("id, name").eq(
            "id", request.client_id
        ).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not client_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )

        # Create audit
        audit_data = {
            **request.model_dump(),
            "workspace_id": current_user.workspace_id,
            "status": "intake",
            "current_phase": "intake",
            "progress_percent": 0,
            "payment_status": "pending" if request.tier == "professional" else "paid",
        }

        audit_result = await supabase.table("audits").insert(audit_data).execute()

        if not audit_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create audit"
            )

        audit = audit_result.data[0]

        # Create empty intake_responses record
        await supabase.table("intake_responses").insert({
            "audit_id": audit["id"],
            "is_complete": False,
            "current_section": 1,
            "responses": {},
        }).execute()

        logger.info(f"Audit created: {audit['id']} for client {request.client_id} by {current_user.email}")

        return AuditResponse(**audit)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create audit error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create audit"
        )


@router.get("/statuses")
async def get_statuses():
    """
    Get list of audit statuses for dropdown.
    """
    return {"statuses": AUDIT_STATUSES}


@router.get("/tiers")
async def get_tiers():
    """
    Get list of audit tiers with pricing.
    """
    return {"tiers": AUDIT_TIERS}


@router.get("/phases")
async def get_phases():
    """
    Get list of analysis phases.
    """
    return {"phases": ANALYSIS_PHASES}


@router.get("/{audit_id}", response_model=AuditWithClient)
async def get_audit(
    audit_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Get a single audit by ID with client details.
    """
    try:
        supabase = await get_async_supabase()

        result = await supabase.table("audits").select(
            "*, clients(name, industry)"
        ).eq(
            "id", audit_id
        ).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found"
            )

        # Extract client info
        client_info = result.data.pop("clients", None)

        audit = AuditWithClient(
            **result.data,
            client_name=client_info.get("name") if client_info else None,
            client_industry=client_info.get("industry") if client_info else None,
        )

        return audit

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get audit error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit not found"
        )


@router.patch("/{audit_id}", response_model=AuditResponse)
async def update_audit(
    audit_id: str,
    request: AuditUpdate,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Update an audit.
    """
    try:
        supabase = await get_async_supabase()

        # Verify audit exists and belongs to workspace
        existing = await supabase.table("audits").select("id, status").eq(
            "id", audit_id
        ).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found"
            )

        # Update only provided fields
        update_data = request.model_dump(exclude_none=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        # Handle status transitions
        if "status" in update_data:
            new_status = update_data["status"]
            if new_status == "processing" and existing.data["status"] == "intake":
                update_data["started_at"] = datetime.utcnow().isoformat()
            elif new_status == "completed":
                update_data["completed_at"] = datetime.utcnow().isoformat()

        result = await supabase.table("audits").update(
            update_data
        ).eq("id", audit_id).execute()

        logger.info(f"Audit updated: {audit_id} by {current_user.email}")

        return AuditResponse(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update audit error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update audit"
        )


@router.delete("/{audit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audit(
    audit_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Delete an audit.

    Only allowed for audits in 'intake' status or failed audits.
    """
    try:
        supabase = await get_async_supabase()

        # Verify audit exists and check status
        existing = await supabase.table("audits").select("id, status").eq(
            "id", audit_id
        ).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found"
            )

        # Only allow deletion of intake or failed audits
        if existing.data["status"] not in ["intake", "failed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete audit that is processing or completed"
            )

        # Delete audit (cascades to findings, recommendations, etc.)
        await supabase.table("audits").delete().eq("id", audit_id).execute()

        logger.info(f"Audit deleted: {audit_id} by {current_user.email}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete audit error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete audit"
        )


@router.get("/{audit_id}/findings")
async def get_audit_findings(
    audit_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Get all findings for an audit.
    """
    try:
        supabase = await get_async_supabase()

        # Verify audit belongs to workspace
        audit_check = await supabase.table("audits").select("id").eq(
            "id", audit_id
        ).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not audit_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found"
            )

        # Get findings
        result = await supabase.table("findings").select("*").eq(
            "audit_id", audit_id
        ).order("priority").execute()

        return {"data": result.data, "total": len(result.data)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get findings error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get findings"
        )


@router.get("/{audit_id}/recommendations")
async def get_audit_recommendations(
    audit_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Get all recommendations for an audit.
    """
    try:
        supabase = await get_async_supabase()

        # Verify audit belongs to workspace
        audit_check = await supabase.table("audits").select("id").eq(
            "id", audit_id
        ).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not audit_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found"
            )

        # Get recommendations
        result = await supabase.table("recommendations").select("*").eq(
            "audit_id", audit_id
        ).order("priority").execute()

        return {"data": result.data, "total": len(result.data)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get recommendations error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recommendations"
        )


@router.get("/{audit_id}/reports")
async def get_audit_reports(
    audit_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Get all reports for an audit.
    """
    try:
        supabase = await get_async_supabase()

        # Verify audit belongs to workspace
        audit_check = await supabase.table("audits").select("id").eq(
            "id", audit_id
        ).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not audit_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found"
            )

        # Get reports
        result = await supabase.table("reports").select("*").eq(
            "audit_id", audit_id
        ).order("created_at", desc=True).execute()

        return {"data": result.data, "total": len(result.data)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get reports error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get reports"
        )


@router.get("/{audit_id}/activity")
async def get_audit_activity(
    audit_id: str,
    current_user: CurrentUser = Depends(require_workspace),
    limit: int = Query(default=50, ge=1, le=200),
):
    """
    Get activity log for an audit.
    """
    try:
        supabase = await get_async_supabase()

        # Verify audit belongs to workspace
        audit_check = await supabase.table("audits").select("id").eq(
            "id", audit_id
        ).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not audit_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found"
            )

        # Get activity log
        result = await supabase.table("audit_activity_log").select("*").eq(
            "audit_id", audit_id
        ).order("created_at", desc=True).limit(limit).execute()

        return {"data": result.data, "total": len(result.data)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get activity error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get activity log"
        )


@router.post("/{audit_id}/start-analysis")
async def start_analysis(
    audit_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Start the CRB analysis for an audit.

    Audit must be in 'processing' status with completed intake.
    """
    try:
        supabase = await get_async_supabase()

        # Verify audit exists and is ready
        audit_check = await supabase.table("audits").select(
            "id, status, current_phase"
        ).eq(
            "id", audit_id
        ).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not audit_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found"
            )

        if audit_check.data["status"] not in ["processing"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Audit is not ready for analysis (status: {audit_check.data['status']})"
            )

        # Log activity
        await supabase.table("audit_activity_log").insert({
            "audit_id": audit_id,
            "action": "analysis_started",
            "details": {"triggered_by": current_user.email},
            "performed_by": current_user.id,
        }).execute()

        return {
            "message": "Analysis started",
            "audit_id": audit_id,
            "stream_url": f"/api/audits/{audit_id}/stream",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Start analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start analysis"
        )


@router.get("/{audit_id}/stream")
async def stream_analysis(
    audit_id: str,
):
    """
    SSE endpoint for streaming analysis progress.

    Returns Server-Sent Events with progress updates.
    """
    from src.agents.crb_agent import start_analysis

    async def event_generator():
        try:
            async for event in start_analysis(audit_id):
                yield event
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {{'error': '{str(e)}'}}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
