"""
Analysis Skills

Skills for financial and business analysis.

Available Skills:
- ROICalculatorSkill: Calculate ROI with transparent assumptions
- VendorMatchingSkill: Match findings to specific vendor solutions
- QuickWinIdentifierSkill: Identify low-effort, high-impact opportunities
- SourceValidatorSkill: Validate claims against knowledge base
- IndustryBenchmarkerSkill: Compare company to industry benchmarks
- CompetitorAnalyzerSkill: Analyze competitor AI adoption
- PlaybookGeneratorSkill: Generate implementation playbooks
"""

from .roi_calculator import ROICalculatorSkill
from .vendor_matching import VendorMatchingSkill
from .quick_win_identifier import QuickWinIdentifierSkill
from .source_validator import SourceValidatorSkill
from .industry_benchmarker import IndustryBenchmarkerSkill
from .competitor_analyzer import CompetitorAnalyzerSkill
from .playbook_generator import PlaybookGeneratorSkill

__all__ = [
    "ROICalculatorSkill",
    "VendorMatchingSkill",
    "QuickWinIdentifierSkill",
    "SourceValidatorSkill",
    "IndustryBenchmarkerSkill",
    "CompetitorAnalyzerSkill",
    "PlaybookGeneratorSkill",
]
