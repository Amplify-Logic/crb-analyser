"""
Report Generation Service

Generates CRB analysis reports from quiz session data.
Implements the two pillars methodology from FRAMEWORK.md.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, AsyncGenerator

from anthropic import Anthropic

from src.config.settings import settings
from src.config.supabase_client import get_async_supabase
from src.knowledge import (
    get_industry_context,
    get_relevant_opportunities,
    get_vendor_recommendations,
    get_benchmarks_for_metrics,
    normalize_industry,
)

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates CRB analysis reports following the two pillars methodology.

    Report tiers:
    - quick: 10-15 findings, essential recommendations
    - full: 25-50 findings, comprehensive analysis with roadmap
    """

    SYSTEM_PROMPT = """You are the CRB Analyser, an expert in business process optimization and AI implementation consulting for SMBs.

Your mission is to analyze quiz responses and generate actionable Cost/Risk/Benefit analysis for AI implementation opportunities.

═══════════════════════════════════════════════════════════════════════════════
CORE METHODOLOGY: TWO PILLARS (BOTH REQUIRED)
═══════════════════════════════════════════════════════════════════════════════

Every recommendation must pass BOTH tests:

1. CUSTOMER VALUE SCORE (1-10): "Does this make THEIR customers' lives better?"
   - Better customer experience
   - More value delivered to customers
   - Increased trust and loyalty

2. BUSINESS HEALTH SCORE (1-10): "Does this help the business survive and thrive?"
   - Sustainable margins
   - Build capability (not just cut costs)
   - Reduce existential risk

ONLY recommend items that score 6+ on BOTH dimensions.

═══════════════════════════════════════════════════════════════════════════════
VALUE CALCULATION
═══════════════════════════════════════════════════════════════════════════════

Always calculate TWO types of value:

1. VALUE SAVED (Efficiency):
   Time saved × Hourly cost = € saved annually
   Example: 10 hrs/week × €50/hr × 52 weeks = €26,000/year

2. VALUE CREATED (Growth):
   - New revenue opportunities enabled
   - Increased conversion rates
   - Higher customer lifetime value

═══════════════════════════════════════════════════════════════════════════════
THREE OPTIONS PATTERN (REQUIRED FOR EACH RECOMMENDATION)
═══════════════════════════════════════════════════════════════════════════════

Option A: OFF-THE-SHELF - Existing SaaS, plug and play, fastest
Option B: BEST-IN-CLASS - Premium vendor, full implementation
Option C: CUSTOM AI SOLUTION - Built specifically for them, competitive moat

Always include all three options with specific vendor names and pricing.

═══════════════════════════════════════════════════════════════════════════════
THREE TIME HORIZONS (REQUIRED)
═══════════════════════════════════════════════════════════════════════════════

Short Term (0-6 months): Quick wins, immediate impact
Mid Term (6-18 months): Foundation building, scaling
Long Term (18+ months): Strategic transformation

═══════════════════════════════════════════════════════════════════════════════
IMPARTIALITY & HONESTY
═══════════════════════════════════════════════════════════════════════════════

You are a TRUSTED ADVISOR. Be willing to say:
- "You're not ready for AI yet - fix these fundamentals first"
- "This process doesn't need automation"
- "The ROI doesn't justify the investment"
- "Wait 6-12 months - tools aren't mature enough"

Include a "NOT RECOMMENDED" section with honest reasons.

═══════════════════════════════════════════════════════════════════════════════
QUALITY STANDARDS
═══════════════════════════════════════════════════════════════════════════════

- Show ranges (min-max), never single numbers
- List all assumptions
- Rate confidence: High/Medium/Low
- Cite sources when possible
- Never recommend replacing teams - augment instead"""

    def __init__(self, quiz_session_id: str, tier: str = "quick"):
        self.quiz_session_id = quiz_session_id
        self.tier = tier
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.context: Dict[str, Any] = {}
        self.report_id: Optional[str] = None

    async def generate_report(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate a full CRB report from quiz session data.

        Yields progress updates during generation.
        """
        supabase = await get_async_supabase()

        try:
            # Phase 1: Load quiz data
            yield {"phase": "loading", "step": "Loading quiz data...", "progress": 5}

            quiz_result = await supabase.table("quiz_sessions").select("*").eq(
                "id", self.quiz_session_id
            ).single().execute()

            if not quiz_result.data:
                raise ValueError(f"Quiz session not found: {self.quiz_session_id}")

            quiz_data = quiz_result.data
            self.context["quiz"] = quiz_data
            self.context["email"] = quiz_data.get("email")
            self.context["answers"] = quiz_data.get("answers", {})
            self.context["results"] = quiz_data.get("results", {})

            # Create report record
            yield {"phase": "loading", "step": "Creating report...", "progress": 10}

            report_result = await supabase.table("reports").insert({
                "quiz_session_id": self.quiz_session_id,
                "tier": self.tier,
                "status": "generating",
                "generation_started_at": datetime.utcnow().isoformat(),
            }).execute()

            self.report_id = report_result.data[0]["id"]

            # Update quiz session with report ID
            await supabase.table("quiz_sessions").update({
                "report_id": self.report_id,
            }).eq("id", self.quiz_session_id).execute()

            # Phase 2: Load industry context
            yield {"phase": "research", "step": "Loading industry knowledge...", "progress": 15}

            industry = self._extract_industry()
            self.context["industry"] = industry
            self.context["industry_knowledge"] = get_industry_context(industry)
            self.context["opportunities"] = get_relevant_opportunities(industry)
            self.context["vendors"] = get_vendor_recommendations(industry)
            self.context["benchmarks"] = get_benchmarks_for_metrics(industry)

            yield {"phase": "research", "step": f"Loaded {industry} context", "progress": 20}

            # Phase 3: Generate analysis
            yield {"phase": "analysis", "step": "Analyzing business context...", "progress": 25}

            executive_summary = await self._generate_executive_summary()
            yield {"phase": "analysis", "step": "Executive summary complete", "progress": 35}

            # Save progress
            await supabase.table("reports").update({
                "executive_summary": executive_summary,
            }).eq("id", self.report_id).execute()

            # Phase 4: Generate findings
            yield {"phase": "findings", "step": "Generating findings...", "progress": 40}

            findings = await self._generate_findings()
            yield {"phase": "findings", "step": f"Generated {len(findings)} findings", "progress": 55}

            await supabase.table("reports").update({
                "findings": findings,
            }).eq("id", self.report_id).execute()

            # Phase 5: Generate recommendations
            yield {"phase": "recommendations", "step": "Generating recommendations...", "progress": 60}

            recommendations = await self._generate_recommendations(findings)
            yield {"phase": "recommendations", "step": f"Generated {len(recommendations)} recommendations", "progress": 75}

            await supabase.table("reports").update({
                "recommendations": recommendations,
            }).eq("id", self.report_id).execute()

            # Phase 6: Generate roadmap and value summary
            yield {"phase": "roadmap", "step": "Building implementation roadmap...", "progress": 80}

            roadmap = await self._generate_roadmap(recommendations)
            value_summary = self._calculate_value_summary(findings, recommendations)
            methodology_notes = self._generate_methodology_notes()

            await supabase.table("reports").update({
                "roadmap": roadmap,
                "value_summary": value_summary,
                "methodology_notes": methodology_notes,
            }).eq("id", self.report_id).execute()

            yield {"phase": "roadmap", "step": "Roadmap complete", "progress": 90}

            # Phase 7: Finalize
            yield {"phase": "finalizing", "step": "Finalizing report...", "progress": 95}

            await supabase.table("reports").update({
                "status": "completed",
                "generation_completed_at": datetime.utcnow().isoformat(),
            }).eq("id", self.report_id).execute()

            # Update quiz session
            await supabase.table("quiz_sessions").update({
                "status": "completed",
                "report_generated_at": datetime.utcnow().isoformat(),
            }).eq("id", self.quiz_session_id).execute()

            yield {
                "phase": "complete",
                "step": "Report generation complete!",
                "progress": 100,
                "report_id": self.report_id,
                "executive_summary": executive_summary,
            }

        except Exception as e:
            logger.error(f"Report generation error: {e}", exc_info=True)

            if self.report_id:
                await supabase.table("reports").update({
                    "status": "failed",
                    "error_message": str(e),
                }).eq("id", self.report_id).execute()

            yield {
                "phase": "error",
                "step": f"Report generation failed: {str(e)}",
                "progress": 0,
                "error": str(e),
            }

    def _extract_industry(self) -> str:
        """Extract and normalize industry from quiz answers."""
        answers = self.context.get("answers", {})
        results = self.context.get("results", {})

        # Try to get industry from various sources
        industry = answers.get("industry") or results.get("industry") or "general"
        return normalize_industry(industry)

    async def _generate_executive_summary(self) -> Dict[str, Any]:
        """Generate executive summary using Claude."""
        answers = self.context.get("answers", {})
        results = self.context.get("results", {})
        industry_knowledge = self.context.get("industry_knowledge", {})

        prompt = f"""Based on the following quiz responses, generate an executive summary for a CRB Analysis report.

QUIZ ANSWERS:
{json.dumps(answers, indent=2)}

PRELIMINARY RESULTS:
{json.dumps(results, indent=2)}

INDUSTRY: {self.context.get('industry', 'general')}
INDUSTRY KNOWLEDGE AVAILABLE: {industry_knowledge.get('is_supported', False)}

Generate a JSON executive summary with this EXACT structure:
{{
    "ai_readiness_score": <number 0-100>,
    "customer_value_score": <number 1-10>,
    "business_health_score": <number 1-10>,
    "key_insight": "<one sentence main insight>",
    "total_value_potential": {{
        "min": <number in euros>,
        "max": <number in euros>,
        "projection_years": 3
    }},
    "top_opportunities": [
        {{
            "title": "<opportunity name>",
            "value_potential": "<range like €10K-20K>",
            "time_horizon": "short|mid|long"
        }}
    ],
    "not_recommended": [
        {{
            "title": "<what NOT to do>",
            "reason": "<why not>"
        }}
    ],
    "recommended_investment": {{
        "year_1_min": <number>,
        "year_1_max": <number>
    }}
}}

Be realistic and honest. Include at least one "not_recommended" item.
Return ONLY the JSON, no explanation."""

        response = self.client.messages.create(
            model=settings.DEFAULT_MODEL,
            max_tokens=2000,
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            content = response.content[0].text.strip()
            # Handle potential markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse executive summary: {e}")
            # Return default structure
            return {
                "ai_readiness_score": results.get("ai_readiness_score", 50),
                "customer_value_score": 5,
                "business_health_score": 5,
                "key_insight": "Analysis requires more data for accurate assessment.",
                "total_value_potential": {"min": 10000, "max": 50000, "projection_years": 3},
                "top_opportunities": [],
                "not_recommended": [],
                "recommended_investment": {"year_1_min": 2000, "year_1_max": 10000},
            }

    async def _generate_findings(self) -> List[Dict[str, Any]]:
        """Generate findings based on quiz data and industry knowledge."""
        answers = self.context.get("answers", {})
        opportunities = self.context.get("opportunities", [])
        industry_knowledge = self.context.get("industry_knowledge", {})

        max_findings = settings.MAX_FINDINGS_QUICK if self.tier == "quick" else settings.MAX_FINDINGS_FULL

        prompt = f"""Analyze the quiz responses and generate findings for a CRB report.

QUIZ ANSWERS:
{json.dumps(answers, indent=2)}

INDUSTRY OPPORTUNITIES AVAILABLE:
{json.dumps(opportunities[:10], indent=2) if opportunities else "None specific to this industry"}

INDUSTRY BENCHMARKS:
{json.dumps(self.context.get('benchmarks', {}), indent=2, default=str)[:1500]}

Generate {max_findings} findings as a JSON array. Each finding must have:
{{
    "id": "<uuid>",
    "title": "<finding title>",
    "description": "<detailed description>",
    "category": "efficiency|growth|risk|compliance|customer_experience",
    "customer_value_score": <1-10>,
    "business_health_score": <1-10>,
    "value_saved": {{
        "hours_per_week": <number>,
        "hourly_rate": <number, default 50>,
        "annual_savings": <calculated>
    }},
    "value_created": {{
        "description": "<how this creates new value>",
        "potential_revenue": <number or null>
    }},
    "confidence": "high|medium|low",
    "sources": ["<source references>"],
    "time_horizon": "short|mid|long"
}}

Requirements:
- Only include findings that score 6+ on BOTH customer_value_score AND business_health_score
- Be specific about time savings (hours per week)
- Show realistic value calculations
- Include confidence levels
- Mix of quick wins and strategic items

Return ONLY the JSON array, no explanation."""

        response = self.client.messages.create(
            model=settings.DEFAULT_MODEL,
            max_tokens=4000,
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            content = response.content[0].text.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            findings = json.loads(content)

            # Ensure each finding has an ID
            for finding in findings:
                if "id" not in finding:
                    finding["id"] = str(uuid.uuid4())

            return findings[:max_findings]
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse findings: {e}")
            return []

    async def _generate_recommendations(self, findings: List[Dict]) -> List[Dict[str, Any]]:
        """Generate recommendations with three options pattern."""
        vendors = self.context.get("vendors", [])

        # Group findings by priority
        high_priority = [f for f in findings if f.get("customer_value_score", 0) >= 8 or f.get("business_health_score", 0) >= 8]
        other = [f for f in findings if f not in high_priority]

        priority_findings = high_priority[:5] + other[:5]  # Top 10 for recommendations

        prompt = f"""Based on these findings, generate detailed recommendations with the THREE OPTIONS pattern.

TOP FINDINGS:
{json.dumps(priority_findings, indent=2)}

AVAILABLE VENDORS FOR THIS INDUSTRY:
{json.dumps(vendors[:15], indent=2) if vendors else "Use general market vendors"}

For each recommendation, use this EXACT structure:
{{
    "id": "<uuid>",
    "finding_id": "<id of related finding>",
    "title": "<recommendation title>",
    "description": "<what to do>",
    "why_it_matters": {{
        "customer_value": "<how this helps their customers>",
        "business_health": "<how this helps the business>"
    }},
    "priority": "high|medium|low",
    "crb_analysis": {{
        "cost": {{
            "short_term": {{ "software": <number>, "implementation": <number>, "training": <number> }},
            "mid_term": {{ "software": <number>, "maintenance": <number> }},
            "long_term": {{ "software": <number>, "upgrades": <number> }},
            "total": <sum>
        }},
        "risk": [
            {{
                "description": "<risk>",
                "probability": "low|medium|high",
                "impact": <number>,
                "mitigation": "<how to mitigate>",
                "time_horizon": "short|mid|long"
            }}
        ],
        "benefit": {{
            "short_term": {{ "value_saved": <number>, "value_created": <number> }},
            "mid_term": {{ "value_saved": <number>, "value_created": <number> }},
            "long_term": {{ "value_saved": <number>, "value_created": <number> }},
            "total": <sum>
        }}
    }},
    "options": {{
        "off_the_shelf": {{
            "name": "<specific tool name>",
            "vendor": "<company>",
            "monthly_cost": <number>,
            "implementation_weeks": <number>,
            "pros": ["<pro1>", "<pro2>"],
            "cons": ["<con1>", "<con2>"]
        }},
        "best_in_class": {{
            "name": "<specific tool name>",
            "vendor": "<company>",
            "monthly_cost": <number>,
            "implementation_weeks": <number>,
            "pros": ["<pro1>", "<pro2>"],
            "cons": ["<con1>", "<con2>"]
        }},
        "custom_solution": {{
            "approach": "<what a custom solution would look like>",
            "estimated_cost": {{ "min": <number>, "max": <number> }},
            "implementation_weeks": <number>,
            "pros": ["<pro1>", "<pro2>"],
            "cons": ["<con1>", "<con2>"]
        }}
    }},
    "our_recommendation": "off_the_shelf|best_in_class|custom_solution",
    "recommendation_rationale": "<why we recommend this option>",
    "roi_percentage": <number>,
    "payback_months": <number>,
    "assumptions": ["<assumption1>", "<assumption2>"]
}}

Generate 5-10 recommendations. Return ONLY the JSON array."""

        response = self.client.messages.create(
            model=settings.DEFAULT_MODEL,
            max_tokens=6000,
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            content = response.content[0].text.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            recommendations = json.loads(content)

            # Ensure each recommendation has an ID
            for rec in recommendations:
                if "id" not in rec:
                    rec["id"] = str(uuid.uuid4())

            return recommendations
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse recommendations: {e}")
            return []

    async def _generate_roadmap(self, recommendations: List[Dict]) -> Dict[str, Any]:
        """Generate implementation roadmap from recommendations."""
        prompt = f"""Based on these recommendations, create an implementation roadmap.

RECOMMENDATIONS:
{json.dumps(recommendations[:10], indent=2)}

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

Put quick wins first. Be specific and actionable.
Return ONLY the JSON."""

        response = self.client.messages.create(
            model=settings.DEFAULT_MODEL,
            max_tokens=2000,
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            content = response.content[0].text.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse roadmap: {e}")
            return {"short_term": [], "mid_term": [], "long_term": []}

    def _calculate_value_summary(self, findings: List[Dict], recommendations: List[Dict]) -> Dict[str, Any]:
        """Calculate total value summary from findings and recommendations."""
        # Calculate value saved
        total_hours_saved = sum(
            f.get("value_saved", {}).get("hours_per_week", 0) for f in findings
        )
        hourly_rate = 50  # Default hourly rate
        time_savings = total_hours_saved * hourly_rate * 52  # Annual

        # Calculate value created from findings
        value_created_from_findings = sum(
            f.get("value_created", {}).get("potential_revenue", 0) or 0 for f in findings
        )

        # Calculate from recommendations
        total_benefit_from_recs = sum(
            rec.get("crb_analysis", {}).get("benefit", {}).get("total", 0) or 0
            for rec in recommendations
        )

        # Apply uncertainty ranges (±20%)
        time_savings_min = int(time_savings * 0.8)
        time_savings_max = int(time_savings * 1.2)

        value_created_min = int((value_created_from_findings + total_benefit_from_recs) * 0.7)
        value_created_max = int((value_created_from_findings + total_benefit_from_recs) * 1.3)

        return {
            "value_saved": {
                "hours_per_week": total_hours_saved,
                "hourly_rate": hourly_rate,
                "time_savings_annual": time_savings,
                "subtotal": {"min": time_savings_min, "max": time_savings_max},
            },
            "value_created": {
                "from_findings": value_created_from_findings,
                "from_recommendations": total_benefit_from_recs,
                "subtotal": {"min": value_created_min, "max": value_created_max},
            },
            "total": {
                "min": time_savings_min + value_created_min,
                "max": time_savings_max + value_created_max,
            },
            "projection_years": 3,
        }

    def _generate_methodology_notes(self) -> Dict[str, Any]:
        """Generate methodology notes and disclaimers."""
        return {
            "data_sources": [
                "Quiz responses provided by business owner",
                "Industry benchmarks from our knowledge base",
                "Vendor pricing data (verified where possible)",
                "AI/automation adoption studies",
            ],
            "assumptions": [
                f"Hourly rate assumed at €50 unless specified",
                "3-year projection period for ROI calculations",
                "All estimates include ±20% uncertainty range",
                "Vendor pricing as of report generation date",
            ],
            "limitations": [
                "Estimates based on self-reported data",
                "Actual implementation results may vary",
                "Market conditions may affect vendor availability/pricing",
                "Recommendations should be validated with actual business data",
            ],
            "industry_benchmarks_used": list(self.context.get("benchmarks", {}).keys())[:5],
            "confidence_notes": "Findings marked as 'high' confidence have multiple supporting data points. "
                               "'Medium' confidence items are based on industry patterns. "
                               "'Low' confidence items are estimates requiring validation.",
        }


async def generate_report_for_quiz(quiz_session_id: str, tier: str = "quick") -> str:
    """
    Generate a report for a quiz session.

    Returns the report ID.
    """
    generator = ReportGenerator(quiz_session_id, tier)

    report_id = None
    async for update in generator.generate_report():
        logger.info(f"Report generation: {update.get('step')} ({update.get('progress')}%)")
        if update.get("report_id"):
            report_id = update["report_id"]

    return report_id


async def generate_report_streaming(quiz_session_id: str, tier: str = "quick") -> AsyncGenerator[str, None]:
    """
    Generate a report with SSE streaming updates.

    Yields SSE-formatted events.
    """
    generator = ReportGenerator(quiz_session_id, tier)

    async for update in generator.generate_report():
        yield f"data: {json.dumps(update)}\n\n"


async def get_report(report_id: str) -> Optional[Dict[str, Any]]:
    """Get a report by ID."""
    supabase = await get_async_supabase()

    result = await supabase.table("reports").select("*").eq(
        "id", report_id
    ).single().execute()

    return result.data if result.data else None


async def get_report_by_quiz_session(quiz_session_id: str) -> Optional[Dict[str, Any]]:
    """Get a report by quiz session ID."""
    supabase = await get_async_supabase()

    result = await supabase.table("reports").select("*").eq(
        "quiz_session_id", quiz_session_id
    ).single().execute()

    return result.data if result.data else None
