"""
Discovery Tools

Tools for the discovery phase of CRB analysis.
"""

from typing import Dict, Any


async def analyze_intake_responses(
    inputs: Dict[str, Any],
    context: Dict[str, Any],
    audit_id: str,
) -> Dict[str, Any]:
    """Analyze intake questionnaire responses."""
    intake = context.get("intake_responses", {})
    client = context.get("client", {})
    focus_areas = inputs.get("focus_areas", [])

    # Extract key insights
    pain_points = []
    opportunities = []
    strengths = []

    # Analyze biggest challenge
    challenge = intake.get("biggest_challenge", "")
    if challenge:
        pain_points.append({
            "area": "primary_challenge",
            "description": challenge,
            "source": "intake_response",
        })

    # Analyze time wasters
    time_wasters = intake.get("time_wasters", "")
    if time_wasters:
        pain_points.append({
            "area": "time_wasters",
            "description": time_wasters,
            "source": "intake_response",
        })

    # Analyze repetitive tasks
    repetitive = intake.get("repetitive_tasks", "")
    if repetitive:
        opportunities.append({
            "area": "automation",
            "description": f"Repetitive tasks identified: {repetitive}",
            "potential": "high",
        })

    # Analyze tech comfort
    tech_comfort = intake.get("technology_comfort", 5)
    if isinstance(tech_comfort, int):
        if tech_comfort >= 7:
            strengths.append({
                "area": "technology_adoption",
                "description": "Team is comfortable with new technology",
                "score": tech_comfort,
            })
        elif tech_comfort <= 3:
            pain_points.append({
                "area": "change_resistance",
                "description": "Team may resist new technology adoption",
                "score": tech_comfort,
            })

    # Analyze AI interest
    ai_areas = intake.get("ai_interest_areas", [])
    if ai_areas:
        for area in ai_areas:
            opportunities.append({
                "area": area,
                "description": f"Interest in AI for {area.replace('_', ' ')}",
                "potential": "medium",
            })

    # Analyze goals
    goals = intake.get("primary_goals", [])

    return {
        "company_profile": {
            "name": client.get("name", "Unknown"),
            "industry": client.get("industry", "Unknown"),
            "size": client.get("company_size", "Unknown"),
        },
        "pain_points": pain_points,
        "opportunities": opportunities,
        "strengths": strengths,
        "primary_goals": goals,
        "admin_hours_weekly": intake.get("time_on_admin", 0),
        "has_manual_data_entry": intake.get("manual_data_entry") == "yes",
        "analysis_complete": True,
    }


async def map_business_processes(
    inputs: Dict[str, Any],
    context: Dict[str, Any],
    audit_id: str,
) -> Dict[str, Any]:
    """Map business processes from intake responses."""
    intake = context.get("intake_responses", {})
    process_type = inputs.get("process_type", "all")

    processes = []

    # Main processes
    main_processes = intake.get("main_processes", "")
    if main_processes:
        processes.append({
            "name": "Core Operations",
            "type": "core",
            "description": main_processes,
            "automation_potential": "unknown",
        })

    # Repetitive tasks
    repetitive = intake.get("repetitive_tasks", "")
    if repetitive:
        processes.append({
            "name": "Repetitive Tasks",
            "type": "administrative",
            "description": repetitive,
            "automation_potential": "high",
        })

    # Bottlenecks
    bottlenecks = intake.get("biggest_bottlenecks", "")
    if bottlenecks:
        processes.append({
            "name": "Bottleneck Processes",
            "type": "constraint",
            "description": bottlenecks,
            "automation_potential": "medium",
        })

    # Manual data entry
    if intake.get("manual_data_entry") == "yes":
        details = intake.get("manual_data_entry_details", "Manual data transfer between systems")
        processes.append({
            "name": "Data Entry",
            "type": "administrative",
            "description": details,
            "automation_potential": "high",
        })

    # Filter by type if specified
    if process_type != "all":
        type_map = {
            "customer_facing": ["core", "customer"],
            "internal": ["internal", "core"],
            "administrative": ["administrative"],
        }
        allowed_types = type_map.get(process_type, [])
        processes = [p for p in processes if p["type"] in allowed_types]

    return {
        "processes": processes,
        "total_count": len(processes),
        "high_automation_potential": len([p for p in processes if p.get("automation_potential") == "high"]),
    }


async def identify_tech_stack(
    inputs: Dict[str, Any],
    context: Dict[str, Any],
    audit_id: str,
) -> Dict[str, Any]:
    """Identify current technology stack."""
    intake = context.get("intake_responses", {})

    tools = intake.get("current_tools", [])
    ai_tools = intake.get("ai_tools_used", [])
    integration_score = intake.get("integration_issues", 5)

    # Categorize tools
    categories = {
        "crm": [],
        "project_management": [],
        "communication": [],
        "analytics": [],
        "accounting": [],
        "marketing": [],
        "ecommerce": [],
        "other": [],
    }

    tool_category_map = {
        "crm": "crm",
        "project_management": "project_management",
        "communication": "communication",
        "analytics": "analytics",
        "accounting": "accounting",
        "email_marketing": "marketing",
        "social_media": "marketing",
        "ecommerce": "ecommerce",
        "spreadsheets": "other",
    }

    for tool in tools:
        cat = tool_category_map.get(tool, "other")
        categories[cat].append(tool)

    # Assess AI maturity
    ai_maturity = "none"
    if ai_tools and "none" not in ai_tools:
        if len(ai_tools) >= 3:
            ai_maturity = "advanced"
        elif len(ai_tools) >= 1:
            ai_maturity = "exploring"

    return {
        "tools_by_category": {k: v for k, v in categories.items() if v},
        "total_tools": len(tools),
        "ai_tools_in_use": [t for t in ai_tools if t != "none"],
        "ai_maturity": ai_maturity,
        "integration_score": integration_score,
        "integration_quality": "good" if integration_score >= 7 else "needs_work" if integration_score >= 4 else "poor",
        "tool_frustrations": intake.get("tool_pain_points", ""),
    }
