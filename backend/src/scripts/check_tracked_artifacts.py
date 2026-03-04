"""Fail CI if generated/sensitive artifacts are tracked by git."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


DENYLIST_PATTERNS = [
    re.compile(r"^test-results/"),
    re.compile(r"(^|/)\.playwright-cli/"),
    re.compile(r"^screenshots/"),
    re.compile(r"^backend/reports/"),
    re.compile(r"^backend/gtd/"),
    re.compile(r"^backend/bonbon_.*\.(json|txt)$"),
    re.compile(r"^backend/.*_debug_output\.txt$"),
]


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def get_tracked_files(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    repo_root = get_repo_root()
    tracked = get_tracked_files(repo_root)

    violations = [
        path for path in tracked if any(pattern.search(path) for pattern in DENYLIST_PATTERNS)
    ]

    if violations:
        print("Tracked generated/sensitive artifacts detected:")
        for path in sorted(violations):
            print(f"- {path}")
        print("\nMove these artifacts out of git tracking or update workflows accordingly.")
        return 1

    print("Artifact denylist check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
