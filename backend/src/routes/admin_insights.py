"""
Admin Insights Routes

Administrative endpoints for managing curated insights.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from anthropic import Anthropic
from fastapi import APIRouter, HTTPException, status, Query, Body
from pydantic import BaseModel, Field

from src.config.settings import settings

from src.models.insight import (
    CredibilityLevel,
    ExtractedInsights,
    Insight,
    InsightSearchQuery,
    InsightSearchResult,
    InsightTags,
    InsightType,
    UseIn,
    UserStage,
)
from src.services.insight_service import get_insight_service
from src.skills.extraction.insight_extraction import (
    InsightExtractionSkill,
    extract_insights_from_content,
)
from src.skills.base import SkillContext

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Pydantic Request/Response Models
# =============================================================================

class InsightCreateRequest(BaseModel):
    """Request to create a new insight."""
    id: str = Field(..., min_length=3, max_length=100)
    type: str = Field(..., description="trend, framework, case_study, statistic, quote, prediction")
    title: str = Field(..., min_length=3, max_length=200)
    content: str = Field(..., min_length=10)
    supporting_data: Optional[List[Dict[str, Any]]] = None
    actionable_insight: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    source: Dict[str, Any]
    reviewed: bool = False


class InsightUpdateRequest(BaseModel):
    """Request to update an insight."""
    title: Optional[str] = None
    content: Optional[str] = None
    supporting_data: Optional[List[Dict[str, Any]]] = None
    actionable_insight: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    reviewed: Optional[bool] = None


class ExtractionRequest(BaseModel):
    """Request to extract insights from content."""
    raw_content: str = Field(..., min_length=100)
    source_title: str = Field(..., min_length=3)
    source_author: Optional[str] = None
    source_url: Optional[str] = None
    source_date: Optional[str] = None
    source_type: str = Field(default="article")


class SearchRequest(BaseModel):
    """Request to search insights."""
    use_in: Optional[str] = None
    types: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    user_stage: Optional[str] = None
    context_query: Optional[str] = None
    reviewed_only: bool = True
    limit: int = Field(default=10, ge=1, le=50)


class InsightResponse(BaseModel):
    """Response containing an insight."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class InsightsListResponse(BaseModel):
    """Response containing a list of insights."""
    success: bool
    data: List[Dict[str, Any]]
    total: int


class StatsResponse(BaseModel):
    """Response containing insight statistics."""
    success: bool
    data: Dict[str, Any]


# =============================================================================
# Routes
# =============================================================================

@router.get("/stats")
async def get_stats() -> StatsResponse:
    """Get insight collection statistics."""
    service = get_insight_service()
    stats = service.get_stats()
    return StatsResponse(success=True, data=stats)


@router.get("/public/landing")
async def get_landing_insights(
    limit: int = Query(3, ge=1, le=10),
) -> InsightsListResponse:
    """
    Get reviewed insights suitable for landing page display.
    Returns only reviewed insights tagged for 'landing' use.
    """
    service = get_insight_service()

    # Get all reviewed insights tagged for landing
    all_insights = service.get_all_insights(reviewed_only=True)
    landing_insights = [
        i for i in all_insights
        if "landing" in [u.value if hasattr(u, 'value') else u for u in i.tags.use_in]
    ]

    # Return limited number
    landing_insights = landing_insights[:limit]

    return InsightsListResponse(
        success=True,
        data=[i.model_dump() for i in landing_insights],
        total=len(landing_insights),
    )


@router.get("/list")
async def list_insights(
    type: Optional[str] = Query(None, description="Filter by type"),
    reviewed_only: bool = Query(False, description="Only show reviewed insights"),
    limit: int = Query(100, ge=1, le=500),
) -> InsightsListResponse:
    """List all insights with optional filtering."""
    service = get_insight_service()

    if type:
        try:
            insight_type = InsightType(type)
            insights = service.get_insights_by_type(insight_type, reviewed_only=reviewed_only)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid type: {type}. Valid types: {[t.value for t in InsightType]}"
            )
    else:
        insights = service.get_all_insights(reviewed_only=reviewed_only)

    # Apply limit
    insights = insights[:limit]

    return InsightsListResponse(
        success=True,
        data=[i.model_dump() for i in insights],
        total=len(insights),
    )


@router.get("/{insight_id}")
async def get_insight(insight_id: str) -> InsightResponse:
    """Get a specific insight by ID."""
    service = get_insight_service()
    insight = service.get_insight_by_id(insight_id)

    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insight not found: {insight_id}"
        )

    return InsightResponse(success=True, data=insight.model_dump())


@router.post("/search")
async def search_insights(request: SearchRequest) -> InsightsListResponse:
    """Search insights with filtering and semantic matching."""
    service = get_insight_service()

    query = InsightSearchQuery(
        use_in=UseIn(request.use_in) if request.use_in else None,
        types=[InsightType(t) for t in request.types] if request.types else None,
        industries=request.industries,
        topics=request.topics,
        user_stage=UserStage(request.user_stage) if request.user_stage else None,
        context_query=request.context_query,
        reviewed_only=request.reviewed_only,
        limit=request.limit,
    )

    results = service.search_insights(query)

    return InsightsListResponse(
        success=True,
        data=[
            {
                **r.insight.model_dump(),
                "relevance_score": r.relevance_score,
                "match_reason": r.match_reason,
            }
            for r in results
        ],
        total=len(results),
    )


