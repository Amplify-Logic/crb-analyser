# Personalized Workshop Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the premium personalized 90-minute workshop with confirmation, deep-dives, and milestone summaries.

**Architecture:** Three-phase workshop (Confirm → Deep-Dive → Synthesis) with 4 new backend skills, new API routes, and a complete frontend page with phase components. Uses existing skills infrastructure and knowledge base.

**Tech Stack:** FastAPI, Python 3.12, React 18, TypeScript, Framer Motion, Tailwind CSS, Anthropic Claude API

**Design Doc:** `docs/plans/2026-01-03-personalized-workshop-design.md`

---

## Implementation Batches

| Batch | Focus | Estimated Tasks |
|-------|-------|-----------------|
| 1 | Data Models & Database | 8 tasks |
| 2 | Backend Skills | 16 tasks |
| 3 | Backend Routes | 12 tasks |
| 4 | Frontend Phase 1 (Confirmation) | 14 tasks |
| 5 | Frontend Phase 2 (Deep-Dive) | 16 tasks |
| 6 | Frontend Milestone Summaries | 10 tasks |
| 7 | Frontend Phase 3 (Synthesis) | 10 tasks |
| 8 | Integration & Polish | 8 tasks |

**Total:** ~94 tasks

---

# Batch 1: Data Models & Database

## Task 1.1: Create Workshop Data Models

**Files:**
- Create: `backend/src/models/workshop.py`
- Test: `backend/tests/test_workshop_models.py`

**Step 1: Write the test file**

