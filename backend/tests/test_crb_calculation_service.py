"""
Tests for CRB Calculation Service

Comprehensive tests covering:
- get_effective_hourly_rate resolution priority and edge cases
- INDUSTRY_HOURLY_RATES_EUR completeness and sanity
- ROI/payback calculation math via CRBCalculationService._calculate_roi
- build_connect_path_crb and build_replace_path_crb
- _build_recommendation_summary logic
- validate_crb_analysis edge cases
- compare_paths and _score_path
- Integration-style tests verifying proportional behavior
"""

import pytest

from src.services.crb_calculation_service import (
    CRBCalculationService,
    crb_service,
    build_connect_crb,
    build_replace_crb,
    validate_crb,
    get_effective_hourly_rate,
    INDUSTRY_HOURLY_RATES_EUR,
    DEFAULT_HOURLY_RATE_EUR,
    ANNUAL_WORKING_HOURS,
    PROFESSIONAL_COST_MULTIPLIER,
    MAX_CREDIBLE_ROI_PERCENT,
    MIN_CREDIBLE_PAYBACK_MONTHS,
)
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


# ---------------------------------------------------------------------------
# get_effective_hourly_rate
# ---------------------------------------------------------------------------


class TestGetEffectiveHourlyRate:
    """Tests for the get_effective_hourly_rate function."""

    # -- Priority 1: explicit hourly_rate from quiz answers --

    def test_explicit_hourly_rate_from_quiz_answers(self):
        """Explicit hourly_rate in quiz_answers takes highest priority."""
        rate, source = get_effective_hourly_rate(
            industry="dental",
            quiz_answers={"hourly_rate": 95},
        )
        assert rate == 95
        assert source == "provided by user"

    def test_explicit_labor_cost_key(self):
        """labor_cost key is also accepted as explicit hourly rate."""
        rate, source = get_effective_hourly_rate(
            industry="dental",
            quiz_answers={"labor_cost": 110},
        )
        assert rate == 110
        assert source == "provided by user"

    def test_explicit_rate_as_string(self):
        """Explicit rate provided as a string should be parsed correctly."""
        rate, source = get_effective_hourly_rate(
            industry="ecommerce",
            quiz_answers={"hourly_rate": "75"},
        )
        assert rate == 75
        assert source == "provided by user"

    def test_explicit_rate_below_minimum_falls_through(self):
        """Hourly rate below 5 EUR is considered out of range and skipped."""
        rate, source = get_effective_hourly_rate(
            industry="dental",
            quiz_answers={"hourly_rate": 3},
        )
        # Should fall through to industry default for dental (85)
        assert rate == 85
        assert "industry default" in source

    def test_explicit_rate_above_maximum_falls_through(self):
        """Hourly rate above 500 EUR is considered out of range and skipped."""
        rate, source = get_effective_hourly_rate(
            industry="dental",
            quiz_answers={"hourly_rate": 600},
        )
        assert rate == 85
        assert "industry default" in source

    def test_explicit_rate_at_lower_boundary(self):
        """Hourly rate exactly 5 EUR is accepted."""
        rate, source = get_effective_hourly_rate(
            quiz_answers={"hourly_rate": 5},
        )
        assert rate == 5
        assert source == "provided by user"

    def test_explicit_rate_at_upper_boundary(self):
        """Hourly rate exactly 500 EUR is accepted."""
        rate, source = get_effective_hourly_rate(
            quiz_answers={"hourly_rate": 500},
        )
        assert rate == 500
        assert source == "provided by user"

    def test_explicit_rate_invalid_string_falls_through(self):
        """Non-numeric hourly_rate string is skipped."""
        rate, source = get_effective_hourly_rate(
            industry="dental",
            quiz_answers={"hourly_rate": "not-a-number"},
        )
        assert rate == 85
        assert "industry default" in source

    def test_explicit_rate_none_falls_through(self):
        """None hourly_rate is treated as absent."""
        rate, source = get_effective_hourly_rate(
            industry="dental",
            quiz_answers={"hourly_rate": None},
        )
        assert rate == 85
        assert "industry default" in source

    # -- Priority 2: salary conversion --

    def test_salary_conversion(self):
        """Annual salary is converted to hourly rate via / 2080."""
        rate, source = get_effective_hourly_rate(
            industry="dental",
            quiz_answers={"annual_salary": 104000},
        )
        assert rate == 50.0  # 104000 / 2080 = 50
        assert "derived from annual salary" in source
        assert "104,000" in source

    def test_salary_key_variant(self):
        """The 'salary' key also works for salary conversion."""
        rate, source = get_effective_hourly_rate(
            industry="dental",
            quiz_answers={"salary": 52000},
        )
        assert rate == 25.0  # 52000 / 2080 = 25
        assert "derived from annual salary" in source

    def test_salary_as_string(self):
        """Salary provided as string should be parsed correctly."""
        rate, source = get_effective_hourly_rate(
            quiz_answers={"annual_salary": "83200"},
        )
        assert rate == 40.0  # 83200 / 2080 = 40
        assert "derived from annual salary" in source

    def test_salary_yielding_rate_below_minimum_falls_through(self):
        """Salary that yields a rate below 5 EUR/hr is skipped."""
        # 5 EUR/hr * 2080 = 10400; anything below that yields rate < 5
        rate, source = get_effective_hourly_rate(
            industry="dental",
            quiz_answers={"annual_salary": 8000},
        )
        # 8000 / 2080 = 3.85 -> below 5, falls through to industry default
        assert rate == 85
        assert "industry default" in source

    def test_salary_yielding_rate_above_maximum_falls_through(self):
        """Salary that yields a rate above 500 EUR/hr is skipped."""
        # 500 * 2080 = 1,040,000; anything above yields rate > 500
        rate, source = get_effective_hourly_rate(
            industry="dental",
            quiz_answers={"annual_salary": 2000000},
        )
        # 2000000 / 2080 = 961.54 -> above 500, falls through
        assert rate == 85
        assert "industry default" in source

    def test_zero_salary_falls_through(self):
        """Zero salary is skipped."""
        rate, source = get_effective_hourly_rate(
            industry="dental",
            quiz_answers={"annual_salary": 0},
        )
        assert rate == 85
        assert "industry default" in source

    def test_negative_salary_falls_through(self):
        """Negative salary is skipped (not > 0)."""
        rate, source = get_effective_hourly_rate(
            industry="dental",
            quiz_answers={"annual_salary": -50000},
        )
        assert rate == 85
        assert "industry default" in source

    def test_invalid_salary_string_falls_through(self):
        """Non-numeric salary string is skipped."""
        rate, source = get_effective_hourly_rate(
            industry="dental",
            quiz_answers={"annual_salary": "not-a-number"},
        )
        assert rate == 85
        assert "industry default" in source

    # -- Priority 1 > Priority 2 --

    def test_explicit_rate_takes_priority_over_salary(self):
        """When both hourly_rate and salary are present, hourly_rate wins."""
        rate, source = get_effective_hourly_rate(
            industry="dental",
            quiz_answers={"hourly_rate": 120, "annual_salary": 60000},
        )
        assert rate == 120
        assert source == "provided by user"

    # -- Priority 3: industry defaults --

    def test_industry_default_professional_services(self):
        """professional-services industry returns 125 EUR/hr."""
        rate, source = get_effective_hourly_rate(industry="professional-services")
        assert rate == 125
        assert "industry default" in source

    def test_industry_default_professional_services_underscore(self):
        """professional_services (underscore) also returns 125 EUR/hr."""
        rate, source = get_effective_hourly_rate(industry="professional_services")
        assert rate == 125
        assert "industry default" in source

    def test_industry_default_dental(self):
        """dental industry returns 85 EUR/hr."""
        rate, source = get_effective_hourly_rate(industry="dental")
        assert rate == 85
        assert "industry default" in source

    def test_industry_default_ecommerce(self):
        """ecommerce industry returns 35 EUR/hr."""
        rate, source = get_effective_hourly_rate(industry="ecommerce")
        assert rate == 35
        assert "industry default" in source

    def test_industry_default_e_commerce_hyphen(self):
        """e-commerce (hyphenated) also returns 35 EUR/hr."""
        rate, source = get_effective_hourly_rate(industry="e-commerce")
        assert rate == 35
        assert "industry default" in source

    def test_industry_default_home_services(self):
        """home-services industry returns 65 EUR/hr."""
        rate, source = get_effective_hourly_rate(industry="home-services")
        assert rate == 65

    def test_industry_default_recruiting(self):
        """recruiting industry returns 75 EUR/hr."""
        rate, source = get_effective_hourly_rate(industry="recruiting")
        assert rate == 75

    def test_industry_default_coaching(self):
        """coaching industry returns 100 EUR/hr."""
        rate, source = get_effective_hourly_rate(industry="coaching")
        assert rate == 100

    def test_industry_default_veterinary(self):
        """veterinary industry returns 70 EUR/hr."""
        rate, source = get_effective_hourly_rate(industry="veterinary")
        assert rate == 70

    def test_industry_default_music_studios(self):
        """music-studios industry returns 55 EUR/hr."""
        rate, source = get_effective_hourly_rate(industry="music-studios")
        assert rate == 55

    def test_industry_case_insensitive(self):
        """Industry matching is case-insensitive."""
        rate, source = get_effective_hourly_rate(industry="DENTAL")
        # DENTAL.lower() = dental which is in the dict
        assert rate == 85

    def test_industry_with_whitespace(self):
        """Industry with leading/trailing whitespace is trimmed."""
        rate, source = get_effective_hourly_rate(industry="  dental  ")
        assert rate == 85

    # -- Priority 4: global fallback --

    def test_unknown_industry_falls_back_to_global_default(self):
        """Unknown industry falls back to DEFAULT_HOURLY_RATE_EUR (50)."""
        rate, source = get_effective_hourly_rate(industry="underwater-basket-weaving")
        assert rate == DEFAULT_HOURLY_RATE_EUR
        assert rate == 50
        assert "default estimate" in source

    def test_empty_industry_falls_back_to_global_default(self):
        """Empty industry string falls back to global default."""
        rate, source = get_effective_hourly_rate(industry="")
        # "" is in the dict as "default" key? No, "" != "default"
        # So it falls through to global fallback
        assert rate == DEFAULT_HOURLY_RATE_EUR
        assert "default estimate" in source

    def test_no_arguments_falls_back_to_global_default(self):
        """No arguments at all falls back to global default."""
        rate, source = get_effective_hourly_rate()
        assert rate == DEFAULT_HOURLY_RATE_EUR
        assert "default estimate" in source

    def test_none_quiz_answers_uses_industry_or_default(self):
        """None quiz_answers is treated as empty dict."""
        rate, source = get_effective_hourly_rate(
            industry="coaching",
            quiz_answers=None,
        )
        assert rate == 100
        assert "industry default" in source


