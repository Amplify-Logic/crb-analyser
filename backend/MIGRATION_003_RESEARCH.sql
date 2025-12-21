-- =============================================================================
-- CRB ANALYSER - MIGRATION 003: RESEARCH INTEGRATION
-- Adds columns for pre-research agent functionality
-- Run this in Supabase SQL Editor
-- =============================================================================

-- Add progress tracking columns
ALTER TABLE quiz_sessions
ADD COLUMN IF NOT EXISTS current_section INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS current_question INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

-- Add research-related columns
ALTER TABLE quiz_sessions
ADD COLUMN IF NOT EXISTS research_id UUID,
ADD COLUMN IF NOT EXISTS research_status TEXT DEFAULT 'not_started'
    CHECK (research_status IN ('not_started', 'pending', 'researching', 'generating_questions', 'complete', 'failed')),
ADD COLUMN IF NOT EXISTS company_name TEXT,
ADD COLUMN IF NOT EXISTS company_website TEXT,
ADD COLUMN IF NOT EXISTS company_profile JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS dynamic_questionnaire JSONB DEFAULT '{}'::jsonb;

-- Add index for research lookups
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_research_id ON quiz_sessions(research_id);
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_research_status ON quiz_sessions(research_status);

-- Update the status check constraint to include 'in_progress'
-- First drop the existing constraint
ALTER TABLE quiz_sessions DROP CONSTRAINT IF EXISTS quiz_sessions_status_check;

-- Add the updated constraint with 'in_progress' status
ALTER TABLE quiz_sessions ADD CONSTRAINT quiz_sessions_status_check
    CHECK (status IN ('in_progress', 'pending_payment', 'paid', 'expired', 'completed'));

-- =============================================================================
-- DONE!
-- =============================================================================

SELECT 'SUCCESS: Research columns added to quiz_sessions!' as result;
