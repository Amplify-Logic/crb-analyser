"""Tests for UserProfile model."""
import pytest
from src.models.user_profile import (
    UserProfile,
    CapabilityLevel,
    ImplementationPreference,
    BudgetTier,
    Urgency,
)


class TestUserProfile:
    """Test UserProfile model creation and validation."""

    def test_create_user_profile_minimal(self):
        """Test creating profile with required fields only."""
        profile = UserProfile(
            capability=CapabilityLevel.AUTOMATION_USER,
            preference=ImplementationPreference.CONNECT,
            budget=BudgetTier.MODERATE,
        )
        assert profile.capability == CapabilityLevel.AUTOMATION_USER
        assert profile.preference == ImplementationPreference.CONNECT
        assert profile.budget == BudgetTier.MODERATE
        assert profile.urgency is None
        assert profile.existing_stack_api_ready is False

    def test_create_user_profile_full(self):
        """Test creating profile with all fields."""
        profile = UserProfile(
            capability=CapabilityLevel.AI_CODER,
            preference=ImplementationPreference.BUILD,
            budget=BudgetTier.COMFORTABLE,
            urgency=Urgency.THIS_QUARTER,
            existing_stack_api_ready=True,
            industry="tech_startup",
        )
        assert profile.capability == CapabilityLevel.AI_CODER
        assert profile.urgency == Urgency.THIS_QUARTER
        assert profile.existing_stack_api_ready is True
        assert profile.industry == "tech_startup"

    def test_from_quiz_answers(self):
        """Test creating profile from quiz answers dict."""
        answers = {
            "implementation_capability": "automation_user",
            "implementation_preference": "connect",
            "budget_comfort": "moderate",
            "implementation_urgency": "this_month",
            "industry": "consulting",
        }
        profile = UserProfile.from_quiz_answers(answers)
        assert profile.capability == CapabilityLevel.AUTOMATION_USER
        assert profile.preference == ImplementationPreference.CONNECT
        assert profile.budget == BudgetTier.MODERATE
        assert profile.urgency == Urgency.THIS_MONTH

    def test_from_quiz_answers_with_defaults(self):
        """Test profile uses defaults when answers missing."""
        answers = {"industry": "dental"}
        profile = UserProfile.from_quiz_answers(answers)
        # Should use industry defaults for dental
        assert profile.capability == CapabilityLevel.NON_TECHNICAL
        assert profile.preference == ImplementationPreference.BUY
        assert profile.budget == BudgetTier.MODERATE
