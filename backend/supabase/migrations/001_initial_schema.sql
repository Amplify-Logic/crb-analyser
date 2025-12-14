-- CRB Analyser Database Schema
-- Run this in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Workspaces (multi-tenancy)
CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY,  -- Matches Supabase Auth user ID
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    workspace_id UUID REFERENCES workspaces(id),
    role TEXT DEFAULT 'user',  -- 'user', 'admin', 'owner'
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Subscriptions
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id),
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    plan TEXT DEFAULT 'free',  -- 'free', 'professional'
    status TEXT DEFAULT 'active',  -- 'active', 'cancelled', 'past_due'
    current_period_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- AUDIT TABLES
-- ============================================================================

-- Clients (businesses being audited)
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) NOT NULL,
    name TEXT NOT NULL,
    industry TEXT NOT NULL,
    company_size TEXT,  -- 'solo', '2-10', '11-50', '51-200', '201-500', '500+'
    revenue_range TEXT,
    website TEXT,
    contact_email TEXT,
    contact_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audits (CRB analysis projects)
CREATE TABLE audits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES workspaces(id) NOT NULL,
    title TEXT NOT NULL,
    tier TEXT NOT NULL DEFAULT 'professional',  -- 'free', 'professional'
    status TEXT DEFAULT 'intake',  -- 'intake', 'processing', 'completed', 'failed'

    -- Progress tracking
    current_phase TEXT DEFAULT 'intake',
    progress_percent INTEGER DEFAULT 0,
    phase_details JSONB DEFAULT '{}',

    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Payment
    payment_status TEXT DEFAULT 'pending',  -- 'pending', 'paid', 'refunded'
    stripe_payment_id TEXT,
    price_paid DECIMAL(10,2),
    currency TEXT DEFAULT 'EUR',

    -- Results
    ai_readiness_score INTEGER,  -- 0-100
    total_findings INTEGER DEFAULT 0,
    total_potential_savings DECIMAL(12,2),

    -- Retry tracking
    retry_count INTEGER DEFAULT 0,
    last_error TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Intake Responses
CREATE TABLE intake_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    audit_id UUID REFERENCES audits(id) ON DELETE CASCADE,

    -- Progress
    is_complete BOOLEAN DEFAULT FALSE,
    current_section INTEGER DEFAULT 1,
    completed_sections JSONB DEFAULT '[]',

    -- Responses stored as JSONB
    responses JSONB DEFAULT '{}',

    -- Metadata
    last_saved_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Findings (discovered issues/opportunities)
CREATE TABLE findings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    audit_id UUID REFERENCES audits(id) ON DELETE CASCADE,

    -- Classification
    category TEXT NOT NULL,  -- 'process', 'technology', 'cost', 'risk', 'opportunity'
    subcategory TEXT,
    severity TEXT NOT NULL,  -- 'critical', 'high', 'medium', 'low'

    -- Content
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    current_state TEXT,
    impact_description TEXT,

    -- Quantification
    estimated_annual_cost DECIMAL(12,2),
    estimated_hours_wasted_weekly DECIMAL(6,2),

    -- Confidence
    confidence_score DECIMAL(3,2),  -- 0.00 to 1.00
    is_verified BOOLEAN DEFAULT FALSE,  -- verified vs AI-estimated

    -- Evidence
    sources JSONB DEFAULT '[]',
    evidence JSONB DEFAULT '{}',

    -- Sorting
    priority INTEGER,
    effort_score INTEGER,  -- 1-10, higher = more effort
    impact_score INTEGER,  -- 1-10, higher = more impact

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Recommendations (proposed solutions)
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    finding_id UUID REFERENCES findings(id) ON DELETE CASCADE,
    audit_id UUID REFERENCES audits(id) ON DELETE CASCADE,

    -- Content
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    implementation_steps JSONB DEFAULT '[]',

    -- Vendor options
    vendor_options JSONB DEFAULT '[]',
    recommended_vendor TEXT,

    -- ROI Analysis
    estimated_cost DECIMAL(12,2),
    estimated_annual_savings DECIMAL(12,2),
    estimated_one_time_benefit DECIMAL(12,2),
    payback_months DECIMAL(4,1),
    roi_percent DECIMAL(6,2),

    -- Risk & Effort
    implementation_risk TEXT,  -- 'low', 'medium', 'high'
    risk_factors JSONB DEFAULT '[]',
    effort_level TEXT,  -- 'quick_win', 'moderate', 'major_project'
    timeline_weeks INTEGER,

    -- Assumptions
    assumptions JSONB DEFAULT '[]',

    -- Sorting
    priority INTEGER,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Reports (generated deliverables)
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    audit_id UUID REFERENCES audits(id) ON DELETE CASCADE,

    -- Content
    title TEXT NOT NULL,
    executive_summary TEXT,
    full_content JSONB,

    -- Files
    pdf_storage_path TEXT,
    pdf_url TEXT,
    json_export_path TEXT,

    -- Metadata
    version INTEGER DEFAULT 1,
    status TEXT DEFAULT 'draft',  -- 'draft', 'final'

    -- Access tracking
    downloaded_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,  -- 1 year retention

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- DATA TABLES (Our Competitive Advantage)
-- ============================================================================

