"""
Skill Registry - Discovery and loading of skills.

The registry handles:
1. Auto-discovery of skills from the skills directory
2. Loading skills on-demand
3. Caching skill instances
4. Dependency resolution between skills

Usage:
    from src.skills import get_skill, list_skills

    # Get a skill by name
    skill = get_skill("report-generation/exec-summary")

    # List all available skills
    skills = list_skills()
"""

import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
from functools import lru_cache

from anthropic import Anthropic

from .base import BaseSkill, SyncSkill, LLMSkill, SkillContext, SkillResult

# Base classes to exclude from skill discovery
_BASE_CLASSES = {BaseSkill, SyncSkill, LLMSkill}

logger = logging.getLogger(__name__)

# =============================================================================
# Skill Metadata
# =============================================================================

class SkillMetadata:
    """Metadata about a registered skill."""

    def __init__(
        self,
        name: str,
        path: Path,
        skill_class: Optional[Type[BaseSkill]] = None,
        description: str = "",
        version: str = "1.0.0",
        dependencies: List[str] = None,
    ):
        self.name = name
        self.path = path
        self.skill_class = skill_class
        self.description = description
        self.version = version
        self.dependencies = dependencies or []

    def __repr__(self) -> str:
        return f"<SkillMetadata name='{self.name}' path='{self.path}'>"


# =============================================================================
# Skill Registry
# =============================================================================

class SkillRegistry:
    """
    Central registry for all available skills.

    Handles discovery, loading, and caching of skills.
    """

    def __init__(self, skills_dir: Optional[Path] = None, client: Optional[Anthropic] = None):
        """
        Initialize the registry.

        Args:
            skills_dir: Path to skills directory (defaults to this package's directory)
            client: Optional Anthropic client for LLM-powered skills
        """
        self.skills_dir = skills_dir or Path(__file__).parent
        self.client = client

        # Registered skills: name -> metadata
        self._registry: Dict[str, SkillMetadata] = {}

        # Cached skill instances: name -> instance
        self._instances: Dict[str, BaseSkill] = {}

        # Auto-discover skills on init
        self._discover_skills()

    def _discover_skills(self) -> None:
        """
        Discover all skills in the skills directory.

        Looks for Python files with classes that inherit from BaseSkill.
        """
        logger.info(f"Discovering skills in {self.skills_dir}")

        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            if skill_dir.name.startswith('_') or skill_dir.name.startswith('.'):
                continue
            if skill_dir.name in ('__pycache__',):
                continue

            # Check for skill.py first (canonical skill file)
            skill_file = skill_dir / "skill.py"
            if skill_file.exists():
                skill_class = self._load_skill_class(skill_file)
                if skill_class:
                    skill_name = skill_dir.name
                    self._register_skill(skill_name, skill_file, skill_class)
                continue

            # Look for any .py file with a skill class (excluding __init__.py)
            for py_file in skill_dir.glob("*.py"):
                if py_file.name.startswith('_'):
                    continue
                skill_class = self._load_skill_class(py_file)
                if skill_class:
                    skill_name = f"{skill_dir.name}/{py_file.stem}"
                    self._register_skill(skill_name, py_file, skill_class)

        logger.info(f"Discovered {len(self._registry)} skills")

    def _load_skill_class(self, file_path: Path) -> Optional[Type[BaseSkill]]:
        """
        Load a skill class from a Python file.

        Args:
            file_path: Path to the Python file

        Returns:
            The skill class or None if not found
        """
        import sys

        # Skip __init__.py files - they often have relative imports that fail
        # when loaded in isolation. We'll load skill files directly instead.
        if file_path.name == "__init__.py":
            return None

        try:
            # Add parent directory to path temporarily for relative imports
            parent_dir = str(file_path.parent)
            skills_dir = str(self.skills_dir)

            paths_to_add = []
            if parent_dir not in sys.path:
                paths_to_add.append(parent_dir)
            if skills_dir not in sys.path:
                paths_to_add.append(skills_dir)

            for path in paths_to_add:
                sys.path.insert(0, path)

            try:
                spec = importlib.util.spec_from_file_location(
                    f"skill_{file_path.stem}",
                    file_path
                )
                if spec is None or spec.loader is None:
                    return None

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Look for classes that inherit from BaseSkill
                # Exclude base classes themselves (BaseSkill, SyncSkill, LLMSkill)
                for name, obj in vars(module).items():
                    if (
                        isinstance(obj, type) and
                        issubclass(obj, BaseSkill) and
                        obj not in _BASE_CLASSES and
                        not name.startswith('_') and
                        name not in ('BaseSkill', 'SyncSkill', 'LLMSkill')
                    ):
                        return obj

                return None

            finally:
                # Clean up sys.path
                for path in paths_to_add:
                    if path in sys.path:
                        sys.path.remove(path)

        except Exception as e:
            logger.warning(f"Failed to load skill from {file_path}: {e}")
            return None

    def _register_skill(
        self,
        name: str,
        path: Path,
        skill_class: Type[BaseSkill]
    ) -> None:
        """Register a skill in the registry."""
        metadata = SkillMetadata(
            name=name,
            path=path,
            skill_class=skill_class,
            description=getattr(skill_class, 'description', ''),
            version=getattr(skill_class, 'version', '1.0.0'),
            dependencies=getattr(skill_class, 'dependencies', []),
        )
        self._registry[name] = metadata
        logger.debug(f"Registered skill: {name}")

        # Also register by the skill's class name attribute if different
        # This allows lookup by skill.name (e.g., "followup-question") as well as path
        skill_name = getattr(skill_class, 'name', None)
        if skill_name and skill_name != name and skill_name not in self._registry:
            self._registry[skill_name] = metadata
            logger.debug(f"Also registered as: {skill_name}")

    def register(self, skill_class: Type[BaseSkill], name: Optional[str] = None) -> None:
        """
        Manually register a skill class.

        Args:
            skill_class: The skill class to register
            name: Optional name override (defaults to skill's name attribute)
        """
        skill_name = name or getattr(skill_class, 'name', skill_class.__name__)
        metadata = SkillMetadata(
            name=skill_name,
            path=Path(__file__),  # Placeholder
            skill_class=skill_class,
            description=getattr(skill_class, 'description', ''),
            version=getattr(skill_class, 'version', '1.0.0'),
            dependencies=getattr(skill_class, 'dependencies', []),
        )
        self._registry[skill_name] = metadata
        logger.info(f"Manually registered skill: {skill_name}")

    def get(self, name: str, fresh: bool = False) -> Optional[BaseSkill]:
        """
        Get a skill instance by name.

        Args:
            name: The skill name (e.g., "report-generation/exec-summary" or "exec-summary")
            fresh: If True, create a new instance instead of cached

        Returns:
            The skill instance or None if not found
        """
        # Try exact match first
        if name in self._registry:
            pass  # Use as-is
        else:
            # Normalize query for flexible matching
            normalized = name.replace('/', '-').replace('\\', '-').replace('_', '-')

            # Try to find a matching skill
            matched = False
            for registered_name in self._registry:
                # Normalize the registered name for comparison
                reg_normalized = registered_name.replace('/', '-').replace('\\', '-').replace('_', '-')

                if (reg_normalized == normalized or
                    registered_name.endswith(name) or
                    name.endswith(registered_name) or
                    reg_normalized.endswith(normalized) or
                    normalized.endswith(reg_normalized)):
                    name = registered_name
                    matched = True
                    break

            if not matched:
                logger.warning(f"Skill not found: {name}")
                return None

        # Check cache
        if not fresh and name in self._instances:
            return self._instances[name]

        # Create new instance
        metadata = self._registry[name]
        if not metadata.skill_class:
            logger.error(f"Skill {name} has no class")
            return None

        try:
            instance = metadata.skill_class(client=self.client)
            self._instances[name] = instance
            return instance

        except Exception as e:
            logger.error(f"Failed to instantiate skill {name}: {e}")
            return None

    def list(self) -> List[SkillMetadata]:
        """List all registered skills."""
        return list(self._registry.values())

    def list_names(self) -> List[str]:
        """List all registered skill names."""
        return list(self._registry.keys())

    def has(self, name: str) -> bool:
        """Check if a skill is registered."""
        return name in self._registry

    def clear_cache(self) -> None:
        """Clear all cached skill instances."""
        self._instances.clear()

    def set_client(self, client: Anthropic) -> None:
        """Set the Anthropic client for LLM-powered skills."""
        self.client = client
        # Clear cache so new instances get the client
        self.clear_cache()


