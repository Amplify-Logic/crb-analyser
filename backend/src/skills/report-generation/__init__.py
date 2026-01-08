"""
Report Generation Skills

Skills for generating CRB report components with consistent formatting
and expertise-calibrated insights.

Available Skills:
- ExecSummarySkill: Generate executive summaries with AI readiness scoring
- FindingGenerationSkill: Generate findings with Two Pillars scoring
- ThreeOptionsSkill: Format recommendations in Three Options pattern
- VerdictSkill: Generate Go/Caution/Wait/No verdicts
- AutomationSummarySkill: Generate automation roadmap summary from findings
"""

from .automation_summary import AutomationSummarySkill
from .exec_summary import ExecSummarySkill
from .finding_generation import FindingGenerationSkill
from .three_options import ThreeOptionsSkill
from .verdict import VerdictSkill

__all__ = [
    "AutomationSummarySkill",
    "ExecSummarySkill",
    "FindingGenerationSkill",
    "ThreeOptionsSkill",
    "VerdictSkill",
]
