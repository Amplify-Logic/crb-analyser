-- Migration: Update status constraints to include QA statuses
-- Required for the human QA review workflow (admin_qa.py)

-- ============================================================================
-- REPORTS TABLE
-- ============================================================================

-- Drop the old constraint
ALTER TABLE reports DROP CONSTRAINT IF EXISTS reports_status_check;

-- Add the new constraint with QA statuses
ALTER TABLE reports ADD CONSTRAINT reports_status_check
    CHECK (status IN (
        'pending',        -- Initial state
        'generating',     -- Report being generated
        'completed',      -- Generation done (legacy, use 'released' for QA flow)
        'failed',         -- Generation failed
        'qa_pending',     -- Awaiting QA review
        'qa_rejected',    -- QA rejected, needs regeneration
        'released'        -- QA approved, visible to customer
    ));

-- Add dev_feedback column if not exists (for DevModePanel feedback storage)
ALTER TABLE reports ADD COLUMN IF NOT EXISTS dev_feedback JSONB;

-- Add index for QA queue queries
CREATE INDEX IF NOT EXISTS idx_reports_qa_status ON reports(status) WHERE status IN ('qa_pending', 'qa_rejected');

COMMENT ON COLUMN reports.status IS 'Report status: pending, generating, completed, failed, qa_pending, qa_rejected, released';
COMMENT ON COLUMN reports.dev_feedback IS 'Dev/admin feedback for Signal Loop learning';

-- ============================================================================
-- QUIZ_SESSIONS TABLE
-- ============================================================================

-- Drop the old constraint
ALTER TABLE quiz_sessions DROP CONSTRAINT IF EXISTS quiz_sessions_status_check;

-- Add the new constraint with QA statuses
ALTER TABLE quiz_sessions ADD CONSTRAINT quiz_sessions_status_check
    CHECK (status IN (
        'pending_payment',  -- Awaiting payment
        'paid',             -- Payment received, ready for generation
        'in_progress',      -- Quiz/interview in progress
        'generating',       -- Report being generated
        'completed',        -- Report generated (legacy)
        'expired',          -- Session expired
        'qa_pending',       -- Report awaiting QA review
        'qa_rejected',      -- Report rejected by QA
        'released'          -- Report approved and released
    ));

COMMENT ON COLUMN quiz_sessions.status IS 'Session status: pending_payment, paid, generating, completed, expired, qa_pending, qa_rejected, released';
