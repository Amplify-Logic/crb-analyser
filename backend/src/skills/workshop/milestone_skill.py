# backend/src/skills/workshop/milestone_skill.py
"""
Milestone Synthesis Skill

Synthesizes deep-dive conversation into a draft finding with:
- Structured finding summary
- ROI calculation
- Vendor recommendations
- Confidence score

This is shown to the user after each deep-dive as a "value moment".
"""

from typing import Any, Dict, List

from src.skills.base import LLMSkill, SkillContext, SkillError


class MilestoneSynthesisSkill(LLMSkill[Dict[str, Any]]):
    """
    Synthesize deep-dive transcript into draft finding and ROI.

    Uses Sonnet for quality since this is user-facing output.
    """

    name = "milestone-synthesis"
    description = "Synthesize deep-dive into finding with ROI"
    version = "1.0.0"

    default_model = "claude-sonnet-4-20250514"  # Quality matters
    default_max_tokens = 2000

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Synthesize a deep-dive into a milestone summary.

        Args:
            context: SkillContext with metadata containing:
                - pain_point_id: ID of the pain point
                - pain_point_label: Human-readable name
                - transcript: List of conversation messages
                - company_name: Company name
                - tools_mentioned: Tools identified in conversation

        Returns:
            Dict with finding, roi, vendors, confidence
        """
        metadata = context.metadata or {}

        pain_point_id = metadata.get("pain_point_id", "unknown")
        pain_label = metadata.get("pain_point_label", "This challenge")
        transcript = metadata.get("transcript", [])
        company_name = metadata.get("company_name", "the company")
        tools = metadata.get("tools_mentioned", [])

        if not transcript:
            raise SkillError(
                self.name,
                "No transcript provided for synthesis",
                recoverable=False
            )

        prompt = self._build_prompt(
            pain_label=pain_label,
            transcript=transcript,
            company_name=company_name,
            tools=tools,
            industry=context.industry,
        )

        system = self._get_system_prompt()

        result = await self.call_llm_json(prompt, system)

        # Validate and enrich result
        result["pain_point_id"] = pain_point_id
        result["pain_point_label"] = pain_label

        return result

    def _get_system_prompt(self) -> str:
        return """You are a business analyst synthesizing discovery interview data into actionable insights.

Your output will be shown directly to the user as a "draft finding" during a workshop.
Be specific, use their exact numbers and context, and provide realistic ROI calculations.

Always return valid JSON matching the requested schema. Be conservative with ROI estimates."""

    def _build_prompt(
        self,
        pain_label: str,
        transcript: List[Dict[str, str]],
        company_name: str,
        tools: List[str],
        industry: str,
    ) -> str:
        # Format transcript
        conv = "\n".join([
            f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
            for m in transcript
        ])

        return f"""Analyze this deep-dive conversation about "{pain_label}" at {company_name} ({industry}).

CONVERSATION:
{conv}

TOOLS MENTIONED: {', '.join(tools) if tools else 'None identified'}

Synthesize into a milestone summary. Return JSON:

{{
    "finding": {{
        "title": "<Concise opportunity title>",
        "summary": "<2-3 sentence summary of the opportunity>",
        "current_process": "<How it works today, from their words>",
        "pain_severity": "low|medium|high",
        "recommendation": "<High-level recommendation>"
    }},
    "roi": {{
        "hours_per_week": <number, from their data or estimate>,
        "hourly_rate": <estimated rate based on role/industry, default 75>,
        "annual_cost": <calculated: hours_per_week * hourly_rate * 52>,
        "potential_savings": <conservative estimate, usually 60-80% of cost>,
        "savings_percentage": <percentage>,
        "calculation_notes": "<brief explanation of how you calculated this>"
    }},
    "vendors": [
        {{
            "name": "<vendor name>",
            "fit": "high|medium|low",
            "reason": "<why this vendor fits their situation>"
        }}
    ],
    "confidence": <0.0-1.0, based on specificity of data provided>,
    "data_gaps": ["<list any information that would improve accuracy>"]
}}

Use THEIR actual numbers when provided. If estimating, be conservative and note it.
Return ONLY the JSON, no other text."""
