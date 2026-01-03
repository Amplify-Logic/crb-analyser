# backend/tests/test_workshop_models.py
"""Tests for workshop data models."""

import pytest
from src.models.workshop import (
    WorkshopPhase,
    AccuracyRating,
    DetectedSignals,
    ConfirmationData,
    DeepDiveData,
    MilestoneData,
    WorkshopData,
    WorkshopConfidence,
    DepthDimensions,
)


class TestDetectedSignals:
    """Test adaptive signal detection model."""

    def test_default_signals(self):
        signals = DetectedSignals()
        assert signals.technical is False
        assert signals.budget_ready is False
        assert signals.decision_maker is False

    def test_from_quiz_data_technical_role(self):
        signals = DetectedSignals.from_quiz_data(
            role="CTO",
            company_size="11-50",
            budget_answer="15000-50000",
            quiz_answers={}
        )
        assert signals.technical is True
        assert signals.budget_ready is True

    def test_from_quiz_data_non_technical(self):
        signals = DetectedSignals.from_quiz_data(
            role="CEO",
            company_size="1-10",
            budget_answer="2000-5000",
            quiz_answers={}
        )
        assert signals.technical is False
        assert signals.decision_maker is True

    def test_from_quiz_data_technical_keywords(self):
        signals = DetectedSignals.from_quiz_data(
            role="Manager",
            company_size="50-100",
            budget_answer="5000-15000",
            quiz_answers={"tools": "We built a custom API integration"}
        )
        assert signals.technical is True

    def test_to_dict(self):
        signals = DetectedSignals(technical=True, budget_ready=False, decision_maker=True)
        result = signals.to_dict()
        assert result == {
            "technical": True,
            "budget_ready": False,
            "decision_maker": True,
        }


class TestWorkshopConfidence:
    """Test enhanced confidence framework."""

    def test_calculate_overall_score(self):
        conf = WorkshopConfidence(
            topics={
                "current_challenges": {"coverage": 25, "depth": 20, "specificity": 18, "actionability": 15},
                "business_goals": {"coverage": 20, "depth": 15, "specificity": 10, "actionability": 10},
                "team_operations": {"coverage": 15, "depth": 10, "specificity": 8, "actionability": 5},
                "technology": {"coverage": 20, "depth": 15, "specificity": 12, "actionability": 10},
                "budget_timeline": {"coverage": 10, "depth": 5, "specificity": 5, "actionability": 5},
            },
            depth_dimensions=DepthDimensions(
                integration_depth=0.7,
                cost_quantification=0.8,
                stakeholder_mapping=0.6,
                implementation_readiness=0.5,
            )
        )
        score = conf.calculate_overall()
        assert 0.5 <= score <= 0.8  # Expected range given inputs

    def test_is_ready_for_report(self):
        conf = WorkshopConfidence(
            topics={
                "current_challenges": {"coverage": 25, "depth": 22, "specificity": 20, "actionability": 18},
                "business_goals": {"coverage": 22, "depth": 18, "specificity": 15, "actionability": 12},
                "team_operations": {"coverage": 18, "depth": 15, "specificity": 12, "actionability": 10},
                "technology": {"coverage": 20, "depth": 18, "specificity": 15, "actionability": 12},
                "budget_timeline": {"coverage": 15, "depth": 10, "specificity": 8, "actionability": 8},
            },
            depth_dimensions=DepthDimensions(
                integration_depth=0.8,
                cost_quantification=0.9,
                stakeholder_mapping=0.7,
                implementation_readiness=0.7,
            ),
            quality_indicators={
                "pain_points_extracted": 3,
                "quantifiable_impacts": 4,
            }
        )
        assert conf.is_ready_for_report() is True

    def test_not_ready_low_challenges(self):
        conf = WorkshopConfidence(
            topics={
                "current_challenges": {"coverage": 10, "depth": 5, "specificity": 5, "actionability": 5},
                "business_goals": {"coverage": 20, "depth": 15, "specificity": 10, "actionability": 10},
                "team_operations": {"coverage": 15, "depth": 10, "specificity": 8, "actionability": 5},
                "technology": {"coverage": 20, "depth": 15, "specificity": 12, "actionability": 10},
                "budget_timeline": {"coverage": 10, "depth": 5, "specificity": 5, "actionability": 5},
            },
            depth_dimensions=DepthDimensions(),
            quality_indicators={"pain_points_extracted": 0}
        )
        assert conf.is_ready_for_report() is False


class TestDepthDimensions:
    """Test depth dimensions model."""

    def test_default_values(self):
        dims = DepthDimensions()
        assert dims.integration_depth == 0.0
        assert dims.cost_quantification == 0.0
        assert dims.stakeholder_mapping == 0.0
        assert dims.implementation_readiness == 0.0

    def test_average(self):
        dims = DepthDimensions(
            integration_depth=0.8,
            cost_quantification=0.6,
            stakeholder_mapping=0.4,
            implementation_readiness=0.2,
        )
        assert dims.average() == 0.5

    def test_to_dict(self):
        dims = DepthDimensions(
            integration_depth=0.7,
            cost_quantification=0.8,
            stakeholder_mapping=0.5,
            implementation_readiness=0.6,
        )
        result = dims.to_dict()
        assert result == {
            "integration_depth": 0.7,
            "cost_quantification": 0.8,
            "stakeholder_mapping": 0.5,
            "implementation_readiness": 0.6,
        }


class TestWorkshopPhase:
    """Test workshop phase enum."""

    def test_phase_values(self):
        assert WorkshopPhase.CONFIRMATION.value == "confirmation"
        assert WorkshopPhase.DEEPDIVE.value == "deepdive"
        assert WorkshopPhase.SYNTHESIS.value == "synthesis"
        assert WorkshopPhase.COMPLETE.value == "complete"


class TestAccuracyRating:
    """Test accuracy rating enum."""

    def test_rating_values(self):
        assert AccuracyRating.ACCURATE.value == "accurate"
        assert AccuracyRating.INACCURATE.value == "inaccurate"
        assert AccuracyRating.EDITED.value == "edited"


class TestWorkshopData:
    """Test complete workshop data model."""

    def test_default_values(self):
        data = WorkshopData()
        assert data.phase == WorkshopPhase.CONFIRMATION
        assert data.detected_signals.technical is False
        assert data.deep_dives == []
        assert data.milestones == []

    def test_to_dict(self):
        data = WorkshopData()
        result = data.to_dict()
        assert "phase" in result
        assert result["phase"] == "confirmation"
        assert "detected_signals" in result
        assert "deep_dives" in result

    def test_from_dict_empty(self):
        data = WorkshopData.from_dict({})
        assert data.phase == WorkshopPhase.CONFIRMATION

    def test_from_dict_with_data(self):
        data = WorkshopData.from_dict({
            "phase": "deepdive",
            "detected_signals": {
                "technical": True,
                "budget_ready": False,
                "decision_maker": True,
            }
        })
        assert data.phase == WorkshopPhase.DEEPDIVE
        assert data.detected_signals.technical is True
        assert data.detected_signals.decision_maker is True
