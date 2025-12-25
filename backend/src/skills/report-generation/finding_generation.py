"""
Finding Generation Skill

Generates consistent, calibrated findings for CRB reports.

This skill:
1. Analyzes quiz/interview data to identify opportunities and issues
2. Scores each finding on Two Pillars (Customer Value + Business Health)
3. Assigns confidence levels based on evidence strength
4. Creates proper source citations
5. Includes "not recommended" items with alternatives
6. Uses expertise data for calibration when available

Output Schema:
[
    {
        "id": "finding-001",
        "title": "Short descriptive title",
        "description": "Clear description",
        "category": "efficiency|growth|risk|compliance|customer_experience",
        "customer_value_score": 1-10,
        "business_health_score": 1-10,
        "current_state": "How they do this now",
        "value_saved": {"hours_per_week": N, "hourly_rate": 50, "annual_savings": N},
        "value_created": {"description": "...", "potential_revenue": N},
        "confidence": "high|medium|low",
        "sources": ["Specific source citations"],
        "time_horizon": "short|mid|long",
        "is_not_recommended": false,
        "why_not": null,
        "what_instead": null
    }
]
"""

import json
import logging
from typing import Dict, Any, List, Optional

from src.skills.base import LLMSkill, SkillContext, SkillError

logger = logging.getLogger(__name__)


