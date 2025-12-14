"""
Research Routes

API endpoints for company pre-research and dynamic questionnaire generation.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.config.supabase_client import get_async_supabase
from src.middleware.auth import require_workspace, CurrentUser
from src.models.research import (
    StartResearchRequest,
    ResearchStatusResponse,
    ResearchCompleteResponse,
    SaveResearchAnswersRequest,
)
from src.agents.pre_research_agent import start_company_research, PreResearchAgent

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/start")
async def start_research(
    request: StartResearchRequest,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Start researching a company.

    Returns a research_id and streams progress via SSE.
    """
    try:
        # Create research record in database
        supabase = await get_async_supabase()

        research_data = {
            "workspace_id": current_user.workspace_id,
            "company_name": request.company_name,
            "website_url": request.website_url,
            "status": "pending",
            "additional_context": request.additional_context,
        }

        result = await supabase.table("company_research").insert(research_data).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create research record",
            )

        research_id = result.data[0]["id"]

        logger.info(f"Started research for {request.company_name} (ID: {research_id})")

        return {
            "research_id": research_id,
            "message": f"Research started for {request.company_name}",
            "stream_url": f"/api/research/{research_id}/stream",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Start research error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{research_id}/stream")
async def stream_research(
    research_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Stream research progress via Server-Sent Events.
    """
    try:
        supabase = await get_async_supabase()

        # Verify research belongs to workspace
        research = await supabase.table("company_research").select("*").eq(
            "id", research_id
        ).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not research.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research not found",
            )

        company_name = research.data["company_name"]
        website_url = research.data.get("website_url")

        # Update status to researching
        await supabase.table("company_research").update({
            "status": "researching",
        }).eq("id", research_id).execute()

        async def generate():
            try:
                async for event in start_company_research(company_name, website_url):
                    yield event

                    # Parse event to check for completion
                    if '"status": "ready"' in event or '"status": "failed"' in event:
                        # Update database with result
                        import json
                        data = json.loads(event.replace("data: ", ""))

                        if data.get("status") == "ready":
                            result = data.get("result", {})
                            await supabase.table("company_research").update({
                                "status": "completed",
                                "company_profile": result.get("company_profile"),
                                "questionnaire": result.get("questionnaire"),
                            }).eq("id", research_id).execute()
                        else:
                            await supabase.table("company_research").update({
                                "status": "failed",
                                "error": data.get("error"),
                            }).eq("id", research_id).execute()

            except Exception as e:
                logger.error(f"Research stream error: {e}")
                await supabase.table("company_research").update({
                    "status": "failed",
                    "error": str(e),
                }).eq("id", research_id).execute()
                yield f"data: {{\"status\": \"failed\", \"error\": \"{str(e)}\"}}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stream research error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{research_id}")
async def get_research(
    research_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Get research results.
    """
    try:
        supabase = await get_async_supabase()

        result = await supabase.table("company_research").select("*").eq(
            "id", research_id
        ).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research not found",
            )

        return result.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get research error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/{research_id}/answers")
async def save_research_answers(
    research_id: str,
    request: SaveResearchAnswersRequest,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Save answers to the dynamic questionnaire.

    This completes the research phase and creates a client + audit.
    """
    try:
        supabase = await get_async_supabase()

        # Get research
        research = await supabase.table("company_research").select("*").eq(
            "id", research_id
        ).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not research.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research not found",
            )

        if research.data["status"] != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Research not yet complete",
            )

        company_profile = research.data.get("company_profile", {})
        company_name = research.data["company_name"]

        # Extract company info from profile
        basics = company_profile.get("basics", {})
        size = company_profile.get("size", {})
        industry_info = company_profile.get("industry", {})

        # Determine industry from profile
        industry = "other"
        if industry_info:
            primary = industry_info.get("primary_industry", {})
            if isinstance(primary, dict):
                industry = primary.get("value", "other")

        # Determine company size
        company_size = "51-200"
        if size:
            emp_range = size.get("employee_range", {})
            if isinstance(emp_range, dict):
                company_size = emp_range.get("value", "51-200")

        # Create client
        client_data = {
            "workspace_id": current_user.workspace_id,
            "name": company_name,
            "industry": industry,
            "company_size": company_size,
            "website": research.data.get("website_url"),
        }

        client_result = await supabase.table("clients").insert(client_data).execute()

        if not client_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create client",
            )

        client_id = client_result.data[0]["id"]

        # Create audit
        audit_data = {
            "workspace_id": current_user.workspace_id,
            "client_id": client_id,
            "title": f"{company_name} - CRB Audit",
            "tier": request.tier,
            "status": "pending" if request.tier == "free" else "analyzing",
        }

        audit_result = await supabase.table("audits").insert(audit_data).execute()

        if not audit_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create audit",
            )

        audit_id = audit_result.data[0]["id"]

        # Merge research profile with questionnaire answers
        combined_responses = {
            **company_profile,  # Pre-researched data
            "questionnaire_answers": request.answers,  # User answers
        }

        # Create intake responses
        intake_data = {
            "audit_id": audit_id,
            "responses": combined_responses,
            "is_complete": True,
            "current_section": 5,
        }

        await supabase.table("intake_responses").insert(intake_data).execute()

        # Update research record
        await supabase.table("company_research").update({
            "client_id": client_id,
            "audit_id": audit_id,
            "answers": request.answers,
        }).eq("id", research_id).execute()

        logger.info(f"Created client {client_id} and audit {audit_id} from research {research_id}")

        return {
            "success": True,
            "client_id": client_id,
            "audit_id": audit_id,
            "message": "Client and audit created successfully",
            "next_url": f"/audit/{audit_id}/progress",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Save research answers error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("")
async def list_research(
    current_user: CurrentUser = Depends(require_workspace),
    limit: int = 20,
):
    """
    List recent research for the workspace.
    """
    try:
        supabase = await get_async_supabase()

        result = await supabase.table("company_research").select("*").eq(
            "workspace_id", current_user.workspace_id
        ).order("created_at", desc=True).limit(limit).execute()

        return {"data": result.data, "total": len(result.data)}

    except Exception as e:
        logger.error(f"List research error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
