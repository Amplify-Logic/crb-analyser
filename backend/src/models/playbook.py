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