# =============================================================================
# Global Registry Instance
# =============================================================================

_registry: Optional[SkillRegistry] = None


def get_registry(client: Optional[Anthropic] = None) -> SkillRegistry:
    """
    Get the global skill registry.

    Args:
        client: Optional Anthropic client for LLM skills

    Returns:
        The global SkillRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = SkillRegistry(client=client)
    elif client and not _registry.client:
        _registry.set_client(client)
    return _registry


def get_skill(name: str, client: Optional[Anthropic] = None) -> Optional[BaseSkill]:
    """
    Get a skill by name.

    Convenience function that uses the global registry.

    Args:
        name: The skill name
        client: Optional Anthropic client

    Returns:
        The skill instance or None
    """
    return get_registry(client).get(name)


def list_skills() -> List[str]:
    """List all available skill names."""
    return get_registry().list_names()


def has_skill(name: str) -> bool:
    """Check if a skill exists."""
    return get_registry().has(name)


# =============================================================================
# Skill Execution Helper
# =============================================================================

async def run_skill(
    name: str,
    context: SkillContext,
    client: Optional[Anthropic] = None
) -> SkillResult:
    """
    Run a skill by name with the given context.

    Convenience function for one-off skill execution.

    Args:
        name: The skill name
        context: The execution context
        client: Optional Anthropic client

    Returns:
        The skill result

    Raises:
        ValueError: If skill not found
    """
    skill = get_skill(name, client)
    if not skill:
        raise ValueError(f"Skill not found: {name}")

    return await skill.run(context)


# =============================================================================
# Decorator for Skill Registration
# =============================================================================

def skill(name: Optional[str] = None):
    """
    Decorator to register a skill class.

    Usage:
        @skill("my-custom-skill")
        class MySkill(BaseSkill):
            ...

    Args:
        name: Optional name override
    """
    def decorator(cls: Type[BaseSkill]) -> Type[BaseSkill]:
        get_registry().register(cls, name)
        return cls
    return decorator
