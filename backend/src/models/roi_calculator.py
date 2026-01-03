# backend/src/models/roi_calculator.py
"""
ROI Calculator models for interactive what-if scenarios.

Includes the Jevons Effect: when efficiency increases, costs drop,
demand often increases, leading to MORE capacity utilization and revenue.
This reframes AI from "cost-cutting" to "growth enabler".

Reference: https://en.wikipedia.org/wiki/Jevons_paradox
Video insight: "The Boring AI Niches Making Millionaires in 2026" - Ben (2025)
"""
from datetime import datetime
from typing import Optional, List, Literal, Dict
from pydantic import BaseModel, Field


class ROIInputs(BaseModel):
    """User-adjustable inputs for ROI calculation."""
    hours_weekly: float = Field(10, ge=0, le=80)
    hourly_rate: float = Field(50, ge=0, le=500)
    automation_rate: float = Field(0.7, ge=0.1, le=0.95)
    implementation_approach: Literal["diy", "saas", "freelancer"] = "saas"


# =============================================================================
# JEVONS EFFECT / DEMAND EXPANSION MODELS
# =============================================================================
# The Jevons Effect: When AI increases efficiency → costs drop → demand increases
# → often MORE labor/capacity is needed, not less.
#
# Examples from real markets:
# - AI radiology: Better diagnosis → cheaper scans → more people get scans → MORE radiologists needed
# - AI receptionist: 24/7 booking → capture more leads → MORE revenue capacity
# - Containerization: Automated loading → cheaper shipping → MORE trade → MORE logistics jobs
#
# This is critical for our narrative: AI isn't just about cutting costs,
# it's about SCALING CAPACITY which can grow revenue.
# =============================================================================


class DemandExpansionScenario(BaseModel):
    """
    Model the Jevons Effect: efficiency gains → demand expansion → revenue growth.

    This captures the often-overlooked second-order effect of AI automation:
    when you can serve customers faster/cheaper, you can serve MORE customers.
    """
    # What efficiency gain triggers demand expansion
    efficiency_trigger: str = Field(
        ...,
        description="The efficiency gain that enables expansion. E.g., '50% faster service delivery'"
    )

    # Current capacity constraints
    current_capacity: Dict[str, float] = Field(
        default_factory=dict,
        description="Current capacity metrics. E.g., {'clients_per_month': 50, 'jobs_per_day': 8}"
    )

    # New capacity after AI
    new_capacity: Dict[str, float] = Field(
        default_factory=dict,
        description="Projected capacity after AI. E.g., {'clients_per_month': 75, 'jobs_per_day': 12}"
    )

    # Demand expansion assumptions
    demand_expansion_rate: float = Field(
        0.3, ge=0, le=1.0,
        description="Expected demand increase as percentage (0.3 = 30% more demand). Conservative default."
    )

    # Revenue impact
    revenue_per_unit: float = Field(
        ...,
        description="Average revenue per additional unit of capacity utilized"
    )

    # Calculated fields (populated by calculator)
    additional_units: Optional[float] = Field(
        None,
        description="Additional units that can be served"
    )
    additional_revenue_monthly: Optional[float] = Field(
        None,
        description="Additional monthly revenue from demand expansion"
    )
    additional_revenue_yearly: Optional[float] = Field(
        None,
        description="Additional yearly revenue from demand expansion"
    )


class JevonsEffectExample(BaseModel):
    """
    Pre-built Jevons Effect examples for common industries.
    Used to illustrate the concept with real-world parallels.
    """
    industry: str
    scenario: str
    efficiency_gain: str
    demand_expansion_result: str
    source: Optional[str] = None


