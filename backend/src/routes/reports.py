"""
Report Routes

Routes for managing and generating reports.
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.config.supabase_client import get_async_supabase
from src.config.redis_client import get_redis
from src.middleware.auth import require_workspace, CurrentUser, get_optional_user
from src.services.pdf_generator import generate_pdf_report
from src.services.report_service import (
    get_report as get_report_by_id,
    get_report_by_quiz_session,
    generate_report_streaming,
)
from src.services.storage_service import (
    get_storage_service,
    upload_report_pdf,
    get_report_download_url,
)

logger = logging.getLogger(__name__)

# Lock expiry for report generation (5 minutes)
REPORT_GENERATION_LOCK_TTL = 300

router = APIRouter()

# Load sample report at startup
SAMPLE_REPORT_PATH = Path(__file__).parent.parent / "data" / "sample_report.json"
_sample_report = None

def get_sample_report():
    """Load sample report from file (cached)."""
    global _sample_report
    if _sample_report is None:
        try:
            with open(SAMPLE_REPORT_PATH) as f:
                _sample_report = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load sample report: {e}")
            _sample_report = {}
    return _sample_report


# ============================================================================
# PUBLIC ROUTES (for guest/quiz-based reports)
# ============================================================================

@router.get("/sample")
async def get_sample_report_endpoint():
    """
    Get a sample demo report to showcase the analysis.
    No authentication required.
    """
    report = get_sample_report()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sample report not available"
        )
    return report


@router.get("/public/{report_id}")
async def get_public_report(report_id: str):
    """
    Get a report by ID (public access for quiz-based reports).
    Requires payment to have been completed.
    """
    try:
        report = await get_report_by_id(report_id)

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )

        # Verify payment status via quiz session
        quiz_session_id = report.get("quiz_session_id")
        if quiz_session_id:
            supabase = await get_async_supabase()
            session_result = await supabase.table("quiz_sessions").select(
                "status"
            ).eq("id", quiz_session_id).single().execute()

            if session_result.data:
                session_status = session_result.data.get("status")
                # Only allow access if payment was completed
                if session_status not in ["paid", "completed", "generating"]:
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail="Payment required to access this report"
                    )

        # Only return completed/viewable reports
        viewable_statuses = ["completed", "qa_pending", "released"]
        if report.get("status") not in viewable_statuses:
            return {
                "status": report.get("status"),
                "message": "Report is being generated. Please check back shortly.",
            }

        return {
            "id": report["id"],
            "tier": report.get("tier"),
            "status": report.get("status"),
            "executive_summary": report.get("executive_summary"),
            "value_summary": report.get("value_summary"),
            "findings": report.get("findings", []),
            "recommendations": report.get("recommendations", []),
            "roadmap": report.get("roadmap"),
            "methodology_notes": report.get("methodology_notes"),
            "created_at": report.get("created_at"),
            # Enhanced report data
            "playbooks": report.get("playbooks", []),
            "system_architecture": report.get("system_architecture", {}),
            "industry_insights": report.get("industry_insights", {}),
            # Transparency / Accuracy data
            "math_validation": report.get("math_validation", {}),
            "assumption_log": report.get("assumption_log", {}),
            # RAG retrieval data (for debugging/verification)
            "semantic_retrieval": report.get("semantic_retrieval", {}),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get public report error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get report"
        )


@router.get("/by-quiz/{quiz_session_id}")
async def get_report_by_quiz(quiz_session_id: str):
    """
    Get a report by quiz session ID.
    """
    try:
        report = await get_report_by_quiz_session(quiz_session_id)

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found for this quiz session"
            )

        return {
            "id": report["id"],
            "status": report.get("status"),
            "tier": report.get("tier"),
            "executive_summary": report.get("executive_summary") if report.get("status") == "completed" else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get report by quiz error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get report"
        )


async def _poll_existing_generation(quiz_session_id: str):
    """
    Poll for existing report generation progress.
    Used when another request is already generating the report.
    """
    supabase = await get_async_supabase()
    poll_interval = 2  # seconds
    max_polls = 150  # 5 minutes max

    for i in range(max_polls):
        try:
            # Check quiz session status
            result = await supabase.table("quiz_sessions").select(
                "status, report_id"
            ).eq("id", quiz_session_id).single().execute()

            if not result.data:
                yield f"data: {json.dumps({'phase': 'error', 'step': 'Session not found', 'progress': 0})}\n\n"
                return

            status = result.data.get("status")
            report_id = result.data.get("report_id")

            if status == "completed" and report_id:
                yield f"data: {json.dumps({'phase': 'complete', 'report_id': report_id, 'progress': 100})}\n\n"
                return
            elif status == "generating":
                # Estimate progress based on time
                progress = min(10 + (i * 2), 90)
                yield f"data: {json.dumps({'phase': 'generating', 'step': 'Report generation in progress...', 'progress': progress})}\n\n"
            elif status in ["paid"]:
                yield f"data: {json.dumps({'phase': 'waiting', 'step': 'Waiting for generation to start...', 'progress': 5})}\n\n"
            else:
                yield f"data: {json.dumps({'phase': 'error', 'step': f'Unexpected status: {status}', 'progress': 0})}\n\n"
                return

            await asyncio.sleep(poll_interval)

        except Exception as e:
            logger.error(f"Poll error: {e}")
            yield f"data: {json.dumps({'phase': 'error', 'step': str(e), 'progress': 0})}\n\n"
            return

    yield f"data: {json.dumps({'phase': 'error', 'step': 'Generation timeout', 'progress': 0})}\n\n"


@router.get("/stream/{quiz_session_id}")
async def stream_report_generation(quiz_session_id: str, tier: str = "quick"):
    """
    Server-Sent Events stream for report generation progress.

    Uses Redis lock to prevent duplicate generation from multiple tabs.

    Events:
    - progress: {"phase": "...", "step": "...", "progress": 25}
    - finding: {"id": "...", "title": "...", "preview": "..."}
    - recommendation: {"id": "...", "title": "..."}
    - complete: {"report_id": "...", "status": "completed"}
    - error: {"message": "...", "recoverable": true}

    Usage:
        const eventSource = new EventSource('/api/reports/stream/{quiz_session_id}');
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            // Handle progress updates
        };
    """
    lock_key = f"report_generation:{quiz_session_id}"

    async def event_generator():
        redis = await get_redis()
        lock_acquired = False

        try:
            # Try to acquire lock (only if Redis is available)
            if redis:
                lock_acquired = await redis.set(
                    lock_key, "1", nx=True, ex=REPORT_GENERATION_LOCK_TTL
                )

            if redis and not lock_acquired:
                # Another generation in progress, poll for status
                logger.info(f"Report generation already in progress for {quiz_session_id}, polling...")
                async for event in _poll_existing_generation(quiz_session_id):
                    yield event
                return

            # We have the lock (or Redis unavailable), proceed with generation
            async for event in generate_report_streaming(quiz_session_id, tier):
                yield event

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'phase': 'error', 'step': str(e), 'progress': 0})}\n\n"

        finally:
            # Release lock
            if redis and lock_acquired:
                try:
                    await redis.delete(lock_key)
                except Exception as e:
                    logger.warning(f"Failed to release report generation lock: {e}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.get("/status/{quiz_session_id}")
async def get_report_status(quiz_session_id: str):
    """
    Get the current status of report generation for a quiz session.

    Returns the report status and progress without SSE.
    Useful for polling if SSE is not available.
    """
    try:
        supabase = await get_async_supabase()

        # Check quiz session status
        quiz_result = await supabase.table("quiz_sessions").select(
            "id, status, report_id"
        ).eq("id", quiz_session_id).single().execute()

        if not quiz_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz session not found"
            )

        quiz = quiz_result.data
        report_id = quiz.get("report_id")

        if not report_id:
            return {
                "quiz_session_id": quiz_session_id,
                "status": quiz["status"],
                "report_id": None,
                "report_status": None,
                "progress": 0 if quiz["status"] == "paid" else None,
            }

        # Get report status
        report_result = await supabase.table("reports").select(
            "id, status, generation_started_at, generation_completed_at"
        ).eq("id", report_id).single().execute()

        if not report_result.data:
            return {
                "quiz_session_id": quiz_session_id,
                "status": quiz["status"],
                "report_id": report_id,
                "report_status": "unknown",
                "progress": 0,
            }

        report = report_result.data

        # Estimate progress based on status
        progress_map = {
            "generating": 50,  # Rough midpoint
            "completed": 100,
            "failed": 0,
        }

        return {
            "quiz_session_id": quiz_session_id,
            "status": quiz["status"],
            "report_id": report_id,
            "report_status": report["status"],
            "progress": progress_map.get(report["status"], 0),
            "started_at": report.get("generation_started_at"),
            "completed_at": report.get("generation_completed_at"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get report status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get report status"
        )


@router.post("/regenerate/{quiz_session_id}")
async def regenerate_report(quiz_session_id: str, tier: Optional[str] = None):
    """
    Regenerate a report for an existing quiz session.

    If the original report failed or needs to be refreshed, this endpoint
    triggers a new generation.
    """
    try:
        supabase = await get_async_supabase()

        # Get quiz session
        quiz_result = await supabase.table("quiz_sessions").select("*").eq(
            "id", quiz_session_id
        ).single().execute()

        if not quiz_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz session not found"
            )

        quiz = quiz_result.data

        # Check if paid
        if quiz["status"] not in ["paid", "completed", "generating"]:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Payment required before generating report"
            )

        # Use specified tier or original tier
        report_tier = tier or quiz.get("tier", "quick")

        # Mark existing report as superseded if it exists
        if quiz.get("report_id"):
            await supabase.table("reports").update({
                "status": "superseded",
            }).eq("id", quiz["report_id"]).execute()

        # Update quiz session status
        await supabase.table("quiz_sessions").update({
            "status": "generating",
            "report_id": None,  # Will be set by report generator
        }).eq("id", quiz_session_id).execute()

        logger.info(f"Regenerating report for quiz session {quiz_session_id}")

        # Return stream URL for client to connect to
        return {
            "success": True,
            "quiz_session_id": quiz_session_id,
            "tier": report_tier,
            "stream_url": f"/api/reports/stream/{quiz_session_id}?tier={report_tier}",
            "message": "Report regeneration started. Connect to stream_url for progress.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Regenerate report error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start report regeneration"
        )


@router.get("/public/{report_id}/pdf")
async def download_public_pdf(report_id: str):
    """
    Download PDF for a public report.
    Checks storage cache first, generates if not found.
    Requires payment to have been completed.
    """
    try:
        from src.services.pdf_generator import generate_pdf_from_report_data
        import io

        report = await get_report_by_id(report_id)

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )

        # Verify payment status via quiz session
        quiz_session_id = report.get("quiz_session_id")
        if quiz_session_id:
            supabase = await get_async_supabase()
            session_result = await supabase.table("quiz_sessions").select(
                "status"
            ).eq("id", quiz_session_id).single().execute()

            if session_result.data:
                session_status = session_result.data.get("status")
                if session_status not in ["paid", "completed", "generating"]:
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail="Payment required to access this report"
                    )

        if report.get("status") != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Report is not ready yet"
            )

        # Check if PDF is already cached in storage
        storage = get_storage_service()
        if await storage.file_exists(report_id):
            # Get signed URL for cached PDF
            signed_url = await get_report_download_url(report_id)
            if signed_url:
                from fastapi.responses import RedirectResponse
                return RedirectResponse(url=signed_url)

        # Generate PDF from report data
        pdf_buffer = await generate_pdf_from_report_data(report)

        # Read buffer content for storage
        pdf_bytes = pdf_buffer.read()
        pdf_buffer.seek(0)  # Reset for streaming response

        # Cache PDF in storage (non-blocking)
        try:
            await upload_report_pdf(report_id, pdf_bytes)
            logger.info(f"PDF cached in storage for report {report_id}")
        except Exception as storage_err:
            logger.warning(f"Failed to cache PDF in storage: {storage_err}")

        filename = f"CRB_Report_{datetime.now().strftime('%Y%m%d')}.pdf"

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Public PDF generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PDF"
        )


# ============================================================================
# AUTHENTICATED ROUTES (for workspace-based reports)
# ============================================================================


@router.get("/{audit_id}")
async def get_report(
    audit_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Get the main report for an audit.
    """
    try:
        supabase = await get_async_supabase()

        # Verify audit belongs to workspace
        audit_result = await supabase.table("audits").select(
            "*, clients(name, industry, company_size)"
        ).eq("id", audit_id).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not audit_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found"
            )

        audit = audit_result.data
        client = audit.pop("clients", {})

        # Get report
        report_result = await supabase.table("reports").select("*").eq(
            "audit_id", audit_id
        ).order("created_at", desc=True).limit(1).execute()

        report = report_result.data[0] if report_result.data else None

        # Get findings
        findings_result = await supabase.table("findings").select("*").eq(
            "audit_id", audit_id
        ).order("priority").execute()

        # Get recommendations
        recs_result = await supabase.table("recommendations").select("*").eq(
            "audit_id", audit_id
        ).order("priority").execute()

        return {
            "audit": {
                **audit,
                "client_name": client.get("name"),
                "client_industry": client.get("industry"),
            },
            "report": report,
            "findings": findings_result.data or [],
            "recommendations": recs_result.data or [],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get report error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get report"
        )


