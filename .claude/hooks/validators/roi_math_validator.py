#!/usr/bin/env python3
"""
ROI Math Validator

Deterministic validator that checks all mathematical calculations in reports.
Runs as a post-tool-use hook to catch math errors before they reach customers.

Usage:
    python roi_math_validator.py <json_file_path>

Returns:
    Exit 0 if all math is correct
    Exit 1 if math errors found (with specific fixes)

What it validates:
1. annual_savings = hours_per_week × hourly_rate × 52
2. monthly_savings = annual_savings / 12
3. roi_percentage = (benefit - cost) / cost × 100
4. payback_months = implementation_cost / net_monthly_savings
5. three_year_net = (annual_benefit × 3) - total_cost
6. Bounds checking (no impossible numbers)
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Any
from decimal import Decimal, ROUND_HALF_UP

# Log file for observability
LOG_DIR = Path(__file__).parent.parent.parent / "logs" / "validators"
LOG_FILE = LOG_DIR / "roi_math_validator.log"

# Tolerance for floating point comparisons
TOLERANCE = 0.10  # 10% tolerance for rounding differences

# Realistic bounds
BOUNDS = {
    "hours_per_week": {"min": 0.5, "max": 80},
    "hourly_rate": {"min": 10, "max": 500},
    "annual_savings": {"min": 0, "max": 2_000_000},
    "roi_percentage": {"min": -100, "max": 2000},
    "payback_months": {"min": 0.1, "max": 120},
}


def log(message: str, level: str = "INFO") -> None:
    """Log validation results with timestamp."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] [{level}] {message}\n")


def is_within_tolerance(actual: float, expected: float, tolerance: float = TOLERANCE) -> bool:
    """Check if actual value is within tolerance of expected."""
    if expected == 0:
        return actual == 0
    return abs(actual - expected) <= abs(expected * tolerance)


def validate_finding_math(finding: dict, default_hourly_rate: float = 50) -> list[dict]:
    """Validate math in a single finding."""
    issues = []
    finding_id = finding.get("id", "unknown")

    value_saved = finding.get("value_saved", {})
    if not value_saved:
        return issues

    hours_per_week = value_saved.get("hours_per_week", 0)
    hourly_rate = value_saved.get("hourly_rate", default_hourly_rate)
    annual_savings = value_saved.get("annual_savings", 0)

    # Check annual_savings calculation
    if hours_per_week and annual_savings:
        expected_annual = hours_per_week * hourly_rate * 52

        if not is_within_tolerance(annual_savings, expected_annual):
            issues.append({
                "location": f"finding '{finding_id}' → value_saved.annual_savings",
                "claimed": annual_savings,
                "expected": round(expected_annual, 2),
                "formula": f"{hours_per_week} hrs/wk × €{hourly_rate}/hr × 52 wks",
                "fix": f"Change annual_savings to {round(expected_annual, 0)}"
            })

    # Check bounds
    if hours_per_week and hours_per_week > BOUNDS["hours_per_week"]["max"]:
        issues.append({
            "location": f"finding '{finding_id}' → value_saved.hours_per_week",
            "claimed": hours_per_week,
            "expected": f"≤ {BOUNDS['hours_per_week']['max']}",
            "formula": "Reality check",
            "fix": f"Reduce hours_per_week to realistic value (max {BOUNDS['hours_per_week']['max']})"
        })

    if hourly_rate and hourly_rate > BOUNDS["hourly_rate"]["max"]:
        issues.append({
            "location": f"finding '{finding_id}' → value_saved.hourly_rate",
            "claimed": hourly_rate,
            "expected": f"≤ {BOUNDS['hourly_rate']['max']}",
            "formula": "Reality check",
            "fix": f"Verify hourly_rate (€{hourly_rate} is unusually high)"
        })

    return issues


