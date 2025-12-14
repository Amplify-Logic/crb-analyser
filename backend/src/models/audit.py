"""
Audit Models
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AuditBase(BaseModel):
    """Base audit fields."""
    title: str = Field(..., min_length=1, max_length=200)
    tier: str = Field(default="professional", pattern="^(free|professional)$")


class AuditCreate(AuditBase):
    """Request model for creating an audit."""
    client_id: str


class AuditUpdate(BaseModel):
    """Request model for updating an audit."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[str] = Field(
        None,
        pattern="^(intake|processing|completed|failed)$"
    )


class AuditResponse(BaseModel):
    """Response model for an audit."""
    id: str
    client_id: str
    workspace_id: str
    title: str
    tier: str
    status: str

    # Progress
    current_phase: str
    progress_percent: int
    phase_details: Optional[Dict[str, Any]] = None

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Payment
    payment_status: str
    price_paid: Optional[Decimal] = None
    currency: str

    # Results
    ai_readiness_score: Optional[int] = None
    total_findings: int
    total_potential_savings: Optional[Decimal] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AuditListResponse(BaseModel):
    """Response model for audit list."""
    data: List[AuditResponse]
    total: int


class AuditWithClient(AuditResponse):
    """Audit response including client details."""
    client_name: Optional[str] = None
    client_industry: Optional[str] = None


class AuditProgress(BaseModel):
    """Model for audit progress updates (SSE)."""
    audit_id: str
    phase: str
    progress_percent: int
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime


# Audit statuses
AUDIT_STATUSES = [
    {"value": "intake", "label": "Intake", "description": "Collecting information"},
    {"value": "processing", "label": "Processing", "description": "AI analysis in progress"},
    {"value": "completed", "label": "Completed", "description": "Report ready"},
    {"value": "failed", "label": "Failed", "description": "Analysis failed"}
]

# Audit tiers
AUDIT_TIERS = [
    {"value": "free", "label": "Free", "price": 0, "findings_limit": 3},
    {"value": "professional", "label": "Professional", "price": 697, "findings_limit": 20}
]

# Analysis phases
ANALYSIS_PHASES = [
    {"value": "intake", "label": "Intake", "order": 1},
    {"value": "discovery", "label": "Discovery", "order": 2},
    {"value": "research", "label": "Research", "order": 3},
    {"value": "analysis", "label": "Analysis", "order": 4},
    {"value": "modeling", "label": "Modeling", "order": 5},
    {"value": "report", "label": "Report Generation", "order": 6}
]
