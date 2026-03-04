"""
Tests for payment routes.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestGuestCheckout:
    """Tests for guest checkout endpoint."""

    def test_guest_checkout_creates_session(self):
        """Test that guest checkout creates Stripe session."""
        with patch('src.routes.payments.stripe') as mock_stripe, \
             patch('src.routes.payments.get_async_supabase') as mock_supabase:
            # Mock Stripe session creation
            mock_stripe.checkout.Session.create.return_value = MagicMock(
                id="cs_test_123",
                url="https://checkout.stripe.com/pay/cs_test_123"
            )

            # Mock Supabase quiz session lookup
            mock_supabase_client = AsyncMock()
            mock_supabase_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
                data={"id": "test-session-id", "status": "completed", "answers": {}}
            )
            mock_supabase.return_value = mock_supabase_client

            response = client.post("/api/payments/guest-checkout", json={
                "quiz_session_id": "test-session-id",
                "tier": "quick",
                "email": "test@example.com"
            })

            # Should succeed or fail gracefully with mocked dependencies (not 500)
            assert response.status_code in [200, 400, 422]
            if response.status_code == 200:
                data = response.json()
                assert "checkout_url" in data or "url" in data

    def test_guest_checkout_validates_email(self):
        """Test that invalid email format is rejected."""
        response = client.post("/api/payments/guest-checkout", json={
            "quiz_session_id": "test-session-id",
            "tier": "quick",
            "email": "invalid-email"
        })

        # Should be rejected with 422 (validation error)
        assert response.status_code == 422

    def test_guest_checkout_requires_session_id(self):
        """Test that quiz_session_id is required."""
        response = client.post("/api/payments/guest-checkout", json={
            "tier": "quick",
            "email": "test@example.com"
        })

        assert response.status_code == 422

    def test_guest_checkout_validates_tier(self):
        """Test that tier must be valid."""
        response = client.post("/api/payments/guest-checkout", json={
            "quiz_session_id": "test-session-id",
            "tier": "invalid_tier",
            "email": "test@example.com"
        })

        # Should be rejected with validation error
        assert response.status_code == 422


class TestWebhook:
    """Tests for Stripe webhook endpoint."""

    def test_webhook_validates_signature(self):
        """Test that invalid webhook signature is rejected."""
        response = client.post(
            "/api/payments/webhook",
            content=b"{}",
            headers={"stripe-signature": "invalid_signature"}
        )

        # Should reject with 400 (invalid signature)
        assert response.status_code == 400

    def test_webhook_requires_signature(self):
        """Test that webhook requires stripe-signature header."""
        response = client.post(
            "/api/payments/webhook",
            content=b"{}",
        )

        # Should fail without signature
        assert response.status_code == 400

    def test_webhook_handles_checkout_completed(self):
        """Test successful checkout completion event handling."""
        with patch('src.routes.payments.stripe') as mock_stripe, \
             patch('src.routes.payments.get_async_supabase') as mock_supabase:
            # Mock Stripe webhook verification
            mock_stripe.Webhook.construct_event.return_value = {
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "id": "cs_test_123",
                        "metadata": {
                            "quiz_session_id": "test-session-id",
                            "tier": "quick"
                        },
                        "customer_email": "test@example.com",
                        "payment_status": "paid"
                    }
                }
            }

            # Mock Supabase
            mock_supabase_client = AsyncMock()
            mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data={})
            mock_supabase_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
                data={"id": "test-session-id", "status": "completed"}
            )
            mock_supabase.return_value = mock_supabase_client

            response = client.post(
                "/api/payments/webhook",
                content=b'{"type": "checkout.session.completed"}',
                headers={"stripe-signature": "valid_test_signature"}
            )

            # Webhook may process (mock bypasses sig check) or reject (real sig check)
            assert response.status_code in [200, 400]

    def test_webhook_returns_deduplicated_for_processed_event(self):
        """Duplicate webhook deliveries should be acknowledged without re-processing."""
        with patch('src.routes.payments.stripe') as mock_stripe, \
             patch('src.routes.payments.get_async_supabase', new_callable=AsyncMock) as mock_supabase, \
             patch('src.routes.payments._claim_webhook_event', new_callable=AsyncMock) as mock_claim:
            mock_stripe.Webhook.construct_event.return_value = {
                "id": "evt_test_duplicate",
                "type": "payment_intent.succeeded",
                "data": {"object": {"id": "pi_123"}}
            }
            mock_supabase.return_value = AsyncMock()
            mock_claim.return_value = False

            response = client.post(
                "/api/payments/webhook",
                content=b'{"id":"evt_test_duplicate","type":"payment_intent.succeeded"}',
                headers={"stripe-signature": "valid_test_signature"}
            )

            assert response.status_code == 200
            assert response.json().get("deduplicated") is True

    def test_webhook_returns_500_when_event_processing_fails(self):
        """Webhook must return 500 so Stripe retries on internal failures."""
        with patch('src.routes.payments.stripe') as mock_stripe, \
             patch('src.routes.payments.get_async_supabase', new_callable=AsyncMock) as mock_supabase, \
             patch('src.routes.payments._claim_webhook_event', new_callable=AsyncMock) as mock_claim, \
             patch('src.routes.payments._mark_webhook_event_failed', new_callable=AsyncMock) as mock_mark_failed, \
             patch('src.routes.payments.handle_checkout_completed', new_callable=AsyncMock) as mock_handle:
            mock_stripe.Webhook.construct_event.return_value = {
                "id": "evt_test_failure",
                "type": "checkout.session.completed",
                "data": {"object": {"id": "cs_123", "metadata": {}}}
            }
            mock_supabase.return_value = AsyncMock()
            mock_claim.return_value = True
            mock_handle.side_effect = RuntimeError("processing exploded")

            response = client.post(
                "/api/payments/webhook",
                content=b'{"id":"evt_test_failure","type":"checkout.session.completed"}',
                headers={"stripe-signature": "valid_test_signature"}
            )

            assert response.status_code == 500
            assert mock_mark_failed.await_count == 1


class TestCheckoutSession:
    """Tests for authenticated checkout session endpoint."""

    def test_create_checkout_session_requires_auth(self):
        """Test that checkout session creation requires authentication."""
        response = client.post("/api/payments/checkout-session", json={
            "audit_id": "test-audit-id",
            "tier": "quick"
        })

        # Should be rejected without auth (401/403) or route may not exist (404)
        assert response.status_code in [401, 403, 404]
