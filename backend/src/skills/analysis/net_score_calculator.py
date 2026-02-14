"""
NET SCORE Calculator Skill

Implements the core CRB framework formula:
    NET SCORE = Benefit Score - Cost Score - (Risk Score / 10)

This makes the "best option obvious" when comparing options
(Off-the-Shelf, Best-in-Class, Custom Build / BUY, CONNECT, BUILD, HIRE).

The 6 Costs:
    1. Financial Cost (implementation + ongoing)
    2. Time Cost (implementation time, learning curve)
    3. Opportunity Cost (what you can't do while implementing)
    4. Complexity Cost (integration difficulty, maintenance burden)
    5. Risk Cost (vendor dependency, reversal difficulty)
    6. Brand/Trust Cost (customer-facing risk during transition)

The 4 Benefits:
    1. Financial Benefit (cost savings, revenue increase)
    2. Time Benefit (hours saved per week/month)
    3. Strategic Benefit (competitive advantage, market position)
    4. Quality Benefit (error reduction, consistency, customer satisfaction)

Risk Score: 0-100 scale based on implementation risk, dependency risk, reversal difficulty.

Verdict thresholds:
    - strong_yes:       NET SCORE > 70
    - recommended:      NET SCORE 40-70
    - conditional:      NET SCORE 10-40
    - not_recommended:  NET SCORE < 10
"""

import logging
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field

from src.skills.base import SyncSkill, SkillContext, SkillError

logger = logging.getLogger(__name__)


# =============================================================================
# Input/Output Models
# =============================================================================

class CostScores(BaseModel):
    """The 6 cost dimensions, each scored 0-100."""
    financial: float = Field(
        ..., ge=0, le=100,
        description="Financial cost: implementation + ongoing monthly/yearly costs"
    )
    time: float = Field(
        ..., ge=0, le=100,
        description="Time cost: implementation duration, learning curve"
    )
    opportunity: float = Field(
        ..., ge=0, le=100,
        description="Opportunity cost: what you can't do while implementing"
    )
    complexity: float = Field(
        ..., ge=0, le=100,
        description="Complexity cost: integration difficulty, maintenance burden"
    )
    risk: float = Field(
        ..., ge=0, le=100,
        description="Risk cost: vendor dependency, technical risk"
    )
    brand_trust: float = Field(
        ..., ge=0, le=100,
        description="Brand/Trust cost: customer-facing risk during transition"
    )

    @property
    def total(self) -> float:
        """Average of all 6 cost dimensions (0-100 scale)."""
        return (
            self.financial + self.time + self.opportunity +
            self.complexity + self.risk + self.brand_trust
        ) / 6


class BenefitScores(BaseModel):
    """The 4 benefit dimensions, each scored 0-100."""
    financial: float = Field(
        ..., ge=0, le=100,
        description="Financial benefit: cost savings, revenue increase"
    )
    time: float = Field(
        ..., ge=0, le=100,
        description="Time benefit: hours saved per week/month"
    )
    strategic: float = Field(
        ..., ge=0, le=100,
        description="Strategic benefit: competitive advantage, market position"
    )
    quality: float = Field(
        ..., ge=0, le=100,
        description="Quality benefit: error reduction, consistency, customer satisfaction"
    )

    @property
    def total(self) -> float:
        """Average of all 4 benefit dimensions (0-100 scale)."""
        return (
            self.financial + self.time + self.strategic + self.quality
        ) / 4


class OptionInput(BaseModel):
    """Input for a single option to score."""
    option_type: str = Field(
        ...,
        description="Option identifier: off_the_shelf, best_in_class, custom_solution, buy, connect, build, hire"
    )
    label: str = Field(
        default="",
        description="Human-readable label for the option"
    )

    # Financial data (used to derive cost/benefit scores)
    implementation_cost: float = Field(default=0, ge=0, description="One-time implementation cost")
    monthly_cost: float = Field(default=0, ge=0, description="Monthly ongoing cost")
    implementation_weeks: float = Field(default=0, ge=0, description="Weeks to implement")
    monthly_savings: float = Field(default=0, ge=0, description="Monthly savings generated")
    hours_saved_per_week: float = Field(default=0, ge=0, description="Hours saved per week")

    # Qualitative scores (0-100), optional overrides
    # If not provided, they are estimated from the financial data
    cost_scores: Optional[CostScores] = None
    benefit_scores: Optional[BenefitScores] = None
    risk_score: Optional[float] = Field(None, ge=0, le=100, description="Overall risk score 0-100")

    # Risk factors for automatic risk scoring
    implementation_complexity: int = Field(
        default=3, ge=1, le=5,
        description="Implementation complexity 1-5"
    )
    vendor_dependency: str = Field(
        default="medium",
        description="Vendor lock-in level: low, medium, high"
    )
    reversal_difficulty: str = Field(
        default="Medium",
        description="How hard to undo: Easy, Medium, Hard"
    )


