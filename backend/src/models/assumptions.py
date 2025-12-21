"""
Assumption Tracking Models

Per the Non-Assumption Principles in the CRB Framework:
- All assumptions must be EXPLICIT to the inputter
- Assumptions must be recorded in backlog/appendix of report
- Gather further input where assumptions cannot be removed
"""

from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class AssumptionStatus(str, Enum):
    """Status of an assumption in the analysis."""
    PENDING_VALIDATION = "pending_validation"  # Needs inputter confirmation
    VALIDATED = "validated"  # Confirmed by inputter
    REJECTED = "rejected"  # Inputter said this is wrong
    ASSUMED = "assumed"  # Used without validation (must be disclosed)
    REMOVED = "removed"  # No longer needed (got actual data)


class AssumptionCategory(str, Enum):
    """Category of assumption being made."""
    FINANCIAL = "financial"  # Cost, pricing, budget assumptions
    OPERATIONAL = "operational"  # Process, capacity, efficiency
    TECHNICAL = "technical"  # Tech stack, integration, capabilities
    HUMAN = "human"  # Team size, skills, availability
    MARKET = "market"  # Competition, industry, trends
    TIMELINE = "timeline"  # Implementation, adoption timing
    BEHAVIORAL = "behavioral"  # User adoption, change management


class AssumptionSource(str, Enum):
    """Where the assumption comes from."""
    INPUTTER_DATA = "inputter_data"  # Derived from quiz/interview responses
    INDUSTRY_BENCHMARK = "industry_benchmark"  # From our knowledge base
    PEER_REVIEWED = "peer_reviewed"  # Scientific/academic source
    VENDOR_DATA = "vendor_data"  # From vendor databases
    ANALYST_INFERENCE = "analyst_inference"  # Logical inference by AI
    DEFAULT_VALUE = "default_value"  # Standard default when no data


class Assumption(BaseModel):
    """
    A single assumption made during CRB analysis.

    Every assumption must be:
    1. Explicitly stated
    2. Categorized
    3. Sourced
    4. Tracked for validation
    """
    id: str = Field(..., description="Unique identifier for this assumption")
    category: AssumptionCategory
    status: AssumptionStatus = AssumptionStatus.PENDING_VALIDATION

    # What we're assuming
    statement: str = Field(
        ...,
        description="Clear statement of what is being assumed",
        examples=["Hourly labor cost is €50/hour"]
    )

    # Why we need this assumption
    reason: str = Field(
        ...,
        description="Why this assumption is necessary for the analysis",
        examples=["Required to calculate time savings value"]
    )

    # What it affects
    impacts: List[str] = Field(
        default_factory=list,
        description="Which findings/recommendations depend on this assumption",
        examples=["finding-001", "rec-003"]
    )

    # Source and confidence
    source: AssumptionSource
    source_detail: Optional[str] = Field(
        None,
        description="Specific source citation or reference",
        examples=["Quiz answer: 'We have about 5 employees'"]
    )
    confidence: str = Field(
        "medium",
        description="How confident we are: high/medium/low"
    )

    # Validation
    validation_question: Optional[str] = Field(
        None,
        description="Question to ask inputter to validate this assumption",
        examples=["Is €50/hour a reasonable estimate for your team's hourly cost?"]
    )
    validated_at: Optional[datetime] = None
    validated_value: Optional[str] = Field(
        None,
        description="The actual value if different from assumption"
    )

    # Risk if wrong
    sensitivity: str = Field(
        "medium",
        description="How much would results change if assumption is wrong: high/medium/low"
    )
    if_wrong: Optional[str] = Field(
        None,
        description="What happens to analysis if this assumption is incorrect",
        examples=["ROI calculations could be off by 20-30%"]
    )


