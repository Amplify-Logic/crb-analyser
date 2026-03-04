"""
Check migration source-of-truth consistency.

Enforces:
- Supabase migrations directory is the active migration source.
- No new SQL migrations are added to legacy src/migrations/versions.
- Supabase migration version prefixes are unique.
"""

from pathlib import Path
import re
import sys


def _version_prefix(filename: str) -> int | None:
    match = re.match(r"^(\d+)_", filename)
    if not match:
        return None
    return int(match.group(1))


def main() -> int:
    backend_root = Path(__file__).resolve().parents[2]
    supabase_dir = backend_root / "supabase" / "migrations"
    legacy_dir = backend_root / "src" / "migrations" / "versions"

    issues: list[str] = []

    if not supabase_dir.exists():
        issues.append(f"Missing migrations directory: {supabase_dir}")
        supabase_files: list[Path] = []
    else:
        supabase_files = sorted(supabase_dir.glob("*.sql"))
        if not supabase_files:
            issues.append("No SQL migrations found in backend/supabase/migrations")

    legacy_files = sorted(legacy_dir.glob("*.sql")) if legacy_dir.exists() else []
    legacy_allowed = {"001_initial_schema.sql", "004_playbook_progress.sql"}
    unexpected_legacy = [f.name for f in legacy_files if f.name not in legacy_allowed]
    if unexpected_legacy:
        issues.append(
            "Legacy migration directory contains unexpected files: "
            + ", ".join(unexpected_legacy)
        )

    supabase_versions = [v for v in (_version_prefix(f.name) for f in supabase_files) if v is not None]
    if len(supabase_versions) != len(set(supabase_versions)):
        issues.append("Duplicate numeric version prefixes detected in Supabase migrations")

    legacy_versions = [v for v in (_version_prefix(f.name) for f in legacy_files) if v is not None]
    if legacy_versions and supabase_versions:
        if max(supabase_versions) < max(legacy_versions):
            issues.append(
                "Supabase migration versions lag behind legacy versions "
                f"(max supabase={max(supabase_versions)}, max legacy={max(legacy_versions)})"
            )

    if issues:
        print("Migration drift check failed:")
        for issue in issues:
            print(f"- {issue}")
        print(
            "\nUse backend/supabase/migrations as source-of-truth and apply with:\n"
            "  supabase db push"
        )
        return 1

    print("Migration drift check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
