"""
Tests for Interview Skills

Tests for FollowUpQuestionSkill and PainExtractionSkill.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.skills import get_skill, SkillContext
from src.skills.interview.followup import FollowUpQuestionSkill, INTERVIEW_TOPICS
from src.skills.interview.pain_extraction import PainExtractionSkill, PAIN_CATEGORIES


# =============================================================================
# FollowUpQuestionSkill Tests
# =============================================================================

class TestFollowUpQuestionSkill:
    """Tests for the FollowUpQuestionSkill."""

    def test_skill_discovery(self):
        """Test that the skill can be discovered by name."""
        # Reset registry to pick up new registrations
        from src.skills import registry
        registry._registry = None

        skill = get_skill("followup-question")
        assert skill is not None
        assert skill.name == "followup-question"
        assert skill.__class__.__name__ == "FollowUpQuestionSkill"

    def test_skill_metadata(self):
        """Test skill metadata is correct."""
        skill = FollowUpQuestionSkill()
        assert skill.name == "followup-question"
        assert skill.description == "Generate adaptive follow-up questions for interviews"
        assert skill.version == "1.0.0"
        assert skill.requires_llm is True

    def test_question_types_defined(self):
        """Test that question types are properly defined."""
        skill = FollowUpQuestionSkill()
        assert "clarification" in skill.QUESTION_TYPES
        assert "deepdive" in skill.QUESTION_TYPES
        assert "transition" in skill.QUESTION_TYPES
        assert "probing" in skill.QUESTION_TYPES

    def test_interview_topics_structure(self):
        """Test interview topics have required structure."""
        for topic in INTERVIEW_TOPICS:
            assert "id" in topic
            assert "name" in topic
            assert "probing_questions" in topic
            assert len(topic["probing_questions"]) >= 1

    def test_get_uncovered_topics(self):
        """Test uncovered topics calculation."""
        skill = FollowUpQuestionSkill()

        # No topics covered
        uncovered = skill._get_uncovered_topics([])
        assert len(uncovered) == len(INTERVIEW_TOPICS)

        # Some topics covered
        uncovered = skill._get_uncovered_topics(["Current Challenges", "Business Goals"])
        assert "Current Challenges" not in uncovered
        assert "Business Goals" not in uncovered
        assert "Technology & Tools" in uncovered

    def test_build_expertise_context_empty(self):
        """Test expertise context with no data."""
        skill = FollowUpQuestionSkill()
        context = skill._build_expertise_context(None, "dental")
        assert context["has_data"] is False

    def test_build_expertise_context_with_data(self):
        """Test expertise context with industry data."""
        skill = FollowUpQuestionSkill()
        expertise = {
            "industry_expertise": {
                "total_analyses": 10,
                "pain_points": {"scheduling": {"count": 5}, "billing": {"count": 3}},
                "effective_patterns": [
                    {"recommendation": "Use automated scheduling"},
                    {"recommendation": "Implement online booking"},
                ],
            }
        }
        context = skill._build_expertise_context(expertise, "dental")
        assert context["has_data"] is True
        assert context["total_analyses"] == 10
        assert "scheduling" in context["common_pain_points"]
        assert len(context["effective_patterns"]) <= 3

    @pytest.mark.asyncio
    async def test_skill_execution_success(self):
        """Test successful skill execution with mocked LLM."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"question": "Can you tell me more about that scheduling issue?", "question_type": "deepdive", "reasoning": "User mentioned scheduling", "topics_touched": ["Current Challenges"], "suggested_followups": ["How often does this happen?"], "is_completion_candidate": false}')]
        mock_client.messages.create.return_value = mock_response

        skill = FollowUpQuestionSkill(client=mock_client)

        context = SkillContext(
            industry="dental",
            metadata={
                "user_message": "We spend too much time on scheduling patients.",
                "previous_messages": [],
                "topics_covered": ["introduction"],
                "question_count": 1,
            }
        )

        result = await skill.run(context)

        assert result.success is True
        assert "question" in result.data
        assert "question_type" in result.data
        assert result.data["question_type"] in skill.QUESTION_TYPES

    @pytest.mark.asyncio
    async def test_skill_requires_user_message(self):
        """Test skill fails without user_message."""
        from src.skills.base import SkillError

        mock_client = MagicMock()
        skill = FollowUpQuestionSkill(client=mock_client)

        context = SkillContext(
            industry="dental",
            metadata={
                # No user_message
                "topics_covered": [],
                "question_count": 0,
            }
        )

        # Skill raises SkillError for missing required data
        with pytest.raises(SkillError) as exc_info:
            await skill.execute(context)

        assert "user_message" in str(exc_info.value)

    def test_fallback_question_wrapping_up(self):
        """Test fallback question suggests wrapping up when appropriate."""
        skill = FollowUpQuestionSkill()
        result = skill._get_fallback_question([], 15)
        assert result["is_completion_candidate"] is True

    def test_fallback_question_next_topic(self):
        """Test fallback question moves to uncovered topic."""
        skill = FollowUpQuestionSkill()
        result = skill._get_fallback_question(["Business Goals"], 3)
        assert result["is_completion_candidate"] is False
        assert "Business Goals" in result["topics_touched"]


