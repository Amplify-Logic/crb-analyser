"""
Option Scoring Service

Calculates weighted match scores (0-100) for BUY/CONNECT/BUILD/HIRE options
based on user profile (capability, preference, budget, urgency).
"""

from typing import Dict, List, Optional
from src.models.user_profile import (
    UserProfile,
    CapabilityLevel,
    ImplementationPreference,
    BudgetTier,
    Urgency,
)
from src.models.four_options import OptionType, OptionScore, CostEstimate


# Scoring weights (must sum to 1.0)
SCORING_WEIGHTS = {
    "capability_match": 0.30,
    "preference_match": 0.20,
    "budget_fit": 0.20,
    "time_fit": 0.15,
    "value_ratio": 0.15,
}

# Capability matrix: option -> capability -> score
CAPABILITY_MATRIX: Dict[OptionType, Dict[CapabilityLevel, int]] = {
    OptionType.BUY: {
        CapabilityLevel.NON_TECHNICAL: 100,
        CapabilityLevel.TUTORIAL_FOLLOWER: 100,
        CapabilityLevel.AUTOMATION_USER: 90,
        CapabilityLevel.AI_CODER: 80,
        CapabilityLevel.HAS_DEVELOPERS: 70,
    },
    OptionType.CONNECT: {
        CapabilityLevel.NON_TECHNICAL: 20,
        CapabilityLevel.TUTORIAL_FOLLOWER: 60,
        CapabilityLevel.AUTOMATION_USER: 100,
        CapabilityLevel.AI_CODER: 90,
        CapabilityLevel.HAS_DEVELOPERS: 85,
    },
    OptionType.BUILD: {
        CapabilityLevel.NON_TECHNICAL: 10,
        CapabilityLevel.TUTORIAL_FOLLOWER: 30,
        CapabilityLevel.AUTOMATION_USER: 50,
        CapabilityLevel.AI_CODER: 100,
        CapabilityLevel.HAS_DEVELOPERS: 100,
    },
    OptionType.HIRE: {
        CapabilityLevel.NON_TECHNICAL: 90,
        CapabilityLevel.TUTORIAL_FOLLOWER: 85,
        CapabilityLevel.AUTOMATION_USER: 80,
        CapabilityLevel.AI_CODER: 70,
        CapabilityLevel.HAS_DEVELOPERS: 50,
    },
}

# Budget limits in EUR (annual)
BUDGET_LIMITS = {
    BudgetTier.LOW: 600,           # 50/month
    BudgetTier.MODERATE: 2400,     # 200/month
    BudgetTier.COMFORTABLE: 6000,  # 500/month
    BudgetTier.HIGH: 50000,
}

# Time limits in days
URGENCY_LIMITS = {
    Urgency.THIS_WEEK: 7,
    Urgency.THIS_MONTH: 30,
    Urgency.THIS_QUARTER: 90,
    Urgency.NO_RUSH: 365,
}

# Time to value mappings
TIME_MAP = {
    "1 day": 1,
    "2 days": 2,
    "3 days": 3,
    "1 week": 7,
    "2 weeks": 14,
    "3 weeks": 21,
    "4 weeks": 28,
    "1 month": 30,
    "2-3 weeks": 18,
    "2-4 weeks": 21,
    "4-6 weeks": 35,
    "4-8 weeks": 42,
    "30 minutes": 0.02,
    "1 hour": 0.04,
    "2 hours": 0.08,
    "4 hours": 0.17,
    "8 hours": 0.33,
}

# Match reasons by option and capability
CAPABILITY_MATCH_REASONS: Dict[OptionType, Dict[CapabilityLevel, str]] = {
    OptionType.BUY: {
        CapabilityLevel.NON_TECHNICAL: "No technical skills needed",
        CapabilityLevel.TUTORIAL_FOLLOWER: "Simple setup you can handle",
        CapabilityLevel.AUTOMATION_USER: "Quick win - save your automation skills for bigger projects",
        CapabilityLevel.AI_CODER: "Fast solution - save your coding time for custom needs",
        CapabilityLevel.HAS_DEVELOPERS: "Don't waste dev time on solved problems",
    },
    OptionType.CONNECT: {
        CapabilityLevel.AUTOMATION_USER: "Perfect match for your automation skills",
        CapabilityLevel.AI_CODER: "Quick integration using tools you know",
        CapabilityLevel.HAS_DEVELOPERS: "Your team can set this up quickly",
    },
    OptionType.BUILD: {
        CapabilityLevel.AI_CODER: "Your AI coding skills make this very achievable",
        CapabilityLevel.HAS_DEVELOPERS: "Your dev team can build exactly what you need",
    },
    OptionType.HIRE: {
        CapabilityLevel.NON_TECHNICAL: "Expert handles everything for you",
        CapabilityLevel.TUTORIAL_FOLLOWER: "Professional setup, you maintain",
    },
}


