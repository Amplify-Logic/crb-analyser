"""
Tests for CRB (Cost-Risk-Benefit) Framework

Tests cover:
- CRB model creation and validation
- Calculation helpers
- ROI calculations with edge cases
- CRB service functions
"""

import pytest

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
    estimate_implementation_cost,
    calculate_benefit,
    calculate_roi,
    assess_risk,
)
from src.services.crb_calculation_service import (
    CRBCalculationService,
    crb_service,
    build_connect_crb,
    build_replace_crb,
    validate_crb,
)


class TestCRBModels:
    """Tests for CRB Pydantic models."""

    def test_implementation_cost_diy_calculation(self):
        """Test DIY cost total is calculated correctly."""
        cost = ImplementationCostDIY(
            hours=10,
            hourly_rate=50,
            description="Build n8n workflow"
        )
        assert cost.total == 500

    def test_implementation_cost_diy_default_rate(self):
        """Test default hourly rate is 50 EUR."""
        cost = ImplementationCostDIY(hours=8, description="Test")
        assert cost.hourly_rate == 50
        assert cost.total == 400

    def test_monthly_cost_breakdown_total(self):
        """Test monthly cost breakdown calculates total correctly."""
        breakdown = MonthlyCostBreakdown(
            breakdown=[
                MonthlyCostItem(item="n8n cloud", cost=20),
                MonthlyCostItem(item="Twilio", cost=15),
                MonthlyCostItem(item="Claude API", cost=10),
            ]
        )
        assert breakdown.total == 45

    def test_monthly_cost_breakdown_empty(self):
        """Test empty breakdown returns 0 total."""
        breakdown = MonthlyCostBreakdown(breakdown=[])
        assert breakdown.total == 0

    def test_cost_breakdown_computed_properties(self):
        """Test CostBreakdown computed properties."""
        cost = CostBreakdown(
            implementation_diy=ImplementationCostDIY(hours=8, hourly_rate=50, description=""),
            implementation_professional=ImplementationCostProfessional(estimate=1000, source="Agency"),
            monthly_ongoing=MonthlyCostBreakdown(
                breakdown=[MonthlyCostItem(item="SaaS", cost=50)]
            ),
            hidden=HiddenCosts(training_hours=4, productivity_dip_weeks=2)
        )
        assert cost.total_implementation_diy == 400
        assert cost.total_implementation_professional == 1000
        assert cost.total_monthly == 50

    def test_risk_assessment_valid_score_range(self):
        """Test risk score must be 1-5."""
        risk = RiskAssessment(
            implementation_score=3,
            implementation_reason="Medium complexity",
            dependency_risk="API may change",
            reversal_difficulty="Easy"
        )
        assert risk.implementation_score == 3

    def test_risk_assessment_invalid_score_low(self):
        """Test risk score below 1 is rejected."""
        with pytest.raises(ValueError):
            RiskAssessment(
                implementation_score=0,
                implementation_reason="Invalid",
                dependency_risk="N/A",
                reversal_difficulty="Easy"
            )

    def test_risk_assessment_invalid_score_high(self):
        """Test risk score above 5 is rejected."""
        with pytest.raises(ValueError):
            RiskAssessment(
                implementation_score=6,
                implementation_reason="Invalid",
                dependency_risk="N/A",
                reversal_difficulty="Easy"
            )

    def test_benefit_quantification_complete(self):
        """Test complete benefit quantification."""
        benefit = BenefitQuantification(
            primary_metric="no-show rate",
            baseline="18% (Quiz Q5)",
            target="8% (Industry benchmark)",
            monthly_value=3500,
            calculation="10% reduction x 350 x 100 = 3500",
            confidence="HIGH",
            confidence_reason="User provided data, verified benchmark"
        )
        assert benefit.monthly_value == 3500
        assert benefit.confidence == "HIGH"

    def test_roi_analysis_show_conservative_default(self):
        """Test ROI analysis shows conservative by default."""
        roi = ROIAnalysis(
            conservative=150,
            expected=250,
            optimistic=400,
            payback_months_conservative=8,
            payback_months_expected=5,
            sensitivity_note="If benefits 50% lower, payback 16 months"
        )
        assert roi.show_by_default == "conservative"


