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
