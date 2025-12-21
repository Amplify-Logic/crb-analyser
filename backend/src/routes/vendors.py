"""
Vendor Routes

API routes for vendor management, comparison, and pricing refresh.
Uses JSON-based knowledge base for public endpoints.
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException, status, Query, Depends

from src.services.vendor_service import (
    vendor_service,
    search_vendors_kb,
    get_vendor_kb,
    compare_vendors_kb,
    get_category_overview,
    get_vendors_for_use_case,
    get_knowledge_stats,
    get_llm_recommendation,
)
from src.services.vendor_refresh_service import vendor_refresh_service
from src.middleware.auth import require_workspace, CurrentUser, require_admin
from src.knowledge import list_vendor_categories
from src.models.vendor import VendorCreate, VendorUpdate, VendorResponse, RefreshResult

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# PUBLIC ROUTES (no auth required) - Uses JSON Knowledge Base
# ============================================================================

@router.get("")
async def list_vendors(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    company_size: Optional[str] = Query(None, description="Filter by company size"),
    max_price: Optional[float] = Query(None, description="Max starting price"),
    has_free_tier: Optional[bool] = Query(None, description="Only vendors with free tier"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
):
    """
    List vendors from knowledge base with optional filtering.

    Public endpoint - no authentication required.
    """
    try:
        result = search_vendors_kb(
            query=search,
            category=category,
            company_size=company_size,
            max_price=max_price,
            has_free_tier=has_free_tier,
            limit=limit,
        )

        return {
            "vendors": result["vendors"],
            "total": result["total"],
            "filters_applied": result["filters_applied"],
        }

    except Exception as e:
        logger.error(f"List vendors error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list vendors"
        )


@router.get("/categories")
async def list_categories():
    """
    List all vendor categories.

    Public endpoint - no authentication required.
    """
    try:
        categories = list_vendor_categories()
        result = []
        for cat in categories:
            overview = get_category_overview(cat)
            if "error" not in overview:
                result.append({
                    "category": cat,
                    "description": overview.get("description", ""),
                    "vendor_count": overview.get("vendor_count", 0),
                })

        return result

    except Exception as e:
        logger.error(f"List categories error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list categories"
        )


@router.get("/categories/{category}")
async def get_category(category: str):
    """
    Get detailed category overview with all vendors.

    Public endpoint - no authentication required.
    """
    try:
        result = get_category_overview(category)

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get category error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get category"
        )


@router.get("/recommend")
async def recommend_vendors(
    use_case: str = Query(..., description="What you need the vendor for"),
    budget: Optional[float] = Query(None, description="Monthly budget"),
    company_size: Optional[str] = Query(None, description="Company size"),
    prefer_free: bool = Query(False, description="Prefer free tiers"),
    limit: int = Query(5, ge=1, le=10, description="Max recommendations"),
):
    """
    Get vendor recommendations for a specific use case.

    Public endpoint - no authentication required.
    """
    try:
        result = get_vendors_for_use_case(
            use_case=use_case,
            budget_monthly=budget,
            company_size=company_size,
            prefer_free=prefer_free,
            limit=limit,
        )

        return result

    except Exception as e:
        logger.error(f"Recommend vendors error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recommendations"
        )


@router.get("/llm-recommend")
async def recommend_llm(
    use_case: str = Query(..., description="What you'll use the LLM for"),
    volume: str = Query("medium", description="Monthly volume: low, medium, high"),
    priority: str = Query("balanced", description="Priority: cost, quality, speed, balanced"),
):
    """
    Get LLM/AI model recommendations with cost estimates.

    Public endpoint - no authentication required.
    """
    try:
        result = get_llm_recommendation(
            use_case=use_case,
            monthly_volume=volume,
            priority=priority,
        )

        return result

    except Exception as e:
        logger.error(f"LLM recommend error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get LLM recommendations"
        )


@router.get("/stats")
async def get_stats():
    """
    Get knowledge base statistics.

    Public endpoint - no authentication required.
    """
    try:
        return get_knowledge_stats()

    except Exception as e:
        logger.error(f"Get stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get stats"
        )


@router.get("/{slug}")
async def get_vendor(slug: str):
    """
    Get a single vendor by slug from knowledge base.

    Public endpoint - no authentication required.
    """
    try:
        vendor = get_vendor_kb(slug)

        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )

        return vendor

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get vendor error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get vendor"
        )


@router.post("/compare")
async def compare_vendors(slugs: List[str] = Query(..., description="Vendor slugs to compare")):
    """
    Compare multiple vendors side by side.

    Public endpoint - no authentication required.
    """
    if len(slugs) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 vendors required for comparison"
        )

    if len(slugs) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 vendors can be compared at once"
        )

    try:
        result = compare_vendors_kb(slugs)

        if not result.get("vendors"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No vendors found with the provided slugs"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Compare vendors error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare vendors"
        )


# ============================================================================
# AUTHENTICATED ROUTES (workspace required)
# ============================================================================

@router.post("", response_model=VendorResponse)
async def create_vendor(
    vendor: VendorCreate,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Create a new vendor.

    Requires authentication and workspace membership.
    """
    try:
        # Check if slug already exists
        existing = await vendor_service.get_vendor(vendor.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Vendor with slug '{vendor.slug}' already exists"
            )

        vendor_data = vendor.model_dump(exclude_none=True)
        result = await vendor_service.create_vendor(vendor_data)

        logger.info(f"Vendor created: {vendor.slug} by {current_user.email}")
        return VendorResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create vendor error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create vendor"
        )