```python
# backend/tests/test_workshop_models.py
"""Tests for workshop data models."""

import pytest
from src.models.workshop import (
    WorkshopPhase,
    AccuracyRating,
    DetectedSignals,
    ConfirmationData,
    DeepDiveData,
    MilestoneData,
    WorkshopData,
    WorkshopConfidence,
    DepthDimensions,
)


class TestDetectedSignals:
    """Test adaptive signal detection model."""

    def test_default_signals(self):
        signals = DetectedSignals()
        assert signals.technical is False
        assert signals.budget_ready is False
        assert signals.decision_maker is False

    def test_from_quiz_data_technical_role(self):
        signals = DetectedSignals.from_quiz_data(
            role="CTO",
            company_size="11-50",
            budget_answer="15000-50000",
            quiz_answers={}
        )
        assert signals.technical is True
        assert signals.budget_ready is True

    def test_from_quiz_data_non_technical(self):
        signals = DetectedSignals.from_quiz_data(
            role="CEO",
            company_size="1-10",
            budget_answer="2000-5000",
            quiz_answers={}
        )
        assert signals.technical is False
        assert signals.decision_maker is True


class TestWorkshopConfidence:
    """Test enhanced confidence framework."""

    def test_calculate_overall_score(self):
        conf = WorkshopConfidence(
            topics={
                "current_challenges": {"coverage": 25, "depth": 20, "specificity": 18, "actionability": 15},
                "business_goals": {"coverage": 20, "depth": 15, "specificity": 10, "actionability": 10},
                "team_operations": {"coverage": 15, "depth": 10, "specificity": 8, "actionability": 5},
                "technology": {"coverage": 20, "depth": 15, "specificity": 12, "actionability": 10},
                "budget_timeline": {"coverage": 10, "depth": 5, "specificity": 5, "actionability": 5},
            },
            depth_dimensions=DepthDimensions(
                integration_depth=0.7,
                cost_quantification=0.8,
                stakeholder_mapping=0.6,
                implementation_readiness=0.5,
            )
        )
        score = conf.calculate_overall()
        assert 0.5 <= score <= 0.8  # Expected range given inputs

    def test_is_ready_for_report(self):
        conf = WorkshopConfidence(
            topics={
                "current_challenges": {"coverage": 25, "depth": 22, "specificity": 20, "actionability": 18},
                "business_goals": {"coverage": 22, "depth": 18, "specificity": 15, "actionability": 12},
                "team_operations": {"coverage": 18, "depth": 15, "specificity": 12, "actionability": 10},
                "technology": {"coverage": 20, "depth": 18, "specificity": 15, "actionability": 12},
                "budget_timeline": {"coverage": 15, "depth": 10, "specificity": 8, "actionability": 8},
            },
            depth_dimensions=DepthDimensions(
                integration_depth=0.8,
                cost_quantification=0.9,
                stakeholder_mapping=0.7,
                implementation_readiness=0.7,
            ),
            quality_indicators={
                "pain_points_extracted": 3,
                "quantifiable_impacts": 4,
            }
        )
        assert conf.is_ready_for_report() is True
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/test_workshop_models.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.models.workshop'"

**Step 3: Write the implementation**

```python
# backend/src/models/workshop.py
"""
Workshop Data Models

Data structures for the personalized 90-minute workshop experience.
Includes confidence framework, adaptive signals, and session data.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class WorkshopPhase(Enum):
    """Current phase of the workshop."""
    CONFIRMATION = "confirmation"
    DEEPDIVE = "deepdive"
    SYNTHESIS = "synthesis"
    COMPLETE = "complete"


class AccuracyRating(Enum):
    """User rating for confirmation items."""
    ACCURATE = "accurate"
    INACCURATE = "inaccurate"
    EDITED = "edited"


@dataclass
class DetectedSignals:
    """Adaptive signals detected from quiz/profile data."""
    technical: bool = False
    budget_ready: bool = False
    decision_maker: bool = False

    @classmethod
    def from_quiz_data(
        cls,
        role: Optional[str] = None,
        company_size: Optional[str] = None,
        budget_answer: Optional[str] = None,
        quiz_answers: Optional[Dict[str, Any]] = None,
    ) -> "DetectedSignals":
        """Detect signals from quiz and profile data."""
        quiz_answers = quiz_answers or {}

        # Technical detection
        technical_roles = ["cto", "developer", "engineer", "it", "tech", "devops"]
        technical = False
        if role:
            technical = any(t in role.lower() for t in technical_roles)
        if not technical and quiz_answers:
            tech_keywords = ["api", "integration", "webhook", "built", "code"]
            answers_text = str(quiz_answers).lower()
            technical = any(k in answers_text for k in tech_keywords)

        # Budget ready detection
        budget_ready = False
        high_budgets = ["15000-50000", "50000+", "50000-100000", "100000+"]
        if budget_answer:
            budget_ready = budget_answer in high_budgets

        # Decision maker detection
        decision_maker = False
        dm_roles = ["ceo", "owner", "founder", "director", "president", "partner"]
        if role:
            decision_maker = any(d in role.lower() for d in dm_roles)
        if not decision_maker and company_size:
            small_sizes = ["1-10", "1-5", "solo"]
            decision_maker = company_size in small_sizes

        return cls(
            technical=technical,
            budget_ready=budget_ready,
            decision_maker=decision_maker,
        )

    def to_dict(self) -> Dict[str, bool]:
        return {
            "technical": self.technical,
            "budget_ready": self.budget_ready,
            "decision_maker": self.decision_maker,
        }


@dataclass
class ConfirmationCorrection:
    """A correction made during confirmation phase."""
    field: str
    original: str
    corrected: str
    corrected_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "original": self.original,
            "corrected": self.corrected,
            "corrected_at": self.corrected_at.isoformat(),
        }


@dataclass
class ConfirmationData:
    """Data from Phase 1: Confirmation."""
    ratings: Dict[str, AccuracyRating] = field(default_factory=dict)
    corrections: List[ConfirmationCorrection] = field(default_factory=list)
    priority_order: List[str] = field(default_factory=list)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ratings": {k: v.value for k, v in self.ratings.items()},
            "corrections": [c.to_dict() for c in self.corrections],
            "priority_order": self.priority_order,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class DeepDiveFinding:
    """A finding generated during deep-dive."""
    title: str
    current_cost: float
    potential_savings: float
    confidence: float
    summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "current_cost": self.current_cost,
            "potential_savings": self.potential_savings,
            "confidence": self.confidence,
            "summary": self.summary,
        }


@dataclass
class DeepDiveData:
    """Data from a single deep-dive conversation."""
    pain_point_id: str
    pain_point_label: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    transcript: List[Dict[str, str]] = field(default_factory=list)
    finding: Optional[DeepDiveFinding] = None
    user_feedback: Optional[str] = None  # "looks_good" | "needs_edit"
    user_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pain_point_id": self.pain_point_id,
            "pain_point_label": self.pain_point_label,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "transcript": self.transcript,
            "finding": self.finding.to_dict() if self.finding else None,
            "user_feedback": self.user_feedback,
            "user_notes": self.user_notes,
        }


@dataclass
class MilestoneData:
    """Data from a milestone summary."""
    pain_point_id: str
    finding: Dict[str, Any]
    roi: Dict[str, Any]
    vendors: List[Dict[str, Any]]
    user_feedback: str
    user_notes: Optional[str] = None
    shown_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pain_point_id": self.pain_point_id,
            "finding": self.finding,
            "roi": self.roi,
            "vendors": self.vendors,
            "user_feedback": self.user_feedback,
            "user_notes": self.user_notes,
            "shown_at": self.shown_at.isoformat(),
        }


@dataclass
class FinalAnswers:
    """Final answers from Phase 3."""
    stakeholders: List[str] = field(default_factory=list)
    timeline: Optional[str] = None
    additions: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stakeholders": self.stakeholders,
            "timeline": self.timeline,
            "additions": self.additions,
        }


@dataclass
class WorkshopData:
    """Complete workshop session data."""
    phase: WorkshopPhase = WorkshopPhase.CONFIRMATION
    detected_signals: DetectedSignals = field(default_factory=DetectedSignals)
    confirmation: ConfirmationData = field(default_factory=ConfirmationData)
    deep_dives: List[DeepDiveData] = field(default_factory=list)
    milestones: List[MilestoneData] = field(default_factory=list)
    final_answers: Optional[FinalAnswers] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "detected_signals": self.detected_signals.to_dict(),
            "confirmation": self.confirmation.to_dict(),
            "deep_dives": [d.to_dict() for d in self.deep_dives],
            "milestones": [m.to_dict() for m in self.milestones],
            "final_answers": self.final_answers.to_dict() if self.final_answers else None,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_minutes": self.duration_minutes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkshopData":
        """Reconstruct WorkshopData from dict (e.g., from database)."""
        if not data:
            return cls()

        # Parse detected signals
        signals_data = data.get("detected_signals", {})
        detected_signals = DetectedSignals(
            technical=signals_data.get("technical", False),
            budget_ready=signals_data.get("budget_ready", False),
            decision_maker=signals_data.get("decision_maker", False),
        )

        # Parse phase
        phase_str = data.get("phase", "confirmation")
        phase = WorkshopPhase(phase_str)

        return cls(
            phase=phase,
            detected_signals=detected_signals,
            # Note: Full parsing of nested objects would go here
            # Simplified for initial implementation
        )


# =============================================================================
# Enhanced Confidence Framework
# =============================================================================

@dataclass
class DepthDimensions:
    """Depth dimensions tracked during workshop."""
    integration_depth: float = 0.0
    cost_quantification: float = 0.0
    stakeholder_mapping: float = 0.0
    implementation_readiness: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "integration_depth": self.integration_depth,
            "cost_quantification": self.cost_quantification,
            "stakeholder_mapping": self.stakeholder_mapping,
            "implementation_readiness": self.implementation_readiness,
        }

    def average(self) -> float:
        values = [
            self.integration_depth,
            self.cost_quantification,
            self.stakeholder_mapping,
            self.implementation_readiness,
        ]
        return sum(values) / len(values)


# Topic weights for overall score calculation
WORKSHOP_TOPIC_WEIGHTS = {
    "current_challenges": 1.5,
    "business_goals": 1.2,
    "team_operations": 1.0,
    "technology": 1.0,
    "budget_timeline": 0.8,
}


@dataclass
class WorkshopConfidence:
    """Enhanced confidence framework for workshop."""
    topics: Dict[str, Dict[str, int]] = field(default_factory=dict)
    depth_dimensions: DepthDimensions = field(default_factory=DepthDimensions)
    quality_indicators: Dict[str, Any] = field(default_factory=dict)
    overall_score: float = 0.0
    level: str = "insufficient"

    def calculate_topic_confidence(self, topic_id: str) -> float:
        """Calculate confidence for a single topic (0.0-1.0)."""
        if topic_id not in self.topics:
            return 0.0
        scores = self.topics[topic_id]
        total = sum(scores.values())
        return total / 100.0

    def calculate_overall(self) -> float:
        """Calculate weighted overall confidence score."""
        if not self.topics:
            return 0.0

        total_weight = sum(WORKSHOP_TOPIC_WEIGHTS.values())
        weighted_sum = 0.0

        for topic_id, weight in WORKSHOP_TOPIC_WEIGHTS.items():
            topic_conf = self.calculate_topic_confidence(topic_id)
            weighted_sum += topic_conf * weight

        base_score = weighted_sum / total_weight

        # Apply depth dimension boost (up to 15% bonus)
        depth_bonus = self.depth_dimensions.average() * 0.15

        # Apply quality indicator boost (up to 10% bonus)
        quality_bonus = 0.0
        pain_points = self.quality_indicators.get("pain_points_extracted", 0)
        if pain_points >= 3:
            quality_bonus += 0.05
        impacts = self.quality_indicators.get("quantifiable_impacts", 0)
        if impacts >= 2:
            quality_bonus += 0.05

        self.overall_score = min(1.0, base_score + depth_bonus + quality_bonus)

        # Set level
        if self.overall_score >= 0.8:
            self.level = "excellent"
        elif self.overall_score >= 0.6:
            self.level = "acceptable"
        else:
            self.level = "insufficient"

        return self.overall_score

    def is_ready_for_report(self) -> bool:
        """Check if workshop has enough data for report generation."""
        self.calculate_overall()

        # Hard gates
        challenges_conf = self.calculate_topic_confidence("current_challenges")
        if challenges_conf < 0.5:
            return False

        # At least 3 topics with 40%+ coverage
        covered_count = sum(
            1 for topic_id in WORKSHOP_TOPIC_WEIGHTS
            if self.calculate_topic_confidence(topic_id) >= 0.4
        )
        if covered_count < 3:
            return False

        # At least 1 pain point extracted
        if self.quality_indicators.get("pain_points_extracted", 0) < 1:
            return False

        return self.level in ["acceptable", "excellent"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topics": self.topics,
            "depth_dimensions": self.depth_dimensions.to_dict(),
            "quality_indicators": self.quality_indicators,
            "overall_score": self.overall_score,
            "level": self.level,
            "is_ready_for_report": self.is_ready_for_report(),
        }
```

**Step 4: Run tests to verify they pass**

```bash
cd backend && pytest tests/test_workshop_models.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/models/workshop.py backend/tests/test_workshop_models.py
git commit -m "feat(workshop): add workshop data models and confidence framework"
```

---

## Task 1.2: Create Database Migration

**Files:**
- Create: `backend/supabase/migrations/014_workshop_columns.sql`

**Step 1: Write the migration**

```sql
-- backend/supabase/migrations/014_workshop_columns.sql
-- Add workshop columns to quiz_sessions table

-- Workshop phase tracking
ALTER TABLE quiz_sessions
ADD COLUMN IF NOT EXISTS workshop_phase TEXT
CHECK (workshop_phase IN ('confirmation', 'deepdive', 'synthesis', 'complete'));

-- Workshop data (all session data as JSONB)
ALTER TABLE quiz_sessions
ADD COLUMN IF NOT EXISTS workshop_data JSONB DEFAULT '{}'::jsonb;

-- Workshop confidence scores (enhanced framework)
ALTER TABLE quiz_sessions
ADD COLUMN IF NOT EXISTS workshop_confidence JSONB DEFAULT '{}'::jsonb;

-- Workshop timestamps
ALTER TABLE quiz_sessions
ADD COLUMN IF NOT EXISTS workshop_started_at TIMESTAMPTZ;

ALTER TABLE quiz_sessions
ADD COLUMN IF NOT EXISTS workshop_completed_at TIMESTAMPTZ;

-- Index for querying active workshops
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_workshop_phase
ON quiz_sessions(workshop_phase)
WHERE workshop_phase IS NOT NULL;

-- Comment
COMMENT ON COLUMN quiz_sessions.workshop_phase IS 'Current phase: confirmation, deepdive, synthesis, complete';
COMMENT ON COLUMN quiz_sessions.workshop_data IS 'All workshop session data including signals, deep-dives, milestones';
COMMENT ON COLUMN quiz_sessions.workshop_confidence IS 'Enhanced confidence scores for report readiness';
```

**Step 2: Verify migration syntax**

```bash
cd backend && cat supabase/migrations/014_workshop_columns.sql
```

**Step 3: Commit**

```bash
git add backend/supabase/migrations/014_workshop_columns.sql
git commit -m "feat(db): add workshop columns migration"
```

---

## Task 1.3: Add Models to Package Init

**Files:**
- Modify: `backend/src/models/__init__.py`

**Step 1: Read current file**

```bash
cat backend/src/models/__init__.py
```

**Step 2: Add workshop imports**

Add to `backend/src/models/__init__.py`:

```python
from .workshop import (
    WorkshopPhase,
    AccuracyRating,
    DetectedSignals,
    ConfirmationData,
    DeepDiveData,
    MilestoneData,
    WorkshopData,
    WorkshopConfidence,
    DepthDimensions,
)
```

**Step 3: Commit**

```bash
git add backend/src/models/__init__.py
git commit -m "feat(models): export workshop models"
```

---

# Batch 2: Backend Skills

## Task 2.1: Create Signal Detection Skill

**Files:**
- Create: `backend/src/skills/workshop/__init__.py`
- Create: `backend/src/skills/workshop/signal_detector.py`
- Test: `backend/tests/test_workshop_skills.py`

**Step 1: Create the workshop skills directory**

```bash
mkdir -p backend/src/skills/workshop
```

**Step 2: Write the test**

```python
# backend/tests/test_workshop_skills.py
"""Tests for workshop skills."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from src.skills import SkillContext
from src.skills.workshop.signal_detector import AdaptiveSignalDetectorSkill


