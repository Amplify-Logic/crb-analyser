"""Tests for option scoring algorithm."""
import pytest
from src.services.option_scoring import (
    score_option,
    calculate_capability_match,
    calculate_budget_fit,
    calculate_time_fit,
    get_recommendations,
    SCORING_WEIGHTS,
)
from src.models.user_profile import (
    UserProfile,
    CapabilityLevel,
    ImplementationPreference,
    BudgetTier,
    Urgency,
)
from src.models.four_options import OptionType, CostEstimate


class TestCapabilityMatch:
    """Test capability matching logic."""

    def test_non_technical_scores_high_for_buy(self):
        """Non-technical user should score 100 for BUY."""
        score = calculate_capability_match(
            OptionType.BUY,
            CapabilityLevel.NON_TECHNICAL
        )
        assert score == 100

    def test_non_technical_scores_low_for_build(self):
        """Non-technical user should score very low for BUILD."""
        score = calculate_capability_match(
            OptionType.BUILD,
            CapabilityLevel.NON_TECHNICAL
        )
        assert score <= 20

    def test_ai_coder_scores_high_for_build(self):
        """AI coder should score 100 for BUILD."""
        score = calculate_capability_match(
            OptionType.BUILD,
            CapabilityLevel.AI_CODER
        )
        assert score == 100

    def test_automation_user_scores_high_for_connect(self):
        """Automation user should score 100 for CONNECT."""
        score = calculate_capability_match(
            OptionType.CONNECT,
            CapabilityLevel.AUTOMATION_USER
        )
        assert score == 100


class TestBudgetFit:
    """Test budget fit scoring."""

    def test_low_budget_fits_cheap_option(self):
        """Low budget should fit option under 600/year."""
        cost = CostEstimate(year_one_total=144)  # 12/month
        score = calculate_budget_fit(cost, BudgetTier.LOW)
        assert score >= 80

    def test_low_budget_does_not_fit_expensive(self):
        """Low budget should not fit 5K option."""
        cost = CostEstimate(year_one_total=5000)
        score = calculate_budget_fit(cost, BudgetTier.LOW)
        assert score <= 30


class TestTimeFit:
    """Test time fit scoring."""

    def test_this_week_urgency_fits_1_day(self):
        """This week urgency should fit 1-day option."""
        score = calculate_time_fit("1 day", Urgency.THIS_WEEK)
        assert score == 100

    def test_this_week_urgency_does_not_fit_4_weeks(self):
        """This week urgency should not fit 4-week option."""
        score = calculate_time_fit("4 weeks", Urgency.THIS_WEEK)
        assert score <= 30


class TestFullScoring:
    """Test full option scoring."""

    def test_non_technical_low_budget_recommends_buy(self):
        """Non-technical user with low budget should get BUY recommended."""
        profile = UserProfile(
            capability=CapabilityLevel.NON_TECHNICAL,
            preference=ImplementationPreference.BUY,
            budget=BudgetTier.LOW,
            urgency=Urgency.THIS_MONTH,
        )

        # Mock option costs
        option_costs = {
            OptionType.BUY: CostEstimate(year_one_total=144),
            OptionType.CONNECT: CostEstimate(year_one_total=200),
            OptionType.BUILD: CostEstimate(year_one_total=3000),
            OptionType.HIRE: CostEstimate(year_one_total=5000),
        }
        option_times = {
            OptionType.BUY: "1 day",
            OptionType.CONNECT: "1 week",
            OptionType.BUILD: "3 weeks",
            OptionType.HIRE: "2 weeks",
        }

        recommendations = get_recommendations(
            profile, option_costs, option_times
        )

        assert recommendations[0].option == OptionType.BUY
        assert recommendations[0].is_recommended is True
        assert recommendations[0].score >= 80

    def test_ai_coder_comfortable_budget_considers_build(self):
        """AI coder with comfortable budget should have BUILD score highly."""
        profile = UserProfile(
            capability=CapabilityLevel.AI_CODER,
            preference=ImplementationPreference.BUILD,
            budget=BudgetTier.COMFORTABLE,
            urgency=Urgency.THIS_QUARTER,
        )

        option_costs = {
            OptionType.BUY: CostEstimate(year_one_total=144),
            OptionType.CONNECT: CostEstimate(year_one_total=200),
            OptionType.BUILD: CostEstimate(year_one_total=3000),
            OptionType.HIRE: CostEstimate(year_one_total=5000),
        }
        option_times = {
            OptionType.BUY: "1 day",
            OptionType.CONNECT: "1 week",
            OptionType.BUILD: "3 weeks",
            OptionType.HIRE: "2 weeks",
        }

        recommendations = get_recommendations(
            profile, option_costs, option_times
        )

        # BUILD should be recommended or score highly
        build_score = next(
            r for r in recommendations if r.option == OptionType.BUILD
        )
        assert build_score.score >= 70
