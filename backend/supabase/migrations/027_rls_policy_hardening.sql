-- Harden permissive RLS policies for payment/report/vendor/refiner surfaces

-- ============================================================================
-- QUIZ SESSIONS
-- ============================================================================

DROP POLICY IF EXISTS "quiz_sessions_insert_public" ON quiz_sessions;
DROP POLICY IF EXISTS "quiz_sessions_select" ON quiz_sessions;
DROP POLICY IF EXISTS "quiz_sessions_update_service" ON quiz_sessions;

CREATE POLICY "quiz_sessions_insert_service"
    ON quiz_sessions
    FOR INSERT
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "quiz_sessions_select_own_or_service"
    ON quiz_sessions
    FOR SELECT
    USING (
        user_id = auth.uid()
        OR auth.role() = 'service_role'
    );

CREATE POLICY "quiz_sessions_update_service"
    ON quiz_sessions
    FOR UPDATE
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- ============================================================================
-- REPORTS
-- ============================================================================

DROP POLICY IF EXISTS "reports_service_all" ON reports;
DROP POLICY IF EXISTS "reports_select_own" ON reports;

CREATE POLICY "reports_service_all"
    ON reports
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "reports_select_own"
    ON reports
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM quiz_sessions qs
            WHERE qs.id = reports.quiz_session_id
            AND qs.user_id = auth.uid()
        )
        OR EXISTS (
            SELECT 1
            FROM audits a
            JOIN users u ON u.workspace_id = a.workspace_id
            WHERE a.id = reports.audit_id
            AND u.id = auth.uid()
        )
    );

-- ============================================================================
-- VENDOR TABLES (SERVICE WRITE POLICIES)
-- ============================================================================

DROP POLICY IF EXISTS "vendors_insert_service" ON vendors;
DROP POLICY IF EXISTS "vendors_update_service" ON vendors;
DROP POLICY IF EXISTS "vendors_delete_service" ON vendors;

DROP POLICY IF EXISTS "industry_tiers_insert_service" ON industry_vendor_tiers;
DROP POLICY IF EXISTS "industry_tiers_update_service" ON industry_vendor_tiers;
DROP POLICY IF EXISTS "industry_tiers_delete_service" ON industry_vendor_tiers;

DROP POLICY IF EXISTS "audit_log_select_public" ON vendor_audit_log;
DROP POLICY IF EXISTS "audit_log_insert_service" ON vendor_audit_log;

CREATE POLICY "vendors_insert_service"
    ON vendors
    FOR INSERT
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "vendors_update_service"
    ON vendors
    FOR UPDATE
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "vendors_delete_service"
    ON vendors
    FOR DELETE
    USING (auth.role() = 'service_role');

CREATE POLICY "industry_tiers_insert_service"
    ON industry_vendor_tiers
    FOR INSERT
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "industry_tiers_update_service"
    ON industry_vendor_tiers
    FOR UPDATE
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "industry_tiers_delete_service"
    ON industry_vendor_tiers
    FOR DELETE
    USING (auth.role() = 'service_role');

CREATE POLICY "audit_log_select_service"
    ON vendor_audit_log
    FOR SELECT
    USING (auth.role() = 'service_role');

CREATE POLICY "audit_log_insert_service"
    ON vendor_audit_log
    FOR INSERT
    WITH CHECK (auth.role() = 'service_role');

-- ============================================================================
-- REPORT REFINER
-- ============================================================================

DROP POLICY IF EXISTS "report_conversations_service_all" ON report_conversations;
DROP POLICY IF EXISTS "report_messages_service_all" ON report_messages;
DROP POLICY IF EXISTS "report_conversations_select" ON report_conversations;
DROP POLICY IF EXISTS "report_messages_select" ON report_messages;

CREATE POLICY "report_conversations_service_all"
    ON report_conversations
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "report_messages_service_all"
    ON report_messages
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "report_conversations_select"
    ON report_conversations
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1
            FROM reports r
            LEFT JOIN quiz_sessions qs ON qs.id = r.quiz_session_id
            LEFT JOIN audits a ON a.id = r.audit_id
            LEFT JOIN users u ON u.workspace_id = a.workspace_id
            WHERE r.id = report_conversations.report_id
            AND (
                qs.user_id = auth.uid()
                OR u.id = auth.uid()
            )
        )
    );

CREATE POLICY "report_messages_select"
    ON report_messages
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1
            FROM report_conversations rc
            JOIN reports r ON r.id = rc.report_id
            LEFT JOIN quiz_sessions qs ON qs.id = r.quiz_session_id
            LEFT JOIN audits a ON a.id = r.audit_id
            LEFT JOIN users u ON u.workspace_id = a.workspace_id
            WHERE rc.id = report_messages.conversation_id
            AND (
                qs.user_id = auth.uid()
                OR u.id = auth.uid()
            )
        )
    );
