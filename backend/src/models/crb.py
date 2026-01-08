"""
CRB (Cost-Risk-Benefit) Framework Models

Every recommendation must include a complete CRB analysis to prevent "AI slop" output.
See: docs/handoffs/2026-01-07-master-roadmap.md

CRB Structure:
- COST: Implementation cost (DIY vs Professional), ongoing costs, hidden costs
- RISK: Implementation risk (1-5), dependency risk, reversal difficulty
- BENEFIT: Quantified metric improvement with calculation chain
"""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field, computed_field


class ImplementationCostDIY(BaseModel):
    """DIY implementation cost calculation."""
    hours: float = Field(..., ge=0, description="Estimated hours for DIY implementation")
    hourly_rate: float = Field(default=50.0, ge=0, description="Assumed hourly rate in EUR")
    description: str = Field(default="", description="What work is required")

    @computed_field
    @property
    def total(self) -> float:
        """Calculate total DIY cost."""
        return self.hours * self.hourly_rate


class ImplementationCostProfessional(BaseModel):
    """Professional implementation cost."""
    estimate: float = Field(..., ge=0, description="Professional implementation estimate in EUR")
    source: str = Field(
        default="Agency/freelancer market rates",
        description="Source of estimate (e.g., 'n8n agency rates')"
    )


class MonthlyCostItem(BaseModel):
    """A single monthly cost item."""
    item: str = Field(..., description="Cost item name (e.g., 'n8n cloud', 'Twilio SMS')")
    cost: float = Field(..., ge=0, description="Monthly cost in EUR")


class MonthlyCostBreakdown(BaseModel):
    """Monthly ongoing costs breakdown."""
    breakdown: List[MonthlyCostItem] = Field(
        default_factory=list,
        description="List of monthly cost items"
    )

    @computed_field
    @property
    def total(self) -> float:
        """Sum of all monthly costs."""
        return sum(item.cost for item in self.breakdown)


class HiddenCosts(BaseModel):
    """Hidden costs often overlooked in ROI calculations."""
    training_hours: float = Field(
        default=0,
        ge=0,
        description="Hours needed for team training"
    )
    productivity_dip_weeks: float = Field(
        default=0,
        ge=0,
        description="Weeks of reduced productivity during transition"
    )
    notes: Optional[str] = Field(
        None,
        description="Additional hidden cost notes"
    )


class CostBreakdown(BaseModel):
    """
    Complete cost analysis for a recommendation.

    Includes one-time implementation costs (DIY vs professional),
    ongoing monthly costs, and hidden costs that affect true ROI.
    """
    implementation_diy: Optional[ImplementationCostDIY] = Field(
        None,
        description="DIY implementation cost"
    )
    implementation_professional: Optional[ImplementationCostProfessional] = Field(
        None,
        description="Professional implementation cost"
    )
    monthly_ongoing: MonthlyCostBreakdown = Field(
        default_factory=MonthlyCostBreakdown,
        description="Monthly ongoing costs"
    )
    hidden: HiddenCosts = Field(
        default_factory=HiddenCosts,
        description="Hidden costs (training, productivity)"
    )

    @computed_field
    @property
    def total_implementation_diy(self) -> float:
        """Total DIY implementation cost."""
        if self.implementation_diy:
            return self.implementation_diy.total
        return 0.0

    @computed_field
    @property
    def total_implementation_professional(self) -> float:
        """Total professional implementation cost."""
        if self.implementation_professional:
            return self.implementation_professional.estimate
        return 0.0

    @computed_field
    @property
    def total_monthly(self) -> float:
        """Total monthly ongoing cost."""
        return self.monthly_ongoing.total


class RiskAssessment(BaseModel):
    """
    Risk assessment for a recommendation.

    Covers implementation risk (how hard to build),
    dependency risk (what if vendor fails), and
    reversal difficulty (how hard to undo).
    """
    implementation_score: int = Field(
        ...,
        ge=1,
        le=5,
        description="Implementation risk 1-5 (1=trivial, 5=complex/risky)"
    )
    implementation_reason: str = Field(
        ...,
        description="Explanation of implementation score"
    )
    dependency_risk: str = Field(
        ...,
        description="What happens if vendor/API goes down or changes"
    )
    reversal_difficulty: Literal["Easy", "Medium", "Hard"] = Field(
        ...,
        description="How hard to undo if it doesn't work"
    )
    additional_risks: List[str] = Field(
        default_factory=list,
        description="Any additional risk factors"
    )