class OptionNetScore(BaseModel):
    """NET SCORE result for a single option."""
    option_type: str
    label: str

    # Component scores (all 0-100 scale)
    benefit_score: float = Field(..., description="Averaged benefit score (0-100)")
    cost_score: float = Field(..., description="Averaged cost score (0-100)")
    risk_score: float = Field(..., description="Risk score (0-100)")

    # The formula
    net_score: float = Field(..., description="NET SCORE = Benefit - Cost - (Risk / 10)")

    # Verdict
    verdict: Literal["strong_yes", "recommended", "conditional", "not_recommended"]
    verdict_label: str = Field(..., description="Human-readable verdict")

    # Breakdowns
    cost_breakdown: CostScores
    benefit_breakdown: BenefitScores

    # Debug
    formula_display: str = Field(
        ...,
        description="Human-readable formula: e.g. '72.5 - 35.0 - (40.0 / 10) = 33.5'"
    )


class NetScoreResult(BaseModel):
    """Complete NET SCORE result for all options."""
    options: List[OptionNetScore]
    recommended_option: str = Field(
        ...,
        description="The option_type with the highest NET SCORE"
    )
    recommended_label: str = Field(
        ...,
        description="Human-readable label for the recommended option"
    )
    score_gap: float = Field(
        ...,
        description="Difference between #1 and #2 scored options (larger = more obvious choice)"
    )
    comparison_summary: str = Field(
        ...,
        description="One-sentence summary of why the recommended option wins"
    )


# =============================================================================
# Score Estimation Helpers
# =============================================================================

# Budget reference points for normalizing financial costs
# These represent "typical SMB" ranges for scoring purposes
_COST_REFERENCE = {
    "implementation_high": 20000,   # Implementation cost that scores 100
    "monthly_high": 500,           # Monthly cost that scores 100
}

_BENEFIT_REFERENCE = {
    "monthly_savings_high": 5000,  # Monthly savings that scores 100
    "hours_saved_high": 20,        # Hours/week saved that scores 100
}


def _clamp(value: float, low: float = 0, high: float = 100) -> float:
    """Clamp a value to a range."""
    return max(low, min(high, value))


def _estimate_cost_scores(option: OptionInput) -> CostScores:
    """
    Estimate cost scores from financial data when not explicitly provided.

    Scores are 0-100 where higher = more costly (worse).
    """
    # Financial cost: based on implementation + 12 months of ongoing
    total_first_year = option.implementation_cost + (option.monthly_cost * 12)
    financial = _clamp(
        (total_first_year / _COST_REFERENCE["implementation_high"]) * 80
    )

    # Time cost: based on implementation weeks
    time = _clamp(option.implementation_weeks * 10)  # 10 weeks = 100

    # Opportunity cost: longer implementation = higher opportunity cost
    opportunity = _clamp(option.implementation_weeks * 8)  # 12.5 weeks = 100

    # Complexity cost: based on implementation complexity (1-5 scale)
    complexity = _clamp((option.implementation_complexity / 5) * 100)

    # Risk cost: from vendor dependency
    dependency_scores = {"low": 20, "medium": 50, "high": 80}
    risk = dependency_scores.get(option.vendor_dependency.lower(), 50)

    # Brand/Trust cost: based on reversal difficulty
    reversal_scores = {"easy": 15, "medium": 40, "hard": 75}
    brand_trust = reversal_scores.get(option.reversal_difficulty.lower(), 40)

    return CostScores(
        financial=round(financial, 1),
        time=round(time, 1),
        opportunity=round(opportunity, 1),
        complexity=round(complexity, 1),
        risk=round(risk, 1),
        brand_trust=round(brand_trust, 1),
    )


