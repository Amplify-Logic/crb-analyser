"""
Interview Confidence Skill

Analyzes interview transcripts to calculate confidence scores per topic
and determine overall readiness for report generation.

This skill:
1. Segments the transcript by topic
2. Scores each topic on 4 dimensions (coverage, depth, specificity, actionability)
3. Extracts quality indicators (pain points, impacts, tools, budget)
4. Calculates overall readiness with weighted scoring
5. Determines if interview is ready for report generation

Output Schema:
{
    "topic_confidences": {
        "current_challenges": {...},
        "business_goals": {...},
        ...
    },
    "quality_indicators": {...},
    "overall_readiness": {...},
    "trigger_decision": {...}
}
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional

from src.skills.base import LLMSkill, SkillContext, SkillError
from src.models.interview_confidence import (
    TopicConfidence,
    TopicID,
    QualityIndicators,
    OverallReadiness,
    InterviewCompletionTrigger,
    TOPIC_WEIGHTS,
)

logger = logging.getLogger(__name__)


# Topic definitions with keywords for matching
TOPIC_DEFINITIONS = {
    TopicID.CURRENT_CHALLENGES: {
        "name": "Current Challenges",
        "keywords": [
            "challenge", "problem", "issue", "frustration", "pain", "struggle",
            "difficult", "bottleneck", "waste", "inefficient", "manual", "slow",
            "error", "mistake", "complaint", "headache", "tedious", "repetitive"
        ],
        "probing_indicators": [
            "how often", "how long", "impact", "cost", "time spent",
            "when did", "example", "specific", "describe"
        ],
    },
    TopicID.BUSINESS_GOALS: {
        "name": "Business Goals",
        "keywords": [
            "goal", "objective", "target", "growth", "expand", "improve",
            "increase", "reduce", "save", "achieve", "success", "vision",
            "strategy", "priority", "focus", "want to", "trying to", "plan"
        ],
        "probing_indicators": [
            "measure", "timeline", "by when", "kpi", "metric", "result"
        ],
    },
    TopicID.TEAM_OPERATIONS: {
        "name": "Team & Operations",
        "keywords": [
            "team", "staff", "employee", "workflow", "process", "operation",
            "department", "role", "responsibility", "handoff", "communication",
            "meeting", "daily", "weekly", "routine", "procedure", "step"
        ],
        "probing_indicators": [
            "who", "how many", "how long", "typical day", "walk me through"
        ],
    },
    TopicID.TECHNOLOGY: {
        "name": "Technology & Tools",
        "keywords": [
            "software", "tool", "app", "system", "platform", "technology",
            "integration", "api", "automate", "crm", "erp", "spreadsheet",
            "excel", "google", "salesforce", "hubspot", "slack", "email"
        ],
        "probing_indicators": [
            "use", "using", "integrate", "connect", "sync", "feature"
        ],
    },
    TopicID.BUDGET_TIMELINE: {
        "name": "Budget & Timeline",
        "keywords": [
            "budget", "cost", "invest", "spend", "afford", "price",
            "timeline", "deadline", "urgency", "asap", "quarter", "year",
            "month", "soon", "priority", "resource", "capacity"
        ],
        "probing_indicators": [
            "how much", "range", "willing", "allocate", "approve"
        ],
    },
}


class InterviewConfidenceSkill(LLMSkill[Dict[str, Any]]):
    """
    Analyze interview transcript and calculate confidence scores.

    This skill uses Claude to deeply analyze the conversation,
    extracting topic coverage, depth, and quality indicators.
    """

    name = "interview-confidence"
    description = "Calculate interview confidence scores and readiness"
    version = "1.0.0"

    requires_llm = True
    requires_expertise = False

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Analyze interview transcript and calculate confidence.

        Args:
            context: SkillContext with:
                - metadata.session_id: Quiz session ID
                - metadata.messages: List of interview messages
                - metadata.company_profile: Company context
                - industry: Business industry

        Returns:
            Dictionary with topic_confidences, quality_indicators,
            overall_readiness, and trigger_decision
        """
        session_id = context.metadata.get("session_id", "unknown")
        messages = context.metadata.get("messages", [])
        company_profile = context.metadata.get("company_profile", {})

        if not messages:
            raise SkillError(
                self.name,
                "No interview messages provided",
                recoverable=False
            )

        # Build transcript text for analysis
        transcript = self._build_transcript(messages)

        # Use LLM to analyze transcript deeply
        analysis = await self._analyze_transcript(
            transcript=transcript,
            company_profile=company_profile,
            industry=context.industry,
        )

        # Build topic confidences from analysis
        topic_confidences = self._build_topic_confidences(analysis, messages)

        # Build quality indicators from analysis
        quality_indicators = self._build_quality_indicators(analysis)

        # Calculate overall readiness
        readiness = OverallReadiness(
            topic_confidences=topic_confidences,
            quality_indicators=quality_indicators,
        ).calculate()

        # Make trigger decision
        trigger = InterviewCompletionTrigger(
            session_id=session_id,
            readiness=readiness,
        ).evaluate()

        logger.info(
            f"Interview confidence calculated: "
            f"score={readiness.final_score:.2f}, "
            f"level={readiness.level.value}, "
            f"ready={readiness.is_ready_for_report}"
        )

        return {
            "topic_confidences": {
                topic_id.value: tc.to_dict()
                for topic_id, tc in topic_confidences.items()
            },
            "quality_indicators": quality_indicators.to_dict(),
            "overall_readiness": readiness.to_dict(),
            "trigger_decision": trigger.to_dict(),
        }

    def _build_transcript(self, messages: List[Dict[str, str]]) -> str:
        """Build readable transcript from messages."""
        lines = []
        for msg in messages:
            role = msg.get("role", "user").upper()
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n\n".join(lines)

    async def _analyze_transcript(
        self,
        transcript: str,
        company_profile: Dict[str, Any],
        industry: str,
    ) -> Dict[str, Any]:
        """Use LLM to deeply analyze the interview transcript."""
        company_name = "the company"
        if company_profile:
            basics = company_profile.get("basics", {})
            name_obj = basics.get("name", {})
            if isinstance(name_obj, dict):
                company_name = name_obj.get("value", "the company")
            elif isinstance(name_obj, str):
                company_name = name_obj

        prompt = f"""Analyze this CRB interview transcript and extract structured data.

COMPANY: {company_name}
INDUSTRY: {industry}

TRANSCRIPT:
{transcript}

Analyze the transcript and provide a detailed JSON assessment:

{{
    "topics": {{
        "current_challenges": {{
            "discussed": true/false,
            "exchanges_count": <number of back-and-forth exchanges on this topic>,
            "specific_examples": ["list of specific examples mentioned"],
            "quantified_impacts": ["list of any numbers, hours, costs mentioned"],
            "depth_assessment": "shallow|moderate|deep",
            "key_insights": ["actionable insights extracted"]
        }},
        "business_goals": {{
            "discussed": true/false,
            "exchanges_count": <number>,
            "specific_goals": ["list of specific goals mentioned"],
            "success_metrics": ["any KPIs or success criteria mentioned"],
            "depth_assessment": "shallow|moderate|deep",
            "key_insights": ["actionable insights extracted"]
        }},
        "team_operations": {{
            "discussed": true/false,
            "exchanges_count": <number>,
            "workflows_described": ["list of workflows or processes described"],
            "bottlenecks_identified": ["specific bottlenecks mentioned"],
            "depth_assessment": "shallow|moderate|deep",
            "key_insights": ["actionable insights extracted"]
        }},
        "technology": {{
            "discussed": true/false,
            "exchanges_count": <number>,
            "tools_mentioned": ["list of specific tools/software named"],
            "integration_issues": ["any integration problems mentioned"],
            "depth_assessment": "shallow|moderate|deep",
            "key_insights": ["actionable insights extracted"]
        }},
        "budget_timeline": {{
            "discussed": true/false,
            "exchanges_count": <number>,
            "budget_range": "<specific range if mentioned, else 'not specified'>",
            "timeline_mentioned": "<specific timeline if mentioned, else 'not specified'>",
            "depth_assessment": "shallow|moderate|deep",
            "key_insights": ["actionable insights extracted"]
        }}
    }},
    "quality_extraction": {{
        "pain_points": [
            {{
                "description": "<pain point description>",
                "category": "operations|technology|communication|cost|time",
                "severity": "low|medium|high",
                "quantified": true/false
            }}
        ],
        "quantifiable_impacts": [
            "<specific number or metric mentioned, e.g., '5 hours per week on data entry'>"
        ],
        "tools_identified": ["<list of specific software/tools named>"],
        "decision_maker_signals": {{
            "is_decision_maker": true/false,
            "evidence": "<why you think this>"
        }}
    }},
    "overall_assessment": {{
        "interview_quality": "poor|fair|good|excellent",
        "information_gaps": ["<topics or areas needing more exploration>"],
        "ready_for_report": true/false,
        "readiness_reasoning": "<why ready or not ready>"
    }}
}}

Be thorough and extract as much structured data as possible.
Return ONLY the JSON, no other text."""

        try:
            response = await self.call_llm_json(
                prompt=prompt,
                system=self._get_system_prompt(),
            )
            return response
        except Exception as e:
            logger.error(f"Failed to analyze transcript: {e}")
            # Return minimal analysis on failure
            return self._get_fallback_analysis(transcript)

    def _get_system_prompt(self) -> str:
        """System prompt for transcript analysis."""
        return """You are an expert interview analyst for CRB (Cost/Risk/Benefit) business assessments.

Your task is to analyze interview transcripts and extract structured data about:
1. Topic coverage and depth
2. Specific pain points and challenges
3. Quantifiable business impacts
4. Technology and tools in use
5. Budget and timeline context

Be thorough and precise. Extract specific examples, numbers, and named entities.
When assessing depth:
- "shallow" = topic mentioned but not explored (1-2 brief exchanges)
- "moderate" = topic discussed with some detail (3-4 exchanges)
- "deep" = topic thoroughly explored with examples and specifics (5+ exchanges)

Always return valid JSON matching the requested schema."""

    def _get_fallback_analysis(self, transcript: str) -> Dict[str, Any]:
        """Fallback analysis when LLM fails."""
        # Do basic keyword-based analysis
        transcript_lower = transcript.lower()

        topics = {}
        for topic_id, defn in TOPIC_DEFINITIONS.items():
            keyword_hits = sum(
                1 for kw in defn["keywords"]
                if kw in transcript_lower
            )
            topics[topic_id.value] = {
                "discussed": keyword_hits >= 2,
                "exchanges_count": min(keyword_hits, 5),
                "specific_examples": [],
                "depth_assessment": "shallow" if keyword_hits < 3 else "moderate",
                "key_insights": [],
            }

        return {
            "topics": topics,
            "quality_extraction": {
                "pain_points": [],
                "quantifiable_impacts": [],
                "tools_identified": [],
                "decision_maker_signals": {"is_decision_maker": False, "evidence": ""},
            },
            "overall_assessment": {
                "interview_quality": "fair",
                "information_gaps": ["LLM analysis failed, using fallback"],
                "ready_for_report": False,
                "readiness_reasoning": "Fallback analysis - manual review recommended",
            },
        }

    def _build_topic_confidences(
        self,
        analysis: Dict[str, Any],
        messages: List[Dict[str, str]],
    ) -> Dict[TopicID, TopicConfidence]:
        """Build TopicConfidence objects from LLM analysis."""
        topics_data = analysis.get("topics", {})
        confidences = {}

        for topic_id in TopicID:
            topic_key = topic_id.value
            topic_analysis = topics_data.get(topic_key, {})

            # Calculate scores based on analysis
            discussed = topic_analysis.get("discussed", False)
            exchanges = topic_analysis.get("exchanges_count", 0)
            depth = topic_analysis.get("depth_assessment", "shallow")
            examples = topic_analysis.get("specific_examples", [])
            insights = topic_analysis.get("key_insights", [])

            # Coverage score (0-25)
            coverage = 25 if discussed else 0

            # Depth score (0-25) based on exchanges and depth assessment
            depth_map = {"shallow": 8, "moderate": 16, "deep": 25}
            depth_score = depth_map.get(depth, 0)
            # Adjust by exchange count
            depth_score = min(25, depth_score + min(exchanges, 5))

            # Specificity score (0-25) based on examples and quantified data
            specificity = min(25, len(examples) * 8 + len(topic_analysis.get("quantified_impacts", [])) * 5)

            # Actionability score (0-25) based on insights
            actionability = min(25, len(insights) * 8)

            # If not discussed, zero out other scores
            if not discussed:
                depth_score = 0
                specificity = 0
                actionability = 0

            confidences[topic_id] = TopicConfidence(
                topic_id=topic_id,
                topic_name=TOPIC_DEFINITIONS[topic_id]["name"],
                coverage=coverage,
                depth=depth_score,
                specificity=specificity,
                actionability=actionability,
                extracted_insights=insights,
            )

        return confidences

    def _build_quality_indicators(
        self,
        analysis: Dict[str, Any],
    ) -> QualityIndicators:
        """Build QualityIndicators from LLM analysis."""
        quality_data = analysis.get("quality_extraction", {})
        topics_data = analysis.get("topics", {})

        pain_points = quality_data.get("pain_points", [])
        impacts = quality_data.get("quantifiable_impacts", [])
        tools = quality_data.get("tools_identified", [])
        decision_maker = quality_data.get("decision_maker_signals", {})

        # Check budget clarity
        budget_data = topics_data.get("budget_timeline", {})
        budget_range = budget_data.get("budget_range", "not specified")
        budget_clarity = budget_range != "not specified" and budget_range != ""

        # Check timeline clarity
        timeline = budget_data.get("timeline_mentioned", "not specified")
        timeline_clarity = timeline != "not specified" and timeline != ""

        return QualityIndicators(
            pain_points_extracted=len(pain_points),
            quantifiable_impacts=len(impacts),
            specific_tools_mentioned=len(tools),
            budget_clarity=budget_clarity,
            timeline_clarity=timeline_clarity,
            decision_maker_identified=decision_maker.get("is_decision_maker", False),
        )


# For skill discovery
__all__ = ["InterviewConfidenceSkill"]
