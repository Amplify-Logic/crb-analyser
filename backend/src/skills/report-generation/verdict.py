"""
Verdict Skill

Generates the overall AI adoption verdict for CRB reports.

Verdict types:
- GO: High readiness, clear ROI, low risk - proceed with confidence
- CAUTION: Good potential but needs preparation - proceed carefully
- WAIT: Not ready yet - focus on prerequisites first
- NO: AI not recommended - explain why and what to do instead

This skill:
1. Analyzes executive summary scores
2. Reviews findings and recommendations
3. Considers company context (size, budget, tech comfort)
4. Uses expertise data for calibration
5. Generates honest, actionable verdict

Output Schema:
{
    "recommendation": "proceed|proceed_cautiously|wait|not_recommended",
    "headline": "Short punchy headline",
    "subheadline": "Supporting context",
    "reasoning": ["Reason 1", "Reason 2", "Reason 3"],
    "confidence": "high|medium|low",
    "color": "green|yellow|orange|gray",
    "when_to_revisit": "Specific timing for re-evaluation",
    "recommended_approach": ["Step 1", "Step 2", "Step 3"],
    "what_to_do_instead": ["If wait/not_recommended: alternative actions"]
}
"""

import logging
from typing import Dict, Any, List, Optional

from src.skills.base import LLMSkill, SkillContext, SkillError

logger = logging.getLogger(__name__)


# Verdict thresholds
VERDICT_THRESHOLDS = {
    "go": {
        "min_ai_readiness": 70,
        "min_cv_score": 7,
        "min_bh_score": 7,
        "max_not_recommended_ratio": 0.3,
    },
    "caution": {
        "min_ai_readiness": 50,
        "min_cv_score": 5,
        "min_bh_score": 5,
        "max_not_recommended_ratio": 0.4,
    },
    "wait": {
        "min_ai_readiness": 30,
        "min_cv_score": 4,
        "min_bh_score": 4,
        "max_not_recommended_ratio": 0.5,
    },
    # Below wait thresholds = no
}


