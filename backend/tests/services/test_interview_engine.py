"""Tests for InterviewEngine."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.services.interview_engine import InterviewEngine, InterviewState


class TestInterviewEngine:
    """Test the interview engine orchestration."""

    def setup_method(self):
        self.mock_client = MagicMock()
        self.engine = InterviewEngine(anthropic_client=self.mock_client)

    def test_initial_state(self):
        """Should start at anchor 1 (problem)."""
        state = InterviewState(industry="plumbing", company_name="Test Co")
        assert state.current_anchor == 1
        assert state.questions_asked == 0
        assert state.phase == "anchor"

    def test_get_anchor_question(self):
        """Should return correct anchor question."""
        q1 = self.engine.get_anchor_question(1)
        assert "time or money" in q1.lower()

        q2 = self.engine.get_anchor_question(2)
        assert "step by step" in q2.lower()

        q3 = self.engine.get_anchor_question(3)
        assert "90 days" in q3.lower()

    @pytest.mark.asyncio
    async def test_process_answer_detects_signals(self):
        """Should detect signals in answer."""
        state = InterviewState(industry="plumbing", company_name="Test")

        result = await self.engine.process_answer(
            state=state,
            answer="Scheduling is a nightmare, we do it all by hand"
        )

        assert "pain_intensity" in result.signals_detected or "manual_work" in result.signals_detected

    @pytest.mark.asyncio
    async def test_decides_follow_up_or_next_anchor(self):
        """Should decide whether to follow up or move to next anchor."""
        state = InterviewState(industry="dental", company_name="Test")

        # Short vague answer should trigger follow-up
        result = await self.engine.process_answer(
            state=state,
            answer="It's okay"
        )
        assert result.next_question_type == "follow_up"

    @pytest.mark.asyncio
    async def test_moves_to_next_anchor_on_rich_answer(self):
        """Should move to next anchor on detailed answer."""
        state = InterviewState(industry="plumbing", company_name="Test")
        state.current_anchor = 1
        state.follow_ups_for_current_anchor = 1  # Already asked one follow-up

        # Rich detailed answer
        result = await self.engine.process_answer(
            state=state,
            answer="We spend about 20 hours a week on scheduling. My wife handles calls, writes them on paper, then enters them in Google Calendar, then texts the crew. About 3 jobs a week get messed up."
        )

        # Should move to anchor 2 (process)
        assert result.next_question_type == "anchor"
        assert "step by step" in result.next_question.lower()

    @pytest.mark.asyncio
    async def test_completes_after_anchor_3(self):
        """Should complete interview after anchor 3."""
        state = InterviewState(industry="dental", company_name="Test")
        state.current_anchor = 3
        state.questions_asked = 6

        result = await self.engine.process_answer(
            state=state,
            answer="Probably worth $50K a year if we fixed it"
        )

        assert result.interview_complete == True
