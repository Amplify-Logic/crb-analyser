-- Migration: 012_vendor_database.sql
-- Description: Create vendor knowledge base tables for admin management
-- Date: 2025-12-31

-- Enable pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- VENDORS TABLE
-- Main table storing all vendor/tool information
-- ============================================================================

CREATE TABLE IF NOT EXISTS vendors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  category TEXT NOT NULL,  -- 'crm', 'customer_support', 'ai_sales_tools', etc.
  subcategory TEXT,

  -- Core info
  website TEXT,
  pricing_url TEXT,
  description TEXT,
  tagline TEXT,

  -- Pricing (JSONB for flexibility)
  -- Structure: {model, currency, tiers[], starting_price, free_tier, custom_pricing, free_trial_days, startup_discount}
  pricing JSONB,

  -- Fit criteria
  company_sizes TEXT[] DEFAULT '{}',  -- ['startup', 'smb', 'mid_market', 'enterprise']
  industries TEXT[] DEFAULT '{}',      -- ['dental', 'recruiting', 'saas', 'professional-services', etc.]
  best_for TEXT[] DEFAULT '{}',
  avoid_if TEXT[] DEFAULT '{}',

  -- Recommendations
  recommended_default BOOLEAN DEFAULT false,
  recommended_for TEXT[] DEFAULT '{}',  -- ['website_chat', 'sales_enrichment', 'lead_research']

  -- Ratings
  our_rating DECIMAL(2,1),
  our_notes TEXT,
  g2_score DECIMAL(2,1),
  g2_reviews INTEGER,
  capterra_score DECIMAL(2,1),
  capterra_reviews INTEGER,

  -- Implementation
  implementation_weeks INTEGER,
  implementation_complexity TEXT CHECK (implementation_complexity IN ('low', 'medium', 'high')),
  implementation_cost JSONB,  -- {diy: {min, max}, with_help: {min, max}, full_service: {min, max}}
  requires_developer BOOLEAN DEFAULT false,

  -- Integrations & API
  integrations TEXT[] DEFAULT '{}',
  api_available BOOLEAN DEFAULT false,
  api_type TEXT,  -- 'REST', 'GraphQL', etc.
  api_docs_url TEXT,

  -- Competitors & alternatives
  competitors TEXT[] DEFAULT '{}',

  -- Key capabilities (for display)
  key_capabilities TEXT[] DEFAULT '{}',

  -- Metadata
  verified_at TIMESTAMPTZ,
  verified_by TEXT,
  source_url TEXT,
  notes TEXT,
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'deprecated', 'needs_review')),

  -- Deprecation info (if status = 'deprecated')
  deprecated_at TIMESTAMPTZ,
  deprecated_reason TEXT,
  replacement_vendor_id UUID REFERENCES vendors(id),

  -- Semantic search embedding
  embedding VECTOR(1536),

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_vendors_slug ON vendors(slug);
CREATE INDEX IF NOT EXISTS idx_vendors_category ON vendors(category);
CREATE INDEX IF NOT EXISTS idx_vendors_status ON vendors(status);
CREATE INDEX IF NOT EXISTS idx_vendors_recommended ON vendors(recommended_default) WHERE recommended_default = true;
CREATE INDEX IF NOT EXISTS idx_vendors_industries ON vendors USING GIN(industries);
CREATE INDEX IF NOT EXISTS idx_vendors_company_sizes ON vendors USING GIN(company_sizes);
CREATE INDEX IF NOT EXISTS idx_vendors_recommended_for ON vendors USING GIN(recommended_for);
CREATE INDEX IF NOT EXISTS idx_vendors_verified_at ON vendors(verified_at);

-- Semantic search index (IVFFlat for approximate nearest neighbor)
CREATE INDEX IF NOT EXISTS idx_vendors_embedding ON vendors
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- ============================================================================
-- INDUSTRY VENDOR TIERS TABLE
-- Maps vendors to industry-specific tier rankings with boost scores
-- ============================================================================

CREATE TABLE IF NOT EXISTS industry_vendor_tiers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  industry TEXT NOT NULL,  -- 'dental', 'recruiting', 'home-services', etc.
  vendor_id UUID NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
  tier INTEGER NOT NULL CHECK (tier BETWEEN 1 AND 3),  -- 1 = top pick, 2 = recommended, 3 = alternative
  boost_score INTEGER DEFAULT 0,  -- Extra points added in vendor matching
  notes TEXT,

  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),

  -- Each vendor can only appear once per industry
  UNIQUE(industry, vendor_id)
);

