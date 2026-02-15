"""
Tests for Quality Validator Service

Tests content quality checks that run post-generation:
- Banned buzzword detection
- Confidence distribution enforcement
- User data quoting validation
- Source citation checks
- ROI stuck-at-zero detection
- Vendor existence verification
"""

import pytest
from src.services.quality_validator import (
    QualityValidator,
    QualityIssue,
    QualityResult,
    Severity,
)


# =============================================================================
# Test Data Fixtures
# =============================================================================


def _make_finding(
    title="Test Finding",
    description="Based on your answer: 'We spend 20 hours/week on invoicing'. This represents a significant opportunity.",
    confidence="medium",
    sources=None,
    is_not_recommended=False,
    value_saved=None,
):
    return {
        "id": "finding-001",
        "title": title,
        "description": description,
        "confidence": confidence,
        "sources": ["Quiz Q3: '20 hours/week on invoicing'"] if sources is None else sources,
        "is_not_recommended": is_not_recommended,
        "customer_value_score": 7,
        "business_health_score": 6,
        "value_saved": value_saved or {"annual_savings": 15000},
    }


def _make_recommendation(
    title="Automate Invoice Processing",
    roi_percentage=180,
    payback_months=4,
    roi_pending_calculation=False,
    options=None,
):
    return {
        "id": "rec-001",
        "title": title,
        "roi_percentage": roi_percentage,
        "payback_months": payback_months,
        "roi_pending_calculation": roi_pending_calculation,
        "recommendation_rationale": "Based on your 20 hours/week spent on invoicing, automating this process saves €15K/year.",
        "options": options or {
            "off_the_shelf": {
                "vendor_slug": "zapier",
                "vendor_name": "Zapier",
                "price": "€19.99/mo",
            },
            "best_in_class": {
                "vendor_slug": "make",
                "vendor_name": "Make",
                "price": "€9/mo",
            },
            "custom_solution": {
                "description": "Build custom automation",
            },
        },
    }


def _make_report(findings=None, recommendations=None, exec_summary=None):
    return {
        "findings": findings or [],
        "recommendations": recommendations or [],
        "executive_summary": exec_summary or {
            "key_insight": "Your practice spends 20+ hours weekly on manual tasks.",
            "ai_readiness_score": 62,
        },
    }


# =============================================================================
# 1. Buzzword Detection
# =============================================================================


class TestBuzzwordDetection:
    """Banned phrases must be detected in any text field."""

    def test_clean_text_passes(self):
        finding = _make_finding(
            description="Reduce invoice processing from 4 hours to 30 minutes, saving €2,400/month."
        )
        report = _make_report(findings=[finding])
        result = QualityValidator.check_buzzwords(report)
        assert len(result) == 0

    def test_detects_streamline(self):
        finding = _make_finding(
            description="Streamline your operations with AI-powered tools."
        )
        report = _make_report(findings=[finding])
        result = QualityValidator.check_buzzwords(report)
        assert len(result) >= 1
        assert any("streamline" in issue.detail.lower() for issue in result)

    def test_detects_leverage(self):
        finding = _make_finding(
            description="Leverage AI capabilities to enhance efficiency."
        )
        report = _make_report(findings=[finding])
        result = QualityValidator.check_buzzwords(report)
        assert len(result) >= 1
        assert any("leverage" in issue.detail.lower() for issue in result)

    def test_detects_in_exec_summary(self):
        report = _make_report(
            findings=[_make_finding()],
            exec_summary={
                "key_insight": "Transform your business with seamless integration.",
                "ai_readiness_score": 62,
            },
        )
        result = QualityValidator.check_buzzwords(report)
        assert len(result) >= 1

    def test_detects_in_recommendation_rationale(self):
        rec = _make_recommendation(title="Unlock potential with automation")
        report = _make_report(recommendations=[rec])
        result = QualityValidator.check_buzzwords(report)
        assert len(result) >= 1

    def test_case_insensitive(self):
        finding = _make_finding(
            description="STREAMLINE your OPERATIONS for maximum impact."
        )
        report = _make_report(findings=[finding])
        result = QualityValidator.check_buzzwords(report)
        assert len(result) >= 1

    def test_all_severity_is_warning(self):
        finding = _make_finding(description="Leverage AI to streamline operations.")
        report = _make_report(findings=[finding])
        result = QualityValidator.check_buzzwords(report)
        for issue in result:
            assert issue.severity == Severity.WARNING


# =============================================================================
# 2. Confidence Distribution
# =============================================================================


