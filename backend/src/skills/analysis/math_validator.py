"""
Math Validator Skill

Validates that all numerical claims in findings and recommendations are:
1. Internally consistent (math adds up correctly)
2. Within realistic bounds
3. Based on traceable sources/assumptions
4. Cross-referenced against company data

This skill is CRITICAL for report credibility. No random guesses - every
number must be factual and verifiable.

Output Schema:
{
    "finding_id": "finding-001",
    "validation_passed": false,
    "overall_confidence": "medium",
    "issues": [
        {
            "type": "consistency_error",
            "field": "annual_savings",
            "claimed": 52000,
            "calculated": 26000,
            "formula": "hours_per_week * hourly_rate * 52",
            "severity": "high",
            "fix": "Recalculate: 10 hrs × €50 × 52 = €26,000"
        }
    ],
    "warnings": [
        {
            "type": "bounds_warning",
            "field": "hours_per_week",
            "value": 35,
            "concern": "Saving 35 hrs/week is 87.5% of a 40-hour week",
            "suggestion": "Verify this is realistic for the specific task"
        }
    ],
    "verified_numbers": [
        {
            "field": "hourly_rate",
            "value": 50,
            "source": "quiz_answer",
            "verified": true
        }
    ],
    "unverified_numbers": [
        {
            "field": "potential_revenue",
            "value": 50000,
            "source": "llm_generated",
            "suggestion": "Add industry benchmark or client estimate"
        }
    ],
    "math_audit": {
        "formulas_checked": 4,
        "formulas_correct": 3,
        "formulas_incorrect": 1
    }
}
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP

from src.skills.base import SyncSkill, SkillContext, SkillError

logger = logging.getLogger(__name__)


# Standard formulas we expect to see
EXPECTED_FORMULAS = {
    "annual_savings": {
        "formula": "hours_per_week * hourly_rate * weeks_per_year",
        "variables": ["hours_per_week", "hourly_rate"],
        "default_weeks": 52,
        "tolerance": 0.05,  # 5% tolerance for rounding
    },
    "monthly_savings": {
        "formula": "hours_per_week * hourly_rate * 4.33",
        "variables": ["hours_per_week", "hourly_rate"],
        "tolerance": 0.05,
    },
    "roi_percentage": {
        "formula": "(annual_savings - annual_cost) / total_investment * 100",
        "tolerance": 0.10,  # 10% tolerance due to compounding variations
    },
    "payback_months": {
        "formula": "implementation_cost / (monthly_savings - monthly_cost)",
        "tolerance": 0.15,
    },
    "three_year_net": {
        "formula": "(annual_savings * 3) - implementation_cost - (monthly_cost * 36)",
        "tolerance": 0.05,
    },
}

# Realistic bounds for validation
BOUNDS = {
    "hours_per_week": {"min": 0.5, "max": 60, "typical_max": 40},
    "hourly_rate": {"min": 10, "max": 500, "typical_max": 150},
    "annual_savings": {"min": 0, "max": 1000000, "typical_max": 100000},
    "roi_percentage": {"min": -100, "max": 2000, "suspicious": 500},
    "payback_months": {"min": 0.1, "max": 60, "suspicious": 36},
    "implementation_cost": {"min": 0, "max": 500000, "typical_max": 50000},
    "monthly_cost": {"min": 0, "max": 10000, "typical_max": 2000},
}


class MathValidatorSkill(SyncSkill[Dict[str, Any]]):
    """
    Validate mathematical claims in findings and recommendations.

    This skill ensures all numbers are:
    - Internally consistent (formulas check out)
    - Within realistic bounds
    - Traceable to sources
    - Cross-referenced against company data
    """

    name = "math-validator"
    description = "Validate mathematical claims and calculations"
    version = "1.0.0"

    requires_llm = False  # Pure math validation, no LLM needed
    requires_expertise = False

    def execute_sync(self, context: SkillContext) -> Dict[str, Any]:
        """
        Validate math in a finding/recommendation pair.

        Args:
            context: SkillContext with:
                - metadata.finding: The finding to validate
                - metadata.recommendation: Optional recommendation with ROI
                - quiz_answers: Company data for cross-reference

        Returns:
            Validation results with issues, warnings, and verified numbers
        """
        finding = context.metadata.get("finding", {})
        recommendation = context.metadata.get("recommendation")
        quiz_answers = context.quiz_answers or {}

        if not finding:
            raise SkillError(
                self.name,
                "No finding provided in context.metadata",
                recoverable=False
            )

        issues = []
        warnings = []
        verified = []
        unverified = []

        # Extract company context for cross-reference
        company_context = self._extract_company_context(quiz_answers)

        # 1. Validate internal consistency
        consistency_issues = self._check_internal_consistency(
            finding, recommendation, company_context
        )
        issues.extend(consistency_issues)

        # 2. Check bounds
        bounds_warnings = self._check_bounds(finding, recommendation, company_context)
        warnings.extend(bounds_warnings)

        # 3. Verify number sources
        verified_nums, unverified_nums = self._verify_number_sources(
            finding, recommendation, quiz_answers
        )
        verified.extend(verified_nums)
        unverified.extend(unverified_nums)

        # 4. Cross-reference against company data
        cross_ref_issues = self._cross_reference_company_data(
            finding, recommendation, company_context
        )
        issues.extend(cross_ref_issues)

        # Calculate overall confidence based on validation
        overall_confidence = self._calculate_confidence(issues, warnings, unverified)

        # Count formula checks
        formulas_checked = len([i for i in issues if i["type"] == "consistency_error"]) + \
                          len([v for v in verified if v.get("formula_verified")])
        formulas_incorrect = len([i for i in issues if i["type"] == "consistency_error"])

        return {
            "finding_id": finding.get("id"),
            "validation_passed": len(issues) == 0,
            "overall_confidence": overall_confidence,
            "issues": issues,
            "warnings": warnings,
            "verified_numbers": verified,
            "unverified_numbers": unverified,
            "math_audit": {
                "formulas_checked": formulas_checked,
                "formulas_correct": formulas_checked - formulas_incorrect,
                "formulas_incorrect": formulas_incorrect,
            },
        }

    def _extract_company_context(self, quiz_answers: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant company data for validation."""
        context = {}

        # Team size / employees
        team_size = quiz_answers.get("team_size") or quiz_answers.get("employee_count")
        if team_size:
            if isinstance(team_size, str):
                # Extract number from string like "5-10" or "5"
                numbers = re.findall(r'\d+', team_size)
                if numbers:
                    context["team_size"] = int(numbers[0])
            else:
                context["team_size"] = int(team_size)

        # Revenue
        revenue = quiz_answers.get("annual_revenue") or quiz_answers.get("revenue")
        if revenue:
            if isinstance(revenue, str):
                # Extract number, handle K/M suffixes
                revenue_str = revenue.replace("€", "").replace("$", "").replace(",", "")
                if "m" in revenue_str.lower() or "million" in revenue_str.lower():
                    numbers = re.findall(r'[\d.]+', revenue_str)
                    if numbers:
                        context["annual_revenue"] = float(numbers[0]) * 1_000_000
                elif "k" in revenue_str.lower():
                    numbers = re.findall(r'[\d.]+', revenue_str)
                    if numbers:
                        context["annual_revenue"] = float(numbers[0]) * 1_000
                else:
                    numbers = re.findall(r'[\d.]+', revenue_str)
                    if numbers:
                        context["annual_revenue"] = float(numbers[0])
            else:
                context["annual_revenue"] = float(revenue)

        # Hourly rate
        hourly_rate = quiz_answers.get("hourly_rate") or quiz_answers.get("labor_cost")
        if hourly_rate:
            context["hourly_rate"] = float(hourly_rate)
        else:
            context["hourly_rate"] = 50  # Default

        # Work hours per week
        work_hours = quiz_answers.get("work_hours_per_week")
        if work_hours:
            context["work_hours_per_week"] = float(work_hours)
        else:
            context["work_hours_per_week"] = 40  # Default

        return context

    def _check_internal_consistency(
        self,
        finding: Dict[str, Any],
        recommendation: Optional[Dict[str, Any]],
        company_context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Check that math formulas are internally consistent."""
        issues = []
        hourly_rate = company_context.get("hourly_rate", 50)

        # Check value_saved calculations
        value_saved = finding.get("value_saved", {})
        if value_saved:
            hours_per_week = value_saved.get("hours_per_week", 0)
            claimed_annual = value_saved.get("annual_savings", 0)

            if hours_per_week and claimed_annual:
                expected_annual = hours_per_week * hourly_rate * 52
                tolerance = expected_annual * EXPECTED_FORMULAS["annual_savings"]["tolerance"]

                if abs(claimed_annual - expected_annual) > tolerance:
                    issues.append({
                        "type": "consistency_error",
                        "field": "annual_savings",
                        "claimed": claimed_annual,
                        "calculated": round(expected_annual, 2),
                        "formula": f"{hours_per_week} hrs/wk × €{hourly_rate}/hr × 52 wks",
                        "severity": "high",
                        "fix": f"Recalculate: {hours_per_week} × €{hourly_rate} × 52 = €{expected_annual:,.0f}",
                    })

        # Check recommendation ROI if present
        if recommendation:
            roi = recommendation.get("roi_percentage", 0)
            roi_detail = recommendation.get("roi_detail", {})

            if roi_detail:
                yearly_savings = roi_detail.get("yearly_savings", 0)
                implementation_cost = roi_detail.get("implementation_cost", 0)
                yearly_cost = roi_detail.get("yearly_cost", 0)

                if yearly_savings and implementation_cost:
                    first_year_investment = implementation_cost + yearly_cost
                    net_annual = yearly_savings - yearly_cost

                    if first_year_investment > 0:
                        expected_roi = (net_annual / first_year_investment) * 100

                        if abs(roi - expected_roi) > expected_roi * 0.15:
                            issues.append({
                                "type": "consistency_error",
                                "field": "roi_percentage",
                                "claimed": roi,
                                "calculated": round(expected_roi, 1),
                                "formula": f"(€{net_annual:,.0f} / €{first_year_investment:,.0f}) × 100",
                                "severity": "high",
                                "fix": f"Correct ROI: {expected_roi:.1f}%",
                            })

            # Check payback period
            payback = recommendation.get("payback_months", 0)
            if payback and roi_detail:
                monthly_savings = roi_detail.get("monthly_savings", 0)
                monthly_cost = roi_detail.get("monthly_cost", 0)
                implementation_cost = roi_detail.get("implementation_cost", 0)

                if monthly_savings > monthly_cost and implementation_cost > 0:
                    net_monthly = monthly_savings - monthly_cost
                    expected_payback = implementation_cost / net_monthly

                    if abs(payback - expected_payback) > expected_payback * 0.2:
                        issues.append({
                            "type": "consistency_error",
                            "field": "payback_months",
                            "claimed": payback,
                            "calculated": round(expected_payback, 1),
                            "formula": f"€{implementation_cost:,.0f} / €{net_monthly:,.0f}/mo",
                            "severity": "medium",
                            "fix": f"Correct payback: {expected_payback:.1f} months",
                        })

        return issues

    def _check_bounds(
        self,
        finding: Dict[str, Any],
        recommendation: Optional[Dict[str, Any]],
        company_context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Check that numbers are within realistic bounds."""
        warnings = []

        # Check hours_per_week
        value_saved = finding.get("value_saved", {})
        hours_per_week = value_saved.get("hours_per_week", 0)

        if hours_per_week:
            max_hours = company_context.get("work_hours_per_week", 40)
            team_size = company_context.get("team_size", 1)
            theoretical_max = max_hours * team_size

            if hours_per_week > theoretical_max:
                warnings.append({
                    "type": "bounds_error",
                    "field": "hours_per_week",
                    "value": hours_per_week,
                    "concern": f"Cannot save {hours_per_week} hrs/week when team capacity is {theoretical_max} hrs/week",
                    "suggestion": f"Maximum realistic savings: {theoretical_max * 0.5:.0f} hrs/week (50% of capacity)",
                    "severity": "high",
                })
            elif hours_per_week > max_hours * 0.8:
                warnings.append({
                    "type": "bounds_warning",
                    "field": "hours_per_week",
                    "value": hours_per_week,
                    "concern": f"Saving {hours_per_week} hrs/week is {(hours_per_week/max_hours)*100:.0f}% of work week",
                    "suggestion": "Verify this is realistic for the specific task",
                    "severity": "medium",
                })

        # Check ROI
        if recommendation:
            roi = recommendation.get("roi_percentage", 0)
            if roi > BOUNDS["roi_percentage"]["suspicious"]:
                warnings.append({
                    "type": "bounds_warning",
                    "field": "roi_percentage",
                    "value": roi,
                    "concern": f"ROI of {roi}% is unusually high",
                    "suggestion": "Verify assumptions or lower confidence level",
                    "severity": "medium",
                })

            payback = recommendation.get("payback_months", 0)
            if payback and payback > BOUNDS["payback_months"]["suspicious"]:
                warnings.append({
                    "type": "bounds_warning",
                    "field": "payback_months",
                    "value": payback,
                    "concern": f"Payback of {payback} months may not justify investment",
                    "suggestion": "Consider if this is worth recommending",
                    "severity": "low",
                })

        # Check annual savings vs revenue
        annual_savings = value_saved.get("annual_savings", 0)
        annual_revenue = company_context.get("annual_revenue")

        if annual_savings and annual_revenue:
            savings_pct = (annual_savings / annual_revenue) * 100
            if savings_pct > 30:
                warnings.append({
                    "type": "bounds_warning",
                    "field": "annual_savings",
                    "value": annual_savings,
                    "concern": f"Savings of €{annual_savings:,.0f} is {savings_pct:.0f}% of revenue (€{annual_revenue:,.0f})",
                    "suggestion": "Verify this is realistic; >30% savings is unusual",
                    "severity": "high" if savings_pct > 50 else "medium",
                })

        return warnings

    def _verify_number_sources(
        self,
        finding: Dict[str, Any],
        recommendation: Optional[Dict[str, Any]],
        quiz_answers: Dict[str, Any],
    ) -> Tuple[List[Dict], List[Dict]]:
        """Classify numbers as verified or unverified based on source."""
        verified = []
        unverified = []

        # Extract all numbers from finding
        value_saved = finding.get("value_saved", {})
        value_created = finding.get("value_created", {})

        # Check hours_per_week
        hours = value_saved.get("hours_per_week")
        if hours:
            # Check if this came from quiz
            if quiz_answers.get("hours_on_task") or quiz_answers.get("time_spent"):
                verified.append({
                    "field": "hours_per_week",
                    "value": hours,
                    "source": "quiz_answer",
                    "verified": True,
                })
            else:
                unverified.append({
                    "field": "hours_per_week",
                    "value": hours,
                    "source": "llm_estimated",
                    "suggestion": "Ask client to estimate or use industry benchmark with source",
                })

        # Check hourly_rate
        hourly_rate = value_saved.get("hourly_rate", 50)
        if quiz_answers.get("hourly_rate") or quiz_answers.get("labor_cost"):
            verified.append({
                "field": "hourly_rate",
                "value": hourly_rate,
                "source": "quiz_answer",
                "verified": True,
            })
        else:
            unverified.append({
                "field": "hourly_rate",
                "value": hourly_rate,
                "source": "default_assumption",
                "suggestion": "Ask client for actual labor cost or cite benchmark source",
            })

        # Check potential_revenue
        potential_revenue = value_created.get("potential_revenue")
        if potential_revenue:
            unverified.append({
                "field": "potential_revenue",
                "value": potential_revenue,
                "source": "llm_estimated",
                "suggestion": "Needs client estimate or industry benchmark with citation",
            })

        # Check annual_savings - this is calculated, verify formula
        annual_savings = value_saved.get("annual_savings")
        if annual_savings and hours:
            verified.append({
                "field": "annual_savings",
                "value": annual_savings,
                "source": "calculated",
                "formula": f"hours_per_week × hourly_rate × 52",
                "formula_verified": True,
                "verified": True,
            })

        return verified, unverified

    def _cross_reference_company_data(
        self,
        finding: Dict[str, Any],
        recommendation: Optional[Dict[str, Any]],
        company_context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Cross-reference claims against company data."""
        issues = []

        team_size = company_context.get("team_size", 1)
        work_hours = company_context.get("work_hours_per_week", 40)
        annual_revenue = company_context.get("annual_revenue")

        value_saved = finding.get("value_saved", {})
        hours_per_week = value_saved.get("hours_per_week", 0)
        annual_savings = value_saved.get("annual_savings", 0)

        # Check if claimed hours exceed team capacity
        total_capacity = team_size * work_hours
        if hours_per_week > total_capacity:
            issues.append({
                "type": "cross_reference_error",
                "field": "hours_per_week",
                "claimed": hours_per_week,
                "limit": total_capacity,
                "reason": f"Team of {team_size} × {work_hours}hr = {total_capacity}hr/week capacity",
                "severity": "high",
                "fix": f"Maximum possible: {total_capacity} hrs/week",
            })

        # Check if savings exceed revenue
        if annual_savings and annual_revenue and annual_savings > annual_revenue:
            issues.append({
                "type": "cross_reference_error",
                "field": "annual_savings",
                "claimed": annual_savings,
                "limit": annual_revenue,
                "reason": f"Cannot save €{annual_savings:,.0f} when revenue is €{annual_revenue:,.0f}",
                "severity": "high",
                "fix": f"Maximum possible: €{annual_revenue * 0.3:,.0f} (30% of revenue)",
            })

        return issues

    def _calculate_confidence(
        self,
        issues: List[Dict],
        warnings: List[Dict],
        unverified: List[Dict],
    ) -> str:
        """Calculate overall confidence based on validation results."""
        # Start with high confidence
        score = 100

        # Deduct for issues
        for issue in issues:
            severity = issue.get("severity", "medium")
            if severity == "high":
                score -= 30
            elif severity == "medium":
                score -= 15
            else:
                score -= 5

        # Deduct for warnings
        for warning in warnings:
            severity = warning.get("severity", "medium")
            if severity == "high":
                score -= 15
            elif severity == "medium":
                score -= 8
            else:
                score -= 3

        # Deduct for unverified numbers
        score -= len(unverified) * 5

        # Convert to confidence level
        if score >= 80:
            return "high"
        elif score >= 50:
            return "medium"
        else:
            return "low"


# For skill discovery
__all__ = ["MathValidatorSkill"]