class BenefitQuantification(BaseModel):
    """
    Quantified benefit analysis with traceable calculation.

    Every benefit claim MUST show the math with cited inputs.
    No made-up numbers - calculations must trace to quiz answers or benchmarks.
    """
    primary_metric: str = Field(
        ...,
        description="What metric improves (e.g., 'response time', 'no-show rate')"
    )
    baseline: str = Field(
        ...,
        description="Current state (from quiz answer or industry average with source)"
    )
    target: str = Field(
        ...,
        description="Expected state (from benchmark with source)"
    )
    monthly_value: float = Field(
        ...,
        ge=0,
        description="Monthly monetary value in EUR"
    )
    calculation: str = Field(
        ...,
        description="Show the math with inputs cited (e.g., '10% reduction x 350 x 100 = 3500')"
    )
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        ...,
        description="Confidence in this benefit estimate"
    )
    confidence_reason: str = Field(
        default="",
        description="Why this confidence level"
    )
    time_to_value_weeks: Optional[int] = Field(
        None,
        ge=0,
        description="Weeks until benefit is realized"
    )


class ROIAnalysis(BaseModel):
    """
    ROI calculation with conservative/expected/optimistic scenarios.

    Always shows conservative by default to avoid over-promising.
    """
    conservative: float = Field(
        ...,
        description="Conservative ROI percentage (use 70% of expected)"
    )
    expected: float = Field(
        ...,
        description="Expected ROI percentage"
    )
    optimistic: float = Field(
        ...,
        description="Optimistic ROI percentage (best case)"
    )
    payback_months_conservative: float = Field(
        ...,
        ge=0,
        description="Conservative payback period in months"
    )
    payback_months_expected: float = Field(
        ...,
        ge=0,
        description="Expected payback period in months"
    )
    sensitivity_note: str = Field(
        default="",
        description="Sensitivity analysis (e.g., 'If benefits 50% lower, payback extends to X months')"
    )

    @computed_field
    @property
    def show_by_default(self) -> str:
        """Always show conservative estimate by default."""
        return "conservative"


class CRBAnalysis(BaseModel):
    """
    Complete Cost-Risk-Benefit analysis for a recommendation.

    This is the core model that ensures every recommendation has:
    - Traceable cost breakdown
    - Explicit risk assessment
    - Quantified benefit with calculation chain
    - Clear recommendation with confidence level
    """
    cost: CostBreakdown = Field(..., description="Cost breakdown")
    risk: RiskAssessment = Field(..., description="Risk assessment")
    benefit: BenefitQuantification = Field(..., description="Quantified benefit")
    roi: Optional[ROIAnalysis] = Field(None, description="ROI analysis")

    recommendation_summary: str = Field(
        ...,
        description="Clear 1-2 sentence recommendation"
    )
    confidence_level: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        ...,
        description="Overall confidence in this recommendation"
    )
    data_gaps: List[str] = Field(
        default_factory=list,
        description="What we don't know - data gaps that affect confidence"
    )


# Helper functions for CRB calculations

def estimate_implementation_cost(
    hours_diy: float,
    hourly_rate: float = 50.0,
    professional_multiplier: float = 2.5,
    description: str = ""
) -> tuple[ImplementationCostDIY, ImplementationCostProfessional]:
    """
    Estimate implementation cost for both DIY and professional approaches.

    Args:
        hours_diy: Estimated DIY hours
        hourly_rate: Assumed hourly rate (default €50 for business owner time)
        professional_multiplier: How much more professional costs vs DIY
        description: Description of what work is required

    Returns:
        Tuple of (DIY cost, Professional cost)
    """
    diy = ImplementationCostDIY(
        hours=hours_diy,
        hourly_rate=hourly_rate,
        description=description
    )

    professional = ImplementationCostProfessional(
        estimate=hours_diy * hourly_rate * professional_multiplier,
        source="Estimated at {:.1f}x DIY cost (agency/freelancer rates)".format(professional_multiplier)
    )

    return diy, professional


def calculate_benefit(
    metric_name: str,
    baseline_value: float,
    target_value: float,
    value_per_unit: float,
    unit_volume: float,
    baseline_source: str,
    target_source: str,
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"
) -> BenefitQuantification:
    """
    Calculate quantified benefit with traceable formula.

    Args:
        metric_name: What metric improves (e.g., "no-show rate")
        baseline_value: Current value (e.g., 0.18 for 18%)
        target_value: Target value (e.g., 0.08 for 8%)
        value_per_unit: Value per unit in EUR (e.g., €350/appointment)
        unit_volume: Monthly volume (e.g., 100 appointments/month)
        baseline_source: Source for baseline (e.g., "Quiz Q5")
        target_source: Source for target (e.g., "Industry benchmark, Dental Hygiene 2024")
        confidence: Confidence level

    Returns:
        BenefitQuantification with calculation chain
    """
    improvement = baseline_value - target_value
    monthly_value = improvement * value_per_unit * unit_volume

    # Build calculation string showing the math
    calculation = (
        f"{improvement:.1%} reduction x €{value_per_unit:,.0f} x {unit_volume:,.0f}/month "
        f"= €{monthly_value:,.0f}/month"
    )

    confidence_reason = _get_confidence_reason(confidence, baseline_source, target_source)

    return BenefitQuantification(
        primary_metric=metric_name,
        baseline=f"{baseline_value:.0%} ({baseline_source})",
        target=f"{target_value:.0%} ({target_source})",
        monthly_value=monthly_value,
        calculation=calculation,
        confidence=confidence,
        confidence_reason=confidence_reason
    )


