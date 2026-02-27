"""
Recommendation Models

Implements the AIOS Options pattern (best-fit-first philosophy):
- Connect & Automate: Wire existing tools with AI workflows
- Enhance with AI: Add intelligence layer on top
- Targeted Upgrade: Adopt dedicated tool when it genuinely serves the company best

Backward compatible with legacy Three Options keys.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, Field


# AIOS option types (primary)
AIOSOptionType = Literal["connect_and_automate", "enhance_with_ai", "targeted_upgrade"]

# Legacy option types (backward compat)
LegacyOptionType = Literal["off_the_shelf", "best_in_class", "custom_solution"]

# Combined for flexible validation
OptionType = Literal[
    "connect_and_automate", "enhance_with_ai", "targeted_upgrade",
    "off_the_shelf", "best_in_class", "custom_solution",
]
ConfidenceLevel = Literal["high", "medium", "low"]
TimeHorizon = Literal["short", "mid", "long"]
RiskProbability = Literal["low", "medium", "high"]
FindingCategory = Literal["efficiency", "growth", "risk", "compliance", "customer_experience"]


class CostBreakdown(BaseModel):
    """Cost breakdown by time horizon."""
    software: int = Field(default=0, description="Software/subscription costs")
    implementation: int = Field(default=0, description="One-time implementation cost")
    training: int = Field(default=0, description="Training costs")
    maintenance: int = Field(default=0, description="Ongoing maintenance")
    upgrades: int = Field(default=0, description="Future upgrade costs")


class CostAnalysis(BaseModel):
    """Full cost analysis across time horizons."""
    short_term: CostBreakdown = Field(default_factory=CostBreakdown)
    mid_term: CostBreakdown = Field(default_factory=CostBreakdown)
    long_term: CostBreakdown = Field(default_factory=CostBreakdown)
    total: int = Field(default=0, description="Total cost over projection period")


class BenefitBreakdown(BaseModel):
    """Benefit breakdown by type."""
    value_saved: int = Field(default=0, description="Cost savings from efficiency")
    value_created: int = Field(default=0, description="New revenue/value generated")


class BenefitAnalysis(BaseModel):
    """Full benefit analysis across time horizons."""
    short_term: BenefitBreakdown = Field(default_factory=BenefitBreakdown)
    mid_term: BenefitBreakdown = Field(default_factory=BenefitBreakdown)
    long_term: BenefitBreakdown = Field(default_factory=BenefitBreakdown)
    total: int = Field(default=0, description="Total benefit over projection period")


class RiskItem(BaseModel):
    """Individual risk assessment."""
    description: str = Field(..., description="What could go wrong")
    probability: RiskProbability = Field(default="medium")
    impact: int = Field(default=0, description="Estimated cost if risk occurs")
    mitigation: str = Field(default="", description="How to reduce/avoid this risk")
    time_horizon: TimeHorizon = Field(default="short")


class CRBAnalysis(BaseModel):
    """Full Cost/Risk/Benefit analysis."""
    cost: CostAnalysis = Field(default_factory=CostAnalysis)
    risk: List[RiskItem] = Field(default_factory=list)
    benefit: BenefitAnalysis = Field(default_factory=BenefitAnalysis)


class OptionDetail(BaseModel):
    """
    Detailed option for Three Options pattern.

    Used for off_the_shelf and best_in_class options.
    """
    name: str = Field(..., description="Product/service name, e.g., 'Intercom AI Bot'")
    vendor: str = Field(..., description="Company name, e.g., 'Intercom'")
    monthly_cost: Optional[int] = Field(None, description="Monthly subscription cost in EUR")
    implementation_weeks: int = Field(default=4, description="Weeks to implement")
    implementation_cost: int = Field(default=0, description="One-time setup cost")
    pros: List[str] = Field(default_factory=list, min_length=1)
    cons: List[str] = Field(default_factory=list, min_length=1)

    # Optional fields for additional context
    website: Optional[str] = Field(None, description="Vendor website")
    pricing_tier: Optional[str] = Field(None, description="Which pricing tier recommended")
    integrations: Optional[List[str]] = Field(None, description="Key integrations available")


class CustomSolutionDetail(BaseModel):
    """
    Detailed option for custom/build-it-yourself solutions.

    Includes AI tool recommendations and build guidance per AGENT-3 spec.
    """
    approach: str = Field(..., description="Brief description of custom solution approach")
    estimated_cost: Dict[str, int] = Field(
        default_factory=lambda: {"min": 0, "max": 0},
        description="Cost range for custom build"
    )
    monthly_running_cost: int = Field(default=0, description="Ongoing monthly costs (API, hosting)")
    implementation_weeks: int = Field(default=8, description="Weeks to build")
    pros: List[str] = Field(default_factory=list, min_length=1)
    cons: List[str] = Field(default_factory=list, min_length=1)

    # Build It Yourself fields (required for custom solutions)
    build_tools: List[str] = Field(
        default_factory=list,
        description="Tools needed, e.g., ['Claude API', 'Cursor', 'Vercel']"
    )
    model_recommendation: Optional[str] = Field(
        None,
        description="Specific AI model recommendation with reasoning"
    )
    skills_required: List[str] = Field(
        default_factory=list,
        description="Skills needed, e.g., ['Python', 'Basic API integration']"
    )
    dev_hours_estimate: Optional[str] = Field(
        None,
        description="Development time range, e.g., '80-120 hours'"
    )

    # Additional guidance
    recommended_stack: Optional[Dict[str, str]] = Field(
        None,
        description="Full stack recommendation: {ai_model, ide, hosting, database}"
    )
    key_apis: Optional[List[Dict[str, str]]] = Field(
        None,
        description="APIs needed with pricing info"
    )
    resources: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Helpful resources: {documentation, tutorials, communities}"
    )


class AIOSConnectOption(BaseModel):
    """Connect & Automate option — wire existing tools with AI workflows."""
    approach: str = Field(default="", description="Specific steps connecting existing tools")
    build_time: str = Field(default="", description="e.g., '1 week (solo) / 2 days (guided)'")
    tools_used: List[str] = Field(default_factory=list, description="Existing + new tools")
    mcp_servers: List[str] = Field(default_factory=list)
    monthly_cost: str = Field(default="", description="EUR range")
    prerequisite: Optional[str] = Field(None)
    diy_complexity: Optional[str] = Field(None, description="low|moderate|high")
    automation_flow: Optional[Dict[str, Any]] = Field(None, description="Nodes and edges")
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)

    # AIOS layer enrichment
    aios_layers_touched: List[str] = Field(
        default_factory=list,
        description="Which AIOS layers this option builds (e.g., connections, intelligence, skills)"
    )
    skills_created: Optional[List[str]] = Field(
        None, description="Claude Code skills that result from this implementation"
    )
    context_needed: Optional[List[str]] = Field(
        None, description="Context OS data needed (e.g., client profiles, process docs)"
    )
    education_prereq: Optional[str] = Field(
        None, description="What to learn first (e.g., 'Claude Code basics')"
    )
    cowork_tasks: Optional[List[str]] = Field(
        None, description="Tasks Cowork handles on an ongoing basis"
    )


class AIOSEnhanceOption(BaseModel):
    """Enhance with AI option — add intelligence layer on top."""
    approach: str = Field(default="")
    build_time: str = Field(default="")
    tools_used: List[str] = Field(default_factory=list)
    monthly_cost: str = Field(default="")
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)


class AIOSUpgradeOption(BaseModel):
    """Targeted Upgrade option — adopt dedicated tool when it genuinely serves the company best."""
    when_needed: str = Field(default="", description="When this option genuinely makes sense for this company")
    tools: List[str] = Field(default_factory=list)
    cost_range: str = Field(default="")
    migration_time: str = Field(default="")
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)


class RecommendationOptions(BaseModel):
    """
    AIOS Options pattern — connect-first philosophy.

    Primary keys: connect_and_automate, enhance_with_ai, targeted_upgrade
    Legacy keys: off_the_shelf, best_in_class, custom_solution (still accepted)
    """
    # AIOS format (primary)
    connect_and_automate: Optional[AIOSConnectOption] = Field(
        None, description="Wire existing tools with AI workflows"
    )
    enhance_with_ai: Optional[AIOSEnhanceOption] = Field(
        None, description="Add intelligence layer on top of existing data"
    )
    targeted_upgrade: Optional[AIOSUpgradeOption] = Field(
        None, description="Adopt dedicated SaaS tool when it genuinely serves the company best"
    )

    # Legacy format (backward compat)
    off_the_shelf: Optional[OptionDetail] = Field(None)
    best_in_class: Optional[OptionDetail] = Field(None)
    custom_solution: Optional[CustomSolutionDetail] = Field(None)

    our_recommendation: OptionType = Field(
        ...,
        description="Which option we recommend"
    )
    recommendation_rationale: str = Field(
        ...,
        description="Why we recommend this specific option"
    )


class WhyItMatters(BaseModel):
    """Two Pillars explanation for a recommendation."""
    customer_value: str = Field(..., description="How this helps their customers")
    business_health: str = Field(..., description="How this strengthens the business")


class ValueSaved(BaseModel):
    """Efficiency/time savings calculation."""
    hours_per_week: float = Field(default=0)
    hourly_rate: int = Field(default=50, description="EUR per hour")
    annual_savings: int = Field(default=0, description="Calculated annual savings")
    description: Optional[str] = Field(None)


class ValueCreated(BaseModel):
    """New value/revenue generation."""
    description: str = Field(default="")
    potential_revenue: int = Field(default=0)


class AgentOpportunity(BaseModel):
    """What a CRB-managed agent could automate for this finding."""
    agent_type: str = Field(..., description="e.g., 'Support Agent', 'Returns Processor'")
    what_it_does: str = Field(..., description="Specific tasks the agent handles, 2-3 sentences")
    estimated_impact: Dict[str, Any] = Field(
        ...,
        description="Measurable impact: hours_saved_monthly, tickets_handled, monthly_value_eur, etc."
    )
    deployment_timeline: str = Field(..., description="e.g., '2 weeks'")
    prerequisites: List[str] = Field(
        default_factory=list,
        description="What's needed: 'Shopify store', 'Gorgias account', etc."
    )


class Finding(BaseModel):
    """
    A discovered opportunity or issue from the analysis.

    Implements Two Pillars scoring (Customer Value + Business Health).
    """
    id: str = Field(..., description="Unique identifier, e.g., 'finding-001'")
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., description="What this opportunity is and why it matters")
    category: FindingCategory = Field(default="efficiency")

    # Two Pillars scores (1-10)
    customer_value_score: int = Field(..., ge=1, le=10)
    business_health_score: int = Field(..., ge=1, le=10)

    # Current state
    current_state: Optional[str] = Field(None, description="How they're doing it now")

    # Value calculations
    value_saved: Optional[ValueSaved] = Field(None)
    value_created: Optional[ValueCreated] = Field(None)

    # Confidence and timing
    confidence: ConfidenceLevel = Field(default="medium")
    time_horizon: TimeHorizon = Field(default="mid")

    # Sources (required per AGENT-3 spec)
    sources: List[str] = Field(
        default_factory=list,
        min_length=1,
        description="Evidence sources - quiz responses, benchmarks, calculations"
    )

    # For not-recommended findings
    is_not_recommended: bool = Field(default=False)
    why_not: Optional[str] = Field(None, description="Why NOT to implement this")
    what_instead: Optional[str] = Field(None, description="What to do instead")

    # Agent opportunity (e-commerce only)
    agent_opportunity: Optional[AgentOpportunity] = Field(
        None, description="CRB agent deployment opportunity, included for e-commerce findings"
    )


class Recommendation(BaseModel):
    """
    A full recommendation with Three Options pattern.
    """
    id: str = Field(..., description="Unique identifier, e.g., 'rec-001'")
    finding_id: str = Field(..., description="Related finding ID")
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., description="What we recommend and why")
    priority: Literal["high", "medium", "low"] = Field(default="medium")

    # Two Pillars explanation
    why_it_matters: WhyItMatters

    # Full CRB Analysis
    crb_analysis: CRBAnalysis = Field(default_factory=CRBAnalysis)

    # Three Options (required)
    options: RecommendationOptions

    # ROI summary
    roi_percentage: int = Field(default=0, description="Return on investment percentage")
    payback_months: int = Field(default=0, description="Months until investment recovered")

    # Transparency
    assumptions: List[str] = Field(
        default_factory=list,
        description="All assumptions made in calculations"
    )


class Verdict(BaseModel):
    """
    Honest verdict about whether AI is right for this business.
    """
    recommendation: Literal["proceed", "proceed_cautiously", "wait", "not_recommended"]
    headline: str = Field(..., description="Main verdict message")
    subheadline: str = Field(..., description="Supporting context")
    color: Literal["green", "yellow", "orange", "gray"] = Field(default="yellow")
    confidence: ConfidenceLevel = Field(default="medium")

    # Reasoning
    reasoning: List[str] = Field(default_factory=list, min_length=1)

    # Next steps
    recommended_approach: Optional[List[str]] = Field(None)
    what_to_do_instead: Optional[List[str]] = Field(None)
    when_to_revisit: Optional[str] = Field(None)


class RoadmapItem(BaseModel):
    """Single item in implementation roadmap."""
    title: str
    description: str
    timeline: str = Field(..., description="e.g., 'Week 1-4' or 'Month 3-6'")
    expected_outcome: str
    related_recommendation_id: Optional[str] = None


class Roadmap(BaseModel):
    """Implementation roadmap by time horizon."""
    short_term: List[RoadmapItem] = Field(default_factory=list)
    mid_term: List[RoadmapItem] = Field(default_factory=list)
    long_term: List[RoadmapItem] = Field(default_factory=list)


class ValueSummary(BaseModel):
    """Total value summary for report."""
    value_saved: Dict[str, Any] = Field(default_factory=dict)
    value_created: Dict[str, Any] = Field(default_factory=dict)
    total: Dict[str, int] = Field(default_factory=lambda: {"min": 0, "max": 0})
    projection_years: int = Field(default=3)


class ExecutiveSummary(BaseModel):
    """Report executive summary."""
    ai_readiness_score: int = Field(..., ge=0, le=100)
    customer_value_score: int = Field(..., ge=1, le=10)
    business_health_score: int = Field(..., ge=1, le=10)
    key_insight: str
    total_value_potential: Dict[str, Any]
    top_opportunities: List[Dict[str, Any]]
    not_recommended: List[Dict[str, Any]]
    recommended_investment: Dict[str, int]
    verdict: Optional[Verdict] = None


class MethodologyNotes(BaseModel):
    """Transparency notes about report methodology."""
    data_sources: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    industry_benchmarks_used: List[str] = Field(default_factory=list)
    confidence_notes: str = ""


class Report(BaseModel):
    """
    Complete CRB Analysis Report.
    """
    id: str
    quiz_session_id: str
    tier: str
    status: str

    # Content
    executive_summary: ExecutiveSummary
    findings: List[Finding]
    recommendations: List[Recommendation]
    roadmap: Roadmap
    value_summary: ValueSummary
    methodology_notes: MethodologyNotes

    # Metadata
    generation_started_at: Optional[datetime] = None
    generation_completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
