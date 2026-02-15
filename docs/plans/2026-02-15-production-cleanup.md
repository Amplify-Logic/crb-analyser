# Production Cleanup & Documentation Alignment Plan

> **Created:** 2026-02-15
> **Purpose:** Clean up outdated documentation, fix code blockers, and align everything to the 3-vertical launch (Professional Services, Dental, E-commerce).
> **Tracking:** PRODUCTION-READY.md (project root)

---

## Context for Agent Team

### What happened
The project evolved rapidly through multiple phases:
- Dec 2024: Initial industry selection (included Home Services)
- Jan 2026: EXECUTION-STRATEGY.md written with Home Services-only focus
- Jan 26, 2026: Multi-vertical architecture decision locked in 3 verticals: **Professional Services, Dental, E-commerce**
- Feb 2026: Product audit found 22+ issues, many addressed but docs never updated

### The problem
Documentation is fragmented and contradictory. At least 5 documents give different answers to "what are our target markets?" This will cause AI agents and new developers to make wrong assumptions.

### The 3 verticals (SOURCE OF TRUTH)
1. **Professional Services** (accounting, legal, consulting)
2. **Dental Practices** (practices & DSOs)
3. **E-commerce** (online retail, DTC)

### Single pricing tier: **€147**

---

## Batch 1: Documentation Cleanup (No Code Changes)

### Task 1.1: Update TARGET_INDUSTRIES.md
**File:** `docs/TARGET_INDUSTRIES.md`
**Action:** Replace Home Services with E-commerce as primary. Update the decision lock date to January 2026.
**Details:**
- Primary Industries: Professional Services (89/100), Dental (85/100), E-commerce (NEW - needs scoring)
- Move Home Services to Secondary Industries (Phase 2)
- Update "Decision locked" date from December 2024 to January 2026
- Update "Unified Positioning" to include e-commerce language
- Update "Last updated" to February 2026
- Add to Dropped section: reason Home Services moved to Phase 2

### Task 1.2: Archive stale root docs
**Action:** Create `docs/archive/` directory. Move these files there:
- `CRB-ANALYSER-OVERVIEW.md` → `docs/archive/` (Dec 2024, wrong target markets + wrong pricing tiers)
- `NEXT_SESSION_PROMPT.md` → `docs/archive/` (session-specific, stale)
- `NEXT-SESSION-PROMPT.md` → `docs/archive/` (duplicate of above)
- `SESSION_SUMMARY_2024-12-20.md` → `docs/archive/` (session-specific)
- `SETUP_PROMPT.md` → `docs/archive/` (superseded by CLAUDE.md)
- `HANDOFF.md` → `docs/archive/` (superseded by docs/handoffs/)
- `HANDOFF_GTM_STRATEGY.md` → `docs/archive/` (superseded by docs/GTM_STRATEGY.md)
- `HANDOFF_REPORT_SERVICE.md` → `docs/archive/` (superseded by docs/handoffs/)
- `GTM_STRATEGY_FINAL.md` → `docs/archive/` (superseded by docs/GTM_STRATEGY.md)
- `TESTING-FINDINGS.md` → `docs/archive/` (addressed)
- `DEVOPS-TICKETS.md` → `docs/archive/` (tickets format, stale)
- `TICKETS-INTEGRATIONS.md` → `docs/archive/` (tickets format, stale)

### Task 1.3: Archive stale docs/ files
**Action:** Move to `docs/archive/`:
- `docs/EXECUTION-STRATEGY.md` → `docs/archive/` (Home Services-only focus, contradicts everything)
- `docs/HANDOFF-2024-12-24-knowledge-bases.md` → `docs/archive/` (Dec 2024, superseded)
- `docs/SYSTEM-PROMPT-PROPOSAL.md` → `docs/archive/` (proposal, not current)
- `docs/VIDEO_TRANSCRIPT_ANALYSIS_PROMPT.md` → `docs/archive/` (one-time use prompt)

### Task 1.4: Update PRD.md pricing section
**File:** `PRD.md`
**Action:** Replace the 3-tier pricing (€147/€697/€2,997) with the current single-tier model:
- Single tier: €147 - Quiz + 90-min workshop + human-reviewed report (24-48hr delivery)
- Add note: "Future tiers planned after 50+ reports delivered"
- Keep everything else in PRD.md unchanged