class FindingGenerationSkill(LLMSkill[List[Dict[str, Any]]]):
    """
    Generate findings for CRB reports.

    This is an LLM-powered skill that analyzes quiz data and generates
    structured findings with Two Pillars scoring and confidence levels.
    When expertise data is available, it calibrates the output to
    industry norms and uses proven patterns.
    """

    name = "finding-generation"
    description = "Generate calibrated findings with Two Pillars scoring"
    version = "1.0.0"

    requires_llm = True
    requires_expertise = False  # Works without, but better with

    # Default finding template
    FINDING_TEMPLATE = {
        "id": "",
        "title": "",
        "description": "",
        "category": "efficiency",
        "customer_value_score": 5,
        "business_health_score": 5,
        "current_state": "",
        "value_saved": {"hours_per_week": 0, "hourly_rate": 50, "annual_savings": 0},
        "value_created": {"description": "", "potential_revenue": 0},
        "confidence": "medium",
        "sources": [],
        "time_horizon": "mid",
        "is_not_recommended": False,
        "why_not": None,
        "what_instead": None,
    }

    # Confidence distribution targets
    CONFIDENCE_DISTRIBUTION = {
        "high": 0.30,    # ~30% of findings
        "medium": 0.50,  # ~50% of findings
        "low": 0.20,     # ~20% of findings
    }

    async def execute(self, context: SkillContext) -> List[Dict[str, Any]]:
        """
        Generate findings from context.

        Args:
            context: SkillContext with quiz_answers, industry, and optional expertise

        Returns:
            List of finding dictionaries matching report schema
        """
        # Get configuration from metadata
        tier = context.metadata.get("tier", "quick")
        max_findings = 10 if tier == "quick" else 15
        min_not_recommended = 3

        # Extract data from context
        answers = context.quiz_answers or {}
        industry = context.industry
        expertise = context.expertise or {}
        knowledge = context.knowledge or {}

        # Get opportunities and benchmarks from knowledge
        opportunities = knowledge.get("opportunities", [])
        benchmarks = knowledge.get("benchmarks", {})

        # Build expertise context for calibration
        expertise_context = self._build_expertise_context(expertise, industry)

        # Generate findings using LLM
        findings = await self._generate_findings(
            answers=answers,
            industry=industry,
            opportunities=opportunities,
            benchmarks=benchmarks,
            expertise_context=expertise_context,
            max_findings=max_findings,
            min_not_recommended=min_not_recommended,
        )

        # Apply expertise calibration if available
        if expertise:
            findings = self._calibrate_with_expertise(findings, expertise)

        # Validate and normalize findings
        findings = self._validate_findings(findings)

        return findings

    def _build_expertise_context(
        self,
        expertise: Dict[str, Any],
        industry: str
    ) -> Dict[str, Any]:
        """Build expertise context for prompt injection."""
        industry_expertise = expertise.get("industry_expertise", {})

        if not industry_expertise or industry_expertise.get("total_analyses", 0) == 0:
            return {"has_data": False}

        return {
            "has_data": True,
            "total_analyses": industry_expertise.get("total_analyses", 0),
            "confidence": industry_expertise.get("confidence", "low"),
            "common_pain_points": list(
                industry_expertise.get("pain_points", {}).keys()
            )[:5],
            "effective_patterns": [
                p.get("recommendation", "") if isinstance(p, dict) else str(p)
                for p in industry_expertise.get("effective_patterns", [])[:5]
            ],
            "anti_patterns": industry_expertise.get("anti_patterns", [])[:3],
            "avg_potential_savings": industry_expertise.get("avg_potential_savings", 0),
        }

    async def _generate_findings(
        self,
        answers: Dict[str, Any],
        industry: str,
        opportunities: List[Dict[str, Any]],
        benchmarks: Dict[str, Any],
        expertise_context: Dict[str, Any],
        max_findings: int,
        min_not_recommended: int,
    ) -> List[Dict[str, Any]]:
        """Generate findings using Claude."""
        # Build expertise injection for prompt
        expertise_injection = ""
        if expertise_context.get("has_data"):
            expertise_injection = f"""
INDUSTRY EXPERTISE (from {expertise_context['total_analyses']} previous analyses):
- Common pain points in {industry}: {', '.join(expertise_context['common_pain_points'][:3]) or 'None recorded'}
- What works well: {', '.join(expertise_context['effective_patterns'][:2]) or 'No patterns yet'}
- What to AVOID recommending: {', '.join(expertise_context['anti_patterns'][:2]) or 'No anti-patterns yet'}
- Average potential savings: €{expertise_context['avg_potential_savings']:,.0f}

USE THIS EXPERTISE:
- Prioritize findings around known pain points
- Apply effective patterns to recommendations
- AVOID anti-patterns in your findings
"""

        prompt = f"""Analyze the quiz responses and generate findings for a CRB Analysis report.

QUIZ ANSWERS:
{json.dumps(answers, indent=2)}

INDUSTRY: {industry}

INDUSTRY OPPORTUNITIES AVAILABLE:
{json.dumps(opportunities[:5], indent=2) if opportunities else "None specific"}

INDUSTRY BENCHMARKS:
{json.dumps(benchmarks, indent=2) if benchmarks else "Use general industry standards"}
{expertise_injection}

═══════════════════════════════════════════════════════════════════════════════
FINDING REQUIREMENTS
═══════════════════════════════════════════════════════════════════════════════

Generate {max_findings} findings total:
- At least {max_findings - min_not_recommended} RECOMMENDED findings (score 6+ on BOTH pillars)
- Exactly {min_not_recommended} NOT-RECOMMENDED findings (score below 6 on at least one pillar)

═══════════════════════════════════════════════════════════════════════════════
TWO PILLARS SCORING (CRITICAL)
═══════════════════════════════════════════════════════════════════════════════

Every finding MUST be scored on TWO pillars:

1. Customer Value Score (1-10): How does this benefit their customers?
   - 8-10: Transformative customer experience improvement
   - 5-7: Noticeable improvement for customers
   - 1-4: Minimal or negative customer impact

2. Business Health Score (1-10): How does this strengthen the business?
   - 8-10: Significant operational or financial improvement
   - 5-7: Moderate business benefit
   - 1-4: Minimal or risky for business

RECOMMENDED = Both scores 6+
NOT RECOMMENDED = Either score below 6

═══════════════════════════════════════════════════════════════════════════════
SOURCE CITATION REQUIREMENTS
═══════════════════════════════════════════════════════════════════════════════

Every finding MUST have at least one specific source:
1. Quiz response: "Based on your answer: '[quote from their answer]'"
2. Industry benchmark: "Industry average: X (Source: [benchmark name])"
3. Calculation: "Calculated: [formula with numbers]"
4. Industry pattern: "[Industry] businesses typically see [pattern]"

═══════════════════════════════════════════════════════════════════════════════
CONFIDENCE SCORING CRITERIA
═══════════════════════════════════════════════════════════════════════════════

Rate each finding's confidence:

HIGH (~30% of findings):
- Quiz answer directly mentions this problem
- Multiple data points support the finding
- Calculation uses user-provided numbers

MEDIUM (~50% of findings):
- Quiz answer implies this issue
- Industry pattern likely applies
- One strong supporting data point

LOW (~20% of findings):
- Industry pattern suggests this
- Significant assumptions required
- Hypothesis worth validating

═══════════════════════════════════════════════════════════════════════════════

Generate a JSON array with this structure:
[
    {{
        "id": "finding-001",
        "title": "Short descriptive title",
        "description": "Clear description of the opportunity or issue",
        "category": "efficiency|growth|risk|compliance|customer_experience",
        "customer_value_score": <1-10>,
        "business_health_score": <1-10>,
        "current_state": "How they're doing this now (from quiz answers)",
        "value_saved": {{
            "hours_per_week": <number>,
            "hourly_rate": 50,
            "annual_savings": <hours * 50 * 52>
        }},
        "value_created": {{
            "description": "How this creates new value",
            "potential_revenue": <number or 0>
        }},
        "confidence": "high|medium|low",
        "sources": ["Specific citation 1", "Specific citation 2"],
        "time_horizon": "short|mid|long",
        "is_not_recommended": false
    }},
    {{
        "id": "finding-not-001",
        "title": "What NOT to do",
        "description": "Why this approach is wrong",
        "category": "...",
        "customer_value_score": <below 6>,
        "business_health_score": <below 6>,
        "confidence": "high",
        "sources": ["Evidence why this is bad"],
        "time_horizon": "...",
        "is_not_recommended": true,
        "why_not": "Clear explanation",
        "what_instead": "Better alternative"
    }}
]

Return ONLY the JSON array, no explanation."""

        try:
            response = await self.call_llm_json(
                prompt=prompt,
                system=self._get_system_prompt(),
            )

            if isinstance(response, list):
                return response
            elif isinstance(response, dict) and "findings" in response:
                return response["findings"]
            else:
                logger.warning("Unexpected response format, returning empty list")
                return []

        except SkillError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate findings: {e}")
            return []

    def _get_system_prompt(self) -> str:
        """Get the system prompt for finding generation."""
        return """You are an expert AI business analyst generating findings for CRB Analysis reports.

Your role is to identify automation opportunities AND anti-recommendations with honest, evidence-based analysis.

Key principles:
1. EVIDENCE-BASED: Every finding needs specific sources
2. TWO PILLARS: Always score both Customer Value AND Business Health
3. CONFIDENCE: Be honest about uncertainty - not everything is HIGH confidence
4. INCLUDE WARNINGS: Always include "not recommended" items with alternatives
5. SPECIFIC: Generic findings are useless - be specific to their situation
6. REALISTIC: Don't oversell potential savings - use conservative estimates

Scoring guidance:
- A score of 10 is rare - reserve for truly transformative impacts
- Most findings should be 6-8 range
- "Not recommended" items should have at least one score below 6
- If both pillars are high, it's a priority recommendation"""

    def _calibrate_with_expertise(
        self,
        findings: List[Dict[str, Any]],
        expertise: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Calibrate findings using expertise data.

        Adjusts scores and adds expertise-based context.
        """
        industry_expertise = expertise.get("industry_expertise", {})

        if not industry_expertise or industry_expertise.get("total_analyses", 0) < 5:
            return findings

        # Get anti-patterns to check against
        anti_patterns = set(
            p.lower() if isinstance(p, str) else p.get("pattern", "").lower()
            for p in industry_expertise.get("anti_patterns", [])
        )

        # Get effective patterns to boost
        effective_patterns = set(
            p.get("recommendation", "").lower() if isinstance(p, dict) else p.lower()
            for p in industry_expertise.get("effective_patterns", [])
        )

        for finding in findings:
            title_lower = finding.get("title", "").lower()
            desc_lower = finding.get("description", "").lower()

            # Check if finding matches anti-pattern
            for anti in anti_patterns:
                if anti and (anti in title_lower or anti in desc_lower):
                    finding["is_not_recommended"] = True
                    if not finding.get("why_not"):
                        finding["why_not"] = f"Based on {industry_expertise.get('total_analyses', 0)} previous analyses, this approach often underperforms."
                    finding["sources"] = finding.get("sources", []) + [
                        f"Expertise: This matches known anti-pattern from industry analysis"
                    ]
                    break

            # Boost confidence for effective patterns
            for pattern in effective_patterns:
                if pattern and (pattern in title_lower or pattern in desc_lower):
                    if finding.get("confidence") == "low":
                        finding["confidence"] = "medium"
                    finding["sources"] = finding.get("sources", []) + [
                        f"Expertise: Similar approach successful in previous analyses"
                    ]
                    break

        return findings

    def _validate_findings(
        self,
        findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate and normalize findings structure."""
        validated = []

        for i, finding in enumerate(findings):
            if not isinstance(finding, dict):
                continue

            # Create validated finding with defaults
            validated_finding = self.FINDING_TEMPLATE.copy()
            validated_finding["id"] = finding.get("id", f"finding-{i+1:03d}")
            validated_finding["title"] = finding.get("title", "Untitled Finding")
            validated_finding["description"] = finding.get("description", "")
            validated_finding["category"] = finding.get("category", "efficiency")

            # Clamp scores to valid range
            cv_score = finding.get("customer_value_score", 5)
            bh_score = finding.get("business_health_score", 5)
            validated_finding["customer_value_score"] = max(1, min(10, int(cv_score)))
            validated_finding["business_health_score"] = max(1, min(10, int(bh_score)))

            # Copy other fields
            validated_finding["current_state"] = finding.get("current_state", "")
            validated_finding["confidence"] = finding.get("confidence", "medium").lower()
            if validated_finding["confidence"] not in ("high", "medium", "low"):
                validated_finding["confidence"] = "medium"

            validated_finding["sources"] = finding.get("sources", [])
            validated_finding["time_horizon"] = finding.get("time_horizon", "mid")
            validated_finding["is_not_recommended"] = finding.get("is_not_recommended", False)

            if validated_finding["is_not_recommended"]:
                validated_finding["why_not"] = finding.get("why_not", "")
                validated_finding["what_instead"] = finding.get("what_instead", "")

            # Handle value_saved
            if isinstance(finding.get("value_saved"), dict):
                vs = finding["value_saved"]
                validated_finding["value_saved"] = {
                    "hours_per_week": vs.get("hours_per_week", 0),
                    "hourly_rate": vs.get("hourly_rate", 50),
                    "annual_savings": vs.get("annual_savings", 0),
                }
            else:
                validated_finding["value_saved"] = self.FINDING_TEMPLATE["value_saved"].copy()

            # Handle value_created
            if isinstance(finding.get("value_created"), dict):
                vc = finding["value_created"]
                validated_finding["value_created"] = {
                    "description": vc.get("description", ""),
                    "potential_revenue": vc.get("potential_revenue", 0),
                }
            else:
                validated_finding["value_created"] = self.FINDING_TEMPLATE["value_created"].copy()

            validated.append(validated_finding)

        return validated


# For skill discovery
__all__ = ["FindingGenerationSkill"]