@router.post("/create")
async def create_insight(request: InsightCreateRequest) -> InsightResponse:
    """Create a new insight manually."""
    service = get_insight_service()

    # Check for duplicate
    existing = service.get_insight_by_id(request.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Insight with ID '{request.id}' already exists"
        )

    # Build insight
    try:
        from src.models.insight import InsightSource, SupportingData

        insight = Insight(
            id=request.id,
            type=InsightType(request.type),
            title=request.title,
            content=request.content,
            supporting_data=[SupportingData(**sd) for sd in (request.supporting_data or [])],
            actionable_insight=request.actionable_insight,
            tags=InsightTags(**(request.tags or {})),
            source=InsightSource(**request.source),
            reviewed=request.reviewed,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid insight data: {e}"
        )

    if not service.add_insight(insight):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save insight"
        )

    return InsightResponse(
        success=True,
        data=insight.model_dump(),
        message="Insight created successfully"
    )


@router.put("/{insight_id}")
async def update_insight(insight_id: str, request: InsightUpdateRequest) -> InsightResponse:
    """Update an existing insight."""
    service = get_insight_service()

    existing = service.get_insight_by_id(insight_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insight not found: {insight_id}"
        )

    # Build updates dict
    updates = {}
    if request.title is not None:
        updates["title"] = request.title
    if request.content is not None:
        updates["content"] = request.content
    if request.supporting_data is not None:
        updates["supporting_data"] = request.supporting_data
    if request.actionable_insight is not None:
        updates["actionable_insight"] = request.actionable_insight
    if request.tags is not None:
        updates["tags"] = request.tags
    if request.reviewed is not None:
        updates["reviewed"] = request.reviewed

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No updates provided"
        )

    if not service.update_insight(insight_id, updates):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update insight"
        )

    updated = service.get_insight_by_id(insight_id)
    return InsightResponse(
        success=True,
        data=updated.model_dump() if updated else None,
        message="Insight updated successfully"
    )


@router.post("/{insight_id}/review")
async def mark_reviewed(
    insight_id: str,
    reviewed: bool = Query(True, description="Set reviewed status")
) -> InsightResponse:
    """Mark an insight as reviewed or unreviewed."""
    service = get_insight_service()

    existing = service.get_insight_by_id(insight_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insight not found: {insight_id}"
        )

    if not service.mark_reviewed(insight_id, reviewed):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update review status"
        )

    return InsightResponse(
        success=True,
        message=f"Insight {'marked as reviewed' if reviewed else 'unmarked as reviewed'}"
    )


@router.delete("/{insight_id}")
async def delete_insight(insight_id: str) -> InsightResponse:
    """Delete an insight."""
    service = get_insight_service()

    existing = service.get_insight_by_id(insight_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insight not found: {insight_id}"
        )

    if not service.delete_insight(insight_id):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete insight"
        )

    return InsightResponse(success=True, message="Insight deleted successfully")


@router.post("/extract")
async def extract_insights(request: ExtractionRequest) -> Dict[str, Any]:
    """
    Extract insights from raw content using AI.

    Returns extracted insights for review before saving.
    """
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ANTHROPIC_API_KEY not configured"
        )
    api_key = settings.ANTHROPIC_API_KEY

    client = Anthropic(api_key=api_key)

    try:
        extracted = await extract_insights_from_content(
            client=client,
            raw_content=request.raw_content,
            source_title=request.source_title,
            source_author=request.source_author,
            source_url=request.source_url,
            source_date=request.source_date,
            source_type=request.source_type,
        )
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed: {str(e)}"
        )

    return {
        "success": True,
        "data": {
            "source": extracted.source.model_dump(),
            "extracted_at": extracted.extracted_at,
            "insights": [i.model_dump() for i in extracted.insights],
            "extraction_notes": extracted.extraction_notes,
        },
        "message": f"Extracted {len(extracted.insights)} insights"
    }


@router.post("/save-extracted")
async def save_extracted_insights(
    insights: List[Dict[str, Any]] = Body(..., description="List of insights to save")
) -> Dict[str, Any]:
    """
    Save extracted insights after review.

    Accepts the insights array from the extract endpoint after user review/editing.
    """
    service = get_insight_service()

    # Parse insights
    parsed_insights = []
    for raw in insights:
        try:
            insight = Insight(**raw)
            parsed_insights.append(insight)
        except Exception as e:
            logger.warning(f"Failed to parse insight: {e}")
            continue

    if not parsed_insights:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid insights to save"
        )

    result = service.add_insights_batch(parsed_insights)

    return {
        "success": True,
        "data": result,
        "message": f"Saved {result['added']} insights ({result['skipped']} skipped)"
    }


# =============================================================================
# Dashboard Aggregation
# =============================================================================

@router.get("/dashboard/summary")
async def get_dashboard_summary() -> Dict[str, Any]:
    """
    Get summary data for the admin dashboard.

    Returns stats across insights, vendors, and other admin data.
    """
    service = get_insight_service()
    insight_stats = service.get_stats()

    # Get vendor stats (if vendor service is available)
    try:
        from src.services.vendor_service import vendor_service
        vendor_stats = {
            "total": len(vendor_service.get_all_vendors()),
        }
    except Exception:
        vendor_stats = {"total": 0}

    return {
        "success": True,
        "data": {
            "insights": insight_stats,
            "vendors": vendor_stats,
            "last_updated": datetime.now().isoformat(),
        }
    }
