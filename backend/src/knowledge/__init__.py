"""
Industry Knowledge Base

Provides industry-specific data for CRB analysis including:
- Common processes and pain points
- AI opportunities with ROI examples
- Benchmarks and metrics
- Vendor recommendations
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

KNOWLEDGE_BASE_PATH = Path(__file__).parent

# Industry mapping - normalize various inputs to folder names
INDUSTRY_MAPPING = {
    # Marketing agencies
    "marketing": "marketing-agencies",
    "marketing_agency": "marketing-agencies",
    "marketing-agency": "marketing-agencies",
    "marketing-agencies": "marketing-agencies",
    "creative_agency": "marketing-agencies",
    "creative agency": "marketing-agencies",
    "advertising": "marketing-agencies",
    "digital_marketing": "marketing-agencies",

    # E-commerce
    "ecommerce": "ecommerce",
    "e-commerce": "ecommerce",
    "e_commerce": "ecommerce",
    "online_retail": "ecommerce",
    "dtc": "ecommerce",
    "d2c": "ecommerce",

    # Retail
    "retail": "retail",
    "brick_and_mortar": "retail",
    "store": "retail",
    "shops": "retail",

    # Tech companies
    "tech": "tech-companies",
    "tech-companies": "tech-companies",
    "technology": "tech-companies",
    "saas": "tech-companies",
    "software": "tech-companies",
    "startup": "tech-companies",

    # Music studios
    "music": "music-studios",
    "music-studios": "music-studios",
    "music_studio": "music-studios",
    "recording_studio": "music-studios",
    "audio": "music-studios",
    "production": "music-studios",
}

SUPPORTED_INDUSTRIES = [
    "marketing-agencies",
    "ecommerce",
    "retail",
    "tech-companies",
    "music-studios",
]


def normalize_industry(industry: str) -> str:
    """Convert industry input to normalized folder name."""
    normalized = industry.lower().strip().replace(" ", "_")
    return INDUSTRY_MAPPING.get(normalized, "general")


def load_industry_data(industry: str, data_type: str) -> Optional[Dict[str, Any]]:
    """
    Load specific data type for an industry.

    Args:
        industry: Industry name (will be normalized)
        data_type: One of 'processes', 'opportunities', 'benchmarks', 'vendors'

    Returns:
        Loaded JSON data or None if not found
    """
    normalized = normalize_industry(industry)

    if normalized == "general" or normalized not in SUPPORTED_INDUSTRIES:
        logger.warning(f"Industry '{industry}' not found, using general fallback")
        return None

    file_path = KNOWLEDGE_BASE_PATH / normalized / f"{data_type}.json"

    if not file_path.exists():
        logger.warning(f"Data file not found: {file_path}")
        return None

    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse {file_path}: {e}")
        return None


def get_industry_context(industry: str) -> Dict[str, Any]:
    """
    Load all available data for an industry.

    Returns a dict with all available knowledge for the industry.
    """
    normalized = normalize_industry(industry)

    context = {
        "industry": normalized,
        "is_supported": normalized in SUPPORTED_INDUSTRIES,
        "processes": load_industry_data(industry, "processes"),
        "opportunities": load_industry_data(industry, "opportunities"),
        "benchmarks": load_industry_data(industry, "benchmarks"),
        "vendors": load_industry_data(industry, "vendors"),
    }

    # Add summary stats
    if context["processes"]:
        context["process_count"] = len(context["processes"].get("common_processes", []))

    if context["opportunities"]:
        context["opportunity_count"] = len(context["opportunities"].get("ai_opportunities", []))
        context["quick_wins"] = context["opportunities"].get("quick_wins", [])
        context["not_recommended"] = context["opportunities"].get("not_recommended", [])

    return context


def get_relevant_opportunities(industry: str, pain_points: List[str] = None) -> List[Dict]:
    """
    Get AI opportunities relevant to specific pain points.

    Args:
        industry: Industry name
        pain_points: List of pain point keywords to match against

    Returns:
        List of relevant opportunities sorted by potential impact
    """
    opportunities_data = load_industry_data(industry, "opportunities")

    if not opportunities_data:
        return []

    opportunities = opportunities_data.get("ai_opportunities", [])

    if not pain_points:
        # Return all sorted by business health score
        return sorted(
            opportunities,
            key=lambda x: x.get("business_health_score", 0) + x.get("customer_value_score", 0),
            reverse=True
        )

    # Filter and rank by relevance to pain points
    pain_point_set = set(p.lower() for p in pain_points)

    def relevance_score(opp: Dict) -> int:
        score = opp.get("business_health_score", 0) + opp.get("customer_value_score", 0)

        # Boost if matches pain points
        opp_text = json.dumps(opp).lower()
        for pain_point in pain_point_set:
            if pain_point in opp_text:
                score += 5

        return score

    return sorted(opportunities, key=relevance_score, reverse=True)


def get_benchmarks_for_metrics(industry: str, metric_category: str = None) -> Dict[str, Any]:
    """
    Get industry benchmarks, optionally filtered by category.

    Args:
        industry: Industry name
        metric_category: Optional category like 'financial', 'operational', 'ai_adoption'
    """
    benchmarks = load_industry_data(industry, "benchmarks")

    if not benchmarks:
        return {}

    if metric_category:
        return benchmarks.get("benchmarks", {}).get(metric_category, {})

    return benchmarks.get("benchmarks", {})


def get_vendor_recommendations(industry: str, category: str = None) -> List[Dict]:
    """
    Get vendor recommendations for an industry.

    Args:
        industry: Industry name
        category: Optional category like 'ai-content-creation', 'ai-reporting'
    """
    vendors_data = load_industry_data(industry, "vendors")

    if not vendors_data:
        return []

    categories = vendors_data.get("vendor_categories", [])

    if category:
        for cat in categories:
            if cat.get("category") == category:
                return cat.get("vendors", [])
        return []

    # Return all vendors
    all_vendors = []
    for cat in categories:
        all_vendors.extend(cat.get("vendors", []))

    return all_vendors


# Quick access functions for common queries
def get_quick_wins(industry: str) -> List[Dict]:
    """Get quick wins for an industry."""
    opportunities = load_industry_data(industry, "opportunities")
    return opportunities.get("quick_wins", []) if opportunities else []


def get_not_recommended(industry: str) -> List[Dict]:
    """Get things NOT recommended for an industry."""
    opportunities = load_industry_data(industry, "opportunities")
    return opportunities.get("not_recommended", []) if opportunities else []


def list_supported_industries() -> List[str]:
    """List all supported industries."""
    return SUPPORTED_INDUSTRIES.copy()
