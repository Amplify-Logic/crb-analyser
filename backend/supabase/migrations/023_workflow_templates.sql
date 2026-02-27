-- Migration: 023_workflow_templates.sql
-- Description: Create workflow templates index table
-- Date: 2026-02-27
-- Reference: docs/plans/2026-02-27-aios-data-optimization-design.md

-- ============================================================================
-- WORKFLOW TEMPLATES TABLE
-- Database index for KB JSON workflow files
-- Enables querying workflow templates by industry, tools, pain points, AIOS layers
-- ============================================================================

CREATE TABLE IF NOT EXISTS workflow_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  industry TEXT NOT NULL,
  category TEXT NOT NULL,

  -- Matching criteria (used to find relevant templates for a client)
  required_tools TEXT[],
  optional_tools TEXT[],
  required_capabilities TEXT[],
  pain_points_addressed TEXT[],

  -- AIOS layer mapping (which layers this workflow touches)
  aios_layers_involved TEXT[] CHECK (aios_layers_involved <@ ARRAY[
    'stack', 'connections', 'intelligence', 'data_os', 'skills', 'context_os', 'dashboard'
  ]),

  -- Complexity & effort
  complexity TEXT CHECK (complexity IN ('low', 'medium', 'high')),
  build_time_hours INT,
  mcp_servers_used TEXT[],
  claude_code_involved BOOLEAN DEFAULT false,
  cowork_involved BOOLEAN DEFAULT false,

  -- Flow diagram data (for visual rendering)
  flow_diagram JSONB,

  -- Value estimates
  estimated_monthly_value INT,
  estimated_time_saved_hours INT,

  -- Source tracking (link back to KB JSON file)
  source_file TEXT,
  content_hash TEXT,
  synced_at TIMESTAMPTZ,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_wt_industry
  ON workflow_templates(industry);

CREATE INDEX IF NOT EXISTS idx_wt_category
  ON workflow_templates(category);

CREATE INDEX IF NOT EXISTS idx_wt_required_tools
  ON workflow_templates USING GIN(required_tools);

CREATE INDEX IF NOT EXISTS idx_wt_pain_points
  ON workflow_templates USING GIN(pain_points_addressed);

CREATE INDEX IF NOT EXISTS idx_wt_mcp_servers
  ON workflow_templates USING GIN(mcp_servers_used);

CREATE INDEX IF NOT EXISTS idx_wt_aios_layers
  ON workflow_templates USING GIN(aios_layers_involved);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE workflow_templates ENABLE ROW LEVEL SECURITY;

-- Public read access
CREATE POLICY "Public read workflow_templates" ON workflow_templates
  FOR SELECT USING (true);

-- Service role write access (backend only)
CREATE POLICY "Service write workflow_templates" ON workflow_templates
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE workflow_templates IS
  'Index table for KB JSON workflow files — enables querying templates by industry, tools, pain points, and AIOS layers';

COMMENT ON COLUMN workflow_templates.aios_layers_involved IS
  'Which AIOS layers this workflow touches: stack, connections, intelligence, data_os, skills, context_os, dashboard';

COMMENT ON COLUMN workflow_templates.source_file IS
  'Path to the source JSON file in the knowledge base (for sync tracking)';

COMMENT ON COLUMN workflow_templates.content_hash IS
  'SHA256 hash of the source file content (for change detection during sync)';

-- ============================================================================
-- ROLLBACK
-- ============================================================================
-- DROP TABLE IF EXISTS workflow_templates;
