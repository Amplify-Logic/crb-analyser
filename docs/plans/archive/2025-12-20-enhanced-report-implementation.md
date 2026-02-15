# Enhanced Report System - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add personalized playbooks, system architecture diagrams, industry insights, and interactive ROI calculator to CRB reports.

**Architecture:** Extend existing report generation with new phases for playbook/stack generation. Add new React components for interactive features. Store playbook progress in Supabase.

**Tech Stack:** FastAPI, Pydantic, React 18, TypeScript, Framer Motion, Supabase, Recharts (for interactive charts)

---

## Phase 1: Playbook Data Models & Generation

### Task 1.1: Create Playbook Pydantic Models

**Files:**
- Create: `backend/src/models/playbook.py`
- Modify: `backend/src/models/__init__.py`

**Step 1: Create the playbook models file**

```python
# backend/src/models/playbook.py
"""
Playbook models for personalized implementation guides.
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class TaskCRB(BaseModel):
    """CRB breakdown for a single task."""
    cost: str = Field(..., description="Cost description, e.g., '€0 (free tier)'")
    risk: Literal["low", "medium", "high"] = "low"
    benefit: str = Field(..., description="Benefit description, e.g., 'Saves 2 hrs/week'")


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


class Playbook(BaseModel):
    """Complete playbook for a recommendation option."""
    id: str
    recommendation_id: str
    option_type: Literal["off_the_shelf", "best_in_class", "custom_solution"]
    total_weeks: int
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
```

**Step 2: Export from models __init__.py**

Add to `backend/src/models/__init__.py`:

```python
from .playbook import (
    TaskCRB,
    PlaybookTask,
    Week,
    PhaseCRBSummary,
    Phase,
    PersonalizationContext,
    Playbook,
    PlaybookProgress,
)
```

And add to `__all__`:

```python
    # Playbook
    "TaskCRB",
    "PlaybookTask",
    "Week",
    "PhaseCRBSummary",
    "Phase",
    "PersonalizationContext",
    "Playbook",
    "PlaybookProgress",
```

**Step 3: Run type check**

```bash
cd /Users/larsmusic/CRB\ Analyser/crb-analyser/backend
python -c "from src.models.playbook import Playbook, PlaybookTask, Phase; print('Models OK')"
```

**Step 4: Commit**

```bash
git add backend/src/models/playbook.py backend/src/models/__init__.py
git commit -m "feat: add playbook data models for personalized implementation guides"
```

---

### Task 1.2: Create System Architecture Models

**Files:**
- Create: `backend/src/models/system_architecture.py`
- Modify: `backend/src/models/__init__.py`

**Step 1: Create the system architecture models**

```python
# backend/src/models/system_architecture.py
"""
System Architecture models for visualizing integrated AI systems.
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class NodeCRB(BaseModel):
    """CRB for a single tool/node in the architecture."""
    cost: str
    risk: str
    risk_level: Literal["low", "medium", "high"] = "low"
    benefit: str
    powers: List[str] = Field(default_factory=list, description="What automations this powers")


class Position(BaseModel):
    """Position for diagram layout."""
    x: int = 0
    y: int = 0
    column: Literal["existing", "ai_layer", "automations"] = "existing"


class ToolNode(BaseModel):
    """A tool or service in the architecture."""
    id: str
    name: str
    category: Literal["existing", "ai_brain", "automation", "database", "hosting"] = "existing"
    icon: Optional[str] = None
    monthly_cost: float = 0
    one_time_cost: float = 0
    crb: NodeCRB
    position: Position = Field(default_factory=Position)
    is_existing: bool = False  # True if user already has this tool


class Connection(BaseModel):
    """Connection between two nodes showing data flow."""
    id: str
    from_node: str
    to_node: str
    data_flow: str  # "Customer inquiries", "Lead data"
    integration_type: Literal["api", "webhook", "zapier", "native", "custom"] = "api"


class AutomationNode(BaseModel):
    """An automation/workflow output."""
    id: str
    name: str
    trigger: str
    action: str
    tools_used: List[str]
    output_type: str  # "notification", "report", "action"


class CostItem(BaseModel):
    """A single cost line item."""
    name: str
    monthly_cost: float
    one_time_cost: float = 0
    category: Literal["saas", "diy", "both"] = "saas"


class CostBreakdown(BaseModel):
    """Complete cost breakdown for a route."""
    items: List[CostItem]
    total_monthly: float
    total_one_time: float = 0


class CostComparison(BaseModel):
    """Compare SaaS vs DIY routes."""
    saas_route: CostBreakdown
    diy_route: CostBreakdown
    monthly_savings: float
    savings_percentage: float
    build_cost: float
    breakeven_months: float


class SystemArchitecture(BaseModel):
    """Complete system architecture for a report."""
    report_id: str
    existing_tools: List[ToolNode]
    ai_layer: List[ToolNode]
    automations: List[AutomationNode]
    connections: List[Connection]
    cost_comparison: CostComparison
```

**Step 2: Export from models __init__.py**

Add imports and exports for system architecture models.

**Step 3: Run type check**

```bash
python -c "from src.models.system_architecture import SystemArchitecture, ToolNode; print('OK')"
```

**Step 4: Commit**

```bash
git add backend/src/models/system_architecture.py backend/src/models/__init__.py
git commit -m "feat: add system architecture models for stack visualization"
```

---

### Task 1.3: Create Industry Insights Models

**Files:**
- Create: `backend/src/models/industry_insights.py`
- Modify: `backend/src/models/__init__.py`

**Step 1: Create industry insights models**

```python
# backend/src/models/industry_insights.py
"""
Industry Insights models for competitive/market context.
"""
from typing import List, Literal
from pydantic import BaseModel, Field


class InsightCRB(BaseModel):
    """Typical CRB for an industry capability."""
    typical_cost: str  # "€50-200/mo"
    risk_level: Literal["low", "medium", "high"] = "medium"
    typical_benefit: str  # "12 hrs/wk saved"


class AdoptionStat(BaseModel):
    """Adoption statistics for an AI capability."""
    capability: str  # "Content automation"
    adoption_percentage: int = Field(..., ge=0, le=100)
    average_outcome: str  # "12 hrs/week saved"
    crb: InsightCRB


class OpportunityMap(BaseModel):
    """Map of opportunities by maturity."""
    emerging: List[str] = Field(default_factory=list, description="Early wins, less proven")
    growing: List[str] = Field(default_factory=list, description="Sweet spot, high impact")
    established: List[str] = Field(default_factory=list, description="Table stakes")
    best_fit: Literal["emerging", "growing", "established"] = "growing"
    rationale: str = ""


class SocialProof(BaseModel):
    """Social proof from similar businesses."""
    quote: str
    company_description: str  # "8-person agency, similar size"
    outcome: str
    industry: str


class IndustryInsights(BaseModel):
    """Complete industry insights for a report."""
    industry: str
    industry_display_name: str
    adoption_stats: List[AdoptionStat]
    opportunity_map: OpportunityMap
    social_proof: List[SocialProof]
```

