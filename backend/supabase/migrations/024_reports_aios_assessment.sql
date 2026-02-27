-- Migration: 024_reports_aios_assessment.sql
-- Description: Add AIOS maturity and readiness profile fields to reports
-- Date: 2026-02-27
-- Reference: docs/plans/2026-02-27-aios-data-optimization-design.md

-- ============================================================================
-- ADD AIOS ASSESSMENT FIELDS TO REPORTS TABLE
-- Note: system_architecture column already exists (migration 007)
-- ============================================================================

-- AIOS maturity assessment (per-layer scoring)
-- Structure: {
--   current_level: 'disconnected' | 'partially_connected' | 'automated' | 'ai_native',
--   layer_scores: { stack: 1-10, connections: 1-10, intelligence: 1-10,
--                   data_os: 1-10, skills: 1-10, context_os: 1-10, dashboard: 1-10 },
--   overall_score: 1-100,
--   gaps: ['No MCP connections', 'No custom skills', 'No Context OS'],
--   quick_wins: ['Connect CRM via MCP', 'Create CLAUDE.md'],
--   target_level: 'automated',
--   path_to_target: ['Connect CRM via MCP', 'Build 3 core skills', 'Create CLAUDE.md']
-- }
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reports' AND column_name = 'aios_maturity'
    ) THEN
        ALTER TABLE reports ADD COLUMN aios_maturity JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- Readiness profile (client's readiness for AIOS adoption)
-- Structure: {
--   infrastructure: 'digitized' | 'partial' | 'paper-based',
--   build_willingness: 'eager' | 'open' | 'prefers-turnkey',
--   ai_experience: 'none' | 'dabbled' | 'active-user',
--   stack_api_readiness: 'most-apis' | 'mixed' | 'mostly-closed',
--   urgency: 'this_week' | 'this_month' | 'this_quarter' | 'no_rush'
-- }
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reports' AND column_name = 'readiness_profile'
    ) THEN
        ALTER TABLE reports ADD COLUMN readiness_profile JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON COLUMN reports.aios_maturity IS
  'AIOS maturity assessment: per-layer scores (1-10), overall score (1-100), gaps, quick wins, and target path';

COMMENT ON COLUMN reports.readiness_profile IS
  'Client readiness profile: infrastructure level, build willingness, AI experience, stack API readiness, urgency';

-- ============================================================================
-- ROLLBACK
-- ============================================================================
-- ALTER TABLE reports DROP COLUMN IF EXISTS aios_maturity;
-- ALTER TABLE reports DROP COLUMN IF EXISTS readiness_profile;
