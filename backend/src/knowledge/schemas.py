"""
Pydantic schemas for knowledge base validation.

These schemas match the AGENT-4 specification for:
- Vendor database entries
- AI tool/LLM provider data
- Industry benchmarks
- Opportunity templates
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, HttpUrl


# =============================================================================
# VENDOR SCHEMAS
# =============================================================================

class PricingTier(BaseModel):
    """Individual pricing tier for a vendor."""
    name: str
    price: float
    per: str = Field(description="e.g., 'seat/month', 'month', 'usage'")
    billing: Literal["monthly", "annual", "usage_based"] = "annual"
    features: List[str] = []
    limits: Optional[Dict[str, Any]] = None


class VendorPricing(BaseModel):
    """Vendor pricing structure."""
    model: Literal["per_seat", "flat", "usage_based", "tiered", "freemium", "custom"]
    currency: str = "USD"
    billing_options: List[str] = ["monthly", "annual"]
    annual_discount_percent: Optional[int] = None
    tiers: List[PricingTier] = []
    starting_price: Optional[float] = Field(None, description="Lowest starting price")
    custom_pricing: bool = False
    free_trial_days: Optional[int] = None
    free_tier: bool = False
    startup_discount: Optional[str] = None


class VendorImplementation(BaseModel):
    """Implementation details for a vendor."""
    avg_weeks: int = Field(description="Average implementation time in weeks")
    complexity: Literal["low", "medium", "high"]
    requires_developer: bool = False
    cost_range: Optional[Dict[str, Dict[str, int]]] = Field(
        None,
        description="Cost ranges for DIY, with_help, full_service"
    )


class VendorRatings(BaseModel):
    """Vendor ratings from various sources."""
    g2: Optional[Dict[str, Any]] = None
    capterra: Optional[Dict[str, Any]] = None
    trustpilot: Optional[Dict[str, Any]] = None
    our_rating: Optional[float] = Field(None, ge=0, le=5)
    our_notes: Optional[str] = None


class Vendor(BaseModel):
    """Complete vendor entry matching AGENT-4 spec."""
    slug: str = Field(description="URL-friendly identifier")
    name: str
    category: str
    subcategory: Optional[str] = None
    website: str
    pricing_url: Optional[str] = None

    description: str
    tagline: Optional[str] = None

    pricing: VendorPricing

    best_for: List[str] = Field(default=[], description="Target use cases")
    industries: List[str] = Field(default=[], description="Target industries")
    company_sizes: List[str] = Field(default=[], description="e.g., startup, smb, enterprise")
    avoid_if: List[str] = Field(default=[], description="When NOT to recommend")

    implementation: Optional[VendorImplementation] = None
    ratings: Optional[VendorRatings] = None

    integrations: List[str] = []
    api: Optional[Dict[str, Any]] = None
    competitors: List[str] = []

    verified_at: datetime
    verified_by: Literal["manual", "automated", "ai_extracted"] = "manual"
    source_url: Optional[str] = None
    notes: Optional[str] = None


class VendorCategory(BaseModel):
    """A category of vendors."""
    category: str
    description: str
    vendors: List[Vendor]
    last_updated: datetime


# =============================================================================
# AI TOOLS / LLM PROVIDER SCHEMAS
# =============================================================================

class LLMModelPricing(BaseModel):
    """Pricing for a specific LLM model."""
    input_per_1m: float = Field(description="Cost per 1M input tokens")
    output_per_1m: float = Field(description="Cost per 1M output tokens")
    cached_input_per_1m: Optional[float] = None
    batch_input_per_1m: Optional[float] = None
    batch_output_per_1m: Optional[float] = None


class LLMModel(BaseModel):
    """Individual LLM model details."""
    name: str
    model_id: str
    description: str
    best_for: List[str]
    context_window: int
    max_output_tokens: Optional[int] = None
    pricing: LLMModelPricing
    speed: Literal["fastest", "fast", "medium", "slower", "slowest"]
    quality: Literal["good", "high", "very_high", "highest"]
    supports_vision: bool = False
    supports_tools: bool = True


class LLMUseCaseEstimate(BaseModel):
    """Monthly cost estimate for a use case."""
    recommended_model: str
    monthly_cost_estimate: Dict[str, float] = Field(
        description="Cost by volume: low_volume, medium_volume, high_volume"
    )
    implementation_hours: Optional[str] = None
    note: Optional[str] = None


class LLMProvider(BaseModel):
    """LLM API provider entry."""
    slug: str
    name: str
    provider: str
    category: str = "ai_development"
    subcategory: str = "llm_api"
    website: str
    pricing_url: str
    docs_url: Optional[str] = None

    models: List[LLMModel]
    use_cases: Dict[str, LLMUseCaseEstimate] = {}
    compared_to: Dict[str, str] = Field(
        default={},
        description="Comparison notes vs other providers"
    )

    verified_at: datetime
    notes: Optional[str] = None


class AIDevTool(BaseModel):
    """AI development tool (IDE, no-code, etc.)."""
    slug: str
    name: str
    category: str
    subcategory: str
    website: str
    pricing_url: Optional[str] = None

    description: str

    pricing: VendorPricing

    best_for: List[str] = []
    features: List[str] = []
    integrations: List[str] = []

    verified_at: datetime
    notes: Optional[str] = None


# =============================================================================
# BENCHMARK SCHEMAS
# =============================================================================

class BenchmarkMetric(BaseModel):
    """Individual benchmark metric with percentiles."""
    value: Optional[float] = None
    description: str
    unit: str
    percentiles: Optional[Dict[str, float]] = Field(
        None,
        description="p25, p50, p75 percentile values"
    )
    low: Optional[float] = None
    median: Optional[float] = None
    high: Optional[float] = None
    source: str
    source_url: Optional[str] = None
    year: Optional[int] = None


class AutomationPotential(BaseModel):
    """Automation potential for a business area."""
    automatable_percent: int = Field(ge=0, le=100)
    typical_savings: str = Field(description="e.g., '40-60%'")
    implementation_difficulty: Literal["low", "medium", "high"]
    notes: Optional[str] = None


class IndustryBenchmarks(BaseModel):
    """Industry benchmarks with company size segmentation."""
    industry: str
    company_size: str = Field(description="e.g., 'micro', 'small', 'medium'")

    operational_metrics: Dict[str, BenchmarkMetric] = {}
    financial_metrics: Dict[str, BenchmarkMetric] = {}
    ai_adoption_metrics: Dict[str, BenchmarkMetric] = {}
    automation_potential: Dict[str, AutomationPotential] = {}

    verified_at: datetime
    notes: Optional[str] = None


# =============================================================================
# OPPORTUNITY TEMPLATE SCHEMAS
# =============================================================================

class TypicalFindings(BaseModel):
    """Typical findings ranges for an opportunity."""
    hours_saved_weekly: Optional[Dict[str, int]] = Field(
        None, description="min/max hours saved per week"
    )
    cost_reduction_percent: Optional[Dict[str, int]] = Field(
        None, description="min/max cost reduction percentage"
    )
    revenue_impact: Optional[Dict[str, int]] = None
    customer_satisfaction_improvement: Optional[Dict[str, int]] = None


class SolutionOption(BaseModel):
    """Solution option for an opportunity."""
    tools: List[str]
    cost_range: str = Field(description="e.g., '$50-200/month'")
    pros: List[str]
    cons: List[str]


class OpportunityTemplate(BaseModel):
    """Pre-built opportunity template."""
    id: str
    title: str
    category: Literal[
        "efficiency", "growth", "risk", "compliance",
        "customer_experience", "cost_reduction"
    ]

    typical_findings: TypicalFindings

    relevant_if: List[str] = Field(
        description="Conditions when this opportunity is relevant"
    )

    recommended_solutions: Dict[str, SolutionOption] = Field(
        description="off_the_shelf, best_in_class, custom options"
    )

    implementation_notes: Optional[str] = None
    quick_win: bool = False


class IndustryOpportunities(BaseModel):
    """Opportunity templates for an industry."""
    industry: str
    opportunities: List[OpportunityTemplate]
    quick_wins: List[Dict[str, Any]] = []
    not_recommended: List[Dict[str, Any]] = []

    verified_at: datetime


# =============================================================================
# FRESHNESS UTILITIES
# =============================================================================

def get_freshness_status(verified_at: datetime) -> str:
    """
    Get freshness status for a knowledge entry.

    Returns:
        'fresh' (< 7 days), 'current' (< 30 days),
        'aging' (< 90 days), 'stale' (> 90 days)
    """
    days_old = (datetime.now() - verified_at).days

    if days_old <= 7:
        return "fresh"
    elif days_old <= 30:
        return "current"
    elif days_old <= 90:
        return "aging"
    else:
        return "stale"