class VerdictSkill(LLMSkill[Dict[str, Any]]):
    """
    Generate overall AI adoption verdict for CRB reports.

    This is an LLM-powered skill that synthesizes all report data
    into a clear Go/Caution/Wait/No recommendation with reasoning.
    """

    name = "verdict"
    description = "Generate Go/Caution/Wait/No verdict with reasoning"
    version = "1.0.0"

    requires_llm = True
    requires_expertise = False  # Works without, but better with

    # Verdict templates - keys match internal codes, values used for frontend
    # NOTE: Subheadlines are defaults - LLM should generate specific ones with metrics
    VERDICT_TEMPLATES = {
        "go": {
            "recommendation": "proceed",
            "color": "green",
            "headline": "Go For It",
            "subheadline": "Clear ROI path with manageable risk",  # No buzzwords
            "when_to_revisit": "Quarterly check-ins to measure progress",
        },
        "caution": {
            "recommendation": "proceed_cautiously",
            "color": "yellow",
            "headline": "Proceed with Caution",
            "subheadline": "ROI potential exists, monitor risks closely",  # Specific
            "when_to_revisit": "Re-evaluate after first pilot (3-6 months)",
        },
        "wait": {
            "recommendation": "wait",
            "color": "orange",
            "headline": "Wait and Prepare",
            "subheadline": "Address data/process gaps before investing",  # Specific
            "when_to_revisit": "Re-evaluate in 6-12 months after prerequisites done",
        },
        "no": {
            "recommendation": "not_recommended",
            "color": "gray",
            "headline": "Not Recommended Now",
            "subheadline": "Current gaps make ROI unlikely",  # Honest
            "when_to_revisit": "Revisit in 12-18 months after core process improvements",
        },
    }

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Generate verdict from report data.

        Args:
            context: SkillContext with report_data containing scores and findings

        Returns:
            Verdict dictionary with recommendation and reasoning
        """
        report_data = context.report_data or {}
        executive_summary = report_data.get("executive_summary", {})
        findings = report_data.get("findings", [])
        recommendations = report_data.get("recommendations", [])

        # Calculate metrics for verdict
        metrics = self._calculate_metrics(executive_summary, findings)

        # Determine initial verdict based on thresholds
        initial_verdict = self._determine_verdict(metrics)

        # Get expertise context for calibration
        expertise_context = {}
        if context.expertise:
            expertise_context = self._build_expertise_context(
                context.expertise,
                context.industry
            )

        # Generate detailed verdict with LLM
        verdict = await self._generate_verdict(
            metrics=metrics,
            initial_verdict=initial_verdict,
            executive_summary=executive_summary,
            findings=findings,
            recommendations=recommendations,
            industry=context.industry,
            company_context={
                "name": context.company_name,
                "size": context.company_size,
                "tech_comfort": context.quiz_answers.get("tech_comfort", "medium") if context.quiz_answers else "medium",
            },
            expertise_context=expertise_context,
        )

        # Apply expertise calibration if significant data exists
        if expertise_context.get("has_data") and expertise_context.get("confidence") != "low":
            verdict = self._calibrate_verdict(verdict, metrics, expertise_context)

        return verdict

    def _calculate_metrics(
        self,
        executive_summary: Dict[str, Any],
        findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate metrics for verdict determination."""
        ai_readiness = executive_summary.get("ai_readiness_score", 50)
        cv_score = executive_summary.get("customer_value_score", 5)
        bh_score = executive_summary.get("business_health_score", 5)

        # Count finding types
        total_findings = len(findings)
        not_recommended = sum(1 for f in findings if f.get("is_not_recommended"))
        high_confidence = sum(1 for f in findings if f.get("confidence") == "high")

        not_recommended_ratio = not_recommended / total_findings if total_findings > 0 else 0
        high_confidence_ratio = high_confidence / total_findings if total_findings > 0 else 0

        return {
            "ai_readiness": ai_readiness,
            "cv_score": cv_score,
            "bh_score": bh_score,
            "total_findings": total_findings,
            "not_recommended_count": not_recommended,
            "not_recommended_ratio": not_recommended_ratio,
            "high_confidence_ratio": high_confidence_ratio,
            "combined_score": (ai_readiness / 10 + cv_score + bh_score) / 3,
        }

    def _determine_verdict(self, metrics: Dict[str, Any]) -> str:
        """Determine initial verdict based on thresholds."""
        ai_readiness = metrics["ai_readiness"]
        cv_score = metrics["cv_score"]
        bh_score = metrics["bh_score"]
        not_recommended_ratio = metrics["not_recommended_ratio"]

        # Check GO thresholds
        go = VERDICT_THRESHOLDS["go"]
        if (ai_readiness >= go["min_ai_readiness"] and
            cv_score >= go["min_cv_score"] and
            bh_score >= go["min_bh_score"] and
            not_recommended_ratio <= go["max_not_recommended_ratio"]):
            return "go"

        # Check CAUTION thresholds
        caution = VERDICT_THRESHOLDS["caution"]
        if (ai_readiness >= caution["min_ai_readiness"] and
            cv_score >= caution["min_cv_score"] and
            bh_score >= caution["min_bh_score"] and
            not_recommended_ratio <= caution["max_not_recommended_ratio"]):
            return "caution"

        # Check WAIT thresholds
        wait = VERDICT_THRESHOLDS["wait"]
        if (ai_readiness >= wait["min_ai_readiness"] and
            cv_score >= wait["min_cv_score"] and
            bh_score >= wait["min_bh_score"] and
            not_recommended_ratio <= wait["max_not_recommended_ratio"]):
            return "wait"

        # Below all thresholds = NO
        return "no"

    def _build_expertise_context(
        self,
        expertise: Dict[str, Any],
        industry: str
    ) -> Dict[str, Any]:
        """Build expertise context for calibration."""
        industry_expertise = expertise.get("industry_expertise", {})

        if not industry_expertise or industry_expertise.get("total_analyses", 0) == 0:
            return {"has_data": False}

        return {
            "has_data": True,
            "total_analyses": industry_expertise.get("total_analyses", 0),
            "confidence": industry_expertise.get("confidence", "low"),
            "avg_ai_readiness": industry_expertise.get("avg_ai_readiness", 50),
            "success_rate": industry_expertise.get("success_rate", 0.5),
        }

    async def _generate_verdict(
        self,
        metrics: Dict[str, Any],
        initial_verdict: str,
        executive_summary: Dict[str, Any],
        findings: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]],
        industry: str,
        company_context: Dict[str, Any],
        expertise_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate detailed verdict using Claude."""
        # Build expertise injection
        expertise_injection = ""
        if expertise_context.get("has_data"):
            expertise_injection = f"""
INDUSTRY EXPERTISE (from {expertise_context['total_analyses']} analyses):
- Average AI readiness in {industry}: {expertise_context.get('avg_ai_readiness', 50):.0f}/100
- Industry success rate: {expertise_context.get('success_rate', 0.5)*100:.0f}%
"""

        # Summarize findings
        finding_summary = []
        for f in findings[:5]:
            status = "NOT RECOMMENDED" if f.get("is_not_recommended") else "Recommended"
            finding_summary.append(
                f"- {f.get('title', 'Finding')}: CV={f.get('customer_value_score', 5)}, "
                f"BH={f.get('business_health_score', 5)}, {status}"
            )

        prompt = f"""Generate an AI adoption verdict based on this CRB Analysis.

