# Workshop Quality Improvement Handoff

**Date:** 2026-01-10
**Status:** Ready for implementation
**Previous Session:** Fixed quiz findings page with verified industry stats

---

## Session Summary: What Was Done

### Quiz Findings Page - Industry Stats (COMPLETED)

Fixed the hardcoded "15-25 hours/week" message on the quiz findings page. Now shows:

1. **Industry-specific verified stat** (green card) - only if industry recognized
2. **General McKinsey stat** (blue card) - always shown

#### Verified Stats Implemented:

| Industry | Stat | Source |
|----------|------|--------|
| Dental | "Automated reminders reduce dental no-shows by up to 38%" | [Dialog Health](https://www.dialoghealth.com/post/patient-appointment-reminder-statistics) |
| Recruiting | "Recruiters using AI save a full day per week (20% of time)" | [LinkedIn Future of Recruiting](https://business.linkedin.com/talent-solutions/resources/future-of-recruiting) |
| Coaching | "47% of coaches now use digital platforms — are you keeping up?" | [ICF Global Coaching Study](https://coachingfederation.org/resource/2025-icf-global-coaching-study-executive-summary/) |
| Home Services | "Technicians spend 30% of their day on admin, only 29% on actual service" | [Salesforce via Zuper](https://www.zuper.co/field-service/field-service-management-trends-2025) |
| Veterinary | "39% of vet practices want AI tools — early adopters gain the edge" | [AAHA/Digitail Survey](https://www.aaha.org/trends-magazine/trends-may-2024/applications-of-ai-in-veterinary-practice/) |
| Professional Services | "Lawyers bill just 37% of their day (2.9 hours) — AI can change that" | [Clio Legal Trends Report](https://www.clio.com/resources/legal-trends/2024-report/) |
| Fallback | "88% of organizations now use AI regularly — is yours capturing full value?" | [McKinsey State of AI 2025](https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai) |

**Files Modified:**
- `frontend/src/pages/Quiz.tsx` (lines 1686-1937)

---

## Workshop Quality Assessment

### Architecture Overview

The workshop is a **90-minute personalized session** with 3 phases:

```
Phase 1: Confirmation    → Verify research findings, prioritize pain points
Phase 2: Deep-Dive       → Adaptive Q&A per pain point (5 stages each)
Phase 2.5: Milestone     → Synthesized finding + ROI after each pain point
Phase 3: Synthesis       → Final questions, stakeholders, timeline
         ↓
      Report Generation
```

### What Works Well

- Clean phase-based architecture
- Good separation of concerns (skills, models, routes)
- Adaptive signal detection for personalization
- Resume capability via session state
- Voice/text input toggle
- Proper async/await patterns with logging

### Quality Issues Identified

#### HIGH PRIORITY

1. **Confidence Framework Not Enforced**
   - `WorkshopConfidence` class exists in `backend/src/models/workshop.py` but `is_ready_for_report()` gate is NOT enforced
   - Users can complete workshop without sufficient data quality
   - **Fix:** Enforce minimum confidence threshold before report generation

2. **Vendor Recommendations Are LLM-Generated**
   - Milestone synthesis generates vendor suggestions via LLM
   - No lookup against actual vendor database (`backend/src/knowledge/vendors/`)
   - **Fix:** Integrate vendor database lookup in milestone skill

3. **Milestone Feedback Not Actionable**
   - User can select "Needs adjustments" but cannot re-enter conversation
   - Feedback is stored but not used
   - **Fix:** Allow re-asking questions after adjustment request

4. **No Progress Persistence During Phases**
   - If user refreshes mid-deepdive, conversation is lost
   - Only phase transitions are persisted
   - **Fix:** Save conversation state on each message

#### MEDIUM PRIORITY

5. **Data Gaps Shown But Not Actionable**
   - Milestone shows "data gaps" warnings but user can't address them
   - **Fix:** Allow targeted follow-up questions for gaps

6. **Pain Point Extraction Limited**
   - Only extracts up to 5 pain points from quiz
   - No confidence ranking on pain points
   - Pain point IDs are simple strings (`pain_0`, `pain_1`)

7. **No Session Timeout/Conflict Detection**
   - Multiple tabs can cause stale data issues
   - No explicit session expiry logic
   - **Fix:** Add optimistic locking or tab conflict detection

#### LOW PRIORITY

8. **SynthesisForm Inline in Workshop.tsx**
   - Should be extracted to separate component for maintainability

9. **Type Safety Issues**
   - Frontend types don't perfectly match backend (camelCase vs snake_case)
   - Manual transformation needed in several places

10. **Skip to Summary Button**
    - Exists for testing but no production safeguard
    - Should be removed or hidden behind dev mode

---

## Key Files for Workshop

### Frontend
- `frontend/src/pages/Workshop.tsx` - Main orchestrator (554 lines)
- `frontend/src/components/workshop/WorkshopConfirmation.tsx` - Phase 1 (400 lines)
- `frontend/src/components/workshop/WorkshopDeepDive.tsx` - Phase 2 (400 lines)
- `frontend/src/components/workshop/WorkshopMilestone.tsx` - Milestone review (473 lines)

### Backend
- `backend/src/routes/workshop.py` - API endpoints (828 lines)
- `backend/src/models/workshop.py` - Data models (382 lines)
- `backend/src/skills/workshop/` - LLM skills:
  - `adaptive-signal-detector` - SyncSkill (no LLM)
  - `workshop-question` - Haiku 4.5 (question generation)
  - `milestone-synthesis` - Sonnet 4 (finding + ROI synthesis)

### API Endpoints
```
GET    /api/workshop/state/{session_id}    → Resume session
POST   /api/workshop/start                  → Phase 1 init
POST   /api/workshop/confirm                → Phase 1 → 2
POST   /api/workshop/respond                → Phase 2 Q&A loop
POST   /api/workshop/milestone              → Generate milestone
POST   /api/workshop/milestone/feedback     → Store feedback
POST   /api/workshop/complete               → Phase 3 → Report
```

---

## Recommended Implementation Order

### Phase 1: Critical Fixes (Do First)

1. **Enforce Confidence Gate**
   ```python
   # In workshop.py /complete endpoint
   if not workshop_confidence.is_ready_for_report():
       return {"error": "Insufficient data quality", "gaps": workshop_confidence.get_gaps()}
   ```

2. **Persist Conversation State**
   - Save messages array to `workshop_data.deep_dives[i].messages` on each response
   - Load on resume

3. **Integrate Vendor Database in Milestone**
   - In `milestone-synthesis` skill, lookup vendors from `backend/src/knowledge/vendors/`
   - Match by industry + category

### Phase 2: UX Improvements

4. **Actionable Milestone Feedback**
   - If "Needs adjustments" selected, show targeted follow-up questions
   - Use data gaps to drive questions

5. **Data Gap Follow-ups**
   - After milestone, if critical gaps exist, offer "Tell me more about X"

### Phase 3: Polish

6. **Extract SynthesisForm Component**
7. **Add Session Conflict Detection**
8. **Remove/Hide Skip Button in Production**

---

## Testing the Workshop

### Manual Test Flow

1. Complete quiz for a test company (use dev panel)
2. Ensure payment status is `paid` or bypass via admin
3. Navigate to `/workshop?session_id=XXX`
4. Test each phase:
   - **Welcome:** Start button, audio upload option
   - **Confirmation:** Rate cards, reorder pain points
   - **Deep-Dive:** Voice/text toggle, confidence bar, stage progression
   - **Milestone:** Finding summary, ROI, vendor suggestions
   - **Synthesis:** Final form, stakeholder input
   - **Complete:** Duration shown, navigation to report

### Key Things to Check

- [ ] Resume works after refresh (phases persist)
- [ ] Voice recording transcribes correctly
- [ ] Confidence bar updates with each response
- [ ] Milestone shows reasonable ROI estimates
- [ ] Vendor suggestions are relevant to industry
- [ ] Data gaps are identified when insufficient info
- [ ] Complete triggers report generation

---

## Context for New Session

### Quick Start Commands
```bash
# Backend (port 8383)
cd backend && source venv/bin/activate && uvicorn src.main:app --reload --port 8383

# Frontend (port 5174)
cd frontend && npm run dev

# Redis (required)
brew services start redis
```

### Pre-existing Build Errors
The frontend has pre-existing TypeScript errors in `Quiz.tsx` around lines 814-855 (unrelated to workshop):
- `setEmail` and `setCompanyWebsite` referenced but not defined
- These are WIP and don't affect workshop functionality

### Industry Slugs for Testing
- `dental`
- `recruiting`
- `coaching`
- `home-services`
- `veterinary`
- `professional-services`

---

## Summary

**Done:** Quiz findings page now shows verified, industry-specific stats with clickable sources.

**Next:** Workshop needs quality improvements:
1. Enforce confidence gate before report generation
2. Persist conversation state for resume
3. Integrate vendor database in milestone synthesis
4. Make milestone feedback actionable

The workshop architecture is solid but needs these fixes to ensure report quality matches quiz quality.