def calculate_capability_match(
    option: OptionType,
    capability: CapabilityLevel
) -> int:
    """Score how well user's capability matches option requirements."""
    return CAPABILITY_MATRIX.get(option, {}).get(capability, 50)


def calculate_budget_fit(
    cost: CostEstimate,
    budget_tier: BudgetTier
) -> int:
    """Score how well option cost fits user's budget."""
    limit = BUDGET_LIMITS.get(budget_tier, 2400)
    annual_cost = cost.year_one_total

    if annual_cost <= limit * 0.5:
        return 100  # Well within budget
    elif annual_cost <= limit:
        return 80   # Fits budget
    elif annual_cost <= limit * 1.5:
        return 50   # Stretch
    else:
        return 20   # Out of budget


def calculate_time_fit(
    time_to_value: str,
    urgency: Optional[Urgency]
) -> int:
    """Score how well option timeline fits user's urgency."""
    if urgency is None:
        return 80  # No urgency specified, neutral score

    days_needed = TIME_MAP.get(time_to_value, 14)
    days_available = URGENCY_LIMITS.get(urgency, 90)

    if days_needed <= days_available * 0.5:
        return 100
    elif days_needed <= days_available:
        return 80
    elif days_needed <= days_available * 1.5:
        return 50
    else:
        return 20


def score_option(
    option: OptionType,
    profile: UserProfile,
    cost: CostEstimate,
    time_to_value: str,
    value_score: int = 80,  # Default good value
) -> OptionScore:
    """
    Calculate weighted match score for an option.

    Returns OptionScore with 0-100 score and reasoning.
    """
    breakdown = {}
    match_reasons = []
    concern_reasons = []

    # 1. Capability Match (30%)
    cap_score = calculate_capability_match(option, profile.capability)
    breakdown["capability_match"] = cap_score
    if cap_score >= 80:
        reason = CAPABILITY_MATCH_REASONS.get(option, {}).get(profile.capability)
        if reason:
            match_reasons.append(reason)
    elif cap_score < 50:
        if option == OptionType.BUILD:
            concern_reasons.append("Requires technical skills")
        elif option == OptionType.CONNECT:
            concern_reasons.append("Requires automation tool experience")

    # 2. Preference Match (20%)
    pref_map = {
        ImplementationPreference.BUY: OptionType.BUY,
        ImplementationPreference.CONNECT: OptionType.CONNECT,
        ImplementationPreference.BUILD: OptionType.BUILD,
        ImplementationPreference.HIRE: OptionType.HIRE,
    }
    pref_score = 100 if pref_map.get(profile.preference) == option else 60
    breakdown["preference_match"] = pref_score
    if pref_score == 100:
        match_reasons.append(f"Matches your '{option.value}' preference")

    # 3. Budget Fit (20%)
    budget_score = calculate_budget_fit(cost, profile.budget)
    breakdown["budget_fit"] = budget_score
    if budget_score >= 80:
        match_reasons.append(f"Within your {profile.budget.value} budget")
    elif budget_score < 50:
        concern_reasons.append(f"May stretch your {profile.budget.value} budget")

    # 4. Time Fit (15%)
    time_score = calculate_time_fit(time_to_value, profile.urgency)
    breakdown["time_fit"] = time_score
    if time_score >= 80 and profile.urgency:
        match_reasons.append(f"Fits your {profile.urgency.value.replace('_', ' ')} timeline")
    elif time_score < 50 and profile.urgency:
        concern_reasons.append(f"May not meet your {profile.urgency.value.replace('_', ' ')} deadline")

    # 5. Value Ratio (15%) - passed in, default 80
    breakdown["value_ratio"] = value_score
    if value_score >= 80:
        match_reasons.append("Good ROI for this specific problem")

    # Calculate weighted total
    total_score = sum(
        breakdown[factor] * weight
        for factor, weight in SCORING_WEIGHTS.items()
    )

    return OptionScore(
        option=option,
        score=round(total_score, 0),
        breakdown=breakdown,
        match_reasons=match_reasons[:3],  # Top 3
        concern_reasons=concern_reasons[:2],  # Top 2
        is_recommended=False,  # Set later
    )


def get_recommendations(
    profile: UserProfile,
    option_costs: Dict[OptionType, CostEstimate],
    option_times: Dict[OptionType, str],
    option_values: Optional[Dict[OptionType, int]] = None,
) -> List[OptionScore]:
    """
    Score all options and return ranked list.

    Highest scoring option is marked as recommended.
    """
    if option_values is None:
        option_values = {opt: 80 for opt in OptionType}

    scores = []
    for option in OptionType:
        cost = option_costs.get(option, CostEstimate())
        time = option_times.get(option, "2 weeks")
        value = option_values.get(option, 80)

        score = score_option(option, profile, cost, time, value)
        scores.append(score)

    # Sort by score descending
    scores.sort(key=lambda x: x.score, reverse=True)

    # Mark highest as recommended
    if scores:
        scores[0].is_recommended = True

    return scores
