# backend/tests/test_workshop_skills.py
"""Tests for workshop skills."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from src.skills import SkillContext
from src.skills.workshop.signal_detector import AdaptiveSignalDetectorSkill
from src.skills.workshop.question_skill import WorkshopQuestionSkill
from src.skills.workshop.milestone_skill import MilestoneSynthesisSkill


class TestAdaptiveSignalDetectorSkill:
    """Test the signal detection skill."""

    @pytest.fixture
    def skill(self):
        return AdaptiveSignalDetectorSkill()

    @pytest.fixture
    def technical_context(self):
        return SkillContext(
            industry="technology",
            metadata={
                "role": "CTO",
                "company_size": "11-50",
                "budget_answer": "15000-50000",
                "quiz_answers": {
                    "current_tools": ["Salesforce", "custom API integrations"],
                },
            }
        )

    @pytest.fixture
    def non_technical_context(self):
        return SkillContext(
            industry="dental",
            metadata={
                "role": "Practice Owner",
                "company_size": "1-10",
                "budget_answer": "5000-15000",
                "quiz_answers": {
                    "current_tools": ["Dentrix", "Google Calendar"],
                },
            }
        )

    @pytest.mark.asyncio
    async def test_detect_technical_user(self, skill, technical_context):
        result = await skill.run(technical_context)
        assert result.success is True
        assert result.data["technical"] is True
        assert result.data["budget_ready"] is True

    @pytest.mark.asyncio
    async def test_detect_non_technical_decision_maker(self, skill, non_technical_context):
        result = await skill.run(non_technical_context)
        assert result.success is True
        assert result.data["technical"] is False
        assert result.data["decision_maker"] is True

    @pytest.mark.asyncio
    async def test_detection_sources_included(self, skill, technical_context):
        result = await skill.run(technical_context)
        assert result.success is True
        assert "detection_sources" in result.data
        assert result.data["detection_sources"]["role"] == "CTO"

    @pytest.mark.asyncio
    async def test_empty_metadata(self, skill):
        context = SkillContext(industry="general", metadata={})
        result = await skill.run(context)
        assert result.success is True
        assert result.data["technical"] is False
        assert result.data["budget_ready"] is False
        assert result.data["decision_maker"] is False


class TestWorkshopQuestionSkill:
    """Test the adaptive question generation skill."""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client.messages.create = MagicMock(return_value=MagicMock(
            content=[MagicMock(text='"Walk me through how client reporting works today - who handles it and how long does it typically take?"')]
        ))
        return client

    @pytest.fixture
    def skill(self, mock_client):
        return WorkshopQuestionSkill(client=mock_client)

    @pytest.fixture
    def deep_dive_context(self):
        return SkillContext(
            industry="marketing-agencies",
            metadata={
                "phase": "deepdive",
                "current_pain_point": "client_reporting",
                "pain_point_label": "Client Reporting",
                "conversation_stage": "current_state",
                "signals": {"technical": False, "budget_ready": True, "decision_maker": True},
                "previous_messages": [],
                "company_name": "Acme Agency",
            }
        )

    @pytest.mark.asyncio
    async def test_generates_contextual_question(self, skill, deep_dive_context):
        result = await skill.run(deep_dive_context)
        assert result.success is True
        assert "question" in result.data
        assert len(result.data["question"]) > 20

    @pytest.mark.asyncio
    async def test_returns_next_stage(self, skill, deep_dive_context):
        result = await skill.run(deep_dive_context)
        assert result.success is True
        assert "next_stage" in result.data
        assert result.data["next_stage"] == "failed_attempts"

    @pytest.mark.asyncio
    async def test_includes_pain_point(self, skill, deep_dive_context):
        result = await skill.run(deep_dive_context)
        assert result.success is True
        assert result.data["pain_point"] == "client_reporting"

    @pytest.mark.asyncio
    async def test_handles_last_stage(self, skill, mock_client):
        context = SkillContext(
            industry="marketing-agencies",
            metadata={
                "phase": "deepdive",
                "current_pain_point": "client_reporting",
                "pain_point_label": "Client Reporting",
                "conversation_stage": "stakeholders",
                "signals": {},
                "previous_messages": [],
                "company_name": "Acme Agency",
            }
        )
        result = await skill.run(context)
        assert result.success is True
        assert result.data["next_stage"] == "complete"


class TestMilestoneSynthesisSkill:
    """Test milestone synthesis skill."""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        # Mock JSON response
        client.messages.create = MagicMock(return_value=MagicMock(
            content=[MagicMock(text='''{
                "finding": {
                    "title": "Client Reporting Automation Opportunity",
                    "summary": "Automate weekly client reports to save 8 hours per week",
                    "current_process": "Manual data gathering from 4 sources",
                    "pain_severity": "high",
                    "recommendation": "Implement automated reporting with Databox"
                },
                "roi": {
                    "hours_per_week": 8,
                    "hourly_rate": 75,
                    "annual_cost": 31200,
                    "potential_savings": 23400,
                    "savings_percentage": 75,
                    "calculation_notes": "Based on 8 hrs/week at $75/hr"
                },
                "vendors": [
                    {"name": "Databox", "fit": "high", "reason": "Integrates with HubSpot"},
                    {"name": "Whatagraph", "fit": "medium", "reason": "Good for agencies"}
                ],
                "confidence": 0.82,
                "data_gaps": ["Team size handling reports"]
            }''')]
        ))
        return client

    @pytest.fixture
    def skill(self, mock_client):
        return MilestoneSynthesisSkill(client=mock_client)

    @pytest.fixture
    def synthesis_context(self):
        return SkillContext(
            industry="marketing-agencies",
            metadata={
                "pain_point_id": "reporting",
                "pain_point_label": "Client Reporting",
                "transcript": [
                    {"role": "assistant", "content": "How does reporting work today?"},
                    {"role": "user", "content": "We spend about 8 hours a week gathering data from HubSpot, GA4, and social platforms, then manually creating reports in Google Slides."},
                    {"role": "assistant", "content": "What have you tried to fix this?"},
                    {"role": "user", "content": "We tried Supermetrics but it was too complex for the team."},
                ],
                "company_name": "Acme Agency",
                "tools_mentioned": ["HubSpot", "GA4", "Google Slides"],
            }
        )

    @pytest.mark.asyncio
    async def test_generates_finding(self, skill, synthesis_context):
        result = await skill.run(synthesis_context)
        assert result.success is True
        assert "finding" in result.data
        assert "title" in result.data["finding"]

    @pytest.mark.asyncio
    async def test_calculates_roi(self, skill, synthesis_context):
        result = await skill.run(synthesis_context)
        assert result.success is True
        assert "roi" in result.data
        assert "potential_savings" in result.data["roi"]

    @pytest.mark.asyncio
    async def test_includes_vendors(self, skill, synthesis_context, mocker):
        # Mock vendor service to return test vendors
        mock_vendors = [
            {
                "name": "Databox",
                "slug": "databox",
                "_tier": 1,
                "best_for": ["Automated reporting"],
                "pricing": {"free_tier": True},
            },
            {
                "name": "Whatagraph",
                "slug": "whatagraph",
                "_tier": 2,
                "best_for": ["Agency reporting"],
                "pricing": {"starting_price": 199, "currency": "USD"},
            },
        ]
        mocker.patch(
            "src.skills.workshop.milestone_skill.vendor_service.get_vendors_with_tier_boost",
            new_callable=AsyncMock,
            return_value=mock_vendors,
        )

        result = await skill.run(synthesis_context)
        assert result.success is True
        assert "vendors" in result.data
        assert len(result.data["vendors"]) > 0
        # Verify vendor data structure
        assert result.data["vendors"][0]["name"] == "Databox"
        assert result.data["vendors"][0]["fit"] == "high"  # Tier 1 = high fit

    @pytest.mark.asyncio
    async def test_includes_pain_point_id(self, skill, synthesis_context):
        result = await skill.run(synthesis_context)
        assert result.success is True
        assert result.data["pain_point_id"] == "reporting"

    @pytest.mark.asyncio
    async def test_includes_confidence(self, skill, synthesis_context):
        result = await skill.run(synthesis_context)
        assert result.success is True
        assert "confidence" in result.data
        assert 0.0 <= result.data["confidence"] <= 1.0