def _get_confidence_reason(
    confidence: Literal["HIGH", "MEDIUM", "LOW"],
    baseline_source: str,
    target_source: str
) -> str:
    """Generate confidence reason based on sources."""
    if confidence == "HIGH":
        return f"User provided baseline ({baseline_source}), target from verified benchmark ({target_source})"
    elif confidence == "MEDIUM":
        return f"Baseline from {baseline_source}, target from {target_source} - some assumptions"
    else:
        return f"Based on industry patterns, user data limited"


def calculate_roi(
    monthly_benefit: float,
    implementation_cost: float,
    monthly_cost: float,
    months: int = 12
) -> ROIAnalysis:
    """
    Calculate ROI with conservative/expected/optimistic scenarios.

    Args:
        monthly_benefit: Expected monthly benefit in EUR
        implementation_cost: One-time implementation cost in EUR
        monthly_cost: Monthly ongoing cost in EUR
        months: Time horizon for ROI calculation (default 12 months)

    Returns:
        ROIAnalysis with three scenarios
    """
    # Total benefit over period
    total_benefit = monthly_benefit * months

    # Total cost over period
    total_cost = implementation_cost + (monthly_cost * months)

    if total_cost <= 0:
        # Avoid division by zero
        return ROIAnalysis(
            conservative=0,
            expected=0,
            optimistic=0,
            payback_months_conservative=999,
            payback_months_expected=999,
            sensitivity_note="No cost data available"
        )

    # Expected ROI
    expected_roi = ((total_benefit - total_cost) / total_cost) * 100

    # Conservative (70% of expected benefit)
    conservative_benefit = total_benefit * 0.7
    conservative_roi = ((conservative_benefit - total_cost) / total_cost) * 100

    # Optimistic (130% of expected benefit)
    optimistic_benefit = total_benefit * 1.3
    optimistic_roi = ((optimistic_benefit - total_cost) / total_cost) * 100

    # Payback calculation
    net_monthly = monthly_benefit - monthly_cost
    if net_monthly <= 0:
        payback_expected = 999
        payback_conservative = 999
    else:
        payback_expected = implementation_cost / net_monthly
        payback_conservative = implementation_cost / (net_monthly * 0.7)

    # Sensitivity note
    sensitivity_note = ""
    if payback_expected < 6:
        half_benefit = monthly_benefit * 0.5
        half_payback = implementation_cost / (half_benefit - monthly_cost) if (half_benefit - monthly_cost) > 0 else 999
        sensitivity_note = f"If benefits are 50% lower, payback extends to {half_payback:.1f} months"

    return ROIAnalysis(
        conservative=round(conservative_roi, 1),
        expected=round(expected_roi, 1),
        optimistic=round(optimistic_roi, 1),
        payback_months_conservative=round(payback_conservative, 1),
        payback_months_expected=round(payback_expected, 1),
        sensitivity_note=sensitivity_note
    )


def assess_risk(
    implementation_complexity: int,
    reason: str,
    vendor_dependency: str,
    reversal: Literal["Easy", "Medium", "Hard"],
    additional: Optional[List[str]] = None
) -> RiskAssessment:
    """
    Create a standardized risk assessment.

    Args:
        implementation_complexity: 1-5 (1=trivial, 5=complex)
        reason: Why this complexity score
        vendor_dependency: What happens if vendor fails
        reversal: How hard to undo
        additional: Additional risk factors

    Returns:
        RiskAssessment model
    """
    return RiskAssessment(
        implementation_score=implementation_complexity,
        implementation_reason=reason,
        dependency_risk=vendor_dependency,
        reversal_difficulty=reversal,
        additional_risks=additional or []
    )


# Export all models and helpers
__all__ = [
    # Models
    "ImplementationCostDIY",
    "ImplementationCostProfessional",
    "MonthlyCostItem",
    "MonthlyCostBreakdown",
    "HiddenCosts",
    "CostBreakdown",
    "RiskAssessment",
    "BenefitQuantification",
    "ROIAnalysis",
    "CRBAnalysis",
    # Helper functions
    "estimate_implementation_cost",
    "calculate_benefit",
    "calculate_roi",
    "assess_risk",
]
