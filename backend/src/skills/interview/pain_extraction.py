"""
Pain Extraction Skill

Extracts structured pain points from interview transcripts.

This skill:
1. Analyzes interview transcript for explicit and implicit pain points
2. Categorizes pain points by type (operational, financial, customer, etc.)
3. Scores severity and frequency based on language
4. Maps pain points to potential AI/automation solutions
5. Uses industry expertise to validate and enrich findings

Output Schema:
{
    "pain_points": [
        {
            "id": "pain-001",
            "title": "Short title",
            "description": "Detailed description",
            "category": "operational|financial|customer|technology|team|compliance",
            "severity": "high|medium|low",
            "frequency": "daily|weekly|monthly|occasionally",
            "quote": "Direct quote from transcript",
            "impact": {
                "time_hours_per_week": 0,
                "cost_per_month": 0,
                "customer_impact": "description"
            },
            "automation_potential": "high|medium|low",
            "suggested_solutions": ["solution1", "solution2"]
        }
    ],
    "themes": ["theme1", "theme2"],
    "priority_ranking": ["pain-001", "pain-002"],
    "confidence_score": 0.85
}
"""

import json
import logging
from typing import Dict, Any, List, Optional

from src.skills.base import LLMSkill, SkillContext, SkillError

logger = logging.getLogger(__name__)


# Pain point categories aligned with CRB analysis
PAIN_CATEGORIES = {
    "operational": "Day-to-day process inefficiencies",
    "financial": "Revenue leakage, cost overruns, pricing issues",
    "customer": "Customer experience and satisfaction issues",
    "technology": "Tool limitations, integration problems",
    "team": "Staff productivity, communication, skills gaps",
    "compliance": "Regulatory, quality, or risk management issues",
}

# Severity indicators in language
SEVERITY_INDICATORS = {
    "high": [
        "critical", "urgent", "constantly", "always", "major",
        "significant", "terrible", "nightmare", "killing us",
        "losing", "frustrated", "fed up", "huge problem"
    ],
    "medium": [
        "often", "regularly", "sometimes", "annoying", "issue",
        "problem", "challenging", "difficult", "struggling"
    ],
    "low": [
        "occasionally", "minor", "small", "slight", "could be better",
        "nice to have", "would help", "ideally"
    ],
}


