"""
E2E Smoke Tests for All 4 Verticals

Tests the critical path for each primary industry:
- professional-services (EUR 125/hr)
- dental (EUR 85/hr)
- ecommerce (EUR 35/hr)
- b2b-platforms (EUR 75/hr)

Covers:
1. Knowledge base completeness (all 4 files per industry)
2. Industry questions loading
3. Hourly rate defaults
4. NET SCORE calculation
5. Sample report serving
6. Industry normalization (variant slugs)
7. Vendor data integrity
"""

import json
import pytest
from pathlib import Path

from src.knowledge import (
    load_industry_data,
    normalize_industry,
    get_industry_context,
    get_relevant_opportunities,
    get_vendor_recommendations,
    PRIMARY_INDUSTRIES,
    list_primary_industries,
)
from src.services.crb_calculation_service import (
    get_effective_hourly_rate,
    INDUSTRY_HOURLY_RATES_EUR,
)
from src.skills.analysis.net_score_calculator import (
    NetScoreCalculatorSkill,
    OptionInput,
    OptionNetScore,
)
from src.skills.base import (
    SkillContext,
    currency_for_country,
    COUNTRY_CURRENCY_MAP,
    LOCATION_OPTIONS,
    CURRENCY_SYMBOLS,
)


# =============================================================================
# Constants
# =============================================================================

VERTICALS = ["professional-services", "dental", "ecommerce", "b2b-platforms"]
DATA_TYPES = ["processes", "opportunities", "benchmarks", "vendors"]

EXPECTED_HOURLY_RATES = {
    "professional-services": 125.0,
    "dental": 85.0,
    "ecommerce": 35.0,
    "b2b-platforms": 75.0,
}

KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "src" / "knowledge"
INDUSTRY_QUESTIONS_PATH = KNOWLEDGE_BASE_PATH / "industry_questions"


# =============================================================================
# 1. Knowledge Base Completeness
# =============================================================================

class TestKnowledgeBaseCompleteness:
    """Verify all 3 verticals have complete knowledge base files."""

    @pytest.mark.parametrize("industry", VERTICALS)
    @pytest.mark.parametrize("data_type", DATA_TYPES)
    def test_knowledge_file_exists_and_loads(self, industry, data_type):
        """Each vertical must have all 4 KB data types."""
        data = load_industry_data(industry, data_type)
        assert data is not None, f"Missing {data_type} for {industry}"
        assert isinstance(data, dict), f"{data_type} for {industry} is not a dict"

    @pytest.mark.parametrize("industry", VERTICALS)
    def test_processes_have_content(self, industry):
        """Processes file must have common_processes with at least 3 entries."""
        data = load_industry_data(industry, "processes")
        processes = data.get("common_processes", [])
        assert len(processes) >= 3, (
            f"{industry} has only {len(processes)} processes, need at least 3"
        )

    @pytest.mark.parametrize("industry", VERTICALS)
    def test_opportunities_have_content(self, industry):
        """Opportunities file must have at least 5 AI opportunities."""
        data = load_industry_data(industry, "opportunities")
        opportunities = data.get("ai_opportunities", [])
        assert len(opportunities) >= 5, (
            f"{industry} has only {len(opportunities)} opportunities, need at least 5"
        )

    @pytest.mark.parametrize("industry", VERTICALS)
    def test_benchmarks_have_content(self, industry):
        """Benchmarks file must have meaningful data."""
        data = load_industry_data(industry, "benchmarks")
        # Different verticals may structure benchmarks differently:
        # dental/ecommerce use "benchmarks" sub-key, professional-services uses top-level keys
        benchmarks = data.get("benchmarks", {})
        has_benchmarks_key = len(benchmarks) >= 1
        has_top_level_data = len(data) >= 3  # industry, last_updated, + actual data
        assert has_benchmarks_key or has_top_level_data, (
            f"{industry} benchmarks has no meaningful data"
        )

    @pytest.mark.parametrize("industry", VERTICALS)
    def test_vendors_have_content(self, industry):
        """Vendors file must have vendor categories with vendors."""
        data = load_industry_data(industry, "vendors")
        # Two formats: "vendor_categories" (list) or "categories" (dict)
        categories_list = data.get("vendor_categories", [])
        categories_dict = data.get("categories", {})
        has_list = len(categories_list) >= 2
        has_dict = len(categories_dict) >= 2
        assert has_list or has_dict, (
            f"{industry} has insufficient vendor categories"
        )

    @pytest.mark.parametrize("industry", VERTICALS)
    def test_vendor_structure(self, industry):
        """Each vendor should have name, slug, and pricing fields."""
        data = load_industry_data(industry, "vendors")
        categories = data.get("vendor_categories", [])
        for cat in categories:
            for vendor in cat.get("vendors", []):
                assert "name" in vendor, f"Vendor missing 'name' in {industry}"
                assert "pricing" in vendor or "description" in vendor, (
                    f"Vendor '{vendor.get('name', '?')}' in {industry} missing pricing or description"
                )


