"""
Quiz Answer Fabricator

Converts seed business profiles + optional scraped website data
into realistic quiz_session data for the report pipeline.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.skills.base import COUNTRY_CURRENCY_MAP


# Average Order Value by product category (EUR)
CATEGORY_AOV = {
    "fashion": 85,
    "electronics": 150,
    "health": 65,
    "beauty": 55,
    "home": 120,
    "food": 45,
    "sports": 95,
    "pets": 60,
    "jewelry": 200,
    "kids": 70,
    "general": 80,
}

# Hourly cost defaults by country (local currency)
COUNTRY_HOURLY_COST = {
    "NL": 45, "DE": 45, "FR": 40, "BE": 42,
    "UK": 40, "GB": 40,
    "US": 55, "CA": 50,
    "AU": 50, "NZ": 45,
}


def fabricate_quiz_session(
    seed: Dict[str, Any],
    tier_defaults: Dict[str, Any],
    scraped_data: Optional[Dict[str, Any]] = None,
    report_tier: str = "quick",
) -> Dict[str, Any]:
    """
    Build a complete quiz_session dict from seed + scraped data.

    Args:
        seed: Business seed from ecommerce.json
        tier_defaults: Default values for this business tier (small/mid/scaling)
        scraped_data: Optional scraped website data
        report_tier: "quick" or "full"

    Returns:
        Dict ready to INSERT into quiz_sessions table
    """
    profile = seed["profile"]
    country = seed.get("country", "NL")
    currency = COUNTRY_CURRENCY_MAP.get(country, "EUR")

    # Estimate monthly revenue from orders * category AOV
    category = profile.get("product_category", "general")
    aov = CATEGORY_AOV.get(category, CATEGORY_AOV["general"])
    monthly_orders = profile.get("monthly_orders", 300)
    monthly_revenue = monthly_orders * aov

    # Use seed pain points, falling back to tier defaults
    pain_points = profile.get("pain_points") or tier_defaults.get("pain_points", [])

    # Hourly cost: country-specific or tier default
    hourly_cost = COUNTRY_HOURLY_COST.get(country, tier_defaults.get("hourly_cost", 40))

    # Build answers dict (mirrors what quiz UI would produce)
    answers = {
        "industry": "ecommerce",
        "company_size": profile.get("staff_size", "1-10"),
        "current_tools": profile.get("current_tools", []),
        "pain_points": pain_points,
        "biggest_challenge": pain_points[0] if pain_points else "scaling operations",
        "monthly_revenue": monthly_revenue,
        "hourly_rate": hourly_cost,
        "budget": tier_defaults.get("budget", 1000),
        "currency": currency,
        "platform": profile.get("platform", "shopify"),
        "has_erp": profile.get("has_erp", False),
        "product_category": category,
        "monthly_orders": monthly_orders,
    }

    # Build company profile from scraped data or seed
    if scraped_data:
        company_profile = {
            "description": scraped_data.get("description", ""),
            "products": scraped_data.get("products", []),
            "visible_tech": scraped_data.get("visible_tech", []),
            "source": "cli_scraper",
            **{k: v for k, v in scraped_data.items() if k not in ("description", "products", "visible_tech")},
        }
    else:
        company_profile = {
            "description": f"{seed['name']} - {category} e-commerce store",
            "products": [],
            "visible_tech": profile.get("current_tools", []),
            "source": "seed_only",
        }

    now = datetime.now(timezone.utc).isoformat()

    return {
        "id": str(uuid.uuid4()),
        "email": f"cli-{uuid.uuid4().hex[:8]}@crb-analyser.local",
        "tier": report_tier,
        "status": "paid",
        "current_section": 0,
        "current_question": 0,
        "answers": answers,
        "results": {},
        "company_name": seed["name"],
        "company_website": seed.get("website", ""),
        "company_profile": company_profile,
        "existing_stack": _build_existing_stack(profile),
        "interview_data": {"messages": [], "confidence": {}},
        "created_at": now,
        "updated_at": now,
    }


def _build_existing_stack(profile: Dict[str, Any]) -> list:
    """Build existing_stack list from seed tools."""
    tools = profile.get("current_tools", [])
    return [
        {"name": tool, "slug": tool.lower().replace(" ", "-"), "api_score": 3}
        for tool in tools
    ]
