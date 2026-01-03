"""
Quiz Confidence Framework Models

This module defines the data structures for the adaptive quiz system.
The quiz adapts based on research findings and confidence gaps, asking
only what's needed to reach minimum thresholds for a quality teaser report.

Key concepts:
1. ConfidenceCategory: The 8 categories we need confidence in
2. ConfidenceState: Tracks scores, facts, and gaps per category
3. AdaptiveQuestion: A dynamically generated question with metadata
4. AnswerAnalysis: Extracted insights from a user's answer
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class ConfidenceCategory(str, Enum):
    """Categories we need confidence in before showing teaser."""
    COMPANY_BASICS = "company_basics"           # Size, industry, business model
    TECH_STACK = "tech_stack"                   # Tools and systems they use
    PAIN_POINTS = "pain_points"                 # Challenges and frustrations
    OPERATIONS = "operations"                   # How they work day-to-day
    GOALS_PRIORITIES = "goals_priorities"       # What they want to achieve
    QUANTIFIABLE_METRICS = "quantifiable_metrics"  # Numbers for ROI calc
    INDUSTRY_CONTEXT = "industry_context"       # Industry-specific details
    BUYING_SIGNALS = "buying_signals"           # Budget, timeline, decision maker


# Minimum thresholds required to unlock teaser report
CONFIDENCE_THRESHOLDS: Dict[ConfidenceCategory, int] = {
    ConfidenceCategory.COMPANY_BASICS: 80,
    ConfidenceCategory.TECH_STACK: 60,
    ConfidenceCategory.PAIN_POINTS: 80,
    ConfidenceCategory.OPERATIONS: 60,
    ConfidenceCategory.GOALS_PRIORITIES: 70,
    ConfidenceCategory.QUANTIFIABLE_METRICS: 50,
    ConfidenceCategory.INDUSTRY_CONTEXT: 60,
    ConfidenceCategory.BUYING_SIGNALS: 40,
}

# Human-readable category labels
CATEGORY_LABELS: Dict[ConfidenceCategory, str] = {
    ConfidenceCategory.COMPANY_BASICS: "Company",
    ConfidenceCategory.TECH_STACK: "Tools",
    ConfidenceCategory.PAIN_POINTS: "Challenges",
    ConfidenceCategory.OPERATIONS: "Operations",
    ConfidenceCategory.GOALS_PRIORITIES: "Goals",
    ConfidenceCategory.QUANTIFIABLE_METRICS: "Metrics",
    ConfidenceCategory.INDUSTRY_CONTEXT: "Industry",
    ConfidenceCategory.BUYING_SIGNALS: "Readiness",
}


class ExtractedFact(BaseModel):
    """A fact extracted from research or an answer."""
    fact: str
    value: Optional[Any] = None
    confidence: str = "medium"  # high, medium, low
    source: str = "quiz"  # research, quiz
    extracted_at: datetime = Field(default_factory=datetime.utcnow)


class ConfidenceState(BaseModel):
    """
    Tracks confidence across all categories for a quiz session.

    This is the core state object that determines:
    - What questions to ask (based on gaps)
    - When to stop (when thresholds are met)
    - What facts we've learned
    """
    # Scores per category (0-100)
    scores: Dict[ConfidenceCategory, int] = Field(
        default_factory=lambda: {cat: 0 for cat in ConfidenceCategory}
    )

    # Extracted facts per category
    facts: Dict[ConfidenceCategory, List[ExtractedFact]] = Field(
        default_factory=lambda: {cat: [] for cat in ConfidenceCategory}
    )

    # Categories below their threshold
    gaps: List[ConfidenceCategory] = Field(default_factory=list)

    # Whether all thresholds are met
    ready_for_teaser: bool = False

    # Tracking
    questions_asked: int = 0
    research_quality_score: int = 0  # From pre-research

    class Config:
        use_enum_values = True

    def recalculate_gaps(self) -> None:
        """Recalculate which categories are below threshold."""
        self.gaps = [
            cat for cat, score in self.scores.items()
            if score < CONFIDENCE_THRESHOLDS[cat]
        ]
        self.ready_for_teaser = len(self.gaps) == 0

    def update_score(self, category: ConfidenceCategory, boost: int) -> None:
        """Add points to a category, capped at 100."""
        current = self.scores.get(category, 0)
        self.scores[category] = min(100, current + boost)
        self.recalculate_gaps()

    def add_fact(self, category: ConfidenceCategory, fact: ExtractedFact) -> None:
        """Add an extracted fact to a category."""
        if category not in self.facts:
            self.facts[category] = []
        self.facts[category].append(fact)

    def get_sorted_gaps(self) -> List[ConfidenceCategory]:
        """Get gaps sorted by how far below threshold they are (worst first)."""
        return sorted(
            self.gaps,
            key=lambda cat: CONFIDENCE_THRESHOLDS[cat] - self.scores.get(cat, 0),
            reverse=True,
        )

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get a summary of progress for the frontend."""
        # Helper to get string value from enum or string
        def to_str(cat):
            return cat.value if hasattr(cat, 'value') else str(cat)

        return {
            "scores": {to_str(cat): score for cat, score in self.scores.items()},
            "thresholds": {cat.value: thresh for cat, thresh in CONFIDENCE_THRESHOLDS.items()},
            "gaps": [to_str(cat) for cat in self.gaps],
            "ready_for_teaser": self.ready_for_teaser,
            "questions_asked": self.questions_asked,
            "facts_collected": sum(len(facts) for facts in self.facts.values()),
        }

    def to_teaser_summary(self) -> Dict[str, Any]:
        """Generate summary for teaser report generation."""
        # Helper to get facts by category (handles both enum and string keys)
        def get_facts(category: ConfidenceCategory) -> List[ExtractedFact]:
            return self.facts.get(category, []) or self.facts.get(category.value, [])

        # Helper to get string value from enum or string
        def to_str(cat):
            return cat.value if hasattr(cat, 'value') else str(cat)

        return {
            "pain_points": [f.model_dump(mode='json') for f in get_facts(ConfidenceCategory.PAIN_POINTS)],
            "goals": [f.model_dump(mode='json') for f in get_facts(ConfidenceCategory.GOALS_PRIORITIES)],
            "metrics": [f.model_dump(mode='json') for f in get_facts(ConfidenceCategory.QUANTIFIABLE_METRICS)],
            "tools": [f.model_dump(mode='json') for f in get_facts(ConfidenceCategory.TECH_STACK)],
            "operations": [f.model_dump(mode='json') for f in get_facts(ConfidenceCategory.OPERATIONS)],
            "questions_asked": self.questions_asked,
            "final_scores": {to_str(cat): score for cat, score in self.scores.items()},
        }


