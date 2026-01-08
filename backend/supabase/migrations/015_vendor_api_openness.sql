-- Migration: 015_vendor_api_openness.sql
-- Description: Add API openness and integration capability fields to vendors
-- Date: 2026-01-04
-- Reference: docs/handoffs/2026-01-04-ai-automation-layer-design.md

-- ============================================================================
-- ADD API OPENNESS FIELDS TO VENDORS TABLE
-- These fields enable the "automation-first" recommendation approach
-- ============================================================================

-- API Openness Score (1-5):
-- 5 = Full REST API, webhooks, OAuth (e.g., Stripe, Twilio, HubSpot)
-- 4 = Good API, some limitations (e.g., Salesforce, Zendesk)
-- 3 = Basic API, limited endpoints (e.g., many dental PMS)
-- 2 = Zapier/Make only, no direct API
-- 1 = Closed system, no integrations
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS api_openness_score INTEGER
  CHECK (api_openness_score BETWEEN 1 AND 5);

-- Webhook support for event-driven automation
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS has_webhooks BOOLEAN DEFAULT false;

-- OAuth support for secure third-party authentication
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS has_oauth BOOLEAN DEFAULT false;

-- Integration platform support
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS zapier_integration BOOLEAN DEFAULT false;
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS make_integration BOOLEAN DEFAULT false;
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS n8n_integration BOOLEAN DEFAULT false;

-- API rate limits (free-form text, e.g., "1000/min", "100 req/hour")
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS api_rate_limits TEXT;

-- Examples of custom tools that can be built with this vendor's API
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS custom_tool_examples TEXT[] DEFAULT '{}';

-- Comment explaining the API openness scoring system
COMMENT ON COLUMN vendors.api_openness_score IS
  'API openness rating 1-5: 5=full REST+webhooks+OAuth, 4=good API, 3=basic API, 2=Zapier only, 1=closed';

COMMENT ON COLUMN vendors.has_webhooks IS
  'Vendor supports webhooks for real-time event notifications';

COMMENT ON COLUMN vendors.has_oauth IS
  'Vendor supports OAuth for secure third-party authentication';

COMMENT ON COLUMN vendors.custom_tool_examples IS
  'Examples of custom AI/automation tools that can be built using this vendor API';

-- ============================================================================
-- ADD INDEX FOR API OPENNESS QUERIES
-- ============================================================================

-- Index for finding API-friendly vendors (score >= 4)
CREATE INDEX IF NOT EXISTS idx_vendors_api_openness
  ON vendors(api_openness_score)
  WHERE api_openness_score IS NOT NULL;

-- Index for finding vendors with webhook support
CREATE INDEX IF NOT EXISTS idx_vendors_has_webhooks
  ON vendors(has_webhooks)
  WHERE has_webhooks = true;

-- ============================================================================
-- ROLLBACK
-- ============================================================================
-- To rollback this migration:
-- ALTER TABLE vendors DROP COLUMN IF EXISTS api_openness_score;
-- ALTER TABLE vendors DROP COLUMN IF EXISTS has_webhooks;
-- ALTER TABLE vendors DROP COLUMN IF EXISTS has_oauth;
-- ALTER TABLE vendors DROP COLUMN IF EXISTS zapier_integration;
-- ALTER TABLE vendors DROP COLUMN IF EXISTS make_integration;
-- ALTER TABLE vendors DROP COLUMN IF EXISTS n8n_integration;
-- ALTER TABLE vendors DROP COLUMN IF EXISTS api_rate_limits;
-- ALTER TABLE vendors DROP COLUMN IF EXISTS custom_tool_examples;
-- DROP INDEX IF EXISTS idx_vendors_api_openness;
-- DROP INDEX IF EXISTS idx_vendors_has_webhooks;
