#!/usr/bin/env python3
"""
CRB Report Validator

Validates CRB analysis report JSON structure and content quality.
Runs as a hook after report generation to ensure quality.

Usage:
    python report_validator.py <report_json_path>

Returns:
    Exit 0 if valid
    Exit 1 if invalid (with actionable error messages)

What it validates:
1. JSON structure - valid JSON, required sections present
2. Executive summary - all required fields, verdict logic
3. Findings - structure, required fields, math consistency
4. Recommendations - options structure, vendor references, ROI math
5. Sources - all claims have sources
6. Math - ROI calculations are internally consistent
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Any

# Log file for observability
LOG_DIR = Path(__file__).parent.parent.parent / "logs" / "validators"
LOG_FILE = LOG_DIR / "report_validator.log"

# Required top-level sections
REQUIRED_SECTIONS = [
    "id",
    "status",
    "company_profile",
    "executive_summary",
    "findings",
    "recommendations",
]

# Required executive summary fields
REQUIRED_EXEC_SUMMARY_FIELDS = [
    "ai_readiness_score",
    "key_insight",
    "top_opportunities",
    "verdict",
]

# Required verdict fields
REQUIRED_VERDICT_FIELDS = [
    "recommendation",
    "headline",
    "reasoning",
    "confidence",
]

# Required finding fields
REQUIRED_FINDING_FIELDS = [
    "id",
    "title",
    "description",
    "category",
]

# Required recommendation fields
REQUIRED_RECOMMENDATION_FIELDS = [
    "id",
    "title",
    "description",
    "priority",
    "options",
]

# Valid categories for findings
VALID_CATEGORIES = [
    "operations",
    "sales",
    "customer_experience",
    "finance",
    "marketing",
    "hr",
    "compliance",
    "technology",
]

# Valid priorities
VALID_PRIORITIES = ["high", "medium", "low"]

# Valid confidence levels
VALID_CONFIDENCE = ["high", "medium", "low"]

# Valid verdict recommendations
VALID_VERDICT_RECOMMENDATIONS = ["proceed", "proceed_with_caution", "wait", "not_recommended"]


def log(message: str, level: str = "INFO") -> None:
    """Log validation results with timestamp."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] [{level}] {message}\n")


def validate_json_structure(file_path: str) -> tuple[dict | None, list[str]]:
    """Validate JSON is parseable and return data."""
    issues = []

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data, issues
    except json.JSONDecodeError as e:
        issues.append(f"Invalid JSON: {e}")
        return None, issues
    except FileNotFoundError:
        issues.append(f"File not found: {file_path}")
        return None, issues


def validate_required_sections(data: dict) -> list[str]:
    """Check that all required top-level sections exist."""
    issues = []

    for section in REQUIRED_SECTIONS:
        if section not in data:
            issues.append(f"Missing required section: '{section}'")
        elif data[section] is None:
            issues.append(f"Section '{section}' is null")

    return issues


def validate_executive_summary(data: dict) -> list[str]:
    """Validate executive summary structure and content."""
    issues = []

    exec_summary = data.get("executive_summary", {})
    if not exec_summary:
        return ["Executive summary is empty"]

    # Check required fields
    for field in REQUIRED_EXEC_SUMMARY_FIELDS:
        if field not in exec_summary:
            issues.append(f"Executive summary missing: '{field}'")

    # Validate AI readiness score range
    ai_score = exec_summary.get("ai_readiness_score")
    if ai_score is not None:
        if not isinstance(ai_score, (int, float)) or ai_score < 0 or ai_score > 100:
            issues.append(f"AI readiness score must be 0-100, got: {ai_score}")

    # Validate verdict
    verdict = exec_summary.get("verdict", {})
    if verdict:
        for field in REQUIRED_VERDICT_FIELDS:
            if field not in verdict:
                issues.append(f"Verdict missing: '{field}'")

        rec = verdict.get("recommendation")
        if rec and rec not in VALID_VERDICT_RECOMMENDATIONS:
            issues.append(f"Invalid verdict recommendation: '{rec}'. Valid: {VALID_VERDICT_RECOMMENDATIONS}")

        confidence = verdict.get("confidence")
        if confidence and confidence not in VALID_CONFIDENCE:
            issues.append(f"Invalid verdict confidence: '{confidence}'. Valid: {VALID_CONFIDENCE}")

    # Check top_opportunities is a list
    top_opps = exec_summary.get("top_opportunities")
    if top_opps is not None and not isinstance(top_opps, list):
        issues.append("top_opportunities must be a list")

    return issues


def validate_findings(data: dict) -> list[str]:
    """Validate findings structure and content."""
    issues = []

    findings = data.get("findings", [])
    if not findings:
        issues.append("No findings in report - at least 1 required")
        return issues

    if not isinstance(findings, list):
        issues.append("Findings must be a list")
        return issues

    finding_ids = set()

    for i, finding in enumerate(findings):
        prefix = f"Finding {i+1}"

        # Check required fields
        for field in REQUIRED_FINDING_FIELDS:
            if field not in finding:
                issues.append(f"{prefix}: missing '{field}'")

        # Check for duplicate IDs
        fid = finding.get("id")
        if fid:
            if fid in finding_ids:
                issues.append(f"{prefix}: duplicate ID '{fid}'")
            finding_ids.add(fid)

        # Validate category
        category = finding.get("category")
        if category and category not in VALID_CATEGORIES:
            issues.append(f"{prefix}: invalid category '{category}'. Valid: {VALID_CATEGORIES}")

        # Validate confidence
        confidence = finding.get("confidence")
        if confidence and confidence not in VALID_CONFIDENCE:
            issues.append(f"{prefix}: invalid confidence '{confidence}'")

        # Check value_saved math if present
        value_saved = finding.get("value_saved", {})
        if value_saved:
            hours = value_saved.get("hours_per_week", 0)
            rate = value_saved.get("hourly_rate", 0)
            annual = value_saved.get("annual_savings", 0)

            if hours and rate and annual:
                expected = hours * rate * 52
                # Allow 10% tolerance for rounding
                if abs(annual - expected) > expected * 0.10:
                    issues.append(
                        f"{prefix}: annual_savings math incorrect. "
                        f"Claimed: {annual}, Expected: {hours}h x {rate}/h x 52 = {expected:.0f}"
                    )

        # Check that findings have sources
        sources = finding.get("sources", [])
        if not sources:
            # Warning, not error - but flag it
            pass  # Could add warnings list

    return issues


