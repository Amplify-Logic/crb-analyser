"""
Generation Trace Model

Captures detailed reasoning, tool calls, and logic used during report generation.
Displayed in dev mode for debugging and transparency.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class TraceEventType(str, Enum):
    """Types of events in the generation trace."""
    PHASE_START = "phase_start"
    PHASE_END = "phase_end"
    LLM_CALL = "llm_call"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    TOOL_CALL = "tool_call"
    DECISION = "decision"
    VALIDATION = "validation"
    ERROR = "error"
    INFO = "info"


class LLMCallTrace(BaseModel):
    """Trace of a single LLM call."""
    task: str
    model: str
    prompt_preview: str  # First 500 chars
    prompt_tokens: int
    response_preview: str  # First 500 chars
    response_tokens: int
    duration_ms: float
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class KnowledgeRetrievalTrace(BaseModel):
    """Trace of knowledge base retrieval."""
    source: str  # e.g., "industry_knowledge", "semantic_rag", "vendors"
    query: Optional[str] = None
    results_count: int
    results_preview: List[str]  # Titles/names of top results
    duration_ms: float
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class DecisionTrace(BaseModel):
    """Trace of a decision point in generation."""
    decision_type: str  # e.g., "finding_inclusion", "confidence_level", "recommendation_priority"
    input_factors: Dict[str, Any]
    outcome: str
    reasoning: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ValidationTrace(BaseModel):
    """Trace of a validation step."""
    validation_type: str  # e.g., "math_check", "source_verification", "consistency_check"
    items_checked: int
    issues_found: int
    adjustments_made: List[str]
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class PhaseTrace(BaseModel):
    """Trace of a generation phase."""
    phase_name: str
    started_at: str
    completed_at: Optional[str] = None
    duration_ms: Optional[float] = None
    steps: List[str] = Field(default_factory=list)
    llm_calls: List[LLMCallTrace] = Field(default_factory=list)
    knowledge_retrievals: List[KnowledgeRetrievalTrace] = Field(default_factory=list)
    decisions: List[DecisionTrace] = Field(default_factory=list)
    validations: List[ValidationTrace] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    output_summary: Optional[str] = None


class GenerationTrace(BaseModel):
    """
    Complete trace of a report generation.

    Captures all phases, LLM calls, knowledge retrievals, decisions,
    and reasoning used during generation.
    """
    report_id: str
    session_id: str
    tier: str
    started_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    total_duration_ms: Optional[float] = None

    # Summary stats
    total_llm_calls: int = 0
    total_tokens_used: int = 0
    total_knowledge_retrievals: int = 0
    total_decisions: int = 0

    # Input summary
    input_summary: Dict[str, Any] = Field(default_factory=dict)

    # Phases
    phases: List[PhaseTrace] = Field(default_factory=list)

    # Cross-phase info
    models_used: List[str] = Field(default_factory=list)
    knowledge_sources_used: List[str] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return self.model_dump()


class TraceCollector:
    """
    Collects trace events during report generation.

    Usage:
        collector = TraceCollector(report_id, session_id, tier)
        collector.start_phase("analysis")
        collector.log_llm_call(task, model, prompt, response, tokens, duration)
        collector.log_decision("finding_inclusion", factors, outcome, reasoning)
        collector.end_phase("analysis", "Generated executive summary")
        trace = collector.finalize()
    """

    def __init__(self, report_id: str, session_id: str, tier: str):
        self.report_id = report_id
        self.session_id = session_id
        self.tier = tier
        self.started_at = datetime.utcnow()
        self.current_phase: Optional[PhaseTrace] = None
        self.phases: List[PhaseTrace] = []
        self.models_used: set = set()
        self.knowledge_sources: set = set()
        self.total_llm_calls = 0
        self.total_tokens = 0
        self.total_retrievals = 0
        self.total_decisions = 0
        self.input_summary: Dict[str, Any] = {}

    def set_input_summary(
        self,
        company_name: str,
        industry: str,
        answers_count: int,
        interview_messages: int,
        has_company_profile: bool,
    ):
        """Record summary of input data."""
        self.input_summary = {
            "company_name": company_name,
            "industry": industry,
            "quiz_answers_count": answers_count,
            "interview_messages": interview_messages,
            "has_company_profile": has_company_profile,
        }

    def start_phase(self, phase_name: str):
        """Start a new generation phase."""
        if self.current_phase:
            self.end_phase(self.current_phase.phase_name)

        self.current_phase = PhaseTrace(
            phase_name=phase_name,
            started_at=datetime.utcnow().isoformat(),
        )

    def add_step(self, step: str):
        """Add a step to the current phase."""
        if self.current_phase:
            self.current_phase.steps.append(step)

    def log_llm_call(
        self,
        task: str,
        model: str,
        prompt: str,
        response: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: float,
    ):
        """Log an LLM call."""
        trace = LLMCallTrace(
            task=task,
            model=model,
            prompt_preview=prompt[:500] + ("..." if len(prompt) > 500 else ""),
            prompt_tokens=input_tokens,
            response_preview=response[:500] + ("..." if len(response) > 500 else ""),
            response_tokens=output_tokens,
            duration_ms=duration_ms,
        )

        if self.current_phase:
            self.current_phase.llm_calls.append(trace)

        self.models_used.add(model)
        self.total_llm_calls += 1
        self.total_tokens += input_tokens + output_tokens

    def log_knowledge_retrieval(
        self,
        source: str,
        results_count: int,
        results_preview: List[str],
        duration_ms: float = 0,
        query: Optional[str] = None,
    ):
        """Log a knowledge base retrieval."""
        trace = KnowledgeRetrievalTrace(
            source=source,
            query=query[:200] if query else None,
            results_count=results_count,
            results_preview=results_preview[:5],  # Top 5
            duration_ms=duration_ms,
        )

        if self.current_phase:
            self.current_phase.knowledge_retrievals.append(trace)

        self.knowledge_sources.add(source)
        self.total_retrievals += 1

    def log_decision(
        self,
        decision_type: str,
        input_factors: Dict[str, Any],
        outcome: str,
        reasoning: str,
    ):
        """Log a decision point."""
        trace = DecisionTrace(
            decision_type=decision_type,
            input_factors=input_factors,
            outcome=outcome,
            reasoning=reasoning,
        )

        if self.current_phase:
            self.current_phase.decisions.append(trace)

        self.total_decisions += 1

    def log_validation(
        self,
        validation_type: str,
        items_checked: int,
        issues_found: int,
        adjustments_made: List[str],
    ):
        """Log a validation step."""
        trace = ValidationTrace(
            validation_type=validation_type,
            items_checked=items_checked,
            issues_found=issues_found,
            adjustments_made=adjustments_made,
        )

        if self.current_phase:
            self.current_phase.validations.append(trace)

    def log_error(self, error_message: str):
        """Log an error in the current phase."""
        if self.current_phase:
            self.current_phase.errors.append(error_message)

    def end_phase(self, phase_name: str, output_summary: Optional[str] = None):
        """End the current phase."""
        if self.current_phase and self.current_phase.phase_name == phase_name:
            now = datetime.utcnow()
            started = datetime.fromisoformat(self.current_phase.started_at)
            self.current_phase.completed_at = now.isoformat()
            self.current_phase.duration_ms = (now - started).total_seconds() * 1000
            self.current_phase.output_summary = output_summary
            self.phases.append(self.current_phase)
            self.current_phase = None

    def finalize(self) -> GenerationTrace:
        """Finalize and return the complete trace."""
        # End any open phase
        if self.current_phase:
            self.end_phase(self.current_phase.phase_name)

        now = datetime.utcnow()
        total_duration = (now - self.started_at).total_seconds() * 1000

        return GenerationTrace(
            report_id=self.report_id,
            session_id=self.session_id,
            tier=self.tier,
            started_at=self.started_at.isoformat(),
            completed_at=now.isoformat(),
            total_duration_ms=total_duration,
            total_llm_calls=self.total_llm_calls,
            total_tokens_used=self.total_tokens,
            total_knowledge_retrievals=self.total_retrievals,
            total_decisions=self.total_decisions,
            input_summary=self.input_summary,
            phases=self.phases,
            models_used=list(self.models_used),
            knowledge_sources_used=list(self.knowledge_sources),
        )
