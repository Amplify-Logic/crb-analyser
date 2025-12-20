# backend/src/services/insights_generator.py
"""
Industry Insights Generator

Generates industry benchmarks and adoption statistics.
"""
from typing import List, Literal

from pydantic import BaseModel, Field


# =============================================================================
# INLINE MODELS (Stubs - will be replaced when models/industry_insights.py is created)
# =============================================================================

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


# =============================================================================
# INDUSTRY DATA
# =============================================================================

INDUSTRY_DATA = {
    "marketing-agencies": {
        "display_name": "Marketing Agencies",
        "adoption_stats": [
            {
                "capability": "Content automation",
                "adoption": 62,
                "outcome": "12 hrs/week saved",
                "cost": "€50-200/mo",
                "risk": "low",
                "benefit": "12 hrs/wk saved"
            },
            {
                "capability": "AI-assisted reporting",
                "adoption": 41,
                "outcome": "Reports in minutes",
                "cost": "€30-100/mo",
                "risk": "low",
                "benefit": "5 hrs/wk saved"
            },
            {
                "capability": "Lead scoring",
                "adoption": 28,
                "outcome": "2x conversion on hot leads",
                "cost": "€50-150/mo",
                "risk": "medium",
                "benefit": "2x conversion"
            },
            {
                "capability": "Chatbots",
                "adoption": 35,
                "outcome": "24/7 response capability",
                "cost": "€20-80/mo",
                "risk": "low",
                "benefit": "Always-on support"
            },
        ],
        "opportunities": {
            "emerging": ["AI video generation", "Voice agents", "Predictive analytics"],
            "growing": ["Lead scoring", "Content personalization", "Chatbots"],
            "established": ["Content drafts", "Email automation", "Social scheduling"],
        },
        "social_proof": [
            {
                "quote": "We started with content automation - now saving 15 hours/week. Paid for itself in month one.",
                "company": "8-person agency, similar size",
                "outcome": "15 hrs/wk saved"
            },
            {
                "quote": "AI lead scoring doubled our close rate. Wish we'd done it sooner.",
                "company": "Digital marketing agency",
                "outcome": "2x close rate"
            },
        ],
    },
    "tech-companies": {
        "display_name": "Tech Companies",
        "adoption_stats": [
            {
                "capability": "Code assistance",
                "adoption": 78,
                "outcome": "30% faster development",
                "cost": "€20-50/mo",
                "risk": "low",
                "benefit": "30% faster dev"
            },
            {
                "capability": "Documentation automation",
                "adoption": 55,
                "outcome": "90% less manual docs",
                "cost": "€0-30/mo",
                "risk": "low",
                "benefit": "90% less docs time"
            },
            {
                "capability": "Customer support AI",
                "adoption": 62,
                "outcome": "70% ticket deflection",
                "cost": "€50-200/mo",
                "risk": "medium",
                "benefit": "70% deflection"
            },
            {
                "capability": "Data analysis",
                "adoption": 48,
                "outcome": "Insights in seconds",
                "cost": "€30-100/mo",
                "risk": "low",
                "benefit": "Real-time insights"
            },
        ],
        "opportunities": {
            "emerging": ["Autonomous agents", "AI code review", "Predictive debugging"],
            "growing": ["Customer support AI", "Data analysis", "Content generation"],
            "established": ["Code assistance", "Documentation", "Testing automation"],
        },
        "social_proof": [
            {
                "quote": "GitHub Copilot + Claude for reviews cut our PR cycle from 3 days to 4 hours.",
                "company": "15-person startup",
                "outcome": "18x faster PRs"
            },
            {
                "quote": "AI handles 70% of support tickets. Team focuses on complex issues now.",
                "company": "SaaS company, 20 employees",
                "outcome": "70% ticket deflection"
            },
        ],
    },
    "ecommerce": {
        "display_name": "E-commerce",
        "adoption_stats": [
            {
                "capability": "Product descriptions",
                "adoption": 52,
                "outcome": "10x faster catalog updates",
                "cost": "€30-100/mo",
                "risk": "low",
                "benefit": "10x faster updates"
            },
            {
                "capability": "Customer service chatbot",
                "adoption": 45,
                "outcome": "24/7 support, 60% resolution",
                "cost": "€50-150/mo",
                "risk": "medium",
                "benefit": "24/7 availability"
            },
            {
                "capability": "Personalized recommendations",
                "adoption": 38,
                "outcome": "15% increase in AOV",
                "cost": "€100-300/mo",
                "risk": "medium",
                "benefit": "+15% AOV"
            },
            {
                "capability": "Inventory forecasting",
                "adoption": 25,
                "outcome": "30% less stockouts",
                "cost": "€50-200/mo",
                "risk": "medium",
                "benefit": "30% fewer stockouts"
            },
        ],
        "opportunities": {
            "emerging": ["Visual search", "Dynamic pricing AI", "Automated photography"],
            "growing": ["Personalization", "Inventory AI", "Customer service bots"],
            "established": ["Product descriptions", "Email automation", "Review management"],
        },
        "social_proof": [
            {
                "quote": "AI-generated descriptions for 5,000 SKUs in a weekend. Used to take us 3 months.",
                "company": "Online retailer, €2M revenue",
                "outcome": "100x faster catalog"
            },
            {
                "quote": "Personalization AI increased our average order value by 22%.",
                "company": "Fashion e-commerce",
                "outcome": "+22% AOV"
            },
        ],
    },
    "consulting": {
        "display_name": "Consulting & Professional Services",
        "adoption_stats": [
            {
                "capability": "Proposal generation",
                "adoption": 45,
                "outcome": "70% faster proposals",
                "cost": "€30-80/mo",
                "risk": "low",
                "benefit": "70% faster proposals"
            },
            {
                "capability": "Research synthesis",
                "adoption": 52,
                "outcome": "Days of research in hours",
                "cost": "€50-150/mo",
                "risk": "low",
                "benefit": "10x faster research"
            },
            {
                "capability": "Meeting summaries",
                "adoption": 68,
                "outcome": "Perfect notes, no effort",
                "cost": "€10-30/mo",
                "risk": "low",
                "benefit": "100% capture"
            },
            {
                "capability": "Client reporting",
                "adoption": 35,
                "outcome": "Automated weekly reports",
                "cost": "€30-100/mo",
                "risk": "low",
                "benefit": "5 hrs/wk saved"
            },
        ],
        "opportunities": {
            "emerging": ["AI strategy advisors", "Predictive client insights", "Autonomous research"],
            "growing": ["Proposal automation", "Research synthesis", "Client portals"],
            "established": ["Meeting transcription", "Document drafting", "Email automation"],
        },
        "social_proof": [
            {
                "quote": "Proposals that took 2 days now take 3 hours. Quality is actually better.",
                "company": "Management consultancy, 12 partners",
                "outcome": "6x faster proposals"
            },
            {
                "quote": "AI research synthesis is like having a junior analyst who never sleeps.",
                "company": "Strategy consulting firm",
                "outcome": "40 hrs/wk capacity freed"
            },
        ],
    },
    "healthcare": {
        "display_name": "Healthcare & Medical",
        "adoption_stats": [
            {
                "capability": "Appointment scheduling",
                "adoption": 42,
                "outcome": "80% fewer no-shows",
                "cost": "€30-80/mo",
                "risk": "low",
                "benefit": "80% fewer no-shows"
            },
            {
                "capability": "Patient communications",
                "adoption": 38,
                "outcome": "24/7 patient support",
                "cost": "€50-150/mo",
                "risk": "medium",
                "benefit": "24/7 availability"
            },
            {
                "capability": "Documentation assistance",
                "adoption": 55,
                "outcome": "50% less admin time",
                "cost": "€100-300/mo",
                "risk": "medium",
                "benefit": "50% less admin"
            },
            {
                "capability": "Billing automation",
                "adoption": 30,
                "outcome": "Faster reimbursements",
                "cost": "€50-200/mo",
                "risk": "low",
                "benefit": "20% faster payments"
            },
        ],
        "opportunities": {
            "emerging": ["Diagnostic assistance", "Treatment personalization", "Predictive health"],
            "growing": ["Documentation AI", "Patient engagement", "Billing automation"],
            "established": ["Scheduling", "Reminders", "Basic patient chat"],
        },
        "social_proof": [
            {
                "quote": "AI scheduling reduced no-shows from 25% to 5%. Massive revenue impact.",
                "company": "Multi-location dental practice",
                "outcome": "80% fewer no-shows"
            },
            {
                "quote": "Doctors spend 30% less time on documentation now. Patient time increased.",
                "company": "Primary care clinic",
                "outcome": "30% more patient time"
            },
        ],
    },
    "real-estate": {
        "display_name": "Real Estate",
        "adoption_stats": [
            {
                "capability": "Property descriptions",
                "adoption": 55,
                "outcome": "Listings in minutes",
                "cost": "€20-50/mo",
                "risk": "low",
                "benefit": "90% faster listings"
            },
            {
                "capability": "Lead qualification",
                "adoption": 40,
                "outcome": "Focus on serious buyers",
                "cost": "€30-100/mo",
                "risk": "low",
                "benefit": "2x close rate"
            },
            {
                "capability": "Market analysis",
                "adoption": 35,
                "outcome": "Instant comps and insights",
                "cost": "€50-150/mo",
                "risk": "low",
                "benefit": "10x faster analysis"
            },
            {
                "capability": "Client follow-up",
                "adoption": 48,
                "outcome": "Never miss a touchpoint",
                "cost": "€20-60/mo",
                "risk": "low",
                "benefit": "100% follow-up rate"
            },
        ],
        "opportunities": {
            "emerging": ["Virtual staging", "Predictive pricing", "AI property matching"],
            "growing": ["Lead scoring", "Market analysis", "Automated follow-up"],
            "established": ["Listing descriptions", "Email drips", "Scheduling"],
        },
        "social_proof": [
            {
                "quote": "AI qualifies leads before I call. My close rate doubled.",
                "company": "Independent agent, €3M GCI",
                "outcome": "2x close rate"
            },
            {
                "quote": "Listings that took an hour now take 5 minutes. Quality improved too.",
                "company": "Real estate team, 8 agents",
                "outcome": "12x faster listings"
            },
        ],
    },
    "general": {
        "display_name": "General Business",
        "adoption_stats": [
            {
                "capability": "Email automation",
                "adoption": 55,
                "outcome": "5 hrs/week saved",
                "cost": "€20-50/mo",
                "risk": "low",
                "benefit": "5 hrs/wk saved"
            },
            {
                "capability": "Document processing",
                "adoption": 35,
                "outcome": "80% faster processing",
                "cost": "€30-100/mo",
                "risk": "low",
                "benefit": "80% faster docs"
            },
            {
                "capability": "Meeting transcription",
                "adoption": 42,
                "outcome": "No more note-taking",
                "cost": "€10-30/mo",
                "risk": "low",
                "benefit": "100% capture"
            },
            {
                "capability": "Customer support",
                "adoption": 30,
                "outcome": "24/7 availability",
                "cost": "€50-150/mo",
                "risk": "medium",
                "benefit": "24/7 support"
            },
        ],
        "opportunities": {
            "emerging": ["Voice interfaces", "Autonomous agents", "Predictive analytics"],
            "growing": ["Customer support AI", "Content generation", "Data analysis"],
            "established": ["Email automation", "Transcription", "Document processing"],
        },
        "social_proof": [
            {
                "quote": "Started with email automation, now AI handles half our admin work.",
                "company": "Small business, 5 employees",
                "outcome": "50% less admin"
            },
        ],
    },
}