# =============================================================================
# 2. Industry Questions
# =============================================================================

class TestIndustryQuestions:
    """Verify industry-specific quiz questions exist and are well-formed."""

    @pytest.mark.parametrize("industry,filename", [
        ("ecommerce", "ecommerce.json"),
        ("dental", "dental.json"),
        ("professional-services", "professional_services.json"),
        ("b2b-platforms", "b2b_platforms.json"),
    ])
    def test_question_file_exists(self, industry, filename):
        """Each vertical must have an industry question file."""
        filepath = INDUSTRY_QUESTIONS_PATH / filename
        assert filepath.exists(), f"Missing question file: {filepath}"

    @pytest.mark.parametrize("industry,filename", [
        ("ecommerce", "ecommerce.json"),
        ("dental", "dental.json"),
        ("professional-services", "professional_services.json"),
        ("b2b-platforms", "b2b_platforms.json"),
    ])
    def test_questions_valid_json(self, industry, filename):
        """Question files must be valid JSON with questions array."""
        filepath = INDUSTRY_QUESTIONS_PATH / filename
        with open(filepath) as f:
            data = json.load(f)
        questions = data.get("questions", [])
        assert len(questions) >= 5, (
            f"{industry} has only {len(questions)} questions, need at least 5"
        )

    @pytest.mark.parametrize("industry,filename", [
        ("ecommerce", "ecommerce.json"),
        ("dental", "dental.json"),
        ("professional-services", "professional_services.json"),
        ("b2b-platforms", "b2b_platforms.json"),
    ])
    def test_question_structure(self, industry, filename):
        """Each question must have required fields."""
        filepath = INDUSTRY_QUESTIONS_PATH / filename
        with open(filepath) as f:
            data = json.load(f)

        for q in data.get("questions", []):
            assert "id" in q, f"Question missing 'id' in {industry}"
            assert "question" in q, f"Question missing 'question' in {industry}: {q.get('id')}"
            assert "input_type" in q, f"Question missing 'input_type' in {industry}: {q.get('id')}"
            assert q["input_type"] in ("select", "multi_select", "number", "voice", "text", "slider"), (
                f"Invalid input_type '{q['input_type']}' in {industry}: {q.get('id')}"
            )


# =============================================================================
# 3. Hourly Rate Defaults
# =============================================================================

