"""
Interview Confidence Framework Models

This module defines the data structures for measuring interview quality
and determining when we have enough context for a quality report.

The framework has 4 layers:
1. TopicConfidence: Per-topic scoring (coverage, depth, specificity, actionability)
2. OverallReadiness: Weighted aggregate with quality multipliers
3. ReadinessThresholds: Decision gates for report generation
4. TriggerResult: Final decision with reasoning
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime


class ReadinessLevel(Enum):
    """Overall readiness classification."""
    INSUFFICIENT = "insufficient"      # 0.0 - 0.59: Continue interviewing
    ACCEPTABLE = "acceptable"          # 0.60 - 0.79: Can complete if user wants
    EXCELLENT = "excellent"            # 0.80 - 1.0: Ready for report generation


class TopicID(Enum):
    """Interview topic identifiers."""
    CURRENT_CHALLENGES = "current_challenges"
    BUSINESS_GOALS = "business_goals"
    TEAM_OPERATIONS = "team_operations"
    TECHNOLOGY = "technology"
    BUDGET_TIMELINE = "budget_timeline"


# Topic weights for overall readiness calculation
TOPIC_WEIGHTS = {
    TopicID.CURRENT_CHALLENGES: 1.5,   # Most important - drives findings
    TopicID.BUSINESS_GOALS: 1.2,       # Important - drives recommendations
    TopicID.TEAM_OPERATIONS: 1.0,      # Standard weight
    TopicID.TECHNOLOGY: 1.0,           # Standard weight
    TopicID.BUDGET_TIMELINE: 0.8,      # Nice to have, not critical
}

# Minimum thresholds (hard gates)
MIN_CHALLENGES_CONFIDENCE = 0.5    # Must have decent understanding of challenges
MIN_TOPICS_WITH_COVERAGE = 3       # At least 3 topics with confidence >= 0.4
MIN_TOPIC_THRESHOLD = 0.4          # Minimum confidence to count as "covered"
MIN_PAIN_POINTS = 1                # At least 1 pain point must be extracted

# Readiness thresholds
THRESHOLD_ACCEPTABLE = 0.60
THRESHOLD_EXCELLENT = 0.80


@dataclass
class TopicConfidence:
    """
    Confidence score for a single interview topic.

    Each dimension is scored 0-25, total 0-100, normalized to 0.0-1.0
    """
    topic_id: TopicID
    topic_name: str

    # Scoring dimensions (0-25 each)
    coverage: int = 0          # Was the topic discussed at all?
    depth: int = 0             # How many substantive exchanges?
    specificity: int = 0       # Concrete examples, numbers, names?
    actionability: int = 0     # Can we make recommendations from this?

    # Evidence
    exchanges: List[Dict[str, str]] = field(default_factory=list)
    extracted_insights: List[str] = field(default_factory=list)

    @property
    def total_score(self) -> int:
        """Total raw score out of 100."""
        return self.coverage + self.depth + self.specificity + self.actionability

    @property
    def confidence(self) -> float:
        """Normalized confidence score (0.0 - 1.0)."""
        return self.total_score / 100.0

    @property
    def is_covered(self) -> bool:
        """Whether topic meets minimum coverage threshold."""
        return self.confidence >= MIN_TOPIC_THRESHOLD

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/API."""
        return {
            "topic_id": self.topic_id.value,
            "topic_name": self.topic_name,
            "scores": {
                "coverage": self.coverage,
                "depth": self.depth,
                "specificity": self.specificity,
                "actionability": self.actionability,
            },
            "total_score": self.total_score,
            "confidence": round(self.confidence, 3),
            "is_covered": self.is_covered,
            "exchanges_count": len(self.exchanges),
            "insights_count": len(self.extracted_insights),
        }


