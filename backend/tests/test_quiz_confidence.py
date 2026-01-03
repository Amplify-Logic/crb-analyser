"""
Tests for the Quiz Confidence Framework

Tests the confidence initialization from research and updates from answers.
"""

import pytest
from src.models.quiz_confidence import (
    ConfidenceCategory,
    ConfidenceState,
    AdaptiveQuestion,
    AnswerAnalysis,
    ExtractedFact,
    CONFIDENCE_THRESHOLDS,
    create_initial_confidence_from_research,
    update_confidence_from_analysis,
)


class TestConfidenceState:
    """Tests for ConfidenceState model."""

    def test_empty_state_has_all_gaps(self):
        """Empty state should have all categories as gaps."""
        state = ConfidenceState()
        state.recalculate_gaps()

        assert len(state.gaps) == len(ConfidenceCategory)
        assert not state.ready_for_teaser

    def test_update_score_caps_at_100(self):
        """Scores should cap at 100."""
        state = ConfidenceState()
        state.update_score(ConfidenceCategory.COMPANY_BASICS, 150)

        assert state.scores[ConfidenceCategory.COMPANY_BASICS] == 100

    def test_update_score_accumulates(self):
        """Multiple updates should accumulate."""
        state = ConfidenceState()
        state.update_score(ConfidenceCategory.PAIN_POINTS, 30)
        state.update_score(ConfidenceCategory.PAIN_POINTS, 25)

        assert state.scores[ConfidenceCategory.PAIN_POINTS] == 55

    def test_ready_when_all_thresholds_met(self):
        """Should be ready when all categories meet thresholds."""
        state = ConfidenceState()

        # Set all scores to meet thresholds
        for cat, threshold in CONFIDENCE_THRESHOLDS.items():
            state.scores[cat] = threshold

        state.recalculate_gaps()

        assert len(state.gaps) == 0
        assert state.ready_for_teaser

    def test_not_ready_when_one_gap(self):
        """Should not be ready if any category is below threshold."""
        state = ConfidenceState()

        # Set all scores to meet thresholds except one
        for cat, threshold in CONFIDENCE_THRESHOLDS.items():
            state.scores[cat] = threshold

        # Drop one below threshold
        state.scores[ConfidenceCategory.PAIN_POINTS] = 50  # Threshold is 80

        state.recalculate_gaps()

        assert ConfidenceCategory.PAIN_POINTS in state.gaps
        assert not state.ready_for_teaser

    def test_add_fact(self):
        """Should be able to add facts to categories."""
        state = ConfidenceState()

        fact = ExtractedFact(
            fact="uses_hubspot",
            value="HubSpot CRM",
            confidence="high",
            source="research",
        )
        state.add_fact(ConfidenceCategory.TECH_STACK, fact)

        assert len(state.facts[ConfidenceCategory.TECH_STACK]) == 1
        assert state.facts[ConfidenceCategory.TECH_STACK][0].value == "HubSpot CRM"

    def test_sorted_gaps_worst_first(self):
        """Gaps should be sorted by how far below threshold."""
        state = ConfidenceState()

        # Set all categories to meet their thresholds first
        for cat, threshold in CONFIDENCE_THRESHOLDS.items():
            state.scores[cat] = threshold

        # Now set specific ones below threshold with varying gaps
        state.scores[ConfidenceCategory.COMPANY_BASICS] = 70  # Need 80, gap of 10
        state.scores[ConfidenceCategory.PAIN_POINTS] = 20  # Need 80, gap of 60
        state.scores[ConfidenceCategory.TECH_STACK] = 50  # Need 60, gap of 10

        state.recalculate_gaps()
        sorted_gaps = state.get_sorted_gaps()

        # Pain points should be first (biggest gap of 60)
        assert sorted_gaps[0] == ConfidenceCategory.PAIN_POINTS
        # Should have exactly 3 gaps
        assert len(sorted_gaps) == 3