class TestHourlyRates:
    """Verify correct hourly rates for each vertical."""

    @pytest.mark.parametrize("industry,expected_rate", [
        ("professional-services", 125.0),
        ("dental", 85.0),
        ("ecommerce", 35.0),
        ("b2b-platforms", 75.0),
    ])
    def test_industry_default_rate(self, industry, expected_rate):
        """Each industry should return correct default hourly rate."""
        rate, source = get_effective_hourly_rate(industry, None)
        assert rate == expected_rate, (
            f"{industry} rate is {rate}, expected {expected_rate}"
        )
        assert "industry default" in source

    @pytest.mark.parametrize("industry,expected_rate", [
        ("professional_services", 125.0),
        ("e-commerce", 35.0),
        ("b2b_platforms", 75.0),
    ])
    def test_alternate_slug_rates(self, industry, expected_rate):
        """Alternate slug formats should return same hourly rate."""
        rate, _ = get_effective_hourly_rate(industry, None)
        assert rate == expected_rate

    def test_explicit_hourly_rate_overrides(self):
        """User-provided hourly rate should override industry default."""
        rate, source = get_effective_hourly_rate("dental", {"hourly_rate": 95})
        assert rate == 95.0
        assert "provided by user" in source

    def test_salary_conversion(self):
        """Salary should convert to hourly rate via /2080."""
        rate, source = get_effective_hourly_rate("dental", {"annual_salary": 176800})
        assert rate == 85.0  # 176800 / 2080 = 85
        assert "derived from annual salary" in source

    def test_salary_takes_precedence_over_industry(self):
        """Salary should override industry default but not explicit hourly rate."""
        rate, source = get_effective_hourly_rate("ecommerce", {"salary": 72800})
        assert rate == 35.0  # 72800 / 2080 = 35
        assert "derived from annual salary" in source

    def test_unknown_industry_falls_back(self):
        """Unknown industry should fall back to global default of 50."""
        rate, source = get_effective_hourly_rate("unknown_industry", None)
        assert rate == 50.0
        assert "default" in source.lower()


# =============================================================================
# 4. NET SCORE Calculation
# =============================================================================

class TestNetScoreCalculation:
    """Verify NET SCORE formula works correctly for option comparison."""

    def _make_context(self, options: list) -> SkillContext:
        return SkillContext(
            industry="test",
            metadata={"options": [o.model_dump() for o in options]},
        )

    def test_basic_formula(self):
        """NET SCORE = Benefit - Cost - (Risk / 10)."""
        skill = NetScoreCalculatorSkill()
        option = OptionInput(
            option_type="off_the_shelf",
            implementation_cost=500,
            monthly_cost=100,
            implementation_weeks=2,
            monthly_savings=2000,
            hours_saved_per_week=10,
            implementation_complexity=2,
            vendor_dependency="low",
            reversal_difficulty="Easy",
        )
        context = self._make_context([option])
        result = skill.execute_sync(context)

        assert len(result.options) == 1
        scored = result.options[0]

        # Verify formula
        expected_net = scored.benefit_score - scored.cost_score - (scored.risk_score / 10)
        assert abs(scored.net_score - expected_net) < 0.15, (
            f"NET SCORE {scored.net_score} != formula result {expected_net}"
        )

    def test_three_options_ranking(self):
        """Three options should be ranked by NET SCORE descending."""
        skill = NetScoreCalculatorSkill()
        options = [
            OptionInput(
                option_type="off_the_shelf",
                implementation_cost=500,
                monthly_cost=100,
                implementation_weeks=2,
                monthly_savings=1500,
                hours_saved_per_week=10,
                implementation_complexity=2,
                vendor_dependency="medium",
                reversal_difficulty="Easy",
            ),
            OptionInput(
                option_type="best_in_class",
                implementation_cost=3000,
                monthly_cost=300,
                implementation_weeks=4,
                monthly_savings=2000,
                hours_saved_per_week=15,
                implementation_complexity=3,
                vendor_dependency="high",
                reversal_difficulty="Medium",
            ),
            OptionInput(
                option_type="custom_solution",
                implementation_cost=20000,
                monthly_cost=50,
                implementation_weeks=16,
                monthly_savings=2500,
                hours_saved_per_week=20,
                implementation_complexity=5,
                vendor_dependency="low",
                reversal_difficulty="Hard",
            ),
        ]
        context = self._make_context(options)
        result = skill.execute_sync(context)

        # Should be sorted descending by net_score
        scores = [o.net_score for o in result.options]
        assert scores == sorted(scores, reverse=True), (
            f"Options not sorted by NET SCORE: {scores}"
        )

        # Recommended should be highest
        assert result.recommended_option == result.options[0].option_type

        # Score gap should be positive (or zero if tied)
        assert result.score_gap >= 0

    def test_verdict_thresholds(self):
        """Verify verdict labels match NET SCORE thresholds."""
        skill = NetScoreCalculatorSkill()

        # Create options that produce different NET SCOREs by varying cost/benefit
        test_cases = [
            # High benefit, low cost → strong_yes (>70)
            OptionInput(
                option_type="off_the_shelf",
                implementation_cost=200,
                monthly_cost=50,
                implementation_weeks=1,
                monthly_savings=5000,
                hours_saved_per_week=20,
                implementation_complexity=1,
                vendor_dependency="low",
                reversal_difficulty="Easy",
            ),
            # Very high cost, moderate benefit → not_recommended (<10)
            OptionInput(
                option_type="custom_solution",
                implementation_cost=20000,
                monthly_cost=500,
                implementation_weeks=10,
                monthly_savings=100,
                hours_saved_per_week=1,
                implementation_complexity=5,
                vendor_dependency="high",
                reversal_difficulty="Hard",
            ),
        ]

        for option in test_cases:
            context = self._make_context([option])
            result = skill.execute_sync(context)
            scored = result.options[0]

            if scored.net_score > 70:
                assert scored.verdict == "strong_yes", (
                    f"Score {scored.net_score} should be strong_yes, got {scored.verdict}"
                )
            elif scored.net_score >= 40:
                assert scored.verdict == "recommended"
            elif scored.net_score >= 10:
                assert scored.verdict == "conditional"
            else:
                assert scored.verdict == "not_recommended", (
                    f"Score {scored.net_score} should be not_recommended, got {scored.verdict}"
                )

    def test_formula_display_string(self):
        """Formula display should show the calculation."""
        skill = NetScoreCalculatorSkill()
        option = OptionInput(
            option_type="off_the_shelf",
            implementation_cost=1000,
            monthly_cost=100,
            implementation_weeks=2,
            monthly_savings=1000,
            hours_saved_per_week=5,
        )
        context = self._make_context([option])
        result = skill.execute_sync(context)
        scored = result.options[0]

        # Should contain the equals sign and the NET SCORE value
        assert "=" in scored.formula_display
        assert str(round(scored.net_score, 1)) in scored.formula_display


