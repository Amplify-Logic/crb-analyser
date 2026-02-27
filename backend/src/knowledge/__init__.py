"""
Industry Knowledge Base

Provides industry-specific data for CRB analysis including:
- Common processes and pain points
- AI opportunities with ROI examples
- Benchmarks and metrics
- Vendor recommendations (industry-specific and category-based)
- AI tools and LLM provider pricing
"""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.utils.quiz_utils import get_monthly_budget_range

logger = logging.getLogger(__name__)

KNOWLEDGE_BASE_PATH = Path(__file__).parent
PLATFORMS_DIR = KNOWLEDGE_BASE_PATH / "platforms"

# =============================================================================
# VENDOR CATEGORIES (new category-based vendor files)
# =============================================================================

VENDOR_CATEGORIES = [
    "ai_assistants",
    "ai_agents",
    "ai_content_creation",
    "ai_sales_tools",
    "analytics",
    "automation",
    "crm",
    "customer_support",
    "dev_tools",
    "ecommerce",
    "finance",
    "hr_payroll",
    "marketing",
    "project_management",
    "scheduling",
]

AI_TOOLS_TYPES = [
    "llm_providers",
]

# =============================================================================
# INDUSTRY MAPPING (backward compatible)
# =============================================================================

INDUSTRY_MAPPING = {
    # ==========================================================================
    # PRIMARY INDUSTRIES (Launch Priority)
    # ==========================================================================

    # Professional Services (Legal, Accounting, Consulting)
    "professional_services": "professional-services",
    "professional-services": "professional-services",
    "professional services": "professional-services",
    "consulting": "professional-services",
    "legal": "professional-services",
    "law_firm": "professional-services",
    "law firm": "professional-services",
    "accounting": "professional-services",
    "accountant": "professional-services",
    "cpa": "professional-services",
    "bookkeeping": "professional-services",

    # Dental (Practices & DSOs)
    "dental": "dental",
    "dentist": "dental",
    "dental_practice": "dental",
    "dental practice": "dental",
    "dso": "dental",
    "orthodontics": "dental",
    "oral_surgery": "dental",

    # E-commerce (Launch Priority)
    "ecommerce": "ecommerce",
    "e-commerce": "ecommerce",
    "e_commerce": "ecommerce",
    "online_retail": "ecommerce",
    "dtc": "ecommerce",
    "d2c": "ecommerce",
    "online_store": "ecommerce",
    "shopify": "ecommerce",

    # B2B Platforms (Hardware-to-Platform, IoT, Connected Devices)
    "b2b-platforms": "b2b-platforms",
    "b2b-platform": "b2b-platforms",
    "b2b_platforms": "b2b-platforms",
    "b2b platforms": "b2b-platforms",
    "iot": "b2b-platforms",
    "iot-platform": "b2b-platforms",
    "iot_platform": "b2b-platforms",
    "hardware-platform": "b2b-platforms",
    "hardware_platform": "b2b-platforms",
    "connected-devices": "b2b-platforms",
    "connected_devices": "b2b-platforms",
    "device-platform": "b2b-platforms",
    "saas-hardware": "b2b-platforms",
    "water-tech": "b2b-platforms",
    "cleantech": "b2b-platforms",
    "hydration": "b2b-platforms",

    # ==========================================================================
    # SECONDARY INDUSTRIES (Phase 2) - Placeholders for future
    # ==========================================================================

    # Home Services (HVAC, Plumbing, Electrical)
    "home-services": "home-services",
    "home_services": "home-services",
    "home services": "home-services",
    "hvac": "home-services",
    "plumbing": "home-services",
    "plumber": "home-services",
    "electrical": "home-services",
    "electrician": "home-services",
    "contractor": "home-services",
    "home_improvement": "home-services",
    "field_service": "home-services",
    "trades": "home-services",

    # Recruiting/Staffing
    "recruiting": "recruiting",
    "staffing": "recruiting",
    "recruitment": "recruiting",
    "hr_agency": "recruiting",

    # Coaching
    "coaching": "coaching",
    "business_coaching": "coaching",
    "executive_coaching": "coaching",

    # Veterinary/Pet Care
    "veterinary": "veterinary",
    "vet": "veterinary",
    "pet_care": "veterinary",
    "animal_hospital": "veterinary",

    # ==========================================================================
    # EXPANSION INDUSTRIES (Phase 3) - Placeholders for future
    # ==========================================================================

    # Physical Therapy/Chiropractic
    "physical-therapy": "physical-therapy",
    "physical_therapy": "physical-therapy",
    "pt": "physical-therapy",
    "chiropractic": "physical-therapy",
    "chiropractor": "physical-therapy",

    # MedSpa/Beauty
    "medspa": "medspa",
    "med_spa": "medspa",
    "medical_spa": "medspa",
    "beauty": "medspa",
    "aesthetics": "medspa",

    # ==========================================================================
    # LEGACY INDUSTRIES (Dropped - kept for backward compatibility)
    # ==========================================================================

    # Marketing agencies (DROPPED - DIY mentality)
    "marketing": "marketing-agencies",
    "marketing_agency": "marketing-agencies",
    "marketing-agency": "marketing-agencies",
    "marketing-agencies": "marketing-agencies",
    "creative_agency": "marketing-agencies",
    "creative agency": "marketing-agencies",
    "advertising": "marketing-agencies",
    "digital_marketing": "marketing-agencies",

    # Retail (DROPPED - not passion-driven service)
    "retail": "retail",
    "brick_and_mortar": "retail",
    "store": "retail",
    "shops": "retail",

    # Tech companies (DROPPED - DIY mentality)
    "tech": "tech-companies",
    "tech-companies": "tech-companies",
    "technology": "tech-companies",
    "saas": "tech-companies",
    "software": "tech-companies",
    "startup": "tech-companies",

    # Music studios (DROPPED - budget constraints)
    "music": "music-studios",
    "music-studios": "music-studios",
    "music_studio": "music-studios",
    "recording_studio": "music-studios",
    "audio": "music-studios",
    "production": "music-studios",
}

