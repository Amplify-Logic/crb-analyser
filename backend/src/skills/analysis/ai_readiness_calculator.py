"""
AI Readiness Calculator

Formula-based calculation of AI readiness score (0-100) with transparent breakdown.

This replaces LLM-guessed scores with a deterministic formula that:
1. Uses actual quiz answers and stack assessment data
2. Provides a breakdown users can understand
3. Gives actionable improvement suggestions

Score Components (total 100 points):
- Tech Stack Openness: 0-30 points (based on API scores of existing tools)
- Data Readiness: 0-25 points (digital processes, centralized data)
- Team Readiness: 0-25 points (tech comfort, change willingness)
- Process Maturity: 0-20 points (documented workflows, consistency)
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from src.skills.base import SyncSkill, SkillContext

logger = logging.getLogger(__name__)


@dataclass
class AIReadinessBreakdown:
    """Detailed breakdown of AI readiness score."""

    # Component scores
    tech_stack_score: int  # 0-30
    data_readiness_score: int  # 0-25
    team_readiness_score: int  # 0-25
    process_maturity_score: int  # 0-20

    # Total
    total_score: int  # 0-100

    # Component details for UI
    tech_stack_details: Dict[str, Any]
    data_readiness_details: Dict[str, Any]
    team_readiness_details: Dict[str, Any]
    process_maturity_details: Dict[str, Any]

    # Improvement suggestions
    improvement_suggestions: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_score": self.total_score,
            "components": {
                "tech_stack": {
                    "score": self.tech_stack_score,
                    "max": 30,
                    "label": "Tech Stack Openness",
                    "description": "How well your current tools support automation via APIs",
                    **self.tech_stack_details,
                },
                "data_readiness": {
                    "score": self.data_readiness_score,
                    "max": 25,
                    "label": "Data Readiness",
                    "description": "Whether your business data is digital and organized",
                    **self.data_readiness_details,
                },
                "team_readiness": {
                    "score": self.team_readiness_score,
                    "max": 25,
                    "label": "Team Readiness",
                    "description": "Your team's comfort with technology and change",
                    **self.team_readiness_details,
                },
                "process_maturity": {
                    "score": self.process_maturity_score,
                    "max": 20,
                    "label": "Process Maturity",
                    "description": "How documented and consistent your workflows are",
                    **self.process_maturity_details,
                },
            },
            "improvement_suggestions": self.improvement_suggestions,
            "threshold_labels": {
                "70": {"label": "AI Ready", "color": "green"},
                "50": {"label": "Moderate", "color": "amber"},
                "35": {"label": "Developing", "color": "orange"},
                "0": {"label": "Early Stage", "color": "red"},
            },
        }


class AIReadinessCalculator(SyncSkill[AIReadinessBreakdown]):
    """
    Calculate AI readiness score using a transparent formula.

    This skill uses quiz answers and stack assessment data to compute
    a deterministic score that users can understand and act on.
    """

    name = "ai-readiness-calculator"
    description = "Calculate AI readiness score with transparent breakdown"
    version = "1.0.0"

    requires_llm = False  # Pure formula-based

    # Implementation capability weights
    IMPL_CAPABILITY_SCORES = {
        "non_technical": 1,
        "tutorial_follower": 3,
        "automation_user": 6,
        "ai_coder": 8,
        "has_developers": 10,
    }

    # Number of tools as a proxy for digital maturity
    MIN_TOOLS_FOR_FULL_SCORE = 5

    def execute_sync(self, context: SkillContext) -> AIReadinessBreakdown:
        """Calculate AI readiness from context data."""

        answers = context.quiz_answers or {}
        existing_stack = context.existing_stack or []

        # Calculate each component
        tech_stack = self._calculate_tech_stack_score(existing_stack, answers)
        data_readiness = self._calculate_data_readiness_score(answers)
        team_readiness = self._calculate_team_readiness_score(answers)
        process_maturity = self._calculate_process_maturity_score(answers)

        # Calculate total
        total = (
            tech_stack["score"] +
            data_readiness["score"] +
            team_readiness["score"] +
            process_maturity["score"]
        )

        # Generate improvement suggestions
        suggestions = self._generate_suggestions(
            tech_stack, data_readiness, team_readiness, process_maturity
        )

        return AIReadinessBreakdown(
            tech_stack_score=tech_stack["score"],
            data_readiness_score=data_readiness["score"],
            team_readiness_score=team_readiness["score"],
            process_maturity_score=process_maturity["score"],
            total_score=total,
            tech_stack_details=tech_stack["details"],
            data_readiness_details=data_readiness["details"],
            team_readiness_details=team_readiness["details"],
            process_maturity_details=process_maturity["details"],
            improvement_suggestions=suggestions,
        )

    def _calculate_tech_stack_score(
        self,
        existing_stack: List[Dict[str, Any]],
        answers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate tech stack openness score (0-30).

        Based on:
        - Average API score of existing tools (0-5 scale → 0-18 points)
        - Tool integration rating from quiz (1-10 → 0-12 points)
        """
        max_score = 30

        # Component 1: API scores from stack assessment (0-18 points)
        if existing_stack:
            api_scores = [
                tool.get("api_score", 3)
                for tool in existing_stack
                if isinstance(tool.get("api_score"), (int, float))
            ]
            avg_api_score = sum(api_scores) / len(api_scores) if api_scores else 3
            api_points = min(18, int((avg_api_score / 5) * 18))
        else:
            # No stack data - use moderate default
            avg_api_score = 3
            api_points = 11  # Middle ground

        # Component 2: Integration rating from quiz (0-12 points)
        integration_rating = answers.get("integration_issues", 5)
        if isinstance(integration_rating, str):
            try:
                integration_rating = int(integration_rating)
            except ValueError:
                integration_rating = 5
        integration_points = min(12, int((integration_rating / 10) * 12))

        score = min(max_score, api_points + integration_points)

        return {
            "score": score,
            "details": {
                "factors": [
                    f"Tool API scores: {avg_api_score:.1f}/5 avg",
                    f"Integration rating: {integration_rating}/10",
                ],
                "api_average": round(avg_api_score, 1),
                "tools_assessed": len(existing_stack),
            },
        }

    def _calculate_data_readiness_score(
        self,
        answers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate data readiness score (0-25).

        Based on:
        - Manual data entry (YES = -8 points)
        - Number of digital tool categories used (0-17 points)
        """
        max_score = 25

        # Component 1: Manual data entry penalty (-8 points if yes)
        has_manual_entry = answers.get("manual_data_entry", "no")
        if isinstance(has_manual_entry, bool):
            has_manual_entry = "yes" if has_manual_entry else "no"
        manual_penalty = 8 if has_manual_entry.lower() == "yes" else 0

        # Component 2: Digital tool adoption (0-17 points)
        current_tools = answers.get("current_tools", [])
        if isinstance(current_tools, str):
            current_tools = [current_tools]
        tool_count = len(current_tools) if isinstance(current_tools, list) else 0
        # More tool categories = more digitized
        tool_points = min(17, int((tool_count / self.MIN_TOOLS_FOR_FULL_SCORE) * 17))

        score = max(0, min(max_score, tool_points + (17 - manual_penalty)))

        return {
            "score": score,
            "details": {
                "factors": [
                    f"Digital tools: {tool_count} categories",
                    f"Manual data entry: {'Yes (needs improvement)' if manual_penalty > 0 else 'No (good)'}",
                ],
                "has_manual_entry": manual_penalty > 0,
                "tool_categories": tool_count,
            },
        }

    def _calculate_team_readiness_score(
        self,
        answers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate team readiness score (0-25).

        Based on:
        - Technology comfort rating (1-10 → 0-12 points)
        - Implementation capability (0-10 points)
        - AI tools already used (0-3 bonus points)
        """
        max_score = 25

        # Component 1: Tech comfort (0-12 points)
        tech_comfort = answers.get("technology_comfort", 5)
        if isinstance(tech_comfort, str):
            try:
                tech_comfort = int(tech_comfort)
            except ValueError:
                tech_comfort = 5
        comfort_points = min(12, int((tech_comfort / 10) * 12))

        # Component 2: Implementation capability (0-10 points)
        impl_capability = answers.get("implementation_capability", "tutorial_follower")
        capability_value = self.IMPL_CAPABILITY_SCORES.get(impl_capability, 3)
        capability_points = capability_value

        # Component 3: AI tool experience bonus (0-3 points)
        ai_tools = answers.get("ai_tools_used", [])
        if isinstance(ai_tools, str):
            ai_tools = [ai_tools]
        if isinstance(ai_tools, list):
            # Exclude "none" option
            ai_tools_count = len([t for t in ai_tools if t != "none"])
        else:
            ai_tools_count = 0
        ai_bonus = min(3, ai_tools_count)

        score = min(max_score, comfort_points + capability_points + ai_bonus)

        return {
            "score": score,
            "details": {
                "factors": [
                    f"Tech comfort: {tech_comfort}/10",
                    f"Implementation capability: {impl_capability}",
                    f"AI tools used: {ai_tools_count}",
                ],
                "tech_comfort_rating": tech_comfort,
                "capability_level": impl_capability,
                "ai_experience": ai_tools_count > 0,
            },
        }

    def _calculate_process_maturity_score(
        self,
        answers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate process maturity score (0-20).

        Based on:
        - Admin time efficiency (lower hours = more efficient, 0-10 points)
        - Quality issues (NO = +5 points)
        - Process documentation evidence (text answers, 0-5 points)
        """
        max_score = 20

        # Component 1: Admin efficiency (0-10 points)
        # Less time on admin = more mature processes
        admin_hours = answers.get("time_on_admin", 20)
        if isinstance(admin_hours, str):
            try:
                admin_hours = int(admin_hours)
            except ValueError:
                admin_hours = 20
        # 0 hours = 10 points, 40+ hours = 0 points (linear scale)
        efficiency_points = max(0, min(10, 10 - int(admin_hours / 4)))

        # Component 2: Quality consistency (0-5 points)
        has_quality_issues = answers.get("quality_issues", "no")
        if isinstance(has_quality_issues, bool):
            has_quality_issues = "yes" if has_quality_issues else "no"
        quality_points = 0 if has_quality_issues.lower() == "yes" else 5

        # Component 3: Process documentation (0-5 points)
        # Check if main_processes text is substantial (indicates documented processes)
        main_processes = answers.get("main_processes", "")
        if isinstance(main_processes, str):
            # More detailed description = more documented
            doc_points = min(5, len(main_processes) // 50)  # 1 point per 50 chars
        else:
            doc_points = 2  # Default moderate

        score = min(max_score, efficiency_points + quality_points + doc_points)

        return {
            "score": score,
            "details": {
                "factors": [
                    f"Admin hours/week: {admin_hours}",
                    f"Quality issues: {'Yes' if quality_points == 0 else 'No'}",
                    f"Process documentation: {'Detailed' if doc_points >= 4 else 'Basic' if doc_points >= 2 else 'Limited'}",
                ],
                "admin_hours_weekly": admin_hours,
                "has_quality_issues": quality_points == 0,
                "documentation_level": "detailed" if doc_points >= 4 else "basic" if doc_points >= 2 else "limited",
            },
        }

    def _generate_suggestions(
        self,
        tech_stack: Dict,
        data_readiness: Dict,
        team_readiness: Dict,
        process_maturity: Dict,
    ) -> List[str]:
        """Generate actionable improvement suggestions based on scores."""
        suggestions = []

        # Tech stack improvements
        if tech_stack["score"] < 20:
            details = tech_stack["details"]
            if details.get("api_average", 3) < 3.5:
                suggestions.append(
                    "Consider tools with better API support for future automation"
                )
            if details.get("tools_assessed", 0) == 0:
                suggestions.append(
                    "Add your current software stack to get personalized recommendations"
                )

        # Data readiness improvements
        if data_readiness["score"] < 18:
            details = data_readiness["details"]
            if details.get("has_manual_entry"):
                suggestions.append(
                    "Reduce manual data entry by connecting your tools with Make or Zapier"
                )
            if details.get("tool_categories", 0) < 3:
                suggestions.append(
                    "Digitize more processes by adopting tools for key business functions"
                )

        # Team readiness improvements
        if team_readiness["score"] < 18:
            details = team_readiness["details"]
            if details.get("tech_comfort_rating", 5) < 6:
                suggestions.append(
                    "Build team confidence with small automation wins before larger projects"
                )
            if not details.get("ai_experience"):
                suggestions.append(
                    "Start using AI tools like ChatGPT for simple tasks to build familiarity"
                )

        # Process maturity improvements
        if process_maturity["score"] < 14:
            details = process_maturity["details"]
            if details.get("has_quality_issues"):
                suggestions.append(
                    "Address quality inconsistencies before automating to avoid scaling problems"
                )
            if details.get("documentation_level") == "limited":
                suggestions.append(
                    "Document your key workflows - automation requires clear process definitions"
                )
            if details.get("admin_hours_weekly", 0) > 30:
                suggestions.append(
                    "High admin time suggests quick-win automation opportunities"
                )

        # If score is already good
        if not suggestions:
            suggestions.append(
                "Strong foundation! Focus on high-impact automation opportunities"
            )

        return suggestions[:4]  # Max 4 suggestions


# Convenience function for direct calculation
def calculate_ai_readiness(
    quiz_answers: Dict[str, Any],
    existing_stack: Optional[List[Dict[str, Any]]] = None,
    industry: str = "general",
) -> Dict[str, Any]:
    """
    Calculate AI readiness score directly without skill context.

    Args:
        quiz_answers: Dictionary of quiz answer values
        existing_stack: Optional list of tools with api_score
        industry: Industry slug

    Returns:
        Dictionary with total_score and component breakdown
    """
    context = SkillContext(
        industry=industry,
        quiz_answers=quiz_answers,
        existing_stack=existing_stack or [],
    )

    calculator = AIReadinessCalculator()
    result = calculator.execute_sync(context)
    return result.to_dict()


# For skill discovery
__all__ = ["AIReadinessCalculator", "AIReadinessBreakdown", "calculate_ai_readiness"]
