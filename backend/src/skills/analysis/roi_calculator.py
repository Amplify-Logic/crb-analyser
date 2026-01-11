"""
ROI Calculator Skill

Calculates ROI with transparent assumptions and sensitivity analysis.

This skill:
1. Takes a finding + recommendation + company context
2. Calculates time and cost savings
3. Applies confidence adjustments
4. Generates sensitivity analysis (best/worst case)
5. Tracks all assumptions explicitly

Output Schema:
{
    "roi_percentage": 180,
    "roi_confidence_adjusted": 153,
    "payback_months": 4,
    "confidence": "medium",
    "time_savings": {
        "hours_per_week": 10,
        "hours_per_month": 43,
        "hours_per_year": 520
    },
    "financial_impact": {
        "monthly_savings": 2150,
        "yearly_savings": 25800,
        "implementation_cost": 5000,
        "monthly_cost": 150,
        "three_year_net": 67200
    },
    "sensitivity": {
        "best_case": {"roi": 250, "payback_months": 2},
        "expected": {"roi": 180, "payback_months": 4},
        "worst_case": {"roi": 95, "payback_months": 8}
    },
    "assumptions": [
        {
            "statement": "Hourly labor cost is €50",
            "source": "industry_benchmark",
            "sensitivity": "high",
            "if_wrong": "ROI varies by 20-40%"
        }
    ],
    "calculation_breakdown": "Step-by-step explanation"
}
"""

import logging
from typing import Dict, Any, List, Optional

from src.skills.base import LLMSkill, SkillContext, SkillError

logger = logging.getLogger(__name__)


# Confidence adjustment factors (from CLAUDE.md)
CONFIDENCE_FACTORS = {
    "high": 1.0,
    "medium": 0.85,
    "low": 0.70
}

# Default assumptions with sources
DEFAULT_ASSUMPTIONS = {
    "hourly_rate": {
        "value": 50,
        "currency": "EUR",
        "statement": "Hourly labor cost is €50",
        "source": "industry_benchmark",
        "source_detail": "European SMB labor cost benchmarks 2024",
        "sensitivity": "high",
        "if_wrong": "ROI calculations could vary by 20-40%"
    },
    "work_weeks_per_year": {
        "value": 48,
        "statement": "48 working weeks per year (excluding holidays)",
        "source": "default_value",
        "sensitivity": "low"
    },
    "hours_per_week": {
        "value": 40,
        "statement": "40-hour work week",
        "source": "default_value",
        "sensitivity": "low"
    },
    "automation_efficiency": {
        "value": 0.70,
        "statement": "70% of identified time can actually be automated",
        "source": "industry_benchmark",
        "source_detail": "Automation efficiency meta-analysis",
        "sensitivity": "high",
        "if_wrong": "Actual savings may be 50-90% of estimate"
    },
    "adoption_rate": {
        "value": 0.80,
        "statement": "80% team adoption within 3 months",
        "source": "industry_benchmark",
        "source_detail": "Software adoption curve studies",
        "sensitivity": "medium",
        "if_wrong": "Benefits may take longer to realize"
    },
    "implementation_buffer": {
        "value": 1.5,
        "statement": "1.5x buffer on implementation time estimates",
        "source": "industry_benchmark",
        "source_detail": "Vendor estimate accuracy studies",
        "sensitivity": "medium"
    }
}


