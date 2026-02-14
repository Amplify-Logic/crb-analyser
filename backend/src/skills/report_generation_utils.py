"""
Report Generation Utilities

Shared helper functions for report-generation skills (three_options, four_options)
that need to load and format vendor data from the knowledge base.

These utilities solve the problem of LLM hallucination by injecting actual
vendor data from the KB into prompts, so the LLM uses real names and prices
instead of making them up.
"""

import json
import logging
from typing import Dict, Any, List, Optional

from src.knowledge import (
    get_vendor_recommendations,
    load_vendor_category,
    normalize_industry,
    VENDOR_CATEGORIES,
)

logger = logging.getLogger(__name__)

# Map finding text keywords to vendor categories
FINDING_CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "automation": [
        "workflow", "automation", "integrate", "integration", "connect",
        "automate", "sync", "trigger", "zap", "n8n", "make",
    ],
    "crm": [
        "crm", "customer relationship", "sales", "lead", "pipeline",
        "contact", "opportunity", "deal",
    ],
    "customer_support": [
        "support", "helpdesk", "ticket", "customer service", "chat",
        "chatbot", "help desk",
    ],
    "scheduling": [
        "schedule", "scheduling", "appointment", "booking", "calendar",
        "book", "availability",
    ],
    "project_management": [
        "project", "task", "kanban", "sprint", "agile",
    ],
    "finance": [
        "invoice", "invoicing", "accounting", "payment", "billing",
        "expense",
    ],
    "hr_payroll": [
        "hr", "payroll", "employee", "hiring", "recruitment", "onboarding",
    ],
    "marketing": [
        "marketing", "email", "campaign", "newsletter",
        "seo", "ads", "social media", "content marketing",
    ],
    "analytics": [
        "analytics", "reporting", "dashboard", "metrics", "data",
    ],
    "ai_assistants": [
        "ai assistant", "chatbot", "copilot", "intelligent assistant",
    ],
    "ai_content_creation": [
        "content creation", "video", "presentation", "copywriting",
        "content generation",
    ],
    "ai_sales_tools": [
        "sales automation", "outreach", "prospecting", "lead enrichment",
    ],
    "ai_agents": [
        "ai agent", "autonomous", "agent",
    ],
    "ecommerce": [
        "ecommerce", "e-commerce", "online store", "shop", "cart",
    ],
    "dev_tools": [
        "developer", "coding", "api", "sdk", "development",
    ],
}


def get_relevant_vendor_categories(finding: Dict[str, Any]) -> List[str]:
    """
    Detect which vendor categories are relevant to a finding based on its text.

    Args:
        finding: Finding dict with title, description, category fields

    Returns:
        List of relevant vendor category slugs (e.g., ["crm", "automation"])
    """
    text = " ".join([
        str(finding.get("title", "")),
        str(finding.get("description", "")),
        str(finding.get("category", "")),
        str(finding.get("pain_point", "")),
    ]).lower()

    category_scores: Dict[str, int] = {}
    for category, keywords in FINDING_CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            category_scores[category] = score

    # Return categories sorted by relevance score, top 3
    sorted_cats = sorted(category_scores, key=category_scores.get, reverse=True)
    return sorted_cats[:3]