class TestConfidenceDistribution:
    """Confidence levels must follow ~30% HIGH / ~50% MEDIUM / ~20% LOW."""

    def test_good_distribution_passes(self):
        """3 HIGH, 5 MEDIUM, 2 LOW = 30/50/20 - perfect."""
        findings = (
            [_make_finding(confidence="high") for _ in range(3)]
            + [_make_finding(confidence="medium") for _ in range(5)]
            + [_make_finding(confidence="low") for _ in range(2)]
        )
        report = _make_report(findings=findings)
        result = QualityValidator.check_confidence_distribution(report)
        assert len(result) == 0

    def test_all_high_fails(self):
        """All HIGH confidence is dishonest."""
        findings = [_make_finding(confidence="high") for _ in range(10)]
        report = _make_report(findings=findings)
        result = QualityValidator.check_confidence_distribution(report)
        assert len(result) >= 1
        assert any("high" in issue.detail.lower() for issue in result)

    def test_no_low_flags_warning(self):
        """Missing LOW confidence findings is suspicious."""
        findings = (
            [_make_finding(confidence="high") for _ in range(3)]
            + [_make_finding(confidence="medium") for _ in range(7)]
        )
        report = _make_report(findings=findings)
        result = QualityValidator.check_confidence_distribution(report)
        assert len(result) >= 1

    def test_too_few_findings_skips_check(self):
        """< 5 findings - too few to enforce distribution."""
        findings = [_make_finding(confidence="high") for _ in range(3)]
        report = _make_report(findings=findings)
        result = QualityValidator.check_confidence_distribution(report)
        assert len(result) == 0


# =============================================================================
# 3. User Data Quoting
# =============================================================================


class TestUserDataQuoting:
    """Findings must reference user's quiz answers."""

    def test_finding_with_quote_passes(self):
        finding = _make_finding(
            description="Based on your answer: 'We spend 20 hours on invoicing'. This is well above the industry average."
        )
        report = _make_report(findings=[finding])
        result = QualityValidator.check_user_data_quoting(report)
        assert len(result) == 0

    def test_finding_with_quiz_reference_passes(self):
        finding = _make_finding(
            description="You mentioned spending 20 hours/week on repetitive tasks (Quiz Q3)."
        )
        report = _make_report(findings=[finding])
        result = QualityValidator.check_user_data_quoting(report)
        assert len(result) == 0

    def test_generic_finding_flagged(self):
        finding = _make_finding(
            description="Support teams often face repetitive work that could be automated with modern tools."
        )
        report = _make_report(findings=[finding])
        result = QualityValidator.check_user_data_quoting(report)
        assert len(result) >= 1
        assert result[0].severity == Severity.WARNING

    def test_not_recommended_findings_skipped(self):
        """Not-recommended findings don't need user quotes."""
        finding = _make_finding(
            description="Generic industry observation about chatbots.",
            is_not_recommended=True,
        )
        report = _make_report(findings=[finding])
        result = QualityValidator.check_user_data_quoting(report)
        assert len(result) == 0


# =============================================================================
# 4. ROI Stuck at Zero
# =============================================================================


class TestROIValidation:
    """ROI values must not be silently stuck at 0."""

    def test_normal_roi_passes(self):
        rec = _make_recommendation(roi_percentage=180, payback_months=4)
        report = _make_report(recommendations=[rec])
        result = QualityValidator.check_roi_values(report)
        assert len(result) == 0

    def test_zero_roi_with_pending_flag_errors(self):
        rec = _make_recommendation(
            roi_percentage=0, payback_months=0, roi_pending_calculation=True
        )
        report = _make_report(recommendations=[rec])
        result = QualityValidator.check_roi_values(report)
        assert len(result) >= 1
        assert result[0].severity == Severity.ERROR

    def test_zero_roi_without_pending_flag_warns(self):
        """0% ROI without pending flag could be legitimate negative ROI."""
        rec = _make_recommendation(
            roi_percentage=0, payback_months=0, roi_pending_calculation=False
        )
        report = _make_report(recommendations=[rec])
        result = QualityValidator.check_roi_values(report)
        assert len(result) >= 1
        assert result[0].severity == Severity.WARNING

    def test_negative_roi_is_allowed(self):
        """Negative ROI is legitimate (not-recommended items)."""
        rec = _make_recommendation(roi_percentage=-25, payback_months=0)
        report = _make_report(recommendations=[rec])
        result = QualityValidator.check_roi_values(report)
        assert len(result) == 0

    def test_roi_calculation_failed_warns(self):
        """roi_calculation_failed=True is a WARNING (we tried, it failed)."""
        rec = _make_recommendation(
            roi_percentage=0, payback_months=0, roi_pending_calculation=False
        )
        rec["roi_calculation_failed"] = True
        report = _make_report(recommendations=[rec])
        result = QualityValidator.check_roi_values(report)
        assert len(result) >= 1
        assert result[0].severity == Severity.WARNING
        assert result[0].check == "roi_calculation_failed"

    def test_successful_recalculation_clears_pending(self):
        """After successful ROI calculation, no errors should appear."""
        rec = _make_recommendation(
            roi_percentage=150, payback_months=6, roi_pending_calculation=False
        )
        report = _make_report(recommendations=[rec])
        result = QualityValidator.check_roi_values(report)
        assert len(result) == 0


