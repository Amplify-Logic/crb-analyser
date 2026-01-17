"""
Insight models for curated AI/industry insights system.

These models define the structure for storing and retrieving
curated insights from various sources (research, transcripts, articles).
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class InsightType(str, Enum):
    """Types of insights that can be extracted."""
    TREND = "trend"
    FRAMEWORK = "framework"
    QUOTE = "quote"
    CASE_STUDY = "case_study"
    STATISTIC = "statistic"
    PREDICTION = "prediction"


class CredibilityLevel(str, Enum):
    """Credibility level of supporting data."""
    PEER_REVIEWED = "peer_reviewed"
    ACADEMIC = "academic"
    INDUSTRY_RESEARCH = "industry_research"
    INDUSTRY_DATA = "industry_data"
    ANALYST = "analyst"
    ANECDOTAL = "anecdotal"


class UserStage(str, Enum):
    """User journey stage where insight is relevant."""
    UNAWARE = "unaware"
    CONSIDERING = "considering"
    EARLY_ADOPTER = "early_adopter"
    SCALING = "scaling"


class AudienceRelevance(str, Enum):
    """
    How relevant is this insight for our target audience?

    Target: SMB owner-operators ($500K-$20M) in service businesses
    who want to save time/money and get back to work they love.
    """
    HIGH = "high"      # Directly actionable: "How do I save time/money?"
    MEDIUM = "medium"  # Useful context, not directly actionable
    LOW = "low"        # Interesting but doesn't help their decision


# Audience relevance rules for each surface
SURFACE_RELEVANCE_RULES = {
    "landing": [AudienceRelevance.HIGH],           # Only high - homepage real estate is precious
    "quiz_results": [AudienceRelevance.HIGH],      # Only high - they want answers, not theory
    "report": [AudienceRelevance.HIGH, AudienceRelevance.MEDIUM],  # Context OK in reports
    "email": [AudienceRelevance.HIGH],             # Only high - don't waste their inbox
}


class UseIn(str, Enum):
    """Surfaces where insight can be displayed."""
    REPORT = "report"
    QUIZ_RESULTS = "quiz_results"
    LANDING = "landing"
    EMAIL = "email"


class SupportingData(BaseModel):
    """A piece of data supporting an insight claim."""
    claim: str = Field(..., description="The specific claim or data point")
    source: str = Field(..., description="Source name (e.g., 'McKinsey', 'Stanford HAI')")
    source_url: Optional[str] = Field(None, description="URL to source if available")
    date: Optional[str] = Field(None, description="Date of the data (YYYY-MM or YYYY)")
    credibility: CredibilityLevel = Field(
        default=CredibilityLevel.ANECDOTAL,
        description="Credibility level of this data point"
    )


class InsightSource(BaseModel):
    """Original source of the insight."""
    title: str = Field(..., description="Title of the source content")
    author: Optional[str] = Field(None, description="Author or creator")
    url: Optional[str] = Field(None, description="URL to the source")
    date: Optional[str] = Field(None, description="Publication date (YYYY-MM-DD)")
    type: Optional[str] = Field(None, description="Type: youtube, article, report, etc.")


class InsightTags(BaseModel):
    """Tags for filtering and retrieval."""
    topics: list[str] = Field(
        default_factory=list,
        description="Topic tags (e.g., 'model-selection', 'workflows', 'roi')"
    )
    industries: list[str] = Field(
        default_factory=lambda: ["all"],
        description="Industries this applies to (or 'all')"
    )
    use_in: list[UseIn] = Field(
        default_factory=list,
        description="Surfaces where this can be displayed"
    )
    user_stages: list[UserStage] = Field(
        default_factory=list,
        description="User journey stages where relevant"
    )


class Insight(BaseModel):
    """A curated insight from external content."""
    id: str = Field(..., description="Unique identifier (e.g., 'trend-2026-models-commoditized')")
    type: InsightType = Field(..., description="Type of insight")
    title: str = Field(..., description="Short title for the insight")
    content: str = Field(..., description="The main insight content")
    supporting_data: list[SupportingData] = Field(
        default_factory=list,
        description="Data points supporting this insight"
    )
    actionable_insight: Optional[str] = Field(
        None,
        description="Actionable takeaway for the user"
    )
    tags: InsightTags = Field(
        default_factory=InsightTags,
        description="Tags for filtering and retrieval"
    )
    source: InsightSource = Field(..., description="Original source of the insight")
    extracted_at: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d"),
        description="When this insight was extracted"
    )
    reviewed: bool = Field(
        default=False,
        description="Whether this insight has been human-reviewed"
    )
    audience_relevance: AudienceRelevance = Field(
        default=AudienceRelevance.MEDIUM,
        description="How relevant for SMB owner-operators considering AI automation"
    )
    relevance_reason: Optional[str] = Field(
        None,
        description="Why this relevance level was assigned"
    )
    embedding: Optional[list[float]] = Field(
        None,
        description="Vector embedding for semantic search (excluded from JSON export)"
    )

    class Config:
        use_enum_values = True


class InsightCollection(BaseModel):
    """Collection of insights of a single type."""
    type: InsightType
    description: str
    last_updated: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d")
    )
    insights: list[Insight] = Field(default_factory=list)


class ExtractedInsights(BaseModel):
    """Result of AI extraction from raw content."""
    source: InsightSource
    raw_content_path: Optional[str] = None
    extracted_at: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d")
    )
    insights: list[Insight] = Field(default_factory=list)
    extraction_notes: Optional[str] = None


class InsightSearchQuery(BaseModel):
    """Query parameters for insight retrieval."""
    use_in: Optional[UseIn] = None
    types: Optional[list[InsightType]] = None
    industries: Optional[list[str]] = None
    topics: Optional[list[str]] = None
    user_stage: Optional[UserStage] = None
    reviewed_only: bool = True
    limit: int = Field(default=5, ge=1, le=20)
    # For semantic search
    context_query: Optional[str] = Field(
        None,
        description="Natural language context for semantic matching"
    )


class InsightSearchResult(BaseModel):
    """Result from insight search."""
    insight: Insight
    relevance_score: float = Field(
        default=1.0,
        description="Relevance score (1.0 = exact match, <1.0 = semantic match)"
    )
    match_reason: Optional[str] = Field(
        None,
        description="Why this insight matched (for debugging)"
    )
