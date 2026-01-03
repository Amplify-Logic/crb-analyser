-- ============================================================================
-- MIGRATION 007: Add Missing Report Columns
-- ============================================================================
-- Adds assumption_log and partial_data columns to reports table
-- Also adds playbooks, system_architecture, industry_insights, error_at columns
-- ============================================================================

-- Add assumption_log to reports if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reports' AND column_name = 'assumption_log'
    ) THEN
        ALTER TABLE reports ADD COLUMN assumption_log JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- Add partial_data to reports if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reports' AND column_name = 'partial_data'
    ) THEN
        ALTER TABLE reports ADD COLUMN partial_data JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- Add playbooks to reports if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reports' AND column_name = 'playbooks'
    ) THEN
        ALTER TABLE reports ADD COLUMN playbooks JSONB DEFAULT '[]'::jsonb;
    END IF;
END $$;

-- Add system_architecture to reports if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reports' AND column_name = 'system_architecture'
    ) THEN
        ALTER TABLE reports ADD COLUMN system_architecture JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- Add industry_insights to reports if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reports' AND column_name = 'industry_insights'
    ) THEN
        ALTER TABLE reports ADD COLUMN industry_insights JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- Add error_at to reports if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reports' AND column_name = 'error_at'
    ) THEN
        ALTER TABLE reports ADD COLUMN error_at TIMESTAMPTZ;
    END IF;
END $$;

-- Add token_usage to reports if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reports' AND column_name = 'token_usage'
    ) THEN
        ALTER TABLE reports ADD COLUMN token_usage JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- Add math_validation to reports if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reports' AND column_name = 'math_validation'
    ) THEN
        ALTER TABLE reports ADD COLUMN math_validation JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- Add follow_up_schedule to reports if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reports' AND column_name = 'follow_up_schedule'
    ) THEN
        ALTER TABLE reports ADD COLUMN follow_up_schedule JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- Add upsell_analysis to reports if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reports' AND column_name = 'upsell_analysis'
    ) THEN
        ALTER TABLE reports ADD COLUMN upsell_analysis JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON COLUMN reports.assumption_log IS 'Log of assumptions made during report generation with their sources';
COMMENT ON COLUMN reports.partial_data IS 'Partial report data for recovery in case of failures';
COMMENT ON COLUMN reports.playbooks IS 'Implementation playbooks for each recommendation';
COMMENT ON COLUMN reports.system_architecture IS 'Recommended system architecture diagram data';
COMMENT ON COLUMN reports.industry_insights IS 'Industry-specific insights and benchmarks used';
COMMENT ON COLUMN reports.error_at IS 'Timestamp when an error occurred during generation';
COMMENT ON COLUMN reports.token_usage IS 'Token usage breakdown by model and task for cost tracking';
COMMENT ON COLUMN reports.math_validation IS 'Results of mathematical validation checks on findings and recommendations';
COMMENT ON COLUMN reports.follow_up_schedule IS 'Recommended follow-up schedule for customer engagement';
COMMENT ON COLUMN reports.upsell_analysis IS 'Analysis of upsell opportunities for this customer';