# =============================================================================
# INSIGHTS GENERATOR
# =============================================================================

class InsightsGenerator:
    """Generate industry insights and benchmarks."""

    def generate_insights(
        self,
        industry: str,
        ai_readiness_score: int,
    ) -> IndustryInsights:
        """Generate industry insights for a report."""

        # Normalize industry
        industry_key = industry.lower().replace(" ", "-").replace("_", "-")
        data = INDUSTRY_DATA.get(industry_key, INDUSTRY_DATA["general"])

        # Build adoption stats
        adoption_stats = []
        for stat in data["adoption_stats"]:
            adoption_stats.append(AdoptionStat(
                capability=stat["capability"],
                adoption_percentage=stat["adoption"],
                average_outcome=stat["outcome"],
                crb=InsightCRB(
                    typical_cost=stat["cost"],
                    risk_level=stat["risk"],
                    typical_benefit=stat["benefit"],
                ),
            ))

        # Build opportunity map
        opps = data["opportunities"]
        # Determine best fit based on readiness
        if ai_readiness_score >= 70:
            best_fit = "emerging"
            rationale = "High readiness - explore cutting-edge opportunities"
        elif ai_readiness_score >= 50:
            best_fit = "growing"
            rationale = "Solid foundation - focus on proven, high-impact areas"
        else:
            best_fit = "established"
            rationale = "Start with proven patterns to build momentum"

        opportunity_map = OpportunityMap(
            emerging=opps.get("emerging", []),
            growing=opps.get("growing", []),
            established=opps.get("established", []),
            best_fit=best_fit,
            rationale=rationale,
        )

        # Build social proof
        social_proof = []
        for proof in data.get("social_proof", []):
            social_proof.append(SocialProof(
                quote=proof["quote"],
                company_description=proof["company"],
                outcome=proof["outcome"],
                industry=industry_key,
            ))

        return IndustryInsights(
            industry=industry_key,
            industry_display_name=data["display_name"],
            adoption_stats=adoption_stats,
            opportunity_map=opportunity_map,
            social_proof=social_proof,
        )