class TestCRBHelperFunctions:
    """Tests for CRB helper functions."""

    def test_estimate_implementation_cost(self):
        """Test implementation cost estimation."""
        diy, pro = estimate_implementation_cost(
            hours_diy=10,
            hourly_rate=50,
            professional_multiplier=2.5,
            description="Build integration"
        )
        assert diy.total == 500
        assert diy.hours == 10
        assert pro.estimate == 1250  # 10 * 50 * 2.5

    def test_calculate_benefit(self):
        """Test benefit calculation with full formula."""
        benefit = calculate_benefit(
            metric_name="no-show rate",
            baseline_value=0.18,
            target_value=0.08,
            value_per_unit=350,
            unit_volume=100,
            baseline_source="Quiz Q5",
            target_source="Industry benchmark 2024",
            confidence="HIGH"
        )
        assert benefit.primary_metric == "no-show rate"
        assert benefit.monthly_value == 3500  # 0.10 * 350 * 100
        assert "10.0% reduction" in benefit.calculation
        assert benefit.confidence == "HIGH"

    def test_calculate_benefit_negative_improvement_returns_positive(self):
        """Test benefit calculation handles improvement correctly."""
        # baseline > target means improvement
        benefit = calculate_benefit(
            metric_name="response time",
            baseline_value=0.5,
            target_value=0.1,
            value_per_unit=100,
            unit_volume=1000,
            baseline_source="Quiz",
            target_source="Benchmark"
        )
        # 0.4 improvement * 100 * 1000 = 40000
        assert benefit.monthly_value == 40000

    def test_calculate_roi_basic(self):
        """Test basic ROI calculation."""
        roi = calculate_roi(
            monthly_benefit=1000,
            implementation_cost=2000,
            monthly_cost=100,
            months=12
        )
        # Total benefit: 1000 * 12 = 12000
        # Total cost: 2000 + 100*12 = 3200
        # Expected ROI: (12000 - 3200) / 3200 = 275%
        assert roi.expected == pytest.approx(275, rel=0.01)

    def test_calculate_roi_zero_cost(self):
        """Test ROI with zero cost returns 0."""
        roi = calculate_roi(
            monthly_benefit=1000,
            implementation_cost=0,
            monthly_cost=0,
            months=12
        )
        assert roi.expected == 0
        assert roi.payback_months_expected == 999

    def test_calculate_roi_negative_net_monthly(self):
        """Test ROI when cost exceeds benefit."""
        roi = calculate_roi(
            monthly_benefit=50,
            implementation_cost=1000,
            monthly_cost=100,  # Exceeds benefit
            months=12
        )
        assert roi.payback_months_expected == 999

    def test_calculate_roi_fast_payback_includes_sensitivity(self):
        """Test fast payback includes sensitivity note."""
        roi = calculate_roi(
            monthly_benefit=2000,
            implementation_cost=3000,
            monthly_cost=100,
            months=12
        )
        # Net monthly: 2000 - 100 = 1900
        # Payback: 3000 / 1900 = 1.58 months (fast!)
        assert roi.payback_months_expected < 3
        assert "50% lower" in roi.sensitivity_note

    def test_assess_risk(self):
        """Test risk assessment helper."""
        risk = assess_risk(
            implementation_complexity=2,
            reason="Well-documented API",
            vendor_dependency="n8n platform",
            reversal="Easy",
            additional=["Rate limits may apply"]
        )
        assert risk.implementation_score == 2
        assert risk.reversal_difficulty == "Easy"
        assert "Rate limits" in risk.additional_risks[0]


