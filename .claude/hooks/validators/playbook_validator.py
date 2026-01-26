#!/usr/bin/env python3
"""
Playbook Task Validator

Validates playbook structure in CRB reports:
- Task dependencies form valid DAG (no cycles)
- Hours estimates are realistic
- All referenced tasks exist
- Phase structure is valid

Usage:
    python playbook_validator.py <json_file_path>

Returns:
    Exit 0 if playbook is valid
    Exit 1 if issues found (with specific fixes)

What it validates:
1. Task IDs are unique within playbook
2. Dependencies reference existing tasks
3. No circular dependencies
4. Hours estimates are realistic (0.5-40 per task)
5. Phase durations match task totals
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Any
from collections import defaultdict

# Log file for observability
LOG_DIR = Path(__file__).parent.parent.parent / "logs" / "validators"
LOG_FILE = LOG_DIR / "playbook_validator.log"

# Realistic bounds for task hours
HOURS_BOUNDS = {
    "min": 0.25,      # 15 minutes minimum
    "max": 40,        # 1 week maximum for single task
    "warning_high": 16,  # Flag tasks > 2 days
}

# Valid difficulty levels
VALID_DIFFICULTIES = ["easy", "medium", "hard"]


def log(message: str, level: str = "INFO") -> None:
    """Log validation results with timestamp."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] [{level}] {message}\n")


def find_cycle(graph: dict[str, list[str]], start: str, visited: set, path: list) -> list | None:
    """DFS to find cycles in dependency graph."""
    if start in path:
        cycle_start = path.index(start)
        return path[cycle_start:] + [start]

    if start in visited:
        return None

    visited.add(start)
    path.append(start)

    for neighbor in graph.get(start, []):
        cycle = find_cycle(graph, neighbor, visited, path.copy())
        if cycle:
            return cycle

    return None


def validate_playbook(playbook: dict, playbook_index: int) -> tuple[list[dict], list[dict]]:
    """Validate a single playbook."""
    errors = []
    warnings = []

    playbook_id = playbook.get("id", f"playbook[{playbook_index}]")
    prefix = f"Playbook '{playbook_id}'"

    phases = playbook.get("phases", [])
    if not phases:
        errors.append({
            "location": prefix,
            "issue": "no_phases",
            "fix": "Add at least one phase with tasks"
        })
        return errors, warnings

    # Collect all task IDs and build dependency graph
    all_task_ids = set()
    dependency_graph = defaultdict(list)
    task_hours = {}

    for phase_idx, phase in enumerate(phases):
        phase_name = phase.get("name") or phase.get("title") or f"phase[{phase_idx}]"
        tasks = phase.get("tasks", [])

        if not tasks:
            warnings.append({
                "location": f"{prefix} → {phase_name}",
                "issue": "empty_phase",
                "fix": "Add tasks to this phase or remove it"
            })
            continue

        phase_total_hours = 0

        for task in tasks:
            task_id = task.get("id")
            task_title = task.get("title", "untitled")

            # Check for task ID
            if not task_id:
                errors.append({
                    "location": f"{prefix} → {phase_name} → '{task_title}'",
                    "issue": "missing_task_id",
                    "fix": "Add unique 'id' field to task"
                })
                continue

            # Check for duplicate IDs
            if task_id in all_task_ids:
                errors.append({
                    "location": f"{prefix} → {phase_name} → task '{task_id}'",
                    "issue": "duplicate_task_id",
                    "fix": f"Task ID '{task_id}' is used multiple times - make IDs unique"
                })
            all_task_ids.add(task_id)

            # Check hours
            hours = task.get("hours", 0)
            task_hours[task_id] = hours

            if hours < HOURS_BOUNDS["min"]:
                errors.append({
                    "location": f"{prefix} → task '{task_id}'",
                    "issue": f"hours_too_low ({hours}h)",
                    "fix": f"Minimum task hours is {HOURS_BOUNDS['min']}h"
                })
            elif hours > HOURS_BOUNDS["max"]:
                errors.append({
                    "location": f"{prefix} → task '{task_id}'",
                    "issue": f"hours_too_high ({hours}h)",
                    "fix": f"Break down tasks > {HOURS_BOUNDS['max']}h into smaller tasks"
                })
            elif hours > HOURS_BOUNDS["warning_high"]:
                warnings.append({
                    "location": f"{prefix} → task '{task_id}'",
                    "issue": f"long_task ({hours}h)",
                    "fix": "Consider breaking this into smaller tasks"
                })

            phase_total_hours += hours

            # Check difficulty
            difficulty = task.get("difficulty")
            if difficulty and difficulty not in VALID_DIFFICULTIES:
                errors.append({
                    "location": f"{prefix} → task '{task_id}'",
                    "issue": f"invalid_difficulty '{difficulty}'",
                    "fix": f"Use one of: {VALID_DIFFICULTIES}"
                })

            # Build dependency graph
            dependencies = task.get("dependencies", [])
            for dep in dependencies:
                dependency_graph[task_id].append(dep)

        # Check phase duration vs task hours
        duration_weeks = phase.get("duration_weeks", 0)
        if duration_weeks:
            expected_hours = duration_weeks * 40  # Assume 40h/week
            if phase_total_hours > expected_hours * 1.5:
                warnings.append({
                    "location": f"{prefix} → {phase_name}",
                    "issue": f"duration_mismatch",
                    "fix": f"Phase has {phase_total_hours}h of tasks but only {duration_weeks} weeks ({expected_hours}h capacity)"
                })

    # Validate dependencies reference existing tasks
    for task_id, deps in dependency_graph.items():
        for dep in deps:
            if dep not in all_task_ids:
                errors.append({
                    "location": f"{prefix} → task '{task_id}'",
                    "issue": f"invalid_dependency '{dep}'",
                    "fix": f"Dependency '{dep}' does not exist - check task ID spelling"
                })

    # Check for circular dependencies
    visited = set()
    for task_id in all_task_ids:
        if task_id not in visited:
            cycle = find_cycle(dependency_graph, task_id, visited, [])
            if cycle:
                errors.append({
                    "location": f"{prefix}",
                    "issue": f"circular_dependency",
                    "fix": f"Circular dependency found: {' → '.join(cycle)}"
                })
                break  # Only report first cycle found

    return errors, warnings


