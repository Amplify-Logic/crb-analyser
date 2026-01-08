-- ============================================================================
-- MIGRATION 017: Add automation_summary column to reports
-- ============================================================================
-- Adds automation_summary column for the "Your Automation Roadmap" section
-- This stores the Connect vs Replace summary generated from findings
-- See: docs/plans/2026-01-07-connect-vs-replace-design.md
-- ============================================================================

-- Add automation_summary to reports if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reports' AND column_name = 'automation_summary'
    ) THEN
        ALTER TABLE reports ADD COLUMN automation_summary JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON COLUMN reports.automation_summary IS 'Automation roadmap summary with stack assessment, Connect vs Replace opportunities, and tier-aware next steps';
