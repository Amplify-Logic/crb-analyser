"""Guardrails for RLS hardening migration content."""

from pathlib import Path


MIGRATION_PATH = (
    Path(__file__).resolve().parent.parent
    / "supabase"
    / "migrations"
    / "027_rls_policy_hardening.sql"
)


def _read_migration() -> str:
    assert MIGRATION_PATH.exists(), f"Missing migration: {MIGRATION_PATH}"
    return MIGRATION_PATH.read_text(encoding="utf-8")


def test_hardening_migration_exists() -> None:
    """The policy-hardening migration must exist in version control."""
    assert MIGRATION_PATH.exists()


def test_service_policies_require_service_role() -> None:
    """Critical service policies must require service_role."""
    sql = _read_migration()

    required_policy_snippets = [
        'CREATE POLICY "quiz_sessions_update_service"',
        'CREATE POLICY "reports_service_all"',
        'CREATE POLICY "vendors_update_service"',
        'CREATE POLICY "industry_tiers_update_service"',
        'CREATE POLICY "report_conversations_service_all"',
        'CREATE POLICY "report_messages_service_all"',
    ]
    for snippet in required_policy_snippets:
        assert snippet in sql

    assert "auth.role() = 'service_role'" in sql


def test_hardening_migration_avoids_permissive_true_clauses() -> None:
    """The hardening migration should not reintroduce open true/true policies."""
    sql = _read_migration()

    assert "USING (true)" not in sql
    assert "WITH CHECK (true)" not in sql


def test_refiner_select_policies_bind_to_user_context() -> None:
    """Refiner read policies must tie access to report owner/workspace."""
    sql = _read_migration()

    assert 'CREATE POLICY "report_conversations_select"' in sql
    assert 'CREATE POLICY "report_messages_select"' in sql
    assert "qs.user_id = auth.uid()" in sql
    assert "u.id = auth.uid()" in sql
