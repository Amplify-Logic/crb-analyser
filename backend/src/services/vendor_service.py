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

# API openness boost scores (used in automation-first recommendations)
API_OPENNESS_BOOST = {
    5: 25,  # Full API + webhooks + OAuth
    4: 15,  # Good API
    3: 5,   # Basic API
    2: 0,   # Zapier only
    1: -10, # Closed system (penalize)
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
        company_context: Optional[Dict[str, Any]] = None,
        prefer_automation: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get vendors for an industry with tier boosts applied.

        Args:
            industry: Industry slug (e.g., 'dental', 'recruiting')
            category: Optional category filter
            finding_tags: Tags from finding for recommended_for matching
            company_context: Optional dict with budget, employee_count, etc.
            prefer_automation: If True, boost vendors with high API openness scores

        Returns:
            Vendors with _tier_boost, _api_openness_boost, and _recommendation_score fields
        """
        company_context = company_context or {}
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
            budget = company_context.get("budget", "moderate")

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

                # API Openness scoring (automation-first approach)
                api_openness = vendor.get("api_openness_score")
                if prefer_automation and api_openness:
                    api_boost = API_OPENNESS_BOOST.get(api_openness, 0)
                    vendor["_api_openness_boost"] = api_boost
                    score += api_boost

                    # Extra boost for vendors with webhook + OAuth (full automation ready)
                    if vendor.get("has_webhooks") and vendor.get("has_oauth"):
                        score += 10
                    # Boost for n8n/Make/Zapier integrations
                    integration_count = sum([
                        vendor.get("n8n_integration", False),
                        vendor.get("make_integration", False),
                        vendor.get("zapier_integration", False),
                    ])
                    if integration_count >= 2:
                        score += 5
                else:
                    vendor["_api_openness_boost"] = 0

                # Budget-aware filtering
                # Penalize expensive/enterprise vendors when company has limited budget
                pricing = vendor.get("pricing") or {}
                starting_price = pricing.get("starting_price")
                is_custom_pricing = pricing.get("custom_pricing", False)

                if budget == "low":
                    # Strong penalty for enterprise/custom pricing
                    if is_custom_pricing or starting_price is None:
                        score -= 25
                    elif starting_price and starting_price > 100:
                        # Penalize vendors over $100/mo for budget-conscious
                        penalty = min(20, int((starting_price - 100) / 25) * 5)
                        score -= penalty
                elif budget == "moderate":
                    # Light penalty for custom pricing only
                    if is_custom_pricing or starting_price is None:
                        score -= 10

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

    async def get_stack_picker_options(
        self,
        industry: str,
    ) -> Dict[str, Any]:
        """
        Get software options for the existing stack picker in the quiz.

        Uses industry_vendor_tiers to show relevant, curated software options
        for a given industry, sorted by tier (T1 first).

        Args:
            industry: Industry slug (e.g., 'dental', 'home-services')

        Returns:
            Dict with:
                - industry: The industry slug
                - categories: List of unique categories
                - options_by_category: Dict mapping category -> list of options
                - total_options: Total count
        """
        supabase = await get_async_supabase()

        try:
            # Get all tier assignments for this industry with vendor details
            tiers_result = await supabase.table("industry_vendor_tiers").select(
                "vendor_id, tier"
            ).eq("industry", industry).execute()

            tier_map = {t["vendor_id"]: t["tier"] for t in (tiers_result.data or [])}

            if not tier_map:
                logger.warning(f"No tier assignments found for industry: {industry}")
                return self._get_fallback_stack_options(industry)

            # Get vendor details for all tiered vendors
            vendor_ids = list(tier_map.keys())
            vendors_result = await supabase.table("vendors").select(
                "id, slug, name, category"
            ).in_("id", vendor_ids).eq("status", "active").execute()

            vendors = vendors_result.data or []

            # Map category slugs to display names
            category_display_names = {
                "dental_practice_management": "Practice Management",
                "pt_practice_management": "Practice Management",
                "veterinary_practice_management": "Practice Management",
                "medspa_management": "Practice Management",
                "coaching_platform": "Coaching Platform",
                "accounting_practice_management": "Practice Management",
                "legal_practice_management": "Practice Management",
                "field_service_management": "Job Management",
                "recruitment_ats": "ATS",
                "recruitment_sourcing": "Sourcing",
                "recruitment_automation": "Automation",
                "patient_communication": "Patient Communication",
                "crm": "CRM",
                "customer_support": "Customer Support",
                "marketing_automation": "Email Marketing",
                "finance": "Accounting",
                "project_management": "Project Management",
                "automation": "Automation",
                "scheduling": "Scheduling",
                "ai_assistants": "AI Assistants",
                "ai_receptionist": "AI Receptionist",
            }

            # Group by display category and sort by tier
            options_by_category: Dict[str, List[Dict[str, Any]]] = {}

            for vendor in vendors:
                tier = tier_map.get(vendor["id"], 3)
                raw_category = vendor.get("category", "Other")
                display_category = category_display_names.get(raw_category, raw_category.replace("_", " ").title())

                option = {
                    "slug": vendor["slug"],
                    "name": vendor["name"],
                    "category": display_category,
                    "_tier": tier,
                }

                if display_category not in options_by_category:
                    options_by_category[display_category] = []
                options_by_category[display_category].append(option)

            # Sort each category by tier (T1 first)
            for category in options_by_category:
                options_by_category[category].sort(key=lambda x: x.get("_tier", 3))
                # Remove internal tier field from response
                for opt in options_by_category[category]:
                    opt.pop("_tier", None)

            # Add cross-industry tools
            cross_industry = await self._get_cross_industry_options()
            for opt in cross_industry:
                cat = opt["category"]
                if cat not in options_by_category:
                    options_by_category[cat] = []
                # Avoid duplicates
                if not any(o["slug"] == opt["slug"] for o in options_by_category[cat]):
                    options_by_category[cat].append(opt)

            # Sort categories: industry-specific first, then cross-industry
            industry_categories = [
                "Practice Management", "Job Management", "ATS", "Sourcing",
                "Patient Communication", "Coaching Platform",
            ]
            cross_categories = [
                "CRM", "Accounting", "Email Marketing", "Customer Support",
                "Communication", "Project Management", "Scheduling",
            ]

            sorted_categories = []
            for cat in industry_categories:
                if cat in options_by_category:
                    sorted_categories.append(cat)
            for cat in cross_categories:
                if cat in options_by_category and cat not in sorted_categories:
                    sorted_categories.append(cat)
            for cat in options_by_category:
                if cat not in sorted_categories:
                    sorted_categories.append(cat)

            total = sum(len(opts) for opts in options_by_category.values())

            return {
                "industry": industry,
                "categories": sorted_categories,
                "options_by_category": options_by_category,
                "total_options": total,
            }

        except Exception as e:
            logger.error(f"Failed to get stack picker options for {industry}: {e}")
            return self._get_fallback_stack_options(industry)

    async def _get_cross_industry_options(self) -> List[Dict[str, str]]:
        """Get cross-industry software options (CRM, accounting, etc.)."""
        supabase = await get_async_supabase()

        # Popular cross-industry tools that most businesses use
        cross_industry_slugs = [
            # CRM
            "hubspot", "salesforce", "pipedrive", "zoho-crm",
            # Accounting
            "quickbooks", "xero", "freshbooks", "wave",
            # Communication
            "slack", "microsoft-teams", "zoom", "google-meet",
            # Email Marketing
            "mailchimp", "klaviyo", "activecampaign", "brevo",
            # Customer Support
            "zendesk", "intercom", "freshdesk", "help-scout",
            # Project Management
            "asana", "monday-com", "trello", "notion", "clickup",
            # Scheduling
            "calendly", "acuity-scheduling", "cal-com",
        ]

        try:
            result = await supabase.table("vendors").select(
                "slug, name, category"
            ).in_("slug", cross_industry_slugs).eq("status", "active").execute()

            category_map = {
                "crm": "CRM",
                "finance": "Accounting",
                "marketing_automation": "Email Marketing",
                "customer_support": "Customer Support",
                "project_management": "Project Management",
                "scheduling": "Scheduling",
            }

            options = []
            for v in (result.data or []):
                raw_cat = v.get("category", "Other")
                display_cat = category_map.get(raw_cat, raw_cat.replace("_", " ").title())

                # Add Communication category for known tools
                if v["slug"] in ["slack", "microsoft-teams", "zoom", "google-meet"]:
                    display_cat = "Communication"

                options.append({
                    "slug": v["slug"],
                    "name": v["name"],
                    "category": display_cat,
                })

            return options

        except Exception as e:
            logger.warning(f"Failed to get cross-industry options: {e}")
            return []

    def _get_fallback_stack_options(self, industry: str) -> Dict[str, Any]:
        """Fallback to hardcoded options if Supabase query fails."""
        from src.config.existing_stack import get_software_options_grouped, get_all_categories

        grouped = get_software_options_grouped(industry)
        categories = get_all_categories(industry)
        total = sum(len(opts) for opts in grouped.values())

        return {
            "industry": industry,
            "categories": categories,
            "options_by_category": grouped,
            "total_options": total,
            "_fallback": True,
        }

    async def get_automation_ready_vendors(
        self,
        category: Optional[str] = None,
        min_openness_score: int = 4,
        require_webhooks: bool = False,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get vendors that are automation-ready (high API openness).

        This is the automation-first approach: find vendors that can be
        integrated with n8n, Make, Zapier, or custom Claude Code scripts.

        Args:
            category: Optional category filter
            min_openness_score: Minimum API openness score (1-5, default 4)
            require_webhooks: Only return vendors with webhook support
            limit: Max results

        Returns:
            Vendors sorted by API capabilities
        """
        supabase = await get_async_supabase()

        try:
            query = supabase.table("vendors").select("*").eq("status", "active")

            if category:
                query = query.eq("category", category)

            # Filter by API openness
            query = query.gte("api_openness_score", min_openness_score)

            if require_webhooks:
                query = query.eq("has_webhooks", True)

            query = query.order("api_openness_score", desc=True).limit(limit)

            result = await query.execute()
            vendors = result.data or []

            # Add automation compatibility info
            for vendor in vendors:
                vendor["_automation_ready"] = True
                vendor["_integration_platforms"] = []
                if vendor.get("n8n_integration"):
                    vendor["_integration_platforms"].append("n8n")
                if vendor.get("make_integration"):
                    vendor["_integration_platforms"].append("Make")
                if vendor.get("zapier_integration"):
                    vendor["_integration_platforms"].append("Zapier")

            return vendors

        except Exception as e:
            logger.error(f"Failed to get automation-ready vendors: {e}")
            return []

    async def get_vendors_needing_api_audit(
        self,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get vendors that don't have API openness scores yet.

        Use this to identify vendors that need their API capabilities documented.
        """
        supabase = await get_async_supabase()

        try:
            result = await supabase.table("vendors").select(
                "id, slug, name, category, website, api_available, api_docs_url"
            ).eq("status", "active").is_("api_openness_score", "null").limit(
                limit
            ).execute()

            return result.data or []

        except Exception as e:
            logger.error(f"Failed to get vendors needing API audit: {e}")
            return []

    async def update_vendor_api_info(
        self,
        slug: str,
        api_openness_score: int,
        has_webhooks: bool = False,
        has_oauth: bool = False,
        zapier_integration: bool = False,
        make_integration: bool = False,
        n8n_integration: bool = False,
        api_rate_limits: Optional[str] = None,
        custom_tool_examples: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Update a vendor's API and integration information.

        Args:
            slug: Vendor slug
            api_openness_score: API openness rating (1-5)
            has_webhooks: Supports webhooks
            has_oauth: Supports OAuth
            zapier_integration: Has Zapier integration
            make_integration: Has Make integration
            n8n_integration: Has n8n integration
            api_rate_limits: Rate limit info (e.g., "1000/min")
            custom_tool_examples: Examples of automations possible

        Returns:
            Updated vendor data or None
        """
        supabase = await get_async_supabase()

        update_data = {
            "api_openness_score": api_openness_score,
            "has_webhooks": has_webhooks,
            "has_oauth": has_oauth,
            "zapier_integration": zapier_integration,
            "make_integration": make_integration,
            "n8n_integration": n8n_integration,
            "updated_at": datetime.utcnow().isoformat(),
        }

        if api_rate_limits:
            update_data["api_rate_limits"] = api_rate_limits

        if custom_tool_examples:
            update_data["custom_tool_examples"] = custom_tool_examples

        try:
            result = await supabase.table("vendors").update(update_data).eq(
                "slug", slug
            ).execute()

            if result.data:
                logger.info(
                    f"Updated API info for {slug}: score={api_openness_score}"
                )
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Failed to update vendor API info for {slug}: {e}")
            return None

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
