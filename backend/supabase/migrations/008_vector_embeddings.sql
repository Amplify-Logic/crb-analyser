-- Vector Embeddings for RAG-based Knowledge Retrieval
-- Enables semantic search across vendors, opportunities, benchmarks, and insights
-- Run this in your Supabase SQL Editor

-- ============================================================================
-- ENABLE PGVECTOR EXTENSION
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- KNOWLEDGE EMBEDDINGS TABLE
-- Stores embeddings for all knowledge base content
-- ============================================================================

CREATE TABLE knowledge_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Content identification
    content_type TEXT NOT NULL,  -- 'vendor', 'opportunity', 'benchmark', 'case_study', 'pattern', 'insight'
    content_id TEXT NOT NULL,    -- Unique ID within content type (e.g., vendor slug, opportunity id)
    industry TEXT,               -- NULL for cross-industry content

    -- The actual content that was embedded
    title TEXT NOT NULL,
    content TEXT NOT NULL,       -- The text that was embedded
    metadata JSONB DEFAULT '{}', -- Additional structured data (pricing, scores, etc.)

    -- Vector embedding (OpenAI text-embedding-3-small = 1536 dimensions)
    embedding vector(1536),

    -- Source tracking
    source_file TEXT,            -- Original JSON file path
    source_url TEXT,             -- External source URL if applicable

    -- Versioning
    content_hash TEXT,           -- Hash of content for change detection
    embedded_at TIMESTAMPTZ DEFAULT NOW(),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure unique content
    UNIQUE(content_type, content_id)
);

-- ============================================================================
-- INDEXES FOR FAST RETRIEVAL
-- ============================================================================

-- Vector similarity search index (IVFFlat for good balance of speed/accuracy)
-- Lists = sqrt(n) where n is expected row count, start with 100 for ~10k rows
CREATE INDEX knowledge_embeddings_vector_idx
ON knowledge_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Filter indexes
CREATE INDEX knowledge_embeddings_content_type_idx ON knowledge_embeddings(content_type);
CREATE INDEX knowledge_embeddings_industry_idx ON knowledge_embeddings(industry);
CREATE INDEX knowledge_embeddings_content_type_industry_idx ON knowledge_embeddings(content_type, industry);

-- ============================================================================
-- VENDOR EMBEDDINGS (extend existing vendor_catalog)
-- ============================================================================

-- Add embedding column to vendor_catalog if it exists
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'vendor_catalog') THEN
        ALTER TABLE vendor_catalog ADD COLUMN IF NOT EXISTS embedding vector(1536);
        ALTER TABLE vendor_catalog ADD COLUMN IF NOT EXISTS embedded_at TIMESTAMPTZ;
    END IF;
END $$;

-- ============================================================================
-- SEARCH FUNCTIONS
-- ============================================================================

