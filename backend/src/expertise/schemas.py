"""
Expertise Schemas - Data models for self-improving agent expertise.

These models define the "mental model" that the CRB agent builds over time.
Each analysis contributes to this evolving knowledge base.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class PainPointPattern(BaseModel):
    """A recurring pain point observed across analyses."""
    name: str
    frequency: int = 1  # How many times observed
    avg_impact: str = "medium"  # low, medium, high
    typical_causes: List[str] = Field(default_factory=list)
    effective_solutions: List[str] = Field(default_factory=list)
    last_seen: datetime = Field(default_factory=datetime.utcnow)


class VendorFit(BaseModel):
    """Learned knowledge about when a vendor works well."""
    vendor_name: str
    good_for: List[str] = Field(default_factory=list)  # Use cases where it excels
    not_good_for: List[str] = Field(default_factory=list)  # Use cases to avoid
    company_size_fit: List[str] = Field(default_factory=list)  # solo, small, medium, large
    price_accuracy: float = 1.0  # Multiplier if our prices are off
    recommendation_count: int = 0
    notes: List[str] = Field(default_factory=list)


class RecommendationPattern(BaseModel):
    """A successful recommendation pattern."""
    pattern: str  # e.g., "For agencies under 10 people with client communication issues"
    recommendation: str  # What we recommended
    frequency: int = 1
    context: Dict[str, Any] = Field(default_factory=dict)


class ProcessInsight(BaseModel):
    """Learned insight about a business process."""
    process_name: str
    automation_potential_observed: List[int] = Field(default_factory=list)  # Scores we've given
    common_tools_used: List[str] = Field(default_factory=list)
    common_blockers: List[str] = Field(default_factory=list)
    quick_win_potential: bool = False


class IndustryExpertise(BaseModel):
    """
    The agent's evolving mental model for a specific industry.

    This is what makes an "agent expert" - accumulated knowledge
    that improves recommendations over time.
    """
    industry: str
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    total_analyses: int = 0
    confidence: str = "low"  # low, medium, high (based on analysis count)

    # Pain points we've observed
    pain_points: Dict[str, PainPointPattern] = Field(default_factory=dict)

    # Process insights
    processes: Dict[str, ProcessInsight] = Field(default_factory=dict)

    # What works for this industry
    effective_patterns: List[RecommendationPattern] = Field(default_factory=list)

    # What doesn't work (learned from experience)
    anti_patterns: List[str] = Field(default_factory=list)

    # Company size specific learnings
    size_specific: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # Average metrics we've seen
    avg_ai_readiness: float = 50.0
    avg_potential_savings: float = 0.0
    common_tech_stacks: List[str] = Field(default_factory=list)

    def update_confidence(self):
        """Update confidence based on analysis count."""
        if self.total_analyses >= 20:
            self.confidence = "high"
        elif self.total_analyses >= 5:
            self.confidence = "medium"
        else:
            self.confidence = "low"


class VendorExpertise(BaseModel):
    """
    Accumulated knowledge about vendors across all analyses.
    """
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    total_recommendations: int = 0

    # Vendor-specific learnings
    vendors: Dict[str, VendorFit] = Field(default_factory=dict)

    # Category insights (e.g., "CRM tools for small teams")
    category_insights: Dict[str, List[str]] = Field(default_factory=dict)


class PromptEffectiveness(BaseModel):
    """
    Track which prompts/approaches produce better results.
    """
    prompt_id: str
    phase: str
    effectiveness_score: float = 0.5  # 0-1
    usage_count: int = 0
    notes: List[str] = Field(default_factory=list)


class ExecutionExpertise(BaseModel):
    """
    Learnings about the execution process itself.
    """
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    total_executions: int = 0

    # Tool effectiveness
    tool_success_rates: Dict[str, float] = Field(default_factory=dict)

    # Phase insights
    phase_insights: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # Common failure patterns
    failure_patterns: List[str] = Field(default_factory=list)

    # Prompt effectiveness
    prompt_effectiveness: Dict[str, PromptEffectiveness] = Field(default_factory=dict)


class AnalysisRecord(BaseModel):
    """
    Record of a single analysis for learning purposes.
    Stored temporarily, then distilled into expertise.
    """
    audit_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    industry: str
    company_size: str

    # What was discovered
    pain_points_found: List[str] = Field(default_factory=list)
    processes_analyzed: List[str] = Field(default_factory=list)
    recommendations_made: List[Dict[str, Any]] = Field(default_factory=list)
    vendors_recommended: List[str] = Field(default_factory=list)

    # Outcomes
    ai_readiness_score: int = 50
    total_potential_savings: float = 0.0
    findings_count: int = 0

    # Execution metrics
    tools_used: Dict[str, int] = Field(default_factory=dict)  # tool_name: usage_count
    token_usage: Dict[str, int] = Field(default_factory=dict)
    phases_completed: List[str] = Field(default_factory=list)
    errors_encountered: List[str] = Field(default_factory=list)
