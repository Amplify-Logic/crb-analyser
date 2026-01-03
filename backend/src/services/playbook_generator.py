# backend/src/services/playbook_generator.py
"""
Playbook Generation Service

Generates personalized implementation playbooks from recommendations.
"""
import json
import logging
import re
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Literal

from anthropic import Anthropic
from pydantic import BaseModel, Field, field_validator

from src.config.settings import settings
from src.config.model_routing import get_model_for_task

logger = logging.getLogger(__name__)


# =============================================================================
# INLINE MODELS (Stubs - will be replaced when models/playbook.py is created)
# =============================================================================

class TaskCRB(BaseModel):
    """CRB breakdown for a single task."""
    cost: str = Field(..., description="Cost description, e.g., '€0 (free tier)'")
    risk: Literal["low", "medium", "high"] = "low"
    benefit: str = Field(..., description="Benefit description, e.g., 'Saves 2 hrs/week'")

    @field_validator('risk', mode='before')
    @classmethod
    def extract_risk_level(cls, v):
        """Extract just the risk level from strings like 'medium - pricing accuracy critical'."""
        if isinstance(v, str):
            v_lower = v.lower().strip()
            if v_lower.startswith('high'):
                return 'high'
            elif v_lower.startswith('medium'):
                return 'medium'
            elif v_lower.startswith('low'):
                return 'low'
            # Try to find keywords anywhere in the string
            if 'high' in v_lower:
                return 'high'
            elif 'medium' in v_lower:
                return 'medium'
            else:
                return 'low'  # Default to low
        return v


class PlaybookTask(BaseModel):
    """A single actionable task within a week."""
    id: str
    title: str
    description: str = ""
    time_estimate_minutes: int = 30
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    executor: Literal["owner", "team", "hire_out"] = "owner"
    tools: List[str] = Field(default_factory=list)
    tutorial_hint: Optional[str] = None
    crb: TaskCRB
    completed: bool = False
    completed_at: Optional[datetime] = None


class Week(BaseModel):
    """A week of tasks within a phase."""
    week_number: int
    theme: str
    tasks: List[PlaybookTask]
    checkpoint: str = Field(..., description="What success looks like at end of week")


class PhaseCRBSummary(BaseModel):
    """Aggregated CRB for an entire phase."""
    total_cost: str
    monthly_cost: str
    setup_hours: int
    risks: List[str]
    benefits: List[str]
    crb_score: float = Field(..., ge=0, le=10)


class Phase(BaseModel):
    """A major phase of the playbook (3-5 per playbook)."""
    phase_number: int
    title: str
    duration_weeks: int
    outcome: str
    crb_summary: PhaseCRBSummary
    weeks: List[Week]


class PersonalizationContext(BaseModel):
    """Context derived from quiz answers for personalization."""
    team_size: Literal["solo", "small", "medium", "large"] = "solo"
    technical_level: int = Field(3, ge=1, le=5)
    budget_monthly: int = 500
    existing_tools: List[str] = Field(default_factory=list)
    primary_pain_point: str = ""
    industry: str = "general"
    urgency: Literal["asap", "normal", "flexible"] = "normal"


class ImmediateFirstStep(BaseModel):
    """The ONE thing to do before reading further - creates momentum."""
    action: str = Field(..., description="What to do, e.g., 'Create a Calendly account'")
    url: Optional[str] = Field(None, description="Direct URL to start")
    time_minutes: int = Field(15, description="Time to complete (5-30 min)")
    outcome: str = Field(..., description="What they'll have after, e.g., 'A booking link ready to share'")
    do_this_now: str = Field(
        "Do this before reading the rest of the playbook.",
        description="Instruction to act immediately"
    )


class Playbook(BaseModel):
    """Complete playbook for a recommendation option."""
    id: str
    recommendation_id: str
    option_type: Literal["off_the_shelf", "best_in_class", "custom_solution"]
    total_weeks: int
    immediate_first_step: Optional[ImmediateFirstStep] = Field(
        None,
        description="The ONE thing to do right now before reading further"
    )
    phases: List[Phase]
    personalization_context: PersonalizationContext
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PlaybookProgress(BaseModel):
    """Track user progress through playbook."""
    report_id: str
    playbook_id: str
    tasks_completed: int = 0
    tasks_total: int = 0
    current_phase: int = 1
    current_week: int = 1
    started_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None


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