class TestConfidenceFromResearch:
    """Tests for initializing confidence from research profile."""

    def test_empty_profile_gives_zero_scores(self):
        """Empty profile should result in all zeros."""
        state = create_initial_confidence_from_research({})

        assert all(score == 0 for score in state.scores.values())

    def test_basic_name_adds_confidence(self):
        """Company name should add to company_basics."""
        profile = {
            "basics": {
                "name": {"value": "Acme Corp"},
            }
        }

        state = create_initial_confidence_from_research(profile)

        assert state.scores[ConfidenceCategory.COMPANY_BASICS] >= 20

    def test_full_basics_adds_significant_confidence(self):
        """Full basics should add significant confidence."""
        profile = {
            "basics": {
                "name": {"value": "Acme Corp"},
                "description": {"value": "A software company"},
            },
            "size": {
                "employee_range": {"value": "11-50"},
            },
            "industry": {
                "primary_industry": {"value": "Software"},
            },
        }

        state = create_initial_confidence_from_research(profile)

        # Should have meaningful confidence in basics
        assert state.scores[ConfidenceCategory.COMPANY_BASICS] >= 60

    def test_tech_stack_adds_confidence(self):
        """Detected technologies should add to tech_stack."""
        profile = {
            "basics": {"name": {"value": "Test Co"}},
            "tech_stack": {
                "technologies_detected": [
                    {"value": "HubSpot"},
                    {"value": "Slack"},
                    {"value": "Salesforce"},
                ],
            },
        }

        state = create_initial_confidence_from_research(profile)

        # Each tech should add ~12 points, capped
        assert state.scores[ConfidenceCategory.TECH_STACK] >= 30

    def test_industry_adds_to_multiple_categories(self):
        """Industry info should add to basics and industry_context."""
        profile = {
            "basics": {"name": {"value": "Test Co"}},
            "industry": {
                "primary_industry": {"value": "Healthcare"},
                "business_model": {"value": "B2B SaaS"},
            },
        }

        state = create_initial_confidence_from_research(profile)

        assert state.scores[ConfidenceCategory.INDUSTRY_CONTEXT] >= 30
        assert state.scores[ConfidenceCategory.COMPANY_BASICS] >= 20

    def test_facts_are_extracted(self):
        """Research should extract facts into the state."""
        profile = {
            "basics": {
                "name": {"value": "Acme Corp"},
            },
            "industry": {
                "primary_industry": {"value": "Dental"},
            },
        }

        state = create_initial_confidence_from_research(profile)

        # Should have company name as a fact
        basics_facts = state.facts[ConfidenceCategory.COMPANY_BASICS]
        assert any(f.fact == "company_name" for f in basics_facts)

        # Should have industry as a fact
        industry_facts = state.facts[ConfidenceCategory.INDUSTRY_CONTEXT]
        assert any(f.value == "Dental" for f in industry_facts)

    def test_gaps_calculated_after_research(self):
        """Gaps should be calculated based on research quality."""
        profile = {
            "basics": {
                "name": {"value": "Acme Corp"},
                "description": {"value": "A great company"},
            },
            "size": {
                "employee_range": {"value": "11-50"},
            },
            "industry": {
                "primary_industry": {"value": "Software"},
            },
        }

        state = create_initial_confidence_from_research(profile)

        # Pain points should still be a gap (can't find publicly)
        assert ConfidenceCategory.PAIN_POINTS in state.gaps

        # Goals should still be a gap (can't find publicly)
        assert ConfidenceCategory.GOALS_PRIORITIES in state.gaps


