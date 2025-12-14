"""
Report Tools

Tools for the report generation phase of CRB analysis.
"""

import logging
from typing import Dict, Any

from src.config.supabase_client import get_async_supabase

logger = logging.getLogger(__name__)


async def create_finding(
    inputs: Dict[str, Any],
    context: Dict[str, Any],
    audit_id: str,
) -> Dict[str, Any]:
    """Create and save a finding to the database."""
    supabase = await get_async_supabase()

    # Map severity from priority if not provided
    priority = inputs.get("priority", 3)
    severity_map = {1: "critical", 2: "high", 3: "medium", 4: "low", 5: "low"}
    severity = inputs.get("severity", severity_map.get(priority, "medium"))

    # Convert confidence to 0-1 scale if provided as percentage
    confidence = inputs.get("confidence_score", inputs.get("confidence_level", 70))
    if confidence > 1:
        confidence = confidence / 100.0

    finding_data = {
        "audit_id": audit_id,
        "title": inputs.get("title", "Untitled Finding"),
        "category": inputs.get("category", "opportunity"),
        "severity": severity,
        "description": inputs.get("description", ""),
        "current_state": inputs.get("current_state"),
        "impact_description": inputs.get("impact_description"),
        "estimated_annual_cost": inputs.get("estimated_annual_cost", inputs.get("estimated_cost_saved")),
        "estimated_hours_wasted_weekly": inputs.get("estimated_hours_wasted_weekly", inputs.get("estimated_hours_saved")),
        "confidence_score": confidence,
        "is_verified": not inputs.get("is_ai_estimated", True),
        "sources": inputs.get("sources", []),
        "priority": priority,
        "impact_score": inputs.get("impact_score", 5),
        "effort_score": inputs.get("effort_score", 5),
    }

    try:
        result = await supabase.table("findings").insert(finding_data).execute()

        if result.data:
            finding = result.data[0]
            # Add to context for later use
            context.setdefault("findings", []).append(finding)

            return {
                "success": True,
                "finding_id": finding["id"],
                "title": finding["title"],
                "message": f"Finding created: {finding['title']}",
            }
        else:
            return {"success": False, "error": "Failed to create finding"}

    except Exception as e:
        logger.error(f"Create finding error: {e}")
        return {"success": False, "error": str(e)}


async def create_recommendation(
    inputs: Dict[str, Any],
    context: Dict[str, Any],
    audit_id: str,
) -> Dict[str, Any]:
    """Create and save a recommendation to the database."""
    supabase = await get_async_supabase()

    # Find related finding ID if provided
    finding_id = None
    finding_title = inputs.get("finding_title")
    if finding_title:
        for finding in context.get("findings", []):
            if finding.get("title") == finding_title:
                finding_id = finding.get("id")
                break

    # Build vendor options if vendor info provided
    vendor_options = inputs.get("vendor_options", [])
    if inputs.get("vendor_name") and not vendor_options:
        vendor_options = [{
            "name": inputs.get("vendor_name"),
            "category": inputs.get("vendor_category"),
            "monthly_cost": inputs.get("monthly_cost"),
        }]

    recommendation_data = {
        "audit_id": audit_id,
        "finding_id": finding_id,
        "title": inputs.get("title", "Untitled Recommendation"),
        "description": inputs.get("description", ""),
        "implementation_steps": inputs.get("implementation_steps", []),
        "vendor_options": vendor_options,
        "recommended_vendor": inputs.get("vendor_name"),
        "estimated_cost": inputs.get("implementation_cost", inputs.get("estimated_cost")),
        "estimated_annual_savings": inputs.get("estimated_annual_savings"),
        "payback_months": inputs.get("payback_months"),
        "roi_percent": inputs.get("roi_percentage", inputs.get("roi_percent")),
        "implementation_risk": inputs.get("implementation_risk", "medium"),
        "effort_level": inputs.get("effort_level", "moderate"),
        "timeline_weeks": inputs.get("timeline_weeks", inputs.get("implementation_timeline")),
        "assumptions": inputs.get("assumptions", []),
        "priority": inputs.get("priority", 3),
    }

    try:
        result = await supabase.table("recommendations").insert(recommendation_data).execute()

        if result.data:
            rec = result.data[0]
            # Add to context
            context.setdefault("recommendations", []).append(rec)

            return {
                "success": True,
                "recommendation_id": rec["id"],
                "title": rec["title"],
                "message": f"Recommendation created: {rec['title']}",
            }
        else:
            return {"success": False, "error": "Failed to create recommendation"}

    except Exception as e:
        logger.error(f"Create recommendation error: {e}")
        return {"success": False, "error": str(e)}


async def generate_executive_summary(
    inputs: Dict[str, Any],
    context: Dict[str, Any],
    audit_id: str,
) -> Dict[str, Any]:
    """Generate executive summary for the report."""
    supabase = await get_async_supabase()

    key_findings = inputs.get("key_findings", [])
    total_potential_savings = inputs.get("total_potential_savings", 0)
    ai_readiness_summary = inputs.get("ai_readiness_summary", "")

    # Get counts from context
    findings = context.get("findings", [])
    recommendations = context.get("recommendations", [])

    # Calculate metrics
    high_priority_findings = len([f for f in findings if f.get("priority", 5) <= 2])
    quick_wins = len([r for r in recommendations if r.get("payback_months", 99) <= 6])

    summary_data = {
        "audit_id": audit_id,
        "key_findings": key_findings[:5],  # Top 5
        "total_findings": len(findings),
        "total_recommendations": len(recommendations),
        "high_priority_count": high_priority_findings,
        "quick_wins_count": quick_wins,
        "total_potential_savings": total_potential_savings,
        "ai_readiness_summary": ai_readiness_summary,
    }

    # Save summary to reports table
    try:
        # Get client name for title
        client = context.get("client", {})
        client_name = client.get("name", "Company")

        report_data = {
            "audit_id": audit_id,
            "title": f"{client_name} - CRB Analysis Report",
            "executive_summary": ai_readiness_summary,
            "full_content": summary_data,
            "status": "final",
        }

        result = await supabase.table("reports").insert(report_data).execute()

        return {
            "success": True,
            "summary": summary_data,
            "report_id": result.data[0]["id"] if result.data else None,
            "message": "Executive summary generated successfully",
        }

    except Exception as e:
        logger.error(f"Generate summary error: {e}")
        return {
            "success": False,
            "summary": summary_data,
            "error": str(e),
        }
