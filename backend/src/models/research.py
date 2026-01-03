"""
Research Models

Schemas for company research and dynamic questionnaire generation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ConfidenceLevel(str, Enum):
    """Confidence level for research findings."""
    HIGH = "high"      # Found in multiple reliable sources
    MEDIUM = "medium"  # Found in one source or inferred
    LOW = "low"        # Estimated/guessed
    UNKNOWN = "unknown"


class ResearchedField(BaseModel):
    """A field with its value and confidence."""
    value: Any
    confidence: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    source: Optional[str] = None
    source_url: Optional[str] = None


# ============================================================================
# COMPANY PROFILE (Output of Pre-Research Agent)
# ============================================================================

class CompanyBasics(BaseModel):
    """Basic company information."""
    name: ResearchedField
    website: Optional[str] = None
    description: Optional[ResearchedField] = None
    tagline: Optional[ResearchedField] = None
    founded_year: Optional[ResearchedField] = None
    headquarters: Optional[ResearchedField] = None


class CompanySize(BaseModel):
    """Company size and scale metrics."""
    employee_count: Optional[ResearchedField] = None
    employee_range: Optional[ResearchedField] = None  # "51-200"
    revenue_estimate: Optional[ResearchedField] = None
    funding_raised: Optional[ResearchedField] = None
    funding_stage: Optional[ResearchedField] = None  # "Series A", "Bootstrapped"


class IndustryInfo(BaseModel):
    """Industry and market information."""
    primary_industry: Optional[ResearchedField] = None
    sub_industry: Optional[ResearchedField] = None
    business_model: Optional[ResearchedField] = None  # "B2B SaaS", "B2C E-commerce"
    target_market: Optional[ResearchedField] = None
    competitors: Optional[List[ResearchedField]] = None


class ProductsServices(BaseModel):
    """Products and services offered."""
    main_products: Optional[List[ResearchedField]] = None
    services: Optional[List[ResearchedField]] = None
    pricing_model: Optional[ResearchedField] = None  # "Subscription", "One-time"
    key_features: Optional[List[str]] = None

    @field_validator('key_features', mode='before')
    @classmethod
    def parse_key_features(cls, v):
        """Convert string, dict, or nested lists to flat list of strings."""
        if v is None:
            return None
        if isinstance(v, str):
            # Split by comma or newline
            return [f.strip() for f in v.replace('\n', ',').split(',') if f.strip()]
        if isinstance(v, dict):
            # LLM returned dict like {'feature_name': 'description'} - extract values
            return list(v.values()) if v else None
        if isinstance(v, list):
            # Flatten nested lists - LLM sometimes returns [[feature1], [feature2]]
            result = []
            for item in v:
                if isinstance(item, list):
                    # Flatten: extract strings from nested list
                    result.extend(str(x) for x in item if x)
                elif isinstance(item, str):
                    result.append(item)
                elif item is not None:
                    result.append(str(item))
            return result if result else None
        return None


class TechStack(BaseModel):
    """Technology stack and tools."""
    technologies_detected: Optional[List[ResearchedField]] = None  # From job postings, website
    platforms_used: Optional[List[ResearchedField]] = None  # Salesforce, HubSpot, etc.
    infrastructure: Optional[ResearchedField] = None  # AWS, GCP, etc.


class TeamLeadership(BaseModel):
    """Leadership and team information."""
    founders: Optional[List[ResearchedField]] = None
    key_executives: Optional[List[ResearchedField]] = None
    team_size_by_dept: Optional[Dict[str, ResearchedField]] = None  # {"engineering": 20, "sales": 10}
    hiring_roles: Optional[List[str]] = None  # Currently hiring for

    @field_validator('hiring_roles', mode='before')
    @classmethod
    def parse_hiring_roles(cls, v):
        """Convert string to list if needed."""
        if isinstance(v, str):
            return [r.strip() for r in v.replace('\n', ',').split(',') if r.strip()]
        return v


class RecentActivity(BaseModel):
    """Recent news and activity."""
    recent_news: Optional[List[ResearchedField]] = None
    press_releases: Optional[List[ResearchedField]] = None
    social_presence: Optional[Dict[str, str]] = None  # {"linkedin": url, "twitter": url}
    content_themes: Optional[List[str]] = None  # What they talk about

    @field_validator('content_themes', mode='before')
    @classmethod
    def parse_content_themes(cls, v):
        """Convert string to list if needed."""
        if isinstance(v, str):
            return [t.strip() for t in v.replace('\n', ',').split(',') if t.strip()]
        return v

    @field_validator('social_presence', mode='before')
    @classmethod
    def parse_social_presence(cls, v):
        """Convert string, list, or dict to proper dict format with string values."""
        if v is None:
            return None
        if isinstance(v, str):
            # If it's a description, try to extract platforms mentioned
            result = {}
            if 'linkedin' in v.lower():
                result['linkedin'] = 'active'
            if 'twitter' in v.lower() or 'x.com' in v.lower():
                result['twitter'] = 'active'
            if 'facebook' in v.lower():
                result['facebook'] = 'active'
            if 'instagram' in v.lower():
                result['instagram'] = 'active'
            if 'youtube' in v.lower():
                result['youtube'] = 'active'
            if not result:
                result['notes'] = v
            return result
        if isinstance(v, list):
            # LLM returned list like [{'platform': 'LinkedIn', 'url': '...'}]
            result = {}
            for item in v:
                if isinstance(item, dict):
                    platform = item.get('platform', item.get('name', '')).lower()
                    url = item.get('url', item.get('link', 'active'))
                    if platform:
                        result[platform] = str(url) if url else 'active'
                elif isinstance(item, str):
                    # Just a platform name
                    result[item.lower()] = 'active'
            return result if result else None
        if isinstance(v, dict):
            # Normalize dict values - LLM sometimes returns booleans instead of strings
            result = {}
            for key, val in v.items():
                if isinstance(val, bool):
                    result[key] = 'active' if val else 'inactive'
                elif val is None:
                    result[key] = 'unknown'
                else:
                    result[key] = str(val)
            return result
        return v


class CompanyProfile(BaseModel):
    """
    Complete company profile from pre-research.

    This is the output of the Pre-Research Agent.
    """
    # Metadata
    research_id: Optional[str] = None
    researched_at: datetime = Field(default_factory=datetime.utcnow)
    research_quality_score: int = Field(default=0, ge=0, le=100)  # Overall confidence
    sources_used: List[str] = Field(default_factory=list)

    @field_validator('sources_used', mode='before')
    @classmethod
    def parse_sources_used(cls, v):
        """Convert list of dicts to list of strings if needed."""
        if v is None:
            return []
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, dict):
                    # Extract URL or name from dict
                    source = item.get('url', item.get('source', item.get('name', str(item))))
                    result.append(str(source))
                elif isinstance(item, str):
                    result.append(item)
                else:
                    result.append(str(item))
            return result
        return v

    # Company data
    basics: CompanyBasics
    size: Optional[CompanySize] = None
    industry: Optional[IndustryInfo] = None
    products: Optional[ProductsServices] = None
    tech_stack: Optional[TechStack] = None
    team: Optional[TeamLeadership] = None
    activity: Optional[RecentActivity] = None

    # Raw data for reference
    raw_website_content: Optional[str] = None
    raw_search_results: Optional[List[Dict[str, Any]]] = None


# ============================================================================
# DYNAMIC QUESTIONNAIRE
# ============================================================================

class QuestionPurpose(str, Enum):
    """Why we're asking this question."""
    CONFIRM = "confirm"        # Confirm something we found
    CLARIFY = "clarify"        # Clarify uncertain info
    DISCOVER = "discover"      # Can't find publicly
    DEEP_DIVE = "deep_dive"    # Industry-specific deep question