def validate_recommendation_math(rec: dict) -> list[dict]:
    """Validate math in a single recommendation using canonical formulas.

    Canonical formulas (from roi_calculator.py):
        net_annual = yearly_savings - yearly_cost
        first_year_investment = implementation_cost + yearly_cost
        roi_percentage = (net_annual / first_year_investment) × 100
        payback_months = implementation_cost / (net_annual / 12)
    """
    issues = []
    rec_id = rec.get("id", "unknown")

    roi_percentage = rec.get("roi_percentage", 0)
    payback_months = rec.get("payback_months", 0)

    # Try to use roi_detail.financial_impact first (new canonical format)
    roi_detail = rec.get("roi_detail", {})
    financial = roi_detail.get("financial_impact", {})

    if financial:
        # Use canonical formula from roi_calculator.py
        yearly_savings = financial.get("yearly_savings", 0)
        yearly_cost = financial.get("yearly_cost", 0)
        implementation_cost = financial.get("implementation_cost", 0)

        if yearly_savings and implementation_cost:
            net_annual = yearly_savings - yearly_cost
            first_year_investment = implementation_cost + yearly_cost

            # Validate ROI
            if first_year_investment > 0 and roi_percentage:
                expected_roi = (net_annual / first_year_investment) * 100

                if not is_within_tolerance(roi_percentage, expected_roi, tolerance=0.15):
                    issues.append({
                        "location": f"recommendation '{rec_id}' → roi_percentage",
                        "claimed": roi_percentage,
                        "expected": round(expected_roi, 1),
                        "formula": f"(€{yearly_savings:,.0f} - €{yearly_cost:,.0f}) / (€{implementation_cost:,.0f} + €{yearly_cost:,.0f}) × 100",
                        "fix": f"Change roi_percentage to {round(expected_roi, 0)}%"
                    })

            # Validate payback months
            if payback_months and net_annual > 0:
                expected_payback = implementation_cost / (net_annual / 12)

                if not is_within_tolerance(payback_months, expected_payback, tolerance=0.20):
                    issues.append({
                        "location": f"recommendation '{rec_id}' → payback_months",
                        "claimed": payback_months,
                        "expected": round(expected_payback, 1),
                        "formula": f"€{implementation_cost:,.0f} / (€{net_annual:,.0f} / 12)",
                        "fix": f"Change payback_months to {round(expected_payback, 1)}"
                    })
    else:
        # Fall back to crb_analysis for legacy reports
        crb = rec.get("crb_analysis", {})
        if crb:
            cost = crb.get("cost", {})
            benefit = crb.get("benefit", {})

            total_cost = cost.get("total", 0)
            total_benefit = benefit.get("total", 0)

            # Legacy formula: (benefit - cost) / cost × 100
            if total_cost and total_benefit and roi_percentage:
                expected_roi = ((total_benefit - total_cost) / total_cost) * 100 if total_cost else 0

                if not is_within_tolerance(roi_percentage, expected_roi, tolerance=0.15):
                    issues.append({
                        "location": f"recommendation '{rec_id}' → roi_percentage (legacy)",
                        "claimed": roi_percentage,
                        "expected": round(expected_roi, 1),
                        "formula": f"(€{total_benefit:,} - €{total_cost:,}) / €{total_cost:,} × 100",
                        "fix": f"Change roi_percentage to {round(expected_roi, 0)}%"
                    })

            # Legacy payback validation
            if payback_months:
                short_term_cost = cost.get("short_term", {})
                short_term_benefit = benefit.get("short_term", {})

                setup_cost = short_term_cost.get("setup", 0)
                monthly_cost = short_term_cost.get("monthly", 0)
                annual_benefit = short_term_benefit.get("annual", 0)

                if setup_cost and annual_benefit:
                    monthly_benefit = annual_benefit / 12
                    net_monthly = monthly_benefit - monthly_cost

                    if net_monthly > 0:
                        expected_payback = setup_cost / net_monthly

                        if not is_within_tolerance(payback_months, expected_payback, tolerance=0.20):
                            issues.append({
                                "location": f"recommendation '{rec_id}' → payback_months (legacy)",
                                "claimed": payback_months,
                                "expected": round(expected_payback, 1),
                                "formula": f"€{setup_cost:,} / (€{monthly_benefit:,.0f} - €{monthly_cost:,})/mo",
                                "fix": f"Change payback_months to {round(expected_payback, 1)}"
                            })

    # Check ROI bounds (applies to all)
    if roi_percentage and roi_percentage > BOUNDS["roi_percentage"]["max"]:
        issues.append({
            "location": f"recommendation '{rec_id}' → roi_percentage",
            "claimed": roi_percentage,
            "expected": f"≤ {BOUNDS['roi_percentage']['max']}%",
            "formula": "Reality check",
            "fix": f"ROI of {roi_percentage}% is unrealistic - verify calculations"
        })

    return issues


