"""Tests for FourOptionsSkill."""
import pytest
from unittest.mock import MagicMock
# Import using importlib since directory has hyphen
import importlib.util
import sys
from pathlib import Path

# Load the module from the hyphenated directory
skill_path = Path(__file__).parent.parent.parent / "src" / "skills" / "report-generation" / "four_options.py"
spec = importlib.util.spec_from_file_location("four_options", skill_path)
four_options_module = importlib.util.module_from_spec(spec)
sys.modules["four_options"] = four_options_module
spec.loader.exec_module(four_options_module)
FourOptionsSkill = four_options_module.FourOptionsSkill
from src.skills.base import SkillContext
from src.models.user_profile import (
    UserProfile,
    CapabilityLevel,
    ImplementationPreference,
    BudgetTier,
)


class TestFourOptionsSkill:
    """Test FourOptionsSkill."""

    @pytest.fixture
    def skill(self):
        """Create skill instance."""
        return FourOptionsSkill()

    @pytest.fixture
    def mock_context(self):
        """Create mock skill context."""
        return SkillContext(
            industry="consulting",
            finding={
                "id": "finding-001",
                "title": "Automate appointment reminders",
                "description": "Send automatic reminders before appointments",
                "category": "efficiency",
            },
            user_profile=UserProfile(
                capability=CapabilityLevel.AUTOMATION_USER,
                preference=ImplementationPreference.CONNECT,
                budget=BudgetTier.MODERATE,
            ),
            vendors=[
                {"slug": "calendly", "name": "Calendly", "monthly_price": 12},
            ],
        )

    def test_skill_metadata(self, skill):
        """Test skill has correct metadata."""
        assert skill.name == "four-options"
        assert skill.requires_llm is True

    def test_build_prompt_includes_user_profile(self, skill, mock_context):
        """Test prompt includes user profile context."""
        prompt = skill._build_prompt(mock_context)

        assert "automation_user" in prompt.lower() or "automation user" in prompt.lower()
        assert "connect" in prompt.lower()
        assert "moderate" in prompt.lower()

    def test_build_prompt_includes_finding(self, skill, mock_context):
        """Test prompt includes finding details."""
        prompt = skill._build_prompt(mock_context)

        assert "appointment reminders" in prompt.lower()
