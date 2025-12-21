# CRB Analyser - Next Session Prompt

> **Last Session:** December 20, 2024
> **Read first:** `SESSION_SUMMARY_2024-12-20.md` for full context

---

## What Was Accomplished Last Session

1. ✅ Lennard briefing on Graham Shoes thinking
2. ✅ Clarified philosophy, underlying logic & system prompts
3. ✅ Showed software presentation and roadmap
4. ✅ Created comprehensive belief system clarification and implemented it
5. ✅ **Deep research on target industries** - 10 criteria PMF analysis
6. ✅ **Locked 8 target industries** across 3 tiers
7. ✅ **Built prompt system** with industry-specific configs (`backend/src/prompts/`)

---

## Target Industries (LOCKED)

### Tier 1 - Primary (Launch)
1. **Professional Services** (Legal/Accounting/Consulting) - 89/100
2. **Home Services** (HVAC/Plumbing/Electrical) - 85/100
3. **Dental** (Practices & DSOs) - 85/100

### Tier 2 - Secondary
4. **Recruiting/Staffing** - 82/100
5. **Coaching** (businesses) - 80/100
6. **Veterinary** - 80/100

### Tier 3 - Expansion
7. **Physical Therapy/Chiro** - 79/100
8. **MedSpa/Beauty** - 78/100

---

## This Session: Build to MVP

### Priority 1: Wire Prompt System into CRB Agent

The prompt system is built (`backend/src/prompts/crb_analysis_v1.py`).

**Task:** Integrate it with the CRB agent:

```python
from prompts import get_crb_prompt

# In crb_agent.py - use industry-specific prompts
prompt = get_crb_prompt(
    industry="dental",  # from quiz selection
    business_context={...}  # from intake/interview
)
```

**Files to modify:**
- `backend/src/agents/crb_agent.py`
- `backend/src/routes/interview.py` (pass industry context)

---

### Priority 2: Industry Selection in Intake

Users need to select their industry early in the flow.

**Task:** Add industry selection to quiz/intake:
- Map to the 8 industries in `INDUSTRY_CONFIGS`
- Store with session/report data
- Pass to prompt system

---

### Priority 3: Data Quality Framework

**CRITICAL:** Ensure we can iterate prompts based on outcomes.

**Task:** Track with each report:
```python
{
    "prompt_version": "1.0.0",
    "industry": "dental",
    "business_context": {...},
    "report_generated_at": "...",
    # Later: outcome tracking
    "outcome_tracked": false,
    "customer_purchased": null,
    "predicted_roi": null,
    "actual_roi": null,  # if we get follow-up
}
```

**Files to modify:**
- `backend/src/services/report_service.py`
- Database schema if needed

---

### Priority 4: Test Full Flow Per Industry

For each Tier 1 industry, test:
```
Quiz (select industry) → Intake → Interview → Report Generation → Report View
```

**Test with:**
1. Professional Services (e.g., small law firm)
2. Home Services (e.g., HVAC company)
3. Dental (e.g., 3-dentist practice)

---

### Priority 5: Previous Testing Items

From previous session notes (may still apply):
- [ ] Voice interview working OR documented as broken
- [ ] Report viewer confirmed working
- [ ] PDF export functional
- [ ] Terms/Privacy pages created

---

## Key Files to Review

| File | Purpose |
|------|---------|
| `backend/src/prompts/crb_analysis_v1.py` | Master prompt + 8 industry configs |
| `backend/src/agents/crb_agent.py` | Main CRB analysis agent |
| `docs/TARGET_INDUSTRIES.md` | Locked industry decisions |
| `SESSION_SUMMARY_2024-12-20.md` | Last session full context |
| `CLAUDE.md` | Development guide |

---

## Business Model Note

**Future expansion:** Have implementation partners perform work, CRB Analyser takes commission on referrals.

---

## Environment Setup

```bash
# Backend
cd backend && source venv/bin/activate && uvicorn src.main:app --reload --port 8383

# Frontend
cd frontend && npm run dev

# Redis
brew services start redis
```

---

## Success Criteria for This Session

- [ ] Prompt system integrated with CRB agent
- [ ] Industry selection in intake flow
- [ ] Data quality tracking in place (prompt version, industry, context)
- [ ] At least 1 full test per Tier 1 industry
- [ ] Reports quality-checked for each industry
- [ ] Remaining issues documented

---

## Positioning (Locked)

> "We help passion-driven service professionals - from lawyers to plumbers, dentists to recruiters - get the AI clarity they need to stop wasting time on admin and get back to the work they love."
