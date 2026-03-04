# backend/src/services/playbook_generator.py
"""
Playbook Generation Service

Generates personalized implementation playbooks from recommendations.
Uses canonical models from src/models/playbook.py with full validation.
"""
import json
import structlog
import re
import uuid
from typing import Dict, Any, List, Optional

from anthropic import Anthropic

from src.config.settings import settings
from src.config.model_routing import get_model_for_task
from src.models.playbook import (
    Playbook,
    Phase,
    Week,
    PlaybookTask,
    TaskCRB,
    PhaseCRBSummary,
    PersonalizationContext,
    ImmediateFirstStep,
    PlaybookValidationResult,
    validate_playbook_data,
    MIN_TASK_MINUTES,
    MAX_TASK_MINUTES,
)
from src.skills import get_skill, SkillContext
from src.expertise import get_expertise_store

logger = structlog.get_logger(__name__)


# =============================================================================
# PLAYBOOK GENERATOR
# =============================================================================

class PlaybookGenerator:
    """Generate personalized playbooks from recommendations."""

    SYSTEM_PROMPT = """You are an expert AIOS (AI Operating System) implementation consultant creating actionable playbooks.

Your playbooks follow the AIOS implementation timeline:
- Phase 1: CONNECT — Wire existing tools together with API integrations and Claude workflows
- Phase 2: AUTOMATE — Deploy AI workflows on connected data (Claude agents, MCP servers)
- Phase 3: ENHANCE — Build intelligence layers (dashboards, monitoring, predictive agents)
- Phase 4: COMMAND STATION — Unified oversight and human-in-the-loop controls
- Phase 5 (only if needed): TARGETED UPGRADES — Replace specific dead-end tools

Your playbooks must be:
1. SPECIFIC - Exact tool names, exact steps, no vague instructions
2. FAST-PACED - Things can move fast with modern tools. Compress timelines.
3. CONNECT-FIRST - Always start by wiring existing tools before suggesting replacements
4. PERSONALIZED - Adapt to team size, tech level, existing tools
5. CRB-FOCUSED - Every task shows Cost, Risk, Benefit with real EUR amounts
6. DEPENDENCY-AWARE - Tasks reference prerequisites by ID

MANDATORY RULES:
- NEVER use "TBD" for cost or benefit fields. Always provide a concrete EUR estimate.
- Cost fields MUST show EUR amounts (e.g., "€0 (free tier)", "€50 setup", "€29/mo").
- Benefit fields MUST describe concrete value (e.g., "Saves 2 hrs/week (€160/mo)", "Foundation for later automation").
- Risk MUST correlate with task difficulty: easy tasks→"low", medium tasks→"medium", hard/integration/migration tasks→"high".
- Executor MUST match team size: solo teams→"owner" for everything, small/medium/large teams→"team" for medium/hard tasks.
- Time estimates MUST vary by task type: sign-up=15-30min, configure=30-60min, integration=120-240min, migration=240-480min.
- Phase crb_summary.total_cost MUST be non-zero when phases include paid tools.
- Include Claude Code build hours and MCP servers where applicable.

CRITICAL: Your playbook must ONLY reference concepts, tools, and workflows that apply to the client's stated industry. A dental practice playbook should NEVER mention field technicians, dispatch routing, or service zones. A plumbing company playbook should NEVER mention patient records or clinical notes. Match your language and examples to the industry.

Generate aggressive but achievable week-by-week plans with proper task dependencies."""

    def __init__(self, client: Optional[Any] = None):
        self.client = client if client is not None else Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def _extract_personalization_context(
        self, quiz_answers: Dict[str, Any]
    ) -> PersonalizationContext:
        """Extract personalization context from quiz answers."""
        # Team size mapping
        team_size_raw = quiz_answers.get("team_size", "1")
        if isinstance(team_size_raw, str):
            if "1" in team_size_raw or "solo" in team_size_raw.lower():
                team_size = "solo"
            elif any(x in team_size_raw for x in ["2", "3", "4", "5"]):
                team_size = "small"
            elif any(x in team_size_raw for x in ["6", "10", "15", "20"]):
                team_size = "medium"
            else:
                team_size = "large"
        else:
            team_size = "solo"

        # Technical level
        tech_comfort = quiz_answers.get("technical_comfort", 3)
        if isinstance(tech_comfort, str):
            tech_comfort = int(tech_comfort) if tech_comfort.isdigit() else 3

        # Existing tools
        existing_tools = quiz_answers.get("current_tools", [])
        if isinstance(existing_tools, str):
            existing_tools = [t.strip() for t in existing_tools.split(",")]

        # Budget
        budget = quiz_answers.get("monthly_budget", 500)
        if isinstance(budget, str):
            # Extract number from strings like "€500" or "500-1000"
            numbers = re.findall(r'\d+', budget)
            budget = int(numbers[0]) if numbers else 500

        # Urgency
        urgency_raw = quiz_answers.get("timeline_urgency", "normal")
        if "asap" in str(urgency_raw).lower() or "urgent" in str(urgency_raw).lower():
            urgency = "asap"
        elif "flexible" in str(urgency_raw).lower():
            urgency = "flexible"
        else:
            urgency = "normal"

        return PersonalizationContext(
            team_size=team_size,
            technical_level=tech_comfort,
            budget_monthly=budget,
            existing_tools=existing_tools,
            primary_pain_point=quiz_answers.get("biggest_challenge", ""),
            industry=quiz_answers.get("industry", "professional-services"),
            urgency=urgency,
        )

    def _extract_cost_context(
        self,
        recommendation: Dict[str, Any],
        option_type: str,
        context: PersonalizationContext,
    ) -> Dict[str, Any]:
        """Extract financial context from recommendation data for both code paths.

        Returns a dict with all optional fields (None if missing):
        - total_implementation_cost, monthly_ongoing_cost, first_year_total
        - annual_benefit, roi_percentage, payback_months
        - time_savings_hours_per_week, risks, team_size
        """
        option = recommendation.get("options", {}).get(option_type, {})
        crb = recommendation.get("crb_analysis", {})

        # --- Setup / implementation cost ---
        setup_cost: Optional[float] = None
        cost_data = crb.get("cost", {})
        short_term = cost_data.get("short_term", {})
        if short_term.get("setup") is not None:
            setup_cost = float(short_term["setup"])
        elif option_type in ("custom_solution", "connect_and_automate", "enhance_with_ai"):
            est = option.get("estimated_cost", {})
            if isinstance(est, dict):
                # Use midpoint of min/max
                lo = est.get("min", 0)
                hi = est.get("max", lo)
                setup_cost = (lo + hi) / 2.0
            elif est:
                try:
                    setup_cost = float(est)
                except (ValueError, TypeError):
                    pass

        # --- Monthly ongoing cost ---
        monthly_cost: Optional[float] = None
        if option.get("monthly_cost") is not None:
            raw_cost = option["monthly_cost"]
            if isinstance(raw_cost, str):
                import re as _re
                nums = _re.findall(r'\d+\.?\d*', raw_cost)
                monthly_cost = sum(float(n) for n in nums) / max(len(nums), 1) if nums else None
            else:
                monthly_cost = float(raw_cost)
        elif short_term.get("monthly") is not None:
            monthly_cost = float(short_term["monthly"])

        # --- First year total ---
        first_year_total: Optional[float] = None
        if setup_cost is not None and monthly_cost is not None:
            first_year_total = setup_cost + 12 * monthly_cost
        elif setup_cost is not None:
            first_year_total = setup_cost

        # --- Annual benefit ---
        annual_benefit: Optional[float] = None
        benefit_data = crb.get("benefit", {})
        short_benefit = benefit_data.get("short_term", {})
        if short_benefit.get("annual") is not None:
            annual_benefit = float(short_benefit["annual"])
        elif benefit_data.get("total") is not None:
            # Approximate annual from 3-year total
            annual_benefit = float(benefit_data["total"]) / 3.0

        # --- ROI and payback ---
        roi_pct = recommendation.get("roi_percentage")
        payback = recommendation.get("payback_months")

        # --- Time savings ---
        roi_detail = recommendation.get("roi_detail", {})
        time_savings = roi_detail.get("time_savings", {})
        hours_per_week = time_savings.get("hours_per_week")

        # --- Risks ---
        risks_raw = crb.get("risk", [])
        risks: List[Dict[str, Any]] = []
        if isinstance(risks_raw, list):
            for r in risks_raw:
                if isinstance(r, dict):
                    risks.append({
                        "description": r.get("description", ""),
                        "probability": r.get("probability", "medium"),
                        "impact": r.get("impact", 3),
                    })

        return {
            "total_implementation_cost": setup_cost,
            "monthly_ongoing_cost": monthly_cost,
            "first_year_total": first_year_total,
            "annual_benefit": annual_benefit,
            "roi_percentage": roi_pct,
            "payback_months": payback,
            "time_savings_hours_per_week": hours_per_week,
            "risks": risks,
            "team_size": context.team_size,
        }

    def _get_week_count(self, urgency: str, option_type: str) -> int:
        """Get total weeks based on urgency and option type."""
        base_weeks = {
            # AIOS option types
            "connect_and_automate": 4,
            "enhance_with_ai": 8,
            "targeted_upgrade": 10,
            # Legacy option types (backward compat)
            "off_the_shelf": 6,
            "best_in_class": 10,
            "custom_solution": 12,
        }
        base = base_weeks.get(option_type, 8)

        if urgency == "asap":
            return max(4, int(base * 0.7))
        elif urgency == "flexible":
            return int(base * 1.3)
        return base

    def _build_generation_prompt(
        self,
        recommendation: Dict[str, Any],
        option_type: str,
        option: Dict[str, Any],
        context: PersonalizationContext,
        total_weeks: int,
        cost_context: Optional[Dict[str, Any]] = None,
        quiz_answers: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build the LLM prompt for playbook generation."""
        executor_guidance = {
            "solo": "all tasks go to 'owner' since this is a solo operation",
            "small": "most tasks go to 'owner', assign 'team' for medium/hard tasks that benefit from collaboration",
            "medium": "'owner' for strategic/easy tasks, 'team' for medium/hard implementation tasks",
            "large": "'owner' for oversight/approval, 'team' for most implementation, 'hire_out' for specialized hard tasks",
        }.get(context.team_size, "distribute between 'owner' and 'team' based on skill requirements")

        detail_level = (
            "detailed hand-holding with step-by-step instructions"
            if context.technical_level <= 2
            else "link to docs, skip basics - user is technically proficient"
            if context.technical_level >= 4
            else "moderate detail - explain key concepts but don't over-explain"
        )

        # Build financial context section from extracted data
        financial_section = ""
        if cost_context:
            lines = ["FINANCIAL CONTEXT (use these numbers, do NOT use TBD):"]
            if cost_context.get("total_implementation_cost") is not None:
                lines.append(f"- Total implementation cost: €{cost_context['total_implementation_cost']:,.0f}")
            if cost_context.get("monthly_ongoing_cost") is not None:
                lines.append(f"- Monthly ongoing cost: €{cost_context['monthly_ongoing_cost']:,.0f}/mo")
            if cost_context.get("first_year_total") is not None:
                lines.append(f"- First year total: €{cost_context['first_year_total']:,.0f}")
            if cost_context.get("annual_benefit") is not None:
                lines.append(f"- Annual benefit: €{cost_context['annual_benefit']:,.0f}")
            if cost_context.get("roi_percentage") is not None:
                lines.append(f"- ROI: {cost_context['roi_percentage']}%")
            if cost_context.get("payback_months") is not None:
                lines.append(f"- Payback period: {cost_context['payback_months']} months")
            if cost_context.get("time_savings_hours_per_week") is not None:
                lines.append(f"- Time savings: {cost_context['time_savings_hours_per_week']} hrs/week")
            if cost_context.get("risks"):
                risk_strs = [f"{r['description']} ({r['probability']})" for r in cost_context["risks"][:3]]
                lines.append(f"- Key risks: {'; '.join(risk_strs)}")
            financial_section = "\n".join(lines)

        # Determine compliance framework from country/location
        _qa = quiz_answers or {}
        country_str = str(_qa.get("country", "") or _qa.get("locations", "") or "").upper()
        eu_indicators = ("NL", "DE", "FR", "BE", "AT", "IT", "ES", "EU",
                         "NETHERLANDS", "AMSTERDAM", "GERMANY", "FRANCE",
                         "BELGIUM", "DUTCH", "VIENNA", "BERLIN", "PARIS")
        is_eu = any(ind in country_str for ind in eu_indicators)
        is_healthcare = context.industry.lower() in ("dental", "medical", "healthcare")
        if is_eu:
            compliance = "GDPR"
        elif is_healthcare:
            compliance = "HIPAA"
        else:
            compliance = "general"
        wrong_compliance = "HIPAA" if compliance == "GDPR" else "GDPR"

        team_executor = (
            "owner does everything" if context.team_size == "solo"
            else "assign to relevant team members"
        )
        industry_rules = f"""
CRITICAL INDUSTRY RULES:
- Industry: {context.industry}. Generate content ONLY relevant to {context.industry} practices.
- Compliance: Use {compliance} (NOT {wrong_compliance}).
- NEVER reference field technicians, service zones, dispatch, or routing unless the industry is field services (HVAC, plumbing, electrical).
- NEVER reference clinical diagnostics, imaging, or treatment planning unless the recommendation specifically addresses those areas.
- All role references must match {context.team_size} team: {team_executor}."""

        return f"""Generate a detailed implementation playbook.

RECOMMENDATION: {recommendation.get('title')}
OPTION: {option_type.replace('_', ' ').title()}
OPTION DETAILS: {json.dumps(option, indent=2)}

{financial_section}

PERSONALIZATION:
- Team size: {context.team_size}
- Technical level: {context.technical_level}/5
- Budget: €{context.budget_monthly}/month
- Existing tools: {', '.join(context.existing_tools) or 'None specified'}
- Industry: {context.industry}
- Urgency: {context.urgency}
- Primary pain: {context.primary_pain_point}
{industry_rules}

TOTAL WEEKS: {total_weeks}

Generate a JSON playbook with this EXACT structure:
{{
    "phases": [
        {{
            "phase_number": 1,
            "title": "Setup & Quick Wins",
            "duration_weeks": 2,
            "outcome": "Basic system running, first automation live",
            "crb_summary": {{
                "total_cost": "€200",
                "monthly_cost": "€50/mo",
                "setup_hours": 8,
                "risks": ["Learning curve"],
                "benefits": ["2 hrs/week saved immediately"],
                "crb_score": 8.5
            }},
            "weeks": [
                {{
                    "week_number": 1,
                    "theme": "Foundation",
                    "tasks": [
                        {{
                            "id": "p1-w1-t1",
                            "title": "Sign up for [specific tool]",
                            "description": "Create account and complete onboarding",
                            "time_estimate_minutes": 20,
                            "difficulty": "easy",
                            "executor": "owner",
                            "tools": ["tool-name"],
                            "tutorial_hint": "Use code SAVE20 for discount",
                            "dependencies": [],
                            "crb": {{
                                "cost": "€0 (free trial)",
                                "risk": "low",
                                "benefit": "Access to platform"
                            }}
                        }},
                        {{
                            "id": "p1-w1-t2",
                            "title": "Configure basic settings",
                            "description": "Set up essential configurations",
                            "time_estimate_minutes": 45,
                            "difficulty": "easy",
                            "executor": "owner",
                            "tools": ["tool-name"],
                            "dependencies": ["p1-w1-t1"],
                            "crb": {{
                                "cost": "€50 (pro plan setup)",
                                "risk": "low",
                                "benefit": "System ready for use"
                            }}
                        }}
                    ],
                    "checkpoint": "Account created and configured"
                }}
            ]
        }}
    ]
}}

ESTIMATION RULES (follow strictly):
- Time: "Sign up/create account" = 15-30min, "Configure/set up" = 30-60min, "Integrate/connect" = 120-240min, "Migrate data" = 240-480min
- Cost: Distribute the total implementation cost proportionally across tasks weighted by difficulty. NEVER use "TBD".
- Benefit: Early phases = "Foundation for €X/yr savings", later phases = proportional share of annual benefit. NEVER use "TBD".
- Risk: easy tasks → "low", medium tasks → "medium", hard/integration/migration tasks → "high"
- Executor for {context.team_size} team: {executor_guidance}
- Phase total_cost: Sum of task costs in that phase. Must be > €0 if any paid tools are involved.

REQUIREMENTS:
1. 3-5 phases total, covering all {total_weeks} weeks
2. 3-6 tasks per week
3. Tasks are {MIN_TASK_MINUTES}-{MAX_TASK_MINUTES} minutes each (most should be 15-120 min)
4. Executor: {executor_guidance}
5. Skip setup for tools they already have: {context.existing_tools}
6. Technical level {context.technical_level}/5 means {detail_level}
7. Every task MUST have a CRB breakdown with real EUR amounts
8. IMPORTANT: Task IDs follow pattern "p{{phase}}-w{{week}}-t{{task}}" (e.g., p1-w1-t1, p1-w1-t2, p1-w2-t1)
9. Dependencies MUST reference existing task IDs from earlier in the playbook
10. First task of first week has no dependencies (empty array)
11. Later tasks should reference their prerequisites

DEPENDENCY RULES:
- Only reference task IDs that appear BEFORE the current task
- Use dependencies to show logical order (e.g., "configure" depends on "sign up")
- Cross-week dependencies are allowed (task in week 2 can depend on task in week 1)
- Cross-phase dependencies are allowed but should be minimal

Return ONLY valid JSON, no explanation."""

    def _sanitize_task_data(
        self,
        task_data: Dict[str, Any],
        phase_num: int,
        week_num: int,
        task_num: int,
        cost_context: Optional[Dict[str, Any]] = None,
        total_tasks: int = 1,
    ) -> Dict[str, Any]:
        """Sanitize and normalize task data from LLM response.

        Uses cost_context to derive smart fallbacks instead of static defaults.
        """
        # Ensure valid ID
        task_id = task_data.get("id") or f"p{phase_num}-w{week_num}-t{task_num}"

        # Ensure valid difficulty (needed before time/cost defaults)
        difficulty = task_data.get("difficulty", "medium")
        if difficulty not in ("easy", "medium", "hard"):
            difficulty = "medium"

        # Difficulty-based default time estimates instead of flat 30
        default_minutes = {"easy": 20, "medium": 60, "hard": 180}
        time_est = task_data.get("time_estimate_minutes")
        if time_est is None or time_est == 60:
            # 60 is the old hardcoded default — treat as missing
            time_est = default_minutes[difficulty]
        if not isinstance(time_est, int):
            try:
                time_est = int(time_est)
            except (ValueError, TypeError):
                time_est = default_minutes[difficulty]
        time_est = max(MIN_TASK_MINUTES, min(MAX_TASK_MINUTES, time_est))

        # Ensure valid executor — team-size aware
        executor = task_data.get("executor", "")
        team_size = (cost_context or {}).get("team_size", "solo")
        if executor not in ("owner", "team", "hire_out"):
            # Smart default based on team size and difficulty
            if team_size == "solo":
                executor = "owner"
            elif difficulty == "easy":
                executor = "owner"
            else:
                executor = "team"

        # Ensure dependencies is a list
        dependencies = task_data.get("dependencies", [])
        if not isinstance(dependencies, list):
            dependencies = []
        dependencies = [d for d in dependencies if isinstance(d, str) and d]

        # Build CRB with smart fallbacks
        crb_data = task_data.get("crb", {})
        if not isinstance(crb_data, dict):
            crb_data = {}

        cost_str = crb_data.get("cost", "")
        risk_str = crb_data.get("risk", "")
        benefit_str = crb_data.get("benefit", "")

        # --- Cost fallback: proportional share weighted by difficulty ---
        if not cost_str or cost_str == "TBD":
            cost_str = self._derive_task_cost(difficulty, cost_context, total_tasks)

        # --- Risk fallback: correlate with difficulty ---
        risk_map = {"easy": "low", "medium": "medium", "hard": "high"}
        if not risk_str or risk_str == "low":
            # Only override if it was the old blanket default "low"
            # and we have a non-easy difficulty
            if difficulty != "easy" and crb_data.get("risk") in (None, "low"):
                risk_str = risk_map[difficulty]
            elif not risk_str:
                risk_str = risk_map[difficulty]

        # --- Benefit fallback ---
        if not benefit_str or benefit_str == "TBD":
            benefit_str = self._derive_task_benefit(
                phase_num, difficulty, cost_context, total_tasks
            )

        return {
            "id": task_id,
            "title": task_data.get("title", f"Task {task_num}"),
            "description": task_data.get("description", ""),
            "time_estimate_minutes": time_est,
            "difficulty": difficulty,
            "executor": executor,
            "tools": task_data.get("tools", []),
            "tutorial_hint": task_data.get("tutorial_hint"),
            "dependencies": dependencies,
            "crb": {
                "cost": cost_str,
                "risk": risk_str,
                "benefit": benefit_str,
            },
        }

    @staticmethod
    def _derive_task_cost(
        difficulty: str,
        cost_context: Optional[Dict[str, Any]],
        total_tasks: int,
    ) -> str:
        """Derive a cost estimate for a task from the recommendation financials."""
        if not cost_context:
            return "€0"

        total_cost = cost_context.get("total_implementation_cost")
        monthly = cost_context.get("monthly_ongoing_cost")

        if total_cost is not None and total_tasks > 0:
            weight = {"easy": 0.5, "medium": 1.0, "hard": 2.0}[difficulty]
            share = (total_cost * weight) / max(total_tasks, 1)
            if share < 1:
                return "€0 (included)"
            return f"€{share:,.0f}"

        if monthly is not None:
            return f"€{monthly:,.0f}/mo (shared)"

        return "€0"

    @staticmethod
    def _derive_task_benefit(
        phase_num: int,
        difficulty: str,
        cost_context: Optional[Dict[str, Any]],
        total_tasks: int,
    ) -> str:
        """Derive a benefit description for a task."""
        if not cost_context:
            return "Process improvement"

        annual = cost_context.get("annual_benefit")
        hours = cost_context.get("time_savings_hours_per_week")

        # Early phases (1-2) are foundational
        if phase_num <= 2:
            if annual is not None:
                return f"Foundation for €{annual:,.0f}/yr savings"
            if hours is not None:
                return f"Foundation for {hours} hrs/week savings"
            return "Foundational setup for later savings"

        # Later phases get proportional benefit
        if annual is not None and total_tasks > 0:
            weight = {"easy": 0.5, "medium": 1.0, "hard": 2.0}[difficulty]
            share = (annual * weight) / max(total_tasks, 1)
            return f"~€{share:,.0f}/yr value"

        if hours is not None:
            frac = {"easy": 0.5, "medium": 1.0, "hard": 2.0}[difficulty]
            hrs = hours * frac / max(total_tasks, 1)
            if hrs >= 0.5:
                return f"~{hrs:.1f} hrs/week saved"
            return "Incremental time savings"

        return "Efficiency improvement"

    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse and extract JSON from LLM response."""
        if not content:
            raise ValueError("Empty response from LLM")

        # Clean markdown code blocks
        if "```" in content:
            match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
            if match:
                content = match.group(1).strip()

        # Find JSON object if response has extra text
        if not content.startswith("{"):
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                content = json_match.group(0)
            else:
                raise ValueError("No valid JSON in response")

        return json.loads(content)

    def _build_playbook_from_data(
        self,
        data: Dict[str, Any],
        recommendation: Dict[str, Any],
        option_type: str,
        option: Dict[str, Any],
        context: PersonalizationContext,
        total_weeks: int,
        cost_context: Optional[Dict[str, Any]] = None,
    ) -> Playbook:
        """Build Playbook model from parsed data with sanitization."""
        phases: List[Phase] = []
        all_task_ids: set = set()

        # Count total tasks for proportional cost/benefit distribution
        total_task_count = sum(
            len(task)
            for phase_data in data.get("phases", [])
            for week_data in phase_data.get("weeks", [])
            for task in [week_data.get("tasks", [])]
        )

        num_phases = len(data.get("phases", [])) or 1

        for pi, phase_data in enumerate(data.get("phases", [])):
            phase_num = phase_data.get("phase_number", pi + 1)
            weeks: List[Week] = []

            for wi, week_data in enumerate(phase_data.get("weeks", [])):
                week_num = week_data.get("week_number", wi + 1)
                tasks: List[PlaybookTask] = []

                for ti, task_data in enumerate(week_data.get("tasks", [])):
                    sanitized = self._sanitize_task_data(
                        task_data, phase_num, week_num, ti + 1,
                        cost_context=cost_context,
                        total_tasks=total_task_count,
                    )

                    # Filter dependencies to only include existing task IDs
                    valid_deps = [
                        d for d in sanitized["dependencies"]
                        if d in all_task_ids
                    ]
                    if len(valid_deps) != len(sanitized["dependencies"]):
                        invalid = set(sanitized["dependencies"]) - set(valid_deps)
                        logger.warning(
                            f"Task {sanitized['id']} has invalid dependencies "
                            f"removed: {invalid}"
                        )
                        sanitized["dependencies"] = valid_deps

                    tasks.append(PlaybookTask(
                        id=sanitized["id"],
                        title=sanitized["title"],
                        description=sanitized["description"],
                        time_estimate_minutes=sanitized["time_estimate_minutes"],
                        difficulty=sanitized["difficulty"],
                        executor=sanitized["executor"],
                        tools=sanitized["tools"],
                        tutorial_hint=sanitized["tutorial_hint"],
                        dependencies=sanitized["dependencies"],
                        crb=TaskCRB(**sanitized["crb"]),
                    ))

                    all_task_ids.add(sanitized["id"])

                weeks.append(Week(
                    week_number=week_num,
                    theme=week_data.get("theme", f"Week {week_num}"),
                    tasks=tasks,
                    checkpoint=week_data.get("checkpoint", "Review progress"),
                ))

            # Phase CRB summary — derive from cost_context if LLM left defaults
            crb_sum = phase_data.get("crb_summary", {})
            phase_total_cost = crb_sum.get("total_cost", "€0")
            phase_monthly_cost = crb_sum.get("monthly_cost", "€0")
            phase_benefits = crb_sum.get("benefits", [])
            phase_risks = crb_sum.get("risks", [])

            if phase_total_cost == "€0" and cost_context:
                impl_cost = cost_context.get("total_implementation_cost")
                if impl_cost is not None:
                    phase_total_cost = f"€{impl_cost / num_phases:,.0f}"
            if phase_monthly_cost == "€0" and cost_context:
                monthly = cost_context.get("monthly_ongoing_cost")
                if monthly is not None:
                    phase_monthly_cost = f"€{monthly:,.0f}/mo"
            if not phase_benefits and cost_context:
                annual = cost_context.get("annual_benefit")
                if annual is not None:
                    phase_benefits = [f"€{annual / num_phases:,.0f}/yr value"]
            if not phase_risks and cost_context and cost_context.get("risks"):
                phase_risks = [r["description"] for r in cost_context["risks"][:2]]

            phases.append(Phase(
                phase_number=phase_num,
                title=phase_data.get("title", f"Phase {phase_num}"),
                duration_weeks=phase_data.get("duration_weeks", len(weeks)),
                outcome=phase_data.get("outcome", ""),
                crb_summary=PhaseCRBSummary(
                    total_cost=phase_total_cost,
                    monthly_cost=phase_monthly_cost,
                    setup_hours=max(0, crb_sum.get("setup_hours", 0)),
                    risks=phase_risks,
                    benefits=phase_benefits,
                    crb_score=min(10, max(0, crb_sum.get("crb_score", 5.0))),
                ),
                weeks=weeks,
            ))

        # Extract immediate first step
        immediate_step = self._extract_immediate_first_step(phases, option, option_type)

        return Playbook(
            id=f"playbook-{uuid.uuid4().hex[:8]}",
            recommendation_id=recommendation.get("id", ""),
            option_type=option_type,
            total_weeks=total_weeks,
            immediate_first_step=immediate_step,
            phases=phases,
            personalization_context=context,
        )

    async def generate_playbook(
        self,
        recommendation: Dict[str, Any],
        option_type: str,
        quiz_answers: Dict[str, Any],
        industry_context: Dict[str, Any],
    ) -> Playbook:
        """Generate a complete playbook for a recommendation option.

        Uses the skills framework for consistent output and expertise integration.
        Falls back to legacy method if skill fails.
        """
        # Try skill-based generation first
        skill = get_skill("playbook-generator", client=self.client)

        if skill:
            try:
                industry = industry_context.get("industry", "professional-services")

                # Get expertise data for this industry
                try:
                    store = get_expertise_store()
                    expertise = store.get_all_expertise_context(industry)
                except (KeyError, ValueError, RuntimeError) as e:
                    logger.warning("playbook_expertise_load_failed", error=str(e))
                    expertise = None

                context = SkillContext(
                    industry=industry,
                    quiz_answers=quiz_answers,
                    expertise=expertise,
                    metadata={
                        "recommendation": recommendation,
                        "option_chosen": option_type,
                        "company_context": industry_context,
                    },
                )
                result = await skill.run(context)

                if result.success:
                    logger.info(
                        f"Playbook generated via skill "
                        f"(expertise_applied={result.expertise_applied}, "
                        f"execution_time={result.execution_time_ms:.0f}ms)"
                    )
                    return self._skill_result_to_playbook(
                        result.data, recommendation, option_type, quiz_answers, industry_context
                    )
                else:
                    logger.warning(
                        f"PlaybookGeneratorSkill failed, using legacy method: "
                        f"{result.warnings}"
                    )
            except (ValueError, KeyError, TypeError, RuntimeError) as e:
                logger.warning("playbook_skill_failed", error=str(e), error_type=type(e).__name__)

        # Fall back to legacy method
        return await self._generate_playbook_legacy(
            recommendation, option_type, quiz_answers, industry_context
        )

    def _skill_result_to_playbook(
        self,
        skill_data: Dict[str, Any],
        recommendation: Dict[str, Any],
        option_type: str,
        quiz_answers: Dict[str, Any],
        industry_context: Dict[str, Any],
    ) -> Playbook:
        """Bridge skill output (simpler dict) to the richer Playbook Pydantic model."""
        context = self._extract_personalization_context(quiz_answers)
        option = recommendation.get("options", {}).get(option_type, {})

        # Extract financial context for smart defaults
        cost_context = self._extract_cost_context(recommendation, option_type, context)

        # The skill returns a timeline with phases — convert to Playbook format
        timeline = skill_data.get("timeline", {})
        total_weeks = timeline.get("total_weeks", self._get_week_count(context.urgency, option_type))

        # Count total tasks across all phases for proportional distribution
        all_phases = timeline.get("phases", [])
        total_task_count = sum(
            len(p.get("tasks", [])) for p in all_phases
        )
        num_phases = len(all_phases) or 1

        phases: List[Phase] = []
        for pi, phase_data in enumerate(all_phases):
            phase_num = phase_data.get("phase", pi + 1)

            # Skill returns flat task lists per phase, wrap them into a single week
            tasks_list = phase_data.get("tasks", [])
            playbook_tasks: List[PlaybookTask] = []

            for ti, task_text in enumerate(tasks_list):
                task_id = f"p{phase_num}-w1-t{ti + 1}"

                # Infer difficulty from task text
                title = task_text if isinstance(task_text, str) else task_text.get("title", f"Task {ti + 1}")
                description = task_text if isinstance(task_text, str) else task_text.get("description", "")
                difficulty = self._infer_difficulty_from_title(title)

                # Build raw task data and run through sanitizer
                raw_task = {
                    "id": task_id,
                    "title": title,
                    "description": description,
                    "difficulty": difficulty,
                    "tools": [],
                    "dependencies": [],
                }
                sanitized = self._sanitize_task_data(
                    raw_task, phase_num, 1, ti + 1,
                    cost_context=cost_context,
                    total_tasks=total_task_count,
                )

                playbook_tasks.append(PlaybookTask(
                    id=sanitized["id"],
                    title=sanitized["title"],
                    description=sanitized["description"],
                    time_estimate_minutes=sanitized["time_estimate_minutes"],
                    difficulty=sanitized["difficulty"],
                    executor=sanitized["executor"],
                    tools=sanitized["tools"],
                    dependencies=sanitized["dependencies"],
                    crb=TaskCRB(**sanitized["crb"]),
                ))

            # Parse weeks range from phase
            week_num = phase_num  # Use phase number as week start

            weeks = [Week(
                week_number=week_num,
                theme=phase_data.get("name", f"Phase {phase_num}"),
                tasks=playbook_tasks,
                checkpoint=phase_data.get("deliverables", ["Review progress"])[0]
                if phase_data.get("deliverables") else "Review progress",
            )]

            # Derive phase CRB summary from cost_context
            phase_total_cost = "€0"
            phase_monthly_cost = "€0"
            phase_benefits: List[str] = []
            phase_risks: List[str] = []

            if cost_context:
                impl_cost = cost_context.get("total_implementation_cost")
                if impl_cost is not None:
                    phase_total_cost = f"€{impl_cost / num_phases:,.0f}"
                monthly = cost_context.get("monthly_ongoing_cost")
                if monthly is not None:
                    phase_monthly_cost = f"€{monthly:,.0f}/mo"
                annual = cost_context.get("annual_benefit")
                if annual is not None:
                    phase_benefits = [f"€{annual / num_phases:,.0f}/yr value"]
                if cost_context.get("risks"):
                    phase_risks = [r["description"] for r in cost_context["risks"][:2]]

            phases.append(Phase(
                phase_number=phase_num,
                title=phase_data.get("name", f"Phase {phase_num}"),
                duration_weeks=phase_data.get("duration_weeks", 2),
                outcome=phase_data.get("focus", ""),
                crb_summary=PhaseCRBSummary(
                    total_cost=phase_total_cost,
                    monthly_cost=phase_monthly_cost,
                    setup_hours=0,
                    risks=phase_risks,
                    benefits=phase_benefits,
                    crb_score=5.0,
                ),
                weeks=weeks,
            ))

        # Extract immediate first step
        immediate_step = self._extract_immediate_first_step(phases, option, option_type)

        return Playbook(
            id=f"playbook-{uuid.uuid4().hex[:8]}",
            recommendation_id=recommendation.get("id", ""),
            option_type=option_type,
            total_weeks=total_weeks,
            immediate_first_step=immediate_step,
            phases=phases,
            personalization_context=context,
        )

    @staticmethod
    def _infer_difficulty_from_title(title: str) -> str:
        """Infer task difficulty from the title text."""
        lower = title.lower()
        hard_keywords = ["integrat", "migrat", "custom", "build", "develop", "api", "automat"]
        easy_keywords = ["sign up", "create account", "review", "document", "explore", "read"]

        if any(kw in lower for kw in hard_keywords):
            return "hard"
        if any(kw in lower for kw in easy_keywords):
            return "easy"
        return "medium"

    async def _generate_playbook_legacy(
        self,
        recommendation: Dict[str, Any],
        option_type: str,
        quiz_answers: Dict[str, Any],
        industry_context: Dict[str, Any],
    ) -> Playbook:
        """Generate a complete playbook using direct LLM calls (legacy method)."""
        context = self._extract_personalization_context(quiz_answers)
        total_weeks = self._get_week_count(context.urgency, option_type)

        # Get the specific option details
        option = recommendation.get("options", {}).get(option_type, {})

        # Extract financial context for prompt enrichment and sanitization
        cost_context = self._extract_cost_context(recommendation, option_type, context)

        prompt = self._build_generation_prompt(
            recommendation, option_type, option, context, total_weeks,
            cost_context=cost_context,
            quiz_answers=quiz_answers,
        )

        try:
            model = get_model_for_task("generate_playbook", "full")
            response = self.client.messages.create(
                model=model,
                max_tokens=8000,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text.strip() if response.content else ""
            data = self._parse_llm_response(content)

            # Pre-validate the data
            validation = validate_playbook_data(data)
            if not validation.valid:
                logger.error(f"Playbook validation errors: {validation.errors}")
                # Try to fix common issues and continue
                for warning in validation.warnings:
                    logger.warning(f"Playbook warning: {warning}")

            # Build the playbook (with sanitization)
            playbook = self._build_playbook_from_data(
                data, recommendation, option_type, option, context, total_weeks,
                cost_context=cost_context,
            )

            return playbook

        except Exception as e:
            logger.error(f"Failed to generate playbook: {e}")
            raise

    def _extract_immediate_first_step(
        self,
        phases: List[Phase],
        option: Dict[str, Any],
        option_type: str,
    ) -> ImmediateFirstStep:
        """Extract or generate the immediate first step for momentum."""
        # Try to get from first task of first phase
        if phases and phases[0].weeks and phases[0].weeks[0].tasks:
            first_task = phases[0].weeks[0].tasks[0]
            return ImmediateFirstStep(
                action=first_task.title,
                url=first_task.tools[0] if first_task.tools else None,
                time_minutes=min(30, first_task.time_estimate_minutes),
                outcome=first_task.crb.benefit,
            )

        # Generate from option data
        vendor = option.get("vendor") or option.get("name", "")
        matched = option.get("matched_vendor", {})
        if matched.get("vendor"):
            vendor = matched["vendor"]

        # Common vendor URLs for quick lookup
        vendor_urls = {
            "calendly": "https://calendly.com/signup",
            "acuity": "https://acuityscheduling.com/signup",
            "hubspot": "https://app.hubspot.com/signup",
            "zapier": "https://zapier.com/sign-up",
            "make": "https://www.make.com/en/register",
            "n8n": "https://n8n.io/get-started",
            "slack": "https://slack.com/get-started",
            "notion": "https://www.notion.so/signup",
            "airtable": "https://airtable.com/signup",
            "stripe": "https://dashboard.stripe.com/register",
        }

        vendor_lower = vendor.lower() if vendor else ""
        url = None
        for key, vendor_url in vendor_urls.items():
            if key in vendor_lower:
                url = vendor_url
                break

        if vendor:
            return ImmediateFirstStep(
                action=f"Create a free {vendor} account",
                url=url,
                time_minutes=10,
                outcome=f"Access to {vendor} to start exploring the platform",
            )

        # Default by option type
        if option_type in ("custom_solution", "connect_and_automate"):
            return ImmediateFirstStep(
                action="Create a GitHub repository for your project",
                url="https://github.com/new",
                time_minutes=5,
                outcome="A project home for your custom solution",
            )
        else:
            return ImmediateFirstStep(
                action="Document your current workflow in Notion",
                url="https://www.notion.so/signup",
                time_minutes=20,
                outcome="A clear process map to guide implementation",
            )