Generate aggressive but achievable week-by-week plans."""

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

    async def generate_playbook(
        self,
        recommendation: Dict[str, Any],
        option_type: str,
        quiz_answers: Dict[str, Any],
        industry_context: Dict[str, Any],
    ) -> Playbook:
        """Generate a complete playbook for a recommendation option."""
        context = self._extract_personalization_context(quiz_answers)
        total_weeks = self._get_week_count(context.urgency, option_type)

        # Get the specific option details
        option = recommendation.get("options", {}).get(option_type, {})

        prompt = f"""Generate a detailed implementation playbook.

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
                            "id": "task-1-1-1",
                            "title": "Sign up for [specific tool]",
                            "description": "Create account and complete onboarding",
                            "time_estimate_minutes": 30,
                            "difficulty": "easy",
                            "executor": "owner",
                            "tools": ["tool-name"],
                            "tutorial_hint": "Use code SAVE20 for discount",
                            "crb": {{
                                "cost": "€0 (free trial)",
                                "risk": "low",
                                "benefit": "Access to platform"
                            }}
                        }}
                    ],
                    "checkpoint": "Account created and verified"
                }}
            ]
        }}
    ]
}}

REQUIREMENTS:
1. 3-5 phases total, covering all {total_weeks} weeks
2. 3-6 tasks per week
3. Tasks are 15-120 minutes each
4. Executor based on team size: "{context.team_size}" means {'all tasks go to owner' if context.team_size == 'solo' else 'distribute between owner and team'}
5. Skip setup for tools they already have: {context.existing_tools}
6. Technical level {context.technical_level}/5 means {'detailed hand-holding' if context.technical_level <= 2 else 'link to docs, skip basics' if context.technical_level >= 4 else 'moderate detail'}
7. Every task MUST have a CRB breakdown

Return ONLY valid JSON, no explanation."""

        try:
            model = get_model_for_task("generate_playbook", "full")
            response = self.client.messages.create(
                model=model,
                max_tokens=8000,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text.strip() if response.content else ""

            # Check for empty response
            if not content:
                logger.warning("Empty response from LLM for playbook generation")
                raise ValueError("Empty response from LLM")

            # Clean and parse JSON
            if "```" in content:
                match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
                if match:
                    content = match.group(1).strip()

            # Additional cleanup - find JSON object
            if not content.startswith("{"):
                # Try to find JSON object in response
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    content = json_match.group(0)
                else:
                    logger.warning(f"No JSON found in playbook response: {content[:200]}")
                    raise ValueError("No valid JSON in response")

            data = json.loads(content)

            # Build Playbook model
            phases = []
            for phase_data in data.get("phases", []):
                weeks = []
                for week_data in phase_data.get("weeks", []):
                    tasks = []
                    for task_data in week_data.get("tasks", []):
                        crb_data = task_data.get("crb", {})
                        tasks.append(PlaybookTask(
                            id=task_data.get("id", f"task-{uuid.uuid4().hex[:8]}"),
                            title=task_data.get("title", ""),
                            description=task_data.get("description", ""),
                            time_estimate_minutes=task_data.get("time_estimate_minutes", 30),
                            difficulty=task_data.get("difficulty", "medium"),
                            executor=task_data.get("executor", "owner"),
                            tools=task_data.get("tools", []),
                            tutorial_hint=task_data.get("tutorial_hint"),
                            crb=TaskCRB(
                                cost=crb_data.get("cost", "TBD"),
                                risk=crb_data.get("risk", "low"),
                                benefit=crb_data.get("benefit", "TBD"),
                            ),
                        ))

                    weeks.append(Week(
                        week_number=week_data.get("week_number", 1),
                        theme=week_data.get("theme", ""),
                        tasks=tasks,
                        checkpoint=week_data.get("checkpoint", ""),
                    ))

                crb_sum = phase_data.get("crb_summary", {})
                phases.append(Phase(
                    phase_number=phase_data.get("phase_number", 1),
                    title=phase_data.get("title", ""),
                    duration_weeks=phase_data.get("duration_weeks", 2),
                    outcome=phase_data.get("outcome", ""),
                    crb_summary=PhaseCRBSummary(
                        total_cost=crb_sum.get("total_cost", "€0"),
                        monthly_cost=crb_sum.get("monthly_cost", "€0"),
                        setup_hours=crb_sum.get("setup_hours", 0),
                        risks=crb_sum.get("risks", []),
                        benefits=crb_sum.get("benefits", []),
                        crb_score=crb_sum.get("crb_score", 5.0),
                    ),
                    weeks=weeks,
                ))

            # Extract immediate first step from first task or generate one
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
