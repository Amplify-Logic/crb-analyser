"""
Finding Paths Models - Connect vs Replace

Models for the Connect vs Replace automation paths in findings.
Each finding can have both paths, with a verdict recommending one approach.

Connect Path: Use existing tools to build automation
Replace Path: Switch to new software that provides the capability

Each path includes full CRB (Cost-Risk-Benefit) analysis.
See:
- docs/plans/2026-01-07-connect-vs-replace-design.md
- docs/handoffs/2026-01-07-master-roadmap.md (CRB Framework)
"""

from typing import Optional, List, Literal

from pydantic import BaseModel, Field

from src.models.crb import (
    CostBreakdown,
    RiskAssessment,
    BenefitQuantification,
    CRBAnalysis,
)


class StackItem(BaseModel):
    """A tool from the user's existing software stack."""
    slug: str = Field(..., description="Vendor slug or custom identifier")
    name: str = Field(..., description="Display name")
    api_score: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="API openness score 1-5"
    )
    category: Optional[str] = Field(None, description="Software category")
    has_api: Optional[bool] = Field(None, description="Has documented API")
    has_webhooks: Optional[bool] = Field(None, description="Supports webhooks")
    has_zapier: Optional[bool] = Field(None, description="Has Zapier integration")


class ConnectPath(BaseModel):
    """
    The Connect path: How to solve with existing tools.

    Shows how to build automation using the user's current software stack
    via APIs, webhooks, or integration platforms like n8n/Make/Zapier.

    Includes full CRB (Cost-Risk-Benefit) analysis.
    """
    integration_flow: str = Field(
        ...,
        description=(
            "Integration flow diagram as text, e.g., "
            "'Open Dental -> n8n -> Twilio SMS'"
        )
    )
    flow_steps: List[str] = Field(
        default_factory=list,
        description="Detailed steps to implement the integration"
    )
    what_it_does: str = Field(
        ...,
        description="Brief description of what this automation accomplishes"
    )

    # Legacy fields (kept for backwards compatibility, prefer CRB structure)
    monthly_cost_estimate: float = Field(
        default=0,
        ge=0,
        description="Estimated monthly cost in EUR (legacy, use crb.cost)"
    )
    setup_effort_hours: float = Field(
        default=0,
        ge=0,
        description="Estimated hours to set up (legacy, use crb.cost)"
    )

    # CRB Analysis (the new standard)
    crb: Optional[CRBAnalysis] = Field(
        None,
        description="Full Cost-Risk-Benefit analysis for this Connect path"
    )

    # Backwards-compatible individual CRB components (for migration)
    cost: Optional[CostBreakdown] = Field(
        None,
        description="Cost breakdown (part of CRB)"
    )
    risk: Optional[RiskAssessment] = Field(
        None,
        description="Risk assessment (part of CRB)"
    )
    benefit: Optional[BenefitQuantification] = Field(
        None,
        description="Quantified benefit (part of CRB)"
    )

    why_this_works: str = Field(
        default="",
        description="Why the existing stack enables this (API capabilities)"
    )
    tools_used: List[str] = Field(
        default_factory=list,
        description="List of tools/platforms used (e.g., n8n, Twilio, Claude API)"
    )
    prerequisites: List[str] = Field(
        default_factory=list,
        description="Prerequisites or requirements for this integration"
    )
    limitations: Optional[str] = Field(
        None,
        description="Known limitations of this approach"
    )


class ReplacePath(BaseModel):
    """
    The Replace path: New software recommendation.

    Recommends switching to software that provides the capability natively,
    with pricing, migration effort, and trade-offs.

    Includes full CRB (Cost-Risk-Benefit) analysis.
    """
    vendor_slug: str = Field(..., description="Recommended vendor slug")
    vendor_name: str = Field(..., description="Recommended vendor name")
    vendor_description: str = Field(
        default="",
        description="Brief description of what this vendor does"
    )

    # Legacy fields (kept for backwards compatibility, prefer CRB structure)
    monthly_cost: float = Field(
        default=0,
        ge=0,
        description="Monthly cost in EUR (legacy, use crb.cost)"
    )
    setup_effort_weeks: float = Field(
        default=0,
        ge=0,
        description="Setup/migration effort in weeks (legacy, use crb.cost)"
    )

    # CRB Analysis (the new standard)
    crb: Optional[CRBAnalysis] = Field(
        None,
        description="Full Cost-Risk-Benefit analysis for this Replace path"
    )

    # Backwards-compatible individual CRB components (for migration)
    cost: Optional[CostBreakdown] = Field(
        None,
        description="Cost breakdown (part of CRB)"
    )
    risk: Optional[RiskAssessment] = Field(
        None,
        description="Risk assessment (part of CRB)"
    )
    benefit: Optional[BenefitQuantification] = Field(
        None,
        description="Quantified benefit (part of CRB)"
    )

    requires_migration: bool = Field(
        default=True,
        description="Whether this requires data migration from existing tools"
    )
    trade_offs: List[str] = Field(
        default_factory=list,
        description="Trade-offs compared to Connect path"
    )
    benefits: List[str] = Field(
        default_factory=list,
        description="Benefits of switching to this vendor"
    )


