# backend/src/services/insights_generator.py
"""
Industry Insights Generator

Generates industry benchmarks and adoption statistics.
Enriches with curated insights from InsightService when available.
"""
import logging
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from src.services.insight_service import get_insight_service
from src.models.insight import InsightType, UseIn

logger = logging.getLogger(__name__)


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
    source: str = ""  # e.g. "McKinsey 2025 AI Adoption Report"


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


class CuratedInsightSummary(BaseModel):
    """Serialized summary of a curated insight for report inclusion."""
    id: str
    title: str
    content: str
    actionable_insight: Optional[str] = None
    source_title: str = ""
    source_author: Optional[str] = None


class CuratedInsights(BaseModel):
    """Curated insights grouped by type for report surfacing."""
    trends: List[CuratedInsightSummary] = Field(default_factory=list)
    case_studies: List[CuratedInsightSummary] = Field(default_factory=list)
    statistics: List[CuratedInsightSummary] = Field(default_factory=list)
    quotes: List[CuratedInsightSummary] = Field(default_factory=list)


class IndustryInsights(BaseModel):
    """Complete industry insights for a report."""
    industry: str
    industry_display_name: str
    adoption_stats: List[AdoptionStat]
    opportunity_map: OpportunityMap
    social_proof: List[SocialProof]
    curated_insights: CuratedInsights = Field(default_factory=CuratedInsights)


# =============================================================================
# INDUSTRY DATA
# =============================================================================