**Step 2: Export and verify**

**Step 3: Commit**

```bash
git add backend/src/models/industry_insights.py backend/src/models/__init__.py
git commit -m "feat: add industry insights models"
```

---

### Task 1.4: Create ROI Calculator Models

**Files:**
- Create: `backend/src/models/roi_calculator.py`
- Modify: `backend/src/models/__init__.py`

**Step 1: Create ROI calculator models**

```python
# backend/src/models/roi_calculator.py
"""
ROI Calculator models for interactive what-if scenarios.
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class ROIInputs(BaseModel):
    """User-adjustable inputs for ROI calculation."""
    hours_weekly: float = Field(10, ge=0, le=80)
    hourly_rate: float = Field(50, ge=0, le=500)
    automation_rate: float = Field(0.7, ge=0.1, le=0.95)
    implementation_approach: Literal["diy", "saas", "freelancer"] = "saas"


class CalculatorCRB(BaseModel):
    """CRB display for calculator results."""
    cost_display: str  # "€150/mo + €2,400 build"
    risk_display: str  # "Low (proven pattern)"
    risk_bar: float = Field(..., ge=0, le=1)  # 0-1 for visual
    benefit_display: str  # "€3,150/mo saved"
    time_benefit: str  # "10.5 hrs/wk freed"


class ROIResults(BaseModel):
    """Calculated ROI results."""
    # Time
    hours_saved_weekly: float
    hours_saved_monthly: float
    hours_saved_yearly: float

    # Cost
    implementation_cost: float  # One-time
    monthly_cost: float  # Ongoing

    # Benefit
    monthly_savings: float
    yearly_savings: float

    # Analysis
    roi_percentage: float
    breakeven_months: float
    three_year_net: float

    # CRB Display
    crb_summary: CalculatorCRB


class SavedScenario(BaseModel):
    """A saved ROI scenario for comparison."""
    id: str
    name: str
    inputs: ROIInputs
    results: ROIResults
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ROICalculator(BaseModel):
    """Complete ROI calculator state for a report."""
    report_id: str
    default_inputs: ROIInputs
    scenarios: List[SavedScenario] = Field(default_factory=list)
```

**Step 2: Export and verify**

**Step 3: Commit**

```bash
git add backend/src/models/roi_calculator.py backend/src/models/__init__.py
git commit -m "feat: add ROI calculator models for interactive scenarios"
```

---

### Task 1.5: Create Playbook Generation Service

**Files:**
- Create: `backend/src/services/playbook_generator.py`

**Step 1: Create the playbook generator service**

```python
# backend/src/services/playbook_generator.py
"""
Playbook Generation Service

Generates personalized implementation playbooks from recommendations.
"""
import json
import logging
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
)

logger = logging.getLogger(__name__)


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
            import re
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

            content = response.content[0].text.strip()

            # Clean and parse JSON
            if "```" in content:
                import re
                match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
                if match:
                    content = match.group(1)

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

            return Playbook(
                id=f"playbook-{uuid.uuid4().hex[:8]}",
                recommendation_id=recommendation.get("id", ""),
                option_type=option_type,
                total_weeks=total_weeks,
                phases=phases,
                personalization_context=context,
            )

        except Exception as e:
            logger.error(f"Failed to generate playbook: {e}")
            raise
```

**Step 2: Verify import**

```bash
python -c "from src.services.playbook_generator import PlaybookGenerator; print('OK')"
```

**Step 3: Commit**

```bash
git add backend/src/services/playbook_generator.py
git commit -m "feat: add playbook generation service with personalization"
```

---

### Task 1.6: Create System Architecture Generator

**Files:**
- Create: `backend/src/services/architecture_generator.py`

**Step 1: Create the architecture generator**

```python
# backend/src/services/architecture_generator.py
"""
System Architecture Generator

Creates visual system architecture from recommendations and quiz data.
"""
import json
import logging
from typing import Dict, Any, List

from src.models.system_architecture import (
    SystemArchitecture,
    ToolNode,
    Connection,
    AutomationNode,
    NodeCRB,
    Position,
    CostComparison,
    CostBreakdown,
    CostItem,
)

logger = logging.getLogger(__name__)


# Tool database with costs and categories
TOOL_DATABASE = {
    # AI Models
    "claude": {"name": "Claude Sonnet 4.5", "category": "ai_brain", "monthly_cost": 50, "icon": "brain"},
    "claude_opus": {"name": "Claude Opus 4.5", "category": "ai_brain", "monthly_cost": 150, "icon": "brain"},
    "gemini": {"name": "Gemini 3 Flash", "category": "ai_brain", "monthly_cost": 20, "icon": "brain"},
    "gpt": {"name": "GPT-5", "category": "ai_brain", "monthly_cost": 40, "icon": "brain"},

    # Automation
    "make": {"name": "Make.com", "category": "automation", "monthly_cost": 20, "icon": "zap"},
    "zapier": {"name": "Zapier", "category": "automation", "monthly_cost": 30, "icon": "zap"},
    "n8n": {"name": "n8n", "category": "automation", "monthly_cost": 0, "icon": "zap"},

    # CRM
    "hubspot": {"name": "HubSpot", "category": "existing", "monthly_cost": 50, "icon": "users"},
    "salesforce": {"name": "Salesforce", "category": "existing", "monthly_cost": 150, "icon": "users"},

    # Communication
    "slack": {"name": "Slack", "category": "existing", "monthly_cost": 0, "icon": "message"},
    "intercom": {"name": "Intercom", "category": "existing", "monthly_cost": 89, "icon": "message"},

    # Database/Hosting
    "supabase": {"name": "Supabase", "category": "database", "monthly_cost": 0, "icon": "database"},
    "vercel": {"name": "Vercel", "category": "hosting", "monthly_cost": 0, "icon": "cloud"},

    # Billing
    "stripe": {"name": "Stripe", "category": "existing", "monthly_cost": 0, "icon": "credit-card"},
}

# SaaS alternatives with costs
SAAS_ALTERNATIVES = {
    "customer_support": {"name": "Intercom", "monthly_cost": 89},
    "content_generation": {"name": "Jasper", "monthly_cost": 49},
    "lead_scoring": {"name": "Salesforce Einstein", "monthly_cost": 150},
    "analytics": {"name": "Mixpanel", "monthly_cost": 89},
    "email_automation": {"name": "Mailchimp Pro", "monthly_cost": 50},
}


