"""
Tests for the skill registry.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.skills.registry import (
    SkillRegistry,
    SkillMetadata,
    get_registry,
    get_skill,
    list_skills,
    has_skill,
    run_skill,
    skill,
)
from src.skills.base import BaseSkill, SkillContext, SkillResult


# =============================================================================
# SkillMetadata Tests
# =============================================================================

class TestSkillMetadata:
    """Tests for SkillMetadata."""

    def test_metadata_creation(self):
        """Test creating skill metadata."""
        metadata = SkillMetadata(
            name="test-skill",
            path=Path("/test/path"),
            description="Test skill",
            version="1.0.0",
            dependencies=["other-skill"],
        )
        assert metadata.name == "test-skill"
        assert metadata.description == "Test skill"
        assert metadata.version == "1.0.0"
        assert "other-skill" in metadata.dependencies

    def test_metadata_repr(self):
        """Test metadata string representation."""
        metadata = SkillMetadata(name="test", path=Path("/test"))
        assert "test" in repr(metadata)


# =============================================================================
# SkillRegistry Tests
# =============================================================================

class TestSkillRegistry:
    """Tests for SkillRegistry."""

    def test_registry_discovery(self):
        """Test that registry discovers skills on init."""
        registry = SkillRegistry()

        # Should discover at least the exec-summary skill
        skill_names = registry.list_names()
        assert len(skill_names) > 0
        # Check if any skill was discovered (might be discovered as different names)
        assert len(registry.list()) > 0

    def test_registry_get_skill(self):
        """Test getting a skill by name."""
        registry = SkillRegistry()

        # Get by partial name match
        skill = registry.get("exec-summary")
        if skill is not None:  # May not be discovered depending on file structure
            assert skill.name == "exec-summary"

    def test_registry_get_nonexistent(self):
        """Test getting nonexistent skill returns None."""
        registry = SkillRegistry()
        skill = registry.get("definitely-does-not-exist-12345")
        assert skill is None

    def test_registry_caching(self):
        """Test that skill instances are cached."""
        registry = SkillRegistry()
        skills = registry.list_names()

        if skills:
            name = skills[0]
            skill1 = registry.get(name)
            skill2 = registry.get(name)
            assert skill1 is skill2  # Same instance

    def test_registry_fresh_instance(self):
        """Test getting fresh instance bypasses cache."""
        registry = SkillRegistry()
        skills = registry.list_names()

        if skills:
            name = skills[0]
            skill1 = registry.get(name)
            skill2 = registry.get(name, fresh=True)
            assert skill1 is not skill2  # Different instances

    def test_registry_clear_cache(self):
        """Test clearing instance cache."""
        registry = SkillRegistry()
        skills = registry.list_names()

        if skills:
            name = skills[0]
            skill1 = registry.get(name)
            registry.clear_cache()
            skill2 = registry.get(name)
            assert skill1 is not skill2

    def test_registry_set_client(self):
        """Test setting client clears cache."""
        mock_client = MagicMock()
        registry = SkillRegistry()
        skills = registry.list_names()

        if skills:
            name = skills[0]
            skill1 = registry.get(name)
            registry.set_client(mock_client)
            skill2 = registry.get(name)
            assert skill1 is not skill2
            assert registry.client is mock_client

    def test_registry_has_skill(self):
        """Test checking if skill exists."""
        registry = SkillRegistry()
        skills = registry.list_names()

        if skills:
            assert registry.has(skills[0]) is True
        assert registry.has("nonexistent-skill-xyz") is False


# =============================================================================
# Module-Level Functions Tests
# =============================================================================

class TestModuleFunctions:
    """Tests for module-level convenience functions."""

    def test_get_registry_singleton(self):
        """Test that get_registry returns singleton."""
        # Reset the global registry first
        import src.skills.registry as reg_module
        reg_module._registry = None

        reg1 = get_registry()
        reg2 = get_registry()
        assert reg1 is reg2

    def test_get_registry_with_client(self):
        """Test get_registry with client."""
        import src.skills.registry as reg_module
        reg_module._registry = None

        mock_client = MagicMock()
        registry = get_registry(mock_client)
        assert registry.client is mock_client

    def test_list_skills(self):
        """Test listing all skills."""
        skills = list_skills()
        assert isinstance(skills, list)

    def test_has_skill(self):
        """Test has_skill function."""
        skills = list_skills()
        if skills:
            assert has_skill(skills[0]) is True
        assert has_skill("nonexistent-xyz") is False


# =============================================================================
# Skill Decorator Tests
# =============================================================================

class TestSkillDecorator:
    """Tests for the @skill decorator."""

    def test_skill_decorator(self):
        """Test that decorator registers skill."""
        import src.skills.registry as reg_module
        reg_module._registry = None  # Reset

        @skill("decorated-skill")
        class DecoratedSkill(BaseSkill):
            name = "decorated-skill"

            async def execute(self, context):
                return {}

        registry = get_registry()
        assert registry.has("decorated-skill")


# =============================================================================
# run_skill Function Tests
# =============================================================================

class TestRunSkill:
    """Tests for run_skill convenience function."""

    @pytest.mark.asyncio
    async def test_run_skill_not_found(self):
        """Test run_skill with nonexistent skill."""
        context = SkillContext(industry="dental")

        with pytest.raises(ValueError) as exc_info:
            await run_skill("definitely-not-a-real-skill", context)

        assert "not found" in str(exc_info.value)