# Primary target industries with full knowledge bases
PRIMARY_INDUSTRIES = [
    "professional-services",
    "dental",
    "ecommerce",
    "b2b-platforms",
]

# Secondary industries (Phase 2) - knowledge bases to be built
SECONDARY_INDUSTRIES = [
    "home-services",
    "recruiting",
    "coaching",
    "veterinary",
]

# Expansion industries (Phase 3) - knowledge bases to be built
EXPANSION_INDUSTRIES = [
    "physical-therapy",
    "medspa",
]

# Legacy industries (still supported but not target market)
LEGACY_INDUSTRIES = [
    "marketing-agencies",
    "retail",
    "tech-companies",
    "music-studios",
]

# All supported industries (for backward compatibility)
SUPPORTED_INDUSTRIES = PRIMARY_INDUSTRIES + SECONDARY_INDUSTRIES + EXPANSION_INDUSTRIES + LEGACY_INDUSTRIES


# =============================================================================
# CORE LOADING FUNCTIONS
# =============================================================================

def normalize_industry(industry: str) -> str:
    """Convert industry input to normalized folder name."""
    normalized = industry.lower().strip().replace(" ", "_")
    return INDUSTRY_MAPPING.get(normalized, "general")


def _load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely."""
    if not file_path.exists():
        logger.debug(f"File not found: {file_path}")
        return None

    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse {file_path}: {e}")
        return None


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
        # Phase 3 expansion industries (physical-therapy, medspa, etc.) may not have KB data yet
        logger.warning(
            f"Industry '{industry}' (normalized: '{normalized}') has no knowledge base data. "
            f"Phase 3 expansion - using general benchmarks."
        )
        return None

    file_path = KNOWLEDGE_BASE_PATH / normalized / f"{data_type}.json"
    return _load_json_file(file_path)


def load_industry_workflows(industry: str) -> Optional[List[Dict[str, Any]]]:
    """
    Load AI workflow templates for an industry.

    Args:
        industry: Industry name (will be normalized)

    Returns:
        List of workflow templates or None if not found
    """
    normalized = normalize_industry(industry)
    file_path = KNOWLEDGE_BASE_PATH / normalized / "workflows.json"
    data = _load_json_file(file_path)
    return data.get("workflows", []) if data else None


# =============================================================================
# NEW: CATEGORY-BASED VENDOR LOADING
# =============================================================================

@lru_cache(maxsize=32)
def load_vendor_category(category: str) -> Optional[Dict[str, Any]]:
    """
    Load vendors for a specific category from vendors/ folder.

    Args:
        category: One of VENDOR_CATEGORIES (e.g., 'crm', 'automation', 'customer_support')

    Returns:
        Vendor category data with list of vendors, or None if not found
    """
    if category not in VENDOR_CATEGORIES:
        logger.warning(f"Unknown vendor category: {category}")
        return None

    file_path = KNOWLEDGE_BASE_PATH / "vendors" / f"{category}.json"
    return _load_json_file(file_path)


def get_all_vendors(categories: List[str] = None) -> List[Dict[str, Any]]:
    """
    Get all vendors, optionally filtered by categories.

    Args:
        categories: List of categories to include (default: all)

    Returns:
        List of all vendor entries
    """
    cats = categories or VENDOR_CATEGORIES
    all_vendors = []

    for category in cats:
        data = load_vendor_category(category)
        if data and "vendors" in data:
            all_vendors.extend(data["vendors"])

    return all_vendors


def search_vendors(
    query: str = None,
    category: str = None,
    company_size: str = None,
    max_price: float = None,
    has_free_tier: bool = None,
) -> List[Dict[str, Any]]:
    """
    Search vendors with filters.

    Args:
        query: Search term to match against name, description, best_for
        category: Filter by vendor category
        company_size: Filter by company size ('startup', 'smb', 'mid-market', 'enterprise')
        max_price: Maximum starting price per month
        has_free_tier: Filter vendors with free tier

    Returns:
        List of matching vendors
    """
    # Get vendors from specified category or all
    if category:
        data = load_vendor_category(category)
        vendors = data.get("vendors", []) if data else []
    else:
        vendors = get_all_vendors()

    results = []

    for vendor in vendors:
        # Text search
        if query:
            query_lower = query.lower()
            searchable = json.dumps(vendor).lower()
            if query_lower not in searchable:
                continue

        # Company size filter
        if company_size:
            vendor_sizes = vendor.get("company_sizes", [])
            if company_size not in vendor_sizes:
                continue

        # Price filter
        if max_price is not None:
            pricing = vendor.get("pricing", {})
            starting = pricing.get("starting_price")
            if starting and starting > max_price:
                continue

        # Free tier filter
        if has_free_tier is not None:
            pricing = vendor.get("pricing", {})
            if pricing.get("free_tier", False) != has_free_tier:
                continue

        results.append(vendor)

    return results


def get_vendor_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific vendor by slug.

    Args:
        slug: Vendor slug (e.g., 'intercom', 'zapier')

    Returns:
        Vendor data or None if not found
    """
    for category in VENDOR_CATEGORIES:
        data = load_vendor_category(category)
        if data and "vendors" in data:
            for vendor in data["vendors"]:
                if vendor.get("slug") == slug:
                    return vendor
    return None


