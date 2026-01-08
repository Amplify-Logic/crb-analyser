"""
Admin Research Routes

Endpoints for the vendor research agent:
- Refresh stale vendors
- Discover new vendors
- Apply approved updates
"""

import json
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.agents.research import (
    RefreshRequest,
    RefreshScope,
    DiscoverRequest,
    refresh_vendors,
    discover_vendors,
    get_stale_count,
    apply_vendor_updates,
    add_multiple_vendors,
    DiscoveredVendor,
    VendorUpdate,
)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class RefreshRequestBody(BaseModel):
    """Request body for refresh endpoint."""
    scope: str = Field(default="stale", description="stale, all, or specific")
    vendor_slugs: list[str] = Field(default_factory=list)
    category: Optional[str] = None
    industry: Optional[str] = None
    dry_run: bool = False


class DiscoverRequestBody(BaseModel):
    """Request body for discover endpoint."""
    category: str
    industry: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=50)


class ApplyUpdatesBody(BaseModel):
    """Request body for applying approved updates."""
    task_id: str
    approved_slugs: list[str]
    updates: list[dict]  # VendorUpdate dicts from the preview


class ApplyDiscoveriesBody(BaseModel):
    """Request body for adding discovered vendors."""
    task_id: str
    approved_vendors: list[dict]  # DiscoveredVendor dicts


class StaleCountResponse(BaseModel):
    """Response with stale vendor count."""
    count: int
    category: Optional[str] = None
    industry: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/stale-count")
async def get_stale_vendor_count(
    category: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
) -> StaleCountResponse:
    """Get count of stale vendors matching filters."""
    count = await get_stale_count(category=category, industry=industry)
    return StaleCountResponse(count=count, category=category, industry=industry)


@router.post("/refresh")
async def refresh_vendor_data(body: RefreshRequestBody):
    """
    Refresh vendor pricing data.

    Returns SSE stream with progress updates.
    """
    # Convert to internal request
    scope = RefreshScope.STALE
    if body.scope == "all":
        scope = RefreshScope.ALL
    elif body.scope == "specific":
        scope = RefreshScope.SPECIFIC

    request = RefreshRequest(
        scope=scope,
        vendor_slugs=body.vendor_slugs,
        category=body.category,
        industry=body.industry,
        dry_run=body.dry_run,
    )

    async def generate():
        async for update in refresh_vendors(request):
            yield f"data: {json.dumps(update)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/discover")
async def discover_new_vendors(body: DiscoverRequestBody):
    """
    Discover new vendors in a category.

    Returns SSE stream with progress updates.
    """
    request = DiscoverRequest(
        category=body.category,
        industry=body.industry,
        limit=body.limit,
    )

    async def generate():
        async for update in discover_vendors(request):
            yield f"data: {json.dumps(update)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/apply-updates")
async def apply_refresh_updates(body: ApplyUpdatesBody):
    """Apply approved vendor updates from a refresh task."""
    # Convert dicts back to VendorUpdate objects
    updates = []
    for u in body.updates:
        try:
            update = VendorUpdate(**u)
            updates.append(update)
        except Exception:
            continue

    result = await apply_vendor_updates(
        task_id=body.task_id,
        approved_slugs=body.approved_slugs,
        updates=updates,
    )

    return result


@router.post("/apply-discoveries")
async def apply_discovered_vendors(body: ApplyDiscoveriesBody):
    """Add approved discovered vendors to the database."""
    # Convert dicts to DiscoveredVendor objects
    vendors = []
    for v in body.approved_vendors:
        try:
            vendor = DiscoveredVendor(**v)
            vendors.append(vendor)
        except Exception:
            continue

    result = await add_multiple_vendors(vendors)

    return result