# =============================================================================
# 5. Sample Report Serving
# =============================================================================

class TestSampleReports:
    """Verify sample report files exist and are valid for all verticals."""

    SAMPLE_DATA_DIR = Path(__file__).parent.parent / "src" / "data"

    EXPECTED_FILES = {
        "professional-services": "sample_report.json",
        "dental": "sample_report_dental.json",
        "ecommerce": "sample_report_ecommerce.json",
        "b2b-platforms": "sample_report_b2b_platforms.json",
    }

    @pytest.mark.parametrize("industry", VERTICALS)
    def test_sample_file_exists(self, industry):
        """Each vertical must have a sample report JSON file."""
        filename = self.EXPECTED_FILES[industry]
        filepath = self.SAMPLE_DATA_DIR / filename
        assert filepath.exists(), f"Missing sample report: {filepath}"

    @pytest.mark.parametrize("industry", VERTICALS)
    def test_sample_valid_json(self, industry):
        """Sample report files must be valid JSON."""
        filename = self.EXPECTED_FILES[industry]
        filepath = self.SAMPLE_DATA_DIR / filename
        with open(filepath) as f:
            data = json.load(f)
        assert isinstance(data, dict), f"Sample report for {industry} is not a dict"

    @pytest.mark.parametrize("industry", VERTICALS)
    def test_sample_has_required_sections(self, industry):
        """Sample reports must have the key sections for ReportViewer."""
        filename = self.EXPECTED_FILES[industry]
        filepath = self.SAMPLE_DATA_DIR / filename
        with open(filepath) as f:
            data = json.load(f)

        required_keys = [
            "executive_summary",
            "findings",
            "recommendations",
        ]
        for key in required_keys:
            assert key in data, f"Sample report for {industry} missing '{key}'"

    @pytest.mark.parametrize("industry", VERTICALS)
    def test_sample_has_findings(self, industry):
        """Sample reports must have at least 3 findings."""
        filename = self.EXPECTED_FILES[industry]
        filepath = self.SAMPLE_DATA_DIR / filename
        with open(filepath) as f:
            data = json.load(f)

        findings = data.get("findings", [])
        assert len(findings) >= 3, (
            f"Sample report for {industry} has only {len(findings)} findings"
        )

    @pytest.mark.parametrize("industry", VERTICALS)
    def test_sample_has_recommendations(self, industry):
        """Sample reports must have at least 2 recommendations."""
        filename = self.EXPECTED_FILES[industry]
        filepath = self.SAMPLE_DATA_DIR / filename
        with open(filepath) as f:
            data = json.load(f)

        recommendations = data.get("recommendations", [])
        assert len(recommendations) >= 2, (
            f"Sample report for {industry} has only {len(recommendations)} recommendations"
        )


