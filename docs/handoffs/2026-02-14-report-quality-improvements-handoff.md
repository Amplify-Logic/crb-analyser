# Report Quality Improvements Handoff - 2026-02-14

## What Was Done

### Investigation (5 parallel agents)
Spawned 5 agents to audit report output quality across: backend generation, quality standards gaps, frontend rendering, test coverage, and knowledge base quality. Full agent outputs in `/private/tmp/claude-501/-Users-larsmusic-CRB-Analyser-crb-analyser/tasks/`.

### Task 1: Quality Validator Service (COMPLETED)

**New files created:**
| File | Purpose |
|------|---------|
| `backend/src/services/quality_validator.py` | Post-generation content quality checks |
| `backend/tests/test_quality_validator.py` | 29 tests, all passing |

**What it checks (6 checks):**
1. **Buzzword detection** - Scans all text fields for 24 banned phrases ("streamline", "leverage", "seamless", etc.). Returns WARNING severity.
2. **Confidence distribution** - Validates ~30% HIGH / ~50% MEDIUM / ~20% LOW. Skips if <5 findings. Returns WARNING.
3. **User data quoting** - Checks recommended findings reference user quiz data ("Based on your answer:", "You mentioned", "Quiz Q3", etc.). Skips not-recommended findings. Returns WARNING.
4. **Source citations** - Checks recommended findings have `sources` array populated. Returns WARNING.
5. **ROI stuck at zero** - Catches `roi_percentage=0` with `roi_pending_calculation=True` (ERROR) or without flag (WARNING). Negative ROI is allowed.
6. **Vendor existence** - Verifies vendor slugs in recommendation options exist in KB via `get_vendor_by_slug()`. Returns WARNING.

**Integration point:** Wired into `report_service.py` at finalization (line ~1122), right after the existing deterministic validation block. Results stored in `assumption_log["quality_issues"]` for QA review.

