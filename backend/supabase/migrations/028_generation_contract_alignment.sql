-- Align runtime generation contracts with database constraints.
-- This migration resolves tier/status drift between code and DB.

-- ============================================================================
-- QUIZ_SESSIONS CONSTRAINTS
-- ============================================================================

ALTER TABLE quiz_sessions DROP CONSTRAINT IF EXISTS quiz_sessions_status_check;
ALTER TABLE quiz_sessions ADD CONSTRAINT quiz_sessions_status_check
    CHECK (status IN (
        'pending_payment',
        'processing_payment',
        'paid',
        'in_progress',
        'quiz_complete',
        'generating',
        'completed',
        'expired',
        'failed',
        'qa_pending',
        'qa_rejected',
        'released',
        'workshop_started',
        'workshop_confirmation',
        'workshop_deepdive',
        'workshop',
        'workshop_complete',
        'report_generating',
        'report_delivered',
        'refunded'
    ));

ALTER TABLE quiz_sessions DROP CONSTRAINT IF EXISTS quiz_sessions_tier_check;
ALTER TABLE quiz_sessions ADD CONSTRAINT quiz_sessions_tier_check
    CHECK (tier IN ('quick', 'full', 'ai', 'human'));

-- ============================================================================
-- REPORTS CONSTRAINTS
-- ============================================================================

ALTER TABLE reports DROP CONSTRAINT IF EXISTS reports_status_check;
ALTER TABLE reports ADD CONSTRAINT reports_status_check
    CHECK (status IN (
        'pending',
        'generating',
        'completed',
        'failed',
        'qa_pending',
        'qa_rejected',
        'released',
        'partial',
        'superseded'
    ));

ALTER TABLE reports DROP CONSTRAINT IF EXISTS reports_tier_check;
ALTER TABLE reports ADD CONSTRAINT reports_tier_check
    CHECK (tier IN ('quick', 'full', 'ai', 'human'));

-- ============================================================================
-- PAYMENT LOOKUP INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_quiz_sessions_stripe_payment_id
    ON quiz_sessions(stripe_payment_id);

CREATE INDEX IF NOT EXISTS idx_audits_stripe_payment_id
    ON audits(stripe_payment_id);

-- ============================================================================
-- RETRIEVAL RPC CONTRACT
-- ============================================================================

DROP FUNCTION IF EXISTS search_all_knowledge(vector, INT, TEXT);

CREATE OR REPLACE FUNCTION search_all_knowledge(
    query_embedding vector(1536),
    match_count_per_type INT DEFAULT 3,
    filter_industry TEXT DEFAULT NULL,
    similarity_threshold FLOAT DEFAULT 0.5
)
RETURNS TABLE (
    id UUID,
    content_type TEXT,
    content_id TEXT,
    industry TEXT,
    title TEXT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    (
        -- Vendors
        SELECT ke.id, ke.content_type, ke.content_id, ke.industry, ke.title, ke.content, ke.metadata,
               1 - (ke.embedding <=> query_embedding) AS similarity
        FROM knowledge_embeddings ke
        WHERE ke.content_type = 'vendor'
          AND (filter_industry IS NULL OR ke.industry = filter_industry OR ke.industry IS NULL)
          AND 1 - (ke.embedding <=> query_embedding) >= similarity_threshold
        ORDER BY ke.embedding <=> query_embedding
        LIMIT match_count_per_type
    )
    UNION ALL
    (
        -- Opportunities
        SELECT ke.id, ke.content_type, ke.content_id, ke.industry, ke.title, ke.content, ke.metadata,
               1 - (ke.embedding <=> query_embedding) AS similarity
        FROM knowledge_embeddings ke
        WHERE ke.content_type = 'opportunity'
          AND (filter_industry IS NULL OR ke.industry = filter_industry OR ke.industry IS NULL)
          AND 1 - (ke.embedding <=> query_embedding) >= similarity_threshold
        ORDER BY ke.embedding <=> query_embedding
        LIMIT match_count_per_type
    )
    UNION ALL
    (
        -- Case studies and insights
        SELECT ke.id, ke.content_type, ke.content_id, ke.industry, ke.title, ke.content, ke.metadata,
               1 - (ke.embedding <=> query_embedding) AS similarity
        FROM knowledge_embeddings ke
        WHERE ke.content_type IN ('case_study', 'insight')
          AND (filter_industry IS NULL OR ke.industry = filter_industry OR ke.industry IS NULL)
          AND 1 - (ke.embedding <=> query_embedding) >= similarity_threshold
        ORDER BY ke.embedding <=> query_embedding
        LIMIT match_count_per_type
    )
    UNION ALL
    (
        -- Patterns
        SELECT ke.id, ke.content_type, ke.content_id, ke.industry, ke.title, ke.content, ke.metadata,
               1 - (ke.embedding <=> query_embedding) AS similarity
        FROM knowledge_embeddings ke
        WHERE ke.content_type = 'pattern'
          AND (filter_industry IS NULL OR ke.industry = filter_industry OR ke.industry IS NULL)
          AND 1 - (ke.embedding <=> query_embedding) >= similarity_threshold
        ORDER BY ke.embedding <=> query_embedding
        LIMIT match_count_per_type
    )
    UNION ALL
    (
        -- Benchmarks
        SELECT ke.id, ke.content_type, ke.content_id, ke.industry, ke.title, ke.content, ke.metadata,
               1 - (ke.embedding <=> query_embedding) AS similarity
        FROM knowledge_embeddings ke
        WHERE ke.content_type = 'benchmark'
          AND (filter_industry IS NULL OR ke.industry = filter_industry OR ke.industry IS NULL)
          AND 1 - (ke.embedding <=> query_embedding) >= similarity_threshold
        ORDER BY ke.embedding <=> query_embedding
        LIMIT match_count_per_type
    )
    ORDER BY similarity DESC;
END;
$$;
