"""Test that StoreProfile is loaded and included in report context."""
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.store_profile import DataSource, StoreMetric, StoreProfile
from src.services.store_profile_service import StoreProfileService


class TestStoreProfileInReportContext:
    def test_profile_to_prompt_context_includes_real_data(self) -> None:
        profile = StoreProfile(
            platform="shopify",
            currency="EUR",
            ecommerce_sub_type="dtc_brand",
            sales_channels=["own_website"],
            monthly_revenue=StoreMetric(value=Decimal("25000"), source=DataSource.MANUAL_ENTRY),
            monthly_orders=StoreMetric(value=400, source=DataSource.MANUAL_ENTRY),
            average_order_value=StoreMetric(value=Decimal("62.50"), source=DataSource.MANUAL_ENTRY),
        )
        ctx = profile.to_prompt_context()

        assert ctx["completeness"] == pytest.approx(0.5)
        assert ctx["monthly_revenue"]["value"] == 25000.0
        assert ctx["monthly_revenue"]["source"] == "manual_entry"
        assert ctx["cart_abandonment_rate"] is None  # not provided, will use benchmark

    def test_empty_profile_signals_benchmark_mode(self) -> None:
        profile = StoreProfile(
            platform="shopify",
            currency="EUR",
            ecommerce_sub_type="dtc_brand",
            sales_channels=[],
        )
        ctx = profile.to_prompt_context()

        assert ctx["completeness"] == 0.0
        assert ctx["source"] == "benchmark"
        assert ctx["completeness_label"] == "industry benchmarks"

    @pytest.mark.asyncio
    async def test_load_returns_none_for_no_profile(self) -> None:
        service = StoreProfileService()
        mock_supabase = MagicMock()
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.maybe_single.return_value = mock_table
        mock_table.execute = AsyncMock(return_value=MagicMock(data=None))

        with patch("src.services.store_profile_service.get_async_supabase", new_callable=AsyncMock, return_value=mock_supabase):
            result = await service.load("nonexistent")
        assert result is None