@dataclass
class QualityIndicators:
    """
    Quality indicators extracted from the interview.
    These provide multipliers to the overall readiness score.
    """
    pain_points_extracted: int = 0
    quantifiable_impacts: int = 0      # e.g., "costs us $5K/month", "takes 3 hours"
    specific_tools_mentioned: int = 0  # Named software/tools
    budget_clarity: bool = False       # Did they indicate budget range?
    timeline_clarity: bool = False     # Did they indicate timeline?
    decision_maker_identified: bool = False  # Are we talking to decision maker?

    @property
    def quality_multiplier(self) -> float:
        """Calculate quality multiplier (1.0 - ~1.4)."""
        multiplier = 1.0

        if self.pain_points_extracted >= 3:
            multiplier *= 1.10
        elif self.pain_points_extracted >= 1:
            multiplier *= 1.05

        if self.quantifiable_impacts >= 2:
            multiplier *= 1.10
        elif self.quantifiable_impacts >= 1:
            multiplier *= 1.05

        if self.specific_tools_mentioned >= 2:
            multiplier *= 1.05

        if self.budget_clarity:
            multiplier *= 1.05

        if self.timeline_clarity:
            multiplier *= 1.03

        if self.decision_maker_identified:
            multiplier *= 1.02

        return round(multiplier, 3)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/API."""
        return {
            "pain_points_extracted": self.pain_points_extracted,
            "quantifiable_impacts": self.quantifiable_impacts,
            "specific_tools_mentioned": self.specific_tools_mentioned,
            "budget_clarity": self.budget_clarity,
            "timeline_clarity": self.timeline_clarity,
            "decision_maker_identified": self.decision_maker_identified,
            "quality_multiplier": self.quality_multiplier,
        }


@dataclass
class HardGateResult:
    """Result of checking hard gates (minimum requirements)."""
    passed: bool
    failures: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "failures": self.failures,
        }


@dataclass
class OverallReadiness:
    """
    Overall interview readiness assessment.
    Combines topic confidences with quality indicators.
    """
    topic_confidences: Dict[TopicID, TopicConfidence]
    quality_indicators: QualityIndicators

    # Calculated fields
    weighted_average: float = 0.0
    final_score: float = 0.0
    level: ReadinessLevel = ReadinessLevel.INSUFFICIENT
    hard_gates: HardGateResult = field(default_factory=lambda: HardGateResult(passed=False))

    def calculate(self) -> "OverallReadiness":
        """Calculate overall readiness from components."""
        # Calculate weighted average of topic confidences
        total_weight = sum(TOPIC_WEIGHTS.values())
        weighted_sum = sum(
            self.topic_confidences[topic_id].confidence * weight
            for topic_id, weight in TOPIC_WEIGHTS.items()
            if topic_id in self.topic_confidences
        )
        self.weighted_average = weighted_sum / total_weight

        # Apply quality multiplier
        self.final_score = min(1.0, self.weighted_average * self.quality_indicators.quality_multiplier)

        # Determine level
        if self.final_score >= THRESHOLD_EXCELLENT:
            self.level = ReadinessLevel.EXCELLENT
        elif self.final_score >= THRESHOLD_ACCEPTABLE:
            self.level = ReadinessLevel.ACCEPTABLE
        else:
            self.level = ReadinessLevel.INSUFFICIENT

        # Check hard gates
        self.hard_gates = self._check_hard_gates()

        return self

    def _check_hard_gates(self) -> HardGateResult:
        """Check minimum requirements that must be met."""
        failures = []

        # Gate 1: Current challenges must have decent coverage
        challenges_conf = self.topic_confidences.get(TopicID.CURRENT_CHALLENGES)
        if not challenges_conf or challenges_conf.confidence < MIN_CHALLENGES_CONFIDENCE:
            actual = challenges_conf.confidence if challenges_conf else 0
            failures.append(
                f"Current challenges confidence ({actual:.2f}) below minimum ({MIN_CHALLENGES_CONFIDENCE})"
            )

        # Gate 2: At least 3 topics with minimum coverage
        covered_count = sum(
            1 for tc in self.topic_confidences.values()
            if tc.confidence >= MIN_TOPIC_THRESHOLD
        )
        if covered_count < MIN_TOPICS_WITH_COVERAGE:
            failures.append(
                f"Only {covered_count} topics covered (minimum {MIN_TOPICS_WITH_COVERAGE})"
            )

        # Gate 3: At least 1 pain point extracted
        if self.quality_indicators.pain_points_extracted < MIN_PAIN_POINTS:
            failures.append(
                f"No pain points extracted (minimum {MIN_PAIN_POINTS})"
            )

        return HardGateResult(
            passed=len(failures) == 0,
            failures=failures
        )

    @property
    def is_ready_for_report(self) -> bool:
        """Whether we can trigger report generation."""
        return (
            self.level in [ReadinessLevel.ACCEPTABLE, ReadinessLevel.EXCELLENT]
            and self.hard_gates.passed
        )

    @property
    def should_continue_interview(self) -> bool:
        """Whether we should continue the interview."""
        return not self.is_ready_for_report

    def get_improvement_suggestions(self) -> List[str]:
        """Get suggestions for improving readiness."""
        suggestions = []

        # From hard gate failures
        suggestions.extend(self.hard_gates.failures)

        # From low topic scores
        for topic_id, tc in self.topic_confidences.items():
            if tc.confidence < MIN_TOPIC_THRESHOLD:
                suggestions.append(f"Explore '{tc.topic_name}' more deeply")
            elif tc.specificity < 15:
                suggestions.append(f"Get more specific examples for '{tc.topic_name}'")
            elif tc.actionability < 15:
                suggestions.append(f"Understand desired outcomes for '{tc.topic_name}'")

        # From quality indicators
        if self.quality_indicators.pain_points_extracted < 3:
            suggestions.append("Extract more specific pain points")
        if self.quality_indicators.quantifiable_impacts < 2:
            suggestions.append("Get quantifiable impact data (hours, costs, etc.)")
        if not self.quality_indicators.budget_clarity:
            suggestions.append("Understand budget expectations")

        return suggestions[:5]  # Top 5 suggestions

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/API."""
        return {
            "topic_confidences": {
                topic_id.value: tc.to_dict()
                for topic_id, tc in self.topic_confidences.items()
            },
            "quality_indicators": self.quality_indicators.to_dict(),
            "weighted_average": round(self.weighted_average, 3),
            "final_score": round(self.final_score, 3),
            "level": self.level.value,
            "hard_gates": self.hard_gates.to_dict(),
            "is_ready_for_report": self.is_ready_for_report,
            "should_continue_interview": self.should_continue_interview,
            "improvement_suggestions": self.get_improvement_suggestions(),
        }


