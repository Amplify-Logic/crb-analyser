# backend/src/models/industry_insights.py
"""
Industry Insights models for competitive/market context.
"""
from typing import List, Literal
from pydantic import BaseModel, Field


class InsightCRB(BaseModel):
    """Typical CRB for an industry capability."""
    typical_cost: str  # "€50-200/mo"
    risk_level: Literal["low", "medium", "high"] = "medium"
    typical_benefit: str  # "12 hrs/wk saved"


class AdoptionStat(BaseModel):
    """Adoption statistics for an AI capability."""
    capability: str  # "Content automation"
    adoption_percentage: int = Field(..., ge=0, le=100)
    average_outcome: str  # "12 hrs/week saved"
    crb: InsightCRB


class OpportunityMap(BaseModel):
    """Map of opportunities by maturity."""
    emerging: List[str] = Field(default_factory=list, description="Early wins, less proven")
    growing: List[str] = Field(default_factory=list, description="Sweet spot, high impact")
    established: List[str] = Field(default_factory=list, description="Table stakes")
    best_fit: Literal["emerging", "growing", "established"] = "growing"
    rationale: str = ""


class SocialProof(BaseModel):
    """Social proof from similar businesses."""
    quote: str
    company_description: str  # "8-person agency, similar size"
    outcome: str
    industry: str


class IndustryInsights(BaseModel):
    """Complete industry insights for a report."""
    industry: str
    industry_display_name: str
    adoption_stats: List[AdoptionStat]
    opportunity_map: OpportunityMap
    social_proof: List[SocialProof]
