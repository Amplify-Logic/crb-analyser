"""
Vendor Matching Skill

Matches findings to specific vendors from the knowledge base.

This skill:
1. Takes a finding and company context
2. Searches vendor database for relevant solutions
3. Scores and ranks vendors by fit
4. Returns top matches for each option tier

Output Schema:
{
    "finding_id": "finding-001",
    "category": "scheduling",
    "off_the_shelf": {
        "vendor": "Calendly",
        "slug": "calendly",
        "monthly_cost": 12,
        "implementation_cost": 0,
        "implementation_weeks": 1,
        "fit_score": 92,
        "fit_reasons": ["Easy setup", "Good for SMB"],
        "pricing_tier": "Professional",
        "key_features": [...],
        "limitations": [...]
    },
    "best_in_class": {
        "vendor": "Acuity Scheduling",
        "slug": "acuity",
        "monthly_cost": 25,
        "implementation_cost": 500,
        "implementation_weeks": 2,
        "fit_score": 88,
        "fit_reasons": ["Advanced features", "Better integrations"],
        "pricing_tier": "Growing",
        "key_features": [...],
        "limitations": [...]
    },
    "alternatives": [
        {"vendor": "...", "slug": "...", "fit_score": 85}
    ],
    "match_confidence": "high",
    "match_reasoning": "..."
}
"""

import logging
from typing import Dict, Any, List, Optional

from src.skills.base import LLMSkill, SkillContext, SkillError
from src.knowledge import (
    get_vendor_recommendations,
    get_vendor_by_slug,
    load_vendor_category,
    normalize_industry,
    VENDOR_CATEGORIES,
)

logger = logging.getLogger(__name__)

# Keywords to category mapping for finding classification
CATEGORY_KEYWORDS = {
    "automation": [
        "workflow", "automation", "integrate", "integration", "connect",
        "automate", "sync", "synchronize", "trigger", "zap", "n8n", "make"
    ],
    "crm": [
        "crm", "customer relationship", "sales", "lead", "pipeline",
        "contact", "opportunity", "deal", "salesforce", "hubspot"
    ],
    "customer_support": [
        "support", "helpdesk", "ticket", "customer service", "chat",
        "chatbot", "intercom", "zendesk", "freshdesk", "help desk"
    ],
    "scheduling": [
        "schedule", "scheduling", "appointment", "booking", "calendar",
        "calendly", "acuity", "book", "availability"
    ],
    "project_management": [
        "project", "task", "kanban", "sprint", "agile", "trello",
        "asana", "jira", "monday", "notion", "clickup"
    ],
    "finance": [
        "invoice", "invoicing", "accounting", "payment", "billing",
        "expense", "quickbooks", "xero", "freshbooks", "stripe"
    ],
    "hr_payroll": [
        "hr", "payroll", "employee", "hiring", "recruitment", "onboarding",
        "gusto", "rippling", "bamboo", "workday"
    ],
    "marketing": [
        "marketing", "email", "campaign", "newsletter", "mailchimp",
        "hubspot", "seo", "ads", "social media", "content"
    ],
    "analytics": [
        "analytics", "reporting", "dashboard", "metrics", "data",
        "looker", "tableau", "power bi", "google analytics"
    ],
    "ai_assistants": [
        "ai", "chatbot", "assistant", "copilot", "gpt", "claude",
        "automation", "intelligent", "smart"
    ],
}

# Company size mapping
SIZE_MAPPING = {
    "1-10": "startup",
    "11-50": "smb",
    "51-200": "mid-market",
    "201-500": "mid-market",
    "500+": "enterprise",
}


