-- Migration: 011_add_generation_trace
-- Description: Add generation_trace column to reports table for dev mode debugging
-- Date: 2025-12-28

-- Add generation_trace column to store detailed reasoning/logic trace
ALTER TABLE reports
ADD COLUMN IF NOT EXISTS generation_trace JSONB DEFAULT NULL;

-- Add index for faster dev mode queries
CREATE INDEX IF NOT EXISTS idx_reports_generation_trace_exists
ON reports ((generation_trace IS NOT NULL))
WHERE generation_trace IS NOT NULL;

-- Comment for documentation
COMMENT ON COLUMN reports.generation_trace IS 'Detailed trace of report generation including LLM calls, knowledge retrievals, decisions, and validations. Used for dev mode debugging.';

-- Rollback:
-- ALTER TABLE reports DROP COLUMN IF EXISTS generation_trace;
-- DROP INDEX IF EXISTS idx_reports_generation_trace_exists;