METRICS:
- AI Readiness Score: {metrics['ai_readiness']}/100
- Customer Value Score: {metrics['cv_score']}/10
- Business Health Score: {metrics['bh_score']}/10
- Not Recommended Ratio: {metrics['not_recommended_ratio']*100:.0f}%
- High Confidence Findings: {metrics['high_confidence_ratio']*100:.0f}%

COMPANY:
- Industry: {industry}
- Size: {company_context.get('size', 'Unknown')}
- Tech Comfort: {company_context.get('tech_comfort', 'medium')}
{expertise_injection}

TOP FINDINGS:
{chr(10).join(finding_summary)}

INITIAL ASSESSMENT: {initial_verdict.upper()}

═══════════════════════════════════════════════════════════════════════════════
VERDICT OPTIONS (use these exact values for recommendation field)
═══════════════════════════════════════════════════════════════════════════════

proceed (Green): Proceed with confidence
- AI readiness 70+, both scores 7+
- Clear ROI, minimal risks
- Strong fundamentals

proceed_cautiously (Yellow): Proceed carefully
- AI readiness 50-69, scores 5-7
- Good potential but watch risks
- Some gaps to address

wait (Orange): Prepare first
- AI readiness 30-49, scores 4-6
- Significant prerequisites needed
- Focus on foundation

not_recommended (Gray): Not recommended now
- AI readiness below 30, low scores
- Major gaps or risks
- Better alternatives exist

═══════════════════════════════════════════════════════════════════════════════

Generate a JSON verdict:
{{
    "recommendation": "proceed|proceed_cautiously|wait|not_recommended",
    "headline": "<short punchy headline - max 5 words, NO buzzwords>",
    "subheadline": "<supporting context with specific metric - max 12 words. Example: 'ROI of 280% with 6-month payback on 3 findings'>",
    "reasoning": [
        "<reason 1 - MUST include specific metric: 'ROI calculation: €X savings at Y% confidence'>",
        "<reason 2 - MUST reference finding: 'Finding #3 (no-show reduction) alone justifies investment'>",
        "<reason 3 - MUST cite quiz data: 'Tech comfort rated HIGH (Quiz Q8) supports adoption'>"
    ],
    "confidence": "high|medium|low",
    "when_to_revisit": "<specific timing with trigger: 'After implementing Finding #1 (est. 4 weeks)' or 'In 6 months after CRM data cleanup'>",
    "recommended_approach": [
        "<action 1 - MUST be specific: 'Start with Finding #2: set up n8n webhook for appointment reminders'>",
        "<action 2 - specific next step>",
        "<action 3 - specific next step>"
    ],
    "what_to_do_instead": [
        "<REQUIRED if wait/not_recommended: specific action with finding ref: 'Address Finding #7 data quality first'>",
        "<REQUIRED if wait/not_recommended: another specific alternative>"
    ]
}}

═══════════════════════════════════════════════════════════════════════════════
STRICT REQUIREMENTS - Your output is INVALID if violated:
═══════════════════════════════════════════════════════════════════════════════

1. Each "reasoning" item MUST contain a specific number (€, %, hours) OR finding reference
2. "subheadline" MUST contain a specific metric, NOT buzzwords
3. If recommendation is "wait" or "not_recommended":
   - MUST provide at least 2 specific alternatives in "what_to_do_instead"
   - Each alternative MUST reference a finding or quiz answer
4. "recommended_approach" items MUST be actionable (start with verb, reference specific tool/finding)
5. NEVER use: "strong foundations", "well-positioned", "significant opportunity"

═══════════════════════════════════════════════════════════════════════════════
VALIDATION BEFORE OUTPUT
═══════════════════════════════════════════════════════════════════════════════
Before returning, verify:
- [ ] Each reasoning item has a number or finding reference
- [ ] Subheadline contains a metric (€, %, or count)
- [ ] No banned buzzwords anywhere in output
- [ ] If wait/not_recommended: at least 2 specific alternatives provided

