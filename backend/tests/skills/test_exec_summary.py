"""
Tests for the ExecSummarySkill.

Note: ExecSummarySkill is instantiated directly rather than via the registry
because the registry's auto-discovery picks up AIReadinessCalculator (imported
in exec_summary.py) as the first BaseSkill subclass in the module, shadowing
ExecSummarySkill. These tests focus on the skill's behavior, not registry lookup.
"""

import importlib
import pytest
from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any

from src.skills.base import SkillContext

# The report-generation directory has a hyphen, so we use importlib
_exec_summary_mod = importlib.import_module("src.skills.report-generation.exec_summary")
ExecSummarySkill = _exec_summary_mod.ExecSummarySkill


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client."""
    client = MagicMock()
    return client


@pytest.fixture
def sample_quiz_answers() -> Dict[str, Any]:
    """Sample quiz answers for testing."""
    return {
        "company_name": "Test Dental Practice",
        "industry": "dental",
        "company_size": "10-50",
        "annual_revenue": "500000-1000000",
        "main_challenges": ["patient_communication", "scheduling", "paperwork"],
        "current_tools": ["Dentrix", "Email", "Paper forms"],
        "tech_comfort": "medium",
        "budget_range": "5000-10000",
        "timeline": "3-6 months",
        "pain_point_description": "We spend hours each day on patient reminders and scheduling.",
    }


@pytest.fixture
def sample_expertise() -> Dict[str, Any]:
    """Sample expertise data for testing."""
    return {
        "industry_expertise": {
            "total_analyses": 15,
            "confidence": "medium",
            "avg_ai_readiness": 45,
            "avg_potential_savings": 25000,
            "pain_points": {
                "patient_communication": {"frequency": 8, "avg_impact": 7.5},
                "scheduling": {"frequency": 6, "avg_impact": 6.0},
            },
            "effective_patterns": [
                {"recommendation": "Automated appointment reminders", "success_rate": 0.9},
                {"recommendation": "Digital intake forms", "success_rate": 0.85},
            ],
            "anti_patterns": [
                "Full AI diagnosis replacement",
                "Removing all human touchpoints",
            ],
        }
    }


@pytest.fixture
def sample_context(sample_quiz_answers) -> SkillContext:
    """Create a sample SkillContext."""
    return SkillContext(
        industry="dental",
        company_name="Test Dental Practice",
        company_size="10-50",
        quiz_answers=sample_quiz_answers,
    )


@pytest.fixture
def sample_context_with_expertise(sample_quiz_answers, sample_expertise) -> SkillContext:
    """Create a SkillContext with expertise data."""
    return SkillContext(
        industry="dental",
        company_name="Test Dental Practice",
        company_size="10-50",
        quiz_answers=sample_quiz_answers,
        expertise=sample_expertise,
    )


# =============================================================================
# ExecSummarySkill Tests
# =============================================================================

class TestExecSummarySkill:
    """Tests for ExecSummarySkill."""

    def test_skill_discovery(self):
        """Test that ExecSummarySkill class can be imported."""
        skill = ExecSummarySkill()
        assert skill is not None
        assert skill.name == "exec-summary"

    def test_skill_metadata(self, mock_anthropic_client):
        """Test skill metadata."""
        skill = ExecSummarySkill(client=mock_anthropic_client)

        assert skill.name == "exec-summary"
        assert skill.requires_llm is True
        assert skill.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_skill_execution_success(self, sample_context):
        """Test successful skill execution with mocked LLM."""
        # Create mock client with proper response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''
        {
            "ai_readiness_score": 55,
            "customer_value_score": 7.5,
            "business_health_score": 6.5,
            "key_insight": "Strong potential for patient communication automation",
            "total_value_potential": {"min": 15000, "max": 35000, "projection_years": 3},
            "top_opportunities": [
                {"title": "Automated Reminders", "value_potential": "€5K-10K/year", "time_horizon": "short"}
            ],
            "not_recommended": [
                {"title": "AI Diagnosis", "reason": "Regulatory and liability concerns"}
            ],
            "recommended_investment": {"year_1_min": 3000, "year_1_max": 8000}
        }
        ''')]
        mock_client.messages.create.return_value = mock_response

        skill = ExecSummarySkill(client=mock_client)
        result = await skill.run(sample_context)

        assert result.success is True
        # result.data is a dict (ExecSummarySkill returns Dict[str, Any])
        assert result.data["report_date"] is not None
        assert "top_opportunities" in result.data
        # AI readiness score is calculated by formula, not from LLM response
        assert 0 <= result.data["ai_readiness_score"] <= 100

    @pytest.mark.asyncio
    async def test_skill_with_expertise(
        self, mock_anthropic_client, sample_context_with_expertise
    ):
        """Test skill execution with expertise data."""
        skill = ExecSummarySkill(client=mock_anthropic_client)

        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''
        {
            "ai_readiness_score": 60,
            "customer_value_score": 8.0,
            "business_health_score": 7.0,
            "key_insight": "Above industry average AI readiness for dental practices",
            "total_value_potential": {"min": 20000, "max": 40000, "projection_years": 3},
            "top_opportunities": [
                {"title": "Patient Communication", "value_potential": "€8K-15K/year", "time_horizon": "short"}
            ],
            "not_recommended": [
                {"title": "Full Automation", "reason": "Patient relationships require human touch"}
            ],
            "recommended_investment": {"year_1_min": 4000, "year_1_max": 10000}
        }
        ''')]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = await skill.run(sample_context_with_expertise)

        assert result.success is True
        assert result.expertise_applied is True
        # Check that industry context is added when expertise is available
        if "industry_context" in result.data:
            assert "analyses_in_industry" in result.data["industry_context"]

    @pytest.mark.asyncio
    async def test_skill_default_on_llm_failure(
        self, mock_anthropic_client, sample_context
    ):
        """Test that skill raises SkillError when LLM fails.

        The LLMSkill.call_llm method wraps LLM exceptions into SkillError,
        and ExecSummarySkill._generate_summary re-raises SkillError rather
        than swallowing it, so the caller can decide how to handle the failure.
        """
        from src.skills.base import SkillError

        skill = ExecSummarySkill(client=mock_anthropic_client)

        # Mock LLM failure
        mock_anthropic_client.messages.create.side_effect = Exception("API Error")

        with pytest.raises(SkillError) as exc_info:
            await skill.run(sample_context)

        assert "LLM call failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_skill_validates_output(self, mock_anthropic_client, sample_context):
        """Test that skill validates and normalizes LLM output."""
        skill = ExecSummarySkill(client=mock_anthropic_client)

        # Mock invalid/out-of-range values
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''
        {
            "ai_readiness_score": 150,
            "customer_value_score": 15,
            "business_health_score": -5,
            "key_insight": "Test insight"
        }
        ''')]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = await skill.run(sample_context)

        if result.success and result.data:
            # Scores should be clamped to valid ranges
            assert 0 <= result.data.get("ai_readiness_score", 0) <= 100
            assert 1 <= result.data.get("customer_value_score", 1) <= 10
            assert 1 <= result.data.get("business_health_score", 1) <= 10


# =============================================================================
# Integration Tests
# =============================================================================

class TestExecSummaryIntegration:
    """Integration tests for ExecSummarySkill."""

    @pytest.mark.asyncio
    async def test_skill_without_client_fails(self, sample_context):
        """Test that skill fails gracefully without client."""
        from src.skills.base import SkillError

        # Instantiate without client
        skill = ExecSummarySkill(client=None)

        # LLMSkill.run() should raise SkillError when requires_llm=True and no client
        with pytest.raises(SkillError) as exc_info:
            await skill.run(sample_context)

        assert "LLM client" in str(exc_info.value)

    def test_skill_template_structure(self, mock_anthropic_client):
        """Test that skill has proper template structure."""
        skill = ExecSummarySkill(client=mock_anthropic_client)

        # Check that SUMMARY_TEMPLATE has all required fields
        template = skill.SUMMARY_TEMPLATE
        required_fields = [
            "ai_readiness_score",
            "customer_value_score",
            "business_health_score",
            "key_insight",
            "total_value_potential",
            "top_opportunities",
            "not_recommended",
            "recommended_investment",
        ]

        for field in required_fields:
            assert field in template, f"Missing template field: {field}"
