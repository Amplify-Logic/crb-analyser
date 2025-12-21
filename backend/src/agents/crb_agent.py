"""
CRB Agent - Core Analysis Engine

Orchestrates the Cost/Risk/Benefit analysis using Claude AI.
Processes intake responses through 5 phases to generate findings and recommendations.
"""

import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, Optional, List
from datetime import datetime

from anthropic import Anthropic

from src.config.settings import settings
from src.config.supabase_client import get_async_supabase
from src.config.model_routing import get_model_for_task, TokenTracker, MODELS
from src.config.system_prompt import get_full_system_prompt
from src.tools.tool_registry import TOOL_DEFINITIONS, execute_tool
from src.knowledge import get_industry_context, get_quick_wins, get_not_recommended
from src.expertise import get_expertise_store, get_self_improve_service

logger = logging.getLogger(__name__)


# Phase to model task mapping
PHASE_TASKS = {
    "discovery": "extract_pain_points",  # Fast extraction - use Haiku
    "research": "search_vendors",  # Fast search - use Haiku
    "analysis": "generate_findings",  # Main generation - use Sonnet
    "modeling": "generate_recommendations",  # Main generation - use Sonnet
    "report": "synthesize_report",  # Complex synthesis - use tier-based
}


class CRBAgent:
    """
    CRB Analysis Agent

    Processes business intake data through 5 phases:
    1. Discovery - Analyze intake, map processes
    2. Research - Find benchmarks, vendor solutions
    3. Analysis - Score potential, assess risks
    4. Modeling - Calculate ROI, build recommendations
    5. Report - Generate final report
    """

    PHASES = ["discovery", "research", "analysis", "modeling", "report"]

    # Use the centralized system prompt from config module
    SYSTEM_PROMPT = get_full_system_prompt()

    # Additional context for tool-based agent
    AGENT_CONTEXT = """
You have access to tools for each phase. Work methodically through discovery,
research, analysis, modeling, and report generation.

Remember: You are in STAGE 1 (ANALYSIS) until explicitly moved to STAGE 2 (RECOMMENDATION).
Complete analysis before making any recommendations.
"""

    def __init__(self, audit_id: str, tier: str = "quick"):
        self.audit_id = audit_id
        self.tier = tier  # "quick" or "full" - affects model selection
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.token_tracker = TokenTracker()  # Track token usage and costs
        self.current_phase = "discovery"
        self.progress = 0
        self.context: Dict[str, Any] = {}

        # Expertise system - self-improving agent
        self.expertise_store = get_expertise_store()
        self.tools_used: Dict[str, int] = {}  # Track tool usage for learning
        self.errors_encountered: List[str] = []  # Track errors for learning
        self.phases_completed: List[str] = []  # Track phase completion

    async def run_analysis(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run the full CRB analysis, yielding progress updates.

        Yields SSE-compatible progress updates.
        """
        supabase = await get_async_supabase()

        try:
            # Load audit and intake data
            yield {"phase": "init", "step": "Loading audit data...", "progress": 0}

            audit_result = await supabase.table("audits").select(
                "*, clients(name, industry, company_size, website)"
            ).eq("id", self.audit_id).single().execute()

            if not audit_result.data:
                raise ValueError(f"Audit not found: {self.audit_id}")

            audit = audit_result.data
            client = audit.pop("clients", {})

            # Load intake responses
            intake_result = await supabase.table("intake_responses").select("*").eq(
                "audit_id", self.audit_id
            ).single().execute()

            if not intake_result.data:
                raise ValueError("Intake responses not found")

            intake = intake_result.data

            # Build context
            industry = client.get("industry", "general")
            self.context = {
                "audit": audit,
                "client": client,
                "intake_responses": intake.get("responses", {}),
                "findings": [],
                "recommendations": [],
                "industry": industry,
                "company_size": client.get("company_size", "unknown"),
            }

            # Load industry-specific knowledge
            yield {"phase": "init", "step": "Loading industry knowledge...", "progress": 3}
            industry_knowledge = get_industry_context(industry)
            self.context["industry_knowledge"] = industry_knowledge
            self.context["quick_wins"] = get_quick_wins(industry)
            self.context["not_recommended"] = get_not_recommended(industry)

            if industry_knowledge.get("is_supported"):
                logger.info(f"Loaded knowledge for {industry}: {industry_knowledge.get('opportunity_count', 0)} opportunities")
            else:
                logger.warning(f"No specific knowledge for industry: {industry}")

            # Load agent expertise (self-improving mental model)
            yield {"phase": "init", "step": "Loading agent expertise...", "progress": 4}
            expertise = self.expertise_store.get_industry_expertise(industry)
            self.context["agent_expertise"] = expertise.model_dump()
            if expertise.total_analyses > 0:
                logger.info(
                    f"Loaded expertise for {industry}: {expertise.total_analyses} prior analyses, "
                    f"confidence: {expertise.confidence}"
                )

            yield {"phase": "init", "step": "Loaded audit data and industry knowledge", "progress": 5}

            # Run each phase
            phase_progress = {
                "discovery": (5, 25),
                "research": (25, 45),
                "analysis": (45, 70),
                "modeling": (70, 90),
                "report": (90, 100),
            }

            for phase in self.PHASES:
                self.current_phase = phase
                start_progress, end_progress = phase_progress[phase]

                yield {
                    "phase": phase,
                    "step": f"Starting {phase} phase...",
                    "progress": start_progress,
                }

                # Update audit status
                await supabase.table("audits").update({
                    "current_phase": phase,
                    "progress_percent": start_progress,
                }).eq("id", self.audit_id).execute()

                # Run phase
                async for update in self._run_phase(phase):
                    # Scale progress within phase range
                    if "progress" in update:
                        phase_progress_pct = update["progress"] / 100
                        scaled_progress = int(
                            start_progress + (end_progress - start_progress) * phase_progress_pct
                        )
                        update["progress"] = scaled_progress
                    yield update

                # Track phase completion for learning
                self.phases_completed.append(phase)

                yield {
                    "phase": phase,
                    "step": f"Completed {phase} phase",
                    "progress": end_progress,
                }

            # Finalize
            yield {"phase": "finalizing", "step": "Saving results...", "progress": 98}

            # Calculate final metrics
            total_savings = sum(
                f.get("estimated_cost_saved", 0) for f in self.context["findings"]
            )
            ai_readiness_score = self._calculate_ai_readiness_score()

            # Update audit with final results
            await supabase.table("audits").update({
                "status": "completed",
                "current_phase": "complete",
                "progress_percent": 100,
                "completed_at": datetime.utcnow().isoformat(),
                "ai_readiness_score": ai_readiness_score,
                "total_findings": len(self.context["findings"]),
                "total_potential_savings": total_savings,
            }).eq("id", self.audit_id).execute()

            # Get token usage summary
            token_summary = self.token_tracker.get_summary()
            logger.info(
                f"Analysis complete. Token usage: {token_summary['total_tokens']} "
                f"(estimated cost: ${token_summary['estimated_cost_usd']:.4f})"
            )

            # Self-improve: Learn from this analysis
            yield {"phase": "learning", "step": "Updating agent expertise...", "progress": 99}
            try:
                self_improve_service = get_self_improve_service()
                learning_result = await self_improve_service.learn_from_analysis(
                    audit_id=self.audit_id,
                    industry=industry,
                    company_size=self.context.get("company_size", "unknown"),
                    context={
                        "findings": self.context.get("findings", []),
                        "recommendations": self.context.get("recommendations", []),
                        "ai_readiness_score": ai_readiness_score,
                        "total_potential_savings": total_savings,
                    },
                    execution_metrics={
                        "tools_used": self.tools_used,
                        "token_usage": token_summary,
                        "phases_completed": self.phases_completed,
                        "errors": self.errors_encountered,
                    },
                )
                logger.info(f"Self-improvement complete: {learning_result.get('learned', {})}")
            except Exception as e:
                # Self-improvement is non-critical - don't fail the analysis
                logger.warning(f"Self-improvement failed (non-critical): {e}")

            yield {
                "phase": "complete",
                "step": "Analysis complete!",
                "progress": 100,
                "result": {
                    "ai_readiness_score": ai_readiness_score,
                    "total_findings": len(self.context["findings"]),
                    "total_potential_savings": total_savings,
                    "token_usage": token_summary,
                },
            }

        except Exception as e:
            logger.error(f"CRB Agent error: {e}")

            # Mark audit as failed
            await supabase.table("audits").update({
                "status": "failed",
                "last_error": str(e),
            }).eq("id", self.audit_id).execute()

            yield {
                "phase": "error",
                "step": f"Analysis failed: {str(e)}",
                "progress": self.progress,
                "error": str(e),
            }

    async def _run_phase(self, phase: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Run a specific analysis phase."""

        phase_prompts = {
            "discovery": self._get_discovery_prompt(),
            "research": self._get_research_prompt(),
            "analysis": self._get_analysis_prompt(),
            "modeling": self._get_modeling_prompt(),
            "report": self._get_report_prompt(),
        }

        prompt = phase_prompts[phase]

        # Get relevant tools for this phase
        phase_tools = self._get_phase_tools(phase)

        messages = [{"role": "user", "content": prompt}]

        iteration = 0
        max_iterations = 10

        while iteration < max_iterations:
            iteration += 1

            yield {
                "phase": phase,
                "step": f"Analyzing ({iteration})...",
                "progress": (iteration / max_iterations) * 100,
            }

            try:
                # Get appropriate model for this phase and tier
                task = PHASE_TASKS.get(phase, "generate_findings")
                model = get_model_for_task(task, self.tier)

                response = self.client.messages.create(
                    model=model,
                    max_tokens=4096,
                    system=self.SYSTEM_PROMPT,
                    tools=phase_tools,
                    messages=messages,
                )

                # Track token usage
                self.token_tracker.add_usage(
                    task=f"{phase}_{iteration}",
                    model=model,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                )

                # Process response
                assistant_content = []
                tool_calls = []

                for block in response.content:
                    if block.type == "text":
                        assistant_content.append({"type": "text", "text": block.text})
                    elif block.type == "tool_use":
                        tool_calls.append(block)
                        assistant_content.append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        })

                messages.append({"role": "assistant", "content": assistant_content})

                # If no tool calls, phase is complete
                if not tool_calls:
                    break

                # Execute tool calls
                tool_results = []
                for tool_call in tool_calls:
                    yield {
                        "phase": phase,
                        "step": f"Using tool: {tool_call.name}",
                        "tool": tool_call.name,
                        "progress": (iteration / max_iterations) * 100,
                    }

                    # Track tool usage for learning
                    self.tools_used[tool_call.name] = self.tools_used.get(tool_call.name, 0) + 1

                    result = await execute_tool(
                        tool_call.name,
                        tool_call.input,
                        self.context,
                        self.audit_id,
                    )

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": json.dumps(result),
                    })

                messages.append({"role": "user", "content": tool_results})

                # Check if we should stop
                if response.stop_reason == "end_turn":
                    break

            except Exception as e:
                logger.error(f"Phase {phase} error: {e}")
                # Track errors for learning
                self.errors_encountered.append(f"{phase}: {str(e)}")
                yield {
                    "phase": phase,
                    "step": f"Error: {str(e)}",
                    "progress": (iteration / max_iterations) * 100,
                }
                break

    def _get_phase_tools(self, phase: str) -> List[Dict]:
        """Get tool definitions for a specific phase."""
        phase_tool_names = {
            "discovery": [
                "analyze_intake_responses",
                "map_business_processes",
                "identify_tech_stack",
            ],
            "research": [
                "search_industry_benchmarks",
                "search_vendor_solutions",
                "validate_source",
            ],
            "analysis": [
                "score_automation_potential",
                "calculate_finding_impact",
                "identify_ai_opportunities",
                "assess_implementation_risk",
            ],
            "modeling": [
                "calculate_roi",
                "compare_vendors",
                "generate_timeline",
            ],
            "report": [
                "create_finding",
                "create_recommendation",
                "generate_executive_summary",
            ],
        }

        tool_names = phase_tool_names.get(phase, [])
        return [t for t in TOOL_DEFINITIONS if t["name"] in tool_names]

    def _get_discovery_prompt(self) -> str:
        """Generate discovery phase prompt."""
        intake = json.dumps(self.context["intake_responses"], indent=2)
        client = self.context["client"]
        industry_knowledge = self.context.get("industry_knowledge", {})
        quick_wins = self.context.get("quick_wins", [])
        not_recommended = self.context.get("not_recommended", [])
        agent_expertise = self.context.get("agent_expertise", {})

        # Build industry context section
        industry_context = ""
        if industry_knowledge.get("is_supported"):
            processes = industry_knowledge.get("processes", {})
            if processes:
                common_processes = processes.get("common_processes", [])
                industry_context = f"""
INDUSTRY KNOWLEDGE LOADED: {self.context['industry']}
We have specific data for this industry including:
- {len(common_processes)} common processes mapped
- {industry_knowledge.get('opportunity_count', 0)} AI opportunities identified
- Industry benchmarks available

Common high-pain processes in this industry:
{json.dumps([p['name'] + ' (automation potential: ' + str(p.get('automation_potential', '?')) + '%)' for p in common_processes[:5]], indent=2)}
"""
            if quick_wins:
                industry_context += f"""
QUICK WINS for this industry:
{json.dumps([{'name': qw['name'], 'impact': qw['impact']} for qw in quick_wins], indent=2)}
"""
            if not_recommended:
                industry_context += f"""
THINGS NOT RECOMMENDED for this industry (be willing to say no):
{json.dumps(not_recommended, indent=2)}
"""

        # Build expertise context (learned from previous analyses)
        expertise_context = ""
        if agent_expertise.get("total_analyses", 0) > 0:
            expertise_context = f"""
═══════════════════════════════════════════════════════════════════════════════
AGENT EXPERTISE (learned from {agent_expertise['total_analyses']} prior analyses)
Confidence level: {agent_expertise.get('confidence', 'low')}
═══════════════════════════════════════════════════════════════════════════════
"""
            # Top pain points we've seen in this industry
            pain_points = agent_expertise.get("pain_points", {})
            if pain_points:
                top_pains = sorted(
                    [(k, v.get("frequency", 0)) for k, v in pain_points.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
                if top_pains:
                    expertise_context += f"""
COMMON PAIN POINTS in {self.context['industry']} (from prior analyses):
{json.dumps([{'pain_point': p[0], 'seen_in': f'{p[1]} analyses'} for p in top_pains], indent=2)}
"""

            # Company size specific insights
            size_data = agent_expertise.get("size_specific", {}).get(client.get("company_size", ""), {})
            if size_data:
                expertise_context += f"""
INSIGHTS for {client.get('company_size', '')} companies in this industry:
- Analyzed: {size_data.get('count', 0)} similar companies
- Average AI readiness: {size_data.get('avg_readiness', 50):.0f}
- Common pain points: {', '.join(size_data.get('common_pain_points', [])[:3])}
"""

            # Effective patterns we've learned
            patterns = agent_expertise.get("effective_patterns", [])
            if patterns:
                top_patterns = sorted(patterns, key=lambda p: p.get("frequency", 0), reverse=True)[:3]
                expertise_context += f"""
EFFECTIVE RECOMMENDATIONS we've made for similar companies:
{json.dumps([{'pattern': p.get('pattern', ''), 'recommendation': p.get('recommendation', '')} for p in top_patterns], indent=2)}
"""

        return f"""Phase 1: Discovery

Analyze the following intake responses from {client.get('name', 'the client')}, a {client.get('company_size', '')} company in the {client.get('industry', '')} industry.
{industry_context}{expertise_context}
INTAKE RESPONSES:
{intake}

Your tasks:
1. Use analyze_intake_responses to extract key pain points and opportunities
2. Use map_business_processes to identify the main workflows
3. Use identify_tech_stack to understand their current tools

Focus on understanding:
- What repetitive tasks are consuming the most time?
- Where are the biggest bottlenecks?
- What tools are they using and how well integrated are they?
- What is their AI readiness level?
- Are there any RED FLAGS that suggest they're NOT ready for AI?

IMPORTANT - Be honest:
- If fundamentals aren't in place, note that
- If their team is too small for certain solutions, flag it
- Reference industry benchmarks when available

Provide a structured analysis of the business."""

    def _get_research_prompt(self) -> str:
        """Generate research phase prompt."""
        client = self.context["client"]
        industry_knowledge = self.context.get("industry_knowledge", {})

        # Build benchmarks and vendor context
        benchmarks_context = ""
        if industry_knowledge.get("benchmarks"):
            benchmarks = industry_knowledge["benchmarks"].get("benchmarks", {})
            if benchmarks:
                benchmarks_context = f"""
INDUSTRY BENCHMARKS AVAILABLE:
{json.dumps(benchmarks, indent=2, default=str)[:2000]}...
"""

        vendors_context = ""
        if industry_knowledge.get("vendors"):
            vendors = industry_knowledge["vendors"]
            categories = vendors.get("vendor_categories", [])
            vendors_context = f"""
VENDOR RECOMMENDATIONS FOR THIS INDUSTRY:
{len(categories)} vendor categories available with detailed pricing
Categories: {', '.join([c.get('name', '') for c in categories])}
"""

        return f"""Phase 2: Research

Based on the discovery analysis, research relevant benchmarks and solutions for {client.get('industry', 'this')} industry.
{benchmarks_context}
{vendors_context}
Your tasks:
1. Use search_industry_benchmarks to find relevant metrics for comparison
2. Use search_vendor_solutions to identify tools that could address their pain points
3. Validate any claims with validate_source

Focus on:
- Industry-specific automation benchmarks (we have data loaded)
- Tools appropriate for their company size ({client.get('company_size', 'unknown')})
- Solutions within typical budget ranges for their segment
- ALWAYS include a custom/build option alongside vendors

IMPARTIALITY CHECK:
- Don't default to most expensive option
- If a free tier works for their scale, recommend it
- Note any vendor lock-in risks
- Be skeptical of vendor ROI claims (apply 30% discount)

Be specific with vendor names, pricing, and capabilities."""

    def _get_analysis_prompt(self) -> str:
        """Generate analysis phase prompt."""
        return """Phase 3: Analysis

Now analyze the opportunities and risks based on discovery and research.

Your tasks:
1. Use score_automation_potential on each identified process
2. Use calculate_finding_impact to estimate both VALUE SAVED and VALUE CREATED
3. Use identify_ai_opportunities to find AI use cases
4. Use assess_implementation_risk for each opportunity

For each finding, evaluate:

TWO PILLARS:
- Customer Value Score (0-10): How does this improve THEIR customers' experience?
- Business Health Score (0-10): How does this help the business sustainably?

TWO VALUE TYPES:
- Value SAVED: Time × hourly rate = € saved (efficiency)
- Value CREATED: Revenue increase, new capabilities (growth)

THREE TIME HORIZONS:
- Short term (0-6 months): Quick wins, immediate impact
- Mid term (6-18 months): Foundation building
- Long term (18+ months): Strategic transformation

RISKS by timeline:
- Short: Integration, adoption resistance
- Mid: Scaling challenges, vendor dependencies
- Long: Technology obsolescence, market changes

Only advance findings that score 6+ on BOTH Customer Value AND Business Health."""

    def _get_modeling_prompt(self) -> str:
        """Generate modeling phase prompt."""
        return """Phase 4: Modeling

Build ROI models with THREE OPTIONS for each opportunity.

Your tasks:
1. Use calculate_roi for each major recommendation
2. Use compare_vendors to build the three options
3. Use generate_timeline to create implementation roadmaps

FOR EACH RECOMMENDATION, PROVIDE THREE OPTIONS:

Option A: OFF-THE-SHELF
- Fastest, lowest risk, plug and play
- Name specific tool, pricing, implementation time
- Pros and cons

Option B: BEST-IN-CLASS
- Premium vendor, full implementation
- Name specific tool, pricing, implementation time
- Pros and cons

Option C: CUSTOM AI SOLUTION
- Built specifically for their needs
- Estimated cost range, timeline
- Why this could be a competitive advantage

CALCULATIONS REQUIRED:
- Cost breakdown: Short/Mid/Long term
- Risk matrix: Probability × Impact for each risk
- Benefit breakdown:
  * Value SAVED (efficiency): Show formula
  * Value CREATED (growth): Describe opportunity
- Total ROI with payback period
- All assumptions listed

ALWAYS show ranges (min-max), never single numbers."""

    def _get_report_prompt(self) -> str:
        """Generate report phase prompt."""
        return """Phase 5: Report Generation

Create the final findings and recommendations following our framework.

Your tasks:
1. Use create_finding for each significant insight (aim for 15-20 findings)
2. Use create_recommendation for actionable items
3. Use generate_executive_summary for the report overview

REPORT STRUCTURE:

1. EXECUTIVE SUMMARY
   - AI Readiness Score (0-100)
   - Customer Value Score (0-10)
   - Business Health Score (0-10)
   - Total Value Potential (range, 3-year)
   - Top 3 Opportunities (headlines)

2. VALUE SUMMARY
   - Total Value SAVED (efficiency gains)
   - Total Value CREATED (growth opportunities)
   - Combined potential (range)

3. FINDINGS (prioritized by combined impact)
   Each finding must include:
   - What we discovered
   - Customer Value impact
   - Business Health impact
   - Confidence level + source

4. RECOMMENDATIONS
   Each recommendation must include:
   - The opportunity
   - CRB analysis (Cost/Risk/Benefit by timeline)
   - THREE OPTIONS (Off-shelf / Best-in-class / Custom)
   - Our recommendation and why
   - ROI calculation with assumptions

5. IMPLEMENTATION ROADMAP
   - Phase 1: Quick Wins (0-3 months)
   - Phase 2: Foundation (3-12 months)
   - Phase 3: Transformation (12-24 months)

QUALITY CHECKS:
✓ Every claim has a source
✓ All numbers show ranges (min-max)
✓ Assumptions are listed
✓ Customer Value AND Business Health both score 6+
✓ Three options provided for each recommendation"""

    def _calculate_ai_readiness_score(self) -> int:
        """Calculate the AI readiness score based on findings."""
        intake = self.context.get("intake_responses", {})

        score = 50  # Base score

        # Technology comfort
        tech_comfort = intake.get("technology_comfort", 5)
        if isinstance(tech_comfort, int):
            score += (tech_comfort - 5) * 3  # +/- 15 points

        # Existing AI usage
        ai_tools = intake.get("ai_tools_used", [])
        if isinstance(ai_tools, list) and "none" not in ai_tools:
            score += len(ai_tools) * 3  # Up to +15 points

        # Tool integration
        integration = intake.get("integration_issues", 5)
        if isinstance(integration, int):
            score += (integration - 5) * 2  # +/- 10 points

        # Budget readiness
        budget = intake.get("budget_for_solutions", "")
        budget_scores = {
            "under_100": -5,
            "100_500": 0,
            "500_1000": 5,
            "1000_5000": 10,
            "5000_plus": 15,
        }
        score += budget_scores.get(budget, 0)

        # Clamp score
        return max(0, min(100, score))


async def start_analysis(audit_id: str) -> AsyncGenerator[str, None]:
    """
    Start CRB analysis for an audit.

    Yields SSE-formatted events.
    """
    agent = CRBAgent(audit_id)

    async for update in agent.run_analysis():
        yield f"data: {json.dumps(update)}\n\n"