class DynamicQuestion(BaseModel):
    """A dynamically generated question."""
    id: str
    question: str
    type: str  # text, textarea, select, multi_select, scale, yes_no, number
    purpose: QuestionPurpose

    # Why this question
    rationale: str  # "We couldn't find your team size publicly"

    # Pre-filled from research
    prefilled_value: Optional[Any] = None
    prefilled_confidence: Optional[ConfidenceLevel] = None

    # Question config
    required: bool = True
    options: Optional[List[Dict[str, str]]] = None  # For select/multi_select
    placeholder: Optional[str] = None
    min_value: Optional[int] = None
    max_value: Optional[int] = None

    # Grouping
    section: str = "general"
    priority: int = 1  # Lower = more important

    @field_validator('options', mode='before')
    @classmethod
    def parse_options(cls, v):
        """Convert string options to dict format."""
        if v is None:
            return v
        if isinstance(v, list):
            result = []
            for opt in v:
                if isinstance(opt, str):
                    # Convert string to {value, label}
                    result.append({"value": opt.lower().replace(' ', '_'), "label": opt})
                elif isinstance(opt, dict):
                    result.append(opt)
                else:
                    result.append({"value": str(opt), "label": str(opt)})
            return result
        return v


class DynamicQuestionnaire(BaseModel):
    """
    A questionnaire tailored to a specific company.

    Generated based on CompanyProfile - asks only what we need.
    """
    company_name: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    # Research summary shown to user
    research_summary: str  # "We found that Aquablu is a water tech company..."
    confirmed_facts: List[Dict[str, Any]]  # Facts we're confident about

    # The questions
    questions: List[DynamicQuestion]
    total_questions: int
    estimated_time_minutes: int

    # Sections
    sections: List[Dict[str, Any]]  # [{id, title, description, question_ids}]


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================

