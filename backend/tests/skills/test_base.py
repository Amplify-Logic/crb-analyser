"""
Tests for the skills base classes and models.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Dict, Any

from src.skills.base import (
    BaseSkill,
    SyncSkill,
    LLMSkill,
    SkillContext,
    SkillResult,
    SkillError,
)


# =============================================================================
# SkillContext Tests
# =============================================================================

class TestSkillContext:
    """Tests for SkillContext model."""

    def test_minimal_context(self):
        """Test creating context with just industry."""
        context = SkillContext(industry="dental")
        assert context.industry == "dental"
        assert context.company_name is None
        assert context.quiz_answers is None
        assert context.expertise is None
        assert context.metadata == {}

    def test_full_context(self):
        """Test creating context with all fields."""
        context = SkillContext(
            industry="dental",
            company_name="Test Dental Practice",
            company_size="10-50",
            quiz_answers={"q1": "answer1"},
            interview_data={"messages": []},
            expertise={"industry_expertise": {"avg_ai_readiness": 55}},
            knowledge={"processes": []},
            report_data={"findings": []},
            metadata={"custom_field": "value"},
        )
        assert context.industry == "dental"
        assert context.company_name == "Test Dental Practice"
        assert context.quiz_answers == {"q1": "answer1"}
        assert context.expertise["industry_expertise"]["avg_ai_readiness"] == 55


class TestSkillResult:
    """Tests for SkillResult model."""

    def test_success_result(self):
        """Test successful skill result."""
        result = SkillResult(
            success=True,
            data={"summary": "test"},
            skill_name="test-skill",
            execution_time_ms=123.45,
        )
        assert result.success is True
        assert result.data == {"summary": "test"}
        assert result.skill_name == "test-skill"
        assert result.execution_time_ms == 123.45
        assert result.warnings == []

    def test_failed_result(self):
        """Test failed skill result."""
        result = SkillResult(
            success=False,
            data=None,
            skill_name="test-skill",
            execution_time_ms=50.0,
            warnings=["Something went wrong"],
        )
        assert result.success is False
        assert result.data is None
        assert "Something went wrong" in result.warnings


class TestSkillError:
    """Tests for SkillError exception."""

    def test_recoverable_error(self):
        """Test recoverable skill error."""
        error = SkillError("test-skill", "Something failed", recoverable=True)
        assert error.skill_name == "test-skill"
        assert error.message == "Something failed"
        assert error.recoverable is True
        assert "[test-skill]" in str(error)

    def test_non_recoverable_error(self):
        """Test non-recoverable skill error."""
        error = SkillError("test-skill", "Fatal error", recoverable=False)
        assert error.recoverable is False


# =============================================================================
# BaseSkill Tests
# =============================================================================

class TestableSkill(BaseSkill[Dict[str, Any]]):
    """Concrete implementation for testing BaseSkill."""

    name = "testable-skill"
    description = "A skill for testing"
    version = "1.0.0"

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        return {"result": "success", "industry": context.industry}


class FailingSkill(BaseSkill[Dict[str, Any]]):
    """Skill that always fails for testing."""

    name = "failing-skill"

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        raise ValueError("Intentional failure")


class TestBaseSkill:
    """Tests for BaseSkill class."""

    @pytest.mark.asyncio
    async def test_skill_execution(self):
        """Test basic skill execution."""
        skill = TestableSkill()
        context = SkillContext(industry="dental")

        result = await skill.run(context)

        assert result.success is True
        assert result.data["result"] == "success"
        assert result.data["industry"] == "dental"
        assert result.skill_name == "testable-skill"
        assert result.execution_time_ms > 0

    @pytest.mark.asyncio
    async def test_skill_failure_handling(self):
        """Test that skill failures are handled gracefully."""
        skill = FailingSkill()
        context = SkillContext(industry="dental")

        result = await skill.run(context)

        assert result.success is False
        assert result.data is None
        assert len(result.warnings) > 0
        assert "Intentional failure" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_expertise_warning(self):
        """Test warning when expertise is required but missing."""

        class ExpertiseRequiredSkill(TestableSkill):
            requires_expertise = True

        skill = ExpertiseRequiredSkill()
        context = SkillContext(industry="dental")  # No expertise

        result = await skill.run(context)

        assert result.success is True
        assert any("expertise" in w.lower() for w in result.warnings)

    @pytest.mark.asyncio
    async def test_expertise_applied_flag(self):
        """Test expertise_applied flag in result."""
        skill = TestableSkill()

        # Without expertise
        context_no_exp = SkillContext(industry="dental")
        result_no_exp = await skill.run(context_no_exp)
        assert result_no_exp.expertise_applied is False

        # With expertise
        context_with_exp = SkillContext(
            industry="dental",
            expertise={"industry_expertise": {}}
        )
        result_with_exp = await skill.run(context_with_exp)
        assert result_with_exp.expertise_applied is True

    def test_get_expertise_value(self):
        """Test helper method for getting expertise values."""
        skill = TestableSkill()
        context = SkillContext(
            industry="dental",
            expertise={
                "industry_expertise": {
                    "avg_ai_readiness": 55,
                    "nested": {"value": "test"}
                }
            }
        )

        # Test dot notation
        assert skill.get_expertise_value(context, "industry_expertise.avg_ai_readiness") == 55
        assert skill.get_expertise_value(context, "industry_expertise.nested.value") == "test"

        # Test missing key with default
        assert skill.get_expertise_value(context, "missing.key", default=100) == 100

        # Test with no expertise
        context_no_exp = SkillContext(industry="dental")
        assert skill.get_expertise_value(context_no_exp, "any.key", default="fallback") == "fallback"

    def test_validate_context(self):
        """Test context validation helper."""
        skill = TestableSkill()
        context = SkillContext(
            industry="dental",
            company_name="Test Corp"
        )

        # Valid context
        skill.validate_context(context, ["industry", "company_name"])

        # Invalid context - missing required field
        with pytest.raises(SkillError) as exc_info:
            skill.validate_context(context, ["industry", "quiz_answers"])

        assert "quiz_answers" in str(exc_info.value)
        assert exc_info.value.recoverable is False

    def test_skill_repr(self):
        """Test skill string representation."""
        skill = TestableSkill()
        repr_str = repr(skill)
        assert "TestableSkill" in repr_str
        assert "testable-skill" in repr_str
        assert "1.0.0" in repr_str


# =============================================================================
# SyncSkill Tests
# =============================================================================

class TestableSyncSkill(SyncSkill[str]):
    """Concrete implementation for testing SyncSkill."""

    name = "sync-skill"

    def execute_sync(self, context: SkillContext) -> str:
        return f"Processed: {context.industry}"


class TestSyncSkill:
    """Tests for SyncSkill class."""

    @pytest.mark.asyncio
    async def test_sync_skill_execution(self):
        """Test that sync skills work via async interface."""
        skill = TestableSyncSkill()
        context = SkillContext(industry="dental")

        result = await skill.run(context)

        assert result.success is True
        assert result.data == "Processed: dental"


# =============================================================================
# LLMSkill Tests
# =============================================================================

class TestableLLMSkill(LLMSkill[Dict[str, Any]]):
    """Concrete implementation for testing LLMSkill."""

    name = "llm-skill"

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        response = await self.call_llm_json("Generate test data")
        return response


class TestLLMSkill:
    """Tests for LLMSkill class."""

    @pytest.mark.asyncio
    async def test_llm_skill_requires_client(self):
        """Test that LLM skills fail without client."""
        skill = TestableLLMSkill()  # No client
        context = SkillContext(industry="dental")

        with pytest.raises(SkillError) as exc_info:
            await skill.run(context)

        assert "LLM client" in str(exc_info.value)
        assert exc_info.value.recoverable is False

    @pytest.mark.asyncio
    async def test_llm_call(self):
        """Test LLM call helper."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test response")]
        mock_client.messages.create.return_value = mock_response

        skill = TestableLLMSkill(client=mock_client)

        response = await skill.call_llm("Test prompt")

        assert response == "Test response"
        mock_client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_llm_call_json(self):
        """Test LLM JSON call helper."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"key": "value"}')]
        mock_client.messages.create.return_value = mock_response

        skill = TestableLLMSkill(client=mock_client)

        response = await skill.call_llm_json("Generate JSON")

        assert response == {"key": "value"}

    @pytest.mark.asyncio
    async def test_llm_call_json_with_markdown(self):
        """Test LLM JSON call with markdown code blocks."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='```json\n{"key": "value"}\n```')]
        mock_client.messages.create.return_value = mock_response

        skill = TestableLLMSkill(client=mock_client)

        response = await skill.call_llm_json("Generate JSON")

        assert response == {"key": "value"}

    @pytest.mark.asyncio
    async def test_llm_call_json_parse_error(self):
        """Test LLM JSON call with invalid JSON."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="not valid json")]
        mock_client.messages.create.return_value = mock_response

        skill = TestableLLMSkill(client=mock_client)

        with pytest.raises(SkillError) as exc_info:
            await skill.call_llm_json("Generate JSON")

        assert "JSON" in str(exc_info.value)
        assert exc_info.value.recoverable is True
