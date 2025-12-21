"""
Database migration system for CRB Analyser.
Handles schema versioning and migration execution.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

from supabase import Client

logger = logging.getLogger(__name__)


class Migrator:
    """Handles database migrations for Supabase/PostgreSQL."""

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.migrations_dir = Path(__file__).parent / "versions"

    async def ensure_migrations_table(self) -> None:
        """Create schema_migrations table if it doesn't exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            checksum VARCHAR(64)
        );
        """
        try:
            # Use RPC to execute raw SQL
            self.supabase.rpc("exec_sql", {"sql": create_table_sql}).execute()
            logger.info("Ensured schema_migrations table exists")
        except Exception as e:
            # Table might already exist or we need alternative approach
            logger.warning(f"Could not create migrations table via RPC: {e}")
            # Try direct table check
            try:
                self.supabase.table("schema_migrations").select("version").limit(1).execute()
                logger.info("schema_migrations table already exists")
            except Exception:
                logger.error("schema_migrations table does not exist and cannot be created")
                raise RuntimeError(
                    "Please create schema_migrations table manually in Supabase:\n"
                    "CREATE TABLE schema_migrations (version VARCHAR(255) PRIMARY KEY, "
                    "applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), checksum VARCHAR(64));"
                )

    def get_applied_migrations(self) -> set[str]:
        """Get list of already applied migrations."""
        try:
            result = self.supabase.table("schema_migrations").select("version").execute()
            return {m["version"] for m in result.data}
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return set()

    def get_pending_migrations(self) -> list[Path]:
        """Get migration files that haven't been applied yet."""
        if not self.migrations_dir.exists():
            logger.warning(f"Migrations directory not found: {self.migrations_dir}")
            return []

        applied = self.get_applied_migrations()
        migration_files = sorted(self.migrations_dir.glob("*.sql"))

        pending = []
        for migration_file in migration_files:
            version = migration_file.stem  # e.g., "001_initial_schema"
            if version not in applied:
                pending.append(migration_file)

        return pending

    def _compute_checksum(self, content: str) -> str:
        """Compute SHA256 checksum of migration content."""
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    async def run_migration(self, migration_file: Path) -> bool:
        """Execute a single migration file."""
        version = migration_file.stem
        sql_content = migration_file.read_text()
        checksum = self._compute_checksum(sql_content)

        logger.info(f"Running migration: {version}")

        try:
            # Execute the migration SQL
            # Note: This requires a stored procedure 'exec_sql' in Supabase
            # or you need to use the PostgreSQL connection directly
            self.supabase.rpc("exec_sql", {"sql": sql_content}).execute()

            # Record successful migration
            self.supabase.table("schema_migrations").insert({
                "version": version,
                "applied_at": datetime.utcnow().isoformat(),
                "checksum": checksum
            }).execute()

            logger.info(f"Migration {version} completed successfully")
            return True

        except Exception as e:
            logger.error(f"Migration {version} failed: {e}")
            return False

    async def run_all_pending(self) -> tuple[int, int]:
        """
        Run all pending migrations.
        Returns: (successful_count, failed_count)
        """
        await self.ensure_migrations_table()

        pending = self.get_pending_migrations()
        if not pending:
            logger.info("No pending migrations")
            return (0, 0)

        logger.info(f"Found {len(pending)} pending migrations")

        successful = 0
        failed = 0

        for migration_file in pending:
            if await self.run_migration(migration_file):
                successful += 1
            else:
                failed += 1
                # Stop on first failure to maintain consistency
                logger.error("Stopping migrations due to failure")
                break

        return (successful, failed)

    def status(self) -> dict:
        """Get migration status."""
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()

        return {
            "applied_count": len(applied),
            "pending_count": len(pending),
            "applied": sorted(list(applied)),
            "pending": [p.stem for p in pending]
        }
