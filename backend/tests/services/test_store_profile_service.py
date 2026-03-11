"""Tests for StoreProfileService."""
import uuid
from decimal import Decimal
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.store_profile import DataSource, StoreProfile
from src.services.store_profile_service import StoreProfileService


@pytest.fixture
def service() -> StoreProfileService:
    return StoreProfileService()


@pytest.fixture
def manual_entry_payload() -> Dict[str, Any]:
    return {
        "monthly_revenue": "25000",
        "average_order_value": "62.50",
        "cart_abandonment_rate": "72",
        "repeat_customer_rate": "",
        "email_list_size": "8500",
    }


@pytest.fixture
def quiz_context() -> Dict[str, Any]:
    return {
        "platform": "shopify",
        "currency": "EUR",
        "ecommerce_sub_type": "dtc_brand",
        "sales_channels": ["own_website", "amazon"],
        "monthly_orders": 400,
    }


class TestBuildProfile:
    def test_build_from_manual_entry(
        self,
        service: StoreProfileService,
        manual_entry_payload: Dict[str, Any],
        quiz_context: Dict[str, Any],
    ) -> None:
        profile = service.build_profile(
            source="manual_entry",
            raw_answers=manual_entry_payload,
            **quiz_context,
        )
        assert profile.source == DataSource.MANUAL_ENTRY
        assert profile.monthly_revenue is not None
        assert profile.monthly_revenue.value == Decimal("25000")
        assert profile.repeat_customer_rate is None  # blank
        assert profile.completeness == pytest.approx(5 / 6)  # 5 of 6 filled

    def test_build_skip(
        self,
        service: StoreProfileService,
        quiz_context: Dict[str, Any],
    ) -> None:
        profile = service.build_profile(
            source="skip",
            raw_answers={},
            **quiz_context,
        )
        assert profile.source == DataSource.BENCHMARK
        assert profile.completeness == 0.0


class TestSerializeDeserialize:
    def test_roundtrip(
        self,
        service: StoreProfileService,
        manual_entry_payload: Dict[str, Any],
        quiz_context: Dict[str, Any],
    ) -> None:
        profile = service.build_profile(
            source="manual_entry",
            raw_answers=manual_entry_payload,
            **quiz_context,
        )
        serialized = service.serialize_for_db(profile)
        assert isinstance(serialized["metrics"], dict)
        assert serialized["source"] == "manual_entry"
        assert serialized["completeness"] == pytest.approx(5 / 6)

        restored = service.deserialize_from_db(serialized)
        assert restored.monthly_revenue is not None
        assert restored.monthly_revenue.value == Decimal("25000")
        assert restored.completeness == profile.completeness


class TestSaveAndLoad:
    @pytest.mark.asyncio
    async def test_save_store_profile(
        self,
        service: StoreProfileService,
        manual_entry_payload: Dict[str, Any],
        quiz_context: Dict[str, Any],
    ) -> None:
        session_id = str(uuid.uuid4())
        profile = service.build_profile(
            source="manual_entry",
            raw_answers=manual_entry_payload,
            **quiz_context,
        )

        mock_supabase = MagicMock()
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        mock_table.upsert.return_value = mock_table
        mock_table.execute = AsyncMock(return_value=MagicMock(data=[{"id": "abc"}]))

        with patch("src.services.store_profile_service.get_async_supabase", new_callable=AsyncMock, return_value=mock_supabase):
            await service.save(session_id=session_id, profile=profile)

        mock_supabase.table.assert_called_once_with("store_profiles")
        call_args = mock_table.upsert.call_args[0][0]
        assert call_args["quiz_session_id"] == session_id
        assert call_args["source"] == "manual_entry"

    @pytest.mark.asyncio
    async def test_load_store_profile(
        self,
        service: StoreProfileService,
    ) -> None:
        session_id = str(uuid.uuid4())

        mock_supabase = MagicMock()
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.maybe_single.return_value = mock_table
        mock_table.execute = AsyncMock(return_value=MagicMock(data={
            "source": "manual_entry",
            "completeness": 0.5,
            "currency": "EUR",
            "metrics": {
                "platform": "shopify",
                "ecommerce_sub_type": "dtc_brand",
                "sales_channels": ["own_website"],
                "monthly_revenue": {"value": 25000, "source": "manual_entry", "captured_at": "2026-03-11T00:00:00+00:00"},
            },
        }))

        with patch("src.services.store_profile_service.get_async_supabase", new_callable=AsyncMock, return_value=mock_supabase):
            profile = await service.load(session_id=session_id)

        assert profile is not None
        assert profile.monthly_revenue is not None

    @pytest.mark.asyncio
    async def test_load_returns_none_when_missing(
        self,
        service: StoreProfileService,
    ) -> None:
        session_id = str(uuid.uuid4())

        mock_supabase = MagicMock()
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.maybe_single.return_value = mock_table
        mock_table.execute = AsyncMock(return_value=MagicMock(data=None))

        with patch("src.services.store_profile_service.get_async_supabase", new_callable=AsyncMock, return_value=mock_supabase):
            profile = await service.load(session_id=session_id)

        assert profile is None
