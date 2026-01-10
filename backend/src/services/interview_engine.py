"""
Interview Engine Service

Orchestrates the SOTA voice interview experience:
- Manages 3 anchor questions (Problem -> Process -> Priority)
- Detects signals to decide follow-ups vs next anchor
- Generates warm expert acknowledgments
- Tracks conversation state

Usage:
    engine = InterviewEngine(anthropic_client)
    state = InterviewState(industry="plumbing", company_name="Test Co")
    result = await engine.process_answer(state, "Scheduling is chaos")
"""

import json
import os
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Literal

from src.skills.interview.interview_signal_detector import InterviewSignalDetectorSkill
from src.skills.interview.acknowledgment_generator import AcknowledgmentGeneratorSkill
from src.skills.base import SkillContext

logger = logging.getLogger(__name__)


@dataclass
class InterviewState:
    """Tracks the state of an interview conversation."""

    industry: str
    company_name: str

    # Progress tracking
    current_anchor: int = 1  # 1, 2, or 3
    questions_asked: int = 0
    follow_ups_for_current_anchor: int = 0

    # Conversation data
    answers: List[Dict[str, Any]] = field(default_factory=list)
    all_signals: List[str] = field(default_factory=list)

    # Phase: "anchor" or "follow_up"
    phase: Literal["anchor", "follow_up"] = "anchor"

    # Configuration
    max_follow_ups_per_anchor: int = 2
    max_total_questions: int = 8


@dataclass
class ProcessAnswerResult:
    """Result from processing an answer."""

    # What was detected
    signals_detected: List[str]

    # Response to give
    acknowledgment: str
    next_question: str
    next_question_type: Literal["anchor", "follow_up", "summary"]
    next_topic: Optional[str] = None

    # State updates
    new_anchor: int = 1
    interview_complete: bool = False

    # Debug info
    decision_reason: str = ""


