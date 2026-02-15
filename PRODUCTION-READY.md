# CRB Analyser - Production Readiness Checklist

> **Purpose:** Track every requirement that must be met before the first paying customer touches production.
> **Method:** Each item has a binary pass/fail. No partial credit. Evidence required.
> **Owner:** Complete items in order within each priority tier.
> **Last Updated:** 2026-02-15

---

## Status Summary

| Category | Pass | Fail | Blocked | Total |
|----------|------|------|---------|-------|
| P0 - Launch Blockers | 0 | 12 | 0 | 12 |
| P1 - Critical Quality | 0 | 10 | 0 | 10 |
| P2 - Professional Polish | 0 | 8 | 0 | 8 |
| **TOTAL** | **0** | **30** | **0** | **30** |

**Production gate:** ALL P0 items must pass. 80%+ of P1 items must pass.

---

## P0 - Launch Blockers

> If ANY P0 item fails, do NOT deploy to production.

### Security & Payments

- [ ] **P0-01: No hardcoded localhost in payment flow**
  - File: `backend/src/routes/payments.py:241`
  - Issue: `base_url = "http://localhost:5174"` used for Stripe redirect
  - Fix: Use `settings.FRONTEND_URL` environment variable
  - Evidence: grep returns 0 matches for `localhost` in payments.py
  - Status: FAIL

- [ ] **P0-02: Dev payment bypass removed**
  - File: `frontend/src/pages/Checkout.tsx:61-67`
  - Issue: `?dev=bypass` query param skips Stripe checkout entirely
  - Fix: Remove the dev bypass block or gate behind `import.meta.env.DEV` with additional server-side check
  - Evidence: grep returns 0 matches for `dev.*bypass` in Checkout.tsx
  - Status: FAIL

- [ ] **P0-03: All admin routes require authentication**
  - Files: `backend/src/routes/workshop.py`, `playbook.py`, `validation.py`, `knowledge_admin.py`
  - Issue: Several routes lack `Depends(get_current_user)` or `require_admin`
  - Fix: Audit every route file, add auth dependency where missing
  - Evidence: Every `@router` endpoint in admin routes has auth dependency
  - Status: FAIL

- [ ] **P0-04: FRONTEND_URL configurable via environment**
  - File: `backend/src/config/settings.py`
  - Issue: No `FRONTEND_URL` setting exists; payments.py hardcodes localhost
  - Fix: Add `FRONTEND_URL` to Settings class, use in all redirect logic
  - Evidence: `settings.FRONTEND_URL` used in payments.py, no hardcoded URLs remain
  - Status: FAIL

### Data Integrity

- [ ] **P0-05: NET SCORE formula implemented in code**
  - Formula: `NET SCORE = Benefit - Cost - (Risk / 10)` (per PRODUCT.md:134)
  - Issue: Formula documented but not implemented in calculation service
  - Fix: Implement in `crb_calculation_service.py`, add unit tests
  - Evidence: Test suite passes with correct formula output for known inputs
  - Status: FAIL

- [ ] **P0-06: Industry-specific hourly rates (not hardcoded)**
  - Issue: `€50/hr` hardcoded for all industries, countries, and company sizes
  - Fix: Make configurable per industry/region in knowledge base
  - Evidence: ROI calculations use industry-specific rates from config
  - Status: FAIL

- [ ] **P0-07: Multi-currency support functional**
  - Issue: EUR hardcoded across all calculations and displays
  - Fix: Currency determined by user's region/industry context
  - Evidence: Reports render with correct currency symbol per user context
  - Status: FAIL

- [ ] **P0-08: All 3 vertical knowledge bases complete**
  - Required: `professional-services/`, `dental/`, `ecommerce/`
  - Each must have: `processes.json`, `opportunities.json`, `benchmarks.json`, `vendors.json`
  - Issue: E-commerce KB may be incomplete
  - Evidence: All 12 JSON files exist, are non-empty, have verified_date within 90 days
  - Status: FAIL

### Documentation Consistency

- [ ] **P0-09: Single source of truth for target markets**
  - Required: All docs agree on 3 verticals: Professional Services, Dental, E-commerce
  - Files to update: `docs/TARGET_INDUSTRIES.md`, `docs/EXECUTION-STRATEGY.md`, `CRB-ANALYSER-OVERVIEW.md`, `README.md`
  - Evidence: grep for "home.services" returns 0 matches in non-legacy docs
  - Status: FAIL

