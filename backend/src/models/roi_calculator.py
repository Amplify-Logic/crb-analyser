# backend/src/models/roi_calculator.py
"""
ROI Calculator models for interactive what-if scenarios.
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class ROIInputs(BaseModel):
    """User-adjustable inputs for ROI calculation."""
    hours_weekly: float = Field(10, ge=0, le=80)
    hourly_rate: float = Field(50, ge=0, le=500)
    automation_rate: float = Field(0.7, ge=0.1, le=0.95)
    implementation_approach: Literal["diy", "saas", "freelancer"] = "saas"


class CalculatorCRB(BaseModel):
    """CRB display for calculator results."""
    cost_display: str  # "€150/mo + €2,400 build"
    risk_display: str  # "Low (proven pattern)"
    risk_bar: float = Field(..., ge=0, le=1)  # 0-1 for visual
    benefit_display: str  # "€3,150/mo saved"
    time_benefit: str  # "10.5 hrs/wk freed"


class ROIResults(BaseModel):
    """Calculated ROI results."""
    # Time
    hours_saved_weekly: float
    hours_saved_monthly: float
    hours_saved_yearly: float

    # Cost
    implementation_cost: float  # One-time
    monthly_cost: float  # Ongoing

    # Benefit
    monthly_savings: float
    yearly_savings: float

    # Analysis
    roi_percentage: float
    breakeven_months: float
    three_year_net: float

    # CRB Display
    crb_summary: CalculatorCRB


class SavedScenario(BaseModel):
    """A saved ROI scenario for comparison."""
    id: str
    name: str
    inputs: ROIInputs
    results: ROIResults
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ROICalculator(BaseModel):
    """Complete ROI calculator state for a report."""
    report_id: str
    default_inputs: ROIInputs
    scenarios: List[SavedScenario] = Field(default_factory=list)
