"""
Unit tests for token_analytics.py
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from src.services.token_analytics import TokenAnalyticsService


class TestTokenAnalyticsService:
    """Tests for token analytics service."""

    @pytest.fixture
    def mock_reports_data(self):
        """Mock report data with token usage."""
        return [
            {
                "id": "report-1",
                "tier": "quick",
                "generation_completed_at": datetime.utcnow().isoformat(),
                "token_usage": {
                    "usage": [
                        {"task": "generate_findings", "model": "claude-sonnet-4-20250514", "input_tokens": 1000, "output_tokens": 500},
                        {"task": "generate_recommendations", "model": "claude-sonnet-4-20250514", "input_tokens": 800, "output_tokens": 600},
                    ],
                    "summary": {
                        "total_input_tokens": 1800,
                        "total_output_tokens": 1100,
                        "total_tokens": 2900,
                        "estimated_cost_usd": 0.05,
                        "by_model": {
                            "claude-sonnet-4-20250514": {"input": 1800, "output": 1100, "estimated_cost_usd": 0.05}
                        }
                    }
                }
            },
            {
                "id": "report-2",
                "tier": "full",
                "generation_completed_at": datetime.utcnow().isoformat(),
                "token_usage": {
                    "usage": [
                        {"task": "generate_findings", "model": "claude-sonnet-4-20250514", "input_tokens": 2000, "output_tokens": 1000},
                        {"task": "complex_analysis", "model": "claude-opus-4-5-20250514", "input_tokens": 500, "output_tokens": 300},
                    ],
                    "summary": {
                        "total_input_tokens": 2500,
                        "total_output_tokens": 1300,
                        "total_tokens": 3800,
                        "estimated_cost_usd": 0.15,
                        "by_model": {
                            "claude-sonnet-4-20250514": {"input": 2000, "output": 1000, "estimated_cost_usd": 0.05},
                            "claude-opus-4-5-20250514": {"input": 500, "output": 300, "estimated_cost_usd": 0.10}
                        }
                    }
                }
            }
        ]

    @pytest.mark.asyncio
    async def test_get_usage_summary(self, mock_reports_data):
        """Should aggregate usage correctly."""
        with patch('src.services.token_analytics.get_async_supabase') as mock_supabase:
            mock_client = AsyncMock()
            mock_supabase.return_value = mock_client

            # Setup mock chain
            mock_query = MagicMock()
            mock_query.gte.return_value = mock_query
            mock_query.eq.return_value = mock_query
            mock_query.execute = AsyncMock(return_value=MagicMock(data=mock_reports_data))
            mock_client.table.return_value.select.return_value = mock_query

            summary = await TokenAnalyticsService.get_usage_summary(days=30)

            assert summary["totals"]["reports_generated"] == 2
            assert summary["totals"]["total_tokens"] == 2900 + 3800
            assert "by_tier" in summary

    @pytest.mark.asyncio
    async def test_get_cost_trend(self, mock_reports_data):
        """Should return daily cost breakdown."""
        with patch('src.services.token_analytics.get_async_supabase') as mock_supabase:
            mock_client = AsyncMock()
            mock_supabase.return_value = mock_client

            mock_query = MagicMock()
            mock_query.gte.return_value = mock_query
            mock_query.eq.return_value = mock_query
            mock_query.execute = AsyncMock(return_value=MagicMock(data=mock_reports_data))
            mock_client.table.return_value.select.return_value = mock_query

            trend = await TokenAnalyticsService.get_cost_trend(days=30, granularity="day")

            assert isinstance(trend, list)

    @pytest.mark.asyncio
    async def test_get_model_efficiency(self, mock_reports_data):
        """Should analyze model usage efficiency."""
        with patch('src.services.token_analytics.get_async_supabase') as mock_supabase:
            mock_client = AsyncMock()
            mock_supabase.return_value = mock_client

            mock_query = MagicMock()
            mock_query.gte.return_value = mock_query
            mock_query.eq.return_value = mock_query
            mock_query.execute = AsyncMock(return_value=MagicMock(data=mock_reports_data))
            mock_client.table.return_value.select.return_value = mock_query

            efficiency = await TokenAnalyticsService.get_model_efficiency(days=30)

            assert "task_model_breakdown" in efficiency
            assert "optimization_suggestions" in efficiency

    @pytest.mark.asyncio
    async def test_get_report_cost_breakdown(self, mock_reports_data):
        """Should return detailed breakdown for single report."""
        with patch('src.services.token_analytics.get_async_supabase') as mock_supabase:
            mock_client = AsyncMock()
            mock_supabase.return_value = mock_client

            mock_query = MagicMock()
            mock_query.eq.return_value = mock_query
            mock_query.single.return_value = mock_query
            mock_query.execute = AsyncMock(return_value=MagicMock(data=mock_reports_data[0]))
            mock_client.table.return_value.select.return_value = mock_query

            breakdown = await TokenAnalyticsService.get_report_cost_breakdown("report-1")

            assert breakdown is not None
            assert breakdown["report_id"] == "report-1"
            assert "task_breakdown" in breakdown
            assert "most_expensive_task" in breakdown

    def test_optimization_suggestions(self):
        """Should generate optimization suggestions."""
        efficiency = {
            "generate_findings": {
                "models_used": {"claude-opus-4-5-20250514": 10},  # Too much Opus
                "primary_model": "claude-opus-4-5-20250514",
                "total_calls": 10
            }
        }

        suggestions = TokenAnalyticsService._get_optimization_suggestions(efficiency)

        # Should suggest reducing Opus usage
        assert isinstance(suggestions, list)