def validate_playbooks_in_report(file_path: str) -> tuple[bool, list[dict], list[dict]]:
    """
    Validate all playbooks in a report JSON file.

    Returns:
        (is_valid, errors, warnings)
    """
    all_errors = []
    all_warnings = []

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [{"location": "file", "issue": "invalid_json", "fix": str(e)}], []
    except FileNotFoundError:
        return False, [{"location": "file", "issue": "not_found", "fix": f"File not found"}], []

    # Check for playbooks
    playbooks = data.get("playbooks", [])
    if not playbooks:
        # Not a report with playbooks, skip
        return True, [], []

    for i, playbook in enumerate(playbooks):
        errors, warnings = validate_playbook(playbook, i)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    return len(all_errors) == 0, all_errors, all_warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: playbook_validator.py <json_file_path>")
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
        log(f"SKIP: {file_path}")
        sys.exit(0)

    is_valid, errors, warnings = validate_playbooks_in_report(file_path)

    if is_valid and not warnings:
        log(f"PASS: {file_path}")
        # Only print if playbooks were found
        with open(file_path, 'r') as f:
            data = json.load(f)
        if data.get("playbooks"):
            print(f"Playbook validation passed: {file_path}")
        sys.exit(0)
    elif is_valid:
        log(f"PASS with warnings: {file_path}")
        print(f"Playbook validation passed with warnings: {file_path}")
        print("\nWarnings:")
        for w in warnings:
            print(f"  - {w['location']}: {w['issue']}")
            print(f"    Fix: {w['fix']}")
        sys.exit(0)
    else:
        log(f"FAIL: {file_path} - {len(errors)} errors")
        print(f"Fix these playbook errors in {file_path}:")
        for e in errors:
            print(f"\n  Location: {e['location']}")
            print(f"    Issue: {e['issue']}")
            print(f"    Fix: {e['fix']}")
        if warnings:
            print("\nWarnings:")
            for w in warnings:
                print(f"  - {w['location']}: {w['issue']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
