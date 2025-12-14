-- Company Research Table
-- Stores pre-research data and dynamic questionnaires

CREATE TABLE IF NOT EXISTS company_research (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) NOT NULL,

    -- Input
    company_name TEXT NOT NULL,
    website_url TEXT,
    additional_context TEXT,

    -- Research status
    status TEXT DEFAULT 'pending',  -- 'pending', 'researching', 'completed', 'failed'
    error TEXT,

    -- Results (stored as JSONB)
    company_profile JSONB,  -- CompanyProfile model
    questionnaire JSONB,    -- DynamicQuestionnaire model

    -- User answers to the dynamic questionnaire
    answers JSONB,

    -- Links to created records
    client_id UUID REFERENCES clients(id),
    audit_id UUID REFERENCES audits(id),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for workspace lookups
CREATE INDEX IF NOT EXISTS idx_company_research_workspace ON company_research(workspace_id);

-- Index for status
CREATE INDEX IF NOT EXISTS idx_company_research_status ON company_research(status);

-- RLS Policies
ALTER TABLE company_research ENABLE ROW LEVEL SECURITY;

-- Users can view their workspace's research
CREATE POLICY "Users can view own workspace research"
    ON company_research FOR SELECT
    USING (
        workspace_id IN (
            SELECT workspace_id FROM users WHERE id = auth.uid()
        )
    );

-- Users can insert research for their workspace
CREATE POLICY "Users can insert own workspace research"
    ON company_research FOR INSERT
    WITH CHECK (
        workspace_id IN (
            SELECT workspace_id FROM users WHERE id = auth.uid()
        )
    );

-- Users can update their workspace's research
CREATE POLICY "Users can update own workspace research"
    ON company_research FOR UPDATE
    USING (
        workspace_id IN (
            SELECT workspace_id FROM users WHERE id = auth.uid()
        )
    );

-- Service role bypass
CREATE POLICY "Service role full access to company_research"
    ON company_research FOR ALL
    USING (auth.role() = 'service_role');
