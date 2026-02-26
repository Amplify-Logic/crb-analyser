"""
Readiness Profile Builder

Maps raw quiz answers into a clean readiness profile for the recommendation engine.
Two axes determine recommendations:
1. Infrastructure readiness - paper-based / partial / digitized
2. Build willingness - prefers-turnkey / open / eager
"""

from typing import Any, Dict


def build_readiness_profile(quiz_answers: Dict[str, Any]) -> Dict[str, Any]:
    """Map quiz signals into readiness profile for recommendation engine.

    Args:
        quiz_answers: Raw quiz answer dictionary from quiz session.

    Returns:
        Readiness profile dict with infrastructure, build_willingness,
        ai_experience, stack_api_readiness, urgency, and preference.
    """
    # Infrastructure readiness
    current_tools = quiz_answers.get("current_tools", [])
    integration_score = quiz_answers.get("integration_issues", 5)
    manual_entry = quiz_answers.get("manual_data_entry", False)

    if not current_tools or len(current_tools) <= 1:
        infrastructure = "paper-based"
    elif integration_score < 4 or manual_entry:
        infrastructure = "partial"
    else:
        infrastructure = "digitized"

    # Build willingness (from preference + tech comfort)
    preference = quiz_answers.get("implementation_preference", "buy")
    tech_comfort = quiz_answers.get("technology_comfort", 5)

    if preference in ("build", "connect") or tech_comfort >= 7:
        build_willingness = "eager"
    elif preference == "hire" or tech_comfort <= 3:
        build_willingness = "prefers-turnkey"
    else:
        build_willingness = "open"

    # AI experience
    ai_tools = quiz_answers.get("ai_tools_used", [])
    if not ai_tools or ai_tools == ["none"]:
        ai_experience = "none"
    elif len(ai_tools) >= 3 or "automation" in ai_tools:
        ai_experience = "active-user"
    else:
        ai_experience = "dabbled"

    # Stack API readiness
    api_ready = quiz_answers.get("existing_stack_api_ready", False)
    stack_api = "most-apis" if api_ready else "mixed"

    # Urgency + preference pass through
    urgency = quiz_answers.get("implementation_urgency", "this_quarter")

    return {
        "infrastructure": infrastructure,
        "build_willingness": build_willingness,
        "ai_experience": ai_experience,
        "stack_api_readiness": stack_api,
        "urgency": urgency,
        "preference": preference,
    }