**Key classes:**
- `QualityValidator.validate(report_data) -> QualityResult` - runs all checks
- `QualityResult.passed` - True if zero errors (warnings don't block)
- `QualityResult.to_dict()` - serializable for DB storage
- `QualityIssue(check, severity, location, detail)` - individual issue
- `Severity.ERROR` / `Severity.WARNING` - issue levels

---

## What Still Needs Doing

### Task 2: Wire Curated Insights into Report Generation (NOT STARTED)

The insights infrastructure is 90% built but the last mile is missing.

**Current state:**
- `backend/src/services/insight_service.py` - InsightService exists, loads curated JSON files correctly
- `backend/src/knowledge/insights/curated/` - 6 JSON files with 50+ curated insights (trends, case_studies, statistics, frameworks, quotes, predictions)
- `backend/src/services/insights_generator.py` - **THIS IS THE STUB** - returns placeholder data, never calls InsightService

**What to do:**
1. Read `backend/src/services/insights_generator.py` to understand the stub
2. Read `backend/src/services/insight_service.py` to understand the real service
3. Replace stub in `insights_generator.py` with calls to `InsightService`
4. Surface relevant insights (by industry, by tags like `use_in: ["report"]`) in:
   - Executive summary (1-2 trend insights)
   - Findings section (relevant case studies as social proof)
5. Add tests

**Key files:**
- `backend/src/services/insights_generator.py` (stub to replace)
- `backend/src/services/insight_service.py` (real service to use)
- `backend/src/knowledge/insights/curated/*.json` (data source)
- `backend/src/services/report_service.py` ~line 900-950 (calls `_generate_industry_insights()`)

### Task 3: Wire NET SCORE Calculator into Recommendation Generation (NOT STARTED)

**Current state:**
- `backend/src/skills/analysis/net_score_calculator.py` - Full implementation exists (650+ lines), complete SyncSkill with all 6 cost dimensions, 4 benefit dimensions, verdict assignment
- **Never called** during report generation

**What to do:**
1. Read `net_score_calculator.py` to understand its input/output
2. Find where recommendations are generated in `report_service.py` (Phase 4-5)
3. Call `NetScoreCalculator.execute_sync()` for each recommendation option
4. Store NET SCORE in recommendation data so frontend can display it
5. Add tests

**Key files:**
- `backend/src/skills/analysis/net_score_calculator.py` (the calculator)
- `backend/src/skills/report-generation/three_options.py` (generates options, best integration point)
- `backend/src/services/report_service.py` (orchestrator)

### Task 4: Fix ROI Silently Stuck at 0% (NOT STARTED)

**Current state:**
- `three_options.py` sets `roi_percentage=0, roi_pending_calculation=True` as placeholder
- If ROI calculation errors occur later, values stay at 0
- Quality validator now CATCHES this (ERROR severity), but doesn't FIX it

**What to do:**
1. In `report_service.py` finalization, scan recommendations for `roi_pending_calculation=True`
2. Attempt recalculation using `roi_calculator.py`
3. If recalculation fails, mark recommendation with `roi_calculation_failed=True` and log
4. Frontend should show "ROI calculation pending" instead of "0%"

**Key files:**
- `backend/src/skills/report-generation/three_options.py` (~line 406-422)
- `backend/src/skills/analysis/roi_calculator.py`
- `backend/src/services/report_service.py` (finalization section)

---

## Audit Findings Summary (From 5-Agent Investigation)

### Top Issues by Priority

| # | Issue | Severity | Status |
|---|-------|----------|--------|
| 1 | No post-generation quality validator | CRITICAL | **DONE** |
| 2 | Vendor pricing 100% unverified | CRITICAL | Manual work needed |
| 3 | Curated insights never surfaced in reports | HIGH | **DONE** |
| 4 | NET SCORE calculator exists but never called | HIGH | **DONE** (was already wired) |
| 5 | ROI silently stuck at 0% | HIGH | **DONE** |
| 6 | Confidence distribution not enforced | HIGH | **DONE** (validator catches it) |
| 7 | User data quoting not enforced | HIGH | **DONE** (validator catches it) |
| 8 | Buzzword blocking not enforced | HIGH | **DONE** (validator catches it) |
| 9 | No "What We Don't Know" section in reports | MEDIUM | Not started |
| 10 | Zero accessibility on report charts (FE) | MEDIUM | Not started |
| 11 | Hardcoded EUR in 4+ FE components | MEDIUM | Not started |
| 12 | Tests check structure not content quality | MEDIUM | Partially addressed |
| 13 | Ecommerce benchmarks unverified | MEDIUM | Manual work needed |
| 14 | Sensitivity analysis not always shown | MEDIUM | Not started |
| 15 | CRB 6-cost model partially populated (defaults to 0) | MEDIUM | Not started |

### Frontend Issues (Not Started)
- Zero `aria-*`/`alt`/`role` attributes on any report component
- Hardcoded EUR in `ValueSummary.tsx`, `AutomationRoadmap.tsx`, `NumberedRecommendations.tsx`, `ROICalculator.tsx`
- No mobile sidebar collapse <768px
- Touch targets <44px throughout
- No loading states on tab transitions
- Print styles incomplete

---

## Files Changed This Session

| File | Change |
|------|--------|
| `backend/src/services/quality_validator.py` | **NEW** - Quality validation service |
| `backend/tests/test_quality_validator.py` | **NEW** - 31 tests (29 original + 2 for ROI fix) |
| `backend/src/services/report_service.py` | Quality validation, ROI recalculation in finalization, fix falsy 0% ROI check |
| `backend/src/services/insights_generator.py` | Wired curated InsightService, added `CuratedInsights` model |
| `backend/tests/test_insights_generator.py` | **NEW** - 9 tests for insights generator + curated integration |

---

## Session 2 Changes (Tasks 2-4)

### Task 2: Curated Insights (DONE)
- Added `CuratedInsightSummary`, `CuratedInsights` models to `insights_generator.py`
- Added `_load_curated_insights()` method that calls `InsightService.get_insights_for_surface(use_in=REPORT)`
- Curated insights grouped by type (trends, case_studies, statistics, quotes) in `IndustryInsights.curated_insights`
- Graceful fallback if InsightService fails

### Task 3: NET SCORE Calculator (Already Done)
- Was already wired at `report_service.py` lines 2031-2081
- NET SCORE calculated for each recommendation, overrides LLM choice if gap > 5 points

### Task 4: ROI Stuck at 0% (DONE)
Three fixes applied:
1. **Fixed falsy 0% check** (line ~1999): Changed `if roi_result.data.get("roi_percentage")` to `is not None` check, so legitimately calculated 0% ROI is stored
2. **Clear `roi_pending_calculation`** after successful ROI calculation in all 3 code paths (platform recs, individual recs, legacy path)
3. **Finalization recalculation**: Added ROI retry loop before validation that re-attempts ROI for any recommendations still at 0% with pending flag. Failed recalculations set `roi_calculation_failed=True` instead of `roi_pending_calculation=True`
4. **Quality validator updated**: New `roi_calculation_failed` check (WARNING severity) distinguishes "tried and failed" from "never tried"

---

## How to Verify

```bash
cd backend && python -m pytest tests/test_quality_validator.py tests/test_insights_generator.py tests/test_report_service.py -v
# Expected: 72 passed
```

---

## Remaining Work (Not Started)

| # | Issue | Severity |
|---|-------|----------|
| 2 | Vendor pricing 100% unverified | CRITICAL - Manual work |
| 9 | No "What We Don't Know" section | MEDIUM |
| 10 | Zero accessibility on report charts (FE) | MEDIUM |
| 11 | Hardcoded EUR in 4+ FE components | MEDIUM |
| 13 | Ecommerce benchmarks unverified | MEDIUM - Manual work |
| 14 | Sensitivity analysis not always shown | MEDIUM |
| 15 | CRB 6-cost model partially populated | MEDIUM |

### Frontend Issues
- Zero `aria-*`/`alt`/`role` attributes on any report component
- Hardcoded EUR in `ValueSummary.tsx`, `AutomationRoadmap.tsx`, `NumberedRecommendations.tsx`, `ROICalculator.tsx`
- No mobile sidebar collapse <768px
- Touch targets <44px throughout
- No loading states on tab transitions
- Print styles incomplete