class VendorMatchingSkill(LLMSkill[Dict[str, Any]]):
    """
    Match findings to specific vendors from the knowledge base.

    Uses rule-based category detection with LLM fallback for
    nuanced matching. Scores vendors based on company fit.
    """

    name = "vendor-matching"
    description = "Match findings to specific vendor solutions"
    version = "1.0.0"

    requires_llm = True
    requires_knowledge = True

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Match a finding to vendor solutions.

        Args:
            context: SkillContext with:
                - metadata.finding: The finding to match
                - metadata.company_context: Company size, budget, etc.
                - industry: For industry-specific vendors

        Returns:
            Vendor matches with scoring and reasoning
        """
        finding = context.metadata.get("finding", {})
        company_context = context.metadata.get("company_context", {})

        if not finding:
            raise SkillError(
                self.name,
                "No finding provided in context.metadata",
                recoverable=False
            )

        # Detect category from finding
        category = self._detect_category(finding)

        # Get relevant vendors
        vendors = self._get_candidate_vendors(
            category=category,
            industry=context.industry,
        )

        if not vendors:
            # Try broader search
            vendors = self._search_all_vendors(finding)

        # Score and rank vendors
        scored_vendors = self._score_vendors(
            vendors=vendors,
            finding=finding,
            company_context=company_context,
        )

        # Use LLM for nuanced matching if we have candidates
        if scored_vendors and self.client:
            scored_vendors = await self._llm_refine_matches(
                vendors=scored_vendors,
                finding=finding,
                company_context=company_context,
                industry=context.industry,
            )

        # Select best matches for each tier
        result = self._select_tier_matches(scored_vendors, finding)

        return result

    def _detect_category(self, finding: Dict[str, Any]) -> Optional[str]:
        """Detect vendor category from finding content."""
        # Combine all text fields
        text = " ".join([
            str(finding.get("title", "")),
            str(finding.get("description", "")),
            str(finding.get("category", "")),
            str(finding.get("pain_point", "")),
        ]).lower()

        # Score each category
        category_scores = {}
        for category, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                category_scores[category] = score

        # Return highest scoring category
        if category_scores:
            return max(category_scores, key=category_scores.get)

        return None

    def _get_candidate_vendors(
        self,
        category: Optional[str],
        industry: str,
    ) -> List[Dict[str, Any]]:
        """Get candidate vendors from knowledge base."""
        vendors = []

        # Try industry-specific vendors first
        industry_vendors = get_vendor_recommendations(
            normalize_industry(industry),
            category
        )
        vendors.extend(industry_vendors)

        # Add general vendors from category
        if category and category in VENDOR_CATEGORIES:
            category_data = load_vendor_category(category)
            if category_data and "vendors" in category_data:
                for v in category_data["vendors"]:
                    if v not in vendors:
                        vendors.append(v)

        return vendors

    def _search_all_vendors(self, finding: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search all vendor categories for matches."""
        vendors = []
        text = " ".join([
            str(finding.get("title", "")),
            str(finding.get("description", "")),
        ]).lower()

        for category in VENDOR_CATEGORIES:
            category_data = load_vendor_category(category)
            if category_data and "vendors" in category_data:
                for vendor in category_data["vendors"]:
                    # Check if vendor is relevant
                    vendor_text = " ".join([
                        vendor.get("name", ""),
                        vendor.get("description", ""),
                        " ".join(vendor.get("best_for", [])),
                    ]).lower()

                    # Simple keyword overlap
                    finding_words = set(text.split())
                    vendor_words = set(vendor_text.split())
                    overlap = len(finding_words & vendor_words)

                    if overlap > 2:
                        vendors.append(vendor)

        return vendors[:20]  # Limit candidates

    def _score_vendors(
        self,
        vendors: List[Dict[str, Any]],
        finding: Dict[str, Any],
        company_context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Score vendors based on fit."""
        scored = []

        # Determine company size
        employee_count = company_context.get("employee_count", "11-50")
        if isinstance(employee_count, int):
            if employee_count <= 10:
                company_size = "startup"
            elif employee_count <= 50:
                company_size = "smb"
            elif employee_count <= 200:
                company_size = "mid-market"
            else:
                company_size = "enterprise"
        else:
            company_size = SIZE_MAPPING.get(str(employee_count), "smb")

        for vendor in vendors:
            score = 50  # Base score
            reasons = []
            limitations = []

            # Size fit
            vendor_sizes = vendor.get("company_sizes", [])
            if company_size in vendor_sizes:
                score += 20
                reasons.append(f"Good fit for {company_size}")
            elif vendor_sizes:
                score -= 10
                limitations.append(f"Primarily for {', '.join(vendor_sizes)}")

            # Rating score
            ratings = vendor.get("ratings", {})
            our_rating = ratings.get("our_rating", 0)
            if our_rating >= 4.5:
                score += 15
                reasons.append("Highly rated")
            elif our_rating >= 4.0:
                score += 10

            # G2 score
            g2 = ratings.get("g2", {})
            if g2.get("score", 0) >= 4.5 and g2.get("reviews", 0) > 100:
                score += 10
                reasons.append(f"G2 rating: {g2.get('score')}/5")

            # Implementation complexity
            impl = vendor.get("implementation", {})
            complexity = impl.get("complexity", "medium")
            if complexity == "low":
                score += 10
                reasons.append("Easy to implement")
            elif complexity == "high":
                score -= 5
                limitations.append("Complex implementation")

            # Pricing - check if free tier available
            pricing = vendor.get("pricing", {})
            if pricing.get("free_tier"):
                score += 5
                reasons.append("Free tier available")

            # Check avoid_if conditions
            avoid_if = vendor.get("avoid_if", [])
            for condition in avoid_if:
                if company_size == "startup" and "small" in condition.lower():
                    score -= 15
                    limitations.append(condition)
                    break

            scored.append({
                **vendor,
                "_fit_score": min(100, max(0, score)),
                "_fit_reasons": reasons,
                "_limitations": limitations,
            })

        # Sort by score
        scored.sort(key=lambda x: x["_fit_score"], reverse=True)

        return scored

    async def _llm_refine_matches(
        self,
        vendors: List[Dict[str, Any]],
        finding: Dict[str, Any],
        company_context: Dict[str, Any],
        industry: str,
    ) -> List[Dict[str, Any]]:
        """Use LLM to refine vendor matching."""
        # Only process top candidates to save tokens
        top_vendors = vendors[:6]

        vendor_summaries = []
        for v in top_vendors:
            pricing = v.get("pricing", {})
            tiers = pricing.get("tiers", [])
            starting_tier = tiers[0] if tiers else {}
            mid_tier = tiers[len(tiers)//2] if len(tiers) > 1 else starting_tier

            vendor_summaries.append({
                "slug": v.get("slug"),
                "name": v.get("name"),
                "description": v.get("description", "")[:200],
                "best_for": v.get("best_for", [])[:3],
                "starting_price": pricing.get("starting_price"),
                "mid_tier_price": mid_tier.get("price"),
                "company_sizes": v.get("company_sizes", []),
                "current_score": v.get("_fit_score"),
            })

        prompt = f"""Given this business finding and company context, refine the vendor match scores.

FINDING:
Title: {finding.get('title', 'Unknown')}
Description: {finding.get('description', '')}
Category: {finding.get('category', '')}

COMPANY CONTEXT:
Industry: {industry}
Size: {company_context.get('employee_count', 'SMB')}
Budget: {company_context.get('budget', 'moderate')}

CANDIDATE VENDORS:
{vendor_summaries}

For each vendor, provide:
1. adjusted_score (0-100): Refined fit score
2. tier_recommendation: "off_the_shelf" or "best_in_class"
3. reasoning: Brief explanation (1 sentence)

Return ONLY a JSON object:
{{
    "matches": [
        {{
            "slug": "vendor-slug",
            "adjusted_score": 85,
            "tier_recommendation": "off_the_shelf",
            "reasoning": "..."
        }}
    ]
}}"""

        try:
            result = await self.call_llm_json(
                prompt=prompt,
                system="You are a software selection expert. Match vendors to business needs."
            )

            # Apply adjustments
            matches_by_slug = {
                m["slug"]: m
                for m in result.get("matches", [])
            }

            for vendor in vendors:
                slug = vendor.get("slug")
                if slug in matches_by_slug:
                    match = matches_by_slug[slug]
                    vendor["_fit_score"] = match.get("adjusted_score", vendor["_fit_score"])
                    vendor["_tier_recommendation"] = match.get("tier_recommendation", "off_the_shelf")
                    vendor["_llm_reasoning"] = match.get("reasoning", "")

            # Re-sort
            vendors.sort(key=lambda x: x.get("_fit_score", 0), reverse=True)

        except Exception as e:
            logger.warning(f"LLM vendor refinement failed: {e}")

        return vendors

    def _select_tier_matches(
        self,
        vendors: List[Dict[str, Any]],
        finding: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Select best vendor for each tier."""
        off_the_shelf = None
        best_in_class = None
        alternatives = []

        for vendor in vendors:
            tier_rec = vendor.get("_tier_recommendation", "off_the_shelf")

            # Format vendor data
            formatted = self._format_vendor(vendor)

            if tier_rec == "best_in_class" and not best_in_class:
                best_in_class = formatted
            elif not off_the_shelf:
                off_the_shelf = formatted
            elif len(alternatives) < 3:
                alternatives.append({
                    "vendor": vendor.get("name"),
                    "slug": vendor.get("slug"),
                    "fit_score": vendor.get("_fit_score", 0),
                })

        # If we only have one, use it for off_the_shelf
        if off_the_shelf and not best_in_class and len(vendors) > 1:
            # Find a premium option
            for vendor in vendors[1:]:
                pricing = vendor.get("pricing", {})
                tiers = pricing.get("tiers", [])
                if tiers:
                    mid_tier = tiers[len(tiers)//2]
                    if mid_tier.get("price", 0) > (off_the_shelf.get("monthly_cost", 0) * 1.5):
                        best_in_class = self._format_vendor(vendor)
                        break

        # Determine confidence
        if off_the_shelf and off_the_shelf.get("fit_score", 0) >= 75:
            confidence = "high"
        elif off_the_shelf and off_the_shelf.get("fit_score", 0) >= 50:
            confidence = "medium"
        else:
            confidence = "low"

        return {
            "finding_id": finding.get("id"),
            "category": self._detect_category(finding),
            "off_the_shelf": off_the_shelf,
            "best_in_class": best_in_class,
            "alternatives": alternatives,
            "match_confidence": confidence,
            "match_reasoning": off_the_shelf.get("_llm_reasoning", "") if off_the_shelf else "",
        }

    def _format_vendor(self, vendor: Dict[str, Any]) -> Dict[str, Any]:
        """Format vendor for output."""
        pricing = vendor.get("pricing", {})
        tiers = pricing.get("tiers", [])
        impl = vendor.get("implementation", {})

        # Find appropriate tier
        starter_tier = None
        mid_tier = None
        for tier in tiers:
            if tier.get("price", 0) == 0:
                continue
            if not starter_tier:
                starter_tier = tier
            elif not mid_tier:
                mid_tier = tier
                break

        selected_tier = mid_tier or starter_tier or {}

        # Get cost range for implementation
        cost_range = impl.get("cost_range", {})
        with_help = cost_range.get("with_help", {})
        impl_cost = (with_help.get("min", 0) + with_help.get("max", 0)) / 2 if with_help else 0

        return {
            "vendor": vendor.get("name"),
            "slug": vendor.get("slug"),
            "monthly_cost": selected_tier.get("price", pricing.get("starting_price", 0)),
            "implementation_cost": impl_cost,
            "implementation_weeks": impl.get("avg_weeks", 2),
            "fit_score": vendor.get("_fit_score", 0),
            "fit_reasons": vendor.get("_fit_reasons", []),
            "pricing_tier": selected_tier.get("name", "Standard"),
            "key_features": selected_tier.get("features", [])[:5],
            "limitations": vendor.get("_limitations", []),
            "_llm_reasoning": vendor.get("_llm_reasoning", ""),
        }


# For skill discovery
__all__ = ["VendorMatchingSkill"]