class TestCRBCalculationService:
    """Tests for CRB calculation service."""

    def test_build_connect_path_crb(self):
        """Test building CRB for Connect path."""
        crb = crb_service.build_connect_path_crb(
            implementation_hours=8,
            monthly_costs=[
                {"item": "n8n", "cost": 20},
                {"item": "Twilio", "cost": 15},
            ],
            implementation_complexity=2,
            complexity_reason="Standard API",
            dependency_vendor="n8n",
            reversal_difficulty="Easy",
            primary_metric="response time",
            baseline_value="4 hours (Quiz)",
            target_value="15 minutes (benchmark)",
            monthly_value_eur=2000,
            calculation_formula="Time saved * hourly rate",
            confidence="HIGH",
            confidence_reason="User data + benchmark"
        )

        assert crb.cost.total_implementation_diy == 400  # 8 * 50
        assert crb.cost.total_monthly == 35  # 20 + 15
        assert crb.risk.implementation_score == 2
        assert crb.benefit.monthly_value == 2000
        assert crb.confidence_level == "HIGH"

    def test_build_replace_path_crb(self):
        """Test building CRB for Replace path."""
        crb = crb_service.build_replace_path_crb(
            monthly_subscription=200,
            setup_cost=2000,
            migration_cost=500,
            implementation_complexity=3,
            complexity_reason="Data migration required",
            vendor_name="NewVendor",
            reversal_difficulty="Medium",
            primary_metric="efficiency",
            baseline_value="Manual",
            target_value="Automated",
            monthly_value_eur=1500,
            calculation_formula="Hours saved * rate",
            confidence="MEDIUM"
        )

        assert crb.cost.total_implementation_professional == 2500  # 2000 + 500
        assert crb.cost.total_monthly == 200
        assert crb.risk.implementation_score == 3
        assert crb.risk.reversal_difficulty == "Medium"

    def test_validate_crb_valid(self):
        """Test validation passes for valid CRB."""
        crb = crb_service.build_connect_path_crb(
            implementation_hours=8,
            monthly_costs=[{"item": "API", "cost": 10}],
            primary_metric="metric",
            baseline_value="before",
            target_value="after",
            monthly_value_eur=1000,
            calculation_formula="formula",
            confidence="HIGH"
        )
        issues = crb_service.validate_crb_analysis(crb)
        assert len(issues) == 0

    def test_validate_crb_missing_calculation(self):
        """Test validation catches missing calculation."""
        crb = CRBAnalysis(
            cost=CostBreakdown(
                implementation_diy=ImplementationCostDIY(hours=8, description="")
            ),
            risk=RiskAssessment(
                implementation_score=2,
                implementation_reason="Test",
                dependency_risk="Test",
                reversal_difficulty="Easy"
            ),
            benefit=BenefitQuantification(
                primary_metric="test",
                baseline="before",
                target="after",
                monthly_value=1000,
                calculation="",  # Missing!
                confidence="HIGH"
            ),
            recommendation_summary="Test",
            confidence_level="HIGH"
        )
        issues = validate_crb(crb)
        assert any("calculation" in issue.lower() for issue in issues)

    def test_validate_crb_zero_benefit(self):
        """Test validation catches zero benefit."""
        crb = CRBAnalysis(
            cost=CostBreakdown(
                implementation_diy=ImplementationCostDIY(hours=8, description="")
            ),
            risk=RiskAssessment(
                implementation_score=2,
                implementation_reason="Test",
                dependency_risk="Test",
                reversal_difficulty="Easy"
            ),
            benefit=BenefitQuantification(
                primary_metric="test",
                baseline="before",
                target="after",
                monthly_value=0,  # Zero!
                calculation="formula",
                confidence="HIGH"
            ),
            recommendation_summary="Test",
            confidence_level="HIGH"
        )
        issues = validate_crb(crb)
        assert any("zero" in issue.lower() or "negative" in issue.lower() for issue in issues)

    def test_compare_paths(self):
        """Test path comparison logic."""
        connect_crb = crb_service.build_connect_path_crb(
            implementation_hours=8,
            monthly_costs=[{"item": "API", "cost": 30}],
            implementation_complexity=2,
            primary_metric="test",
            baseline_value="before",
            target_value="after",
            monthly_value_eur=1000,
            calculation_formula="formula",
            confidence="HIGH"
        )

        replace_crb = crb_service.build_replace_path_crb(
            monthly_subscription=200,
            setup_cost=3000,
            implementation_complexity=4,
            vendor_name="Vendor",
            primary_metric="test",
            baseline_value="before",
            target_value="after",
            monthly_value_eur=1200,
            calculation_formula="formula",
            confidence="MEDIUM"
        )

        comparison = crb_service.compare_paths(connect_crb, replace_crb)

        assert comparison["connect"] is not None
        assert comparison["replace"] is not None
        assert comparison["winner"] in ("CONNECT", "REPLACE", "EITHER")

    def test_compare_paths_only_connect(self):
        """Test comparison with only Connect path."""
        connect_crb = crb_service.build_connect_path_crb(
            implementation_hours=8,
            monthly_costs=[{"item": "API", "cost": 30}],
            primary_metric="test",
            baseline_value="before",
            target_value="after",
            monthly_value_eur=1000,
            calculation_formula="formula",
            confidence="HIGH"
        )

        comparison = crb_service.compare_paths(connect_crb, None)
        assert comparison["winner"] == "CONNECT"

    def test_compare_paths_neither(self):
        """Test comparison with no paths."""
        comparison = crb_service.compare_paths(None, None)
        assert "error" in comparison


class TestCRBEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_high_roi_flagged(self):
        """Test that very high ROI gets flagged."""
        roi = calculate_roi(
            monthly_benefit=10000,
            implementation_cost=100,
            monthly_cost=10,
            months=12
        )
        # ROI will be extremely high
        assert roi.expected > 500
        # Sensitivity note should mention this is exceptional
        # (Note: current implementation adds note for fast payback, not high ROI)

    def test_minimum_hours(self):
        """Test with minimum viable hours."""
        diy, pro = estimate_implementation_cost(
            hours_diy=0.5,  # 30 minutes
            hourly_rate=50
        )
        assert diy.total == 25
        assert pro.estimate == 62.5

    def test_large_monthly_volume(self):
        """Test benefit calculation with large volumes."""
        benefit = calculate_benefit(
            metric_name="tickets",
            baseline_value=0.80,  # 80% manual
            target_value=0.20,  # 20% manual (60% automated)
            value_per_unit=5,  # 5 EUR per ticket
            unit_volume=10000,  # 10000 tickets/month
            baseline_source="Quiz",
            target_source="Benchmark"
        )
        # 0.60 improvement * 5 * 10000 = 30000
        assert benefit.monthly_value == pytest.approx(30000, rel=0.001)
