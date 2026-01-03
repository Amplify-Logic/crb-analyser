"""
Admin Vendor Routes

Administrative endpoints for managing the vendor knowledge base.
"""

import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field

from src.config.supabase_client import get_async_supabase
from src.middleware.auth import require_workspace, CurrentUser
from src.services.vendor_service import vendor_service
from src.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


# =============================================================================
# Helper Functions
# =============================================================================

def build_vendor_embedding_text(vendor_data: dict) -> str:
    """
    Build text content for vendor embedding.
    Combines key fields that are useful for semantic search.
    """
    parts = [vendor_data.get("name", "")]

    if vendor_data.get("tagline"):
        parts.append(vendor_data["tagline"])

    if vendor_data.get("description"):
        parts.append(vendor_data["description"])

    if vendor_data.get("category"):
        parts.append(f"Category: {vendor_data['category']}")

    if vendor_data.get("best_for"):
        parts.append(f"Best for: {', '.join(vendor_data['best_for'])}")

    if vendor_data.get("key_capabilities"):
        parts.append(f"Capabilities: {', '.join(vendor_data['key_capabilities'])}")

    if vendor_data.get("industries"):
        parts.append(f"Industries: {', '.join(vendor_data['industries'])}")

    if vendor_data.get("recommended_for"):
        parts.append(f"Recommended for: {', '.join(vendor_data['recommended_for'])}")

    return "\n".join(parts)


async def generate_vendor_embedding(vendor_data: dict) -> Optional[list]:
    """
    Generate embedding for a vendor.
    Returns the embedding vector or None on failure.
    """
    try:
        embedding_service = await get_embedding_service()
        text = build_vendor_embedding_text(vendor_data)
        embedding = await embedding_service.generate_embedding(text)
        return embedding
    except Exception as e:
        logger.warning(f"Failed to generate embedding for vendor: {e}")
        return None

router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================

class PricingTier(BaseModel):
    name: str
    price: Optional[float] = None
    per: Optional[str] = "month"
    features: Optional[List[str]] = None


class VendorPricing(BaseModel):
    model: Optional[str] = None  # 'subscription', 'usage', 'hybrid', 'custom'
    currency: Optional[str] = "EUR"
    tiers: Optional[List[PricingTier]] = None
    starting_price: Optional[float] = None
    free_tier: Optional[bool] = False
    free_trial_days: Optional[int] = None
    custom_pricing: Optional[bool] = False
    startup_discount: Optional[str] = None


class VendorCreate(BaseModel):
    slug: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=2, max_length=50)
    subcategory: Optional[str] = None
    website: Optional[str] = None
    pricing_url: Optional[str] = None
    description: Optional[str] = None
    tagline: Optional[str] = None
    pricing: Optional[VendorPricing] = None
    company_sizes: Optional[List[str]] = Field(default_factory=list)
    industries: Optional[List[str]] = Field(default_factory=list)
    best_for: Optional[List[str]] = Field(default_factory=list)
    avoid_if: Optional[List[str]] = Field(default_factory=list)
    recommended_default: Optional[bool] = False
    recommended_for: Optional[List[str]] = Field(default_factory=list)
    our_rating: Optional[float] = Field(None, ge=0, le=5)
    our_notes: Optional[str] = None
    g2_score: Optional[float] = Field(None, ge=0, le=5)
    g2_reviews: Optional[int] = None
    capterra_score: Optional[float] = Field(None, ge=0, le=5)
    capterra_reviews: Optional[int] = None
    implementation_weeks: Optional[int] = None
    implementation_complexity: Optional[str] = None
    requires_developer: Optional[bool] = False
    integrations: Optional[List[str]] = Field(default_factory=list)
    api_available: Optional[bool] = False
    api_type: Optional[str] = None
    api_docs_url: Optional[str] = None
    competitors: Optional[List[str]] = Field(default_factory=list)
    key_capabilities: Optional[List[str]] = Field(default_factory=list)
    notes: Optional[str] = None


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    website: Optional[str] = None
    pricing_url: Optional[str] = None
    description: Optional[str] = None
    tagline: Optional[str] = None
    pricing: Optional[VendorPricing] = None
    company_sizes: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    best_for: Optional[List[str]] = None
    avoid_if: Optional[List[str]] = None
    recommended_default: Optional[bool] = None
    recommended_for: Optional[List[str]] = None
    our_rating: Optional[float] = Field(None, ge=0, le=5)
    our_notes: Optional[str] = None
    g2_score: Optional[float] = Field(None, ge=0, le=5)
    g2_reviews: Optional[int] = None
    capterra_score: Optional[float] = Field(None, ge=0, le=5)
    capterra_reviews: Optional[int] = None
    implementation_weeks: Optional[int] = None
    implementation_complexity: Optional[str] = None
    requires_developer: Optional[bool] = None
    integrations: Optional[List[str]] = None
    api_available: Optional[bool] = None
    api_type: Optional[str] = None
    api_docs_url: Optional[str] = None
    competitors: Optional[List[str]] = None
    key_capabilities: Optional[List[str]] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class VendorTierAssignment(BaseModel):
    tier: int = Field(..., ge=1, le=3)
    boost_score: Optional[int] = 0
    notes: Optional[str] = None


