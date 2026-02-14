# Audit Remediation Handoff - 2026-02-14

## What Was Done

Executed all 22 findings from `docs/handoffs/2026-02-14-product-audit-handoff.md` using 12 parallel agents across 2 waves. Commit: `a0e0bf7`.

**87 files changed, 5,953 insertions, 497 deletions. Tests: 549 passed (was 213), 8 pre-existing failures being fixed.**

---

## Changes by Category

### New Files Created
| File | Purpose |
|------|---------|
| `backend/src/knowledge/ecommerce/benchmarks.json` | E-commerce industry benchmarks |
| `backend/src/knowledge/ecommerce/processes.json` | E-commerce common processes + pain points |
| `backend/src/knowledge/ecommerce/opportunities.json` | 8 AI opportunities with ROI examples |
| `backend/src/knowledge/ecommerce/vendors.json` | 17 vendors across 6 categories |
| `backend/src/knowledge/industry_questions/ecommerce.json` | 14 quiz questions for e-commerce |
| `backend/src/skills/analysis/net_score_calculator.py` | NET SCORE formula SyncSkill |
| `backend/src/skills/report_generation_utils.py` | Vendor data formatting for LLM prompts |
| `backend/tests/test_crb_calculation_service.py` | 110 tests, 95% coverage |
| `frontend/src/utils/logger.ts` | Dev-only console wrapper |

### Key Behavioral Changes
| Change | Before | After |
|--------|--------|-------|
| **Primary industries** | professional-services, home-services, dental | professional-services, dental, **ecommerce** |
| **Hourly rate** | Hardcoded EUR 50 for all | EUR 125 (legal), EUR 85 (dental), EUR 35 (ecommerce), etc. |
| **NET SCORE** | Not implemented | `Benefit - Cost - (Risk/10)` auto-calculated, overrides LLM when gap >5 |
| **Negative ROI** | Silently capped to 0% | Flows through with `is_not_recommended` flag + red styling |
| **Currency** | Hardcoded EUR everywhere | From `SkillContext.currency` / `currency_symbol` |
| **Vendor prompts** | "Use REAL vendors" (no data) | Full KB catalog injected with anti-hallucination rules |
| **Admin routes** | `require_workspace` (any user) | `require_admin` on all 56 admin endpoints |
| **Quiz resume** | No rate limiting | 5 per email per 15 minutes |
| **Exception handling** | 32 bare `except: pass` blocks | Specific types + structured logging |
| **Model routing** | Hardcoded in 5 skills | Centralized `get_model_for_task()` |
| **Console.log** | 31 files with raw console calls | Dev-only `logger` utility |

---

## What Still Needs Doing

### Priority 1: Vendor Data Verification (Manual Research)
All vendor pricing in the knowledge base is marked `verified: false`. This directly affects report accuracy.

**Files to verify:**
- `backend/src/knowledge/ecommerce/vendors.json` - 17 vendors, ALL unverified (new)
- `backend/src/knowledge/professional-services/vendors.json` - ALL unverified
- `backend/src/knowledge/dental/vendors.json` - check verified_date freshness

**Process:** For each vendor, check their website pricing page and update:
- `pricing.starting_price` / tier prices
- `verified: true`
- `verified_date: "2026-02"`

Can be done via admin UI at `/admin/vendors` or with CLI: `python -m backend.src.agents.research.cli refresh --slug <vendor-slug>`

### Priority 2: E2E Smoke Test All 3 Verticals
The e-commerce vertical is brand new. Run through the full quiz flow for each:

1. **Professional Services** - existing, should work. Verify hourly rate shows EUR 125/hr in report assumptions.
2. **Dental** - existing, should work. Verify hourly rate shows EUR 85/hr.
3. **E-Commerce** - NEW. Verify:
   - Quiz loads e-commerce-specific questions
   - AI readiness score generates properly
   - Teaser/preview uses e-commerce benchmarks
   - Report findings reference e-commerce vendors from KB (not hallucinated)
   - NET SCORE appears on three-options comparison

**How to test:**
```bash
# Start services
cd backend && source venv/bin/activate && uvicorn src.main:app --reload --port 8383
cd frontend && npm run dev
# Navigate to http://localhost:5174/quiz
```

