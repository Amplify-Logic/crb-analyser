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


# =============================================================================
# Product Strategy Insights (from docs/video-insights/)
# =============================================================================

class ProductInsightSummary(BaseModel):
    """Summary of a product strategy insight."""
    filename: str
    title: str
    date: str
    relevance_score: Optional[str] = None
    tldr: Optional[str] = None
    immediate_actions: List[Dict[str, Any]] = []
    watch_list: List[str] = []
    file_path: str


class ProductInsightsResponse(BaseModel):
    """Response containing product insights."""
    success: bool
    data: List[ProductInsightSummary]
    total: int


def parse_product_insight_markdown(filepath: str) -> Optional[ProductInsightSummary]:
    """Parse a product insight markdown file and extract key sections."""
    import re
    from pathlib import Path

    path = Path(filepath)
    if not path.exists():
        return None

    content = path.read_text()
    filename = path.name

    # Extract date from filename (e.g., 2026-01-21-disposable-software-analysis.md)
    date_match = re.match(r'^(\d{4}-\d{2}-\d{2})', filename)
    date = date_match.group(1) if date_match else "Unknown"

    # Extract title from first H1
    title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else filename.replace('.md', '').replace('-', ' ').title()

    # Extract relevance score
    score_match = re.search(r'RELEVANCE SCORE[:\s]+(\d+/10)', content, re.IGNORECASE)
    relevance_score = score_match.group(1) if score_match else None

    # Extract TL;DR
    tldr_match = re.search(r'\*\*TL;DR[:\s]*\*\*\s*(.+?)(?=\n\n|\*\*Immediate)', content, re.DOTALL | re.IGNORECASE)
    tldr = tldr_match.group(1).strip() if tldr_match else None

    # Extract immediate actions (checkbox items)
    actions = []
    actions_section = re.search(r'\*\*Immediate actions.*?\*\*[:\s]*\n((?:- \[[ x]\].+\n?)+)', content, re.IGNORECASE)
    if actions_section:
        action_lines = re.findall(r'- \[([ x])\] (.+)', actions_section.group(1))
        for completed, text in action_lines:
            actions.append({
                "text": text.strip(),
                "completed": completed.lower() == 'x'
            })

    # Extract watch list
    watch_list = []
    watch_section = re.search(r'\*\*Watch list.*?\*\*[:\s]*\n((?:- .+\n?)+)', content, re.IGNORECASE)
    if watch_section:
        watch_items = re.findall(r'- (.+)', watch_section.group(1))
        watch_list = [item.strip() for item in watch_items]

    return ProductInsightSummary(
        filename=filename,
        title=title,
        date=date,
        relevance_score=relevance_score,
        tldr=tldr,
        immediate_actions=actions,
        watch_list=watch_list,
        file_path=str(path),
    )


@router.get("/product-insights")
async def list_product_insights() -> ProductInsightsResponse:
    """
    List all product strategy insights from docs/video-insights/.

    These are internal insights for informing product decisions,
    NOT customer-facing insights.
    """
    from pathlib import Path

    # Find the docs/video-insights directory relative to backend
    backend_dir = Path(__file__).parent.parent.parent
    insights_dir = backend_dir.parent / "docs" / "video-insights"

    if not insights_dir.exists():
        return ProductInsightsResponse(success=True, data=[], total=0)

    insights = []
    for md_file in sorted(insights_dir.glob("*.md"), reverse=True):
        parsed = parse_product_insight_markdown(str(md_file))
        if parsed:
            insights.append(parsed)

    return ProductInsightsResponse(
        success=True,
        data=insights,
        total=len(insights),
    )


@router.get("/product-insights/{filename}")
async def get_product_insight(filename: str) -> Dict[str, Any]:
    """
    Get the full content of a specific product insight.
    """
    from pathlib import Path

    backend_dir = Path(__file__).parent.parent.parent
    insights_dir = backend_dir.parent / "docs" / "video-insights"
    filepath = insights_dir / filename

    if not filepath.exists() or not filepath.suffix == '.md':
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product insight not found: {filename}"
        )

    content = filepath.read_text()
    parsed = parse_product_insight_markdown(str(filepath))

    return {
        "success": True,
        "data": {
            "summary": parsed.model_dump() if parsed else None,
            "content": content,
        }
    }


@router.post("/product-insights/{filename}/toggle-action")
async def toggle_product_insight_action(
    filename: str,
    action_index: int = Query(..., description="Index of the action to toggle")
) -> Dict[str, Any]:
    """
    Toggle the completion status of an action item in a product insight.

    Updates the markdown file directly.
    """
    from pathlib import Path
    import re

    backend_dir = Path(__file__).parent.parent.parent
    insights_dir = backend_dir.parent / "docs" / "video-insights"
    filepath = insights_dir / filename

    if not filepath.exists() or not filepath.suffix == '.md':
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product insight not found: {filename}"
        )

    content = filepath.read_text()

    # Find all checkbox items in immediate actions section
    pattern = r'(\*\*Immediate actions.*?\*\*[:\s]*\n)((?:- \[[ x]\].+\n?)+)'
    match = re.search(pattern, content, re.IGNORECASE)

    if not match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No immediate actions section found"
        )

    header = match.group(1)
    actions_text = match.group(2)

    # Parse and toggle the specific action
    lines = actions_text.strip().split('\n')
    if action_index < 0 or action_index >= len(lines):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action index: {action_index}"
        )

    line = lines[action_index]
    if '[ ]' in line:
        lines[action_index] = line.replace('[ ]', '[x]')
        new_status = True
    else:
        lines[action_index] = line.replace('[x]', '[ ]')
        new_status = False

    # Rebuild content
    new_actions = '\n'.join(lines) + '\n'
    new_content = content[:match.start()] + header + new_actions + content[match.end():]

    # Write back
    filepath.write_text(new_content)

    return {
        "success": True,
        "message": f"Action {'completed' if new_status else 'uncompleted'}",
        "data": {"completed": new_status}
    }
