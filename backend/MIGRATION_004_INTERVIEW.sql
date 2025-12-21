-- =============================================================================
-- CRB ANALYSER - MIGRATION 004: INTERVIEW INTEGRATION
-- Adds columns for post-payment AI interview functionality
-- Run this in Supabase SQL Editor
-- =============================================================================

-- Add interview-related columns
ALTER TABLE quiz_sessions
ADD COLUMN IF NOT EXISTS interview_completed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS interview_data JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS interview_started_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS interview_completed_at TIMESTAMPTZ;

-- Add index for interview lookups
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_interview_completed ON quiz_sessions(interview_completed);

-- =============================================================================
-- DONE!
-- =============================================================================

SELECT 'SUCCESS: Interview columns added to quiz_sessions!' as result;