-- Semantic search function with optional filters
CREATE OR REPLACE FUNCTION search_knowledge(
    query_embedding vector(1536),
    match_count INT DEFAULT 10,
    filter_content_type TEXT DEFAULT NULL,
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
    SELECT
        ke.id,
        ke.content_type,
        ke.content_id,
        ke.industry,
        ke.title,
        ke.content,
        ke.metadata,
        1 - (ke.embedding <=> query_embedding) AS similarity
    FROM knowledge_embeddings ke
    WHERE
        (filter_content_type IS NULL OR ke.content_type = filter_content_type)
        AND (filter_industry IS NULL OR ke.industry = filter_industry OR ke.industry IS NULL)
        AND 1 - (ke.embedding <=> query_embedding) > similarity_threshold
    ORDER BY ke.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Search within specific content types
CREATE OR REPLACE FUNCTION search_vendors_semantic(
    query_embedding vector(1536),
    match_count INT DEFAULT 5,
    filter_industry TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    content_id TEXT,
    title TEXT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        ke.id,
        ke.content_id,
        ke.title,
        ke.content,
        ke.metadata,
        1 - (ke.embedding <=> query_embedding) AS similarity
    FROM knowledge_embeddings ke
    WHERE
        ke.content_type = 'vendor'
        AND (filter_industry IS NULL OR ke.industry = filter_industry OR ke.industry IS NULL)
    ORDER BY ke.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Search opportunities by pain point similarity
CREATE OR REPLACE FUNCTION search_opportunities_semantic(
    query_embedding vector(1536),
    match_count INT DEFAULT 5,
    filter_industry TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
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
    SELECT
        ke.id,
        ke.content_id,
        ke.industry,
        ke.title,
        ke.content,
        ke.metadata,
        1 - (ke.embedding <=> query_embedding) AS similarity
    FROM knowledge_embeddings ke
    WHERE
        ke.content_type = 'opportunity'
        AND (filter_industry IS NULL OR ke.industry = filter_industry)
    ORDER BY ke.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Multi-type search for comprehensive retrieval
CREATE OR REPLACE FUNCTION search_all_knowledge(
    query_embedding vector(1536),
    match_count_per_type INT DEFAULT 3,
    filter_industry TEXT DEFAULT NULL
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
        AND (filter_industry IS NULL OR ke.industry = filter_industry)
        ORDER BY ke.embedding <=> query_embedding
        LIMIT match_count_per_type
    )
    UNION ALL
    (
        -- Case studies / examples
        SELECT ke.id, ke.content_type, ke.content_id, ke.industry, ke.title, ke.content, ke.metadata,
               1 - (ke.embedding <=> query_embedding) AS similarity
        FROM knowledge_embeddings ke
        WHERE ke.content_type IN ('case_study', 'insight', 'pattern')
        ORDER BY ke.embedding <=> query_embedding
        LIMIT match_count_per_type
    )
    ORDER BY similarity DESC;
END;
$$;

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

-- Knowledge embeddings are public read (no tenant isolation needed)
ALTER TABLE knowledge_embeddings ENABLE ROW LEVEL SECURITY;

-- Everyone can read knowledge
CREATE POLICY "Knowledge is publicly readable"
ON knowledge_embeddings FOR SELECT
USING (true);

-- Only service role can insert/update/delete
CREATE POLICY "Service role can manage knowledge"
ON knowledge_embeddings FOR ALL
USING (auth.role() = 'service_role');

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Upsert knowledge embedding
CREATE OR REPLACE FUNCTION upsert_knowledge_embedding(
    p_content_type TEXT,
    p_content_id TEXT,
    p_industry TEXT,
    p_title TEXT,
    p_content TEXT,
    p_metadata JSONB,
    p_embedding vector(1536),
    p_source_file TEXT DEFAULT NULL,
    p_content_hash TEXT DEFAULT NULL
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    result_id UUID;
BEGIN
    INSERT INTO knowledge_embeddings (
        content_type, content_id, industry, title, content, metadata,
        embedding, source_file, content_hash, embedded_at
    )
    VALUES (
        p_content_type, p_content_id, p_industry, p_title, p_content, p_metadata,
        p_embedding, p_source_file, p_content_hash, NOW()
    )
    ON CONFLICT (content_type, content_id)
    DO UPDATE SET
        industry = EXCLUDED.industry,
        title = EXCLUDED.title,
        content = EXCLUDED.content,
        metadata = EXCLUDED.metadata,
        embedding = EXCLUDED.embedding,
        source_file = EXCLUDED.source_file,
        content_hash = EXCLUDED.content_hash,
        embedded_at = NOW(),
        updated_at = NOW()
    RETURNING id INTO result_id;

    RETURN result_id;
END;
$$;

-- Get embedding stats
CREATE OR REPLACE FUNCTION get_embedding_stats()
RETURNS TABLE (
    content_type TEXT,
    count BIGINT,
    industries TEXT[],
    last_updated TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        ke.content_type,
        COUNT(*)::BIGINT,
        ARRAY_AGG(DISTINCT ke.industry) FILTER (WHERE ke.industry IS NOT NULL),
        MAX(ke.embedded_at)
    FROM knowledge_embeddings ke
    GROUP BY ke.content_type
    ORDER BY COUNT(*) DESC;
END;
$$;
