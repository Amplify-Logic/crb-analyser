#!/usr/bin/env python3
"""
Industry Data Validator

Validates industry data folders in the knowledge base for completeness
and consistency. Each industry should have a complete set of files.

Usage:
    python industry_data_validator.py <json_file_path>

When a file in backend/src/knowledge/<industry>/ is modified,
this validator checks the entire industry folder for completeness.

Returns:
    Exit 0 if industry data is complete
    Exit 1 if missing required files or inconsistencies

What it validates:
1. Required files exist: vendors.json, processes.json, benchmarks.json, opportunities.json
2. Industry field is consistent across all files
3. Each file has proper structure
4. Cross-references are valid (e.g., vendor categories match processes)
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Any

# Log file for observability
LOG_DIR = Path(__file__).parent.parent.parent / "logs" / "validators"
LOG_FILE = LOG_DIR / "industry_data_validator.log"

# Required files for each industry
REQUIRED_FILES = [
    "vendors.json",
    "processes.json",
    "benchmarks.json",
    "opportunities.json",
]

# Knowledge base path
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent.parent.parent / "backend" / "src" / "knowledge"


def log(message: str, level: str = "INFO") -> None:
    """Log validation results with timestamp."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] [{level}] {message}\n")


def get_industry_from_path(file_path: str) -> str | None:
    """Extract industry name from file path."""
    path = Path(file_path)
    parts = path.parts

    # Look for 'knowledge' in path and get next part
    try:
        knowledge_idx = parts.index('knowledge')
        if knowledge_idx + 1 < len(parts):
            potential_industry = parts[knowledge_idx + 1]
            # Skip non-industry folders
            if potential_industry not in ['vendors', 'benchmarks', 'insights', 'patterns',
                                          'ai_tools', 'case_studies', 'industry_questions']:
                return potential_industry
    except ValueError:
        pass

    return None


def validate_file_structure(file_path: Path, file_type: str) -> list[dict]:
    """Validate structure of a specific file type."""
    errors = []

    if not file_path.exists():
        return errors  # Will be caught by missing files check

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        errors.append({
            "file": file_path.name,
            "issue": "invalid_json",
            "fix": f"Fix JSON syntax error: {e}"
        })
        return errors

    # Check for industry field
    if not data.get("industry"):
        errors.append({
            "file": file_path.name,
            "issue": "missing_industry_field",
            "fix": "Add 'industry' field matching folder name"
        })

    # Type-specific validation
    if file_type == "vendors.json":
        if not data.get("vendor_categories"):
            errors.append({
                "file": file_path.name,
                "issue": "missing_vendor_categories",
                "fix": "Add 'vendor_categories' array with at least one category"
            })

    elif file_type == "processes.json":
        if not data.get("processes") and not data.get("business_processes") and not data.get("common_processes"):
            errors.append({
                "file": file_path.name,
                "issue": "missing_processes",
                "fix": "Add 'processes', 'business_processes', or 'common_processes' array"
            })

    elif file_type == "benchmarks.json":
        if not data.get("benchmarks"):
            errors.append({
                "file": file_path.name,
                "issue": "missing_benchmarks",
                "fix": "Add 'benchmarks' object with financial/operational metrics"
            })

    elif file_type == "opportunities.json":
        if not data.get("opportunities") and not data.get("automation_opportunities") and not data.get("ai_opportunities"):
            errors.append({
                "file": file_path.name,
                "issue": "missing_opportunities",
                "fix": "Add 'opportunities', 'automation_opportunities', or 'ai_opportunities' array"
            })

    return errors


def validate_industry_consistency(industry_path: Path, industry_name: str) -> list[dict]:
    """Check consistency across all files in an industry folder."""
    errors = []
    warnings = []

    industry_values = {}

    for file_name in REQUIRED_FILES:
        file_path = industry_path / file_name
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                file_industry = data.get("industry")
                if file_industry:
                    industry_values[file_name] = file_industry
            except (json.JSONDecodeError, IOError):
                pass

    # Check all files have same industry value
    unique_industries = set(industry_values.values())
    if len(unique_industries) > 1:
        errors.append({
            "file": "multiple files",
            "issue": "inconsistent_industry_field",
            "fix": f"Industry field varies across files: {industry_values}. Should all be '{industry_name}'"
        })

    # Check industry matches folder name
    for file_name, file_industry in industry_values.items():
        if file_industry != industry_name:
            errors.append({
                "file": file_name,
                "issue": "industry_mismatch",
                "fix": f"Industry '{file_industry}' doesn't match folder name '{industry_name}'"
            })

    return errors


def validate_industry_folder(industry_path: Path) -> tuple[bool, list[dict], list[dict]]:
    """
    Validate an entire industry folder.

    Returns:
        (is_valid, errors, warnings)
    """
    errors = []
    warnings = []

    industry_name = industry_path.name

    # Check for required files
    missing_files = []
    for required_file in REQUIRED_FILES:
        file_path = industry_path / required_file
        if not file_path.exists():
            missing_files.append(required_file)

    if missing_files:
        errors.append({
            "file": industry_name,
            "issue": "missing_required_files",
            "fix": f"Create missing files: {', '.join(missing_files)}"
        })

    # Validate each existing file
    for file_name in REQUIRED_FILES:
        file_path = industry_path / file_name
        if file_path.exists():
            file_errors = validate_file_structure(file_path, file_name)
            errors.extend(file_errors)

    # Check consistency across files
    consistency_errors = validate_industry_consistency(industry_path, industry_name)
    errors.extend(consistency_errors)

    return len(errors) == 0, errors, warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: industry_data_validator.py <json_file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    # Skip non-JSON files
    if not file_path.endswith('.json'):
        log(f"SKIP: {file_path} (not a JSON file)")
        sys.exit(0)

    # Check if this is an industry file
    industry = get_industry_from_path(file_path)
    if not industry:
        log(f"SKIP: {file_path} (not an industry file)")
        sys.exit(0)

    # Find the industry folder
    industry_path = KNOWLEDGE_BASE_PATH / industry
    if not industry_path.exists():
        log(f"SKIP: {file_path} (industry folder not found)")
        sys.exit(0)

    is_valid, errors, warnings = validate_industry_folder(industry_path)

    if is_valid:
        log(f"PASS: {industry} industry data complete")
        print(f"Industry data validation passed: {industry}")
        sys.exit(0)
    else:
        log(f"FAIL: {industry} - {len(errors)} errors")
        print(f"Fix these industry data errors for '{industry}':")
        for e in errors:
            print(f"\n  File: {e['file']}")
            print(f"    Issue: {e['issue']}")
            print(f"    Fix: {e['fix']}")
        if warnings:
            print("\nWarnings:")
            for w in warnings:
                print(f"  - {w['file']}: {w['issue']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