class TestAdaptiveSignalDetectorSkill:
    """Test the signal detection skill."""

    @pytest.fixture
    def skill(self):
        return AdaptiveSignalDetectorSkill()

    @pytest.fixture
    def technical_context(self):
        return SkillContext(
            industry="technology",
            metadata={
                "role": "CTO",
                "company_size": "11-50",
                "budget_answer": "15000-50000",
                "quiz_answers": {
                    "current_tools": ["Salesforce", "custom API integrations"],
                },
            }
        )

    @pytest.fixture
    def non_technical_context(self):
        return SkillContext(
            industry="dental",
            metadata={
                "role": "Practice Owner",
                "company_size": "1-10",
                "budget_answer": "5000-15000",
                "quiz_answers": {
                    "current_tools": ["Dentrix", "Google Calendar"],
                },
            }
        )

    @pytest.mark.asyncio
    async def test_detect_technical_user(self, skill, technical_context):
        result = await skill.run(technical_context)
        assert result.success is True
        assert result.data["technical"] is True
        assert result.data["budget_ready"] is True

    @pytest.mark.asyncio
    async def test_detect_non_technical_decision_maker(self, skill, non_technical_context):
        result = await skill.run(non_technical_context)
        assert result.success is True
        assert result.data["technical"] is False
        assert result.data["decision_maker"] is True
```

**Step 3: Run test to verify it fails**

```bash
cd backend && pytest tests/test_workshop_skills.py::TestAdaptiveSignalDetectorSkill -v
```

Expected: FAIL

**Step 4: Write the implementation**

```python
# backend/src/skills/workshop/__init__.py
"""Workshop skills for the personalized 90-minute experience."""

from .signal_detector import AdaptiveSignalDetectorSkill

__all__ = [
    "AdaptiveSignalDetectorSkill",
]
```

```python
# backend/src/skills/workshop/signal_detector.py
"""
Adaptive Signal Detector Skill

Detects user signals from quiz data and company profile to adapt
workshop questions and recommendations.

Signals detected:
- technical: User has technical background, can discuss APIs/integrations
- budget_ready: User has budget allocated, can discuss implementation
- decision_maker: User can make purchasing decisions
"""

from typing import Any, Dict
from src.skills.base import SyncSkill, SkillContext
from src.models.workshop import DetectedSignals


class AdaptiveSignalDetectorSkill(SyncSkill[Dict[str, Any]]):
    """
    Detect adaptive signals from quiz and profile data.

    This skill analyzes user data to determine how to frame
    questions during the workshop.
    """

    name = "adaptive-signal-detector"
    description = "Detect user signals for adaptive workshop questioning"
    version = "1.0.0"

    requires_llm = False
    requires_expertise = False

    def execute_sync(self, context: SkillContext) -> Dict[str, Any]:
        """
        Detect signals from context.

        Args:
            context: SkillContext with metadata containing:
                - role: User's job title
                - company_size: Company size range
                - budget_answer: Selected budget range
                - quiz_answers: All quiz answers
                - company_profile: Research data (optional)

        Returns:
            Dict with detected signals and confidence
        """
        metadata = context.metadata or {}

        role = metadata.get("role")
        company_size = metadata.get("company_size")
        budget_answer = metadata.get("budget_answer")
        quiz_answers = metadata.get("quiz_answers", {})

        # Also check company profile for role if not in metadata
        company_profile = metadata.get("company_profile", {})
        if not role and company_profile:
            # Try to extract from profile
            basics = company_profile.get("basics", {})
            role = basics.get("contact_role", {}).get("value")

        signals = DetectedSignals.from_quiz_data(
            role=role,
            company_size=company_size,
            budget_answer=budget_answer,
            quiz_answers=quiz_answers,
        )

        return {
            "technical": signals.technical,
            "budget_ready": signals.budget_ready,
            "decision_maker": signals.decision_maker,
            "detection_sources": {
                "role": role,
                "company_size": company_size,
                "budget_answer": budget_answer,
            },
        }
```

**Step 5: Run tests to verify they pass**

```bash
cd backend && pytest tests/test_workshop_skills.py::TestAdaptiveSignalDetectorSkill -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add backend/src/skills/workshop/
git add backend/tests/test_workshop_skills.py
git commit -m "feat(skills): add adaptive signal detector skill"
```

---

## Task 2.2: Create Workshop Question Skill

**Files:**
- Create: `backend/src/skills/workshop/question_skill.py`
- Modify: `backend/src/skills/workshop/__init__.py`
- Test: `backend/tests/test_workshop_skills.py` (append)

**Step 1: Add test class**

Append to `backend/tests/test_workshop_skills.py`:

```python
from src.skills.workshop.question_skill import WorkshopQuestionSkill


class TestWorkshopQuestionSkill:
    """Test the adaptive question generation skill."""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client.messages.create = MagicMock(return_value=MagicMock(
            content=[MagicMock(text='"Walk me through how client reporting works today - who handles it and how long does it typically take?"')]
        ))
        return client

    @pytest.fixture
    def skill(self, mock_client):
        return WorkshopQuestionSkill(client=mock_client)

    @pytest.fixture
    def deep_dive_context(self):
        return SkillContext(
            industry="marketing-agencies",
            metadata={
                "phase": "deepdive",
                "current_pain_point": "client_reporting",
                "pain_point_label": "Client Reporting",
                "conversation_stage": "current_state",
                "signals": {"technical": False, "budget_ready": True, "decision_maker": True},
                "previous_messages": [],
                "company_name": "Acme Agency",
            }
        )

    @pytest.mark.asyncio
    async def test_generates_contextual_question(self, skill, deep_dive_context):
        result = await skill.run(deep_dive_context)
        assert result.success is True
        assert "question" in result.data
        assert len(result.data["question"]) > 20

    @pytest.mark.asyncio
    async def test_includes_company_name(self, skill, deep_dive_context):
        result = await skill.run(deep_dive_context)
        # The prompt should reference company context
        assert result.success is True
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/test_workshop_skills.py::TestWorkshopQuestionSkill -v
```

Expected: FAIL

**Step 3: Write the implementation**

```python
# backend/src/skills/workshop/question_skill.py
"""
Workshop Question Skill

Generates adaptive, contextual questions for the workshop deep-dive phase.
Uses detected signals to frame questions appropriately.
"""

from typing import Any, Dict, List, Optional
from src.skills.base import LLMSkill, SkillContext, SkillError


# Conversation stages within a deep-dive
CONVERSATION_STAGES = [
    "current_state",     # How does this work today?
    "failed_attempts",   # What have you tried?
    "cost_impact",       # What's the real cost?
    "ideal_state",       # What would perfect look like?
    "stakeholders",      # Who else is involved?
]


class WorkshopQuestionSkill(LLMSkill[Dict[str, Any]]):
    """
    Generate adaptive questions for workshop deep-dives.

    Takes into account:
    - Current pain point being explored
    - Conversation stage within the deep-dive
    - Detected user signals (technical, budget, decision-maker)
    - Previous messages in the conversation
    """

    name = "workshop-question"
    description = "Generate adaptive workshop questions"
    version = "1.0.0"

    default_model = "claude-haiku-4-5-20251001"  # Fast for questions
    default_max_tokens = 500

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Generate the next question for the workshop.

        Args:
            context: SkillContext with metadata containing:
                - phase: Current workshop phase
                - current_pain_point: ID of pain point being explored
                - pain_point_label: Human-readable pain point name
                - conversation_stage: current_state, failed_attempts, etc.
                - signals: Detected user signals
                - previous_messages: Conversation history
                - company_name: Company name for personalization

        Returns:
            Dict with question, next_stage, and metadata
        """
        metadata = context.metadata or {}

        pain_point = metadata.get("current_pain_point", "unknown")
        pain_label = metadata.get("pain_point_label", "this challenge")
        stage = metadata.get("conversation_stage", "current_state")
        signals = metadata.get("signals", {})
        previous = metadata.get("previous_messages", [])
        company_name = metadata.get("company_name", "your company")

        # Build the prompt
        prompt = self._build_prompt(
            pain_label=pain_label,
            stage=stage,
            signals=signals,
            previous=previous,
            company_name=company_name,
            industry=context.industry,
        )

        system = self._get_system_prompt(signals)

        question = await self.call_llm(prompt, system)

        # Clean up the response
        question = question.strip().strip('"').strip("'")

        # Determine next stage
        stage_idx = CONVERSATION_STAGES.index(stage) if stage in CONVERSATION_STAGES else 0
        next_stage = CONVERSATION_STAGES[stage_idx + 1] if stage_idx < len(CONVERSATION_STAGES) - 1 else "complete"

        return {
            "question": question,
            "stage": stage,
            "next_stage": next_stage,
            "pain_point": pain_point,
            "signals_applied": signals,
        }

    def _get_system_prompt(self, signals: Dict[str, bool]) -> str:
        """Build system prompt based on detected signals."""
        base = """You are an expert business consultant conducting a discovery workshop.
