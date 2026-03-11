"""Tests for store profile quiz endpoint."""
import uuid
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models.store_profile import DataSource, StoreProfile

client = TestClient(app)


@pytest.fixture
def session_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def manual_entry_body() -> Dict[str, Any]:
    return {
        "source": "manual_entry",
        "store_metrics": {
            "monthly_revenue": "25000",
            "average_order_value": "62.50",
            "cart_abandonment_rate": "72",
            "repeat_customer_rate": "",
            "email_list_size": "8500",
        },
        "platform": "shopify",
        "currency": "EUR",
        "ecommerce_sub_type": "dtc_brand",
        "sales_channels": ["own_website"],
        "monthly_orders": 400,
    }


@pytest.fixture
def skip_body() -> Dict[str, Any]:
    return {
        "source": "skip",
        "store_metrics": {},
        "platform": "shopify",
        "currency": "EUR",
        "ecommerce_sub_type": "dtc_brand",
        "sales_channels": ["own_website"],
    }


class TestStoreProfileEndpoint:
    def test_save_manual_entry(
        self, session_id: str, manual_entry_body: Dict[str, Any]
    ) -> None:
        mock_supabase = MagicMock()
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        # Session lookup chain
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.maybe_single.return_value = mock_table
        mock_table.execute = AsyncMock(return_value=MagicMock(data={"id": session_id}))
        # Upsert chain (for service.save)
        mock_table.upsert.return_value = mock_table

        with patch("src.routes.quiz.get_async_supabase", new_callable=AsyncMock, return_value=mock_supabase), \
             patch("src.services.store_profile_service.get_async_supabase", new_callable=AsyncMock, return_value=mock_supabase):
            resp = client.post(
                f"/api/quiz/sessions/{session_id}/store-profile",
                json=manual_entry_body,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "completeness" in data
        assert data["source"] == "manual_entry"

    def test_save_skip(
        self, session_id: str, skip_body: Dict[str, Any]
    ) -> None:
        mock_supabase = MagicMock()
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.maybe_single.return_value = mock_table
        mock_table.execute = AsyncMock(return_value=MagicMock(data={"id": session_id}))
        mock_table.upsert.return_value = mock_table

        with patch("src.routes.quiz.get_async_supabase", new_callable=AsyncMock, return_value=mock_supabase), \
             patch("src.services.store_profile_service.get_async_supabase", new_callable=AsyncMock, return_value=mock_supabase):
            resp = client.post(
                f"/api/quiz/sessions/{session_id}/store-profile",
                json=skip_body,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] == "benchmark"
        assert data["completeness"] == 0.0
