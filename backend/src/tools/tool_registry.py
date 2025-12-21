"""
CRB Tool Registry

Defines and registers all tools available to the CRB Agent.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


# Tool definitions for Claude API
TOOL_DEFINITIONS: List[Dict] = [
    # Discovery Tools
    {
        "name": "analyze_intake_responses",
        "description": "Analyze intake questionnaire responses to extract key business insights, pain points, and opportunities.",
        "input_schema": {
            "type": "object",
            "properties": {
                "focus_areas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific areas to focus the analysis on",
                },
            },
            "required": [],
        },
    },
    {
        "name": "map_business_processes",
        "description": "Create a structured map of the company's main business processes based on intake responses.",
        "input_schema": {
            "type": "object",
            "properties": {
                "process_type": {
                    "type": "string",
                    "enum": ["all", "customer_facing", "internal", "administrative"],
                    "description": "Type of processes to map",
                },
            },
            "required": [],
        },
    },
    {
        "name": "identify_tech_stack",
        "description": "Identify and categorize the company's current technology stack from intake responses.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    # Research Tools
    {
        "name": "search_industry_benchmarks",
        "description": "Search for industry-specific benchmarks and metrics for comparison.",
        "input_schema": {
            "type": "object",
            "properties": {
                "industry": {
                    "type": "string",
                    "description": "Industry to search benchmarks for",
                },
                "metric_type": {
                    "type": "string",
                    "description": "Type of metric to search for (e.g., 'automation rate', 'labor costs')",
                },
            },
            "required": ["industry"],
        },
    },
    {
        "name": "search_vendor_solutions",
        "description": "Search for vendor solutions that match specific requirements.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Solution category (e.g., 'CRM', 'automation', 'AI')",
                },
                "company_size": {
                    "type": "string",
                    "description": "Target company size",
                },
                "budget_range": {
                    "type": "string",
                    "description": "Budget range (e.g., '100-500/month')",
                },
            },
            "required": ["category"],
        },
    },
    {
        "name": "validate_source",
        "description": "Validate the credibility of a data source or claim.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Source or claim to validate",
                },
                "claim": {
                    "type": "string",
                    "description": "Specific claim being made",
                },
            },
            "required": ["source"],
        },
    },
    # Analysis Tools
    {
        "name": "score_automation_potential",
        "description": "Score a business process for automation potential (0-100).",
        "input_schema": {
            "type": "object",
            "properties": {
                "process_name": {
                    "type": "string",
                    "description": "Name of the process to score",
                },
                "process_description": {
                    "type": "string",
                    "description": "Description of the process",
                },
                "current_time_hours": {
                    "type": "number",
                    "description": "Current time spent on process (hours/month)",
                },
                "is_repetitive": {
                    "type": "boolean",
                    "description": "Whether the process is repetitive",
                },
                "requires_judgment": {
                    "type": "boolean",
                    "description": "Whether the process requires human judgment",
                },
            },
            "required": ["process_name", "process_description"],
        },
    },
    {
        "name": "calculate_finding_impact",
        "description": "Calculate the business impact of a finding.",
        "input_schema": {
            "type": "object",
            "properties": {
                "finding_title": {
                    "type": "string",
                    "description": "Title of the finding",
                },
                "hours_saved_per_month": {
                    "type": "number",
                    "description": "Estimated hours saved per month",
                },
                "hourly_rate": {
                    "type": "number",
                    "description": "Hourly rate of employees affected (EUR)",
                },
                "affected_employees": {
                    "type": "integer",
                    "description": "Number of employees affected",
                },
            },
            "required": ["finding_title", "hours_saved_per_month"],
        },
    },
    {
        "name": "identify_ai_opportunities",
        "description": "Identify specific AI implementation opportunities based on process analysis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "process_area": {
                    "type": "string",
                    "description": "Area to analyze for AI opportunities",
                },
            },
            "required": ["process_area"],
        },
    },
    {
        "name": "assess_implementation_risk",
        "description": "Assess the implementation risk for a proposed change.",
        "input_schema": {
            "type": "object",
            "properties": {
                "change_description": {
                    "type": "string",
                    "description": "Description of the proposed change",
                },
                "complexity": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Complexity of the change",
                },
                "requires_training": {
                    "type": "boolean",
                    "description": "Whether the change requires employee training",
                },
            },
            "required": ["change_description"],
        },
    },
    # Modeling Tools
    {
        "name": "calculate_roi",
        "description": "Calculate ROI for a proposed solution with transparent assumptions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "solution_name": {
                    "type": "string",
                    "description": "Name of the solution",
                },
                "implementation_cost": {
                    "type": "number",
                    "description": "One-time implementation cost (EUR)",
                },
                "monthly_cost": {
                    "type": "number",
                    "description": "Monthly recurring cost (EUR)",
                },
                "monthly_savings": {
                    "type": "number",
                    "description": "Expected monthly savings (EUR)",
                },
                "time_horizon_months": {
                    "type": "integer",
                    "description": "Time horizon for ROI calculation (months)",
                },
            },
            "required": ["solution_name", "implementation_cost", "monthly_cost", "monthly_savings"],
        },
    },
    {
        "name": "compare_vendors",
        "description": "Compare multiple vendors for a solution category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Solution category",
                },
                "requirements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key requirements to compare",
                },
                "budget_max": {
                    "type": "number",
                    "description": "Maximum budget (EUR/month)",
                },
            },
            "required": ["category"],
        },
    },
    {
        "name": "generate_timeline",
        "description": "Generate an implementation timeline for a set of recommendations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "recommendations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of recommendations to timeline",
                },
                "start_date": {
                    "type": "string",
                    "description": "Proposed start date (YYYY-MM-DD)",
                },
            },
            "required": ["recommendations"],
        },
    },
    # Report Tools
    {
        "name": "create_finding",
        "description": "Create and save a finding to the database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Finding title",
                },
                "category": {
                    "type": "string",
                    "enum": ["process", "technology", "cost", "risk", "opportunity"],
                    "description": "Finding category",
                },
                "priority": {
                    "type": "integer",
                    "description": "Priority (1=highest, 5=lowest)",
                    "minimum": 1,
                    "maximum": 5,
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description",
                },
                "current_state": {
                    "type": "string",
                    "description": "Description of current state",
                },
                "estimated_hours_saved": {
                    "type": "number",
                    "description": "Estimated hours saved per month",
                },
                "estimated_cost_saved": {
                    "type": "number",
                    "description": "Estimated annual cost savings (EUR)",
                },
                "confidence_level": {
                    "type": "integer",
                    "description": "Confidence level (0-100)",
                    "minimum": 0,
                    "maximum": 100,
                },
                "is_ai_estimated": {
                    "type": "boolean",
                    "description": "Whether this is an AI estimate vs verified data",
                },
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Sources supporting this finding",
                },
            },
            "required": ["title", "category", "priority", "description"],
        },
    },
    {
        "name": "create_recommendation",
        "description": "Create and save a recommendation to the database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "finding_title": {
                    "type": "string",
                    "description": "Title of the related finding",
                },
                "title": {
                    "type": "string",
                    "description": "Recommendation title",
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description",
                },
                "vendor_name": {
                    "type": "string",
                    "description": "Recommended vendor name",
                },
                "vendor_category": {
                    "type": "string",
                    "description": "Vendor category",
                },
                "implementation_cost": {
                    "type": "number",
                    "description": "One-time implementation cost (EUR)",
                },
                "monthly_cost": {
                    "type": "number",
                    "description": "Monthly cost (EUR)",
                },
                "roi_percentage": {
                    "type": "number",
                    "description": "Expected ROI percentage",
                },
                "payback_months": {
                    "type": "integer",
                    "description": "Payback period in months",
                },
                "implementation_timeline": {
                    "type": "string",
                    "description": "Implementation timeline description",
                },
                "priority": {
                    "type": "integer",
                    "description": "Priority (1=highest, 5=lowest)",
                },
            },
            "required": ["title", "description", "priority"],
        },
    },
    {
        "name": "generate_executive_summary",
        "description": "Generate an executive summary of all findings and recommendations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key_findings": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Top key findings to highlight",
                },
                "total_potential_savings": {
                    "type": "number",
                    "description": "Total potential annual savings (EUR)",
                },
                "ai_readiness_summary": {
                    "type": "string",
                    "description": "Summary of AI readiness assessment",
                },
            },
            "required": ["key_findings", "total_potential_savings"],
        },
    },
]


from src.config.settings import settings


# Tool category to timeout mapping
TOOL_TIMEOUTS = {
    # Discovery tools
    "analyze_intake_responses": settings.TOOL_TIMEOUT_DISCOVERY,
    "map_business_processes": settings.TOOL_TIMEOUT_DISCOVERY,
    "identify_tech_stack": settings.TOOL_TIMEOUT_DISCOVERY,
    # Research tools (need more time for external calls)
    "search_industry_benchmarks": settings.TOOL_TIMEOUT_RESEARCH,
    "search_vendor_solutions": settings.TOOL_TIMEOUT_RESEARCH,
    "validate_source": settings.TOOL_TIMEOUT_RESEARCH,
    # Analysis tools
    "score_automation_potential": settings.TOOL_TIMEOUT_ANALYSIS,
    "calculate_finding_impact": settings.TOOL_TIMEOUT_ANALYSIS,
    "identify_ai_opportunities": settings.TOOL_TIMEOUT_ANALYSIS,
    "assess_implementation_risk": settings.TOOL_TIMEOUT_ANALYSIS,
    # Modeling tools
    "calculate_roi": settings.TOOL_TIMEOUT_ANALYSIS,
    "compare_vendors": settings.TOOL_TIMEOUT_RESEARCH,
    "generate_timeline": settings.TOOL_TIMEOUT_ANALYSIS,
    # Report tools
    "create_finding": settings.TOOL_TIMEOUT_DEFAULT,
    "create_recommendation": settings.TOOL_TIMEOUT_DEFAULT,
    "generate_executive_summary": settings.TOOL_TIMEOUT_DEFAULT,
}


async def execute_tool(
    tool_name: str,
    tool_input: Dict[str, Any],
    context: Dict[str, Any],
    audit_id: str,
) -> Dict[str, Any]:
    """
    Execute a tool and return its result.

    Args:
        tool_name: Name of the tool to execute
        tool_input: Input parameters for the tool
        context: Current analysis context
        audit_id: ID of the audit being analyzed

    Returns:
        Tool execution result
    """
    return await execute_tool_with_retry(
        tool_name, tool_input, context, audit_id
    )


async def execute_tool_with_retry(
    tool_name: str,
    tool_input: Dict[str, Any],
    context: Dict[str, Any],
    audit_id: str,
    max_retries: int = None,
) -> Dict[str, Any]:
    """
    Execute a tool with retry logic and timeout.

    Features:
    - Configurable timeout per tool type
    - Exponential backoff retry for transient failures
    - Structured error responses with retry information

    Args:
        tool_name: Name of the tool to execute
        tool_input: Input parameters for the tool
        context: Current analysis context
        audit_id: ID of the audit being analyzed
        max_retries: Override for retry attempts

    Returns:
        Tool execution result or structured error
    """
    import asyncio
    import time

    from src.tools.discovery_tools import (
        analyze_intake_responses,
        map_business_processes,
        identify_tech_stack,
    )
    from src.tools.research_tools import (
        search_industry_benchmarks,
        search_vendor_solutions,
        validate_source,
    )
    from src.tools.analysis_tools import (
        score_automation_potential,
        calculate_finding_impact,
        identify_ai_opportunities,
        assess_implementation_risk,
    )
    from src.tools.modeling_tools import (
        calculate_roi,
        compare_vendors,
        generate_timeline,
    )
    from src.tools.report_tools import (
        create_finding,
        create_recommendation,
        generate_executive_summary,
    )

    tool_map = {
        # Discovery
        "analyze_intake_responses": analyze_intake_responses,
        "map_business_processes": map_business_processes,
        "identify_tech_stack": identify_tech_stack,
        # Research
        "search_industry_benchmarks": search_industry_benchmarks,
        "search_vendor_solutions": search_vendor_solutions,
        "validate_source": validate_source,
        # Analysis
        "score_automation_potential": score_automation_potential,
        "calculate_finding_impact": calculate_finding_impact,
        "identify_ai_opportunities": identify_ai_opportunities,
        "assess_implementation_risk": assess_implementation_risk,
        # Modeling
        "calculate_roi": calculate_roi,
        "compare_vendors": compare_vendors,
        "generate_timeline": generate_timeline,
        # Report
        "create_finding": create_finding,
        "create_recommendation": create_recommendation,
        "generate_executive_summary": generate_executive_summary,
    }

    if tool_name not in tool_map:
        return {
            "error": {
                "type": "unknown_tool",
                "message": f"Unknown tool: {tool_name}",
                "retryable": False,
            }
        }

    # Get timeout and retry settings
    timeout = TOOL_TIMEOUTS.get(tool_name, settings.TOOL_TIMEOUT_DEFAULT)
    retries = max_retries if max_retries is not None else settings.TOOL_RETRY_ATTEMPTS
    base_delay = settings.TOOL_RETRY_DELAY

    last_error = None
    start_time = time.time()

    for attempt in range(retries):
        try:
            # Log tool execution start
            logger.info(
                f"Tool {tool_name} starting (attempt {attempt + 1}/{retries}, "
                f"timeout={timeout}s)"
            )

            # Execute with timeout
            result = await asyncio.wait_for(
                tool_map[tool_name](tool_input, context, audit_id),
                timeout=timeout
            )

            # Log success
            duration = time.time() - start_time
            logger.info(
                f"Tool {tool_name} completed in {duration:.2f}s "
                f"(attempt {attempt + 1})"
            )

            return result

        except asyncio.TimeoutError:
            last_error = f"Tool timed out after {timeout}s"
            logger.warning(
                f"Tool {tool_name} timeout (attempt {attempt + 1}/{retries})"
            )

            # Timeouts are retryable
            if attempt < retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.info(f"Retrying {tool_name} in {delay:.1f}s...")
                await asyncio.sleep(delay)

        except Exception as e:
            last_error = str(e)
            logger.warning(
                f"Tool {tool_name} error (attempt {attempt + 1}/{retries}): {e}"
            )

            # Check if error is retryable
            retryable = _is_retryable_error(e)

            if retryable and attempt < retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.info(f"Retrying {tool_name} in {delay:.1f}s...")
                await asyncio.sleep(delay)
            elif not retryable:
                # Non-retryable error, fail immediately
                break

    # All retries exhausted
    duration = time.time() - start_time
    logger.error(
        f"Tool {tool_name} failed after {retries} attempts in {duration:.2f}s: "
        f"{last_error}"
    )

    return {
        "error": {
            "type": "tool_execution_failed",
            "message": last_error,
            "tool_name": tool_name,
            "attempts": retries,
            "duration_seconds": round(duration, 2),
            "retryable": False,  # All retries exhausted
        }
    }


def _is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error is retryable.

    Retryable errors include:
    - Network/connection errors
    - Temporary service unavailability
    - Rate limiting

    Non-retryable errors include:
    - Validation errors
    - Authentication errors
    - Not found errors
    """
    error_str = str(error).lower()

    # Retryable patterns
    retryable_patterns = [
        "timeout",
        "connection",
        "network",
        "temporary",
        "unavailable",
        "rate limit",
        "429",
        "503",
        "504",
    ]

    # Non-retryable patterns
    non_retryable_patterns = [
        "validation",
        "invalid",
        "not found",
        "404",
        "401",
        "403",
        "permission",
        "unauthorized",
    ]

    for pattern in non_retryable_patterns:
        if pattern in error_str:
            return False

    for pattern in retryable_patterns:
        if pattern in error_str:
            return True

    # Default to retryable for unknown errors
    return True