class PainExtractionSkill(LLMSkill[Dict[str, Any]]):
    """
    Extract structured pain points from interview transcripts.

    This is an LLM-powered skill that analyzes interview conversations
    and extracts actionable pain points with severity scoring and
    solution mapping. When expertise data is available, it validates
    findings against known industry patterns.
    """

    name = "pain-extraction"
    description = "Extract structured pain points from interview transcripts"
    version = "1.0.0"

    requires_llm = True
    requires_expertise = False  # Works without, enriched with

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Extract pain points from interview transcript.

        Args:
            context: SkillContext with:
                - metadata.transcript: List of interview messages
                - metadata.company_profile: Company information
                - industry: The business industry
                - expertise: Industry expertise for validation

        Returns:
            Dictionary with pain_points and metadata
        """
        # Extract transcript
        transcript = context.metadata.get("transcript", [])
        if not transcript:
            raise SkillError(
                self.name,
                "No transcript provided in context.metadata",
                recoverable=False
            )

        # Get company context
        company_profile = context.metadata.get("company_profile", {})

        # Build expertise context
        expertise_context = self._build_expertise_context(
            context.expertise,
            context.industry
        )

        # Extract pain points
        result = await self._extract_pain_points(
            transcript=transcript,
            company_profile=company_profile,
            industry=context.industry,
            expertise_context=expertise_context,
        )

        # Validate against expertise if available
        if expertise_context.get("has_data"):
            result = self._validate_with_expertise(result, expertise_context)

        return result

    def _build_expertise_context(
        self,
        expertise: Optional[Dict[str, Any]],
        industry: str
    ) -> Dict[str, Any]:
        """Build expertise context for validation."""
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
            ),
            "pain_point_frequencies": industry_expertise.get("pain_points", {}),
            "effective_solutions": [
                p.get("recommendation", "") if isinstance(p, dict) else str(p)
                for p in industry_expertise.get("effective_patterns", [])
            ],
        }

    async def _extract_pain_points(
        self,
        transcript: List[Dict[str, str]],
        company_profile: Dict[str, Any],
        industry: str,
        expertise_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract pain points using Claude."""
        # Format transcript
        formatted_transcript = "\n".join([
            f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}"
            for msg in transcript
        ])

        # Build company context
        company_info = ""
        if company_profile:
            basics = company_profile.get("basics", {})
            company_name = basics.get("name", {}).get("value", "the company")
            company_info = f"Company: {company_name}"

        # Build expertise injection
        expertise_injection = ""
        if expertise_context.get("has_data"):
            known_pains = expertise_context.get("common_pain_points", [])
            expertise_injection = f"""
INDUSTRY EXPERTISE (from {expertise_context['total_analyses']} previous analyses):
Known pain points in {industry}:
{chr(10).join(f'- {p}' for p in known_pains[:8]) if known_pains else '- No specific patterns yet'}

VALIDATION: Check if extracted pain points align with known industry patterns.
If a pain point matches a known pattern, increase confidence.
"""

        prompt = f"""Extract structured pain points from this interview transcript.

TRANSCRIPT:
{formatted_transcript}

CONTEXT:
- Industry: {industry}
- {company_info}
{expertise_injection}

PAIN POINT CATEGORIES:
{chr(10).join(f'- {k}: {v}' for k, v in PAIN_CATEGORIES.items())}

EXTRACTION RULES:
1. Look for explicit complaints, frustrations, and challenges
2. Look for implicit issues (workarounds, time drains, manual processes)
3. Extract direct quotes when possible
4. Estimate impact based on context clues
5. Map to potential AI/automation solutions
6. Score severity based on language intensity and business impact

SEVERITY SCORING:
- HIGH: Critical business impact, frequent occurrence, strong language
- MEDIUM: Notable impact, regular occurrence
- LOW: Minor inconvenience, occasional occurrence

Generate a JSON response:
{{
    "pain_points": [
        {{
            "id": "pain-001",
            "title": "<short descriptive title>",
            "description": "<detailed description of the pain point>",
            "category": "operational|financial|customer|technology|team|compliance",
            "severity": "high|medium|low",
            "frequency": "daily|weekly|monthly|occasionally",
            "quote": "<direct quote from transcript, or null>",
            "impact": {{
                "time_hours_per_week": <estimated hours lost, or 0>,
                "cost_per_month": <estimated cost in EUR, or 0>,
                "customer_impact": "<description of customer impact, or null>"
            }},
            "automation_potential": "high|medium|low",
            "suggested_solutions": ["<solution 1>", "<solution 2>"]
        }}
    ],
    "themes": ["<recurring theme 1>", "<recurring theme 2>"],
    "priority_ranking": ["pain-001", "pain-002"],
    "confidence_score": <0.0-1.0 based on clarity of evidence>
}}

IMPORTANT:
- Only extract pain points with clear evidence in the transcript
- Include direct quotes when the user explicitly states a problem
- Be conservative with impact estimates
- If no clear pain points, return empty list with low confidence

Return ONLY the JSON."""

        try:
            response = await self.call_llm_json(
                prompt=prompt,
                system=self._get_system_prompt(),
            )

            # Validate and normalize
            return self._validate_response(response)

        except SkillError:
            raise
        except Exception as e:
            logger.error(f"Failed to extract pain points: {e}")
            return self._get_empty_result()

    def _get_system_prompt(self) -> str:
        """Get the system prompt for pain extraction."""
        return """You are an expert business analyst extracting pain points from interview transcripts.

Your role is to identify both explicit and implicit business challenges that could benefit from AI or automation solutions.

Key principles:
1. EVIDENCE-BASED: Only extract pain points with clear evidence in the transcript
2. SPECIFIC: Generic pain points are useless - be specific to what was said
3. CONSERVATIVE: Don't inflate severity or impact estimates
4. ACTIONABLE: Each pain point should map to a potential solution
5. QUOTED: Include direct quotes when the user explicitly describes a problem

Look for:
- Explicit complaints ("we spend too much time on X")
- Frustration signals ("it's annoying when...")
- Manual processes ("we have to manually...")
- Workarounds ("we use spreadsheets to track...")
- Time sinks ("it takes hours to...")
- Frequency indicators ("every day we have to...")
- Impact statements ("this costs us..." or "customers complain about...")"""

    def _validate_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize the response structure."""
        pain_points = response.get("pain_points", [])

        validated_pains = []
        for i, pain in enumerate(pain_points):
            if not isinstance(pain, dict):
                continue

            validated_pain = {
                "id": pain.get("id", f"pain-{i+1:03d}"),
                "title": pain.get("title", "Untitled Pain Point"),
                "description": pain.get("description", ""),
                "category": pain.get("category", "operational"),
                "severity": pain.get("severity", "medium"),
                "frequency": pain.get("frequency", "occasionally"),
                "quote": pain.get("quote"),
                "impact": {
                    "time_hours_per_week": pain.get("impact", {}).get("time_hours_per_week", 0),
                    "cost_per_month": pain.get("impact", {}).get("cost_per_month", 0),
                    "customer_impact": pain.get("impact", {}).get("customer_impact"),
                },
                "automation_potential": pain.get("automation_potential", "medium"),
                "suggested_solutions": pain.get("suggested_solutions", [])[:3],
            }

            # Validate category
            if validated_pain["category"] not in PAIN_CATEGORIES:
                validated_pain["category"] = "operational"

            # Validate severity
            if validated_pain["severity"] not in ("high", "medium", "low"):
                validated_pain["severity"] = "medium"

            # Validate frequency
            if validated_pain["frequency"] not in ("daily", "weekly", "monthly", "occasionally"):
                validated_pain["frequency"] = "occasionally"

            validated_pains.append(validated_pain)

        # Sort by severity for priority ranking
        severity_order = {"high": 0, "medium": 1, "low": 2}
        validated_pains.sort(key=lambda p: severity_order.get(p["severity"], 1))

        return {
            "pain_points": validated_pains,
            "themes": response.get("themes", [])[:5],
            "priority_ranking": [p["id"] for p in validated_pains],
            "confidence_score": min(1.0, max(0.0, response.get("confidence_score", 0.5))),
        }

    def _validate_with_expertise(
        self,
        result: Dict[str, Any],
        expertise_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and enrich pain points using expertise data."""
        known_pains = set(
            p.lower() for p in expertise_context.get("common_pain_points", [])
        )
        pain_frequencies = expertise_context.get("pain_point_frequencies", {})

        for pain in result.get("pain_points", []):
            title_lower = pain.get("title", "").lower()
            desc_lower = pain.get("description", "").lower()

            # Check if this matches a known pain point
            for known in known_pains:
                if known in title_lower or known in desc_lower:
                    # Add expertise validation
                    pain["expertise_validated"] = True
                    pain["industry_frequency"] = pain_frequencies.get(known, {}).get(
                        "count", 0
                    )
                    break
            else:
                pain["expertise_validated"] = False

        # Boost confidence if we found expertise-validated pains
        validated_count = sum(
            1 for p in result.get("pain_points", [])
            if p.get("expertise_validated")
        )
        if validated_count > 0:
            total = len(result.get("pain_points", []))
            boost = 0.1 * (validated_count / max(total, 1))
            result["confidence_score"] = min(1.0, result["confidence_score"] + boost)

        return result

    def _get_empty_result(self) -> Dict[str, Any]:
        """Return an empty result when extraction fails."""
        return {
            "pain_points": [],
            "themes": [],
            "priority_ranking": [],
            "confidence_score": 0.0,
        }


# For skill discovery
__all__ = ["PainExtractionSkill"]
