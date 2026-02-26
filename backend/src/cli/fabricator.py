"""
Quiz Answer Fabricator — Multi-Industry

Converts seed business profiles + optional scraped website data
into realistic quiz_session data for the report pipeline.
Supports: ecommerce, dental, professional-services.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.skills.base import COUNTRY_CURRENCY_MAP


# ============================================================================
# E-COMMERCE CONSTANTS
# ============================================================================

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

# ============================================================================
# SHARED CONSTANTS
# ============================================================================

COUNTRY_HOURLY_COST = {
    "NL": 45, "DE": 45, "FR": 40, "BE": 42,
    "UK": 40, "GB": 40,
    "US": 55, "CA": 50,
    "AU": 50, "NZ": 45,
}

# Tools that indicate higher technical sophistication
MODERN_TOOLS = {
    "zapier", "segment", "make", "n8n", "klaviyo", "gorgias",
    "netsuite", "brightpearl", "recharge", "attentive", "gladly",
    "aws", "vercel", "react", "custom_nextjs",
}


def _infer_tech_comfort(tools: List[str], profile: Dict[str, Any]) -> int:
    """Infer technology comfort (3-9) from tool count and sophistication."""
    tool_count = len(tools)
    modern_count = sum(1 for t in tools if t.lower() in MODERN_TOOLS)

    if tool_count >= 5 or modern_count >= 2:
        return 8
    if tool_count >= 3 or modern_count >= 1:
        return 6
    if tool_count >= 2:
        return 4
    return 3


def _infer_ai_tools(tools: List[str]) -> List[str]:
    """Infer AI tool usage from stack sophistication."""
    modern_count = sum(1 for t in tools if t.lower() in MODERN_TOOLS)
    if modern_count >= 2:
        return ["chatgpt", "copilot"]
    if modern_count >= 1 or len(tools) >= 4:
        return ["chatgpt"]
    return []


def fabricate_quiz_session(
    seed: Dict[str, Any],
    tier_defaults: Dict[str, Any],
    scraped_data: Optional[Dict[str, Any]] = None,
    report_tier: str = "quick",
) -> Dict[str, Any]:
    """
    Build a complete quiz_session dict from seed + scraped data.

    Dispatches to industry-specific answer builders based on
    seed["profile"]["industry"]. Falls back to ecommerce for
    backward compatibility with seeds that lack an industry field.
    """
    profile = seed["profile"]
    industry = profile.get("industry", "ecommerce")
    country = seed.get("country", "NL")
    currency = COUNTRY_CURRENCY_MAP.get(country, "EUR")
    hourly_cost = COUNTRY_HOURLY_COST.get(country, tier_defaults.get("hourly_cost", 40))

    pain_points = profile.get("pain_points") or tier_defaults.get("pain_points", [])

    # Build industry-specific answers
    answers = _build_answers(industry, profile, tier_defaults, pain_points, hourly_cost, currency)

    # Build company profile
    company_profile = _build_company_profile(seed, profile, industry, scraped_data)

    # Build interview data from workshop transcript
    interview_data = _build_interview_data(seed)

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
        "interview_data": interview_data,
        "created_at": now,
        "updated_at": now,
    }


def _build_answers(
    industry: str,
    profile: Dict[str, Any],
    tier_defaults: Dict[str, Any],
    pain_points: List[str],
    hourly_cost: int,
    currency: str,
) -> Dict[str, Any]:
    """Build the answers dict based on industry."""
    # Common fields across all industries
    base = {
        "industry": industry,
        "company_size": profile.get("staff_size", "1-10"),
        "current_tools": profile.get("current_tools", []),
        "pain_points": pain_points,
        "biggest_challenge": pain_points[0] if pain_points else "operational efficiency",
        "monthly_revenue": profile.get("monthly_revenue", 50000),
        "hourly_rate": profile.get("hourly_rate", hourly_cost),
        "budget": tier_defaults.get("budget", 1000),
        "currency": currency,
    }

    # Readiness profile fields (used by adaptive recommendations engine)
    tools = profile.get("current_tools", [])
    base.update({
        "technology_comfort": _infer_tech_comfort(tools, profile),
        "implementation_preference": profile.get("implementation_preference", "connect"),
        "ai_tools_used": profile.get("ai_tools_used", _infer_ai_tools(tools)),
        "existing_stack_api_ready": len(tools) >= 3,
        "integration_issues": profile.get("integration_issues", 5),
        "manual_data_entry": profile.get("manual_data_entry", len(tools) < 2),
        "implementation_urgency": profile.get("implementation_urgency", "this_quarter"),
    })

    if industry == "ecommerce":
        category = profile.get("product_category", "general")
        aov = CATEGORY_AOV.get(category, CATEGORY_AOV["general"])
        monthly_orders = profile.get("monthly_orders", 300)
        base.update({
            "monthly_revenue": monthly_orders * aov,
            "platform": profile.get("platform", "shopify"),
            "has_erp": profile.get("has_erp", False),
            "product_category": category,
            "monthly_orders": monthly_orders,
        })

    elif industry == "dental":
        base.update({
            "practice_type": profile.get("practice_type", "general_dentistry"),
            "locations": profile.get("locations", 1),
            "patient_volume": profile.get("patient_volume", 200),
            "insurance_mix": profile.get("insurance_mix", "mixed"),
        })

    elif industry == "professional-services":
        base.update({
            "service_type": profile.get("service_type", "consulting"),
            "billing_model": profile.get("billing_model", "hourly"),
            "client_count": profile.get("client_count", 50),
            "compliance_requirements": profile.get("compliance_requirements", []),
        })

    return base


def _build_company_profile(
    seed: Dict[str, Any],
    profile: Dict[str, Any],
    industry: str,
    scraped_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the company_profile dict from scraped data or seed."""
    if scraped_data:
        return {
            "description": scraped_data.get("description", ""),
            "products": scraped_data.get("products", []),
            "visible_tech": scraped_data.get("visible_tech", []),
            "source": "cli_scraper",
            **{k: v for k, v in scraped_data.items()
               if k not in ("description", "products", "visible_tech")},
        }

    # Industry-specific descriptions
    if industry == "dental":
        locations = profile.get("locations", 1)
        loc_str = f"{locations} location{'s' if locations > 1 else ''}"
        desc = f"{seed['name']} — {profile.get('practice_type', 'general dentistry').replace('_', ' ')} with {loc_str}"
    elif industry == "professional-services":
        desc = f"{seed['name']} — {profile.get('service_type', 'consulting').replace('_', ' ')} firm"
    else:
        category = profile.get("product_category", "general")
        desc = f"{seed['name']} — {category} e-commerce store"

    return {
        "description": desc,
        "products": [],
        "visible_tech": profile.get("current_tools", []),
        "source": "seed_only",
    }


def _build_interview_data(seed: Dict[str, Any]) -> Dict[str, Any]:
    """Build interview_data from workshop transcript if available."""
    transcript = seed.get("workshop_transcript", [])
    if not transcript:
        return {"messages": [], "confidence": {}}

    return {
        "messages": transcript,
        "confidence": {
            "overall": 0.85,
            "tools": 0.9,
            "pain_points": 0.85,
            "budget": 0.8,
            "workflows": 0.85,
        },
    }


def _build_existing_stack(profile: Dict[str, Any]) -> list:
    """Build existing_stack list from seed tools."""
    tools = profile.get("current_tools", [])
    return [
        {"name": tool, "slug": tool.lower().replace(" ", "-"), "api_score": 3}
        for tool in tools
    ]
