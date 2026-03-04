"""
Deprecated migration runner.

Use Supabase CLI for schema changes:
    supabase db push

Use this script only for migration drift checks:
    python -m src.scripts.check_migration_drift
"""

from src.scripts.check_migration_drift import main


if __name__ == "__main__":
    raise SystemExit(main())
