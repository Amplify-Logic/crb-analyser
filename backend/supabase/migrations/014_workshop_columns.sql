-- backend/supabase/migrations/014_workshop_columns.sql
-- Add workshop columns to quiz_sessions table
-- Run this in Supabase SQL Editor

-- 1. Add columns
ALTER TABLE quiz_sessions
ADD COLUMN IF NOT EXISTS workshop_phase TEXT;

ALTER TABLE quiz_sessions
ADD COLUMN IF NOT EXISTS workshop_data JSONB DEFAULT '{}'::jsonb;

ALTER TABLE quiz_sessions
ADD COLUMN IF NOT EXISTS workshop_confidence JSONB DEFAULT '{}'::jsonb;

ALTER TABLE quiz_sessions
ADD COLUMN IF NOT EXISTS workshop_started_at TIMESTAMPTZ;

ALTER TABLE quiz_sessions
ADD COLUMN IF NOT EXISTS workshop_completed_at TIMESTAMPTZ;

-- 2. Add CHECK constraint on workshop_phase (separate from column creation)
DO $$
BEGIN
    ALTER TABLE quiz_sessions
    ADD CONSTRAINT quiz_sessions_workshop_phase_check
    CHECK (workshop_phase IS NULL OR workshop_phase IN ('confirmation', 'deepdive', 'synthesis', 'complete'));
EXCEPTION WHEN duplicate_object THEN
    -- Constraint already exists, skip
    NULL;
END $$;

-- 3. Index for querying active workshops
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_workshop_phase
ON quiz_sessions(workshop_phase)
WHERE workshop_phase IS NOT NULL;

-- 4. Notify PostgREST to reload schema cache
NOTIFY pgrst, 'reload schema';

-- Comments
COMMENT ON COLUMN quiz_sessions.workshop_phase IS 'Current phase: confirmation, deepdive, synthesis, complete';
COMMENT ON COLUMN quiz_sessions.workshop_data IS 'All workshop session data including signals, deep-dives, milestones';
COMMENT ON COLUMN quiz_sessions.workshop_confidence IS 'Enhanced confidence scores for report readiness';

-- Rollback:
-- ALTER TABLE quiz_sessions DROP CONSTRAINT IF EXISTS quiz_sessions_workshop_phase_check;
-- ALTER TABLE quiz_sessions DROP COLUMN IF EXISTS workshop_phase;
-- ALTER TABLE quiz_sessions DROP COLUMN IF EXISTS workshop_data;
-- ALTER TABLE quiz_sessions DROP COLUMN IF EXISTS workshop_confidence;
-- ALTER TABLE quiz_sessions DROP COLUMN IF EXISTS workshop_started_at;
-- ALTER TABLE quiz_sessions DROP COLUMN IF EXISTS workshop_completed_at;
-- DROP INDEX IF EXISTS idx_quiz_sessions_workshop_phase;
