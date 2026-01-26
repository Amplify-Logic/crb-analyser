"""
Tests for Playbook models and validation.

Tests cover:
- Task time estimate bounds
- Dependency validation (references to existing tasks)
- Circular dependency detection
- Phase/week consistency
- Executor assignment validation for team size
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.playbook import (
    PlaybookTask,
    TaskCRB,
    Week,
    Phase,
    PhaseCRBSummary,
    Playbook,
    PersonalizationContext,
    ImmediateFirstStep,
    PlaybookValidationResult,
    validate_playbook_data,
    MIN_TASK_MINUTES,
    MAX_TASK_MINUTES,
    WARN_TASK_MINUTES,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_crb():
    """Sample CRB for tasks."""
    return TaskCRB(
        cost="€0 (free tier)",
        risk="low",
        benefit="Saves 2 hrs/week"
    )


@pytest.fixture
def sample_task(sample_crb):
    """Sample valid task."""
    return PlaybookTask(
        id="p1-w1-t1",
        title="Sign up for Calendly",
        description="Create account",
        time_estimate_minutes=30,
        difficulty="easy",
        executor="owner",
        tools=["Calendly"],
        crb=sample_crb,
        dependencies=[],
    )


@pytest.fixture
def sample_week(sample_task):
    """Sample week with one task."""
    return Week(
        week_number=1,
        theme="Foundation",
        tasks=[sample_task],
        checkpoint="Account created",
    )


@pytest.fixture
def sample_phase(sample_week):
    """Sample phase with one week."""
    return Phase(
        phase_number=1,
        title="Setup",
        duration_weeks=1,
        outcome="Basic setup complete",
        crb_summary=PhaseCRBSummary(
            total_cost="€0",
            monthly_cost="€0",
            setup_hours=2,
            risks=["Learning curve"],
            benefits=["2 hrs/week saved"],
            crb_score=8.0,
        ),
        weeks=[sample_week],
    )


@pytest.fixture
def sample_context():
    """Sample personalization context."""
    return PersonalizationContext(
        team_size="solo",
        technical_level=3,
        budget_monthly=500,
        existing_tools=["Google Calendar"],
        primary_pain_point="Manual scheduling",
        industry="dental",
        urgency="normal",
    )


# =============================================================================
# TASK TIME ESTIMATE TESTS
# =============================================================================

class TestTaskTimeEstimates:
    """Tests for task time estimate validation."""

    def test_valid_time_estimate(self, sample_crb):
        """Task with valid time estimate should pass."""
        task = PlaybookTask(
            id="t1",
            title="Test",
            time_estimate_minutes=60,
            crb=sample_crb,
        )
        assert task.time_estimate_minutes == 60

    def test_minimum_time_estimate(self, sample_crb):
        """Task with minimum time should pass."""
        task = PlaybookTask(
            id="t1",
            title="Test",
            time_estimate_minutes=MIN_TASK_MINUTES,
            crb=sample_crb,
        )
        assert task.time_estimate_minutes == MIN_TASK_MINUTES

    def test_maximum_time_estimate(self, sample_crb):
        """Task with maximum time should pass."""
        task = PlaybookTask(
            id="t1",
            title="Test",
            time_estimate_minutes=MAX_TASK_MINUTES,
            crb=sample_crb,
        )
        assert task.time_estimate_minutes == MAX_TASK_MINUTES

    def test_time_below_minimum_fails(self, sample_crb):
        """Task with time below minimum should fail."""
        with pytest.raises(ValidationError) as exc_info:
            PlaybookTask(
                id="t1",
                title="Test",
                time_estimate_minutes=MIN_TASK_MINUTES - 1,
                crb=sample_crb,
            )
        assert "time_estimate_minutes" in str(exc_info.value)

    def test_time_above_maximum_fails(self, sample_crb):
        """Task with time above maximum should fail."""
        with pytest.raises(ValidationError) as exc_info:
            PlaybookTask(
                id="t1",
                title="Test",
                time_estimate_minutes=MAX_TASK_MINUTES + 1,
                crb=sample_crb,
            )
        assert "time_estimate_minutes" in str(exc_info.value)

    def test_zero_time_fails(self, sample_crb):
        """Task with zero time should fail."""
        with pytest.raises(ValidationError):
            PlaybookTask(
                id="t1",
                title="Test",
                time_estimate_minutes=0,
                crb=sample_crb,
            )

    def test_negative_time_fails(self, sample_crb):
        """Task with negative time should fail."""
        with pytest.raises(ValidationError):
            PlaybookTask(
                id="t1",
                title="Test",
                time_estimate_minutes=-30,
                crb=sample_crb,
            )


# =============================================================================
# DEPENDENCY VALIDATION TESTS
# =============================================================================

class TestDependencyValidation:
    """Tests for dependency reference validation."""

    def test_valid_dependencies(self, sample_crb, sample_context):
        """Playbook with valid dependencies should pass."""
        task1 = PlaybookTask(
            id="p1-w1-t1",
            title="Sign up",
            crb=sample_crb,
            dependencies=[],
        )
        task2 = PlaybookTask(
            id="p1-w1-t2",
            title="Configure",
            crb=sample_crb,
            dependencies=["p1-w1-t1"],
        )
        week = Week(
            week_number=1,
            theme="Setup",
            tasks=[task1, task2],
            checkpoint="Done",
        )
        phase = Phase(
            phase_number=1,
            title="Phase 1",
            duration_weeks=1,
            outcome="Complete",
            crb_summary=PhaseCRBSummary(
                total_cost="€0",
                monthly_cost="€0",
                setup_hours=2,
                risks=[],
                benefits=[],
                crb_score=5.0,
            ),
            weeks=[week],
        )
        playbook = Playbook(
            id="pb-1",
            recommendation_id="rec-1",
            option_type="off_the_shelf",
            total_weeks=1,
            phases=[phase],
            personalization_context=sample_context,
        )
        assert playbook.id == "pb-1"

    def test_invalid_dependency_reference_fails(self, sample_crb, sample_context):
        """Playbook with invalid dependency reference should fail."""
        task1 = PlaybookTask(
            id="p1-w1-t1",
            title="Sign up",
            crb=sample_crb,
            dependencies=["nonexistent-task"],  # Invalid reference
        )
        week = Week(
            week_number=1,
            theme="Setup",
            tasks=[task1],
            checkpoint="Done",
        )
        phase = Phase(
            phase_number=1,
            title="Phase 1",
            duration_weeks=1,
            outcome="Complete",
            crb_summary=PhaseCRBSummary(
                total_cost="€0",
                monthly_cost="€0",
                setup_hours=2,
                risks=[],
                benefits=[],
                crb_score=5.0,
            ),
            weeks=[week],
        )
        with pytest.raises(ValidationError) as exc_info:
            Playbook(
                id="pb-1",
                recommendation_id="rec-1",
                option_type="off_the_shelf",
                total_weeks=1,
                phases=[phase],
                personalization_context=sample_context,
            )
        assert "Invalid dependency" in str(exc_info.value)

    def test_self_dependency_fails(self, sample_crb, sample_context):
        """Task depending on itself should fail."""
        task1 = PlaybookTask(
            id="p1-w1-t1",
            title="Sign up",
            crb=sample_crb,
            dependencies=["p1-w1-t1"],  # Self-reference
        )
        week = Week(
            week_number=1,
            theme="Setup",
            tasks=[task1],
            checkpoint="Done",
        )
        phase = Phase(
            phase_number=1,
            title="Phase 1",
            duration_weeks=1,
            outcome="Complete",
            crb_summary=PhaseCRBSummary(
                total_cost="€0",
                monthly_cost="€0",
                setup_hours=2,
                risks=[],
                benefits=[],
                crb_score=5.0,
            ),
            weeks=[week],
        )
        with pytest.raises(ValidationError) as exc_info:
            Playbook(
                id="pb-1",
                recommendation_id="rec-1",
                option_type="off_the_shelf",
                total_weeks=1,
                phases=[phase],
                personalization_context=sample_context,
            )
        assert "Invalid dependency" in str(exc_info.value) or "Circular" in str(exc_info.value)


# =============================================================================
# CIRCULAR DEPENDENCY TESTS
# =============================================================================

class TestCircularDependencies:
    """Tests for circular dependency detection."""

    def test_circular_dependency_two_tasks(self, sample_crb, sample_context):
        """Two tasks depending on each other should fail."""
        task1 = PlaybookTask(
            id="t1",
            title="Task 1",
            crb=sample_crb,
            dependencies=["t2"],  # Circular: t1 -> t2 -> t1
        )
        task2 = PlaybookTask(
            id="t2",
            title="Task 2",
            crb=sample_crb,
            dependencies=["t1"],
        )
        week = Week(
            week_number=1,
            theme="Setup",
            tasks=[task1, task2],
            checkpoint="Done",
        )
        phase = Phase(
            phase_number=1,
            title="Phase 1",
            duration_weeks=1,
            outcome="Complete",
            crb_summary=PhaseCRBSummary(
                total_cost="€0",
                monthly_cost="€0",
                setup_hours=2,
                risks=[],
                benefits=[],
                crb_score=5.0,
            ),
            weeks=[week],
        )
        with pytest.raises(ValidationError) as exc_info:
            Playbook(
                id="pb-1",
                recommendation_id="rec-1",
                option_type="off_the_shelf",
                total_weeks=1,
                phases=[phase],
                personalization_context=sample_context,
            )
        assert "Circular" in str(exc_info.value)

    def test_circular_dependency_three_tasks(self, sample_crb, sample_context):
        """Three tasks in a cycle should fail."""
        task1 = PlaybookTask(
            id="t1",
            title="Task 1",
            crb=sample_crb,
            dependencies=["t3"],  # Circular: t1 -> t3 -> t2 -> t1
        )
        task2 = PlaybookTask(
            id="t2",
            title="Task 2",
            crb=sample_crb,
            dependencies=["t1"],
        )
        task3 = PlaybookTask(
            id="t3",
            title="Task 3",
            crb=sample_crb,
            dependencies=["t2"],
        )
        week = Week(
            week_number=1,
            theme="Setup",
            tasks=[task1, task2, task3],
            checkpoint="Done",
        )
        phase = Phase(
            phase_number=1,
            title="Phase 1",
            duration_weeks=1,
            outcome="Complete",
            crb_summary=PhaseCRBSummary(
                total_cost="€0",
                monthly_cost="€0",
                setup_hours=2,
                risks=[],
                benefits=[],
                crb_score=5.0,
            ),
            weeks=[week],
        )
        with pytest.raises(ValidationError) as exc_info:
            Playbook(
                id="pb-1",
                recommendation_id="rec-1",
                option_type="off_the_shelf",
                total_weeks=1,
                phases=[phase],
                personalization_context=sample_context,
            )
        assert "Circular" in str(exc_info.value)

    def test_chain_dependency_no_cycle(self, sample_crb, sample_context):
        """Linear dependency chain should pass."""
        task1 = PlaybookTask(
            id="t1",
            title="Task 1",
            crb=sample_crb,
            dependencies=[],
        )
        task2 = PlaybookTask(
            id="t2",
            title="Task 2",
            crb=sample_crb,
            dependencies=["t1"],
        )
        task3 = PlaybookTask(
            id="t3",
            title="Task 3",
            crb=sample_crb,
            dependencies=["t2"],
        )
        week = Week(
            week_number=1,
            theme="Setup",
            tasks=[task1, task2, task3],
            checkpoint="Done",
        )
        phase = Phase(
            phase_number=1,
            title="Phase 1",
            duration_weeks=1,
            outcome="Complete",
            crb_summary=PhaseCRBSummary(
                total_cost="€0",
                monthly_cost="€0",
                setup_hours=2,
                risks=[],
                benefits=[],
                crb_score=5.0,
            ),
            weeks=[week],
        )
        playbook = Playbook(
            id="pb-1",
            recommendation_id="rec-1",
            option_type="off_the_shelf",
            total_weeks=1,
            phases=[phase],
            personalization_context=sample_context,
        )
        assert playbook.id == "pb-1"


# =============================================================================
# DUPLICATE TASK ID TESTS
# =============================================================================

class TestDuplicateTaskIds:
    """Tests for duplicate task ID detection."""

    def test_duplicate_task_id_fails(self, sample_crb, sample_context):
        """Duplicate task IDs should fail."""
        task1 = PlaybookTask(
            id="same-id",
            title="Task 1",
            crb=sample_crb,
            dependencies=[],
        )
        task2 = PlaybookTask(
            id="same-id",  # Duplicate!
            title="Task 2",
            crb=sample_crb,
            dependencies=[],
        )
        week = Week(
            week_number=1,
            theme="Setup",
            tasks=[task1, task2],
            checkpoint="Done",
        )
        phase = Phase(
            phase_number=1,
            title="Phase 1",
            duration_weeks=1,
            outcome="Complete",
            crb_summary=PhaseCRBSummary(
                total_cost="€0",
                monthly_cost="€0",
                setup_hours=2,
                risks=[],
                benefits=[],
                crb_score=5.0,
            ),
            weeks=[week],
        )
        with pytest.raises(ValidationError) as exc_info:
            Playbook(
                id="pb-1",
                recommendation_id="rec-1",
                option_type="off_the_shelf",
                total_weeks=1,
                phases=[phase],
                personalization_context=sample_context,
            )
        assert "Duplicate task ID" in str(exc_info.value)


# =============================================================================
# VALIDATE_PLAYBOOK_DATA FUNCTION TESTS
# =============================================================================

class TestValidatePlaybookData:
    """Tests for the validate_playbook_data utility function."""

    def test_valid_data(self):
        """Valid playbook data should pass."""
        data = {
            "phases": [
                {
                    "phase_number": 1,
                    "weeks": [
                        {
                            "week_number": 1,
                            "tasks": [
                                {
                                    "id": "t1",
                                    "time_estimate_minutes": 30,
                                    "dependencies": [],
                                },
                                {
                                    "id": "t2",
                                    "time_estimate_minutes": 45,
                                    "dependencies": ["t1"],
                                },
                            ],
                        }
                    ],
                }
            ]
        }
        result = validate_playbook_data(data)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_missing_phases(self):
        """Data with no phases should fail."""
        data = {"phases": []}
        result = validate_playbook_data(data)
        assert result.valid is False
        assert any("no phases" in e.lower() for e in result.errors)

    def test_invalid_time_too_low(self):
        """Task with time below minimum should fail."""
        data = {
            "phases": [
                {
                    "phase_number": 1,
                    "weeks": [
                        {
                            "week_number": 1,
                            "tasks": [
                                {
                                    "id": "t1",
                                    "time_estimate_minutes": 1,  # Too low
                                    "dependencies": [],
                                },
                            ],
                        }
                    ],
                }
            ]
        }
        result = validate_playbook_data(data)
        assert result.valid is False
        assert any("invalid time" in e.lower() for e in result.errors)

    def test_invalid_time_too_high(self):
        """Task with time above maximum should fail."""
        data = {
            "phases": [
                {
                    "phase_number": 1,
                    "weeks": [
                        {
                            "week_number": 1,
                            "tasks": [
                                {
                                    "id": "t1",
                                    "time_estimate_minutes": 1000,  # Too high
                                    "dependencies": [],
                                },
                            ],
                        }
                    ],
                }
            ]
        }
        result = validate_playbook_data(data)
        assert result.valid is False
        assert any("invalid time" in e.lower() for e in result.errors)

    def test_warning_for_long_task(self):
        """Task with long but valid time should generate warning."""
        data = {
            "phases": [
                {
                    "phase_number": 1,
                    "weeks": [
                        {
                            "week_number": 1,
                            "tasks": [
                                {
                                    "id": "t1",
                                    "time_estimate_minutes": WARN_TASK_MINUTES + 10,
                                    "dependencies": [],
                                },
                            ],
                        }
                    ],
                }
            ]
        }
        result = validate_playbook_data(data)
        assert result.valid is True
        assert any("breaking down" in w.lower() or "consider" in w.lower() for w in result.warnings)

    def test_duplicate_task_id(self):
        """Duplicate task IDs should fail."""
        data = {
            "phases": [
                {
                    "phase_number": 1,
                    "weeks": [
                        {
                            "week_number": 1,
                            "tasks": [
                                {"id": "t1", "dependencies": []},
                                {"id": "t1", "dependencies": []},  # Duplicate
                            ],
                        }
                    ],
                }
            ]
        }
        result = validate_playbook_data(data)
        assert result.valid is False
        assert any("duplicate" in e.lower() for e in result.errors)

    def test_invalid_dependency_reference(self):
        """Reference to non-existent task should fail."""
        data = {
            "phases": [
                {
                    "phase_number": 1,
                    "weeks": [
                        {
                            "week_number": 1,
                            "tasks": [
                                {
                                    "id": "t1",
                                    "dependencies": ["nonexistent"],
                                },
                            ],
                        }
                    ],
                }
            ]
        }
        result = validate_playbook_data(data)
        assert result.valid is False
        assert any("non-existent" in e.lower() for e in result.errors)

    def test_self_dependency(self):
        """Task depending on itself should fail."""
        data = {
            "phases": [
                {
                    "phase_number": 1,
                    "weeks": [
                        {
                            "week_number": 1,
                            "tasks": [
                                {
                                    "id": "t1",
                                    "dependencies": ["t1"],  # Self-reference
                                },
                            ],
                        }
                    ],
                }
            ]
        }
        result = validate_playbook_data(data)
        assert result.valid is False
        assert any("itself" in e.lower() for e in result.errors)

    def test_circular_dependency(self):
        """Circular dependencies should fail."""
        data = {
            "phases": [
                {
                    "phase_number": 1,
                    "weeks": [
                        {
                            "week_number": 1,
                            "tasks": [
                                {"id": "t1", "dependencies": ["t2"]},
                                {"id": "t2", "dependencies": ["t1"]},
                            ],
                        }
                    ],
                }
            ]
        }
        result = validate_playbook_data(data)
        assert result.valid is False
        assert any("circular" in e.lower() for e in result.errors)


# =============================================================================
# HELPER METHOD TESTS
# =============================================================================

class TestPlaybookHelperMethods:
    """Tests for Playbook helper methods."""

    def test_get_all_task_ids(self, sample_crb, sample_context):
        """get_all_task_ids should return all task IDs."""
        task1 = PlaybookTask(id="t1", title="T1", crb=sample_crb, dependencies=[])
        task2 = PlaybookTask(id="t2", title="T2", crb=sample_crb, dependencies=["t1"])
        task3 = PlaybookTask(id="t3", title="T3", crb=sample_crb, dependencies=["t1"])
        week1 = Week(week_number=1, theme="W1", tasks=[task1, task2], checkpoint="C")
        week2 = Week(week_number=2, theme="W2", tasks=[task3], checkpoint="C")
        phase = Phase(
            phase_number=1,
            title="P1",
            duration_weeks=2,
            outcome="O",
            crb_summary=PhaseCRBSummary(
                total_cost="€0",
                monthly_cost="€0",
                setup_hours=2,
                risks=[],
                benefits=[],
                crb_score=5.0,
            ),
            weeks=[week1, week2],
        )
        playbook = Playbook(
            id="pb-1",
            recommendation_id="rec-1",
            option_type="off_the_shelf",
            total_weeks=2,
            phases=[phase],
            personalization_context=sample_context,
        )
        assert playbook.get_all_task_ids() == {"t1", "t2", "t3"}

    def test_get_all_tasks(self, sample_crb, sample_context):
        """get_all_tasks should return all tasks."""
        task1 = PlaybookTask(id="t1", title="T1", crb=sample_crb, dependencies=[])
        task2 = PlaybookTask(id="t2", title="T2", crb=sample_crb, dependencies=["t1"])
        week = Week(week_number=1, theme="W1", tasks=[task1, task2], checkpoint="C")
        phase = Phase(
            phase_number=1,
            title="P1",
            duration_weeks=1,
            outcome="O",
            crb_summary=PhaseCRBSummary(
                total_cost="€0",
                monthly_cost="€0",
                setup_hours=2,
                risks=[],
                benefits=[],
                crb_score=5.0,
            ),
            weeks=[week],
        )
        playbook = Playbook(
            id="pb-1",
            recommendation_id="rec-1",
            option_type="off_the_shelf",
            total_weeks=1,
            phases=[phase],
            personalization_context=sample_context,
        )
        tasks = playbook.get_all_tasks()
        assert len(tasks) == 2
        assert tasks[0].id == "t1"
        assert tasks[1].id == "t2"

    def test_build_dependency_graph(self, sample_crb, sample_context):
        """build_dependency_graph should return correct graph."""
        task1 = PlaybookTask(id="t1", title="T1", crb=sample_crb, dependencies=[])
        task2 = PlaybookTask(id="t2", title="T2", crb=sample_crb, dependencies=["t1"])
        task3 = PlaybookTask(id="t3", title="T3", crb=sample_crb, dependencies=["t1", "t2"])
        week = Week(week_number=1, theme="W1", tasks=[task1, task2, task3], checkpoint="C")
        phase = Phase(
            phase_number=1,
            title="P1",
            duration_weeks=1,
            outcome="O",
            crb_summary=PhaseCRBSummary(
                total_cost="€0",
                monthly_cost="€0",
                setup_hours=2,
                risks=[],
                benefits=[],
                crb_score=5.0,
            ),
            weeks=[week],
        )
        playbook = Playbook(
            id="pb-1",
            recommendation_id="rec-1",
            option_type="off_the_shelf",
            total_weeks=1,
            phases=[phase],
            personalization_context=sample_context,
        )
        graph = playbook.build_dependency_graph()
        assert graph == {"t1": [], "t2": ["t1"], "t3": ["t1", "t2"]}


# =============================================================================
# CRB RISK VALIDATOR TESTS
# =============================================================================

class TestTaskCRBValidation:
    """Tests for TaskCRB risk level extraction."""

    def test_risk_low(self):
        """Low risk should be extracted."""
        crb = TaskCRB(cost="€0", risk="low", benefit="Test")
        assert crb.risk == "low"

    def test_risk_medium(self):
        """Medium risk should be extracted."""
        crb = TaskCRB(cost="€0", risk="medium", benefit="Test")
        assert crb.risk == "medium"

    def test_risk_high(self):
        """High risk should be extracted."""
        crb = TaskCRB(cost="€0", risk="high", benefit="Test")
        assert crb.risk == "high"

    def test_risk_with_description(self):
        """Risk with description should extract level."""
        crb = TaskCRB(cost="€0", risk="medium - pricing may change", benefit="Test")
        assert crb.risk == "medium"

    def test_risk_high_with_description(self):
        """High risk with description should extract level."""
        crb = TaskCRB(cost="€0", risk="high - critical path item", benefit="Test")
        assert crb.risk == "high"

    def test_risk_default_to_low(self):
        """Unknown risk should default to low."""
        crb = TaskCRB(cost="€0", risk="uncertain", benefit="Test")
        assert crb.risk == "low"


# =============================================================================
# IMMEDIATE FIRST STEP TESTS
# =============================================================================

class TestImmediateFirstStep:
    """Tests for ImmediateFirstStep validation."""

    def test_valid_first_step(self):
        """Valid first step should pass."""
        step = ImmediateFirstStep(
            action="Sign up for Calendly",
            url="https://calendly.com/signup",
            time_minutes=10,
            outcome="Booking link ready",
        )
        assert step.action == "Sign up for Calendly"

    def test_time_within_bounds(self):
        """Time should be between 1 and 60 minutes."""
        step = ImmediateFirstStep(
            action="Test",
            time_minutes=30,
            outcome="Done",
        )
        assert step.time_minutes == 30

    def test_time_too_high_fails(self):
        """Time above 60 should fail."""
        with pytest.raises(ValidationError):
            ImmediateFirstStep(
                action="Test",
                time_minutes=120,  # > 60
                outcome="Done",
            )

    def test_time_zero_fails(self):
        """Time of zero should fail."""
        with pytest.raises(ValidationError):
            ImmediateFirstStep(
                action="Test",
                time_minutes=0,
                outcome="Done",
            )
