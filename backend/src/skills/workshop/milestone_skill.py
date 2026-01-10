# backend/src/skills/workshop/milestone_skill.py
"""
Milestone Synthesis Skill

Synthesizes deep-dive conversation into a draft finding with:
- Structured finding summary
- ROI calculation
- Vendor recommendations (from database)
- Confidence score

This is shown to the user after each deep-dive as a "value moment".
"""

import logging
from typing import Any, Dict, List, Optional

from src.skills.base import LLMSkill, SkillContext, SkillError
from src.services.vendor_service import vendor_service

logger = logging.getLogger(__name__)

# Map pain point keywords to vendor categories
PAIN_TO_CATEGORY_MAP = {
    # CRM/Sales related
    "lead": "crm",
    "sales": "crm",
    "client": "crm",
    "prospect": "crm",
    "followup": "crm",
    "follow-up": "crm",
    # Automation
    "manual": "automation",
    "repetitive": "automation",
    "workflow": "automation",
    "process": "automation",
    "automate": "automation",
    # Customer support
    "support": "customer_support",
    "ticket": "customer_support",
    "help desk": "customer_support",
    "customer service": "customer_support",
    # Scheduling
    "schedule": "scheduling",
    "appointment": "scheduling",
    "booking": "scheduling",
    "calendar": "scheduling",
    # Project management
    "project": "project_management",
    "task": "project_management",
    "team": "project_management",
    "collaboration": "project_management",
    # Marketing
    "email": "marketing",
    "campaign": "marketing",
    "marketing": "marketing",
    "newsletter": "marketing",
    # Finance
    "invoice": "finance",
    "billing": "finance",
    "payment": "finance",
    "accounting": "finance",
    # Analytics
    "report": "analytics",
    "dashboard": "analytics",
    "metric": "analytics",
    "data": "analytics",
}