CREATE INDEX IF NOT EXISTS idx_industry_tiers_industry ON industry_vendor_tiers(industry);
CREATE INDEX IF NOT EXISTS idx_industry_tiers_vendor ON industry_vendor_tiers(vendor_id);
CREATE INDEX IF NOT EXISTS idx_industry_tiers_tier ON industry_vendor_tiers(tier);

-- ============================================================================
-- VENDOR AUDIT LOG TABLE
-- Tracks all changes to vendors for accountability and rollback
-- ============================================================================

CREATE TABLE IF NOT EXISTS vendor_audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vendor_id UUID REFERENCES vendors(id) ON DELETE SET NULL,
  vendor_slug TEXT NOT NULL,  -- Preserved even if vendor deleted
  action TEXT NOT NULL CHECK (action IN ('create', 'update', 'delete', 'deprecate', 'restore')),
  changed_by TEXT NOT NULL,  -- 'claude-code', 'admin-ui', email, etc.
  changes JSONB,  -- {field: {old: value, new: value}, ...}

  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_vendor ON vendor_audit_log(vendor_id);
CREATE INDEX IF NOT EXISTS idx_audit_slug ON vendor_audit_log(vendor_slug);
CREATE INDEX IF NOT EXISTS idx_audit_action ON vendor_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_created ON vendor_audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_changed_by ON vendor_audit_log(changed_by);

-- ============================================================================
-- VENDOR CATEGORIES TABLE (Reference)
-- Lookup table for valid vendor categories
-- ============================================================================

