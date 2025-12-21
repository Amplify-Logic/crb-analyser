"""
Unit tests for report_service.py

Tests cover:
- Model routing
- Token tracking
- Three Options validation
- Not-recommended requirements
- Source citations
- Error handling and retries
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

from src.config.model_routing import get_model_for_task, TokenTracker, MODELS
from src.config.ai_tools import (
    get_ai_recommendation,
    get_build_it_yourself_context,
    get_ai_tools_prompt_context,
    get_diy_resources,
)
from src.services.report_validator import ReportValidator, validate_report


class TestModelRouting:
    """Tests for model routing configuration."""

    def test_haiku_for_extraction_tasks(self):
        """Haiku should be used for simple extraction tasks."""
        extraction_tasks = [
            "parse_quiz_responses",
            "extract_industry",
            "validate_json",
            "classify_finding",
        ]
        for task in extraction_tasks:
            model = get_model_for_task(task, "quick")
            assert "haiku" in model.lower(), f"Task '{task}' should use Haiku, got {model}"

    def test_sonnet_for_generation_tasks(self):
        """Sonnet should be used for main generation tasks."""
        generation_tasks = [
            "generate_executive_summary",
            "generate_findings",
            "generate_recommendations",
            "generate_roadmap",
        ]
        for task in generation_tasks:
            model = get_model_for_task(task, "quick")
            assert "sonnet" in model.lower(), f"Task '{task}' should use Sonnet, got {model}"

    def test_opus_for_full_tier_complex_analysis(self):
        """Opus should only be used for full tier complex analysis."""
        model = get_model_for_task("complex_analysis", "full")
        assert "opus" in model.lower(), f"Full tier complex_analysis should use Opus, got {model}"

    def test_quick_tier_avoids_opus(self):
        """Quick tier should never use Opus."""
        model = get_model_for_task("complex_analysis", "quick")
        assert "opus" not in model.lower(), f"Quick tier should not use Opus, got {model}"

    def test_fallback_to_default(self):
        """Unknown tasks should fall back to default model."""
        model = get_model_for_task("unknown_task_xyz", "quick")
        assert model is not None, "Should return a fallback model"


class TestTokenTracker:
    """Tests for token usage tracking."""

    def test_tracks_usage(self):
        """Token tracker should correctly sum usage."""
        tracker = TokenTracker()
        tracker.add_usage("task1", MODELS["sonnet"], 1000, 500)
        tracker.add_usage("task2", MODELS["haiku"], 500, 200)

        summary = tracker.get_summary()
        assert summary["total_input_tokens"] == 1500
        assert summary["total_output_tokens"] == 700
        assert summary["total_tokens"] == 2200

    def test_cost_estimation(self):
        """Token tracker should estimate costs correctly."""
        tracker = TokenTracker()
        # Add 1M input tokens of Sonnet ($3) + 1M output tokens ($15) = $18
        tracker.add_usage("test", MODELS["sonnet"], 1_000_000, 1_000_000)

        summary = tracker.get_summary()
        assert summary["estimated_cost_usd"] == pytest.approx(18.0, rel=0.01)

    def test_by_model_breakdown(self):
        """Token tracker should break down by model."""
        tracker = TokenTracker()
        tracker.add_usage("task1", MODELS["sonnet"], 100, 50)
        tracker.add_usage("task2", MODELS["haiku"], 200, 100)
        tracker.add_usage("task3", MODELS["sonnet"], 150, 75)

        summary = tracker.get_summary()
        by_model = summary["by_model"]

        assert MODELS["sonnet"] in by_model
        assert by_model[MODELS["sonnet"]]["input"] == 250
        assert MODELS["haiku"] in by_model
        assert by_model[MODELS["haiku"]]["input"] == 200

    def test_to_dict_export(self):
        """Token tracker should export full data."""
        tracker = TokenTracker()
        tracker.add_usage("test", MODELS["sonnet"], 100, 50)

        data = tracker.to_dict()
        assert "usage" in data
        assert "summary" in data
        assert len(data["usage"]) == 1
        assert data["usage"][0]["task"] == "test"


class TestAITools:
    """Tests for AI tools configuration."""

    def test_get_ai_recommendation(self):
        """Should return AI recommendations for known use cases."""
        rec = get_ai_recommendation("chatbot")
        assert "model" in rec
        assert "Claude" in rec["model"] or "claude" in rec.get("model_id", "")

    def test_get_build_it_yourself_context(self):
        """Should return complete DIY context."""
        context = get_build_it_yourself_context("chatbot")

        assert "ai_model" in context
        assert "recommended_stack" in context
        assert "skills_required" in context
        assert "build_tools" in context
        assert "typical_timeline" in context

    def test_get_ai_tools_prompt_context(self):
        """Should return formatted prompt context string."""
        context = get_ai_tools_prompt_context()

        assert isinstance(context, str)
        assert len(context) > 100
        assert "Claude" in context or "Cursor" in context

    def test_diy_resources_loads(self):
        """DIY resources JSON should load correctly."""
        resources = get_diy_resources()

        # Check structure if loaded
        if resources:
            assert "ai_providers" in resources or "tutorials_by_use_case" in resources


class TestReportValidator:
    """Tests for report validation."""

    def test_valid_report_passes(self, mock_report_data):
        """Valid report should pass validation."""
        is_valid, issues = validate_report(mock_report_data)

        errors = [i for i in issues if i.get("severity") == "error"]
        assert is_valid or len(errors) == 0, f"Valid report should pass: {errors}"

    def test_missing_findings_fails(self, mock_report_data):
        """Report with too few findings should fail."""
        mock_report_data["findings"] = mock_report_data["findings"][:2]  # Only 2 findings

        is_valid, issues = validate_report(mock_report_data)

        errors = [i for i in issues if i.get("severity") == "error"]
        assert any("min_findings" in str(e) for e in errors)

    def test_missing_not_recommended_fails(self, mock_report_data):
        """Report without enough not-recommended items should fail."""
        # Remove all not-recommended findings
        mock_report_data["findings"] = [
            f for f in mock_report_data["findings"]
            if not f.get("is_not_recommended")
        ]

        is_valid, issues = validate_report(mock_report_data)

        errors = [i for i in issues if i.get("severity") == "error"]
        assert any("not_recommended" in str(e) for e in errors)

    def test_missing_three_options_fails(self, mock_report_data):
        """Recommendations missing options should fail."""
        # Remove an option
        del mock_report_data["recommendations"][0]["options"]["custom_solution"]

        is_valid, issues = validate_report(mock_report_data)

        errors = [i for i in issues if i.get("severity") == "error"]
        assert any("three_options" in str(e) or "custom_solution" in str(e) for e in errors)

    def test_invalid_scores_fail(self, mock_report_data):
        """Scores outside 1-10 range should fail."""
        mock_report_data["findings"][0]["customer_value_score"] = 15  # Invalid

        is_valid, issues = validate_report(mock_report_data)

        errors = [i for i in issues if i.get("severity") == "error"]
        assert any("score" in str(e).lower() for e in errors)

    def test_missing_sources_warning(self, mock_report_data):
        """Findings without sources should generate warning."""
        mock_report_data["findings"][0]["sources"] = []

        is_valid, issues = validate_report(mock_report_data)

        warnings = [i for i in issues if i.get("severity") == "warning"]
        assert any("source" in str(w).lower() for w in warnings)

    def test_validation_summary(self, mock_report_data):
        """Validation summary should include counts."""
        summary = ReportValidator.get_validation_summary(mock_report_data)

        assert "is_valid" in summary
        assert "error_count" in summary
        assert "warning_count" in summary
        assert "summary" in summary
        assert "findings_count" in summary["summary"]


class TestReportGeneratorIntegration:
    """Integration tests for ReportGenerator (with mocks)."""

    @pytest.mark.asyncio
    async def test_call_claude_with_retry_rate_limit(self):
        """Should retry on rate limit errors."""
        from src.services.report_service import ReportGenerator
        from anthropic import RateLimitError

        with patch.object(ReportGenerator, '__init__', lambda x, y, z: None):
            generator = ReportGenerator.__new__(ReportGenerator)
            generator.tier = "quick"
            generator.token_tracker = TokenTracker()
            generator.client = MagicMock()
            generator.MAX_RETRIES = 3
            generator.RETRY_DELAYS = [0.01, 0.02, 0.04]  # Fast for testing
            generator.SYSTEM_PROMPT = "test"

            # First two calls fail, third succeeds
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="success")]
            mock_response.usage = MagicMock(input_tokens=10, output_tokens=5)

            generator.client.messages.create = MagicMock(
                side_effect=[
                    RateLimitError("Rate limited", response=MagicMock(), body={}),
                    RateLimitError("Rate limited", response=MagicMock(), body={}),
                    mock_response
                ]
            )

            result = generator._call_claude("test_task", "test prompt")
            assert result == "success"
            assert generator.client.messages.create.call_count == 3

    def test_error_categorization(self):
        """Errors should be categorized correctly."""
        from src.services.report_service import ReportGenerator
        from anthropic import RateLimitError, APIConnectionError, APIError

        with patch.object(ReportGenerator, '__init__', lambda x, y, z: None):
            generator = ReportGenerator.__new__(ReportGenerator)

            # Rate limit error
            error = RateLimitError("test", response=MagicMock(), body={})
            result = generator._categorize_error(error)
            assert result["type"] == "rate_limit"
            assert result["retryable"] is True

            # Connection error
            error = APIConnectionError(request=MagicMock())
            result = generator._categorize_error(error)
            assert result["type"] == "connection"
            assert result["retryable"] is True

            # Generic error
            error = ValueError("Unknown error")
            result = generator._categorize_error(error)
            assert result["type"] == "unknown"
            assert result["retryable"] is False


class TestThreeOptionsPattern:
    """Tests for Three Options pattern requirements."""

    def test_custom_solution_has_required_fields(self, mock_recommendations):
        """Custom solutions must have build tools and model recommendation."""
        for rec in mock_recommendations:
            custom = rec["options"]["custom_solution"]

            assert "build_tools" in custom, f"Missing build_tools in {rec['title']}"
            assert len(custom["build_tools"]) > 0, "build_tools should not be empty"

            assert "model_recommendation" in custom, f"Missing model_recommendation in {rec['title']}"
            assert custom["model_recommendation"], "model_recommendation should not be empty"

            assert "skills_required" in custom, f"Missing skills_required in {rec['title']}"

    def test_all_three_options_present(self, mock_recommendations):
        """Every recommendation should have all three options."""
        required_options = ["off_the_shelf", "best_in_class", "custom_solution"]

        for rec in mock_recommendations:
            options = rec.get("options", {})
            for opt in required_options:
                assert opt in options, f"Missing {opt} in recommendation {rec['title']}"

    def test_vendor_options_have_pricing(self, mock_recommendations):
        """Off-the-shelf and best-in-class should have pricing info."""
        for rec in mock_recommendations:
            for opt_name in ["off_the_shelf", "best_in_class"]:
                opt = rec["options"][opt_name]
                assert "monthly_cost" in opt or "implementation_cost" in opt, \
                    f"Missing cost info in {opt_name} for {rec['title']}"


class TestNotRecommendedFindings:
    """Tests for not-recommended finding requirements."""

    def test_not_recommended_have_low_scores(self, mock_findings):
        """Not-recommended findings should have at least one low score."""
        not_recommended = [f for f in mock_findings if f.get("is_not_recommended")]

        for finding in not_recommended:
            cv_score = finding.get("customer_value_score", 10)
            bh_score = finding.get("business_health_score", 10)

            # At least one score should be below 6
            assert cv_score < 6 or bh_score < 6, \
                f"Not-recommended '{finding['title']}' should have low scores"

    def test_not_recommended_have_explanations(self, mock_findings):
        """Not-recommended findings should have why_not and what_instead."""
        not_recommended = [f for f in mock_findings if f.get("is_not_recommended")]

        for finding in not_recommended:
            assert finding.get("why_not"), \
                f"Missing why_not for '{finding['title']}'"
            assert finding.get("what_instead"), \
                f"Missing what_instead for '{finding['title']}'"

    def test_minimum_not_recommended_count(self, mock_findings):
        """Should have minimum 3 not-recommended findings."""
        not_recommended = [f for f in mock_findings if f.get("is_not_recommended")]
        assert len(not_recommended) >= 3, \
            f"Should have at least 3 not-recommended, got {len(not_recommended)}"


class TestSourceCitations:
    """Tests for source citation requirements."""

    def test_findings_have_sources(self, mock_findings):
        """All findings should have at least one source."""
        for finding in mock_findings:
            sources = finding.get("sources", [])
            assert len(sources) >= 1, \
                f"Finding '{finding['title']}' should have sources"

    def test_sources_are_specific(self, mock_findings):
        """Sources should be specific, not generic."""
        generic_sources = ["Industry benchmark", "Best practice", "Standard"]

        for finding in mock_findings:
            sources = finding.get("sources", [])
            for source in sources:
                is_generic = any(g.lower() in source.lower() for g in generic_sources)
                # Source should either be not generic, or have additional context
                if is_generic:
                    assert len(source) > 20, \
                        f"Source '{source}' in '{finding['title']}' is too generic"


class TestConfidenceScoring:
    """Tests for confidence scoring requirements."""

    def test_valid_confidence_levels(self, mock_findings):
        """Confidence should be high, medium, or low."""
        valid_levels = ["high", "medium", "low"]

        for finding in mock_findings:
            confidence = finding.get("confidence", "").lower()
            assert confidence in valid_levels, \
                f"Invalid confidence '{confidence}' in '{finding['title']}'"

    def test_confidence_distribution(self, mock_findings):
        """Should have a mix of confidence levels."""
        confidence_counts = {"high": 0, "medium": 0, "low": 0}

        for finding in mock_findings:
            conf = finding.get("confidence", "medium").lower()
            if conf in confidence_counts:
                confidence_counts[conf] += 1

        # Should have at least some variety
        non_zero_levels = sum(1 for c in confidence_counts.values() if c > 0)
        assert non_zero_levels >= 2, \
            f"Should have variety in confidence levels: {confidence_counts}"