### Task 1.5: Update README.md target markets
**File:** `README.md`
**Action:** Ensure target markets listed as Professional Services, Dental, E-commerce (not Home Services).

### Task 1.6: Populate evolution-log.md
**File:** `docs/evolution-log.md`
**Action:** Add entries for major changes since Jan 8, 2026:
- Jan 14: Curated insights system added
- Jan 17: Three-industry launch architecture decided
- Jan 22: Formula audit completed
- Jan 24: Multi-region vendor system planned
- Jan 26: Multi-vertical architecture implemented
- Feb 14: Product audit (22 findings), report quality improvements
- Feb 14: Audit remediation completed
- Feb 15: Production readiness checklist created

---

## Batch 2: Backend Code Fixes (P0 Items)

### Task 2.1: Add FRONTEND_URL to settings
**File:** `backend/src/config/settings.py`
**Action:** Add `FRONTEND_URL: str = "http://localhost:5174"` to Settings class.

### Task 2.2: Fix hardcoded localhost in payments
**File:** `backend/src/routes/payments.py`
**Action:** Replace `base_url = "http://localhost:5174"` with `base_url = settings.FRONTEND_URL`.
**Import:** Add settings import if not present.

### Task 2.3: Fix model version inconsistency
**File:** `backend/src/config/llm_client.py`
**Action:** Change `claude-opus-4-5-20251202` to `claude-opus-4-5-20251101` to match model_routing.py.

### Task 2.4: Replace print() with logging in production code
**Files:** `backend/src/config/model_routing.py`, any other non-CLI files with print()
**Action:** Replace `print()` with `logger.info()` / `logger.debug()`. Add `import structlog; logger = structlog.get_logger()` if not present.
**Exclude:** CLI files (migrations/run.py, agents/research/cli.py) may keep print().

### Task 2.5: Audit route authentication
**Files:** All files in `backend/src/routes/`
**Action:** Verify every route has appropriate auth:
- Public routes (quiz, health, landing data): OK without auth
- User routes (workshop, playbook, interview): Must have `Depends(get_current_user)`
- Admin routes: Must have `require_admin` dependency
**Report:** List every unprotected endpoint that should be protected.

---

## Batch 3: Frontend Code Fixes (P0/P1 Items)

### Task 3.1: Remove unused dependencies
**Action:** Run:
```bash
cd frontend && pnpm remove socket.io-client @supabase/supabase-js apexcharts react-apexcharts
```
Then remove any imports of these packages from source files.

### Task 3.2: Centralize API base URL
**Action:** Remove all instances of:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8383'
```
Replace with import from apiClient.ts. If apiClient.ts doesn't export the base URL, add the export.
**Files affected:** ~18 files (search for `VITE_API_BASE_URL` in `frontend/src/`)

### Task 3.3: Remove dead routes and pages
**Files to remove:**
- `frontend/src/pages/Landing.tsx` (replaced by LandingHome.tsx)
- Remove `/interview-legacy` route from App.tsx
- Remove `/new-audit-legacy` route from App.tsx
- Remove `/preview/report` route from App.tsx (mock-only page)
**Verify:** No imports reference removed files.

### Task 3.4: Externalize hardcoded values
**File:** `frontend/src/pages/CheckoutSuccess.tsx`
**Action:** Move `support@readypath.ai` to a constants file or environment variable.

---

## Batch 4: CLAUDE.md Alignment

### Task 4.1: Update CLAUDE.md to match reality
**File:** `CLAUDE.md`
**Action:** After all other batches complete, verify:
- All file paths in "Key Files" section exist
- All routes in "Frontend Routes" section match App.tsx
- Model versions match what's in code
- Industry references match the 3 verticals
- No references to deprecated features or old pricing

---

## Execution Notes

- Execute batches sequentially (1 → 2 → 3 → 4)
- Within each batch, tasks can run in parallel
- After each batch, run `pytest` to verify nothing broke
- After Batch 4, run all verification commands from PRODUCTION-READY.md
- Update PRODUCTION-READY.md checkboxes as items are verified
