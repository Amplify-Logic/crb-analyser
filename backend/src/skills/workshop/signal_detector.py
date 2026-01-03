# backend/src/skills/workshop/signal_detector.py
"""
Adaptive Signal Detector Skill

Detects user signals from quiz data and company profile to adapt
workshop questions and recommendations.

Signals detected:
- technical: User has technical background, can discuss APIs/integrations
- budget_ready: User has budget allocated, can discuss implementation
- decision_maker: User can make purchasing decisions
"""

from typing import Any, Dict

from src.skills.base import SyncSkill, SkillContext
from src.models.workshop import DetectedSignals


class AdaptiveSignalDetectorSkill(SyncSkill[Dict[str, Any]]):
    """
    Detect adaptive signals from quiz and profile data.

    This skill analyzes user data to determine how to frame
    questions during the workshop.
    """

    name = "adaptive-signal-detector"
    description = "Detect user signals for adaptive workshop questioning"
    version = "1.0.0"

    requires_llm = False
    requires_expertise = False

    def execute_sync(self, context: SkillContext) -> Dict[str, Any]:
        """
        Detect signals from context.

        Args:
            context: SkillContext with metadata containing:
                - role: User's job title
                - company_size: Company size range
                - budget_answer: Selected budget range
                - quiz_answers: All quiz answers
                - company_profile: Research data (optional)

        Returns:
            Dict with detected signals and confidence
        """
        metadata = context.metadata or {}

        role = metadata.get("role")
        company_size = metadata.get("company_size")
        budget_answer = metadata.get("budget_answer")
        quiz_answers = metadata.get("quiz_answers", {})

        # Also check company profile for role if not in metadata
        company_profile = metadata.get("company_profile", {})
        if not role and company_profile:
            # Try to extract from profile
            basics = company_profile.get("basics", {})
            role = basics.get("contact_role", {}).get("value")

        signals = DetectedSignals.from_quiz_data(
            role=role,
            company_size=company_size,
            budget_answer=budget_answer,
            quiz_answers=quiz_answers,
        )

        return {
            "technical": signals.technical,
            "budget_ready": signals.budget_ready,
            "decision_maker": signals.decision_maker,
            "detection_sources": {
                "role": role,
                "company_size": company_size,
                "budget_answer": budget_answer,
            },
        }