# =============================================================================
# 6. Industry Normalization
# =============================================================================

class TestIndustryNormalization:
    """Verify industry slug normalization works for common variants."""

    @pytest.mark.parametrize("input_slug,expected", [
        # Professional Services variants
        ("professional-services", "professional-services"),
        ("professional_services", "professional-services"),
        ("professional services", "professional-services"),
        ("legal", "professional-services"),
        ("accounting", "professional-services"),
        ("consulting", "professional-services"),
        # Dental variants
        ("dental", "dental"),
        ("dentist", "dental"),
        ("dental practice", "dental"),
        ("dso", "dental"),
        # E-commerce variants
        ("ecommerce", "ecommerce"),
        ("e-commerce", "ecommerce"),
        ("dtc", "ecommerce"),
        ("shopify", "ecommerce"),
        ("online_retail", "ecommerce"),
        # B2B Platforms variants
        ("b2b-platforms", "b2b-platforms"),
        ("b2b_platforms", "b2b-platforms"),
        ("iot", "b2b-platforms"),
        ("connected-devices", "b2b-platforms"),
    ])
    def test_normalization(self, input_slug, expected):
        """Various industry name inputs should normalize correctly."""
        assert normalize_industry(input_slug) == expected

    def test_unknown_industry_returns_general(self):
        """Unknown industries should normalize to 'general'."""
        result = normalize_industry("underwater_basket_weaving")
        assert result == "general"

    def test_primary_industries_list(self):
        """Primary industries should be exactly our 4 verticals."""
        primaries = list_primary_industries()
        assert set(primaries) == set(VERTICALS)


# =============================================================================
# 7. Industry Context Loading
# =============================================================================

class TestIndustryContext:
    """Verify get_industry_context returns complete data for each vertical."""

    @pytest.mark.parametrize("industry", VERTICALS)
    def test_context_is_supported(self, industry):
        """Each vertical should be marked as supported."""
        context = get_industry_context(industry)
        assert context["is_supported"] is True

    @pytest.mark.parametrize("industry", VERTICALS)
    def test_context_has_all_data(self, industry):
        """Each vertical should have all 4 data types loaded."""
        context = get_industry_context(industry)
        assert context["processes"] is not None, f"{industry} missing processes"
        assert context["opportunities"] is not None, f"{industry} missing opportunities"
        assert context["benchmarks"] is not None, f"{industry} missing benchmarks"
        assert context["vendors"] is not None, f"{industry} missing vendors"

    @pytest.mark.parametrize("industry", VERTICALS)
    def test_context_has_counts(self, industry):
        """Context should include process and opportunity counts."""
        context = get_industry_context(industry)
        assert context.get("process_count", 0) >= 3
        assert context.get("opportunity_count", 0) >= 5


# =============================================================================
# 8. Currency Integration
# =============================================================================