# Pre-built examples for education/illustration
JEVONS_EFFECT_EXAMPLES: List[Dict] = [
    {
        "industry": "Healthcare - Radiology",
        "scenario": "AI-assisted diagnosis",
        "efficiency_gain": "AI reads scans faster and more accurately than humans alone",
        "demand_expansion_result": "Lower cost per scan → more people get preventive scans → MORE radiologists needed to review edge cases",
        "source": "Video: 'Boring AI Niches' (2025) - AI radiology example"
    },
    {
        "industry": "Home Services",
        "scenario": "AI receptionist for HVAC company",
        "efficiency_gain": "24/7 call handling, instant booking, no missed calls",
        "demand_expansion_result": "Capture 30% more leads → book more jobs → need MORE technicians to handle volume",
        "source": "Auto Ace, Smith.ai case studies"
    },
    {
        "industry": "Dental",
        "scenario": "AI scheduling and patient communication",
        "efficiency_gain": "Reduce admin time by 50%, fill more appointment slots",
        "demand_expansion_result": "Lower overhead per patient → can offer competitive pricing → MORE patients → need MORE hygienists",
        "source": "Barti AI Series A (2025)"
    },
    {
        "industry": "Recruiting",
        "scenario": "AI candidate screening",
        "efficiency_gain": "Screen 10x more candidates in same time",
        "demand_expansion_result": "Faster placements → handle more job orders → MORE revenue → may need MORE recruiters for final interviews",
        "source": "Industry pattern"
    },
    {
        "industry": "Logistics (Historical)",
        "scenario": "Containerization",
        "efficiency_gain": "Automated container loading replaced dock workers",
        "demand_expansion_result": "Cheaper shipping → explosion in global trade → MASSIVE increase in logistics and warehousing jobs",
        "source": "Historical economics - Jevons paradox"
    },
    {
        "industry": "Cloud Computing (Historical)",
        "scenario": "Cloud transition",
        "efficiency_gain": "Eliminated on-prem server management jobs",
        "demand_expansion_result": "Cheaper compute → explosion of web apps → MASSIVE increase in DevOps, cloud engineering jobs",
        "source": "Historical - AWS/cloud era"
    }
]


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

    # Benefit - Traditional (Cost Savings)
    monthly_savings: float
    yearly_savings: float

    # Benefit - Jevons Effect (Demand Expansion / Growth)
    # These capture the second-order effect: efficiency → more capacity → more revenue
    demand_expansion: Optional[DemandExpansionScenario] = Field(
        None,
        description="Optional demand expansion scenario (Jevons Effect)"
    )
    additional_revenue_monthly: float = Field(
        0,
        description="Additional monthly revenue from capacity expansion (Jevons Effect)"
    )
    additional_revenue_yearly: float = Field(
        0,
        description="Additional yearly revenue from capacity expansion (Jevons Effect)"
    )

    # Combined Benefit (Savings + Growth)
    total_monthly_benefit: Optional[float] = Field(
        None,
        description="Total monthly benefit = savings + demand expansion revenue"
    )
    total_yearly_benefit: Optional[float] = Field(
        None,
        description="Total yearly benefit = savings + demand expansion revenue"
    )

    # Analysis
    roi_percentage: float  # Traditional ROI (savings only)
    roi_percentage_with_growth: Optional[float] = Field(
        None,
        description="ROI including demand expansion (Jevons Effect)"
    )
    breakeven_months: float
    breakeven_months_with_growth: Optional[float] = Field(
        None,
        description="Breakeven including demand expansion revenue"
    )
    three_year_net: float
    three_year_net_with_growth: Optional[float] = Field(
        None,
        description="3-year net including demand expansion revenue"
    )

    # CRB Display
    crb_summary: CalculatorCRB

    def calculate_totals(self) -> None:
        """Calculate combined benefits including Jevons Effect."""
        self.total_monthly_benefit = self.monthly_savings + self.additional_revenue_monthly
        self.total_yearly_benefit = self.yearly_savings + self.additional_revenue_yearly

        if self.additional_revenue_yearly > 0:
            total_cost = self.implementation_cost + (self.monthly_cost * 12)
            if total_cost > 0:
                self.roi_percentage_with_growth = (
                    (self.total_yearly_benefit - total_cost) / total_cost
                ) * 100

            if self.total_monthly_benefit > self.monthly_cost:
                net_monthly = self.total_monthly_benefit - self.monthly_cost
                self.breakeven_months_with_growth = self.implementation_cost / net_monthly

            self.three_year_net_with_growth = (
                (self.total_yearly_benefit * 3) -
                self.implementation_cost -
                (self.monthly_cost * 36)
            )


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

    # Jevons Effect / Demand Expansion
    demand_expansion_enabled: bool = Field(
        False,
        description="Whether to include demand expansion in ROI calculations"
    )
    demand_expansion_scenario: Optional[DemandExpansionScenario] = Field(
        None,
        description="The demand expansion scenario for this report"
    )


# =============================================================================
# INDUSTRY-SPECIFIC DEMAND EXPANSION PATTERNS
# =============================================================================
# These are default demand expansion assumptions per industry,
# based on observed patterns and the Jevons Effect.
# =============================================================================

INDUSTRY_DEMAND_EXPANSION_DEFAULTS: Dict[str, Dict] = {
    "home-services": {
        "typical_expansion_rate": 0.25,  # 25% more capacity utilized
        "trigger": "AI receptionist captures after-hours calls, AI dispatch fits more jobs/day",
        "example": "HVAC company: 24/7 booking → 25% more jobs booked → need more technicians",
        "revenue_multiplier": 1.25
    },
    "dental": {
        "typical_expansion_rate": 0.20,  # 20% more patients
        "trigger": "AI scheduling fills gaps, reduces no-shows, handles patient communication",
        "example": "Dental practice: 50% less admin → lower overhead → competitive pricing → 20% more patients",
        "revenue_multiplier": 1.20
    },
    "veterinary": {
        "typical_expansion_rate": 0.20,
        "trigger": "AI handles appointment booking, reminders, follow-ups",
        "example": "Vet clinic: AI receptionist → capture emergency calls 24/7 → 20% more visits",
        "revenue_multiplier": 1.20
    },
    "professional-services": {
        "typical_expansion_rate": 0.30,  # 30% more billable capacity
        "trigger": "AI handles admin, document prep, client communication",
        "example": "Law firm: 40% less admin time → 30% more billable hours available",
        "revenue_multiplier": 1.30
    },
    "recruiting": {
        "typical_expansion_rate": 0.40,  # 40% more placements
        "trigger": "AI screens candidates, handles initial outreach, schedules interviews",
        "example": "Staffing agency: 10x faster screening → 40% more placements per recruiter",
        "revenue_multiplier": 1.40
    },
    "coaching": {
        "typical_expansion_rate": 0.25,
        "trigger": "AI handles scheduling, session prep, follow-ups, admin",
        "example": "Business coach: AI assistant → 25% more client capacity",
        "revenue_multiplier": 1.25
    }
}


