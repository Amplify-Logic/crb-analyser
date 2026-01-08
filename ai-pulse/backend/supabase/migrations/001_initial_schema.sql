-- AI Pulse Initial Schema
-- Run this in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Users Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    timezone TEXT DEFAULT 'UTC',
    preferred_time TEXT DEFAULT 'lunch' CHECK (preferred_time IN ('morning', 'lunch', 'evening')),
    stripe_customer_id TEXT,
    subscription_status TEXT DEFAULT 'inactive' CHECK (subscription_status IN ('active', 'inactive', 'past_due', 'canceled', 'trialing')),
    subscription_id TEXT,
    currency TEXT DEFAULT 'USD' CHECK (currency IN ('USD', 'EUR')),
    role TEXT DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for subscription queries
CREATE INDEX idx_users_subscription_status ON users(subscription_status);
CREATE INDEX idx_users_preferred_time ON users(preferred_time);
CREATE INDEX idx_users_stripe_customer ON users(stripe_customer_id);

-- ============================================================================
-- Sources Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('rss', 'youtube', 'reddit', 'twitter')),
    url TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('ai_news', 'ai_agents', 'ai_tools', 'ai_research', 'ai_business', 'automation')),
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    enabled BOOLEAN DEFAULT TRUE,
    description TEXT,
    channel_id TEXT,  -- YouTube
    subreddit TEXT,   -- Reddit
    twitter_handle TEXT,  -- Twitter
    last_fetched_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fetching enabled sources by type
CREATE INDEX idx_sources_type_enabled ON sources(source_type, enabled);

-- ============================================================================
-- Articles Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id TEXT REFERENCES sources(slug) ON DELETE CASCADE,
    external_id TEXT NOT NULL,
    content_type TEXT NOT NULL CHECK (content_type IN ('article', 'video', 'post', 'paper', 'tweet')),
    title TEXT NOT NULL,
    description TEXT,
    url TEXT NOT NULL,
    thumbnail_url TEXT,
    published_at TIMESTAMPTZ NOT NULL,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    views INTEGER,
    likes INTEGER,
    comments INTEGER,
    score DECIMAL(5,4) DEFAULT 0,
    novelty_score DECIMAL(5,4) DEFAULT 0,
    impact_score DECIMAL(5,4) DEFAULT 0,
    summary TEXT,
    categories TEXT[] DEFAULT '{}',
    is_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_id, external_id)
);

-- Indexes for article queries
CREATE INDEX idx_articles_score ON articles(score DESC);
CREATE INDEX idx_articles_published ON articles(published_at DESC);
CREATE INDEX idx_articles_source ON articles(source_id);
CREATE INDEX idx_articles_fetched ON articles(fetched_at DESC);

-- ============================================================================
-- Digests Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS digests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    article_ids UUID[] NOT NULL,
    subject_line TEXT NOT NULL,
    stats JSONB DEFAULT '{}'
);

-- Index for recent digests
CREATE INDEX idx_digests_created ON digests(created_at DESC);

-- ============================================================================
-- Digest Sends Table (tracks who received which digest)
-- ============================================================================
CREATE TABLE IF NOT EXISTS digest_sends (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    digest_id UUID REFERENCES digests(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'opened', 'clicked', 'bounced', 'failed')),
    UNIQUE(digest_id, user_id)
);

-- Indexes for digest tracking
CREATE INDEX idx_digest_sends_user ON digest_sends(user_id);
CREATE INDEX idx_digest_sends_status ON digest_sends(status);
CREATE INDEX idx_digest_sends_sent ON digest_sends(sent_at DESC);

-- ============================================================================
-- Updated At Triggers
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sources_updated_at
    BEFORE UPDATE ON sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Row Level Security (RLS)
-- ============================================================================

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE digest_sends ENABLE ROW LEVEL SECURITY;

-- Users can only see their own record
CREATE POLICY users_select_own ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY users_update_own ON users
    FOR UPDATE USING (auth.uid() = id);

-- Digest sends - users can only see their own
CREATE POLICY digest_sends_select_own ON digest_sends
    FOR SELECT USING (auth.uid() = user_id);

-- Articles and sources are public read
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE digests ENABLE ROW LEVEL SECURITY;

CREATE POLICY articles_select_all ON articles FOR SELECT TO authenticated USING (true);
CREATE POLICY sources_select_all ON sources FOR SELECT TO authenticated USING (true);
CREATE POLICY digests_select_all ON digests FOR SELECT TO authenticated USING (true);

-- Service role can do everything (for backend)
CREATE POLICY users_service_all ON users TO service_role USING (true) WITH CHECK (true);
CREATE POLICY articles_service_all ON articles TO service_role USING (true) WITH CHECK (true);
CREATE POLICY sources_service_all ON sources TO service_role USING (true) WITH CHECK (true);
CREATE POLICY digests_service_all ON digests TO service_role USING (true) WITH CHECK (true);
CREATE POLICY digest_sends_service_all ON digest_sends TO service_role USING (true) WITH CHECK (true);

-- ============================================================================
-- Sample Sources (optional - uncomment to seed)
-- ============================================================================
-- INSERT INTO sources (slug, name, source_type, url, category, priority, description) VALUES
-- ('openai-blog', 'OpenAI Blog', 'rss', 'https://openai.com/blog/rss.xml', 'ai_news', 10, 'Official OpenAI announcements'),
-- ('anthropic-news', 'Anthropic News', 'rss', 'https://www.anthropic.com/feed.xml', 'ai_news', 10, 'Official Anthropic announcements'),
-- ('huggingface-blog', 'Hugging Face Blog', 'rss', 'https://huggingface.co/blog/feed.xml', 'ai_tools', 9, 'Open source AI models'),
-- ('techcrunch-ai', 'TechCrunch AI', 'rss', 'https://techcrunch.com/category/artificial-intelligence/feed/', 'ai_news', 8, 'AI industry news'),
-- ('r-machinelearning', 'r/MachineLearning', 'reddit', 'https://www.reddit.com/r/MachineLearning/', 'ai_research', 9, 'ML research discussions'),
-- ('r-localllama', 'r/LocalLLaMA', 'reddit', 'https://www.reddit.com/r/LocalLLaMA/', 'ai_tools', 9, 'Local LLM discussions')
-- ON CONFLICT (slug) DO NOTHING;
