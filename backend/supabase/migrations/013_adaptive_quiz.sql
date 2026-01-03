-- Adaptive Quiz System
-- Adds columns to quiz_sessions for confidence-driven adaptive questioning

-- Add adaptive quiz columns to quiz_sessions
DO $$
BEGIN
    -- Quiz mode: 'static' (old) or 'adaptive' (new confidence-driven)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'quiz_mode') THEN
        ALTER TABLE quiz_sessions ADD COLUMN quiz_mode TEXT DEFAULT 'static';
    END IF;

    -- Confidence state: tracks scores per category
    -- Structure: {
    --   scores: {category: 0-100},
    --   facts: {category: [{fact, value, confidence, source}]},
    --   gaps: [categories below threshold],
    --   ready_for_teaser: bool,
    --   questions_asked: int
    -- }
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'confidence_state') THEN
        ALTER TABLE quiz_sessions ADD COLUMN confidence_state JSONB;
    END IF;

    -- Adaptive answers: array of Q&A with analysis
    -- Structure: [{
    --   question_id, question, answer, analysis: {extracted_facts, confidence_boosts, signals}
    -- }]
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'adaptive_answers') THEN
        ALTER TABLE quiz_sessions ADD COLUMN adaptive_answers JSONB DEFAULT '[]';
    END IF;

    -- Quiz completion timestamp (separate from payment completion)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'quiz_completed_at') THEN
        ALTER TABLE quiz_sessions ADD COLUMN quiz_completed_at TIMESTAMPTZ;
    END IF;

    -- Interview data: stores voice interview messages and extracted info
    -- Used by both quiz and full workshop
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'interview_data') THEN
        ALTER TABLE quiz_sessions ADD COLUMN interview_data JSONB DEFAULT '{}';
    END IF;

    -- Report ID: links to the generated report after payment
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'report_id') THEN
        ALTER TABLE quiz_sessions ADD COLUMN report_id UUID;
    END IF;
END $$;

-- Update status constraint to include new states
DO $$
BEGIN
    -- Drop existing constraint if it exists
    ALTER TABLE quiz_sessions DROP CONSTRAINT IF EXISTS quiz_sessions_status_check;

    -- Add new constraint with additional states
    ALTER TABLE quiz_sessions ADD CONSTRAINT quiz_sessions_status_check
        CHECK (status IN (
            'in_progress',      -- Quiz in progress
            'quiz_complete',    -- Quiz done, ready for teaser
            'pending_payment',  -- Shown teaser, awaiting payment
            'paid',             -- Payment received
            'generating',       -- Report being generated
            'completed',        -- Report delivered
            'expired',          -- Session expired
            'failed'            -- Something went wrong
        ));
EXCEPTION WHEN OTHERS THEN
    -- Constraint might not exist or have different name, ignore
    NULL;
END $$;

-- Index for finding sessions by quiz mode
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_quiz_mode ON quiz_sessions(quiz_mode);

-- Index for finding sessions with confidence data
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_confidence ON quiz_sessions((confidence_state IS NOT NULL));

-- Comment on new columns
COMMENT ON COLUMN quiz_sessions.quiz_mode IS 'Quiz type: static (form-based) or adaptive (confidence-driven)';
COMMENT ON COLUMN quiz_sessions.confidence_state IS 'Confidence tracker state for adaptive quiz (scores, facts, gaps)';
COMMENT ON COLUMN quiz_sessions.adaptive_answers IS 'Array of Q&A with extracted facts and analysis';
COMMENT ON COLUMN quiz_sessions.quiz_completed_at IS 'When quiz reached confidence thresholds';
COMMENT ON COLUMN quiz_sessions.interview_data IS 'Voice interview messages and extracted data';
COMMENT ON COLUMN quiz_sessions.report_id IS 'Reference to generated report after payment';
