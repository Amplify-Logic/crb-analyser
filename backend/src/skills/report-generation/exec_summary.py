"""
Executive Summary Skill

Generates compelling, calibrated executive summaries for CRB reports.

This skill:
1. Analyzes quiz/interview data to extract key insights
2. Scores AI readiness, customer value, and business health
3. Uses expertise data to calibrate scores to industry norms
4. Identifies top opportunities and what NOT to recommend
5. Provides honest, actionable assessments

Output Schema:
{
    "ai_readiness_score": int (0-100),
    "customer_value_score": float (1-10),
    "business_health_score": float (1-10),
    "key_insight": str,
    "total_value_potential": {"min": int, "max": int, "projection_years": int},
    "top_opportunities": [{"title": str, "value_potential": str, "time_horizon": str}],
    "not_recommended": [{"title": str, "reason": str}],
    "recommended_investment": {"year_1_min": int, "year_1_max": int},
    "report_date": str,
    "industry_context": {...}  # Optional, if expertise available
}
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from src.skills.base import LLMSkill, SkillContext, SkillError

logger = logging.getLogger(__name__)


class ExecSummarySkill(LLMSkill[Dict[str, Any]]):
    """
    Generate executive summaries for CRB reports.

    This is an LLM-powered skill that uses Claude to synthesize
    quiz data into a compelling executive summary. When expertise
    data is available, it calibrates the output to industry norms.
    """

    name = "exec-summary"
    description = "Generate compelling, calibrated executive summaries"
    version = "1.0.0"

    requires_llm = True
    requires_expertise = False  # Works without, but better with

    # Template for consistent structure
    SUMMARY_TEMPLATE = {
        "ai_readiness_score": 50,
        "customer_value_score": 5.0,
        "business_health_score": 5.0,
        "key_insight": "",
        "total_value_potential": {"min": 10000, "max": 50000, "projection_years": 3},
        "top_opportunities": [],
        "not_recommended": [],
        "recommended_investment": {"year_1_min": 2000, "year_1_max": 10000},
    }

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Generate executive summary from context.

        Args:
            context: SkillContext with quiz_answers, industry, and optional expertise

        Returns:
            Executive summary dict matching report schema
        """
        # Extract data from context
        answers = context.quiz_answers or {}
        industry = context.industry
        expertise = context.expertise or {}
        interview_data = context.interview_data or {}

        # Build expertise context for calibration
        expertise_context = self._build_expertise_context(expertise, industry)

        # Generate the summary using LLM
        summary = await self._generate_summary(
            answers=answers,
            industry=industry,
            expertise_context=expertise_context,
            interview_data=interview_data,
        )

        # Apply expertise calibration if available
        if expertise:
            summary = self._calibrate_with_expertise(summary, expertise)

        # Add metadata
        summary["report_date"] = datetime.utcnow().strftime("%B %d, %Y")

        if expertise_context.get("has_data"):
            summary["industry_context"] = {
                "analyses_in_industry": expertise_context.get("total_analyses", 0),
                "confidence": expertise_context.get("confidence", "low"),
                "avg_ai_readiness": expertise_context.get("avg_ai_readiness"),
            }

        return summary

    def _build_expertise_context(
        self,
        expertise: Dict[str, Any],
        industry: str
    ) -> Dict[str, Any]:
        """
        Build expertise context for prompt injection.

        Extracts relevant expertise data for the LLM to use.
        """
        industry_expertise = expertise.get("industry_expertise", {})

        if not industry_expertise or industry_expertise.get("total_analyses", 0) == 0:
            return {"has_data": False}

        return {
            "has_data": True,
            "total_analyses": industry_expertise.get("total_analyses", 0),
            "confidence": industry_expertise.get("confidence", "low"),
            "avg_ai_readiness": industry_expertise.get("avg_ai_readiness", 50),
            "avg_potential_savings": industry_expertise.get("avg_potential_savings", 0),
            "common_pain_points": list(
                industry_expertise.get("pain_points", {}).keys()
            )[:5],
            "effective_patterns": [
                p.get("recommendation", "") if isinstance(p, dict) else str(p)
                for p in industry_expertise.get("effective_patterns", [])[:3]
            ],
            "anti_patterns": industry_expertise.get("anti_patterns", [])[:3],
        }

    async def _generate_summary(
        self,
        answers: Dict[str, Any],
        industry: str,
        expertise_context: Dict[str, Any],
        interview_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate the executive summary using Claude.
        """
        # Build expertise injection for prompt
        expertise_injection = ""
        if expertise_context.get("has_data"):
            expertise_injection = f"""
INDUSTRY EXPERTISE (from {expertise_context['total_analyses']} previous analyses):
- Average AI readiness in {industry}: {expertise_context['avg_ai_readiness']:.0f}/100
- Common pain points: {', '.join(expertise_context['common_pain_points'][:3]) or 'None recorded'}
- What works well: {', '.join(expertise_context['effective_patterns'][:2]) or 'No patterns yet'}
- What to avoid: {', '.join(expertise_context['anti_patterns'][:2]) or 'No anti-patterns yet'}
- Confidence level: {expertise_context['confidence']}

Use this expertise to calibrate your assessment. If the client's AI readiness
is significantly different from industry average, note this in key_insight.
"""

        # Build interview context if available
        interview_injection = ""
        if interview_data:
            messages = interview_data.get("messages", [])
            topics = interview_data.get("topics_covered", [])
            if messages:
                # Extract key points from interview
                interview_injection = f"""
INTERVIEW INSIGHTS:
- Topics covered: {', '.join(topics) if topics else 'General'}
- Key quotes from interview: (summarized from {len(messages)} messages)
"""

        prompt = f"""Generate an executive summary for a CRB (Cost/Risk/Benefit) Analysis report.

QUIZ ANSWERS:
{json.dumps(answers, indent=2)}

INDUSTRY: {industry}
{expertise_injection}
{interview_injection}

Generate a JSON executive summary with this EXACT structure:
{{
    "ai_readiness_score": <number 0-100, based on current tech adoption and team readiness>,
    "customer_value_score": <number 1-10, how AI would benefit their customers>,
    "business_health_score": <number 1-10, how AI would improve operations>,
    "key_insight": "<one compelling sentence - the main takeaway>",
    "total_value_potential": {{
        "min": <conservative estimate in euros>,
        "max": <optimistic estimate in euros>,
        "projection_years": 3
    }},
    "top_opportunities": [
        {{
            "title": "<specific opportunity name>",
            "value_potential": "<range like €10K-20K/year>",
            "time_horizon": "short|mid|long"
        }}
    ],
    "not_recommended": [
        {{
            "title": "<what they should NOT do>",
            "reason": "<honest reason why>"
        }}
    ],
    "recommended_investment": {{
        "year_1_min": <conservative first-year investment>,
        "year_1_max": <maximum first-year investment>
    }}
}}

REQUIREMENTS:
1. Be HONEST and REALISTIC - don't oversell
2. Include at least ONE "not_recommended" item
3. Make key_insight specific to their situation, not generic
4. If expertise data suggests their scores differ from industry average, mention it
5. Top opportunities should be actionable and specific

Return ONLY the JSON, no explanation or markdown."""

        try:
            response = await self.call_llm_json(
                prompt=prompt,
                system=self._get_system_prompt(),
            )

            # Validate and fill in missing fields
            return self._validate_summary(response)

        except SkillError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate executive summary: {e}")
            # Return default with error indication
            default = self.SUMMARY_TEMPLATE.copy()
            default["key_insight"] = "Analysis completed with limited data."
            return default

    def _get_system_prompt(self) -> str:
        """Get the system prompt for executive summary generation."""
        return """You are an expert AI business consultant generating executive summaries for CRB Analysis reports.

Your role is to be an honest advisor - like a trusted consultant who tells clients what they need to hear, not what they want to hear.

Key principles:
1. HONEST ASSESSMENT: Never oversell. If AI isn't a good fit, say so.
2. SPECIFIC INSIGHTS: Generic insights are useless. Be specific to their situation.
3. CALIBRATED SCORING: Use industry expertise when available to calibrate scores.
4. ACTIONABLE: Every recommendation should be something they can act on.
5. INCLUDE WARNINGS: Always include what they should NOT do.

Score Guidelines:
- AI Readiness (0-100): Current state, not potential. 70+ = AI-ready, 50-69 = needs prep, <50 = significant gaps
- Customer Value (1-10): How much would AI improve their customer experience? 8+ = transformative
- Business Health (1-10): How much would AI improve operations/margins? 8+ = significant impact"""

    def _validate_summary(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fill in missing fields with defaults."""
        result = self.SUMMARY_TEMPLATE.copy()

        # Copy over valid fields
        if isinstance(summary.get("ai_readiness_score"), (int, float)):
            result["ai_readiness_score"] = int(
                max(0, min(100, summary["ai_readiness_score"]))
            )

        if isinstance(summary.get("customer_value_score"), (int, float)):
            result["customer_value_score"] = float(
                max(1, min(10, summary["customer_value_score"]))
            )

        if isinstance(summary.get("business_health_score"), (int, float)):
            result["business_health_score"] = float(
                max(1, min(10, summary["business_health_score"]))
            )

        if isinstance(summary.get("key_insight"), str) and summary["key_insight"]:
            result["key_insight"] = summary["key_insight"]

        if isinstance(summary.get("total_value_potential"), dict):
            result["total_value_potential"] = {
                "min": summary["total_value_potential"].get("min", 10000),
                "max": summary["total_value_potential"].get("max", 50000),
                "projection_years": summary["total_value_potential"].get("projection_years", 3),
            }

        if isinstance(summary.get("top_opportunities"), list):
            result["top_opportunities"] = summary["top_opportunities"][:5]

        if isinstance(summary.get("not_recommended"), list):
            result["not_recommended"] = summary["not_recommended"]

        if isinstance(summary.get("recommended_investment"), dict):
            result["recommended_investment"] = {
                "year_1_min": summary["recommended_investment"].get("year_1_min", 2000),
                "year_1_max": summary["recommended_investment"].get("year_1_max", 10000),
            }

        return result

    def _calibrate_with_expertise(
        self,
        summary: Dict[str, Any],
        expertise: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calibrate summary scores using expertise data.

        When we have enough industry data, we can adjust scores
        to be more accurate relative to what we've seen before.
        """
        industry_expertise = expertise.get("industry_expertise", {})

        if not industry_expertise or industry_expertise.get("total_analyses", 0) < 5:
            # Not enough data for calibration
            return summary

        confidence = industry_expertise.get("confidence", "low")
        if confidence == "low":
            return summary

        # Get industry averages
        avg_readiness = industry_expertise.get("avg_ai_readiness", 50)

        # Add comparison context to key insight if significantly different
        current_readiness = summary.get("ai_readiness_score", 50)
        diff = current_readiness - avg_readiness

        if abs(diff) >= 15:
            direction = "above" if diff > 0 else "below"
            current_insight = summary.get("key_insight", "")

            if not any(word in current_insight.lower() for word in ["industry", "average", "compared"]):
                # Append industry comparison
                comparison = f" (Your AI readiness is {abs(diff):.0f} points {direction} industry average.)"
                summary["key_insight"] = current_insight.rstrip(".") + comparison

        return summary


# For skill discovery
__all__ = ["ExecSummarySkill"]
