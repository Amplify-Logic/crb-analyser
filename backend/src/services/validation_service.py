"""
Report Validation Service

Deterministic validators for CRB reports that run during report generation.
These validate structure, math, and data quality WITHOUT needing LLM calls.

Usage:
    from src.services.validation_service import validate_report, ValidationResult

    result = validate_report(report_data)
    if not result.is_valid:
        logger.error(f"Validation failed: {result.errors}")
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from decimal import Decimal

logger = logging.getLogger(__name__)


# ============================================================================
# Validation Result
# ============================================================================

@dataclass
class ValidationResult:
    """Result of validation with errors and warnings."""
    is_valid: bool
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge another validation result into this one."""
        return ValidationResult(
            is_valid=self.is_valid and other.is_valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
        )


# ============================================================================
# Math Validation (Deterministic)
# ============================================================================

TOLERANCE = 0.10  # 10% tolerance for rounding

BOUNDS = {
    "hours_per_week": {"min": 0.5, "max": 80},
    "hourly_rate": {"min": 10, "max": 500},
    "annual_savings": {"min": 0, "max": 2_000_000},
    "roi_percentage": {"min": -100, "max": 2000},
    "payback_months": {"min": 0.1, "max": 120},
}


def _is_within_tolerance(actual: float, expected: float, tolerance: float = TOLERANCE) -> bool:
    """Check if actual value is within tolerance of expected."""
    if expected == 0:
        return actual == 0
    return abs(actual - expected) <= abs(expected * tolerance)


def validate_finding_math(finding: Dict[str, Any], default_hourly_rate: float = 50) -> ValidationResult:
    """Validate math in a single finding."""
    errors = []
    warnings = []
    finding_id = finding.get("id", "unknown")

    value_saved = finding.get("value_saved", {})
    if not value_saved:
        return ValidationResult(is_valid=True)

    hours_per_week = value_saved.get("hours_per_week", 0)
    hourly_rate = value_saved.get("hourly_rate", default_hourly_rate)
    annual_savings = value_saved.get("annual_savings", 0)

    # Check annual_savings calculation
    if hours_per_week and annual_savings:
        expected_annual = hours_per_week * hourly_rate * 52

        if not _is_within_tolerance(annual_savings, expected_annual):
            errors.append({
                "location": f"finding '{finding_id}' → value_saved.annual_savings",
                "claimed": annual_savings,
                "expected": round(expected_annual, 2),
                "formula": f"{hours_per_week} hrs/wk × €{hourly_rate}/hr × 52 wks",
                "fix": f"Change annual_savings to {round(expected_annual, 0)}"
            })

    # Bounds checking
    if hours_per_week and hours_per_week > BOUNDS["hours_per_week"]["max"]:
        errors.append({
            "location": f"finding '{finding_id}' → hours_per_week",
            "issue": f"Value {hours_per_week} exceeds maximum {BOUNDS['hours_per_week']['max']}",
        })

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_recommendation_math(rec: Dict[str, Any]) -> ValidationResult:
    """Validate math in a single recommendation."""
    errors = []
    warnings = []
    rec_id = rec.get("id", "unknown")

    roi_percentage = rec.get("roi_percentage", 0)
    payback_months = rec.get("payback_months", 0)

    crb = rec.get("crb_analysis", {})
    if not crb:
        return ValidationResult(is_valid=True)

    cost = crb.get("cost", {})
    benefit = crb.get("benefit", {})

    total_cost = cost.get("total", 0)
    total_benefit = benefit.get("total", 0)

    # Validate ROI bounds (not formula - that may vary by methodology)
    if roi_percentage and roi_percentage > BOUNDS["roi_percentage"]["max"]:
        warnings.append({
            "location": f"recommendation '{rec_id}' → roi_percentage",
            "issue": f"ROI of {roi_percentage}% is unusually high - verify calculation",
        })

    if roi_percentage and roi_percentage < BOUNDS["roi_percentage"]["min"]:
        errors.append({
            "location": f"recommendation '{rec_id}' → roi_percentage",
            "issue": f"ROI cannot be less than {BOUNDS['roi_percentage']['min']}%",
        })

    # Validate payback bounds
    if payback_months and payback_months > BOUNDS["payback_months"]["max"]:
        warnings.append({
            "location": f"recommendation '{rec_id}' → payback_months",
            "issue": f"Payback of {payback_months} months may not justify investment",
        })

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


# ============================================================================
# Structure Validation
# ============================================================================

