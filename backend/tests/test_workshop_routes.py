# backend/tests/test_workshop_routes.py
"""Tests for workshop routes."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime


class TestWorkshopRoutes:
    """Test workshop API endpoints."""

    @pytest.fixture
    def mock_supabase(self):
        """Create mock Supabase client."""
        mock = MagicMock()
        mock.table = MagicMock(return_value=mock)
        mock.select = MagicMock(return_value=mock)
        mock.eq = MagicMock(return_value=mock)
        mock.single = MagicMock(return_value=mock)
        mock.update = MagicMock(return_value=mock)
        mock.execute = AsyncMock()
        return mock

    @pytest.fixture
    def sample_session(self):
        """Sample paid session data."""
        return {
            "id": "test-session-123",
            "status": "paid",
            "company_name": "Test Company",
            "company_profile": {
                "basics": {
                    "name": {"value": "Test Company Inc"},
                    "description": {"value": "A test company"},
                },
                "industry": {
                    "primary_industry": {"value": "technology"},
                },
            },
            "answers": {
                "industry": "technology",
                "role": "CTO",
                "company_size": "11-50",
                "pain_points": ["Manual reporting", "Slow lead follow-up"],
                "current_tools": ["Salesforce", "Slack"],
            },
            "workshop_data": {},
        }

    @pytest.fixture
    def mock_skill_result(self):
        """Mock skill result."""
        return MagicMock(
            success=True,
            data={
                "technical": True,
                "budget_ready": True,
                "decision_maker": False,
            }
        )

    @pytest.mark.asyncio
    async def test_build_confirmation_cards(self):
        """Test confirmation card building."""
        from src.routes.workshop import _build_confirmation_cards

        company_profile = {
            "basics": {
                "name": {"value": "Test Co"},
                "description": {"value": "A test company"},
            },
            "industry": {
                "primary_industry": {"value": "marketing"},
            },
        }
        answers = {
            "pain_points": ["Slow reporting", "Manual data entry"],
            "current_tools": ["HubSpot", "Slack"],
        }

        cards = _build_confirmation_cards(company_profile, answers)

        assert len(cards) > 0
        categories = [c.category for c in cards]
        assert "business" in categories
        assert "pain_points" in categories

    @pytest.mark.asyncio
    async def test_extract_pain_points(self):
        """Test pain point extraction."""
        from src.routes.workshop import _extract_pain_points

        answers = {
            "pain_points": ["Slow reporting", "Manual data entry", "Poor follow-up"],
        }
        company_profile = {}

        pain_points = _extract_pain_points(answers, company_profile)

        assert len(pain_points) == 3
        assert pain_points[0]["id"] == "pain_0"
        assert pain_points[0]["label"] == "Slow reporting"
        assert pain_points[0]["source"] == "quiz"

    @pytest.mark.asyncio
    async def test_get_pain_point_label(self):
        """Test pain point label mapping."""
        from src.routes.workshop import _get_pain_point_label

        # Test known pain points
        assert _get_pain_point_label("reporting") == "Client Reporting"
        assert _get_pain_point_label("lead_followup") == "Lead Follow-up"

        # Test unknown pain points
        assert _get_pain_point_label("custom_issue") == "Custom Issue"

        # Test pain_X format
        assert "Pain Point" in _get_pain_point_label("pain_2")


class TestWorkshopStartEndpoint:
    """Test /api/workshop/start endpoint."""

    @pytest.fixture
    def mock_session_data(self):
        return {
            "id": "session-123",
            "status": "paid",
            "company_profile": {
                "basics": {"name": {"value": "Acme Corp"}},
            },
            "answers": {
                "industry": "marketing-agencies",
                "pain_points": ["Client reporting takes too long"],
            },
            "workshop_data": {},
        }

    @pytest.mark.asyncio
    async def test_start_returns_confirmation_cards(self, mock_session_data):
        """Test that start returns confirmation cards."""
        from src.routes.workshop import _build_confirmation_cards

        cards = _build_confirmation_cards(
            mock_session_data["company_profile"],
            mock_session_data["answers"]
        )

        # Should have at least business and pain_points cards
        categories = [c.category for c in cards]
        assert "pain_points" in categories


class TestWorkshopConfirmEndpoint:
    """Test /api/workshop/confirm endpoint."""

    @pytest.mark.asyncio
    async def test_confirm_request_model(self):
        """Test confirmation request model validation."""
        from src.routes.workshop import WorkshopConfirmRequest

        request = WorkshopConfirmRequest(
            session_id="test-123",
            ratings={
                "business": "accurate",
                "pain_points": "edited",
            },
            corrections=[
                {"field": "pain_points", "original": "Old text", "corrected": "New text"}
            ],
            priority_order=["pain_0", "pain_1"],
        )

        assert request.session_id == "test-123"
        assert request.ratings["business"] == "accurate"
        assert len(request.corrections) == 1
        assert len(request.priority_order) == 2


class TestWorkshopRespondEndpoint:
    """Test /api/workshop/respond endpoint."""

    @pytest.mark.asyncio
    async def test_respond_request_model(self):
        """Test respond request model validation."""
        from src.routes.workshop import WorkshopRespondRequest

        request = WorkshopRespondRequest(
            session_id="test-123",
            message="We spend about 8 hours a week on reports",
            current_pain_point="reporting",
        )

        assert request.session_id == "test-123"
        assert "8 hours" in request.message
        assert request.current_pain_point == "reporting"

    @pytest.mark.asyncio
    async def test_respond_response_model(self):
        """Test respond response model."""
        from src.routes.workshop import WorkshopRespondResponse

        response = WorkshopRespondResponse(
            response="That's helpful! How do you currently create those reports?",
            confidence_update={"messages": 2, "stage": "current_state"},
            should_show_milestone=False,
            estimated_remaining="30-45 min",
        )

        assert "reports" in response.response
        assert response.should_show_milestone is False


class TestMilestoneEndpoint:
    """Test /api/workshop/milestone endpoint."""

    @pytest.mark.asyncio
    async def test_milestone_request_model(self):
        """Test milestone request model validation."""
        from src.routes.workshop import MilestoneRequest

        request = MilestoneRequest(
            session_id="test-123",
            pain_point_id="reporting",
        )

        assert request.session_id == "test-123"
        assert request.pain_point_id == "reporting"

    @pytest.mark.asyncio
    async def test_milestone_feedback_model(self):
        """Test milestone feedback model validation."""
        from src.routes.workshop import MilestoneFeedbackRequest

        request = MilestoneFeedbackRequest(
            session_id="test-123",
            pain_point_id="reporting",
            feedback="looks_good",
            notes="This captures the issue well",
        )

        assert request.feedback == "looks_good"
        assert "captures" in request.notes


class TestWorkshopCompleteEndpoint:
    """Test /api/workshop/complete endpoint."""

    @pytest.mark.asyncio
    async def test_complete_request_model(self):
        """Test complete request model validation."""
        from src.routes.workshop import WorkshopCompleteRequest

        request = WorkshopCompleteRequest(
            session_id="test-123",
            final_answers={
                "stakeholders": ["CEO", "Marketing Lead"],
                "timeline": "Q1 2026",
                "additions": "We also need to consider budget constraints",
            }
        )

        assert request.session_id == "test-123"
        assert len(request.final_answers["stakeholders"]) == 2
        assert request.final_answers["timeline"] == "Q1 2026"