class VendorListResponse(BaseModel):
    vendors: List[dict]
    total: int
    page: int
    page_size: int
    has_more: bool


class VendorResponse(BaseModel):
    vendor: dict
    tiers: Optional[List[dict]] = None


class AuditLogResponse(BaseModel):
    entries: List[dict]
    total: int
    page: int
    page_size: int


# ============================================================================
# Vendor List & Search
# ============================================================================

@router.get("/vendors", response_model=VendorListResponse)
async def list_vendors(
    category: Optional[str] = None,
    industry: Optional[str] = None,
    status: Optional[str] = None,
    company_size: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    List all vendors with filtering and pagination.
    """
    supabase = await get_async_supabase()

    # Build query
    query = supabase.table("vendors").select("*", count="exact")

    if category:
        query = query.eq("category", category)

    if industry:
        query = query.contains("industries", [industry])

    if status:
        query = query.eq("status", status)
    else:
        # Default to active vendors
        query = query.neq("status", "deprecated")

    if company_size:
        query = query.contains("company_sizes", [company_size])

    if search:
        # Search in name, description, and tagline
        query = query.or_(
            f"name.ilike.%{search}%,description.ilike.%{search}%,tagline.ilike.%{search}%"
        )

    # Pagination
    offset = (page - 1) * page_size
    query = query.range(offset, offset + page_size - 1)

    # Order by name
    query = query.order("name")

    result = await query.execute()

    return VendorListResponse(
        vendors=result.data or [],
        total=result.count or 0,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < (result.count or 0),
    )


@router.get("/vendors/categories")
async def list_categories(
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Get all vendor categories with counts.
    """
    supabase = await get_async_supabase()

    # Get categories from reference table
    cats_result = await supabase.table("vendor_categories").select("*").order("display_order").execute()
    categories = cats_result.data or []

    # Get vendor counts per category
    vendors_result = await supabase.table("vendors").select("category").neq("status", "deprecated").execute()

    category_counts = {}
    for row in vendors_result.data or []:
        cat = row["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Merge counts into categories
    for cat in categories:
        cat["vendor_count"] = category_counts.get(cat["slug"], 0)

    return {"categories": categories}


@router.get("/vendors/industries")
async def list_industries(
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Get all supported industries.
    """
    supabase = await get_async_supabase()

    result = await supabase.table("supported_industries").select("*").order("display_order").execute()

    return {"industries": result.data or []}


@router.get("/vendors/stats")
async def get_vendor_stats(
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Get vendor database statistics.
    """
    supabase = await get_async_supabase()

    # Total vendors by status
    vendors_result = await supabase.table("vendors").select("status").execute()
    vendors = vendors_result.data or []

    status_counts = {"active": 0, "deprecated": 0, "needs_review": 0}
    for v in vendors:
        status = v.get("status", "active")
        status_counts[status] = status_counts.get(status, 0) + 1

    # Vendors by category
    category_counts = {}
    vendors_with_cat = await supabase.table("vendors").select("category").neq("status", "deprecated").execute()
    for v in vendors_with_cat.data or []:
        cat = v.get("category")
        if cat:
            category_counts[cat] = category_counts.get(cat, 0) + 1

    # Industry tier counts
    tiers_result = await supabase.table("industry_vendor_tiers").select("industry, tier").execute()
    tier_counts = {}
    for t in tiers_result.data or []:
        industry = t["industry"]
        if industry not in tier_counts:
            tier_counts[industry] = {"tier_1": 0, "tier_2": 0, "tier_3": 0}
        tier_key = f"tier_{t['tier']}"
        tier_counts[industry][tier_key] += 1

    # Stale vendors (not verified in 90+ days)
    from datetime import timedelta
    stale_cutoff = (datetime.utcnow() - timedelta(days=90)).isoformat()
    stale_result = await supabase.table("vendors").select("id", count="exact").or_(
        f"verified_at.is.null,verified_at.lt.{stale_cutoff}"
    ).eq("status", "active").execute()

    return {
        "total_vendors": len(vendors),
        "by_status": status_counts,
        "by_category": category_counts,
        "tier_assignments": tier_counts,
        "stale_vendors": stale_result.count or 0,
    }


# ============================================================================
# Vendor CRUD
# ============================================================================

@router.get("/vendors/{slug}", response_model=VendorResponse)
async def get_vendor(
    slug: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Get a single vendor by slug.
    """
    supabase = await get_async_supabase()

    result = await supabase.table("vendors").select("*").eq("slug", slug).single().execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor '{slug}' not found"
        )

    # Get tier assignments for this vendor
    vendor_id = result.data["id"]
    tiers_result = await supabase.table("industry_vendor_tiers").select(
        "industry, tier, boost_score, notes"
    ).eq("vendor_id", vendor_id).execute()

    return VendorResponse(
        vendor=result.data,
        tiers=tiers_result.data or []
    )


@router.post("/vendors")
async def create_vendor(
    vendor: VendorCreate,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Create a new vendor.
    """
    supabase = await get_async_supabase()

    # Check if slug exists
    existing = await supabase.table("vendors").select("id").eq("slug", vendor.slug).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vendor with slug '{vendor.slug}' already exists"
        )

    # Prepare data
    vendor_data = vendor.model_dump(exclude_none=True)
    if "pricing" in vendor_data and vendor_data["pricing"]:
        vendor_data["pricing"] = dict(vendor_data["pricing"])
        if "tiers" in vendor_data["pricing"]:
            vendor_data["pricing"]["tiers"] = [dict(t) for t in vendor_data["pricing"]["tiers"]]

    vendor_data["created_at"] = datetime.utcnow().isoformat()
    vendor_data["updated_at"] = datetime.utcnow().isoformat()
    vendor_data["status"] = "active"

    # Generate embedding for semantic search
    embedding = await generate_vendor_embedding(vendor_data)
    if embedding:
        vendor_data["embedding"] = embedding

    # Insert
    result = await supabase.table("vendors").insert(vendor_data).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create vendor"
        )

    created_vendor = result.data[0]

    # Log audit
    audit_changes = {k: v for k, v in vendor_data.items() if k != "embedding"}
    await supabase.table("vendor_audit_log").insert({
        "vendor_id": created_vendor["id"],
        "vendor_slug": vendor.slug,
        "action": "create",
        "changed_by": current_user.email or "admin-ui",
        "changes": {"created": audit_changes},
    }).execute()

    logger.info(f"Created vendor: {vendor.slug}" + (" (with embedding)" if embedding else ""))
    return {"vendor": created_vendor, "message": "Vendor created successfully"}


@router.put("/vendors/{slug}")
async def update_vendor(
    slug: str,
    vendor_update: VendorUpdate,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Update an existing vendor.
    """
    supabase = await get_async_supabase()

    # Get existing vendor
    existing = await supabase.table("vendors").select("*").eq("slug", slug).single().execute()
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor '{slug}' not found"
        )

    old_data = existing.data

    # Prepare update data
    update_data = vendor_update.model_dump(exclude_none=True)
    if "pricing" in update_data and update_data["pricing"]:
        update_data["pricing"] = dict(update_data["pricing"])
        if "tiers" in update_data["pricing"]:
            update_data["pricing"]["tiers"] = [dict(t) for t in update_data["pricing"]["tiers"]]

    update_data["updated_at"] = datetime.utcnow().isoformat()

    # Check if any embedding-relevant fields changed
    embedding_fields = {"name", "tagline", "description", "category", "best_for",
                       "key_capabilities", "industries", "recommended_for"}
    embedding_changed = any(field in update_data for field in embedding_fields)

    # Regenerate embedding if relevant fields changed
    embedding_updated = False
    if embedding_changed:
        # Merge old_data with update_data to get full vendor state
        merged_data = {**old_data, **update_data}
        embedding = await generate_vendor_embedding(merged_data)
        if embedding:
            update_data["embedding"] = embedding
            embedding_updated = True

    # Update
    result = await supabase.table("vendors").update(update_data).eq("slug", slug).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update vendor"
        )

    updated_vendor = result.data[0]

    # Build changes log (exclude embedding from audit)
    changes = {}
    for key, new_value in update_data.items():
        if key not in ("updated_at", "embedding"):
            old_value = old_data.get(key)
            if old_value != new_value:
                changes[key] = {"old": old_value, "new": new_value}

    # Log audit
    if changes:
        await supabase.table("vendor_audit_log").insert({
            "vendor_id": updated_vendor["id"],
            "vendor_slug": slug,
            "action": "update",
            "changed_by": current_user.email or "admin-ui",
            "changes": changes,
        }).execute()

    logger.info(f"Updated vendor: {slug}" + (" (embedding regenerated)" if embedding_updated else ""))
    return {"vendor": updated_vendor, "message": "Vendor updated successfully"}


@router.delete("/vendors/{slug}")
async def delete_vendor(
    slug: str,
    hard_delete: bool = False,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Delete a vendor (soft delete by default - sets status to 'deprecated').
    Use hard_delete=true for permanent deletion.
    """
    supabase = await get_async_supabase()

    # Get existing vendor
    existing = await supabase.table("vendors").select("*").eq("slug", slug).single().execute()
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor '{slug}' not found"
        )

    vendor_id = existing.data["id"]

    if hard_delete:
        # Permanent deletion
        await supabase.table("vendors").delete().eq("slug", slug).execute()
        action = "delete"
        message = "Vendor permanently deleted"
    else:
        # Soft delete
        await supabase.table("vendors").update({
            "status": "deprecated",
            "deprecated_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("slug", slug).execute()
        action = "deprecate"
        message = "Vendor deprecated"

    # Log audit
    await supabase.table("vendor_audit_log").insert({
        "vendor_id": vendor_id if not hard_delete else None,
        "vendor_slug": slug,
        "action": action,
        "changed_by": current_user.email or "admin-ui",
        "changes": {"previous_data": existing.data},
    }).execute()

    logger.info(f"{action.capitalize()}d vendor: {slug}")
    return {"message": message, "slug": slug}


@router.post("/vendors/{slug}/verify")
async def verify_vendor(
    slug: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Mark a vendor as verified (updates verified_at timestamp).
    """
    supabase = await get_async_supabase()

    now = datetime.utcnow().isoformat()

    result = await supabase.table("vendors").update({
        "verified_at": now,
        "verified_by": current_user.email or "admin-ui",
        "status": "active",
        "updated_at": now,
    }).eq("slug", slug).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor '{slug}' not found"
        )

    return {"message": "Vendor marked as verified", "verified_at": now}


# ============================================================================
# Industry Tier Management
# ============================================================================

@router.get("/vendors/industries/{industry}/tiers")
async def get_industry_tiers(
    industry: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Get all vendors in tiers for an industry.
    """
    supabase = await get_async_supabase()

    # Get tier assignments with vendor details
    tiers_result = await supabase.table("industry_vendor_tiers").select(
        "*, vendors(id, slug, name, category, description, our_rating)"
    ).eq("industry", industry).order("tier").order("boost_score", desc=True).execute()

    # Group by tier
    tier_groups = {1: [], 2: [], 3: []}
    for item in tiers_result.data or []:
        tier = item["tier"]
        if tier in tier_groups:
            tier_groups[tier].append({
                "vendor": item.get("vendors"),
                "tier": tier,
                "boost_score": item.get("boost_score", 0),
                "notes": item.get("notes"),
            })

    return {
        "industry": industry,
        "tier_1": tier_groups[1],
        "tier_2": tier_groups[2],
        "tier_3": tier_groups[3],
    }


@router.post("/vendors/industries/{industry}/tiers/{vendor_id}")
async def set_vendor_tier(
    industry: str,
    vendor_id: str,
    assignment: VendorTierAssignment,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Set or update a vendor's tier for an industry.
    """
    success = await vendor_service.set_vendor_tier(
        industry=industry,
        vendor_id=vendor_id,
        tier=assignment.tier,
        boost_score=assignment.boost_score or 0,
        notes=assignment.notes,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set vendor tier"
        )

    return {"message": f"Vendor set to tier {assignment.tier} for {industry}"}


@router.delete("/vendors/industries/{industry}/tiers/{vendor_id}")
async def remove_vendor_tier(
    industry: str,
    vendor_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Remove a vendor from an industry's tier list.
    """
    success = await vendor_service.remove_vendor_tier(industry, vendor_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove vendor tier"
        )

    return {"message": f"Vendor removed from {industry} tiers"}


# ============================================================================
# Audit Log
# ============================================================================

@router.get("/vendors/audit", response_model=AuditLogResponse)
async def get_audit_log(
    vendor_slug: Optional[str] = None,
    action: Optional[str] = None,
    changed_by: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Get the vendor audit log with filtering.
    """
    supabase = await get_async_supabase()

    query = supabase.table("vendor_audit_log").select("*", count="exact")

    if vendor_slug:
        query = query.eq("vendor_slug", vendor_slug)

    if action:
        query = query.eq("action", action)

    if changed_by:
        query = query.eq("changed_by", changed_by)

    # Pagination
    offset = (page - 1) * page_size
    query = query.range(offset, offset + page_size - 1)

    # Order by most recent first
    query = query.order("created_at", desc=True)

    result = await query.execute()

    return AuditLogResponse(
        entries=result.data or [],
        total=result.count or 0,
        page=page,
        page_size=page_size,
    )


# ============================================================================
# Stale Vendors
# ============================================================================

@router.get("/vendors/stale")
async def get_stale_vendors(
    days: int = Query(90, ge=1, le=365),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Get vendors that haven't been verified in a specified number of days.
    """
    supabase = await get_async_supabase()

    from datetime import timedelta
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

    query = supabase.table("vendors").select("*", count="exact").or_(
        f"verified_at.is.null,verified_at.lt.{cutoff}"
    ).eq("status", "active")

    # Pagination
    offset = (page - 1) * page_size
    query = query.range(offset, offset + page_size - 1)
    query = query.order("verified_at", nullsfirst=True)

    result = await query.execute()

    return {
        "vendors": result.data or [],
        "total": result.count or 0,
        "page": page,
        "page_size": page_size,
        "cutoff_days": days,
    }


# ============================================================================
# Semantic Search
# ============================================================================

class SemanticSearchResponse(BaseModel):
    vendors: List[dict]
    query: str
    total: int


@router.post("/vendors/semantic-search", response_model=SemanticSearchResponse)
async def semantic_search_vendors(
    query: str = Query(..., min_length=3, max_length=500, description="Natural language search query"),
    category: Optional[str] = None,
    industry: Optional[str] = None,
    company_size: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    threshold: float = Query(0.5, ge=0.0, le=1.0, description="Minimum similarity score"),
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Search vendors using semantic similarity.

    Uses vector embeddings to find vendors matching natural language descriptions.
    Example queries:
    - "AI receptionist for phone calls"
    - "CRM with good HubSpot alternative"
    - "tool for automated lead qualification"
    """
    # Generate embedding for the query
    embedding_service = await get_embedding_service()
    query_embedding = await embedding_service.generate_embedding(query)

    if not query_embedding:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding service unavailable"
        )

    supabase = await get_async_supabase()

    # Use the database semantic search function
    result = await supabase.rpc(
        "search_vendors_semantic",
        {
            "query_embedding": query_embedding,
            "match_threshold": threshold,
            "match_count": limit,
            "filter_category": category,
            "filter_industry": industry,
            "filter_company_size": company_size,
        }
    ).execute()

    vendors = result.data or []

    # Fetch full vendor details for the matched IDs
    if vendors:
        vendor_ids = [v["id"] for v in vendors]
        details_result = await supabase.table("vendors").select(
            "id, slug, name, category, description, tagline, our_rating, pricing, website"
        ).in_("id", vendor_ids).execute()

        # Create lookup and preserve similarity scores
        similarity_lookup = {v["id"]: v["similarity"] for v in vendors}
        vendor_details = []
        for v in details_result.data or []:
            v["similarity"] = similarity_lookup.get(v["id"], 0)
            vendor_details.append(v)

        # Sort by similarity
        vendor_details.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        vendors = vendor_details

    logger.info(f"Semantic search: '{query[:50]}...' returned {len(vendors)} results")

    return SemanticSearchResponse(
        vendors=vendors,
        query=query,
        total=len(vendors)
    )


@router.post("/vendors/regenerate-embeddings")
async def regenerate_all_embeddings(
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Regenerate embeddings for all active vendors.

    Use this if the embedding model changes or after bulk imports.
    """
    supabase = await get_async_supabase()

    # Get all active vendors
    result = await supabase.table("vendors").select("*").eq("status", "active").execute()
    vendors = result.data or []

    if not vendors:
        return {"message": "No active vendors found", "updated": 0}

    updated_count = 0
    failed_count = 0

    for vendor in vendors:
        embedding = await generate_vendor_embedding(vendor)
        if embedding:
            await supabase.table("vendors").update({
                "embedding": embedding
            }).eq("id", vendor["id"]).execute()
            updated_count += 1
        else:
            failed_count += 1

    logger.info(f"Regenerated embeddings: {updated_count} success, {failed_count} failed")

    return {
        "message": f"Regenerated {updated_count} embeddings",
        "updated": updated_count,
        "failed": failed_count,
        "total": len(vendors)
    }
