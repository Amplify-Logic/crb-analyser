# CRB Analyser - Next Session Prompt

Copy and paste this into a fresh Claude Code session:

---

## Context

I have **CRB Analyser** - an AI-powered Cost/Risk/Benefit analysis tool. The codebase is at `/Users/larsmusic/CRB Analyser/crb-analyser/`.

## Tech Stack
- **Backend:** FastAPI + Python 3.12 (port 8383)
- **Frontend:** React 18 + Vite + TypeScript (port 5174)
- **Database:** Supabase (PostgreSQL)
- **AI:** Anthropic Claude API
- **Web Search:** Brave API
- **Voice (optional):** Deepgram API

## Current State

### Just Built: Research-First Onboarding Flow
The new `/new-audit` page now:
1. User enters company name + website URL
2. Pre-Research Agent scrapes website, LinkedIn, Crunchbase, news, jobs
3. Builds company profile with confidence scores
4. Generates tailored questionnaire (only asks what we don't know)
5. User answers ~13 targeted questions
6. CRB Agent runs with enriched context

### Working Features
- Auth (signup, login, logout)
- Pre-Research Agent with web scraping
- Dynamic questionnaire generation
- Questions now display correctly in sections
- SSE streaming for research progress

## Immediate Tasks

### 1. Add Voice Input to Questions (Priority)

Setup:
```bash
cd backend && pip install deepgram-sdk==3.8.0
```

Add to `backend/.env`:
```
DEEPGRAM_API_KEY=your_key_here
```

Get free key: https://console.deepgram.com ($200 credits)

**Implementation needed in `frontend/src/components/research/DynamicQuestionnaireStep.tsx`:**
- Add mic icon next to text/textarea questions
- Click to start recording (pulsing red indicator)
- Click again to stop and transcribe
- Transcribed text appends to existing answer

### 2. Fix Confidence Cards Display

**File:** `frontend/src/components/research/DynamicQuestionnaireStep.tsx` (around line 286-302)

**Issue:** Cards show "high confidence" without the fact text

**Data from backend:**
```json
{"fact": "Amsterdam-based company", "confidence": "high"}
```

**Fix:** Change `fact.label` and `fact.value` to `fact.fact`

### 3. Complete Audit Creation Flow

After questionnaire, `POST /api/research/{id}/answers` should:
- Create client from profile
- Create audit record
- Return audit_id for redirect to `/audit/{id}/progress`

## Key Files

| What | File |
|------|------|
| Pre-Research Agent | `backend/src/agents/pre_research_agent.py` |
| Research Models | `backend/src/models/research.py` |
| Research Routes | `backend/src/routes/research.py` |
| Questionnaire Component | `frontend/src/components/research/DynamicQuestionnaireStep.tsx` |
| New Audit Page | `frontend/src/pages/NewAuditV2.tsx` |

## Quick Start

```bash
# Terminal 1 - Backend
cd /Users/larsmusic/CRB\ Analyser/crb-analyser/backend
source venv/bin/activate
uvicorn src.main:app --reload --port 8383

# Terminal 2 - Frontend
cd /Users/larsmusic/CRB\ Analyser/crb-analyser/frontend
npm run dev
```

## Test the Flow

1. Go to http://localhost:5174
2. Login (lars.tolhurst1@gmail.com)
3. Dashboard → New Audit
4. Enter "Aquablu" + "https://www.aquablu.com"
5. Watch research progress
6. Answer tailored questions
7. Select tier → Start analysis

---

Start by reading `HANDOFF.md` for full context, then implement voice input for the questionnaire.
