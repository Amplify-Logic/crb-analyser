"""
User Profile Model

Captures implementation capability, preference, and budget
for personalized 4-option recommendations.
"""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class CapabilityLevel(str, Enum):
    """Technical capability levels for option scoring."""
    NON_TECHNICAL = "non_technical"
    TUTORIAL_FOLLOWER = "tutorial_follower"
    AUTOMATION_USER = "automation_user"
    AI_CODER = "ai_coder"
    HAS_DEVELOPERS = "has_developers"


class ImplementationPreference(str, Enum):
    """User's preferred approach to solving problems."""
    BUY = "buy"
    CONNECT = "connect"
    BUILD = "build"
    HIRE = "hire"


class BudgetTier(str, Enum):
    """Budget comfort level for automation tools."""
    LOW = "low"              # Under 50/month
    MODERATE = "moderate"    # 50-200/month
    COMFORTABLE = "comfortable"  # 200-500/month
    HIGH = "high"            # 500+/month or 2K-10K one-time


class Urgency(str, Enum):
    """How soon user needs solution working."""
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    THIS_QUARTER = "this_quarter"
    NO_RUSH = "no_rush"


# Industry defaults when quiz answers are missing
INDUSTRY_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "dental": {
        "capability": CapabilityLevel.NON_TECHNICAL,
        "preference": ImplementationPreference.BUY,
        "budget": BudgetTier.MODERATE,
    },
    "legal": {
        "capability": CapabilityLevel.TUTORIAL_FOLLOWER,
        "preference": ImplementationPreference.BUY,
        "budget": BudgetTier.COMFORTABLE,
    },
    "tech_startup": {
        "capability": CapabilityLevel.HAS_DEVELOPERS,
        "preference": ImplementationPreference.BUILD,
        "budget": BudgetTier.LOW,
    },
    "ecommerce": {
        "capability": CapabilityLevel.AUTOMATION_USER,
        "preference": ImplementationPreference.CONNECT,
        "budget": BudgetTier.MODERATE,
    },
    "healthcare": {
        "capability": CapabilityLevel.NON_TECHNICAL,
        "preference": ImplementationPreference.HIRE,
        "budget": BudgetTier.COMFORTABLE,
    },
    "consulting": {
        "capability": CapabilityLevel.AUTOMATION_USER,
        "preference": ImplementationPreference.CONNECT,
        "budget": BudgetTier.MODERATE,
    },
    "real_estate": {
        "capability": CapabilityLevel.TUTORIAL_FOLLOWER,
        "preference": ImplementationPreference.BUY,
        "budget": BudgetTier.COMFORTABLE,
    },
}

# Fallback defaults
DEFAULT_PROFILE: Dict[str, Any] = {
    "capability": CapabilityLevel.TUTORIAL_FOLLOWER,
    "preference": ImplementationPreference.BUY,
    "budget": BudgetTier.MODERATE,
}


class UserProfile(BaseModel):
    """
    User's implementation profile for recommendation scoring.

    Captures capability, preference, budget, and urgency to
    calculate personalized match scores for BUY/CONNECT/BUILD/HIRE.
    """
    capability: CapabilityLevel = Field(
        ...,
        description="Technical capability level"
    )
    preference: ImplementationPreference = Field(
        ...,
        description="Preferred implementation approach"
    )
    budget: BudgetTier = Field(
        ...,
        description="Budget comfort level"
    )
    urgency: Optional[Urgency] = Field(
        default=None,
        description="How soon solution is needed"
    )
    existing_stack_api_ready: bool = Field(
        default=False,
        description="Whether existing tools have good API support"
    )
    industry: Optional[str] = Field(
        default=None,
        description="User's industry for context"
    )

    @classmethod
    def from_quiz_answers(
        cls,
        answers: Dict[str, Any],
        existing_stack_api_ready: bool = False,
    ) -> "UserProfile":
        """
        Create UserProfile from quiz answers dict.

        Falls back to industry defaults, then global defaults.
        """
        industry = answers.get("industry", "")
        industry_defaults = INDUSTRY_DEFAULTS.get(industry, DEFAULT_PROFILE)

        # Get capability with fallback
        capability_str = answers.get("implementation_capability")
        if capability_str:
            capability = CapabilityLevel(capability_str)
        else:
            capability = industry_defaults.get("capability", DEFAULT_PROFILE["capability"])

        # Get preference with fallback
        preference_str = answers.get("implementation_preference")
        if preference_str:
            preference = ImplementationPreference(preference_str)
        else:
            preference = industry_defaults.get("preference", DEFAULT_PROFILE["preference"])

        # Get budget with fallback
        budget_str = answers.get("budget_comfort")
        if budget_str:
            budget = BudgetTier(budget_str)
        else:
            budget = industry_defaults.get("budget", DEFAULT_PROFILE["budget"])

        # Get urgency (optional, no default)
        urgency_str = answers.get("implementation_urgency")
        urgency = Urgency(urgency_str) if urgency_str else None

        return cls(
            capability=capability,
            preference=preference,
            budget=budget,
            urgency=urgency,
            existing_stack_api_ready=existing_stack_api_ready,
            industry=industry if industry else None,
        )