Your goal is to deeply understand ONE specific pain point before recommending solutions.

Key principles:
- Ask ONE question at a time
- Be conversational and warm, not interrogative
- Reference what they've already shared
- Probe for specifics: numbers, examples, names
- Keep questions under 30 words

"""
        if signals.get("technical"):
            base += """
This user has a technical background. You can:
- Ask about APIs, integrations, data flows
- Use technical terminology appropriately
- Probe about system architecture
"""
        else:
            base += """
This user is non-technical. You should:
- Focus on outcomes and business impact
- Avoid technical jargon
- Ask about team adoption and change management
"""

        if signals.get("budget_ready"):
            base += """
This user has budget available. You can:
- Discuss implementation options
- Ask about build vs. buy preferences
- Explore timeline for ROI
"""
        else:
            base += """
This user is budget-constrained. You should:
- Focus on quick wins and phased approaches
- Ask about what would unlock more budget
- Emphasize free/low-cost options
"""

        return base

    def _build_prompt(
        self,
        pain_label: str,
        stage: str,
        signals: Dict[str, bool],
        previous: List[Dict[str, str]],
        company_name: str,
        industry: str,
    ) -> str:
        """Build the question generation prompt."""
        # Stage-specific guidance
        stage_guidance = {
            "current_state": f"Ask about how {pain_label} works TODAY at {company_name}. Who does it? How long does it take? What tools are used?",
            "failed_attempts": f"Ask what they've already tried to solve {pain_label}. Past tools? Workarounds? Why didn't they work?",
            "cost_impact": f"Help quantify the cost of {pain_label}. Hours per week? Impact on revenue? Team frustration?",
            "ideal_state": f"Ask what 'solved' looks like for {pain_label}. What would be perfect? What outcomes matter most?",
            "stakeholders": f"Ask who else is involved in or affected by {pain_label}. Who needs to approve changes? Who needs to adopt?",
        }

        guidance = stage_guidance.get(stage, stage_guidance["current_state"])

        # Build conversation context
        conv_context = ""
        if previous:
            conv_context = "\n\nRecent conversation:\n"
            for msg in previous[-4:]:  # Last 4 messages
                role = msg.get("role", "user").upper()
                content = msg.get("content", "")[:200]
                conv_context += f"{role}: {content}\n"

        prompt = f"""Company: {company_name}
Industry: {industry}
Pain Point: {pain_label}
Current Stage: {stage}

{guidance}
{conv_context}

Generate the next question. Return ONLY the question text, nothing else."""

        return prompt
```

**Step 4: Update __init__.py**

```python
# backend/src/skills/workshop/__init__.py
"""Workshop skills for the personalized 90-minute experience."""

from .signal_detector import AdaptiveSignalDetectorSkill
from .question_skill import WorkshopQuestionSkill

__all__ = [
    "AdaptiveSignalDetectorSkill",
    "WorkshopQuestionSkill",
]
```

**Step 5: Run tests**

```bash
cd backend && pytest tests/test_workshop_skills.py::TestWorkshopQuestionSkill -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add backend/src/skills/workshop/
git add backend/tests/test_workshop_skills.py
git commit -m "feat(skills): add workshop question generation skill"
```

---

## Task 2.3: Create Milestone Synthesis Skill

**Files:**
- Create: `backend/src/skills/workshop/milestone_skill.py`
- Modify: `backend/src/skills/workshop/__init__.py`
- Test: `backend/tests/test_workshop_skills.py` (append)

**Step 1: Add test class**

Append to `backend/tests/test_workshop_skills.py`:

```python
from src.skills.workshop.milestone_skill import MilestoneSynthesisSkill


class TestMilestoneSynthesisSkill:
    """Test milestone synthesis skill."""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        # Mock JSON response
        client.messages.create = MagicMock(return_value=MagicMock(
            content=[MagicMock(text='''{
                "finding": {
                    "title": "Client Reporting Automation Opportunity",
                    "summary": "Automate weekly client reports to save 8 hours per week",
                    "current_process": "Manual data gathering from 4 sources",
                    "recommendation": "Implement automated reporting with Databox"
                },
                "roi": {
                    "hours_per_week": 8,
                    "hourly_rate": 75,
                    "annual_cost": 31200,
                    "potential_savings": 23400,
                    "savings_percentage": 75
                },
                "vendors": [
                    {"name": "Databox", "fit": "high", "reason": "Integrates with HubSpot"},
                    {"name": "Whatagraph", "fit": "medium", "reason": "Good for agencies"}
                ],
                "confidence": 0.82
            }''')]
        ))
        return client

    @pytest.fixture
    def skill(self, mock_client):
        return MilestoneSynthesisSkill(client=mock_client)

    @pytest.fixture
    def synthesis_context(self):
        return SkillContext(
            industry="marketing-agencies",
            metadata={
                "pain_point_id": "reporting",
                "pain_point_label": "Client Reporting",
                "transcript": [
                    {"role": "assistant", "content": "How does reporting work today?"},
                    {"role": "user", "content": "We spend about 8 hours a week gathering data from HubSpot, GA4, and social platforms, then manually creating reports in Google Slides."},
                    {"role": "assistant", "content": "What have you tried to fix this?"},
                    {"role": "user", "content": "We tried Supermetrics but it was too complex for the team."},
                ],
                "company_name": "Acme Agency",
                "tools_mentioned": ["HubSpot", "GA4", "Google Slides"],
            }
        )

    @pytest.mark.asyncio
    async def test_generates_finding(self, skill, synthesis_context):
        result = await skill.run(synthesis_context)
        assert result.success is True
        assert "finding" in result.data
        assert "title" in result.data["finding"]

    @pytest.mark.asyncio
    async def test_calculates_roi(self, skill, synthesis_context):
        result = await skill.run(synthesis_context)
        assert result.success is True
        assert "roi" in result.data
        assert "potential_savings" in result.data["roi"]

    @pytest.mark.asyncio
    async def test_includes_vendors(self, skill, synthesis_context):
        result = await skill.run(synthesis_context)
        assert result.success is True
        assert "vendors" in result.data
        assert len(result.data["vendors"]) > 0
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/test_workshop_skills.py::TestMilestoneSynthesisSkill -v
```

Expected: FAIL

**Step 3: Write the implementation**

```python
# backend/src/skills/workshop/milestone_skill.py
"""
Milestone Synthesis Skill

Synthesizes deep-dive conversation into a draft finding with:
- Structured finding summary
- ROI calculation
- Vendor recommendations
- Confidence score

This is shown to the user after each deep-dive as a "value moment".
"""

from typing import Any, Dict, List
from src.skills.base import LLMSkill, SkillContext, SkillError


class MilestoneSynthesisSkill(LLMSkill[Dict[str, Any]]):
    """
    Synthesize deep-dive transcript into draft finding and ROI.

    Uses Sonnet for quality since this is user-facing output.
    """

    name = "milestone-synthesis"
    description = "Synthesize deep-dive into finding with ROI"
    version = "1.0.0"

    default_model = "claude-sonnet-4-20250514"  # Quality matters
    default_max_tokens = 2000

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Synthesize a deep-dive into a milestone summary.

        Args:
            context: SkillContext with metadata containing:
                - pain_point_id: ID of the pain point
                - pain_point_label: Human-readable name
                - transcript: List of conversation messages
                - company_name: Company name
                - tools_mentioned: Tools identified in conversation

        Returns:
            Dict with finding, roi, vendors, confidence
        """
        metadata = context.metadata or {}

        pain_point_id = metadata.get("pain_point_id", "unknown")
        pain_label = metadata.get("pain_point_label", "This challenge")
        transcript = metadata.get("transcript", [])
        company_name = metadata.get("company_name", "the company")
        tools = metadata.get("tools_mentioned", [])

        if not transcript:
            raise SkillError(
                self.name,
                "No transcript provided for synthesis",
                recoverable=False
            )

        prompt = self._build_prompt(
            pain_label=pain_label,
            transcript=transcript,
            company_name=company_name,
            tools=tools,
            industry=context.industry,
        )

        system = self._get_system_prompt()

        result = await self.call_llm_json(prompt, system)

        # Validate and enrich result
        result["pain_point_id"] = pain_point_id
        result["pain_point_label"] = pain_label

        return result

    def _get_system_prompt(self) -> str:
        return """You are a business analyst synthesizing discovery interview data into actionable insights.

Your output will be shown directly to the user as a "draft finding" during a workshop.
Be specific, use their exact numbers and context, and provide realistic ROI calculations.

Always return valid JSON matching the requested schema. Be conservative with ROI estimates."""

    def _build_prompt(
        self,
        pain_label: str,
        transcript: List[Dict[str, str]],
        company_name: str,
        tools: List[str],
        industry: str,
    ) -> str:
        # Format transcript
        conv = "\n".join([
            f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
            for m in transcript
        ])

        return f"""Analyze this deep-dive conversation about "{pain_label}" at {company_name} ({industry}).

CONVERSATION:
{conv}

TOOLS MENTIONED: {', '.join(tools) if tools else 'None identified'}

Synthesize into a milestone summary. Return JSON:

{{
    "finding": {{
        "title": "<Concise opportunity title>",
        "summary": "<2-3 sentence summary of the opportunity>",
        "current_process": "<How it works today, from their words>",
        "pain_severity": "low|medium|high",
        "recommendation": "<High-level recommendation>"
    }},
    "roi": {{
        "hours_per_week": <number, from their data or estimate>,
        "hourly_rate": <estimated rate based on role/industry, default 75>,
        "annual_cost": <calculated: hours_per_week * hourly_rate * 52>,
        "potential_savings": <conservative estimate, usually 60-80% of cost>,
        "savings_percentage": <percentage>,
        "calculation_notes": "<brief explanation of how you calculated this>"
    }},
    "vendors": [
        {{
            "name": "<vendor name>",
            "fit": "high|medium|low",
            "reason": "<why this vendor fits their situation>"
        }}
    ],
    "confidence": <0.0-1.0, based on specificity of data provided>,
    "data_gaps": ["<list any information that would improve accuracy>"]
}}

Use THEIR actual numbers when provided. If estimating, be conservative and note it.
Return ONLY the JSON, no other text."""
```

**Step 4: Update __init__.py**

Add to `backend/src/skills/workshop/__init__.py`:

```python
from .milestone_skill import MilestoneSynthesisSkill