def compare_vendors(slugs: List[str]) -> Dict[str, Any]:
    """
    Get comparison data for multiple vendors.

    Args:
        slugs: List of vendor slugs to compare

    Returns:
        Dict with vendor data and comparison summary
    """
    vendors = []
    for slug in slugs:
        vendor = get_vendor_by_slug(slug)
        if vendor:
            vendors.append(vendor)

    if not vendors:
        return {"vendors": [], "comparison": None}

    # Build comparison summary
    comparison = {
        "pricing_range": {
            "min": min(
                v.get("pricing", {}).get("starting_price", 0)
                for v in vendors if v.get("pricing", {}).get("starting_price")
            ) if any(v.get("pricing", {}).get("starting_price") for v in vendors) else None,
            "max": max(
                v.get("pricing", {}).get("starting_price", 0)
                for v in vendors if v.get("pricing", {}).get("starting_price")
            ) if any(v.get("pricing", {}).get("starting_price") for v in vendors) else None,
        },
        "free_tier_available": any(v.get("pricing", {}).get("free_tier", False) for v in vendors),
        "categories": list(set(v.get("category", "") for v in vendors)),
    }

    return {"vendors": vendors, "comparison": comparison}


# =============================================================================
# NEW: AI TOOLS / LLM PROVIDER LOADING
# =============================================================================

@lru_cache(maxsize=8)
def load_ai_tools(tool_type: str) -> Optional[Dict[str, Any]]:
    """
    Load AI tools data.

    Args:
        tool_type: Type of AI tools ('llm_providers', etc.)

    Returns:
        AI tools data or None
    """
    file_path = KNOWLEDGE_BASE_PATH / "ai_tools" / f"{tool_type}.json"
    return _load_json_file(file_path)


def get_llm_providers() -> List[Dict[str, Any]]:
    """Get all LLM providers with pricing."""
    data = load_ai_tools("llm_providers")
    # Handle both list format and dict with "providers" key
    if isinstance(data, list):
        return data
    return data.get("providers", []) if data else []


def get_llm_provider(slug: str) -> Optional[Dict[str, Any]]:
    """Get a specific LLM provider by slug."""
    providers = get_llm_providers()
    for provider in providers:
        if provider.get("slug") == slug:
            return provider
    return None


