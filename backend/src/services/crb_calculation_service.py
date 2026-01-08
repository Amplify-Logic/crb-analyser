"""
CRB Calculation Service

Provides calculation and validation functions for Cost-Risk-Benefit analyses.
This service ensures all CRB outputs are traceable and realistic.

See: docs/handoffs/2026-01-07-master-roadmap.md (CRB Framework)
"""

import logging
from typing import Optional, List, Dict, Any, Literal

from src.models.crb import (
    ImplementationCostDIY,
    ImplementationCostProfessional,
    MonthlyCostItem,
    MonthlyCostBreakdown,
    HiddenCosts,
    CostBreakdown,
    RiskAssessment,
    BenefitQuantification,
    ROIAnalysis,
    CRBAnalysis,
)

logger = logging.getLogger(__name__)


# Constants for realistic validation
MAX_CREDIBLE_ROI_PERCENT = 500  # Above this requires explanation
MIN_CREDIBLE_PAYBACK_MONTHS = 3  # Below this is exceptional
DEFAULT_HOURLY_RATE_EUR = 50  # Business owner time
PROFESSIONAL_COST_MULTIPLIER = 2.5


class CRBCalculationService:
    """
    Service for building and validating CRB analyses.

    Ensures all calculations are:
    - Traceable (inputs are cited)
    - Realistic (ROI bounds checked)
    - Complete (all required fields present)
    """

    def build_connect_path_crb(
        self,
        # Cost inputs
        implementation_hours: float,
        monthly_costs: List[Dict[str, Any]],
        hidden_training_hours: float = 2,
        hidden_productivity_dip_weeks: float = 1,
        # Risk inputs
        implementation_complexity: int = 2,
        complexity_reason: str = "Standard API integration",
        dependency_vendor: str = "integration platform",
        reversal_difficulty: Literal["Easy", "Medium", "Hard"] = "Easy",
        # Benefit inputs
        primary_metric: str = "",
        baseline_value: str = "",
        target_value: str = "",
        monthly_value_eur: float = 0,
        calculation_formula: str = "",
        confidence: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM",
        confidence_reason: str = "",
        # Additional
        data_gaps: Optional[List[str]] = None,
    ) -> CRBAnalysis:
        """
        Build a complete CRB analysis for a Connect path.

        Args:
            implementation_hours: DIY implementation hours
            monthly_costs: List of {"item": str, "cost": float} dicts
            hidden_training_hours: Hours for team training
            hidden_productivity_dip_weeks: Weeks of reduced productivity
            implementation_complexity: 1-5 score
            complexity_reason: Why this complexity
            dependency_vendor: What vendor/API we depend on
            reversal_difficulty: How hard to undo
            primary_metric: What metric improves
            baseline_value: Current state (with source)
            target_value: Expected state (with source)
            monthly_value_eur: Monthly value in EUR
            calculation_formula: Show the math
            confidence: HIGH/MEDIUM/LOW
            confidence_reason: Why this confidence
            data_gaps: List of unknowns

        Returns:
            Complete CRBAnalysis
        """
        # Build cost breakdown
        diy_cost = ImplementationCostDIY(
            hours=implementation_hours,
            hourly_rate=DEFAULT_HOURLY_RATE_EUR,
            description="DIY implementation via n8n/Make/custom code"
        )

        professional_cost = ImplementationCostProfessional(
            estimate=implementation_hours * DEFAULT_HOURLY_RATE_EUR * PROFESSIONAL_COST_MULTIPLIER,
            source=f"Estimated at {PROFESSIONAL_COST_MULTIPLIER}x DIY (agency/freelancer rates)"
        )

        monthly_items = [
            MonthlyCostItem(item=c["item"], cost=c["cost"])
            for c in monthly_costs
        ]

        cost = CostBreakdown(
            implementation_diy=diy_cost,
            implementation_professional=professional_cost,
            monthly_ongoing=MonthlyCostBreakdown(breakdown=monthly_items),
            hidden=HiddenCosts(
                training_hours=hidden_training_hours,
                productivity_dip_weeks=hidden_productivity_dip_weeks
            )
        )

        # Build risk assessment
        risk = RiskAssessment(
            implementation_score=implementation_complexity,
            implementation_reason=complexity_reason,
            dependency_risk=f"If {dependency_vendor} goes down or changes API, automation stops",
            reversal_difficulty=reversal_difficulty
        )

        # Build benefit quantification
        benefit = BenefitQuantification(
            primary_metric=primary_metric,
            baseline=baseline_value,
            target=target_value,
            monthly_value=monthly_value_eur,
            calculation=calculation_formula,
            confidence=confidence,
            confidence_reason=confidence_reason
        )

        # Calculate ROI
        roi = self._calculate_roi(
            monthly_benefit=monthly_value_eur,
            implementation_cost=diy_cost.total,
            monthly_cost=cost.total_monthly
        )

        # Build recommendation summary
        recommendation = self._build_recommendation_summary(
            monthly_value_eur, cost.total_monthly, diy_cost.total, confidence
        )

        return CRBAnalysis(
            cost=cost,
            risk=risk,
            benefit=benefit,
            roi=roi,
            recommendation_summary=recommendation,
            confidence_level=confidence,
            data_gaps=data_gaps or []
        )

    def build_replace_path_crb(
        self,
        # Cost inputs
        monthly_subscription: float,
        setup_cost: float,
        migration_cost: float = 0,
        hidden_training_hours: float = 4,
        hidden_productivity_dip_weeks: float = 2,
        # Risk inputs
        implementation_complexity: int = 3,
        complexity_reason: str = "Requires data migration",
        vendor_name: str = "vendor",
        reversal_difficulty: Literal["Easy", "Medium", "Hard"] = "Medium",
        # Benefit inputs
        primary_metric: str = "",
        baseline_value: str = "",
        target_value: str = "",
        monthly_value_eur: float = 0,
        calculation_formula: str = "",
        confidence: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM",
        confidence_reason: str = "",
        # Additional
        data_gaps: Optional[List[str]] = None,
    ) -> CRBAnalysis:
        """
        Build a complete CRB analysis for a Replace path.

        Replace paths typically have:
        - Higher upfront cost (migration, setup)
        - Lower ongoing effort (vendor handles maintenance)
        - Higher risk (vendor lock-in, migration complexity)
        """
        # Build cost breakdown - Replace uses professional cost structure
        professional_cost = ImplementationCostProfessional(
            estimate=setup_cost + migration_cost,
            source="Vendor setup + data migration costs"
        )

        monthly_items = [
            MonthlyCostItem(item=f"{vendor_name} subscription", cost=monthly_subscription)
        ]

        cost = CostBreakdown(
            implementation_diy=None,  # No DIY for Replace
            implementation_professional=professional_cost,
            monthly_ongoing=MonthlyCostBreakdown(breakdown=monthly_items),
            hidden=HiddenCosts(
                training_hours=hidden_training_hours,
                productivity_dip_weeks=hidden_productivity_dip_weeks,
                notes="New software often requires more training than connecting existing tools"
            )
        )

        # Build risk assessment
        risk = RiskAssessment(
            implementation_score=implementation_complexity,
            implementation_reason=complexity_reason,
            dependency_risk=f"Vendor lock-in with {vendor_name}. Switching later requires re-migration.",
            reversal_difficulty=reversal_difficulty,
            additional_risks=[
                "Data migration may lose some historical data",
                "Team needs to learn new software interface"
            ]
        )

        # Build benefit quantification
        benefit = BenefitQuantification(
            primary_metric=primary_metric,
            baseline=baseline_value,
            target=target_value,
            monthly_value=monthly_value_eur,
            calculation=calculation_formula,
            confidence=confidence,
            confidence_reason=confidence_reason
        )

        # Calculate ROI
        total_implementation = setup_cost + migration_cost
        roi = self._calculate_roi(
            monthly_benefit=monthly_value_eur,
            implementation_cost=total_implementation,
            monthly_cost=monthly_subscription
        )

        # Build recommendation summary
        recommendation = self._build_recommendation_summary(
            monthly_value_eur, monthly_subscription, total_implementation, confidence
        )

        return CRBAnalysis(
            cost=cost,
            risk=risk,
            benefit=benefit,
            roi=roi,
            recommendation_summary=recommendation,
            confidence_level=confidence,
            data_gaps=data_gaps or []
        )

    def _calculate_roi(
        self,
        monthly_benefit: float,
        implementation_cost: float,
        monthly_cost: float,
        months: int = 12
    ) -> ROIAnalysis:
        """Calculate ROI with conservative/expected/optimistic scenarios."""
        if implementation_cost <= 0 and monthly_cost <= 0:
            return ROIAnalysis(
                conservative=0,
                expected=0,
                optimistic=0,
                payback_months_conservative=999,
                payback_months_expected=999,
                sensitivity_note="No cost data - cannot calculate ROI"
            )

        total_benefit = monthly_benefit * months
        total_cost = implementation_cost + (monthly_cost * months)

        if total_cost <= 0:
            return ROIAnalysis(
                conservative=0,
                expected=0,
                optimistic=0,
                payback_months_conservative=999,
                payback_months_expected=999,
                sensitivity_note="Zero cost - ROI undefined"
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
            payback_expected = implementation_cost / net_monthly if implementation_cost > 0 else 0
            payback_conservative = implementation_cost / (net_monthly * 0.7) if implementation_cost > 0 else 0

        # Sensitivity note
        sensitivity_note = ""
        if expected_roi > MAX_CREDIBLE_ROI_PERCENT:
            sensitivity_note = f"ROI above {MAX_CREDIBLE_ROI_PERCENT}% is exceptional - verify inputs"
        elif payback_expected < MIN_CREDIBLE_PAYBACK_MONTHS and payback_expected > 0:
            half_benefit = monthly_benefit * 0.5
            half_net = half_benefit - monthly_cost
            half_payback = implementation_cost / half_net if half_net > 0 else 999
            sensitivity_note = f"Fast payback ({payback_expected:.1f} months). If benefits 50% lower: {half_payback:.1f} months"

        return ROIAnalysis(
            conservative=round(conservative_roi, 1),
            expected=round(expected_roi, 1),
            optimistic=round(optimistic_roi, 1),
            payback_months_conservative=round(payback_conservative, 1),
            payback_months_expected=round(payback_expected, 1),
            sensitivity_note=sensitivity_note
        )

    def _build_recommendation_summary(
        self,
        monthly_benefit: float,
        monthly_cost: float,
        implementation_cost: float,
        confidence: Literal["HIGH", "MEDIUM", "LOW"]
    ) -> str:
        """Build a clear recommendation summary."""
        net_monthly = monthly_benefit - monthly_cost

        if net_monthly <= 0:
            return f"Cost exceeds benefit ({monthly_cost:.0f}/month vs {monthly_benefit:.0f}/month). Not recommended."

        if implementation_cost > 0:
            payback = implementation_cost / net_monthly
            return (
                f"Net benefit: {net_monthly:.0f}/month after costs. "
                f"Payback: {payback:.1f} months. "
                f"Confidence: {confidence}."
            )
        else:
            return f"Net benefit: {net_monthly:.0f}/month. No implementation cost. Confidence: {confidence}."

    def validate_crb_analysis(self, crb: CRBAnalysis) -> List[str]:
        """
        Validate a CRB analysis for completeness and realism.

        Returns list of validation issues (empty if valid).
        """
        issues = []

        # Check cost is present
        if not crb.cost.implementation_diy and not crb.cost.implementation_professional:
            issues.append("Missing implementation cost (either DIY or professional required)")

        # Check benefit has calculation
        if not crb.benefit.calculation:
            issues.append("Missing benefit calculation formula")

        if crb.benefit.monthly_value <= 0:
            issues.append("Benefit monthly value is zero or negative")

        # Check ROI is reasonable
        if crb.roi:
            if crb.roi.expected > MAX_CREDIBLE_ROI_PERCENT and not crb.roi.sensitivity_note:
                issues.append(f"ROI > {MAX_CREDIBLE_ROI_PERCENT}% without explanation")

            if 0 < crb.roi.payback_months_expected < MIN_CREDIBLE_PAYBACK_MONTHS:
                if not crb.roi.sensitivity_note:
                    issues.append(f"Payback < {MIN_CREDIBLE_PAYBACK_MONTHS} months without sensitivity analysis")

        # Check risk is complete
        if crb.risk.implementation_score < 1 or crb.risk.implementation_score > 5:
            issues.append("Risk score must be 1-5")

        if not crb.risk.implementation_reason:
            issues.append("Missing risk implementation reason")

        # Log issues
        if issues:
            logger.warning(f"CRB validation issues: {issues}")

        return issues

    def compare_paths(
        self,
        connect_crb: Optional[CRBAnalysis],
        replace_crb: Optional[CRBAnalysis]
    ) -> Dict[str, Any]:
        """
        Compare Connect vs Replace paths and return comparison summary.
        """
        if not connect_crb and not replace_crb:
            return {"error": "No paths to compare"}

        comparison = {
            "connect": None,
            "replace": None,
            "winner": None,
            "reasoning": ""
        }

        if connect_crb:
            comparison["connect"] = {
                "implementation_cost": connect_crb.cost.total_implementation_diy,
                "monthly_cost": connect_crb.cost.total_monthly,
                "monthly_benefit": connect_crb.benefit.monthly_value,
                "risk_score": connect_crb.risk.implementation_score,
                "roi_expected": connect_crb.roi.expected if connect_crb.roi else 0,
                "confidence": connect_crb.confidence_level
            }

        if replace_crb:
            comparison["replace"] = {
                "implementation_cost": replace_crb.cost.total_implementation_professional,
                "monthly_cost": replace_crb.cost.total_monthly,
                "monthly_benefit": replace_crb.benefit.monthly_value,
                "risk_score": replace_crb.risk.implementation_score,
                "roi_expected": replace_crb.roi.expected if replace_crb.roi else 0,
                "confidence": replace_crb.confidence_level
            }

        # Determine winner
        if connect_crb and replace_crb:
            connect_score = self._score_path(comparison["connect"])
            replace_score = self._score_path(comparison["replace"])

            if connect_score > replace_score:
                comparison["winner"] = "CONNECT"
                comparison["reasoning"] = "Connect path has better cost-adjusted ROI with lower risk"
            elif replace_score > connect_score:
                comparison["winner"] = "REPLACE"
                comparison["reasoning"] = "Replace path offers better value despite higher upfront cost"
            else:
                comparison["winner"] = "EITHER"
                comparison["reasoning"] = "Both paths are viable - consider technical preference"
        elif connect_crb:
            comparison["winner"] = "CONNECT"
            comparison["reasoning"] = "Only Connect path available"
        else:
            comparison["winner"] = "REPLACE"
            comparison["reasoning"] = "Only Replace path available"

        return comparison

    def _score_path(self, path_data: Dict[str, Any]) -> float:
        """Score a path for comparison (higher is better)."""
        if not path_data:
            return 0

        # Factors: ROI (positive), risk (negative), confidence (positive)
        roi_score = min(path_data.get("roi_expected", 0) / 100, 5)  # Cap at 500% = 5 points
        risk_penalty = path_data.get("risk_score", 3) * 0.5  # Higher risk = lower score
        confidence_bonus = {"HIGH": 1, "MEDIUM": 0.5, "LOW": 0}.get(
            path_data.get("confidence", "MEDIUM"), 0.5
        )

        return roi_score - risk_penalty + confidence_bonus


# Singleton instance
crb_service = CRBCalculationService()


# Convenience functions
def build_connect_crb(*args, **kwargs) -> CRBAnalysis:
    """Build CRB analysis for Connect path."""
    return crb_service.build_connect_path_crb(*args, **kwargs)


def build_replace_crb(*args, **kwargs) -> CRBAnalysis:
    """Build CRB analysis for Replace path."""
    return crb_service.build_replace_path_crb(*args, **kwargs)


def validate_crb(crb: CRBAnalysis) -> List[str]:
    """Validate CRB analysis."""
    return crb_service.validate_crb_analysis(crb)


__all__ = [
    "CRBCalculationService",
    "crb_service",
    "build_connect_crb",
    "build_replace_crb",
    "validate_crb",
]
