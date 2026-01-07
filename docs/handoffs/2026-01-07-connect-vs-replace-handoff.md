# Connect vs Replace Implementation Handoff

**Date:** 2026-01-07
**Status:** Implementation Complete — Needs Verification
**Design Doc:** `docs/plans/2026-01-07-connect-vs-replace-design.md`

---

## What Was Built

### Phase 1: API Openness Scoring ✅
Added API openness fields to vendor database for automation-first recommendations.

**Files:**
- `backend/supabase/migrations/015_vendor_api_openness.sql`
- `backend/src/models/vendor.py` — Added `ApiOpennessScore`, `VendorApiIntegration`
- `backend/src/services/vendor_service.py` — Added `API_OPENNESS_BOOST`, `get_automation_ready_vendors()`, `update_vendor_api_info()`
- `frontend/src/pages/admin/VendorAdmin.tsx` — API section in vendor editor
- `backend/src/scripts/audit_vendor_apis.py` — CLI for rating vendors

**Status:** Migration applied, 9 vendors rated, 188 need scores.

---

### Phase 2A: Quiz — Existing Stack Capture ✅
Added "What software do you use?" question to quiz.

**Expected Files:**
- `backend/supabase/migrations/016_existing_stack.sql`
- `backend/src/routes/quiz.py` — Accepts `existing_stack`
- `frontend/src/pages/Quiz.tsx` — Multi-select UI + "Other" free text

**Data Structure:**
```json
[
  {"slug": "hubspot", "source": "selected"},
  {"name": "CustomPMS", "source": "free_text"}
]
```

---

### Phase 2B: Unknown Software Research ✅
Auto-research software not in our vendor DB.

**Expected Files:**
- `backend/src/services/software_research_service.py`
- Integration in quiz submission or report generation

**Functionality:**
- Web search for API docs, Zapier, webhooks
- Claude summarizes → estimated API score
- Results cached in session or upserted to vendors as "unverified"

---

### Phase 2C: Finding Generation — Connect vs Replace ✅
Findings now show both paths.

**Expected Files:**
- `backend/src/services/report_service.py` — Updated
- `backend/src/skills/report-generation/finding_generation.py` — Updated
- New prompt template for Connect vs Replace

**Finding Format:**
```
FINDING: High No-Show Rate
Impact: €4,200/mo

Option A: CONNECT ✓ Recommended
  Open Dental → n8n → Twilio
  Cost: ~€30/mo | Effort: 6-8 hours

Option B: REPLACE
  Weave: €250/mo | Migration: 2-3 weeks

Verdict: Connect — your stack supports automation
```

---

### Phase 2D: Automation Summary Section ✅
Report ends with "Your Automation Roadmap".

**Expected Files:**
- `backend/src/models/report.py` — `AutomationSummary` model
- `backend/src/skills/report-generation/automation_summary.py`
- `frontend/src/components/report/AutomationRoadmap.tsx`

**Features:**
- Stack assessment with visual API scores
- Opportunities table (automation, impact, effort, approach)
- Tier-aware next steps messaging

---

## Verification Checklist

Run these to confirm everything works:

### 1. Backend Starts
```bash
cd backend && source venv/bin/activate
uvicorn src.main:app --reload --port 8383
# Should start without import errors
```

### 2. Frontend Starts
```bash
cd frontend && npm run dev
# Should compile without errors
```

### 3. Database Migration
```bash
# Check migration was applied
supabase db diff
# Or check in Supabase dashboard that existing_stack column exists on quiz_sessions
```

### 4. Quiz Flow Test
1. Go to `/quiz`
2. Complete industry/company questions
3. See "What software do you use?" question
4. Select some options + add "Other" free text
5. Complete quiz
6. Check session in DB has `existing_stack` populated

### 5. Report Generation Test
1. Complete a quiz with existing stack
2. Generate report (or use existing test endpoint)
3. Verify findings have Connect vs Replace sections
4. Verify Automation Roadmap appears at end

### 6. Type Checking
```bash
cd backend && mypy src --ignore-missing-imports
cd frontend && npm run typecheck  # if available
```

---

## Next Steps (Pick One)

### Option A: Populate Vendor API Scores
188 vendors still need API openness ratings.

```bash
cd backend && source venv/bin/activate

# See what needs rating
python -m src.scripts.audit_vendor_apis stats

# List unrated vendors
python -m src.scripts.audit_vendor_apis list

# Bulk update known vendors (add more to KNOWN_API_SCORES dict)
python -m src.scripts.audit_vendor_apis bulk

# Rate individual vendor
python -m src.scripts.audit_vendor_apis rate <slug> <score>
```

Or rate via Admin UI: `/admin/vendors` → Edit vendor → API section

---

### Option B: Test with Real Users
Deploy and gather feedback:
1. Push to staging/production
2. Monitor quiz completions with existing_stack data
3. Review generated reports for Connect vs Replace quality
4. Iterate based on feedback

---

### Option C: Sprint Tier Implementation
Build the "we implement for you" workflow:
1. When user upgrades to Sprint (€1,997)
2. Auto-create implementation project from their automation opportunities
3. Assign to implementation team
4. Track progress

---

### Option D: Fix/Polish Issues
If verification reveals issues:
1. Document the issue
2. Fix in isolated branch
3. Test and merge

---

## Key Decisions Made

1. **No automation templates** — Original Phase 2 planned n8n/Claude Code templates. Scrapped because users can't implement them. Focus on report value instead.

2. **Connect vs Replace framing** — Instead of "buy this software", show how to automate existing stack OR why replacement is needed.

3. **Light upsell** — Report-focused with one clear CTA. €497 includes strategy call. Sprint (€1,997) includes implementation.

4. **Web research for unknown software** — When user enters software not in our DB, auto-research its API capabilities.

5. **Tier-aware messaging** — Summary section adapts based on purchase tier.

---

## Prompt for Next Session

```
Read docs/handoffs/2026-01-07-connect-vs-replace-handoff.md

Run the verification checklist to confirm Phases 2A-2D work correctly.
Fix any issues found.
Then proceed with Option A (populate vendor API scores) or ask what's next.
```
