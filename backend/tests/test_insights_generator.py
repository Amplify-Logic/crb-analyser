"""Tests for InsightsGenerator with curated insights integration."""
import pytest
from unittest.mock import patch, MagicMock

from src.services.insights_generator import InsightsGenerator, IndustryInsights
from src.models.insight import (
    Insight,
    InsightType,
    InsightSource,
    InsightTags,
    UseIn,
    AudienceRelevance,
)


def _make_curated_insight(
    *,
    id: str = "trend-test-1",
    type: InsightType = InsightType.TREND,
    title: str = "Test Trend",
    content: str = "Test content",
    actionable_insight: str = "Do something",
    industries: list = None,
    use_in: list = None,
    reviewed: bool = True,
    audience_relevance: AudienceRelevance = AudienceRelevance.HIGH,
) -> Insight:
    """Helper to create a curated insight for testing."""
    return Insight(
        id=id,
        type=type,
        title=title,
        content=content,
        actionable_insight=actionable_insight,
        tags=InsightTags(
            topics=["test"],
            industries=industries or ["all"],
            use_in=use_in or [UseIn.REPORT],
            user_stages=[],
        ),
        source=InsightSource(title="Test Source", author="Test Author"),
        reviewed=reviewed,
        audience_relevance=audience_relevance,
    )


class TestInsightsGeneratorBase:
    """Test base insights generation (existing functionality)."""

    def test_generates_insights_for_known_industry(self):
        gen = InsightsGenerator()
        result = gen.generate_insights(industry="professional-services", ai_readiness_score=50)
        assert isinstance(result, IndustryInsights)
        assert result.industry == "professional-services"
        assert len(result.adoption_stats) > 0
        assert len(result.social_proof) > 0

    def test_raises_for_unknown_industry(self):
        gen = InsightsGenerator()
        with pytest.raises(ValueError, match="Unsupported industry"):
            gen.generate_insights(industry="unknown-industry", ai_readiness_score=50)

    def test_best_fit_based_on_readiness(self):
        gen = InsightsGenerator()
        high = gen.generate_insights(industry="dental", ai_readiness_score=80)
        mid = gen.generate_insights(industry="dental", ai_readiness_score=55)
        low = gen.generate_insights(industry="dental", ai_readiness_score=30)
        assert high.opportunity_map.best_fit == "emerging"
        assert mid.opportunity_map.best_fit == "growing"
        assert low.opportunity_map.best_fit == "established"


class TestCuratedInsightsIntegration:
    """Test that curated insights from InsightService are included."""

    @patch("src.services.insights_generator.get_insight_service")
    def test_curated_trends_included_in_result(self, mock_get_service):
        """Curated trend insights should appear in the result."""
        mock_service = MagicMock()
        mock_service.get_insights_for_surface.return_value = [
            _make_curated_insight(
                id="trend-real-1",
                type=InsightType.TREND,
                title="AI Models Are Commoditized",
                content="Performance gaps are narrowing",
                actionable_insight="Focus on integration",
            ),
        ]
        mock_get_service.return_value = mock_service

        gen = InsightsGenerator()
        result = gen.generate_insights(industry="professional-services", ai_readiness_score=50)

        assert "curated_insights" in result.model_dump()
        curated = result.model_dump()["curated_insights"]
        assert len(curated["trends"]) == 1
        assert curated["trends"][0]["title"] == "AI Models Are Commoditized"

    @patch("src.services.insights_generator.get_insight_service")
    def test_curated_case_studies_included(self, mock_get_service):
        """Curated case studies should appear in the result."""
        mock_service = MagicMock()
        mock_service.get_insights_for_surface.return_value = [
            _make_curated_insight(
                id="case-1",
                type=InsightType.CASE_STUDY,
                title="Agency Saves 15 Hours/Week",
                content="Marketing agency automated content",
                actionable_insight="Start with content automation",
            ),
        ]
        mock_get_service.return_value = mock_service

        gen = InsightsGenerator()
        result = gen.generate_insights(industry="professional-services", ai_readiness_score=50)

        curated = result.model_dump()["curated_insights"]
        assert len(curated["case_studies"]) == 1
        assert curated["case_studies"][0]["title"] == "Agency Saves 15 Hours/Week"

    @patch("src.services.insights_generator.get_insight_service")
    def test_curated_statistics_included(self, mock_get_service):
        """Curated statistics should appear in the result."""
        mock_service = MagicMock()
        mock_service.get_insights_for_surface.return_value = [
            _make_curated_insight(
                id="stat-1",
                type=InsightType.STATISTIC,
                title="72% of SMBs use AI",
                content="Most small businesses have adopted AI",
            ),
        ]
        mock_get_service.return_value = mock_service

        gen = InsightsGenerator()
        result = gen.generate_insights(industry="ecommerce", ai_readiness_score=50)

        curated = result.model_dump()["curated_insights"]
        assert len(curated["statistics"]) == 1

    @patch("src.services.insights_generator.get_insight_service")
    def test_filters_by_industry(self, mock_get_service):
        """Should pass industry to InsightService for filtering."""
        mock_service = MagicMock()
        mock_service.get_insights_for_surface.return_value = []
        mock_get_service.return_value = mock_service

        gen = InsightsGenerator()
        gen.generate_insights(industry="dental", ai_readiness_score=50)

        mock_service.get_insights_for_surface.assert_called_once_with(
            use_in=UseIn.REPORT,
            industry="dental",
            limit=10,
        )

    @patch("src.services.insights_generator.get_insight_service")
    def test_graceful_failure_when_service_unavailable(self, mock_get_service):
        """Should still work if InsightService fails."""
        mock_get_service.side_effect = Exception("Service unavailable")

        gen = InsightsGenerator()
        result = gen.generate_insights(industry="b2b-platforms", ai_readiness_score=50)

        # Should still return base insights
        assert isinstance(result, IndustryInsights)
        assert len(result.adoption_stats) > 0
        # curated_insights should be empty but present
        curated = result.model_dump()["curated_insights"]
        assert curated["trends"] == []
        assert curated["case_studies"] == []

    @patch("src.services.insights_generator.get_insight_service")
    def test_mixed_types_are_separated(self, mock_get_service):
        """Insights of different types should be separated by type."""
        mock_service = MagicMock()
        mock_service.get_insights_for_surface.return_value = [
            _make_curated_insight(id="trend-1", type=InsightType.TREND, title="Trend 1"),
            _make_curated_insight(id="case-1", type=InsightType.CASE_STUDY, title="Case 1"),
            _make_curated_insight(id="stat-1", type=InsightType.STATISTIC, title="Stat 1"),
            _make_curated_insight(id="quote-1", type=InsightType.QUOTE, title="Quote 1"),
        ]
        mock_get_service.return_value = mock_service

        gen = InsightsGenerator()
        result = gen.generate_insights(industry="ecommerce", ai_readiness_score=50)
        curated = result.model_dump()["curated_insights"]

        assert len(curated["trends"]) == 1
        assert len(curated["case_studies"]) == 1
        assert len(curated["statistics"]) == 1
        assert len(curated["quotes"]) == 1