# Add to __all__
__all__ = [
    "AdaptiveSignalDetectorSkill",
    "WorkshopQuestionSkill",
    "MilestoneSynthesisSkill",
]
```

**Step 5: Run tests**

```bash
cd backend && pytest tests/test_workshop_skills.py::TestMilestoneSynthesisSkill -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add backend/src/skills/workshop/
git add backend/tests/test_workshop_skills.py
git commit -m "feat(skills): add milestone synthesis skill with ROI calculation"
```

---

## Task 2.4: Create Workshop Confidence Skill

**Files:**
- Create: `backend/src/skills/workshop/confidence_skill.py`
- Modify: `backend/src/skills/workshop/__init__.py`
- Test: `backend/tests/test_workshop_skills.py` (append)

**Step 1: Add test class**

Append to `backend/tests/test_workshop_skills.py`:

```python
from src.skills.workshop.confidence_skill import WorkshopConfidenceSkill


class TestWorkshopConfidenceSkill:
    """Test workshop confidence calculation skill."""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client.messages.create = MagicMock(return_value=MagicMock(
            content=[MagicMock(text='''{
                "topics": {
                    "current_challenges": {"coverage": 25, "depth": 20, "specificity": 18, "actionability": 15},
                    "business_goals": {"coverage": 20, "depth": 15, "specificity": 10, "actionability": 10},
                    "team_operations": {"coverage": 15, "depth": 12, "specificity": 10, "actionability": 8},
                    "technology": {"coverage": 22, "depth": 18, "specificity": 15, "actionability": 12},
                    "budget_timeline": {"coverage": 12, "depth": 8, "specificity": 5, "actionability": 5}
                },
                "depth_dimensions": {
                    "integration_depth": 0.72,
                    "cost_quantification": 0.85,
                    "stakeholder_mapping": 0.58,
                    "implementation_readiness": 0.45
                },
                "quality_indicators": {
                    "pain_points_extracted": 3,
                    "quantifiable_impacts": 2,
                    "specific_tools_mentioned": 5,
                    "budget_clarity": true,
                    "timeline_clarity": false,
                    "decision_maker_identified": true
                }
            }''')]
        ))
        return client

    @pytest.fixture
    def skill(self, mock_client):
        return WorkshopConfidenceSkill(client=mock_client)

    @pytest.fixture
    def confidence_context(self):
        return SkillContext(
            industry="marketing-agencies",
            metadata={
                "workshop_data": {
                    "deep_dives": [
                        {"pain_point_id": "reporting", "transcript": [...]},
                        {"pain_point_id": "leads", "transcript": [...]},
                    ],
                    "milestones": [
                        {"finding": {"title": "Reporting Automation"}, "roi": {"potential_savings": 23400}},
                    ],
                },
                "company_profile": {"basics": {"name": {"value": "Acme Agency"}}},
            }
        )

    @pytest.mark.asyncio
    async def test_calculates_topic_scores(self, skill, confidence_context):
        result = await skill.run(confidence_context)
        assert result.success is True
        assert "topics" in result.data
        assert "current_challenges" in result.data["topics"]

    @pytest.mark.asyncio
    async def test_calculates_overall_readiness(self, skill, confidence_context):
        result = await skill.run(confidence_context)
        assert result.success is True
        assert "overall" in result.data
        assert "is_ready_for_report" in result.data["overall"]
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/test_workshop_skills.py::TestWorkshopConfidenceSkill -v
```

Expected: FAIL

**Step 3: Write the implementation**

```python
# backend/src/skills/workshop/confidence_skill.py
"""
Workshop Confidence Skill

Analyzes complete workshop data to calculate enhanced confidence scores.
Determines overall readiness for report generation.
"""

from typing import Any, Dict
from src.skills.base import LLMSkill, SkillContext, SkillError
from src.models.workshop import WorkshopConfidence, DepthDimensions


class WorkshopConfidenceSkill(LLMSkill[Dict[str, Any]]):
    """
    Calculate confidence scores from workshop data.

    Analyzes all deep-dives and milestones to determine:
    - Per-topic confidence (5 topics × 4 dimensions)
    - Depth dimensions (integration, cost, stakeholders, implementation)
    - Quality indicators
    - Overall readiness for report generation
    """

    name = "workshop-confidence"
    description = "Calculate workshop confidence and readiness"
    version = "1.0.0"

    default_model = "claude-haiku-4-5-20251001"  # Structured analysis
    default_max_tokens = 2000

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Calculate confidence from workshop data.

        Args:
            context: SkillContext with metadata containing:
                - workshop_data: Full workshop session data
                - company_profile: Company research data

        Returns:
            Dict with topics, depth_dimensions, quality_indicators, overall
        """
        metadata = context.metadata or {}
        workshop_data = metadata.get("workshop_data", {})

        if not workshop_data.get("deep_dives"):
            # No deep-dives yet, return minimal confidence
            return self._empty_confidence()

        prompt = self._build_prompt(workshop_data, context.industry)
        system = self._get_system_prompt()

        result = await self.call_llm_json(prompt, system)

        # Build WorkshopConfidence object for validation
        confidence = WorkshopConfidence(
            topics=result.get("topics", {}),
            depth_dimensions=DepthDimensions(**result.get("depth_dimensions", {})),
            quality_indicators=result.get("quality_indicators", {}),
        )

        # Calculate overall score
        overall_score = confidence.calculate_overall()
        is_ready = confidence.is_ready_for_report()

        return {
            "topics": result.get("topics", {}),
            "depth_dimensions": result.get("depth_dimensions", {}),
            "quality_indicators": result.get("quality_indicators", {}),
            "overall": {
                "score": overall_score,
                "level": confidence.level,
                "is_ready_for_report": is_ready,
            },
        }

    def _empty_confidence(self) -> Dict[str, Any]:
        """Return empty confidence structure."""
        return {
            "topics": {},
            "depth_dimensions": {
                "integration_depth": 0.0,
                "cost_quantification": 0.0,
                "stakeholder_mapping": 0.0,
                "implementation_readiness": 0.0,
            },
            "quality_indicators": {
                "pain_points_extracted": 0,
                "quantifiable_impacts": 0,
            },
            "overall": {
                "score": 0.0,
                "level": "insufficient",
                "is_ready_for_report": False,
            },
        }

    def _get_system_prompt(self) -> str:
        return """You are analyzing a business discovery workshop to assess data quality and completeness.

Score each topic and dimension based on what was actually discussed and captured.
Be objective - if something wasn't discussed, score it low.

Scoring guide:
- coverage (0-25): Was the topic discussed at all?
- depth (0-25): How many substantive exchanges? (0-2: low, 3-4: medium, 5+: high)
- specificity (0-25): Were concrete examples, numbers, or names provided?
- actionability (0-25): Can we make specific recommendations from this?

Return valid JSON only."""

    def _build_prompt(self, workshop_data: Dict[str, Any], industry: str) -> str:
        # Summarize deep-dives
        deep_dives = workshop_data.get("deep_dives", [])
        dd_summary = "\n".join([
            f"- {dd.get('pain_point_label', 'Unknown')}: {len(dd.get('transcript', []))} messages"
            for dd in deep_dives
        ])

        # Summarize milestones
        milestones = workshop_data.get("milestones", [])
        ms_summary = "\n".join([
            f"- {ms.get('finding', {}).get('title', 'Unknown')}: €{ms.get('roi', {}).get('potential_savings', 0)}"
            for ms in milestones
        ])

        # Get full transcripts for analysis
        all_transcripts = []
        for dd in deep_dives:
            for msg in dd.get("transcript", []):
                all_transcripts.append(f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}")

        transcript_text = "\n".join(all_transcripts[-50:])  # Last 50 messages

        return f"""Analyze this workshop data for {industry}:

DEEP-DIVES COMPLETED:
{dd_summary}

MILESTONES GENERATED:
{ms_summary}

TRANSCRIPT (recent):
{transcript_text}

Analyze and return JSON:
{{
    "topics": {{
        "current_challenges": {{"coverage": 0-25, "depth": 0-25, "specificity": 0-25, "actionability": 0-25}},
        "business_goals": {{"coverage": 0-25, "depth": 0-25, "specificity": 0-25, "actionability": 0-25}},
        "team_operations": {{"coverage": 0-25, "depth": 0-25, "specificity": 0-25, "actionability": 0-25}},
        "technology": {{"coverage": 0-25, "depth": 0-25, "specificity": 0-25, "actionability": 0-25}},
        "budget_timeline": {{"coverage": 0-25, "depth": 0-25, "specificity": 0-25, "actionability": 0-25}}
    }},
    "depth_dimensions": {{
        "integration_depth": 0.0-1.0,
        "cost_quantification": 0.0-1.0,
        "stakeholder_mapping": 0.0-1.0,
        "implementation_readiness": 0.0-1.0
    }},
    "quality_indicators": {{
        "pain_points_extracted": <count>,
        "quantifiable_impacts": <count of specific numbers mentioned>,
        "specific_tools_mentioned": <count>,
        "budget_clarity": true/false,
        "timeline_clarity": true/false,
        "decision_maker_identified": true/false
    }}
}}"""
```

**Step 4: Update __init__.py**

Add to `backend/src/skills/workshop/__init__.py`:

```python
from .confidence_skill import WorkshopConfidenceSkill

__all__ = [
    "AdaptiveSignalDetectorSkill",
    "WorkshopQuestionSkill",
    "MilestoneSynthesisSkill",
    "WorkshopConfidenceSkill",
]
```

**Step 5: Run tests**

```bash
cd backend && pytest tests/test_workshop_skills.py::TestWorkshopConfidenceSkill -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add backend/src/skills/workshop/
git add backend/tests/test_workshop_skills.py
git commit -m "feat(skills): add workshop confidence calculation skill"
```

---

## Task 2.5: Register Workshop Skills

**Files:**
- Modify: `backend/src/skills/registry.py`

**Step 1: Read current registry**

```bash
cat backend/src/skills/registry.py | head -100
```

**Step 2: Add workshop skills to registry**

In the `_discover_skills` method or skill registration section, add:

```python
# Workshop skills
from src.skills.workshop import (
    AdaptiveSignalDetectorSkill,
    WorkshopQuestionSkill,
    MilestoneSynthesisSkill,
    WorkshopConfidenceSkill,
)

# Register in the registry
self.register("adaptive-signal-detector", AdaptiveSignalDetectorSkill)
self.register("workshop-question", WorkshopQuestionSkill)
self.register("milestone-synthesis", MilestoneSynthesisSkill)
self.register("workshop-confidence", WorkshopConfidenceSkill)
```

**Step 3: Verify registration works**

```bash
cd backend && python -c "from src.skills import get_skill; print(get_skill('workshop-question'))"
```

**Step 4: Commit**

```bash
git add backend/src/skills/registry.py
git commit -m "feat(skills): register workshop skills in registry"
```

---

# Batch 3: Backend Routes

## Task 3.1: Create Workshop Routes File

**Files:**
- Create: `backend/src/routes/workshop.py`
- Test: `backend/tests/test_workshop_routes.py`

**Step 1: Write the test file**

```python
# backend/tests/test_workshop_routes.py
"""Tests for workshop API routes."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


