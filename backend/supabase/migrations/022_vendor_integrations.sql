-- Migration: 022_vendor_integrations.sql
-- Description: Create vendor integration graph table
-- Date: 2026-02-27
-- Reference: docs/plans/2026-02-27-aios-data-optimization-design.md

-- ============================================================================
-- VENDOR INTEGRATIONS TABLE (Connection Graph)
-- Maps known integration paths between vendors
-- Used to recommend connection strategies in AIOS blueprints
-- ============================================================================

CREATE TABLE IF NOT EXISTS vendor_integrations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- The two vendors being connected
  from_vendor_id UUID NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
  to_vendor_id UUID NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,

  -- Connection metadata
  connection_type TEXT NOT NULL CHECK (connection_type IN (
    'mcp', 'native', 'api', 'webhook', 'zapier', 'make', 'n8n', 'custom'
  )),
  connection_quality TEXT NOT NULL CHECK (connection_quality IN (
    'production', 'reliable', 'basic', 'workaround'
  )),
  setup_complexity TEXT CHECK (setup_complexity IN ('easy', 'moderate', 'complex')),
  bidirectional BOOLEAN DEFAULT false,

  -- What data flows through this connection
  data_flows TEXT[],

  -- Implementation details
  setup_time_hours INT,
  requires_claude_code BOOLEAN DEFAULT false,
  mcp_server_slug TEXT,

  -- Verification
  verified_at TIMESTAMPTZ,
  notes TEXT,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),

  -- Prevent duplicate connections of the same type
  UNIQUE(from_vendor_id, to_vendor_id, connection_type)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_vi_from
  ON vendor_integrations(from_vendor_id);

CREATE INDEX IF NOT EXISTS idx_vi_to
  ON vendor_integrations(to_vendor_id);

CREATE INDEX IF NOT EXISTS idx_vi_type
  ON vendor_integrations(connection_type);

CREATE INDEX IF NOT EXISTS idx_vi_mcp
  ON vendor_integrations(mcp_server_slug)
  WHERE mcp_server_slug IS NOT NULL;

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE vendor_integrations ENABLE ROW LEVEL SECURITY;

-- Public read access (same as vendors table)
CREATE POLICY "Public read vendor_integrations" ON vendor_integrations
  FOR SELECT USING (true);

-- Service role write access (backend only)
CREATE POLICY "Service write vendor_integrations" ON vendor_integrations
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE vendor_integrations IS
  'Maps known integration paths between vendors — used for AIOS connection blueprints';

COMMENT ON COLUMN vendor_integrations.connection_type IS
  'How the vendors connect: mcp (Model Context Protocol), native (built-in), api (custom), webhook, zapier, make, n8n, custom';

COMMENT ON COLUMN vendor_integrations.connection_quality IS
  'Reliability: production (battle-tested), reliable (works well), basic (limited), workaround (hacky)';

COMMENT ON COLUMN vendor_integrations.data_flows IS
  'What data moves through this connection, e.g. contacts, invoices, tasks, messages';

COMMENT ON COLUMN vendor_integrations.requires_claude_code IS
  'Whether Claude Code is needed to build/maintain this integration';

-- ============================================================================
-- ROLLBACK
-- ============================================================================
-- DROP TABLE IF EXISTS vendor_integrations;
