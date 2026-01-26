"""
Quiz Answer Parsing Utilities

Helper functions to parse and normalize quiz answers consistently
across the codebase.
"""

from typing import Any, Optional, Dict, List


def parse_employee_count(value: Any) -> int:
    """
    Parse employee_count from various formats to an integer.

    Handles formats like:
    - 25 (int)
    - "25" (string)
    - "1" (solo)
    - "2-10" (range string - uses midpoint)
    - "11-50" (range string - uses midpoint)
    - "51-200" (range string - uses midpoint)
    - "200+" (200+ string - uses 250)

    Args:
        value: The employee count value from quiz answers

    Returns:
        Integer employee count (midpoint for ranges)
    """
    if value is None:
        return 5  # Default for SMB

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    if isinstance(value, str):
        value = value.strip()

        # Handle "200+" format
        if value.endswith("+"):
            try:
                base = int(value[:-1])
                return base + 50  # e.g., 200+ -> 250
            except ValueError:
                pass

        # Check for range format like "11-50"
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


def parse_budget_tier(answers: Dict[str, Any]) -> str:
    """
    Parse budget tier from quiz answers, preferring the more granular field.

    Combines budget_for_solutions (Section 6, more granular) and
    budget_comfort (Section 4) into a single budget tier.

    Priority:
    1. budget_for_solutions (more granular: under_100, 100_500, 500_1000, 1000_5000, 5000_plus)
    2. budget_comfort (less granular: low, moderate, comfortable, high)

    Returns:
        Budget tier string: "low", "moderate", "comfortable", or "high"
    """
    # Check the more granular field first
    budget_for_solutions = answers.get("budget_for_solutions")
    if budget_for_solutions and budget_for_solutions != "not_sure":
        return _map_budget_for_solutions(budget_for_solutions)

    # Fall back to less granular field
    budget_comfort = answers.get("budget_comfort")
    if budget_comfort:
        return budget_comfort

    # Default
    return "moderate"


def _map_budget_for_solutions(value: str) -> str:
    """Map budget_for_solutions values to budget tier."""
    mapping = {
        "under_100": "low",
        "100_500": "moderate",
        "500_1000": "comfortable",
        "1000_5000": "high",
        "5000_plus": "high",
        "not_sure": "moderate",
    }
    return mapping.get(value, "moderate")


def get_monthly_budget_range(answers: Dict[str, Any]) -> tuple[int, int]:
    """
    Get the monthly budget range in EUR from quiz answers.

    Returns:
        Tuple of (min_budget, max_budget) in EUR
    """
    budget_for_solutions = answers.get("budget_for_solutions")
    if budget_for_solutions:
        ranges = {
            "under_100": (0, 100),
            "100_500": (100, 500),
            "500_1000": (500, 1000),
            "1000_5000": (1000, 5000),
            "5000_plus": (5000, 50000),
            "not_sure": (0, 5000),  # Wide range for uncertainty
        }
        return ranges.get(budget_for_solutions, (0, 5000))

    # Fall back to budget_comfort
    budget_comfort = answers.get("budget_comfort")
    if budget_comfort:
        ranges = {
            "low": (0, 50),
            "moderate": (50, 200),
            "comfortable": (200, 500),
            "high": (500, 10000),
        }
        return ranges.get(budget_comfort, (0, 500))

    return (0, 500)  # Default range


def parse_urgency(answers: Dict[str, Any]) -> Optional[str]:
    """
    Parse urgency from quiz answers, combining both urgency fields.

    Combines implementation_urgency (Section 4) and
    implementation_timeline (Section 6) into a single urgency value.

    Priority:
    1. implementation_urgency (direct urgency)
    2. implementation_timeline (maps to urgency)

    Returns:
        Urgency string: "this_week", "this_month", "this_quarter", or "no_rush"
    """
    # Check direct urgency field first
    urgency = answers.get("implementation_urgency")
    if urgency:
        return urgency

    # Map timeline to urgency
    timeline = answers.get("implementation_timeline")
    if timeline:
        return _map_timeline_to_urgency(timeline)

    return None


def _map_timeline_to_urgency(timeline: str) -> str:
    """Map implementation_timeline to urgency value."""
    mapping = {
        "asap": "this_week",
        "1_3_months": "this_month",
        "3_6_months": "this_quarter",
        "6_12_months": "no_rush",
        "no_rush": "no_rush",
    }
    return mapping.get(timeline, "this_month")


def parse_current_tools(answers: Dict[str, Any]) -> List[str]:
    """
    Parse current_tools from quiz answers.

    The current_tools field is a multi-select with category values like:
    - "crm", "project_management", "accounting", "email_marketing", etc.

    Returns:
        List of tool category strings
    """
    current_tools = answers.get("current_tools")
    if not current_tools:
        return []

    if isinstance(current_tools, list):
        return current_tools

    if isinstance(current_tools, str):
        # Handle comma-separated string
        return [t.strip() for t in current_tools.split(",") if t.strip()]

    return []


def get_complexity_level(answers: Dict[str, Any]) -> str:
    """
    Determine the appropriate recommendation complexity based on user's technical level.

    Based on implementation_capability:
    - non_technical -> simple (no technical jargon, step-by-step guidance)
    - tutorial_follower -> basic (light technical terms, clear instructions)
    - automation_user -> intermediate (comfortable with automation concepts)
    - ai_coder -> advanced (technical details appreciated)
    - has_developers -> technical (full technical depth)

    Returns:
        Complexity level: "simple", "basic", "intermediate", "advanced", or "technical"
    """
    capability = answers.get("implementation_capability", "tutorial_follower")

    mapping = {
        "non_technical": "simple",
        "tutorial_follower": "basic",
        "automation_user": "intermediate",
        "ai_coder": "advanced",
        "has_developers": "technical",
    }

    return mapping.get(capability, "basic")


def get_viable_option_types(answers: Dict[str, Any]) -> List[str]:
    """
    Determine which option types are viable based on user's capability.

    Returns list of viable option types: ["buy", "connect", "build", "hire"]
    """
    capability = answers.get("implementation_capability", "tutorial_follower")

    # All users can use BUY and HIRE
    viable = ["buy", "hire"]

    # CONNECT requires at least automation_user level
    if capability in ["automation_user", "ai_coder", "has_developers"]:
        viable.append("connect")

    # BUILD requires ai_coder or has_developers
    if capability in ["ai_coder", "has_developers"]:
        viable.append("build")

    return viable


# Tool category to quiz answer mapping
QUIZ_TOOL_TO_STACK_CATEGORY = {
    "crm": "CRM",
    "project_management": "Project Management",
    "accounting": "Accounting",
    "email_marketing": "Email Marketing",
    "social_media": "Social Media",
    "ecommerce": "E-commerce",
    "spreadsheets": "Spreadsheets",
    "communication": "Team Communication",
    "analytics": "Analytics",
}
