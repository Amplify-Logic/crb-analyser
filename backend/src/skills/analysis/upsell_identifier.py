"""
Upsell Identifier Skill

Identifies opportunities to upsell customers to higher tiers.

This skill:
1. Analyzes report complexity and customer signals
2. Identifies when human consulting would add value
3. Generates personalized upsell recommendations
4. Provides pitch points and timing suggestions

Output Schema:
{
    "upsell_recommended": true,
    "recommendation": {
        "target_tier": "human",
        "confidence": "high",
        "reason": "Complex integrations need hands-on help",
        "timing": "immediate"
    },
    "pitch_points": [
        {
            "point": "Your custom integration needs expert guidance",
            "evidence": "3 recommendations require API development"
        }
    ],
    "signals": {
        "complexity_score": 8,
        "custom_dev_needed": true,
        "high_value_opportunity": true,
        "stuck_indicators": false
    },
    "suggested_approach": "Offer a free 15-minute consultation to discuss custom implementations"
}
"""

import logging
from typing import Dict, Any, List, Optional

from src.skills.base import LLMSkill, SkillContext, SkillError

logger = logging.getLogger(__name__)

# Upsell trigger thresholds
UPSELL_THRESHOLDS = {
    "complexity_score": 6,  # Out of 10
    "custom_recommendations": 2,  # Number of custom solutions
    "high_value_findings": 3,  # High-scoring findings
    "total_roi_potential": 50000,  # Annual EUR
}

# Tier definitions
TIER_FEATURES = {
    "ai": {
        "name": "AI Report",
        "price": "€147",
        "includes": ["AI-generated report", "Quick wins", "Vendor recommendations"],
    },
    "human": {
        "name": "Human + AI",
        "price": "€497",
        "includes": ["Everything in AI", "1-hour consultation call", "Implementation guidance", "30-day email support"],
    },
}

# Upsell pitch templates by reason
PITCH_TEMPLATES = {
    "custom_dev": {
        "headline": "Your recommendations need expert implementation",
        "pitch": "Your report identified {count} custom solutions that could transform your business. Our experts can guide you through the technical implementation.",
    },
    "high_complexity": {
        "headline": "Complex implementation needs hands-on support",
        "pitch": "With {findings} interconnected findings, you'll benefit from expert prioritization and a tailored implementation roadmap.",
    },
    "high_value": {
        "headline": "Maximize your €{roi:,} ROI potential",
        "pitch": "Your report shows significant ROI potential. A consultation call ensures you capture the full value without costly mistakes.",
    },
    "stuck": {
        "headline": "Get unstuck with expert guidance",
        "pitch": "Implementing AI can be overwhelming. Our experts have helped hundreds of {industry} businesses navigate these exact challenges.",
    },
}


