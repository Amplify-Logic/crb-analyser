"""
Research Tools

Tools for the research phase of CRB analysis.
Uses the JSON-based knowledge base for vendor and benchmark data.
"""

from typing import Dict, Any, List

# Import knowledge base functions
from src.knowledge import (
    get_benchmarks_for_metrics,
    normalize_industry,
    search_vendors,
    get_all_vendors,
    load_vendor_category,
    list_vendor_categories,
    get_llm_providers,
)


# Category mapping from tool input to knowledge base categories
CATEGORY_MAP = {
    "crm": "crm",
    "automation": "automation",
    "ai": "ai_assistants",
    "ai_development": "ai_assistants",
    "project_management": "project_management",
    "project management": "project_management",
    "customer_service": "customer_support",
    "customer service": "customer_support",
    "support": "customer_support",
    "analytics": "analytics",
    "marketing": "marketing",
    "email": "marketing",
    "ecommerce": "ecommerce",
    "finance": "finance",
    "accounting": "finance",
    "hr": "hr_payroll",
    "payroll": "hr_payroll",
    "dev_tools": "dev_tools",
    "development": "dev_tools",
}


def _format_vendor_for_tool(vendor: Dict) -> Dict:
    """Format a vendor from knowledge base for tool output."""
    pricing = vendor.get("pricing", {})
    tiers = pricing.get("tiers", [])

    # Build pricing string
    if pricing.get("free_tier"):
        price_str = "Free"
        if tiers:
            paid_tiers = [t for t in tiers if (t.get("price") or 0) > 0]
            if paid_tiers:
                max_price = max((t.get("price") or 0) for t in paid_tiers)
                price_str += f"-${int(max_price)}/mo"
    elif tiers:
        prices = [(t.get("price") or 0) for t in tiers if t.get("price")]
        if prices:
            price_str = f"${int(min(prices))}-${int(max(prices))}/mo"
        else:
            price_str = "Contact for pricing"
    else:
        starting = pricing.get("starting_price")
        if starting:
            price_str = f"From ${int(starting)}/mo"
        else:
            price_str = "Contact for pricing"

    return {
        "name": vendor.get("name"),
        "slug": vendor.get("slug"),
        "pricing": price_str,
        "best_for": ", ".join(vendor.get("best_for", [])[:3]),
        "features": vendor.get("best_for", [])[:5],
        "website": vendor.get("website"),
        "free_tier": pricing.get("free_tier", False),
        "verified_at": vendor.get("verified_at"),
    }


async def search_industry_benchmarks(
    inputs: Dict[str, Any],
    context: Dict[str, Any],
    audit_id: str,
) -> Dict[str, Any]:
    """Search for industry-specific benchmarks from knowledge base."""
    industry = inputs.get("industry", context.get("industry", "general"))
    metric_type = inputs.get("metric_type")

    # Normalize and get benchmarks from knowledge base
    normalized = normalize_industry(industry)
    benchmarks = get_benchmarks_for_metrics(industry, metric_type)

    if not benchmarks:
        # Fall back to general benchmarks if industry not found
        return {
            "industry": industry,
            "normalized_industry": normalized,
            "benchmarks": {},
            "source": "CRB Industry Knowledge Base",
            "note": f"No specific benchmarks found for {industry}. Consider using general industry metrics.",
        }

    if metric_type:
        # Return specific metric category
        return {
            "industry": industry,
            "normalized_industry": normalized,
            "metric_category": metric_type,
            "data": benchmarks,
            "source": "CRB Industry Knowledge Base (verified sources)",
        }

    return {
        "industry": industry,
        "normalized_industry": normalized,
        "benchmarks": benchmarks,
        "source": "CRB Industry Knowledge Base",
        "note": "Benchmarks sourced from McKinsey, Gartner, Deloitte, and industry reports",
    }


async def search_vendor_solutions(
    inputs: Dict[str, Any],
    context: Dict[str, Any],
    audit_id: str,
) -> Dict[str, Any]:
    """Search for vendor solutions from knowledge base matching requirements."""
    category = inputs.get("category", "")
    company_size = inputs.get("company_size", context.get("company_size", ""))
    budget_range = inputs.get("budget_range", "")
    query = inputs.get("query", "")

    # Normalize category to knowledge base category
    normalized_category = CATEGORY_MAP.get(category.lower(), category.lower())

    # Map company size to knowledge base format
    size_map = {
        "solo": "startup",
        "1": "startup",
        "2-10": "startup",
        "11-50": "smb",
        "51-200": "mid-market",
        "200+": "enterprise",
        "201+": "enterprise",
    }
    kb_company_size = size_map.get(company_size, company_size.lower() if company_size else None)

    # Parse budget if provided (e.g., "$0-100", "100-500")
    max_price = None
    if budget_range:
        try:
            # Extract max number from budget range
            import re
            numbers = re.findall(r'\d+', budget_range)
            if numbers:
                max_price = float(max(int(n) for n in numbers))
        except (ValueError, TypeError):
            pass

    # Search vendors from knowledge base
    vendors = search_vendors(
        query=query or None,
        category=normalized_category if normalized_category in list_vendor_categories() else None,
        company_size=kb_company_size,
        max_price=max_price,
    )

    # Format vendors for tool output
    formatted_vendors = [_format_vendor_for_tool(v) for v in vendors[:5]]

    return {
        "category": category,
        "normalized_category": normalized_category,
        "vendors": formatted_vendors,
        "total_found": len(vendors),
        "available_categories": list_vendor_categories(),
        "filters_applied": {
            "company_size": company_size,
            "budget_range": budget_range,
            "query": query,
        },
        "source": "CRB Vendor Knowledge Base (verified December 2025)",
    }


async def validate_source(
    inputs: Dict[str, Any],
    context: Dict[str, Any],
    audit_id: str,
) -> Dict[str, Any]:
    """Validate the credibility of a source or claim."""
    source = inputs.get("source", "")
    claim = inputs.get("claim", "")

    # Simple credibility scoring (in production, would use actual validation)
    credibility_score = 70  # Default
    validation_notes = []

    # Check for known reliable sources
    reliable_sources = [
        "gartner", "forrester", "mckinsey", "deloitte", "accenture",
        "statista", "ibm", "microsoft", "google", "salesforce",
    ]

    source_lower = source.lower()
    if any(rs in source_lower for rs in reliable_sources):
        credibility_score = 90
        validation_notes.append("Source is a recognized industry authority")

    # Check for red flags
    if "unverified" in source_lower or "estimate" in source_lower:
        credibility_score -= 20
        validation_notes.append("Source indicates estimates or unverified data")

    if claim:
        # Check if claim has specific numbers
        if any(char.isdigit() for char in claim):
            validation_notes.append("Claim includes specific figures")
        else:
            credibility_score -= 10
            validation_notes.append("Claim lacks specific quantification")

    return {
        "source": source,
        "claim": claim,
        "credibility_score": max(0, min(100, credibility_score)),
        "credibility_level": "high" if credibility_score >= 80 else "medium" if credibility_score >= 50 else "low",
        "validation_notes": validation_notes,
        "recommendation": "Can be cited" if credibility_score >= 60 else "Should be marked as estimate",
    }
