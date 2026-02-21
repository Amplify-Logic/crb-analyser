"""
Quiz Optimization Skill

Optimizes question selection using confidence gaps and expertise data.

This skill:
1. Analyzes current confidence state to identify biggest gaps
2. Uses expertise data to identify high-value questions for the industry
3. Generates a context-aware question optimized for information gain
4. Returns structured question data ready for the quiz engine

Output Schema:
{
    "question": "How do you currently handle patient scheduling?",
    "question_type": "voice",
    "input_type": "voice",
    "options": null,
    "target_categories": ["operations", "pain_points"],
    "expected_boosts": {"operations": 25, "pain_points": 15},
    "rationale": "Scheduling is a top pain point in dental practices...",
    "acknowledgment": "That's helpful context about your team."
}
"""

import logging
from typing import Dict, Any, List, Optional

from src.skills.base import LLMSkill, SkillContext, SkillError

logger = logging.getLogger(__name__)


class QuizOptimizationSkill(LLMSkill[Dict[str, Any]]):
    """
    Optimize quiz question selection using confidence gaps and expertise.

    Uses industry expertise to ask higher-value questions that fill
    knowledge gaps more efficiently than generic questions.
    """

    name = "quiz-optimization"
    description = "Optimize question selection using confidence gaps and expertise"
    version = "1.0.0"

    requires_llm = True
    requires_expertise = True  # Works without but significantly better with

    # Use a fast model for quiz — latency matters in interactive flow
    default_task = "extract_company_profile"
    default_tier = "quick"
    default_max_tokens = 1024

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Generate an optimized question.

        Args:
            context: SkillContext with:
                - metadata.confidence_state: Dict of category -> score
                - metadata.conversation_history: List of prior Q&A
                - metadata.company_name: Company name
                - metadata.company_size: Company size
                - metadata.last_answer: Last user answer (optional)
                - industry: Industry for expertise lookup
                - expertise: Optional expertise data

        Returns:
            Dict with question, target_categories, expected_boosts, etc.
        """
        confidence_state = context.metadata.get("confidence_state", {})
        conversation_history = context.metadata.get("conversation_history", [])

        if not confidence_state:
            raise SkillError(
                self.name,
                "No confidence_state provided in context.metadata",
                recoverable=False,
            )

        prompt = self._build_prompt(confidence_state, conversation_history, context)
        system = self._build_system_prompt(context)

        result = await self.call_llm_json(
            prompt=prompt,
            system=system,
        )

        return self._validate_question(result)

    def _build_system_prompt(self, context: SkillContext) -> str:
        """Build system prompt with expertise-enhanced guidance."""
        base = (
            "You are an expert business analyst conducting a personalized discovery interview. "
            "Your goal is to fill knowledge gaps efficiently while building rapport. "
            "Ask ONE question at a time. Be conversational, not interrogative."
        )

        if context.expertise:
            industry_data = context.expertise.get("industry_expertise", {})

            # Add industry-specific high-value topics
            key_topics = industry_data.get("key_assessment_areas", [])
            if key_topics:
                topics_text = ", ".join(key_topics[:5])
                base += f"\n\nHigh-value topics for {context.industry}: {topics_text}"

            # Add common pain points to help target questions
            common_pains = industry_data.get("common_pain_points", [])
            if common_pains:
                pains_text = ", ".join(common_pains[:5])
                base += f"\n\nCommon pain points in {context.industry}: {pains_text}"

            # Add typical tech stack to reference
            typical_stack = industry_data.get("typical_tech_stack", [])
            if typical_stack:
                stack_text = ", ".join(typical_stack[:5])
                base += f"\n\nTypical tools in {context.industry}: {stack_text}"

        return base

    def _build_prompt(
        self,
        confidence_state: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        context: SkillContext,
    ) -> str:
        """Build the question generation prompt."""
        # Format confidence gaps
        gaps = []
        for category, score in sorted(confidence_state.items(), key=lambda x: x[1]):
            if score < 70:  # Below typical threshold
                gaps.append(f"- {category}: {score}% (gap: {70 - score}%)")

        gaps_text = "\n".join(gaps[:5]) if gaps else "All categories above threshold"

        # Format conversation history
        history_text = "(First question)" if not conversation_history else "\n".join(
            f"Q: {item.get('question', '?')}"
            for item in conversation_history[-5:]
        )

        # Get last answer
        last_answer = context.metadata.get("last_answer", "(First question)")

        # Company context
        company_name = context.metadata.get("company_name", context.company_name or "the company")
        company_size = context.metadata.get("company_size", context.company_size or "unknown")

        return f"""Generate the next question for this discovery interview.

COMPANY: {company_name}
INDUSTRY: {context.industry}
SIZE: {company_size}

CURRENT CONFIDENCE SCORES (lower = bigger gap):
{gaps_text}

CONVERSATION SO FAR:
{history_text}

LAST ANSWER: {last_answer}

RULES:
1. Target the BIGGEST confidence gap
2. Never ask what we already know with high confidence
3. Be specific to their industry and business
4. Use their company name when natural
5. Keep it conversational
6. Use "structured" + "select/multi_select" for factual gaps, "voice" for discovery

OUTPUT FORMAT (JSON only):
{{
    "acknowledgment": "Brief response to last answer (null if first question)",
    "question": "The question to ask",
    "question_type": "structured|voice",
    "input_type": "text|number|select|multi_select|scale|voice",
    "options": null,
    "target_categories": ["pain_points", "operations"],
    "expected_boosts": {{"pain_points": 20, "operations": 15}},
    "rationale": "Why asking this now"
}}

Generate the question:"""

    def _validate_question(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize question output."""
        if not isinstance(data, dict):
            raise SkillError(
                self.name,
                "LLM returned non-dict response",
                recoverable=True,
            )

        # Ensure required fields
        question = data.get("question")
        if not question:
            raise SkillError(
                self.name,
                "LLM response missing 'question' field",
                recoverable=True,
            )

        # Normalize question_type
        question_type = data.get("question_type", "voice")
        if question_type not in ("structured", "voice"):
            question_type = "voice"

        # Normalize input_type
        input_type = data.get("input_type", "voice")
        valid_input_types = ("text", "number", "select", "multi_select", "scale", "voice")
        if input_type not in valid_input_types:
            input_type = "voice"

        # Validate target_categories is a list
        target_categories = data.get("target_categories", [])
        if not isinstance(target_categories, list):
            target_categories = []

        # Validate expected_boosts is a dict with int values
        expected_boosts = data.get("expected_boosts", {})
        if not isinstance(expected_boosts, dict):
            expected_boosts = {}
        expected_boosts = {
            k: min(30, int(v))
            for k, v in expected_boosts.items()
            if isinstance(v, (int, float))
        }

        return {
            "acknowledgment": data.get("acknowledgment"),
            "question": question,
            "question_type": question_type,
            "input_type": input_type,
            "options": data.get("options"),
            "target_categories": target_categories,
            "expected_boosts": expected_boosts,
            "rationale": data.get("rationale", ""),
        }


# For skill discovery
__all__ = ["QuizOptimizationSkill"]
