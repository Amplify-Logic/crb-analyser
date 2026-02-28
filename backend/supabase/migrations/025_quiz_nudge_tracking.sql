-- Add nudge tracking columns to quiz_sessions for re-engagement emails
-- Rollback: ALTER TABLE quiz_sessions DROP COLUMN IF EXISTS nudge_count, DROP COLUMN IF EXISTS last_nudge_at;

ALTER TABLE quiz_sessions
ADD COLUMN IF NOT EXISTS nudge_count integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_nudge_at timestamptz;

COMMENT ON COLUMN quiz_sessions.nudge_count IS 'Number of re-engagement nudge emails sent (0, 1, or 2)';
COMMENT ON COLUMN quiz_sessions.last_nudge_at IS 'Timestamp of most recent nudge email';
