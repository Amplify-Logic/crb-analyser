"""
Follow-up Scheduler Skill

Determines optimal follow-up timing and content based on report analysis.

This skill:
1. Analyzes report complexity and customer engagement signals
2. Determines optimal follow-up timing
3. Identifies focus areas for follow-up
4. Generates personalized email templates

Output Schema:
{
    "follow_up_schedule": [
        {
            "timing": "1 week",
            "type": "check_in",
            "focus_areas": ["Quick win #1 progress", "Tool setup"],
            "channel": "email",
            "priority": "high"
        },
        {
            "timing": "2 weeks",
            "type": "progress_review",
            "focus_areas": ["Implementation status", "Blockers"],
            "channel": "call",
            "priority": "medium"
        }
    ],
    "email_templates": {
        "1_week": {
            "subject": "How's your AI implementation going?",
            "body": "..."
        }
    },
    "engagement_score": 75,
    "recommended_touchpoints": 3,
    "escalation_triggers": [
        "No response after 2 attempts",
        "Reported blocker"
    ]
}
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.skills.base import LLMSkill, SkillContext, SkillError

logger = logging.getLogger(__name__)

# Follow-up timing based on report complexity
FOLLOW_UP_TIMING = {
    "simple": {
        "first_check": 7,  # days
        "progress_review": 14,
        "final_check": 30,
    },
    "medium": {
        "first_check": 5,
        "progress_review": 14,
        "milestone_check": 21,
        "final_check": 45,
    },
    "complex": {
        "first_check": 3,
        "progress_review": 7,
        "milestone_check": 14,
        "deep_review": 30,
        "final_check": 60,
    },
}

# Email templates by follow-up type
EMAIL_TEMPLATES = {
    "first_check": {
        "subject": "Quick check: How's your {quick_win} implementation going?",
        "preview": "Just wanted to see if you've had a chance to get started...",
    },
    "progress_review": {
        "subject": "Your AI implementation progress - let's review",
        "preview": "It's been {days} days since your report. Let's check in...",
    },
    "milestone_check": {
        "subject": "Milestone check: {milestone_name}",
        "preview": "You should be completing {milestone_name} around now...",
    },
    "blocker_check": {
        "subject": "Need help with your implementation?",
        "preview": "We noticed you might be stuck. Here's how we can help...",
    },
}


class FollowupSchedulerSkill(LLMSkill[Dict[str, Any]]):
    """
    Schedule optimal follow-up touchpoints.

    Determines when and how to follow up with customers
    based on their report and engagement signals.
    """

    name = "followup-scheduler"
    description = "Determine optimal follow-up timing and content"
    version = "1.0.0"

    requires_llm = False  # LLM is optional, uses default templates fallback
    requires_expertise = False

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Schedule follow-up touchpoints.

        Args:
            context: SkillContext with:
                - metadata.report: The generated report
                - metadata.quick_wins: Identified quick wins
                - metadata.customer_tier: Payment tier
                - metadata.engagement_signals: Optional engagement data

        Returns:
            Follow-up schedule with templates
        """
        report = context.metadata.get("report", {})
        quick_wins = context.metadata.get("quick_wins", [])
        customer_tier = context.metadata.get("customer_tier", "ai")
        engagement_signals = context.metadata.get("engagement_signals", {})

        # Assess report complexity
        complexity = self._assess_complexity(report, quick_wins)

        # Calculate engagement score
        engagement_score = self._calculate_engagement_score(engagement_signals)

        # Generate follow-up schedule
        schedule = self._generate_schedule(
            complexity=complexity,
            customer_tier=customer_tier,
            engagement_score=engagement_score,
            quick_wins=quick_wins,
        )

        # Generate email templates
        templates = await self._generate_templates(
            schedule=schedule,
            quick_wins=quick_wins,
            industry=context.industry,
            company_name=context.metadata.get("company_name", "your company"),
        )

        # Determine escalation triggers
        escalation_triggers = self._get_escalation_triggers(
            complexity=complexity,
            customer_tier=customer_tier,
        )

        return {
            "follow_up_schedule": schedule,
            "email_templates": templates,
            "engagement_score": engagement_score,
            "recommended_touchpoints": len(schedule),
            "escalation_triggers": escalation_triggers,
            "complexity": complexity,
        }

    def _assess_complexity(
        self,
        report: Dict[str, Any],
        quick_wins: List[Dict[str, Any]],
    ) -> str:
        """Assess report/implementation complexity."""
        findings_count = len(report.get("findings", []))
        recommendations_count = len(report.get("recommendations", []))

        # Check for custom solutions
        has_custom = False
        for rec in report.get("recommendations", []):
            if rec.get("our_recommendation") == "custom_solution":
                has_custom = True
                break

        # Check verdict
        verdict = report.get("verdict", {}).get("decision", "")

        # Score complexity
        complexity_score = 0

        if findings_count > 5:
            complexity_score += 2
        elif findings_count > 3:
            complexity_score += 1

        if recommendations_count > 4:
            complexity_score += 2
        elif recommendations_count > 2:
            complexity_score += 1

        if has_custom:
            complexity_score += 2

        if verdict in ["caution", "wait"]:
            complexity_score += 1

        # Quick wins reduce perceived complexity
        if len(quick_wins) >= 2:
            complexity_score -= 1

        if complexity_score >= 4:
            return "complex"
        elif complexity_score >= 2:
            return "medium"
        else:
            return "simple"

    def _calculate_engagement_score(
        self,
        signals: Dict[str, Any],
    ) -> int:
        """Calculate customer engagement score (0-100)."""
        score = 50  # Base score

        # Positive signals
        if signals.get("report_viewed"):
            score += 10
        if signals.get("report_downloaded"):
            score += 10
        if signals.get("quick_win_clicked"):
            score += 15
        if signals.get("vendor_link_clicked"):
            score += 10
        if signals.get("replied_to_email"):
            score += 20

        # Negative signals
        if signals.get("bounced_email"):
            score -= 30
        if signals.get("unsubscribed"):
            score -= 50

        # Time-based decay
        days_since_report = signals.get("days_since_report", 0)
        if days_since_report > 14:
            score -= 10
        if days_since_report > 30:
            score -= 20

        return max(0, min(100, score))

    def _generate_schedule(
        self,
        complexity: str,
        customer_tier: str,
        engagement_score: int,
        quick_wins: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generate follow-up schedule."""
        timing = FOLLOW_UP_TIMING.get(complexity, FOLLOW_UP_TIMING["medium"])
        schedule = []

        # First check - always include
        first_focus = []
        if quick_wins:
            first_focus.append(f"Quick win: {quick_wins[0].get('title', 'first implementation')}")
        first_focus.append("Initial setup progress")

        schedule.append({
            "timing": f"{timing['first_check']} days",
            "timing_days": timing["first_check"],
            "type": "first_check",
            "focus_areas": first_focus,
            "channel": "email",
            "priority": "high" if engagement_score < 60 else "medium",
        })

        # Progress review
        schedule.append({
            "timing": f"{timing['progress_review']} days",
            "timing_days": timing["progress_review"],
            "type": "progress_review",
            "focus_areas": ["Implementation status", "Blockers encountered", "Questions"],
            "channel": "call" if customer_tier == "human" else "email",
            "priority": "high",
        })

        # Milestone check (for medium/complex)
        if "milestone_check" in timing:
            schedule.append({
                "timing": f"{timing['milestone_check']} days",
                "timing_days": timing["milestone_check"],
                "type": "milestone_check",
                "focus_areas": ["Milestone completion", "ROI measurement", "Next steps"],
                "channel": "email",
                "priority": "medium",
            })

        # Deep review (for complex)
        if "deep_review" in timing:
            schedule.append({
                "timing": f"{timing['deep_review']} days",
                "timing_days": timing["deep_review"],
                "type": "deep_review",
                "focus_areas": ["Full progress assessment", "Adjustments needed", "Additional support"],
                "channel": "call",
                "priority": "high",
            })

        # Final check
        schedule.append({
            "timing": f"{timing['final_check']} days",
            "timing_days": timing["final_check"],
            "type": "final_check",
            "focus_areas": ["Overall success", "Lessons learned", "Future opportunities"],
            "channel": "email",
            "priority": "low",
        })

        return schedule

    async def _generate_templates(
        self,
        schedule: List[Dict[str, Any]],
        quick_wins: List[Dict[str, Any]],
        industry: str,
        company_name: str,
    ) -> Dict[str, Dict[str, str]]:
        """Generate email templates for each touchpoint."""
        if not self.client:
            return self._get_default_templates(schedule, quick_wins, company_name)

        # Get first quick win for personalization
        first_quick_win = quick_wins[0].get("title", "your first implementation") if quick_wins else "your AI implementation"

        touchpoint_types = [s["type"] for s in schedule]

        prompt = f"""Generate personalized follow-up email templates for a {industry} company.

COMPANY: {company_name}
FIRST QUICK WIN: {first_quick_win}
TOUCHPOINTS: {touchpoint_types}

For each touchpoint type, generate:
1. Subject line (compelling, personalized)
2. Email body (2-3 paragraphs, friendly, actionable)

Return ONLY a JSON object:
{{
    "templates": {{
        "first_check": {{
            "subject": "...",
            "body": "..."
        }},
        "progress_review": {{
            "subject": "...",
            "body": "..."
        }}
    }}
}}"""

        try:
            result = await self.call_llm_json(
                prompt=prompt,
                system="You are a customer success manager. Write warm, professional follow-up emails that encourage action without being pushy."
            )
            return result.get("templates", self._get_default_templates(schedule, quick_wins, company_name))

        except Exception as e:
            logger.warning(f"Template generation failed: {e}")
            return self._get_default_templates(schedule, quick_wins, company_name)

    def _get_default_templates(
        self,
        schedule: List[Dict[str, Any]],
        quick_wins: List[Dict[str, Any]],
        company_name: str,
    ) -> Dict[str, Dict[str, str]]:
        """Get default email templates."""
        first_qw = quick_wins[0].get("title", "your quick win") if quick_wins else "your implementation"

        return {
            "first_check": {
                "subject": f"How's the {first_qw} going?",
                "body": f"""Hi there,

It's been a few days since you received your CRB Analysis report. I wanted to check in and see if you've had a chance to start on {first_qw}.

If you've run into any questions or need help getting started, just reply to this email - I'm here to help!

Best regards,
The CRB Team"""
            },
            "progress_review": {
                "subject": "Let's review your AI implementation progress",
                "body": f"""Hi there,

You're now a couple of weeks into your AI implementation journey. I'd love to hear how things are going!

A few questions:
- Have you started implementing any of the quick wins?
- Are there any blockers I can help with?
- What's working well so far?

Looking forward to hearing from you!

Best,
The CRB Team"""
            },
            "milestone_check": {
                "subject": "Milestone check-in: How are results looking?",
                "body": f"""Hi there,

By now you should be starting to see some early results from your implementations.

I'd love to hear:
- What improvements have you noticed?
- Are the time/cost savings matching expectations?
- What would you do differently?

Your feedback helps us improve our recommendations for others too!

Best,
The CRB Team"""
            },
            "final_check": {
                "subject": "Looking back: Your AI implementation journey",
                "body": f"""Hi there,

It's been a while since your CRB Analysis, and I wanted to check in one more time.

I'd love to hear about your overall experience:
- What's been the biggest win?
- Are there recommendations you haven't implemented yet?
- Would you like to explore additional opportunities?

Thanks for trusting us with your AI journey!

Best,
The CRB Team"""
            },
        }

    def _get_escalation_triggers(
        self,
        complexity: str,
        customer_tier: str,
    ) -> List[str]:
        """Get escalation triggers based on context."""
        triggers = [
            "No response after 2 email attempts",
            "Customer reports being stuck/blocked",
            "Negative feedback received",
        ]

        if customer_tier == "human":
            triggers.append("Missed scheduled call")
            triggers.append("Implementation significantly behind schedule")

        if complexity == "complex":
            triggers.append("Technical issues requiring expert support")
            triggers.append("Scope creep detected")

        return triggers


# For skill discovery
__all__ = ["FollowupSchedulerSkill"]