class InterviewEngine:
    """
    Orchestrates the adaptive voice interview.
    """

    def __init__(self, anthropic_client=None):
        self.client = anthropic_client
        self.signal_detector = InterviewSignalDetectorSkill()
        self.ack_generator = AcknowledgmentGeneratorSkill(client=anthropic_client)
        self._follow_ups = self._load_follow_ups()

    def _load_follow_ups(self) -> Dict[str, Any]:
        """Load the follow-up question bank."""
        path = os.path.join(
            os.path.dirname(__file__),
            "../expertise/data/interview/follow_ups.json"
        )
        try:
            with open(path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Follow-up bank not found, using defaults")
            return {
                "anchor_questions": {
                    "problem": "What's the one thing in your business that costs you the most time or money right now?",
                    "process": "Walk me through how that works today - what happens step by step?",
                    "priority": "If we could fix that in the next 90 days, what would that be worth to your business?"
                },
                "signals": {}
            }

    def get_anchor_question(self, anchor_num: int) -> str:
        """Get the anchor question for a given anchor number."""
        anchors = self._follow_ups.get("anchor_questions", {})
        if anchor_num == 1:
            return anchors.get("problem", "What costs you the most time or money?")
        elif anchor_num == 2:
            return anchors.get("process", "Walk me through how that works step by step?")
        elif anchor_num == 3:
            return anchors.get("priority", "What would fixing this be worth to your business?")
        else:
            return "Is there anything else you'd like to add?"

    def get_anchor_topic(self, anchor_num: int) -> str:
        """Get the topic name for an anchor."""
        topics = {1: "Problem", 2: "Process", 3: "Priority"}
        return topics.get(anchor_num, "Summary")

    async def process_answer(
        self,
        state: InterviewState,
        answer: str
    ) -> ProcessAnswerResult:
        """
        Process a user's answer and determine next steps.

        Args:
            state: Current interview state
            answer: The user's answer text

        Returns:
            ProcessAnswerResult with acknowledgment, next question, and state updates
        """
        # Step 1: Detect signals in the answer
        signal_context = SkillContext(
            industry=state.industry,
            metadata={"answer": answer}
        )
        signal_result = await self.signal_detector.run(signal_context)

        signals = signal_result.data.get("signals_detected", [])
        should_probe = signal_result.data.get("should_probe_deeper", False)
        suggested_follow_ups = signal_result.data.get("suggested_follow_ups", [])

        # Update state with detected signals
        state.all_signals.extend(signals)
        state.questions_asked += 1

        # Store the answer
        state.answers.append({
            "anchor": state.current_anchor,
            "question_type": state.phase,
            "answer": answer,
            "signals": signals
        })

        # Step 2: Decide next action
        decision = self._decide_next_action(state, signals, should_probe, suggested_follow_ups)

        # Step 3: Generate acknowledgment (only for anchors, use simpler for follow-ups)
        if state.phase == "anchor" and self.client:
            ack_context = SkillContext(
                industry=state.industry,
                company_name=state.company_name,
                metadata={
                    "answer": answer,
                    "signals_detected": signals,
                    "next_question": decision["next_question"]
                }
            )
            ack_result = await self.ack_generator.run(ack_context)
            acknowledgment = ack_result.data.get("acknowledgment", "Got it.")
        else:
            # Simple acknowledgment for follow-ups
            acknowledgment = self._get_simple_acknowledgment(signals)

        # Step 4: Update state based on decision
        if decision["type"] == "anchor":
            state.current_anchor = decision["new_anchor"]
            state.follow_ups_for_current_anchor = 0
            state.phase = "anchor"
        elif decision["type"] == "follow_up":
            state.follow_ups_for_current_anchor += 1
            state.phase = "follow_up"

        return ProcessAnswerResult(
            signals_detected=signals,
            acknowledgment=acknowledgment,
            next_question=decision["next_question"],
            next_question_type=decision["type"],
            next_topic=decision.get("topic"),
            new_anchor=state.current_anchor,
            interview_complete=decision.get("complete", False),
            decision_reason=decision.get("reason", "")
        )

    def _decide_next_action(
        self,
        state: InterviewState,
        signals: List[str],
        should_probe: bool,
        suggested_follow_ups: List[str]
    ) -> Dict[str, Any]:
        """Decide whether to follow up, move to next anchor, or complete."""

        # Check if we're at max questions
        if state.questions_asked >= state.max_total_questions:
            return {
                "type": "summary",
                "next_question": "Thanks for sharing all that. Is there anything else you'd like to add?",
                "complete": True,
                "reason": "Max questions reached"
            }

        # Check if we've completed anchor 3
        if state.current_anchor == 3 and state.phase == "anchor":
            return {
                "type": "summary",
                "next_question": "Thanks for sharing all that. Is there anything else you'd like to add?",
                "complete": True,
                "reason": "Completed all anchors"
            }

        # Decide: follow-up or next anchor?
        should_follow_up = (
            should_probe and
            state.follow_ups_for_current_anchor < state.max_follow_ups_per_anchor and
            len(suggested_follow_ups) > 0
        )

        if should_follow_up:
            return {
                "type": "follow_up",
                "next_question": suggested_follow_ups[0],
                "topic": self.get_anchor_topic(state.current_anchor),
                "reason": f"Probing deeper on signals: {signals}"
            }
        else:
            # Move to next anchor
            next_anchor = state.current_anchor + 1
            if next_anchor > 3:
                return {
                    "type": "summary",
                    "next_question": "Thanks for sharing all that. Is there anything else you'd like to add?",
                    "complete": True,
                    "reason": "Completed all anchors"
                }
            return {
                "type": "anchor",
                "next_question": self.get_anchor_question(next_anchor),
                "new_anchor": next_anchor,
                "topic": self.get_anchor_topic(next_anchor),
                "reason": f"Moving to anchor {next_anchor}"
            }

    def _get_simple_acknowledgment(self, signals: List[str]) -> str:
        """Get a simple acknowledgment for follow-up questions."""
        if "pain_intensity" in signals:
            return "I can see why that's frustrating."
        elif "manual_work" in signals:
            return "That's a lot of manual work."
        elif "customer_impact" in signals:
            return "That definitely affects the customer experience."
        elif "growth_blocker" in signals:
            return "Growth constraints like that are tough."
        else:
            return "Got it."

    def get_first_question(self, state: InterviewState) -> str:
        """Get the first question to start the interview."""
        return self.get_anchor_question(1)
