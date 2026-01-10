"""Tests for /api/interview/process-answer endpoint."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


class TestProcessAnswerEndpoint:
    """Test the process-answer endpoint."""

    def test_process_answer_success(self):
        """Should process answer and return next question."""
        # This tests the actual endpoint with the real engine
        # but uses a vague answer to avoid needing LLM
        response = client.post(
            "/api/interview/process-answer",
            json={
                "session_id": "test-123",
                "answer_text": "It's okay",
                "current_anchor": 1,
                "industry": "plumbing",
                "company_name": "Test Plumbing"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "acknowledgment" in data
        assert "next_question" in data
        assert "signals_detected" in data
        assert "progress" in data
        # Vague answer should trigger follow-up
        assert data["next_question_type"] == "follow_up"

    def test_process_answer_missing_fields(self):
        """Should return 422 for missing required fields."""
        response = client.post(
            "/api/interview/process-answer",
            json={"session_id": "test-123"}
        )
        assert response.status_code == 422

    def test_first_question_endpoint(self):
        """Should return the first question."""
        response = client.get(
            "/api/interview/first-question",
            params={"industry": "dental", "company_name": "Test Dental"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "question" in data
        assert "time or money" in data["question"].lower()
        assert data["anchor"] == 1
        assert data["topic"] == "Problem"
