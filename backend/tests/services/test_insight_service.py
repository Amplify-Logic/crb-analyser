"""
Tests for InsightService

Tests the curated insights management service including:
- Loading and caching insights
- CRUD operations
- Filtering by type, tags, and review status
- Search functionality
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from src.models.insight import (
    Insight,
    InsightCollection,
    InsightTags,
    InsightType,
    InsightSource,
    UseIn,
)
from src.services.insight_service import InsightService, CURATED_PATH, TYPE_FILES


@pytest.fixture
def sample_insight() -> Insight:
    """Create a sample insight for testing."""
    return Insight(
        id="test-insight-001",
        type=InsightType.TREND,
        title="Test AI Trend",
        content="This is a test insight about AI trends.",
        tags=InsightTags(
            topics=["ai", "automation"],
            industries=["all"],
            use_in=[UseIn.REPORT, UseIn.LANDING],
            user_stages=["considering"],
        ),
        source=InsightSource(
            title="Test Source",
            author="Test Author",
            url="https://example.com",
            date="2026-01-15",
            type="article",
        ),
        reviewed=False,
    )


@pytest.fixture
def sample_insights() -> list[Insight]:
    """Create a list of sample insights for testing."""
    return [
        Insight(
            id="trend-001",
            type=InsightType.TREND,
            title="Trend 1",
            content="Content for trend 1",
            tags=InsightTags(
                topics=["ai"],
                industries=["all"],
                use_in=[UseIn.REPORT, UseIn.LANDING],
                user_stages=["considering"],
            ),
            source=InsightSource(title="Source 1", type="article"),
            reviewed=True,
        ),
        Insight(
            id="trend-002",
            type=InsightType.TREND,
            title="Trend 2",
            content="Content for trend 2",
            tags=InsightTags(
                topics=["automation"],
                industries=["healthcare"],
                use_in=[UseIn.REPORT],
                user_stages=["early_adopter"],
            ),
            source=InsightSource(title="Source 2", type="article"),
            reviewed=False,
        ),
        Insight(
            id="case-study-001",
            type=InsightType.CASE_STUDY,
            title="Case Study 1",
            content="Content for case study",
            tags=InsightTags(
                topics=["implementation"],
                industries=["retail"],
                use_in=[UseIn.REPORT, UseIn.QUIZ_RESULTS],
                user_stages=["scaling"],
            ),
            source=InsightSource(title="Source 3", type="report"),
            reviewed=True,
        ),
    ]


class TestInsightService:
    """Test suite for InsightService."""

    def test_get_all_insights_empty(self):
        """Test getting insights when none exist."""
        service = InsightService()
        # Clear cache to simulate fresh state
        service._cache.clear()
        service._cache_time = None

        # This should return insights from disk or empty list
        insights = service.get_all_insights(reviewed_only=False)
        # We just verify it returns a list without error
        assert isinstance(insights, list)

    def test_get_stats(self):
        """Test getting insight statistics."""
        service = InsightService()
        stats = service.get_stats()

        assert "total" in stats
        assert "reviewed" in stats
        assert "unreviewed" in stats
        assert "by_type" in stats
        assert "by_use_in" in stats
        assert isinstance(stats["total"], int)
        assert stats["total"] >= 0

    def test_get_insights_by_type(self):
        """Test filtering insights by type."""
        service = InsightService()

        # Get trends
        trends = service.get_insights_by_type(InsightType.TREND, reviewed_only=False)
        assert isinstance(trends, list)

        # All returned insights should be of type TREND
        for insight in trends:
            assert insight.type == InsightType.TREND

    def test_get_insights_reviewed_only(self):
        """Test filtering by reviewed status."""
        service = InsightService()

        # Get only reviewed insights
        reviewed = service.get_all_insights(reviewed_only=True)

        # All returned insights should be reviewed
        for insight in reviewed:
            assert insight.reviewed is True

    def test_get_insight_by_id_not_found(self):
        """Test getting insight by non-existent ID."""
        service = InsightService()

        insight = service.get_insight_by_id("non-existent-id-12345")
        assert insight is None

    def test_get_insights_for_surface(self):
        """Test getting insights for a specific surface."""
        service = InsightService()

        # Get insights for landing page
        landing_insights = service.get_insights_for_surface(
            use_in=UseIn.LANDING,
            limit=5,
        )

        assert isinstance(landing_insights, list)
        assert len(landing_insights) <= 5

        # All returned insights should have landing in use_in
        for insight in landing_insights:
            use_in_values = [
                u.value if hasattr(u, 'value') else u
                for u in insight.tags.use_in
            ]
            assert "landing" in use_in_values

    def test_cache_refresh(self):
        """Test that cache is properly managed."""
        service = InsightService()

        # First call should populate cache
        _ = service.get_all_insights(reviewed_only=False)
        first_cache_time = service._cache_time

        # Second call within TTL should use cache
        _ = service.get_all_insights(reviewed_only=False)
        second_cache_time = service._cache_time

        assert first_cache_time == second_cache_time


class TestInsightServiceWithMockedData:
    """Tests using mocked insight data."""

    @pytest.fixture
    def service_with_mocked_cache(self, sample_insights):
        """Create service with mocked cache data."""
        service = InsightService()

        # Create collections from sample insights
        from collections import defaultdict
        collections = defaultdict(list)
        for insight in sample_insights:
            # insight.type might be a string if Pydantic serialized it
            insight_type = insight.type if isinstance(insight.type, InsightType) else InsightType(insight.type)
            collections[insight_type].append(insight)

        # Populate cache
        for insight_type, insights in collections.items():
            type_value = insight_type.value if isinstance(insight_type, InsightType) else insight_type
            service._cache[insight_type] = InsightCollection(
                type=insight_type,
                description=f"{type_value} insights",
                insights=insights,
            )

        from datetime import datetime
        service._cache_time = datetime.now()

        return service

    def test_filter_by_type_with_mocked_data(self, service_with_mocked_cache):
        """Test filtering by type with known data."""
        trends = service_with_mocked_cache.get_insights_by_type(
            InsightType.TREND, reviewed_only=False
        )

        assert len(trends) == 2
        assert all(i.type == InsightType.TREND for i in trends)

    def test_filter_reviewed_with_mocked_data(self, service_with_mocked_cache):
        """Test filtering by reviewed status with known data."""
        reviewed = service_with_mocked_cache.get_all_insights(reviewed_only=True)

        # We know we have 2 reviewed insights (trend-001 and case-study-001)
        assert len(reviewed) == 2
        assert all(i.reviewed for i in reviewed)

    def test_get_insight_by_id_with_mocked_data(self, service_with_mocked_cache):
        """Test getting insight by ID with known data."""
        insight = service_with_mocked_cache.get_insight_by_id("trend-001")

        assert insight is not None
        assert insight.id == "trend-001"
        assert insight.type == InsightType.TREND
        assert insight.title == "Trend 1"

    def test_stats_with_mocked_data(self, service_with_mocked_cache):
        """Test stats calculation with known data."""
        stats = service_with_mocked_cache.get_stats()

        assert stats["total"] == 3
        assert stats["reviewed"] == 2
        assert stats["unreviewed"] == 1
        assert stats["by_type"]["trend"]["total"] == 2
        assert stats["by_type"]["trend"]["reviewed"] == 1


class TestInsightCRUD:
    """Test CRUD operations on insights."""

    def test_add_insight_creates_valid_insight(self, sample_insight):
        """Test that adding an insight works correctly."""
        service = InsightService()

        # Note: This will actually save to disk, so we should use a fixture
        # that mocks the file system in a real test suite
        # For now, we just test the method doesn't error

        # Clean up first if the test insight exists
        existing = service.get_insight_by_id(sample_insight.id)
        if existing:
            service.delete_insight(sample_insight.id)

        result = service.add_insight(sample_insight)
        assert result is True

        # Verify it was added
        retrieved = service.get_insight_by_id(sample_insight.id)
        assert retrieved is not None
        assert retrieved.id == sample_insight.id

        # Clean up
        service.delete_insight(sample_insight.id)

    def test_update_insight(self, sample_insight):
        """Test updating an insight."""
        service = InsightService()

        # Add insight first
        existing = service.get_insight_by_id(sample_insight.id)
        if existing:
            service.delete_insight(sample_insight.id)

        service.add_insight(sample_insight)

        # Update the insight
        result = service.update_insight(sample_insight.id, {"title": "Updated Title"})
        assert result is True

        # Verify update
        updated = service.get_insight_by_id(sample_insight.id)
        assert updated.title == "Updated Title"

        # Clean up
        service.delete_insight(sample_insight.id)

    def test_mark_reviewed(self, sample_insight):
        """Test marking an insight as reviewed."""
        service = InsightService()

        # Add insight first
        existing = service.get_insight_by_id(sample_insight.id)
        if existing:
            service.delete_insight(sample_insight.id)

        service.add_insight(sample_insight)
        assert service.get_insight_by_id(sample_insight.id).reviewed is False

        # Mark as reviewed
        result = service.mark_reviewed(sample_insight.id, True)
        assert result is True

        # Verify
        reviewed = service.get_insight_by_id(sample_insight.id)
        assert reviewed.reviewed is True

        # Clean up
        service.delete_insight(sample_insight.id)

    def test_delete_insight(self, sample_insight):
        """Test deleting an insight."""
        service = InsightService()

        # Add insight first
        existing = service.get_insight_by_id(sample_insight.id)
        if existing:
            service.delete_insight(sample_insight.id)

        service.add_insight(sample_insight)

        # Delete
        result = service.delete_insight(sample_insight.id)
        assert result is True

        # Verify deletion
        deleted = service.get_insight_by_id(sample_insight.id)
        assert deleted is None
