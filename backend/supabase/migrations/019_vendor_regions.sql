-- Migration: 019_vendor_regions.sql
-- Description: Add multi-region support to vendor system
-- Date: 2026-01-24

-- ============================================================================
-- ADD REGION/COUNTRY SUPPORT TO VENDORS
-- ============================================================================

-- Countries where vendor operates (ISO 3166-1 alpha-2 codes)
-- Primary: US, CA, UK, NZ, AU
-- Secondary: IE, NL, DE, SE, DK, NO
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS
  countries TEXT[] DEFAULT '{}';

-- Vendor tier for recommendation priority
-- 1 = Primary recommendation (full detail)
-- 2 = Alternative (essentials)
-- 3 = Niche/specialized (minimal)
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS
  tier INTEGER DEFAULT 2 CHECK (tier BETWEEN 1 AND 3);

-- Home services specific subcategory
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS
  home_services_subcategory TEXT;

-- One-liner description for Tier 3 vendors
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS
  one_liner TEXT;

-- ============================================================================
-- INDEXES FOR EFFICIENT FILTERING
-- ============================================================================

-- GIN index for country array filtering
CREATE INDEX IF NOT EXISTS idx_vendors_countries
  ON vendors USING GIN(countries);

-- Index for tier-based sorting
CREATE INDEX IF NOT EXISTS idx_vendors_tier
  ON vendors(tier);

-- Composite index for common query pattern: country + category + tier
CREATE INDEX IF NOT EXISTS idx_vendors_country_category_tier
  ON vendors(category, tier)
  WHERE status = 'active';

-- ============================================================================
-- HOME SERVICES SUBCATEGORIES
-- ============================================================================

-- Add home services subcategories to vendor_categories if not exists
INSERT INTO vendor_categories (slug, name, description, display_order) VALUES
  ('field-service-management', 'Field Service Management', 'All-in-one platforms for scheduling, dispatch, invoicing', 20),
  ('quoting-estimating', 'Quoting & Estimating', 'Tools for creating quotes and estimates', 21),
  ('accounting-finance', 'Accounting & Finance', 'Bookkeeping and financial management', 22),
  ('communication-reputation', 'Communication & Reputation', 'Customer communication and review management', 23),
  ('call-handling', 'Call Handling & Answering', 'Phone answering and AI call services', 24),
  ('payments-financing', 'Payments & Financing', 'Payment processing and customer financing', 25),
  ('fleet-gps', 'Fleet & GPS Tracking', 'Vehicle tracking and fleet management', 26),
  ('marketing-lead-gen', 'Marketing & Lead Gen', 'Lead generation and marketing platforms', 27)
ON CONFLICT (slug) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  display_order = EXCLUDED.display_order;

-- ============================================================================
-- HELPER FUNCTION: GET VENDORS BY COUNTRY
-- ============================================================================

CREATE OR REPLACE FUNCTION get_vendors_by_country(
  target_country TEXT,
  target_category TEXT DEFAULT NULL,
  target_tier INTEGER DEFAULT NULL,
  max_results INTEGER DEFAULT 50
)
RETURNS TABLE (
  id UUID,
  slug TEXT,
  name TEXT,
  category TEXT,
  tier INTEGER,
  pricing JSONB,
  best_for TEXT[],
  pros TEXT[],
  cons TEXT[]
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    v.id,
    v.slug,
    v.name,
    v.category,
    v.tier,
    v.pricing,
    v.best_for,
    ARRAY(SELECT unnest(string_to_array(v.our_notes, '|'))) as pros,  -- temporary until we add pros/cons columns
    v.avoid_if as cons
  FROM vendors v
  WHERE v.status = 'active'
    AND target_country = ANY(v.countries)
    AND (target_category IS NULL OR v.category = target_category)
    AND (target_tier IS NULL OR v.tier <= target_tier)
  ORDER BY v.tier ASC, v.our_rating DESC NULLS LAST
  LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- ROLLBACK
-- ============================================================================
-- To rollback this migration, run:
-- ALTER TABLE vendors DROP COLUMN IF EXISTS countries;
-- ALTER TABLE vendors DROP COLUMN IF EXISTS tier;
-- ALTER TABLE vendors DROP COLUMN IF EXISTS home_services_subcategory;
-- ALTER TABLE vendors DROP COLUMN IF EXISTS one_liner;
-- DROP INDEX IF EXISTS idx_vendors_countries;
-- DROP INDEX IF EXISTS idx_vendors_tier;
-- DROP INDEX IF EXISTS idx_vendors_country_category_tier;
-- DROP FUNCTION IF EXISTS get_vendors_by_country;
