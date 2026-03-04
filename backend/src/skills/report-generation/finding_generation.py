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
import structlog
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
from src.services.crb_calculation_service import get_effective_hourly_rate

logger = structlog.get_logger(__name__)


# Categories that map to different types of existing software
# Must match VALID_CATEGORIES in validation_service.py
VALID_FINDING_CATEGORIES = [
    "operations", "sales", "customer_experience", "finance",
    "marketing", "hr", "compliance", "technology"
]

CATEGORY_TO_STACK_MAPPING = {
    "operations": ["Practice Management", "Job Management", "Project Management", "Automation"],
    "sales": ["CRM", "Sales", "Quoting", "Proposals"],
    "customer_experience": [
        "Customer Support", "Patient Communication", "Client Communication",
        "Phone & SMS", "Scheduling", "CRM"
    ],
    "finance": ["Accounting", "Invoicing", "Payments", "Bookkeeping"],
    "marketing": ["Marketing", "Email Marketing", "Social Media", "SEO"],
    "hr": ["HR", "Payroll", "Time Tracking", "Scheduling"],
    "compliance": ["Practice Management", "Document Management", "Compliance", "Security"],
    "technology": ["IT Management", "Automation", "Integration", "API"],
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
        "category": "operations",
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
        # Agent opportunity (e-commerce only)
        "agent_opportunity": None,
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
        max_findings = 7 if tier == "quick" else 15
        min_not_recommended = 2 if tier == "quick" else 3

        # Extract data from context
        answers = context.quiz_answers or {}
        industry = context.industry
        expertise = context.expertise or {}
        knowledge = context.knowledge or {}
        existing_stack = context.existing_stack or []
        currency = context.currency
        currency_symbol = context.currency_symbol

        # Extract hourly_rate using industry-aware resolution
        hourly_rate, hourly_rate_source = get_effective_hourly_rate(
            industry=industry,
            quiz_answers=answers,
        )
        # Also check metadata override (e.g., from workshop or admin)
        if context.metadata.get("hourly_rate"):
            try:
                hourly_rate = float(context.metadata["hourly_rate"])
                hourly_rate_source = "metadata override"
            except (ValueError, TypeError):
                pass

        # Store for use in validation and downstream reporting
        context.metadata["effective_hourly_rate"] = hourly_rate
        context.metadata["hourly_rate_source"] = hourly_rate_source

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

        # Extract tool categories from context (from quiz current_tools answer)
        tool_categories = context.current_tool_categories or answers.get("current_tools", [])
        semantic_retrieval = context.metadata.get("semantic_retrieval", {})
        if not isinstance(semantic_retrieval, dict):
            semantic_retrieval = {}

        # Generate findings using LLM
        findings = await self._generate_findings(
            answers=answers,
            industry=industry,
            opportunities=opportunities,
            benchmarks=benchmarks,
            semantic_retrieval=semantic_retrieval,
            expertise_context=expertise_context,
            existing_stack=existing_stack,
            max_findings=max_findings,
            min_not_recommended=min_not_recommended,
            currency=currency,
            currency_symbol=currency_symbol,
            hourly_rate=hourly_rate,
            tool_categories=tool_categories,
        )

        # Apply expertise calibration if available
        if expertise:
            findings = self._calibrate_with_expertise(findings, expertise)

        # Post-process: Add Connect vs Replace paths and verdicts
        findings = self._add_automation_paths(findings, existing_stack)

        # Validate and normalize findings with the effective hourly rate
        findings = self._validate_findings(findings, default_hourly_rate=hourly_rate)

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

        category = finding.get("category", "operations")
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

    def _format_tool_categories(self, tool_categories: Optional[List[str]]) -> str:
        """Format tool categories from quiz answers for the prompt."""
        if not tool_categories:
            return ""

        # Map category values to readable names
        category_names = {
            "crm": "CRM (Salesforce, HubSpot, etc.)",
            "project_management": "Project Management (Asana, Monday, Trello)",
            "accounting": "Accounting (QuickBooks, Xero, etc.)",
            "email_marketing": "Email Marketing (Mailchimp, etc.)",
            "social_media": "Social Media Management",
            "ecommerce": "E-commerce Platform (Shopify, WooCommerce)",
            "spreadsheets": "Spreadsheets (Excel, Google Sheets)",
            "communication": "Team Communication (Slack, Teams)",
            "analytics": "Analytics (Google Analytics, etc.)",
        }

        lines = ["USER'S CURRENT TOOL CATEGORIES (from quiz):"]
        for cat in tool_categories:
            readable = category_names.get(cat, cat.replace("_", " ").title())
            lines.append(f"- {readable}")

        lines.append("")
        lines.append("IMPORTANT: When generating findings, acknowledge these existing tool categories.")
        lines.append("Recommendations should CONNECT with these tools where possible, not ignore them.")

        return "\n".join(lines)

    async def _generate_findings(
        self,
        answers: Dict[str, Any],
        industry: str,
        opportunities: List[Dict[str, Any]],
        benchmarks: Dict[str, Any],
        semantic_retrieval: Optional[Dict[str, Any]],
        expertise_context: Dict[str, Any],
        existing_stack: List[Dict[str, Any]],
        max_findings: int,
        min_not_recommended: int,
        currency: str = "EUR",
        currency_symbol: str = "€",
        hourly_rate: float = 50,
        tool_categories: Optional[List[str]] = None,
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

        # Build agent opportunity prompt for e-commerce
        agent_opportunity_prompt = ""
        if industry.lower() in ("ecommerce", "e-commerce", "ecom"):
            agent_opps = []
            for opp in opportunities:
                if "agent_opportunity" in opp:
                    agent_opps.append({
                        "opportunity_id": opp.get("id"),
                        "agent_type": opp["agent_opportunity"]["agent_type"],
                        "what_it_does": opp["agent_opportunity"]["what_it_does"],
                        "estimated_impact": opp["agent_opportunity"]["estimated_impact"],
                        "deployment_timeline": opp["agent_opportunity"]["deployment_timeline"],
                        "prerequisites": opp["agent_opportunity"]["prerequisites"],
                    })

            if agent_opps:
                agent_opportunity_prompt = f"""
===============================================================================
AGENT OPPORTUNITY (E-COMMERCE ONLY)
===============================================================================

For e-commerce findings, some opportunities can be handled by a CRB-managed AI agent.
When a finding matches one of the agent opportunities below, include the agent_opportunity
field in that finding's JSON output.

AVAILABLE AGENT OPPORTUNITIES:
{json.dumps(agent_opps, indent=2)}

For findings that match an agent opportunity, add this field to the finding JSON:
"agent_opportunity": {{
  "agent_type": "<from the matching opportunity>",
  "what_it_does": "<from the matching opportunity, adjusted to client context>",
  "estimated_impact": {{<adjust estimates based on quiz answers — company size, ticket volume, etc.>}},
  "deployment_timeline": "<from the matching opportunity>",
  "prerequisites": [<from matching opportunity, filtered to what client doesn't already have>]
}}

IMPORTANT:
- Only include agent_opportunity when the finding genuinely matches an available agent
- Adjust impact estimates based on the client's actual numbers from quiz answers
- Remove prerequisites the client already has (check their existing stack)
- Do NOT add agent_opportunity to every finding — only where it's genuinely applicable
"""

        # Format existing stack for prompt
        stack_context = self._format_existing_stack(existing_stack)
        has_stack = bool(existing_stack)

        # Format tool categories from quiz
        tool_categories_context = self._format_tool_categories(tool_categories)
        has_tool_categories = bool(tool_categories)

        semantic_items: List[Dict[str, Any]] = []
        semantic_retrieval = semantic_retrieval or {}
        for source_key in ("opportunities", "vendors", "case_studies", "patterns"):
            for item in semantic_retrieval.get(source_key, [])[:3]:
                semantic_items.append({
                    "type": source_key.rstrip("s"),
                    "title": item.get("title", ""),
                    "similarity": item.get("similarity"),
                    "summary": str(item.get("content", ""))[:220],
                })

        prompt = f"""Analyze the quiz responses and generate findings for a CRB Analysis report.

CURRENCY: {currency} (use {currency_symbol} symbol for all monetary values)

QUIZ ANSWERS:
{json.dumps(answers, indent=2)}

INDUSTRY: {industry}

INDUSTRY OPPORTUNITIES AVAILABLE:
{json.dumps(opportunities[:5], indent=2) if opportunities else "None specific"}

INDUSTRY BENCHMARKS:
{json.dumps(benchmarks, indent=2) if benchmarks else "Use general industry standards"}

SEMANTICALLY RETRIEVED CONTEXT (RAG):
{json.dumps(semantic_items, indent=2) if semantic_items else "No semantic retrieval available"}

{stack_context}
{tool_categories_context}
{expertise_injection}
{agent_opportunity_prompt}

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
        "category": "operations|sales|customer_experience|finance|marketing|hr|compliance|technology",
        "customer_value_score": <1-10>,
        "business_health_score": <1-10>,
        "current_state": "How they're doing this now (from quiz answers)",
        "value_saved": {{
            "hours_per_week": <number>,
            "hourly_rate": {hourly_rate},
            "annual_savings": <hours * {hourly_rate} * 52>
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
                    "hourly_rate": {hourly_rate},
                    "total": <hours × {hourly_rate}>,
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
                }},
                "opportunity_cost": <number in EUR, what you can't do while implementing>,
                "opportunity_cost_description": "e.g., Delays CRM migration by 3 months",
                "complexity_cost": <number in EUR, integration complexity and maintenance burden>,
                "complexity_cost_description": "e.g., Requires connecting 3 systems with ongoing API maintenance",
                "brand_trust_cost": <number in EUR, risk to brand/customer trust during transition>,
                "brand_trust_cost_description": "e.g., Customers may experience slower responses during 2-week migration"
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
                "migration_estimate": <number or 0>,
                "opportunity_cost": <number in EUR, what you can't do while migrating>,
                "opportunity_cost_description": "e.g., Team focused on migration instead of client work for 4 weeks",
                "complexity_cost": <number in EUR, migration complexity and data mapping effort>,
                "complexity_cost_description": "e.g., Data migration from 3 legacy systems, custom field mapping required",
                "brand_trust_cost": <number in EUR, risk to brand/customer trust during switchover>,
                "brand_trust_cost_description": "e.g., 1-week service disruption risk during data migration"
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
                max_tokens=10000,
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
THE 6 COST DIMENSIONS (6C FRAMEWORK) - INCLUDE IN EVERY PATH
═══════════════════════════════════════════════════════════════════════════════
Every cost analysis must address all 6 cost dimensions:
1. Financial Cost - implementation + ongoing (captured in implementation_diy/professional + monthly_ongoing)
2. Time Cost - learning curve, training (captured in hidden.training_hours + hidden.productivity_dip_weeks)
3. Opportunity Cost - what they CAN'T do while implementing (opportunity_cost + opportunity_cost_description)
4. Complexity Cost - integration difficulty, maintenance burden (complexity_cost + complexity_cost_description)
5. Risk Cost - captured separately in the risk section
6. Brand/Trust Cost - customer-facing risk during transition (brand_trust_cost + brand_trust_cost_description)

For opportunity_cost, complexity_cost, brand_trust_cost: estimate in EUR. Use 0 if truly negligible.
Always provide a description explaining the cost even when the EUR value is 0.

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

    def _parse_cost_breakdown(self, cost_data: Dict[str, Any], default_hourly_rate: float = 50) -> Dict[str, Any]:
        """Parse CRB cost breakdown from LLM output, including 6C dimensions."""
        result = {}

        # Implementation DIY
        if cost_data.get("implementation_diy"):
            diy = cost_data["implementation_diy"]
            rate = diy.get("hourly_rate", default_hourly_rate)
            result["implementation_diy"] = {
                "hours": diy.get("hours", 0),
                "hourly_rate": rate,
                "total": diy.get("total", diy.get("hours", 0) * rate),
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

        # 6C additional cost dimensions (opportunity, complexity, brand/trust)
        result["opportunity_cost"] = cost_data.get("opportunity_cost", 0)
        result["opportunity_cost_description"] = cost_data.get("opportunity_cost_description", "")
        result["complexity_cost"] = cost_data.get("complexity_cost", 0)
        result["complexity_cost_description"] = cost_data.get("complexity_cost_description", "")
        result["brand_trust_cost"] = cost_data.get("brand_trust_cost", 0)
        result["brand_trust_cost_description"] = cost_data.get("brand_trust_cost_description", "")

        return result

    def _parse_replace_cost(self, cost_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse CRB cost for Replace path, including 6C dimensions."""
        return {
            "monthly": cost_data.get("monthly", 0),
            "setup_one_time": cost_data.get("setup_one_time", 0),
            "migration_estimate": cost_data.get("migration_estimate", 0),
            "opportunity_cost": cost_data.get("opportunity_cost", 0),
            "opportunity_cost_description": cost_data.get("opportunity_cost_description", ""),
            "complexity_cost": cost_data.get("complexity_cost", 0),
            "complexity_cost_description": cost_data.get("complexity_cost_description", ""),
            "brand_trust_cost": cost_data.get("brand_trust_cost", 0),
            "brand_trust_cost_description": cost_data.get("brand_trust_cost_description", ""),
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
        findings: List[Dict[str, Any]],
        default_hourly_rate: float = 50,
    ) -> List[Dict[str, Any]]:
        """Validate and normalize findings structure with deterministic calculations."""
        validated = []
        seen_ids = set()  # Track IDs for duplicate detection

        for i, finding in enumerate(findings):
            if not isinstance(finding, dict):
                continue

            # Create validated finding with defaults
            validated_finding = self.FINDING_TEMPLATE.copy()

            # Generate unique ID, handling duplicates
            finding_id = finding.get("id", f"finding-{i+1:03d}")
            if finding_id in seen_ids:
                logger.warning(f"Duplicate finding ID '{finding_id}', generating new ID")
                finding_id = f"finding-{i+1:03d}-{len(validated)+1}"
            seen_ids.add(finding_id)
            validated_finding["id"] = finding_id

            validated_finding["title"] = finding.get("title", "Untitled Finding")
            validated_finding["description"] = finding.get("description", "")

            # Validate category against allowed list
            category = finding.get("category", "operations")
            if category not in VALID_FINDING_CATEGORIES:
                logger.warning(f"Invalid category '{category}' for finding '{finding_id}', defaulting to 'operations'")
                category = "operations"
            validated_finding["category"] = category

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

            # Handle value_saved with DETERMINISTIC recalculation
            if isinstance(finding.get("value_saved"), dict):
                vs = finding["value_saved"]
                hours_per_week = vs.get("hours_per_week", 0) or 0
                # Use LLM-provided hourly_rate if present, otherwise use default from context
                hourly_rate = vs.get("hourly_rate") or default_hourly_rate
                # ALWAYS recalculate annual_savings deterministically
                # Formula: hours_per_week × hourly_rate × 52 weeks
                annual_savings = hours_per_week * hourly_rate * 52

                llm_annual = vs.get("annual_savings", 0) or 0
                if llm_annual > 0 and abs(llm_annual - annual_savings) > 1:
                    logger.info(
                        f"Recalculated annual_savings for '{validated_finding['id']}': "
                        f"LLM={llm_annual}, calculated={annual_savings} "
                        f"(hours={hours_per_week}, rate={hourly_rate})"
                    )

                validated_finding["value_saved"] = {
                    "hours_per_week": hours_per_week,
                    "hourly_rate": hourly_rate,
                    "annual_savings": annual_savings,
                }
            else:
                # Use default template but with context-aware hourly rate
                default_vs = self.FINDING_TEMPLATE["value_saved"].copy()
                default_vs["hourly_rate"] = default_hourly_rate
                validated_finding["value_saved"] = default_vs

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
                    validated_connect["cost"] = self._parse_cost_breakdown(cp["cost"], default_hourly_rate=default_hourly_rate)
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

            # Parse agent opportunity if present
            agent_opp = finding.get("agent_opportunity")
            if agent_opp and isinstance(agent_opp, dict):
                validated_finding["agent_opportunity"] = {
                    "agent_type": agent_opp.get("agent_type", ""),
                    "what_it_does": agent_opp.get("what_it_does", ""),
                    "estimated_impact": agent_opp.get("estimated_impact", {}),
                    "deployment_timeline": agent_opp.get("deployment_timeline", ""),
                    "prerequisites": agent_opp.get("prerequisites", []),
                }

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