### Priority 3: Multi-Currency Quiz Question
The currency system is fully built (`SkillContext.currency`, `CURRENCY_SYMBOLS`, all skills use it) but there's no quiz question asking the user's country/currency. Without this, everyone defaults to EUR.

**What to add:**
- Quiz question: "What country is your business based in?" or "What currency do you operate in?"
- Map answer to currency code (UK -> GBP, US -> USD, Australia -> AUD, EU -> EUR)
- Pass through to SkillContext when generating report

**Files involved:**
- `backend/src/knowledge/industry_questions/*.json` - add currency question to each
- `backend/src/services/report_service.py` - extract currency from quiz answers into context
- `backend/src/skills/base.py` - SkillContext already has `currency: str = "EUR"`

### Priority 4: Sample Report for Landing Pages
Links now go to `/quiz` instead of broken `/report/sample`. A real sample report would convert better.

**Options:**
- Generate a report for a fictional business and save to DB with a known ID
- Create a static sample report page that doesn't need DB
- Add a "preview mode" to ReportViewer that loads sample data

### Priority 5: Fix Pre-Existing Test Failures (In Progress)
8 tests in `test_exec_summary.py` and `test_registry.py` have been failing since before the audit. An agent is currently fixing these. If not committed by next session, the issues are:
- Registry fuzzy matching returns wrong skill for "exec-summary"
- Test uses dict subscript on Pydantic model (`result["field"]` vs `result.field`)

---

## Architecture Notes for Next Session

### NET SCORE System
```
Finding → Three/Four Options → NET SCORE Calculator → Report
                                    ↓
                              Overrides LLM recommendation
                              if score gap > 5 points
```
The skill is at `backend/src/skills/analysis/net_score_calculator.py`. It's a `SyncSkill` (no LLM needed). Input: option financial data. Output: scores, verdict, ranking.

### Industry Hourly Rate Resolution
```
Priority chain:
1. quiz_answers["hourly_rate"] (explicit)
2. quiz_answers["salary"] / 2080
3. INDUSTRY_HOURLY_RATES_EUR[industry]
4. DEFAULT_HOURLY_RATE_EUR = 50 (fallback)
```
Function: `get_effective_hourly_rate(industry, quiz_answers)` in `crb_calculation_service.py`

### Vendor Data in Prompts
```
Finding → detect relevant categories → load KB vendors → format for prompt
                                                              ↓
                                                    "VENDOR CATALOG" section
                                                    with anti-hallucination rules
```
Utility: `backend/src/skills/report_generation_utils.py`

### Admin Auth
All admin routes now use `require_admin` from `src/middleware/auth.py`. This checks `user.role == "admin"` from the Supabase user record.

### Email Rate Limiter
`EmailRateLimiter` in `src/middleware/security.py`. Redis-primary with in-memory fallback. Dual-key (email + IP). Applied to quiz `/sessions/resume` endpoint.

---

## Commands for Next Session

```bash
# Run tests
cd backend && python -m pytest tests/ -q

# Check vendor verification status
cd backend && python -c "
from src.knowledge import load_industry_data
import json
for industry in ['professional-services', 'dental', 'ecommerce']:
    data = load_industry_data(industry, 'vendors')
    if data:
        cats = data.get('vendor_categories', [])
        total = sum(len(c.get('vendors', [])) for c in cats)
        unverified = sum(1 for c in cats for v in c.get('vendors', []) if not v.get('verified'))
        print(f'{industry}: {unverified}/{total} unverified')
"

# Check primary industries
cd backend && python -c "from src.knowledge import list_primary_industries; print(list_primary_industries())"

# Start backend + frontend
cd backend && source venv/bin/activate && uvicorn src.main:app --reload --port 8383
cd frontend && npm run dev
```

---

## What NOT to Touch
- Three Options structure (correctly implemented)
- Connect vs Replace logic (correctly implemented)
- Confidence factors in roi_calculator.py (single source of truth now)
- AI readiness formula (correctly formula-based)
- Verdict thresholds and logic (correctly implemented)
- Workshop/interview skills (working, not modified)
- Automation summary aggregation (correct)
