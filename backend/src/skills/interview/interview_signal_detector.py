"""
Interview Signal Detector Skill

Detects signals in user answers to determine:
- Pain intensity (frustration level)
- Manual work (automation opportunities)
- Customer impact (urgency)
- Growth blockers (scalability issues)
- Tech frustration (integration needs)
- Vague answers (need to probe deeper)

Returns detected signals and suggested follow-up questions.
"""

import json
import os
from typing import Any, Dict, List

from src.skills.base import SyncSkill, SkillContext


class InterviewSignalDetectorSkill(SyncSkill[Dict[str, Any]]):
    """
    Detect signals from interview answers to guide follow-up questions.
    """

    name = "interview-signal-detector"
    description = "Detect signals in interview answers for adaptive follow-ups"
    version = "1.0.0"

    requires_llm = False
    requires_expertise = False

    def __init__(self):
        super().__init__()
        self._follow_ups = self._load_follow_ups()

    def _load_follow_ups(self) -> Dict[str, Any]:
        """Load follow-up question bank."""
        path = os.path.join(
            os.path.dirname(__file__),
            "../../expertise/data/interview/follow_ups.json"
        )
        try:
            with open(path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # Return minimal default if file not found
            return {"signals": {}, "anchor_questions": {}}

    def execute_sync(self, context: SkillContext) -> Dict[str, Any]:
        """
        Detect signals in the given answer.

        Args:
            context: SkillContext with metadata containing:
                - answer: The user's answer text
                - current_topic: Optional topic being discussed

        Returns:
            Dict with:
                - signals_detected: List of signal names
                - signal_details: Dict of signal -> confidence
                - suggested_follow_ups: List of follow-up questions
                - should_probe_deeper: bool
        """
        answer = context.metadata.get("answer", "").lower()
        signals_config = self._follow_ups.get("signals", {})

        detected_signals: List[str] = []
        signal_details: Dict[str, Dict[str, Any]] = {}
        suggested_follow_ups: List[str] = []

        # Check each signal type
        for signal_name, config in signals_config.items():
            patterns = config.get("patterns", [])

            # Special handling for vague_answer (based on length)
            if signal_name == "vague_answer":
                min_words = config.get("min_words", 5)
                word_count = len(answer.split())
                if word_count < min_words:
                    detected_signals.append(signal_name)
                    signal_details[signal_name] = {
                        "reason": f"Short answer ({word_count} words)",
                        "confidence": 0.9
                    }
                    suggested_follow_ups.extend(config.get("follow_ups", [])[:1])
                continue

            # Pattern matching for other signals
            matched_patterns = [p for p in patterns if p in answer]
            if matched_patterns:
                detected_signals.append(signal_name)
                signal_details[signal_name] = {
                    "matched_patterns": matched_patterns,
                    "confidence": min(0.5 + 0.2 * len(matched_patterns), 1.0)
                }
                # Add one follow-up from this signal's bank
                follow_ups = config.get("follow_ups", [])
                if follow_ups:
                    suggested_follow_ups.append(follow_ups[0])

        # Determine if we should probe deeper
        should_probe = (
            "vague_answer" in detected_signals or
            len(detected_signals) == 0
        )

        return {
            "signals_detected": detected_signals,
            "signal_details": signal_details,
            "suggested_follow_ups": suggested_follow_ups[:2],  # Max 2 suggestions
            "should_probe_deeper": should_probe,
            "answer_word_count": len(answer.split())
        }
