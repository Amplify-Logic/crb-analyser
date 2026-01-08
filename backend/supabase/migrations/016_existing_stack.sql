-- Migration: 016_existing_stack.sql
-- Description: Add existing_stack column for Connect vs Replace feature
-- Date: 2026-01-07

-- Add existing_stack column to quiz_sessions
-- Stores user's current software tools for Connect vs Replace recommendations
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'quiz_sessions'
        AND column_name = 'existing_stack'
    ) THEN
        ALTER TABLE quiz_sessions ADD COLUMN existing_stack JSONB DEFAULT '[]';
    END IF;
END $$;

-- Comment on new column
COMMENT ON COLUMN quiz_sessions.existing_stack IS 'User existing software stack for Connect vs Replace recommendations. Structure: [{slug, source: "selected"|"free_text", name?}]';

-- ============================================================================
-- ROLLBACK
-- ============================================================================
-- To rollback this migration, run:
-- ALTER TABLE quiz_sessions DROP COLUMN IF EXISTS existing_stack;