class AdaptiveQuestion(BaseModel):
    """
    A dynamically generated question for the adaptive quiz.

    Includes metadata about what category it targets and
    expected confidence boosts.
    """
    id: str
    question: str
    acknowledgment: Optional[str] = None  # Response to previous answer

    # Question format
    question_type: str = "voice"  # "structured" | "voice"
    input_type: str = "voice"  # "text" | "number" | "select" | "multi_select" | "scale" | "voice"
    options: Optional[List[Dict[str, str]]] = None  # For select types
    placeholder: Optional[str] = None

    # Targeting
    target_categories: List[ConfidenceCategory]
    expected_boosts: Dict[ConfidenceCategory, int] = Field(default_factory=dict)

    # Metadata
    rationale: str = ""  # Why we're asking this (for debugging)
    is_deep_dive: bool = False  # Whether this is a follow-up on a signal
    priority: int = 1  # Lower = more important

    # Industry-specific
    industry: Optional[str] = None

    class Config:
        use_enum_values = True


class AnswerAnalysis(BaseModel):
    """
    Result of analyzing a user's answer.

    Contains extracted facts, confidence boosts, and signals
    for whether to deep dive.
    """
    # What we learned
    extracted_facts: Dict[ConfidenceCategory, List[ExtractedFact]] = Field(
        default_factory=dict
    )

    # Confidence updates
    confidence_boosts: Dict[ConfidenceCategory, int] = Field(default_factory=dict)

    # Signals detected
    detected_signals: List[str] = Field(default_factory=list)
    # e.g., "pain_signal", "urgency", "budget_mention", "quantifiable"

    # Deep dive decision
    should_deep_dive: bool = False
    deep_dive_topic: Optional[str] = None

    # Sentiment
    sentiment: str = "neutral"  # "frustrated", "neutral", "enthusiastic"

    # Raw extraction for debugging
    raw_extraction: Optional[Dict[str, Any]] = None

    class Config:
        use_enum_values = True


class QuizCompletionResult(BaseModel):
    """Result when quiz reaches completion (all thresholds met)."""
    complete: bool = True
    confidence_state: ConfidenceState
    wrap_up_message: str
    teaser_summary: Dict[str, Any]
    redirect_url: str


# ============================================================================
# Factory Functions
# ============================================================================

