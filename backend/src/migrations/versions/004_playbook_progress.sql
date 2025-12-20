-- backend/src/migrations/versions/004_playbook_progress.sql
-- Playbook progress tracking and ROI scenarios

-- Playbook progress tracking
CREATE TABLE IF NOT EXISTS playbook_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    playbook_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMPTZ,
    completed_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(report_id, playbook_id, task_id)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_playbook_progress_report
    ON playbook_progress(report_id);
CREATE INDEX IF NOT EXISTS idx_playbook_progress_playbook
    ON playbook_progress(report_id, playbook_id);

-- ROI scenarios
CREATE TABLE IF NOT EXISTS roi_scenarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    inputs JSONB NOT NULL,
    results JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_roi_scenarios_report
    ON roi_scenarios(report_id);

-- Model freshness tracking (for keeping AI model recommendations current)
CREATE TABLE IF NOT EXISTS model_updates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_slug TEXT NOT NULL,
    change_type TEXT NOT NULL,  -- 'price', 'new', 'benchmark', 'deprecated'
    old_value JSONB,
    new_value JSONB,
    status TEXT DEFAULT 'pending',  -- 'pending', 'approved', 'dismissed'
    reviewed_at TIMESTAMPTZ,
    reviewed_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_model_updates_status
    ON model_updates(status);

-- Enable RLS
ALTER TABLE playbook_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE roi_scenarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_updates ENABLE ROW LEVEL SECURITY;

-- RLS policies for playbook_progress (public read, authenticated write)
CREATE POLICY "Anyone can view playbook progress"
    ON playbook_progress FOR SELECT
    USING (true);

CREATE POLICY "Anyone can insert playbook progress"
    ON playbook_progress FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Anyone can update playbook progress"
    ON playbook_progress FOR UPDATE
    USING (true);

-- RLS policies for roi_scenarios
CREATE POLICY "Anyone can view roi scenarios"
    ON roi_scenarios FOR SELECT
    USING (true);

CREATE POLICY "Anyone can insert roi scenarios"
    ON roi_scenarios FOR INSERT
    WITH CHECK (true);

-- Admin-only for model_updates
CREATE POLICY "Admin can manage model updates"
    ON model_updates FOR ALL
    USING (auth.jwt() ->> 'role' = 'admin');
