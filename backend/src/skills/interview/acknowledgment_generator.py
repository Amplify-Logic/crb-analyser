"""
Acknowledgment Generator Skill

Generates warm expert acknowledgments that:
1. Name the user's specific pain (use their words)
2. Add industry insight showing expertise
3. Bridge naturally to the next question

Uses LLM for anchor questions, has fallback for errors.
"""

import json
import os
import logging
from typing import Any, Dict, List, Optional

from src.skills.base import LLMSkill, SkillContext, SkillError
from src.utils.prompt_safety import sanitize_user_input

logger = logging.getLogger(__name__)


ACKNOWLEDGMENT_SYSTEM_PROMPT = """You are a warm, experienced business consultant conducting a voice interview.

Your job is to generate a brief acknowledgment (1-2 sentences max) that:
1. Names their specific pain using their actual words
2. Adds a brief industry insight showing you've seen this before
3. Feels conversational and warm, not corporate

AVOID these phrases:
- "That's helpful"
- "Thanks for sharing"
- "I understand"
- "Great question"

USE phrases like:
- "Ah, [their problem]..."
- "That's really common in [industry]..."
- "I see this constantly..."
- "[Problem] in [industry] usually means..."

Keep it to ONE breath - not a paragraph. This will be spoken aloud."""


class AcknowledgmentGeneratorSkill(LLMSkill[Dict[str, Any]]):
    """
    Generate warm expert acknowledgments for interview answers.
    """

    name = "acknowledgment-generator"
    description = "Generate warm expert acknowledgments for interview answers"
    version = "1.0.0"

    requires_llm = True
    default_model = "claude-haiku-4-5-20251001"  # Fast model for quick responses
    default_max_tokens = 150

    def __init__(self, client=None):
        super().__init__(client)
        self._industry_insights = self._load_industry_insights()

    def _load_industry_insights(self) -> Dict[str, Any]:
        """Load industry-specific insights for acknowledgments."""
        insights = {}
        industries_path = os.path.join(
            os.path.dirname(__file__),
            "../../expertise/data/industries"
        )

        if os.path.exists(industries_path):
            for filename in os.listdir(industries_path):
                if filename.endswith(".json"):
                    industry = filename.replace(".json", "")
                    try:
                        with open(os.path.join(industries_path, filename)) as f:
                            data = json.load(f)
                            if "interview_insights" in data:
                                insights[industry] = data["interview_insights"]
                    except Exception as e:
                        logger.warning(f"Failed to load insights for {industry}: {e}")

        return insights

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Generate an acknowledgment for the user's answer.

        Args:
            context: SkillContext with metadata containing:
                - answer: The user's answer
                - signals_detected: List of detected signals
                - next_question: The next question to ask

        Returns:
            Dict with:
                - acknowledgment: The generated acknowledgment
                - used_llm: Whether LLM was used or fallback
        """
        raw_answer = context.metadata.get("answer", "")
        answer = sanitize_user_input(raw_answer)
        signals = context.metadata.get("signals_detected", [])
        next_question = context.metadata.get("next_question", "")
        industry = context.industry
        company_name = context.company_name or "your company"

        # Get industry-specific insights if available
        industry_insights = self._industry_insights.get(industry, {})
        common_pains = industry_insights.get("common_pains", [])

        # Build the prompt
        prompt = f"""Generate an acknowledgment for this interview answer.

Industry: {industry}
Company: {company_name}
Their answer: "{answer}"
Signals detected: {', '.join(signals) if signals else 'none'}
Next question we'll ask: "{next_question}"

Industry insights to potentially use:
{chr(10).join(f'- {p}' for p in common_pains[:3]) if common_pains else 'No specific insights available'}

Generate a 1-2 sentence acknowledgment that validates their pain and bridges to the next question.
Output ONLY the acknowledgment text, nothing else."""

        try:
            acknowledgment = await self.call_llm(
                prompt=prompt,
                system=ACKNOWLEDGMENT_SYSTEM_PROMPT,
            )
            return {
                "acknowledgment": acknowledgment.strip(),
                "used_llm": True
            }

        except Exception as e:
            logger.warning(f"LLM acknowledgment failed, using fallback: {e}")
            # Fallback acknowledgment
            fallback = self._get_fallback_acknowledgment(industry, signals)
            return {
                "acknowledgment": fallback,
                "used_llm": False,
                "fallback_reason": str(e)
            }

    def _get_fallback_acknowledgment(
        self,
        industry: str,
        signals: List[str]
    ) -> str:
        """Generate a simple fallback acknowledgment."""
        if "pain_intensity" in signals:
            return f"That's a challenge I hear often in {industry}. Let me dig into that a bit more."
        elif "manual_work" in signals:
            return "Manual processes like that are really common - and usually a great candidate for automation."
        elif "customer_impact" in signals:
            return "Customer experience issues like that can really add up. Let me understand the process better."
        else:
            return "Got it, that's helpful context. Let me ask a follow-up."
