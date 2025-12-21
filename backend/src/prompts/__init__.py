"""
CRB Analyser - Prompt Library
=============================

Versioned prompts for CRB analysis across target industries.
Designed for iteration and improvement based on outcome data.

Usage:
    from prompts import get_crb_prompt, get_available_industries

    # Get prompt for dental industry
    prompt = get_crb_prompt("dental")

    # Get prompt with business context
    prompt = get_crb_prompt(
        industry="home_services",
        business_context={
            "company_name": "ABC Plumbing",
            "team_size": "12 technicians",
            "current_software": "Housecall Pro",
            "main_pain_point": "Scheduling inefficiency",
        }
    )
"""

from .crb_analysis_v1 import (
    get_crb_prompt,
    get_available_industries,
    get_industry_config,
    INDUSTRY_CONFIGS,
    PROMPT_VERSION,
)

__all__ = [
    "get_crb_prompt",
    "get_available_industries",
    "get_industry_config",
    "INDUSTRY_CONFIGS",
    "PROMPT_VERSION",
]
