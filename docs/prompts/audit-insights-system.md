# Audit & Improve: Curated Insights System

## Context

We just built a Curated Insights System for storing and surfacing AI/industry insights from external content (YouTube transcripts, articles, research reports). The goal is to enrich our reports, quiz results, and landing page with credible, sourced insights.

## What was built

### Backend
- **Models**: `backend/src/models/insight.py` - Pydantic models for insights with types (trend, framework, case_study, statistic, quote, prediction), supporting data, tags, and source attribution
- **Service**: `backend/src/services/insight_service.py` - CRUD operations, tag-based filtering, basic semantic search
- **Extraction Skill**: `backend/src/skills/extraction/insight_extraction.py` - AI-powered extraction from raw content
- **API Routes**: `backend/src/routes/admin_insights.py` - Admin endpoints for list, search, create, update, delete, extract
- **CLI**: `backend/scripts/extract_insights.py` - Command-line tool for extraction and management
- **Storage**: `backend/src/knowledge/insights/curated/*.json` - JSON files per insight type

### Frontend
- **Admin Dashboard**: `frontend/src/pages/admin/AdminDashboard.tsx` - Central hub with stats and quick actions
- **Insights Admin**: `frontend/src/pages/admin/InsightsAdmin.tsx` - List, filter, edit, review insights
- **Insight Extractor**: `frontend/src/pages/admin/InsightExtractor.tsx` - Paste content → AI extracts → Review → Save

### Sample Content
- Raw transcript saved: `backend/src/knowledge/insights/raw/2026-01-jeff-su-ai-trends.txt` (Jeff Su's "Top 6 AI Trends for 2026")

## Your Task

Conduct a comprehensive audit of this system and implement improvements. Work through these areas:

### 1. Run the System End-to-End
- Start the backend (`cd backend && source venv/bin/activate && uvicorn src.main:app --reload --port 8383`)
- Start the frontend (`cd frontend && npm run dev`)
- Navigate to http://localhost:5174/admin
- Test the full extraction flow with the Jeff Su transcript
- Note any errors, UX friction, or missing functionality

### 2. Code Quality Audit
Review each file for:
- **Type safety**: Are all types properly defined? Any `Any` that should be specific?
- **Error handling**: Are errors caught and displayed appropriately?
- **Edge cases**: Empty states, loading states, error states all handled?
- **Code patterns**: Does it follow existing patterns in the codebase?
- **Security**: Any input validation missing? XSS risks in the UI?

### 3. UX/UI Improvements
Evaluate and improve:
- **Extraction flow**: Is it intuitive? Can we reduce steps?
- **Review workflow**: Is it easy to approve/edit/reject insights?
- **List view**: Are filters useful? Is the information hierarchy right?
- **Feedback**: Are loading states, success messages, errors clear?
- **Mobile**: Does it work on smaller screens?

### 4. Integration Gaps
The system stores insights but doesn't yet USE them. Implement or plan:
- **Report integration**: How do insights get woven into report sections?
- **Quiz results**: Where/how should we show 1-2 relevant insights?
- **Landing page**: How do we display rotating stats/quotes?
- **Service interface**: Does `insight_service.get_insights_for_surface()` work correctly?

### 5. Data Quality
- **Extraction prompt**: Is the AI extracting high-quality insights? Test with the Jeff Su transcript.
- **Credibility scoring**: Are sources being properly attributed?
- **Deduplication**: Can we detect similar insights?
- **Freshness**: Should insights have expiration dates?

### 6. Missing Features
Consider adding:
- **Bulk review**: Mark multiple insights as reviewed at once
- **Source management**: List/manage original sources separately
- **Import/export**: Backup and restore insights
- **Search**: Full-text search across all insights
- **Embeddings**: Vector search for better semantic matching
- **Usage tracking**: Which insights are being surfaced most?

### 7. Testing
- Add tests for `insight_service.py`
- Add tests for `insight_extraction.py` skill
- Add tests for admin API routes

## Approach

1. **First**: Run the system and test the extraction flow
2. **Second**: Fix any bugs or critical issues you find
3. **Third**: Implement UX improvements
4. **Fourth**: Add integration with at least one surface (report or landing page)
5. **Fifth**: Add tests for critical paths

## Key Files to Read

Start by reading these to understand the system:
```
backend/src/models/insight.py
backend/src/services/insight_service.py
backend/src/skills/extraction/insight_extraction.py
backend/src/routes/admin_insights.py
frontend/src/pages/admin/InsightsAdmin.tsx
frontend/src/pages/admin/InsightExtractor.tsx
docs/plans/2026-01-14-curated-insights-system.md
```

## Success Criteria

- [ ] Extraction flow works end-to-end without errors
- [ ] Jeff Su transcript extracts 8-12 quality insights
- [ ] Insights can be reviewed, edited, and saved
- [ ] At least one integration point is working (report OR landing page)
- [ ] Tests exist for the insight service
- [ ] UX is polished (loading states, error handling, empty states)

## Notes

- The system uses hybrid retrieval: tag-based filtering + semantic matching
- Insights are stored in JSON files, not the database (by design for now)
- Each insight has a `reviewed` flag - unreviewed insights shouldn't appear in production
- The extraction skill uses Claude Sonnet for cost efficiency

Good luck! Focus on making this system actually useful, not just functional.
