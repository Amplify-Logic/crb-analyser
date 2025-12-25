"""
Follow-Up Question Skill

Generates adaptive follow-up questions for CRB interviews.

This skill:
1. Analyzes user's previous response for key themes
2. Considers topics already covered vs. topics needed
3. Uses industry expertise to probe known pain points
4. Generates natural, conversational follow-up questions
5. Adapts depth based on response quality

Output Schema:
{
    "question": "The follow-up question to ask",
    "question_type": "clarification|deepdive|transition|probing",
    "reasoning": "Why this question was chosen",
    "topics_touched": ["topic1", "topic2"],
    "suggested_followups": ["backup question 1", "backup question 2"],
    "is_completion_candidate": false
}
"""

import json
import logging
from typing import Dict, Any, List, Optional

from src.skills.base import LLMSkill, SkillContext, SkillError

logger = logging.getLogger(__name__)


# Interview topics from the interview routes
INTERVIEW_TOPICS = [
    {
        "id": "current_challenges",
        "name": "Current Challenges",
        "probing_questions": [
            "Can you give me a specific example of that challenge?",
            "How often does this issue occur?",
            "What's the impact when this happens?",
        ]
    },
    {
        "id": "business_goals",
        "name": "Business Goals",
        "probing_questions": [
            "What would achieving that goal mean for your business?",
            "What's currently preventing you from reaching that goal?",
            "How would you measure success?",
        ]
    },
    {
        "id": "team_operations",
        "name": "Team & Operations",
        "probing_questions": [
            "How long does that process typically take?",
            "Who's involved in that workflow?",
            "Where do delays usually happen?",
        ]
    },
    {
        "id": "technology",
        "name": "Technology & Tools",
        "probing_questions": [
            "What do you like about your current tools?",
            "What's frustrating about them?",
            "Are there features you wish you had?",
        ]
    },
    {
        "id": "budget_timeline",
        "name": "Budget & Timeline",
        "probing_questions": [
            "What would make this investment worthwhile?",
            "Have you allocated budget for this already?",
            "What's your ideal timeline for seeing results?",
        ]
    },
]