class ArchitectureGenerator:
    """Generate system architecture diagrams from recommendations."""

    def generate_architecture(
        self,
        recommendations: List[Dict[str, Any]],
        quiz_answers: Dict[str, Any],
    ) -> SystemArchitecture:
        """Generate complete system architecture."""

        # Extract existing tools from quiz
        existing_tools_raw = quiz_answers.get("current_tools", [])
        if isinstance(existing_tools_raw, str):
            existing_tools_raw = [t.strip().lower() for t in existing_tools_raw.split(",")]

        # Build existing tools nodes
        existing_tools = []
        for i, tool_key in enumerate(existing_tools_raw[:6]):  # Max 6 existing tools
            tool_info = self._match_tool(tool_key)
            if tool_info:
                existing_tools.append(ToolNode(
                    id=f"existing-{i}",
                    name=tool_info["name"],
                    category="existing",
                    monthly_cost=0,  # Already paying for it
                    crb=NodeCRB(
                        cost="Already owned",
                        risk="None",
                        risk_level="low",
                        benefit="Foundation for integrations",
                        powers=[],
                    ),
                    position=Position(x=0, y=i * 100, column="existing"),
                    is_existing=True,
                ))

        # Build AI layer from recommendations
        ai_layer = [
            ToolNode(
                id="ai-claude",
                name="Claude Sonnet 4.5",
                category="ai_brain",
                monthly_cost=50,
                crb=NodeCRB(
                    cost="~€50/mo at typical usage",
                    risk="API dependency",
                    risk_level="low",
                    benefit="Powers all AI automations",
                    powers=["Lead scoring", "Content generation", "Support responses"],
                ),
                position=Position(x=200, y=0, column="ai_layer"),
            ),
            ToolNode(
                id="ai-automation",
                name="Make.com",
                category="automation",
                monthly_cost=20,
                crb=NodeCRB(
                    cost="€20/mo",
                    risk="Workflow complexity",
                    risk_level="low",
                    benefit="Connects all tools",
                    powers=["Workflows", "Triggers", "Scheduling"],
                ),
                position=Position(x=200, y=100, column="ai_layer"),
            ),
        ]

        # Build automations from recommendations
        automations = []
        for i, rec in enumerate(recommendations[:5]):
            automations.append(AutomationNode(
                id=f"auto-{i}",
                name=rec.get("title", "Automation")[:30],
                trigger=f"When {rec.get('title', 'event').lower().split()[0]} occurs",
                action=rec.get("description", "")[:50],
                tools_used=["claude", "make"],
                output_type="action",
            ))

        # Build connections
        connections = []
        for i, existing in enumerate(existing_tools):
            connections.append(Connection(
                id=f"conn-{i}",
                from_node=existing.id,
                to_node="ai-claude",
                data_flow="Data sync",
                integration_type="api",
            ))

        # Calculate costs
        cost_comparison = self._calculate_costs(recommendations, ai_layer)

        return SystemArchitecture(
            report_id="",  # Set by caller
            existing_tools=existing_tools,
            ai_layer=ai_layer,
            automations=automations,
            connections=connections,
            cost_comparison=cost_comparison,
        )

    def _match_tool(self, tool_key: str) -> Dict[str, Any] | None:
        """Match a tool key to our database."""
        tool_key = tool_key.lower().strip()
        for key, info in TOOL_DATABASE.items():
            if key in tool_key or tool_key in info["name"].lower():
                return info
        return None

    def _calculate_costs(
        self,
        recommendations: List[Dict[str, Any]],
        ai_layer: List[ToolNode],
    ) -> CostComparison:
        """Calculate SaaS vs DIY cost comparison."""

        # DIY costs
        diy_items = [
            CostItem(name=node.name, monthly_cost=node.monthly_cost, category="diy")
            for node in ai_layer
        ]
        diy_items.append(CostItem(name="Supabase", monthly_cost=0, category="diy"))
        diy_items.append(CostItem(name="Vercel", monthly_cost=0, category="diy"))

        diy_total = sum(item.monthly_cost for item in diy_items)
        build_cost = 2400  # Typical freelancer cost

        # SaaS costs (what they'd pay for equivalent functionality)
        saas_items = []
        saas_total = 0
        for rec in recommendations[:5]:
            title_lower = rec.get("title", "").lower()
            for key, saas in SAAS_ALTERNATIVES.items():
                if key.replace("_", " ") in title_lower or key.replace("_", "") in title_lower:
                    saas_items.append(CostItem(
                        name=saas["name"],
                        monthly_cost=saas["monthly_cost"],
                        category="saas",
                    ))
                    saas_total += saas["monthly_cost"]
                    break

        # Ensure minimum SaaS cost for comparison
        if saas_total < 200:
            saas_total = 400
            saas_items = [
                CostItem(name="Multiple SaaS tools", monthly_cost=400, category="saas")
            ]

        monthly_savings = saas_total - diy_total
        savings_pct = (monthly_savings / saas_total * 100) if saas_total > 0 else 0
        breakeven = build_cost / monthly_savings if monthly_savings > 0 else 999

        return CostComparison(
            saas_route=CostBreakdown(items=saas_items, total_monthly=saas_total),
            diy_route=CostBreakdown(items=diy_items, total_monthly=diy_total, total_one_time=build_cost),
            monthly_savings=monthly_savings,
            savings_percentage=savings_pct,
            build_cost=build_cost,
            breakeven_months=round(breakeven, 1),
        )
```

**Step 2: Verify and commit**

```bash
python -c "from src.services.architecture_generator import ArchitectureGenerator; print('OK')"
git add backend/src/services/architecture_generator.py
git commit -m "feat: add system architecture generator for stack visualization"
```

---

### Task 1.7: Create Industry Insights Generator

**Files:**
- Create: `backend/src/services/insights_generator.py`

**Step 1: Create the insights generator**

```python
# backend/src/services/insights_generator.py
"""
Industry Insights Generator

Generates industry benchmarks and adoption statistics.
"""
from typing import Dict, Any, List

from src.models.industry_insights import (
    IndustryInsights,
    AdoptionStat,
    InsightCRB,
    OpportunityMap,
    SocialProof,
)