class UpsellIdentifierSkill(LLMSkill[Dict[str, Any]]):
    """
    Identify upsell opportunities to human consulting tier.

    Analyzes report complexity and customer signals to
    determine when upgrading to human support makes sense.
    """

    name = "upsell-identifier"
    description = "Identify opportunities for human consulting tier"
    version = "1.0.0"

    requires_llm = False  # LLM is optional, uses default approach fallback
    requires_expertise = False

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Identify upsell opportunities.

        Args:
            context: SkillContext with:
                - metadata.report: The generated report
                - metadata.current_tier: Customer's current tier
                - metadata.engagement_signals: Customer behavior data
                - metadata.company_context: Company info

        Returns:
            Upsell recommendation with pitch points
        """
        report = context.metadata.get("report", {})
        current_tier = context.metadata.get("current_tier", "ai")
        engagement = context.metadata.get("engagement_signals", {})
        company = context.metadata.get("company_context", {})

        # Already on highest tier
        if current_tier == "human":
            return {
                "upsell_recommended": False,
                "recommendation": None,
                "reason": "Customer already on human tier",
                "signals": {},
                "pitch_points": [],
                "suggested_approach": None,
            }

        # Analyze signals
        signals = self._analyze_signals(report, engagement, company)

        # Determine if upsell is recommended
        upsell_recommended, confidence, primary_reason = self._evaluate_upsell(signals)

        if not upsell_recommended:
            return {
                "upsell_recommended": False,
                "recommendation": None,
                "reason": "No strong upsell indicators",
                "signals": signals,
                "pitch_points": [],
                "suggested_approach": None,
            }

        # Generate pitch points
        pitch_points = self._generate_pitch_points(
            signals=signals,
            report=report,
            industry=context.industry,
        )

        # Determine timing
        timing = self._determine_timing(signals, engagement)

        # Generate approach
        approach = await self._generate_approach(
            signals=signals,
            pitch_points=pitch_points,
            industry=context.industry,
            company_name=company.get("name", "the customer"),
        )

        return {
            "upsell_recommended": True,
            "recommendation": {
                "target_tier": "human",
                "confidence": confidence,
                "reason": primary_reason,
                "timing": timing,
                "price_difference": "€350",
            },
            "pitch_points": pitch_points,
            "signals": signals,
            "suggested_approach": approach,
        }

    def _analyze_signals(
        self,
        report: Dict[str, Any],
        engagement: Dict[str, Any],
        company: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze all signals for upsell potential."""
        findings = report.get("findings", [])
        recommendations = report.get("recommendations", [])

        # Count custom solutions
        custom_count = sum(
            1 for r in recommendations
            if r.get("our_recommendation") == "custom_solution"
        )

        # Count high-value findings
        high_value_count = sum(
            1 for f in findings
            if f.get("customer_value_score", 0) >= 8 or f.get("business_health_score", 0) >= 8
        )

        # Calculate total ROI potential
        total_roi = 0
        for rec in recommendations:
            roi_detail = rec.get("roi_detail", {})
            annual = roi_detail.get("financial_impact", {}).get("annual_savings", 0)
            total_roi += annual

        # Calculate complexity score (0-10)
        complexity = 0
        complexity += min(3, len(findings) // 2)  # Up to 3 for many findings
        complexity += min(3, custom_count)  # Up to 3 for custom solutions
        complexity += 2 if report.get("verdict", {}).get("decision") in ["caution", "wait"] else 0
        complexity += 2 if len(recommendations) > 4 else 0
        complexity = min(10, complexity)

        # Check for stuck indicators
        stuck = (
            engagement.get("days_since_report", 0) > 14 and
            not engagement.get("quick_win_clicked") and
            engagement.get("report_views", 0) > 3
        )

        # Company size indicator
        company_size = company.get("employee_count", 0)
        mid_market = 10 <= company_size <= 200

        return {
            "complexity_score": complexity,
            "custom_dev_needed": custom_count >= 2,
            "custom_recommendations": custom_count,
            "high_value_findings": high_value_count,
            "high_value_opportunity": total_roi >= UPSELL_THRESHOLDS["total_roi_potential"],
            "total_roi_potential": total_roi,
            "stuck_indicators": stuck,
            "mid_market_company": mid_market,
            "findings_count": len(findings),
            "recommendations_count": len(recommendations),
        }

    def _evaluate_upsell(
        self,
        signals: Dict[str, Any],
    ) -> tuple[bool, str, str]:
        """Evaluate if upsell should be recommended."""
        score = 0
        reasons = []

        # Custom dev needed is strong signal
        if signals["custom_dev_needed"]:
            score += 3
            reasons.append("custom_dev")

        # High complexity
        if signals["complexity_score"] >= UPSELL_THRESHOLDS["complexity_score"]:
            score += 2
            reasons.append("high_complexity")

        # High value opportunity
        if signals["high_value_opportunity"]:
            score += 2
            reasons.append("high_value")

        # Stuck indicators
        if signals["stuck_indicators"]:
            score += 2
            reasons.append("stuck")

        # Mid-market companies can afford it
        if signals["mid_market_company"]:
            score += 1

        # Determine confidence
        if score >= 5:
            confidence = "high"
        elif score >= 3:
            confidence = "medium"
        else:
            confidence = "low"

        # Primary reason
        primary_reason = reasons[0] if reasons else "general_value"
        reason_text = {
            "custom_dev": "Complex integrations need hands-on guidance",
            "high_complexity": "Report complexity benefits from expert walkthrough",
            "high_value": "High ROI potential justifies expert support",
            "stuck": "Customer may be overwhelmed and needs help",
            "general_value": "Expert guidance would accelerate implementation",
        }

        recommended = score >= 3
        return recommended, confidence, reason_text.get(primary_reason, reason_text["general_value"])

    def _generate_pitch_points(
        self,
        signals: Dict[str, Any],
        report: Dict[str, Any],
        industry: str,
    ) -> List[Dict[str, str]]:
        """Generate pitch points based on signals."""
        points = []

        if signals["custom_dev_needed"]:
            points.append({
                "point": f"Your report includes {signals['custom_recommendations']} custom solutions that require technical expertise",
                "evidence": "Custom implementations have 3x higher success rate with expert guidance",
                "template": "custom_dev",
            })

        if signals["complexity_score"] >= 6:
            points.append({
                "point": f"With {signals['findings_count']} findings and {signals['recommendations_count']} recommendations, prioritization is key",
                "evidence": "Expert prioritization prevents wasted effort on low-impact items",
                "template": "high_complexity",
            })

        if signals["high_value_opportunity"]:
            roi = signals["total_roi_potential"]
            points.append({
                "point": f"Your €{roi:,} annual ROI potential deserves protection",
                "evidence": "Human guidance ensures you capture maximum value",
                "template": "high_value",
            })

        if signals["stuck_indicators"]:
            points.append({
                "point": "Getting started is often the hardest part",
                "evidence": f"Our experts have helped hundreds of {industry} businesses overcome this exact challenge",
                "template": "stuck",
            })

        # Always add value proposition
        points.append({
            "point": "1-hour consultation + 30 days of email support for €350 more",
            "evidence": "Average customer saves 10+ hours of research and trial-and-error",
            "template": "value_prop",
        })

        return points[:4]  # Max 4 points

    def _determine_timing(
        self,
        signals: Dict[str, Any],
        engagement: Dict[str, Any],
    ) -> str:
        """Determine best timing for upsell."""
        if signals["stuck_indicators"]:
            return "immediate"

        if signals["custom_dev_needed"] and signals["complexity_score"] >= 7:
            return "immediate"

        days = engagement.get("days_since_report", 0)
        if days < 3:
            return "after_first_action"  # Let them try first
        elif days < 14:
            return "now"
        else:
            return "rescue"  # They may be stuck

    async def _generate_approach(
        self,
        signals: Dict[str, Any],
        pitch_points: List[Dict[str, str]],
        industry: str,
        company_name: str,
    ) -> str:
        """Generate personalized approach recommendation."""
        if not self.client:
            return self._get_default_approach(signals)

        prompt = f"""Generate a brief, personalized upsell approach for a {industry} company.

COMPANY: {company_name}
SIGNALS:
- Complexity: {signals['complexity_score']}/10
- Custom dev needed: {signals['custom_dev_needed']}
- ROI potential: €{signals['total_roi_potential']:,}
- Stuck: {signals['stuck_indicators']}

PITCH POINTS:
{[p['point'] for p in pitch_points]}

Generate a 1-2 sentence approach recommendation. Be specific about:
1. How to frame the conversation
2. What to offer (free consultation, demo, etc.)

Return ONLY a JSON object:
{{
    "approach": "Your recommended approach here..."
}}"""

        try:
            result = await self.call_llm_json(
                prompt=prompt,
                system="You are a customer success expert. Provide helpful, non-pushy upsell approaches."
            )
            return result.get("approach", self._get_default_approach(signals))

        except Exception as e:
            logger.warning(f"Approach generation failed: {e}")
            return self._get_default_approach(signals)

    def _get_default_approach(self, signals: Dict[str, Any]) -> str:
        """Get default approach based on signals."""
        if signals["stuck_indicators"]:
            return "Offer a free 15-minute 'unstuck' call to review their specific blockers and create an action plan."

        if signals["custom_dev_needed"]:
            return "Offer a free 15-minute technical consultation to scope the custom implementation requirements."

        if signals["high_value_opportunity"]:
            return "Highlight the ROI at risk and offer a consultation to ensure they maximize the value."

        return "Include a soft upsell in the follow-up email, emphasizing the time savings of expert guidance."


# For skill discovery
__all__ = ["UpsellIdentifierSkill"]