-- Vendor Catalog
CREATE TABLE vendor_catalog (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,  -- 'crm', 'automation', 'analytics', 'ai_tool', 'project_management', 'customer_service'
    subcategory TEXT,

    -- Pricing
    pricing_model TEXT,  -- 'per_seat', 'flat', 'usage', 'custom'
    pricing_tiers JSONB,
    pricing_last_verified TIMESTAMPTZ,

    -- Info
    website TEXT,
    description TEXT,
    logo_url TEXT,

    -- Fit
    best_for JSONB DEFAULT '[]',
    avoid_if JSONB DEFAULT '[]',
    industries JSONB DEFAULT '[]',
    company_sizes JSONB DEFAULT '[]',

    -- Ratings
    g2_rating DECIMAL(2,1),
    capterra_rating DECIMAL(2,1),
    our_rating DECIMAL(2,1),

    -- Implementation
    avg_implementation_weeks INTEGER,
    avg_implementation_cost_smb DECIMAL(10,2),
    avg_implementation_cost_mid DECIMAL(10,2),

    -- Integrations
    integrations JSONB DEFAULT '[]',

    is_active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Industry Benchmarks
CREATE TABLE industry_benchmarks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    industry TEXT NOT NULL,
    company_size TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value DECIMAL(10,4),
    metric_unit TEXT,

    -- Percentiles
    percentile_25 DECIMAL(10,4),
    percentile_50 DECIMAL(10,4),
    percentile_75 DECIMAL(10,4),

    -- Source
    source_name TEXT NOT NULL,
    source_url TEXT,
    source_date DATE,

    is_active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- ACTIVITY & LOGGING
-- ============================================================================

-- Audit Activity Log (for progress streaming)
CREATE TABLE audit_activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    audit_id UUID REFERENCES audits(id) ON DELETE CASCADE,

    action TEXT NOT NULL,
    phase TEXT,
    description TEXT,
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_users_workspace ON users(workspace_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_clients_workspace ON clients(workspace_id);
CREATE INDEX idx_audits_workspace ON audits(workspace_id);
CREATE INDEX idx_audits_client ON audits(client_id);
CREATE INDEX idx_audits_status ON audits(status);
CREATE INDEX idx_intake_responses_audit ON intake_responses(audit_id);
CREATE INDEX idx_findings_audit ON findings(audit_id);
CREATE INDEX idx_findings_category ON findings(category);
CREATE INDEX idx_recommendations_audit ON recommendations(audit_id);
CREATE INDEX idx_recommendations_finding ON recommendations(finding_id);
CREATE INDEX idx_reports_audit ON reports(audit_id);
CREATE INDEX idx_vendor_catalog_category ON vendor_catalog(category);
CREATE INDEX idx_vendor_catalog_slug ON vendor_catalog(slug);
CREATE INDEX idx_industry_benchmarks_lookup ON industry_benchmarks(industry, company_size);
CREATE INDEX idx_audit_activity_audit ON audit_activity_log(audit_id);
CREATE INDEX idx_audit_activity_created ON audit_activity_log(created_at);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE audits ENABLE ROW LEVEL SECURITY;
ALTER TABLE intake_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE findings ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_activity_log ENABLE ROW LEVEL SECURITY;

-- Users can see their own record
CREATE POLICY users_own_record ON users
    FOR ALL USING (id = auth.uid());

-- Workspace isolation for all tenant data
CREATE POLICY workspace_isolation_clients ON clients
    FOR ALL USING (workspace_id IN (
        SELECT workspace_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY workspace_isolation_audits ON audits
    FOR ALL USING (workspace_id IN (
        SELECT workspace_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY workspace_isolation_intake ON intake_responses
    FOR ALL USING (audit_id IN (
        SELECT id FROM audits WHERE workspace_id IN (
            SELECT workspace_id FROM users WHERE id = auth.uid()
        )
    ));

CREATE POLICY workspace_isolation_findings ON findings
    FOR ALL USING (audit_id IN (
        SELECT id FROM audits WHERE workspace_id IN (
            SELECT workspace_id FROM users WHERE id = auth.uid()
        )
    ));

CREATE POLICY workspace_isolation_recommendations ON recommendations
    FOR ALL USING (audit_id IN (
        SELECT id FROM audits WHERE workspace_id IN (
            SELECT workspace_id FROM users WHERE id = auth.uid()
        )
    ));

CREATE POLICY workspace_isolation_reports ON reports
    FOR ALL USING (audit_id IN (
        SELECT id FROM audits WHERE workspace_id IN (
            SELECT workspace_id FROM users WHERE id = auth.uid()
        )
    ));

CREATE POLICY workspace_isolation_activity ON audit_activity_log
    FOR ALL USING (audit_id IN (
        SELECT id FROM audits WHERE workspace_id IN (
            SELECT workspace_id FROM users WHERE id = auth.uid()
        )
    ));

CREATE POLICY workspace_isolation_subscriptions ON subscriptions
    FOR ALL USING (workspace_id IN (
        SELECT workspace_id FROM users WHERE id = auth.uid()
    ));

-- Public read access for vendor catalog and benchmarks
CREATE POLICY public_read_vendors ON vendor_catalog
    FOR SELECT USING (true);

CREATE POLICY public_read_benchmarks ON industry_benchmarks
    FOR SELECT USING (true);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_workspaces_updated_at BEFORE UPDATE ON workspaces
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_audits_updated_at BEFORE UPDATE ON audits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_intake_updated_at BEFORE UPDATE ON intake_responses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- SEED DATA: Industries for dropdown
-- ============================================================================

-- This will be populated separately with vendor and benchmark data
