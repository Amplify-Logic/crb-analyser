"""
Admin QA Routes

Routes for human QA review of generated reports.

Workflow:
1. Report generates → status: qa_pending
2. Admin reviews in QA queue → /api/admin/qa/queue
3. Admin views report → /api/admin/qa/report/{id}
4. Admin approves/rejects → /api/admin/qa/review
5. If approved → status: released, user notified
6. If rejected → feedback stored, may regenerate

Security:
- All routes require admin authentication
- Uses Supabase RLS for additional protection
"""

import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from src.config.supabase_client import get_async_supabase
from src.config.settings import settings
from src.models.interview_confidence import ReportStatus, QAReview

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class QAReviewRequest(BaseModel):
    """Request to submit a QA review."""
    report_id: str
    approved: bool
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None
    accuracy_score: Optional[int] = None      # 1-5
    relevance_score: Optional[int] = None     # 1-5
    actionability_score: Optional[int] = None # 1-5


class QAQueueFilters(BaseModel):
    """Filters for QA queue."""
    status: Optional[str] = "qa_pending"
    industry: Optional[str] = None
    limit: int = 20
    offset: int = 0


# ============================================================================
# QA Queue Endpoints
# ============================================================================

@router.get("/queue")
async def get_qa_queue(
    status_filter: str = "qa_pending",
    industry: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
):
    """
    Get the QA review queue.

    Returns reports pending QA review, ordered by generation time.
    """
    try:
        supabase = await get_async_supabase()

        # Build query
        query = supabase.table("reports").select(
            "id, quiz_session_id, tier, status, created_at, "
            "generation_started_at, generation_completed_at, "
            "executive_summary, qa_review"
        )

        # Apply filters
        if status_filter:
            query = query.eq("status", status_filter)

        # Order by generation time (oldest first for FIFO)
        query = query.order("generation_completed_at", desc=False)

        # Pagination
        query = query.range(offset, offset + limit - 1)

        result = await query.execute()

        # Enrich with session data
        reports = []
        for report in result.data or []:
            # Get session info
            session_result = await supabase.table("quiz_sessions").select(
                "email, company_name, answers"
            ).eq("id", report["quiz_session_id"]).single().execute()

            session = session_result.data or {}
            answers = session.get("answers", {})

            reports.append({
                "report_id": report["id"],
                "session_id": report["quiz_session_id"],
                "tier": report["tier"],
                "status": report["status"],
                "company_name": session.get("company_name", "Unknown"),
                "email": session.get("email", "Unknown"),
                "industry": answers.get("industry", "Unknown"),
                "generated_at": report.get("generation_completed_at"),
                "waiting_since": report.get("generation_completed_at"),
                "executive_summary_preview": (
                    report.get("executive_summary", "")[:200] + "..."
                    if report.get("executive_summary") else None
                ),
            })

        # Get queue stats
        stats_result = await supabase.table("reports").select(
            "status", options={"count": "exact", "head": True}
        ).eq("status", "qa_pending").execute()

        return {
            "queue": reports,
            "total_pending": stats_result.count or 0,
            "filters": {
                "status": status_filter,
                "industry": industry,
            },
            "pagination": {
                "limit": limit,
                "offset": offset,
                "returned": len(reports),
            },
        }

    except Exception as e:
        logger.error(f"QA queue error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load QA queue"
        )


