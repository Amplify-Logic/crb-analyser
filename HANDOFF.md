# CRB Analyser - Handoff Document

> **Last Updated:** December 14, 2025
> **Status:** Core flow working, pricing model validated

---

## Business Model (Updated)

```
FREE → €47 → €297 → €2,000+ Services
```

| Tier | Price | What They Get |
|------|-------|---------------|
| Free | €0 | AI Readiness Score + 3 teaser findings |
| Quick Report | €47 | Full findings (10-15) + basic ROI + PDF |
| Full Analysis | €297 | Above + vendor comparisons + 30-min call + 90-day support |
| Services | €2,000+ | Done-for-you implementation |

**Key insight:** €47 impulse buy qualifies serious buyers, €297 with call builds trust.

See `SCOPE.md` for full roadmap and revenue projections

---

## Latest Session Summary

### What Was Built This Session

#### 1. Pre-Research Agent
- **File:** `backend/src/agents/pre_research_agent.py`
- Scrapes company website using BeautifulSoup
- Searches LinkedIn, Crunchbase, news, job postings via Brave API
- Builds structured CompanyProfile with confidence scores
- Generates tailored questionnaire based on findings

#### 2. Research Models
- **File:** `backend/src/models/research.py`
- CompanyProfile schema with nested objects (basics, size, products, tech, etc.)
- DynamicQuestion schema with pre-filled values
- DynamicQuestionnaire with sections and question_ids mapping

#### 3. Research API Routes
- **File:** `backend/src/routes/research.py`
- `POST /api/research/start` - Start research, returns research_id
- `GET /api/research/{id}/stream` - SSE streaming progress
- `POST /api/research/{id}/answers` - Save questionnaire answers
- `GET /api/research/{id}` - Get research results

#### 4. Frontend Components
- `frontend/src/components/research/CompanyResearchStep.tsx` - Company input + research progress
- `frontend/src/components/research/DynamicQuestionnaireStep.tsx` - Tailored questions display
- `frontend/src/pages/NewAuditV2.tsx` - New research-first flow (now default at `/new-audit`)

#### 5. Database
- Created `company_research` table in Supabase (migration: `002_company_research.sql`)

---

## What Needs Work Next

### 1. Voice Input for Questions (Priority)

**Setup:**
```bash
cd backend && pip install deepgram-sdk==3.8.0
```

**Add to `backend/.env`:**
```
DEEPGRAM_API_KEY=your_key_here
```

Get free key at: https://console.deepgram.com ($200 free credits)

**Implementation needed in `DynamicQuestionnaireStep.tsx`:**
- Add mic icon next to text/textarea questions
- Click to start recording (pulsing red indicator)
- Click again to stop and transcribe
- Transcribed text appends to existing answer

### 2. Fix Confidence Cards Display

**Issue:** Cards show "high confidence" without the actual fact text.

**Data structure from backend:**
```json
{
  "fact": "Amsterdam-based health and wellness company",
  "confidence": "high"
}
```

**Fix in `DynamicQuestionnaireStep.tsx` around line 286-302:**
```tsx
// Change from:
<p className="text-xs text-gray-500 uppercase tracking-wide">{fact.label}</p>
<p className="text-sm font-medium text-gray-900 mt-1">
  {typeof fact.value === 'object' ? fact.value?.value : fact.value}
</p>

// To:
<p className="text-sm font-medium text-gray-900">{fact.fact}</p>
```

### 3. Complete Audit Creation Flow

After questionnaire completion, the `/api/research/{id}/answers` endpoint needs to:
- Create client from research profile
- Create audit record
- Link to research
- Return audit_id for redirect

---

## Commands to Start

```bash
# Terminal 1 - Backend
cd backend && source venv/bin/activate && uvicorn src.main:app --reload --port 8383

# Terminal 2 - Frontend
cd frontend && npm run dev

# Redis (for caching)
brew services start redis
```

---

## Test the Research Flow

1. Go to http://localhost:5174
2. Login (lars.tolhurst1@gmail.com)
3. Click "New Audit" from dashboard
4. Enter "Aquablu" + "https://www.aquablu.com"
5. Watch research progress (scrapes website, LinkedIn, etc.)
6. Answer tailored questions (now showing correctly!)
7. Select tier and start analysis

---

## Key Files (New)

| Area | File |
|------|------|
| Pre-Research Agent | `backend/src/agents/pre_research_agent.py` |
| Research Models | `backend/src/models/research.py` |
| Research Routes | `backend/src/routes/research.py` |
| Scraper Tools | `backend/src/tools/research_scraper_tools.py` |
| Research Step (FE) | `frontend/src/components/research/CompanyResearchStep.tsx` |
| Questionnaire (FE) | `frontend/src/components/research/DynamicQuestionnaireStep.tsx` |
| New Audit Page | `frontend/src/pages/NewAuditV2.tsx` |
| DB Migration | `backend/supabase/migrations/002_company_research.sql` |

---

## API Endpoints (New)

### Research
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/research/start` | Start company research |
| GET | `/api/research/{id}/stream` | SSE progress stream |
| GET | `/api/research/{id}` | Get research results |
| POST | `/api/research/{id}/answers` | Save questionnaire answers |

---

## Environment Variables

### Backend (.env)
```bash
# Required
SUPABASE_URL=https://hgytaxcglijrhhlnbmeh.supabase.co
SUPABASE_SERVICE_KEY=eyJ...  # Service role key
ANTHROPIC_API_KEY=sk-ant-...
BRAVE_API_KEY=...  # For web search in research

# Optional
DEEPGRAM_API_KEY=...  # For voice input
STRIPE_SECRET_KEY=sk_...
REDIS_URL=redis://localhost:6379
```

### Frontend (.env)
```bash
VITE_API_BASE_URL=http://localhost:8383
VITE_SUPABASE_URL=https://hgytaxcglijrhhlnbmeh.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
```

---

## Architecture: New Research-First Flow

```
┌─────────────────────────────────────────────────────────────┐
│  NEW ONBOARDING FLOW (Research-First)                       │
├─────────────────────────────────────────────────────────────┤
│  1. User provides: Company name + Website URL               │
│                                                             │
│  2. PRE-RESEARCH AGENT runs:                                │
│     ├── Scrape company website (about, services, team)      │
│     ├── LinkedIn (company size, tech stack from jobs)       │
│     ├── Crunchbase (funding, industry)                      │
│     ├── News (recent developments)                          │
│     └── Generate company profile with confidence scores     │
│                                                             │
│  3. QUESTION GENERATOR creates tailored questionnaire:      │
│     ├── Skip questions we already know (industry, size)     │
│     ├── Confirm uncertain items ("We think X, correct?")    │
│     ├── Add industry-specific deep questions                │
│     └── Focus on pain points & internal processes           │
│                                                             │
│  4. User answers ~10-15 targeted questions                  │
│                                                             │
│  5. CRB Agent runs with enriched context                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Bugs Fixed This Session

1. **DateTime serialization** - Added custom JSON serializer for datetime/enum objects
2. **Questions not showing** - Fixed section→question mapping (use `question_ids` array)
3. **Deepgram SDK** - Updated transcription service for new SDK API
4. **Empty email validation** - Filter empty strings before sending to backend

---

## Previous MVP Features (Still Working)

- Auth Flow (signup, login, logout)
- Client Management (CRUD)
- Audit Creation
- Intake Wizard (legacy at `/new-audit-legacy`)
- CRB Agent with 16 tools
- Progress Streaming (SSE)
- Report Generation (findings, recommendations)
- PDF Export
- Stripe Payments

---

**Status:** Research-first flow working, voice input implementation pending
