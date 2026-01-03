"""
Report Feedback Model

Collects dev/admin feedback on generated reports to feed into the expertise system.
This is part of the Signal Loop (SIL) - learning from what works and what doesn't.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class FeedbackRating(str, Enum):
    """Rating for individual items."""
    EXCELLENT = "excellent"  # Spot on, use as pattern
    GOOD = "good"           # Accurate, keep
    OKAY = "okay"           # Acceptable but could improve
    POOR = "poor"           # Inaccurate or not helpful
    WRONG = "wrong"         # Completely off, add to anti-patterns


class FindingFeedback(BaseModel):
    """Feedback on a specific finding."""
    finding_id: str
    rating: FeedbackRating
    notes: Optional[str] = None
    should_be_higher_priority: bool = False
    should_be_lower_priority: bool = False
    roi_accurate: Optional[bool] = None  # Was the ROI estimate reasonable?


class RecommendationFeedback(BaseModel):
    """Feedback on a specific recommendation."""
    recommendation_id: str
    rating: FeedbackRating
    notes: Optional[str] = None
    best_option: Optional[str] = None  # Which of the 3 options is actually best?
    vendor_pricing_accurate: bool = True
    would_implement: bool = True  # Would a real customer actually do this?


class ReportFeedback(BaseModel):
    """
    Complete feedback on a generated report.

    This data feeds directly into the expertise system to improve future analyses.
    """
    report_id: str
    session_id: Optional[str] = None

    # Timestamp
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    reviewer: str = "admin"  # For now, just admin

    # Overall scores (1-10)
    overall_quality: int = Field(ge=1, le=10, default=5)
    accuracy_score: int = Field(ge=1, le=10, default=5)
    actionability_score: int = Field(ge=1, le=10, default=5)
    relevance_score: int = Field(ge=1, le=10, default=5)

    # Verdict feedback
    verdict_appropriate: bool = True
    verdict_notes: Optional[str] = None

    # Individual item feedback
    findings_feedback: List[FindingFeedback] = Field(default_factory=list)
    recommendations_feedback: List[RecommendationFeedback] = Field(default_factory=list)

    # What's missing?
    missing_findings: List[str] = Field(default_factory=list)  # Pain points we should have found
    missing_recommendations: List[str] = Field(default_factory=list)  # Solutions we should have suggested

    # What shouldn't be there?
    irrelevant_findings: List[str] = Field(default_factory=list)  # Finding IDs that don't apply
    irrelevant_recommendations: List[str] = Field(default_factory=list)  # Rec IDs that don't apply

    # Industry-specific learnings
    industry_patterns_observed: List[str] = Field(default_factory=list)  # New patterns to add
    industry_anti_patterns: List[str] = Field(default_factory=list)  # Things that don't work

    # Free-form notes
    general_notes: Optional[str] = None

    # For tracking
    time_spent_reviewing_seconds: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "report_id": self.report_id,
            "session_id": self.session_id,
            "submitted_at": self.submitted_at.isoformat(),
            "reviewer": self.reviewer,
            "overall_quality": self.overall_quality,
            "accuracy_score": self.accuracy_score,
            "actionability_score": self.actionability_score,
            "relevance_score": self.relevance_score,
            "verdict_appropriate": self.verdict_appropriate,
            "verdict_notes": self.verdict_notes,
            "findings_feedback": [f.model_dump() for f in self.findings_feedback],
            "recommendations_feedback": [r.model_dump() for r in self.recommendations_feedback],
            "missing_findings": self.missing_findings,
            "missing_recommendations": self.missing_recommendations,
            "irrelevant_findings": self.irrelevant_findings,
            "irrelevant_recommendations": self.irrelevant_recommendations,
            "industry_patterns_observed": self.industry_patterns_observed,
            "industry_anti_patterns": self.industry_anti_patterns,
            "general_notes": self.general_notes,
            "time_spent_reviewing_seconds": self.time_spent_reviewing_seconds,
        }


class ReportContext(BaseModel):
    """
    Full context that went into generating a report.
    Shown in dev mode for QA purposes.
    """
    # Session info
    session_id: str
    email: Optional[str] = None
    company_name: Optional[str] = None

    # Quiz/Interview inputs
    quiz_answers: Dict[str, Any] = Field(default_factory=dict)
    company_profile: Dict[str, Any] = Field(default_factory=dict)
    interview_data: Dict[str, Any] = Field(default_factory=dict)
    interview_transcript: List[Dict[str, str]] = Field(default_factory=list)

    # Research data
    research_data: Dict[str, Any] = Field(default_factory=dict)
    industry_knowledge: Dict[str, Any] = Field(default_factory=dict)
    vendors_considered: List[Dict[str, Any]] = Field(default_factory=list)

    # Generation metadata
    generation_started_at: Optional[str] = None
    generation_completed_at: Optional[str] = None
    model_used: Optional[str] = None
    tokens_used: Optional[Dict[str, Any]] = None  # Token usage summary with cost

    # Generation trace - detailed reasoning, tool calls, logic used
    generation_trace: Optional[Dict[str, Any]] = None

    # Confidence data from interview
    confidence_scores: Dict[str, Any] = Field(default_factory=dict)
