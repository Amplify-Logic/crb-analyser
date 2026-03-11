-- Store profiles: normalized store metrics from manual entry or OAuth.
-- Each quiz session can have one store profile with metrics stored as JSONB.
-- Rollback: DROP TABLE IF EXISTS store_profiles CASCADE;

CREATE TABLE store_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_session_id UUID NOT NULL REFERENCES quiz_sessions(id) ON DELETE CASCADE,
    source TEXT NOT NULL DEFAULT 'benchmark',
    completeness FLOAT NOT NULL DEFAULT 0.0,
    currency TEXT NOT NULL DEFAULT 'EUR',
    metrics JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_store_profiles_session UNIQUE (quiz_session_id),
    CONSTRAINT chk_source CHECK (source IN ('manual_entry', 'shopify_oauth', 'benchmark')),
    CONSTRAINT chk_completeness CHECK (completeness >= 0.0 AND completeness <= 1.0)
);

CREATE INDEX idx_store_profiles_session ON store_profiles(quiz_session_id);
CREATE INDEX idx_store_profiles_source ON store_profiles(source);

-- RLS: service role only (store profiles are internal data)
ALTER TABLE store_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access" ON store_profiles
    FOR ALL USING (auth.role() = 'service_role');
