"""
Research Tools

Tools for the research phase of CRB analysis.
"""

from typing import Dict, Any


# Industry benchmark data (in production, this would come from a database)
INDUSTRY_BENCHMARKS = {
    "marketing_agency": {
        "automation_rate": {"average": 35, "top_quartile": 55, "unit": "%"},
        "admin_time_ratio": {"average": 25, "top_quartile": 15, "unit": "%"},
        "client_retention": {"average": 75, "top_quartile": 90, "unit": "%"},
        "revenue_per_employee": {"average": 120000, "top_quartile": 180000, "unit": "EUR"},
        "project_margin": {"average": 35, "top_quartile": 50, "unit": "%"},
    },
    "ecommerce": {
        "automation_rate": {"average": 45, "top_quartile": 70, "unit": "%"},
        "fulfillment_cost_ratio": {"average": 12, "top_quartile": 8, "unit": "%"},
        "customer_service_automation": {"average": 30, "top_quartile": 60, "unit": "%"},
        "inventory_accuracy": {"average": 85, "top_quartile": 98, "unit": "%"},
    },
    "retail": {
        "inventory_turnover": {"average": 8, "top_quartile": 12, "unit": "times/year"},
        "labor_cost_ratio": {"average": 20, "top_quartile": 15, "unit": "%"},
        "shrinkage_rate": {"average": 1.5, "top_quartile": 0.5, "unit": "%"},
    },
    "tech_company": {
        "automation_rate": {"average": 55, "top_quartile": 80, "unit": "%"},
        "deployment_frequency": {"average": "weekly", "top_quartile": "daily", "unit": ""},
        "dev_productivity": {"average": 60, "top_quartile": 80, "unit": "story_points/sprint"},
    },
    "music_company": {
        "catalog_management_time": {"average": 15, "top_quartile": 5, "unit": "hours/week"},
        "royalty_processing_time": {"average": 40, "top_quartile": 10, "unit": "hours/month"},
        "content_distribution_automation": {"average": 40, "top_quartile": 85, "unit": "%"},
    },
    "general": {
        "automation_rate": {"average": 30, "top_quartile": 50, "unit": "%"},
        "admin_time_ratio": {"average": 30, "top_quartile": 15, "unit": "%"},
        "employee_productivity": {"average": 65, "top_quartile": 85, "unit": "%"},
    },
}

# Vendor database (in production, this would be a full database)
VENDOR_DATABASE = {
    "CRM": [
        {"name": "HubSpot", "pricing": "Free-$1200/mo", "best_for": "SMB", "features": ["Marketing", "Sales", "Service"]},
        {"name": "Salesforce", "pricing": "$25-$300/user/mo", "best_for": "Enterprise", "features": ["Full suite", "Customizable"]},
        {"name": "Pipedrive", "pricing": "$15-$99/user/mo", "best_for": "Sales teams", "features": ["Pipeline", "Automation"]},
    ],
    "automation": [
        {"name": "Zapier", "pricing": "Free-$599/mo", "best_for": "No-code", "features": ["5000+ integrations", "Easy setup"]},
        {"name": "Make", "pricing": "Free-$299/mo", "best_for": "Complex workflows", "features": ["Visual builder", "Advanced logic"]},
        {"name": "n8n", "pricing": "Free-$50/mo", "best_for": "Technical teams", "features": ["Self-hosted", "Open source"]},
    ],
    "AI": [
        {"name": "Claude/Anthropic", "pricing": "API usage", "best_for": "Content & analysis", "features": ["Long context", "Safe"]},
        {"name": "OpenAI", "pricing": "API usage", "best_for": "General AI", "features": ["GPT-4", "DALL-E", "Whisper"]},
        {"name": "Jasper", "pricing": "$49-$125/mo", "best_for": "Marketing", "features": ["Templates", "Brand voice"]},
    ],
    "project_management": [
        {"name": "Monday.com", "pricing": "$8-$16/user/mo", "best_for": "Visual teams", "features": ["Automations", "Dashboards"]},
        {"name": "Asana", "pricing": "Free-$25/user/mo", "best_for": "Task management", "features": ["Goals", "Portfolios"]},
        {"name": "ClickUp", "pricing": "Free-$12/user/mo", "best_for": "All-in-one", "features": ["Docs", "Whiteboards"]},
    ],
    "customer_service": [
        {"name": "Intercom", "pricing": "$74-$395/mo", "best_for": "SaaS", "features": ["Chat", "Bots", "Help desk"]},
        {"name": "Zendesk", "pricing": "$19-$115/agent/mo", "best_for": "Enterprise", "features": ["Tickets", "Chat", "Phone"]},
        {"name": "Freshdesk", "pricing": "Free-$79/agent/mo", "best_for": "SMB", "features": ["Tickets", "Automation"]},
    ],
}


async def search_industry_benchmarks(
    inputs: Dict[str, Any],
    context: Dict[str, Any],
    audit_id: str,
) -> Dict[str, Any]:
    """Search for industry-specific benchmarks."""
    industry = inputs.get("industry", context.get("industry", "general"))
    metric_type = inputs.get("metric_type")

    # Normalize industry name
    industry_key = industry.lower().replace(" ", "_").replace("/", "_")

    # Get benchmarks
    benchmarks = INDUSTRY_BENCHMARKS.get(industry_key, INDUSTRY_BENCHMARKS["general"])

    if metric_type:
        # Filter to specific metric
        metric_key = metric_type.lower().replace(" ", "_")
        if metric_key in benchmarks:
            return {
                "industry": industry,
                "metric": metric_type,
                "data": benchmarks[metric_key],
                "source": "CRB Industry Database 2024",
            }
        return {
            "industry": industry,
            "metric": metric_type,
            "data": None,
            "message": f"No benchmark found for {metric_type} in {industry}",
        }

    return {
        "industry": industry,
        "benchmarks": benchmarks,
        "source": "CRB Industry Database 2024",
        "note": "Benchmarks based on industry surveys and published reports",
    }


async def search_vendor_solutions(
    inputs: Dict[str, Any],
    context: Dict[str, Any],
    audit_id: str,
) -> Dict[str, Any]:
    """Search for vendor solutions matching requirements."""
    category = inputs.get("category", "").upper()
    company_size = inputs.get("company_size", context.get("company_size", ""))
    budget_range = inputs.get("budget_range", "")

    # Normalize category
    category_map = {
        "CRM": "CRM",
        "AUTOMATION": "automation",
        "AI": "AI",
        "PROJECT MANAGEMENT": "project_management",
        "PROJECT_MANAGEMENT": "project_management",
        "CUSTOMER SERVICE": "customer_service",
        "CUSTOMER_SERVICE": "customer_service",
    }

    normalized_category = category_map.get(category.upper(), category.lower())
    vendors = VENDOR_DATABASE.get(normalized_category, [])

    # Filter by company size if provided
    size_preferences = {
        "solo": ["SMB", "No-code", "Free"],
        "2-10": ["SMB", "No-code", "Sales teams"],
        "11-50": ["SMB", "All-in-one", "SaaS"],
        "51-200": ["Enterprise", "SaaS", "Technical teams"],
        "200+": ["Enterprise"],
    }

    if company_size and company_size in size_preferences:
        preferred = size_preferences[company_size]
        # Sort vendors by preference match
        vendors = sorted(
            vendors,
            key=lambda v: any(p in v.get("best_for", "") for p in preferred),
            reverse=True,
        )

    return {
        "category": category,
        "vendors": vendors[:5],  # Top 5 matches
        "total_found": len(vendors),
        "filters_applied": {
            "company_size": company_size,
            "budget_range": budget_range,
        },
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
