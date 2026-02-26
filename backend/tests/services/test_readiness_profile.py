"""Tests for readiness profile builder function."""
import pytest
from src.services.readiness_profile import build_readiness_profile
from src.cli.fabricator import fabricate_quiz_session


class TestInfrastructure:
    """Test infrastructure readiness mapping."""

    def test_no_tools_is_paper_based(self):
        """Client with no digital tools is paper-based."""
        profile = build_readiness_profile({"current_tools": []})
        assert profile["infrastructure"] == "paper-based"

    def test_single_tool_is_paper_based(self):
        """Client with only one tool is still paper-based."""
        profile = build_readiness_profile({"current_tools": ["accounting"]})
        assert profile["infrastructure"] == "paper-based"

    def test_missing_tools_field_is_paper_based(self):
        """Client with no tools field defaults to paper-based."""
        profile = build_readiness_profile({})
        assert profile["infrastructure"] == "paper-based"

    def test_low_integration_score_is_partial(self):
        """Client with tools but poor integration is partial."""
        profile = build_readiness_profile({
            "current_tools": ["crm", "accounting", "email"],
            "integration_issues": 3,
        })
        assert profile["infrastructure"] == "partial"

    def test_manual_data_entry_is_partial(self):
        """Client with manual data entry is partial even with good integration score."""
        profile = build_readiness_profile({
            "current_tools": ["crm", "accounting"],
            "integration_issues": 7,
            "manual_data_entry": True,
        })
        assert profile["infrastructure"] == "partial"

    def test_good_tools_and_integration_is_digitized(self):
        """Client with multiple tools and good integration is digitized."""
        profile = build_readiness_profile({
            "current_tools": ["crm", "accounting", "scheduling"],
            "integration_issues": 6,
            "manual_data_entry": False,
        })
        assert profile["infrastructure"] == "digitized"


class TestBuildWillingness:
    """Test build willingness mapping."""

    def test_build_preference_is_eager(self):
        """Client who prefers building is eager."""
        profile = build_readiness_profile({
            "implementation_preference": "build",
        })
        assert profile["build_willingness"] == "eager"

    def test_connect_preference_is_eager(self):
        """Client who prefers connecting is eager."""
        profile = build_readiness_profile({
            "implementation_preference": "connect",
        })
        assert profile["build_willingness"] == "eager"

    def test_high_tech_comfort_is_eager(self):
        """High tech comfort makes client eager regardless of preference."""
        profile = build_readiness_profile({
            "implementation_preference": "buy",
            "technology_comfort": 8,
        })
        assert profile["build_willingness"] == "eager"

    def test_hire_preference_is_turnkey(self):
        """Client who prefers hiring wants turnkey."""
        profile = build_readiness_profile({
            "implementation_preference": "hire",
            "technology_comfort": 5,
        })
        assert profile["build_willingness"] == "prefers-turnkey"

    def test_low_tech_comfort_is_turnkey(self):
        """Low tech comfort leans toward turnkey."""
        profile = build_readiness_profile({
            "implementation_preference": "buy",
            "technology_comfort": 2,
        })
        assert profile["build_willingness"] == "prefers-turnkey"

    def test_moderate_preference_is_open(self):
        """Moderate buy preference with medium comfort is open."""
        profile = build_readiness_profile({
            "implementation_preference": "buy",
            "technology_comfort": 5,
        })
        assert profile["build_willingness"] == "open"


