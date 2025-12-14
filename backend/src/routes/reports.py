"""
Report Routes

Routes for managing and generating reports.
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.config.supabase_client import get_async_supabase
from src.middleware.auth import require_workspace, CurrentUser
from src.services.pdf_generator import generate_pdf_report

logger = logging.getLogger(__name__)

router = APIRouter()


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
    """
    try:
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

        # Generate PDF
        pdf_buffer = await generate_pdf_report(audit_id)

        client_name = audit.get("clients", {}).get("name", "client")
        filename = f"CRB_Report_{client_name}_{datetime.now().strftime('%Y%m%d')}.pdf"

        return StreamingResponse(
            pdf_buffer,
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