class TestCurrencyIntegration:
    """Verify currency system works correctly for multi-vertical use."""

    def test_all_currencies_have_symbols(self):
        """Every currency code in the country map should have a symbol."""
        unique_currencies = set(COUNTRY_CURRENCY_MAP.values())
        for currency in unique_currencies:
            assert currency in CURRENCY_SYMBOLS, (
                f"Currency {currency} has no symbol in CURRENCY_SYMBOLS"
            )

    def test_location_options_cover_major_markets(self):
        """Location options should include key European and English-speaking markets."""
        values = {opt["value"] for opt in LOCATION_OPTIONS}
        assert "NL" in values, "Missing Netherlands"
        assert "DE" in values, "Missing Germany"
        assert "UK" in values or "GB" in values, "Missing UK"
        assert "US" in values, "Missing US"

    @pytest.mark.parametrize("country,expected_currency", [
        ("NL", "EUR"),
        ("DE", "EUR"),
        ("UK", "GBP"),
        ("GB", "GBP"),
        ("US", "USD"),
        ("AU", "AUD"),
        ("CH", "CHF"),
    ])
    def test_country_to_currency(self, country, expected_currency):
        """Country codes should map to correct currencies."""
        assert currency_for_country(country) == expected_currency

    def test_unknown_country_defaults_to_eur(self):
        """Unknown country should default to EUR."""
        assert currency_for_country("XX") == "EUR"


# =============================================================================
# 9. Vendor Recommendations per Industry
# =============================================================================

class TestVendorRecommendations:
    """Verify vendor recommendations load correctly for each vertical."""

    @pytest.mark.parametrize("industry", ["dental", "ecommerce"])
    def test_vendors_load(self, industry):
        """Dental and ecommerce should return vendor recommendations via vendor_categories."""
        vendors = get_vendor_recommendations(industry)
        assert len(vendors) >= 3, (
            f"{industry} has only {len(vendors)} vendors, need at least 3"
        )

    def test_professional_services_vendors_exist(self):
        """Professional-services uses 'categories' dict format (not vendor_categories list)."""
        data = load_industry_data("professional-services", "vendors")
        categories = data.get("categories", {})
        total_vendors = sum(
            len(cat.get("vendors", [])) if isinstance(cat, dict) else 0
            for cat in (categories.values() if isinstance(categories, dict) else [])
        )
        assert total_vendors >= 3, (
            f"professional-services has only {total_vendors} vendors"
        )

    @pytest.mark.parametrize("industry", ["dental", "ecommerce"])
    def test_vendors_have_names(self, industry):
        """All vendors should have a name."""
        vendors = get_vendor_recommendations(industry)
        for v in vendors:
            assert v.get("name"), f"Vendor without name in {industry}: {v}"


# =============================================================================
# 10. Opportunities per Industry
# =============================================================================

class TestOpportunities:
    """Verify AI opportunity data is meaningful for each vertical."""

    @pytest.mark.parametrize("industry", VERTICALS)
    def test_opportunities_load(self, industry):
        """Each vertical should return relevant opportunities."""
        opportunities = get_relevant_opportunities(industry)
        assert len(opportunities) >= 5, (
            f"{industry} has only {len(opportunities)} opportunities"
        )

    @pytest.mark.parametrize("industry", VERTICALS)
    def test_opportunities_have_required_fields(self, industry):
        """Each opportunity should have title and description."""
        opportunities = get_relevant_opportunities(industry)
        for opp in opportunities:
            assert "title" in opp or "name" in opp, (
                f"Opportunity in {industry} missing title/name: {opp.keys()}"
            )


# =============================================================================
# 11. Sample Report Endpoint (via function, no HTTP)
# =============================================================================

class TestSampleReportEndpoint:
    """Test the sample report loading function directly."""

    def test_default_sample_loads(self):
        """Default (no industry) should load professional-services sample."""
        from src.routes.reports import get_sample_report, _sample_reports
        _sample_reports.clear()  # Clear cache
        report = get_sample_report()
        assert report, "Default sample report failed to load"
        assert "findings" in report

    @pytest.mark.parametrize("industry", VERTICALS)
    def test_industry_sample_loads(self, industry):
        """Each industry sample should load successfully."""
        from src.routes.reports import get_sample_report, _sample_reports
        _sample_reports.clear()  # Clear cache
        report = get_sample_report(industry)
        assert report, f"Sample report for {industry} failed to load"
        assert "findings" in report

    def test_unknown_industry_falls_back(self):
        """Unknown industry should fall back to default sample."""
        from src.routes.reports import get_sample_report, _sample_reports
        _sample_reports.clear()  # Clear cache
        report = get_sample_report("unknown_industry")
        assert report, "Fallback sample report failed to load"