class TestConfidenceFromAnalysis:
    """Tests for updating confidence from answer analysis."""

    def test_boosts_applied(self):
        """Confidence boosts should be applied."""
        state = ConfidenceState()
        state.scores[ConfidenceCategory.PAIN_POINTS] = 20

        analysis = AnswerAnalysis(
            confidence_boosts={
                ConfidenceCategory.PAIN_POINTS: 25,
                ConfidenceCategory.OPERATIONS: 15,
            }
        )

        state = update_confidence_from_analysis(state, analysis)

        assert state.scores[ConfidenceCategory.PAIN_POINTS] == 45
        assert state.scores[ConfidenceCategory.OPERATIONS] == 15

    def test_facts_added(self):
        """Extracted facts should be added to state."""
        state = ConfidenceState()

        fact = ExtractedFact(
            fact="time_on_admin",
            value="20 hours/week",
            confidence="high",
        )
        analysis = AnswerAnalysis(
            extracted_facts={
                ConfidenceCategory.QUANTIFIABLE_METRICS: [fact],
            }
        )

        state = update_confidence_from_analysis(state, analysis)

        facts = state.facts[ConfidenceCategory.QUANTIFIABLE_METRICS]
        assert len(facts) == 1
        assert facts[0].value == "20 hours/week"

    def test_questions_asked_incremented(self):
        """Questions asked counter should increment."""
        state = ConfidenceState()
        assert state.questions_asked == 0

        analysis = AnswerAnalysis()
        state = update_confidence_from_analysis(state, analysis)

        assert state.questions_asked == 1

    def test_gaps_recalculated(self):
        """Gaps should be recalculated after update."""
        state = ConfidenceState()

        # Set all to just below threshold
        for cat in ConfidenceCategory:
            state.scores[cat] = CONFIDENCE_THRESHOLDS[cat] - 5

        state.recalculate_gaps()
        assert len(state.gaps) == len(ConfidenceCategory)

        # Now boost all above threshold
        analysis = AnswerAnalysis(
            confidence_boosts={cat: 10 for cat in ConfidenceCategory}
        )

        state = update_confidence_from_analysis(state, analysis)

        assert state.ready_for_teaser


class TestAdaptiveQuestion:
    """Tests for AdaptiveQuestion model."""

    def test_basic_creation(self):
        """Should create a valid question."""
        question = AdaptiveQuestion(
            id="q_123",
            question="What's your biggest challenge?",
            target_categories=[ConfidenceCategory.PAIN_POINTS],
            expected_boosts={ConfidenceCategory.PAIN_POINTS: 25},
        )

        assert question.id == "q_123"
        assert question.question_type == "voice"  # Default
        assert not question.is_deep_dive

    def test_deep_dive_flag(self):
        """Deep dive questions should be flagged."""
        question = AdaptiveQuestion(
            id="dd_123",
            question="Tell me more about that",
            target_categories=[ConfidenceCategory.PAIN_POINTS],
            is_deep_dive=True,
        )

        assert question.is_deep_dive


class TestAnswerAnalysis:
    """Tests for AnswerAnalysis model."""

    def test_empty_analysis(self):
        """Empty analysis should have safe defaults."""
        analysis = AnswerAnalysis()

        assert analysis.extracted_facts == {}
        assert analysis.confidence_boosts == {}
        assert analysis.detected_signals == []
        assert not analysis.should_deep_dive
        assert analysis.sentiment == "neutral"

    def test_with_signals(self):
        """Should track detected signals."""
        analysis = AnswerAnalysis(
            detected_signals=["pain_signal", "urgency"],
            should_deep_dive=True,
            deep_dive_topic="call handling",
        )

        assert "pain_signal" in analysis.detected_signals
        assert analysis.should_deep_dive
        assert analysis.deep_dive_topic == "call handling"


# ============================================================================
# Tests for Industry Question Bank
# ============================================================================

from src.services.quiz_engine import (
    IndustryQuestionBank,
    get_available_industries,
)