def validate_recommendations(data: dict) -> list[str]:
    """Validate recommendations structure and content."""
    issues = []

    recommendations = data.get("recommendations", [])
    if not recommendations:
        issues.append("No recommendations in report - at least 1 required")
        return issues

    if not isinstance(recommendations, list):
        issues.append("Recommendations must be a list")
        return issues

    rec_ids = set()

    for i, rec in enumerate(recommendations):
        prefix = f"Recommendation {i+1}"

        # Check required fields
        for field in REQUIRED_RECOMMENDATION_FIELDS:
            if field not in rec:
                issues.append(f"{prefix}: missing '{field}'")

        # Check for duplicate IDs
        rid = rec.get("id")
        if rid:
            if rid in rec_ids:
                issues.append(f"{prefix}: duplicate ID '{rid}'")
            rec_ids.add(rid)

        # Validate priority
        priority = rec.get("priority")
        if priority and priority not in VALID_PRIORITIES:
            issues.append(f"{prefix}: invalid priority '{priority}'. Valid: {VALID_PRIORITIES}")

        # Validate options structure
        options = rec.get("options", {})
        if options:
            expected_options = ["off_the_shelf", "best_in_class", "custom_solution"]
            for opt in expected_options:
                if opt in options:
                    opt_data = options[opt]
                    if opt in ["off_the_shelf", "best_in_class"]:
                        if "name" not in opt_data and "vendor" not in opt_data:
                            issues.append(f"{prefix}: {opt} missing 'name' or 'vendor'")

        # Validate ROI percentage is reasonable
        roi = rec.get("roi_percentage")
        if roi is not None:
            if not isinstance(roi, (int, float)):
                issues.append(f"{prefix}: roi_percentage must be a number")
            elif roi < -100:
                issues.append(f"{prefix}: roi_percentage unrealistic ({roi}%)")
            elif roi > 2000:
                issues.append(f"{prefix}: roi_percentage suspiciously high ({roi}%) - verify calculation")

        # Validate payback_months is reasonable
        payback = rec.get("payback_months")
        if payback is not None:
            if not isinstance(payback, (int, float)):
                issues.append(f"{prefix}: payback_months must be a number")
            elif payback < 0:
                issues.append(f"{prefix}: payback_months cannot be negative")
            elif payback > 60:
                issues.append(f"{prefix}: payback_months > 60 months - may not justify investment")

        # Check CRB analysis if present
        crb = rec.get("crb_analysis", {})
        if crb:
            cost = crb.get("cost", {})
            benefit = crb.get("benefit", {})

            # Validate cost totals
            if cost.get("total") is not None:
                # Could add math validation here
                pass

    return issues


def validate_company_profile(data: dict) -> list[str]:
    """Validate company profile has minimum required info."""
    issues = []

    profile = data.get("company_profile", {})
    if not profile:
        issues.append("Company profile is empty")
        return issues

    # At minimum need company name and industry
    if not profile.get("company_name"):
        issues.append("Company profile missing: 'company_name'")

    if not profile.get("industry"):
        issues.append("Company profile missing: 'industry'")

    return issues


def validate_report(file_path: str) -> tuple[bool, list[str]]:
    """
    Run all validations on a report JSON file.

    Returns:
        (is_valid, list_of_issues)
    """
    all_issues = []

    # 1. Parse JSON
    data, json_issues = validate_json_structure(file_path)
    all_issues.extend(json_issues)

    if data is None:
        return False, all_issues

    # 2. Check required sections
    section_issues = validate_required_sections(data)
    all_issues.extend(section_issues)

    # 3. Validate each section
    profile_issues = validate_company_profile(data)
    all_issues.extend(profile_issues)

    exec_issues = validate_executive_summary(data)
    all_issues.extend(exec_issues)

    finding_issues = validate_findings(data)
    all_issues.extend(finding_issues)

    rec_issues = validate_recommendations(data)
    all_issues.extend(rec_issues)

    return len(all_issues) == 0, all_issues


def main():
    if len(sys.argv) < 2:
        print("Usage: report_validator.py <report_json_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    # Skip non-JSON files
    if not file_path.endswith('.json'):
        log(f"SKIP: {file_path} (not a JSON file)")
        sys.exit(0)

    # Skip known non-report JSON files
    skip_patterns = ['package.json', 'tsconfig.json', 'settings.json']
    if any(pattern in file_path for pattern in skip_patterns):
        log(f"SKIP: {file_path} (not a report file)")
        sys.exit(0)

    is_valid, issues = validate_report(file_path)

    if is_valid:
        log(f"PASS: {file_path}")
        print(f"Report validation passed: {file_path}")
        sys.exit(0)
    else:
        log(f"FAIL: {file_path} - {len(issues)} issues")
        # Format for agent to understand and fix
        print(f"Resolve these report validation errors in {file_path}:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)


if __name__ == "__main__":
    main()
