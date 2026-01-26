"""
Platform Consolidation Skill

Identifies when multiple findings can be solved by a single platform solution
rather than recommending separate vendors for each finding.

Platform categories (pick ONE, it solves many problems):
- Field Service Management (FSM): scheduling, dispatch, invoicing, quoting, CRM
- Practice Management: scheduling, billing, patient records, communication
- All-in-one CRM: sales, marketing, support, automation

Point solution categories (can add alongside platforms):
- Review/Reputation management
- Call answering/AI phone
- Payments/Financing
- Specialized automation (Make/Zapier)

This skill runs BEFORE individual recommendations to:
1. Group findings by what platform could solve them
2. Recommend ONE platform for the group
3. Only recommend point solutions for gaps
"""

import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# Platform categories - vendors that solve MULTIPLE finding types
# Key: category slug, Value: finding categories/keywords it addresses
PLATFORM_CATEGORIES = {
    "field-service-management": {
        "display_name": "Field Service Management",
        "solves": [
            "scheduling", "dispatch", "invoicing", "quoting", "quotes",
            "job management", "customer management", "CRM", "booking",
            "appointments", "estimates", "billing", "payments",
            "field service", "work orders", "time tracking"
        ],
        "vendors": ["servicetitan", "housecall-pro", "jobber", "fieldedge",
                   "service-fusion", "workwave", "kickserv", "simPRO",
                   "tradify", "servicem8", "fergus"],
        "pick_one": True,  # Only recommend ONE from this category
    },
    "dental-practice-management": {
        "display_name": "Dental Practice Management",
        "solves": [
            "scheduling", "patient records", "billing", "insurance",
            "treatment plans", "clinical notes", "imaging", "charting"
        ],
        "vendors": ["dentrix", "eaglesoft", "open-dental", "curve-dental",
                   "denticon", "tab32", "planet-dds"],
        "pick_one": True,
    },
    "professional-services-automation": {
        "display_name": "Professional Services Automation (PSA)",
        "solves": [
            "project management", "time tracking", "billing", "resource planning",
            "client management", "invoicing", "reporting"
        ],
        "vendors": ["connectwise", "autotask", "halo-psa", "syncro"],
        "pick_one": True,
    },
    "all-in-one-crm": {
        "display_name": "All-in-One CRM",
        "solves": [
            "CRM", "sales", "marketing", "email", "automation",
            "lead management", "pipeline", "customer support"
        ],
        "vendors": ["hubspot", "salesforce", "zoho-crm", "pipedrive", "monday-crm"],
        "pick_one": True,
    },
}

# Point solution categories - can recommend alongside platforms
POINT_SOLUTION_CATEGORIES = {
    "reputation-management": {
        "display_name": "Reputation & Reviews",
        "solves": ["reviews", "reputation", "customer feedback", "NPS"],
        "vendors": ["podium", "birdeye", "broadly", "nicejob"],
        "pick_one": False,  # Can add one as complement
    },
    "call-handling": {
        "display_name": "AI Call Handling",
        "solves": ["call answering", "after hours", "missed calls", "phone"],
        "vendors": ["smith-ai", "ruby", "answerconnect", "patlive"],
        "pick_one": False,
    },
    "automation-integration": {
        "display_name": "Automation & Integration",
        "solves": ["automation", "integration", "workflow", "connect tools"],
        "vendors": ["make", "zapier", "n8n", "workato"],
        "pick_one": False,
    },
    "payments-financing": {
        "display_name": "Payments & Financing",
        "solves": ["financing", "payment plans", "BNPL", "customer financing"],
        "vendors": ["wisetack", "greensky", "hearth", "enerbank"],
        "pick_one": False,
    },
}


@dataclass
class PlatformRecommendation:
    """A consolidated platform recommendation that solves multiple findings."""
    category: str
    display_name: str
    recommended_vendor: str
    solves_findings: List[str]  # Finding IDs this platform addresses
    finding_titles: List[str]   # For display
    why_this_vendor: str
    alternatives: List[str]
    estimated_monthly_cost: float


@dataclass
class ConsolidationResult:
    """Result of platform consolidation analysis."""
    platform_recommendations: List[PlatformRecommendation]
    point_solution_findings: List[str]  # Finding IDs that need point solutions
    already_covered_findings: Set[str]  # Finding IDs covered by platforms
    consolidation_savings: str  # e.g., "Using one FSM instead of 3 tools saves €200/mo"


def normalize_text(text: str) -> str:
    """Normalize text for matching."""
    return text.lower().strip()


def finding_matches_category(finding: Dict[str, Any], solves: List[str]) -> bool:
    """Check if a finding matches any of the problems a category solves."""
    text_to_check = normalize_text(" ".join([
        finding.get("title", ""),
        finding.get("description", ""),
        finding.get("category", ""),
    ]))

    for keyword in solves:
        if normalize_text(keyword) in text_to_check:
            return True
    return False


