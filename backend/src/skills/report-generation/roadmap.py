"""
Roadmap Skill

Generates implementation roadmap from recommendations.

This skill:
1. Takes a list of recommendations from the CRB analysis
2. Generates short-term, mid-term, and long-term action items
3. Enhances with expertise data (industry-specific timelines, common pitfalls)
4. Returns structured roadmap with actionable items

Output Schema:
{
    "short_term": [
        {
            "title": "Set up Calendly for online booking",
            "description": "Replace phone-based scheduling with...",
            "timeline": "Week 1-2",
            "expected_outcome": "50% of bookings online within 2 weeks",
            "related_recommendation_id": "rec-001"
        }
    ],
    "mid_term": [...],
    "long_term": [...]
}
"""

import logging
from typing import Dict, Any, List

from src.skills.base import LLMSkill, SkillContext, SkillError

logger = logging.getLogger(__name__)


class RoadmapSkill(LLMSkill[Dict[str, Any]]):
    """
    Generate implementation roadmap from recommendations.

    Provides a phased implementation plan that prioritizes quick wins
    and sequences actions for maximum impact.
    """

    name = "roadmap-generator"
    description = "Generate implementation roadmap from recommendations"
    version = "1.0.0"

    requires_llm = True
    requires_expertise = False  # Works without but better with expertise
    requires_knowledge = False

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Generate an implementation roadmap.

        Args:
            context: SkillContext with:
                - metadata.recommendations: List of recommendation dicts
                - industry: Industry for context-aware timelines
                - expertise: Optional expertise data for calibration

        Returns:
            Roadmap dict with short_term, mid_term, long_term action items
        """
        recommendations = context.metadata.get("recommendations", [])

        if not recommendations:
            raise SkillError(
                self.name,
                "No recommendations provided in context.metadata",
                recoverable=False,
            )

        # Build expertise-enhanced prompt
        prompt = self._build_prompt(recommendations, context)
        system = self._build_system_prompt(context)

        result = await self.call_llm_json(
            prompt=prompt,
            system=system,
        )

        # Validate structure
        validated = self._validate_roadmap(result)

        return validated

    def _build_system_prompt(self, context: SkillContext) -> str:
        """Build system prompt with optional expertise calibration."""
        base = (
            "You are an expert implementation consultant creating actionable roadmaps. "
            "Prioritize quick wins first. Be specific with tool names and timelines. "
            "Every action item should be concrete enough to start immediately."
        )

        # Enhance with expertise if available
        if context.expertise:
            industry_data = context.expertise.get("industry_expertise", {})
            common_pitfalls = industry_data.get("common_pitfalls", [])
            avg_timeline = industry_data.get("avg_implementation_weeks")

            if common_pitfalls:
                pitfall_text = ", ".join(common_pitfalls[:3])
                base += f"\n\nCommon pitfalls in {context.industry}: {pitfall_text}. Account for these in your timeline."

            if avg_timeline:
                base += f"\n\nTypical implementation in {context.industry} takes ~{avg_timeline} weeks."

        return base

    def _build_prompt(
        self,
        recommendations: List[Dict[str, Any]],
        context: SkillContext,
    ) -> str:
        """Build the generation prompt."""
        import json

        # Limit recommendations to avoid token overflow
        recs_json = json.dumps(recommendations[:10], indent=2)

        expertise_guidance = ""
        if context.expertise:
            benchmarks = context.expertise.get("industry_benchmarks", {})
            if benchmarks:
                expertise_guidance = f"""

INDUSTRY BENCHMARKS ({context.industry}):
- Use these benchmarks to set realistic timelines and outcomes
- Benchmarks: {json.dumps(benchmarks, indent=2)}
"""

        return f"""Based on these recommendations, create an implementation roadmap.

INDUSTRY: {context.industry}

RECOMMENDATIONS:
{recs_json}
{expertise_guidance}
Generate a JSON roadmap with this structure:
{{
    "short_term": [
        {{
            "title": "<action item>",
            "description": "<details>",
            "timeline": "Week 1-4",
            "expected_outcome": "<what success looks like>",
            "related_recommendation_id": "<id>"
        }}
    ],
    "mid_term": [
        {{
            "title": "<action item>",
            "description": "<details>",
            "timeline": "Month 3-6",
            "expected_outcome": "<what success looks like>",
            "related_recommendation_id": "<id>"
        }}
    ],
    "long_term": [
        {{
            "title": "<action item>",
            "description": "<details>",
            "timeline": "Month 12-18",
            "expected_outcome": "<what success looks like>",
            "related_recommendation_id": "<id>"
        }}
    ]
}}

RULES:
1. Put quick wins (low effort, high impact) in short_term
2. Be specific and actionable - name exact tools, steps, timelines
3. Each item should have a clear, measurable expected_outcome
4. Link each item to a recommendation via related_recommendation_id
5. 3-5 items per category
6. Short-term: weeks 1-4, Mid-term: months 2-6, Long-term: months 6-18

Return ONLY the JSON."""

    def _validate_roadmap(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize roadmap structure."""
        default = {"short_term": [], "mid_term": [], "long_term": []}

        if not isinstance(data, dict):
            logger.warning("roadmap_invalid_structure", data_type=type(data).__name__)
            return default

        result = {}
        for key in ("short_term", "mid_term", "long_term"):
            items = data.get(key, [])
            if not isinstance(items, list):
                items = []

            # Validate each item has required fields
            validated_items = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                validated_items.append({
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "timeline": item.get("timeline", ""),
                    "expected_outcome": item.get("expected_outcome", ""),
                    "related_recommendation_id": item.get("related_recommendation_id", ""),
                })
            result[key] = validated_items

        return result


# For skill discovery
__all__ = ["RoadmapSkill"]
