"""
Quiz Engine Service

This module provides the core logic for the adaptive quiz system:
1. AnswerAnalyzer - Extracts insights from user answers using AI
2. QuestionGenerator - Generates adaptive questions based on confidence gaps

The engine uses research findings as context and adapts questions
in real-time based on what we learn from each answer.
"""

import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, AsyncGenerator

from anthropic import Anthropic

from src.config.settings import settings
from src.models.quiz_confidence import (
    ConfidenceCategory,
    ConfidenceState,
    AdaptiveQuestion,
    AnswerAnalysis,
    ExtractedFact,
    CONFIDENCE_THRESHOLDS,
    CATEGORY_LABELS,
    create_initial_confidence_from_research,
    update_confidence_from_analysis,
)
from src.models.research import CompanyProfile

logger = logging.getLogger(__name__)


# ============================================================================
# Industry Question Bank
# ============================================================================

@dataclass
class IndustryQuestionBank:
    """
    Holds industry-specific questions, deep dive templates, and woven confirmations.
    """
    industry: str
    display_name: str
    questions: List[Dict[str, Any]] = field(default_factory=list)
    deep_dive_templates: List[Dict[str, Any]] = field(default_factory=list)
    woven_confirmation_templates: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def load(cls, industry: str) -> "IndustryQuestionBank":
        """Load question bank for an industry."""
        # Normalize industry slug
        industry_slug = industry.lower().replace(" ", "_").replace("-", "_")

        # Also try with hyphens
        industry_slugs = [industry_slug, industry_slug.replace("_", "-")]

        for slug in industry_slugs:
            path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "knowledge",
                "industry_questions",
                f"{slug}.json"
            )

            if os.path.exists(path):
                try:
                    with open(path) as f:
                        data = json.load(f)
                        return cls(
                            industry=data.get("industry", industry),
                            display_name=data.get("display_name", industry.title()),
                            questions=data.get("questions", []),
                            deep_dive_templates=data.get("deep_dive_templates", []),
                            woven_confirmation_templates=data.get("woven_confirmation_templates", []),
                        )
                except Exception as e:
                    logger.warning(f"Failed to load industry questions from {path}: {e}")

        # Return empty bank if not found
        logger.info(f"No question bank found for industry: {industry}")
        return cls(industry=industry, display_name=industry.title())

    def get_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific question by ID."""
        for q in self.questions:
            if q.get("id") == question_id:
                return q
        return None

    def get_questions_for_category(
        self,
        category: ConfidenceCategory,
        exclude_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get questions that target a specific category."""
        exclude_ids = exclude_ids or []
        result = []
        # Handle both enum and string category
        category_str = category.value if hasattr(category, 'value') else str(category)
        for q in self.questions:
            if q.get("id") in exclude_ids:
                continue
            targets = q.get("target_categories", [])
            if category_str in targets:
                result.append(q)
        # Sort by priority (lower = higher priority)
        return sorted(result, key=lambda x: x.get("priority", 99))

    def get_deep_dive_for_answer(
        self,
        question_id: str,
        answer_value: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check if the answer triggers a predefined deep dive.

        Args:
            question_id: The ID of the question that was answered
            answer_value: The value selected/entered by user

        Returns:
            Deep dive template if triggered, None otherwise
        """
        for template in self.deep_dive_templates:
            if template.get("trigger_question") == question_id:
                trigger_values = template.get("trigger_values", [])
                if answer_value in trigger_values:
                    return template
        return None

    def get_woven_confirmation(
        self,
        research_facts: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Get a woven confirmation template that matches known research facts.

        Args:
            research_facts: Dict of facts from research (e.g., {"tech_stack.practice_management": "Dentrix"})

        Returns:
            Woven confirmation template with interpolated values
        """
        for template in self.woven_confirmation_templates:
            condition = template.get("condition", "")
            # Check if the condition field exists in research facts
            if condition in research_facts and research_facts[condition]:
                # Create a copy with interpolated template
                result = template.copy()
                question = template.get("template", "")
                # Replace template variables
                for key, value in research_facts.items():
                    question = question.replace(f"{{{key}}}", str(value))
                result["question"] = question
                return result
        return None

    def to_question_list_for_prompt(self, max_questions: int = 5) -> str:
        """Format questions for inclusion in AI prompt."""
        if not self.questions:
            return "No industry-specific questions available."

        lines = []
        for q in self.questions[:max_questions]:
            targets = ", ".join(q.get("target_categories", []))
            lines.append(f"- [{q['id']}] {q['question']} (targets: {targets})")
        return "\n".join(lines)


def get_available_industries() -> List[str]:
    """List all industries with question banks."""
    questions_dir = os.path.join(
        os.path.dirname(__file__),
        "..",
        "knowledge",
        "industry_questions"
    )

    industries = []
    if os.path.exists(questions_dir):
        for filename in os.listdir(questions_dir):
            if filename.endswith(".json"):
                industries.append(filename.replace(".json", ""))

    return sorted(industries)


# ============================================================================
# Answer Analyzer
# ============================================================================

class AnswerAnalyzer:
    """
    Analyzes user answers to extract facts and determine confidence boosts.

    Uses a fast AI model (Haiku) to parse answers and extract:
    - Explicit facts (numbers, tools, processes)
    - Pain signals worth exploring
    - Quantifiable metrics
    - Sentiment and urgency
    """

    ANALYSIS_PROMPT = """Analyze this answer from a business discovery interview.

QUESTION ASKED: {question}
QUESTION TARGETS: {target_categories}
USER'S ANSWER: {answer}

COMPANY CONTEXT:
- Name: {company_name}
- Industry: {industry}
- Size: {company_size}

Your task: Extract actionable insights from this answer.

## EXTRACTION RULES

1. **Explicit Facts**: Look for concrete information
   - Numbers: employees, hours, costs, volumes
   - Tools: software, platforms, systems mentioned
   - Processes: workflows, procedures described
   - People: roles, team structures

2. **Pain Signals**: Indicators of frustration or problems
   - Words like: "frustrated", "waste", "slow", "manual", "nightmare"
   - Time drains: "hours each week", "takes forever"
   - Cost concerns: "expensive", "costs us"

3. **Quantifiable Metrics**: Numbers we can use for ROI
   - Time: "20 hours/week on admin"
   - Money: "$5000/month on contractors"
   - Volume: "50 leads/month", "100 patients/week"

4. **Deep Dive Decision**: Should we explore this further?
   - Yes if: specific pain mentioned, interesting process revealed, surprising detail
   - No if: generic answer, already covered, low signal

## OUTPUT FORMAT (JSON only, no markdown)
{{
  "extracted_facts": {{
    "company_basics": [{{"fact": "description", "value": "extracted value", "confidence": "high|medium|low"}}],
    "tech_stack": [...],
    "pain_points": [...],
    "operations": [...],
    "goals_priorities": [...],
    "quantifiable_metrics": [...],
    "industry_context": [...],
    "buying_signals": [...]
  }},
  "confidence_boosts": {{
    "pain_points": 20,
    "operations": 15
  }},
  "detected_signals": ["pain_signal", "quantifiable", "urgency"],
  "should_deep_dive": true,
  "deep_dive_topic": "their call handling process",
  "sentiment": "frustrated"
}}

IMPORTANT:
- Only include categories where you found relevant information
- confidence_boosts should reflect how much this answer helps (0-30 per category)
- detected_signals can include: pain_signal, urgency, budget_mention, quantifiable, tool_mention, process_detail
- sentiment is: frustrated, neutral, or enthusiastic

Analyze the answer now:"""

    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        # Use Haiku for fast analysis
        self.model = "claude-haiku-4-5-20251001"

    async def analyze(
        self,
        answer: str,
        question: AdaptiveQuestion,
        profile: CompanyProfile,
    ) -> AnswerAnalysis:
        """
        Analyze a user's answer and extract insights.

        Args:
            answer: The user's answer text
            question: The question that was asked
            profile: Company profile from research

        Returns:
            AnswerAnalysis with extracted facts and confidence boosts
        """
        try:
            # Build context from profile
            company_name = "Unknown"
            industry = "Unknown"
            company_size = "Unknown"

            if profile.basics and profile.basics.name:
                name_val = profile.basics.name
                company_name = name_val.value if hasattr(name_val, 'value') else str(name_val)

            if profile.industry and profile.industry.primary_industry:
                ind_val = profile.industry.primary_industry
                industry = ind_val.value if hasattr(ind_val, 'value') else str(ind_val)

            if profile.size and profile.size.employee_range:
                size_val = profile.size.employee_range
                company_size = size_val.value if hasattr(size_val, 'value') else str(size_val)

            prompt = self.ANALYSIS_PROMPT.format(
                question=question.question,
                target_categories=", ".join(question.target_categories),
                answer=answer,
                company_name=company_name,
                industry=industry,
                company_size=company_size,
            )

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse response
            response_text = response.content[0].text
            data = self._extract_json(response_text)

            # Convert to AnswerAnalysis
            extracted_facts: Dict[ConfidenceCategory, List[ExtractedFact]] = {}
            for cat_str, facts in data.get("extracted_facts", {}).items():
                try:
                    category = ConfidenceCategory(cat_str)
                    extracted_facts[category] = [
                        ExtractedFact(
                            fact=f.get("fact", ""),
                            value=f.get("value"),
                            confidence=f.get("confidence", "medium"),
                            source="quiz",
                        )
                        for f in facts
                    ]
                except ValueError:
                    logger.warning(f"Unknown category in analysis: {cat_str}")

            confidence_boosts: Dict[ConfidenceCategory, int] = {}
            for cat_str, boost in data.get("confidence_boosts", {}).items():
                try:
                    category = ConfidenceCategory(cat_str)
                    confidence_boosts[category] = min(30, int(boost))  # Cap at 30
                except (ValueError, TypeError):
                    logger.warning(f"Invalid confidence boost: {cat_str}={boost}")

            return AnswerAnalysis(
                extracted_facts=extracted_facts,
                confidence_boosts=confidence_boosts,
                detected_signals=data.get("detected_signals", []),
                should_deep_dive=data.get("should_deep_dive", False),
                deep_dive_topic=data.get("deep_dive_topic"),
                sentiment=data.get("sentiment", "neutral"),
                raw_extraction=data,
            )

        except Exception as e:
            logger.error(f"Answer analysis failed: {e}")
            # Return empty analysis on failure
            return AnswerAnalysis(
                extracted_facts={},
                confidence_boosts={},
                detected_signals=[],
                should_deep_dive=False,
                sentiment="neutral",
            )

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from response text."""
        import re

        # Try to find JSON block
        json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try raw JSON
        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        logger.warning("Could not extract JSON from analysis response")
        return {}


# ============================================================================
# Question Generator
# ============================================================================

class QuestionGenerator:
    """
    Generates adaptive questions based on confidence gaps and research.

    Uses research findings as context to ask personalized questions
    that fill knowledge gaps efficiently.
    """

    GENERATION_PROMPT = """You are an expert business analyst conducting a personalized discovery interview.
Your goal is to fill knowledge gaps efficiently while building rapport.

## COMPANY PROFILE
{profile_summary}

## CURRENT CONFIDENCE SCORES
{confidence_summary}

## BIGGEST GAPS (prioritize these)
{gaps}

## CONVERSATION SO FAR
{conversation_history}

## LAST ANSWER (if any)
{last_answer}

## INDUSTRY QUESTION BANK (use if relevant)
{industry_questions}

## YOUR TASK
Generate the next question following these rules:

### QUESTION STYLE RULES
1. NEVER ask what we already know with high confidence
2. WEAVE confirmations into discovery: "Since you're using [tool], how's that working for [use case]?"
3. BE SPECIFIC to their business - use their company name and industry
4. USE THEIR LANGUAGE from previous answers if available
5. KEEP IT CONVERSATIONAL, not interrogative
6. ONE QUESTION at a time (may have brief acknowledgment first)

### QUESTION TYPE GUIDANCE
- Use "structured" + "select/multi_select" for factual gaps (tools, size)
- Use "voice" for discovery questions (pain points, goals, operations)
- Use "number" for quantifiable metrics

### OUTPUT FORMAT (JSON only)
{{
  "acknowledgment": "Brief, natural response to last answer (null if first question)",
  "question": "The question to ask",
  "question_type": "structured|voice",
  "input_type": "text|number|select|multi_select|scale|voice",
  "options": [{{"value": "option_id", "label": "Option Label"}}],
  "target_categories": ["pain_points", "operations"],
  "expected_boosts": {{"pain_points": 20, "operations": 15}},
  "rationale": "Why asking this now"
}}

Generate a question that feels natural and specific to this business."""

    DEEP_DIVE_PROMPT = """The user just revealed something worth exploring deeper.

THEIR ANSWER: {last_answer}
TOPIC TO EXPLORE: {topic}
COMPANY: {company_name}

Generate a natural follow-up that:
1. Acknowledges what they said (use their exact words if notable)
2. Goes deeper on the specific pain or opportunity
3. Tries to get quantifiable details (hours, costs, frequency)

Keep it conversational, not interrogative.

OUTPUT FORMAT (JSON only):
{{
  "acknowledgment": "Empathetic response using their words",
  "question": "The follow-up question",
  "question_type": "voice",
  "input_type": "voice",
  "target_categories": ["pain_points", "quantifiable_metrics"],
  "expected_boosts": {{"pain_points": 25, "quantifiable_metrics": 15}},
  "rationale": "Deep diving on: {topic}"
}}"""

    def __init__(self, profile: CompanyProfile, industry: str):
        self.profile = profile
        self.industry = industry
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-5-20250929"  # Smarter model for generation
        self.conversation_history: List[Dict[str, Any]] = []
        self.asked_question_ids: List[str] = []  # Track which industry questions we've asked

        # Load full industry question bank
        self.question_bank = IndustryQuestionBank.load(industry)
        # Keep backward compatibility
        self.industry_questions = self.question_bank.questions

    def get_next_industry_question(
        self,
        confidence: ConfidenceState,
        last_question_id: Optional[str] = None,
        last_answer_value: Optional[str] = None,
    ) -> Optional[AdaptiveQuestion]:
        """
        Get the next industry-specific question from the question bank.

        Prioritizes:
        1. Deep dive questions if answer triggers one
        2. Questions targeting the biggest gaps
        3. Questions not yet asked

        Returns None if no suitable question found.
        """
        # Check for triggered deep dive
        if last_question_id and last_answer_value:
            deep_dive = self.question_bank.get_deep_dive_for_answer(
                last_question_id, last_answer_value
            )
            if deep_dive:
                return self._convert_template_to_question(deep_dive, is_deep_dive=True)

        # Get biggest gap
        sorted_gaps = confidence.get_sorted_gaps()
        if not sorted_gaps:
            return None

        # Find a question targeting the biggest gap
        for gap_category in sorted_gaps[:3]:
            questions = self.question_bank.get_questions_for_category(
                gap_category,
                exclude_ids=self.asked_question_ids
            )
            if questions:
                q = questions[0]
                self.asked_question_ids.append(q["id"])
                return self._convert_bank_question(q)

        return None

    def _convert_bank_question(self, q: Dict[str, Any]) -> AdaptiveQuestion:
        """Convert a question bank entry to AdaptiveQuestion."""
        target_cats = []
        for cat_str in q.get("target_categories", []):
            try:
                target_cats.append(ConfidenceCategory(cat_str))
            except ValueError:
                pass

        expected_boosts = {}
        for cat_str, boost in q.get("expected_boosts", {}).items():
            try:
                expected_boosts[ConfidenceCategory(cat_str)] = int(boost)
            except (ValueError, TypeError):
                pass

        return AdaptiveQuestion(
            id=q.get("id", f"iq_{uuid.uuid4().hex[:8]}"),
            question=q.get("question", ""),
            question_type="structured" if q.get("input_type") in ["select", "multi_select", "number"] else "voice",
            input_type=q.get("input_type", "voice"),
            options=q.get("options"),
            placeholder=q.get("placeholder"),
            target_categories=target_cats,
            expected_boosts=expected_boosts,
            rationale=f"Industry question: {q.get('id')}",
            is_deep_dive=False,
            industry=self.industry,
        )

    def _convert_template_to_question(
        self,
        template: Dict[str, Any],
        is_deep_dive: bool = False
    ) -> AdaptiveQuestion:
        """Convert a template (deep dive or woven) to AdaptiveQuestion."""
        target_cats = []
        for cat_str in template.get("target_categories", []):
            try:
                target_cats.append(ConfidenceCategory(cat_str))
            except ValueError:
                pass

        expected_boosts = {}
        for cat_str, boost in template.get("expected_boosts", {}).items():
            try:
                expected_boosts[ConfidenceCategory(cat_str)] = int(boost)
            except (ValueError, TypeError):
                pass

        return AdaptiveQuestion(
            id=template.get("id", f"tpl_{uuid.uuid4().hex[:8]}"),
            question=template.get("template", template.get("question", "")),
            question_type="voice",
            input_type="voice",
            target_categories=target_cats,
            expected_boosts=expected_boosts,
            rationale=f"Template: {template.get('id', 'unknown')}",
            is_deep_dive=is_deep_dive,
            industry=self.industry,
        )

    async def generate_next_question(
        self,
        confidence: ConfidenceState,
        last_answer: Optional[str] = None,
        last_analysis: Optional[AnswerAnalysis] = None,
    ) -> AdaptiveQuestion:
        """
        Generate the next question based on current state.

        Args:
            confidence: Current confidence state
            last_answer: The user's last answer (if any)
            last_analysis: Analysis of last answer (if any)

        Returns:
            AdaptiveQuestion to ask next
        """
        # Check if we should deep dive on last answer
        if last_analysis and last_analysis.should_deep_dive:
            return await self._generate_deep_dive(
                last_answer or "",
                last_analysis.deep_dive_topic or "this topic",
            )

        # Check if all thresholds met
        if confidence.ready_for_teaser:
            return self._generate_wrap_up(confidence)

        # Otherwise, generate from gaps
        return await self._generate_gap_question(confidence, last_answer)

    async def _generate_gap_question(
        self,
        confidence: ConfidenceState,
        last_answer: Optional[str] = None,
    ) -> AdaptiveQuestion:
        """Generate question targeting biggest gaps."""
        sorted_gaps = confidence.get_sorted_gaps()

        prompt = self.GENERATION_PROMPT.format(
            profile_summary=self._format_profile(),
            confidence_summary=self._format_confidence(confidence),
            gaps=[g.value for g in sorted_gaps[:3]],
            conversation_history=self._format_conversation(),
            last_answer=last_answer or "(First question)",
            industry_questions=json.dumps(self.industry_questions[:3], indent=2),
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text
            data = self._extract_json(response_text)

            # Parse target categories
            target_cats = []
            for cat_str in data.get("target_categories", []):
                try:
                    target_cats.append(ConfidenceCategory(cat_str))
                except ValueError:
                    pass

            # Parse expected boosts
            expected_boosts = {}
            for cat_str, boost in data.get("expected_boosts", {}).items():
                try:
                    expected_boosts[ConfidenceCategory(cat_str)] = int(boost)
                except (ValueError, TypeError):
                    pass

            question = AdaptiveQuestion(
                id=f"q_{uuid.uuid4().hex[:8]}",
                question=data.get("question", "Tell me more about your business."),
                acknowledgment=data.get("acknowledgment"),
                question_type=data.get("question_type", "voice"),
                input_type=data.get("input_type", "voice"),
                options=data.get("options"),
                target_categories=target_cats or [sorted_gaps[0]] if sorted_gaps else [],
                expected_boosts=expected_boosts,
                rationale=data.get("rationale", ""),
                is_deep_dive=False,
                industry=self.industry,
            )

            # Track in conversation history
            self.conversation_history.append({
                "question": question.question,
                "target": [c.value for c in question.target_categories],
            })

            return question

        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            # Return fallback question
            return self._generate_fallback_question(sorted_gaps)

    async def _generate_deep_dive(
        self,
        last_answer: str,
        topic: str,
    ) -> AdaptiveQuestion:
        """Generate a follow-up question exploring a signal."""
        company_name = "your company"
        if self.profile.basics and self.profile.basics.name:
            name_val = self.profile.basics.name
            company_name = name_val.value if hasattr(name_val, 'value') else str(name_val)

        prompt = self.DEEP_DIVE_PROMPT.format(
            last_answer=last_answer,
            topic=topic,
            company_name=company_name,
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text
            data = self._extract_json(response_text)

            # Parse categories
            target_cats = []
            for cat_str in data.get("target_categories", ["pain_points"]):
                try:
                    target_cats.append(ConfidenceCategory(cat_str))
                except ValueError:
                    pass

            expected_boosts = {}
            for cat_str, boost in data.get("expected_boosts", {}).items():
                try:
                    expected_boosts[ConfidenceCategory(cat_str)] = int(boost)
                except (ValueError, TypeError):
                    pass

            return AdaptiveQuestion(
                id=f"dd_{uuid.uuid4().hex[:8]}",
                question=data.get("question", f"Tell me more about {topic}."),
                acknowledgment=data.get("acknowledgment"),
                question_type="voice",
                input_type="voice",
                target_categories=target_cats,
                expected_boosts=expected_boosts,
                rationale=f"Deep diving on: {topic}",
                is_deep_dive=True,
                industry=self.industry,
            )

        except Exception as e:
            logger.error(f"Deep dive generation failed: {e}")
            return AdaptiveQuestion(
                id=f"dd_{uuid.uuid4().hex[:8]}",
                question=f"That's interesting. Can you tell me more about {topic}?",
                acknowledgment="I'd like to understand this better.",
                question_type="voice",
                input_type="voice",
                target_categories=[ConfidenceCategory.PAIN_POINTS],
                expected_boosts={ConfidenceCategory.PAIN_POINTS: 15},
                rationale=f"Deep diving on: {topic}",
                is_deep_dive=True,
            )

    def _generate_wrap_up(self, confidence: ConfidenceState) -> AdaptiveQuestion:
        """Generate closing question when all thresholds met."""
        return AdaptiveQuestion(
            id="wrap_up",
            question="Before I analyze everything - is there anything else about your situation I should know?",
            acknowledgment="This has been really helpful.",
            question_type="voice",
            input_type="voice",
            target_categories=[],
            expected_boosts={},
            rationale="All thresholds met, giving chance for final input",
            is_deep_dive=False,
        )

    def _generate_fallback_question(
        self,
        gaps: List[ConfidenceCategory],
    ) -> AdaptiveQuestion:
        """Generate a fallback question if AI generation fails."""
        # Fallback questions per category
        fallbacks = {
            ConfidenceCategory.PAIN_POINTS: (
                "What's the biggest challenge you face in your day-to-day operations?",
                "voice",
            ),
            ConfidenceCategory.OPERATIONS: (
                "Can you walk me through a typical workday for your team?",
                "voice",
            ),
            ConfidenceCategory.TECH_STACK: (
                "What are the main software tools your team relies on?",
                "voice",
            ),
            ConfidenceCategory.GOALS_PRIORITIES: (
                "What would success look like for your business in the next 12 months?",
                "voice",
            ),
            ConfidenceCategory.QUANTIFIABLE_METRICS: (
                "How much time does your team spend on repetitive tasks each week?",
                "voice",
            ),
            ConfidenceCategory.INDUSTRY_CONTEXT: (
                "What makes your business different from others in your industry?",
                "voice",
            ),
            ConfidenceCategory.BUYING_SIGNALS: (
                "What's your timeline for making improvements to your operations?",
                "voice",
            ),
            ConfidenceCategory.COMPANY_BASICS: (
                "Tell me a bit more about what your company does.",
                "voice",
            ),
        }

        target = gaps[0] if gaps else ConfidenceCategory.PAIN_POINTS
        question_text, input_type = fallbacks.get(
            target,
            ("What else should I know about your business?", "voice")
        )

        return AdaptiveQuestion(
            id=f"fb_{uuid.uuid4().hex[:8]}",
            question=question_text,
            question_type="voice",
            input_type=input_type,
            target_categories=[target],
            expected_boosts={target: 20},
            rationale="Fallback question for gap",
        )

    def _format_profile(self) -> str:
        """Format company profile for prompt."""
        lines = []

        if self.profile.basics:
            if self.profile.basics.name:
                name_val = self.profile.basics.name
                name = name_val.value if hasattr(name_val, 'value') else str(name_val)
                lines.append(f"Company: {name}")

            if self.profile.basics.description:
                desc_val = self.profile.basics.description
                desc = desc_val.value if hasattr(desc_val, 'value') else str(desc_val)
                lines.append(f"Description: {desc[:200]}...")

        if self.profile.size and self.profile.size.employee_range:
            size_val = self.profile.size.employee_range
            size = size_val.value if hasattr(size_val, 'value') else str(size_val)
            lines.append(f"Size: {size} employees")

        if self.profile.industry:
            if self.profile.industry.primary_industry:
                ind_val = self.profile.industry.primary_industry
                ind = ind_val.value if hasattr(ind_val, 'value') else str(ind_val)
                lines.append(f"Industry: {ind}")

        if self.profile.tech_stack and self.profile.tech_stack.technologies_detected:
            techs = []
            for t in self.profile.tech_stack.technologies_detected[:5]:
                tech_val = t.value if hasattr(t, 'value') else str(t)
                techs.append(tech_val)
            if techs:
                lines.append(f"Tools detected: {', '.join(techs)}")

        return "\n".join(lines) if lines else "Limited research available"

    def _format_confidence(self, confidence: ConfidenceState) -> str:
        """Format confidence scores for prompt."""
        lines = []
        for cat in ConfidenceCategory:
            score = confidence.scores.get(cat, 0)
            threshold = CONFIDENCE_THRESHOLDS[cat]
            status = "OK" if score >= threshold else f"GAP (-{threshold - score})"
            lines.append(f"{CATEGORY_LABELS[cat]}: {score}% / {threshold}% {status}")
        return "\n".join(lines)

    def _format_conversation(self) -> str:
        """Format conversation history for prompt."""
        if not self.conversation_history:
            return "(First question)"
        return "\n".join([
            f"Q: {item['question']}"
            for item in self.conversation_history[-5:]
        ])

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from response text."""
        import re

        json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        logger.warning("Could not extract JSON from generation response")
        return {}


# ============================================================================
# Convenience Functions
# ============================================================================

async def analyze_answer(
    answer: str,
    question: AdaptiveQuestion,
    profile: CompanyProfile,
) -> AnswerAnalysis:
    """Convenience function to analyze an answer."""
    analyzer = AnswerAnalyzer()
    return await analyzer.analyze(answer, question, profile)
