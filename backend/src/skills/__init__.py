"""
Skills Module - Reusable code workflows for CRB analysis.

Skills are the CODE layer in the three-layer intelligence system:
- Layer 1: Knowledge (static data)
- Layer 2: Expertise (learned data)
- Layer 3: Skills (reusable code) <-- This module

Skills provide:
- Proven code patterns that don't need regenerating
- Consistent output formatting
- Integration with expertise for context-aware execution
- Composable workflows

Usage:
    from src.skills import get_skill, run_skill, SkillContext

    # Get and run a skill
    skill = get_skill("report-generation/exec-summary")
    context = SkillContext(
        industry="dental",
        report_data={...},
        expertise={...}
    )
    result = await skill.run(context)

    # Or use the convenience function
    result = await run_skill("report-generation/exec-summary", context)

Available Skills:
    - report-generation/exec-summary: Generate executive summaries
    - report-generation/three-options: Format Three Options recommendations
    - finding-generation/structure: Structure findings consistently
    - interview/followup: Generate adaptive follow-up questions
    - (more to come)

See Also:
    - docs/ARCHITECTURE.md for the full architecture
    - src/expertise/ for the learned data layer
    - src/knowledge/ for the static data layer
"""

from .base import (
    BaseSkill,
    SyncSkill,
    LLMSkill,
    SkillContext,
    SkillResult,
    SkillError,
)

from .registry import (
    SkillRegistry,
    SkillMetadata,
    get_registry,
    get_skill,
    list_skills,
    has_skill,
    run_skill,
    skill,
)

__all__ = [
    # Base classes
    "BaseSkill",
    "SyncSkill",
    "LLMSkill",
    # Models
    "SkillContext",
    "SkillResult",
    "SkillError",
    # Registry
    "SkillRegistry",
    "SkillMetadata",
    "get_registry",
    "get_skill",
    "list_skills",
    "has_skill",
    "run_skill",
    "skill",
]


def init_skills(client=None):
    """
    Initialize the skills system.

    Call this at application startup to:
    1. Discover all skills
    2. Set up the LLM client for LLM-powered skills

    Args:
        client: Optional Anthropic client for LLM skills
    """
    registry = get_registry(client)
    return registry
