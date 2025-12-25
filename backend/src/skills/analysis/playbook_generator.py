"""
Playbook Generator Skill

Generates implementation playbooks for recommendations.

This skill:
1. Takes a recommendation and chosen option
2. Generates week-by-week implementation plan
3. Lists required resources and skills
4. Defines success metrics

Output Schema:
{
    "recommendation_id": "rec-001",
    "option_chosen": "off_the_shelf",
    "vendor": "Calendly",
    "timeline": {
        "total_weeks": 4,
        "phases": [
            {
                "phase": 1,
                "name": "Setup",
                "weeks": "1-2",
                "tasks": [
                    "Sign up for Calendly Pro account",
                    "Configure availability settings",
                    "Set up team members"
                ],
                "deliverables": ["Account configured", "Team added"],
                "owner": "Operations Manager"
            }
        ]
    },
    "resources": [
        {
            "type": "documentation",
            "title": "Calendly Quick Start Guide",
            "url": "https://help.calendly.com/..."
        }
    ],
    "skills_required": ["Basic computer skills", "Calendar management"],
    "success_metrics": [
        {
            "metric": "Online bookings per week",
            "baseline": 0,
            "target": "50% of all bookings",
            "measurement": "Calendly analytics"
        }
    ],
    "risks_and_mitigations": [
        {
            "risk": "Staff resistance to new tool",
            "mitigation": "Involve team in configuration, provide training"
        }
    ]
}
"""

import logging
from typing import Dict, Any, List, Optional

from src.skills.base import LLMSkill, SkillContext, SkillError

logger = logging.getLogger(__name__)

# Standard implementation phases
IMPLEMENTATION_PHASES = {
    "off_the_shelf": [
        {"name": "Setup & Configuration", "weeks": 1, "focus": "Account setup, basic configuration"},
        {"name": "Team Onboarding", "weeks": 1, "focus": "Training, user setup"},
        {"name": "Integration", "weeks": 1, "focus": "Connect with existing tools"},
        {"name": "Go-Live & Optimization", "weeks": 1, "focus": "Launch, monitor, adjust"},
    ],
    "best_in_class": [
        {"name": "Planning & Setup", "weeks": 2, "focus": "Account setup, requirements gathering"},
        {"name": "Configuration", "weeks": 2, "focus": "Advanced configuration, customization"},
        {"name": "Integration & Testing", "weeks": 2, "focus": "Connect systems, test workflows"},
        {"name": "Training & Rollout", "weeks": 2, "focus": "Team training, phased launch"},
    ],
    "custom_solution": [
        {"name": "Requirements & Design", "weeks": 2, "focus": "Document requirements, design solution"},
        {"name": "Development Sprint 1", "weeks": 3, "focus": "Core functionality"},
        {"name": "Development Sprint 2", "weeks": 3, "focus": "Integration, polish"},
        {"name": "Testing & QA", "weeks": 2, "focus": "Testing, bug fixes"},
        {"name": "Deployment & Training", "weeks": 2, "focus": "Deploy, train team"},
    ],
}


