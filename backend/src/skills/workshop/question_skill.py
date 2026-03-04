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

# Followup stage is special - used after milestone feedback
FOLLOWUP_STAGE = "followup"


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

    default_task = "classify_finding"  # Fast model for quick question generation
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
        data_gaps = metadata.get("data_gaps", [])
        user_notes = metadata.get("user_notes")

        # Build the prompt
        prompt = self._build_prompt(
            pain_label=pain_label,
            stage=stage,
            signals=signals,
            previous=previous,
            company_name=company_name,
            industry=context.industry,
            data_gaps=data_gaps,
            user_notes=user_notes,
        )

        system = self._get_system_prompt(
            signals=signals,
            company_name=company_name,
            industry=context.industry,
        )

        question = await self.call_llm(prompt, system)

        # Clean up the response
        question = question.strip().strip('"').strip("'")

        # Determine next stage
        if stage == FOLLOWUP_STAGE:
            # Followup mode: check if we have enough info now
            followup_count = metadata.get("followup_count", 0)
            next_stage = "complete" if followup_count >= 2 else FOLLOWUP_STAGE
        elif stage in CONVERSATION_STAGES:
            stage_idx = CONVERSATION_STAGES.index(stage)
            next_stage = CONVERSATION_STAGES[stage_idx + 1] if stage_idx < len(CONVERSATION_STAGES) - 1 else "complete"
        else:
            next_stage = "complete"

        return {
            "question": question,
            "stage": stage,
            "next_stage": next_stage,
            "pain_point": pain_point,
            "signals_applied": signals,
        }

    def _get_system_prompt(
        self,
        signals: Dict[str, bool],
        company_name: str = "your company",
        industry: str = "ecommerce",
    ) -> str:
        """Build system prompt with consultant persona based on detected signals."""
        base = f"""You are a senior technology strategist at a boutique consulting firm, \
conducting a deep-dive discovery session with {company_name}.

YOUR PERSONA:
- You've consulted for 100+ {industry} businesses on technology transformation
- You're direct but empathetic — you genuinely care about their success
- You demonstrate expertise by connecting their situation to patterns you've seen
- You challenge assumptions when needed: "Many firms think X, but we find Y works better"
- You celebrate good insights: "That's a significant finding" / "Most firms miss this"

CONVERSATION RULES:
- Ask ONE question at a time
- Keep questions under 40 words (allow context that shows you listened)
- Reference specific details they shared — use their exact words and numbers
- When they share a number, validate it: "6 hours a week — that's over 300 hours a year"
- When you detect frustration, acknowledge it before asking more
- When you detect enthusiasm, build on it
- Inject industry context: "In {industry}, the benchmark for this is typically..."

WHAT MAKES YOU DIFFERENT FROM A CHATBOT:
- You proactively surface implications they haven't considered
- You challenge vague answers: "When you say 'a lot of time', can you estimate hours per week?"
- You connect dots across topics: "This reminds me of what you said about [earlier topic]..."
- You share relevant patterns: "I see this exact problem in about 70% of {industry} firms"

"""
        # Add ecommerce-specific context when relevant
        if industry == "ecommerce":
            base += """ECOMMERCE-SPECIFIC PROBES (use when relevant to the pain point):
- Return handling: "Walk me through what happens when a customer requests a return"
- Multi-channel inventory: "How do you manage inventory across channels — Shopify, marketplaces, wholesale?"
- Shipping logistics: "What does your fulfillment workflow look like from order to doorstep?"
- Customer lifetime value: "How do you track repeat purchases and customer retention?"
- Marketing attribution: "After iOS changes, how confident are you in your ad spend decisions?"

"""

        if signals.get("technical"):
            base += """TECHNICAL USER DETECTED:
- Use precise technical terminology (APIs, integrations, data flows, webhooks)
- Ask about system architecture and data model
- Probe about build vs. buy trade-offs
- Reference specific technologies and their limitations

"""
        else:
            base += """BUSINESS-FOCUSED USER DETECTED:
- Focus on outcomes, not technology details
- Translate technical concepts to business impact
- Ask about team adoption and change management
- Use analogies to explain complex integrations

"""

        if signals.get("budget_ready"):
            base += """BUDGET-READY USER:
- Discuss implementation timelines and phased rollouts
- Compare build vs. buy economics
- Explore ROI expectations and payback periods
- Ask about internal resources available for implementation

"""
        else:
            base += """BUDGET-EXPLORING USER:
- Focus on quick wins with immediate ROI
- Emphasize free tiers and low-cost starting points
- Help them build the internal business case
- Ask what would unlock more budget: "If you could show your team that X saves Y hours..."

"""

        if signals.get("decision_maker"):
            base += """DECISION-MAKER:
- Focus on strategic impact and competitive advantage
- Ask about board/partner priorities
- Discuss risk tolerance and change appetite
"""
        else:
            base += """INFLUENCER (NOT FINAL DECISION-MAKER):
- Help them build the case for decision-makers
- Ask what their boss/partner would need to see
- Focus on measurable outcomes they can present
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
        data_gaps: Optional[List[str]] = None,
        user_notes: Optional[str] = None,
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

        # Handle followup stage specially
        if stage == FOLLOWUP_STAGE:
            gaps_text = ", ".join(data_gaps[:2]) if data_gaps else "missing details"
            user_feedback = f"The user said: '{user_notes}'" if user_notes else "The user wants to refine the finding."

            guidance = f"""This is a FOLLOW-UP question. {user_feedback}

We need more information about: {gaps_text}

Ask a specific, targeted question to fill in the missing data. Focus on getting concrete numbers, examples, or clarifications."""
        else:
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
