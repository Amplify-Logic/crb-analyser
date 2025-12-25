"""
Tests for Phase 4 Skills (Followup Scheduler, Upsell Identifier)
"""

import pytest
from unittest.mock import MagicMock

from src.skills import get_skill, SkillContext
from src.skills.analysis.followup_scheduler import (
    FollowupSchedulerSkill,
    FOLLOW_UP_TIMING,
    EMAIL_TEMPLATES,
)
from src.skills.analysis.upsell_identifier import (
    UpsellIdentifierSkill,
    UPSELL_THRESHOLDS,
    TIER_FEATURES,
)


# ==================== Followup Scheduler Tests ====================

class TestFollowupSchedulerSkill:
    """Tests for the FollowupSchedulerSkill."""

    def test_skill_discovery(self):
        """Test that the skill can be discovered by name."""
        from src.skills import registry
        registry._registry = None

        skill = get_skill("followup-scheduler")
        assert skill is not None
        assert skill.name == "followup-scheduler"

    def test_skill_metadata(self):
        """Test skill metadata is correct."""
        skill = FollowupSchedulerSkill()
        assert skill.name == "followup-scheduler"
        assert skill.version == "1.0.0"
        assert skill.requires_llm is False  # LLM is optional

    def test_follow_up_timing_defined(self):
        """Test follow-up timing templates are defined."""
        assert "simple" in FOLLOW_UP_TIMING
        assert "medium" in FOLLOW_UP_TIMING
        assert "complex" in FOLLOW_UP_TIMING

        for complexity, timing in FOLLOW_UP_TIMING.items():
            assert "first_check" in timing
            assert "final_check" in timing

    def test_assess_complexity_simple(self):
        """Test complexity assessment for simple reports."""
        skill = FollowupSchedulerSkill()

        report = {
            "findings": [{"id": "f1"}, {"id": "f2"}],
            "recommendations": [
                {"id": "r1", "our_recommendation": "off_the_shelf"}
            ],
            "verdict": {"decision": "go"},
        }
        quick_wins = [{"id": "qw1"}, {"id": "qw2"}]

        complexity = skill._assess_complexity(report, quick_wins)
        assert complexity == "simple"

    def test_assess_complexity_complex(self):
        """Test complexity assessment for complex reports."""
        skill = FollowupSchedulerSkill()

        report = {
            "findings": [{"id": f"f{i}"} for i in range(8)],
            "recommendations": [
                {"id": "r1", "our_recommendation": "custom_solution"},
                {"id": "r2", "our_recommendation": "custom_solution"},
                {"id": "r3", "our_recommendation": "off_the_shelf"},
                {"id": "r4", "our_recommendation": "off_the_shelf"},
                {"id": "r5", "our_recommendation": "off_the_shelf"},
            ],
            "verdict": {"decision": "caution"},
        }
        quick_wins = []

        complexity = skill._assess_complexity(report, quick_wins)
        assert complexity == "complex"

    def test_calculate_engagement_score_base(self):
        """Test base engagement score calculation."""
        skill = FollowupSchedulerSkill()

        signals = {}
        score = skill._calculate_engagement_score(signals)
        assert score == 50  # Base score

    def test_calculate_engagement_score_positive(self):
        """Test engagement score with positive signals."""
        skill = FollowupSchedulerSkill()

        signals = {
            "report_viewed": True,
            "report_downloaded": True,
            "quick_win_clicked": True,
            "replied_to_email": True,
        }
        score = skill._calculate_engagement_score(signals)
        assert score > 80

    def test_calculate_engagement_score_negative(self):
        """Test engagement score with negative signals."""
        skill = FollowupSchedulerSkill()

        signals = {
            "bounced_email": True,
            "days_since_report": 45,
        }
        score = skill._calculate_engagement_score(signals)
        assert score < 30

    def test_generate_schedule_simple(self):
        """Test schedule generation for simple complexity."""
        skill = FollowupSchedulerSkill()

        schedule = skill._generate_schedule(
            complexity="simple",
            customer_tier="ai",
            engagement_score=60,
            quick_wins=[{"title": "Online booking"}],
        )

        assert len(schedule) >= 3
        assert schedule[0]["type"] == "first_check"
        assert schedule[-1]["type"] == "final_check"
        assert all("timing_days" in s for s in schedule)

    def test_generate_schedule_human_tier(self):
        """Test schedule includes calls for human tier."""
        skill = FollowupSchedulerSkill()

        schedule = skill._generate_schedule(
            complexity="medium",
            customer_tier="human",
            engagement_score=70,
            quick_wins=[],
        )

        # Human tier should have at least one call
        has_call = any(s["channel"] == "call" for s in schedule)
        assert has_call

    def test_get_default_templates(self):
        """Test default email templates generation."""
        skill = FollowupSchedulerSkill()

        templates = skill._get_default_templates(
            schedule=[{"type": "first_check"}],
            quick_wins=[{"title": "Online booking"}],
            company_name="Test Company",
        )

        assert "first_check" in templates
        assert "subject" in templates["first_check"]
        assert "body" in templates["first_check"]

    def test_get_escalation_triggers(self):
        """Test escalation trigger generation."""
        skill = FollowupSchedulerSkill()

        triggers = skill._get_escalation_triggers(
            complexity="complex",
            customer_tier="human",
        )

        assert len(triggers) > 3
        assert any("response" in t.lower() for t in triggers)

    @pytest.mark.asyncio
    async def test_skill_execution_success(self):
        """Test successful skill execution."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{"templates": {}}''')]
        mock_client.messages.create.return_value = mock_response

        skill = FollowupSchedulerSkill(client=mock_client)

        context = SkillContext(
            industry="dental",
            metadata={
                "report": {
                    "findings": [{"id": "f1"}],
                    "recommendations": [{"id": "r1", "our_recommendation": "off_the_shelf"}],
                    "verdict": {"decision": "go"},
                },
                "quick_wins": [{"title": "Online booking"}],
                "customer_tier": "ai",
            }
        )

        result = await skill.run(context)

        assert result.success is True
        assert "follow_up_schedule" in result.data
        assert "email_templates" in result.data
        assert "engagement_score" in result.data
        assert "recommended_touchpoints" in result.data


# ==================== Upsell Identifier Tests ====================

class TestUpsellIdentifierSkill:
    """Tests for the UpsellIdentifierSkill."""

    def test_skill_discovery(self):
        """Test that the skill can be discovered by name."""
        from src.skills import registry
        registry._registry = None

        skill = get_skill("upsell-identifier")
        assert skill is not None
        assert skill.name == "upsell-identifier"

    def test_skill_metadata(self):
        """Test skill metadata is correct."""
        skill = UpsellIdentifierSkill()
        assert skill.name == "upsell-identifier"
        assert skill.version == "1.0.0"
        assert skill.requires_llm is False  # LLM is optional

    def test_upsell_thresholds_defined(self):
        """Test upsell thresholds are defined."""
        assert "complexity_score" in UPSELL_THRESHOLDS
        assert "custom_recommendations" in UPSELL_THRESHOLDS
        assert "total_roi_potential" in UPSELL_THRESHOLDS

    def test_tier_features_defined(self):
        """Test tier features are defined."""
        assert "ai" in TIER_FEATURES
        assert "human" in TIER_FEATURES
        assert "price" in TIER_FEATURES["human"]

    def test_analyze_signals_simple(self):
        """Test signal analysis for simple report."""
        skill = UpsellIdentifierSkill()

        report = {
            "findings": [{"id": "f1", "customer_value_score": 5}],
            "recommendations": [
                {"id": "r1", "our_recommendation": "off_the_shelf"}
            ],
            "verdict": {"decision": "go"},
        }

        signals = skill._analyze_signals(report, {}, {})

        assert signals["complexity_score"] < 6
        assert signals["custom_dev_needed"] is False
        assert signals["custom_recommendations"] == 0

    def test_analyze_signals_complex_custom(self):
        """Test signal analysis with custom solutions."""
        skill = UpsellIdentifierSkill()

        report = {
            "findings": [
                {"id": "f1", "customer_value_score": 9},
                {"id": "f2", "business_health_score": 8},
                {"id": "f3", "customer_value_score": 9},
            ],
            "recommendations": [
                {"id": "r1", "our_recommendation": "custom_solution", "roi_detail": {"financial_impact": {"annual_savings": 30000}}},
                {"id": "r2", "our_recommendation": "custom_solution", "roi_detail": {"financial_impact": {"annual_savings": 25000}}},
                {"id": "r3", "our_recommendation": "off_the_shelf"},
            ],
            "verdict": {"decision": "caution"},
        }

        signals = skill._analyze_signals(report, {}, {})

        assert signals["custom_dev_needed"] is True
        assert signals["custom_recommendations"] == 2
        assert signals["high_value_findings"] >= 2
        assert signals["total_roi_potential"] == 55000

    def test_evaluate_upsell_not_recommended(self):
        """Test upsell not recommended for simple cases."""
        skill = UpsellIdentifierSkill()

        signals = {
            "complexity_score": 2,
            "custom_dev_needed": False,
            "high_value_opportunity": False,
            "stuck_indicators": False,
            "mid_market_company": False,
        }

        recommended, confidence, reason = skill._evaluate_upsell(signals)
        assert recommended is False

    def test_evaluate_upsell_recommended_custom_dev(self):
        """Test upsell recommended for custom dev cases."""
        skill = UpsellIdentifierSkill()

        signals = {
            "complexity_score": 7,
            "custom_dev_needed": True,
            "high_value_opportunity": True,
            "stuck_indicators": False,
            "mid_market_company": True,
        }

        recommended, confidence, reason = skill._evaluate_upsell(signals)
        assert recommended is True
        assert confidence in ["high", "medium"]

    def test_generate_pitch_points(self):
        """Test pitch point generation."""
        skill = UpsellIdentifierSkill()

        signals = {
            "custom_dev_needed": True,
            "custom_recommendations": 2,
            "complexity_score": 7,
            "findings_count": 5,
            "recommendations_count": 4,
            "high_value_opportunity": True,
            "total_roi_potential": 60000,
            "stuck_indicators": False,
        }

        points = skill._generate_pitch_points(signals, {}, "dental")

        assert len(points) >= 2
        assert all("point" in p for p in points)
        assert all("evidence" in p for p in points)

    def test_determine_timing_immediate(self):
        """Test immediate timing for stuck customers."""
        skill = UpsellIdentifierSkill()

        signals = {"stuck_indicators": True, "custom_dev_needed": False, "complexity_score": 5}
        timing = skill._determine_timing(signals, {})
        assert timing == "immediate"

    def test_determine_timing_after_action(self):
        """Test timing for new reports."""
        skill = UpsellIdentifierSkill()

        signals = {"stuck_indicators": False, "custom_dev_needed": False, "complexity_score": 5}
        engagement = {"days_since_report": 1}
        timing = skill._determine_timing(signals, engagement)
        assert timing == "after_first_action"

    def test_get_default_approach(self):
        """Test default approach generation."""
        skill = UpsellIdentifierSkill()

        # Stuck customer
        approach = skill._get_default_approach({"stuck_indicators": True, "custom_dev_needed": False, "high_value_opportunity": False})
        assert "unstuck" in approach.lower()

        # Custom dev needed
        approach = skill._get_default_approach({"stuck_indicators": False, "custom_dev_needed": True, "high_value_opportunity": False})
        assert "technical" in approach.lower()

    @pytest.mark.asyncio
    async def test_skill_execution_no_upsell(self):
        """Test skill execution when no upsell recommended."""
        skill = UpsellIdentifierSkill()

        context = SkillContext(
            industry="dental",
            metadata={
                "report": {
                    "findings": [{"id": "f1"}],
                    "recommendations": [{"id": "r1", "our_recommendation": "off_the_shelf"}],
                    "verdict": {"decision": "go"},
                },
                "current_tier": "ai",
            }
        )

        result = await skill.run(context)

        assert result.success is True
        assert result.data["upsell_recommended"] is False

    @pytest.mark.asyncio
    async def test_skill_execution_already_human_tier(self):
        """Test skill execution for human tier customer."""
        skill = UpsellIdentifierSkill()

        context = SkillContext(
            industry="dental",
            metadata={
                "report": {},
                "current_tier": "human",
            }
        )

        result = await skill.run(context)

        assert result.success is True
        assert result.data["upsell_recommended"] is False
        assert "already on human tier" in result.data["reason"].lower()

    @pytest.mark.asyncio
    async def test_skill_execution_upsell_recommended(self):
        """Test skill execution when upsell is recommended."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{"approach": "Custom approach"}''')]
        mock_client.messages.create.return_value = mock_response

        skill = UpsellIdentifierSkill(client=mock_client)

        context = SkillContext(
            industry="dental",
            metadata={
                "report": {
                    "findings": [
                        {"id": "f1", "customer_value_score": 9},
                        {"id": "f2", "business_health_score": 9},
                        {"id": "f3", "customer_value_score": 8},
                    ],
                    "recommendations": [
                        {"id": "r1", "our_recommendation": "custom_solution", "roi_detail": {"financial_impact": {"annual_savings": 30000}}},
                        {"id": "r2", "our_recommendation": "custom_solution", "roi_detail": {"financial_impact": {"annual_savings": 30000}}},
                    ],
                    "verdict": {"decision": "caution"},
                },
                "current_tier": "ai",
                "company_context": {"employee_count": 25},
            }
        )

        result = await skill.run(context)

        assert result.success is True
        assert result.data["upsell_recommended"] is True
        assert "recommendation" in result.data
        assert result.data["recommendation"]["target_tier"] == "human"
        assert "pitch_points" in result.data
        assert len(result.data["pitch_points"]) > 0
