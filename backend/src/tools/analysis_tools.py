"""
Analysis Tools

Tools for the analysis phase of CRB analysis.
"""

from typing import Dict, Any


async def score_automation_potential(
    inputs: Dict[str, Any],
    context: Dict[str, Any],
    audit_id: str,
) -> Dict[str, Any]:
    """Score a process for automation potential (0-100)."""
    process_name = inputs.get("process_name", "")
    process_description = inputs.get("process_description", "")
    current_time = inputs.get("current_time_hours", 0)
    is_repetitive = inputs.get("is_repetitive", True)
    requires_judgment = inputs.get("requires_judgment", False)

    # Base score
    score = 50

    # Adjust for repetitiveness
    if is_repetitive:
        score += 20

    # Adjust for judgment requirement
    if requires_judgment:
        score -= 25
    else:
        score += 10

    # Adjust for time investment (more time = higher priority)
    if current_time > 20:
        score += 15
    elif current_time > 10:
        score += 10
    elif current_time > 5:
        score += 5

    # Check description for automation indicators
    automation_keywords = [
        "data entry", "copy", "paste", "transfer", "report",
        "spreadsheet", "email", "schedule", "reminder", "follow up",
        "invoice", "update", "sync", "export", "import",
    ]

    complexity_keywords = [
        "negotiate", "creative", "strategy", "relationship",
        "custom", "unique", "judgment", "decision", "complex",
    ]

    desc_lower = process_description.lower()
    for keyword in automation_keywords:
        if keyword in desc_lower:
            score += 5

    for keyword in complexity_keywords:
        if keyword in desc_lower:
            score -= 5

    # Clamp score
    score = max(0, min(100, score))

    # Determine automation type
    if score >= 80:
        automation_type = "full_automation"
        recommendation = "Fully automate this process"
    elif score >= 60:
        automation_type = "partial_automation"
        recommendation = "Automate repetitive parts, keep human oversight"
    elif score >= 40:
        automation_type = "assisted"
        recommendation = "Use AI to assist but maintain human control"
    else:
        automation_type = "manual"
        recommendation = "Keep manual, focus automation elsewhere"

    return {
        "process_name": process_name,
        "automation_score": score,
        "automation_type": automation_type,
        "recommendation": recommendation,
        "factors": {
            "is_repetitive": is_repetitive,
            "requires_judgment": requires_judgment,
            "time_investment": current_time,
        },
    }


async def calculate_finding_impact(
    inputs: Dict[str, Any],
    context: Dict[str, Any],
    audit_id: str,
) -> Dict[str, Any]:
    """Calculate the business impact of a finding."""
    finding_title = inputs.get("finding_title", "")
    hours_saved = inputs.get("hours_saved_per_month", 0)
    hourly_rate = inputs.get("hourly_rate", 35)  # Default EUR 35/hour
    affected_employees = inputs.get("affected_employees", 1)

    # Calculate savings
    monthly_hours_saved = hours_saved * affected_employees
    monthly_cost_saved = monthly_hours_saved * hourly_rate
    annual_cost_saved = monthly_cost_saved * 12

    # Calculate productivity gain
    # Assuming 160 working hours per month
    productivity_gain_percent = (monthly_hours_saved / (160 * affected_employees)) * 100

    # Determine impact level
    if annual_cost_saved >= 50000:
        impact_level = "critical"
    elif annual_cost_saved >= 20000:
        impact_level = "high"
    elif annual_cost_saved >= 5000:
        impact_level = "medium"
    else:
        impact_level = "low"

    return {
        "finding_title": finding_title,
        "impact_metrics": {
            "hours_saved_monthly": monthly_hours_saved,
            "hours_saved_annually": monthly_hours_saved * 12,
            "cost_saved_monthly": round(monthly_cost_saved, 2),
            "cost_saved_annually": round(annual_cost_saved, 2),
            "productivity_gain_percent": round(productivity_gain_percent, 1),
        },
        "impact_level": impact_level,
        "assumptions": {
            "hourly_rate_eur": hourly_rate,
            "affected_employees": affected_employees,
            "working_hours_per_month": 160,
        },
    }