def identify_platform_opportunities(
    findings: List[Dict[str, Any]],
    industry: str,
    existing_stack: Optional[List[Dict[str, Any]]] = None,
) -> ConsolidationResult:
    """
    Analyze findings to identify platform consolidation opportunities.

    Returns which findings can be solved by a single platform vs needing
    individual point solutions.
    """
    # Track which findings map to which platform categories
    platform_matches: Dict[str, List[Dict[str, Any]]] = {}
    point_solution_matches: Dict[str, List[Dict[str, Any]]] = {}

    for finding in findings:
        # Skip not-recommended findings
        if finding.get("is_not_recommended"):
            continue

        finding_id = finding.get("id", "")

        # Check platform categories first
        matched_platform = False
        for cat_slug, cat_info in PLATFORM_CATEGORIES.items():
            if finding_matches_category(finding, cat_info["solves"]):
                if cat_slug not in platform_matches:
                    platform_matches[cat_slug] = []
                platform_matches[cat_slug].append(finding)
                matched_platform = True
                break  # A finding only matches ONE platform category

        # If no platform match, check point solutions
        if not matched_platform:
            for cat_slug, cat_info in POINT_SOLUTION_CATEGORIES.items():
                if finding_matches_category(finding, cat_info["solves"]):
                    if cat_slug not in point_solution_matches:
                        point_solution_matches[cat_slug] = []
                    point_solution_matches[cat_slug].append(finding)
                    break

    # Build platform recommendations for categories with 2+ findings
    platform_recommendations = []
    covered_findings: Set[str] = set()

    for cat_slug, matched_findings in platform_matches.items():
        if len(matched_findings) >= 2:  # Only consolidate if 2+ findings match
            cat_info = PLATFORM_CATEGORIES[cat_slug]

            # Select best vendor for this industry/context
            recommended_vendor = _select_best_vendor(
                cat_info["vendors"],
                industry,
                existing_stack,
            )

            finding_ids = [f.get("id", "") for f in matched_findings]
            finding_titles = [f.get("title", "") for f in matched_findings]

            platform_recommendations.append(PlatformRecommendation(
                category=cat_slug,
                display_name=cat_info["display_name"],
                recommended_vendor=recommended_vendor,
                solves_findings=finding_ids,
                finding_titles=finding_titles,
                why_this_vendor=f"Addresses {len(matched_findings)} of your findings in one platform",
                alternatives=cat_info["vendors"][:3],
                estimated_monthly_cost=0,  # Will be filled by caller
            ))

            covered_findings.update(finding_ids)

    # Identify findings that still need individual recommendations
    point_solution_finding_ids = []
    for cat_slug, matched_findings in point_solution_matches.items():
        for f in matched_findings:
            fid = f.get("id", "")
            if fid not in covered_findings:
                point_solution_finding_ids.append(fid)

    # Also add any platform findings with only 1 match (not worth consolidating)
    for cat_slug, matched_findings in platform_matches.items():
        if len(matched_findings) == 1:
            fid = matched_findings[0].get("id", "")
            if fid not in covered_findings:
                point_solution_finding_ids.append(fid)

    # Calculate consolidation savings message
    total_consolidated = len(covered_findings)
    savings_msg = ""
    if total_consolidated >= 2:
        savings_msg = (
            f"By using {len(platform_recommendations)} platform(s) instead of "
            f"{total_consolidated} separate tools, you simplify your stack and "
            f"reduce integration complexity."
        )

    return ConsolidationResult(
        platform_recommendations=platform_recommendations,
        point_solution_findings=point_solution_finding_ids,
        already_covered_findings=covered_findings,
        consolidation_savings=savings_msg,
    )


def _select_best_vendor(
    vendors: List[str],
    industry: str,
    existing_stack: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Select the best vendor from a list based on industry and context.

    For now, uses simple heuristics. Could be enhanced with:
    - Industry-specific tier data
    - Company size matching
    - Existing stack compatibility
    """
    # Check if user already has one of these vendors
    if existing_stack:
        existing_slugs = {
            tool.get("slug", "").lower()
            for tool in existing_stack
        }
        for vendor in vendors:
            if vendor.lower() in existing_slugs:
                return vendor  # They already have it, recommend sticking with it

    # Industry-specific preferences
    industry_preferences = {
        "home-services": ["jobber", "housecall-pro", "servicetitan"],
        "home_services": ["jobber", "housecall-pro", "servicetitan"],
        "dental": ["dentrix", "curve-dental", "open-dental"],
        "professional-services": ["connectwise", "hubspot"],
    }

    preferred = industry_preferences.get(industry.lower(), [])
    for vendor in preferred:
        if vendor in vendors:
            return vendor

    # Default to first vendor
    return vendors[0] if vendors else "unknown"


def get_platform_for_finding(
    finding: Dict[str, Any],
    consolidation_result: ConsolidationResult,
) -> Optional[PlatformRecommendation]:
    """
    Get the platform recommendation that covers a specific finding.

    Returns None if the finding should get individual point solution.
    """
    finding_id = finding.get("id", "")

    for platform_rec in consolidation_result.platform_recommendations:
        if finding_id in platform_rec.solves_findings:
            return platform_rec

    return None


# Export for skill discovery
__all__ = [
    "identify_platform_opportunities",
    "get_platform_for_finding",
    "PlatformRecommendation",
    "ConsolidationResult",
    "PLATFORM_CATEGORIES",
    "POINT_SOLUTION_CATEGORIES",
]
