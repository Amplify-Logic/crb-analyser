#!/usr/bin/env python3
"""
Benchmark Source Validator

Validates that all benchmarks in knowledge base files have proper sources.
Every stat needs a source and verification date for credibility.

Usage:
    python benchmark_source_validator.py <json_file_path>

Returns:
    Exit 0 if all sources present
    Exit 1 if missing sources (with specific items to fix)

What it validates:
1. Top-level verification_status and verified_date
2. Each benchmark has a "source" field
3. Verification dates are not stale (> 180 days)
4. Source URLs are present where claimed
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any

# Log file for observability
LOG_DIR = Path(__file__).parent.parent.parent / "logs" / "validators"
LOG_FILE = LOG_DIR / "benchmark_source_validator.log"

# Stale threshold
STALE_DAYS = 180  # 6 months


def log(message: str, level: str = "INFO") -> None:
    """Log validation results with timestamp."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] [{level}] {message}\n")


def parse_date(date_str: str) -> datetime | None:
    """Parse date in various formats."""
    if not date_str:
        return None
    formats = ["%Y-%m-%d", "%Y-%m", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str[:len(fmt.replace('%', '').replace('-', '').replace(':', '').replace('.', '').replace('T', ''))], fmt)
        except (ValueError, TypeError):
            continue
    # Try simpler parsing
    try:
        if len(date_str) == 7:  # YYYY-MM format
            return datetime.strptime(date_str, "%Y-%m")
        elif len(date_str) >= 10:
            return datetime.strptime(date_str[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        pass
    return None


def check_staleness(date_str: str, threshold_days: int = STALE_DAYS) -> tuple[bool, int]:
    """Check if a date is stale. Returns (is_stale, days_old)."""
    date = parse_date(date_str)
    if not date:
        return True, -1  # Can't parse = treat as stale
    days_old = (datetime.now() - date).days
    return days_old > threshold_days, days_old


def find_missing_sources(obj: Any, path: str = "") -> list[dict]:
    """Recursively find benchmark entries missing sources."""
    issues = []

    if isinstance(obj, dict):
        # Check if this looks like a benchmark entry (has numeric values but no source)
        has_numeric = any(isinstance(v, (int, float)) for v in obj.values())
        has_source = "source" in obj or "source_url" in obj
        has_nested = any(isinstance(v, dict) for v in obj.values())

        # If it has numeric data but no source and isn't a container
        if has_numeric and not has_source and not has_nested:
            # Check if parent path suggests it's a benchmark
            if any(kw in path.lower() for kw in ['benchmark', 'stat', 'metric', 'rate', 'percentage', 'revenue', 'cost', 'margin']):
                issues.append({
                    "path": path,
                    "issue": "missing_source",
                    "fix": f"Add 'source' field with citation"
                })

        # Check nested
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key
            issues.extend(find_missing_sources(value, new_path))

    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            new_path = f"{path}[{i}]"
            issues.extend(find_missing_sources(item, new_path))

    return issues


def validate_benchmark_file(file_path: str) -> tuple[bool, list[dict], list[dict]]:
    """
    Validate benchmark sources in a JSON file.

    Returns:
        (is_valid, errors, warnings)
    """
    errors = []
    warnings = []

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [{"path": "file", "issue": "invalid_json", "fix": str(e)}], []
    except FileNotFoundError:
        return False, [{"path": "file", "issue": "not_found", "fix": f"File not found: {file_path}"}], []

    # Check top-level verification status
    verification_status = data.get("verification_status")
    if verification_status == "UNVERIFIED":
        warnings.append({
            "path": "verification_status",
            "issue": "unverified_data",
            "fix": "Mark as VERIFIED after confirming sources, or add verification_note explaining why"
        })
    elif not verification_status:
        errors.append({
            "path": "verification_status",
            "issue": "missing_verification_status",
            "fix": "Add 'verification_status': 'VERIFIED' or 'UNVERIFIED'"
        })

    # Check verified_date / last_updated
    verified_date = data.get("verified_date") or data.get("last_updated")
    if not verified_date:
        errors.append({
            "path": "verified_date",
            "issue": "missing_date",
            "fix": "Add 'verified_date': 'YYYY-MM-DD' with date sources were verified"
        })
    else:
        is_stale, days_old = check_staleness(verified_date)
        if is_stale and days_old > 0:
            warnings.append({
                "path": "verified_date",
                "issue": f"stale_data ({days_old} days old)",
                "fix": f"Data verified {days_old} days ago - consider refreshing (threshold: {STALE_DAYS} days)"
            })

    # Check for verification_sources (top-level)
    if data.get("verification_status") == "VERIFIED" and not data.get("verification_sources"):
        warnings.append({
            "path": "verification_sources",
            "issue": "missing_verification_sources",
            "fix": "Add 'verification_sources': ['url1', 'url2'] listing where data was verified"
        })

    # Check benchmarks section if present
    benchmarks = data.get("benchmarks", {})
    if benchmarks:
        for category, metrics in benchmarks.items():
            if isinstance(metrics, dict):
                for metric_name, metric_data in metrics.items():
                    if isinstance(metric_data, dict):
                        # Check for source
                        if not metric_data.get("source"):
                            errors.append({
                                "path": f"benchmarks.{category}.{metric_name}",
                                "issue": "missing_source",
                                "fix": f"Add 'source' field citing where this data came from"
                            })

                        # Check if verified flag matches actual state
                        if metric_data.get("verified") is False or metric_data.get("status") == "ESTIMATE":
                            warnings.append({
                                "path": f"benchmarks.{category}.{metric_name}",
                                "issue": "unverified_metric",
                                "fix": "Verify this metric or mark prominently in reports"
                            })

    # Find any other missing sources in nested structures
    nested_issues = find_missing_sources(data)
    for issue in nested_issues:
        if issue not in errors:  # Avoid duplicates
            warnings.append(issue)

    return len(errors) == 0, errors, warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: benchmark_source_validator.py <json_file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    # Skip non-JSON files
    if not file_path.endswith('.json'):
        log(f"SKIP: {file_path} (not a JSON file)")
        sys.exit(0)

    # Only validate benchmark files
    benchmark_patterns = ['benchmarks.json', 'benchmark', '/knowledge/']
    if not any(pattern in file_path for pattern in benchmark_patterns):
        log(f"SKIP: {file_path} (not a benchmark file)")
        sys.exit(0)

    # Skip certain file types
    skip_patterns = ['package.json', 'tsconfig.json', 'settings.json']
    if any(pattern in file_path for pattern in skip_patterns):
        log(f"SKIP: {file_path}")
        sys.exit(0)

    is_valid, errors, warnings = validate_benchmark_file(file_path)

    if is_valid and not warnings:
        log(f"PASS: {file_path}")
        print(f"Benchmark source validation passed: {file_path}")
        sys.exit(0)
    elif is_valid:
        log(f"PASS with warnings: {file_path} - {len(warnings)} warnings")
        print(f"Benchmark validation passed with warnings: {file_path}")
        print("\nWarnings (non-blocking):")
        for w in warnings:
            print(f"  - {w['path']}: {w['issue']}")
            print(f"    Fix: {w['fix']}")
        sys.exit(0)
    else:
        log(f"FAIL: {file_path} - {len(errors)} errors, {len(warnings)} warnings")
        print(f"Fix these benchmark source errors in {file_path}:")
        for e in errors:
            print(f"\n  Path: {e['path']}")
            print(f"    Issue: {e['issue']}")
            print(f"    Fix: {e['fix']}")
        if warnings:
            print("\nWarnings (non-blocking):")
            for w in warnings:
                print(f"  - {w['path']}: {w['issue']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
