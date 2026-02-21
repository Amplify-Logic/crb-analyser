# backend/src/services/playbook_generator.py
"""
Playbook Generation Service

Generates personalized implementation playbooks from recommendations.
Uses canonical models from src/models/playbook.py with full validation.
"""
import json
import logging
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

logger = logging.getLogger(__name__)


# =============================================================================
# PLAYBOOK GENERATOR
# =============================================================================

class PlaybookGenerator:
    """Generate personalized playbooks from recommendations."""

    SYSTEM_PROMPT = """You are an expert implementation consultant creating actionable playbooks.

Your playbooks must be:
1. SPECIFIC - Exact tool names, exact steps, no vague instructions
2. FAST-PACED - Things can move fast with modern tools. Compress timelines.
3. PERSONALIZED - Adapt to team size, tech level, existing tools
4. CRB-FOCUSED - Every task shows Cost, Risk, Benefit
5. DEPENDENCY-AWARE - Tasks reference prerequisites by ID

Generate aggressive but achievable week-by-week plans with proper task dependencies."""

    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

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
            industry=quiz_answers.get("industry", "general"),
            urgency=urgency,
        )

    def _get_week_count(self, urgency: str, option_type: str) -> int:
        """Get total weeks based on urgency and option type."""
        base_weeks = {
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
    ) -> str:
        """Build the LLM prompt for playbook generation."""
        executor_guidance = (
            "all tasks go to 'owner' since this is a solo operation"
            if context.team_size == "solo"
            else "distribute between 'owner' and 'team' based on skill requirements"
        )

        detail_level = (
            "detailed hand-holding with step-by-step instructions"
            if context.technical_level <= 2
            else "link to docs, skip basics - user is technically proficient"
            if context.technical_level >= 4
            else "moderate detail - explain key concepts but don't over-explain"
        )

        return f"""Generate a detailed implementation playbook.

RECOMMENDATION: {recommendation.get('title')}
OPTION: {option_type.replace('_', ' ').title()}
OPTION DETAILS: {json.dumps(option, indent=2)}

PERSONALIZATION:
- Team size: {context.team_size}
- Technical level: {context.technical_level}/5
- Budget: €{context.budget_monthly}/month
- Existing tools: {', '.join(context.existing_tools) or 'None specified'}
- Industry: {context.industry}
- Urgency: {context.urgency}
- Primary pain: {context.primary_pain_point}

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
                            "time_estimate_minutes": 30,
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
                                "cost": "€0",
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

REQUIREMENTS:
1. 3-5 phases total, covering all {total_weeks} weeks
2. 3-6 tasks per week
3. Tasks are {MIN_TASK_MINUTES}-{MAX_TASK_MINUTES} minutes each (most should be 15-120 min)
4. Executor: {executor_guidance}
5. Skip setup for tools they already have: {context.existing_tools}
6. Technical level {context.technical_level}/5 means {detail_level}
7. Every task MUST have a CRB breakdown
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
    ) -> Dict[str, Any]:
        """Sanitize and normalize task data from LLM response."""
        # Ensure valid ID
        task_id = task_data.get("id") or f"p{phase_num}-w{week_num}-t{task_num}"

        # Ensure time estimate is within bounds
        time_est = task_data.get("time_estimate_minutes", 30)
        if not isinstance(time_est, int):
            try:
                time_est = int(time_est)
            except (ValueError, TypeError):
                time_est = 30
        time_est = max(MIN_TASK_MINUTES, min(MAX_TASK_MINUTES, time_est))

        # Ensure valid difficulty
        difficulty = task_data.get("difficulty", "medium")
        if difficulty not in ("easy", "medium", "hard"):
            difficulty = "medium"

        # Ensure valid executor
        executor = task_data.get("executor", "owner")
        if executor not in ("owner", "team", "hire_out"):
            executor = "owner"

        # Ensure dependencies is a list
        dependencies = task_data.get("dependencies", [])
        if not isinstance(dependencies, list):
            dependencies = []
        # Filter out any non-string dependencies
        dependencies = [d for d in dependencies if isinstance(d, str) and d]

        # Build CRB
        crb_data = task_data.get("crb", {})
        if not isinstance(crb_data, dict):
            crb_data = {}

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
                "cost": crb_data.get("cost", "TBD"),
                "risk": crb_data.get("risk", "low"),
                "benefit": crb_data.get("benefit", "TBD"),
            },
        }

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
    ) -> Playbook:
        """Build Playbook model from parsed data with sanitization."""
        phases: List[Phase] = []
        all_task_ids: set = set()

        for pi, phase_data in enumerate(data.get("phases", [])):
            phase_num = phase_data.get("phase_number", pi + 1)
            weeks: List[Week] = []

            for wi, week_data in enumerate(phase_data.get("weeks", [])):
                week_num = week_data.get("week_number", wi + 1)
                tasks: List[PlaybookTask] = []

                for ti, task_data in enumerate(week_data.get("tasks", [])):
                    sanitized = self._sanitize_task_data(
                        task_data, phase_num, week_num, ti + 1
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

            crb_sum = phase_data.get("crb_summary", {})
            phases.append(Phase(
                phase_number=phase_num,
                title=phase_data.get("title", f"Phase {phase_num}"),
                duration_weeks=phase_data.get("duration_weeks", len(weeks)),
                outcome=phase_data.get("outcome", ""),
                crb_summary=PhaseCRBSummary(
                    total_cost=crb_sum.get("total_cost", "€0"),
                    monthly_cost=crb_sum.get("monthly_cost", "€0"),
                    setup_hours=max(0, crb_sum.get("setup_hours", 0)),
                    risks=crb_sum.get("risks", []),
                    benefits=crb_sum.get("benefits", []),
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
                industry = industry_context.get("industry", "general")

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

        # The skill returns a timeline with phases — convert to Playbook format
        timeline = skill_data.get("timeline", {})
        total_weeks = timeline.get("total_weeks", self._get_week_count(context.urgency, option_type))

        phases: List[Phase] = []
        for pi, phase_data in enumerate(timeline.get("phases", [])):
            phase_num = phase_data.get("phase", pi + 1)

            # Skill returns flat task lists per phase, wrap them into a single week
            tasks_list = phase_data.get("tasks", [])
            playbook_tasks: List[PlaybookTask] = []

            for ti, task_text in enumerate(tasks_list):
                task_id = f"p{phase_num}-w1-t{ti + 1}"
                playbook_tasks.append(PlaybookTask(
                    id=task_id,
                    title=task_text if isinstance(task_text, str) else task_text.get("title", f"Task {ti + 1}"),
                    description=task_text if isinstance(task_text, str) else task_text.get("description", ""),
                    time_estimate_minutes=60,
                    difficulty="medium",
                    executor="owner",
                    tools=[],
                    dependencies=[],
                    crb=TaskCRB(cost="TBD", risk="low", benefit="TBD"),
                ))

            # Parse weeks range from phase
            weeks_str = phase_data.get("weeks", str(phase_num))
            week_num = phase_num  # Use phase number as week start

            weeks = [Week(
                week_number=week_num,
                theme=phase_data.get("name", f"Phase {phase_num}"),
                tasks=playbook_tasks,
                checkpoint=phase_data.get("deliverables", ["Review progress"])[0]
                if phase_data.get("deliverables") else "Review progress",
            )]

            phases.append(Phase(
                phase_number=phase_num,
                title=phase_data.get("name", f"Phase {phase_num}"),
                duration_weeks=phase_data.get("duration_weeks", 2),
                outcome=phase_data.get("focus", ""),
                crb_summary=PhaseCRBSummary(
                    total_cost="€0",
                    monthly_cost="€0",
                    setup_hours=0,
                    risks=[],
                    benefits=[],
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

        prompt = self._build_generation_prompt(
            recommendation, option_type, option, context, total_weeks
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
                data, recommendation, option_type, option, context, total_weeks
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
        if option_type == "custom_solution":
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
