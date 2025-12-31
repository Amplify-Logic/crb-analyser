"""
Vendor Service

Core vendor database operations with industry tier boost support.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from src.config.supabase_client import get_async_supabase
from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# Industry tier boost scores
TIER_BOOST = {
    1: 30,  # Top pick
    2: 20,  # Recommended
    3: 10,  # Alternative
}


class VendorService:
    """Service for vendor CRUD and query operations."""

    async def list_vendors(
        self,
        category: Optional[str] = None,
        industry: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        List vendors with filtering and pagination.
        """
        supabase = await get_async_supabase()

        # Build query
        query = supabase.table("vendors").select("*", count="exact")

        if category:
            query = query.eq("category", category)

        if industry:
            query = query.contains("industries", [industry])

        if search:
            query = query.or_(f"name.ilike.%{search}%,description.ilike.%{search}%")

        # Pagination
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)

        # Order by name
        query = query.order("name")

        result = await query.execute()

        total = result.count or 0
        vendors = result.data or []

        return {
            "vendors": vendors,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": (page * page_size) < total,
        }

    async def get_vendor(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get a vendor by slug."""
        supabase = await get_async_supabase()

        result = await supabase.table("vendors").select("*").eq(
            "slug", slug
        ).single().execute()

        return result.data if result.data else None

    async def get_vendor_by_id(self, vendor_id: str) -> Optional[Dict[str, Any]]:
        """Get a vendor by ID."""
        supabase = await get_async_supabase()

        result = await supabase.table("vendors").select("*").eq(
            "id", vendor_id
        ).single().execute()

        return result.data if result.data else None

    async def create_vendor(self, vendor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new vendor."""
        supabase = await get_async_supabase()

        vendor_data["created_at"] = datetime.utcnow().isoformat()
        vendor_data["updated_at"] = datetime.utcnow().isoformat()

        result = await supabase.table("vendors").insert(vendor_data).execute()

        logger.info(f"Created vendor: {vendor_data.get('slug')}")
        return result.data[0]

    async def update_vendor(
        self, slug: str, update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an existing vendor."""
        supabase = await get_async_supabase()

        update_data["updated_at"] = datetime.utcnow().isoformat()

        result = await supabase.table("vendors").update(update_data).eq(
            "slug", slug
        ).execute()

        if result.data:
            logger.info(f"Updated vendor: {slug}")
            return result.data[0]
        return None

    async def delete_vendor(self, slug: str) -> bool:
        """Delete a vendor."""
        supabase = await get_async_supabase()

        result = await supabase.table("vendors").delete().eq(
            "slug", slug
        ).execute()

        if result.data:
            logger.info(f"Deleted vendor: {slug}")
            return True
        return False

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all vendor categories with counts."""
        supabase = await get_async_supabase()

        # Get distinct categories with counts
        result = await supabase.table("vendors").select("category").execute()

        if not result.data:
            return []

        # Count vendors per category
        category_counts = {}
        for row in result.data:
            cat = row["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return [
            {"category": cat, "vendor_count": count}
            for cat, count in sorted(category_counts.items())
        ]

    async def compare_vendors(self, vendor_ids: List[str]) -> Dict[str, Any]:
        """
        Compare multiple vendors side by side.

        Returns vendors and a comparison matrix.
        """
        supabase = await get_async_supabase()

        # Get vendors by ID or slug
        result = await supabase.table("vendors").select("*").in_(
            "id", vendor_ids
        ).execute()

        vendors = result.data or []

        # If no results, try by slug
        if not vendors:
            result = await supabase.table("vendors").select("*").in_(
                "slug", vendor_ids
            ).execute()
            vendors = result.data or []

        if not vendors:
            return {"vendors": [], "comparison": {}}

        # Build comparison matrix
        comparison = {
            "pricing": [],
            "features": [],
            "ratings": [],
            "implementation": [],
        }

        for vendor in vendors:
            pricing = vendor.get("pricing", {})

            # Pricing comparison
            comparison["pricing"].append({
                "vendor": vendor["name"],
                "model": pricing.get("model", "unknown"),
                "starting_price": self._get_starting_price(pricing),
                "free_trial": pricing.get("free_trial_days"),
            })

            # Ratings comparison
            comparison["ratings"].append({
                "vendor": vendor["name"],
                "g2": vendor.get("g2_rating"),
                "capterra": vendor.get("capterra_rating"),
                "our_rating": vendor.get("our_rating"),
            })

            # Implementation comparison
            comparison["implementation"].append({
                "vendor": vendor["name"],
                "weeks": vendor.get("avg_implementation_weeks"),
                "cost_range": vendor.get("implementation_cost_range"),
                "requires_developer": vendor.get("requires_developer", False),
            })

            # Features comparison
            comparison["features"].append({
                "vendor": vendor["name"],
                "best_for": vendor.get("best_for", []),
                "avoid_if": vendor.get("avoid_if", []),
                "api_available": vendor.get("api_available", True),
            })

        return {
            "vendors": vendors,
            "comparison": comparison,
        }

    def _get_starting_price(self, pricing: Dict[str, Any]) -> Optional[str]:
        """Extract starting price from pricing data."""
        tiers = pricing.get("tiers", [])
        if not tiers:
            return None

        # Find lowest non-zero price
        for tier in tiers:
            price = tier.get("price", 0)
            if price > 0:
                per = tier.get("per", "month")
                currency = pricing.get("currency", "EUR")
                return f"{currency} {price}/{per}"

        return "Free tier available"

    async def get_vendors_needing_refresh(
        self,
        older_than_days: int = 7,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get vendors that need pricing refresh."""
        supabase = await get_async_supabase()

        from datetime import timedelta

        cutoff = (datetime.utcnow() - timedelta(days=older_than_days)).isoformat()

        result = await supabase.table("vendors").select("*").eq(
            "auto_refresh_enabled", True
        ).or_(
            f"pricing_verified_at.is.null,pricing_verified_at.lt.{cutoff}"
        ).limit(limit).execute()

        return result.data or []

    async def update_vendor_pricing(
        self,
        vendor_id: str,
        new_pricing: Dict[str, Any],
        source: Optional[str] = None,
    ) -> bool:
        """Update vendor pricing and log history."""
        supabase = await get_async_supabase()

        now = datetime.utcnow().isoformat()

        # Update vendor
        await supabase.table("vendors").update({
            "pricing": new_pricing,
            "pricing_verified_at": now,
            "pricing_source": source,
            "updated_at": now,
        }).eq("id", vendor_id).execute()

        # Log to pricing history
        await supabase.table("vendor_pricing_history").insert({
            "vendor_id": vendor_id,
            "pricing": new_pricing,
            "captured_at": now,
            "source": source,
        }).execute()

        logger.info(f"Updated pricing for vendor {vendor_id}")
        return True

    async def mark_refresh_error(self, vendor_id: str, error: str) -> None:
        """Mark a vendor refresh as failed."""
        supabase = await get_async_supabase()

        await supabase.table("vendors").update({
            "last_refresh_attempt": datetime.utcnow().isoformat(),
            "refresh_error": error,
        }).eq("id", vendor_id).execute()

    # =========================================================================
    # INDUSTRY TIER METHODS
    # =========================================================================

    async def get_vendors_with_tier_boost(
        self,
        industry: str,
        category: Optional[str] = None,
        finding_tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get vendors for an industry with tier boosts applied.

        Args:
            industry: Industry slug (e.g., 'dental', 'recruiting')
            category: Optional category filter
            finding_tags: Tags from finding for recommended_for matching

        Returns:
            Vendors with _tier_boost and _recommendation_score fields
        """
        settings = get_settings()

        if not settings.USE_SUPABASE_VENDORS:
            return self._get_vendors_from_json_with_boost(industry, category, finding_tags)

        supabase = await get_async_supabase()

        try:
            # Query vendors that include this industry
            query = supabase.table("vendors").select("*").eq("status", "active")

            if category:
                query = query.eq("category", category)

            # Filter by industry array (contains)
            query = query.contains("industries", [industry])

            result = await query.execute()
            vendors = result.data or []

            # Apply tier boosts
            vendors = await self._apply_industry_boosts(vendors, industry)

            # Calculate recommendation scores
            for vendor in vendors:
                score = vendor.get("_tier_boost", 0)

                # Boost for recommended_default
                if vendor.get("recommended_default"):
                    score += 25

                # Boost for matching recommended_for tags
                if finding_tags:
                    recommended_for = vendor.get("recommended_for", [])
                    for tag in finding_tags:
                        tag_normalized = tag.lower().replace(" ", "_")
                        if tag_normalized in recommended_for or tag in recommended_for:
                            score += 10
                            break

                vendor["_recommendation_score"] = score

            # Sort by recommendation score
            vendors.sort(key=lambda v: v.get("_recommendation_score", 0), reverse=True)

            return vendors

        except Exception as e:
            logger.error(f"Failed to get vendors with tier boost for {industry}: {e}")
            return self._get_vendors_from_json_with_boost(industry, category, finding_tags)

    async def _apply_industry_boosts(
        self,
        vendors: List[Dict[str, Any]],
        industry: str,
    ) -> List[Dict[str, Any]]:
        """Apply industry tier boosts to vendors."""
        if not vendors:
            return vendors

        supabase = await get_async_supabase()

        try:
            # Get industry tiers for all vendor IDs
            vendor_ids = [v.get("id") for v in vendors if v.get("id")]

            tiers_result = await supabase.table("industry_vendor_tiers").select(
                "vendor_id, tier, boost_score"
            ).eq("industry", industry).in_("vendor_id", vendor_ids).execute()

            tiers_by_vendor = {
                t["vendor_id"]: t for t in (tiers_result.data or [])
            }

            # Apply boosts
            for vendor in vendors:
                vendor_id = vendor.get("id")
                tier_info = tiers_by_vendor.get(vendor_id)

                if tier_info:
                    tier = tier_info.get("tier", 3)
                    custom_boost = tier_info.get("boost_score", 0)
                    vendor["_tier"] = tier
                    vendor["_tier_boost"] = TIER_BOOST.get(tier, 0) + custom_boost
                else:
                    vendor["_tier"] = None
                    vendor["_tier_boost"] = 0

            return vendors

        except Exception as e:
            logger.warning(f"Failed to apply industry boosts: {e}")
            for vendor in vendors:
                vendor["_tier"] = None
                vendor["_tier_boost"] = 0
            return vendors

    async def get_tier_vendors(
        self,
        industry: str,
        tier: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Get vendors in a specific tier for an industry.

        Args:
            industry: Industry slug
            tier: Tier level (1, 2, or 3)

        Returns:
            Vendors in that tier
        """
        supabase = await get_async_supabase()

        try:
            # Get tiers for this industry
            tiers_result = await supabase.table("industry_vendor_tiers").select(
                "vendor_id, tier, boost_score"
            ).eq("industry", industry).eq("tier", tier).execute()

            if not tiers_result.data:
                return []

            vendor_ids = [t["vendor_id"] for t in tiers_result.data]

            # Get the actual vendors
            vendors_result = await supabase.table("vendors").select(
                "*"
            ).in_("id", vendor_ids).eq("status", "active").execute()

            return vendors_result.data or []

        except Exception as e:
            logger.error(f"Failed to get tier {tier} vendors for {industry}: {e}")
            return []

    async def set_vendor_tier(
        self,
        industry: str,
        vendor_id: str,
        tier: int,
        boost_score: int = 0,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Set or update a vendor's tier for an industry.

        Args:
            industry: Industry slug
            vendor_id: Vendor UUID
            tier: Tier level (1, 2, or 3)
            boost_score: Additional boost score
            notes: Optional notes

        Returns:
            True if successful
        """
        supabase = await get_async_supabase()

        try:
            # Upsert the tier assignment
            await supabase.table("industry_vendor_tiers").upsert({
                "industry": industry,
                "vendor_id": vendor_id,
                "tier": tier,
                "boost_score": boost_score,
                "notes": notes,
                "updated_at": datetime.utcnow().isoformat(),
            }).execute()

            logger.info(f"Set vendor {vendor_id} to tier {tier} for {industry}")
            return True

        except Exception as e:
            logger.error(f"Failed to set vendor tier: {e}")
            return False

    async def remove_vendor_tier(self, industry: str, vendor_id: str) -> bool:
        """Remove a vendor from an industry's tier list."""
        supabase = await get_async_supabase()

        try:
            await supabase.table("industry_vendor_tiers").delete().eq(
                "industry", industry
            ).eq("vendor_id", vendor_id).execute()

            logger.info(f"Removed vendor {vendor_id} from {industry} tiers")
            return True

        except Exception as e:
            logger.error(f"Failed to remove vendor tier: {e}")
            return False

    def _get_vendors_from_json_with_boost(
        self,
        industry: str,
        category: Optional[str],
        finding_tags: Optional[List[str]],
    ) -> List[Dict[str, Any]]:
        """Fallback to JSON knowledge base with scoring."""
        from src.knowledge import get_vendor_recommendations, get_all_vendors

        # Get vendors
        if industry:
            vendors = get_vendor_recommendations(industry, category)
            if not vendors:
                vendors = get_all_vendors([category] if category else None)
        else:
            vendors = get_all_vendors([category] if category else None)

        # Apply scoring (no tier boosts in JSON mode)
        for vendor in vendors:
            score = 0

            if vendor.get("recommended_default"):
                score += 25

            if finding_tags:
                recommended_for = vendor.get("recommended_for", [])
                for tag in finding_tags:
                    tag_normalized = tag.lower().replace(" ", "_")
                    if tag_normalized in recommended_for or tag in recommended_for:
                        score += 10
                        break

            vendor["_tier"] = None
            vendor["_tier_boost"] = 0
            vendor["_recommendation_score"] = score

        vendors.sort(key=lambda v: v.get("_recommendation_score", 0), reverse=True)
        return vendors


# Singleton instance
vendor_service = VendorService()


# =============================================================================
# FILE-BASED KNOWLEDGE FUNCTIONS (JSON vendor data)
# =============================================================================

from src.knowledge import (
    get_all_vendors as kb_get_all_vendors,
    get_vendor_by_slug as kb_get_vendor_by_slug,
    search_vendors as kb_search_vendors,
    compare_vendors as kb_compare_vendors,
    load_vendor_category,
    list_vendor_categories,
    get_llm_providers,
    get_llm_provider,
    estimate_llm_cost,
    get_freshness_status,
)


def search_vendors_kb(
    query: str = None,
    category: str = None,
    company_size: str = None,
    max_price: float = None,
    has_free_tier: bool = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """
    Search vendors from JSON knowledge base with filters.

    Args:
        query: Search term
        category: Filter by category
        company_size: Filter by company size
        max_price: Maximum starting price
        has_free_tier: Filter by free tier availability
        limit: Maximum results to return

    Returns:
        Dict with vendors list and metadata
    """
    vendors = kb_search_vendors(
        query=query,
        category=category,
        company_size=company_size,
        max_price=max_price,
        has_free_tier=has_free_tier,
    )

    # Apply limit
    vendors = vendors[:limit]

    # Add freshness status to each vendor
    for vendor in vendors:
        verified_at = vendor.get("verified_at")
        if verified_at:
            vendor["freshness_status"] = get_freshness_status(verified_at)

    return {
        "vendors": vendors,
        "total": len(vendors),
        "filters_applied": {
            "query": query,
            "category": category,
            "company_size": company_size,
            "max_price": max_price,
            "has_free_tier": has_free_tier,
        },
    }


def get_vendor_kb(slug: str) -> Optional[Dict[str, Any]]:
    """
    Get a vendor by slug from JSON knowledge base.

    Args:
        slug: Vendor slug

    Returns:
        Vendor data with freshness status, or None
    """
    vendor = kb_get_vendor_by_slug(slug)
    if vendor:
        verified_at = vendor.get("verified_at")
        if verified_at:
            vendor["freshness_status"] = get_freshness_status(verified_at)
    return vendor


def compare_vendors_kb(slugs: List[str]) -> Dict[str, Any]:
    """
    Compare multiple vendors side-by-side from JSON knowledge base.

    Args:
        slugs: List of vendor slugs to compare

    Returns:
        Comparison data with vendors and summary
    """
    result = kb_compare_vendors(slugs)

    if result["vendors"]:
        vendors = result["vendors"]

        # Determine best for different scenarios
        result["recommendations"] = {
            "best_value": _find_best_value(vendors),
            "best_for_startup": _find_best_for_size(vendors, "startup"),
            "best_for_enterprise": _find_best_for_size(vendors, "enterprise"),
            "has_free_option": [
                v["slug"] for v in vendors
                if v.get("pricing", {}).get("free_tier", False)
            ],
        }

    return result


def _find_best_value(vendors: List[Dict]) -> Optional[str]:
    """Find the best value vendor (lowest starting price with good ratings)."""
    scored = []
    for v in vendors:
        price = v.get("pricing", {}).get("starting_price", float("inf"))
        rating = v.get("ratings", {}).get("our_rating", 0) or 0
        if price and price < float("inf"):
            value_score = rating / (price + 1)
            scored.append((v["slug"], value_score))

    if scored:
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0]
    return None


def _find_best_for_size(vendors: List[Dict], size: str) -> Optional[str]:
    """Find the best vendor for a given company size."""
    for v in vendors:
        if size in v.get("company_sizes", []):
            return v["slug"]
    return None


def get_vendors_for_use_case(
    use_case: str,
    budget_monthly: float = None,
    company_size: str = None,
    prefer_free: bool = False,
    limit: int = 5,
) -> Dict[str, Any]:
    """
    Get vendor recommendations for a specific use case.

    Args:
        use_case: Description of what the vendor is needed for
        budget_monthly: Maximum monthly budget
        company_size: Company size category
        prefer_free: Prefer vendors with free tiers
        limit: Maximum recommendations

    Returns:
        Recommended vendors with reasoning
    """
    # Map use cases to categories
    use_case_mapping = {
        "crm": ["crm"],
        "customer relationship": ["crm"],
        "sales": ["crm"],
        "support": ["customer_support"],
        "helpdesk": ["customer_support"],
        "customer service": ["customer_support"],
        "automation": ["automation"],
        "workflow": ["automation", "project_management"],
        "integration": ["automation"],
        "analytics": ["analytics"],
        "product analytics": ["analytics"],
        "tracking": ["analytics"],
        "project": ["project_management"],
        "task management": ["project_management"],
        "email": ["marketing"],
        "marketing": ["marketing"],
        "email marketing": ["marketing"],
        "ecommerce": ["ecommerce"],
        "online store": ["ecommerce"],
        "shop": ["ecommerce"],
        "accounting": ["finance"],
        "invoicing": ["finance"],
        "bookkeeping": ["finance"],
        "payroll": ["hr_payroll"],
        "hr": ["hr_payroll"],
        "hiring": ["hr_payroll"],
        "development": ["dev_tools"],
        "deployment": ["dev_tools"],
        "hosting": ["dev_tools"],
        "ai": ["ai_assistants"],
        "chatbot": ["ai_assistants", "customer_support"],
    }

    # Find matching categories
    use_case_lower = use_case.lower()
    categories = []
    for keyword, cats in use_case_mapping.items():
        if keyword in use_case_lower:
            categories.extend(cats)
    categories = list(set(categories)) or None

    # Search with filters
    vendors = kb_search_vendors(
        query=use_case,
        category=categories[0] if categories and len(categories) == 1 else None,
        company_size=company_size,
        max_price=budget_monthly,
        has_free_tier=True if prefer_free else None,
    )

    # Score and rank
    scored_vendors = []
    for v in vendors:
        score = 0

        # Rating score
        rating = v.get("ratings", {}).get("our_rating", 0) or 0
        score += rating * 10

        # Free tier bonus
        if prefer_free and v.get("pricing", {}).get("free_tier"):
            score += 20

        # Company size match
        if company_size and company_size in v.get("company_sizes", []):
            score += 15

        # Use case match in best_for
        best_for = " ".join(v.get("best_for", [])).lower()
        if use_case_lower in best_for:
            score += 25

        scored_vendors.append((v, score))

    # Sort by score and take top N
    scored_vendors.sort(key=lambda x: x[1], reverse=True)
    top_vendors = [v for v, _ in scored_vendors[:limit]]

    return {
        "use_case": use_case,
        "recommendations": top_vendors,
        "total_matches": len(vendors),
        "filters": {
            "budget": budget_monthly,
            "company_size": company_size,
            "prefer_free": prefer_free,
        },
    }


def get_category_overview(category: str) -> Dict[str, Any]:
    """
    Get an overview of vendors in a category from JSON knowledge base.

    Args:
        category: Vendor category slug

    Returns:
        Category overview with vendor summary
    """
    data = load_vendor_category(category)
    if not data:
        return {"error": f"Category '{category}' not found"}

    vendors = data.get("vendors", [])

    # Calculate stats
    prices = [
        v.get("pricing", {}).get("starting_price")
        for v in vendors
        if v.get("pricing", {}).get("starting_price")
    ]

    free_vendors = [
        v["name"] for v in vendors
        if v.get("pricing", {}).get("free_tier")
    ]

    return {
        "category": category,
        "description": data.get("description", ""),
        "vendor_count": len(vendors),
        "price_range": {
            "min": min(prices) if prices else None,
            "max": max(prices) if prices else None,
            "avg": round(sum(prices) / len(prices), 2) if prices else None,
        },
        "free_options": free_vendors,
        "vendors": [
            {
                "slug": v["slug"],
                "name": v["name"],
                "starting_price": v.get("pricing", {}).get("starting_price"),
                "free_tier": v.get("pricing", {}).get("free_tier", False),
            }
            for v in vendors
        ],
    }


def get_llm_recommendation(
    use_case: str,
    monthly_volume: str = "medium",
    priority: str = "balanced",
) -> Dict[str, Any]:
    """
    Get LLM recommendation for a use case.

    Args:
        use_case: What the LLM will be used for
        monthly_volume: 'low', 'medium', 'high'
        priority: 'cost', 'quality', 'speed', 'balanced'

    Returns:
        Recommended models with cost estimates
    """
    providers = get_llm_providers()

    volume_estimates = {
        "low": {"input": 100_000, "output": 50_000},
        "medium": {"input": 1_000_000, "output": 500_000},
        "high": {"input": 10_000_000, "output": 5_000_000},
    }

    tokens = volume_estimates.get(monthly_volume, volume_estimates["medium"])

    recommendations = []

    for provider in providers:
        for model in provider.get("models", []):
            pricing = model.get("pricing", {})
            monthly_cost = (
                (tokens["input"] / 1_000_000) * pricing.get("input_per_1m", 0) +
                (tokens["output"] / 1_000_000) * pricing.get("output_per_1m", 0)
            )

            # Score based on priority
            score = 0
            quality = model.get("quality", "")
            speed = model.get("speed", "")

            if priority == "cost":
                score = 1000 / (monthly_cost + 1)
            elif priority == "quality":
                quality_scores = {"highest": 100, "very_high": 80, "high": 60, "good": 40}
                score = quality_scores.get(quality, 0)
            elif priority == "speed":
                speed_scores = {"fastest": 100, "fast": 80, "medium": 60, "slower": 40, "slowest": 20}
                score = speed_scores.get(speed, 0)
            else:  # balanced
                quality_scores = {"highest": 100, "very_high": 80, "high": 60, "good": 40}
                speed_scores = {"fastest": 100, "fast": 80, "medium": 60, "slower": 40, "slowest": 20}
                q_score = quality_scores.get(quality, 0)
                s_score = speed_scores.get(speed, 0)
                cost_score = 100 / (monthly_cost / 100 + 1)
                score = (q_score + s_score + cost_score) / 3

            recommendations.append({
                "provider": provider["slug"],
                "model": model["name"],
                "model_id": model["model_id"],
                "monthly_cost_estimate": round(monthly_cost, 2),
                "quality": quality,
                "speed": speed,
                "context_window": model.get("context_window"),
                "score": round(score, 2),
            })

    # Sort by score
    recommendations.sort(key=lambda x: x["score"], reverse=True)

    return {
        "use_case": use_case,
        "volume": monthly_volume,
        "priority": priority,
        "estimated_tokens": tokens,
        "recommendations": recommendations[:5],
        "all_options": recommendations,
    }


def get_knowledge_stats() -> Dict[str, Any]:
    """Get statistics about the JSON-based knowledge base."""
    vendors = kb_get_all_vendors()
    llm_providers = get_llm_providers()
    categories = list_vendor_categories()

    # Count vendors per category
    category_counts = {}
    for cat in categories:
        data = load_vendor_category(cat)
        if data:
            category_counts[cat] = len(data.get("vendors", []))

    # Count models
    model_count = sum(len(p.get("models", [])) for p in llm_providers)

    return {
        "total_vendors": len(vendors),
        "vendor_categories": len(categories),
        "vendors_per_category": category_counts,
        "llm_providers": len(llm_providers),
        "llm_models": model_count,
    }
