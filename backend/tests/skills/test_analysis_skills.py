"""
Tests for Analysis Skills (Quick Win, Source Validator, Benchmarker, Competitor, Playbook)
"""

import pytest
from unittest.mock import MagicMock

from src.skills import get_skill, SkillContext
from src.skills.analysis.quick_win_identifier import (
    QuickWinIdentifierSkill,
    DEFAULT_THRESHOLDS,
)
from src.skills.analysis.source_validator import (
    SourceValidatorSkill,
    CLAIM_PATTERNS,
)
from src.skills.analysis.industry_benchmarker import (
    IndustryBenchmarkerSkill,
    AI_READINESS_METRICS,
)
from src.skills.analysis.competitor_analyzer import (
    CompetitorAnalyzerSkill,
    INDUSTRY_AI_ADOPTION,
)
from src.skills.analysis.playbook_generator import (
    PlaybookGeneratorSkill,
    IMPLEMENTATION_PHASES,
)


# ==================== Quick Win Identifier Tests ====================

class TestQuickWinIdentifierSkill:
    """Tests for the QuickWinIdentifierSkill."""

    def test_skill_discovery(self):
        """Test that the skill can be discovered by name."""
        from src.skills import registry
        registry._registry = None

        skill = get_skill("quick-win-identifier")
        assert skill is not None
        assert skill.name == "quick-win-identifier"

    def test_skill_metadata(self):
        """Test skill metadata is correct."""
        skill = QuickWinIdentifierSkill()
        assert skill.name == "quick-win-identifier"
        assert skill.version == "1.0.0"
        assert skill.requires_llm is True

    def test_default_thresholds(self):
        """Test default thresholds are defined."""
        assert "max_implementation_hours" in DEFAULT_THRESHOLDS
        assert "min_roi_percentage" in DEFAULT_THRESHOLDS
        assert DEFAULT_THRESHOLDS["max_implementation_hours"] == 40
        assert DEFAULT_THRESHOLDS["min_roi_percentage"] == 100

    def test_score_quick_win_potential(self):
        """Test scoring logic for quick wins."""
        skill = QuickWinIdentifierSkill()

        finding = {
            "id": "f1",
            "title": "Quick scheduling fix",
            "confidence": "high",
            "customer_value_score": 8,
            "business_health_score": 7,
        }
        recommendation = {
            "our_recommendation": "off_the_shelf",
            "options": {
                "off_the_shelf": {"implementation_weeks": 1}
            },
            "roi_percentage": 150,
        }

        score = skill._score_quick_win_potential(finding, recommendation, DEFAULT_THRESHOLDS)

        assert score["qualifies"] is True
        assert score["total_score"] > 50
        assert score["risk"] == "low"

    def test_score_disqualifies_long_implementation(self):
        """Test that long implementations are disqualified."""
        skill = QuickWinIdentifierSkill()

        finding = {"id": "f1", "confidence": "high"}
        recommendation = {
            "our_recommendation": "custom_solution",
            "options": {
                "custom_solution": {"implementation_weeks": 12}  # 240 hours
            },
            "roi_percentage": 200,
        }

        score = skill._score_quick_win_potential(finding, recommendation, DEFAULT_THRESHOLDS)

        assert score["qualifies"] is False
        assert any("too long" in r.lower() for r in score["reasons"])

    @pytest.mark.asyncio
    async def test_skill_execution_success(self):
        """Test successful skill execution."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{
            "quick_wins": [
                {"id": "f1", "why_quick": "Easy setup", "first_step": "Sign up", "expected_result": "50% time saved"}
            ]
        }''')]
        mock_client.messages.create.return_value = mock_response

        skill = QuickWinIdentifierSkill(client=mock_client)

        context = SkillContext(
            industry="dental",
            metadata={
                "findings": [
                    {
                        "id": "f1",
                        "title": "Manual scheduling",
                        "confidence": "high",
                        "customer_value_score": 8,
                    }
                ],
                "recommendations": [
                    {
                        "finding_id": "f1",
                        "our_recommendation": "off_the_shelf",
                        "options": {"off_the_shelf": {"implementation_weeks": 1}},
                        "roi_percentage": 150,
                    }
                ],
            }
        )

        result = await skill.run(context)

        assert result.success is True
        assert "quick_wins" in result.data
        assert "selection_criteria" in result.data

    @pytest.mark.asyncio
    async def test_skill_requires_findings(self):
        """Test skill fails without findings."""
        from src.skills.base import SkillError

        skill = QuickWinIdentifierSkill()

        context = SkillContext(
            industry="dental",
            metadata={"findings": []}
        )

        with pytest.raises(SkillError):
            await skill.execute(context)


# ==================== Source Validator Tests ====================

class TestSourceValidatorSkill:
    """Tests for the SourceValidatorSkill."""

    def test_skill_discovery(self):
        """Test that the skill can be discovered by name."""
        from src.skills import registry
        registry._registry = None

        skill = get_skill("source-validator")
        assert skill is not None
        assert skill.name == "source-validator"

    def test_skill_metadata(self):
        """Test skill metadata is correct."""
        skill = SourceValidatorSkill()
        assert skill.name == "source-validator"
        assert skill.requires_llm is True
        assert skill.requires_knowledge is True

    def test_claim_patterns_defined(self):
        """Test claim patterns are defined."""
        assert len(CLAIM_PATTERNS) > 0
        assert any("%" in p for p in CLAIM_PATTERNS)

    def test_extract_claims(self):
        """Test claim extraction from text."""
        skill = SourceValidatorSkill()

        finding = {
            "title": "Manual scheduling wastes 15 hours per week",
            "description": "35% of practices report scheduling issues. On average, staff spends 2 hours daily on phone calls.",
        }

        claims = skill._extract_claims(finding, None)

        assert len(claims) > 0
        assert any("35%" in c for c in claims)
        assert any("15 hours" in c for c in claims)

    def test_validate_claim_unverified(self):
        """Test claim validation with unverified claim."""
        skill = SourceValidatorSkill()

        claim = "90% of all businesses save money"
        result = skill._validate_claim(claim, {}, None)

        assert result["verified"] is False
        assert "suggested_action" in result

    @pytest.mark.asyncio
    async def test_skill_execution_success(self):
        """Test successful skill execution."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{
            "validations": [
                {"claim": "test claim", "status": "verified", "basis": "Industry knowledge"}
            ]
        }''')]
        mock_client.messages.create.return_value = mock_response

        skill = SourceValidatorSkill(client=mock_client)

        context = SkillContext(
            industry="dental",
            metadata={
                "finding": {
                    "id": "f1",
                    "title": "35% of practices use AI",
                    "description": "Based on industry research.",
                    "confidence": "medium",
                }
            }
        )

        result = await skill.run(context)

        assert result.success is True
        assert "validated_claims" in result.data
        assert "unverified_claims" in result.data
        assert "confidence_adjustment" in result.data


# ==================== Industry Benchmarker Tests ====================

class TestIndustryBenchmarkerSkill:
    """Tests for the IndustryBenchmarkerSkill."""

    def test_skill_discovery(self):
        """Test that the skill can be discovered by name."""
        from src.skills import registry
        registry._registry = None

        skill = get_skill("industry-benchmarker")
        assert skill is not None
        assert skill.name == "industry-benchmarker"

    def test_skill_metadata(self):
        """Test skill metadata is correct."""
        skill = IndustryBenchmarkerSkill()
        assert skill.name == "industry-benchmarker"
        assert skill.requires_llm is True
        assert skill.requires_knowledge is True

    def test_ai_readiness_metrics_defined(self):
        """Test AI readiness metrics are defined."""
        assert "tech_adoption" in AI_READINESS_METRICS
        assert "data_quality" in AI_READINESS_METRICS
        total_weight = sum(m["weight"] for m in AI_READINESS_METRICS.values())
        assert abs(total_weight - 1.0) < 0.01

    def test_extract_company_metrics(self):
        """Test company metrics extraction."""
        skill = IndustryBenchmarkerSkill()

        quiz_answers = {
            "current_tools": ["Calendly", "Slack", "Notion"],
            "data_organization": "organized and structured",
            "processes_documented": "yes, fully documented",
            "team_tech_comfort": 8,
        }

        metrics = skill._extract_company_metrics(quiz_answers, {})

        assert metrics["tech_adoption"] > 30
        assert metrics["data_quality"] >= 70
        assert metrics["process_maturity"] >= 70
        assert metrics["team_capability"] == 80

    def test_calculate_ai_readiness(self):
        """Test AI readiness calculation."""
        skill = IndustryBenchmarkerSkill()

        metrics = {
            "tech_adoption": 70,
            "data_quality": 60,
            "process_maturity": 50,
            "team_capability": 80,
            "budget_availability": 60,
            "leadership_buy_in": 70,
        }

        result = skill._calculate_ai_readiness(metrics, [])

        assert "score" in result
        assert "percentile" in result
        assert 0 <= result["score"] <= 100
        assert 0 <= result["percentile"] <= 100

    @pytest.mark.asyncio
    async def test_skill_execution_success(self):
        """Test successful skill execution."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{
            "recommendations": ["Focus on process documentation", "Increase tech budget"]
        }''')]
        mock_client.messages.create.return_value = mock_response

        skill = IndustryBenchmarkerSkill(client=mock_client)

        context = SkillContext(
            industry="dental",
            quiz_answers={"current_tools": ["Calendly"]},
            metadata={}
        )

        result = await skill.run(context)

        assert result.success is True
        assert "ai_readiness" in result.data
        assert "benchmarks" in result.data
        assert "strengths" in result.data
        assert "gaps" in result.data


