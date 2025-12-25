"""
Tests for ROI Calculator Skill
"""

import pytest
from unittest.mock import MagicMock

from src.skills import get_skill, SkillContext
from src.skills.analysis.roi_calculator import (
    ROICalculatorSkill,
    DEFAULT_ASSUMPTIONS,
    CONFIDENCE_FACTORS,
)


class TestROICalculatorSkill:
    """Tests for the ROICalculatorSkill."""

    def test_skill_discovery(self):
        """Test that the skill can be discovered by name."""
        from src.skills import registry
        registry._registry = None

        skill = get_skill("roi-calculator")
        assert skill is not None
        assert skill.name == "roi-calculator"

    def test_skill_metadata(self):
        """Test skill metadata is correct."""
        skill = ROICalculatorSkill()
        assert skill.name == "roi-calculator"
        assert skill.description == "Calculate ROI with transparent assumptions"
        assert skill.version == "1.0.0"
        assert skill.requires_llm is True

    def test_default_assumptions_defined(self):
        """Test default assumptions are properly defined."""
        assert "hourly_rate" in DEFAULT_ASSUMPTIONS
        assert "automation_efficiency" in DEFAULT_ASSUMPTIONS
        assert "adoption_rate" in DEFAULT_ASSUMPTIONS

        # Check structure
        hourly = DEFAULT_ASSUMPTIONS["hourly_rate"]
        assert "value" in hourly
        assert "statement" in hourly
        assert "source" in hourly
        assert "sensitivity" in hourly

    def test_confidence_factors_defined(self):
        """Test confidence factors match CLAUDE.md spec."""
        assert CONFIDENCE_FACTORS["high"] == 1.0
        assert CONFIDENCE_FACTORS["medium"] == 0.85
        assert CONFIDENCE_FACTORS["low"] == 0.70

    def test_extract_company_data_from_quiz(self):
        """Test company data extraction from quiz answers."""
        skill = ROICalculatorSkill()

        quiz_answers = {
            "hourly_rate": 75,
            "team_size": 10,
        }

        data = skill._extract_company_data(quiz_answers, {})

        assert data["hourly_rate"] == 75
        assert data["hourly_rate_source"] == "quiz_data"
        assert data["team_size"] == 10
        assert data["team_size_source"] == "quiz_data"

    def test_extract_company_data_defaults(self):
        """Test company data falls back to defaults."""
        skill = ROICalculatorSkill()

        data = skill._extract_company_data(None, {})

        assert data["hourly_rate"] == DEFAULT_ASSUMPTIONS["hourly_rate"]["value"]
        assert data["hourly_rate_source"] == "assumption"
        assert data["team_size"] == 5  # Default SMB size

    def test_calculate_financials(self):
        """Test financial calculations."""
        skill = ROICalculatorSkill()

        time_savings = {
            "hours_per_week": 10,
            "hours_per_month": 43.3,
            "hours_per_year": 480,
        }

        recommendation = {
            "our_recommendation": "off_the_shelf",
            "options": {
                "off_the_shelf": {
                    "implementation_cost": 500,
                    "monthly_cost": 50,
                }
            }
        }

        company_data = {"hourly_rate": 50}

        financial = skill._calculate_financials(time_savings, recommendation, company_data)

        assert financial["monthly_savings"] == 43.3 * 50  # 2165
        assert financial["yearly_savings"] == 480 * 50  # 24000
        assert financial["implementation_cost"] == 500
        assert financial["monthly_cost"] == 50
        assert financial["yearly_cost"] == 600

    def test_calculate_roi_metrics(self):
        """Test ROI calculation."""
        skill = ROICalculatorSkill()

        financial = {
            "yearly_savings": 24000,
            "yearly_cost": 600,
            "implementation_cost": 500,
        }

        finding = {"confidence": "high"}

        metrics = skill._calculate_roi_metrics(financial, finding)

        # Net annual = 24000 - 600 = 23400
        # First year investment = 500 + 600 = 1100
        # ROI = (23400 / 1100) * 100 = 2127%
        assert metrics["roi_raw"] > 2000
        assert metrics["roi_adjusted"] == metrics["roi_raw"]  # High confidence = 1.0
        assert metrics["payback_months"] < 1  # Very fast payback

    def test_calculate_roi_with_medium_confidence(self):
        """Test confidence adjustment is applied."""
        skill = ROICalculatorSkill()

        financial = {
            "yearly_savings": 24000,
            "yearly_cost": 600,
            "implementation_cost": 500,
        }

        finding = {"confidence": "medium"}

        metrics = skill._calculate_roi_metrics(financial, finding)

        # Medium confidence = 0.85 factor
        assert metrics["roi_adjusted"] == round(metrics["roi_raw"] * 0.85, 0)

    def test_calculate_sensitivity(self):
        """Test sensitivity analysis generation."""
        skill = ROICalculatorSkill()

        base_metrics = {"roi_raw": 200, "payback_months": 6}
        time_savings = {}
        financial = {}

        sensitivity = skill._calculate_sensitivity(base_metrics, time_savings, financial)

        assert "best_case" in sensitivity
        assert "expected" in sensitivity
        assert "worst_case" in sensitivity

        # Best case should be higher ROI
        assert sensitivity["best_case"]["roi"] > sensitivity["expected"]["roi"]
        # Worst case should be lower ROI
        assert sensitivity["worst_case"]["roi"] < sensitivity["expected"]["roi"]

        # Best case should have faster payback
        assert sensitivity["best_case"]["payback_months"] < sensitivity["expected"]["payback_months"]

    def test_build_assumptions_list(self):
        """Test assumptions list is built correctly."""
        skill = ROICalculatorSkill()

        company_data = {
            "hourly_rate": 50,
            "hourly_rate_source": "assumption",
            "automation_efficiency": 0.70,
            "adoption_rate": 0.80,
        }

        assumptions = skill._build_assumptions_list(company_data)

        # Should include hourly rate (since it's an assumption)
        assert any("hourly" in a.get("statement", "").lower() for a in assumptions)

        # Should always include efficiency and adoption
        assert any("70%" in a.get("statement", "") or "automation" in a.get("statement", "").lower() for a in assumptions)

    def test_generate_breakdown(self):
        """Test calculation breakdown generation."""
        skill = ROICalculatorSkill()

        time_savings = {
            "raw_hours_before_efficiency": 14.3,
            "hours_per_week": 10,
            "hours_per_month": 43,
            "hours_per_year": 480,
        }
        financial = {
            "monthly_savings": 2150,
            "yearly_savings": 24000,
            "implementation_cost": 500,
            "monthly_cost": 50,
            "yearly_cost": 600,
            "three_year_gross_savings": 72000,
            "three_year_total_cost": 2300,
            "three_year_net": 69700,
        }
        roi_metrics = {
            "roi_raw": 2127,
            "roi_adjusted": 2127,
            "confidence_factor": 1.0,
            "payback_months": 0.3,
            "net_annual_benefit": 23400,
        }
        company_data = {
            "hourly_rate": 50,
            "automation_efficiency": 0.70,
        }

        breakdown = skill._generate_breakdown(time_savings, financial, roi_metrics, company_data)

        assert "TIME SAVINGS" in breakdown
        assert "FINANCIAL VALUE" in breakdown
        assert "ROI CALCULATION" in breakdown
        assert "THREE-YEAR PROJECTION" in breakdown
        assert "€50" in breakdown  # Hourly rate

    @pytest.mark.asyncio
    async def test_skill_execution_success(self):
        """Test successful skill execution with mocked LLM."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"hours_per_week": 8, "reasoning": "Based on process analysis"}')]
        mock_client.messages.create.return_value = mock_response

        skill = ROICalculatorSkill(client=mock_client)

        context = SkillContext(
            industry="dental",
            quiz_answers={"hourly_rate": 60, "team_size": 8},
            metadata={
                "finding": {
                    "id": "finding-001",
                    "title": "Manual scheduling",
                    "confidence": "medium",
                },
                "recommendation": {
                    "our_recommendation": "off_the_shelf",
                    "options": {
                        "off_the_shelf": {
                            "implementation_cost": 1000,
                            "monthly_cost": 100,
                        }
                    }
                },
                "company_context": {},
            }
        )

        result = await skill.run(context)

        assert result.success is True
        assert "roi_percentage" in result.data
        assert "roi_confidence_adjusted" in result.data
        assert "payback_months" in result.data
        assert "time_savings" in result.data
        assert "financial_impact" in result.data
        assert "sensitivity" in result.data
        assert "assumptions" in result.data
        assert "calculation_breakdown" in result.data

    @pytest.mark.asyncio
    async def test_skill_requires_finding(self):
        """Test skill fails without finding."""
        from src.skills.base import SkillError

        mock_client = MagicMock()
        skill = ROICalculatorSkill(client=mock_client)

        context = SkillContext(
            industry="dental",
            metadata={
                # No finding
                "recommendation": {},
            }
        )

        with pytest.raises(SkillError) as exc_info:
            await skill.execute(context)

        assert "finding" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_skill_uses_quiz_hourly_rate(self):
        """Test that quiz-provided hourly rate is used."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"hours_per_week": 10, "reasoning": "test"}')]
        mock_client.messages.create.return_value = mock_response

        skill = ROICalculatorSkill(client=mock_client)

        context = SkillContext(
            industry="dental",
            quiz_answers={"hourly_rate": 100},  # Custom rate
            metadata={
                "finding": {"id": "f1", "title": "Test", "confidence": "high"},
                "recommendation": {
                    "our_recommendation": "off_the_shelf",
                    "options": {"off_the_shelf": {"implementation_cost": 0, "monthly_cost": 0}}
                },
            }
        )

        result = await skill.run(context)

        # Monthly savings should use €100/hr rate
        # 10 hrs/week * 0.7 efficiency * 0.8 adoption = 5.6 hrs/week
        # 5.6 * 4.33 = 24.25 hrs/month
        # 24.25 * €100 = €2425
        assert result.data["financial_impact"]["monthly_savings"] > 2000