async def identify_ai_opportunities(
    inputs: Dict[str, Any],
    context: Dict[str, Any],
    audit_id: str,
) -> Dict[str, Any]:
    """Identify AI implementation opportunities."""
    process_area = inputs.get("process_area", "general")

    # AI opportunity templates by area
    ai_opportunities = {
        "customer_service": [
            {
                "opportunity": "AI-powered chatbot for first-line support",
                "potential_impact": "Reduce support tickets by 30-50%",
                "implementation_complexity": "medium",
                "time_to_value": "1-2 months",
            },
            {
                "opportunity": "Automated email categorization and routing",
                "potential_impact": "Save 5-10 hours/week on email triage",
                "implementation_complexity": "low",
                "time_to_value": "2 weeks",
            },
        ],
        "sales": [
            {
                "opportunity": "AI lead scoring and prioritization",
                "potential_impact": "Increase conversion by 15-25%",
                "implementation_complexity": "medium",
                "time_to_value": "1-2 months",
            },
            {
                "opportunity": "Automated sales email personalization",
                "potential_impact": "Increase response rates by 20-40%",
                "implementation_complexity": "low",
                "time_to_value": "2-4 weeks",
            },
        ],
        "marketing": [
            {
                "opportunity": "AI content generation assistance",
                "potential_impact": "2-3x content output with same team",
                "implementation_complexity": "low",
                "time_to_value": "1-2 weeks",
            },
            {
                "opportunity": "Automated social media management",
                "potential_impact": "Save 10-15 hours/week",
                "implementation_complexity": "low",
                "time_to_value": "1 week",
            },
        ],
        "operations": [
            {
                "opportunity": "Process automation with AI decision support",
                "potential_impact": "Reduce manual processing by 60-80%",
                "implementation_complexity": "high",
                "time_to_value": "2-4 months",
            },
            {
                "opportunity": "Document processing and extraction",
                "potential_impact": "Save 5-20 hours/week on data entry",
                "implementation_complexity": "medium",
                "time_to_value": "1-2 months",
            },
        ],
        "analytics": [
            {
                "opportunity": "AI-powered business intelligence",
                "potential_impact": "Faster insights, better decisions",
                "implementation_complexity": "medium",
                "time_to_value": "1-2 months",
            },
            {
                "opportunity": "Automated reporting and dashboards",
                "potential_impact": "Eliminate manual report creation",
                "implementation_complexity": "low",
                "time_to_value": "2-4 weeks",
            },
        ],
        "general": [
            {
                "opportunity": "AI assistant for employee productivity",
                "potential_impact": "10-20% productivity boost per employee",
                "implementation_complexity": "low",
                "time_to_value": "1 week",
            },
            {
                "opportunity": "Meeting transcription and action items",
                "potential_impact": "Save 2-5 hours/week per manager",
                "implementation_complexity": "low",
                "time_to_value": "Same day",
            },
        ],
    }

    area_key = process_area.lower().replace(" ", "_")
    opportunities = ai_opportunities.get(area_key, ai_opportunities["general"])

    return {
        "process_area": process_area,
        "opportunities": opportunities,
        "total_opportunities": len(opportunities),
        "quick_wins": [o for o in opportunities if o["implementation_complexity"] == "low"],
    }


async def assess_implementation_risk(
    inputs: Dict[str, Any],
    context: Dict[str, Any],
    audit_id: str,
) -> Dict[str, Any]:
    """Assess implementation risk for a proposed change."""
    change_description = inputs.get("change_description", "")
    complexity = inputs.get("complexity", "medium")
    requires_training = inputs.get("requires_training", True)

    # Base risk score
    risk_score = 30  # Start medium-low

    # Adjust for complexity
    complexity_scores = {"low": -10, "medium": 0, "high": 20}
    risk_score += complexity_scores.get(complexity, 0)

    # Adjust for training requirement
    if requires_training:
        risk_score += 15

    # Check company tech comfort from context
    intake = context.get("intake_responses", {})
    tech_comfort = intake.get("technology_comfort", 5)
    if isinstance(tech_comfort, int):
        if tech_comfort <= 3:
            risk_score += 20
        elif tech_comfort >= 8:
            risk_score -= 10

    # Check company size (smaller = less risk usually)
    company_size = context.get("company_size", "")
    size_risk = {
        "solo": -10,
        "2-10": -5,
        "11-50": 0,
        "51-200": 10,
        "200+": 20,
    }
    risk_score += size_risk.get(company_size, 0)

    # Clamp score
    risk_score = max(0, min(100, risk_score))

    # Identify risk factors
    risk_factors = []
    if requires_training:
        risk_factors.append("Requires employee training")
    if complexity == "high":
        risk_factors.append("High implementation complexity")
    if tech_comfort and tech_comfort <= 4:
        risk_factors.append("Team may resist technology change")

    # Mitigation suggestions
    mitigations = []
    if requires_training:
        mitigations.append("Plan phased rollout with training sessions")
    if complexity == "high":
        mitigations.append("Consider pilot program before full deployment")
    if risk_score >= 50:
        mitigations.append("Engage change management support")

    return {
        "change_description": change_description,
        "risk_score": risk_score,
        "risk_level": "high" if risk_score >= 60 else "medium" if risk_score >= 30 else "low",
        "risk_factors": risk_factors,
        "mitigations": mitigations,
        "recommendation": "Proceed with caution" if risk_score >= 50 else "Acceptable risk",
    }