REQUIRED_SECTIONS = ["company_profile", "executive_summary", "findings", "recommendations"]
REQUIRED_FINDING_FIELDS = ["id", "title", "description", "category"]
REQUIRED_REC_FIELDS = ["id", "title", "description", "priority", "options"]
VALID_CATEGORIES = ["operations", "sales", "customer_experience", "finance", "marketing", "hr", "compliance", "technology"]
VALID_PRIORITIES = ["high", "medium", "low"]
VALID_CONFIDENCE = ["high", "medium", "low"]


def validate_report_structure(report: Dict[str, Any]) -> ValidationResult:
    """Validate report has required structure."""
    errors = []
    warnings = []

    # Check required sections
    for section in REQUIRED_SECTIONS:
        if section not in report or report[section] is None:
            errors.append({
                "location": section,
                "issue": f"Missing required section: '{section}'",
            })

    # Validate executive summary
    exec_summary = report.get("executive_summary", {})
    if exec_summary:
        if "ai_readiness_score" not in exec_summary:
            errors.append({"location": "executive_summary", "issue": "Missing ai_readiness_score"})
        elif not (0 <= exec_summary.get("ai_readiness_score", 0) <= 100):
            errors.append({"location": "executive_summary.ai_readiness_score", "issue": "Must be 0-100"})

        if "verdict" not in exec_summary:
            errors.append({"location": "executive_summary", "issue": "Missing verdict"})

    # Validate findings
    findings = report.get("findings", [])
    if not findings:
        errors.append({"location": "findings", "issue": "At least one finding required"})
    else:
        finding_ids = set()
        for i, finding in enumerate(findings):
            for field in REQUIRED_FINDING_FIELDS:
                if field not in finding:
                    errors.append({"location": f"findings[{i}]", "issue": f"Missing '{field}'"})

            # Check duplicate IDs
            fid = finding.get("id")
            if fid in finding_ids:
                errors.append({"location": f"findings[{i}]", "issue": f"Duplicate ID '{fid}'"})
            finding_ids.add(fid)

            # Check valid category
            cat = finding.get("category")
            if cat and cat not in VALID_CATEGORIES:
                warnings.append({"location": f"findings[{i}]", "issue": f"Unknown category '{cat}'"})

    # Validate recommendations
    recommendations = report.get("recommendations", [])
    if not recommendations:
        errors.append({"location": "recommendations", "issue": "At least one recommendation required"})
    else:
        rec_ids = set()
        for i, rec in enumerate(recommendations):
            for field in REQUIRED_REC_FIELDS:
                if field not in rec:
                    errors.append({"location": f"recommendations[{i}]", "issue": f"Missing '{field}'"})

            rid = rec.get("id")
            if rid in rec_ids:
                errors.append({"location": f"recommendations[{i}]", "issue": f"Duplicate ID '{rid}'"})
            rec_ids.add(rid)

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


# ============================================================================
# Playbook Validation
# ============================================================================

def validate_playbook(playbook: Dict[str, Any]) -> ValidationResult:
    """Validate a single playbook for valid task structure."""
    errors = []
    warnings = []
    playbook_id = playbook.get("id", "unknown")

    phases = playbook.get("phases", [])
    if not phases:
        errors.append({"location": f"playbook '{playbook_id}'", "issue": "No phases defined"})
        return ValidationResult(is_valid=False, errors=errors)

    all_task_ids = set()
    dependency_graph = {}

    for phase in phases:
        tasks = phase.get("tasks", [])
        for task in tasks:
            task_id = task.get("id")
            if not task_id:
                errors.append({"location": f"playbook '{playbook_id}'", "issue": "Task missing 'id'"})
                continue

            if task_id in all_task_ids:
                errors.append({"location": f"playbook '{playbook_id}'", "issue": f"Duplicate task ID '{task_id}'"})
            all_task_ids.add(task_id)

            # Check hours
            hours = task.get("hours", 0)
            if hours < 0.25:
                errors.append({"location": f"task '{task_id}'", "issue": f"Hours ({hours}) too low"})
            elif hours > 40:
                errors.append({"location": f"task '{task_id}'", "issue": f"Hours ({hours}) too high - break into smaller tasks"})

            # Build dependency graph
            deps = task.get("dependencies", [])
            dependency_graph[task_id] = deps

    # Check dependencies exist
    for task_id, deps in dependency_graph.items():
        for dep in deps:
            if dep not in all_task_ids:
                errors.append({"location": f"task '{task_id}'", "issue": f"Dependency '{dep}' not found"})

    # Check for cycles (simple DFS)
    def has_cycle(node: str, visited: set, path: set) -> bool:
        if node in path:
            return True
        if node in visited:
            return False
        visited.add(node)
        path.add(node)
        for dep in dependency_graph.get(node, []):
            if has_cycle(dep, visited, path):
                return True
        path.remove(node)
        return False

    visited = set()
    for task_id in all_task_ids:
        if has_cycle(task_id, visited, set()):
            errors.append({"location": f"playbook '{playbook_id}'", "issue": "Circular dependency detected"})
            break

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