# Industry-specific data
INDUSTRY_DATA = {
    "marketing-agencies": {
        "display_name": "Marketing Agencies",
        "adoption_stats": [
            {"capability": "Content automation", "adoption": 62, "outcome": "12 hrs/week saved", "cost": "€50-200/mo", "risk": "low", "benefit": "12 hrs/wk saved"},
            {"capability": "AI-assisted reporting", "adoption": 41, "outcome": "Reports in minutes", "cost": "€30-100/mo", "risk": "low", "benefit": "5 hrs/wk saved"},
            {"capability": "Lead scoring", "adoption": 28, "outcome": "2x conversion on hot leads", "cost": "€50-150/mo", "risk": "medium", "benefit": "2x conversion"},
            {"capability": "Chatbots", "adoption": 35, "outcome": "24/7 response capability", "cost": "€20-80/mo", "risk": "low", "benefit": "Always-on support"},
        ],
        "opportunities": {
            "emerging": ["AI video generation", "Voice agents", "Predictive analytics"],
            "growing": ["Lead scoring", "Content personalization", "Chatbots"],
            "established": ["Content drafts", "Email automation", "Social scheduling"],
        },
        "social_proof": [
            {"quote": "We started with content automation - now saving 15 hours/week. Paid for itself in month one.", "company": "8-person agency, similar size", "outcome": "15 hrs/wk saved"},
            {"quote": "AI lead scoring doubled our close rate. Wish we'd done it sooner.", "company": "Digital marketing agency", "outcome": "2x close rate"},
        ],
    },
    "tech-companies": {
        "display_name": "Tech Companies",
        "adoption_stats": [
            {"capability": "Code assistance", "adoption": 78, "outcome": "30% faster development", "cost": "€20-50/mo", "risk": "low", "benefit": "30% faster dev"},
            {"capability": "Documentation automation", "adoption": 55, "outcome": "90% less manual docs", "cost": "€0-30/mo", "risk": "low", "benefit": "90% less docs time"},
            {"capability": "Customer support AI", "adoption": 62, "outcome": "70% ticket deflection", "cost": "€50-200/mo", "risk": "medium", "benefit": "70% deflection"},
            {"capability": "Data analysis", "adoption": 48, "outcome": "Insights in seconds", "cost": "€30-100/mo", "risk": "low", "benefit": "Real-time insights"},
        ],
        "opportunities": {
            "emerging": ["Autonomous agents", "AI code review", "Predictive debugging"],
            "growing": ["Customer support AI", "Data analysis", "Content generation"],
            "established": ["Code assistance", "Documentation", "Testing automation"],
        },
        "social_proof": [
            {"quote": "GitHub Copilot + Claude for reviews cut our PR cycle from 3 days to 4 hours.", "company": "15-person startup", "outcome": "18x faster PRs"},
            {"quote": "AI handles 70% of support tickets. Team focuses on complex issues now.", "company": "SaaS company, 20 employees", "outcome": "70% ticket deflection"},
        ],
    },
    "ecommerce": {
        "display_name": "E-commerce",
        "adoption_stats": [
            {"capability": "Product descriptions", "adoption": 52, "outcome": "10x faster catalog updates", "cost": "€30-100/mo", "risk": "low", "benefit": "10x faster updates"},
            {"capability": "Customer service chatbot", "adoption": 45, "outcome": "24/7 support, 60% resolution", "cost": "€50-150/mo", "risk": "medium", "benefit": "24/7 availability"},
            {"capability": "Personalized recommendations", "adoption": 38, "outcome": "15% increase in AOV", "cost": "€100-300/mo", "risk": "medium", "benefit": "+15% AOV"},
            {"capability": "Inventory forecasting", "adoption": 25, "outcome": "30% less stockouts", "cost": "€50-200/mo", "risk": "medium", "benefit": "30% fewer stockouts"},
        ],
        "opportunities": {
            "emerging": ["Visual search", "Dynamic pricing AI", "Automated photography"],
            "growing": ["Personalization", "Inventory AI", "Customer service bots"],
            "established": ["Product descriptions", "Email automation", "Review management"],
        },
        "social_proof": [
            {"quote": "AI-generated descriptions for 5,000 SKUs in a weekend. Used to take us 3 months.", "company": "Online retailer, €2M revenue", "outcome": "100x faster catalog"},
            {"quote": "Personalization AI increased our average order value by 22%.", "company": "Fashion e-commerce", "outcome": "+22% AOV"},
        ],
    },
    "general": {
        "display_name": "General Business",
        "adoption_stats": [
            {"capability": "Email automation", "adoption": 55, "outcome": "5 hrs/week saved", "cost": "€20-50/mo", "risk": "low", "benefit": "5 hrs/wk saved"},
            {"capability": "Document processing", "adoption": 35, "outcome": "80% faster processing", "cost": "€30-100/mo", "risk": "low", "benefit": "80% faster docs"},
            {"capability": "Meeting transcription", "adoption": 42, "outcome": "No more note-taking", "cost": "€10-30/mo", "risk": "low", "benefit": "100% capture"},
            {"capability": "Customer support", "adoption": 30, "outcome": "24/7 availability", "cost": "€50-150/mo", "risk": "medium", "benefit": "24/7 support"},
        ],
        "opportunities": {
            "emerging": ["Voice interfaces", "Autonomous agents", "Predictive analytics"],
            "growing": ["Customer support AI", "Content generation", "Data analysis"],
            "established": ["Email automation", "Transcription", "Document processing"],
        },
        "social_proof": [
            {"quote": "Started with email automation, now AI handles half our admin work.", "company": "Small business, 5 employees", "outcome": "50% less admin"},
        ],
    },
}


class InsightsGenerator:
    """Generate industry insights and benchmarks."""

    def generate_insights(
        self,
        industry: str,
        ai_readiness_score: int,
    ) -> IndustryInsights:
        """Generate industry insights for a report."""

        # Normalize industry
        industry_key = industry.lower().replace(" ", "-").replace("_", "-")
        data = INDUSTRY_DATA.get(industry_key, INDUSTRY_DATA["general"])

        # Build adoption stats
        adoption_stats = []
        for stat in data["adoption_stats"]:
            adoption_stats.append(AdoptionStat(
                capability=stat["capability"],
                adoption_percentage=stat["adoption"],
                average_outcome=stat["outcome"],
                crb=InsightCRB(
                    typical_cost=stat["cost"],
                    risk_level=stat["risk"],
                    typical_benefit=stat["benefit"],
                ),
            ))

        # Build opportunity map
        opps = data["opportunities"]
        # Determine best fit based on readiness
        if ai_readiness_score >= 70:
            best_fit = "emerging"
            rationale = "High readiness - explore cutting-edge opportunities"
        elif ai_readiness_score >= 50:
            best_fit = "growing"
            rationale = "Solid foundation - focus on proven, high-impact areas"
        else:
            best_fit = "established"
            rationale = "Start with proven patterns to build momentum"

        opportunity_map = OpportunityMap(
            emerging=opps.get("emerging", []),
            growing=opps.get("growing", []),
            established=opps.get("established", []),
            best_fit=best_fit,
            rationale=rationale,
        )

        # Build social proof
        social_proof = []
        for proof in data.get("social_proof", []):
            social_proof.append(SocialProof(
                quote=proof["quote"],
                company_description=proof["company"],
                outcome=proof["outcome"],
                industry=industry_key,
            ))

        return IndustryInsights(
            industry=industry_key,
            industry_display_name=data["display_name"],
            adoption_stats=adoption_stats,
            opportunity_map=opportunity_map,
            social_proof=social_proof,
        )
```

**Step 2: Verify and commit**

```bash
python -c "from src.services.insights_generator import InsightsGenerator; print('OK')"
git add backend/src/services/insights_generator.py
git commit -m "feat: add industry insights generator with adoption stats"
```

---

### Task 1.8: Add Database Migration for Playbook Progress

**Files:**
- Create: `backend/src/migrations/004_playbook_progress.sql`

**Step 1: Create migration file**

```sql
-- backend/src/migrations/004_playbook_progress.sql
-- Playbook progress tracking and ROI scenarios