class TestAIExperience:
    """Test AI experience mapping."""

    def test_no_ai_tools_is_none(self):
        """Client with no AI tools has no experience."""
        profile = build_readiness_profile({"ai_tools_used": []})
        assert profile["ai_experience"] == "none"

    def test_none_string_is_none(self):
        """Client who selected 'none' has no experience."""
        profile = build_readiness_profile({"ai_tools_used": ["none"]})
        assert profile["ai_experience"] == "none"

    def test_missing_field_is_none(self):
        """Missing ai_tools_used defaults to none."""
        profile = build_readiness_profile({})
        assert profile["ai_experience"] == "none"

    def test_few_tools_is_dabbled(self):
        """Client with 1-2 AI tools has dabbled."""
        profile = build_readiness_profile({"ai_tools_used": ["chatgpt", "copilot"]})
        assert profile["ai_experience"] == "dabbled"

    def test_many_tools_is_active_user(self):
        """Client using 3+ AI tools is an active user."""
        profile = build_readiness_profile({
            "ai_tools_used": ["chatgpt", "copilot", "midjourney"],
        })
        assert profile["ai_experience"] == "active-user"

    def test_automation_tool_is_active_user(self):
        """Client using automation tools is an active user."""
        profile = build_readiness_profile({
            "ai_tools_used": ["automation"],
        })
        assert profile["ai_experience"] == "active-user"


class TestStackAPIReadiness:
    """Test stack API readiness mapping."""

    def test_api_ready_stack(self):
        """Client with API-ready stack."""
        profile = build_readiness_profile({
            "existing_stack_api_ready": True,
        })
        assert profile["stack_api_readiness"] == "most-apis"

    def test_not_api_ready_stack(self):
        """Client without API-ready stack."""
        profile = build_readiness_profile({
            "existing_stack_api_ready": False,
        })
        assert profile["stack_api_readiness"] == "mixed"

    def test_missing_api_field_defaults_to_mixed(self):
        """Missing field defaults to mixed."""
        profile = build_readiness_profile({})
        assert profile["stack_api_readiness"] == "mixed"


class TestPassthrough:
    """Test passthrough fields."""

    def test_urgency_passthrough(self):
        """Urgency passes through directly."""
        profile = build_readiness_profile({
            "implementation_urgency": "this_week",
        })
        assert profile["urgency"] == "this_week"

    def test_urgency_default(self):
        """Default urgency is this_quarter."""
        profile = build_readiness_profile({})
        assert profile["urgency"] == "this_quarter"

    def test_preference_passthrough(self):
        """Implementation preference passes through."""
        profile = build_readiness_profile({
            "implementation_preference": "connect",
        })
        assert profile["preference"] == "connect"

    def test_preference_default(self):
        """Default preference is buy."""
        profile = build_readiness_profile({})
        assert profile["preference"] == "buy"


class TestIntegrationScenarios:
    """Test realistic client scenarios end-to-end."""

    def test_paper_based_non_technical(self):
        """Paper-based non-technical client gets appropriate profile."""
        profile = build_readiness_profile({
            "current_tools": [],
            "implementation_preference": "hire",
            "technology_comfort": 2,
            "ai_tools_used": [],
            "existing_stack_api_ready": False,
            "implementation_urgency": "this_quarter",
        })
        assert profile == {
            "infrastructure": "paper-based",
            "build_willingness": "prefers-turnkey",
            "ai_experience": "none",
            "stack_api_readiness": "mixed",
            "urgency": "this_quarter",
            "preference": "hire",
        }

    def test_digitized_eager_builder(self):
        """Digitized eager builder gets appropriate profile."""
        profile = build_readiness_profile({
            "current_tools": ["crm", "accounting", "scheduling", "email"],
            "integration_issues": 7,
            "manual_data_entry": False,
            "implementation_preference": "build",
            "technology_comfort": 9,
            "ai_tools_used": ["chatgpt", "copilot", "automation", "midjourney"],
            "existing_stack_api_ready": True,
            "implementation_urgency": "this_week",
        })
        assert profile == {
            "infrastructure": "digitized",
            "build_willingness": "eager",
            "ai_experience": "active-user",
            "stack_api_readiness": "most-apis",
            "urgency": "this_week",
            "preference": "build",
        }

    def test_partial_with_some_ai(self):
        """Partial infrastructure with some AI experience."""
        profile = build_readiness_profile({
            "current_tools": ["crm", "accounting"],
            "integration_issues": 3,
            "manual_data_entry": False,
            "implementation_preference": "buy",
            "technology_comfort": 5,
            "ai_tools_used": ["chatgpt"],
            "existing_stack_api_ready": False,
            "implementation_urgency": "this_month",
        })
        assert profile == {
            "infrastructure": "partial",
            "build_willingness": "open",
            "ai_experience": "dabbled",
            "stack_api_readiness": "mixed",
            "urgency": "this_month",
            "preference": "buy",
        }


