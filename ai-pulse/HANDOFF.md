# AI Pulse - Handoff Document

## Project Status: ~75% Complete

**Location:** `/Users/larsmusic/CRB Analyser/crb-analyser/ai-pulse/`

---

## COMPLETED

### Backend (100% done)
- `backend/src/config/` - settings, supabase, redis, observability, sources (50+ AI sources)
- `backend/src/middleware/` - auth, error_handler, request_logger
- `backend/src/models/` - schemas, enums (Pydantic models)
- `backend/src/routes/` - auth, articles, digests, sources, checkout, webhooks, admin
- `backend/src/scrapers/` - base, rss, youtube, reddit, twitter
- `backend/src/scoring/` - rules (keyword-based), ai_scorer (Gemini + Claude)
- `backend/src/services/` - digest_service, scheduler_service, email (Brevo + SendGrid)
- `backend/src/jobs/` - fetch_articles, send_digests, cleanup
- `backend/src/main.py` - FastAPI app with lifespan
- `backend/supabase/migrations/001_initial_schema.sql` - full schema

### Frontend (partial)
- `frontend/package.json`, `vite.config.ts`, `tailwind.config.js` - config done
- `frontend/src/main.tsx`, `index.css`, `App.tsx` - entry points done

---

## REMAINING TASKS

### 1. Frontend Auth & API Client
Create:
- `frontend/src/contexts/AuthContext.tsx` - copy pattern from CRB's `/frontend/src/contexts/AuthContext.tsx`
- `frontend/src/services/apiClient.ts` - copy from CRB's `/frontend/src/services/apiClient.ts`

### 2. Frontend Pages
Create in `frontend/src/pages/`:
- `Landing.tsx` - dark theme, hero, pricing ($1/month), sources list
- `Login.tsx` - simple email/password form
- `Signup.tsx` - email/password + timezone + preferred_time selector
- `Dashboard.tsx` - recent articles feed, digest preview
- `Settings.tsx` - update timezone, preferred_time
- `DigestArchive.tsx` - past digests list

### 3. Frontend Components
Create in `frontend/src/components/`:
- `ArticleCard.tsx` - thumbnail, title, source badge, summary
- `DigestPreview.tsx` - list of articles
- `PricingCard.tsx` - $1/month or $10/year

### 4. Environment Files
Create:
- `backend/.env.example`
- `frontend/.env.example`
- `backend/requirements.txt`
- Root `README.md`

### 5. Design Document
Write to `docs/plans/2026-01-05-ai-pulse-design.md`

---

## KEY DECISIONS MADE

- **Sources:** All 4 types (RSS, YouTube, Reddit, Twitter) from day 1
- **Scoring:** Tiered - rules (free) → Gemini Flash (~$0.20/day) → Claude Haiku for summaries
- **Database:** Supabase
- **Email:** Brevo primary + SendGrid backup
- **Pricing:** €1/month EUR, $1/month USD, $10/year annual
- **Digest timing:** User choice (morning 7AM, lunch 12PM default, evening 6PM) in local timezone
- **Personalization:** None for v1 - everyone gets same top 10
- **Deploy:** Railway for both frontend and backend

---

## CONTINUATION PROMPT

```
Continue building the AI Pulse project at /Users/larsmusic/CRB Analyser/crb-analyser/ai-pulse/

REMAINING TASKS:
1. Create frontend/src/contexts/AuthContext.tsx (copy pattern from CRB Analyser)
2. Create frontend/src/services/apiClient.ts (copy pattern from CRB Analyser)
3. Create frontend pages: Landing.tsx, Login.tsx, Signup.tsx, Dashboard.tsx, Settings.tsx, DigestArchive.tsx
4. Create frontend components: ArticleCard.tsx, DigestPreview.tsx, PricingCard.tsx
5. Create backend/.env.example and frontend/.env.example
6. Create backend/requirements.txt
7. Create root README.md

Reference CRB Analyser patterns at /Users/larsmusic/CRB Analyser/crb-analyser/ for frontend components.

The backend is complete. Focus on finishing frontend and env files.
```