-- Playbook progress tracking
CREATE TABLE IF NOT EXISTS playbook_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    playbook_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMPTZ,
    completed_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(report_id, playbook_id, task_id)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_playbook_progress_report
    ON playbook_progress(report_id);
CREATE INDEX IF NOT EXISTS idx_playbook_progress_playbook
    ON playbook_progress(report_id, playbook_id);

-- ROI scenarios
CREATE TABLE IF NOT EXISTS roi_scenarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    inputs JSONB NOT NULL,
    results JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_roi_scenarios_report
    ON roi_scenarios(report_id);

-- Model freshness tracking (for keeping AI model recommendations current)
CREATE TABLE IF NOT EXISTS model_updates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_slug TEXT NOT NULL,
    change_type TEXT NOT NULL,  -- 'price', 'new', 'benchmark', 'deprecated'
    old_value JSONB,
    new_value JSONB,
    status TEXT DEFAULT 'pending',  -- 'pending', 'approved', 'dismissed'
    reviewed_at TIMESTAMPTZ,
    reviewed_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_model_updates_status
    ON model_updates(status);

-- Enable RLS
ALTER TABLE playbook_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE roi_scenarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_updates ENABLE ROW LEVEL SECURITY;

-- RLS policies for playbook_progress (public read, authenticated write)
CREATE POLICY "Anyone can view playbook progress"
    ON playbook_progress FOR SELECT
    USING (true);

CREATE POLICY "Anyone can insert playbook progress"
    ON playbook_progress FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Anyone can update playbook progress"
    ON playbook_progress FOR UPDATE
    USING (true);

-- RLS policies for roi_scenarios
CREATE POLICY "Anyone can view roi scenarios"
    ON roi_scenarios FOR SELECT
    USING (true);

CREATE POLICY "Anyone can insert roi scenarios"
    ON roi_scenarios FOR INSERT
    WITH CHECK (true);

-- Admin-only for model_updates
CREATE POLICY "Admin can manage model updates"
    ON model_updates FOR ALL
    USING (auth.jwt() ->> 'role' = 'admin');
```

**Step 2: Commit**

```bash
git add backend/src/migrations/004_playbook_progress.sql
git commit -m "feat: add database migration for playbook progress and ROI scenarios"
```

---

## Phase 2: Integrate with Report Generation

### Task 2.1: Extend Report Service with New Features

**Files:**
- Modify: `backend/src/services/report_service.py`

**Step 1: Add imports at top of file**

Add after existing imports:

```python
from src.services.playbook_generator import PlaybookGenerator
from src.services.architecture_generator import ArchitectureGenerator
from src.services.insights_generator import InsightsGenerator
```

**Step 2: Add new generation phases**

Add new methods to `ReportGenerator` class (after `_generate_verdict`):

```python
    async def _generate_playbooks(self, recommendations: List[Dict]) -> List[Dict[str, Any]]:
        """Generate playbooks for top recommendations."""
        playbook_gen = PlaybookGenerator()
        playbooks = []

        # Generate playbook for top 3 recommendations
        for rec in recommendations[:3]:
            try:
                # Generate for the recommended option
                our_rec = rec.get("our_recommendation", "off_the_shelf")
                playbook = await playbook_gen.generate_playbook(
                    recommendation=rec,
                    option_type=our_rec,
                    quiz_answers=self.context.get("answers", {}),
                    industry_context=self.context.get("industry_knowledge", {}),
                )
                playbooks.append(playbook.model_dump())
            except Exception as e:
                logger.warning(f"Failed to generate playbook for {rec.get('id')}: {e}")

        return playbooks

    def _generate_system_architecture(self, recommendations: List[Dict]) -> Dict[str, Any]:
        """Generate system architecture diagram data."""
        arch_gen = ArchitectureGenerator()
        architecture = arch_gen.generate_architecture(
            recommendations=recommendations,
            quiz_answers=self.context.get("answers", {}),
        )
        return architecture.model_dump()

    def _generate_industry_insights(self) -> Dict[str, Any]:
        """Generate industry insights and benchmarks."""
        insights_gen = InsightsGenerator()
        exec_summary = self._partial_data.get("executive_summary", {})
        ai_score = exec_summary.get("ai_readiness_score", 50)

        insights = insights_gen.generate_insights(
            industry=self.context.get("industry", "general"),
            ai_readiness_score=ai_score,
        )
        return insights.model_dump()
```

**Step 3: Update generate_report method to include new phases**

In the `generate_report` method, add after Phase 6 (roadmap) and before Phase 7 (finalize):

```python
            # Phase 6b: Generate playbooks
            yield {"phase": "playbooks", "step": "Generating implementation playbooks...", "progress": 82}

            playbooks = await self._generate_playbooks(recommendations)
            self._partial_data["playbooks"] = playbooks

            yield {"phase": "playbooks", "step": f"Generated {len(playbooks)} playbooks", "progress": 86}

            # Phase 6c: Generate system architecture
            yield {"phase": "architecture", "step": "Building system architecture...", "progress": 88}

            system_architecture = self._generate_system_architecture(recommendations)
            self._partial_data["system_architecture"] = system_architecture

            yield {"phase": "architecture", "step": "System architecture complete", "progress": 90}

            # Phase 6d: Generate industry insights
            yield {"phase": "insights", "step": "Loading industry insights...", "progress": 92}

            industry_insights = self._generate_industry_insights()
            self._partial_data["industry_insights"] = industry_insights

            yield {"phase": "insights", "step": "Industry insights complete", "progress": 94}

            # Save all new data
            await supabase.table("reports").update({
                "playbooks": playbooks,
                "system_architecture": system_architecture,
                "industry_insights": industry_insights,
            }).eq("id", self.report_id).execute()
```

**Step 4: Commit**

```bash
git add backend/src/services/report_service.py
git commit -m "feat: integrate playbooks, architecture, and insights into report generation"
```

---

## Phase 3: Frontend Components

### Task 3.1: Create Playbook Tab Component

**Files:**
- Create: `frontend/src/components/report/PlaybookTab.tsx`

**Step 1: Create the component**

```typescript
// frontend/src/components/report/PlaybookTab.tsx
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface TaskCRB {
  cost: string
  risk: 'low' | 'medium' | 'high'
  benefit: string
}

interface PlaybookTask {
  id: string
  title: string
  description: string
  time_estimate_minutes: number
  difficulty: 'easy' | 'medium' | 'hard'
  executor: 'owner' | 'team' | 'hire_out'
  tools: string[]
  tutorial_hint?: string
  crb: TaskCRB
  completed: boolean
}

interface Week {
  week_number: number
  theme: string
  tasks: PlaybookTask[]
  checkpoint: string
}

interface PhaseCRBSummary {
  total_cost: string
  monthly_cost: string
  setup_hours: number
  risks: string[]
  benefits: string[]
  crb_score: number
}