class StartResearchRequest(BaseModel):
    """Request to start company research."""
    company_name: str = Field(..., min_length=1)
    website_url: Optional[str] = None
    additional_context: Optional[str] = None  # User can provide hints


class ResearchStatusResponse(BaseModel):
    """Research progress status."""
    research_id: str
    status: str  # "pending", "researching", "generating_questions", "ready", "failed"
    progress_percent: int
    current_step: Optional[str] = None
    error: Optional[str] = None


class ResearchCompleteResponse(BaseModel):
    """Response when research is complete."""
    research_id: str
    company_profile: CompanyProfile
    questionnaire: DynamicQuestionnaire


class SaveResearchAnswersRequest(BaseModel):
    """Request to save questionnaire answers."""
    answers: Dict[str, Any]  # question_id -> answer
    tier: str = "professional"  # "free" or "professional"


# ============================================================================
# RELIABLE SOURCES CONFIG
# ============================================================================

RELIABLE_SOURCES = {
    "company_website": {
        "priority": 1,
        "confidence": ConfidenceLevel.HIGH,
        "description": "Company's own website",
    },
    "linkedin": {
        "priority": 2,
        "confidence": ConfidenceLevel.HIGH,
        "description": "LinkedIn company page",
        "url_pattern": "linkedin.com/company/",
    },
    "crunchbase": {
        "priority": 3,
        "confidence": ConfidenceLevel.HIGH,
        "description": "Crunchbase profile",
        "url_pattern": "crunchbase.com/organization/",
    },
    "glassdoor": {
        "priority": 4,
        "confidence": ConfidenceLevel.MEDIUM,
        "description": "Glassdoor company profile",
    },
    "news_articles": {
        "priority": 5,
        "confidence": ConfidenceLevel.MEDIUM,
        "description": "Recent news articles",
    },
    "job_postings": {
        "priority": 6,
        "confidence": ConfidenceLevel.MEDIUM,
        "description": "Job postings (for tech stack, team size)",
    },
}