# =============================================================================
# PainExtractionSkill Tests
# =============================================================================

class TestPainExtractionSkill:
    """Tests for the PainExtractionSkill."""

    def test_skill_discovery(self):
        """Test that the skill can be discovered by name."""
        from src.skills import registry
        registry._registry = None

        skill = get_skill("pain-extraction")
        assert skill is not None
        assert skill.name == "pain-extraction"
        assert skill.__class__.__name__ == "PainExtractionSkill"

    def test_skill_metadata(self):
        """Test skill metadata is correct."""
        skill = PainExtractionSkill()
        assert skill.name == "pain-extraction"
        assert skill.description == "Extract structured pain points from interview transcripts"
        assert skill.version == "1.0.0"
        assert skill.requires_llm is True

    def test_pain_categories_defined(self):
        """Test pain categories are properly defined."""
        assert "operational" in PAIN_CATEGORIES
        assert "financial" in PAIN_CATEGORIES
        assert "customer" in PAIN_CATEGORIES
        assert "technology" in PAIN_CATEGORIES
        assert "team" in PAIN_CATEGORIES
        assert "compliance" in PAIN_CATEGORIES

    def test_build_expertise_context_empty(self):
        """Test expertise context with no data."""
        skill = PainExtractionSkill()
        context = skill._build_expertise_context(None, "dental")
        assert context["has_data"] is False

    def test_build_expertise_context_with_data(self):
        """Test expertise context with industry data."""
        skill = PainExtractionSkill()
        expertise = {
            "industry_expertise": {
                "total_analyses": 15,
                "pain_points": {
                    "scheduling": {"count": 8},
                    "insurance": {"count": 5},
                },
                "effective_patterns": [
                    {"recommendation": "Automated reminders"},
                ],
            }
        }
        context = skill._build_expertise_context(expertise, "dental")
        assert context["has_data"] is True
        assert context["total_analyses"] == 15
        assert "scheduling" in context["common_pain_points"]

    @pytest.mark.asyncio
    async def test_skill_execution_success(self):
        """Test successful skill execution with mocked LLM."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''
        {
            "pain_points": [
                {
                    "id": "pain-001",
                    "title": "Manual Scheduling",
                    "description": "Too much time spent on manual patient scheduling",
                    "category": "operational",
                    "severity": "high",
                    "frequency": "daily",
                    "quote": "We spend hours every day on the phone with patients",
                    "impact": {
                        "time_hours_per_week": 20,
                        "cost_per_month": 2000,
                        "customer_impact": "Long wait times for appointments"
                    },
                    "automation_potential": "high",
                    "suggested_solutions": ["Online booking", "Automated reminders"]
                }
            ],
            "themes": ["scheduling", "time waste"],
            "priority_ranking": ["pain-001"],
            "confidence_score": 0.85
        }
        ''')]
        mock_client.messages.create.return_value = mock_response

        skill = PainExtractionSkill(client=mock_client)

        context = SkillContext(
            industry="dental",
            metadata={
                "transcript": [
                    {"role": "assistant", "content": "What challenges do you face?"},
                    {"role": "user", "content": "We spend hours every day on the phone with patients for scheduling."},
                ]
            }
        )

        result = await skill.run(context)

        assert result.success is True
        assert "pain_points" in result.data
        assert len(result.data["pain_points"]) == 1
        assert result.data["pain_points"][0]["title"] == "Manual Scheduling"
        assert result.data["confidence_score"] == 0.85

    @pytest.mark.asyncio
    async def test_skill_requires_transcript(self):
        """Test skill fails without transcript."""
        from src.skills.base import SkillError

        mock_client = MagicMock()
        skill = PainExtractionSkill(client=mock_client)

        context = SkillContext(
            industry="dental",
            metadata={
                # No transcript
            }
        )

        # Skill raises SkillError for missing required data
        with pytest.raises(SkillError) as exc_info:
            await skill.execute(context)

        assert "transcript" in str(exc_info.value)

    def test_validate_response_normalizes_categories(self):
        """Test response validation normalizes invalid categories."""
        skill = PainExtractionSkill()
        response = {
            "pain_points": [
                {
                    "title": "Test Pain",
                    "category": "invalid_category",  # Invalid
                    "severity": "high",
                }
            ],
            "themes": [],
            "priority_ranking": [],
            "confidence_score": 0.5,
        }

        validated = skill._validate_response(response)
        assert validated["pain_points"][0]["category"] == "operational"  # Default

    def test_validate_response_normalizes_severity(self):
        """Test response validation normalizes invalid severity."""
        skill = PainExtractionSkill()
        response = {
            "pain_points": [
                {
                    "title": "Test Pain",
                    "category": "operational",
                    "severity": "critical",  # Invalid
                }
            ],
            "themes": [],
            "priority_ranking": [],
            "confidence_score": 0.5,
        }

        validated = skill._validate_response(response)
        assert validated["pain_points"][0]["severity"] == "medium"  # Default

    def test_validate_with_expertise_boosts_confidence(self):
        """Test expertise validation boosts confidence for matched pain points."""
        skill = PainExtractionSkill()

        result = {
            "pain_points": [
                {
                    "id": "pain-001",
                    "title": "Scheduling Problems",
                    "description": "Manual scheduling takes too long",
                }
            ],
            "themes": [],
            "priority_ranking": ["pain-001"],
            "confidence_score": 0.5,
        }

        expertise_context = {
            "has_data": True,
            "common_pain_points": ["scheduling"],
            "pain_point_frequencies": {"scheduling": {"count": 10}},
        }

        validated = skill._validate_with_expertise(result, expertise_context)

        # Should be validated
        assert validated["pain_points"][0].get("expertise_validated") is True
        # Confidence should be boosted
        assert validated["confidence_score"] > 0.5

    def test_empty_result(self):
        """Test empty result structure."""
        skill = PainExtractionSkill()
        result = skill._get_empty_result()

        assert result["pain_points"] == []
        assert result["themes"] == []
        assert result["priority_ranking"] == []
        assert result["confidence_score"] == 0.0


# =============================================================================
# Integration Tests
# =============================================================================

class TestInterviewSkillsIntegration:
    """Integration tests for interview skills working together."""

    def test_both_skills_discoverable(self):
        """Test both skills can be discovered."""
        from src.skills import registry
        registry._registry = None

        followup = get_skill("followup-question")
        extraction = get_skill("pain-extraction")

        assert followup is not None
        assert extraction is not None

    def test_skills_without_client_fail_gracefully(self):
        """Test skills fail gracefully without client."""
        followup = FollowUpQuestionSkill()  # No client
        extraction = PainExtractionSkill()  # No client

        # Skills should be created but require client for execution
        assert followup.requires_llm is True
        assert extraction.requires_llm is True

    @pytest.mark.asyncio
    async def test_followup_generates_valid_structure(self):
        """Test followup skill validates output structure."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        # Incomplete response
        mock_response.content = [MagicMock(text='{"question": "Tell me more"}')]
        mock_client.messages.create.return_value = mock_response

        skill = FollowUpQuestionSkill(client=mock_client)

        context = SkillContext(
            industry="dental",
            metadata={
                "user_message": "Test message",
                "topics_covered": [],
                "question_count": 0,
            }
        )

        result = await skill.run(context)

        # Should fill in defaults
        assert result.success is True
        assert "question" in result.data
        assert "question_type" in result.data
        assert "reasoning" in result.data

    @pytest.mark.asyncio
    async def test_extraction_generates_valid_structure(self):
        """Test extraction skill validates output structure."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        # Minimal response
        mock_response.content = [MagicMock(text='{"pain_points": [], "themes": [], "priority_ranking": [], "confidence_score": 0.3}')]
        mock_client.messages.create.return_value = mock_response

        skill = PainExtractionSkill(client=mock_client)

        context = SkillContext(
            industry="dental",
            metadata={
                "transcript": [
                    {"role": "user", "content": "Things are fine."},
                ]
            }
        )

        result = await skill.run(context)

        # Should return valid structure
        assert result.success is True
        assert "pain_points" in result.data
        assert "themes" in result.data
        assert "confidence_score" in result.data
