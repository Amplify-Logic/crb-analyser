"""
Run database migration via Supabase API.

Usage:
    cd backend
    python -m src.scripts.run_migration
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.supabase_client import get_async_supabase


async def run_migration():
    """Execute the vector embeddings migration."""

    migration_path = Path(__file__).parent.parent.parent / "supabase" / "migrations" / "008_vector_embeddings.sql"

    if not migration_path.exists():
        print(f"Migration file not found: {migration_path}")
        return False

    print(f"Reading migration: {migration_path}")

    with open(migration_path, 'r') as f:
        sql = f.read()

    # Split into individual statements (rough split on semicolons outside of functions)
    # For complex migrations with functions, we'll run as one block

    print("Connecting to Supabase...")
    supabase = await get_async_supabase()

    print("Running migration...")

    try:
        # Try running the full migration
        # Note: Supabase Python client doesn't have direct SQL execution
        # We'll use the REST API for this

        result = await supabase.rpc("exec_sql", {"sql": sql}).execute()
        print(f"Migration result: {result}")
        return True

    except Exception as e:
        error_msg = str(e)

        if "function" in error_msg.lower() and "does not exist" in error_msg.lower():
            print("\n" + "="*60)
            print("MANUAL MIGRATION REQUIRED")
            print("="*60)
            print("\nThe Supabase Python client cannot execute DDL statements directly.")
            print("\nPlease run the migration manually:")
            print("\n1. Go to your Supabase dashboard")
            print("2. Navigate to SQL Editor")
            print("3. Copy and paste the contents of:")
            print(f"   {migration_path}")
            print("4. Click 'Run'")
            print("\n" + "="*60)
            return False
        else:
            print(f"Migration error: {e}")
            return False


if __name__ == "__main__":
    asyncio.run(run_migration())