class FollowUpQuestionSkill(LLMSkill[Dict[str, Any]]):
    """
    Generate adaptive follow-up questions for interviews.

    This is an LLM-powered skill that analyzes the conversation context
    and generates appropriate follow-up questions. When expertise data
    is available, it prioritizes probing known pain points.
    """

    name = "followup-question"
    description = "Generate adaptive follow-up questions for interviews"
    version = "1.0.0"

    requires_llm = True
    requires_expertise = False  # Works without, better with

    # Question type definitions
    QUESTION_TYPES = {
        "clarification": "Ask for more details about something unclear",
        "deepdive": "Explore a topic more thoroughly",
        "transition": "Move to a new topic area",
        "probing": "Investigate a potential pain point",
    }

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Generate a follow-up question based on interview context.

        Args:
            context: SkillContext with:
                - metadata.user_message: The user's last message
                - metadata.previous_messages: List of previous messages
                - metadata.topics_covered: Topics already discussed
                - metadata.question_count: How many questions asked
                - industry: The business industry
                - expertise: Industry expertise for probing

        Returns:
            Dictionary with question and metadata
        """
        # Extract conversation context
        user_message = context.metadata.get("user_message", "")
        previous_messages = context.metadata.get("previous_messages", [])
        topics_covered = context.metadata.get("topics_covered", [])
        question_count = context.metadata.get("question_count", 0)

        if not user_message:
            raise SkillError(
                self.name,
                "No user_message provided in context.metadata",
                recoverable=False
            )

        # Build expertise context
        expertise_context = self._build_expertise_context(
            context.expertise,
            context.industry
        )

        # Determine what topics still need coverage
        uncovered_topics = self._get_uncovered_topics(topics_covered)

        # Generate follow-up question
        result = await self._generate_followup(
            user_message=user_message,
            previous_messages=previous_messages,
            topics_covered=topics_covered,
            uncovered_topics=uncovered_topics,
            question_count=question_count,
            industry=context.industry,
            expertise_context=expertise_context,
        )

        # Check if we should wrap up
        if question_count >= 12 and len(uncovered_topics) <= 1:
            result["is_completion_candidate"] = True

        return result

    def _build_expertise_context(
        self,
        expertise: Optional[Dict[str, Any]],
        industry: str
    ) -> Dict[str, Any]:
        """Build expertise context for question generation."""
        if not expertise:
            return {"has_data": False}

        industry_expertise = expertise.get("industry_expertise", {})

        if not industry_expertise or industry_expertise.get("total_analyses", 0) == 0:
            return {"has_data": False}

        return {
            "has_data": True,
            "total_analyses": industry_expertise.get("total_analyses", 0),
            "common_pain_points": list(
                industry_expertise.get("pain_points", {}).keys()
            )[:5],
            "effective_patterns": [
                p.get("recommendation", "") if isinstance(p, dict) else str(p)
                for p in industry_expertise.get("effective_patterns", [])[:3]
            ],
        }

    def _get_uncovered_topics(self, topics_covered: List[str]) -> List[str]:
        """Get topics that haven't been covered yet."""
        covered_ids = set()
        for topic in topics_covered:
            for t in INTERVIEW_TOPICS:
                if topic.lower() in t["name"].lower() or topic.lower() in t["id"]:
                    covered_ids.add(t["id"])

        uncovered = [
            t["name"] for t in INTERVIEW_TOPICS
            if t["id"] not in covered_ids
        ]
        return uncovered

    async def _generate_followup(
        self,
        user_message: str,
        previous_messages: List[Dict[str, str]],
        topics_covered: List[str],
        uncovered_topics: List[str],
        question_count: int,
        industry: str,
        expertise_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate follow-up question using Claude."""
        # Build expertise injection
        expertise_injection = ""
        if expertise_context.get("has_data"):
            pain_points = expertise_context.get("common_pain_points", [])
            expertise_injection = f"""
INDUSTRY EXPERTISE (from {expertise_context['total_analyses']} analyses):
Common pain points in {industry}:
{chr(10).join(f'- {p}' for p in pain_points[:5]) if pain_points else '- No specific patterns yet'}

PRIORITY: If the user mentions anything related to these pain points, probe deeper!
"""

        # Build conversation context
        recent_messages = previous_messages[-6:] if previous_messages else []
        conversation_context = "\n".join([
            f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}"
            for msg in recent_messages
        ])

        prompt = f"""Generate an adaptive follow-up question for this CRB interview.

USER'S LAST MESSAGE:
"{user_message}"

RECENT CONVERSATION:
{conversation_context if conversation_context else "This is the first exchange."}

INTERVIEW PROGRESS:
- Questions asked: {question_count}
- Topics covered: {', '.join(topics_covered) if topics_covered else 'None yet'}
- Topics still needed: {', '.join(uncovered_topics) if uncovered_topics else 'All covered'}

INDUSTRY: {industry}
{expertise_injection}

QUESTION TYPE GUIDANCE:
- clarification: Use when the user's response is vague or unclear
- deepdive: Use when the user mentioned something interesting worth exploring
- transition: Use when current topic is exhausted, move to uncovered topic
- probing: Use when user touches on a known pain point (from expertise)

RULES:
1. Ask ONE question only
2. Reference something specific from their response
3. Keep it conversational (under 30 words)
4. If all topics covered and question_count >= 12, suggest wrapping up

Generate a JSON response:
{{
    "question": "<the follow-up question>",
    "question_type": "clarification|deepdive|transition|probing",
    "reasoning": "<why this question was chosen>",
    "topics_touched": ["<topics this question touches on>"],
    "suggested_followups": ["<backup question 1>", "<backup question 2>"],
    "is_completion_candidate": false
}}

Return ONLY the JSON."""

        try:
            response = await self.call_llm_json(
                prompt=prompt,
                system=self._get_system_prompt(),
            )

            # Validate response structure
            return self._validate_response(response)

        except SkillError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate follow-up: {e}")
            return self._get_fallback_question(uncovered_topics, question_count)

    def _get_system_prompt(self) -> str:
        """Get the system prompt for follow-up generation."""
        return """You are an expert business interviewer conducting CRB analysis interviews.

Your role is to generate thoughtful, adaptive follow-up questions that:
1. Show you listened to what the user said (reference their words)
2. Dig deeper into interesting points
3. Guide the conversation toward uncovered topics naturally
4. Gather specific, quantifiable information

Key principles:
- Be curious, not interrogating
- One question at a time
- Use their language back to them
- Probe pain points when you spot them
- Keep it conversational and warm"""

    def _validate_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize the response structure."""
        validated = {
            "question": response.get("question", "Can you tell me more about that?"),
            "question_type": response.get("question_type", "clarification"),
            "reasoning": response.get("reasoning", ""),
            "topics_touched": response.get("topics_touched", []),
            "suggested_followups": response.get("suggested_followups", [])[:2],
            "is_completion_candidate": response.get("is_completion_candidate", False),
        }

        # Validate question_type
        if validated["question_type"] not in self.QUESTION_TYPES:
            validated["question_type"] = "clarification"

        return validated

    def _get_fallback_question(
        self,
        uncovered_topics: List[str],
        question_count: int
    ) -> Dict[str, Any]:
        """Return a fallback question when LLM fails."""
        if question_count >= 12:
            return {
                "question": "Is there anything else you'd like to share before we wrap up?",
                "question_type": "transition",
                "reasoning": "Fallback: Interview is long enough, offer to conclude",
                "topics_touched": ["summary"],
                "suggested_followups": [],
                "is_completion_candidate": True,
            }

        if uncovered_topics:
            topic = uncovered_topics[0]
            topic_data = next(
                (t for t in INTERVIEW_TOPICS if t["name"] == topic),
                None
            )
            if topic_data:
                return {
                    "question": topic_data["probing_questions"][0],
                    "question_type": "transition",
                    "reasoning": f"Fallback: Moving to uncovered topic '{topic}'",
                    "topics_touched": [topic],
                    "suggested_followups": topic_data["probing_questions"][1:],
                    "is_completion_candidate": False,
                }

        return {
            "question": "That's interesting - can you tell me more about that?",
            "question_type": "deepdive",
            "reasoning": "Fallback: Generic follow-up",
            "topics_touched": [],
            "suggested_followups": [],
            "is_completion_candidate": False,
        }


# For skill discovery
__all__ = ["FollowUpQuestionSkill"]
