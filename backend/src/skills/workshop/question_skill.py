# backend/src/skills/workshop/question_skill.py
"""
Workshop Question Skill

Generates adaptive, contextual questions for the workshop deep-dive phase.
Uses detected signals to frame questions appropriately.
"""

from typing import Any, Dict, List, Optional

from src.skills.base import LLMSkill, SkillContext, SkillError


# Conversation stages within a deep-dive
CONVERSATION_STAGES = [
    "current_state",     # How does this work today?
    "failed_attempts",   # What have you tried?
    "cost_impact",       # What's the real cost?
    "ideal_state",       # What would perfect look like?
    "stakeholders",      # Who else is involved?
]


class WorkshopQuestionSkill(LLMSkill[Dict[str, Any]]):
    """
    Generate adaptive questions for workshop deep-dives.

    Takes into account:
    - Current pain point being explored
    - Conversation stage within the deep-dive
    - Detected user signals (technical, budget, decision-maker)
    - Previous messages in the conversation
    """

    name = "workshop-question"
    description = "Generate adaptive workshop questions"
    version = "1.0.0"

    default_model = "claude-haiku-4-5-20251001"  # Fast for questions
    default_max_tokens = 500

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Generate the next question for the workshop.

        Args:
            context: SkillContext with metadata containing:
                - phase: Current workshop phase
                - current_pain_point: ID of pain point being explored
                - pain_point_label: Human-readable pain point name
                - conversation_stage: current_state, failed_attempts, etc.
                - signals: Detected user signals
                - previous_messages: Conversation history
                - company_name: Company name for personalization

        Returns:
            Dict with question, next_stage, and metadata
        """
        metadata = context.metadata or {}

        pain_point = metadata.get("current_pain_point", "unknown")
        pain_label = metadata.get("pain_point_label", "this challenge")
        stage = metadata.get("conversation_stage", "current_state")
        signals = metadata.get("signals", {})
        previous = metadata.get("previous_messages", [])
        company_name = metadata.get("company_name", "your company")

        # Build the prompt
        prompt = self._build_prompt(
            pain_label=pain_label,
            stage=stage,
            signals=signals,
            previous=previous,
            company_name=company_name,
            industry=context.industry,
        )

        system = self._get_system_prompt(signals)

        question = await self.call_llm(prompt, system)

        # Clean up the response
        question = question.strip().strip('"').strip("'")

        # Determine next stage
        stage_idx = CONVERSATION_STAGES.index(stage) if stage in CONVERSATION_STAGES else 0
        next_stage = CONVERSATION_STAGES[stage_idx + 1] if stage_idx < len(CONVERSATION_STAGES) - 1 else "complete"

        return {
            "question": question,
            "stage": stage,
            "next_stage": next_stage,
            "pain_point": pain_point,
            "signals_applied": signals,
        }

    def _get_system_prompt(self, signals: Dict[str, bool]) -> str:
        """Build system prompt based on detected signals."""
        base = """You are an expert business consultant conducting a discovery workshop.
Your goal is to deeply understand ONE specific pain point before recommending solutions.

Key principles:
- Ask ONE question at a time
- Be conversational and warm, not interrogative
- Reference what they've already shared
- Probe for specifics: numbers, examples, names
- Keep questions under 30 words

"""
        if signals.get("technical"):
            base += """
This user has a technical background. You can:
- Ask about APIs, integrations, data flows
- Use technical terminology appropriately
- Probe about system architecture
"""
        else:
            base += """
This user is non-technical. You should:
- Focus on outcomes and business impact
- Avoid technical jargon
- Ask about team adoption and change management
"""

        if signals.get("budget_ready"):
            base += """
This user has budget available. You can:
- Discuss implementation options
- Ask about build vs. buy preferences
- Explore timeline for ROI
"""
        else:
            base += """
This user is budget-constrained. You should:
- Focus on quick wins and phased approaches
- Ask about what would unlock more budget
- Emphasize free/low-cost options
"""

        return base

    def _build_prompt(
        self,
        pain_label: str,
        stage: str,
        signals: Dict[str, bool],
        previous: List[Dict[str, str]],
        company_name: str,
        industry: str,
    ) -> str:
        """Build the question generation prompt."""
        # Stage-specific guidance
        stage_guidance = {
            "current_state": f"Ask about how {pain_label} works TODAY at {company_name}. Who does it? How long does it take? What tools are used?",
            "failed_attempts": f"Ask what they've already tried to solve {pain_label}. Past tools? Workarounds? Why didn't they work?",
            "cost_impact": f"Help quantify the cost of {pain_label}. Hours per week? Impact on revenue? Team frustration?",
            "ideal_state": f"Ask what 'solved' looks like for {pain_label}. What would be perfect? What outcomes matter most?",
            "stakeholders": f"Ask who else is involved in or affected by {pain_label}. Who needs to approve changes? Who needs to adopt?",
        }

        guidance = stage_guidance.get(stage, stage_guidance["current_state"])

        # Build conversation context
        conv_context = ""
        if previous:
            conv_context = "\n\nRecent conversation:\n"
            for msg in previous[-4:]:  # Last 4 messages
                role = msg.get("role", "user").upper()
                content = msg.get("content", "")[:200]
                conv_context += f"{role}: {content}\n"

        prompt = f"""Company: {company_name}
Industry: {industry}
Pain Point: {pain_label}
Current Stage: {stage}

{guidance}
{conv_context}

Generate the next question. Return ONLY the question text, nothing else."""

        return prompt