class TestFabricatorPipeline:
    """Test full pipeline: fabricated quiz answers -> readiness profile."""

    VALID_INFRASTRUCTURE = {"paper-based", "partial", "digitized"}
    VALID_WILLINGNESS = {"prefers-turnkey", "open", "eager"}
    VALID_AI_EXPERIENCE = {"none", "dabbled", "active-user"}
    VALID_API_READINESS = {"most-apis", "mixed"}
    VALID_URGENCY = {"this_week", "this_month", "this_quarter", "no_rush"}

    def _fabricate_and_profile(self, tools: list, **profile_extras) -> dict:
        seed = {
            "name": "Test",
            "website": "https://test.com",
            "country": "NL",
            "profile": {
                "tier": "small",
                "staff_size": "1-10",
                "monthly_orders": 200,
                "platform": "shopify",
                "product_category": "fashion",
                "has_erp": False,
                "current_tools": tools,
                "pain_points": ["manual order processing"],
                **profile_extras,
            },
        }
        defaults = {"budget": 500, "hourly_cost": 40, "pain_points": []}
        session = fabricate_quiz_session(seed, defaults)
        return build_readiness_profile(session["answers"])

    def test_fabricated_answers_produce_valid_profile(self):
        """Fabricated quiz answers produce a valid readiness profile."""
        profile = self._fabricate_and_profile(
            ["shopify", "klaviyo", "gorgias"]
        )
        assert profile["infrastructure"] in self.VALID_INFRASTRUCTURE
        assert profile["build_willingness"] in self.VALID_WILLINGNESS
        assert profile["ai_experience"] in self.VALID_AI_EXPERIENCE
        assert profile["stack_api_readiness"] in self.VALID_API_READINESS
        assert profile["urgency"] in self.VALID_URGENCY

    def test_missing_readiness_fields_produce_safe_fallback(self):
        """Empty answers produce a safe default profile (not an error)."""
        profile = build_readiness_profile({})
        assert profile["infrastructure"] == "paper-based"
        assert profile["build_willingness"] == "open"
        assert profile["ai_experience"] == "none"
        assert profile["stack_api_readiness"] == "mixed"
        assert profile["urgency"] == "this_quarter"

    def test_digital_first_seed_produces_eager_profile(self):
        """Digital-first seed with explicit readiness fields -> eager profile."""
        profile = self._fabricate_and_profile(
            ["shopify", "klaviyo", "segment", "netsuite", "gorgias"],
            implementation_preference="build",
            ai_tools_used=["chatgpt", "copilot", "automation"],
            integration_issues=8,
            manual_data_entry=False,
        )
        assert profile["infrastructure"] == "digitized"
        assert profile["build_willingness"] == "eager"
        assert profile["ai_experience"] == "active-user"
        assert profile["stack_api_readiness"] == "most-apis"

    def test_traditional_seed_produces_turnkey_profile(self):
        """Traditional seed with basic tools -> paper-based/turnkey profile."""
        profile = self._fabricate_and_profile(
            ["paper forms"],
            implementation_preference="hire",
            ai_tools_used=[],
            integration_issues=2,
            manual_data_entry=True,
        )
        assert profile["infrastructure"] == "paper-based"
        assert profile["build_willingness"] == "prefers-turnkey"
        assert profile["ai_experience"] == "none"

    def test_all_profile_values_in_valid_ranges(self):
        """Verify all output values fall within expected enums."""
        for tools in [[], ["shopify"], ["shopify", "klaviyo", "gorgias"]]:
            profile = self._fabricate_and_profile(tools)
            assert profile["infrastructure"] in self.VALID_INFRASTRUCTURE
            assert profile["build_willingness"] in self.VALID_WILLINGNESS
            assert profile["ai_experience"] in self.VALID_AI_EXPERIENCE
            assert profile["stack_api_readiness"] in self.VALID_API_READINESS
            assert profile["urgency"] in self.VALID_URGENCY
