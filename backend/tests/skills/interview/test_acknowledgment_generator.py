"""Tests for AcknowledgmentGeneratorSkill."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from src.skills.interview.acknowledgment_generator import AcknowledgmentGeneratorSkill
from src.skills.base import SkillContext


class TestAcknowledgmentGenerator:
    """Test warm expert acknowledgment generation."""

    def setup_method(self):
        # Create mock Anthropic client
        self.mock_client = MagicMock()
        self.skill = AcknowledgmentGeneratorSkill(client=self.mock_client)

    @pytest.mark.asyncio
    async def test_generates_acknowledgment(self):
        """Should generate acknowledgment using LLM."""
        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Scheduling in trades is brutal - one emergency throws off everything.")]
        self.mock_client.messages.create.return_value = mock_response

        context = SkillContext(
            industry="plumbing",
            company_name="Mount Eden Plumbing",
            metadata={
                "answer": "Scheduling is chaos, we're always double-booked",
                "signals_detected": ["pain_intensity"],
                "next_question": "Walk me through how that works today?"
            }
        )
        result = await self.skill.run(context)

        assert result.success
        assert "acknowledgment" in result.data
        assert len(result.data["acknowledgment"]) > 0

    @pytest.mark.asyncio
    async def test_includes_industry_context(self):
        """Should include industry in the prompt."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Insurance billing is the hidden time-killer.")]
        self.mock_client.messages.create.return_value = mock_response

        context = SkillContext(
            industry="dental",
            company_name="Smile Dental",
            metadata={
                "answer": "Insurance claims take forever",
                "signals_detected": ["pain_intensity"],
                "next_question": "How many hours a week?"
            }
        )
        await self.skill.run(context)

        # Verify the prompt included the industry
        call_args = self.mock_client.messages.create.call_args
        prompt = call_args.kwargs["messages"][0]["content"]
        assert "dental" in prompt.lower()

    @pytest.mark.asyncio
    async def test_fallback_on_error(self):
        """Should return fallback acknowledgment on LLM error."""
        self.mock_client.messages.create.side_effect = Exception("API Error")

        context = SkillContext(
            industry="construction",
            metadata={
                "answer": "Quotes take too long",
                "signals_detected": ["pain_intensity"],
                "next_question": "Walk me through the process?"
            }
        )
        result = await self.skill.run(context)

        assert result.success
        assert "acknowledgment" in result.data
        # Should have a fallback acknowledgment
        assert "construction" in result.data["acknowledgment"].lower() or len(result.data["acknowledgment"]) > 0
