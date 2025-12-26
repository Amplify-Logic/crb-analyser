-- Anonymous Flow Updates
-- Adds columns for research, teaser reports, and proper linking

-- Add research columns (some may already exist, use IF NOT EXISTS pattern)
DO $$
BEGIN
    -- Research data
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'company_name') THEN
        ALTER TABLE quiz_sessions ADD COLUMN company_name TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'company_website') THEN
        ALTER TABLE quiz_sessions ADD COLUMN company_website TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'company_profile') THEN
        ALTER TABLE quiz_sessions ADD COLUMN company_profile JSONB;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'research_id') THEN
        ALTER TABLE quiz_sessions ADD COLUMN research_id UUID;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'research_status') THEN
        ALTER TABLE quiz_sessions ADD COLUMN research_status TEXT DEFAULT 'not_started';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'dynamic_questionnaire') THEN
        ALTER TABLE quiz_sessions ADD COLUMN dynamic_questionnaire JSONB;
    END IF;

    -- Teaser report
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'teaser_report') THEN
        ALTER TABLE quiz_sessions ADD COLUMN teaser_report JSONB;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'teaser_sent_at') THEN
        ALTER TABLE quiz_sessions ADD COLUMN teaser_sent_at TIMESTAMPTZ;
    END IF;

    -- Payment tier
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'tier_purchased') THEN
        ALTER TABLE quiz_sessions ADD COLUMN tier_purchased TEXT;
    END IF;

    -- Progress tracking
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'current_section') THEN
        ALTER TABLE quiz_sessions ADD COLUMN current_section INT DEFAULT 0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'current_question') THEN
        ALTER TABLE quiz_sessions ADD COLUMN current_question INT DEFAULT 0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'completed_at') THEN
        ALTER TABLE quiz_sessions ADD COLUMN completed_at TIMESTAMPTZ;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'updated_at') THEN
        ALTER TABLE quiz_sessions ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
    END IF;

    -- User linking (for post-payment)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'user_id') THEN
        ALTER TABLE quiz_sessions ADD COLUMN user_id UUID;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'workspace_id') THEN
        ALTER TABLE quiz_sessions ADD COLUMN workspace_id UUID;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'audit_id') THEN
        ALTER TABLE quiz_sessions ADD COLUMN audit_id UUID;
    END IF;
END $$;

-- Add workshop columns to audits
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audits' AND column_name = 'workshop_status') THEN
        ALTER TABLE audits ADD COLUMN workshop_status TEXT DEFAULT 'pending';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audits' AND column_name = 'workshop_completed_at') THEN
        ALTER TABLE audits ADD COLUMN workshop_completed_at TIMESTAMPTZ;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audits' AND column_name = 'strategy_call_included') THEN
        ALTER TABLE audits ADD COLUMN strategy_call_included BOOLEAN DEFAULT FALSE;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audits' AND column_name = 'strategy_call_scheduled_at') THEN
        ALTER TABLE audits ADD COLUMN strategy_call_scheduled_at TIMESTAMPTZ;
    END IF;
END $$;

-- Add review columns to reports
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'reports' AND column_name = 'review_status') THEN
        ALTER TABLE reports ADD COLUMN review_status TEXT DEFAULT 'pending';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'reports' AND column_name = 'reviewer_id') THEN
        ALTER TABLE reports ADD COLUMN reviewer_id UUID;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'reports' AND column_name = 'reviewer_notes') THEN
        ALTER TABLE reports ADD COLUMN reviewer_notes TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'reports' AND column_name = 'reviewed_at') THEN
        ALTER TABLE reports ADD COLUMN reviewed_at TIMESTAMPTZ;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'reports' AND column_name = 'published_at') THEN
        ALTER TABLE reports ADD COLUMN published_at TIMESTAMPTZ;
    END IF;
END $$;

-- Create interview_responses table
CREATE TABLE IF NOT EXISTS interview_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_id UUID REFERENCES audits(id) NOT NULL,
    user_id UUID REFERENCES auth.users(id) NOT NULL,

    status TEXT DEFAULT 'not_started',
    current_section INT DEFAULT 0,
    current_question INT DEFAULT 0,
    estimated_time_remaining INT,

    responses JSONB DEFAULT '{}',
    recordings JSONB DEFAULT '[]',

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS for interview_responses
ALTER TABLE interview_responses ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own interview responses" ON interview_responses;
CREATE POLICY "Users can view own interview responses"
    ON interview_responses FOR SELECT
    USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can insert own interview responses" ON interview_responses;
CREATE POLICY "Users can insert own interview responses"
    ON interview_responses FOR INSERT
    WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can update own interview responses" ON interview_responses;
CREATE POLICY "Users can update own interview responses"
    ON interview_responses FOR UPDATE
    USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Service role full access interview_responses" ON interview_responses;
CREATE POLICY "Service role full access interview_responses"
    ON interview_responses FOR ALL
    USING (auth.role() = 'service_role');

-- Index for interview lookups
CREATE INDEX IF NOT EXISTS idx_interview_responses_audit ON interview_responses(audit_id);
CREATE INDEX IF NOT EXISTS idx_interview_responses_user ON interview_responses(user_id);