# =============================================================================
# 5. Vendor Existence
# =============================================================================


class TestVendorExistence:
    """Vendor slugs in recommendations must exist in KB."""

    def test_known_vendor_passes(self):
        rec = _make_recommendation(options={
            "off_the_shelf": {"vendor_slug": "zapier", "vendor_name": "Zapier"},
            "best_in_class": {"vendor_slug": "make", "vendor_name": "Make"},
            "custom_solution": {"description": "Custom build"},
        })
        report = _make_report(recommendations=[rec])
        result = QualityValidator.check_vendor_existence(report)
        assert len(result) == 0

    def test_unknown_vendor_flagged(self):
        rec = _make_recommendation(options={
            "off_the_shelf": {"vendor_slug": "totally-fake-vendor", "vendor_name": "FakeVendor"},
            "best_in_class": {"vendor_slug": "make", "vendor_name": "Make"},
            "custom_solution": {"description": "Custom build"},
        })
        report = _make_report(recommendations=[rec])
        result = QualityValidator.check_vendor_existence(report)
        assert len(result) >= 1
        assert "totally-fake-vendor" in result[0].detail

    def test_custom_solution_skips_vendor_check(self):
        """Custom solutions don't need vendor slugs."""
        rec = _make_recommendation(options={
            "off_the_shelf": {"vendor_slug": "zapier", "vendor_name": "Zapier"},
            "best_in_class": {"vendor_slug": "make", "vendor_name": "Make"},
            "custom_solution": {"description": "Custom build", "vendor_slug": None},
        })
        report = _make_report(recommendations=[rec])
        result = QualityValidator.check_vendor_existence(report)
        assert len(result) == 0

    def test_missing_vendor_slug_skipped(self):
        """Options without vendor_slug are fine (e.g., custom solutions)."""
        rec = _make_recommendation(options={
            "off_the_shelf": {"description": "Generic SaaS"},
            "best_in_class": {"vendor_slug": "make", "vendor_name": "Make"},
            "custom_solution": {"description": "Custom build"},
        })
        report = _make_report(recommendations=[rec])
        result = QualityValidator.check_vendor_existence(report)
        assert len(result) == 0


# =============================================================================
# 6. Source Citations
# =============================================================================


class TestSourceCitations:
    """Recommended findings must have source citations."""

    def test_finding_with_sources_passes(self):
        finding = _make_finding(sources=["Quiz Q3: '20 hours/week'"])
        report = _make_report(findings=[finding])
        result = QualityValidator.check_source_citations(report)
        assert len(result) == 0

    def test_finding_without_sources_flagged(self):
        finding = _make_finding(sources=[])
        report = _make_report(findings=[finding])
        result = QualityValidator.check_source_citations(report)
        assert len(result) >= 1

    def test_not_recommended_without_sources_ok(self):
        finding = _make_finding(sources=[], is_not_recommended=True)
        report = _make_report(findings=[finding])
        result = QualityValidator.check_source_citations(report)
        assert len(result) == 0


# =============================================================================
# 7. Full Validation (Integration)
# =============================================================================


class TestFullValidation:
    """End-to-end quality validation."""

    def test_clean_report_passes(self):
        findings = (
            [_make_finding(confidence="high") for _ in range(3)]
            + [_make_finding(confidence="medium") for _ in range(5)]
            + [_make_finding(confidence="low") for _ in range(2)]
        )
        recs = [_make_recommendation()]
        report = _make_report(findings=findings, recommendations=recs)
        result = QualityValidator.validate(report)
        assert result.passed
        assert result.error_count == 0

    def test_dirty_report_catches_multiple_issues(self):
        findings = [
            _make_finding(
                description="Streamline operations to leverage AI for maximum impact.",
                confidence="high",
                sources=[],
            )
            for _ in range(10)
        ]
        recs = [
            _make_recommendation(roi_percentage=0, roi_pending_calculation=True)
        ]
        report = _make_report(findings=findings, recommendations=recs)
        result = QualityValidator.validate(report)
        assert result.error_count > 0 or result.warning_count > 0
        # Should catch: buzzwords, all-high confidence, missing sources, ROI=0
        assert result.warning_count >= 3

    def test_result_has_summary(self):
        report = _make_report(
            findings=[_make_finding()],
            recommendations=[_make_recommendation()],
        )
        result = QualityValidator.validate(report)
        assert isinstance(result.issues, list)
        assert isinstance(result.error_count, int)
        assert isinstance(result.warning_count, int)