- [ ] **P0-10: Single source of truth for pricing**
  - Required: All docs agree on single €147 tier
  - Files to update: `PRD.md` (references €697/€2,997 tiers)
  - Evidence: grep for "€697\|€2,997\|€2997" returns 0 matches outside archived docs
  - Status: FAIL

### Core Flow

- [ ] **P0-11: Quiz → Checkout → Workshop → Report flow works end-to-end**
  - Test: Complete full flow for each of the 3 verticals
  - Evidence: E2E test passes for professional-services, dental, ecommerce
  - Status: FAIL

- [ ] **P0-12: Stripe webhooks configured for production domain**
  - Issue: Webhook URL must point to production, not localhost
  - Evidence: `stripe listen` or Stripe dashboard shows production endpoint
  - Status: FAIL

---

## P1 - Critical Quality

> 80%+ must pass before production. Remaining items must have remediation plan.

### Test Coverage

- [ ] **P1-01: Payment flow test coverage >= 80%**
  - Current: 8 tests (insufficient)
  - Target: 24+ tests covering: checkout creation, webhook handling, refunds, edge cases
  - Evidence: `pytest --cov=src.routes.payments` shows >= 80%
  - Status: FAIL

- [ ] **P1-02: Auth flow test coverage >= 80%**
  - Current: 12 tests
  - Target: 30+ tests covering: login, signup, token refresh, password reset, RLS
  - Evidence: `pytest --cov=src.routes.auth` shows >= 80%
  - Status: FAIL

- [ ] **P1-03: Report generation test coverage >= 80%**
  - Current: 32 tests (likely sufficient)
  - Evidence: `pytest --cov=src.services.report_service` shows >= 80%
  - Status: FAIL

- [ ] **P1-04: Quiz session management test coverage >= 80%**
  - Current: 39 tests (likely sufficient)
  - Evidence: `pytest --cov=src.routes.quiz` shows >= 80%
  - Status: FAIL

### Frontend Quality

- [ ] **P1-05: API base URL centralized**
  - Issue: `VITE_API_BASE_URL` defined in 18 separate files
  - Fix: All API calls go through `apiClient.ts`, no direct `fetch()` with hardcoded base
  - Evidence: grep for `VITE_API_BASE_URL` returns only `apiClient.ts` and `.env` files
  - Status: FAIL

- [ ] **P1-06: Unused dependencies removed**
  - Remove: `socket.io-client`, `@supabase/supabase-js`, `apexcharts` (consolidate to recharts)
  - Evidence: `pnpm ls` shows none of these packages
  - Status: FAIL

- [ ] **P1-07: Dead routes and legacy pages removed**
  - Remove or archive: `Landing.tsx` (replaced by LandingHome), `NewAudit.tsx` (legacy V1), interview-legacy route
  - Remove mock-only route: `/preview/report` (ReportPreview.tsx with hardcoded data)
  - Evidence: Removed files no longer exist, routes removed from App.tsx
  - Status: FAIL

### Data Quality

- [ ] **P1-08: Vendor pricing verified within 90 days**
  - Issue: Most vendor data verified Dec 2025 (76+ days old)
  - Fix: Run vendor refresh, update `verified_date` fields
  - Evidence: `grep -r "verified_date" backend/src/knowledge/` shows all dates within 90 days
  - Status: FAIL

- [ ] **P1-09: All knowledge base stats have sources**
  - Rule: Every statistic needs `"source"` and `"verified_date"`
  - Evidence: No JSON entry in knowledge/ has `"status": "UNVERIFIED"` without a plan to verify
  - Status: FAIL

- [ ] **P1-10: Model versions consistent across codebase**
  - Issue: `llm_client.py` uses `claude-opus-4-5-20251202`, all other refs use `20251101`
  - Fix: Standardize to one version
  - Evidence: grep for opus model ID returns single consistent version
  - Status: FAIL

---

## P2 - Professional Polish

> Should be addressed before marketing push. Not launch blockers.

### Documentation Cleanup