def estimate_llm_cost(
    provider_slug: str,
    model_id: str,
    input_tokens: int,
    output_tokens: int
) -> Optional[Dict[str, Any]]:
    """
    Estimate cost for LLM usage.

    Args:
        provider_slug: Provider slug (e.g., 'anthropic', 'openai')
        model_id: Model ID (e.g., 'claude-opus-4-5-20251101')
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Cost estimate with breakdown
    """
    provider = get_llm_provider(provider_slug)
    if not provider:
        return None

    for model in provider.get("models", []):
        if model.get("model_id") == model_id:
            pricing = model.get("pricing", {})
            input_cost = (input_tokens / 1_000_000) * pricing.get("input_per_1m", 0)
            output_cost = (output_tokens / 1_000_000) * pricing.get("output_per_1m", 0)

            return {
                "provider": provider_slug,
                "model": model_id,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "input_cost": round(input_cost, 4),
                "output_cost": round(output_cost, 4),
                "total_cost": round(input_cost + output_cost, 4),
                "currency": "USD",
            }

    return None


# =============================================================================
# BACKWARD COMPATIBLE: INDUSTRY-BASED FUNCTIONS
# =============================================================================

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
        "workflows": load_industry_workflows(industry),
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
    if not categories:
        cats_dict = vendors_data.get("categories", {})
        if isinstance(cats_dict, dict):
            categories = list(cats_dict.values())
        elif isinstance(cats_dict, list):
            categories = cats_dict

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


def get_vendors_within_budget(
    industry: str,
    quiz_answers: Dict[str, Any],
    category: str = None,
    include_over_budget: bool = True,
) -> List[Dict]:
    """
    Get vendor recommendations filtered by user's budget from quiz answers.

    Args:
        industry: Industry name
        quiz_answers: Quiz answers dict containing budget fields
        category: Optional category filter
        include_over_budget: If True, include over-budget vendors but mark them

    Returns:
        List of vendors sorted by budget fit, with budget_fit field added
    """
    all_vendors = get_vendor_recommendations(industry, category)
    if not all_vendors:
        return []

    # Get budget range from quiz answers
    min_budget, max_budget = get_monthly_budget_range(quiz_answers)

    filtered_vendors = []
    over_budget_vendors = []

    for vendor in all_vendors:
        # Get vendor price (try multiple pricing fields)
        pricing = vendor.get("pricing", {})
        monthly_price = (
            pricing.get("starting_price") or
            pricing.get("monthly_price") or
            vendor.get("monthly_price") or
            vendor.get("starting_price") or
            0
        )

        # Determine budget fit
        if monthly_price <= 0:
            # No price info - include with warning
            vendor_copy = vendor.copy()
            vendor_copy["budget_fit"] = "unknown"
            vendor_copy["budget_note"] = "Pricing not available"
            filtered_vendors.append(vendor_copy)
        elif monthly_price <= max_budget:
            # Within budget
            vendor_copy = vendor.copy()
            if monthly_price <= min_budget:
                vendor_copy["budget_fit"] = "comfortable"
            elif monthly_price <= max_budget * 0.7:
                vendor_copy["budget_fit"] = "good"
            else:
                vendor_copy["budget_fit"] = "stretch"
            filtered_vendors.append(vendor_copy)
        else:
            # Over budget
            if include_over_budget:
                vendor_copy = vendor.copy()
                vendor_copy["budget_fit"] = "over_budget"
                vendor_copy["budget_note"] = f"€{monthly_price}/mo exceeds budget (max €{max_budget}/mo)"
                over_budget_vendors.append(vendor_copy)

    # Sort within-budget vendors by fit (comfortable first)
    fit_order = {"comfortable": 0, "good": 1, "stretch": 2, "unknown": 3}
    filtered_vendors.sort(key=lambda v: fit_order.get(v.get("budget_fit", "unknown"), 4))

    # Add over-budget at the end if requested
    if include_over_budget:
        filtered_vendors.extend(over_budget_vendors)

    return filtered_vendors


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


def list_primary_industries() -> List[str]:
    """List primary target industries (launch priority)."""
    return PRIMARY_INDUSTRIES.copy()


def list_secondary_industries() -> List[str]:
    """List secondary target industries (Phase 2)."""
    return SECONDARY_INDUSTRIES.copy()


def list_expansion_industries() -> List[str]:
    """List expansion industries (Phase 3)."""
    return EXPANSION_INDUSTRIES.copy()


def list_legacy_industries() -> List[str]:
    """List legacy/dropped industries (still supported but not target)."""
    return LEGACY_INDUSTRIES.copy()


