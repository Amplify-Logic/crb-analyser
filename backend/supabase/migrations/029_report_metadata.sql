-- Report metadata for internal analytics / data moat
-- Rollback: DROP TABLE IF EXISTS report_metadata CASCADE;

CREATE TABLE report_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Links
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    quiz_session_id UUID NOT NULL REFERENCES quiz_sessions(id),

    -- Company profile
    industry TEXT,
    company_name TEXT,
    employee_count TEXT,          -- stored as text range from quiz (e.g. "11-50")
    annual_revenue TEXT,          -- stored as text range from quiz
    tier TEXT NOT NULL,           -- 'quick', 'full', 'ai', 'human'

    -- CRB scores (the core metrics)
    ai_readiness_score NUMERIC,
    customer_value_score NUMERIC,
    business_health_score NUMERIC,
    value_potential_min NUMERIC,  -- EUR
    value_potential_max NUMERIC,  -- EUR

    -- Report content counts
    findings_count INTEGER DEFAULT 0,
    recommendations_count INTEGER DEFAULT 0,
    playbooks_count INTEGER DEFAULT 0,

    -- Top findings (denormalized for quick queries)
    top_finding_categories JSONB DEFAULT '[]',     -- e.g. ["customer_service", "marketing"]
    recommended_vendor_names JSONB DEFAULT '[]',   -- e.g. ["Intercom", "HubSpot"]
    primary_goals JSONB DEFAULT '[]',              -- from quiz answers

    -- Generation performance
    generation_duration_seconds NUMERIC,
    total_tokens INTEGER,
    estimated_cost_eur NUMERIC,
    validation_passed BOOLEAN,

    -- Quiz context
    current_tools JSONB DEFAULT '[]',              -- what they already use
    biggest_challenge TEXT,
    implementation_timeline TEXT,
    budget_comfort TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for future analytics queries
CREATE INDEX idx_report_metadata_industry ON report_metadata(industry);
CREATE INDEX idx_report_metadata_tier ON report_metadata(tier);
CREATE INDEX idx_report_metadata_created ON report_metadata(created_at);
CREATE UNIQUE INDEX idx_report_metadata_report ON report_metadata(report_id);

-- RLS: internal analytics only — service role access
ALTER TABLE report_metadata ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access" ON report_metadata
    FOR ALL USING (auth.role() = 'service_role');