def _estimate_benefit_scores(option: OptionInput) -> BenefitScores:
    """
    Estimate benefit scores from financial data when not explicitly provided.

    Scores are 0-100 where higher = more beneficial (better).
    """
    # Financial benefit: based on monthly savings
    if option.monthly_savings > 0:
        financial = _clamp(
            (option.monthly_savings / _BENEFIT_REFERENCE["monthly_savings_high"]) * 100
        )
    else:
        financial = 20  # Some benefit assumed if recommended

    # Time benefit: based on hours saved per week
    if option.hours_saved_per_week > 0:
        time = _clamp(
            (option.hours_saved_per_week / _BENEFIT_REFERENCE["hours_saved_high"]) * 100
        )
    else:
        time = 20  # Some benefit assumed

    # Strategic benefit: custom solutions typically score higher
    strategic_by_type = {
        "off_the_shelf": 30,
        "best_in_class": 50,
        "custom_solution": 80,
        "buy": 30,
        "connect": 40,
        "build": 75,
        "hire": 50,
    }
    strategic = strategic_by_type.get(option.option_type, 40)

    # Quality benefit: best-in-class and custom tend to be higher quality
    quality_by_type = {
        "off_the_shelf": 50,
        "best_in_class": 75,
        "custom_solution": 70,
        "buy": 55,
        "connect": 45,
        "build": 65,
        "hire": 60,
    }
    quality = quality_by_type.get(option.option_type, 50)

    return BenefitScores(
        financial=round(financial, 1),
        time=round(time, 1),
        strategic=round(strategic, 1),
        quality=round(quality, 1),
    )


def _estimate_risk_score(option: OptionInput) -> float:
    """
    Estimate risk score (0-100) from option attributes.

    Higher = riskier.
    """
    # Base risk from implementation complexity (1-5 -> 10-50)
    base = option.implementation_complexity * 10

    # Vendor dependency adds risk
    dependency_bonus = {"low": 0, "medium": 10, "high": 25}
    dep = dependency_bonus.get(option.vendor_dependency.lower(), 10)

    # Reversal difficulty adds risk
    reversal_bonus = {"easy": 0, "medium": 10, "hard": 25}
    rev = reversal_bonus.get(option.reversal_difficulty.lower(), 10)

    return _clamp(base + dep + rev)


def _get_verdict(net_score: float) -> tuple:
    """Return (verdict_key, verdict_label) based on NET SCORE."""
    if net_score > 70:
        return "strong_yes", "Strong Yes - Clear winner"
    elif net_score >= 40:
        return "recommended", "Recommended - Good fit"
    elif net_score >= 10:
        return "conditional", "Conditional - Proceed with caution"
    else:
        return "not_recommended", "Not Recommended - Better options exist"


# =============================================================================
# Labels for option types
# =============================================================================

_OPTION_LABELS = {
    "off_the_shelf": "Off-the-Shelf",
    "best_in_class": "Best-in-Class",
    "custom_solution": "Custom Build",
    "buy": "Buy (SaaS)",
    "connect": "Connect (Integrate)",
    "build": "Build (Custom)",
    "hire": "Hire (Agency/Freelancer)",
}


# =============================================================================
# NET SCORE Calculator Skill
# =============================================================================

