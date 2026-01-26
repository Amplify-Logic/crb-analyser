#!/usr/bin/env python3
"""
CRB Vendor Data Validator

Validates vendor JSON files in the knowledge base.
Ensures data quality for vendor recommendations.

Usage:
    python vendor_validator.py <vendor_json_path>

Returns:
    Exit 0 if valid
    Exit 1 if invalid (with actionable error messages)

What it validates:
1. JSON structure - valid JSON
2. Required fields - industry, vendor_categories
3. Vendor structure - name, website, pricing
4. Pricing verification - dates not stale (>90 days)
5. URL format - basic website validation
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any

# Log file for observability
LOG_DIR = Path(__file__).parent.parent.parent / "logs" / "validators"
LOG_FILE = LOG_DIR / "vendor_validator.log"

# Stale threshold (days since pricing verified)
STALE_THRESHOLD_DAYS = 90

# Required vendor fields
REQUIRED_VENDOR_FIELDS = ["name", "website"]

# Required category fields
REQUIRED_CATEGORY_FIELDS = ["category", "name", "vendors"]

# Valid company sizes
VALID_COMPANY_SIZES = ["startup", "smb", "mid-market", "enterprise"]


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


def validate_website(website: str) -> bool:
    """Basic website validation."""
    if not website:
        return False
    # Allow domain names with or without protocol
    pattern = r'^[a-zA-Z0-9][-a-zA-Z0-9]*(\.[a-zA-Z0-9][-a-zA-Z0-9]*)+$'
    # Strip protocol if present
    website = re.sub(r'^https?://', '', website)
    website = website.rstrip('/')
    return bool(re.match(pattern, website))


def parse_verified_date(date_str: str) -> datetime | None:
    """Parse verification date in various formats."""
    formats = [
        "%Y-%m",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str[:len(fmt.replace('%', ''))], fmt)
        except (ValueError, TypeError):
            continue
    return None


def validate_vendor(vendor: dict, category_name: str, warnings: list[str]) -> list[str]:
    """Validate individual vendor entry."""
    issues = []
    vendor_name = vendor.get("name", "Unknown")
    prefix = f"Vendor '{vendor_name}' in {category_name}"

    # Check required fields
    for field in REQUIRED_VENDOR_FIELDS:
        if not vendor.get(field):
            issues.append(f"{prefix}: missing '{field}'")

    # Validate website format
    website = vendor.get("website", "")
    if website and not validate_website(website):
        issues.append(f"{prefix}: invalid website format '{website}'")

    # Check pricing exists
    pricing = vendor.get("pricing")
    if not pricing:
        warnings.append(f"{prefix}: missing pricing information")

    # Check pricing verification date staleness
    verified_date_str = vendor.get("pricing_verified_date")
    if verified_date_str:
        verified_date = parse_verified_date(verified_date_str)
        if verified_date:
            days_old = (datetime.now() - verified_date).days
            if days_old > STALE_THRESHOLD_DAYS:
                warnings.append(
                    f"{prefix}: pricing verified {days_old} days ago "
                    f"(threshold: {STALE_THRESHOLD_DAYS} days) - consider refreshing"
                )

    # Validate company_sizes if present
    company_sizes = vendor.get("company_sizes", [])
    for size in company_sizes:
        if size not in VALID_COMPANY_SIZES:
            warnings.append(f"{prefix}: unknown company size '{size}'")

    return issues


def validate_category(category: dict, warnings: list[str]) -> list[str]:
    """Validate vendor category."""
    issues = []
    cat_name = category.get("name", category.get("category", "Unknown"))
    prefix = f"Category '{cat_name}'"

    # Check required fields
    for field in REQUIRED_CATEGORY_FIELDS:
        if field not in category:
            issues.append(f"{prefix}: missing '{field}'")

    # Validate vendors list
    vendors = category.get("vendors", [])
    if not vendors:
        warnings.append(f"{prefix}: no vendors listed")
    elif not isinstance(vendors, list):
        issues.append(f"{prefix}: vendors must be a list")
    else:
        for vendor in vendors:
            vendor_issues = validate_vendor(vendor, cat_name, warnings)
            issues.extend(vendor_issues)

    return issues


def validate_vendor_file(file_path: str) -> tuple[bool, list[str], list[str]]:
    """
    Run all validations on a vendor JSON file.

    Returns:
        (is_valid, list_of_issues, list_of_warnings)
    """
    issues = []
    warnings = []

    # 1. Parse JSON
    data, json_issues = validate_json_structure(file_path)
    issues.extend(json_issues)

    if data is None:
        return False, issues, warnings

    # 2. Check for industry field
    if not data.get("industry"):
        issues.append("Missing 'industry' field")

    # 3. Check verification status
    status = data.get("verification_status")
    if status == "UNVERIFIED":
        warnings.append("Data marked as UNVERIFIED - pricing needs verification")

    # 4. Check last_updated
    last_updated = data.get("last_updated")
    if last_updated:
        updated_date = parse_verified_date(last_updated)
        if updated_date:
            days_old = (datetime.now() - updated_date).days
            if days_old > STALE_THRESHOLD_DAYS:
                warnings.append(f"File last updated {days_old} days ago - consider refreshing")

    # 5. Validate vendor categories
    categories = data.get("vendor_categories", [])
    if not categories:
        issues.append("No vendor_categories found")
    elif not isinstance(categories, list):
        issues.append("vendor_categories must be a list")
    else:
        for category in categories:
            cat_issues = validate_category(category, warnings)
            issues.extend(cat_issues)

    return len(issues) == 0, issues, warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: vendor_validator.py <vendor_json_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    # Skip non-JSON files
    if not file_path.endswith('.json'):
        log(f"SKIP: {file_path} (not a JSON file)")
        sys.exit(0)

    # Only validate vendor files
    if 'vendor' not in file_path.lower():
        log(f"SKIP: {file_path} (not a vendor file)")
        sys.exit(0)

    is_valid, issues, warnings = validate_vendor_file(file_path)

    if is_valid:
        log(f"PASS: {file_path} ({len(warnings)} warnings)")
        print(f"Vendor validation passed: {file_path}")
        if warnings:
            print("\nWarnings (non-blocking):")
            for warning in warnings:
                print(f"  - {warning}")
        sys.exit(0)
    else:
        log(f"FAIL: {file_path} - {len(issues)} issues, {len(warnings)} warnings")
        print(f"Resolve these vendor validation errors in {file_path}:")
        for issue in issues:
            print(f"  - {issue}")
        if warnings:
            print("\nWarnings (non-blocking):")
            for warning in warnings:
                print(f"  - {warning}")
        sys.exit(1)


if __name__ == "__main__":
    main()