INDUSTRY_DATA = {
    "ecommerce": {
        "display_name": "E-commerce",
        "adoption_stats": [
            {
                "capability": "Product descriptions",
                "adoption": 52,
                "outcome": "10x faster catalog updates",
                "cost": "€30-100/mo",
                "risk": "low",
                "benefit": "10x faster updates",
                "source": "Shopify & HubSpot Marketing Reports 2025"
            },
            {
                "capability": "Customer service chatbot",
                "adoption": 45,
                "outcome": "24/7 support, 60% resolution",
                "cost": "€50-150/mo",
                "risk": "medium",
                "benefit": "24/7 availability",
                "source": "Gartner Customer Service Technology Survey 2025"
            },
            {
                "capability": "Personalized recommendations",
                "adoption": 38,
                "outcome": "15% increase in AOV",
                "cost": "€100-300/mo",
                "risk": "medium",
                "benefit": "+15% AOV",
                "source": "Klaviyo Email Marketing Benchmarks 2025"
            },
            {
                "capability": "Inventory forecasting",
                "adoption": 25,
                "outcome": "30% less stockouts",
                "cost": "€50-200/mo",
                "risk": "medium",
                "benefit": "30% fewer stockouts",
                "source": "McKinsey Supply Chain AI Report 2024"
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
    "professional-services": {
        "display_name": "Professional Services",
        "adoption_stats": [
            {
                "capability": "Proposal generation",
                "adoption": 45,
                "outcome": "70% faster proposals",
                "cost": "€30-80/mo",
                "risk": "low",
                "benefit": "70% faster proposals",
                "source": "McKinsey State of AI 2025"
            },
            {
                "capability": "Research synthesis",
                "adoption": 52,
                "outcome": "Days of research in hours",
                "cost": "€50-150/mo",
                "risk": "low",
                "benefit": "10x faster research",
                "source": "McKinsey State of AI 2025"
            },
            {
                "capability": "Meeting summaries",
                "adoption": 68,
                "outcome": "Perfect notes, no effort",
                "cost": "€10-30/mo",
                "risk": "low",
                "benefit": "100% capture",
                "source": "Gartner Workplace Technology Survey 2025"
            },
            {
                "capability": "Client reporting",
                "adoption": 35,
                "outcome": "Automated weekly reports",
                "cost": "€30-100/mo",
                "risk": "low",
                "benefit": "5 hrs/wk saved",
                "source": "McKinsey State of AI 2025"
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
    "dental": {
        "display_name": "Dental Practices",
        "adoption_stats": [
            {
                "capability": "Appointment scheduling",
                "adoption": 42,
                "outcome": "80% fewer no-shows",
                "cost": "€30-80/mo",
                "risk": "low",
                "benefit": "80% fewer no-shows",
                "source": "ADA Health Policy Institute 2025"
            },
            {
                "capability": "Patient communications",
                "adoption": 38,
                "outcome": "24/7 patient support",
                "cost": "€50-150/mo",
                "risk": "medium",
                "benefit": "24/7 availability",
                "source": "ADA Health Policy Institute 2025"
            },
            {
                "capability": "Documentation assistance",
                "adoption": 55,
                "outcome": "50% less admin time",
                "cost": "€100-300/mo",
                "risk": "medium",
                "benefit": "50% less admin",
                "source": "McKinsey Healthcare AI Adoption 2024"
            },
            {
                "capability": "Insurance verification",
                "adoption": 30,
                "outcome": "Faster reimbursements",
                "cost": "€50-200/mo",
                "risk": "low",
                "benefit": "20% faster payments",
                "source": "ADA Health Policy Institute 2025"
            },
        ],
        "opportunities": {
            "emerging": ["AI diagnostic assistance", "Treatment personalization", "Predictive patient health"],
            "growing": ["Documentation AI", "Patient engagement", "Insurance automation"],
            "established": ["Scheduling", "Reminders", "Basic patient chat"],
        },
        "social_proof": [
            {
                "quote": "AI scheduling reduced no-shows from 25% to 5%. Massive revenue impact.",
                "company": "Multi-location dental practice",
                "outcome": "80% fewer no-shows"
            },
            {
                "quote": "Insurance verification went from 30 minutes to 2 minutes per patient.",
                "company": "Group dental practice, 3 locations",
                "outcome": "93% faster verification"
            },
        ],
    },
    "b2b-platforms": {
        "display_name": "B2B Platforms",
        "adoption_stats": [
            {
                "capability": "System integration automation",
                "adoption": 45,
                "outcome": "Eliminate manual data sync",
                "cost": "€100-500/mo",
                "risk": "medium",
                "benefit": "15 hrs/wk saved",
                "source": "KeyBanc 2025 SaaS Survey"
            },
            {
                "capability": "Customer success AI",
                "adoption": 35,
                "outcome": "Predict churn before it happens",
                "cost": "€200-500/mo",
                "risk": "medium",
                "benefit": "25% churn reduction",
                "source": "McKinsey B2B Platform Economics 2024"
            },
            {
                "capability": "Partner onboarding automation",
                "adoption": 28,
                "outcome": "Self-serve partner setup",
                "cost": "€100-300/mo",
                "risk": "low",
                "benefit": "5x faster onboarding",
                "source": "McKinsey B2B Platform Economics 2024"
            },
            {
                "capability": "Field service optimization",
                "adoption": 32,
                "outcome": "Optimal technician routing",
                "cost": "€150-400/mo",
                "risk": "medium",
                "benefit": "30% more jobs/day",
                "source": "McKinsey B2B Platform Economics 2024"
            },
        ],
        "opportunities": {
            "emerging": ["Predictive maintenance", "AI-powered partner matching", "Autonomous IoT diagnostics"],
            "growing": ["Customer success AI", "Integration automation", "Field service optimization"],
            "established": ["CRM automation", "Billing automation", "Reporting dashboards"],
        },
        "social_proof": [
            {
                "quote": "Integrating our IoT data with CRM eliminated 20 hours of manual data entry per week.",
                "company": "Connected devices company, 60 employees",
                "outcome": "20 hrs/wk saved"
            },
            {
                "quote": "AI churn prediction caught 80% of at-risk accounts before they churned.",
                "company": "B2B SaaS platform",
                "outcome": "80% churn early detection"
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
        data = INDUSTRY_DATA.get(industry_key)
        if data is None:
            raise ValueError(
                f"Unsupported industry: '{industry}'. "
                f"Supported: {', '.join(INDUSTRY_DATA.keys())}"
            )

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
                source=stat.get("source", ""),
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

        # Load curated insights from InsightService
        curated = self._load_curated_insights(industry_key)

        return IndustryInsights(
            industry=industry_key,
            industry_display_name=data["display_name"],
            adoption_stats=adoption_stats,
            opportunity_map=opportunity_map,
            social_proof=social_proof,
            curated_insights=curated,
        )

    def _load_curated_insights(self, industry: str) -> CuratedInsights:
        """Load curated insights from InsightService, grouped by type."""
        try:
            service = get_insight_service()
            insights = service.get_insights_for_surface(
                use_in=UseIn.REPORT,
                industry=industry,
                limit=10,
            )
        except Exception as e:
            logger.warning("curated_insights_load_failed: %s", str(e))
            return CuratedInsights()

        # Group by type
        trends = []
        case_studies = []
        statistics = []
        quotes = []

        for insight in insights:
            summary = CuratedInsightSummary(
                id=insight.id,
                title=insight.title,
                content=insight.content,
                actionable_insight=insight.actionable_insight,
                source_title=insight.source.title if insight.source else "",
                source_author=insight.source.author if insight.source else None,
            )
            insight_type = insight.type
            if isinstance(insight_type, str):
                insight_type_val = insight_type
            else:
                insight_type_val = insight_type.value if hasattr(insight_type, "value") else str(insight_type)

            if insight_type_val == InsightType.TREND.value:
                trends.append(summary)
            elif insight_type_val == InsightType.CASE_STUDY.value:
                case_studies.append(summary)
            elif insight_type_val == InsightType.STATISTIC.value:
                statistics.append(summary)
            elif insight_type_val == InsightType.QUOTE.value:
                quotes.append(summary)

        return CuratedInsights(
            trends=trends,
            case_studies=case_studies,
            statistics=statistics,
            quotes=quotes,
        )
