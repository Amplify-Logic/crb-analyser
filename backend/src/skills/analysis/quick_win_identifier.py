"""
Quick Win Identifier Skill

Identifies low-effort, high-impact opportunities from findings.

This skill:
1. Analyzes all findings for quick win potential
2. Scores based on implementation effort vs impact
3. Filters for low-risk, high-ROI opportunities
4. Returns top 3 actionable quick wins

Output Schema:
{
    "quick_wins": [
        {
            "finding_id": "finding-001",
            "title": "Implement online booking",
            "why_quick": "Off-the-shelf solution, no custom dev needed",
            "implementation_hours": 8,
            "estimated_roi": 180,
            "risk_level": "low",
            "first_step": "Sign up for Calendly free trial",
            "expected_result": "50% reduction in phone scheduling time",
            "confidence": "high",
            "action_today": {
                "what": "Create Calendly account and connect your calendar",
                "url": "https://calendly.com/signup",
                "time_minutes": 15,
                "immediate_outcome": "You'll have a booking link to share with 3 clients today"
            }
        }
    ],
    "selection_criteria": {
        "max_implementation_hours": 40,
        "min_roi_percentage": 100,
        "max_risk_level": "medium"
    },
    "total_findings_analyzed": 8,
    "quick_wins_found": 3
}
"""

import logging
from typing import Dict, Any, List, Optional

from src.skills.base import LLMSkill, SkillContext, SkillError

logger = logging.getLogger(__name__)

# Default thresholds for quick wins
DEFAULT_THRESHOLDS = {
    "max_implementation_hours": 40,
    "min_roi_percentage": 100,
    "max_risk_level": "medium",  # low or medium
    "min_confidence": "medium",  # medium or high
}

# Risk level ordering
RISK_LEVELS = {"low": 1, "medium": 2, "high": 3}
CONFIDENCE_LEVELS = {"low": 1, "medium": 2, "high": 3}


