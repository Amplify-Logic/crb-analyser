-- =============================================================================
-- Migration: 001_initial_schema
-- Description: Create quiz_sessions and reports tables
-- =============================================================================

-- Create quiz_sessions table
CREATE TABLE IF NOT EXISTS quiz_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    tier TEXT NOT NULL CHECK (tier IN ('quick', 'full')),
    answers JSONB NOT NULL DEFAULT '{}',
    results JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending_payment' CHECK (status IN ('pending_payment', 'paid', 'expired', 'completed')),

    -- Stripe integration
    stripe_session_id TEXT,
    stripe_payment_id TEXT,
    amount_paid DECIMAL(10, 2),

    -- User linking (optional)
    user_id UUID,
    workspace_id UUID,
    audit_id UUID,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payment_completed_at TIMESTAMPTZ,
    report_generated_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '24 hours'
);

CREATE INDEX IF NOT EXISTS idx_quiz_sessions_email ON quiz_sessions(email);
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_status ON quiz_sessions(status);
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_stripe_session ON quiz_sessions(stripe_session_id);

-- Create reports table
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_session_id UUID REFERENCES quiz_sessions(id) ON DELETE SET NULL,
    audit_id UUID,
    tier TEXT NOT NULL CHECK (tier IN ('quick', 'full')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'generating', 'completed', 'failed')),
    executive_summary JSONB DEFAULT '{}'::jsonb,
    value_summary JSONB DEFAULT '{}'::jsonb,
    findings JSONB DEFAULT '[]'::jsonb,
    recommendations JSONB DEFAULT '[]'::jsonb,
    roadmap JSONB DEFAULT '{}'::jsonb,
    methodology_notes JSONB DEFAULT '{}'::jsonb,
    pdf_url TEXT,
    pdf_generated_at TIMESTAMPTZ,
    generation_started_at TIMESTAMPTZ,
    generation_completed_at TIMESTAMPTZ,
    error_message TEXT,
    agent_context JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reports_quiz_session ON reports(quiz_session_id);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);

-- Add report_id reference to quiz_sessions
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'quiz_sessions' AND column_name = 'report_id'
    ) THEN
        ALTER TABLE quiz_sessions ADD COLUMN report_id UUID REFERENCES reports(id);
    END IF;
END $$;

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_reports_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger (drop first if exists to avoid errors)
DROP TRIGGER IF EXISTS reports_updated_at ON reports;
CREATE TRIGGER reports_updated_at
    BEFORE UPDATE ON reports
    FOR EACH ROW
    EXECUTE FUNCTION update_reports_updated_at();

-- Enable RLS
ALTER TABLE quiz_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- Create permissive policies (for service role)
DROP POLICY IF EXISTS quiz_sessions_all ON quiz_sessions;
CREATE POLICY quiz_sessions_all ON quiz_sessions FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS reports_all ON reports;
CREATE POLICY reports_all ON reports FOR ALL USING (true) WITH CHECK (true);
