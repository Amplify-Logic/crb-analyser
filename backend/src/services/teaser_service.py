"""
Teaser Report Service

Generates the free teaser report with:
- AI Readiness Score
- 2 full findings (unblurred)
- Remaining findings (titles only, blurred)
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_teaser_report(
    company_profile: Dict[str, Any],
    quiz_answers: Dict[str, Any],
    all_findings: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Generate a teaser report from research and quiz data.

    Returns:
        Teaser report with score, 2 full findings, and blurred previews
    """
    # Calculate AI Readiness Score
    score_data = _calculate_ai_readiness_score(company_profile, quiz_answers)

    # Generate or use provided findings
    if all_findings:
        findings = all_findings
    else:
        findings = _generate_preliminary_findings(company_profile, quiz_answers)

    # Split into revealed and blurred
    revealed_findings = findings[:2]  # First 2 are full detail
    blurred_findings = [
        {
            "title": f["title"],
            "category": f.get("category", "opportunity"),
            "blurred": True
        }
        for f in findings[2:6]  # Next 4 are blurred previews
    ]

    return {
        "ai_readiness_score": score_data["score"],
        "score_breakdown": score_data["breakdown"],
        "score_interpretation": _get_score_interpretation(score_data["score"]),
        "revealed_findings": revealed_findings,
        "blurred_findings": blurred_findings,
        "total_findings_available": len(findings),
        "company_name": company_profile.get("basics", {}).get("name", {}).get("value", "Your Company"),
        "industry": company_profile.get("industry", {}).get("primary_industry", {}).get("value", "General"),
        "generated_at": datetime.utcnow().isoformat(),
    }


def _calculate_ai_readiness_score(
    company_profile: Dict[str, Any],
    quiz_answers: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate AI readiness score with breakdown."""
    breakdown = {}

    # Tech maturity (0-25 points)
    tech_stack = company_profile.get("tech_stack", {})
    tech_count = len(tech_stack.get("technologies_detected", []))
    tech_score = min(25, tech_count * 5)
    breakdown["tech_maturity"] = {
        "score": tech_score,
        "max": 25,
        "factors": ["Current tech stack", "Tool adoption"]
    }

    # Process clarity (0-25 points)
    pain_points = quiz_answers.get("pain_points", [])
    has_documented = quiz_answers.get("processes_documented", False)
    process_score = 10 if has_documented else 5
    process_score += min(15, len(pain_points) * 3)  # Identifying pain = clarity
    breakdown["process_clarity"] = {
        "score": process_score,
        "max": 25,
        "factors": ["Documented processes", "Identified pain points"]
    }

    # Data readiness (0-25 points)
    size = company_profile.get("size", {})
    employee_count = size.get("employee_count", {}).get("value", 10)
    if isinstance(employee_count, str):
        # Try to parse from string ranges like "11-50"
        try:
            if "-" in str(employee_count):
                parts = str(employee_count).split("-")
                employee_count = int(parts[0])
            else:
                employee_count = int(employee_count.replace("+", ""))
        except (ValueError, AttributeError):
            employee_count = 10
    data_score = min(25, 5 + (employee_count // 10) * 2)
    breakdown["data_readiness"] = {
        "score": data_score,
        "max": 25,
        "factors": ["Company size", "Data generation potential"]
    }

    # AI experience (0-25 points)
    current_tools = quiz_answers.get("current_tools", [])
    ai_experience = quiz_answers.get("ai_experience", "none")
    ai_score = 5
    if ai_experience == "experimenting":
        ai_score = 12
    elif ai_experience == "using":
        ai_score = 20
    elif ai_experience == "scaling":
        ai_score = 25
    ai_score += min(5, len(current_tools) if isinstance(current_tools, list) else 0)
    ai_score = min(25, ai_score)
    breakdown["ai_experience"] = {
        "score": ai_score,
        "max": 25,
        "factors": ["Current AI usage", "Tool adoption"]
    }

    total_score = sum(b["score"] for b in breakdown.values())

    return {
        "score": total_score,
        "breakdown": breakdown
    }


def _get_score_interpretation(score: int) -> Dict[str, Any]:
    """Get interpretation text for score."""
    if score >= 80:
        return {
            "level": "Excellent",
            "summary": "Your organization is highly ready for AI implementation.",
            "recommendation": "Focus on strategic AI initiatives that drive competitive advantage."
        }
    elif score >= 60:
        return {
            "level": "Good",
            "summary": "You have a solid foundation for AI adoption.",
            "recommendation": "Address a few gaps to maximize AI ROI."
        }
    elif score >= 40:
        return {
            "level": "Developing",
            "summary": "There are opportunities to strengthen your AI readiness.",
            "recommendation": "Start with quick wins while building foundational capabilities."
        }
    else:
        return {
            "level": "Early Stage",
            "summary": "You're at the beginning of your AI journey.",
            "recommendation": "Focus on foundational improvements before major AI investments."
        }


def _generate_preliminary_findings(
    company_profile: Dict[str, Any],
    quiz_answers: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate preliminary findings from profile and answers."""
    findings = []

    # Finding 1: Based on pain points
    pain_points = quiz_answers.get("pain_points", [])
    if pain_points and isinstance(pain_points, list) and len(pain_points) > 0:
        first_pain = pain_points[0] if isinstance(pain_points[0], str) else str(pain_points[0])
        findings.append({
            "title": f"Automation Opportunity: {first_pain}",
            "category": "efficiency",
            "summary": f"Your team identified '{first_pain}' as a key challenge. AI-powered automation could reduce time spent on this by 40-60%.",
            "impact": "high",
            "roi_estimate": {"min": 15000, "max": 45000, "currency": "EUR"},
        })

    # Finding 2: Based on company size
    size = company_profile.get("size", {})
    employee_range = size.get("employee_range", {}).get("value", "11-50")
    if not employee_range:
        employee_range = "11-50"
    findings.append({
        "title": "Process Standardization Gap",
        "category": "operations",
        "summary": f"Companies with {employee_range} employees typically see 25% efficiency gains from standardizing workflows before AI implementation.",
        "impact": "medium",
        "roi_estimate": {"min": 8000, "max": 25000, "currency": "EUR"},
    })

    # Finding 3: Tech stack opportunity
    tech = company_profile.get("tech_stack", {})
    tech_list = tech.get("technologies_detected", [])
    if tech_list and isinstance(tech_list, list) and len(tech_list) > 0:
        first_tech = tech_list[0]
        if isinstance(first_tech, dict):
            first_tech = first_tech.get("value", "Core Systems")
        findings.append({
            "title": f"Integration Opportunity: {first_tech}",
            "category": "technology",
            "summary": "Your current tech stack has integration opportunities that could reduce manual data entry.",
            "impact": "medium",
        })
    else:
        findings.append({
            "title": "Technology Assessment Needed",
            "category": "technology",
            "summary": "A detailed technology assessment would identify quick automation wins.",
            "impact": "medium",
        })

    # Add more generic findings for blurred section
    findings.extend([
        {"title": "Customer Communication Automation", "category": "customer"},
        {"title": "Data Analytics Enhancement", "category": "analytics"},
        {"title": "Workflow Bottleneck Identification", "category": "operations"},
        {"title": "Cost Reduction Opportunities", "category": "efficiency"},
    ])

    return findings