# ==================== Competitor Analyzer Tests ====================

class TestCompetitorAnalyzerSkill:
    """Tests for the CompetitorAnalyzerSkill."""

    def test_skill_discovery(self):
        """Test that the skill can be discovered by name."""
        from src.skills import registry
        registry._registry = None

        skill = get_skill("competitor-analyzer")
        assert skill is not None
        assert skill.name == "competitor-analyzer"

    def test_skill_metadata(self):
        """Test skill metadata is correct."""
        skill = CompetitorAnalyzerSkill()
        assert skill.name == "competitor-analyzer"
        assert skill.requires_llm is False  # LLM is optional

    def test_industry_adoption_data(self):
        """Test industry adoption data is defined."""
        assert "dental" in INDUSTRY_AI_ADOPTION
        assert "home-services" in INDUSTRY_AI_ADOPTION

        dental = INDUSTRY_AI_ADOPTION["dental"]
        assert "adoption_rate" in dental
        assert "adoption_trend" in dental
        assert "source" in dental

    def test_assess_risk_high(self):
        """Test risk assessment for high-adoption industry."""
        skill = CompetitorAnalyzerSkill()

        adoption_data = {"adoption_rate": "70%", "adoption_trend": "accelerating"}
        quiz_answers = {"current_tools": []}

        risk = skill._assess_risk(adoption_data, quiz_answers, [])

        assert risk["risk_level"] == "high"
        assert "Immediate" in risk["time_to_act"]

    def test_assess_risk_low(self):
        """Test risk assessment for low-adoption scenario."""
        skill = CompetitorAnalyzerSkill()

        adoption_data = {"adoption_rate": "20%", "adoption_trend": "increasing"}
        quiz_answers = {"current_tools": ["AI scheduler"]}

        risk = skill._assess_risk(adoption_data, quiz_answers, [])

        assert risk["risk_level"] == "low"

    @pytest.mark.asyncio
    async def test_skill_execution_success(self):
        """Test successful skill execution."""
        skill = CompetitorAnalyzerSkill()

        context = SkillContext(
            industry="dental",
            quiz_answers={},
            metadata={"findings": []}
        )

        result = await skill.run(context)

        assert result.success is True
        assert "ai_adoption_rate" in result.data
        assert "common_implementations" in result.data
        assert "risk_assessment" in result.data
        assert "opportunities" in result.data