Return ONLY the JSON."""

        try:
            response = await self.call_llm_json(
                prompt=prompt,
                system=self._get_system_prompt(),
            )

            # Map internal verdict codes to frontend values if needed
            llm_recommendation = response.get("recommendation", initial_verdict)
            # Handle case where LLM might return internal code like "go" instead of "proceed"
            internal_to_frontend = {
                "go": "proceed",
                "caution": "proceed_cautiously",
                "no": "not_recommended",
                "wait": "wait",
            }
            if llm_recommendation in internal_to_frontend:
                response["recommendation"] = internal_to_frontend[llm_recommendation]
            elif llm_recommendation not in ("proceed", "proceed_cautiously", "wait", "not_recommended"):
                # Unknown value, map from initial_verdict
                template = self.VERDICT_TEMPLATES.get(initial_verdict, self.VERDICT_TEMPLATES["caution"])
                response["recommendation"] = template["recommendation"]

            # Get template based on internal code for defaults
            template = self.VERDICT_TEMPLATES.get(initial_verdict, self.VERDICT_TEMPLATES["caution"])

            # Ensure all required fields are present
            response["color"] = response.get("color") or template["color"]
            if not response.get("headline"):
                response["headline"] = template["headline"]
            if not response.get("subheadline"):
                response["subheadline"] = template["subheadline"]
            if not response.get("when_to_revisit"):
                response["when_to_revisit"] = template["when_to_revisit"]

            return response

        except SkillError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate verdict: {e}")
            return self._get_default_verdict(initial_verdict)

    def _get_system_prompt(self) -> str:
        """Get the system prompt for verdict generation."""
        return """You are an expert AI business consultant delivering the final verdict for CRB Analysis reports.

Your role is to synthesize all analysis into a clear, honest recommendation.

═══════════════════════════════════════════════════════════════════════════════
BANNED LANGUAGE - Using any of these INVALIDATES your output:
═══════════════════════════════════════════════════════════════════════════════
- "well-positioned", "strong foundations", "significant opportunity"
- "leverage", "optimize", "streamline", "transform"
- "best practice", "industry-leading", "robust"

INSTEAD OF: "Strong foundations for AI adoption"
USE: "Your 4/5 API openness score enables automation without software replacement"

═══════════════════════════════════════════════════════════════════════════════
KEY PRINCIPLES
═══════════════════════════════════════════════════════════════════════════════
1. EVIDENCE-BASED: Every reason must cite specific metrics or findings
2. SPECIFIC NUMBERS: Reasoning must include €, %, hours, or finding references
3. ACTIONABLE: Next steps must be concrete with specific first actions
4. CONTEXTUAL: Consider company size, budget, and tech comfort
5. BALANCED: Acknowledge both opportunities AND risks

═══════════════════════════════════════════════════════════════════════════════
REASONING REQUIREMENTS - STRICTLY ENFORCED
═══════════════════════════════════════════════════════════════════════════════
Each reason in the "reasoning" array MUST contain at least ONE of:
- A specific number (€, %, hours)
- A reference to a specific finding by title or ID
- A quote or paraphrase from quiz answers

INVALID: "Clear ROI opportunity with strong potential"
VALID: "€35K annual savings ÷ €10K year-1 investment = 350% ROI (Findings #1-3)"

INVALID: "Team shows readiness to adopt AI"
VALID: "Quiz Q8: Tech comfort rated 'high' + 'eager to try new tools' = strong adoption likelihood"

═══════════════════════════════════════════════════════════════════════════════
VERDICT RULES - NEVER VIOLATE
═══════════════════════════════════════════════════════════════════════════════
NEVER recommend "proceed" (GO) if:
- AI readiness is below 70
- Either pillar score is below 6
- More than 30% of findings are "not recommended"

ALWAYS explain WHY, not just WHAT."""

    def _calibrate_verdict(
        self,
        verdict: Dict[str, Any],
        metrics: Dict[str, Any],
        expertise_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calibrate verdict using expertise data."""
        ai_readiness = metrics["ai_readiness"]
        avg_industry_readiness = expertise_context.get("avg_ai_readiness", 50)

        # Add industry comparison to reasoning if significant difference
        diff = ai_readiness - avg_industry_readiness
        if abs(diff) >= 15:
            direction = "above" if diff > 0 else "below"
            comparison = f"AI readiness is {abs(diff):.0f} points {direction} industry average"

            reasoning = verdict.get("reasoning", [])
            if comparison not in reasoning:
                reasoning.append(comparison)
                verdict["reasoning"] = reasoning[:4]  # Keep max 4 reasons

        return verdict

    def _get_default_verdict(self, initial_verdict: str) -> Dict[str, Any]:
        """Return a default verdict when LLM fails."""
        template = self.VERDICT_TEMPLATES.get(initial_verdict, self.VERDICT_TEMPLATES["caution"])

        return {
            "recommendation": template["recommendation"],
            "headline": template["headline"],
            "subheadline": template["subheadline"],
            "reasoning": ["Based on overall assessment scores"],
            "confidence": "low",
            "color": template["color"],
            "when_to_revisit": template["when_to_revisit"],
            "recommended_approach": ["Review findings for specific actions"],
            "what_to_do_instead": [],
        }


# For skill discovery
__all__ = ["VerdictSkill"]