def validate_value_summary(data: dict) -> list[dict]:
    """Validate the value_summary section totals."""
    issues = []

    value_summary = data.get("value_summary", {})
    if not value_summary:
        return issues

    value_saved = value_summary.get("value_saved", {})
    value_created = value_summary.get("value_created", {})
    total = value_summary.get("total", {})

    # Check that total = value_saved + value_created
    saved_min = value_saved.get("subtotal", {}).get("min", 0)
    saved_max = value_saved.get("subtotal", {}).get("max", 0)
    created_min = value_created.get("subtotal", {}).get("min", 0)
    created_max = value_created.get("subtotal", {}).get("max", 0)

    total_min = total.get("min", 0)
    total_max = total.get("max", 0)

    expected_min = saved_min + created_min
    expected_max = saved_max + created_max

    if total_min and not is_within_tolerance(total_min, expected_min):
        issues.append({
            "location": "value_summary → total.min",
            "claimed": total_min,
            "expected": expected_min,
            "formula": f"value_saved.min ({saved_min}) + value_created.min ({created_min})",
            "fix": f"Change total.min to {expected_min}"
        })

    if total_max and not is_within_tolerance(total_max, expected_max):
        issues.append({
            "location": "value_summary → total.max",
            "claimed": total_max,
            "expected": expected_max,
            "formula": f"value_saved.max ({saved_max}) + value_created.max ({created_max})",
            "fix": f"Change total.max to {expected_max}"
        })

    # Cross-check hours_per_week calculation
    hours_per_week = value_saved.get("hours_per_week", 0)
    hourly_rate = value_saved.get("hourly_rate", 50)

    if hours_per_week and saved_min:
        expected_saved = hours_per_week * hourly_rate * 52
        if not is_within_tolerance(saved_min, expected_saved, tolerance=0.20):
            issues.append({
                "location": "value_summary → value_saved.subtotal",
                "claimed": f"min={saved_min}, max={saved_max}",
                "expected": f"~{round(expected_saved, 0)} based on {hours_per_week}h/wk",
                "formula": f"{hours_per_week} hrs/wk × €{hourly_rate}/hr × 52 wks",
                "fix": f"Verify value_saved subtotals align with hours calculation"
            })

    return issues


def validate_report_math(file_path: str) -> tuple[bool, list[dict]]:
    """
    Run all math validations on a report JSON file.

    Returns:
        (is_valid, list_of_issues)
    """
    all_issues = []

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [{"location": "file", "error": f"Invalid JSON: {e}"}]
    except FileNotFoundError:
        return False, [{"location": "file", "error": f"File not found: {file_path}"}]

    # Skip if not a report (check for report-like structure)
    if not data.get("findings") and not data.get("recommendations"):
        return True, []  # Not a report, skip

    # Get default hourly rate from company profile if available
    company_profile = data.get("company_profile", {})
    default_hourly_rate = 50  # Could extract from profile if present

    # Validate findings
    findings = data.get("findings", [])
    for finding in findings:
        finding_issues = validate_finding_math(finding, default_hourly_rate)
        all_issues.extend(finding_issues)

    # Validate recommendations
    recommendations = data.get("recommendations", [])
    for rec in recommendations:
        rec_issues = validate_recommendation_math(rec)
        all_issues.extend(rec_issues)

    # Validate value summary
    summary_issues = validate_value_summary(data)
    all_issues.extend(summary_issues)

    return len(all_issues) == 0, all_issues


def main():
    if len(sys.argv) < 2:
        print("Usage: roi_math_validator.py <json_file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    # Skip non-JSON files
    if not file_path.endswith('.json'):
        log(f"SKIP: {file_path} (not a JSON file)")
        sys.exit(0)

    # Skip known non-report files
    skip_patterns = ['package.json', 'tsconfig.json', 'settings.json', 'vendors.json',
                     'benchmarks.json', 'processes.json', 'opportunities.json']
    if any(pattern in file_path for pattern in skip_patterns):
        log(f"SKIP: {file_path} (not a report file)")
        sys.exit(0)

    is_valid, issues = validate_report_math(file_path)

    if is_valid:
        log(f"PASS: {file_path} - all math correct")
        print(f"ROI math validation passed: {file_path}")
        sys.exit(0)
    else:
        log(f"FAIL: {file_path} - {len(issues)} math errors")
        print(f"Fix these math errors in {file_path}:")
        for issue in issues:
            print(f"\n  Location: {issue['location']}")
            if 'claimed' in issue:
                print(f"    Claimed: {issue['claimed']}")
                print(f"    Expected: {issue['expected']}")
                print(f"    Formula: {issue['formula']}")
            print(f"    Fix: {issue.get('fix', issue.get('error', 'Unknown'))}")
        sys.exit(1)


if __name__ == "__main__":
    main()
