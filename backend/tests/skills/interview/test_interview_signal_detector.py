"""Tests for InterviewSignalDetectorSkill."""

import pytest
from src.skills.interview.interview_signal_detector import InterviewSignalDetectorSkill
from src.skills.base import SkillContext


class TestInterviewSignalDetector:
    """Test signal detection from interview answers."""

    def setup_method(self):
        self.skill = InterviewSignalDetectorSkill()

    @pytest.mark.asyncio
    async def test_detects_pain_intensity(self):
        """Should detect pain intensity signals."""
        context = SkillContext(
            industry="plumbing",
            metadata={"answer": "Scheduling is a nightmare, we're constantly double-booked"}
        )
        result = await self.skill.run(context)

        assert result.success
        assert "pain_intensity" in result.data["signals_detected"]

    @pytest.mark.asyncio
    async def test_detects_manual_work(self):
        """Should detect manual work signals."""
        context = SkillContext(
            industry="dental",
            metadata={"answer": "We track everything in spreadsheets and copy paste into the billing system"}
        )
        result = await self.skill.run(context)

        assert result.success
        assert "manual_work" in result.data["signals_detected"]

    @pytest.mark.asyncio
    async def test_detects_vague_answer(self):
        """Should detect vague/short answers."""
        context = SkillContext(
            industry="construction",
            metadata={"answer": "It's fine"}
        )
        result = await self.skill.run(context)

        assert result.success
        assert "vague_answer" in result.data["signals_detected"]

    @pytest.mark.asyncio
    async def test_returns_follow_up_suggestions(self):
        """Should return follow-up question suggestions."""
        context = SkillContext(
            industry="plumbing",
            metadata={"answer": "We're drowning in paperwork"}
        )
        result = await self.skill.run(context)

        assert result.success
        assert len(result.data["suggested_follow_ups"]) > 0

    @pytest.mark.asyncio
    async def test_multiple_signals(self):
        """Should detect multiple signals in one answer."""
        context = SkillContext(
            industry="dental",
            metadata={"answer": "The billing is a nightmare and we do it all in spreadsheets manually"}
        )
        result = await self.skill.run(context)

        assert result.success
        signals = result.data["signals_detected"]
        assert "pain_intensity" in signals
        assert "manual_work" in signals
