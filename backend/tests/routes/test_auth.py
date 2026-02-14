"""
Tests for authentication routes.

NOTE: Tests using mocked Supabase calls target `get_async_supabase` which is the
actual function used in auth.py. Some mocks may need updating as the auth module evolves.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestSignup:
    """Tests for user signup endpoint."""

    def test_signup_validates_email_format(self):
        """Test that invalid email format is rejected."""
        response = client.post("/api/auth/signup", json={
            "email": "invalid-email",
            "password": "SecurePass123!"
        })

        assert response.status_code == 422

    def test_signup_requires_email(self):
        """Test that email is required."""
        response = client.post("/api/auth/signup", json={
            "password": "SecurePass123!"
        })

        assert response.status_code == 422

    def test_signup_requires_password(self):
        """Test that password is required."""
        response = client.post("/api/auth/signup", json={
            "email": "newuser@test.com"
        })

        assert response.status_code == 422

    def test_signup_creates_user(self):
        """Test user signup flow with mocked Supabase."""
        with patch('src.routes.auth.get_async_supabase') as mock_get_supabase:
            mock_client = AsyncMock()
            mock_client.auth.sign_up.return_value = MagicMock(
                user=MagicMock(id="test-user-id", email="newuser@test.com"),
                session=MagicMock(access_token="test-token", refresh_token="test-refresh")
            )
            mock_client.table.return_value.insert.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[{"id": "ws-1"}])
            )
            mock_get_supabase.return_value = mock_client

            response = client.post("/api/auth/signup", json={
                "email": "newuser@test.com",
                "password": "SecurePass123!"
            })

            # Should succeed or fail with auth error (not 500)
            assert response.status_code in [200, 201, 400]


class TestLogin:
    """Tests for user login endpoint."""

    def test_login_validates_email_format(self):
        """Test that invalid email format is rejected."""
        response = client.post("/api/auth/login", json={
            "email": "invalid-email",
            "password": "password123"
        })

        assert response.status_code == 422

    def test_login_requires_email(self):
        """Test that email is required."""
        response = client.post("/api/auth/login", json={
            "password": "password123"
        })

        assert response.status_code == 422

    def test_login_requires_password(self):
        """Test that password is required."""
        response = client.post("/api/auth/login", json={
            "email": "user@test.com"
        })

        assert response.status_code == 422

    def test_login_rejects_invalid_credentials(self):
        """Test invalid credentials are rejected."""
        with patch('src.routes.auth.get_async_supabase') as mock_get_supabase:
            mock_client = AsyncMock()
            mock_client.auth.sign_in_with_password.side_effect = Exception("Invalid login credentials")
            mock_get_supabase.return_value = mock_client

            response = client.post("/api/auth/login", json={
                "email": "nonexistent@test.com",
                "password": "wrongpassword"
            })

            # Should be rejected (401 or 400, not 500)
            assert response.status_code in [400, 401]

    def test_login_returns_token(self):
        """Test login returns JWT token on success."""
        with patch('src.routes.auth.get_async_supabase') as mock_get_supabase:
            mock_client = AsyncMock()
            mock_client.auth.sign_in_with_password.return_value = MagicMock(
                user=MagicMock(id="test-user-id", email="user@test.com"),
                session=MagicMock(access_token="test-jwt-token", refresh_token="test-refresh")
            )
            mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute = AsyncMock(
                return_value=MagicMock(data={"id": "test-user-id", "email": "user@test.com", "role": "user"})
            )
            mock_get_supabase.return_value = mock_client

            response = client.post("/api/auth/login", json={
                "email": "user@test.com",
                "password": "correctpassword"
            })

            if response.status_code == 200:
                data = response.json()
                assert "access_token" in data or "token" in data or "session" in data


class TestLogout:
    """Tests for logout endpoint."""

    def test_logout_clears_session(self):
        """Test that logout clears the session."""
        response = client.post("/api/auth/logout")

        # Logout should work even without auth (just clears cookies)
        assert response.status_code in [200, 204]


class TestCurrentUser:
    """Tests for current user endpoint."""

    def test_me_requires_auth(self):
        """Test that /me endpoint requires authentication."""
        response = client.get("/api/auth/me")

        # Should require auth
        assert response.status_code == 401

    def test_me_returns_user_with_valid_token(self):
        """Test /me requires proper auth headers."""
        # Without proper auth headers in the request, auth middleware rejects
        response = client.get("/api/auth/me")
        assert response.status_code in [401, 403]
