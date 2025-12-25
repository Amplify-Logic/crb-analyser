"""
Competitor Analyzer Skill

Identifies what competitors are doing with AI.

This skill:
1. Loads industry AI adoption data
2. Identifies common AI implementations
3. Highlights industry leaders
4. Assesses risk of falling behind

Output Schema:
{
    "industry": "dental",
    "ai_adoption_rate": "35%",
    "adoption_trend": "increasing",
    "common_implementations": [
        {
            "area": "Scheduling",
            "adoption_rate": "45%",
            "typical_tools": ["Calendly", "Acuity"],
            "benefits_reported": ["50% less phone time"]
        }
    ],
    "industry_leaders": [
        {
            "description": "Large DSO chains",
            "ai_usage": "Full practice management automation",
            "competitive_advantage": "Lower operational costs"
        }
    ],
    "risk_assessment": {
        "risk_level": "medium",
        "reasoning": "Early majority adopting, window closing",
        "time_to_act": "6-12 months"
    },
    "opportunities": [
        "Early mover advantage in AI scheduling still available"
    ]
}
"""

import logging
from typing import Dict, Any, List, Optional

from src.skills.base import LLMSkill, SkillContext, SkillError
from src.knowledge import (
    load_industry_data,
    normalize_industry,
    get_industry_context,
)

logger = logging.getLogger(__name__)

# AI adoption data by industry (from verified research)
INDUSTRY_AI_ADOPTION = {
    "dental": {
        "adoption_rate": "35%",
        "adoption_trend": "increasing",
        "source": "GoTu AI in Dentistry 2025",
        "common_areas": ["scheduling", "imaging", "patient_communication"],
    },
    "home-services": {
        "adoption_rate": "70%",
        "adoption_trend": "accelerating",
        "source": "Zuper FSM Trends 2025",
        "common_areas": ["scheduling", "routing", "invoicing"],
    },
    "professional-services": {
        "adoption_rate": "71%",
        "adoption_trend": "mainstream",
        "source": "Industry reports 2025",
        "common_areas": ["document_automation", "research", "client_communication"],
    },
    "recruiting": {
        "adoption_rate": "67%",
        "adoption_trend": "mainstream",
        "source": "StaffingHub 2025",
        "common_areas": ["resume_screening", "candidate_matching", "scheduling"],
    },
    "coaching": {
        "adoption_rate": "40%",
        "adoption_trend": "increasing",
        "source": "ICF Global Coaching Study 2025",
        "common_areas": ["scheduling", "content_creation", "client_tracking"],
    },
    "veterinary": {
        "adoption_rate": "39%",
        "adoption_trend": "increasing",
        "source": "AAHA/Digitail Survey 2024",
        "common_areas": ["scheduling", "records", "client_communication"],
    },
}

# Common AI implementation areas
AI_IMPLEMENTATION_AREAS = {
    "scheduling": {
        "description": "Online booking and appointment management",
        "typical_tools": ["Calendly", "Acuity", "Square Appointments"],
        "benefits": ["50% reduction in phone time", "24/7 booking availability"],
        "implementation_effort": "low",
    },
    "document_automation": {
        "description": "Automated document generation and processing",
        "typical_tools": ["PandaDoc", "DocuSign", "Claude API"],
        "benefits": ["80% faster document creation", "Fewer errors"],
        "implementation_effort": "medium",
    },
    "client_communication": {
        "description": "Automated messaging, chatbots, follow-ups",
        "typical_tools": ["Intercom", "Drift", "Twilio"],
        "benefits": ["Instant responses", "Consistent communication"],
        "implementation_effort": "medium",
    },
    "routing": {
        "description": "Optimized scheduling and route planning",
        "typical_tools": ["OptimoRoute", "Route4Me", "ServiceTitan"],
        "benefits": ["20% more jobs per day", "Lower fuel costs"],
        "implementation_effort": "medium",
    },
    "invoicing": {
        "description": "Automated billing and payment collection",
        "typical_tools": ["QuickBooks", "FreshBooks", "Stripe"],
        "benefits": ["Faster payment collection", "Fewer billing errors"],
        "implementation_effort": "low",
    },
}