class PlaybookGeneratorSkill(LLMSkill[Dict[str, Any]]):
    """
    Generate implementation playbooks for recommendations.

    Provides step-by-step implementation plans that clients
    can follow to implement their chosen solution.
    """

    name = "playbook-generator"
    description = "Generate implementation playbooks"
    version = "1.0.0"

    requires_llm = True
    requires_knowledge = False

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Generate an implementation playbook.

        Args:
            context: SkillContext with:
                - metadata.recommendation: The recommendation
                - metadata.option_chosen: Which option was selected
                - metadata.company_context: Company info

        Returns:
            Implementation playbook with timeline and resources
        """
        recommendation = context.metadata.get("recommendation", {})
        option_chosen = context.metadata.get("option_chosen", "off_the_shelf")
        company_context = context.metadata.get("company_context", {})

        if not recommendation:
            raise SkillError(
                self.name,
                "No recommendation provided in context.metadata",
                recoverable=False
            )

        # Get option details
        options = recommendation.get("options", {})
        option = options.get(option_chosen, {})

        # Get vendor info
        vendor = option.get("vendor") or option.get("name")
        matched_vendor = option.get("matched_vendor", {})
        if not vendor and matched_vendor:
            vendor = matched_vendor.get("vendor")

        # Generate timeline
        timeline = self._generate_timeline(
            option_chosen=option_chosen,
            option_details=option,
            recommendation=recommendation,
        )

        # Generate tasks using LLM
        if self.client:
            timeline = await self._enrich_timeline_with_llm(
                timeline=timeline,
                recommendation=recommendation,
                option=option,
                vendor=vendor,
                industry=context.industry,
            )

        # Get resources
        resources = self._get_resources(vendor, option_chosen, option)

        # Get skills required
        skills = self._get_skills_required(option_chosen, option)

        # Generate success metrics
        metrics = self._generate_success_metrics(recommendation, option)

        # Generate risks and mitigations
        risks = self._generate_risks(option_chosen, company_context)

        return {
            "recommendation_id": recommendation.get("id"),
            "option_chosen": option_chosen,
            "vendor": vendor,
            "timeline": timeline,
            "resources": resources,
            "skills_required": skills,
            "success_metrics": metrics,
            "risks_and_mitigations": risks,
        }

    def _generate_timeline(
        self,
        option_chosen: str,
        option_details: Dict[str, Any],
        recommendation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate implementation timeline."""
        phases_template = IMPLEMENTATION_PHASES.get(
            option_chosen,
            IMPLEMENTATION_PHASES["off_the_shelf"]
        )

        # Adjust based on implementation weeks from option
        impl_weeks = option_details.get("implementation_weeks", 4)
        scale_factor = impl_weeks / sum(p["weeks"] for p in phases_template)

        phases = []
        current_week = 1

        for i, template in enumerate(phases_template):
            weeks = max(1, int(template["weeks"] * scale_factor))
            end_week = current_week + weeks - 1

            phases.append({
                "phase": i + 1,
                "name": template["name"],
                "weeks": f"{current_week}-{end_week}" if weeks > 1 else str(current_week),
                "focus": template["focus"],
                "tasks": [],  # Will be filled by LLM
                "deliverables": [],
                "owner": "Project Lead",
            })

            current_week = end_week + 1

        return {
            "total_weeks": impl_weeks,
            "phases": phases,
        }

    async def _enrich_timeline_with_llm(
        self,
        timeline: Dict[str, Any],
        recommendation: Dict[str, Any],
        option: Dict[str, Any],
        vendor: Optional[str],
        industry: str,
    ) -> Dict[str, Any]:
        """Use LLM to generate specific tasks for each phase."""
        phases_summary = [
            {"phase": p["phase"], "name": p["name"], "focus": p["focus"]}
            for p in timeline["phases"]
        ]

        prompt = f"""Generate specific implementation tasks for this project.

RECOMMENDATION: {recommendation.get('title', 'Unknown')}
OPTION: {option.get('approach', vendor or 'Software implementation')}
VENDOR: {vendor or 'To be selected'}
INDUSTRY: {industry}

PHASES:
{phases_summary}

For each phase, provide:
1. 3-5 specific tasks
2. 1-2 deliverables
3. Suggested owner role

Return ONLY a JSON object:
{{
    "phases": [
        {{
            "phase": 1,
            "tasks": ["Task 1", "Task 2", "Task 3"],
            "deliverables": ["Deliverable 1"],
            "owner": "Role name"
        }}
    ]
}}"""

        try:
            result = await self.call_llm_json(
                prompt=prompt,
                system="You are a project manager creating implementation plans. Be specific and actionable."
            )

            # Merge LLM results with timeline
            phase_updates = {
                p["phase"]: p
                for p in result.get("phases", [])
            }

            for phase in timeline["phases"]:
                if phase["phase"] in phase_updates:
                    update = phase_updates[phase["phase"]]
                    phase["tasks"] = update.get("tasks", phase["tasks"])
                    phase["deliverables"] = update.get("deliverables", phase["deliverables"])
                    phase["owner"] = update.get("owner", phase["owner"])

        except Exception as e:
            logger.warning(f"LLM timeline enrichment failed: {e}")
            # Add default tasks
            for phase in timeline["phases"]:
                phase["tasks"] = [
                    f"Complete {phase['focus'].lower()}",
                    "Document progress",
                    "Review with stakeholders",
                ]
                phase["deliverables"] = [f"{phase['name']} complete"]

        return timeline

    def _get_resources(
        self,
        vendor: Optional[str],
        option_chosen: str,
        option: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Get implementation resources."""
        resources = []

        if vendor:
            resources.append({
                "type": "documentation",
                "title": f"{vendor} Getting Started Guide",
                "url": f"https://help.{vendor.lower().replace(' ', '')}.com" if vendor else None,
            })
            resources.append({
                "type": "documentation",
                "title": f"{vendor} Best Practices",
                "url": None,
            })

        if option_chosen == "custom_solution":
            resources.extend([
                {
                    "type": "documentation",
                    "title": "Claude API Documentation",
                    "url": "https://docs.anthropic.com",
                },
                {
                    "type": "template",
                    "title": "Project Requirements Template",
                    "url": None,
                },
            ])

            # Add build tools
            build_tools = option.get("build_tools", [])
            for tool in build_tools[:3]:
                resources.append({
                    "type": "documentation",
                    "title": f"{tool} Documentation",
                    "url": None,
                })

        return resources

    def _get_skills_required(
        self,
        option_chosen: str,
        option: Dict[str, Any],
    ) -> List[str]:
        """Get skills required for implementation."""
        if option_chosen == "custom_solution":
            return option.get("skills_required", [
                "Python or JavaScript",
                "API integration",
                "Basic DevOps",
            ])
        elif option_chosen == "best_in_class":
            return [
                "Software administration",
                "Process documentation",
                "Basic technical aptitude",
            ]
        else:
            return [
                "Basic computer skills",
                "Willingness to learn new tools",
            ]

    def _generate_success_metrics(
        self,
        recommendation: Dict[str, Any],
        option: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate success metrics."""
        metrics = []

        # Time-based metric
        roi_detail = recommendation.get("roi_detail", {})
        time_savings = roi_detail.get("time_savings", {})
        if time_savings.get("hours_per_week"):
            metrics.append({
                "metric": "Time saved per week",
                "baseline": "0 hours",
                "target": f"{time_savings['hours_per_week']} hours",
                "measurement": "Time tracking before/after",
            })

        # Adoption metric
        metrics.append({
            "metric": "Team adoption rate",
            "baseline": "0%",
            "target": "80% within 30 days",
            "measurement": "Usage analytics",
        })

        # Financial metric
        financial = roi_detail.get("financial_impact", {})
        if financial.get("monthly_savings"):
            metrics.append({
                "metric": "Monthly cost savings",
                "baseline": "€0",
                "target": f"€{financial['monthly_savings']:,.0f}",
                "measurement": "Monthly financial review",
            })

        # Generic outcome metric
        metrics.append({
            "metric": "User satisfaction",
            "baseline": "N/A",
            "target": "4+ out of 5 rating",
            "measurement": "Team survey after 30 days",
        })

        return metrics[:4]

    def _generate_risks(
        self,
        option_chosen: str,
        company_context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate risks and mitigations."""
        risks = [
            {
                "risk": "Staff resistance to change",
                "mitigation": "Involve team early, provide training, celebrate quick wins",
            },
            {
                "risk": "Implementation delays",
                "mitigation": "Build buffer time, identify dependencies early",
            },
        ]

        if option_chosen == "custom_solution":
            risks.extend([
                {
                    "risk": "Technical complexity",
                    "mitigation": "Start with MVP, iterate based on feedback",
                },
                {
                    "risk": "Ongoing maintenance burden",
                    "mitigation": "Document thoroughly, plan for updates",
                },
            ])
        else:
            risks.append({
                "risk": "Vendor pricing changes",
                "mitigation": "Review contract terms, consider annual commitment",
            })

        return risks[:4]


# For skill discovery
__all__ = ["PlaybookGeneratorSkill"]