def create_initial_confidence_from_research(
    profile: Dict[str, Any],
    research_quality_score: int = 0,
) -> ConfidenceState:
    """
    Initialize confidence state from research findings.

    Maps research profile fields to confidence scores.
    """
    state = ConfidenceState(research_quality_score=research_quality_score)

    # Company basics from research
    basics = profile.get("basics", {})
    if basics.get("name"):
        state.update_score(ConfidenceCategory.COMPANY_BASICS, 20)
        state.add_fact(
            ConfidenceCategory.COMPANY_BASICS,
            ExtractedFact(
                fact="company_name",
                value=basics["name"].get("value") if isinstance(basics["name"], dict) else basics["name"],
                confidence="high",
                source="research",
            )
        )

    if basics.get("description"):
        state.update_score(ConfidenceCategory.COMPANY_BASICS, 20)
        desc_value = basics["description"]
        if isinstance(desc_value, dict):
            desc_value = desc_value.get("value", "")
        state.add_fact(
            ConfidenceCategory.COMPANY_BASICS,
            ExtractedFact(fact="description", value=desc_value, confidence="high", source="research")
        )

    # Size info
    size = profile.get("size", {})
    if size:
        if size.get("employee_range") or size.get("employee_count"):
            state.update_score(ConfidenceCategory.COMPANY_BASICS, 20)
            emp_value = size.get("employee_range") or size.get("employee_count")
            if isinstance(emp_value, dict):
                emp_value = emp_value.get("value")
            state.add_fact(
                ConfidenceCategory.COMPANY_BASICS,
                ExtractedFact(fact="employee_count", value=emp_value, confidence="medium", source="research")
            )

        if size.get("revenue_estimate"):
            state.update_score(ConfidenceCategory.COMPANY_BASICS, 10)

        if size.get("funding_raised"):
            state.update_score(ConfidenceCategory.BUYING_SIGNALS, 15)

    # Industry info
    industry = profile.get("industry", {})
    if industry:
        if industry.get("primary_industry"):
            state.update_score(ConfidenceCategory.COMPANY_BASICS, 15)
            state.update_score(ConfidenceCategory.INDUSTRY_CONTEXT, 30)
            ind_value = industry["primary_industry"]
            if isinstance(ind_value, dict):
                ind_value = ind_value.get("value")
            state.add_fact(
                ConfidenceCategory.INDUSTRY_CONTEXT,
                ExtractedFact(fact="industry", value=ind_value, confidence="high", source="research")
            )

        if industry.get("business_model"):
            state.update_score(ConfidenceCategory.COMPANY_BASICS, 10)
            state.update_score(ConfidenceCategory.INDUSTRY_CONTEXT, 15)

    # Tech stack from research
    tech_stack = profile.get("tech_stack", {})
    if tech_stack:
        technologies = tech_stack.get("technologies_detected", [])
        if technologies:
            # Each detected tech adds points
            boost = min(len(technologies) * 12, 50)  # Cap at 50%
            state.update_score(ConfidenceCategory.TECH_STACK, boost)
            for tech in technologies[:5]:  # Store first 5
                tech_value = tech
                if isinstance(tech, dict):
                    tech_value = tech.get("value", str(tech))
                state.add_fact(
                    ConfidenceCategory.TECH_STACK,
                    ExtractedFact(fact="technology", value=tech_value, confidence="medium", source="research")
                )

        platforms = tech_stack.get("platforms_used", [])
        if platforms:
            boost = min(len(platforms) * 10, 30)
            state.update_score(ConfidenceCategory.TECH_STACK, boost)

    # Products/services give operations hints
    products = profile.get("products", {})
    if products:
        if products.get("main_products") or products.get("services"):
            state.update_score(ConfidenceCategory.OPERATIONS, 20)
        if products.get("pricing_model"):
            state.update_score(ConfidenceCategory.INDUSTRY_CONTEXT, 10)

    # Team info
    team = profile.get("team", {})
    if team:
        if team.get("hiring_roles"):
            state.update_score(ConfidenceCategory.OPERATIONS, 15)
            state.update_score(ConfidenceCategory.BUYING_SIGNALS, 10)  # Growth signal

    # Recent activity
    activity = profile.get("activity", {})
    if activity:
        if activity.get("recent_news"):
            state.update_score(ConfidenceCategory.COMPANY_BASICS, 5)

    # Recalculate gaps after all updates
    state.recalculate_gaps()

    return state


def update_confidence_from_analysis(
    state: ConfidenceState,
    analysis: AnswerAnalysis,
) -> ConfidenceState:
    """
    Update confidence state based on answer analysis.

    Applies confidence boosts and adds extracted facts.
    """
    # Apply confidence boosts
    for category, boost in analysis.confidence_boosts.items():
        if isinstance(category, str):
            category = ConfidenceCategory(category)
        state.update_score(category, boost)

    # Add extracted facts
    for category, facts in analysis.extracted_facts.items():
        if isinstance(category, str):
            category = ConfidenceCategory(category)
        for fact in facts:
            state.add_fact(category, fact)

    # Increment question count
    state.questions_asked += 1

    # Recalculate
    state.recalculate_gaps()

    return state