# ---------------------------------------------------------------------------
# INDUSTRY_HOURLY_RATES_EUR validation
# ---------------------------------------------------------------------------


class TestIndustryHourlyRates:
    """Tests for the INDUSTRY_HOURLY_RATES_EUR constant."""

    EXPECTED_INDUSTRIES = [
        "professional-services",
        "professional_services",
        "dental",
        "ecommerce",
        "e-commerce",
        "home-services",
        "home_services",
        "recruiting",
        "coaching",
        "veterinary",
        "music-studios",
        "music_studios",
        "default",
    ]

    def test_all_expected_industries_present(self):
        """All expected industry keys exist in the rates dict."""
        for industry in self.EXPECTED_INDUSTRIES:
            assert industry in INDUSTRY_HOURLY_RATES_EUR, (
                f"Missing industry key: {industry}"
            )

    def test_all_rates_positive(self):
        """All rates must be greater than 0."""
        for industry, rate in INDUSTRY_HOURLY_RATES_EUR.items():
            assert rate > 0, f"Rate for {industry} is not positive: {rate}"

    def test_all_rates_below_500(self):
        """All rates should be below 500 EUR (sanity check)."""
        for industry, rate in INDUSTRY_HOURLY_RATES_EUR.items():
            assert rate < 500, f"Rate for {industry} is unreasonably high: {rate}"

    def test_slug_variants_match(self):
        """Hyphenated and underscored slug variants have the same rate."""
        variants = [
            ("professional-services", "professional_services"),
            ("e-commerce", "ecommerce"),
            ("home-services", "home_services"),
            ("music-studios", "music_studios"),
        ]
        for hyphen, underscore in variants:
            assert INDUSTRY_HOURLY_RATES_EUR[hyphen] == INDUSTRY_HOURLY_RATES_EUR[underscore], (
                f"Rates differ for {hyphen} ({INDUSTRY_HOURLY_RATES_EUR[hyphen]}) "
                f"vs {underscore} ({INDUSTRY_HOURLY_RATES_EUR[underscore]})"
            )

    def test_default_key_equals_constant(self):
        """The 'default' key matches DEFAULT_HOURLY_RATE_EUR."""
        assert INDUSTRY_HOURLY_RATES_EUR["default"] == DEFAULT_HOURLY_RATE_EUR


