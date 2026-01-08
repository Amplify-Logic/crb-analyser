"""
Automation Summary Skill - Phase 2D

Generates the "Your Automation Roadmap" section at the end of reports.
Aggregates all automation opportunities from findings into a summary view.

This is a SyncSkill - no LLM calls needed, pure aggregation logic.

See: docs/plans/2026-01-07-connect-vs-replace-design.md
"""

import logging
from statistics import mean
from typing import Any, Dict, List

from src.models.automation_summary import (
    AutomationOpportunity,
    AutomationSummary,
    StackAssessment,
    StackAssessmentItem,
    get_next_steps,
    get_stack_verdict,
)
from src.skills.base import SkillContext, SyncSkill

logger = logging.getLogger(__name__)


class AutomationSummarySkill(SyncSkill[AutomationSummary]):
    """
    Generate automation roadmap summary from findings.

    This skill:
    1. Aggregates automation opportunities from all findings
    2. Calculates stack assessment from existing_stack
    3. Computes totals (impact, hours, counts)
    4. Generates tier-aware next steps

    No LLM required - pure data aggregation.
    """

    name = "automation-summary"
    description = "Generate automation roadmap summary from findings"
    version = "1.0.0"

    requires_llm = False
    requires_expertise = False
    requires_knowledge = False

    def execute_sync(self, context: SkillContext) -> AutomationSummary:
        """
        Generate automation summary from context.

        Args:
            context: SkillContext with:
                - report_data.findings: List of findings with Connect/Replace paths
                - existing_stack: User's software stack
                - metadata.tier: Report tier for messaging

        Returns:
            AutomationSummary with stack assessment, opportunities, and next steps
        """
        # Extract data from context
        report_data = context.report_data or {}
        findings = report_data.get("findings", [])
        existing_stack = context.existing_stack or []
        tier = context.metadata.get("tier", "quick")

        # Build stack assessment
        stack_assessment = self._build_stack_assessment(existing_stack)

        # Aggregate opportunities from findings
        opportunities = self._aggregate_opportunities(findings)

        # Calculate totals
        total_monthly_impact = sum(opp.impact_monthly for opp in opportunities)
        total_diy_hours = sum(opp.diy_effort_hours for opp in opportunities)
        connect_count = sum(1 for opp in opportunities if opp.approach == "Connect")
        replace_count = sum(1 for opp in opportunities if opp.approach == "Replace")
        either_count = sum(1 for opp in opportunities if opp.approach == "Either")

        # Get tier-aware next steps
        next_steps = get_next_steps(tier)

        return AutomationSummary(
            stack_assessment=stack_assessment,
            opportunities=opportunities,
            total_monthly_impact=total_monthly_impact,
            total_diy_hours=total_diy_hours,
            connect_count=connect_count,
            replace_count=replace_count,
            either_count=either_count,
            next_steps=next_steps,
        )

    def _build_stack_assessment(
        self,
        existing_stack: List[Dict[str, Any]]
    ) -> StackAssessment:
        """
        Build stack assessment from existing tools.

        Args:
            existing_stack: List of tools with API scores

        Returns:
            StackAssessment with tools, average score, and verdict
        """
        if not existing_stack:
            verdict, verdict_text = get_stack_verdict(0)
            return StackAssessment(
                tools=[],
                average_score=0,
                verdict=verdict,
                verdict_text=verdict_text,
            )

        # Convert to StackAssessmentItem models
        tools = []
        scores = []
        for tool in existing_stack:
            api_score = tool.get("api_score")
            if api_score is not None:
                try:
                    score = int(api_score)
                    scores.append(score)
                    tools.append(StackAssessmentItem(
                        name=tool.get("name", tool.get("slug", "Unknown")),
                        slug=tool.get("slug", "unknown"),
                        api_score=max(1, min(5, score)),  # Clamp to 1-5
                        category=tool.get("category"),
                    ))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid API score for tool: {tool}")
                    continue

        # Calculate average
        average_score = mean(scores) if scores else 0

        # Get verdict
        verdict, verdict_text = get_stack_verdict(average_score)

        return StackAssessment(
            tools=tools,
            average_score=round(average_score, 1),
            verdict=verdict,
            verdict_text=verdict_text,
        )

    def _aggregate_opportunities(
        self,
        findings: List[Dict[str, Any]]
    ) -> List[AutomationOpportunity]:
        """
        Aggregate automation opportunities from findings.

        Only includes findings that have Connect or Replace paths
        and are not marked as "not recommended".

        Args:
            findings: List of findings with automation paths

        Returns:
            List of AutomationOpportunity models
        """
        opportunities = []

        for finding in findings:
            # Skip not-recommended findings
            if finding.get("is_not_recommended", False):
                continue

            # Skip findings without automation paths
            connect_path = finding.get("connect_path")
            replace_path = finding.get("replace_path")
            if not connect_path and not replace_path:
                continue

            # Determine approach based on verdict
            verdict = finding.get("verdict", "EITHER")
            if verdict == "CONNECT":
                approach = "Connect"
            elif verdict == "REPLACE":
                approach = "Replace"
            else:
                approach = "Either"

            # Calculate DIY effort hours
            # Use connect_path hours if available, otherwise estimate from replace weeks
            if connect_path and connect_path.get("setup_effort_hours"):
                diy_hours = float(connect_path.get("setup_effort_hours", 0))
            elif replace_path and replace_path.get("setup_effort_weeks"):
                # Estimate hours from weeks (assuming 40 hours/week for full setup)
                # But DIY is typically less, so use 20 hours per week estimate
                diy_hours = float(replace_path.get("setup_effort_weeks", 0)) * 20
            else:
                diy_hours = 0

            # Get monthly impact
            impact_monthly = float(finding.get("impact_monthly", 0))

            # If no impact_monthly, try to calculate from value_saved
            if impact_monthly == 0:
                value_saved = finding.get("value_saved", {})
                if isinstance(value_saved, dict):
                    annual = value_saved.get("annual_savings", 0)
                    if annual:
                        impact_monthly = float(annual) / 12

            # Get tools involved
            tools_involved = []
            if connect_path:
                tools_involved.extend(connect_path.get("tools_used", []))
            # Include relevant stack tools
            relevant_stack = finding.get("relevant_stack", [])
            for tool in relevant_stack:
                name = tool.get("name", tool.get("slug", ""))
                if name and name not in tools_involved:
                    tools_involved.append(name)

            opportunities.append(AutomationOpportunity(
                finding_id=finding.get("id", "unknown"),
                title=finding.get("title", "Untitled Automation"),
                impact_monthly=impact_monthly,
                diy_effort_hours=diy_hours,
                approach=approach,
                tools_involved=tools_involved[:5],  # Limit to 5 tools
                category=finding.get("category", "efficiency"),
            ))

        # Sort by impact (highest first)
        opportunities.sort(key=lambda x: x.impact_monthly, reverse=True)

        return opportunities


# For skill discovery
__all__ = ["AutomationSummarySkill"]
