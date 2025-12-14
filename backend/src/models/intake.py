"""
Intake Models

Pydantic models for intake questionnaire responses.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from pydantic import BaseModel, Field


class IntakeResponseBase(BaseModel):
    """Base intake response fields."""
    responses: Dict[str, Any] = Field(default_factory=dict)
    current_section: int = Field(default=1, ge=1)
    is_complete: bool = False


class IntakeUpdate(BaseModel):
    """Update intake responses."""
    responses: Optional[Dict[str, Any]] = None
    current_section: Optional[int] = Field(default=None, ge=1)


class IntakeComplete(BaseModel):
    """Mark intake as complete."""
    responses: Dict[str, Any]


class IntakeResponse(IntakeResponseBase):
    """Full intake response with metadata."""
    id: str
    audit_id: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IntakeWithAudit(IntakeResponse):
    """Intake response with audit info."""
    audit_title: Optional[str] = None
    audit_status: Optional[str] = None
    client_name: Optional[str] = None
    client_industry: Optional[str] = None


class QuestionOption(BaseModel):
    """Question option for select/multi-select."""
    value: str
    label: str


class Question(BaseModel):
    """Individual question definition."""
    id: str
    question: str
    type: str
    required: bool = False
    placeholder: Optional[str] = None
    options: Optional[List[QuestionOption]] = None
    min: Optional[int] = None
    max: Optional[int] = None
    scale_min: Optional[int] = None
    scale_max: Optional[int] = None
    scale_labels: Optional[Dict[str, str]] = None


class QuestionnaireSection(BaseModel):
    """Questionnaire section."""
    id: int
    title: str
    description: str
    questions: List[Question]


class QuestionnaireResponse(BaseModel):
    """Full questionnaire structure."""
    sections: List[QuestionnaireSection]
    total_questions: int
    total_sections: int


class IntakeValidationError(BaseModel):
    """Validation error for intake."""
    question_id: str
    message: str


class IntakeValidationResult(BaseModel):
    """Result of intake validation."""
    is_valid: bool
    errors: List[IntakeValidationError] = Field(default_factory=list)
    missing_required: List[str] = Field(default_factory=list)