@dataclass
class InterviewCompletionTrigger:
    """
    Result of the interview completion decision.
    Determines whether to trigger report generation.
    """
    session_id: str
    readiness: OverallReadiness

    # Decision
    trigger_report: bool = False
    reason: str = ""

    # Next steps
    next_action: str = ""  # "continue_interview", "trigger_report", "offer_completion"
    suggested_questions: List[str] = field(default_factory=list)

    # Timestamps
    evaluated_at: datetime = field(default_factory=datetime.utcnow)

    def evaluate(self) -> "InterviewCompletionTrigger":
        """Evaluate whether to trigger report generation."""
        if self.readiness.is_ready_for_report:
            if self.readiness.level == ReadinessLevel.EXCELLENT:
                self.trigger_report = True
                self.reason = "Excellent interview quality - all topics covered with high confidence"
                self.next_action = "trigger_report"
            else:
                # Acceptable but not excellent - offer choice
                self.trigger_report = False
                self.reason = "Acceptable interview quality - can proceed or continue for better results"
                self.next_action = "offer_completion"
                self.suggested_questions = self._get_improvement_questions()
        else:
            self.trigger_report = False
            self.reason = f"Interview incomplete: {'; '.join(self.readiness.hard_gates.failures)}"
            self.next_action = "continue_interview"
            self.suggested_questions = self._get_improvement_questions()

        return self

    def _get_improvement_questions(self) -> List[str]:
        """Get questions that would improve readiness."""
        questions = []

        # Based on low topic scores
        for topic_id, tc in self.readiness.topic_confidences.items():
            if tc.confidence < 0.5:
                questions.extend(self._get_topic_questions(topic_id))

        # Based on missing quality indicators
        if self.readiness.quality_indicators.quantifiable_impacts < 2:
            questions.append(
                "Can you help me understand the specific impact? "
                "For example, how many hours per week does this cost your team?"
            )

        if not self.readiness.quality_indicators.budget_clarity:
            questions.append(
                "What budget range are you considering for solving these challenges?"
            )

        return questions[:3]  # Top 3 questions

    def _get_topic_questions(self, topic_id: TopicID) -> List[str]:
        """Get probing questions for a specific topic."""
        topic_questions = {
            TopicID.CURRENT_CHALLENGES: [
                "What's the biggest operational frustration you face daily?",
                "Can you walk me through a recent situation where this caused problems?",
            ],
            TopicID.BUSINESS_GOALS: [
                "What would success look like for your business in the next 12 months?",
                "If we could solve one thing, what would have the biggest impact?",
            ],
            TopicID.TEAM_OPERATIONS: [
                "Can you describe a typical workflow that feels inefficient?",
                "Where do things usually get stuck or delayed?",
            ],
            TopicID.TECHNOLOGY: [
                "What tools does your team rely on most?",
                "Are there integrations that don't work well or are missing?",
            ],
            TopicID.BUDGET_TIMELINE: [
                "What's your timeline for implementing improvements?",
                "Have you allocated budget for this kind of initiative?",
            ],
        }
        return topic_questions.get(topic_id, [])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/API."""
        return {
            "session_id": self.session_id,
            "readiness": self.readiness.to_dict(),
            "trigger_report": self.trigger_report,
            "reason": self.reason,
            "next_action": self.next_action,
            "suggested_questions": self.suggested_questions,
            "evaluated_at": self.evaluated_at.isoformat(),
        }


# Report generation status for the QA workflow
class ReportStatus(Enum):
    """Status of report in the generation/QA pipeline."""
    INTERVIEW_IN_PROGRESS = "interview_in_progress"
    INTERVIEW_COMPLETE = "interview_complete"
    GENERATING = "generating"
    QA_PENDING = "qa_pending"
    QA_APPROVED = "qa_approved"
    QA_REJECTED = "qa_rejected"
    RELEASED = "released"
    FAILED = "failed"


@dataclass
class QAReview:
    """Human QA review of a generated report."""
    report_id: str
    reviewer_id: Optional[str] = None

    # Review result
    approved: bool = False
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None

    # Quality scores (1-5)
    accuracy_score: Optional[int] = None
    relevance_score: Optional[int] = None
    actionability_score: Optional[int] = None

    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "reviewer_id": self.reviewer_id,
            "approved": self.approved,
            "rejection_reason": self.rejection_reason,
            "notes": self.notes,
            "scores": {
                "accuracy": self.accuracy_score,
                "relevance": self.relevance_score,
                "actionability": self.actionability_score,
            },
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