class TestIndustryQuestionBank:
    """Tests for IndustryQuestionBank class."""

    def test_load_dental_bank(self):
        """Should load dental question bank successfully."""
        bank = IndustryQuestionBank.load("dental")

        assert bank.industry == "dental"
        assert bank.display_name == "Dental Practice"
        assert len(bank.questions) > 0

    def test_load_professional_services_bank(self):
        """Should load professional services question bank."""
        bank = IndustryQuestionBank.load("professional_services")

        assert bank.industry == "professional-services"
        assert len(bank.questions) > 0

    def test_load_nonexistent_returns_empty(self):
        """Non-existent industry should return empty bank."""
        bank = IndustryQuestionBank.load("nonexistent_industry_xyz")

        assert bank.industry == "nonexistent_industry_xyz"
        assert len(bank.questions) == 0
        assert len(bank.deep_dive_templates) == 0

    def test_get_question_by_id(self):
        """Should retrieve question by ID."""
        bank = IndustryQuestionBank.load("dental")

        question = bank.get_question_by_id("patient_volume_weekly")
        assert question is not None
        assert "patients" in question["question"].lower()

    def test_get_question_by_id_not_found(self):
        """Should return None for unknown question ID."""
        bank = IndustryQuestionBank.load("dental")

        question = bank.get_question_by_id("nonexistent_question")
        assert question is None

    def test_get_questions_for_category(self):
        """Should filter questions by category."""
        bank = IndustryQuestionBank.load("dental")

        pain_questions = bank.get_questions_for_category(
            ConfidenceCategory.PAIN_POINTS
        )

        assert len(pain_questions) > 0
        for q in pain_questions:
            assert "pain_points" in q.get("target_categories", [])

    def test_get_questions_excludes_ids(self):
        """Should exclude specified question IDs."""
        bank = IndustryQuestionBank.load("dental")

        # Get all pain point questions
        all_pain = bank.get_questions_for_category(ConfidenceCategory.PAIN_POINTS)

        if len(all_pain) > 0:
            first_id = all_pain[0]["id"]

            # Get again excluding the first one
            filtered = bank.get_questions_for_category(
                ConfidenceCategory.PAIN_POINTS,
                exclude_ids=[first_id]
            )

            assert not any(q["id"] == first_id for q in filtered)

    def test_get_deep_dive_for_answer(self):
        """Should return deep dive template when triggered."""
        bank = IndustryQuestionBank.load("dental")

        # No-show rate with high value should trigger deep dive
        deep_dive = bank.get_deep_dive_for_answer("no_show_rate", "over_30")

        assert deep_dive is not None
        assert "template" in deep_dive

    def test_get_deep_dive_no_trigger(self):
        """Should return None when answer doesn't trigger deep dive."""
        bank = IndustryQuestionBank.load("dental")

        # Low no-show rate shouldn't trigger
        deep_dive = bank.get_deep_dive_for_answer("no_show_rate", "under_5")

        assert deep_dive is None

    def test_to_question_list_for_prompt(self):
        """Should format questions for AI prompt."""
        bank = IndustryQuestionBank.load("dental")

        prompt_text = bank.to_question_list_for_prompt(max_questions=3)

        assert "patient" in prompt_text.lower() or len(prompt_text) > 0

    def test_questions_sorted_by_priority(self):
        """Questions should be sorted by priority."""
        bank = IndustryQuestionBank.load("dental")

        questions = bank.get_questions_for_category(ConfidenceCategory.QUANTIFIABLE_METRICS)

        if len(questions) >= 2:
            priorities = [q.get("priority", 99) for q in questions]
            assert priorities == sorted(priorities)


class TestGetAvailableIndustries:
    """Tests for get_available_industries function."""

    def test_returns_list_of_industries(self):
        """Should return a list of available industries."""
        industries = get_available_industries()

        assert isinstance(industries, list)
        assert len(industries) >= 5  # We created at least 5 question banks

    def test_includes_known_industries(self):
        """Should include industries we created."""
        industries = get_available_industries()

        assert "dental" in industries
        assert "coaching" in industries
        assert "veterinary" in industries

    def test_industries_are_sorted(self):
        """Industries should be sorted alphabetically."""
        industries = get_available_industries()

        assert industries == sorted(industries)


class TestQuestionBankIntegration:
    """Integration tests for question bank with confidence system."""

    def test_question_boosts_match_categories(self):
        """Expected boosts should only target categories in target_categories."""
        bank = IndustryQuestionBank.load("dental")

        for q in bank.questions:
            target_cats = set(q.get("target_categories", []))
            boost_cats = set(q.get("expected_boosts", {}).keys())

            # All boost categories should be in target categories
            assert boost_cats.issubset(target_cats), (
                f"Question {q['id']} has boosts for categories not in targets"
            )

    def test_all_industries_have_valid_structure(self):
        """All industry banks should have valid structure."""
        for industry in get_available_industries():
            bank = IndustryQuestionBank.load(industry)

            assert bank.industry  # Has industry name
            assert bank.display_name  # Has display name

            for q in bank.questions:
                assert "id" in q
                assert "question" in q
                assert "input_type" in q
                assert "target_categories" in q
                assert len(q["target_categories"]) > 0

    def test_deep_dive_templates_have_required_fields(self):
        """Deep dive templates should have required fields."""
        for industry in get_available_industries():
            bank = IndustryQuestionBank.load(industry)

            for template in bank.deep_dive_templates:
                assert "id" in template
                assert "trigger_question" in template
                assert "trigger_values" in template
                assert "template" in template
                assert isinstance(template["trigger_values"], list)