class TestROICalculatorIntegration:
    """Integration tests for ROI calculator."""

    def test_skill_without_client(self):
        """Test skill can be created without client."""
        skill = ROICalculatorSkill()
        assert skill.requires_llm is True

    @pytest.mark.asyncio
    async def test_full_calculation_flow(self):
        """Test complete calculation with realistic data."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"hours_per_week": 15, "reasoning": "Admin tasks"}')]
        mock_client.messages.create.return_value = mock_response

        skill = ROICalculatorSkill(client=mock_client)

        context = SkillContext(
            industry="dental",
            quiz_answers={
                "hourly_rate": 50,
                "team_size": 5,
            },
            metadata={
                "finding": {
                    "id": "finding-001",
                    "title": "Manual patient scheduling",
                    "description": "Staff spends 15+ hours/week on phone scheduling",
                    "hours_per_week": 15,  # Provided in finding
                    "confidence": "high",
                },
                "recommendation": {
                    "title": "Implement online booking",
                    "our_recommendation": "off_the_shelf",
                    "options": {
                        "off_the_shelf": {
                            "name": "Calendly",
                            "implementation_cost": 500,
                            "monthly_cost": 50,
                        }
                    }
                },
            }
        )

        result = await skill.run(context)

        assert result.success is True

        data = result.data

        # Check time savings (15 hrs * 0.7 efficiency * 0.8 adoption = 8.4 hrs/week)
        assert data["time_savings"]["hours_per_week"] == pytest.approx(8.4, rel=0.1)

        # Check financial (8.4 * 4.33 * 50 = ~1818/month)
        assert data["financial_impact"]["monthly_savings"] > 1500

        # Check ROI is positive and significant
        assert data["roi_percentage"] > 100

        # Check assumptions are tracked
        assert len(data["assumptions"]) >= 2

        # Check breakdown is generated
        assert "TIME SAVINGS" in data["calculation_breakdown"]