def _extract_vendor_summary(vendor: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    Extract a concise summary from a vendor entry for prompt injection.

    Handles both category-vendor format (vendors/*.json) and
    industry-vendor format (industry/vendors.json).

    Args:
        vendor: Raw vendor dict from KB

    Returns:
        Compact summary dict or None if vendor has no usable data
    """
    name = vendor.get("name", "")
    if not name:
        return None

    # Extract pricing - handle multiple formats
    pricing = vendor.get("pricing", {})
    price_str = ""

    if isinstance(pricing, dict):
        # Category vendor format: pricing.tiers[]
        tiers = pricing.get("tiers", [])
        if tiers:
            # Find first non-free tier for starting price
            free_tier = None
            paid_tier = None
            for tier in tiers:
                tier_price = tier.get("price", 0)
                if tier_price == 0:
                    free_tier = tier
                elif paid_tier is None:
                    paid_tier = tier

            if free_tier and paid_tier:
                price_str = f"Free tier available, paid from {paid_tier.get('price')}/{paid_tier.get('per', 'mo')}"
            elif paid_tier:
                price_str = f"From {paid_tier.get('price')}/{paid_tier.get('per', 'mo')}"
            elif free_tier:
                price_str = "Free"
        elif pricing.get("starting_price"):
            price_str = f"From {pricing['starting_price']}/mo"
        elif pricing.get("custom_pricing"):
            price_str = "Custom pricing (contact sales)"
        else:
            # Industry vendor format: pricing has named tiers like "essentials", "standard"
            tier_prices = []
            for tier_name, tier_data in pricing.items():
                if isinstance(tier_data, dict) and "price" in tier_data:
                    p = tier_data["price"]
                    if p != "custom":
                        period = tier_data.get("period", "month")
                        tier_prices.append(f"{tier_name}: {p}/{period}")
                    else:
                        tier_prices.append(f"{tier_name}: custom")
            if tier_prices:
                price_str = "; ".join(tier_prices[:2])
    elif isinstance(pricing, (int, float)):
        price_str = f"{pricing}/mo"

    # Fallback pricing fields
    if not price_str:
        mp = vendor.get("monthly_price")
        sp = vendor.get("starting_price")
        if mp:
            price_str = f"{mp}/mo"
        elif sp:
            price_str = f"From {sp}/mo"

    # Extract key features (keep concise)
    best_for = vendor.get("best_for", [])
    if isinstance(best_for, str):
        best_for = [best_for]

    description = vendor.get("description", "")
    tagline = vendor.get("tagline", "")

    # Company sizes
    sizes = vendor.get("company_sizes", [])

    summary: Dict[str, str] = {
        "name": name,
    }
    if vendor.get("slug"):
        summary["slug"] = vendor["slug"]
    if price_str:
        summary["pricing"] = price_str
    if tagline:
        summary["what"] = tagline[:80]
    elif description:
        summary["what"] = description[:80]
    if best_for:
        summary["best_for"] = ", ".join(best_for[:2]) if isinstance(best_for, list) else str(best_for)[:80]
    if sizes:
        summary["company_sizes"] = ", ".join(sizes)

    return summary


def load_kb_vendors_for_finding(
    finding: Dict[str, Any],
    industry: str,
    context_vendors: Optional[List[Dict[str, Any]]] = None,
    max_vendors: int = 15,
) -> List[Dict[str, str]]:
    """
    Load relevant vendors from the knowledge base for a specific finding.

    Combines:
    1. Industry-specific vendors from industry/vendors.json
    2. Category vendors from vendors/*.json matched to the finding
    3. Any vendors already passed in context (pre-filtered)

    Deduplicates by name and limits to max_vendors.

    Args:
        finding: The finding dict
        industry: Industry slug
        context_vendors: Vendors already in context (e.g., from report_service)
        max_vendors: Maximum number of vendor summaries to return

    Returns:
        List of vendor summary dicts ready for prompt injection
    """
    seen_names: set = set()
    vendor_summaries: List[Dict[str, str]] = []

    def _add_vendor(vendor: Dict[str, Any]) -> None:
        """Add vendor to results if not already seen."""
        name_key = vendor.get("name", "").lower().strip()
        if not name_key or name_key in seen_names:
            return
        summary = _extract_vendor_summary(vendor)
        if summary:
            seen_names.add(name_key)
            vendor_summaries.append(summary)

    # 1. Add context vendors first (these are pre-filtered by report_service)
    if context_vendors:
        for v in context_vendors:
            if len(vendor_summaries) >= max_vendors:
                break
            _add_vendor(v)

    # 2. Load industry-specific vendors
    normalized = normalize_industry(industry)
    industry_vendors = get_vendor_recommendations(normalized)
    for v in industry_vendors:
        if len(vendor_summaries) >= max_vendors:
            break
        _add_vendor(v)

    # 3. Load category-specific vendors based on finding text
    relevant_categories = get_relevant_vendor_categories(finding)
    for category in relevant_categories:
        if len(vendor_summaries) >= max_vendors:
            break
        if category in VENDOR_CATEGORIES:
            cat_data = load_vendor_category(category)
            if cat_data and "vendors" in cat_data:
                for v in cat_data["vendors"]:
                    if len(vendor_summaries) >= max_vendors:
                        break
                    _add_vendor(v)

    return vendor_summaries


def format_vendors_for_prompt(
    vendors: List[Dict[str, str]],
    currency_symbol: str = "€",
) -> str:
    """
    Format vendor summaries into a concise text block for LLM prompt injection.

    Keeps each vendor to 1-2 lines to avoid bloating the prompt.

    Args:
        vendors: List of vendor summary dicts from load_kb_vendors_for_finding
        currency_symbol: Currency symbol for display

    Returns:
        Formatted string ready to inject into a prompt
    """
    if not vendors:
        return """## VENDOR CATALOG
No vendors found in the knowledge base for this finding's category.
If recommending a BUY option, state that no verified vendor was found and suggest the user research options manually."""

    lines = []
    for v in vendors:
        name = v.get("name", "Unknown")
        slug = v.get("slug", "")
        pricing = v.get("pricing", "Pricing not available")
        what = v.get("what", "")
        best_for = v.get("best_for", "")
        sizes = v.get("company_sizes", "")

        # Build concise 1-2 line entry
        parts = [f"- **{name}**"]
        if slug:
            parts[0] += f" ({slug})"
        parts[0] += f": {pricing}"
        if what:
            parts.append(f"  {what}")
        detail_parts = []
        if best_for:
            detail_parts.append(f"Best for: {best_for}")
        if sizes:
            detail_parts.append(f"Sizes: {sizes}")
        if detail_parts:
            parts.append(f"  {' | '.join(detail_parts)}")

        lines.append("\n".join(parts))

    vendor_block = "\n".join(lines)

    return f"""## VENDOR CATALOG (from verified knowledge base - USE THESE)

{vendor_block}

IMPORTANT: For BUY/off-the-shelf/best-in-class options, ONLY recommend vendors from this catalog.
Use the exact pricing shown. Do NOT invent vendor names or make up prices.
If no vendor in this catalog fits the finding, say "No matching vendor in catalog" rather than fabricating one."""
