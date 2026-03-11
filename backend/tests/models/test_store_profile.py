"""Tests for StoreProfile model."""
from decimal import Decimal
from datetime import datetime, timezone

import pytest

from src.models.store_profile import (
    DataSource,
    StoreMetric,
    StoreProfile,
)


class TestStoreMetric:
    def test_create_manual_metric(self) -> None:
        metric = StoreMetric(
            value=Decimal("25000"),
            source=DataSource.MANUAL_ENTRY,
        )
        assert metric.value == Decimal("25000")
        assert metric.source == DataSource.MANUAL_ENTRY
        assert metric.captured_at is not None

    def test_create_benchmark_metric(self) -> None:
        metric = StoreMetric(
            value=0.65,
            source=DataSource.BENCHMARK,
        )
        assert metric.value == 0.65
        assert metric.source == DataSource.BENCHMARK


class TestStoreProfile:
    def test_empty_profile_has_zero_completeness(self) -> None:
        profile = StoreProfile(
            platform="shopify",
            currency="EUR",
            ecommerce_sub_type="dtc_brand",
            sales_channels=["own_website"],
        )
        assert profile.completeness == 0.0
        assert profile.source == DataSource.BENCHMARK

    def test_partial_manual_entry(self) -> None:
        profile = StoreProfile(
            platform="shopify",
            currency="EUR",
            ecommerce_sub_type="dtc_brand",
            sales_channels=["own_website"],
            monthly_revenue=StoreMetric(
                value=Decimal("25000"),
                source=DataSource.MANUAL_ENTRY,
            ),
            monthly_orders=StoreMetric(
                value=400,
                source=DataSource.MANUAL_ENTRY,
            ),
            average_order_value=StoreMetric(
                value=Decimal("62.50"),
                source=DataSource.MANUAL_ENTRY,
            ),
        )
        # 3 of 6 tier-1 metrics filled = 0.5
        assert profile.completeness == pytest.approx(0.5)
        assert profile.source == DataSource.MANUAL_ENTRY

    def test_full_manual_entry(self) -> None:
        profile = StoreProfile(
            platform="shopify",
            currency="EUR",
            ecommerce_sub_type="dtc_brand",
            sales_channels=["own_website"],
            monthly_revenue=StoreMetric(value=Decimal("25000"), source=DataSource.MANUAL_ENTRY),
            monthly_orders=StoreMetric(value=400, source=DataSource.MANUAL_ENTRY),
            average_order_value=StoreMetric(value=Decimal("62.50"), source=DataSource.MANUAL_ENTRY),
            cart_abandonment_rate=StoreMetric(value=0.72, source=DataSource.MANUAL_ENTRY),
            repeat_customer_rate=StoreMetric(value=0.25, source=DataSource.MANUAL_ENTRY),
            email_list_size=StoreMetric(value=8500, source=DataSource.MANUAL_ENTRY),
        )
        assert profile.completeness == pytest.approx(1.0)

    def test_completeness_label(self) -> None:
        empty = StoreProfile(
            platform="shopify", currency="EUR",
            ecommerce_sub_type="dtc_brand", sales_channels=[],
        )
        assert empty.completeness_label == "industry benchmarks"

        partial = StoreProfile(
            platform="shopify", currency="EUR",
            ecommerce_sub_type="dtc_brand", sales_channels=[],
            monthly_revenue=StoreMetric(value=Decimal("25000"), source=DataSource.MANUAL_ENTRY),
            monthly_orders=StoreMetric(value=400, source=DataSource.MANUAL_ENTRY),
            average_order_value=StoreMetric(value=Decimal("62.50"), source=DataSource.MANUAL_ENTRY),
        )
        assert partial.completeness_label == "your data + benchmarks"

    def test_to_dict_for_prompt(self) -> None:
        profile = StoreProfile(
            platform="shopify", currency="EUR",
            ecommerce_sub_type="dtc_brand", sales_channels=["own_website"],
            monthly_revenue=StoreMetric(value=Decimal("25000"), source=DataSource.MANUAL_ENTRY),
        )
        d = profile.to_prompt_context()
        assert d["monthly_revenue"]["value"] == 25000
        assert d["monthly_revenue"]["source"] == "manual_entry"
        assert d["completeness"] == pytest.approx(1 / 6)

    def test_from_manual_entry(self) -> None:
        """Test factory method from quiz manual entry answers."""
        raw = {
            "monthly_revenue": "25000",
            "average_order_value": "62.50",
            "cart_abandonment_rate": "72",
            "repeat_customer_rate": "",  # left blank = don't know
            "email_list_size": "",
        }
        profile = StoreProfile.from_manual_entry(
            raw_answers=raw,
            platform="shopify",
            currency="EUR",
            ecommerce_sub_type="dtc_brand",
            sales_channels=["own_website"],
            monthly_orders=400,
        )
        assert profile.monthly_revenue is not None
        assert profile.monthly_revenue.value == Decimal("25000")
        assert profile.average_order_value is not None
        assert profile.repeat_customer_rate is None  # blank = skip
        assert profile.email_list_size is None
        assert profile.monthly_orders is not None
        assert profile.monthly_orders.value == 400
