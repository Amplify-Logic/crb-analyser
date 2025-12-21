-- ============================================================================
-- MIGRATION 006: Assumption Validation Sessions
-- ============================================================================
-- This migration creates the table for tracking assumption validation sessions
-- that occur between quiz completion and final report generation.
-- ============================================================================

-- Create validation_sessions table
CREATE TABLE IF NOT EXISTS validation_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    quiz_session_id UUID REFERENCES quiz_sessions(id) ON DELETE CASCADE,

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'abandoned')),

    -- Assumptions data
    assumptions JSONB DEFAULT '[]'::jsonb,
    validated_assumptions JSONB DEFAULT '[]'::jsonb,  -- Array of assumption IDs
    corrected_values JSONB DEFAULT '{}'::jsonb,  -- Map of assumption_id -> corrected value

    -- Conversation history
    messages JSONB DEFAULT '[]'::jsonb,
    questions_asked INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Add validation_session_id to quiz_sessions if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'quiz_sessions' AND column_name = 'validation_session_id'
    ) THEN
        ALTER TABLE quiz_sessions ADD COLUMN validation_session_id UUID REFERENCES validation_sessions(id);
    END IF;
END $$;

-- Add validated_assumptions to quiz_sessions if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'quiz_sessions' AND column_name = 'validated_assumptions'
    ) THEN
        ALTER TABLE quiz_sessions ADD COLUMN validated_assumptions JSONB DEFAULT '[]'::jsonb;
    END IF;
END $$;

-- Add corrected_values to quiz_sessions if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'quiz_sessions' AND column_name = 'corrected_values'
    ) THEN
        ALTER TABLE quiz_sessions ADD COLUMN corrected_values JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- Add assumption_log to reports if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reports' AND column_name = 'assumption_log'
    ) THEN
        ALTER TABLE reports ADD COLUMN assumption_log JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_validation_sessions_quiz_session
    ON validation_sessions(quiz_session_id);
CREATE INDEX IF NOT EXISTS idx_validation_sessions_status
    ON validation_sessions(status);
CREATE INDEX IF NOT EXISTS idx_validation_sessions_created
    ON validation_sessions(created_at);

-- Enable RLS
ALTER TABLE validation_sessions ENABLE ROW LEVEL SECURITY;

-- RLS Policies (validation sessions are tied to quiz sessions, which have their own auth)
CREATE POLICY "Users can view own validation sessions" ON validation_sessions
    FOR SELECT
    USING (
        quiz_session_id IN (
            SELECT id FROM quiz_sessions
            WHERE email = auth.jwt() ->> 'email'
        )
    );

CREATE POLICY "Users can insert own validation sessions" ON validation_sessions
    FOR INSERT
    WITH CHECK (
        quiz_session_id IN (
            SELECT id FROM quiz_sessions
            WHERE email = auth.jwt() ->> 'email'
        )
    );

CREATE POLICY "Users can update own validation sessions" ON validation_sessions
    FOR UPDATE
    USING (
        quiz_session_id IN (
            SELECT id FROM quiz_sessions
            WHERE email = auth.jwt() ->> 'email'
        )
    );

-- Service role can do everything
CREATE POLICY "Service role has full access to validation sessions" ON validation_sessions
    FOR ALL
    USING (auth.role() = 'service_role');

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_validation_session_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_validation_session_timestamp ON validation_sessions;
CREATE TRIGGER trigger_validation_session_timestamp
    BEFORE UPDATE ON validation_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_validation_session_timestamp();

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE validation_sessions IS 'Stores assumption validation conversations between quiz and report generation';
COMMENT ON COLUMN validation_sessions.assumptions IS 'Array of assumption objects extracted from quiz data';
COMMENT ON COLUMN validation_sessions.validated_assumptions IS 'Array of assumption IDs that have been validated';
COMMENT ON COLUMN validation_sessions.corrected_values IS 'Map of assumption_id to user-provided corrected values';
COMMENT ON COLUMN validation_sessions.messages IS 'Full conversation history for the validation session';