class ROICalculatorSkill(LLMSkill[Dict[str, Any]]):
    """
    Calculate ROI with transparent assumptions and sensitivity analysis.

    This skill combines rule-based calculations with LLM-powered
    estimation for qualitative factors. All assumptions are tracked
    and disclosed.
    """

    name = "roi-calculator"
    description = "Calculate ROI with transparent assumptions"
    version = "1.0.0"

    requires_llm = True
    requires_expertise = False  # Helpful but not required

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Calculate ROI for a finding/recommendation pair.

        Args:
            context: SkillContext with:
                - metadata.finding: The finding being addressed
                - metadata.recommendation: The proposed solution
                - metadata.company_context: Company size, budget, etc.
                - quiz_answers: For company-specific data
                - expertise: Industry patterns for calibration

        Returns:
            ROI calculation with assumptions and sensitivity
        """
        finding = context.metadata.get("finding", {})
        recommendation = context.metadata.get("recommendation", {})
        company_context = context.metadata.get("company_context", {})

        if not finding:
            raise SkillError(
                self.name,
                "No finding provided in context.metadata",
                recoverable=False
            )

        # Get company-specific values from quiz answers
        company_data = self._extract_company_data(context.quiz_answers, company_context)

        # Calculate time savings
        time_savings = await self._estimate_time_savings(
            finding=finding,
            recommendation=recommendation,
            company_data=company_data,
            industry=context.industry,
        )

        # Calculate financial impact
        financial = self._calculate_financials(
            time_savings=time_savings,
            recommendation=recommendation,
            company_data=company_data,
        )

        # Calculate ROI metrics
        roi_metrics = self._calculate_roi_metrics(financial, finding)

        # Generate sensitivity analysis
        sensitivity = self._calculate_sensitivity(
            base_metrics=roi_metrics,
            time_savings=time_savings,
            financial=financial,
        )

        # Build assumptions list
        assumptions = self._build_assumptions_list(company_data)

        # Generate calculation breakdown
        breakdown = self._generate_breakdown(
            time_savings=time_savings,
            financial=financial,
            roi_metrics=roi_metrics,
            company_data=company_data,
        )

        return {
            "roi_percentage": roi_metrics["roi_raw"],
            "roi_confidence_adjusted": roi_metrics["roi_adjusted"],
            "payback_months": roi_metrics["payback_months"],
            "confidence": finding.get("confidence", "medium"),
            "time_savings": time_savings,
            "financial_impact": financial,
            "sensitivity": sensitivity,
            "assumptions": assumptions,
            "calculation_breakdown": breakdown,
        }

    def _extract_company_data(
        self,
        quiz_answers: Optional[Dict[str, Any]],
        company_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract company-specific values, falling back to defaults."""
        answers = quiz_answers or {}

        # Try to get from quiz answers first, then company context, then defaults
        hourly_rate = (
            answers.get("hourly_rate") or
            answers.get("labor_cost") or
            company_context.get("hourly_rate") or
            DEFAULT_ASSUMPTIONS["hourly_rate"]["value"]
        )

        team_size_raw = (
            answers.get("team_size") or
            answers.get("employee_count") or
            company_context.get("team_size") or
            5  # Default for SMB
        )

        # Parse team_size - handle range strings like "11-25" or "11-50"
        team_size = self._parse_team_size(team_size_raw)

        # Determine if values came from actual data or assumptions
        hourly_rate_source = "quiz_data" if answers.get("hourly_rate") else "assumption"
        team_size_source = "quiz_data" if answers.get("team_size") else "assumption"

        return {
            "hourly_rate": float(hourly_rate),
            "hourly_rate_source": hourly_rate_source,
            "team_size": team_size,
            "team_size_source": team_size_source,
            "work_weeks": DEFAULT_ASSUMPTIONS["work_weeks_per_year"]["value"],
            "automation_efficiency": DEFAULT_ASSUMPTIONS["automation_efficiency"]["value"],
            "adoption_rate": DEFAULT_ASSUMPTIONS["adoption_rate"]["value"],
        }

    def _parse_team_size(self, value: Any) -> int:
        """Parse team size from various formats (int, string, range string).

        Handles formats like:
        - 25 (int)
        - "25" (string)
        - "11-25" (range string - uses midpoint)
        - "11-50" (range string - uses midpoint)
        """
        if isinstance(value, int):
            return value

        if isinstance(value, str):
            # Check for range format like "11-25" or "11-50"
            if "-" in value:
                try:
                    parts = value.split("-")
                    if len(parts) == 2:
                        low = int(parts[0].strip())
                        high = int(parts[1].strip())
                        return (low + high) // 2  # Use midpoint
                except (ValueError, IndexError):
                    pass

            # Try direct int conversion
            try:
                return int(value)
            except ValueError:
                pass

        # Default fallback
        return 5

    async def _estimate_time_savings(
        self,
        finding: Dict[str, Any],
        recommendation: Dict[str, Any],
        company_data: Dict[str, Any],
        industry: str,
    ) -> Dict[str, Any]:
        """Estimate time savings using LLM for qualitative assessment."""
        # Check if finding already has time estimate
        existing_hours = finding.get("hours_per_week") or finding.get("time_hours_per_week")
        if existing_hours:
            hours_per_week = float(existing_hours) * company_data["automation_efficiency"]
        else:
            # Use LLM to estimate
            hours_per_week = await self._llm_estimate_hours(finding, recommendation, industry)

        # Apply adoption rate
        effective_hours = hours_per_week * company_data["adoption_rate"]

        return {
            "hours_per_week": round(effective_hours, 1),
            "hours_per_month": round(effective_hours * 4.33, 1),
            "hours_per_year": round(effective_hours * company_data["work_weeks"], 1),
            "raw_hours_before_efficiency": hours_per_week / company_data["automation_efficiency"] if company_data["automation_efficiency"] else 0,
            "efficiency_factor_applied": company_data["automation_efficiency"],
            "adoption_rate_applied": company_data["adoption_rate"],
        }

    async def _llm_estimate_hours(
        self,
        finding: Dict[str, Any],
        recommendation: Dict[str, Any],
        industry: str,
    ) -> float:
        """Use LLM to estimate hours saved when not provided."""
        prompt = f"""Estimate weekly hours saved by implementing this solution.

FINDING:
Title: {finding.get('title', 'Unknown')}
Description: {finding.get('description', '')}
Category: {finding.get('category', 'efficiency')}

RECOMMENDATION:
Title: {recommendation.get('title', 'Unknown')}
Approach: {recommendation.get('our_recommendation', 'off_the_shelf')}

INDUSTRY: {industry}

Provide a conservative estimate of hours saved per week for a typical SMB (5-20 employees).

Return ONLY a JSON object:
{{"hours_per_week": <number between 1 and 40>, "reasoning": "<brief explanation>"}}"""

        try:
            result = await self.call_llm_json(
                prompt=prompt,
                system="You are an automation efficiency expert. Provide realistic, conservative estimates."
            )
            return min(40, max(1, float(result.get("hours_per_week", 5))))
        except Exception as e:
            logger.warning(f"LLM hours estimation failed: {e}")
            return 5.0  # Conservative default

    def _calculate_financials(
        self,
        time_savings: Dict[str, Any],
        recommendation: Dict[str, Any],
        company_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculate financial impact from time savings."""
        hourly_rate = company_data["hourly_rate"]

        # Monthly and yearly savings from time
        monthly_savings = time_savings["hours_per_month"] * hourly_rate
        yearly_savings = time_savings["hours_per_year"] * hourly_rate

        # Get costs from recommendation
        options = recommendation.get("options", {})
        our_rec = recommendation.get("our_recommendation", "off_the_shelf")

        if our_rec == "custom_solution":
            option = options.get("custom_solution", {})
            cost_range = option.get("estimated_cost", {})
            implementation_cost = (cost_range.get("min", 5000) + cost_range.get("max", 15000)) / 2
            monthly_cost = option.get("monthly_running_cost", 50)
        elif our_rec == "best_in_class":
            option = options.get("best_in_class", {})
            implementation_cost = option.get("implementation_cost", 2000)
            monthly_cost = option.get("monthly_cost", 200)
        else:  # off_the_shelf
            option = options.get("off_the_shelf", {})
            implementation_cost = option.get("implementation_cost", 500)
            monthly_cost = option.get("monthly_cost", 50)

        # Three-year projection
        three_year_gross = yearly_savings * 3
        three_year_costs = implementation_cost + (monthly_cost * 36)
        three_year_net = three_year_gross - three_year_costs

        return {
            "monthly_savings": round(monthly_savings, 2),
            "yearly_savings": round(yearly_savings, 2),
            "implementation_cost": round(implementation_cost, 2),
            "monthly_cost": round(monthly_cost, 2),
            "yearly_cost": round(monthly_cost * 12, 2),
            "three_year_gross_savings": round(three_year_gross, 2),
            "three_year_total_cost": round(three_year_costs, 2),
            "three_year_net": round(three_year_net, 2),
        }

    def _calculate_roi_metrics(
        self,
        financial: Dict[str, Any],
        finding: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculate ROI percentage and payback period."""
        yearly_savings = financial["yearly_savings"]
        yearly_cost = financial["yearly_cost"]
        implementation_cost = financial["implementation_cost"]

        # Net annual benefit
        net_annual = yearly_savings - yearly_cost

        # Total first year investment
        first_year_investment = implementation_cost + yearly_cost

        # ROI calculation
        if first_year_investment > 0:
            roi_raw = ((net_annual / first_year_investment) * 100)
        else:
            roi_raw = 0

        # Apply confidence adjustment
        confidence = finding.get("confidence", "medium").lower()
        factor = CONFIDENCE_FACTORS.get(confidence, 0.85)
        roi_adjusted = roi_raw * factor

        # Payback period in months
        if net_annual > 0:
            payback_months = (implementation_cost / (net_annual / 12))
        else:
            payback_months = 999  # Never pays back

        return {
            "roi_raw": round(roi_raw, 0),
            "roi_adjusted": round(roi_adjusted, 0),
            "confidence_factor": factor,
            "payback_months": round(min(payback_months, 60), 1),  # Cap at 5 years
            "net_annual_benefit": round(net_annual, 2),
        }

    def _calculate_sensitivity(
        self,
        base_metrics: Dict[str, Any],
        time_savings: Dict[str, Any],
        financial: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculate best/worst case scenarios."""
        base_roi = base_metrics["roi_raw"]
        base_payback = base_metrics["payback_months"]

        # Best case: 130% of estimated savings, 80% of costs
        best_case_roi = base_roi * 1.4
        best_case_payback = base_payback * 0.6

        # Worst case: 60% of estimated savings, 120% of costs
        worst_case_roi = base_roi * 0.5
        worst_case_payback = base_payback * 2.0

        return {
            "best_case": {
                "roi": round(best_case_roi, 0),
                "payback_months": round(max(1, best_case_payback), 1),
                "scenario": "Higher adoption, faster implementation"
            },
            "expected": {
                "roi": round(base_roi, 0),
                "payback_months": round(base_payback, 1),
                "scenario": "Base case with standard assumptions"
            },
            "worst_case": {
                "roi": round(max(0, worst_case_roi), 0),
                "payback_months": round(min(60, worst_case_payback), 1),
                "scenario": "Lower adoption, implementation delays"
            }
        }

    def _build_assumptions_list(
        self,
        company_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Build list of assumptions used in calculation."""
        assumptions = []

        # Hourly rate assumption
        if company_data["hourly_rate_source"] == "assumption":
            assumptions.append({
                **DEFAULT_ASSUMPTIONS["hourly_rate"],
                "value": company_data["hourly_rate"]
            })

        # Always include these assumptions
        assumptions.append({
            **DEFAULT_ASSUMPTIONS["automation_efficiency"],
            "value": company_data["automation_efficiency"]
        })
        assumptions.append({
            **DEFAULT_ASSUMPTIONS["adoption_rate"],
            "value": company_data["adoption_rate"]
        })
        assumptions.append(DEFAULT_ASSUMPTIONS["work_weeks_per_year"])

        return assumptions

    def _generate_breakdown(
        self,
        time_savings: Dict[str, Any],
        financial: Dict[str, Any],
        roi_metrics: Dict[str, Any],
        company_data: Dict[str, Any],
    ) -> str:
        """Generate human-readable calculation breakdown."""
        return f"""ROI Calculation Breakdown:

1. TIME SAVINGS
   - Raw hours identified: {time_savings['raw_hours_before_efficiency']:.1f} hrs/week
   - After automation efficiency ({company_data['automation_efficiency']*100:.0f}%): {time_savings['hours_per_week']:.1f} hrs/week
   - Monthly: {time_savings['hours_per_month']:.1f} hours
   - Yearly: {time_savings['hours_per_year']:.1f} hours

2. FINANCIAL VALUE
   - Hourly rate: €{company_data['hourly_rate']:.0f}
   - Monthly savings: €{financial['monthly_savings']:,.0f}
   - Yearly savings: €{financial['yearly_savings']:,.0f}

3. COSTS
   - Implementation: €{financial['implementation_cost']:,.0f}
   - Monthly ongoing: €{financial['monthly_cost']:,.0f}
   - Yearly ongoing: €{financial['yearly_cost']:,.0f}

4. ROI CALCULATION
   - Net annual benefit: €{roi_metrics['net_annual_benefit']:,.0f}
   - First year investment: €{financial['implementation_cost'] + financial['yearly_cost']:,.0f}
   - ROI: {roi_metrics['roi_raw']:.0f}%
   - Confidence-adjusted ROI: {roi_metrics['roi_adjusted']:.0f}% (factor: {roi_metrics['confidence_factor']})
   - Payback period: {roi_metrics['payback_months']:.1f} months

5. THREE-YEAR PROJECTION
   - Gross savings: €{financial['three_year_gross_savings']:,.0f}
   - Total costs: €{financial['three_year_total_cost']:,.0f}
   - Net value: €{financial['three_year_net']:,.0f}"""


# For skill discovery
__all__ = ["ROICalculatorSkill"]
