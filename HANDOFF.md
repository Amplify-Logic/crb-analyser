# CRB Analyser - Handoff Document
**Date:** 2024-12-20

## Just Completed

### 1. Integration Phase (Enhanced Reports)
- `report_service.py` - Added playbook, architecture, insights generators
- `ReportViewer.tsx` - Added 4 new tabs: Playbook, Stack, ROI Calculator, Industry
- `playbook.py` routes - Progress tracking and ROI scenario endpoints

### 2. Session Persistence Fix
- Added `?new=true` to `/quiz` to force fresh session
- Landing page CTA clears old company data

### 3. AI-Powered Interview
- Upgraded from rule-based to Claude Sonnet 4
- Natural conversation with topic tracking

### 4. Sample Report
- Demo at `/api/reports/sample` and `/report/sample`

### 5. Progress Streaming Fix
- Research shows granular 10-60% progress during tool calls
- Step names: "Scanning website...", "Searching LinkedIn...", etc.

## IN PROGRESS - TASTER ENHANCEMENT

**Goal:** Enhance findings phase (Quiz.tsx ~line 667-880) with:

1. **AI Readiness Score Preview** - Gauge showing ~65%
2. **1-2 Teaser Recommendations** - Real opportunities, blur the rest
3. **Value Potential Estimate** - "€50K-120K/year savings"

### Code Location:
```
frontend/src/pages/Quiz.tsx
Line 797-858: Replace "Initial AI Insights" section with rich taster
```

## User Flow

```
FREE (5-10 min):
1. /quiz → Enter website
2. Research (~1 min) - SHOWS PROGRESS ✓
3. Findings phase - NEEDS TASTER ← HERE
4. Questions (5-10 dynamic)
5. Complete → €147 CTA

PAID:
6. /checkout → Stripe
7. /interview → 90-min AI workshop ✓
8. Report generation
9. /report/:id → Full report ✓
```

## Key Files

| File | Purpose |
|------|---------|
| `frontend/src/pages/Quiz.tsx` | **EDIT THIS** - findings phase taster |
| `frontend/src/pages/ReportViewer.tsx` | Report with new tabs |
| `frontend/src/pages/Interview.tsx` | 90-min workshop UI |
| `backend/src/routes/interview.py` | Claude interview API |
| `backend/src/agents/pre_research_agent.py` | Research with progress |
| `backend/src/data/sample_report.json` | Demo report |

## Servers

```bash
# Backend (8383)
cd backend && source venv/bin/activate && uvicorn src.main:app --reload --port 8383

# Frontend (5174)  
cd frontend && npm run dev
```

## Next Steps

1. **Enhance Quiz.tsx findings phase** with AI score, teaser recs, value estimate
2. **Test full E2E flow** - landing → research → taster → checkout → interview → report
3. **Try sample report** at http://localhost:5174/report/sample
