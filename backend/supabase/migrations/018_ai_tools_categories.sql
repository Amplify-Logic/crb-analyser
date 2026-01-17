-- Migration: 018_ai_tools_categories.sql
-- Description: Add new vendor categories for AI coding tools, app builders, voice, video, and data scraping
-- Date: 2026-01-14

-- ============================================================================
-- ADD NEW VENDOR CATEGORIES
-- ============================================================================

INSERT INTO vendor_categories (slug, name, description, display_order) VALUES
  ('ai_coding_tools', 'AI Coding Tools', 'AI-native IDEs and coding assistants that democratize software development', 15),
  ('ai_app_builders', 'AI App Builders', 'AI-powered platforms for building apps without traditional coding', 16),
  ('ai_voice', 'AI Voice', 'Text-to-speech, speech-to-text, and voice AI platforms', 17),
  ('ai_video', 'AI Video', 'AI-powered video creation, editing, and avatar generation platforms', 18),
  ('data_scraping', 'Data & Scraping', 'Web scraping, data extraction, and automation platforms', 19)
ON CONFLICT (slug) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  display_order = EXCLUDED.display_order;

-- ============================================================================
-- ROLLBACK
-- ============================================================================
-- DELETE FROM vendor_categories WHERE slug IN ('ai_coding_tools', 'ai_app_builders', 'ai_voice', 'ai_video', 'data_scraping');