class TestWorkshopStart:
    """Test POST /api/workshop/start"""

    @pytest.mark.asyncio
    async def test_start_returns_confirmation_data(self, test_client, mock_supabase):
        # Mock session data
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute = AsyncMock(
            return_value=MagicMock(data={
                "id": "test-session-id",
                "company_profile": {
                    "basics": {"name": {"value": "Acme Corp"}},
                    "industry": {"primary_industry": {"value": "marketing-agencies"}},
                },
                "answers": {
                    "pain_points": ["reporting", "lead_followup"],
                    "current_tools": ["HubSpot", "Slack"],
                },
            })
        )

        response = test_client.post(
            "/api/workshop/start",
            json={"session_id": "test-session-id"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "confirmation_cards" in data
        assert "detected_signals" in data


class TestWorkshopRespond:
    """Test POST /api/workshop/respond"""

    @pytest.mark.asyncio
    async def test_respond_returns_next_question(self, test_client, mock_supabase, mock_anthropic):
        response = test_client.post(
            "/api/workshop/respond",
            json={
                "session_id": "test-session-id",
                "message": "We spend about 8 hours per week on client reporting",
                "current_pain_point": "reporting",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "confidence_update" in data
```

**Step 2: Write the routes implementation**

```python
# backend/src/routes/workshop.py
"""
Workshop Routes

API endpoints for the personalized 90-minute workshop experience.
Handles all three phases: Confirmation, Deep-Dive, and Synthesis.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.config.supabase_client import get_async_supabase
from src.config.settings import settings
from src.skills import get_skill, SkillContext
from src.expertise import get_expertise_store
from src.knowledge import normalize_industry
from src.models.workshop import (
    WorkshopPhase,
    WorkshopData,
    DetectedSignals,
    AccuracyRating,
)

import anthropic

logger = logging.getLogger(__name__)

router = APIRouter()

# Global client for skills
_anthropic_client: Optional[anthropic.Anthropic] = None


def get_anthropic_client() -> anthropic.Anthropic:
    """Get or create the Anthropic client."""
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _anthropic_client


# =============================================================================
# Request/Response Models
# =============================================================================

class WorkshopStartRequest(BaseModel):
    """Request to start workshop."""
    session_id: str


class ConfirmationCard(BaseModel):
    """A card shown in Phase 1 confirmation."""
    category: str
    title: str
    items: List[str]
    source_count: int
    editable: bool = True


class WorkshopStartResponse(BaseModel):
    """Response from workshop start."""
    session_id: str
    company_name: str
    confirmation_cards: List[ConfirmationCard]
    detected_signals: Dict[str, bool]
    pain_points: List[Dict[str, str]]


class WorkshopConfirmRequest(BaseModel):
    """Request to save confirmation phase."""
    session_id: str
    ratings: Dict[str, str]  # category -> "accurate" | "inaccurate" | "edited"
    corrections: Optional[List[Dict[str, str]]] = None
    priority_order: Optional[List[str]] = None


class WorkshopRespondRequest(BaseModel):
    """Request to get next workshop response."""
    session_id: str
    message: str
    current_pain_point: str


class WorkshopRespondResponse(BaseModel):
    """Response with next question."""
    response: str
    confidence_update: Dict[str, Any]
    should_show_milestone: bool
    estimated_remaining: str


class MilestoneRequest(BaseModel):
    """Request to generate milestone summary."""
    session_id: str
    pain_point_id: str


class WorkshopCompleteRequest(BaseModel):
    """Request to complete workshop."""
    session_id: str
    final_answers: Dict[str, Any]


# =============================================================================
# Routes
# =============================================================================

@router.post("/start", response_model=WorkshopStartResponse)
async def start_workshop(request: WorkshopStartRequest):
    """
    Start the workshop for a paid session.

    Loads quiz data and company profile, builds confirmation cards,
    detects adaptive signals, and initializes workshop state.
    """
    try:
        supabase = await get_async_supabase()

        # Get session
        result = await supabase.table("quiz_sessions").select("*").eq(
            "id", request.session_id
        ).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = result.data

        # Verify session is paid
        if session.get("status") not in ["paid", "workshop_confirmation", "workshop_deepdive"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session not ready for workshop. Status: {session.get('status')}"
            )

        company_profile = session.get("company_profile", {})
        answers = session.get("answers", {})

        # Extract company name
        basics = company_profile.get("basics", {})
        company_name = basics.get("name", {}).get("value", session.get("company_name", "Your Company"))

        # Build confirmation cards from quiz + research data
        confirmation_cards = _build_confirmation_cards(company_profile, answers)

        # Detect adaptive signals
        client = get_anthropic_client()
        signal_skill = get_skill("adaptive-signal-detector", client=client)

        industry = answers.get("industry", "general")
        normalized_industry = normalize_industry(industry)

        signal_context = SkillContext(
            industry=normalized_industry,
            metadata={
                "role": answers.get("role") or basics.get("contact_role", {}).get("value"),
                "company_size": answers.get("company_size"),
                "budget_answer": answers.get("ai_budget"),
                "quiz_answers": answers,
                "company_profile": company_profile,
            }
        )

        signal_result = await signal_skill.run(signal_context)
        detected_signals = signal_result.data if signal_result.success else {}

        # Build pain points list
        pain_points = _extract_pain_points(answers, company_profile)

        # Initialize workshop data
        workshop_data = WorkshopData(
            phase=WorkshopPhase.CONFIRMATION,
            detected_signals=DetectedSignals(
                technical=detected_signals.get("technical", False),
                budget_ready=detected_signals.get("budget_ready", False),
                decision_maker=detected_signals.get("decision_maker", False),
            ),
        )

        # Update session
        await supabase.table("quiz_sessions").update({
            "workshop_phase": "confirmation",
            "workshop_data": workshop_data.to_dict(),
            "workshop_started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", request.session_id).execute()

        logger.info(f"Workshop started for session {request.session_id}")

        return WorkshopStartResponse(
            session_id=request.session_id,
            company_name=company_name,
            confirmation_cards=confirmation_cards,
            detected_signals=detected_signals,
            pain_points=pain_points,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workshop start error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start workshop"
        )


@router.post("/confirm")
async def save_confirmation(request: WorkshopConfirmRequest):
    """
    Save Phase 1 confirmation ratings and move to deep-dive.
    """
    try:
        supabase = await get_async_supabase()

        # Get session
        result = await supabase.table("quiz_sessions").select(
            "workshop_data, answers"
        ).eq("id", request.session_id).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        workshop_data = result.data.get("workshop_data", {})
        answers = result.data.get("answers", {})

        # Update confirmation data
        workshop_data["confirmation"] = {
            "ratings": request.ratings,
            "corrections": request.corrections or [],
            "priority_order": request.priority_order or [],
            "completed_at": datetime.utcnow().isoformat(),
        }
        workshop_data["phase"] = "deepdive"

        # Determine deep-dive order
        pain_points = _extract_pain_points(answers, {})
        if request.priority_order:
            # Use user's priority
            deep_dive_order = request.priority_order
        else:
            # Default order from quiz pain points
            deep_dive_order = [pp["id"] for pp in pain_points[:4]]

        workshop_data["deep_dive_order"] = deep_dive_order
        workshop_data["current_deep_dive_index"] = 0

        # Update session
        await supabase.table("quiz_sessions").update({
            "workshop_phase": "deepdive",
            "workshop_data": workshop_data,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", request.session_id).execute()

        return {
            "success": True,
            "phase": "deepdive",
            "deep_dive_order": deep_dive_order,
            "first_pain_point": deep_dive_order[0] if deep_dive_order else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Save confirmation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save confirmation"
        )


@router.post("/respond", response_model=WorkshopRespondResponse)
async def workshop_respond(request: WorkshopRespondRequest):
    """
    Process user message and return adaptive response.
    """
    try:
        supabase = await get_async_supabase()

        # Get session
        result = await supabase.table("quiz_sessions").select("*").eq(
            "id", request.session_id
        ).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = result.data
        workshop_data = session.get("workshop_data", {})
        answers = session.get("answers", {})
        company_profile = session.get("company_profile", {})

        # Get current deep-dive state
        current_dd_index = workshop_data.get("current_deep_dive_index", 0)
        deep_dives = workshop_data.get("deep_dives", [])

        # Find or create current deep-dive
        current_dd = None
        for dd in deep_dives:
            if dd.get("pain_point_id") == request.current_pain_point:
                current_dd = dd
                break

        if not current_dd:
            current_dd = {
                "pain_point_id": request.current_pain_point,
                "pain_point_label": _get_pain_point_label(request.current_pain_point),
                "started_at": datetime.utcnow().isoformat(),
                "transcript": [],
                "conversation_stage": "current_state",
            }
            deep_dives.append(current_dd)

        # Add user message to transcript
        current_dd["transcript"].append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Generate response using workshop question skill
        client = get_anthropic_client()
        question_skill = get_skill("workshop-question", client=client)

        industry = answers.get("industry", "general")
        company_name = company_profile.get("basics", {}).get("name", {}).get("value", "your company")

        skill_context = SkillContext(
            industry=normalize_industry(industry),
            metadata={
                "phase": "deepdive",
                "current_pain_point": request.current_pain_point,
                "pain_point_label": current_dd["pain_point_label"],
                "conversation_stage": current_dd.get("conversation_stage", "current_state"),
                "signals": workshop_data.get("detected_signals", {}),
                "previous_messages": current_dd["transcript"][-10:],
                "company_name": company_name,
            }
        )

        question_result = await question_skill.run(skill_context)

        if not question_result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate response"
            )

        response_text = question_result.data["question"]
        next_stage = question_result.data["next_stage"]

        # Add assistant message to transcript
        current_dd["transcript"].append({
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Update conversation stage
        current_dd["conversation_stage"] = next_stage

        # Check if we should show milestone
        should_show_milestone = next_stage == "complete"

        # Calculate confidence update
        message_count = len(current_dd["transcript"])
        confidence_update = {
            "current_pain_point": request.current_pain_point,
            "messages": message_count,
            "stage": next_stage,
            "estimated_completeness": min(100, (message_count / 10) * 100),
        }

        # Calculate remaining time
        total_pain_points = len(workshop_data.get("deep_dive_order", []))
        completed_dds = sum(1 for dd in deep_dives if dd.get("finding"))
        remaining = total_pain_points - completed_dds
        estimated_remaining = f"{remaining * 15}-{remaining * 20} min"

        # Save updated workshop data
        workshop_data["deep_dives"] = deep_dives
        await supabase.table("quiz_sessions").update({
            "workshop_data": workshop_data,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", request.session_id).execute()

        return WorkshopRespondResponse(
            response=response_text,
            confidence_update=confidence_update,
            should_show_milestone=should_show_milestone,
            estimated_remaining=estimated_remaining,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workshop respond error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )


@router.post("/milestone")
async def generate_milestone(request: MilestoneRequest):
    """
    Generate milestone summary after deep-dive.
    """
    try:
        supabase = await get_async_supabase()

        # Get session
        result = await supabase.table("quiz_sessions").select("*").eq(
            "id", request.session_id
        ).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = result.data
        workshop_data = session.get("workshop_data", {})
        answers = session.get("answers", {})
        company_profile = session.get("company_profile", {})

        # Find the deep-dive
        deep_dives = workshop_data.get("deep_dives", [])
        current_dd = None
        for dd in deep_dives:
            if dd.get("pain_point_id") == request.pain_point_id:
                current_dd = dd
                break

        if not current_dd:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deep-dive not found"
            )

        # Generate milestone using skill
        client = get_anthropic_client()
        milestone_skill = get_skill("milestone-synthesis", client=client)

        industry = answers.get("industry", "general")
        company_name = company_profile.get("basics", {}).get("name", {}).get("value", "the company")

        # Extract tools mentioned in conversation
        tools_mentioned = []
        for msg in current_dd.get("transcript", []):
            # Simple extraction - could be enhanced
            content = msg.get("content", "").lower()
            for tool in ["hubspot", "salesforce", "slack", "excel", "google", "zapier", "notion"]:
                if tool in content and tool not in [t.lower() for t in tools_mentioned]:
                    tools_mentioned.append(tool.capitalize())

        skill_context = SkillContext(
            industry=normalize_industry(industry),
            metadata={
                "pain_point_id": request.pain_point_id,
                "pain_point_label": current_dd.get("pain_point_label", "This challenge"),
                "transcript": current_dd.get("transcript", []),
                "company_name": company_name,
                "tools_mentioned": tools_mentioned,
            }
        )

        milestone_result = await milestone_skill.run(skill_context)

        if not milestone_result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate milestone"
            )

        milestone_data = milestone_result.data

        # Save milestone
        milestones = workshop_data.get("milestones", [])
        milestones.append({
            "pain_point_id": request.pain_point_id,
            "finding": milestone_data.get("finding", {}),
            "roi": milestone_data.get("roi", {}),
            "vendors": milestone_data.get("vendors", []),
            "confidence": milestone_data.get("confidence", 0),
            "shown_at": datetime.utcnow().isoformat(),
        })

        # Mark deep-dive as complete
        current_dd["finding"] = milestone_data.get("finding", {})
        current_dd["completed_at"] = datetime.utcnow().isoformat()

        workshop_data["milestones"] = milestones
        workshop_data["deep_dives"] = deep_dives

        await supabase.table("quiz_sessions").update({
            "workshop_data": workshop_data,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", request.session_id).execute()

        return milestone_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate milestone error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate milestone"
        )


@router.get("/confidence/{session_id}")
async def get_workshop_confidence(session_id: str):
    """
    Get current workshop confidence scores.
    """
    try:
        supabase = await get_async_supabase()

        result = await supabase.table("quiz_sessions").select(
            "workshop_data, workshop_confidence, answers"
        ).eq("id", session_id).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        workshop_data = result.data.get("workshop_data", {})
        answers = result.data.get("answers", {})

        # Calculate confidence using skill
        client = get_anthropic_client()
        confidence_skill = get_skill("workshop-confidence", client=client)

        skill_context = SkillContext(
            industry=normalize_industry(answers.get("industry", "general")),
            metadata={
                "workshop_data": workshop_data,
            }
        )

        conf_result = await confidence_skill.run(skill_context)

        if conf_result.success:
            # Save updated confidence
            await supabase.table("quiz_sessions").update({
                "workshop_confidence": conf_result.data,
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("id", session_id).execute()

            return conf_result.data

        return result.data.get("workshop_confidence", {})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get confidence error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get confidence"
        )


@router.post("/complete")
async def complete_workshop(request: WorkshopCompleteRequest):
    """
    Complete the workshop and trigger report generation.
    """
    try:
        supabase = await get_async_supabase()

        result = await supabase.table("quiz_sessions").select("*").eq(
            "id", request.session_id
        ).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = result.data
        workshop_data = session.get("workshop_data", {})

        # Calculate duration
        started_at = workshop_data.get("started_at")
        if started_at:
            start_time = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            duration = int((datetime.utcnow() - start_time.replace(tzinfo=None)).total_seconds() / 60)
        else:
            duration = 0

        # Update workshop data
        workshop_data["phase"] = "complete"
        workshop_data["final_answers"] = request.final_answers
        workshop_data["completed_at"] = datetime.utcnow().isoformat()
        workshop_data["duration_minutes"] = duration

        # Calculate total savings
        total_savings = sum(
            m.get("roi", {}).get("potential_savings", 0)
            for m in workshop_data.get("milestones", [])
        )

        # Update session
        await supabase.table("quiz_sessions").update({
            "workshop_phase": "complete",
            "workshop_data": workshop_data,
            "workshop_completed_at": datetime.utcnow().isoformat(),
            "status": "generating",
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", request.session_id).execute()

        logger.info(f"Workshop completed for session {request.session_id} in {duration} minutes")

        return {
            "success": True,
            "session_id": request.session_id,
            "summary": {
                "duration_minutes": duration,
                "pain_points_analyzed": len(workshop_data.get("deep_dives", [])),
                "total_savings": total_savings,
                "confidence_level": workshop_data.get("overall", {}).get("level", "acceptable"),
            },
            "next_step": f"/api/reports/stream/{request.session_id}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Complete workshop error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete workshop"
        )


# =============================================================================
# Helper Functions
# =============================================================================

def _build_confirmation_cards(
    company_profile: Dict[str, Any],
    answers: Dict[str, Any],
) -> List[ConfirmationCard]:
    """Build confirmation cards from quiz and research data."""
    cards = []

    # Business card
    basics = company_profile.get("basics", {})
    industry_data = company_profile.get("industry", {})
    size_data = company_profile.get("size", {})

    business_items = []
    if basics.get("name", {}).get("value"):
        business_items.append(basics["name"]["value"])
    if industry_data.get("primary_industry", {}).get("value"):
        business_items.append(f"Industry: {industry_data['primary_industry']['value']}")
    if size_data.get("employee_range", {}).get("value"):
        business_items.append(f"Team size: {size_data['employee_range']['value']}")
    if basics.get("description", {}).get("value"):
        desc = basics["description"]["value"][:100]
        business_items.append(desc)

    if business_items:
        cards.append(ConfirmationCard(
            category="business",
            title="Your Business",
            items=business_items,
            source_count=len([i for i in business_items if i]),
        ))

    # Pain points card
    pain_points = answers.get("pain_points", [])
    if isinstance(pain_points, list) and pain_points:
        cards.append(ConfirmationCard(
            category="pain_points",
            title="Pain Points You Mentioned",
            items=pain_points[:5],
            source_count=len(pain_points),
        ))

    # Tools card
    tools = answers.get("current_tools", [])
    tech = company_profile.get("technology", {})
    if isinstance(tools, list):
        all_tools = tools.copy()
    else:
        all_tools = []

    if tech.get("tools_detected", {}).get("value"):
        detected = tech["tools_detected"]["value"]
        if isinstance(detected, list):
            all_tools.extend([t for t in detected if t not in all_tools])

    if all_tools:
        cards.append(ConfirmationCard(
            category="tools",
            title="Your Current Tools",
            items=all_tools[:8],
            source_count=len(all_tools),
        ))

    # Goals card
    goals = []
    if answers.get("main_goal"):
        goals.append(answers["main_goal"])
    if answers.get("success_metrics"):
        if isinstance(answers["success_metrics"], list):
            goals.extend(answers["success_metrics"])
        else:
            goals.append(answers["success_metrics"])

    if goals:
        cards.append(ConfirmationCard(
            category="goals",
            title="What Success Looks Like",
            items=goals[:4],
            source_count=len(goals),
        ))

    return cards


def _extract_pain_points(
    answers: Dict[str, Any],
    company_profile: Dict[str, Any],
) -> List[Dict[str, str]]:
    """Extract pain points as structured list."""
    pain_points = []

    raw_pains = answers.get("pain_points", [])
    if isinstance(raw_pains, list):
        for i, pain in enumerate(raw_pains[:5]):
            pain_points.append({
                "id": f"pain_{i}",
                "label": pain if isinstance(pain, str) else str(pain),
                "source": "quiz",
            })

    return pain_points


def _get_pain_point_label(pain_point_id: str) -> str:
    """Get human-readable label for pain point ID."""
    # Map common IDs to labels
    labels = {
        "reporting": "Client Reporting",
        "lead_followup": "Lead Follow-up",
        "proposals": "Proposal Generation",
        "scheduling": "Scheduling & Coordination",
        "data_entry": "Data Entry",
        "customer_support": "Customer Support",
    }
    return labels.get(pain_point_id, pain_point_id.replace("_", " ").title())
```

**Step 3: Run tests**

```bash
cd backend && pytest tests/test_workshop_routes.py -v
```

**Step 4: Commit**

```bash
git add backend/src/routes/workshop.py backend/tests/test_workshop_routes.py
git commit -m "feat(routes): add workshop API routes for all phases"
```

---

## Task 3.2: Register Workshop Routes

**Files:**
- Modify: `backend/src/main.py`

**Step 1: Add router import and registration**

In `backend/src/main.py`, add:

```python
from src.routes.workshop import router as workshop_router

# In the router registration section:
app.include_router(workshop_router, prefix="/api/workshop", tags=["workshop"])
```

**Step 2: Verify routes are registered**

```bash
cd backend && python -c "from src.main import app; print([r.path for r in app.routes if 'workshop' in r.path])"
```

**Step 3: Commit**

```bash
git add backend/src/main.py
git commit -m "feat(main): register workshop routes"
```

---

# Remaining Batches Summary

Due to length, I'll summarize the remaining batches. Each follows the same TDD pattern with exact file paths and code.

## Batch 4: Frontend Phase 1 (Confirmation)
- Task 4.1: Create WorkshopInterview.tsx page shell
- Task 4.2: Create SummaryCard component
- Task 4.3: Create AccuracyRating component
- Task 4.4: Create Phase1Confirmation container
- Task 4.5: Add animations with Framer Motion
- Task 4.6: Connect to API

## Batch 5: Frontend Phase 2 (Deep-Dive)
- Task 5.1: Create ConversationView component
- Task 5.2: Create ProgressIndicator component
- Task 5.3: Integrate voice recording
- Task 5.4: Add adaptive question display
- Task 5.5: Create Phase2DeepDive container
- Task 5.6: Handle stage transitions

## Batch 6: Frontend Milestone Summaries
- Task 6.1: Create FindingPreview component
- Task 6.2: Create ROICalculation component with animation
- Task 6.3: Create ConfidenceMeter component
- Task 6.4: Create MilestoneSummary modal
- Task 6.5: Add vendor logos display
- Task 6.6: Add user feedback buttons

## Batch 7: Frontend Phase 3 (Synthesis)
- Task 7.1: Create ReportPreview component
- Task 7.2: Create FinalQuestions component
- Task 7.3: Create CompletionSummary component
- Task 7.4: Create Phase3Synthesis container
- Task 7.5: Connect to report generation

## Batch 8: Integration & Polish
- Task 8.1: Add route to App.tsx
- Task 8.2: Update CheckoutSuccess to redirect to workshop
- Task 8.3: Add session recovery/resume
- Task 8.4: Add auto-save
- Task 8.5: End-to-end testing
- Task 8.6: Performance optimization

---

# Quick Start Commands

```bash
# Run all backend tests
cd backend && pytest tests/test_workshop*.py -v

# Run frontend dev server
cd frontend && npm run dev

# Start backend
cd backend && uvicorn src.main:app --reload --port 8383

# View workshop at
http://localhost:5174/workshop?session_id=<paid_session_id>
```

---

# Notes for Implementation

1. **TDD is mandatory** - Write the failing test before implementation
2. **Commit frequently** - After each task or logical unit
3. **Check skills exist** - Use `get_skill()` and verify in registry
4. **Handle errors gracefully** - All routes should return structured errors
5. **Use existing patterns** - Follow VoiceQuizInterview.tsx for frontend patterns
6. **Test with real data** - Use the `/dev/generate-test-report` endpoint

---

**Plan complete and saved to `docs/plans/2026-01-03-personalized-workshop-implementation.md`.**

**Two execution options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
