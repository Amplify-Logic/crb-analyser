"""Tests for CRB operator commands."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_health_command_returns_system_status():
    """Health command should return vendor + KB + DB status."""
    from src.telegram.handlers.crb_commands import format_health_response

    health_data = {
        "vendors": {"stale_count": 3, "total": 148, "status": "warning"},
        "kb": {"stale_files": 0, "status": "healthy"},
        "expertise": {"status": "healthy", "record_count": 12},
    }
    result = format_health_response(health_data)
    assert "148" in result
    assert "3" in result
    assert "OK" in result


@pytest.mark.asyncio
async def test_reports_command_formats_stats():
    """Reports command should show delivery stats."""
    from src.telegram.handlers.crb_commands import format_reports_response

    reports_data = {
        "total": 5,
        "completed": 4,
        "failed": 1,
        "period": "today",
    }
    result = format_reports_response(reports_data)
    assert "5" in result
    assert "4" in result
