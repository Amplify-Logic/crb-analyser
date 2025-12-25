"""
BaseSkill - Foundation class for all CRB skills.

Skills are reusable code workflows that execute specific tasks consistently.
They can optionally use expertise data for context-aware execution.

Design Principles:
1. Skills are CODE, not data - they execute, not just inform
2. Skills can use Expertise for context, but work without it
3. Skills are stateless - all context passed in, results passed out
4. Skills are composable - one skill can call another
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Generic
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Skill Input/Output Models
# =============================================================================

class SkillContext(BaseModel):
    """Context passed to skill execution."""

    # Required
    industry: str

    # Optional context
    company_name: Optional[str] = None
    company_size: Optional[str] = None
    quiz_answers: Optional[Dict[str, Any]] = None
    interview_data: Optional[Dict[str, Any]] = None

    # Expertise injection (from Layer 2)
    expertise: Optional[Dict[str, Any]] = None

    # Knowledge injection (from Layer 1)
    knowledge: Optional[Dict[str, Any]] = None

    # Report data (for report generation skills)
    report_data: Optional[Dict[str, Any]] = None

    # Additional context
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SkillResult(BaseModel):
    """Result from skill execution."""

    success: bool
    data: Any  # The actual result data
    skill_name: str
    execution_time_ms: float

    # Optional metadata
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    expertise_applied: bool = False
    warnings: List[str] = Field(default_factory=list)

    # For debugging/learning
    debug_info: Optional[Dict[str, Any]] = None


class SkillError(Exception):
    """Exception raised when a skill fails."""

    def __init__(self, skill_name: str, message: str, recoverable: bool = True):
        self.skill_name = skill_name
        self.message = message
        self.recoverable = recoverable
        super().__init__(f"[{skill_name}] {message}")


# =============================================================================
# Base Skill Class
# =============================================================================

T = TypeVar('T')


class BaseSkill(ABC, Generic[T]):
    """
    Base class for all CRB skills.

    A skill encapsulates a reusable workflow that:
    - Takes structured input (SkillContext)
    - Executes proven code/templates
    - Returns structured output (SkillResult)
    - Optionally uses expertise for calibration

    Example Usage:
        skill = ExecSummarySkill()
        result = await skill.run(context)
        if result.success:
            summary = result.data
    """

    # Skill metadata - override in subclasses
    name: str = "base-skill"
    description: str = "Base skill class"
    version: str = "1.0.0"

    # Skill configuration
    requires_expertise: bool = False  # If True, warns when expertise not provided
    requires_knowledge: bool = False  # If True, warns when knowledge not provided
    requires_llm: bool = False  # If True, needs Claude API access

    # Dependencies - other skills this skill may call
    dependencies: List[str] = []

    def __init__(self, client: Optional[Any] = None):
        """
        Initialize the skill.

        Args:
            client: Optional Anthropic client for LLM-powered skills
        """
        self.client = client
        self._execution_count = 0

    async def run(self, context: SkillContext) -> SkillResult:
        """
        Execute the skill with given context.

        This is the main entry point. It:
        1. Validates input
        2. Calls the skill's execute method
        3. Wraps result in SkillResult

        Args:
            context: The execution context

        Returns:
            SkillResult with success/failure and data
        """
        start_time = datetime.now()
        warnings = []

        # Validate requirements
        if self.requires_expertise and not context.expertise:
            warnings.append(f"Skill '{self.name}' works better with expertise data")

        if self.requires_knowledge and not context.knowledge:
            warnings.append(f"Skill '{self.name}' works better with knowledge data")

        if self.requires_llm and not self.client:
            raise SkillError(
                self.name,
                "This skill requires an LLM client but none was provided",
                recoverable=False
            )

        try:
            # Execute the skill
            result_data = await self.execute(context)

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            self._execution_count += 1

            return SkillResult(
                success=True,
                data=result_data,
                skill_name=self.name,
                execution_time_ms=execution_time,
                expertise_applied=context.expertise is not None,
                warnings=warnings
            )

        except SkillError:
            raise  # Re-raise skill errors as-is

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Skill '{self.name}' failed: {e}", exc_info=True)

            return SkillResult(
                success=False,
                data=None,
                skill_name=self.name,
                execution_time_ms=execution_time,
                expertise_applied=context.expertise is not None,
                warnings=warnings + [str(e)]
            )

    @abstractmethod
    async def execute(self, context: SkillContext) -> T:
        """
        Execute the skill's core logic.

        Override this in subclasses to implement the skill.

        Args:
            context: The execution context with all needed data

        Returns:
            The skill's result data (type varies by skill)

        Raises:
            SkillError: If the skill cannot complete
        """
        pass

    def validate_context(self, context: SkillContext, required_fields: List[str]) -> None:
        """
        Validate that required fields are present in context.

        Args:
            context: The context to validate
            required_fields: List of required field names

        Raises:
            SkillError: If validation fails
        """
        missing = []
        for field in required_fields:
            if not getattr(context, field, None):
                missing.append(field)

        if missing:
            raise SkillError(
                self.name,
                f"Missing required context fields: {', '.join(missing)}",
                recoverable=False
            )

    def get_expertise_value(
        self,
        context: SkillContext,
        key: str,
        default: Any = None
    ) -> Any:
        """
        Safely get a value from expertise data.

        Args:
            context: The skill context
            key: Dot-notation key (e.g., "industry_expertise.avg_ai_readiness")
            default: Default value if not found

        Returns:
            The value or default
        """
        if not context.expertise:
            return default

        value = context.expertise
        for part in key.split('.'):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return default
            if value is None:
                return default

        return value

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}' v{self.version}>"


# =============================================================================
# Sync Skill Wrapper (for skills that don't need async)
# =============================================================================

class SyncSkill(BaseSkill[T]):
    """
    Base class for synchronous skills.

    Use this when the skill doesn't need async operations.
    """

    async def execute(self, context: SkillContext) -> T:
        """Wraps sync execute_sync in async."""
        return self.execute_sync(context)

    @abstractmethod
    def execute_sync(self, context: SkillContext) -> T:
        """
        Synchronous execution method.

        Override this instead of execute() for sync skills.
        """
        pass


# =============================================================================
# LLM-Powered Skill Base
# =============================================================================

class LLMSkill(BaseSkill[T]):
    """
    Base class for skills that use Claude for generation.

    Provides helper methods for LLM calls with proper error handling.
    """

    requires_llm: bool = True

    # Default model settings
    default_model: str = "claude-sonnet-4-20250514"
    default_max_tokens: int = 4000

    async def call_llm(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Call Claude with the given prompt.

        Args:
            prompt: The user message
            system: Optional system prompt
            model: Model to use (defaults to default_model)
            max_tokens: Max tokens (defaults to default_max_tokens)

        Returns:
            The response text

        Raises:
            SkillError: If the LLM call fails
        """
        if not self.client:
            raise SkillError(self.name, "LLM client not configured", recoverable=False)

        try:
            messages = [{"role": "user", "content": prompt}]

            kwargs = {
                "model": model or self.default_model,
                "max_tokens": max_tokens or self.default_max_tokens,
                "messages": messages,
            }

            if system:
                kwargs["system"] = system

            response = self.client.messages.create(**kwargs)
            return response.content[0].text.strip()

        except Exception as e:
            raise SkillError(
                self.name,
                f"LLM call failed: {e}",
                recoverable=True
            )

    async def call_llm_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Call Claude and parse response as JSON.

        Args:
            prompt: The user message (should request JSON output)
            system: Optional system prompt
            model: Model to use

        Returns:
            Parsed JSON response

        Raises:
            SkillError: If the call or parsing fails
        """
        import json
        import re

        response = await self.call_llm(prompt, system, model)

        # Try to extract JSON from response
        try:
            # Remove markdown code blocks if present
            if "```" in response:
                match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
                if match:
                    response = match.group(1)

            return json.loads(response.strip())

        except json.JSONDecodeError as e:
            raise SkillError(
                self.name,
                f"Failed to parse LLM response as JSON: {e}",
                recoverable=True
            )
