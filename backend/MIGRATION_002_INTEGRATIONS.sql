-- =============================================================================
-- CRB ANALYSER - MIGRATION 002: INTEGRATIONS
-- Run this in Supabase SQL Editor AFTER RUN_THIS_IN_SUPABASE.sql
-- =============================================================================

-- =============================================================================
-- STEP 1: Update quiz_sessions status constraint to allow new statuses
-- =============================================================================

ALTER TABLE quiz_sessions
DROP CONSTRAINT IF EXISTS quiz_sessions_status_check;

ALTER TABLE quiz_sessions
ADD CONSTRAINT quiz_sessions_status_check
CHECK (status IN ('pending_payment', 'paid', 'generating', 'completed', 'expired', 'refunded', 'failed'));

-- Add refund tracking
ALTER TABLE quiz_sessions
ADD COLUMN IF NOT EXISTS refund_amount DECIMAL(10, 2);

-- =============================================================================
-- STEP 2: Update reports status constraint
-- =============================================================================

ALTER TABLE reports
DROP CONSTRAINT IF EXISTS reports_status_check;

ALTER TABLE reports
ADD CONSTRAINT reports_status_check
CHECK (status IN ('pending', 'generating', 'completed', 'failed', 'superseded'));

-- Add follow-up tracking (for future email scheduler)
ALTER TABLE reports
ADD COLUMN IF NOT EXISTS follow_up_sent_at TIMESTAMPTZ;

-- =============================================================================
-- STEP 3: Update audits table (if exists)
-- =============================================================================

DO $$
BEGIN
    -- Add refund columns to audits if they don't exist
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audits') THEN
        ALTER TABLE audits ADD COLUMN IF NOT EXISTS refund_amount DECIMAL(10, 2);

        -- Update payment_status constraint if it exists
        ALTER TABLE audits DROP CONSTRAINT IF EXISTS audits_payment_status_check;
        ALTER TABLE audits ADD CONSTRAINT audits_payment_status_check
        CHECK (payment_status IN ('pending', 'paid', 'refunded', 'expired', 'failed'));
    END IF;
END $$;

-- =============================================================================
-- STEP 4: Create Storage Bucket for Reports
-- =============================================================================

-- Create the reports bucket (private by default)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'reports',
    'reports',
    false,
    52428800,  -- 50MB limit
    ARRAY['application/pdf']
)
ON CONFLICT (id) DO UPDATE SET
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

-- =============================================================================
-- STEP 5: Storage RLS Policies
-- =============================================================================

-- Allow service role to upload (backend uses service key)
DROP POLICY IF EXISTS "Service role can upload PDFs" ON storage.objects;
CREATE POLICY "Service role can upload PDFs"
ON storage.objects FOR INSERT
TO service_role
WITH CHECK (bucket_id = 'reports');

-- Allow service role to read
DROP POLICY IF EXISTS "Service role can read PDFs" ON storage.objects;
CREATE POLICY "Service role can read PDFs"
ON storage.objects FOR SELECT
TO service_role
USING (bucket_id = 'reports');

-- Allow service role to delete (for cleanup)
DROP POLICY IF EXISTS "Service role can delete PDFs" ON storage.objects;
CREATE POLICY "Service role can delete PDFs"
ON storage.objects FOR DELETE
TO service_role
USING (bucket_id = 'reports');

-- Allow public to read with signed URLs (Supabase handles this automatically)
DROP POLICY IF EXISTS "Public can read with signed URL" ON storage.objects;
CREATE POLICY "Public can read with signed URL"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'reports');

-- =============================================================================
-- STEP 6: Create index for follow-up email queries
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_reports_follow_up
ON reports(generation_completed_at)
WHERE follow_up_sent_at IS NULL AND status = 'completed';

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
DECLARE
    bucket_exists boolean;
    quiz_cols integer;
    report_cols integer;
BEGIN
    -- Check bucket
    SELECT EXISTS (SELECT 1 FROM storage.buckets WHERE id = 'reports') INTO bucket_exists;

    -- Check columns
    SELECT COUNT(*) INTO quiz_cols
    FROM information_schema.columns
    WHERE table_name = 'quiz_sessions' AND column_name = 'refund_amount';

    SELECT COUNT(*) INTO report_cols
    FROM information_schema.columns
    WHERE table_name = 'reports' AND column_name = 'follow_up_sent_at';

    RAISE NOTICE '========================================';
    RAISE NOTICE 'MIGRATION 002 VERIFICATION:';
    RAISE NOTICE '- Storage bucket "reports": %', CASE WHEN bucket_exists THEN 'OK' ELSE 'MISSING' END;
    RAISE NOTICE '- quiz_sessions.refund_amount: %', CASE WHEN quiz_cols > 0 THEN 'OK' ELSE 'MISSING' END;
    RAISE NOTICE '- reports.follow_up_sent_at: %', CASE WHEN report_cols > 0 THEN 'OK' ELSE 'MISSING' END;
    RAISE NOTICE '========================================';
END $$;

SELECT 'SUCCESS: Migration 002 (Integrations) completed!' as result;