# =============================================================================
# TIME SAVINGS BENCHMARKS
# =============================================================================
# From Superintelligent ROI Survey (2,500+ use cases, 1,000+ organizations)
# Source: Nathaniel Whittemore, AI Daily Brief / roicervey.ai
# =============================================================================

TIME_SAVINGS_BENCHMARKS: Dict[str, Dict] = {
    "conservative": {
        "hours_per_week": 5,
        "hours_per_year": 260,
        "work_weeks_saved": 6.5,
        "description": "Cluster point from 2,500+ use case study - most common time savings"
    },
    "moderate": {
        "hours_per_week": 10,
        "hours_per_year": 520,
        "work_weeks_saved": 13,
        "description": "Upper range of common time savings"
    },
    "aggressive": {
        "hours_per_week": 20,
        "hours_per_year": 1040,
        "work_weeks_saved": 26,
        "description": "High-impact automation scenarios"
    }
}


# =============================================================================
# ROI CATEGORIES FRAMEWORK
# =============================================================================
# From Superintelligent ROI Survey - 8 categories ordered by frequency
# Key insight: Risk Reduction is lowest frequency (3.4%) but highest
# transformational impact (25%)
# =============================================================================

class ROICategory:
    """ROI category with frequency and impact data from 2,500+ use case study."""

    TIME_SAVINGS = {
        "name": "Time Savings",
        "frequency": 0.35,  # 35% of use cases
        "description": "The default starting point for most organizations",
        "typical_hours_saved": 5,  # hours/week
        "transformational_rate": 0.10  # 10% see transformational impact
    }

    INCREASED_OUTPUT = {
        "name": "Increased Output",
        "frequency": 0.15,
        "description": "More deliverables with same resources",
        "note": "200-1000 person orgs focus heavily here",
        "transformational_rate": 0.12
    }

    QUALITY_IMPROVEMENT = {
        "name": "Quality Improvement",
        "frequency": 0.12,
        "description": "Better results, fewer errors, higher standards",
        "transformational_rate": 0.14
    }

    NEW_CAPABILITIES = {
        "name": "New Capabilities",
        "frequency": 0.10,
        "description": "Doing things that weren't possible before",
        "note": "C-suite leaders focus more here",
        "transformational_rate": 0.18
    }

    IMPROVED_DECISION_MAKING = {
        "name": "Improved Decision-Making",
        "frequency": 0.08,
        "description": "Better data analysis, faster insights, smarter choices",
        "transformational_rate": 0.15
    }

    COST_SAVINGS = {
        "name": "Cost Savings",
        "frequency": 0.07,
        "description": "Direct expense reduction beyond time savings",
        "transformational_rate": 0.12
    }

    INCREASED_REVENUE = {
        "name": "Increased Revenue",
        "frequency": 0.06,
        "description": "Growth impact, new sales, higher conversion",
        "transformational_rate": 0.20
    }

    RISK_REDUCTION = {
        "name": "Risk Reduction",
        "frequency": 0.034,  # Only 3.4% of use cases
        "description": "Compliance, error prevention, security",
        "transformational_rate": 0.25,  # BUT 25% have transformational impact!
        "key_insight": "MOST UNDERRATED - lowest frequency, highest transformational rate",
        "examples": [
            "Contract review and compliance checking",
            "Audit trail analysis",
            "Regulatory monitoring",
            "Quality control at scale",
            "Fraud detection patterns"
        ]
    }

    @classmethod
    def all_categories(cls) -> List[Dict]:
        """Return all categories ordered by frequency."""
        return [
            cls.TIME_SAVINGS,
            cls.INCREASED_OUTPUT,
            cls.QUALITY_IMPROVEMENT,
            cls.NEW_CAPABILITIES,
            cls.IMPROVED_DECISION_MAKING,
            cls.COST_SAVINGS,
            cls.INCREASED_REVENUE,
            cls.RISK_REDUCTION
        ]


# =============================================================================
# MARKET CONTEXT STATS
# =============================================================================
# For use in reports and recommendations
# =============================================================================

MARKET_CONTEXT = {
    "agent_adoption": {
        "source": "KPMG Q3 2024",
        "production_agents_q1": 0.11,  # 11%
        "production_agents_q3": 0.42,  # 42%
        "insight": "4x growth in production agent deployment in 2024"
    },
    "roi_reality": {
        "source": "Superintelligent ROI Survey (2,500+ use cases)",
        "seeing_modest_roi": 0.443,
        "seeing_high_roi": 0.376,
        "negative_roi": 0.05,
        "expect_growth": 0.67
    },
    "scale_challenges": {
        "source": "McKinsey State of AI 2024",
        "fully_at_scale": 0.07,  # Only 7%
        "still_experimenting": 0.62  # 62%
    }
}
