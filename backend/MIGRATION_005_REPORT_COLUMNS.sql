-- Migration 005: Add missing columns to reports table
-- Run this in Supabase SQL Editor

-- Add industry_insights column for storing industry benchmark data
ALTER TABLE reports
ADD COLUMN IF NOT EXISTS industry_insights jsonb;

-- Add error_at column for tracking when errors occurred
ALTER TABLE reports
ADD COLUMN IF NOT EXISTS error_at timestamptz;

-- Add playbooks column if missing
ALTER TABLE reports
ADD COLUMN IF NOT EXISTS playbooks jsonb;

-- Add system_architecture column if missing
ALTER TABLE reports
ADD COLUMN IF NOT EXISTS system_architecture jsonb;

-- Verify columns were added
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'reports'
AND column_name IN ('industry_insights', 'error_at', 'playbooks', 'system_architecture');
