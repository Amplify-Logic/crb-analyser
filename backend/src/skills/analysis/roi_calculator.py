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
    "is_not_recommended": false,
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
        "worst_case": {"roi": -25, "payback_months": 60}
    },
    "assumptions": [...],
    "calculation_breakdown": "Step-by-step explanation",
    "roi_warning": "Only present when ROI is negative",
    "not_recommended_reason": "Only present when is_not_recommended is true"
}

Note: ROI can be negative. When roi_percentage < 0, is_not_recommended=true
and not_recommended_reason explains why. Currency symbols in the breakdown
use the currency from SkillContext (defaults to EUR).
"""

import logging
from typing import Dict, Any, List, Optional

from src.skills.base import LLMSkill, SkillContext, SkillError
from src.utils.quiz_utils import parse_employee_count
from src.services.crb_calculation_service import get_effective_hourly_rate

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
                - currency: Currency code (e.g., "EUR", "GBP", "USD")

        Returns:
            ROI calculation with assumptions and sensitivity.
            Includes is_not_recommended=True when ROI is negative.
        """
        finding = context.metadata.get("finding", {})
        recommendation = context.metadata.get("recommendation", {})
        company_context = context.metadata.get("company_context", {})
        currency_symbol = context.currency_symbol

        if not finding:
            raise SkillError(
                self.name,
                "No finding provided in context.metadata",
                recoverable=False
            )

        # Get company-specific values from quiz answers (industry-aware)
        company_data = self._extract_company_data(
            context.quiz_answers, company_context, industry=context.industry
        )

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

        # Determine if this option should be flagged as not recommended based on ROI
        is_not_recommended = roi_metrics["roi_raw"] < 0

        # Generate sensitivity analysis
        sensitivity = self._calculate_sensitivity(
            base_metrics=roi_metrics,
            time_savings=time_savings,
            financial=financial,
        )

        # Build assumptions list
        assumptions = self._build_assumptions_list(company_data, currency_symbol=currency_symbol)

        # Generate calculation breakdown
        breakdown = self._generate_breakdown(
            time_savings=time_savings,
            financial=financial,
            roi_metrics=roi_metrics,
            company_data=company_data,
            currency_symbol=currency_symbol,
        )

        result: Dict[str, Any] = {
            "roi_percentage": roi_metrics["roi_raw"],
            "roi_confidence_adjusted": roi_metrics["roi_adjusted"],
            "payback_months": roi_metrics["payback_months"],
            "confidence": finding.get("confidence", "medium"),
            "is_not_recommended": is_not_recommended,
            "time_savings": time_savings,
            "financial_impact": financial,
            "sensitivity": sensitivity,
            "assumptions": assumptions,
            "calculation_breakdown": breakdown,
        }

        if roi_metrics.get("roi_warning"):
            result["roi_warning"] = roi_metrics["roi_warning"]

        if is_not_recommended:
            result["not_recommended_reason"] = (
                f"Negative ROI ({roi_metrics['roi_raw']:.0f}%): yearly costs "
                f"({currency_symbol}{financial['yearly_cost']:,.0f}) exceed estimated savings "
                f"({currency_symbol}{financial['yearly_savings']:,.0f}). "
                "This option is NOT recommended based on ROI analysis."
            )

        return result

    def _extract_company_data(
        self,
        quiz_answers: Optional[Dict[str, Any]],
        company_context: Dict[str, Any],
        industry: str = "",
    ) -> Dict[str, Any]:
        """Extract company-specific values, falling back to industry defaults."""
        answers = quiz_answers or {}

        # Use centralized hourly rate resolution (quiz > salary > industry > fallback)
        hourly_rate, rate_source = get_effective_hourly_rate(
            industry=industry,
            quiz_answers=answers,
        )

        # If company_context has an explicit rate, prefer it over industry default
        # (but not over quiz-provided data)
        if rate_source.startswith("industry default") or rate_source.startswith("default estimate"):
            context_rate = company_context.get("hourly_rate")
            if context_rate:
                try:
                    hourly_rate = float(context_rate)
                    rate_source = "company context"
                except (ValueError, TypeError):
                    pass

        team_size_raw = (
            answers.get("team_size") or
            answers.get("employee_count") or
            company_context.get("team_size") or
            5  # Default for SMB
        )

        # Parse team_size - handle range strings like "11-25" or "11-50"
        team_size = parse_employee_count(team_size_raw)

        # Determine if values came from actual data or assumptions
        hourly_rate_source = "quiz_data" if "provided by user" in rate_source else "assumption"
        team_size_source = "quiz_data" if answers.get("team_size") else "assumption"

        return {
            "hourly_rate": float(hourly_rate),
            "hourly_rate_source": hourly_rate_source,
            "hourly_rate_detail": rate_source,
            "team_size": team_size,
            "team_size_source": team_size_source,
            "work_weeks": DEFAULT_ASSUMPTIONS["work_weeks_per_year"]["value"],
            "automation_efficiency": DEFAULT_ASSUMPTIONS["automation_efficiency"]["value"],
            "adoption_rate": DEFAULT_ASSUMPTIONS["adoption_rate"]["value"],
        }

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
        option = options.get(our_rec, {})

        # AIOS option types — costs are string fields
        if our_rec in ("connect_and_automate", "enhance_with_ai", "targeted_upgrade"):
            implementation_cost, monthly_cost = self._extract_aios_costs(option, our_rec)
        # Legacy option types — costs are numeric fields
        elif our_rec == "custom_solution":
            cost_range = option.get("estimated_cost", {})
            implementation_cost = (cost_range.get("min", 5000) + cost_range.get("max", 15000)) / 2
            monthly_cost = option.get("monthly_running_cost", 50)
        elif our_rec == "best_in_class":
            implementation_cost = option.get("implementation_cost", 2000)
            monthly_cost = option.get("monthly_cost", 200)
        else:  # off_the_shelf
            implementation_cost = option.get("implementation_cost", 500)
            monthly_cost = option.get("monthly_cost", 50)

        # Parse string costs if needed (legacy options sometimes have strings too)
        if isinstance(monthly_cost, str):
            monthly_cost = self._parse_eur_cost(monthly_cost)
        if isinstance(implementation_cost, str):
            implementation_cost = self._parse_eur_cost(implementation_cost)

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

    def _extract_aios_costs(
        self,
        option: Dict[str, Any],
        option_type: str,
    ) -> tuple:
        """
        Extract implementation_cost and monthly_cost from an AIOS option.

        AIOS options store costs as strings: "EUR 60-100/month", "2 weeks build".
        Returns (implementation_cost, monthly_cost) as floats.
        """
        # Monthly cost: from "monthly_cost" or "cost_range" fields
        monthly_raw = option.get("monthly_cost", "") or option.get("cost_range", "") or ""
        if isinstance(monthly_raw, str):
            monthly_cost = self._parse_eur_cost(monthly_raw)
        else:
            monthly_cost = float(monthly_raw or 0)

        # Implementation cost: derived from build_time or migration_time
        build_time = option.get("build_time", "") or option.get("migration_time", "") or ""
        if isinstance(build_time, str) and build_time:
            # Parse time string to weeks, then estimate cost
            weeks = self._parse_weeks(build_time)
            # Estimate: 20 hrs/week * €75/hr for guided build
            implementation_cost = weeks * 20 * 75
        else:
            # Fallback: estimate from option type
            fallback = {
                "connect_and_automate": 2000,
                "enhance_with_ai": 4000,
                "targeted_upgrade": 1500,
            }
            implementation_cost = fallback.get(option_type, 2000)

        return implementation_cost, monthly_cost

    @staticmethod
    def _parse_eur_cost(cost_str: str) -> float:
        """Parse EUR cost strings like '€20-50/month' or 'EUR 500' into a numeric value."""
        import re
        if not cost_str:
            return 0.0
        numbers = re.findall(r'[\d,]+(?:\.\d+)?', cost_str.replace(',', ''))
        if not numbers:
            return 0.0
        nums = [float(n) for n in numbers]
        if len(nums) >= 2:
            return (nums[0] + nums[1]) / 2
        return nums[0]

    @staticmethod
    def _parse_weeks(time_str: str) -> float:
        """Parse time strings like '1 week', '2-4 weeks', '3 days' into weeks."""
        import re
        if not time_str:
            return 2.0
        numbers = re.findall(r'\d+\.?\d*', time_str)
        if not numbers:
            return 2.0
        nums = [float(n) for n in numbers]
        val = sum(nums) / len(nums)
        lower = time_str.lower()
        if 'day' in lower:
            return val / 5
        if 'month' in lower:
            return val * 4
        return val  # assume weeks

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

        # Keep negative ROI visible - don't hide bad recommendations
        # Negative ROI means costs exceed savings, which flags this as not recommended
        roi_warning = None
        if roi_raw < 0:
            roi_warning = (
                f"Calculated ROI is negative ({roi_raw:.0f}%), indicating yearly costs "
                f"({yearly_cost:.0f}) exceed savings ({yearly_savings:.0f}). "
                "This option is not recommended based on ROI analysis."
            )
            logger.warning(f"Negative ROI for finding {finding.get('id', 'unknown')}: {roi_warning}")

        # Apply confidence adjustment
        confidence = finding.get("confidence", "medium").lower()
        factor = CONFIDENCE_FACTORS.get(confidence, 0.85)
        roi_adjusted = roi_raw * factor

        # Payback period in months (minimum 1 month — sub-month payback is not credible)
        if net_annual > 0:
            payback_months = max(1.0, implementation_cost / (net_annual / 12))
        else:
            # Net annual is zero or negative - payback is very long or never
            if yearly_savings > 0:
                # Some savings but costs exceed them
                payback_months = 60  # Cap at 5 years
            else:
                payback_months = 999  # No savings at all

        result = {
            "roi_raw": round(roi_raw, 0),
            "roi_adjusted": round(roi_adjusted, 0),
            "confidence_factor": factor,
            "payback_months": round(min(payback_months, 60), 1),  # Cap at 5 years
            "net_annual_benefit": round(net_annual, 2),
        }

        if roi_warning:
            result["roi_warning"] = roi_warning

        return result

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
                "roi": round(worst_case_roi, 0),
                "payback_months": round(min(60, worst_case_payback), 1),
                "scenario": "Lower adoption, implementation delays"
            }
        }

    def _build_assumptions_list(
        self,
        company_data: Dict[str, Any],
        currency_symbol: str = "\u20ac",
    ) -> List[Dict[str, Any]]:
        """Build list of assumptions used in calculation."""
        assumptions = []
        cs = currency_symbol

        # Hourly rate assumption - always include with source detail
        rate_detail = company_data.get("hourly_rate_detail", "assumption")
        rate_value = company_data["hourly_rate"]
        if company_data["hourly_rate_source"] == "assumption":
            assumptions.append({
                **DEFAULT_ASSUMPTIONS["hourly_rate"],
                "value": rate_value,
                "statement": f"Hourly labor cost is {cs}{rate_value:.0f} ({rate_detail})",
                "source_detail": rate_detail,
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
        currency_symbol: str = "\u20ac",
    ) -> str:
        """Generate human-readable calculation breakdown."""
        cs = currency_symbol
        not_recommended_note = ""
        if roi_metrics["roi_raw"] < 0:
            not_recommended_note = (
                "\n\n   ** NOT RECOMMENDED: Negative ROI indicates costs exceed savings. **"
            )

        return f"""ROI Calculation Breakdown:

1. TIME SAVINGS
   - Raw hours identified: {time_savings['raw_hours_before_efficiency']:.1f} hrs/week
   - After automation efficiency ({company_data['automation_efficiency']*100:.0f}%): {time_savings['hours_per_week']:.1f} hrs/week
   - Monthly: {time_savings['hours_per_month']:.1f} hours
   - Yearly: {time_savings['hours_per_year']:.1f} hours

2. FINANCIAL VALUE
   - Hourly rate: {cs}{company_data['hourly_rate']:.0f}
   - Monthly savings: {cs}{financial['monthly_savings']:,.0f}
   - Yearly savings: {cs}{financial['yearly_savings']:,.0f}

3. COSTS
   - Implementation: {cs}{financial['implementation_cost']:,.0f}
   - Monthly ongoing: {cs}{financial['monthly_cost']:,.0f}
   - Yearly ongoing: {cs}{financial['yearly_cost']:,.0f}

4. ROI CALCULATION
   - Net annual benefit: {cs}{roi_metrics['net_annual_benefit']:,.0f}
   - First year investment: {cs}{financial['implementation_cost'] + financial['yearly_cost']:,.0f}
   - ROI: {roi_metrics['roi_raw']:.0f}%
   - Confidence-adjusted ROI: {roi_metrics['roi_adjusted']:.0f}% (factor: {roi_metrics['confidence_factor']})
   - Payback period: {roi_metrics['payback_months']:.1f} months{not_recommended_note}

5. THREE-YEAR PROJECTION
   - Gross savings: {cs}{financial['three_year_gross_savings']:,.0f}
   - Total costs: {cs}{financial['three_year_total_cost']:,.0f}
   - Net value: {cs}{financial['three_year_net']:,.0f}"""


# For skill discovery
__all__ = ["ROICalculatorSkill"]