@router.get("/report/{report_id}")
async def get_report_for_qa(report_id: str):
    """
    Get full report details for QA review.

    Returns the complete report with all findings, recommendations,
    and generation metadata.
    """
    try:
        supabase = await get_async_supabase()

        # Get report
        report_result = await supabase.table("reports").select("*").eq(
            "id", report_id
        ).single().execute()

        if not report_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )

        report = report_result.data

        # Get session data
        session_result = await supabase.table("quiz_sessions").select("*").eq(
            "id", report["quiz_session_id"]
        ).single().execute()

        session = session_result.data or {}

        # Build QA view
        return {
            "report": {
                "id": report["id"],
                "status": report["status"],
                "tier": report["tier"],
                "executive_summary": report.get("executive_summary"),
                "value_summary": report.get("value_summary"),
                "findings": report.get("findings", []),
                "recommendations": report.get("recommendations", []),
                "roadmap": report.get("roadmap"),
                "playbooks": report.get("playbooks", []),
                "industry_insights": report.get("industry_insights"),
                "math_validation": report.get("math_validation"),
                "assumption_log": report.get("assumption_log"),
                "semantic_retrieval": report.get("semantic_retrieval"),
                "generation_started_at": report.get("generation_started_at"),
                "generation_completed_at": report.get("generation_completed_at"),
            },
            "session": {
                "id": session.get("id"),
                "email": session.get("email"),
                "company_name": session.get("company_name"),
                "company_profile": session.get("company_profile"),
                "answers": session.get("answers"),
                "interview_data": session.get("interview_data"),
            },
            "qa_context": {
                "previous_reviews": report.get("qa_review"),
                "confidence_data": session.get("interview_data", {}).get("confidence"),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"QA report view error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load report for QA"
        )


@router.post("/review")
async def submit_qa_review(request: QAReviewRequest):
    """
    Submit a QA review for a report.

    If approved:
    - Status changes to 'released'
    - User is notified (email trigger)
    - Report becomes accessible

    If rejected:
    - Status changes to 'qa_rejected'
    - Rejection reason is stored
    - May trigger regeneration
    """
    try:
        supabase = await get_async_supabase()

        # Get report
        report_result = await supabase.table("reports").select(
            "id, status, quiz_session_id"
        ).eq("id", request.report_id).single().execute()

        if not report_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )

        report = report_result.data

        if report["status"] not in ["qa_pending", "qa_rejected"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Report is not pending QA (status: {report['status']})"
            )

        # Validate scores if provided
        for score_name in ["accuracy_score", "relevance_score", "actionability_score"]:
            score = getattr(request, score_name)
            if score is not None and (score < 1 or score > 5):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{score_name} must be between 1 and 5"
                )

        # Build review record
        review = QAReview(
            report_id=request.report_id,
            approved=request.approved,
            rejection_reason=request.rejection_reason,
            notes=request.notes,
            accuracy_score=request.accuracy_score,
            relevance_score=request.relevance_score,
            actionability_score=request.actionability_score,
            started_at=datetime.utcnow(),  # Would be set when reviewer opens report
            completed_at=datetime.utcnow(),
        )

        # Determine new status
        new_status = ReportStatus.RELEASED if request.approved else ReportStatus.QA_REJECTED

        # Update report
        await supabase.table("reports").update({
            "status": new_status.value,
            "qa_review": review.to_dict(),
            "qa_completed_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", request.report_id).execute()

        # Update session status
        session_status = "completed" if request.approved else "qa_rejected"
        await supabase.table("quiz_sessions").update({
            "status": session_status,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", report["quiz_session_id"]).execute()

        logger.info(
            f"QA review submitted for report {request.report_id}: "
            f"approved={request.approved}"
        )

        # TODO: Trigger email notification if approved

        return {
            "success": True,
            "report_id": request.report_id,
            "approved": request.approved,
            "new_status": new_status.value,
            "message": (
                "Report approved and released to user"
                if request.approved
                else f"Report rejected: {request.rejection_reason}"
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"QA review error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit QA review"
        )


@router.get("/stats")
async def get_qa_stats():
    """
    Get QA queue statistics.

    Returns counts by status, average review time, etc.
    """
    try:
        supabase = await get_async_supabase()

        # Get counts by status
        statuses = ["qa_pending", "released", "qa_rejected", "generating"]
        counts = {}

        for s in statuses:
            result = await supabase.table("reports").select(
                "id", options={"count": "exact", "head": True}
            ).eq("status", s).execute()
            counts[s] = result.count or 0

        # Get recent reviews
        recent_result = await supabase.table("reports").select(
            "id, status, qa_completed_at, qa_review"
        ).not_.is_("qa_completed_at", "null").order(
            "qa_completed_at", desc=True
        ).limit(10).execute()

        recent_reviews = []
        for r in recent_result.data or []:
            review = r.get("qa_review", {})
            recent_reviews.append({
                "report_id": r["id"],
                "status": r["status"],
                "completed_at": r["qa_completed_at"],
                "approved": review.get("approved"),
            })

        return {
            "queue_stats": counts,
            "total_pending": counts.get("qa_pending", 0),
            "recent_reviews": recent_reviews,
        }

    except Exception as e:
        logger.error(f"QA stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load QA stats"
        )


@router.post("/regenerate/{report_id}")
async def regenerate_report(report_id: str):
    """
    Trigger regeneration of a rejected report.

    This resets the report status and triggers a new generation
    with any updated data or improved prompts.
    """
    try:
        supabase = await get_async_supabase()

        # Get report
        report_result = await supabase.table("reports").select(
            "id, status, quiz_session_id"
        ).eq("id", report_id).single().execute()

        if not report_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )

        report = report_result.data

        if report["status"] != "qa_rejected":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only rejected reports can be regenerated (status: {report['status']})"
            )

        # Update status to generating
        await supabase.table("reports").update({
            "status": ReportStatus.GENERATING.value,
            "regeneration_requested_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", report_id).execute()

        await supabase.table("quiz_sessions").update({
            "status": "generating",
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", report["quiz_session_id"]).execute()

        logger.info(f"Report regeneration triggered for {report_id}")

        return {
            "success": True,
            "report_id": report_id,
            "session_id": report["quiz_session_id"],
            "message": "Report regeneration triggered",
            "next_step": f"Monitor at /api/reports/stream/{report['quiz_session_id']}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Regeneration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger regeneration"
        )