class NetScoreCalculatorSkill(SyncSkill[NetScoreResult]):
    """
    Calculate NET SCORE for comparing implementation options.

    Formula: NET SCORE = Benefit Score - Cost Score - (Risk Score / 10)

    This skill:
    - Takes one or more options with cost/benefit data
    - Scores each option on 6 cost dimensions and 4 benefit dimensions
    - Calculates NET SCORE using the CRB formula
    - Returns a ranked list with the recommended option
    - Assigns a verdict to each option

    Can be called:
    - With explicit CostScores/BenefitScores/risk_score (high precision)
    - With just financial data (auto-estimates the dimension scores)
    - With a mix of both
    """

    name = "net-score-calculator"
    description = "Calculate NET SCORE (Benefit - Cost - Risk/10) for option comparison"
    version = "1.0.0"

    requires_llm = False
    requires_expertise = False

    def execute_sync(self, context: SkillContext) -> NetScoreResult:
        """
        Calculate NET SCORE for all options in context.

        Expects context.metadata to contain:
            - options: List[dict] - each matching OptionInput schema
              OR
            - recommendation: dict - a three-options recommendation to score

        Returns:
            NetScoreResult with scored and ranked options
        """
        options_data = context.metadata.get("options", [])

        # If no explicit options list, try to extract from a recommendation
        if not options_data:
            recommendation = context.metadata.get("recommendation", {})
            if recommendation:
                options_data = self._extract_options_from_recommendation(
                    recommendation, context
                )

        if not options_data:
            raise SkillError(
                self.name,
                "No options provided. Pass 'options' list or 'recommendation' dict in context.metadata",
                recoverable=False,
            )

        # Parse and validate option inputs
        option_inputs = []
        for opt_data in options_data:
            try:
                if isinstance(opt_data, OptionInput):
                    option_inputs.append(opt_data)
                else:
                    option_inputs.append(OptionInput(**opt_data))
            except Exception as e:
                logger.warning(f"Skipping invalid option: {e}")
                continue

        if not option_inputs:
            raise SkillError(
                self.name,
                "No valid options to score",
                recoverable=False,
            )

        # Score each option
        scored_options: List[OptionNetScore] = []
        for option in option_inputs:
            scored = self._score_option(option)
            scored_options.append(scored)

        # Sort by NET SCORE descending
        scored_options.sort(key=lambda o: o.net_score, reverse=True)

        # Calculate score gap
        if len(scored_options) >= 2:
            score_gap = scored_options[0].net_score - scored_options[1].net_score
        else:
            score_gap = 0

        # Build comparison summary
        top = scored_options[0]
        summary = self._build_comparison_summary(scored_options)

        return NetScoreResult(
            options=scored_options,
            recommended_option=top.option_type,
            recommended_label=top.label,
            score_gap=round(score_gap, 1),
            comparison_summary=summary,
        )

    def _score_option(self, option: OptionInput) -> OptionNetScore:
        """Score a single option using the NET SCORE formula."""
        # Get or estimate cost scores
        cost_scores = option.cost_scores or _estimate_cost_scores(option)

        # Get or estimate benefit scores
        benefit_scores = option.benefit_scores or _estimate_benefit_scores(option)

        # Get or estimate risk score
        risk_score = option.risk_score if option.risk_score is not None else _estimate_risk_score(option)

        # Calculate component totals (averaged to 0-100 scale)
        benefit_total = benefit_scores.total
        cost_total = cost_scores.total

        # THE FORMULA
        net_score = benefit_total - cost_total - (risk_score / 10)

        # Get verdict
        verdict, verdict_label = _get_verdict(net_score)

        # Label
        label = option.label or _OPTION_LABELS.get(option.option_type, option.option_type)

        # Formula display
        formula_display = (
            f"{benefit_total:.1f} - {cost_total:.1f} - ({risk_score:.1f} / 10) = {net_score:.1f}"
        )

        return OptionNetScore(
            option_type=option.option_type,
            label=label,
            benefit_score=round(benefit_total, 1),
            cost_score=round(cost_total, 1),
            risk_score=round(risk_score, 1),
            net_score=round(net_score, 1),
            verdict=verdict,
            verdict_label=verdict_label,
            cost_breakdown=cost_scores,
            benefit_breakdown=benefit_scores,
            formula_display=formula_display,
        )

    def _extract_options_from_recommendation(
        self,
        recommendation: Dict[str, Any],
        context: SkillContext,
    ) -> List[Dict[str, Any]]:
        """
        Extract option inputs from a three-options or four-options recommendation.

        Converts the recommendation's options dict into OptionInput-compatible dicts.
        """
        options_out = []
        rec_options = recommendation.get("options", {})

        # Get shared benefit data from ROI detail if available
        roi_detail = recommendation.get("roi_detail", {})
        financial_impact = roi_detail.get("financial_impact", {})
        time_savings = roi_detail.get("time_savings", {})
        monthly_savings = financial_impact.get("monthly_savings", 0)
        hours_saved = time_savings.get("hours_per_week", 0)

        # Three-options format: off_the_shelf, best_in_class, custom_solution
        for opt_type in ["off_the_shelf", "best_in_class", "custom_solution"]:
            opt = rec_options.get(opt_type)
            if not opt:
                continue

            impl_cost = opt.get("implementation_cost", 0)
            monthly_cost = opt.get("monthly_cost", 0)
            impl_weeks = opt.get("implementation_weeks", 0)

            # For custom_solution, extract from nested structure
            if opt_type == "custom_solution":
                estimated_cost = opt.get("estimated_cost", {})
                if isinstance(estimated_cost, dict):
                    impl_cost = (estimated_cost.get("min", 0) + estimated_cost.get("max", 0)) / 2
                elif isinstance(estimated_cost, (int, float)):
                    impl_cost = estimated_cost
                monthly_cost = opt.get("monthly_running_cost", 0)

            # Complexity heuristics by option type
            complexity_map = {
                "off_the_shelf": 2,
                "best_in_class": 3,
                "custom_solution": 4,
            }
            vendor_dep_map = {
                "off_the_shelf": "medium",
                "best_in_class": "high",
                "custom_solution": "low",
            }
            reversal_map = {
                "off_the_shelf": "Easy",
                "best_in_class": "Medium",
                "custom_solution": "Hard",
            }

            options_out.append({
                "option_type": opt_type,
                "label": _OPTION_LABELS.get(opt_type, opt_type),
                "implementation_cost": impl_cost,
                "monthly_cost": monthly_cost,
                "implementation_weeks": impl_weeks,
                "monthly_savings": monthly_savings,
                "hours_saved_per_week": hours_saved,
                "implementation_complexity": complexity_map.get(opt_type, 3),
                "vendor_dependency": vendor_dep_map.get(opt_type, "medium"),
                "reversal_difficulty": reversal_map.get(opt_type, "Medium"),
            })

        # Four-options format: buy, connect, build, hire
        for opt_type in ["buy", "connect", "build", "hire"]:
            opt = rec_options.get(opt_type)
            if not opt:
                continue

            cost_data = opt.get("cost", {})
            year_one = cost_data.get("year_one_total", 0) if isinstance(cost_data, dict) else 0
            # Estimate monthly from year one
            monthly_cost = year_one / 12 if year_one else 0

            complexity_map = {
                "buy": 2,
                "connect": 3,
                "build": 4,
                "hire": 2,
            }
            vendor_dep_map = {
                "buy": "medium",
                "connect": "low",
                "build": "low",
                "hire": "low",
            }
            reversal_map = {
                "buy": "Easy",
                "connect": "Medium",
                "build": "Hard",
                "hire": "Medium",
            }

            options_out.append({
                "option_type": opt_type,
                "label": _OPTION_LABELS.get(opt_type, opt_type),
                "implementation_cost": cost_data.get("upfront", 0) if isinstance(cost_data, dict) else 0,
                "monthly_cost": monthly_cost,
                "implementation_weeks": 2,  # Default
                "monthly_savings": monthly_savings,
                "hours_saved_per_week": hours_saved,
                "implementation_complexity": complexity_map.get(opt_type, 3),
                "vendor_dependency": vendor_dep_map.get(opt_type, "medium"),
                "reversal_difficulty": reversal_map.get(opt_type, "Medium"),
            })

        return options_out

    def _build_comparison_summary(self, scored_options: List[OptionNetScore]) -> str:
        """Build a one-sentence comparison summary."""
        if not scored_options:
            return "No options to compare."

        top = scored_options[0]

        if len(scored_options) == 1:
            return f"{top.label} scores {top.net_score:.1f} ({top.verdict_label})."

        runner_up = scored_options[1]
        gap = top.net_score - runner_up.net_score

        if gap > 20:
            clarity = "clear winner"
        elif gap > 10:
            clarity = "ahead"
        else:
            clarity = "slightly ahead"

        return (
            f"{top.label} is the {clarity} with a NET SCORE of {top.net_score:.1f} "
            f"vs {runner_up.label} at {runner_up.net_score:.1f} "
            f"(gap: {gap:.1f} points)."
        )


# For skill discovery
__all__ = ["NetScoreCalculatorSkill"]