# ============================================================================
# Value Consistency Validation
# ============================================================================

VALUE_TOLERANCE = 0.25  # 25% tolerance for value consistency


def validate_value_consistency(report: Dict[str, Any]) -> ValidationResult:
    """
    Validate that values in executive summary align with findings/recommendations.

    Checks:
    1. total_value_potential aligns with sum of findings
    2. recommended_investment aligns with recommendation costs
    3. top_opportunities are sorted by value
    """
    errors = []
    warnings = []

    exec_summary = report.get("executive_summary", {})
    findings = report.get("findings", [])
    recommendations = report.get("recommendations", [])

    # 1. Validate total_value_potential vs findings sum
    total_value = exec_summary.get("total_value_potential", {})
    projection_years = total_value.get("projection_years", 3)

    # Calculate sum from findings
    findings_annual_total = 0
    for f in findings:
        value_saved = f.get("value_saved", {})
        value_created = f.get("value_created", {})

        annual_savings = value_saved.get("annual_savings", 0) or 0
        potential_revenue = value_created.get("potential_revenue", 0) or 0

        findings_annual_total += annual_savings + potential_revenue

    expected_total_min = findings_annual_total * projection_years * 0.7  # Conservative
    expected_total_max = findings_annual_total * projection_years * 1.3  # Optimistic

    exec_total_min = total_value.get("min", 0)
    exec_total_max = total_value.get("max", 0)

    if findings_annual_total > 0:
        # Check if exec summary total is within reasonable range
        if exec_total_min > 0 and exec_total_min < expected_total_min * (1 - VALUE_TOLERANCE):
            warnings.append({
                "location": "executive_summary.total_value_potential.min",
                "issue": f"Value {exec_total_min} seems low compared to findings sum ({findings_annual_total}/year × {projection_years} years = {findings_annual_total * projection_years})",
                "expected_range": f"{int(expected_total_min)}-{int(expected_total_max)}",
            })
        elif exec_total_max > 0 and exec_total_max > expected_total_max * (1 + VALUE_TOLERANCE):
            warnings.append({
                "location": "executive_summary.total_value_potential.max",
                "issue": f"Value {exec_total_max} seems high compared to findings sum ({findings_annual_total}/year × {projection_years} years = {findings_annual_total * projection_years})",
                "expected_range": f"{int(expected_total_min)}-{int(expected_total_max)}",
            })

    # 2. Validate recommended_investment vs recommendation costs
    rec_investment = exec_summary.get("recommended_investment", {})
    year1_min = rec_investment.get("year_1_min", 0)
    year1_max = rec_investment.get("year_1_max", 0)

    total_rec_cost_min = 0
    total_rec_cost_max = 0

    for rec in recommendations:
        our_rec = rec.get("our_recommendation", "off_the_shelf")
        options = rec.get("options", {})
        option = options.get(our_rec, {})

        if our_rec == "custom_solution":
            cost_range = option.get("estimated_cost", {})
            cost_min = cost_range.get("min", 0) or 0
            cost_max = cost_range.get("max", 0) or 0
            total_rec_cost_min += cost_min
            total_rec_cost_max += cost_max
        else:
            monthly_cost = option.get("monthly_cost", 0) or 0
            impl_weeks = option.get("implementation_weeks", 4) or 4
            # Estimate setup cost as impl_weeks × €500
            setup_cost = impl_weeks * 500
            annual_cost = monthly_cost * 12 + setup_cost
            total_rec_cost_min += annual_cost * 0.8
            total_rec_cost_max += annual_cost * 1.2

    if total_rec_cost_min > 0:
        if year1_min > 0 and year1_min < total_rec_cost_min * (1 - VALUE_TOLERANCE):
            warnings.append({
                "location": "executive_summary.recommended_investment.year_1_min",
                "issue": f"Investment {year1_min} seems low vs recommendation costs ({int(total_rec_cost_min)}-{int(total_rec_cost_max)})",
            })
        if year1_max > 0 and year1_max > total_rec_cost_max * (1 + VALUE_TOLERANCE):
            warnings.append({
                "location": "executive_summary.recommended_investment.year_1_max",
                "issue": f"Investment {year1_max} seems high vs recommendation costs ({int(total_rec_cost_min)}-{int(total_rec_cost_max)})",
            })

    # 3. Validate top_opportunities are sorted by value
    top_opps = exec_summary.get("top_opportunities", [])
    if len(top_opps) >= 2:
        import re

        def extract_value(value_str: str) -> float:
            if not isinstance(value_str, str):
                return 0
            numbers = re.findall(r'[\d,]+(?:\.\d+)?', value_str.replace('K', '000').replace('k', '000'))
            if not numbers:
                return 0
            parsed = []
            for num_str in numbers:
                try:
                    parsed.append(float(num_str.replace(',', '')))
                except ValueError:
                    continue
            if not parsed:
                return 0
            return (parsed[0] + parsed[-1]) / 2 if len(parsed) >= 2 else parsed[0]

        values = [extract_value(opp.get("value_potential", "0")) for opp in top_opps]
        if values != sorted(values, reverse=True):
            warnings.append({
                "location": "executive_summary.top_opportunities",
                "issue": "Opportunities not sorted by value (highest first)",
                "current_order": [opp.get("title", "?") for opp in top_opps[:3]],
            })

    return ValidationResult(is_valid=True, errors=errors, warnings=warnings)