# ==================== Playbook Generator Tests ====================

class TestPlaybookGeneratorSkill:
    """Tests for the PlaybookGeneratorSkill."""

    def test_skill_discovery(self):
        """Test that the skill can be discovered by name."""
        from src.skills import registry
        registry._registry = None

        skill = get_skill("playbook-generator")
        assert skill is not None
        assert skill.name == "playbook-generator"

    def test_skill_metadata(self):
        """Test skill metadata is correct."""
        skill = PlaybookGeneratorSkill()
        assert skill.name == "playbook-generator"
        assert skill.requires_llm is True

    def test_implementation_phases_defined(self):
        """Test implementation phases are defined."""
        assert "off_the_shelf" in IMPLEMENTATION_PHASES
        assert "best_in_class" in IMPLEMENTATION_PHASES
        assert "custom_solution" in IMPLEMENTATION_PHASES

        for option, phases in IMPLEMENTATION_PHASES.items():
            assert len(phases) >= 3
            for phase in phases:
                assert "name" in phase
                assert "weeks" in phase

    def test_generate_timeline(self):
        """Test timeline generation."""
        skill = PlaybookGeneratorSkill()

        timeline = skill._generate_timeline(
            option_chosen="off_the_shelf",
            option_details={"implementation_weeks": 4},
            recommendation={"title": "Test"},
        )

        assert "total_weeks" in timeline
        assert "phases" in timeline
        assert len(timeline["phases"]) > 0

    def test_get_skills_required(self):
        """Test skills required by option type."""
        skill = PlaybookGeneratorSkill()

        off_shelf_skills = skill._get_skills_required("off_the_shelf", {})
        assert len(off_shelf_skills) > 0

        custom_skills = skill._get_skills_required("custom_solution", {
            "skills_required": ["Python", "API integration"]
        })
        assert "Python" in custom_skills

    def test_generate_success_metrics(self):
        """Test success metrics generation."""
        skill = PlaybookGeneratorSkill()

        recommendation = {
            "roi_detail": {
                "time_savings": {"hours_per_week": 10},
                "financial_impact": {"monthly_savings": 2000},
            }
        }

        metrics = skill._generate_success_metrics(recommendation, {})

        assert len(metrics) > 0
        assert any("Time saved" in m["metric"] for m in metrics)

    @pytest.mark.asyncio
    async def test_skill_execution_success(self):
        """Test successful skill execution."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{
            "phases": [
                {"phase": 1, "tasks": ["Task 1", "Task 2"], "deliverables": ["Done"], "owner": "Manager"}
            ]
        }''')]
        mock_client.messages.create.return_value = mock_response

        skill = PlaybookGeneratorSkill(client=mock_client)

        context = SkillContext(
            industry="dental",
            metadata={
                "recommendation": {
                    "id": "rec-001",
                    "title": "Implement online booking",
                    "options": {
                        "off_the_shelf": {
                            "vendor": "Calendly",
                            "implementation_weeks": 2,
                        }
                    }
                },
                "option_chosen": "off_the_shelf",
            }
        )

        result = await skill.run(context)

        assert result.success is True
        assert "timeline" in result.data
        assert "resources" in result.data
        assert "success_metrics" in result.data

    @pytest.mark.asyncio
    async def test_skill_requires_recommendation(self):
        """Test skill fails without recommendation."""
        from src.skills.base import SkillError

        skill = PlaybookGeneratorSkill()

        context = SkillContext(
            industry="dental",
            metadata={}
        )

        with pytest.raises(SkillError):
            await skill.execute(context)