class WhyReplaceReasoning(BaseModel):
    """
    Detailed reasoning for why replacement is recommended.

    Used when API score < 3 to explain the limitations of existing stack.
    """
    current_tool: str = Field(
        ...,
        description="The tool being evaluated (e.g., 'Dentrix')"
    )
    api_score: int = Field(
        ...,
        ge=1,
        le=5,
        description="Current API score"
    )
    api_limitations: List[str] = Field(
        ...,
        description="List of specific API limitations"
    )
    what_you_cant_build: List[str] = Field(
        ...,
        description="Automations that can't be built with current stack"
    )
    growth_ceiling: str = Field(
        ...,
        description="Long-term impact on business growth"
    )
    recommended_alternative: str = Field(
        ...,
        description="Recommended alternative software"
    )
    alternative_api_score: int = Field(
        ...,
        ge=1,
        le=5,
        description="API score of recommended alternative"
    )
    alternative_benefits: List[str] = Field(
        ...,
        description="What the alternative enables"
    )
    migration_effort: str = Field(
        ...,
        description="Estimated migration effort description"
    )


class FindingWithPaths(BaseModel):
    """
    A finding enhanced with Connect vs Replace automation paths.

    This extends the base finding structure with both paths and a verdict.
    """
    # Base finding fields
    id: str = Field(..., description="Finding ID")
    title: str = Field(..., description="Finding title")
    description: str = Field(..., description="Finding description")
    category: str = Field(
        default="efficiency",
        description="Finding category"
    )
    customer_value_score: int = Field(..., ge=1, le=10)
    business_health_score: int = Field(..., ge=1, le=10)
    current_state: str = Field(
        default="",
        description="Current state from quiz answers"
    )
    value_saved: dict = Field(
        default_factory=dict,
        description="Hours and cost saved"
    )
    value_created: dict = Field(
        default_factory=dict,
        description="Value created (revenue potential)"
    )
    confidence: str = Field(
        default="medium",
        description="Confidence level"
    )
    sources: List[str] = Field(default_factory=list)
    time_horizon: str = Field(default="mid")
    is_not_recommended: bool = Field(default=False)
    why_not: Optional[str] = None
    what_instead: Optional[str] = None

    # Phase 2C: Connect vs Replace fields
    impact_monthly: float = Field(
        default=0,
        ge=0,
        description="Monthly impact in EUR"
    )
    relevant_stack: List[StackItem] = Field(
        default_factory=list,
        description="Relevant tools from user's stack for this finding"
    )
    avg_api_score: Optional[float] = Field(
        None,
        description="Average API score of relevant stack"
    )

    # The two paths
    connect_path: Optional[ConnectPath] = Field(
        None,
        description="Connect path (use existing tools). None if not viable."
    )
    replace_path: Optional[ReplacePath] = Field(
        None,
        description="Replace path (switch software)"
    )

    # Verdict
    verdict: Literal["CONNECT", "REPLACE", "EITHER"] = Field(
        default="EITHER",
        description="Recommended approach based on API scores"
    )
    verdict_reasoning: str = Field(
        default="",
        description="Explanation of why this verdict was chosen"
    )

    # Why Replace reasoning (when verdict is REPLACE and API score < 3)
    why_replace: Optional[WhyReplaceReasoning] = Field(
        None,
        description="Detailed reasoning when recommending replacement"
    )


def calculate_verdict(avg_api_score: Optional[float]) -> Literal["CONNECT", "REPLACE", "EITHER"]:
    """
    Calculate verdict based on average API score of relevant stack.

    Logic from design doc:
    - avg_score >= 3.5: CONNECT (strong recommendation)
    - avg_score >= 2.5: EITHER (show trade-offs equally)
    - avg_score < 2.5: REPLACE (explain why existing limits growth)
    - None (no relevant stack): REPLACE (need software to automate)

    Args:
        avg_api_score: Average API score of relevant tools (1-5 scale), or None

    Returns:
        Verdict string: "CONNECT", "REPLACE", or "EITHER"
    """
    if avg_api_score is None:
        return "REPLACE"  # No existing tools means need new software

    if avg_api_score >= 3.5:
        return "CONNECT"
    elif avg_api_score >= 2.5:
        return "EITHER"
    else:
        return "REPLACE"


def get_verdict_reasoning(
    verdict: Literal["CONNECT", "REPLACE", "EITHER"],
    avg_api_score: Optional[float],
    connect_cost: Optional[float] = None,
    replace_cost: Optional[float] = None,
) -> str:
    """
    Generate reasoning for the verdict.

    Args:
        verdict: The calculated verdict
        avg_api_score: Average API score of relevant stack
        connect_cost: Monthly cost of Connect path
        replace_cost: Monthly cost of Replace path

    Returns:
        Human-readable reasoning string
    """
    if verdict == "CONNECT":
        cost_comparison = ""
        if connect_cost is not None and replace_cost is not None:
            savings = replace_cost - connect_cost
            if savings > 0:
                cost_comparison = f" Replacing would cost {savings:.0f}/month more with less customization potential."

        return (
            f"Your stack supports automation (API score: {avg_api_score:.1f}/5).{cost_comparison}"
        )

    elif verdict == "REPLACE":
        if avg_api_score is None:
            return "No relevant tools in your current stack for this automation. New software is needed."

        return (
            f"Your current tools have limited API capabilities (score: {avg_api_score:.1f}/5). "
            f"Automation would hit integration ceilings as you grow."
        )

    else:  # EITHER
        return (
            f"Your stack can support basic automation (API score: {avg_api_score:.1f}/5). "
            f"Consider trade-offs: Connect is cheaper but requires technical setup; "
            f"Replace is more expensive but works out of the box."
        )
