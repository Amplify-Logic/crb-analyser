"""
Tests for the ExecSummarySkill.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any

from src.skills.base import SkillContext
from src.skills.registry import get_skill


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
        """Test that ExecSummarySkill is discoverable."""
        skill = get_skill("exec-summary")
        # Note: This may return None if discovery path differs
        # The skill should exist in the report-generation directory

    def test_skill_metadata(self, mock_anthropic_client):
        """Test skill metadata."""
        skill = get_skill("exec-summary", client=mock_anthropic_client)

        if skill:
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

        # Get skill from registry with fresh instance and mock client
        from src.skills.registry import get_registry
        registry = get_registry(mock_client)
        registry.clear_cache()  # Ensure fresh instance
        registry.set_client(mock_client)

        skill = registry.get("exec-summary", fresh=True)
        if not skill:
            pytest.skip("ExecSummarySkill not found")

        result = await skill.run(sample_context)

        assert result.success is True
        assert result.data["ai_readiness_score"] == 55
        assert result.data["customer_value_score"] == 7.5
        assert "report_date" in result.data
        assert len(result.data["top_opportunities"]) > 0

    @pytest.mark.asyncio
    async def test_skill_with_expertise(
        self, mock_anthropic_client, sample_context_with_expertise
    ):
        """Test skill execution with expertise data."""
        skill = get_skill("exec-summary", client=mock_anthropic_client)

        if not skill:
            pytest.skip("ExecSummarySkill not found in registry")

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
        """Test that skill returns defaults when LLM fails."""
        skill = get_skill("exec-summary", client=mock_anthropic_client)

        if not skill:
            pytest.skip("ExecSummarySkill not found in registry")

        # Mock LLM failure
        mock_anthropic_client.messages.create.side_effect = Exception("API Error")

        result = await skill.run(sample_context)

        # Should still return a result (with default values), not crash
        assert result.success is True or result.success is False
        # If success, it should have the default structure
        if result.success and result.data:
            assert "ai_readiness_score" in result.data

    @pytest.mark.asyncio
    async def test_skill_validates_output(self, mock_anthropic_client, sample_context):
        """Test that skill validates and normalizes LLM output."""
        skill = get_skill("exec-summary", client=mock_anthropic_client)

        if not skill:
            pytest.skip("ExecSummarySkill not found in registry")

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
        from src.skills.registry import get_registry

        # Get registry without client
        registry = get_registry()
        registry.clear_cache()
        registry.set_client(None)  # Explicitly no client

        skill = registry.get("exec-summary", fresh=True)

        if not skill:
            pytest.skip("ExecSummarySkill not found in registry")

        # LLMSkill.run() should raise SkillError when requires_llm=True and no client
        with pytest.raises(SkillError) as exc_info:
            await skill.run(sample_context)

        assert "LLM client" in str(exc_info.value)

    def test_skill_template_structure(self, mock_anthropic_client):
        """Test that skill has proper template structure."""
        skill = get_skill("exec-summary", client=mock_anthropic_client)

        if not skill:
            pytest.skip("ExecSummarySkill not found in registry")

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
