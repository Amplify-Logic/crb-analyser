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
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        result = await tool_map[tool_name](tool_input, context, audit_id)
        return result
    except Exception as e:
        logger.error(f"Tool execution error ({tool_name}): {e}")
        return {"error": str(e)}