class AssumptionLog(BaseModel):
    """
    Complete log of assumptions for a report.

    This is included in the report appendix for transparency.
    """
    report_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # All assumptions
    assumptions: List[Assumption] = Field(default_factory=list)

    # Summary counts
    @property
    def total_assumptions(self) -> int:
        return len(self.assumptions)

    @property
    def pending_validation(self) -> int:
        return len([a for a in self.assumptions if a.status == AssumptionStatus.PENDING_VALIDATION])

    @property
    def validated(self) -> int:
        return len([a for a in self.assumptions if a.status == AssumptionStatus.VALIDATED])

    @property
    def high_sensitivity(self) -> int:
        return len([a for a in self.assumptions if a.sensitivity == "high"])

    def get_assumptions_for_finding(self, finding_id: str) -> List[Assumption]:
        """Get all assumptions that impact a specific finding."""
        return [a for a in self.assumptions if finding_id in a.impacts]

    def get_unvalidated_high_sensitivity(self) -> List[Assumption]:
        """Get assumptions that are both unvalidated AND high sensitivity."""
        return [
            a for a in self.assumptions
            if a.status == AssumptionStatus.PENDING_VALIDATION
            and a.sensitivity == "high"
        ]

    def to_report_appendix(self) -> dict:
        """Format assumptions for report appendix."""
        return {
            "summary": {
                "total": self.total_assumptions,
                "validated": self.validated,
                "pending_validation": self.pending_validation,
                "high_sensitivity_unvalidated": len(self.get_unvalidated_high_sensitivity())
            },
            "by_category": self._group_by_category(),
            "high_sensitivity": [a.model_dump() for a in self.assumptions if a.sensitivity == "high"],
            "all_assumptions": [a.model_dump() for a in self.assumptions]
        }

    def _group_by_category(self) -> dict:
        """Group assumptions by category."""
        grouped = {}
        for a in self.assumptions:
            cat = a.category.value
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append({
                "statement": a.statement,
                "status": a.status.value,
                "confidence": a.confidence
            })
        return grouped


# =============================================================================
# Standard Assumptions (Common defaults)
# =============================================================================

STANDARD_ASSUMPTIONS = {
    "hourly_rate": Assumption(
        id="std-hourly-rate",
        category=AssumptionCategory.FINANCIAL,
        statement="Hourly labor cost is €50/hour",
        reason="Industry standard for SMB professional work",
        source=AssumptionSource.INDUSTRY_BENCHMARK,
        source_detail="European SMB labor cost benchmarks 2024",
        confidence="medium",
        sensitivity="high",
        validation_question="What is the approximate hourly cost of your team's time (including overhead)?",
        if_wrong="ROI calculations could vary by 20-40%"
    ),
    "work_weeks": Assumption(
        id="std-work-weeks",
        category=AssumptionCategory.TIMELINE,
        statement="52 working weeks per year",
        reason="Standard annual calculation",
        source=AssumptionSource.DEFAULT_VALUE,
        confidence="high",
        sensitivity="low"
    ),
    "adoption_rate": Assumption(
        id="std-adoption",
        category=AssumptionCategory.BEHAVIORAL,
        statement="70% adoption rate for new tools within 6 months",
        reason="Typical enterprise software adoption curve",
        source=AssumptionSource.INDUSTRY_BENCHMARK,
        source_detail="Gartner enterprise adoption studies",
        confidence="medium",
        sensitivity="high",
        validation_question="How quickly does your team typically adopt new tools?",
        if_wrong="Benefit realization timeline could shift significantly"
    ),
    "implementation_buffer": Assumption(
        id="std-impl-buffer",
        category=AssumptionCategory.TIMELINE,
        statement="Add 50% buffer to vendor-quoted implementation times",
        reason="Vendor estimates historically optimistic",
        source=AssumptionSource.INDUSTRY_BENCHMARK,
        source_detail="Software implementation delay meta-analysis",
        confidence="high",
        sensitivity="medium"
    )
}


def create_assumption(
    category: AssumptionCategory,
    statement: str,
    reason: str,
    source: AssumptionSource,
    source_detail: Optional[str] = None,
    impacts: Optional[List[str]] = None,
    sensitivity: str = "medium"
) -> Assumption:
    """Helper to create a new assumption with proper ID."""
    import uuid
    return Assumption(
        id=f"assum-{uuid.uuid4().hex[:8]}",
        category=category,
        statement=statement,
        reason=reason,
        source=source,
        source_detail=source_detail,
        impacts=impacts or [],
        sensitivity=sensitivity
    )
