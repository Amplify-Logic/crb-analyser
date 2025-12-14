"""
Modeling Tools

Tools for the modeling phase of CRB analysis.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta


async def calculate_roi(
    inputs: Dict[str, Any],
    context: Dict[str, Any],
    audit_id: str,
) -> Dict[str, Any]:
    """Calculate ROI with transparent assumptions."""
    solution_name = inputs.get("solution_name", "")
    implementation_cost = inputs.get("implementation_cost", 0)
    monthly_cost = inputs.get("monthly_cost", 0)
    monthly_savings = inputs.get("monthly_savings", 0)
    time_horizon = inputs.get("time_horizon_months", 12)

    # Calculate total costs
    total_implementation = implementation_cost
    total_recurring = monthly_cost * time_horizon
    total_cost = total_implementation + total_recurring

    # Calculate total savings
    total_savings = monthly_savings * time_horizon

    # Calculate net benefit
    net_benefit = total_savings - total_cost

    # Calculate ROI percentage
    if total_cost > 0:
        roi_percentage = ((net_benefit) / total_cost) * 100
    else:
        roi_percentage = 0 if total_savings == 0 else 100

    # Calculate payback period
    net_monthly_benefit = monthly_savings - monthly_cost
    if net_monthly_benefit > 0:
        payback_months = implementation_cost / net_monthly_benefit
    else:
        payback_months = None  # Never pays back

    # Calculate break-even point
    if net_monthly_benefit > 0:
        break_even_month = int(payback_months) + 1 if payback_months else None
    else:
        break_even_month = None

    # Build year-by-year projection
    yearly_projection = []
    cumulative_cost = implementation_cost
    cumulative_savings = 0

    for year in range(1, 4):  # 3-year projection
        year_cost = monthly_cost * 12
        year_savings = monthly_savings * 12
        cumulative_cost += year_cost
        cumulative_savings += year_savings

        yearly_projection.append({
            "year": year,
            "annual_cost": round(year_cost, 2),
            "annual_savings": round(year_savings, 2),
            "net_benefit": round(year_savings - year_cost, 2),
            "cumulative_net": round(cumulative_savings - cumulative_cost, 2),
        })

    return {
        "solution_name": solution_name,
        "roi_metrics": {
            "roi_percentage": round(roi_percentage, 1),
            "net_benefit": round(net_benefit, 2),
            "payback_months": round(payback_months, 1) if payback_months else None,
            "break_even_month": break_even_month,
        },
        "cost_breakdown": {
            "implementation_cost": implementation_cost,
            "monthly_recurring": monthly_cost,
            "total_cost_period": round(total_cost, 2),
        },
        "savings_breakdown": {
            "monthly_savings": monthly_savings,
            "total_savings_period": round(total_savings, 2),
        },
        "projection": yearly_projection,
        "assumptions": {
            "time_horizon_months": time_horizon,
            "savings_are_recurring": True,
            "no_price_increases_assumed": True,
        },
        "assessment": "Positive ROI" if roi_percentage > 0 else "Negative ROI",
    }


async def compare_vendors(
    inputs: Dict[str, Any],
    context: Dict[str, Any],
    audit_id: str,
) -> Dict[str, Any]:
    """Compare vendors for a solution category."""
    category = inputs.get("category", "")
    requirements = inputs.get("requirements", [])
    budget_max = inputs.get("budget_max", 0)

    # Vendor comparison data (simplified - would come from database)
    vendor_data = {
        "CRM": [
            {
                "name": "HubSpot",
                "monthly_cost": {"starter": 45, "professional": 450, "enterprise": 1200},
                "setup_cost": 0,
                "ease_of_use": 9,
                "features": 8,
                "support": 8,
                "scalability": 9,
                "best_for": "Growing SMBs",
            },
            {
                "name": "Pipedrive",
                "monthly_cost": {"essential": 15, "advanced": 29, "professional": 59},
                "setup_cost": 0,
                "ease_of_use": 9,
                "features": 7,
                "support": 7,
                "scalability": 7,
                "best_for": "Sales-focused teams",
            },
            {
                "name": "Salesforce",
                "monthly_cost": {"essentials": 25, "professional": 75, "enterprise": 150},
                "setup_cost": 2000,
                "ease_of_use": 6,
                "features": 10,
                "support": 9,
                "scalability": 10,
                "best_for": "Enterprise needs",
            },
        ],
        "automation": [
            {
                "name": "Zapier",
                "monthly_cost": {"free": 0, "starter": 20, "professional": 49, "team": 399},
                "setup_cost": 0,
                "ease_of_use": 10,
                "features": 8,
                "support": 7,
                "scalability": 8,
                "best_for": "No-code automation",
            },
            {
                "name": "Make (Integromat)",
                "monthly_cost": {"free": 0, "core": 9, "pro": 16, "teams": 29},
                "setup_cost": 0,
                "ease_of_use": 7,
                "features": 9,
                "support": 7,
                "scalability": 8,
                "best_for": "Complex workflows",
            },
            {
                "name": "n8n",
                "monthly_cost": {"self_hosted": 0, "cloud_starter": 20, "cloud_pro": 50},
                "setup_cost": 0,
                "ease_of_use": 6,
                "features": 9,
                "support": 6,
                "scalability": 9,
                "best_for": "Technical teams",
            },
        ],
    }

    category_key = category.lower().replace(" ", "_")
    vendors = vendor_data.get(category_key, vendor_data.get("automation", []))

    # Filter by budget if specified
    if budget_max > 0:
        vendors = [
            v for v in vendors
            if any(cost <= budget_max for cost in v["monthly_cost"].values())
        ]

    # Score vendors
    for vendor in vendors:
        # Calculate overall score
        vendor["overall_score"] = round(
            (vendor["ease_of_use"] + vendor["features"] + vendor["support"] + vendor["scalability"]) / 4, 1
        )

    # Sort by overall score
    vendors = sorted(vendors, key=lambda v: v["overall_score"], reverse=True)

    return {
        "category": category,
        "vendors_compared": len(vendors),
        "comparison": vendors,
        "recommendation": vendors[0]["name"] if vendors else None,
        "recommendation_reason": f"Best overall score ({vendors[0]['overall_score']}/10)" if vendors else None,
        "budget_filter_applied": budget_max > 0,
    }


async def generate_timeline(
    inputs: Dict[str, Any],
    context: Dict[str, Any],
    audit_id: str,
) -> Dict[str, Any]:
    """Generate implementation timeline."""
    recommendations = inputs.get("recommendations", [])
    start_date_str = inputs.get("start_date")

    # Parse start date or use today + 1 month
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        except ValueError:
            start_date = datetime.now() + timedelta(days=30)
    else:
        start_date = datetime.now() + timedelta(days=30)

    # Default implementation durations by type
    duration_map = {
        "quick_win": 7,  # 1 week
        "short": 14,  # 2 weeks
        "medium": 30,  # 1 month
        "long": 60,  # 2 months
        "complex": 90,  # 3 months
    }

    # Generate timeline items
    timeline = []
    current_date = start_date

    for i, rec in enumerate(recommendations[:10]):  # Max 10 items
        # Estimate duration based on recommendation text
        duration_type = "medium"
        rec_lower = rec.lower()
        if any(w in rec_lower for w in ["quick", "simple", "basic", "start"]):
            duration_type = "quick_win"
        elif any(w in rec_lower for w in ["complex", "full", "enterprise", "migrate"]):
            duration_type = "long"
        elif any(w in rec_lower for w in ["integration", "custom", "develop"]):
            duration_type = "complex"

        duration_days = duration_map[duration_type]

        timeline.append({
            "phase": i + 1,
            "recommendation": rec,
            "start_date": current_date.strftime("%Y-%m-%d"),
            "end_date": (current_date + timedelta(days=duration_days)).strftime("%Y-%m-%d"),
            "duration_days": duration_days,
            "duration_type": duration_type,
        })

        # Overlap phases slightly (start next 1 week before current ends)
        current_date = current_date + timedelta(days=max(7, duration_days - 7))

    total_duration = (
        datetime.strptime(timeline[-1]["end_date"], "%Y-%m-%d") -
        datetime.strptime(timeline[0]["start_date"], "%Y-%m-%d")
    ).days if timeline else 0

    return {
        "timeline": timeline,
        "total_phases": len(timeline),
        "total_duration_days": total_duration,
        "total_duration_weeks": round(total_duration / 7, 1),
        "start_date": start_date.strftime("%Y-%m-%d"),
        "estimated_completion": timeline[-1]["end_date"] if timeline else None,
        "notes": [
            "Timeline assumes sequential implementation with some overlap",
            "Actual duration may vary based on resource availability",
            "Quick wins should be prioritized for early ROI",
        ],
    }