class MilestoneSynthesisSkill(LLMSkill[Dict[str, Any]]):
    """
    Synthesize deep-dive transcript into draft finding and ROI.

    Uses Sonnet for quality since this is user-facing output.
    Vendors are looked up from the database, not LLM-generated.
    """

    name = "milestone-synthesis"
    description = "Synthesize deep-dive into finding with ROI"
    version = "1.1.0"  # Updated for vendor database integration

    default_model = "claude-sonnet-4-20250514"  # Quality matters
    default_max_tokens = 2000

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Synthesize a deep-dive into a milestone summary.

        Args:
            context: SkillContext with metadata containing:
                - pain_point_id: ID of the pain point
                - pain_point_label: Human-readable name
                - transcript: List of conversation messages
                - company_name: Company name
                - tools_mentioned: Tools identified in conversation

        Returns:
            Dict with finding, roi, vendors, confidence
        """
        metadata = context.metadata or {}

        pain_point_id = metadata.get("pain_point_id", "unknown")
        pain_label = metadata.get("pain_point_label", "This challenge")
        transcript = metadata.get("transcript", [])
        company_name = metadata.get("company_name", "the company")
        tools = metadata.get("tools_mentioned", [])

        if not transcript:
            raise SkillError(
                self.name,
                "No transcript provided for synthesis",
                recoverable=False
            )

        # Generate finding and ROI via LLM (without vendors)
        prompt = self._build_prompt(
            pain_label=pain_label,
            transcript=transcript,
            company_name=company_name,
            tools=tools,
            industry=context.industry,
        )

        system = self._get_system_prompt()

        result = await self.call_llm_json(prompt, system)

        # Validate and enrich result
        result["pain_point_id"] = pain_point_id
        result["pain_point_label"] = pain_label

        # Lookup vendors from database
        vendors = await self._lookup_vendors(
            industry=context.industry,
            pain_label=pain_label,
            transcript=transcript,
            finding_title=result.get("finding", {}).get("title", ""),
        )
        result["vendors"] = vendors

        return result

    async def _lookup_vendors(
        self,
        industry: str,
        pain_label: str,
        transcript: List[Dict[str, str]],
        finding_title: str,
    ) -> List[Dict[str, Any]]:
        """
        Lookup relevant vendors from the database.

        Uses pain point keywords and industry to find matching vendors.
        """
        try:
            # Determine relevant category from pain point
            category = self._detect_category(pain_label, transcript, finding_title)

            # Build finding tags for matching
            finding_tags = self._extract_finding_tags(pain_label, finding_title)

            # Query vendors with tier boost
            vendors = await vendor_service.get_vendors_with_tier_boost(
                industry=industry,
                category=category,
                finding_tags=finding_tags,
                prefer_automation=True,  # Prioritize API-ready vendors
            )

            # Format for milestone output (top 3)
            formatted_vendors = []
            for vendor in vendors[:3]:
                fit = "high" if vendor.get("_tier") == 1 else "medium" if vendor.get("_tier") == 2 else "low"

                formatted_vendors.append({
                    "name": vendor.get("name"),
                    "slug": vendor.get("slug"),
                    "fit": fit,
                    "reason": self._generate_fit_reason(vendor, pain_label),
                    "pricing": self._format_pricing_summary(vendor),
                    "tier": vendor.get("_tier"),
                })

            # If no database vendors found, return empty (don't hallucinate)
            if not formatted_vendors:
                logger.warning(
                    f"No vendors found for industry={industry}, category={category}"
                )

            return formatted_vendors

        except Exception as e:
            logger.error(f"Vendor lookup failed: {e}")
            return []  # Return empty rather than LLM-generated

    def _detect_category(
        self,
        pain_label: str,
        transcript: List[Dict[str, str]],
        finding_title: str,
    ) -> Optional[str]:
        """Detect the most relevant vendor category from context."""
        # Combine all text for keyword matching
        all_text = f"{pain_label} {finding_title}".lower()
        for msg in transcript:
            all_text += f" {msg.get('content', '')}".lower()

        # Find matching category
        category_scores: Dict[str, int] = {}
        for keyword, category in PAIN_TO_CATEGORY_MAP.items():
            if keyword in all_text:
                category_scores[category] = category_scores.get(category, 0) + 1

        if category_scores:
            # Return highest scoring category
            return max(category_scores, key=category_scores.get)

        return None  # No specific category detected

    def _extract_finding_tags(
        self,
        pain_label: str,
        finding_title: str,
    ) -> List[str]:
        """Extract tags from finding for vendor matching."""
        tags = []
        text = f"{pain_label} {finding_title}".lower()

        # Common automation opportunities
        if "automat" in text:
            tags.append("automation")
        if "manual" in text or "repetitive" in text:
            tags.append("workflow_automation")
        if "lead" in text or "sales" in text:
            tags.append("sales_automation")
        if "customer" in text or "client" in text:
            tags.append("customer_management")
        if "schedule" in text or "appointment" in text:
            tags.append("scheduling")
        if "invoice" in text or "billing" in text:
            tags.append("billing_automation")
        if "report" in text or "analytics" in text:
            tags.append("reporting")

        return tags

    def _generate_fit_reason(
        self,
        vendor: Dict[str, Any],
        pain_label: str,
    ) -> str:
        """Generate a concise reason why this vendor fits."""
        name = vendor.get("name", "This solution")
        best_for = vendor.get("best_for", [])

        if best_for:
            return f"{name} excels at {best_for[0].lower()}"

        # Fallback based on tier
        tier = vendor.get("_tier")
        if tier == 1:
            return f"{name} is highly recommended for your industry"
        elif tier == 2:
            return f"{name} is a solid choice for this use case"
        else:
            return f"{name} can address this challenge"

    def _format_pricing_summary(self, vendor: Dict[str, Any]) -> Optional[str]:
        """Format a brief pricing summary."""
        pricing = vendor.get("pricing", {})
        if not pricing:
            return None

        if pricing.get("free_tier"):
            return "Free tier available"

        starting = pricing.get("starting_price")
        if starting:
            currency = pricing.get("currency", "USD")
            return f"From {currency} {starting}/mo"

        if pricing.get("custom_pricing"):
            return "Custom pricing"

        return None

    def _get_system_prompt(self) -> str:
        return """You are a business analyst synthesizing discovery interview data into actionable insights.

Your output will be shown directly to the user as a "draft finding" during a workshop.
Be specific, use their exact numbers and context, and provide realistic ROI calculations.

Always return valid JSON matching the requested schema. Be conservative with ROI estimates."""

    def _build_prompt(
        self,
        pain_label: str,
        transcript: List[Dict[str, str]],
        company_name: str,
        tools: List[str],
        industry: str,
    ) -> str:
        # Format transcript
        conv = "\n".join([
            f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
            for m in transcript
        ])

        return f"""Analyze this deep-dive conversation about "{pain_label}" at {company_name} ({industry}).

CONVERSATION:
{conv}

TOOLS MENTIONED: {', '.join(tools) if tools else 'None identified'}

Synthesize into a milestone summary. Return JSON:

{{
    "finding": {{
        "title": "<Concise opportunity title>",
        "summary": "<2-3 sentence summary of the opportunity>",
        "current_process": "<How it works today, from their words>",
        "pain_severity": "low|medium|high",
        "recommendation": "<High-level recommendation>"
    }},
    "roi": {{
        "hours_per_week": <number, from their data or estimate>,
        "hourly_rate": <estimated rate based on role/industry, default 75>,
        "annual_cost": <calculated: hours_per_week * hourly_rate * 52>,
        "potential_savings": <conservative estimate, usually 60-80% of cost>,
        "savings_percentage": <percentage>,
        "calculation_notes": "<brief explanation of how you calculated this>"
    }},
    "confidence": <0.0-1.0, based on specificity of data provided>,
    "data_gaps": ["<list any information that would improve accuracy>"]
}}

NOTE: Do NOT include vendors in your response. Vendor recommendations are handled separately.

Use THEIR actual numbers when provided. If estimating, be conservative and note it.
Return ONLY the JSON, no other text."""
