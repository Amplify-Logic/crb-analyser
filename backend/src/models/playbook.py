# backend/src/models/playbook.py
"""
Playbook models for personalized implementation guides.

Enhanced with:
- Implementation steps and success criteria
- Common pitfalls to avoid
- Resources (docs, videos, tools)
- Task dependencies for critical path
- Validation for time estimates, dependencies, and consistency
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List, Literal, Set, Dict
from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)

# Constants for validation
MIN_TASK_MINUTES = 5
MAX_TASK_MINUTES = 480  # 8 hours - tasks longer than this should be broken down
WARN_TASK_MINUTES = 240  # 4 hours - warn but allow


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


class TaskResource(BaseModel):
    """A resource linked to a task."""
    title: str
    url: Optional[str] = None
    type: Literal["doc", "video", "tool"] = "doc"


class PlaybookTask(BaseModel):
    """A single actionable task within a week."""
    id: str
    title: str
    description: str = ""
    time_estimate_minutes: int = Field(
        default=30,
        ge=MIN_TASK_MINUTES,
        le=MAX_TASK_MINUTES,
        description=f"Task duration in minutes ({MIN_TASK_MINUTES}-{MAX_TASK_MINUTES})"
    )
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    executor: Literal["owner", "team", "hire_out"] = "owner"
    tools: List[str] = Field(default_factory=list)
    tutorial_hint: Optional[str] = None
    crb: TaskCRB
    completed: bool = False
    completed_at: Optional[datetime] = None

    # Enhanced fields for implementation guidance
    steps: List[str] = Field(
        default_factory=list,
        description="Step-by-step implementation instructions"
    )
    success_criteria: List[str] = Field(
        default_factory=list,
        description="How to know when this task is truly complete"
    )
    common_pitfalls: List[str] = Field(
        default_factory=list,
        description="Common mistakes to avoid"
    )
    resources: List[TaskResource] = Field(
        default_factory=list,
        description="Links to helpful docs, videos, or tools"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="IDs of tasks that must be completed before this one"
    )

    @field_validator('time_estimate_minutes', mode='after')
    @classmethod
    def warn_long_tasks(cls, v: int) -> int:
        """Warn about tasks that may need to be broken down."""
        if v > WARN_TASK_MINUTES:
            logger.warning(
                f"Task duration {v} minutes (>{WARN_TASK_MINUTES}) may need breakdown"
            )
        return v


class Week(BaseModel):
    """A week of tasks within a phase."""
    week_number: int = Field(..., ge=1)
    theme: str
    tasks: List[PlaybookTask]
    checkpoint: str = Field(..., description="What success looks like at end of week")

    def get_total_minutes(self) -> int:
        """Get total task minutes for this week."""
        return sum(t.time_estimate_minutes for t in self.tasks)

    def get_task_ids(self) -> Set[str]:
        """Get all task IDs in this week."""
        return {t.id for t in self.tasks}


class PhaseCRBSummary(BaseModel):
    """Aggregated CRB for an entire phase."""
    total_cost: str
    monthly_cost: str
    setup_hours: int = Field(..., ge=0)
    risks: List[str]
    benefits: List[str]
    crb_score: float = Field(..., ge=0, le=10)


class Phase(BaseModel):
    """A major phase of the playbook (3-5 per playbook)."""
    phase_number: int = Field(..., ge=1)
    title: str
    duration_weeks: int = Field(..., ge=1)
    outcome: str
    crb_summary: PhaseCRBSummary
    weeks: List[Week]

    def get_total_minutes(self) -> int:
        """Get total task minutes for this phase."""
        return sum(w.get_total_minutes() for w in self.weeks)

    def get_task_ids(self) -> Set[str]:
        """Get all task IDs in this phase."""
        ids: Set[str] = set()
        for week in self.weeks:
            ids.update(week.get_task_ids())
        return ids

    @model_validator(mode='after')
    def validate_week_count(self) -> 'Phase':
        """Validate that week count matches duration_weeks."""
        if len(self.weeks) != self.duration_weeks:
            logger.warning(
                f"Phase '{self.title}' has {len(self.weeks)} weeks "
                f"but duration_weeks={self.duration_weeks}"
            )
        return self


class PersonalizationContext(BaseModel):
    """Context derived from quiz answers for personalization."""
    team_size: Literal["solo", "small", "medium", "large"] = "solo"
    technical_level: int = Field(3, ge=1, le=5)
    budget_monthly: int = Field(500, ge=0)
    existing_tools: List[str] = Field(default_factory=list)
    primary_pain_point: str = ""
    industry: str = "general"
    urgency: Literal["asap", "normal", "flexible"] = "normal"


class ImmediateFirstStep(BaseModel):
    """The ONE thing to do before reading further - creates momentum."""
    action: str = Field(..., description="What to do, e.g., 'Create a Calendly account'")
    url: Optional[str] = Field(None, description="Direct URL to start")
    time_minutes: int = Field(15, ge=1, le=60, description="Time to complete (1-60 min)")
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
    total_weeks: int = Field(..., ge=1)
    immediate_first_step: Optional[ImmediateFirstStep] = None
    phases: List[Phase]
    personalization_context: PersonalizationContext
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def get_all_task_ids(self) -> Set[str]:
        """Get all task IDs in the playbook."""
        ids: Set[str] = set()
        for phase in self.phases:
            ids.update(phase.get_task_ids())
        return ids

    def get_all_tasks(self) -> List[PlaybookTask]:
        """Get all tasks in the playbook."""
        tasks: List[PlaybookTask] = []
        for phase in self.phases:
            for week in phase.weeks:
                tasks.extend(week.tasks)
        return tasks

    def build_dependency_graph(self) -> Dict[str, List[str]]:
        """Build a graph of task dependencies."""
        graph: Dict[str, List[str]] = {}
        for task in self.get_all_tasks():
            graph[task.id] = task.dependencies
        return graph

    def _detect_cycle(self, graph: Dict[str, List[str]]) -> Optional[List[str]]:
        """
        Detect cycles in dependency graph using DFS.
        Returns the cycle path if found, None otherwise.
        """
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []

        def dfs(node: str) -> Optional[List[str]]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    result = dfs(neighbor)
                    if result:
                        return result
                elif neighbor in rec_stack:
                    # Found cycle - return path from cycle start
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]

            path.pop()
            rec_stack.remove(node)
            return None

        for node in graph:
            if node not in visited:
                cycle = dfs(node)
                if cycle:
                    return cycle

        return None

    @model_validator(mode='after')
    def validate_playbook(self) -> 'Playbook':
        """Validate playbook consistency."""
        all_task_ids = self.get_all_task_ids()

        # Check for duplicate task IDs
        all_tasks = self.get_all_tasks()
        seen_ids: Set[str] = set()
        for task in all_tasks:
            if task.id in seen_ids:
                raise ValueError(f"Duplicate task ID: {task.id}")
            seen_ids.add(task.id)

        # Validate all dependency references exist
        invalid_deps: List[str] = []
        for task in all_tasks:
            for dep_id in task.dependencies:
                if dep_id not in all_task_ids:
                    invalid_deps.append(f"{task.id} -> {dep_id}")

        if invalid_deps:
            raise ValueError(
                f"Invalid dependency references: {', '.join(invalid_deps)}"
            )

        # Check for circular dependencies
        graph = self.build_dependency_graph()
        cycle = self._detect_cycle(graph)
        if cycle:
            raise ValueError(
                f"Circular dependency detected: {' -> '.join(cycle)}"
            )

        # Validate total_weeks matches phase durations
        phase_weeks = sum(p.duration_weeks for p in self.phases)
        if phase_weeks != self.total_weeks:
            logger.warning(
                f"Playbook total_weeks={self.total_weeks} but "
                f"sum of phase durations={phase_weeks}"
            )

        # Validate executor assignments for solo teams
        if self.personalization_context.team_size == "solo":
            team_tasks = [
                t.id for t in all_tasks
                if t.executor == "team"
            ]
            if team_tasks:
                logger.warning(
                    f"Solo team has {len(team_tasks)} tasks assigned to 'team': "
                    f"{team_tasks[:3]}{'...' if len(team_tasks) > 3 else ''}"
                )

        return self


class PlaybookProgress(BaseModel):
    """Track user progress through playbook."""
    report_id: str
    playbook_id: str
    tasks_completed: int = Field(0, ge=0)
    tasks_total: int = Field(0, ge=0)
    current_phase: int = Field(1, ge=1)
    current_week: int = Field(1, ge=1)
    started_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None


# =============================================================================
# VALIDATION UTILITIES
# =============================================================================

class PlaybookValidationResult(BaseModel):
    """Result of playbook validation."""
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


def validate_playbook_data(data: dict) -> PlaybookValidationResult:
    """
    Validate playbook data before creating a Playbook model.
    Returns validation result with errors and warnings.
    """
    errors: List[str] = []
    warnings: List[str] = []

    # Collect all task IDs and check for issues
    task_ids: Set[str] = set()
    tasks_by_id: Dict[str, dict] = {}

    phases = data.get("phases", [])
    if not phases:
        errors.append("Playbook has no phases")

    for pi, phase in enumerate(phases):
        phase_num = phase.get("phase_number", pi + 1)

        weeks = phase.get("weeks", [])
        if not weeks:
            warnings.append(f"Phase {phase_num} has no weeks")

        for wi, week in enumerate(weeks):
            week_num = week.get("week_number", wi + 1)

            tasks = week.get("tasks", [])
            if not tasks:
                warnings.append(f"Phase {phase_num} Week {week_num} has no tasks")

            for task in tasks:
                task_id = task.get("id", "")
                if not task_id:
                    errors.append(f"Task in Phase {phase_num} Week {week_num} has no ID")
                    continue

                if task_id in task_ids:
                    errors.append(f"Duplicate task ID: {task_id}")
                else:
                    task_ids.add(task_id)
                    tasks_by_id[task_id] = task

                # Check time estimate
                time_est = task.get("time_estimate_minutes", 30)
                if time_est < MIN_TASK_MINUTES:
                    errors.append(
                        f"Task {task_id} has invalid time: {time_est} < {MIN_TASK_MINUTES} min"
                    )
                elif time_est > MAX_TASK_MINUTES:
                    errors.append(
                        f"Task {task_id} has invalid time: {time_est} > {MAX_TASK_MINUTES} min"
                    )
                elif time_est > WARN_TASK_MINUTES:
                    warnings.append(
                        f"Task {task_id} is {time_est} min - consider breaking down"
                    )

    # Validate dependencies
    for task_id, task in tasks_by_id.items():
        deps = task.get("dependencies", [])
        for dep_id in deps:
            if dep_id not in task_ids:
                errors.append(f"Task {task_id} depends on non-existent task: {dep_id}")
            elif dep_id == task_id:
                errors.append(f"Task {task_id} depends on itself")

    # Check for cycles
    if not errors:  # Only check cycles if no other errors
        graph = {tid: t.get("dependencies", []) for tid, t in tasks_by_id.items()}
        cycle = _detect_cycle_in_graph(graph)
        if cycle:
            errors.append(f"Circular dependency: {' -> '.join(cycle)}")

    return PlaybookValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def _detect_cycle_in_graph(graph: Dict[str, List[str]]) -> Optional[List[str]]:
    """Detect cycles in a dependency graph."""
    visited: Set[str] = set()
    rec_stack: Set[str] = set()
    path: List[str] = []

    def dfs(node: str) -> Optional[List[str]]:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            if neighbor not in graph:
                continue  # Skip invalid references (handled elsewhere)
            if neighbor not in visited:
                result = dfs(neighbor)
                if result:
                    return result
            elif neighbor in rec_stack:
                cycle_start = path.index(neighbor)
                return path[cycle_start:] + [neighbor]

        path.pop()
        rec_stack.remove(node)
        return None

    for node in graph:
        if node not in visited:
            cycle = dfs(node)
            if cycle:
                return cycle

    return None