interface Phase {
  phase_number: number
  title: string
  duration_weeks: number
  outcome: string
  crb_summary: PhaseCRBSummary
  weeks: Week[]
}

interface Playbook {
  id: string
  recommendation_id: string
  option_type: string
  total_weeks: number
  phases: Phase[]
  personalization_context: {
    team_size: string
    technical_level: number
    budget_monthly: number
  }
}

interface PlaybookTabProps {
  playbooks: Playbook[]
  onTaskComplete?: (playbookId: string, taskId: string, completed: boolean) => void
}

export default function PlaybookTab({ playbooks, onTaskComplete }: PlaybookTabProps) {
  const [selectedPlaybook, setSelectedPlaybook] = useState(0)
  const [expandedPhase, setExpandedPhase] = useState<number | null>(1)
  const [taskState, setTaskState] = useState<Record<string, boolean>>({})

  if (!playbooks || playbooks.length === 0) {
    return (
      <div className="bg-white rounded-2xl p-8 text-center">
        <p className="text-gray-500">No playbooks available yet.</p>
      </div>
    )
  }

  const playbook = playbooks[selectedPlaybook]

  // Calculate progress
  const allTasks = playbook.phases.flatMap(p => p.weeks.flatMap(w => w.tasks))
  const completedTasks = allTasks.filter(t => taskState[t.id] || t.completed).length
  const progressPercent = Math.round((completedTasks / allTasks.length) * 100)

  const handleTaskToggle = (taskId: string) => {
    const newState = !taskState[taskId]
    setTaskState(prev => ({ ...prev, [taskId]: newState }))
    onTaskComplete?.(playbook.id, taskId, newState)
  }

  const difficultyColor = {
    easy: 'bg-green-100 text-green-700',
    medium: 'bg-yellow-100 text-yellow-700',
    hard: 'bg-red-100 text-red-700',
  }

  const executorLabel = {
    owner: 'You',
    team: 'Team',
    hire_out: 'Hire out',
  }

  const riskColor = {
    low: 'text-green-600',
    medium: 'text-yellow-600',
    high: 'text-red-600',
  }

  return (
    <div className="space-y-6">
      {/* Playbook selector */}
      {playbooks.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-2">
          {playbooks.map((pb, i) => (
            <button
              key={pb.id}
              onClick={() => setSelectedPlaybook(i)}
              className={`px-4 py-2 rounded-xl whitespace-nowrap transition ${
                i === selectedPlaybook
                  ? 'bg-primary-600 text-white'
                  : 'bg-white border border-gray-200 hover:bg-gray-50'
              }`}
            >
              {pb.option_type.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
            </button>
          ))}
        </div>
      )}

      {/* Header with progress */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl p-6 shadow-sm"
      >
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Your {playbook.total_weeks}-Week Implementation Playbook
            </h3>
            <p className="text-sm text-gray-500">
              Based on: {playbook.personalization_context.team_size} team •
              Tech level {playbook.personalization_context.technical_level}/5 •
              €{playbook.personalization_context.budget_monthly}/mo budget
            </p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-primary-600">{progressPercent}%</p>
            <p className="text-xs text-gray-500">{completedTasks}/{allTasks.length} tasks</p>
          </div>
        </div>

        {/* Progress bar */}
        <div className="w-full bg-gray-200 rounded-full h-3">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progressPercent}%` }}
            transition={{ duration: 0.5 }}
            className="bg-primary-600 h-3 rounded-full"
          />
        </div>
      </motion.div>

      {/* Phases */}
      <div className="space-y-4">
        {playbook.phases.map((phase) => (
          <motion.div
            key={phase.phase_number}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: phase.phase_number * 0.1 }}
            className="bg-white rounded-2xl shadow-sm overflow-hidden"
          >
            {/* Phase header */}
            <div
              className="p-6 cursor-pointer hover:bg-gray-50 transition"
              onClick={() => setExpandedPhase(
                expandedPhase === phase.phase_number ? null : phase.phase_number
              )}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center font-bold">
                      {phase.phase_number}
                    </span>
                    <h4 className="text-lg font-semibold text-gray-900">{phase.title}</h4>
                    <span className="text-sm text-gray-500">
                      Weeks {phase.weeks[0]?.week_number}-{phase.weeks[phase.weeks.length - 1]?.week_number}
                    </span>
                  </div>
                  <p className="text-gray-600 ml-11">{phase.outcome}</p>

                  {/* Phase CRB summary */}
                  <div className="flex gap-4 mt-3 ml-11 text-sm">
                    <span className="text-gray-600">
                      💰 {phase.crb_summary.total_cost}
                    </span>
                    <span className="text-gray-600">
                      ⏱ {phase.crb_summary.setup_hours} hrs
                    </span>
                    <span className="text-primary-600 font-medium">
                      CRB: {phase.crb_summary.crb_score}/10
                    </span>
                  </div>
                </div>

                <motion.svg
                  animate={{ rotate: expandedPhase === phase.phase_number ? 180 : 0 }}
                  className="w-6 h-6 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </motion.svg>
              </div>
            </div>

            {/* Expanded weeks/tasks */}
            <AnimatePresence>
              {expandedPhase === phase.phase_number && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden border-t"
                >
                  <div className="p-6 space-y-6">
                    {phase.weeks.map((week) => (
                      <div key={week.week_number}>
                        <div className="flex items-center gap-2 mb-3">
                          <h5 className="font-semibold text-gray-900">
                            Week {week.week_number}: {week.theme}
                          </h5>
                          <span className="text-xs text-gray-500">
                            {week.tasks.filter(t => taskState[t.id] || t.completed).length}/{week.tasks.length} complete
                          </span>
                        </div>

                        <div className="space-y-2">
                          {week.tasks.map((task) => (
                            <div
                              key={task.id}
                              className={`p-4 rounded-xl border transition ${
                                taskState[task.id] || task.completed
                                  ? 'bg-green-50 border-green-200'
                                  : 'bg-gray-50 border-gray-200 hover:border-primary-300'
                              }`}
                            >
                              <div className="flex items-start gap-3">
                                <button
                                  onClick={() => handleTaskToggle(task.id)}
                                  className={`w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition ${
                                    taskState[task.id] || task.completed
                                      ? 'bg-green-500 border-green-500 text-white'
                                      : 'border-gray-300 hover:border-primary-500'
                                  }`}
                                >
                                  {(taskState[task.id] || task.completed) && (
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                    </svg>
                                  )}
                                </button>

                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 flex-wrap">
                                    <span className={`font-medium ${taskState[task.id] || task.completed ? 'line-through text-gray-400' : 'text-gray-900'}`}>
                                      {task.title}
                                    </span>
                                    <span className="text-xs text-gray-400">
                                      {task.time_estimate_minutes} min
                                    </span>
                                    <span className={`text-xs px-2 py-0.5 rounded ${difficultyColor[task.difficulty]}`}>
                                      {task.difficulty}
                                    </span>
                                    <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">
                                      {executorLabel[task.executor]}
                                    </span>
                                  </div>

                                  {task.description && (
                                    <p className="text-sm text-gray-500 mt-1">{task.description}</p>
                                  )}

                                  {/* Task CRB */}
                                  <div className="flex gap-4 mt-2 text-xs">
                                    <span className="text-gray-500">💰 {task.crb.cost}</span>
                                    <span className={riskColor[task.crb.risk]}>⚠️ {task.crb.risk}</span>
                                    <span className="text-green-600">📈 {task.crb.benefit}</span>
                                  </div>

                                  {task.tutorial_hint && (
                                    <p className="text-xs text-primary-600 mt-2">
                                      💡 {task.tutorial_hint}
                                    </p>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>

                        {/* Week checkpoint */}
                        <div className="mt-3 p-3 bg-primary-50 rounded-lg">
                          <p className="text-sm text-primary-700">
                            <span className="font-medium">✓ Checkpoint:</span> {week.checkpoint}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/report/PlaybookTab.tsx
git commit -m "feat: add PlaybookTab component with interactive task tracking"
```

---

### Task 3.2: Create Stack Tab Component

**Files:**
- Create: `frontend/src/components/report/StackTab.tsx`

**Step 1: Create the component**

```typescript
// frontend/src/components/report/StackTab.tsx
import { useState } from 'react'
import { motion } from 'framer-motion'

interface NodeCRB {
  cost: string
  risk: string
  risk_level: 'low' | 'medium' | 'high'
  benefit: string
  powers: string[]
}

interface ToolNode {
  id: string
  name: string
  category: string
  monthly_cost: number
  one_time_cost: number
  crb: NodeCRB
  is_existing: boolean
}

interface Connection {
  id: string
  from_node: string
  to_node: string
  data_flow: string
  integration_type: string
}

interface AutomationNode {
  id: string
  name: string
  trigger: string
  action: string
  tools_used: string[]
}

interface CostItem {
  name: string
  monthly_cost: number
  one_time_cost: number
}

interface CostBreakdown {
  items: CostItem[]
  total_monthly: number
  total_one_time: number
}

interface CostComparison {
  saas_route: CostBreakdown
  diy_route: CostBreakdown
  monthly_savings: number
  savings_percentage: number
  build_cost: number
  breakeven_months: number
}

interface SystemArchitecture {
  existing_tools: ToolNode[]
  ai_layer: ToolNode[]
  automations: AutomationNode[]
  connections: Connection[]
  cost_comparison: CostComparison
}

interface StackTabProps {
  architecture: SystemArchitecture
}

export default function StackTab({ architecture }: StackTabProps) {
  const [viewMode, setViewMode] = useState<'saas' | 'diy'>('diy')
  const [selectedNode, setSelectedNode] = useState<ToolNode | null>(null)

  if (!architecture) {
    return (
      <div className="bg-white rounded-2xl p-8 text-center">
        <p className="text-gray-500">System architecture not available.</p>
      </div>
    )
  }

  const { existing_tools, ai_layer, automations, cost_comparison } = architecture

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0
    }).format(value)
  }

  const riskColor = {
    low: 'text-green-600 bg-green-100',
    medium: 'text-yellow-600 bg-yellow-100',
    high: 'text-red-600 bg-red-100',
  }

  return (
    <div className="space-y-6">
      {/* Toggle */}
      <div className="flex justify-center">
        <div className="bg-gray-100 p-1 rounded-xl inline-flex">
          <button
            onClick={() => setViewMode('diy')}
            className={`px-6 py-2 rounded-lg font-medium transition ${
              viewMode === 'diy'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            DIY Route: {formatCurrency(cost_comparison.diy_route.total_monthly)}/mo
          </button>
          <button
            onClick={() => setViewMode('saas')}
            className={`px-6 py-2 rounded-lg font-medium transition ${
              viewMode === 'saas'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            SaaS Route: {formatCurrency(cost_comparison.saas_route.total_monthly)}/mo
          </button>
        </div>
      </div>

      {/* Architecture Diagram */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-white rounded-2xl p-6 shadow-sm"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-6 text-center">
          Your AI-Powered Business System
        </h3>

        <div className="grid grid-cols-3 gap-8">
          {/* Existing Tools Column */}
          <div>
            <h4 className="text-sm font-medium text-gray-500 mb-4 text-center">YOUR TOOLS</h4>
            <div className="space-y-3">
              {existing_tools.map((tool) => (
                <motion.div
                  key={tool.id}
                  whileHover={{ scale: 1.02 }}
                  onClick={() => setSelectedNode(tool)}
                  className="p-4 bg-gray-50 rounded-xl border-2 border-gray-200 cursor-pointer hover:border-primary-300 transition"
                >
                  <p className="font-medium text-gray-900">{tool.name}</p>
                  <p className="text-xs text-gray-500">Already owned</p>
                </motion.div>
              ))}
            </div>
          </div>

          {/* AI Layer Column */}
          <div>
            <h4 className="text-sm font-medium text-gray-500 mb-4 text-center">AI BRAIN</h4>
            <div className="space-y-3">
              {ai_layer.map((tool) => (
                <motion.div
                  key={tool.id}
                  whileHover={{ scale: 1.02 }}
                  onClick={() => setSelectedNode(tool)}
                  className="p-4 bg-purple-50 rounded-xl border-2 border-purple-200 cursor-pointer hover:border-purple-400 transition"
                >
                  <p className="font-medium text-purple-900">{tool.name}</p>
                  <p className="text-sm text-purple-600 font-medium">
                    {formatCurrency(tool.monthly_cost)}/mo
                  </p>
                </motion.div>
              ))}

              {/* Connection arrows */}
              <div className="flex justify-center py-2">
                <svg className="w-8 h-8 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
              </div>
            </div>
          </div>

          {/* Automations Column */}
          <div>
            <h4 className="text-sm font-medium text-gray-500 mb-4 text-center">AUTOMATIONS</h4>
            <div className="space-y-3">
              {automations.slice(0, 4).map((auto) => (
                <div
                  key={auto.id}
                  className="p-4 bg-green-50 rounded-xl border-2 border-green-200"
                >
                  <p className="font-medium text-green-900 text-sm">{auto.name}</p>
                  <p className="text-xs text-green-600 mt-1">{auto.trigger}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Selected Node Detail */}
      {selectedNode && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl p-6 shadow-sm"
        >
          <div className="flex items-start justify-between mb-4">
            <h4 className="text-lg font-semibold text-gray-900">{selectedNode.name}</h4>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 bg-gray-50 rounded-xl">
              <p className="text-xs text-gray-500 mb-1">COST</p>
              <p className="font-medium text-gray-900">{selectedNode.crb.cost}</p>
            </div>
            <div className={`p-4 rounded-xl ${riskColor[selectedNode.crb.risk_level]}`}>
              <p className="text-xs opacity-75 mb-1">RISK</p>
              <p className="font-medium">{selectedNode.crb.risk}</p>
            </div>
            <div className="p-4 bg-green-50 rounded-xl">
              <p className="text-xs text-green-600 mb-1">BENEFIT</p>
              <p className="font-medium text-green-800">{selectedNode.crb.benefit}</p>
            </div>
          </div>

          {selectedNode.crb.powers.length > 0 && (
            <div className="mt-4">
              <p className="text-sm text-gray-500 mb-2">Powers these automations:</p>
              <div className="flex flex-wrap gap-2">
                {selectedNode.crb.powers.map((power, i) => (
                  <span key={i} className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">
                    {power}
                  </span>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* Cost Comparison */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-2xl p-6 shadow-sm"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Cost Comparison</h3>

        <div className="grid grid-cols-3 gap-6">
          <div className="p-4 bg-gray-50 rounded-xl">
            <p className="text-sm text-gray-500 mb-1">SaaS Stack</p>
            <p className="text-2xl font-bold text-gray-900">
              {formatCurrency(cost_comparison.saas_route.total_monthly)}
              <span className="text-sm font-normal text-gray-500">/mo</span>
            </p>
            <div className="mt-3 space-y-1">
              {cost_comparison.saas_route.items.map((item, i) => (
                <div key={i} className="flex justify-between text-sm">
                  <span className="text-gray-600">{item.name}</span>
                  <span className="text-gray-900">{formatCurrency(item.monthly_cost)}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="p-4 bg-primary-50 rounded-xl border-2 border-primary-200">
            <p className="text-sm text-primary-600 mb-1">DIY Stack</p>
            <p className="text-2xl font-bold text-primary-700">
              {formatCurrency(cost_comparison.diy_route.total_monthly)}
              <span className="text-sm font-normal text-primary-500">/mo</span>
            </p>
            <p className="text-sm text-primary-600 mt-1">
              + {formatCurrency(cost_comparison.build_cost)} build cost
            </p>
            <div className="mt-3 space-y-1">
              {cost_comparison.diy_route.items.map((item, i) => (
                <div key={i} className="flex justify-between text-sm">
                  <span className="text-gray-600">{item.name}</span>
                  <span className="text-gray-900">{formatCurrency(item.monthly_cost)}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="p-4 bg-green-50 rounded-xl">
            <p className="text-sm text-green-600 mb-1">You Save</p>
            <p className="text-2xl font-bold text-green-700">
              {formatCurrency(cost_comparison.monthly_savings)}
              <span className="text-sm font-normal text-green-500">/mo</span>
            </p>
            <p className="text-lg font-bold text-green-600 mt-1">
              ({Math.round(cost_comparison.savings_percentage)}%)
            </p>
            <p className="text-sm text-green-600 mt-2">
              Breakeven: {cost_comparison.breakeven_months} months
            </p>
          </div>
        </div>
      </motion.div>

      {/* Actions */}
      <div className="flex gap-4">
        <button className="flex-1 px-6 py-3 bg-white border border-gray-200 rounded-xl font-medium text-gray-700 hover:bg-gray-50 transition flex items-center justify-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Download Architecture PDF
        </button>
        <button className="flex-1 px-6 py-3 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition flex items-center justify-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
          </svg>
          Share with Developer
        </button>
      </div>
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/report/StackTab.tsx
git commit -m "feat: add StackTab component with architecture visualization"
```

---

### Task 3.3: Create ROI Calculator Component

**Files:**
- Create: `frontend/src/components/report/ROICalculator.tsx`

(Similar detailed implementation - create interactive slider-based calculator)

---

### Task 3.4: Create Industry Insights Component

**Files:**
- Create: `frontend/src/components/report/InsightsTab.tsx`

(Similar detailed implementation - create adoption stats and opportunity map display)

---

### Task 3.5: Update ReportViewer with New Tabs

**Files:**
- Modify: `frontend/src/pages/ReportViewer.tsx`

**Step 1: Import new components**

Add imports:

```typescript
import PlaybookTab from '../components/report/PlaybookTab'
import StackTab from '../components/report/StackTab'
import ROICalculator from '../components/report/ROICalculator'
import InsightsTab from '../components/report/InsightsTab'
```

**Step 2: Update Report interface**

Add to interface:

```typescript
interface Report {
  // ... existing fields
  playbooks?: Playbook[]
  system_architecture?: SystemArchitecture
  industry_insights?: IndustryInsights
}
```

**Step 3: Update tabs array**

```typescript
const tabs = [
  { key: 'summary' as const, label: 'Summary' },
  { key: 'findings' as const, label: `Findings (${findings?.length || 0})` },
  { key: 'recommendations' as const, label: `Recommendations (${recommendations?.length || 0})` },
  { key: 'playbook' as const, label: 'Playbook' },
  { key: 'stack' as const, label: 'Stack' },
  { key: 'roi' as const, label: 'ROI Calculator' },
  { key: 'insights' as const, label: 'Industry' },
  { key: 'roadmap' as const, label: 'Roadmap' }
]
```

**Step 4: Add tab content**

Add new tab content in AnimatePresence:

```typescript
{activeTab === 'playbook' && report.playbooks && (
  <PlaybookTab playbooks={report.playbooks} />
)}

{activeTab === 'stack' && report.system_architecture && (
  <StackTab architecture={report.system_architecture} />
)}

{activeTab === 'roi' && (
  <ROICalculator
    recommendations={recommendations}
    valueSummary={value_summary}
  />
)}

{activeTab === 'insights' && report.industry_insights && (
  <InsightsTab insights={report.industry_insights} />
)}
```

**Step 5: Commit**

```bash
git add frontend/src/pages/ReportViewer.tsx
git commit -m "feat: integrate new report tabs - playbook, stack, ROI, insights"
```

---

## Phase 4: API Endpoints for Interactive Features

### Task 4.1: Add Playbook Progress Endpoints

**Files:**
- Create: `backend/src/routes/playbook.py`
- Modify: `backend/src/main.py`

(Add endpoints for tracking task completion, saving ROI scenarios)

---

## Phase 5: Model Freshness System

### Task 5.1: Create Model Freshness Job

**Files:**
- Create: `backend/src/jobs/model_freshness.py`

(Add weekly scraping job for model prices/benchmarks)

---

## Execution Checklist

- [ ] Phase 1: Backend models and generators (Tasks 1.1-1.8)
- [ ] Phase 2: Report service integration (Task 2.1)
- [ ] Phase 3: Frontend components (Tasks 3.1-3.5)
- [ ] Phase 4: API endpoints (Task 4.1)
- [ ] Phase 5: Model freshness (Task 5.1)
- [ ] Run full integration test
- [ ] Deploy to staging

---

**Plan complete and saved to `docs/plans/2025-12-20-enhanced-report-implementation.md`.**

**Two execution options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
