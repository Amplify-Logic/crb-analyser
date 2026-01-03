-- backend/supabase/migrations/014_workshop_columns.sql
-- Add workshop columns to quiz_sessions table

-- Workshop phase tracking
ALTER TABLE quiz_sessions
ADD COLUMN IF NOT EXISTS workshop_phase TEXT
CHECK (workshop_phase IN ('confirmation', 'deepdive', 'synthesis', 'complete'));

-- Workshop data (all session data as JSONB)
ALTER TABLE quiz_sessions
ADD COLUMN IF NOT EXISTS workshop_data JSONB DEFAULT '{}'::jsonb;

-- Workshop confidence scores (enhanced framework)
ALTER TABLE quiz_sessions
ADD COLUMN IF NOT EXISTS workshop_confidence JSONB DEFAULT '{}'::jsonb;

-- Workshop timestamps
ALTER TABLE quiz_sessions
ADD COLUMN IF NOT EXISTS workshop_started_at TIMESTAMPTZ;

ALTER TABLE quiz_sessions
ADD COLUMN IF NOT EXISTS workshop_completed_at TIMESTAMPTZ;

-- Index for querying active workshops
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_workshop_phase
ON quiz_sessions(workshop_phase)
WHERE workshop_phase IS NOT NULL;

-- Comments
COMMENT ON COLUMN quiz_sessions.workshop_phase IS 'Current phase: confirmation, deepdive, synthesis, complete';
COMMENT ON COLUMN quiz_sessions.workshop_data IS 'All workshop session data including signals, deep-dives, milestones';
COMMENT ON COLUMN quiz_sessions.workshop_confidence IS 'Enhanced confidence scores for report readiness';

-- Rollback:
-- ALTER TABLE quiz_sessions DROP COLUMN IF EXISTS workshop_phase;
-- ALTER TABLE quiz_sessions DROP COLUMN IF EXISTS workshop_data;
-- ALTER TABLE quiz_sessions DROP COLUMN IF EXISTS workshop_confidence;
-- ALTER TABLE quiz_sessions DROP COLUMN IF EXISTS workshop_started_at;
-- ALTER TABLE quiz_sessions DROP COLUMN IF EXISTS workshop_completed_at;
-- DROP INDEX IF EXISTS idx_quiz_sessions_workshop_phase;