@router.get("/{audit_id}/pdf")
async def download_pdf(
    audit_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Generate and download PDF report.
    Checks storage cache first, generates if not found.
    """
    try:
        import io
        supabase = await get_async_supabase()

        # Verify audit and tier
        audit_result = await supabase.table("audits").select(
            "*, clients(name, industry, company_size)"
        ).eq("id", audit_id).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not audit_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found"
            )

        audit = audit_result.data

        # Check tier
        if audit["tier"] == "free":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="PDF download requires Professional tier"
            )

        if audit["status"] != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Report not ready - audit not completed"
            )

        client_name = audit.get("clients", {}).get("name", "client")
        filename = f"CRB_Report_{client_name}_{datetime.now().strftime('%Y%m%d')}.pdf"

        # Check if PDF is already cached in storage
        storage = get_storage_service()
        if await storage.file_exists(audit_id):
            # Get signed URL for cached PDF
            signed_url = await get_report_download_url(audit_id)
            if signed_url:
                from fastapi.responses import RedirectResponse
                return RedirectResponse(url=signed_url)

        # Generate PDF
        pdf_buffer = await generate_pdf_report(audit_id)

        # Read buffer content for storage
        pdf_bytes = pdf_buffer.read()

        # Cache PDF in storage
        try:
            await upload_report_pdf(audit_id, pdf_bytes)
            logger.info(f"PDF cached in storage for audit {audit_id}")
        except Exception as storage_err:
            logger.warning(f"Failed to cache PDF in storage: {storage_err}")

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PDF"
        )


@router.get("/{audit_id}/export")
async def export_data(
    audit_id: str,
    format: str = "json",
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Export raw report data.
    """
    try:
        supabase = await get_async_supabase()

        # Verify audit and tier
        audit_result = await supabase.table("audits").select(
            "*, clients(name, industry)"
        ).eq("id", audit_id).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not audit_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found"
            )

        audit = audit_result.data

        if audit["tier"] == "free":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Data export requires Professional tier"
            )

        # Get all data
        findings_result = await supabase.table("findings").select("*").eq(
            "audit_id", audit_id
        ).execute()

        recs_result = await supabase.table("recommendations").select("*").eq(
            "audit_id", audit_id
        ).execute()

        intake_result = await supabase.table("intake_responses").select("*").eq(
            "audit_id", audit_id
        ).single().execute()

        export_data = {
            "export_date": datetime.utcnow().isoformat(),
            "audit": {
                "id": audit["id"],
                "title": audit["title"],
                "status": audit["status"],
                "ai_readiness_score": audit.get("ai_readiness_score"),
                "total_potential_savings": audit.get("total_potential_savings"),
                "client": audit.get("clients", {}),
            },
            "intake_responses": intake_result.data.get("responses", {}) if intake_result.data else {},
            "findings": findings_result.data or [],
            "recommendations": recs_result.data or [],
        }

        return export_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export data"
        )
