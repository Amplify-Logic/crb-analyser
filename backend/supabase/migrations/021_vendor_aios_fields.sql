-- Migration: 021_vendor_aios_fields.sql
-- Description: Add AIOS readiness fields to vendors table
-- Date: 2026-02-27
-- Reference: docs/plans/2026-02-27-aios-data-optimization-design.md

-- ============================================================================
-- ADD AIOS READINESS FIELDS TO VENDORS TABLE
-- These fields enable the 7-layer AIOS assessment and MCP ecosystem matching
-- ============================================================================

-- MCP server slug (references mcp_ecosystem.json)
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS mcp_server_slug TEXT;

-- MCP server maturity level
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS mcp_server_maturity TEXT
  CHECK (mcp_server_maturity IN ('production', 'beta', 'community', 'none'));

-- Claude Code compatibility (has REST API that can be used with Claude Code)
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS claude_code_compatible BOOLEAN DEFAULT false;

-- Whether custom AI agents can be built on this vendor's API
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS agent_buildable BOOLEAN DEFAULT false;

-- Agent patterns supported (e.g., 'data_extraction', 'workflow_automation', 'monitoring')
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS agent_patterns TEXT[] DEFAULT '{}';

-- Data portability level
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS data_portability TEXT
  CHECK (data_portability IN ('full_export', 'api_access', 'limited_export', 'trapped'));

-- Composite AIOS readiness score (1-10, computed on write)
-- Calculation:
--   +2 if api_available AND api_type IN ('REST', 'GraphQL')
--   +2 if has_webhooks
--   +2 if mcp_server_slug IS NOT NULL AND mcp_server_maturity IN ('production', 'beta')
--   +1 if has_oauth
--   +1 if zapier_integration OR make_integration OR n8n_integration
--   +1 if data_portability IN ('full_export', 'api_access')
--   +1 if agent_buildable
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS aios_readiness_score INTEGER
  CHECK (aios_readiness_score BETWEEN 1 AND 10);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index for MCP-enabled vendor queries
CREATE INDEX IF NOT EXISTS idx_vendors_mcp
  ON vendors(mcp_server_slug)
  WHERE mcp_server_slug IS NOT NULL;

-- Index for AIOS-ready vendor queries
CREATE INDEX IF NOT EXISTS idx_vendors_aios_ready
  ON vendors(aios_readiness_score)
  WHERE aios_readiness_score IS NOT NULL;

-- GIN index for agent patterns array queries
CREATE INDEX IF NOT EXISTS idx_vendors_agent_patterns
  ON vendors USING GIN(agent_patterns);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON COLUMN vendors.mcp_server_slug IS
  'Slug referencing the MCP server in mcp_ecosystem.json (e.g., slack, github, linear)';

COMMENT ON COLUMN vendors.mcp_server_maturity IS
  'MCP server maturity: production (stable), beta (usable), community (experimental), none';

COMMENT ON COLUMN vendors.claude_code_compatible IS
  'Whether this vendor has a REST/GraphQL API usable with Claude Code for building integrations';

COMMENT ON COLUMN vendors.agent_buildable IS
  'Whether custom AI agents can be built on this vendor API (sufficient endpoints + docs)';

COMMENT ON COLUMN vendors.agent_patterns IS
  'Types of agent patterns supported: data_extraction, workflow_automation, monitoring, content_generation';

COMMENT ON COLUMN vendors.data_portability IS
  'Data portability: full_export (bulk export), api_access (programmatic), limited_export (partial), trapped (locked in)';

COMMENT ON COLUMN vendors.aios_readiness_score IS
  'Composite AIOS readiness score 1-10: API(2) + webhooks(2) + MCP(2) + OAuth(1) + integrations(1) + portability(1) + agents(1)';

-- ============================================================================
-- ROLLBACK
-- ============================================================================
-- ALTER TABLE vendors DROP COLUMN IF EXISTS mcp_server_slug;
-- ALTER TABLE vendors DROP COLUMN IF EXISTS mcp_server_maturity;
-- ALTER TABLE vendors DROP COLUMN IF EXISTS claude_code_compatible;
-- ALTER TABLE vendors DROP COLUMN IF EXISTS agent_buildable;
-- ALTER TABLE vendors DROP COLUMN IF EXISTS agent_patterns;
-- ALTER TABLE vendors DROP COLUMN IF EXISTS data_portability;
-- ALTER TABLE vendors DROP COLUMN IF EXISTS aios_readiness_score;
-- DROP INDEX IF EXISTS idx_vendors_mcp;
-- DROP INDEX IF EXISTS idx_vendors_aios_ready;
-- DROP INDEX IF EXISTS idx_vendors_agent_patterns;
