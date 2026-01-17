"""
Four Options Models

Data models for BUY/CONNECT/BUILD/HIRE recommendation system.
"""

from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class OptionType(str, Enum):
    """The four implementation options."""
    BUY = "buy"
    CONNECT = "connect"
    BUILD = "build"
    HIRE = "hire"


class CostEstimate(BaseModel):
    """Cost breakdown for TCO calculations."""
    upfront: float = Field(default=0, description="One-time costs")
    monthly: float = Field(default=0, description="Recurring monthly")
    year_one_total: float = Field(default=0, description="Total first year cost")
    year_three_total: float = Field(default=0, description="Total 3-year cost")


class OptionScore(BaseModel):
    """
    Weighted score for a single option.

    Score is 0-100 based on:
    - capability_match (30%)
    - preference_match (20%)
    - budget_fit (20%)
    - time_fit (15%)
    - value_ratio (15%)
    """
    option: OptionType
    score: float = Field(..., ge=0, le=100)
    breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Individual factor scores"
    )
    match_reasons: List[str] = Field(
        default_factory=list,
        description="Why this option scores well (max 3)"
    )
    concern_reasons: List[str] = Field(
        default_factory=list,
        description="Why this option loses points (max 2)"
    )
    is_recommended: bool = Field(
        default=False,
        description="True if this is the top-scoring option"
    )


class NextStep(BaseModel):
    """A single actionable step."""
    order: int
    action: str
    time_estimate: str
    help_link: Optional[str] = None


class BuyOption(BaseModel):
    """
    BUY option: Pre-built SaaS solution.

    Best when: User wants turnkey, no technical skills needed.
    """
    vendor_slug: str = Field(..., description="Vendor identifier")
    vendor_name: str = Field(..., description="Display name")
    price: str = Field(..., description="e.g., '12/mo' or '144/year'")
    setup_time: str = Field(..., description="e.g., '30 minutes'")
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    website: Optional[str] = None
    next_steps: List[NextStep] = Field(default_factory=list)
    cost: CostEstimate = Field(default_factory=CostEstimate)


class ConnectOption(BaseModel):
    """
    CONNECT option: Integrate existing tools via automation.

    Best when: User has existing tools with APIs, some automation comfort.
    """
    integration_platform: str = Field(
        ...,
        description="Make, n8n, Zapier, etc."
    )
    connects_to: List[str] = Field(
        default_factory=list,
        description="Tools being connected"
    )
    estimated_hours: int = Field(..., description="Setup hours")
    complexity: str = Field(default="medium", description="low/medium/high")
    template_url: Optional[str] = Field(
        None,
        description="Link to pre-built template if exists"
    )
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    next_steps: List[NextStep] = Field(default_factory=list)
    cost: CostEstimate = Field(default_factory=CostEstimate)


class BuildOption(BaseModel):
    """
    BUILD option: Custom solution with AI coding tools.

    Best when: User has dev skills OR willing to learn AI coding tools.
    """
    recommended_stack: List[str] = Field(
        default_factory=list,
        description="e.g., ['Claude Code', 'Supabase', 'Vercel']"
    )
    estimated_cost: str = Field(..., description="e.g., '2K-5K'")
    estimated_hours: str = Field(..., description="e.g., '20-40 hours'")
    skills_needed: List[str] = Field(default_factory=list)
    ai_coding_viable: bool = Field(
        default=True,
        description="Can non-dev build this with AI tools?"
    )
    approach: Optional[str] = Field(
        None,
        description="Brief description of what to build"
    )
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    next_steps: List[NextStep] = Field(default_factory=list)
    cost: CostEstimate = Field(default_factory=CostEstimate)


class HireOption(BaseModel):
    """
    HIRE option: Agency or freelancer builds it.

    Best when: User wants custom but lacks time/skills.
    """
    service_type: str = Field(
        ...,
        description="Agency, Freelancer, or Consultant"
    )
    estimated_cost: str = Field(..., description="e.g., '3K-8K'")
    estimated_timeline: str = Field(..., description="e.g., '2-3 weeks'")
    where_to_find: List[str] = Field(
        default_factory=list,
        description="Upwork, Toptal, etc."
    )
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    next_steps: List[NextStep] = Field(default_factory=list)
    cost: CostEstimate = Field(default_factory=CostEstimate)


class TradeoffRow(BaseModel):
    """Single row in comparison table."""
    metric: str
    buy: str
    connect: str
    build: str
    hire: str


class FourOptionRecommendation(BaseModel):
    """
    Complete 4-option recommendation for a finding.

    Includes all four options, scores, and the recommended path.
    """
    finding_id: str
    finding_title: str

    # The four options (all required, but may be marked as "not viable")
    buy: BuyOption
    connect: Optional[ConnectOption] = None
    build: Optional[BuildOption] = None
    hire: Optional[HireOption] = None

    # Scoring
    scores: List[OptionScore] = Field(default_factory=list)
    recommended: OptionType
    recommendation_reasoning: str

    # Comparison table data
    tradeoff_table: List[TradeoffRow] = Field(default_factory=list)

    # Growth path
    growth_path: Optional[str] = Field(
        None,
        description="How this option can evolve over time"
    )

    # Edge case handling
    no_good_match: bool = Field(
        default=False,
        description="True if all options score below 50%"
    )
    fallback_message: Optional[str] = Field(
        None,
        description="Guidance when no option fits well"
    )
