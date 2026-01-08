"""
Automation Summary Models - Phase 2D

Models for the Automation Roadmap section at the end of reports.
Aggregates all Connect vs Replace opportunities from findings.

See: docs/plans/2026-01-07-connect-vs-replace-design.md
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class StackAssessmentItem(BaseModel):
    """A single tool in the stack assessment with visual score."""
    name: str = Field(..., description="Tool display name")
    slug: str = Field(..., description="Tool slug/identifier")
    api_score: int = Field(..., ge=1, le=5, description="API openness score 1-5")
    category: Optional[str] = Field(None, description="Tool category")


class StackAssessment(BaseModel):
    """
    Assessment of user's existing software stack.

    Shows each tool with API score visualization and overall verdict.
    """
    tools: List[StackAssessmentItem] = Field(
        default_factory=list,
        description="List of tools with their API scores"
    )
    average_score: float = Field(
        ...,
        ge=0,
        le=5,
        description="Average API score across all tools"
    )
    verdict: Literal[
        "strong_foundation",
        "good_foundation",
        "moderate_foundation",
        "limited_foundation",
        "no_tools"
    ] = Field(..., description="Overall stack verdict")
    verdict_text: str = Field(
        ...,
        description="Human-readable verdict (e.g., 'Strong foundation for automation')"
    )


class AutomationOpportunity(BaseModel):
    """
    A single automation opportunity for the summary table.

    Aggregated from findings with Connect vs Replace paths.
    """
    finding_id: str = Field(..., description="Source finding ID")
    title: str = Field(..., description="Automation title/name")
    impact_monthly: float = Field(
        ...,
        ge=0,
        description="Monthly impact in EUR"
    )
    diy_effort_hours: float = Field(
        ...,
        ge=0,
        description="DIY setup effort in hours"
    )
    approach: Literal["Connect", "Replace", "Either"] = Field(
        ...,
        description="Recommended approach"
    )
    tools_involved: List[str] = Field(
        default_factory=list,
        description="Tools used in this automation"
    )
    category: str = Field(
        default="efficiency",
        description="Finding category"
    )


# Tier-aware messaging for next steps
TIER_MESSAGES = {
    "quick": {
        "headline": "Need a hand with implementation?",
        "message": "Book an implementation scope call to discuss your automation roadmap with an expert.",
        "cta_text": "Schedule Call",
        "cta_url": "https://calendly.com/crb/implementation",
    },
    "full": {
        "headline": "Your strategy call is included",
        "message": "We'll discuss implementation priorities and next steps in your upcoming strategy session.",
        "cta_text": "Schedule Strategy Call",
        "cta_url": "https://calendly.com/crb/strategy",
    },
    "sprint": {
        "headline": "Your Sprint includes full implementation",
        "message": "Our team will implement these automations for you over the next 2 weeks. Let's kick off!",
        "cta_text": "Start Your Sprint",
        "cta_url": "https://calendly.com/crb/sprint-kickoff",
    },
}


class NextSteps(BaseModel):
    """Tier-aware next steps messaging."""
    tier: str = Field(..., description="Report tier (quick, full, sprint)")
    headline: str = Field(..., description="Headline for next steps section")
    message: str = Field(..., description="Tier-specific message")
    cta_text: str = Field(..., description="Call-to-action button text")
    cta_url: str = Field(..., description="Call-to-action URL")


class AutomationSummary(BaseModel):
    """
    Complete Automation Roadmap summary for end of report.

    Aggregates stack assessment, opportunities from all findings,
    totals, and tier-aware next steps.
    """
    stack_assessment: StackAssessment = Field(
        ...,
        description="Assessment of user's existing software stack"
    )
    opportunities: List[AutomationOpportunity] = Field(
        default_factory=list,
        description="List of automation opportunities from findings"
    )
    total_monthly_impact: float = Field(
        default=0,
        ge=0,
        description="Total monthly impact across all opportunities"
    )
    total_diy_hours: float = Field(
        default=0,
        ge=0,
        description="Total DIY effort hours across all opportunities"
    )
    connect_count: int = Field(
        default=0,
        ge=0,
        description="Number of Connect-path opportunities"
    )
    replace_count: int = Field(
        default=0,
        ge=0,
        description="Number of Replace-path opportunities"
    )
    either_count: int = Field(
        default=0,
        ge=0,
        description="Number of Either-path opportunities"
    )
    next_steps: NextSteps = Field(
        ...,
        description="Tier-aware next steps messaging"
    )


def get_stack_verdict(average_score: float) -> tuple[str, str]:
    """
    Get verdict and text based on average API score.

    Args:
        average_score: Average API score (0-5)

    Returns:
        Tuple of (verdict_key, verdict_text)
    """
    if average_score >= 4.0:
        return ("strong_foundation", "Strong foundation for automation")
    elif average_score >= 3.5:
        return ("good_foundation", "Good foundation for automation")
    elif average_score >= 2.5:
        return ("moderate_foundation", "Moderate automation potential")
    elif average_score > 0:
        return ("limited_foundation", "Limited automation capabilities")
    else:
        return ("no_tools", "No existing tools to assess")


def get_next_steps(tier: str) -> NextSteps:
    """
    Get tier-aware next steps messaging.

    Args:
        tier: Report tier (quick, full, sprint)

    Returns:
        NextSteps model with appropriate messaging
    """
    tier_key = tier.lower()
    if tier_key not in TIER_MESSAGES:
        tier_key = "quick"  # Default to quick tier

    msg = TIER_MESSAGES[tier_key]
    return NextSteps(
        tier=tier,
        headline=msg["headline"],
        message=msg["message"],
        cta_text=msg["cta_text"],
        cta_url=msg["cta_url"],
    )
