-- Reports table for storing CRB analysis reports
-- Links to quiz_sessions and stores full structured report data

CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link to source data
    quiz_session_id UUID REFERENCES quiz_sessions(id) ON DELETE SET NULL,
    audit_id UUID REFERENCES audits(id) ON DELETE SET NULL,

    -- Report metadata
    tier TEXT NOT NULL CHECK (tier IN ('quick', 'full')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'generating', 'completed', 'failed')),

    -- Structured report data (following FRAMEWORK.md)
    executive_summary JSONB DEFAULT '{}'::jsonb,
    -- Format: {
    --   ai_readiness_score: number,
    --   customer_value_score: number,
    --   business_health_score: number,
    --   total_value_potential: { min: number, max: number },
    --   key_insight: string,
    --   top_opportunities: [{ title, value_potential, time_horizon }],
    --   not_recommended: [{ title, reason }],
    --   recommended_investment: { min: number, max: number }
    -- }

    value_summary JSONB DEFAULT '{}'::jsonb,
    -- Format: {
    --   value_saved: { time_savings: number, cost_reduction: number, error_reduction: number, subtotal: { min, max } },
    --   value_created: { new_revenue: number, conversion_increase: number, competitive_advantage: string, subtotal: { min, max } },
    --   total: { min: number, max: number },
    --   projection_years: 3
    -- }

    findings JSONB DEFAULT '[]'::jsonb,
    -- Format: [{
    --   id: string,
    --   title: string,
    --   description: string,
    --   category: string,
    --   customer_value_score: number (1-10),
    --   business_health_score: number (1-10),
    --   value_saved: { hours_per_week: number, hourly_rate: number, annual_savings: number },
    --   value_created: { description: string, potential_revenue: number },
    --   confidence: 'high' | 'medium' | 'low',
    --   sources: [string],
    --   time_horizon: 'short' | 'mid' | 'long'
    -- }]

    recommendations JSONB DEFAULT '[]'::jsonb,
    -- Format: [{
    --   id: string,
    --   finding_id: string,
    --   title: string,
    --   description: string,
    --   why_it_matters: { customer_value: string, business_health: string },
    --   priority: 'high' | 'medium' | 'low',
    --   crb_analysis: {
    --     cost: {
    --       short_term: { software: number, implementation: number, training: number },
    --       mid_term: { software: number, maintenance: number },
    --       long_term: { software: number, upgrades: number },
    --       total: number
    --     },
    --     risk: [{
    --       description: string,
    --       probability: 'low' | 'medium' | 'high',
    --       impact: number,
    --       mitigation: string,
    --       time_horizon: 'short' | 'mid' | 'long'
    --     }],
    --     benefit: {
    --       short_term: { value_saved: number, value_created: number },
    --       mid_term: { value_saved: number, value_created: number },
    --       long_term: { value_saved: number, value_created: number },
    --       total: number
    --     }
    --   },
    --   options: {
    --     off_the_shelf: {
    --       name: string,
    --       vendor: string,
    --       monthly_cost: number,
    --       implementation_weeks: number,
    --       pros: [string],
    --       cons: [string]
    --     },
    --     best_in_class: {
    --       name: string,
    --       vendor: string,
    --       monthly_cost: number,
    --       implementation_weeks: number,
    --       pros: [string],
    --       cons: [string]
    --     },
    --     custom_solution: {
    --       approach: string,
    --       estimated_cost: { min: number, max: number },
    --       implementation_weeks: number,
    --       pros: [string],
    --       cons: [string]
    --     }
    --   },
    --   our_recommendation: string,
    --   recommendation_rationale: string,
    --   roi_percentage: number,
    --   payback_months: number,
    --   assumptions: [string]
    -- }]

    roadmap JSONB DEFAULT '{}'::jsonb,
    -- Format: {
    --   short_term: [{ title, description, timeline, expected_outcome }],
    --   mid_term: [{ title, description, timeline, expected_outcome }],
    --   long_term: [{ title, description, timeline, expected_outcome }]
    -- }

    methodology_notes JSONB DEFAULT '{}'::jsonb,
    -- Format: {
    --   data_sources: [string],
    --   assumptions: [string],
    --   limitations: [string],
    --   industry_benchmarks_used: [string],
    --   confidence_notes: string
    -- }

    -- PDF storage
    pdf_url TEXT,
    pdf_generated_at TIMESTAMPTZ,

    -- Processing metadata
    generation_started_at TIMESTAMPTZ,
    generation_completed_at TIMESTAMPTZ,
    error_message TEXT,
    agent_context JSONB DEFAULT '{}'::jsonb,  -- Store intermediate agent state

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Update quiz_sessions to link to report
ALTER TABLE quiz_sessions
ADD COLUMN IF NOT EXISTS report_id UUID REFERENCES reports(id);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_reports_quiz_session ON reports(quiz_session_id);
CREATE INDEX IF NOT EXISTS idx_reports_audit ON reports(audit_id);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_reports_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER reports_updated_at
    BEFORE UPDATE ON reports
    FOR EACH ROW
    EXECUTE FUNCTION update_reports_updated_at();

-- RLS Policies
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- Service role can do everything (for backend)
CREATE POLICY "reports_service_all" ON reports
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Users can read their own reports (by user_id through quiz_sessions)
CREATE POLICY "reports_select_own" ON reports
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM quiz_sessions qs
            WHERE qs.id = reports.quiz_session_id
            AND qs.user_id = auth.uid()
        )
        OR EXISTS (
            SELECT 1 FROM audits a
            WHERE a.id = reports.audit_id
            AND a.workspace_id IN (
                SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid()
            )
        )
    );

COMMENT ON TABLE reports IS 'Stores CRB analysis reports with structured data following the two pillars methodology';