def get_industry_priority(industry: str) -> str:
    """
    Get the priority tier for an industry.

    Returns: 'primary', 'secondary', 'expansion', 'legacy', or 'unknown'
    """
    normalized = normalize_industry(industry)

    if normalized in PRIMARY_INDUSTRIES:
        return "primary"
    elif normalized in SECONDARY_INDUSTRIES:
        return "secondary"
    elif normalized in EXPANSION_INDUSTRIES:
        return "expansion"
    elif normalized in LEGACY_INDUSTRIES:
        return "legacy"
    else:
        return "unknown"


def list_vendor_categories() -> List[str]:
    """List all vendor categories."""
    return VENDOR_CATEGORIES.copy()


# =============================================================================
# PLATFORM DATA LOADING
# =============================================================================

@lru_cache(maxsize=16)
def load_platform_data(platform_slug: str) -> dict:
    """
    Load a platform JSON file from knowledge/platforms/{slug}.json.

    Args:
        platform_slug: Platform identifier (e.g., 'claude_code', 'mcp_ecosystem')

    Returns:
        Parsed JSON dict, or empty dict if not found
    """
    file_path = PLATFORMS_DIR / f"{platform_slug}.json"

    if not file_path.exists():
        logger.warning(f"Platform file not found: {file_path}")
        return {}

    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse platform file {file_path}: {e}")
        return {}


def get_claude_code_capabilities() -> dict:
    """
    Get the capabilities section from the Claude Code platform data.

    Returns:
        Capabilities dict, or empty dict if not found
    """
    data = load_platform_data("claude_code")
    return data.get("capabilities", {})


def get_mcp_servers(
    category: Optional[str] = None,
    industry: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get MCP servers from the ecosystem data, optionally filtered.

    Args:
        category: Filter by category key (e.g., 'crm', 'payments')
        industry: Filter by industry tag (e.g., 'dental', 'ecommerce')

    Returns:
        Flat list of server dicts matching the filters.
        Returns all servers if no filters are provided.
    """
    data = load_platform_data("mcp_ecosystem")
    categories = data.get("categories", {})

    if not categories:
        return []

    # Determine which categories to scan
    if category:
        cat_data = categories.get(category)
        if not cat_data:
            logger.debug(f"MCP category not found: {category}")
            return []
        category_items = {category: cat_data}
    else:
        category_items = categories

    servers: List[Dict[str, Any]] = []

    for cat_key, cat_data in category_items.items():
        for server in cat_data.get("servers", []):
            if industry:
                server_industries = server.get("industries", [])
                if industry not in server_industries:
                    continue
            servers.append(server)

    return servers


def get_claude_code_building_path(
    opportunity_id: str,
    industry: str,
) -> Optional[Dict[str, Any]]:
    """
    Get the Claude Code building path for a specific opportunity in an industry.

    Loads the industry's opportunities.json, finds the opportunity by ID,
    and returns its claude_code_path field if present.

    Args:
        opportunity_id: Opportunity ID (e.g., 'ai-voice-receptionist')
        industry: Industry name (will be normalized)

    Returns:
        The claude_code_path dict for the opportunity, or None if not found
    """
    opportunities_data = load_industry_data(industry, "opportunities")

    if not opportunities_data:
        return None

    for opp in opportunities_data.get("ai_opportunities", []):
        if opp.get("id") == opportunity_id:
            # claude_code_path can be at top level or inside options
            path = opp.get("claude_code_path")
            if not path:
                path = opp.get("options", {}).get("claude_code_path")
            if path:
                return path
            logger.debug(
                f"Opportunity '{opportunity_id}' in '{industry}' has no claude_code_path"
            )
            return None

    logger.debug(f"Opportunity '{opportunity_id}' not found in '{industry}'")
    return None


# =============================================================================
# FRESHNESS UTILITIES
# =============================================================================

def get_freshness_status(verified_at: str) -> str:
    """
    Get freshness status for a knowledge entry.

    Args:
        verified_at: ISO datetime string

    Returns:
        'fresh' (< 7 days), 'current' (< 30 days),
        'aging' (< 90 days), 'stale' (> 90 days)
    """
    try:
        verified_date = datetime.fromisoformat(verified_at.replace("Z", "+00:00"))
        days_old = (datetime.now(verified_date.tzinfo) - verified_date).days

        if days_old <= 7:
            return "fresh"
        elif days_old <= 30:
            return "current"
        elif days_old <= 90:
            return "aging"
        else:
            return "stale"
    except (ValueError, AttributeError):
        return "unknown"
