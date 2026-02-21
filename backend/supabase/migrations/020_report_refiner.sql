-- Report Refiner: conversations and messages
-- Supports Phase 1 (conversation) and lays foundation for Phase 2+ (refinements, snapshots)

-- Conversations: persistent chat threads per report
CREATE TABLE IF NOT EXISTS report_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    title TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_message_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_report_conversations_report ON report_conversations(report_id);
CREATE INDEX idx_report_conversations_status ON report_conversations(report_id, status);

-- Messages: individual chat messages
CREATE TABLE IF NOT EXISTS report_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES report_conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    suggestions JSONB,
    model_used TEXT,
    tokens_used INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_report_messages_conversation ON report_messages(conversation_id);
CREATE INDEX idx_report_messages_created ON report_messages(conversation_id, created_at);

-- RLS
ALTER TABLE report_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_messages ENABLE ROW LEVEL SECURITY;

-- Service role (backend) can do everything
CREATE POLICY "report_conversations_service_all" ON report_conversations
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "report_messages_service_all" ON report_messages
    FOR ALL USING (true) WITH CHECK (true);

-- Users can read conversations for reports they have access to
CREATE POLICY "report_conversations_select" ON report_conversations
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM reports r
            JOIN quiz_sessions qs ON qs.id = r.quiz_session_id
            WHERE r.id = report_conversations.report_id
            AND qs.status IN ('paid', 'completed', 'generating', 'qa_pending', 'released')
        )
    );

CREATE POLICY "report_messages_select" ON report_messages
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM report_conversations rc
            WHERE rc.id = report_messages.conversation_id
        )
    );
