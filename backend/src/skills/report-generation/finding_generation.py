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
7. Generates Connect vs Replace paths based on existing stack (Phase 2C)

Output includes both automation paths:
- Connect: Use existing tools via API/integrations
- Replace: Switch to new software

See: docs/plans/2026-01-07-connect-vs-replace-design.md
"""

import json
import logging
from typing import Dict, Any, List, Optional
from statistics import mean

from src.skills.base import LLMSkill, SkillContext, SkillError
from src.models.finding_paths import (
    FindingWithPaths,
    ConnectPath,
    ReplacePath,
    WhyReplaceReasoning,
    StackItem,
    calculate_verdict,
    get_verdict_reasoning,
)
from src.models.crb import (
    CostBreakdown,
    RiskAssessment,
    BenefitQuantification,
    CRBAnalysis,
    ImplementationCostDIY,
    ImplementationCostProfessional,
    MonthlyCostItem,
    MonthlyCostBreakdown,
    HiddenCosts,
)

logger = logging.getLogger(__name__)


# Categories that map to different types of existing software
CATEGORY_TO_STACK_MAPPING = {
    "efficiency": ["Practice Management", "Job Management", "Project Management", "Automation"],
    "growth": ["CRM", "Marketing", "Email Marketing", "Sales"],
    "risk": ["Practice Management", "Compliance", "Security"],
    "compliance": ["Practice Management", "Document Management", "Compliance"],
    "customer_experience": [
        "Customer Support", "Patient Communication", "Client Communication",
        "Phone & SMS", "Scheduling", "CRM"
    ],
}


class FindingGenerationSkill(LLMSkill[List[Dict[str, Any]]]):
    """
    Generate findings for CRB reports with Connect vs Replace paths.

    This is an LLM-powered skill that analyzes quiz data and generates
    structured findings with Two Pillars scoring, confidence levels,
    and automation paths (Connect vs Replace) based on existing stack.
    """

    name = "finding-generation"
    description = "Generate calibrated findings with Two Pillars scoring and Connect vs Replace paths"
    version = "2.0.0"

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
        # Phase 2C fields
        "impact_monthly": 0,
        "relevant_stack": [],
        "avg_api_score": None,
        "connect_path": None,
        "replace_path": None,
        "verdict": "EITHER",
        "verdict_reasoning": "",
        "why_replace": None,
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
            context: SkillContext with quiz_answers, industry, existing_stack, and optional expertise

        Returns:
            List of finding dictionaries matching report schema with Connect vs Replace paths
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
        existing_stack = context.existing_stack or []

        # Get opportunities and benchmarks from knowledge
        opportunities_data = knowledge.get("opportunities", {})
        # Handle both dict (with ai_opportunities key) and list formats
        if isinstance(opportunities_data, dict):
            opportunities = opportunities_data.get("ai_opportunities", [])
        else:
            opportunities = opportunities_data if isinstance(opportunities_data, list) else []
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
            existing_stack=existing_stack,
            max_findings=max_findings,
            min_not_recommended=min_not_recommended,
        )

        # Apply expertise calibration if available
        if expertise:
            findings = self._calibrate_with_expertise(findings, expertise)

        # Post-process: Add Connect vs Replace paths and verdicts
        findings = self._add_automation_paths(findings, existing_stack)

        # Validate and normalize findings
        findings = self._validate_findings(findings)

        return findings

    def _get_relevant_stack(
        self,
        finding: Dict[str, Any],
        existing_stack: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Get tools from existing stack relevant to this finding.

        Uses category mapping to find tools that could help automate this finding.
        """
        if not existing_stack:
            return []

        category = finding.get("category", "efficiency")
        relevant_categories = CATEGORY_TO_STACK_MAPPING.get(category, [])

        relevant_tools = []
        for tool in existing_stack:
            tool_category = tool.get("category", "")
            # Check if tool's category matches any relevant category
            if any(cat.lower() in tool_category.lower() for cat in relevant_categories):
                relevant_tools.append(tool)
            # Also include tools with good API scores (they're always useful)
            elif tool.get("api_score", 0) >= 4 and tool not in relevant_tools:
                relevant_tools.append(tool)

        return relevant_tools

    def _calculate_avg_api_score(self, relevant_stack: List[Dict[str, Any]]) -> Optional[float]:
        """Calculate average API score for relevant stack."""
        scores = [
            tool.get("api_score")
            for tool in relevant_stack
            if tool.get("api_score") is not None
        ]
        if not scores:
            return None
        return mean(scores)

    def _add_automation_paths(
        self,
        findings: List[Dict[str, Any]],
        existing_stack: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Add Connect vs Replace paths and verdicts to each finding.

        This is called after the main LLM generation to enrich findings
        with automation paths based on the user's existing stack.
        """
        for finding in findings:
            # Get relevant tools for this finding
            relevant_stack = self._get_relevant_stack(finding, existing_stack)
            finding["relevant_stack"] = relevant_stack

            # Calculate average API score
            avg_api_score = self._calculate_avg_api_score(relevant_stack)
            finding["avg_api_score"] = avg_api_score

            # Calculate verdict based on API score
            verdict = calculate_verdict(avg_api_score)
            finding["verdict"] = verdict

            # Generate verdict reasoning
            connect_cost = (
                finding.get("connect_path", {}).get("monthly_cost_estimate")
                if finding.get("connect_path") else None
            )
            replace_cost = (
                finding.get("replace_path", {}).get("monthly_cost")
                if finding.get("replace_path") else None
            )
            finding["verdict_reasoning"] = get_verdict_reasoning(
                verdict, avg_api_score, connect_cost, replace_cost
            )

            # If Connect path wasn't generated by LLM but score supports it, mark as viable
            if verdict in ("CONNECT", "EITHER") and not finding.get("connect_path"):
                finding["connect_path"] = None  # Explicitly None, not missing

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

    def _format_existing_stack(self, existing_stack: List[Dict[str, Any]]) -> str:
        """Format existing stack for the prompt."""
        if not existing_stack:
            return "No existing software stack provided."

        lines = ["USER'S EXISTING SOFTWARE STACK:"]
        for tool in existing_stack:
            name = tool.get("name", tool.get("slug", "Unknown"))
            api_score = tool.get("api_score", "?")
            category = tool.get("category", "Unknown")
            has_api = "API" if tool.get("has_api") else ""
            has_webhooks = "Webhooks" if tool.get("has_webhooks") else ""
            has_zapier = "Zapier" if tool.get("has_zapier") else ""
            integrations = ", ".join(filter(None, [has_api, has_webhooks, has_zapier]))

            lines.append(
                f"- {name} ({category}): API Score {api_score}/5"
                + (f" - {integrations}" if integrations else "")
            )

        return "\n".join(lines)

    async def _generate_findings(
        self,
        answers: Dict[str, Any],
        industry: str,
        opportunities: List[Dict[str, Any]],
        benchmarks: Dict[str, Any],
        expertise_context: Dict[str, Any],
        existing_stack: List[Dict[str, Any]],
        max_findings: int,
        min_not_recommended: int,
    ) -> List[Dict[str, Any]]:
        """Generate findings using Claude with Connect vs Replace paths."""
        # Build expertise injection for prompt
        expertise_injection = ""
        if expertise_context.get("has_data"):
            expertise_injection = f"""
INDUSTRY EXPERTISE (from {expertise_context['total_analyses']} previous analyses):
- Common pain points in {industry}: {', '.join(expertise_context['common_pain_points'][:3]) or 'None recorded'}
- What works well: {', '.join(expertise_context['effective_patterns'][:2]) or 'No patterns yet'}
- What to AVOID recommending: {', '.join(expertise_context['anti_patterns'][:2]) or 'No anti-patterns yet'}
- Average potential savings: {expertise_context['avg_potential_savings']:,.0f}

USE THIS EXPERTISE:
- Prioritize findings around known pain points
- Apply effective patterns to recommendations
- AVOID anti-patterns in your findings
"""

        # Format existing stack for prompt
        stack_context = self._format_existing_stack(existing_stack)
        has_stack = bool(existing_stack)

        prompt = f"""Analyze the quiz responses and generate findings for a CRB Analysis report.

QUIZ ANSWERS:
{json.dumps(answers, indent=2)}

INDUSTRY: {industry}

INDUSTRY OPPORTUNITIES AVAILABLE:
{json.dumps(opportunities[:5], indent=2) if opportunities else "None specific"}

INDUSTRY BENCHMARKS:
{json.dumps(benchmarks, indent=2) if benchmarks else "Use general industry standards"}

{stack_context}
{expertise_injection}

===============================================================================
FINDING REQUIREMENTS
===============================================================================

Generate {max_findings} findings total:
- At least {max_findings - min_not_recommended} RECOMMENDED findings (score 6+ on BOTH pillars)
- Exactly {min_not_recommended} NOT-RECOMMENDED findings (score below 6 on at least one pillar)

===============================================================================
TWO PILLARS SCORING (CRITICAL)
===============================================================================

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

===============================================================================
CONNECT VS REPLACE PATHS (CRITICAL - PHASE 2C)
===============================================================================

{"For each finding, generate BOTH automation paths:" if has_stack else "Generate Replace paths for each finding (no existing stack provided):"}

**CONNECT PATH** (use existing tools):
- Show how to automate using tools from their existing stack
- Include: integration_flow (e.g., "Open Dental -> n8n -> Twilio"), monthly_cost_estimate, setup_effort_hours
- Explain WHY this works (what API capabilities enable it)
- Only viable if relevant tools have API score >= 3

**REPLACE PATH** (new software):
- Recommend vendor that solves this natively
- Include: vendor_name, monthly_cost, setup_effort_weeks
- List trade-offs vs Connect path

{"If the user's existing tools have low API scores (< 3), explain WHY replacement is recommended in the why_replace field." if has_stack else ""}

===============================================================================
SOURCE CITATION REQUIREMENTS - MANDATORY FOR EVERY FINDING
===============================================================================

Every finding MUST cite sources using ONLY these formats:

1. QUIZ RESPONSE (strongest evidence):
   Format: "Quiz Q[N]: '[exact quote from their answer]'"
   Example: "Quiz Q5: 'We spend 40+ hours per week on repetitive customer support tasks'"

2. BENCHMARK (must include source + year):
   Format: "[Metric]: [Value] (Source: [Organization/Report Name], [Year])"
   Example: "No-show rate: 18% industry average (Journal of Dental Hygiene, 2024)"

3. CALCULATION (must show all inputs):
   Format: "Calculated: [formula] = [result] (inputs from: [source1], [source2])"
   Example: "Calculated: 500 tickets × 15min × €45/hr ÷ 60 = €5,625/month (ticket count: Quiz Q3, time: Zendesk benchmark 2024)"

FORBIDDEN source formats - DO NOT USE:
- "Industry average" without source name and year
- "Studies show" without specific study citation
- "Best practice" without reference
- "Typically" or "usually" without data reference

===============================================================================
CONFIDENCE SCORING - STRICTLY ENFORCED DISTRIBUTION
===============================================================================

For 10 findings, you MUST assign EXACTLY:
- 3 findings = HIGH confidence
- 5 findings = MEDIUM confidence
- 2 findings = LOW confidence

HIGH (exactly 30% of findings):
- REQUIRES: User explicitly stated this problem in quiz (direct quote available)
- REQUIRES: Specific benchmark with source supports the finding
- REQUIRES: ROI calculation uses user-provided numbers

MEDIUM (exactly 50% of findings):
- Quiz answer implies this issue (inference, not direct statement)
- Industry benchmark likely applies but not perfectly matched
- One strong data point, some assumptions

LOW (exactly 20% of findings):
- Based on industry patterns, user did NOT mention this directly
- Significant assumptions required
- MUST include explicit uncertainty: "You didn't mention this, but [industry] businesses often face..."

ENFORCEMENT: Your output MUST have exactly 2 LOW confidence findings that acknowledge uncertainty

===============================================================================

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
        "is_not_recommended": false,
        "impact_monthly": <monthly impact in EUR>,

        "connect_path": {{"If existing stack supports automation (API score >= 3), or null if not viable"
            "integration_flow": "Tool A -> n8n -> Tool B",
            "flow_steps": ["Step 1: specific action", "Step 2: specific action"],
            "what_it_does": "Brief description of automation",

            "cost": {{
                "implementation_diy": {{
                    "hours": <number>,
                    "hourly_rate": 50,
                    "total": <hours × 50>,
                    "description": "What work is required"
                }},
                "implementation_professional": {{
                    "estimate": <number>,
                    "source": "n8n agency rates / freelancer market"
                }},
                "monthly_ongoing": {{
                    "breakdown": [
                        {{"item": "n8n cloud", "cost": <number>}},
                        {{"item": "API costs", "cost": <number>}}
                    ],
                    "total": <sum of breakdown>
                }},
                "hidden": {{
                    "training_hours": <number>,
                    "productivity_dip_weeks": <number>
                }}
            }},

            "risk": {{
                "implementation_score": <1-5, where 1=trivial, 5=complex>,
                "implementation_reason": "Why this score",
                "dependency_risk": "What if [tool] goes down or API changes",
                "reversal_difficulty": "Easy|Medium|Hard - how hard to undo"
            }},

            "benefit": {{
                "primary_metric": "What improves (e.g., response time, no-show rate)",
                "baseline": "Current state from quiz",
                "target": "Expected state from benchmark",
                "monthly_value": <number in EUR>,
                "calculation": "Show math: [baseline] - [target] × [value per unit] = [result]"
            }},

            "tools_used": ["n8n", "Twilio", "Claude API"],
            "why_this_works": "Specific API capabilities that enable this"
        }},

        "replace_path": {{
            "vendor_slug": "vendor-name",
            "vendor_name": "Vendor Name",
            "vendor_description": "What this vendor does",

            "cost": {{
                "monthly": <number>,
                "setup_one_time": <number>,
                "migration_estimate": <number or 0>
            }},

            "risk": {{
                "implementation_score": <1-5>,
                "migration_complexity": "Low|Medium|High",
                "vendor_lock_in": "Risk of switching away later"
            }},

            "benefit": {{
                "primary_metric": "What improves",
                "expected_improvement": "X% reduction in Y",
                "monthly_value": <number>
            }},

            "trade_offs_vs_connect": ["Trade-off 1", "Trade-off 2"],
            "benefits_vs_connect": ["Benefit 1", "Benefit 2"]
        }}
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
        "what_instead": "Better alternative",
        "connect_path": null,
        "replace_path": null
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

═══════════════════════════════════════════════════════════════════════════════
BANNED LANGUAGE - Using any of these INVALIDATES your output:
═══════════════════════════════════════════════════════════════════════════════
- "streamline operations", "optimize workflow", "enhance efficiency"
- "drive growth", "unlock potential", "accelerate transformation"
- "seamless integration", "robust solution", "cutting-edge", "best-in-class"
- "leverage AI", "harness the power of", "revolutionize"
- "well-positioned", "strong foundations", "significant opportunity"

INSTEAD OF: "Streamline your customer support operations"
USE: "Reduce average response time from 4 hours to 15 minutes"

INSTEAD OF: "Leverage AI to optimize scheduling"
USE: "Automate 80% of appointment confirmations, saving 6 hours/week"

═══════════════════════════════════════════════════════════════════════════════
KEY PRINCIPLES
═══════════════════════════════════════════════════════════════════════════════
1. EVIDENCE-BASED: Every finding MUST cite quiz answers or benchmarks with sources
2. TWO PILLARS: Always score both Customer Value AND Business Health
3. CONFIDENCE DISTRIBUTION: Enforce exactly 30% HIGH, 50% MEDIUM, 20% LOW
4. INCLUDE WARNINGS: Always include "not recommended" items with alternatives
5. SPECIFIC NUMBERS: Replace adjectives with quantities (hours, euros, percentages)
6. CONSERVATIVE: Default to lower estimates - under-promise, over-deliver
7. CONNECT VS REPLACE: Show both paths with full CRB (Cost-Risk-Benefit) analysis

═══════════════════════════════════════════════════════════════════════════════
SCORING GUIDANCE
═══════════════════════════════════════════════════════════════════════════════
- Score of 10 is RARE - reserve for truly transformative impacts
- Most findings should be 6-8 range
- "Not recommended" items should have at least one score below 6
- If both pillars are high, it's a priority recommendation

═══════════════════════════════════════════════════════════════════════════════
ROI REALITY CHECKS - APPLY TO EVERY FINDING
═══════════════════════════════════════════════════════════════════════════════
1. If annual_savings > €50,000: Explain why credible for SMB, show detailed calculation
2. If hours_per_week saved > 20: Cite quiz answer proving this time investment exists
3. If ROI > 300%: Include sensitivity analysis, explain why finding is exceptional
4. DEFAULT TO CONSERVATIVE estimates when uncertain

═══════════════════════════════════════════════════════════════════════════════
CONNECT VS REPLACE GUIDANCE
═══════════════════════════════════════════════════════════════════════════════
- If existing tools have good APIs (score 4-5), prefer Connect
- If existing tools have limited APIs (score 1-2), recommend Replace with clear reasoning
- Always show trade-offs between paths
- Be realistic about setup effort and costs
- Include full CRB structure for both paths"""

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

    def _parse_cost_breakdown(self, cost_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse CRB cost breakdown from LLM output."""
        result = {}

        # Implementation DIY
        if cost_data.get("implementation_diy"):
            diy = cost_data["implementation_diy"]
            result["implementation_diy"] = {
                "hours": diy.get("hours", 0),
                "hourly_rate": diy.get("hourly_rate", 50),
                "total": diy.get("total", diy.get("hours", 0) * diy.get("hourly_rate", 50)),
                "description": diy.get("description", ""),
            }

        # Implementation Professional
        if cost_data.get("implementation_professional"):
            pro = cost_data["implementation_professional"]
            result["implementation_professional"] = {
                "estimate": pro.get("estimate", 0),
                "source": pro.get("source", ""),
            }

        # Monthly ongoing
        if cost_data.get("monthly_ongoing"):
            monthly = cost_data["monthly_ongoing"]
            breakdown = []
            for item in monthly.get("breakdown", []):
                if isinstance(item, dict):
                    breakdown.append({
                        "item": item.get("item", ""),
                        "cost": item.get("cost", 0),
                    })
            result["monthly_ongoing"] = {
                "breakdown": breakdown,
                "total": monthly.get("total", sum(i["cost"] for i in breakdown)),
            }

        # Hidden costs
        if cost_data.get("hidden"):
            hidden = cost_data["hidden"]
            result["hidden"] = {
                "training_hours": hidden.get("training_hours", 0),
                "productivity_dip_weeks": hidden.get("productivity_dip_weeks", 0),
            }

        return result

    def _parse_replace_cost(self, cost_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse CRB cost for Replace path."""
        return {
            "monthly": cost_data.get("monthly", 0),
            "setup_one_time": cost_data.get("setup_one_time", 0),
            "migration_estimate": cost_data.get("migration_estimate", 0),
        }

    def _parse_risk_assessment(self, risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse CRB risk assessment from LLM output."""
        return {
            "implementation_score": max(1, min(5, risk_data.get("implementation_score", 3))),
            "implementation_reason": risk_data.get("implementation_reason", ""),
            "dependency_risk": risk_data.get("dependency_risk", ""),
            "reversal_difficulty": risk_data.get("reversal_difficulty", "Medium"),
        }

    def _parse_replace_risk(self, risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse CRB risk for Replace path."""
        return {
            "implementation_score": max(1, min(5, risk_data.get("implementation_score", 3))),
            "migration_complexity": risk_data.get("migration_complexity", "Medium"),
            "vendor_lock_in": risk_data.get("vendor_lock_in", ""),
        }

    def _parse_benefit(self, benefit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse CRB benefit quantification from LLM output."""
        return {
            "primary_metric": benefit_data.get("primary_metric", ""),
            "baseline": benefit_data.get("baseline", ""),
            "target": benefit_data.get("target", ""),
            "monthly_value": benefit_data.get("monthly_value", 0),
            "calculation": benefit_data.get("calculation", ""),
            "expected_improvement": benefit_data.get("expected_improvement", ""),
        }

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

            # Phase 2C fields
            validated_finding["impact_monthly"] = finding.get("impact_monthly", 0)
            validated_finding["relevant_stack"] = finding.get("relevant_stack", [])
            validated_finding["avg_api_score"] = finding.get("avg_api_score")
            validated_finding["verdict"] = finding.get("verdict", "EITHER")
            validated_finding["verdict_reasoning"] = finding.get("verdict_reasoning", "")

            # Handle connect_path with CRB structure
            if finding.get("connect_path") and isinstance(finding["connect_path"], dict):
                cp = finding["connect_path"]
                validated_connect = {
                    "integration_flow": cp.get("integration_flow", ""),
                    "flow_steps": cp.get("flow_steps", []),
                    "what_it_does": cp.get("what_it_does", ""),
                    "monthly_cost_estimate": cp.get("monthly_cost_estimate", 0),
                    "setup_effort_hours": cp.get("setup_effort_hours", 0),
                    "why_this_works": cp.get("why_this_works", ""),
                    "tools_used": cp.get("tools_used", []),
                    "prerequisites": cp.get("prerequisites", []),
                    "limitations": cp.get("limitations"),
                }

                # Parse CRB structure if present
                if cp.get("cost") and isinstance(cp["cost"], dict):
                    validated_connect["cost"] = self._parse_cost_breakdown(cp["cost"])
                if cp.get("risk") and isinstance(cp["risk"], dict):
                    validated_connect["risk"] = self._parse_risk_assessment(cp["risk"])
                if cp.get("benefit") and isinstance(cp["benefit"], dict):
                    validated_connect["benefit"] = self._parse_benefit(cp["benefit"])

                validated_finding["connect_path"] = validated_connect
            else:
                validated_finding["connect_path"] = None

            # Handle replace_path with CRB structure
            if finding.get("replace_path") and isinstance(finding["replace_path"], dict):
                rp = finding["replace_path"]
                validated_replace = {
                    "vendor_slug": rp.get("vendor_slug", ""),
                    "vendor_name": rp.get("vendor_name", ""),
                    "vendor_description": rp.get("vendor_description", ""),
                    "monthly_cost": rp.get("monthly_cost", 0),
                    "setup_effort_weeks": rp.get("setup_effort_weeks", 0),
                    "requires_migration": rp.get("requires_migration", True),
                    "trade_offs": rp.get("trade_offs", rp.get("trade_offs_vs_connect", [])),
                    "benefits": rp.get("benefits", rp.get("benefits_vs_connect", [])),
                }

                # Parse CRB structure if present
                if rp.get("cost") and isinstance(rp["cost"], dict):
                    validated_replace["cost"] = self._parse_replace_cost(rp["cost"])
                if rp.get("risk") and isinstance(rp["risk"], dict):
                    validated_replace["risk"] = self._parse_replace_risk(rp["risk"])
                if rp.get("benefit") and isinstance(rp["benefit"], dict):
                    validated_replace["benefit"] = self._parse_benefit(rp["benefit"])

                validated_finding["replace_path"] = validated_replace
            else:
                validated_finding["replace_path"] = None

            # Handle why_replace (for low API score recommendations)
            if finding.get("why_replace") and isinstance(finding["why_replace"], dict):
                wr = finding["why_replace"]
                validated_finding["why_replace"] = {
                    "current_tool": wr.get("current_tool", ""),
                    "api_score": wr.get("api_score", 0),
                    "api_limitations": wr.get("api_limitations", []),
                    "what_you_cant_build": wr.get("what_you_cant_build", []),
                    "growth_ceiling": wr.get("growth_ceiling", ""),
                    "recommended_alternative": wr.get("recommended_alternative", ""),
                    "alternative_api_score": wr.get("alternative_api_score", 0),
                    "alternative_benefits": wr.get("alternative_benefits", []),
                    "migration_effort": wr.get("migration_effort", ""),
                }
            else:
                validated_finding["why_replace"] = None

            validated.append(validated_finding)

        return validated


# For skill discovery
__all__ = ["FindingGenerationSkill"]