def validate_ai_readiness_breakdown(report: Dict[str, Any]) -> ValidationResult:
    """
    Validate AI readiness breakdown is present and consistent.
    """
    errors = []
    warnings = []

    exec_summary = report.get("executive_summary", {})
    ai_score = exec_summary.get("ai_readiness_score", 0)
    breakdown = exec_summary.get("ai_readiness_breakdown", {})

    if not breakdown:
        warnings.append({
            "location": "executive_summary.ai_readiness_breakdown",
            "issue": "Missing AI readiness breakdown - score explanation unavailable",
        })
        return ValidationResult(is_valid=True, errors=errors, warnings=warnings)

    # Check breakdown totals match score
    components = breakdown.get("components", {})
    component_total = sum(
        comp.get("score", 0)
        for comp in components.values()
        if isinstance(comp, dict)
    )

    breakdown_total = breakdown.get("total_score", 0)

    if breakdown_total != ai_score:
        errors.append({
            "location": "executive_summary.ai_readiness_score",
            "issue": f"Score ({ai_score}) doesn't match breakdown total ({breakdown_total})",
        })

    if component_total != breakdown_total:
        errors.append({
            "location": "executive_summary.ai_readiness_breakdown.components",
            "issue": f"Component sum ({component_total}) doesn't match total ({breakdown_total})",
        })

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


# ============================================================================
# Main Validation Function
# ============================================================================

def validate_report(report: Dict[str, Any], default_hourly_rate: float = 50) -> ValidationResult:
    """
    Run all deterministic validations on a report.

    This should be called before saving a report to catch issues early.

    Args:
        report: The full report dictionary
        default_hourly_rate: Industry-aware hourly rate for math validation

    Returns:
        ValidationResult with is_valid, errors, and warnings
    """
    result = ValidationResult(is_valid=True)

    # 1. Structure validation
    structure_result = validate_report_structure(report)
    result = result.merge(structure_result)

    # 2. Math validation for findings
    for finding in report.get("findings", []):
        finding_result = validate_finding_math(finding, default_hourly_rate=default_hourly_rate)
        result = result.merge(finding_result)

    # 3. Math validation for recommendations
    for rec in report.get("recommendations", []):
        rec_result = validate_recommendation_math(rec)
        result = result.merge(rec_result)

    # 4. Playbook validation
    for playbook in report.get("playbooks", []):
        playbook_result = validate_playbook(playbook)
        result = result.merge(playbook_result)

    # 5. Value consistency validation (NEW)
    value_result = validate_value_consistency(report)
    result = result.merge(value_result)

    # 6. AI readiness breakdown validation (NEW)
    ai_result = validate_ai_readiness_breakdown(report)
    result = result.merge(ai_result)

    # Log summary
    if result.is_valid:
        logger.info(f"Report validation passed ({len(result.warnings)} warnings)")
    else:
        logger.warning(f"Report validation failed: {len(result.errors)} errors, {len(result.warnings)} warnings")
        for error in result.errors:
            logger.warning(f"  Validation error: {error}")

    return result


def validate_report_strict(report: Dict[str, Any]) -> ValidationResult:
    """
    Strict validation that treats warnings as errors.

    Use this for final reports going to customers.
    """
    result = validate_report(report)

    # Convert warnings to errors
    if result.warnings:
        return ValidationResult(
            is_valid=False,
            errors=result.errors + [{"issue": w.get("issue", str(w)), "location": w.get("location", "unknown")} for w in result.warnings],
            warnings=[],
        )

    return result
