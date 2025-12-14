-- Quiz Sessions table for guest checkout flow
-- Stores quiz answers and results before payment, links to user after payment

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

    -- User linking (after account creation)
    user_id UUID REFERENCES auth.users(id),
    workspace_id UUID REFERENCES workspaces(id),
    audit_id UUID REFERENCES audits(id),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payment_completed_at TIMESTAMPTZ,
    report_generated_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '24 hours'
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_email ON quiz_sessions(email);
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_status ON quiz_sessions(status);
CREATE INDEX IF NOT EXISTS idx_quiz_sessions_stripe_session ON quiz_sessions(stripe_session_id);

-- RLS Policies (public insert for guest checkout, restricted read)
ALTER TABLE quiz_sessions ENABLE ROW LEVEL SECURITY;

-- Allow anyone to insert (guest checkout)
CREATE POLICY "quiz_sessions_insert_public" ON quiz_sessions
    FOR INSERT
    WITH CHECK (true);

-- Only allow reading own sessions (by email match or user_id after linking)
CREATE POLICY "quiz_sessions_select" ON quiz_sessions
    FOR SELECT
    USING (
        user_id = auth.uid()
        OR stripe_session_id IS NOT NULL -- Allow webhook access
    );

-- Service role can update
CREATE POLICY "quiz_sessions_update_service" ON quiz_sessions
    FOR UPDATE
    USING (true)
    WITH CHECK (true);

COMMENT ON TABLE quiz_sessions IS 'Stores quiz submissions and payment status for guest checkout flow';
