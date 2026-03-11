"""Tests for report metadata model and extraction logic."""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.report_metadata import (
    ReportMetadataCreate,
    ReportMetadata,
    save_report_metadata,
    _to_decimal,
)


# --- Fixtures ---

def _make_token_tracker(total_tokens: int = 5000, cost_usd: float = 0.25) -> MagicMock:
    tracker = MagicMock()
    tracker.get_summary.return_value = {
        "total_tokens": total_tokens,
        "estimated_cost_usd": cost_usd,
    }
    return tracker


def _make_context(
    industry: str = "ecommerce",
    company_name: str = "Test Co",
) -> dict:
    return {
        "industry": industry,
        "company_name": company_name,
        "answers": {
            "industry": industry,
            "employee_count": "11-50",
            "annual_revenue": "1M-5M",
            "primary_goals": ["reduce_costs", "improve_cx"],
            "current_tools": ["crm", "accounting"],
            "biggest_challenge": "Manual processes",
            "implementation_timeline": "3-6 months",
            "budget_comfort": "moderate",
        },
    }


def _make_executive_summary() -> dict:
    return {
        "ai_readiness_score": 72,
        "customer_value_score": 8,
        "business_health_score": 7,
        "total_value_potential": {"min": 15000, "max": 45000},
    }


def _make_findings(count: int = 3) -> list:
    categories = ["customer_service", "marketing", "operations"]
    return [
        {
            "id": f"f{i}",
            "title": f"Finding {i}",
            "category": categories[i % len(categories)],
            "playbook": {"steps": ["step1"]},
        }
        for i in range(count)
    ]


def _make_recommendations(count: int = 2) -> list:
    return [
        {"vendor_name": "Intercom", "title": "Rec 1"},
        {"vendor": {"name": "HubSpot"}, "title": "Rec 2"},
    ][:count]


# --- from_report_context tests ---

class TestFromReportContext:
    """Test the classmethod that extracts metadata from report artifacts."""

    def test_basic_extraction(self) -> None:
        started = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        metadata = ReportMetadataCreate.from_report_context(
            report_id="rpt-1",
            quiz_session_id="qs-1",
            tier="full",
            context=_make_context(),
            executive_summary=_make_executive_summary(),
            findings=_make_findings(3),
            recommendations=_make_recommendations(2),
            token_tracker=_make_token_tracker(),
            generation_started_at=started,
            generation_completed_at=datetime.utcnow(),
        )

        assert metadata.report_id == "rpt-1"
        assert metadata.quiz_session_id == "qs-1"
        assert metadata.tier == "full"
        assert metadata.industry == "ecommerce"
        assert metadata.company_name == "Test Co"
        assert metadata.employee_count == "11-50"
        assert metadata.annual_revenue == "1M-5M"

    def test_crb_scores(self) -> None:
        metadata = ReportMetadataCreate.from_report_context(
            report_id="rpt-1",
            quiz_session_id="qs-1",
            tier="quick",
            context=_make_context(),
            executive_summary=_make_executive_summary(),
            findings=[],
            recommendations=[],
            token_tracker=_make_token_tracker(),
            generation_started_at=None,
            generation_completed_at=datetime.utcnow(),
        )

        assert metadata.ai_readiness_score == Decimal("72")
        assert metadata.customer_value_score == Decimal("8")
        assert metadata.business_health_score == Decimal("7")
        assert metadata.value_potential_min == Decimal("15000")
        assert metadata.value_potential_max == Decimal("45000")

    def test_content_counts(self) -> None:
        metadata = ReportMetadataCreate.from_report_context(
            report_id="rpt-1",
            quiz_session_id="qs-1",
            tier="full",
            context=_make_context(),
            executive_summary=_make_executive_summary(),
            findings=_make_findings(5),
            recommendations=_make_recommendations(2),
            token_tracker=_make_token_tracker(),
            generation_started_at=None,
            generation_completed_at=datetime.utcnow(),
        )

        assert metadata.findings_count == 5
        assert metadata.recommendations_count == 2
        assert metadata.playbooks_count == 5  # All test findings have playbook

    def test_finding_categories_deduplicated(self) -> None:
        findings = [
            {"category": "marketing"},
            {"category": "marketing"},
            {"category": "operations"},
        ]
        metadata = ReportMetadataCreate.from_report_context(
            report_id="rpt-1",
            quiz_session_id="qs-1",
            tier="quick",
            context=_make_context(),
            executive_summary=_make_executive_summary(),
            findings=findings,
            recommendations=[],
            token_tracker=_make_token_tracker(),
            generation_started_at=None,
            generation_completed_at=datetime.utcnow(),
        )

        assert metadata.top_finding_categories == ["marketing", "operations"]

    def test_vendor_names_from_both_formats(self) -> None:
        recs = [
            {"vendor_name": "Intercom"},
            {"vendor": {"name": "HubSpot"}},
            {"vendor_name": "Intercom"},  # duplicate
        ]
        metadata = ReportMetadataCreate.from_report_context(
            report_id="rpt-1",
            quiz_session_id="qs-1",
            tier="full",
            context=_make_context(),
            executive_summary=_make_executive_summary(),
            findings=[],
            recommendations=recs,
            token_tracker=_make_token_tracker(),
            generation_started_at=None,
            generation_completed_at=datetime.utcnow(),
        )

        assert metadata.recommended_vendor_names == ["Intercom", "HubSpot"]

    def test_generation_duration(self) -> None:
        now = datetime.utcnow()
        started = (now - timedelta(seconds=120)).isoformat()

        metadata = ReportMetadataCreate.from_report_context(
            report_id="rpt-1",
            quiz_session_id="qs-1",
            tier="full",
            context=_make_context(),
            executive_summary=_make_executive_summary(),
            findings=[],
            recommendations=[],
            token_tracker=_make_token_tracker(),
            generation_started_at=started,
            generation_completed_at=now,
        )

        assert metadata.generation_duration_seconds is not None
        assert 119 < float(metadata.generation_duration_seconds) < 121

    def test_duration_none_when_no_start(self) -> None:
        metadata = ReportMetadataCreate.from_report_context(
            report_id="rpt-1",
            quiz_session_id="qs-1",
            tier="quick",
            context=_make_context(),
            executive_summary=_make_executive_summary(),
            findings=[],
            recommendations=[],
            token_tracker=_make_token_tracker(),
            generation_started_at=None,
            generation_completed_at=datetime.utcnow(),
        )

        assert metadata.generation_duration_seconds is None

    def test_token_cost_converted_to_eur(self) -> None:
        metadata = ReportMetadataCreate.from_report_context(
            report_id="rpt-1",
            quiz_session_id="qs-1",
            tier="full",
            context=_make_context(),
            executive_summary=_make_executive_summary(),
            findings=[],
            recommendations=[],
            token_tracker=_make_token_tracker(total_tokens=10000, cost_usd=1.0),
            generation_started_at=None,
            generation_completed_at=datetime.utcnow(),
        )

        assert metadata.total_tokens == 10000
        assert metadata.estimated_cost_eur == Decimal("0.9200")

    def test_quiz_context_fields(self) -> None:
        metadata = ReportMetadataCreate.from_report_context(
            report_id="rpt-1",
            quiz_session_id="qs-1",
            tier="full",
            context=_make_context(),
            executive_summary=_make_executive_summary(),
            findings=[],
            recommendations=[],
            token_tracker=_make_token_tracker(),
            generation_started_at=None,
            generation_completed_at=datetime.utcnow(),
        )

        assert metadata.current_tools == ["crm", "accounting"]
        assert metadata.biggest_challenge == "Manual processes"
        assert metadata.implementation_timeline == "3-6 months"
        assert metadata.budget_comfort == "moderate"
        assert metadata.primary_goals == ["reduce_costs", "improve_cx"]

    def test_empty_context_graceful(self) -> None:
        """Handles missing/empty data without crashing."""
        metadata = ReportMetadataCreate.from_report_context(
            report_id="rpt-1",
            quiz_session_id="qs-1",
            tier="quick",
            context={},
            executive_summary={},
            findings=[],
            recommendations=[],
            token_tracker=_make_token_tracker(total_tokens=0, cost_usd=0),
            generation_started_at=None,
            generation_completed_at=datetime.utcnow(),
        )

        assert metadata.industry is None
        assert metadata.company_name is None
        assert metadata.ai_readiness_score is None
        assert metadata.findings_count == 0
        assert metadata.top_finding_categories == []