@router.patch("/{slug}", response_model=VendorResponse)
async def update_vendor(
    slug: str,
    vendor: VendorUpdate,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Update an existing vendor.

    Requires authentication and workspace membership.
    """
    try:
        existing = await vendor_service.get_vendor(slug)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )

        update_data = vendor.model_dump(exclude_none=True)
        result = await vendor_service.update_vendor(slug, update_data)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update vendor"
            )

        logger.info(f"Vendor updated: {slug} by {current_user.email}")
        return VendorResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update vendor error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update vendor"
        )


@router.delete("/{slug}")
async def delete_vendor(
    slug: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Delete a vendor.

    Requires authentication and workspace membership.
    """
    try:
        existing = await vendor_service.get_vendor(slug)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )

        success = await vendor_service.delete_vendor(slug)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete vendor"
            )

        logger.info(f"Vendor deleted: {slug} by {current_user.email}")
        return {"success": True, "message": f"Vendor '{slug}' deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete vendor error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete vendor"
        )


# ============================================================================
# ADMIN ROUTES (admin role required)
# ============================================================================

@router.post("/refresh/{slug}", response_model=RefreshResult)
async def refresh_vendor_pricing(
    slug: str,
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Trigger a pricing refresh for a single vendor.

    Admin only - fetches current pricing from vendor website
    and updates the database if changed.
    """
    try:
        result = await vendor_refresh_service.refresh_vendor(slug)

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Refresh failed")
            )

        logger.info(f"Vendor pricing refreshed: {slug} by {current_user.email}")
        return RefreshResult(
            vendor_slug=slug,
            success=result["success"],
            changed=result.get("changed", False),
            old_pricing=result.get("old_pricing"),
            new_pricing=result.get("new_pricing"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refresh vendor error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh vendor pricing"
        )


@router.post("/refresh-all")
async def refresh_all_vendors(
    older_than_days: int = Query(7, ge=1, le=30),
    limit: int = Query(50, ge=1, le=100),
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Trigger pricing refresh for all vendors needing updates.

    Admin only - refreshes vendors whose pricing is older than
    the specified number of days.
    """
    try:
        results = await vendor_refresh_service.refresh_all_vendors(
            older_than_days=older_than_days,
            limit=limit,
        )

        success_count = sum(1 for r in results if r.get("success"))
        changed_count = sum(1 for r in results if r.get("changed"))

        logger.info(
            f"Bulk refresh completed by {current_user.email}: "
            f"{success_count}/{len(results)} successful, {changed_count} changed"
        )

        return {
            "total": len(results),
            "successful": success_count,
            "changed": changed_count,
            "results": results,
        }

    except Exception as e:
        logger.error(f"Refresh all vendors error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh vendors"
        )


@router.get("/admin/stats")
async def get_vendor_stats(
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Get vendor database statistics.

    Admin only - returns counts and freshness metrics.
    """
    try:
        from src.config.supabase_client import get_async_supabase
        from datetime import datetime, timedelta

        supabase = await get_async_supabase()

        # Total vendors
        total_result = await supabase.table("vendors").select("id", count="exact").execute()
        total = total_result.count or 0

        # Vendors with pricing
        with_pricing = await supabase.table("vendors").select(
            "id", count="exact"
        ).not_.is_("pricing", "null").execute()

        # Vendors needing refresh (older than 7 days)
        cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
        needing_refresh = await supabase.table("vendors").select(
            "id", count="exact"
        ).eq("auto_refresh_enabled", True).or_(
            f"pricing_verified_at.is.null,pricing_verified_at.lt.{cutoff}"
        ).execute()

        # Categories count
        categories = await vendor_service.get_categories()

        return {
            "total_vendors": total,
            "with_pricing": with_pricing.count or 0,
            "needing_refresh": needing_refresh.count or 0,
            "categories_count": len(categories),
            "categories": categories,
        }

    except Exception as e:
        logger.error(f"Get vendor stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get vendor stats"
        )