- [ ] **P2-01: Stale documentation archived**
  - Move to `docs/archive/`: EXECUTION-STRATEGY.md (home services only), CRB-ANALYSER-OVERVIEW.md (Dec 2024), session summaries, old handoff docs
  - Evidence: `docs/archive/` contains moved files, no stale docs in project root
  - Status: FAIL

- [ ] **P2-02: Evolution log populated**
  - Issue: Only 1 entry despite 40+ commits and 22+ audit findings
  - Fix: Add entries for all major system changes since Jan 8
  - Evidence: `docs/evolution-log.md` has >= 10 entries
  - Status: FAIL

- [ ] **P2-03: CLAUDE.md references only current state**
  - Check: Model versions, file paths, route list, industry list all match reality
  - Evidence: Every file path in CLAUDE.md exists; every route listed matches App.tsx
  - Status: FAIL

### Code Hygiene

- [ ] **P2-04: No print() statements in production code**
  - Issue: `config/model_routing.py` and other files use print() instead of logging
  - Exceptions: CLI tools (`migrations/run.py`, `agents/research/cli.py`) may keep print()
  - Evidence: grep for `print(` in `src/` excluding CLI files returns 0
  - Status: FAIL

- [ ] **P2-05: All TODOs have tracking issues**
  - Issue: 6+ TODO comments in code without linked issues
  - Fix: Create GitHub issues for each, add issue number to comment
  - Evidence: Every `TODO` in code has format `TODO(#123): description`
  - Status: FAIL

- [ ] **P2-06: Hardcoded email addresses externalized**
  - Issue: `support@readypath.ai` hardcoded in `CheckoutSuccess.tsx`
  - Fix: Move to config/environment variable
  - Evidence: grep for `@readypath.ai` in `.tsx` files returns 0
  - Status: FAIL

### Observability

- [ ] **P2-07: Structured logging on all critical paths**
  - Paths: Auth, payments, report generation, quiz completion
  - Evidence: Each critical path logs entry, exit, and error with structured context
  - Status: FAIL

- [ ] **P2-08: Error tracking configured (Sentry or equivalent)**
  - Both frontend and backend should report unhandled errors
  - Evidence: Error tracking dashboard shows test error captured
  - Status: FAIL

---

## Verification Commands

Run these to check current status:

```bash
# P0-01: Check for hardcoded localhost in payments
grep -n "localhost" backend/src/routes/payments.py

# P0-02: Check for dev bypass
grep -n "dev.*bypass\|bypass.*dev" frontend/src/pages/Checkout.tsx

# P0-05: Check NET SCORE implementation
grep -rn "net.score\|NET_SCORE\|net_score" backend/src/ --include="*.py"

# P0-06: Check hardcoded hourly rate
grep -rn "50.*hour\|hourly_rate.*50\|50.0" backend/src/ --include="*.py"

# P0-09: Check target market consistency
grep -rn "home.service" docs/ *.md --include="*.md" | grep -v archive | grep -v evolution

# P0-10: Check pricing consistency
grep -rn "€697\|€2,997\|€2997" *.md docs/ --include="*.md" | grep -v archive

# P1-05: Check API base URL duplication
grep -rn "VITE_API_BASE_URL" frontend/src/ --include="*.ts" --include="*.tsx"

# P1-06: Check unused deps
cd frontend && pnpm ls socket.io-client @supabase/supabase-js apexcharts 2>/dev/null

# P1-10: Check model version consistency
grep -rn "claude-opus" backend/src/ --include="*.py"

# P2-04: Check print statements
grep -rn "print(" backend/src/ --include="*.py" | grep -v cli.py | grep -v run.py | grep -v __pycache__

# Full test suite
cd backend && pytest -v --tb=short 2>&1 | tail -20
```

---

## Completion Protocol

When marking an item as complete:

1. Run the verification command
2. Paste the output as evidence in a PR comment or commit message
3. Change `[ ]` to `[x]` and `FAIL` to `PASS`
4. Update the Status Summary table counts
5. Get a second pair of eyes on P0 items

**Production deploy requires:**
- All 12 P0 items: PASS
- At least 8 of 10 P1 items: PASS
- P2 items: tracked, not blocking

---

*This document is the single gate between development and production. Do not deploy without meeting the criteria above.*