# --- to_db_row tests ---

class TestToDbRow:
    def test_decimals_converted_to_float(self) -> None:
        metadata = ReportMetadataCreate(
            report_id="rpt-1",
            quiz_session_id="qs-1",
            tier="quick",
            ai_readiness_score=Decimal("72.5"),
            estimated_cost_eur=Decimal("0.23"),
        )
        row = metadata.to_db_row()

        assert isinstance(row["ai_readiness_score"], float)
        assert isinstance(row["estimated_cost_eur"], float)
        assert row["ai_readiness_score"] == 72.5


# --- _to_decimal tests ---

class TestToDecimal:
    def test_from_int(self) -> None:
        assert _to_decimal(72) == Decimal("72")

    def test_from_float(self) -> None:
        assert _to_decimal(3.14) == Decimal("3.14")

    def test_from_none(self) -> None:
        assert _to_decimal(None) is None

    def test_from_invalid(self) -> None:
        assert _to_decimal("not-a-number") is None


# --- save_report_metadata tests ---

def _mock_supabase() -> MagicMock:
    """Create a mock supabase client with chained table().insert().execute()."""
    client = MagicMock()
    client.table.return_value.insert.return_value.execute = AsyncMock()
    return client


class TestSaveReportMetadata:
    @pytest.mark.asyncio
    async def test_successful_save(self) -> None:
        metadata = ReportMetadataCreate(
            report_id="rpt-1",
            quiz_session_id="qs-1",
            tier="quick",
        )
        mock_client = _mock_supabase()

        with patch("src.config.supabase_client.get_async_supabase", new_callable=AsyncMock, return_value=mock_client):
            await save_report_metadata(metadata)

        mock_client.table.assert_called_once_with("report_metadata")
        mock_client.table.return_value.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_failure_does_not_raise(self) -> None:
        """Fire-and-forget: errors are logged, not raised."""
        metadata = ReportMetadataCreate(
            report_id="rpt-1",
            quiz_session_id="qs-1",
            tier="quick",
        )
        mock_client = _mock_supabase()
        mock_client.table.return_value.insert.return_value.execute = AsyncMock(
            side_effect=Exception("DB connection failed")
        )

        with patch("src.config.supabase_client.get_async_supabase", new_callable=AsyncMock, return_value=mock_client):
            # Should NOT raise
            await save_report_metadata(metadata)