class QuickWinIdentifierSkill(LLMSkill[Dict[str, Any]]):
    """
    Identify quick wins from findings.

    Quick wins are opportunities that:
    - Can be implemented in < 40 hours
    - Have ROI > 100%
    - Have low to medium risk
    - Use off-the-shelf or simple solutions
    """

    name = "quick-win-identifier"
    description = "Identify low-effort, high-impact opportunities"
    version = "1.0.0"

    requires_llm = True
    requires_expertise = False

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Identify quick wins from findings.

        Args:
            context: SkillContext with:
                - metadata.findings: List of findings to analyze
                - metadata.recommendations: Optional recommendations with ROI
                - metadata.thresholds: Optional custom thresholds

        Returns:
            Quick wins with implementation details
        """
        findings = context.metadata.get("findings", [])
        recommendations = context.metadata.get("recommendations", [])
        custom_thresholds = context.metadata.get("thresholds", {})

        if not findings:
            raise SkillError(
                self.name,
                "No findings provided in context.metadata",
                recoverable=False
            )

        # Merge thresholds
        thresholds = {**DEFAULT_THRESHOLDS, **custom_thresholds}

        # Build recommendation lookup
        rec_by_finding = {
            r.get("finding_id"): r
            for r in recommendations
        }

        # Score all findings for quick win potential
        scored_findings = []
        for finding in findings:
            score = self._score_quick_win_potential(
                finding=finding,
                recommendation=rec_by_finding.get(finding.get("id")),
                thresholds=thresholds,
            )
            if score["qualifies"]:
                scored_findings.append({
                    "finding": finding,
                    "recommendation": rec_by_finding.get(finding.get("id")),
                    "score": score,
                })

        # Sort by quick win score (higher is better)
        scored_findings.sort(key=lambda x: x["score"]["total_score"], reverse=True)

        # Take top 3 and enrich with LLM
        top_candidates = scored_findings[:5]  # Get 5, will refine to 3

        if top_candidates and self.client:
            quick_wins = await self._enrich_quick_wins(
                candidates=top_candidates,
                industry=context.industry,
            )
        else:
            quick_wins = [
                self._format_quick_win(c)
                for c in top_candidates[:3]
            ]

        return {
            "quick_wins": quick_wins[:3],
            "selection_criteria": thresholds,
            "total_findings_analyzed": len(findings),
            "quick_wins_found": len(quick_wins),
        }

    def _score_quick_win_potential(
        self,
        finding: Dict[str, Any],
        recommendation: Optional[Dict[str, Any]],
        thresholds: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Score a finding's quick win potential."""
        score = 0
        qualifies = True
        reasons = []

        # Check confidence
        confidence = finding.get("confidence", "medium").lower()
        if CONFIDENCE_LEVELS.get(confidence, 2) < CONFIDENCE_LEVELS.get(thresholds["min_confidence"], 2):
            qualifies = False
            reasons.append(f"Confidence too low: {confidence}")

        # Get implementation hours
        impl_hours = self._estimate_implementation_hours(finding, recommendation)
        if impl_hours > thresholds["max_implementation_hours"]:
            qualifies = False
            reasons.append(f"Implementation too long: {impl_hours}h")
        else:
            # Score inversely by hours (fewer hours = higher score)
            score += max(0, 50 - impl_hours)

        # Get ROI
        roi = self._get_roi(finding, recommendation)
        if roi < thresholds["min_roi_percentage"]:
            qualifies = False
            reasons.append(f"ROI too low: {roi}%")
        else:
            # Score by ROI (higher = better)
            score += min(50, roi / 4)  # Cap contribution at 50

        # Check risk
        risk = self._assess_risk(finding, recommendation)
        if RISK_LEVELS.get(risk, 2) > RISK_LEVELS.get(thresholds["max_risk_level"], 2):
            qualifies = False
            reasons.append(f"Risk too high: {risk}")
        else:
            # Bonus for low risk
            if risk == "low":
                score += 20

        # Bonus for off-the-shelf solutions
        if recommendation:
            our_rec = recommendation.get("our_recommendation", "")
            if our_rec == "off_the_shelf":
                score += 15
                reasons.append("Off-the-shelf solution available")
            elif our_rec == "best_in_class":
                score += 10

        # Bonus for high Two Pillars scores
        cv_score = finding.get("customer_value_score", 0)
        bh_score = finding.get("business_health_score", 0)
        if cv_score >= 8 or bh_score >= 8:
            score += 10
            reasons.append("High impact on pillars")

        return {
            "total_score": score,
            "qualifies": qualifies,
            "implementation_hours": impl_hours,
            "roi": roi,
            "risk": risk,
            "reasons": reasons,
        }

    def _estimate_implementation_hours(
        self,
        finding: Dict[str, Any],
        recommendation: Optional[Dict[str, Any]],
    ) -> int:
        """Estimate implementation hours."""
        if recommendation:
            our_rec = recommendation.get("our_recommendation", "off_the_shelf")
            options = recommendation.get("options", {})
            option = options.get(our_rec, {})

            # Get implementation weeks and convert to hours
            weeks = option.get("implementation_weeks", 2)
            return weeks * 20  # Assume 20 hours per week

        # Default estimates by finding category
        category = finding.get("category", "").lower()
        if "scheduling" in category or "booking" in category:
            return 8
        elif "automation" in category:
            return 16
        elif "communication" in category:
            return 12
        else:
            return 24  # Default

    def _get_roi(
        self,
        finding: Dict[str, Any],
        recommendation: Optional[Dict[str, Any]],
    ) -> float:
        """Get ROI percentage."""
        if recommendation:
            roi = recommendation.get("roi_percentage", 0)
            if roi:
                return float(roi)

            # Check roi_detail
            roi_detail = recommendation.get("roi_detail", {})
            if roi_detail:
                return float(roi_detail.get("roi_percentage", 0))

        # Estimate from finding
        cv = finding.get("customer_value_score", 5)
        bh = finding.get("business_health_score", 5)
        # Higher scores = higher estimated ROI
        return (cv + bh) * 10  # Rough estimate

    def _assess_risk(
        self,
        finding: Dict[str, Any],
        recommendation: Optional[Dict[str, Any]],
    ) -> str:
        """Assess implementation risk."""
        if recommendation:
            our_rec = recommendation.get("our_recommendation", "")
            if our_rec == "off_the_shelf":
                return "low"
            elif our_rec == "best_in_class":
                return "low"
            elif our_rec == "custom_solution":
                return "medium"

        # Default based on confidence
        confidence = finding.get("confidence", "medium").lower()
        if confidence == "high":
            return "low"
        elif confidence == "medium":
            return "medium"
        else:
            return "high"

    def _format_quick_win(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Format a quick win for output."""
        finding = candidate["finding"]
        recommendation = candidate.get("recommendation", {})
        score = candidate["score"]

        first_step = self._suggest_first_step(finding, recommendation)
        return {
            "finding_id": finding.get("id"),
            "title": finding.get("title", "Quick Win"),
            "why_quick": "; ".join(score.get("reasons", ["Low effort opportunity"])),
            "implementation_hours": score["implementation_hours"],
            "estimated_roi": score["roi"],
            "risk_level": score["risk"],
            "first_step": first_step,
            "expected_result": finding.get("expected_outcome", "Improved efficiency"),
            "confidence": finding.get("confidence", "medium"),
            "action_today": self._generate_action_today(finding, recommendation, first_step),
        }

    def _suggest_first_step(
        self,
        finding: Dict[str, Any],
        recommendation: Optional[Dict[str, Any]],
    ) -> str:
        """Suggest the first actionable step."""
        if recommendation:
            our_rec = recommendation.get("our_recommendation", "")
            options = recommendation.get("options", {})
            option = options.get(our_rec, {})

            vendor = option.get("vendor") or option.get("name")
            if vendor:
                return f"Sign up for {vendor} free trial"

            matched = option.get("matched_vendor", {})
            if matched.get("vendor"):
                return f"Sign up for {matched['vendor']} free trial"

        # Generic first steps by category
        title = finding.get("title", "").lower()
        if "schedul" in title or "book" in title:
            return "Research online booking solutions (Calendly, Acuity)"
        elif "automat" in title:
            return "Map the current manual workflow"
        elif "communicat" in title or "email" in title:
            return "Audit current communication channels"
        else:
            return "Document the current process and pain points"

    def _generate_action_today(
        self,
        finding: Dict[str, Any],
        recommendation: Optional[Dict[str, Any]],
        first_step: str,
    ) -> Dict[str, Any]:
        """Generate the action_today field - one thing they can do in 30 min."""
        title = finding.get("title", "").lower()

        # Check if recommendation has a specific vendor
        if recommendation:
            our_rec = recommendation.get("our_recommendation", "")
            options = recommendation.get("options", {})
            option = options.get(our_rec, {})

            vendor = option.get("vendor") or option.get("name", "")
            matched = option.get("matched_vendor", {})
            if matched.get("vendor"):
                vendor = matched["vendor"]

            # Common vendor URLs
            vendor_urls = {
                "calendly": "https://calendly.com/signup",
                "acuity": "https://acuityscheduling.com/signup",
                "hubspot": "https://app.hubspot.com/signup",
                "zapier": "https://zapier.com/sign-up",
                "make": "https://www.make.com/en/register",
                "n8n": "https://n8n.io/get-started",
                "slack": "https://slack.com/get-started",
                "notion": "https://www.notion.so/signup",
                "airtable": "https://airtable.com/signup",
                "typeform": "https://www.typeform.com/signup",
                "intercom": "https://www.intercom.com/early-stage",
                "freshdesk": "https://freshdesk.com/signup",
                "zendesk": "https://www.zendesk.com/register",
            }

            vendor_lower = vendor.lower() if vendor else ""
            for key, url in vendor_urls.items():
                if key in vendor_lower:
                    return {
                        "what": f"Create a free {vendor} account",
                        "url": url,
                        "time_minutes": 10,
                        "immediate_outcome": f"You'll have access to {vendor} to start exploring"
                    }

        # Default by finding category
        if "schedul" in title or "book" in title:
            return {
                "what": "Create a free Calendly account",
                "url": "https://calendly.com/signup",
                "time_minutes": 10,
                "immediate_outcome": "A booking link you can share with 3 clients today"
            }
        elif "automat" in title or "workflow" in title:
            return {
                "what": "Create a free Make.com account",
                "url": "https://www.make.com/en/register",
                "time_minutes": 15,
                "immediate_outcome": "Access to 1000+ automation templates"
            }
        elif "email" in title or "communicat" in title:
            return {
                "what": "Create a free HubSpot account",
                "url": "https://app.hubspot.com/signup",
                "time_minutes": 15,
                "immediate_outcome": "Email templates and tracking ready to use"
            }
        elif "invoice" in title or "billing" in title:
            return {
                "what": "Set up Stripe invoicing",
                "url": "https://dashboard.stripe.com/register",
                "time_minutes": 20,
                "immediate_outcome": "Send your first automated invoice"
            }
        else:
            return {
                "what": "Document your current process in Notion",
                "url": "https://www.notion.so/signup",
                "time_minutes": 20,
                "immediate_outcome": "A clear process map to share with your team"
            }

    async def _enrich_quick_wins(
        self,
        candidates: List[Dict[str, Any]],
        industry: str,
    ) -> List[Dict[str, Any]]:
        """Use LLM to enrich quick win details."""
        # Format candidates for prompt
        candidate_summaries = []
        for c in candidates:
            finding = c["finding"]
            score = c["score"]
            candidate_summaries.append({
                "id": finding.get("id"),
                "title": finding.get("title"),
                "description": finding.get("description", "")[:200],
                "implementation_hours": score["implementation_hours"],
                "estimated_roi": score["roi"],
                "risk": score["risk"],
            })

        prompt = f"""Select the top 3 quick wins and provide actionable details.

INDUSTRY: {industry}

CANDIDATES (pre-scored for quick win potential):
{candidate_summaries}

For each of the top 3, provide:
1. why_quick: Why this is a quick win (1 sentence)
2. first_step: Specific first action to take
3. expected_result: Concrete expected outcome
4. action_today: THE ONE THING they can do TODAY in under 30 minutes

Return ONLY a JSON object:
{{
    "quick_wins": [
        {{
            "id": "<finding id>",
            "why_quick": "...",
            "first_step": "...",
            "expected_result": "...",
            "action_today": {{
                "what": "<specific action, e.g., 'Create Calendly account'>",
                "url": "<direct URL to start, e.g., 'https://calendly.com/signup'>",
                "time_minutes": <5-30>,
                "immediate_outcome": "<what they'll have after 30 min, e.g., 'A booking link to share with clients'>"
            }}
        }}
    ]
}}

CRITICAL: action_today must be something they can literally do RIGHT NOW. Include real URLs."""

        try:
            result = await self.call_llm_json(
                prompt=prompt,
                system="You are a business efficiency consultant. Provide specific, actionable quick win recommendations."
            )

            # Merge LLM enrichments with candidate data
            enrichments = {
                qw["id"]: qw
                for qw in result.get("quick_wins", [])
            }

            enriched = []
            for c in candidates:
                finding_id = c["finding"].get("id")
                if finding_id in enrichments:
                    formatted = self._format_quick_win(c)
                    llm_data = enrichments[finding_id]
                    formatted["why_quick"] = llm_data.get("why_quick", formatted["why_quick"])
                    formatted["first_step"] = llm_data.get("first_step", formatted["first_step"])
                    formatted["expected_result"] = llm_data.get("expected_result", formatted["expected_result"])
                    # Add action_today from LLM
                    if llm_data.get("action_today"):
                        formatted["action_today"] = llm_data["action_today"]
                    enriched.append(formatted)

            return enriched if enriched else [self._format_quick_win(c) for c in candidates[:3]]

        except Exception as e:
            logger.warning(f"LLM enrichment failed: {e}")
            return [self._format_quick_win(c) for c in candidates[:3]]


# For skill discovery
__all__ = ["QuickWinIdentifierSkill"]
