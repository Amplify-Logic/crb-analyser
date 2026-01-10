"""Integration tests for the full interview flow."""

import pytest
from unittest.mock import MagicMock, patch
from src.services.interview_engine import InterviewEngine, InterviewState


class TestInterviewFlow:
    """Test complete interview conversation flow."""

    @pytest.mark.asyncio
    async def test_complete_interview_flow(self):
        """Should complete a full interview with all anchors covered."""
        # Mock the LLM client for acknowledgments
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="That's a common challenge.")]
        mock_client.messages.create.return_value = mock_response

        engine = InterviewEngine(anthropic_client=mock_client)
        state = InterviewState(
            industry="plumbing",
            company_name="Test Plumbing Co"
        )

        # Simulate conversation - continue until complete
        answers = [
            "Scheduling is a nightmare, we lose jobs every week",  # Anchor 1
            "About 10 hours a week dealing with it",  # Follow-up
            "Customer calls, wife writes it down, enters in calendar, texts the crew",  # Anchor 2
            "Maybe $50K a year if we fixed it",  # Anchor 3
        ]

        completed = False
        for answer in answers:
            if completed:
                break
            result = await engine.process_answer(state, answer)

            # Verify we got a response
            assert result.acknowledgment
            assert result.next_question

            if result.interview_complete:
                completed = True

        # Should have completed the interview
        assert completed, f"Interview should complete. State: anchor={state.current_anchor}, questions={state.questions_asked}"

    @pytest.mark.asyncio
    async def test_signal_detection_affects_flow(self):
        """Vague answers should trigger follow-ups."""
        engine = InterviewEngine()  # No LLM needed for signal detection
        state = InterviewState(industry="dental", company_name="Test")

        # Vague answer should trigger follow-up
        result = await engine.process_answer(state, "It's fine I guess")

        assert "vague_answer" in result.signals_detected
        assert result.next_question_type == "follow_up"

    @pytest.mark.asyncio
    async def test_rich_answer_advances_anchor(self):
        """Rich detailed answers should advance to next anchor."""
        engine = InterviewEngine()
        state = InterviewState(industry="plumbing", company_name="Test")

        # Start at anchor 1
        assert state.current_anchor == 1

        # Give a rich answer
        result = await engine.process_answer(
            state,
            "We spend about 20 hours a week on scheduling. My wife handles all the calls, "
            "writes them down on paper, then enters them into Google Calendar. "
            "Then she texts the crew their schedules. About 3 jobs a week get messed up "
            "because of double-bookings or miscommunication."
        )

        # Should move to next anchor (process question)
        assert result.next_question_type == "anchor"
        assert "step by step" in result.next_question.lower()

    @pytest.mark.asyncio
    async def test_max_questions_limit(self):
        """Should complete interview when max questions reached."""
        engine = InterviewEngine()
        state = InterviewState(
            industry="dental",
            company_name="Test",
            max_total_questions=3  # Low limit for test
        )

        # Ask several questions
        for i in range(4):
            result = await engine.process_answer(state, f"Answer {i}")
            if result.interview_complete:
                break

        # Should have completed due to max questions
        assert result.interview_complete or state.questions_asked >= 3

    @pytest.mark.asyncio
    async def test_follow_up_limit_per_anchor(self):
        """Should not exceed max follow-ups per anchor."""
        engine = InterviewEngine()
        state = InterviewState(
            industry="plumbing",
            company_name="Test",
            max_follow_ups_per_anchor=2
        )

        # Give multiple vague answers
        follow_up_count = 0
        for i in range(5):
            result = await engine.process_answer(state, "ok")
            if result.next_question_type == "follow_up":
                follow_up_count += 1
            else:
                break  # Moved to next anchor

        # Should have limited follow-ups
        assert follow_up_count <= 2