# ---------------------------------------------------------------------------
# CRBCalculationService._calculate_roi  (via build methods)
# ---------------------------------------------------------------------------


class TestCalculateRoi:
    """Tests for CRBCalculationService._calculate_roi."""

    def setup_method(self):
        self.service = CRBCalculationService()

    def test_basic_roi_expected(self):
        """Test expected ROI with known inputs.

        monthly_benefit=1000, implementation_cost=2000, monthly_cost=100
        yearly_benefit = 12000
        yearly_cost = 1200
        first_year_investment = 2000 + 1200 = 3200
        net_annual = 12000 - 1200 = 10800
        ROI = (10800 / 3200) * 100 = 337.5%
        """
        roi = self.service._calculate_roi(
            monthly_benefit=1000,
            implementation_cost=2000,
            monthly_cost=100,
        )
        assert roi.expected == 337.5

    def test_conservative_is_70_percent_of_benefit(self):
        """Conservative scenario uses 70% of expected benefit.

        yearly_benefit * 0.7 = 12000 * 0.7 = 8400
        conservative_net = 8400 - 1200 = 7200
        conservative_roi = (7200 / 3200) * 100 = 225.0%
        """
        roi = self.service._calculate_roi(
            monthly_benefit=1000,
            implementation_cost=2000,
            monthly_cost=100,
        )
        assert roi.conservative == 225.0

    def test_optimistic_is_130_percent_of_benefit(self):
        """Optimistic scenario uses 130% of expected benefit.

        yearly_benefit * 1.3 = 12000 * 1.3 = 15600
        optimistic_net = 15600 - 1200 = 14400
        optimistic_roi = (14400 / 3200) * 100 = 450.0%
        """
        roi = self.service._calculate_roi(
            monthly_benefit=1000,
            implementation_cost=2000,
            monthly_cost=100,
        )
        assert roi.optimistic == 450.0

    def test_ordering_conservative_lt_expected_lt_optimistic(self):
        """Conservative < Expected < Optimistic always holds for positive benefits."""
        roi = self.service._calculate_roi(
            monthly_benefit=500,
            implementation_cost=1000,
            monthly_cost=50,
        )
        assert roi.conservative < roi.expected < roi.optimistic

    def test_payback_expected_calculation(self):
        """Payback = implementation_cost / (monthly_benefit - monthly_cost).

        payback = 2000 / (1000 - 100) = 2000 / 900 = 2.22 months
        """
        roi = self.service._calculate_roi(
            monthly_benefit=1000,
            implementation_cost=2000,
            monthly_cost=100,
        )
        assert roi.payback_months_expected == pytest.approx(2.2, abs=0.1)

    def test_payback_conservative_calculation(self):
        """Conservative payback uses 70% of net monthly.

        payback = 2000 / ((1000 - 100) * 0.7) = 2000 / 630 = 3.17 months
        """
        roi = self.service._calculate_roi(
            monthly_benefit=1000,
            implementation_cost=2000,
            monthly_cost=100,
        )
        assert roi.payback_months_conservative == pytest.approx(3.2, abs=0.1)

    def test_zero_implementation_cost_zero_payback(self):
        """When implementation_cost is 0, payback is 0 months."""
        roi = self.service._calculate_roi(
            monthly_benefit=500,
            implementation_cost=0,
            monthly_cost=50,
        )
        assert roi.payback_months_expected == 0
        assert roi.payback_months_conservative == 0

    def test_zero_costs_returns_undefined_roi(self):
        """When both implementation and monthly costs are 0, ROI is undefined."""
        roi = self.service._calculate_roi(
            monthly_benefit=1000,
            implementation_cost=0,
            monthly_cost=0,
        )
        assert roi.expected == 0
        assert roi.conservative == 0
        assert roi.optimistic == 0
        assert roi.payback_months_expected == 999
        assert roi.payback_months_conservative == 999
        assert "No cost data" in roi.sensitivity_note

    def test_negative_net_monthly_gives_999_payback(self):
        """When monthly cost exceeds benefit, payback is 999 (infinite)."""
        roi = self.service._calculate_roi(
            monthly_benefit=50,
            implementation_cost=1000,
            monthly_cost=200,
        )
        assert roi.payback_months_expected == 999
        assert roi.payback_months_conservative == 999

    def test_negative_roi_when_cost_exceeds_benefit(self):
        """ROI is negative when yearly costs exceed yearly benefits.

        monthly_benefit=100, monthly_cost=200, implementation=1000
        yearly_benefit = 1200
        yearly_cost = 2400
        first_year_investment = 1000 + 2400 = 3400
        net_annual = 1200 - 2400 = -1200
        ROI = (-1200 / 3400) * 100 = -35.3%
        """
        roi = self.service._calculate_roi(
            monthly_benefit=100,
            implementation_cost=1000,
            monthly_cost=200,
        )
        assert roi.expected < 0
        assert roi.expected == pytest.approx(-35.3, abs=0.1)

    def test_very_large_numbers(self):
        """ROI calculation handles very large numbers without overflow."""
        roi = self.service._calculate_roi(
            monthly_benefit=1_000_000,
            implementation_cost=5_000_000,
            monthly_cost=100_000,
        )
        # yearly_benefit = 12M, yearly_cost = 1.2M
        # first_year_investment = 5M + 1.2M = 6.2M
        # net_annual = 12M - 1.2M = 10.8M
        # ROI = 10.8M / 6.2M * 100 = 174.2%
        assert roi.expected == pytest.approx(174.2, abs=0.1)

    def test_very_small_monthly_benefit(self):
        """ROI is calculated correctly with very small monthly benefit."""
        roi = self.service._calculate_roi(
            monthly_benefit=1,
            implementation_cost=100,
            monthly_cost=0.5,
        )
        # yearly_benefit = 12, yearly_cost = 6
        # first_year_investment = 100 + 6 = 106
        # net_annual = 12 - 6 = 6
        # ROI = (6 / 106) * 100 = 5.66%
        assert roi.expected == pytest.approx(5.7, abs=0.1)

    def test_sensitivity_note_on_exceptional_roi(self):
        """ROI above MAX_CREDIBLE_ROI_PERCENT triggers sensitivity note."""
        roi = self.service._calculate_roi(
            monthly_benefit=10000,
            implementation_cost=100,
            monthly_cost=10,
        )
        assert roi.expected > MAX_CREDIBLE_ROI_PERCENT
        assert f"ROI above {MAX_CREDIBLE_ROI_PERCENT}%" in roi.sensitivity_note

    def test_sensitivity_note_on_fast_payback(self):
        """Payback below MIN_CREDIBLE_PAYBACK_MONTHS triggers sensitivity note."""
        roi = self.service._calculate_roi(
            monthly_benefit=5000,
            implementation_cost=5000,
            monthly_cost=50,
        )
        # payback = 5000 / (5000 - 50) = 1.01 months
        assert roi.payback_months_expected < MIN_CREDIBLE_PAYBACK_MONTHS
        # But ROI might also be > 500%, check which note fires
        # ROI = (60000 - 600) / (5000 + 600) * 100 = 59400 / 5600 * 100 = 1060.7%
        # ROI > 500 fires first in the if/elif chain
        assert roi.sensitivity_note != ""

    def test_no_sensitivity_note_for_normal_roi(self):
        """No sensitivity note when ROI and payback are in normal ranges."""
        roi = self.service._calculate_roi(
            monthly_benefit=300,
            implementation_cost=2000,
            monthly_cost=50,
        )
        # payback = 2000 / 250 = 8 months (> 3)
        # yearly_benefit = 3600, yearly_cost = 600
        # ROI = (3000 / 2600) * 100 = 115.4% (< 500)
        assert roi.sensitivity_note == ""


