"""Tests for Four Options models."""
import pytest
from src.models.four_options import (
    OptionType,
    OptionScore,
    BuyOption,
    ConnectOption,
    BuildOption,
    HireOption,
    FourOptionRecommendation,
    CostEstimate,
)


class TestOptionScore:
    """Test OptionScore model."""

    def test_create_option_score(self):
        """Test creating an option score."""
        score = OptionScore(
            option=OptionType.BUY,
            score=85.0,
            breakdown={
                "capability_match": 100,
                "preference_match": 80,
                "budget_fit": 90,
                "time_fit": 70,
                "value_ratio": 85,
            },
            match_reasons=["No technical skills needed", "Within budget"],
            concern_reasons=[],
            is_recommended=True,
        )
        assert score.option == OptionType.BUY
        assert score.score == 85.0
        assert score.is_recommended is True
        assert len(score.match_reasons) == 2


class TestBuyOption:
    """Test BuyOption model."""

    def test_create_buy_option(self):
        """Test creating a BUY option."""
        option = BuyOption(
            vendor_slug="calendly",
            vendor_name="Calendly",
            price="12/mo",
            setup_time="30 minutes",
            pros=["Easy setup", "No technical skills"],
            cons=["Limited customization"],
            website="https://calendly.com",
        )
        assert option.vendor_name == "Calendly"
        assert option.price == "12/mo"


class TestFourOptionRecommendation:
    """Test FourOptionRecommendation model."""

    def test_create_recommendation_with_all_options(self):
        """Test creating recommendation with all 4 options."""
        rec = FourOptionRecommendation(
            finding_id="finding-001",
            finding_title="Automate appointment reminders",
            buy=BuyOption(
                vendor_slug="calendly",
                vendor_name="Calendly",
                price="12/mo",
                setup_time="30 minutes",
                pros=["Easy"],
                cons=["Basic"],
            ),
            connect=ConnectOption(
                integration_platform="Make",
                connects_to=["HubSpot", "Gmail"],
                estimated_hours=4,
                complexity="low",
            ),
            build=BuildOption(
                recommended_stack=["Claude Code", "Supabase"],
                estimated_cost="2K-5K",
                estimated_hours="20-40",
                skills_needed=["Python"],
                ai_coding_viable=True,
            ),
            hire=HireOption(
                service_type="Freelancer",
                estimated_cost="500-1K",
                estimated_timeline="1 week",
                where_to_find=["Upwork"],
            ),
            scores=[
                OptionScore(
                    option=OptionType.BUY,
                    score=92,
                    breakdown={},
                    match_reasons=["Easy"],
                    concern_reasons=[],
                    is_recommended=True,
                ),
            ],
            recommended=OptionType.BUY,
            recommendation_reasoning="Best match for your profile",
        )
        assert rec.recommended == OptionType.BUY
        assert rec.buy.vendor_name == "Calendly"
        assert len(rec.scores) == 1