CREATE TABLE IF NOT EXISTS vendor_categories (
  slug TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  icon TEXT,  -- Optional icon identifier
  display_order INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Seed vendor categories
INSERT INTO vendor_categories (slug, name, description, display_order) VALUES
  ('ai_assistants', 'AI Assistants', 'Consumer AI assistant subscriptions for productivity and research', 1),
  ('ai_agents', 'AI Agents', 'No-code and low-code platforms for building autonomous AI agents', 2),
  ('ai_content_creation', 'AI Content Creation', 'AI-powered content creation tools for video and multimedia', 3),
  ('ai_sales_tools', 'AI Sales Tools', 'AI-powered sales tools for prospecting and meeting intelligence', 4),
  ('analytics', 'Analytics', 'Product analytics and behavior tracking platforms', 5),
  ('automation', 'Automation', 'Workflow automation and integration platforms', 6),
  ('crm', 'CRM', 'Customer Relationship Management platforms', 7),
  ('customer_support', 'Customer Support', 'Helpdesk and customer service platforms', 8),
  ('dev_tools', 'Dev Tools', 'Developer tools for code hosting and deployment', 9),
  ('ecommerce', 'E-commerce', 'E-commerce platforms for online stores', 10),
  ('finance', 'Finance', 'Accounting and financial management software', 11),
  ('hr_payroll', 'HR & Payroll', 'Human resources and payroll platforms', 12),
  ('marketing', 'Marketing', 'Email marketing and marketing automation', 13),
  ('project_management', 'Project Management', 'Project and task management platforms', 14)
ON CONFLICT (slug) DO NOTHING;

-- ============================================================================
-- SUPPORTED INDUSTRIES TABLE (Reference)
-- Lookup table for industries we support with tier lists
-- ============================================================================

CREATE TABLE IF NOT EXISTS supported_industries (
  slug TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  priority TEXT CHECK (priority IN ('primary', 'secondary', 'expansion', 'legacy')),
  display_order INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Seed supported industries
INSERT INTO supported_industries (slug, name, priority, display_order) VALUES
  ('dental', 'Dental', 'primary', 1),
  ('home-services', 'Home Services', 'primary', 2),
  ('professional-services', 'Professional Services', 'primary', 3),
  ('recruiting', 'Recruiting', 'secondary', 4),
  ('coaching', 'Coaching', 'secondary', 5),
  ('veterinary', 'Veterinary', 'secondary', 6),
  ('physical-therapy', 'Physical Therapy', 'expansion', 7),
  ('medspa', 'MedSpa', 'expansion', 8)
ON CONFLICT (slug) DO NOTHING;

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE vendors ENABLE ROW LEVEL SECURITY;
ALTER TABLE industry_vendor_tiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE supported_industries ENABLE ROW LEVEL SECURITY;

-- VENDORS: Public read, service role write
CREATE POLICY "vendors_select_public"
  ON vendors FOR SELECT
  USING (true);

CREATE POLICY "vendors_insert_service"
  ON vendors FOR INSERT
  WITH CHECK (true);  -- Service key bypasses RLS anyway

CREATE POLICY "vendors_update_service"
  ON vendors FOR UPDATE
  USING (true)
  WITH CHECK (true);

CREATE POLICY "vendors_delete_service"
  ON vendors FOR DELETE
  USING (true);

-- INDUSTRY VENDOR TIERS: Public read, service role write
CREATE POLICY "industry_tiers_select_public"
  ON industry_vendor_tiers FOR SELECT
  USING (true);

CREATE POLICY "industry_tiers_insert_service"
  ON industry_vendor_tiers FOR INSERT
  WITH CHECK (true);

CREATE POLICY "industry_tiers_update_service"
  ON industry_vendor_tiers FOR UPDATE
  USING (true)
  WITH CHECK (true);

CREATE POLICY "industry_tiers_delete_service"
  ON industry_vendor_tiers FOR DELETE
  USING (true);

-- VENDOR AUDIT LOG: Public read, service role insert only
CREATE POLICY "audit_log_select_public"
  ON vendor_audit_log FOR SELECT
  USING (true);

CREATE POLICY "audit_log_insert_service"
  ON vendor_audit_log FOR INSERT
  WITH CHECK (true);

-- REFERENCE TABLES: Public read only
CREATE POLICY "vendor_categories_select_public"
  ON vendor_categories FOR SELECT
  USING (true);

CREATE POLICY "supported_industries_select_public"
  ON supported_industries FOR SELECT
  USING (true);

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_vendor_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at on vendors
DROP TRIGGER IF EXISTS trigger_vendors_updated_at ON vendors;
CREATE TRIGGER trigger_vendors_updated_at
  BEFORE UPDATE ON vendors
  FOR EACH ROW
  EXECUTE FUNCTION update_vendor_updated_at();

-- Trigger to auto-update updated_at on industry_vendor_tiers
DROP TRIGGER IF EXISTS trigger_industry_tiers_updated_at ON industry_vendor_tiers;
CREATE TRIGGER trigger_industry_tiers_updated_at
  BEFORE UPDATE ON industry_vendor_tiers
  FOR EACH ROW
  EXECUTE FUNCTION update_vendor_updated_at();

-- Function to search vendors semantically
CREATE OR REPLACE FUNCTION search_vendors_semantic(
  query_embedding VECTOR(1536),
  match_threshold FLOAT DEFAULT 0.7,
  match_count INT DEFAULT 10,
  filter_category TEXT DEFAULT NULL,
  filter_industry TEXT DEFAULT NULL,
  filter_company_size TEXT DEFAULT NULL
)
RETURNS TABLE (
  id UUID,
  slug TEXT,
  name TEXT,
  category TEXT,
  description TEXT,
  similarity FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    v.id,
    v.slug,
    v.name,
    v.category,
    v.description,
    1 - (v.embedding <=> query_embedding) AS similarity
  FROM vendors v
  WHERE v.status = 'active'
    AND v.embedding IS NOT NULL
    AND 1 - (v.embedding <=> query_embedding) > match_threshold
    AND (filter_category IS NULL OR v.category = filter_category)
    AND (filter_industry IS NULL OR filter_industry = ANY(v.industries))
    AND (filter_company_size IS NULL OR filter_company_size = ANY(v.company_sizes))
  ORDER BY v.embedding <=> query_embedding
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- ROLLBACK
-- ============================================================================
-- To rollback this migration, run:
-- DROP TABLE IF EXISTS vendor_audit_log CASCADE;
-- DROP TABLE IF EXISTS industry_vendor_tiers CASCADE;
-- DROP TABLE IF EXISTS vendors CASCADE;
-- DROP TABLE IF EXISTS vendor_categories CASCADE;
-- DROP TABLE IF EXISTS supported_industries CASCADE;
-- DROP FUNCTION IF EXISTS update_vendor_updated_at CASCADE;
-- DROP FUNCTION IF EXISTS search_vendors_semantic CASCADE;