# ---------------------------------------------------------------------------
# build_connect_path_crb
# ---------------------------------------------------------------------------


class TestBuildConnectPathCRB:
    """Tests for CRBCalculationService.build_connect_path_crb."""

    def setup_method(self):
        self.service = CRBCalculationService()

    def test_minimal_inputs(self):
        """Connect CRB can be built with minimal required inputs."""
        crb = self.service.build_connect_path_crb(
            implementation_hours=4,
            monthly_costs=[{"item": "API", "cost": 10}],
            primary_metric="time",
            baseline_value="before",
            target_value="after",
            monthly_value_eur=500,
            calculation_formula="hours * rate",
            confidence="MEDIUM",
        )
        assert isinstance(crb, CRBAnalysis)
        assert crb.confidence_level == "MEDIUM"

    def test_diy_cost_uses_default_hourly_rate(self):
        """DIY cost uses DEFAULT_HOURLY_RATE_EUR (50) when no hourly_rate override."""
        crb = self.service.build_connect_path_crb(
            implementation_hours=10,
            monthly_costs=[],
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=500,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        assert crb.cost.total_implementation_diy == 10 * DEFAULT_HOURLY_RATE_EUR
        assert crb.cost.total_implementation_diy == 500

    def test_diy_cost_uses_custom_hourly_rate(self):
        """DIY cost uses the provided hourly_rate override."""
        crb = self.service.build_connect_path_crb(
            implementation_hours=10,
            monthly_costs=[],
            hourly_rate=100,
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=500,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        assert crb.cost.total_implementation_diy == 10 * 100
        assert crb.cost.total_implementation_diy == 1000

    def test_professional_cost_is_multiplied(self):
        """Professional cost is hours * rate * PROFESSIONAL_COST_MULTIPLIER."""
        crb = self.service.build_connect_path_crb(
            implementation_hours=10,
            monthly_costs=[],
            hourly_rate=80,
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=500,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        expected_professional = 10 * 80 * PROFESSIONAL_COST_MULTIPLIER
        assert crb.cost.total_implementation_professional == expected_professional

    def test_monthly_costs_summed_correctly(self):
        """Monthly costs from multiple items are summed."""
        crb = self.service.build_connect_path_crb(
            implementation_hours=4,
            monthly_costs=[
                {"item": "n8n cloud", "cost": 20},
                {"item": "Twilio SMS", "cost": 15},
                {"item": "Claude API", "cost": 30},
            ],
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=500,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        assert crb.cost.total_monthly == 65  # 20 + 15 + 30

    def test_hidden_costs_set_correctly(self):
        """Hidden costs (training hours, productivity dip) are stored."""
        crb = self.service.build_connect_path_crb(
            implementation_hours=4,
            monthly_costs=[],
            hidden_training_hours=8,
            hidden_productivity_dip_weeks=3,
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=500,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        assert crb.cost.hidden.training_hours == 8
        assert crb.cost.hidden.productivity_dip_weeks == 3

    def test_risk_fields_populated(self):
        """Risk assessment fields are set correctly."""
        crb = self.service.build_connect_path_crb(
            implementation_hours=4,
            monthly_costs=[],
            implementation_complexity=4,
            complexity_reason="Needs custom API",
            dependency_vendor="Zapier",
            reversal_difficulty="Hard",
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=500,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        assert crb.risk.implementation_score == 4
        assert crb.risk.implementation_reason == "Needs custom API"
        assert "Zapier" in crb.risk.dependency_risk
        assert crb.risk.reversal_difficulty == "Hard"

    def test_benefit_fields_populated(self):
        """Benefit quantification fields are set correctly."""
        crb = self.service.build_connect_path_crb(
            implementation_hours=4,
            monthly_costs=[],
            primary_metric="no-show rate",
            baseline_value="18% (user data)",
            target_value="8% (benchmark)",
            monthly_value_eur=3500,
            calculation_formula="10% x 350 x 100",
            confidence="HIGH",
            confidence_reason="User provided data",
        )
        assert crb.benefit.primary_metric == "no-show rate"
        assert crb.benefit.baseline == "18% (user data)"
        assert crb.benefit.target == "8% (benchmark)"
        assert crb.benefit.monthly_value == 3500
        assert crb.benefit.calculation == "10% x 350 x 100"
        assert crb.benefit.confidence == "HIGH"
        assert crb.benefit.confidence_reason == "User provided data"

    def test_data_gaps_stored(self):
        """Data gaps list is stored in the CRB analysis."""
        crb = self.service.build_connect_path_crb(
            implementation_hours=4,
            monthly_costs=[],
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=500,
            calculation_formula="f",
            confidence="LOW",
            data_gaps=["Unknown team size", "No usage data"],
        )
        assert len(crb.data_gaps) == 2
        assert "Unknown team size" in crb.data_gaps

    def test_data_gaps_default_empty(self):
        """Data gaps defaults to empty list when not provided."""
        crb = self.service.build_connect_path_crb(
            implementation_hours=4,
            monthly_costs=[],
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=500,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        assert crb.data_gaps == []

    def test_roi_is_calculated(self):
        """ROI analysis is generated as part of the CRB."""
        crb = self.service.build_connect_path_crb(
            implementation_hours=10,
            monthly_costs=[{"item": "API", "cost": 50}],
            hourly_rate=50,
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=1000,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        assert crb.roi is not None
        assert crb.roi.expected > 0  # 1000/month benefit vs 500 impl + 50/month cost

    def test_recommendation_summary_generated(self):
        """Recommendation summary is generated with benefit and payback info."""
        crb = self.service.build_connect_path_crb(
            implementation_hours=10,
            monthly_costs=[{"item": "API", "cost": 50}],
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=1000,
            calculation_formula="f",
            confidence="HIGH",
        )
        assert "Net benefit" in crb.recommendation_summary
        assert "Payback" in crb.recommendation_summary
        assert "HIGH" in crb.recommendation_summary


# ---------------------------------------------------------------------------
# build_replace_path_crb
# ---------------------------------------------------------------------------


class TestBuildReplacePathCRB:
    """Tests for CRBCalculationService.build_replace_path_crb."""

    def setup_method(self):
        self.service = CRBCalculationService()

    def test_minimal_replace_path(self):
        """Replace CRB can be built with minimal inputs."""
        crb = self.service.build_replace_path_crb(
            monthly_subscription=100,
            setup_cost=500,
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=800,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        assert isinstance(crb, CRBAnalysis)
        assert crb.confidence_level == "MEDIUM"

    def test_no_diy_cost_for_replace(self):
        """Replace path has no DIY implementation cost."""
        crb = self.service.build_replace_path_crb(
            monthly_subscription=100,
            setup_cost=500,
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=800,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        assert crb.cost.implementation_diy is None
        assert crb.cost.total_implementation_diy == 0

    def test_professional_cost_is_setup_plus_migration(self):
        """Professional implementation cost = setup + migration."""
        crb = self.service.build_replace_path_crb(
            monthly_subscription=100,
            setup_cost=2000,
            migration_cost=500,
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=800,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        assert crb.cost.total_implementation_professional == 2500

    def test_monthly_cost_is_subscription(self):
        """Monthly cost is the vendor subscription."""
        crb = self.service.build_replace_path_crb(
            monthly_subscription=199,
            setup_cost=500,
            vendor_name="Zendesk",
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=800,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        assert crb.cost.total_monthly == 199

    def test_vendor_name_in_monthly_item_and_risk(self):
        """Vendor name appears in monthly cost item description and risk."""
        crb = self.service.build_replace_path_crb(
            monthly_subscription=199,
            setup_cost=500,
            vendor_name="HubSpot",
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=800,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        # Vendor name in monthly item
        monthly_items = crb.cost.monthly_ongoing.breakdown
        assert any("HubSpot" in item.item for item in monthly_items)
        # Vendor name in dependency risk
        assert "HubSpot" in crb.risk.dependency_risk

    def test_replace_has_additional_risks(self):
        """Replace path includes additional risks about migration and learning."""
        crb = self.service.build_replace_path_crb(
            monthly_subscription=100,
            setup_cost=500,
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=800,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        assert len(crb.risk.additional_risks) == 2
        assert any("migration" in r.lower() for r in crb.risk.additional_risks)
        assert any("learn" in r.lower() for r in crb.risk.additional_risks)

    def test_replace_hidden_costs_defaults(self):
        """Replace path has higher default training and productivity dip."""
        crb = self.service.build_replace_path_crb(
            monthly_subscription=100,
            setup_cost=500,
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=800,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        # Default: training_hours=4, productivity_dip_weeks=2
        assert crb.cost.hidden.training_hours == 4
        assert crb.cost.hidden.productivity_dip_weeks == 2

    def test_replace_roi_uses_setup_plus_migration_as_implementation(self):
        """ROI calculation uses setup+migration as implementation cost.

        setup=2000, migration=500 -> implementation=2500
        monthly_benefit=1000, monthly_cost=200
        payback = 2500 / (1000 - 200) = 3.125 months
        """
        crb = self.service.build_replace_path_crb(
            monthly_subscription=200,
            setup_cost=2000,
            migration_cost=500,
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=1000,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        assert crb.roi is not None
        assert crb.roi.payback_months_expected == pytest.approx(3.1, abs=0.1)


# ---------------------------------------------------------------------------
# _build_recommendation_summary
# ---------------------------------------------------------------------------


class TestBuildRecommendationSummary:
    """Tests for CRBCalculationService._build_recommendation_summary."""

    def setup_method(self):
        self.service = CRBCalculationService()

    def test_positive_net_with_implementation_cost(self):
        """Recommendation includes net benefit, payback, and confidence."""
        summary = self.service._build_recommendation_summary(
            monthly_benefit=1000,
            monthly_cost=200,
            implementation_cost=2400,
            confidence="HIGH",
        )
        assert "Net benefit: 800/month" in summary
        assert "Payback: 3.0 months" in summary
        assert "Confidence: HIGH" in summary

    def test_positive_net_no_implementation_cost(self):
        """When no implementation cost, summary says so."""
        summary = self.service._build_recommendation_summary(
            monthly_benefit=1000,
            monthly_cost=200,
            implementation_cost=0,
            confidence="MEDIUM",
        )
        assert "Net benefit: 800/month" in summary
        assert "No implementation cost" in summary
        assert "Confidence: MEDIUM" in summary

    def test_cost_exceeds_benefit(self):
        """When cost exceeds benefit, recommendation says 'Not recommended'."""
        summary = self.service._build_recommendation_summary(
            monthly_benefit=100,
            monthly_cost=200,
            implementation_cost=1000,
            confidence="LOW",
        )
        assert "Not recommended" in summary
        assert "200/month vs 100/month" in summary


# ---------------------------------------------------------------------------
# validate_crb_analysis
# ---------------------------------------------------------------------------


class TestValidateCRBAnalysis:
    """Tests for CRBCalculationService.validate_crb_analysis."""

    def setup_method(self):
        self.service = CRBCalculationService()

    def _make_valid_crb(self, **overrides):
        """Helper to build a valid CRB for testing validation."""
        return self.service.build_connect_path_crb(
            implementation_hours=overrides.get("implementation_hours", 8),
            monthly_costs=overrides.get("monthly_costs", [{"item": "API", "cost": 10}]),
            primary_metric=overrides.get("primary_metric", "metric"),
            baseline_value=overrides.get("baseline_value", "before"),
            target_value=overrides.get("target_value", "after"),
            monthly_value_eur=overrides.get("monthly_value_eur", 1000),
            calculation_formula=overrides.get("calculation_formula", "hours * rate"),
            confidence=overrides.get("confidence", "HIGH"),
        )

    def test_valid_crb_has_no_issues(self):
        """A properly built CRB passes validation."""
        crb = self._make_valid_crb()
        issues = self.service.validate_crb_analysis(crb)
        assert issues == []

    def test_missing_both_implementation_costs(self):
        """Validation catches missing implementation costs."""
        crb = CRBAnalysis(
            cost=CostBreakdown(
                # No implementation_diy, no implementation_professional
            ),
            risk=RiskAssessment(
                implementation_score=2,
                implementation_reason="Test",
                dependency_risk="Test",
                reversal_difficulty="Easy",
            ),
            benefit=BenefitQuantification(
                primary_metric="test",
                baseline="b",
                target="t",
                monthly_value=1000,
                calculation="formula",
                confidence="HIGH",
            ),
            recommendation_summary="Test",
            confidence_level="HIGH",
        )
        issues = self.service.validate_crb_analysis(crb)
        assert any("implementation cost" in issue.lower() for issue in issues)

    def test_missing_benefit_calculation(self):
        """Validation catches empty calculation formula."""
        crb = CRBAnalysis(
            cost=CostBreakdown(
                implementation_diy=ImplementationCostDIY(hours=8, description="test"),
            ),
            risk=RiskAssessment(
                implementation_score=2,
                implementation_reason="Test",
                dependency_risk="Test",
                reversal_difficulty="Easy",
            ),
            benefit=BenefitQuantification(
                primary_metric="test",
                baseline="b",
                target="t",
                monthly_value=1000,
                calculation="",
                confidence="HIGH",
            ),
            recommendation_summary="Test",
            confidence_level="HIGH",
        )
        issues = self.service.validate_crb_analysis(crb)
        assert any("calculation" in issue.lower() for issue in issues)

    def test_zero_monthly_benefit_flagged(self):
        """Validation catches zero monthly benefit."""
        crb = self._make_valid_crb(monthly_value_eur=0)
        issues = self.service.validate_crb_analysis(crb)
        assert any("zero" in issue.lower() or "negative" in issue.lower() for issue in issues)

    def test_high_roi_without_sensitivity_note_flagged(self):
        """Validation catches ROI > 500% without sensitivity note."""
        # Build a CRB that will have very high ROI
        crb = self._make_valid_crb(
            implementation_hours=1,
            monthly_costs=[],
            monthly_value_eur=10000,
        )
        # If sensitivity note is already set (which it would be), clear it to test validation
        if crb.roi and crb.roi.sensitivity_note:
            # The service actually sets sensitivity_note for high ROI, so this
            # test verifies the validation logic catches it when note is missing
            crb_no_note = CRBAnalysis(
                cost=crb.cost,
                risk=crb.risk,
                benefit=crb.benefit,
                roi=ROIAnalysis(
                    conservative=crb.roi.conservative,
                    expected=crb.roi.expected,
                    optimistic=crb.roi.optimistic,
                    payback_months_conservative=crb.roi.payback_months_conservative,
                    payback_months_expected=crb.roi.payback_months_expected,
                    sensitivity_note="",  # Force empty
                ),
                recommendation_summary=crb.recommendation_summary,
                confidence_level=crb.confidence_level,
            )
            issues = self.service.validate_crb_analysis(crb_no_note)
            assert any("ROI" in issue for issue in issues)

    def test_missing_risk_reason_flagged(self):
        """Validation catches empty implementation reason."""
        crb = CRBAnalysis(
            cost=CostBreakdown(
                implementation_diy=ImplementationCostDIY(hours=8, description="test"),
            ),
            risk=RiskAssessment(
                implementation_score=2,
                implementation_reason="",
                dependency_risk="Test",
                reversal_difficulty="Easy",
            ),
            benefit=BenefitQuantification(
                primary_metric="test",
                baseline="b",
                target="t",
                monthly_value=1000,
                calculation="formula",
                confidence="HIGH",
            ),
            recommendation_summary="Test",
            confidence_level="HIGH",
        )
        issues = self.service.validate_crb_analysis(crb)
        assert any("reason" in issue.lower() for issue in issues)


# ---------------------------------------------------------------------------
# compare_paths and _score_path
# ---------------------------------------------------------------------------


class TestComparePaths:
    """Tests for CRBCalculationService.compare_paths and _score_path."""

    def setup_method(self):
        self.service = CRBCalculationService()

    def _make_connect(self, monthly_value=1000, implementation_hours=8,
                      monthly_cost=30, confidence="HIGH", complexity=2):
        return self.service.build_connect_path_crb(
            implementation_hours=implementation_hours,
            monthly_costs=[{"item": "API", "cost": monthly_cost}],
            implementation_complexity=complexity,
            primary_metric="test",
            baseline_value="before",
            target_value="after",
            monthly_value_eur=monthly_value,
            calculation_formula="formula",
            confidence=confidence,
        )

    def _make_replace(self, monthly_value=1200, setup_cost=3000,
                      monthly_subscription=200, confidence="MEDIUM", complexity=4):
        return self.service.build_replace_path_crb(
            monthly_subscription=monthly_subscription,
            setup_cost=setup_cost,
            implementation_complexity=complexity,
            vendor_name="Vendor",
            primary_metric="test",
            baseline_value="before",
            target_value="after",
            monthly_value_eur=monthly_value,
            calculation_formula="formula",
            confidence=confidence,
        )

    def test_both_paths_none(self):
        """Comparing no paths returns error."""
        result = self.service.compare_paths(None, None)
        assert "error" in result

    def test_only_connect_path(self):
        """When only connect path exists, it wins."""
        connect = self._make_connect()
        result = self.service.compare_paths(connect, None)
        assert result["winner"] == "CONNECT"
        assert result["connect"] is not None
        assert result["replace"] is None

    def test_only_replace_path(self):
        """When only replace path exists, it wins."""
        replace = self._make_replace()
        result = self.service.compare_paths(None, replace)
        assert result["winner"] == "REPLACE"
        assert result["connect"] is None
        assert result["replace"] is not None

    def test_both_paths_compared(self):
        """When both paths exist, a winner is determined."""
        connect = self._make_connect()
        replace = self._make_replace()
        result = self.service.compare_paths(connect, replace)
        assert result["winner"] in ("CONNECT", "REPLACE", "EITHER")
        assert result["reasoning"] != ""

    def test_comparison_data_includes_expected_fields(self):
        """Comparison data includes key financial and risk metrics."""
        connect = self._make_connect()
        replace = self._make_replace()
        result = self.service.compare_paths(connect, replace)

        for path_key in ["connect", "replace"]:
            path_data = result[path_key]
            assert "implementation_cost" in path_data
            assert "monthly_cost" in path_data
            assert "monthly_benefit" in path_data
            assert "risk_score" in path_data
            assert "roi_expected" in path_data
            assert "confidence" in path_data

    def test_connect_wins_with_better_roi_and_lower_risk(self):
        """Connect wins when it has better ROI and lower risk."""
        # Low cost, high benefit, low risk, high confidence
        connect = self._make_connect(
            monthly_value=2000, implementation_hours=4,
            monthly_cost=20, confidence="HIGH", complexity=1,
        )
        # High cost, same benefit, higher risk, lower confidence
        replace = self._make_replace(
            monthly_value=2000, setup_cost=10000,
            monthly_subscription=500, confidence="LOW", complexity=5,
        )
        result = self.service.compare_paths(connect, replace)
        assert result["winner"] == "CONNECT"

    def test_score_path_empty_data(self):
        """Scoring empty/None path data returns 0."""
        assert self.service._score_path(None) == 0
        assert self.service._score_path({}) == 0

    def test_score_path_higher_roi_gives_higher_score(self):
        """Higher ROI results in higher path score."""
        low_roi = {"roi_expected": 100, "risk_score": 2, "confidence": "MEDIUM"}
        high_roi = {"roi_expected": 400, "risk_score": 2, "confidence": "MEDIUM"}
        assert self.service._score_path(high_roi) > self.service._score_path(low_roi)

    def test_score_path_higher_risk_gives_lower_score(self):
        """Higher risk score results in lower path score."""
        low_risk = {"roi_expected": 200, "risk_score": 1, "confidence": "MEDIUM"}
        high_risk = {"roi_expected": 200, "risk_score": 5, "confidence": "MEDIUM"}
        assert self.service._score_path(low_risk) > self.service._score_path(high_risk)

    def test_score_path_high_confidence_bonus(self):
        """HIGH confidence gives a bonus over LOW confidence."""
        high_conf = {"roi_expected": 200, "risk_score": 3, "confidence": "HIGH"}
        low_conf = {"roi_expected": 200, "risk_score": 3, "confidence": "LOW"}
        assert self.service._score_path(high_conf) > self.service._score_path(low_conf)

    def test_score_path_roi_capped_at_500_percent(self):
        """ROI score is capped at 500% (5 points) to prevent runaway scores."""
        roi_500 = {"roi_expected": 500, "risk_score": 1, "confidence": "HIGH"}
        roi_1000 = {"roi_expected": 1000, "risk_score": 1, "confidence": "HIGH"}
        # Both should have the same ROI contribution (capped at 5)
        assert self.service._score_path(roi_500) == self.service._score_path(roi_1000)


# ---------------------------------------------------------------------------
# Convenience function wrappers
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_build_connect_crb_delegates_to_service(self):
        """build_connect_crb() delegates to crb_service.build_connect_path_crb()."""
        crb = build_connect_crb(
            implementation_hours=4,
            monthly_costs=[{"item": "API", "cost": 10}],
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=500,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        assert isinstance(crb, CRBAnalysis)

    def test_build_replace_crb_delegates_to_service(self):
        """build_replace_crb() delegates to crb_service.build_replace_path_crb()."""
        crb = build_replace_crb(
            monthly_subscription=100,
            setup_cost=500,
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=800,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        assert isinstance(crb, CRBAnalysis)

    def test_validate_crb_delegates_to_service(self):
        """validate_crb() delegates to crb_service.validate_crb_analysis()."""
        crb = build_connect_crb(
            implementation_hours=4,
            monthly_costs=[{"item": "API", "cost": 10}],
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=500,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        issues = validate_crb(crb)
        assert isinstance(issues, list)
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# Integration-style tests
# ---------------------------------------------------------------------------


class TestIntegration:
    """Integration tests verifying end-to-end behavior and proportional relationships."""

    def setup_method(self):
        self.service = CRBCalculationService()

    def test_doubling_hourly_rate_doubles_diy_cost(self):
        """Doubling hourly rate doubles DIY implementation cost."""
        crb_base = self.service.build_connect_path_crb(
            implementation_hours=10,
            monthly_costs=[],
            hourly_rate=50,
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=1000,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        crb_double = self.service.build_connect_path_crb(
            implementation_hours=10,
            monthly_costs=[],
            hourly_rate=100,
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=1000,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        assert crb_double.cost.total_implementation_diy == 2 * crb_base.cost.total_implementation_diy

    def test_doubling_hourly_rate_doubles_professional_cost(self):
        """Doubling hourly rate also doubles professional implementation cost."""
        crb_base = self.service.build_connect_path_crb(
            implementation_hours=10,
            monthly_costs=[],
            hourly_rate=50,
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=1000,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        crb_double = self.service.build_connect_path_crb(
            implementation_hours=10,
            monthly_costs=[],
            hourly_rate=100,
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=1000,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        assert crb_double.cost.total_implementation_professional == (
            2 * crb_base.cost.total_implementation_professional
        )

    def test_higher_benefit_gives_higher_roi(self):
        """Higher monthly benefit produces higher expected ROI."""
        crb_low = self.service.build_connect_path_crb(
            implementation_hours=10,
            monthly_costs=[{"item": "API", "cost": 50}],
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=500,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        crb_high = self.service.build_connect_path_crb(
            implementation_hours=10,
            monthly_costs=[{"item": "API", "cost": 50}],
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=2000,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        assert crb_high.roi.expected > crb_low.roi.expected

    def test_higher_implementation_cost_longer_payback(self):
        """Higher implementation cost leads to longer payback period."""
        crb_cheap = self.service.build_connect_path_crb(
            implementation_hours=4,
            monthly_costs=[{"item": "API", "cost": 50}],
            hourly_rate=50,
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=1000,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        crb_expensive = self.service.build_connect_path_crb(
            implementation_hours=40,
            monthly_costs=[{"item": "API", "cost": 50}],
            hourly_rate=50,
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=1000,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        assert crb_expensive.roi.payback_months_expected > crb_cheap.roi.payback_months_expected

    def test_industry_selection_affects_hourly_rate_and_therefore_roi(self):
        """Different industries produce different hourly rates which affect CRB output."""
        rate_dental, _ = get_effective_hourly_rate(industry="dental")
        rate_ecommerce, _ = get_effective_hourly_rate(industry="ecommerce")

        assert rate_dental != rate_ecommerce

        crb_dental = self.service.build_connect_path_crb(
            implementation_hours=10,
            monthly_costs=[],
            hourly_rate=rate_dental,
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=1000,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        crb_ecommerce = self.service.build_connect_path_crb(
            implementation_hours=10,
            monthly_costs=[],
            hourly_rate=rate_ecommerce,
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=1000,
            calculation_formula="f",
            confidence="MEDIUM",
        )

        # Dental rate (85) > ecommerce rate (35) -> dental has higher implementation cost
        assert crb_dental.cost.total_implementation_diy > crb_ecommerce.cost.total_implementation_diy
        # Higher cost -> lower ROI (same benefit)
        assert crb_dental.roi.expected < crb_ecommerce.roi.expected

    def test_connect_vs_replace_structural_differences(self):
        """Connect and Replace paths have correct structural differences."""
        connect = self.service.build_connect_path_crb(
            implementation_hours=10,
            monthly_costs=[{"item": "n8n", "cost": 20}],
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=1000,
            calculation_formula="f",
            confidence="MEDIUM",
        )
        replace = self.service.build_replace_path_crb(
            monthly_subscription=200,
            setup_cost=2000,
            migration_cost=500,
            primary_metric="m",
            baseline_value="b",
            target_value="t",
            monthly_value_eur=1000,
            calculation_formula="f",
            confidence="MEDIUM",
        )

        # Connect has DIY cost, Replace does not
        assert connect.cost.implementation_diy is not None
        assert replace.cost.implementation_diy is None

        # Replace has additional risks, Connect does not (by default)
        assert len(replace.risk.additional_risks) > len(connect.risk.additional_risks)

        # Replace has higher default hidden costs
        assert replace.cost.hidden.training_hours > connect.cost.hidden.training_hours
        assert replace.cost.hidden.productivity_dip_weeks > connect.cost.hidden.productivity_dip_weeks

    def test_full_pipeline_connect_path(self):
        """Full pipeline: hourly rate resolution -> connect CRB -> validation."""
        # Step 1: Resolve hourly rate from quiz data
        rate, source = get_effective_hourly_rate(
            industry="dental",
            quiz_answers={"annual_salary": 70000},
        )
        assert rate == pytest.approx(33.65, abs=0.01)  # 70000 / 2080

        # Step 2: Build CRB with that rate
        crb = self.service.build_connect_path_crb(
            implementation_hours=8,
            monthly_costs=[{"item": "API", "cost": 20}],
            hourly_rate=rate,
            implementation_complexity=2,
            complexity_reason="Standard integration",
            dependency_vendor="n8n",
            reversal_difficulty="Easy",
            primary_metric="response time",
            baseline_value="4 hours",
            target_value="15 minutes",
            monthly_value_eur=1500,
            calculation_formula="time saved * rate",
            confidence="MEDIUM",
            confidence_reason="User data + benchmark",
        )

        # Step 3: Validate
        issues = self.service.validate_crb_analysis(crb)
        assert issues == []

        # Step 4: Verify outputs make sense
        assert crb.cost.total_implementation_diy == pytest.approx(8 * 33.65, abs=0.1)
        assert crb.roi is not None
        assert crb.roi.expected > 0  # Should be profitable
        assert crb.recommendation_summary != ""

    def test_full_pipeline_replace_path(self):
        """Full pipeline: replace CRB -> validation -> comparison."""
        connect = self.service.build_connect_path_crb(
            implementation_hours=8,
            monthly_costs=[{"item": "API", "cost": 30}],
            implementation_complexity=2,
            primary_metric="efficiency",
            baseline_value="manual",
            target_value="automated",
            monthly_value_eur=1000,
            calculation_formula="hours * rate",
            confidence="HIGH",
        )

        replace = self.service.build_replace_path_crb(
            monthly_subscription=200,
            setup_cost=3000,
            migration_cost=500,
            implementation_complexity=4,
            complexity_reason="Data migration required",
            vendor_name="NewVendor",
            reversal_difficulty="Medium",
            primary_metric="efficiency",
            baseline_value="manual",
            target_value="automated",
            monthly_value_eur=1200,
            calculation_formula="hours * rate",
            confidence="MEDIUM",
        )

        # Both should validate cleanly
        assert self.service.validate_crb_analysis(connect) == []
        assert self.service.validate_crb_analysis(replace) == []

        # Compare should produce a result
        comparison = self.service.compare_paths(connect, replace)
        assert comparison["winner"] in ("CONNECT", "REPLACE", "EITHER")
        assert comparison["connect"] is not None
        assert comparison["replace"] is not None
        assert comparison["reasoning"] != ""


# ---------------------------------------------------------------------------
# Constants sanity checks
# ---------------------------------------------------------------------------


class TestConstants:
    """Sanity checks for module-level constants."""

    def test_default_hourly_rate(self):
        assert DEFAULT_HOURLY_RATE_EUR == 50

    def test_annual_working_hours(self):
        assert ANNUAL_WORKING_HOURS == 2080

    def test_professional_cost_multiplier(self):
        assert PROFESSIONAL_COST_MULTIPLIER == 2.5

    def test_max_credible_roi(self):
        assert MAX_CREDIBLE_ROI_PERCENT == 500

    def test_min_credible_payback(self):
        assert MIN_CREDIBLE_PAYBACK_MONTHS == 3
