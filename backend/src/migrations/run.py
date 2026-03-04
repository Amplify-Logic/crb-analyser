#!/usr/bin/env python
"""
CLI script to run database migrations.

Usage:
    python -m src.migrations.run [status|drift-check]
"""

import sys
import asyncio
import logging

from src.config.supabase_client import get_supabase
from src.migrations.migrator import Migrator
from src.scripts.check_migration_drift import main as run_drift_check

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_status():
    """Show migration status."""
    supabase = get_supabase()
    migrator = Migrator(supabase)

    status = migrator.status()

    print("\n=== Migration Status ===")
    print(f"Applied: {status['applied_count']}")
    print(f"Pending: {status['pending_count']}")

    if status['applied']:
        print("\nApplied migrations:")
        for m in status['applied']:
            print(f"  - {m}")

    if status['pending']:
        print("\nPending migrations:")
        for m in status['pending']:
            print(f"  - {m}")

    print()


async def run_migrate():
    """Deprecated migration command."""
    print(
        "\nDirect SQL execution from Python is deprecated.\n"
        "Use Supabase CLI for migrations:\n"
        "  supabase db push\n"
    )
    sys.exit(1)


async def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.migrations.run [status|drift-check|migrate]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "status":
        await run_status()
    elif command == "drift-check":
        exit_code = run_drift_check()
        sys.exit(exit_code)
    elif command == "migrate":
        await run_migrate()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: status, drift-check, migrate")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