class CompetitorAnalyzerSkill(LLMSkill[Dict[str, Any]]):
    """
    Analyze competitor AI adoption in the industry.

    Creates urgency by showing what competitors are doing
    and the risk of falling behind.
    """

    name = "competitor-analyzer"
    description = "Analyze competitor AI adoption"
    version = "1.0.0"

    requires_llm = False  # LLM is optional, uses default data
    requires_knowledge = True

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Analyze competitor AI usage.

        Args:
            context: SkillContext with:
                - industry: Company's industry
                - quiz_answers: Company's current AI usage
                - metadata.findings: Gaps identified

        Returns:
            Competitor analysis with risk assessment
        """
        industry = normalize_industry(context.industry)
        quiz_answers = context.quiz_answers or {}
        findings = context.metadata.get("findings", [])

        # Get industry adoption data
        adoption_data = INDUSTRY_AI_ADOPTION.get(industry, {
            "adoption_rate": "30%",
            "adoption_trend": "increasing",
            "source": "Industry estimates",
            "common_areas": ["scheduling", "communication"],
        })

        # Get industry context
        industry_context = get_industry_context(industry)

        # Build common implementations
        common_implementations = self._get_common_implementations(
            areas=adoption_data.get("common_areas", []),
            industry=industry,
        )

        # Identify industry leaders
        leaders = await self._identify_leaders(
            industry=industry,
            industry_context=industry_context,
        )

        # Assess risk of falling behind
        risk_assessment = self._assess_risk(
            adoption_data=adoption_data,
            quiz_answers=quiz_answers,
            findings=findings,
        )

        # Identify opportunities
        opportunities = self._identify_opportunities(
            adoption_data=adoption_data,
            findings=findings,
            company_status=quiz_answers,
        )

        return {
            "industry": industry,
            "ai_adoption_rate": adoption_data["adoption_rate"],
            "adoption_trend": adoption_data["adoption_trend"],
            "source": adoption_data.get("source"),
            "common_implementations": common_implementations,
            "industry_leaders": leaders,
            "risk_assessment": risk_assessment,
            "opportunities": opportunities,
        }

    def _get_common_implementations(
        self,
        areas: List[str],
        industry: str,
    ) -> List[Dict[str, Any]]:
        """Get common AI implementations for the industry."""
        implementations = []

        for area in areas:
            if area in AI_IMPLEMENTATION_AREAS:
                impl = AI_IMPLEMENTATION_AREAS[area]
                implementations.append({
                    "area": area.replace("_", " ").title(),
                    "description": impl["description"],
                    "adoption_rate": self._estimate_area_adoption(area, industry),
                    "typical_tools": impl["typical_tools"],
                    "benefits_reported": impl["benefits"],
                    "implementation_effort": impl["implementation_effort"],
                })

        return implementations

    def _estimate_area_adoption(self, area: str, industry: str) -> str:
        """Estimate adoption rate for a specific area."""
        # Base rates by area
        base_rates = {
            "scheduling": 55,
            "invoicing": 60,
            "client_communication": 40,
            "document_automation": 35,
            "routing": 45,
        }

        base = base_rates.get(area, 30)

        # Adjust by industry adoption
        industry_data = INDUSTRY_AI_ADOPTION.get(industry, {})
        trend = industry_data.get("adoption_trend", "increasing")

        if trend == "accelerating":
            base = min(80, base + 15)
        elif trend == "mainstream":
            base = min(75, base + 10)

        return f"{base}%"

    async def _identify_leaders(
        self,
        industry: str,
        industry_context: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Identify AI leaders in the industry."""
        # Default leaders by industry type
        default_leaders = {
            "dental": [
                {
                    "description": "Large DSO chains (Heartland, Aspen)",
                    "ai_usage": "Centralized scheduling, AI imaging analysis, automated patient reminders",
                    "competitive_advantage": "Lower per-patient costs, consistent experience",
                },
                {
                    "description": "Tech-forward independent practices",
                    "ai_usage": "Online booking, automated recalls, digital intake",
                    "competitive_advantage": "Better patient experience, staff efficiency",
                },
            ],
            "home-services": [
                {
                    "description": "National franchise operations",
                    "ai_usage": "AI routing, automated scheduling, smart dispatching",
                    "competitive_advantage": "More jobs per day, predictable service windows",
                },
                {
                    "description": "Tech-enabled regional players",
                    "ai_usage": "Online booking, automated invoicing, customer portal",
                    "competitive_advantage": "Professional image, faster payments",
                },
            ],
            "professional-services": [
                {
                    "description": "Big 4 and large law firms",
                    "ai_usage": "Document automation, research AI, client portals",
                    "competitive_advantage": "Faster turnaround, lower junior staff costs",
                },
                {
                    "description": "Boutique firms with AI focus",
                    "ai_usage": "AI-assisted research, automated reporting",
                    "competitive_advantage": "Premium service at competitive rates",
                },
            ],
        }

        leaders = default_leaders.get(industry, [
            {
                "description": "Early AI adopters in the industry",
                "ai_usage": "Automated scheduling and client communication",
                "competitive_advantage": "Better customer experience, lower costs",
            },
        ])

        return leaders[:3]

    def _assess_risk(
        self,
        adoption_data: Dict[str, Any],
        quiz_answers: Dict[str, Any],
        findings: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Assess risk of falling behind on AI adoption."""
        adoption_rate = adoption_data.get("adoption_rate", "30%")
        trend = adoption_data.get("adoption_trend", "increasing")

        # Parse adoption rate
        try:
            rate_num = int(adoption_rate.replace("%", ""))
        except (ValueError, AttributeError):
            rate_num = 30

        # Determine company's current AI usage
        current_tools = quiz_answers.get("current_tools", [])
        ai_tools_count = 0
        if isinstance(current_tools, list):
            ai_keywords = ["ai", "automat", "bot", "smart", "intelligent"]
            for tool in current_tools:
                if any(kw in str(tool).lower() for kw in ai_keywords):
                    ai_tools_count += 1

        # Calculate risk
        if rate_num >= 60 and ai_tools_count < 2:
            risk_level = "high"
            reasoning = f"Majority ({adoption_rate}) of competitors already using AI"
            time_to_act = "Immediate - within 3 months"
        elif rate_num >= 40 or trend == "accelerating":
            risk_level = "medium"
            reasoning = f"Early majority adopting ({adoption_rate}), window closing"
            time_to_act = "6-12 months"
        else:
            risk_level = "low"
            reasoning = f"Still early adoption phase ({adoption_rate})"
            time_to_act = "12-18 months"

        # Adjust based on findings
        high_priority_findings = len([
            f for f in findings
            if f.get("customer_value_score", 0) >= 8 or f.get("business_health_score", 0) >= 8
        ])

        if high_priority_findings >= 3 and risk_level == "low":
            risk_level = "medium"
            reasoning += "; multiple high-impact gaps identified"

        return {
            "risk_level": risk_level,
            "reasoning": reasoning,
            "time_to_act": time_to_act,
            "industry_adoption": adoption_rate,
        }

    def _identify_opportunities(
        self,
        adoption_data: Dict[str, Any],
        findings: List[Dict[str, Any]],
        company_status: Dict[str, Any],
    ) -> List[str]:
        """Identify opportunities based on competitor analysis."""
        opportunities = []
        common_areas = adoption_data.get("common_areas", [])

        # Find gaps that align with common implementations
        for finding in findings[:5]:
            title = finding.get("title", "").lower()
            for area in common_areas:
                if area.replace("_", " ") in title or area in title:
                    opportunities.append(
                        f"Catch up on {area.replace('_', ' ')} automation - {adoption_data['adoption_rate']} of competitors already using"
                    )
                    break

        # Add trend-based opportunities
        trend = adoption_data.get("adoption_trend", "increasing")
        if trend == "accelerating":
            opportunities.append(
                "Market rapidly adopting AI - early implementation builds competitive moat"
            )
        elif trend == "mainstream":
            opportunities.append(
                "AI becoming table stakes - implementation needed to remain competitive"
            )
        else:
            opportunities.append(
                "Early mover advantage still available in AI adoption"
            )

        return list(set(opportunities))[:4]


# For skill discovery
__all__ = ["CompetitorAnalyzerSkill"]
