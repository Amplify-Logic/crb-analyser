# Handoff: Professional Services Report Quality Cycle

**Date**: 2026-02-27
**Branch**: `feat/adaptive-recommendations`
**Last report**: `backend/reports/professional-services/20260227_180000_van_berg_and_partners.json`

---

## What was done

Ran the professional-services report generation cycle (`python generate_and_review.py --industry professional-services --dev-mode`) and fixed 4 bugs that were blocking quality.

### Bugs Fixed (all confirmed working in run 2)

| Bug | Root Cause | Fix | Files |
|-----|-----------|-----|-------|
| **Playbook `option_type` crash** | `Playbook` model only accepted legacy types (`off_the_shelf` etc) but recs use AIOS types (`connect_and_automate` etc). Caused infinite retry loop. | Updated `Playbook.option_type` Literal to accept both AIOS + legacy types | `models/playbook.py:197`, `services/playbook_generator.py:1020` |
| **Empty vendor names (20 warnings)** | `vendor_validation_service.validate_recommendation()` looked for legacy option keys + `vendor`/`name` fields, but AIOS options use different keys + `matched_vendor` dict | Updated to check both AIOS and legacy keys, extract from `matched_vendor` | `services/vendor_validation_service.py:202-226` |
| **`_parse_weeks` ValueError** | Regex `r'[\d.]+'` matched standalone `.` as a number, `float('.')` crashed | Changed to `r'\d+\.?\d*'` (requires leading digit) | `skills/analysis/net_score_calculator.py:701`, `services/validation_service.py:374,382`, `services/playbook_generator.py:172`, `skills/analysis/math_validator.py:230,234,238` |
| **`client_experience` invalid category** | LLM generates `client_experience` but only `customer_experience` was valid | Added alias mapping | `services/report_service.py:1805-1809` |

### Quality Gates — Run 2 Results

| Gate | Status | Notes |
|------|--------|-------|
| Findings >= 5 | **PASS** | 15 |
| Recommendations >= 3 | **PASS** | 11 |
| At least 2 rec types | **PASS** | connect_and_automate (10) + enhance_with_ai (1) |
| year_one_total > 0 | **FAIL** | 0/11 — cost dict empty on all recs |
| No "No matching vendor" | **PASS** | 0 |
| Exec summary mentions company | **FAIL** | "Van Berg" not in exec summary text |
| NET scores variance | **PASS** | 10/11 have NET scores |
| Playbooks generated | **PASS** | 3 (was 0 in run 1) |
| Empty vendor warnings | **PASS** | 0 (was 20 in run 1) |
| Quality review score >= 6 | **UNKNOWN** | Not found in report output |

---

## Remaining issues to fix (next session)

### 1. `cost.year_one_total` is empty (HARD FAILURE)

All 11 recommendations have an empty `cost` dict at the top level. Costs exist *inside* each AIOS option as strings like `"EUR 50"` or `"€60-100/month"`, but they're not being aggregated into the top-level `cost.year_one_total` field.

**Where to look**:
- `report_service.py` — search for `year_one_total` to find where cost aggregation happens
- The AIOS options store costs as free-text strings (`monthly_cost: "EUR 50"`), not as structured numbers. The aggregation likely expects numeric fields.
- `validation_service.py:370-389` has parsing logic for string costs that was already fixed (regex), but the aggregation step may not be running at all.

### 2. Exec summary missing company name

The executive summary doesn't mention "Van Berg & Partners". Check the exec summary prompt in `report_service.py` or the skill that generates it — the company name should be injected into the prompt.

### 3. Low recommendation diversity (quality tuning, not a bug)

10/11 recs are `connect_and_automate`, only 1 `enhance_with_ai`, 0 `targeted_upgrade`. The NET score calculator is overriding LLM suggestions. This may be correct behavior for this company profile (eager to build, most APIs ready) but should be reviewed.

### 4. `Failed to get vendors with tier boost` (minor)

Empty error message in `vendor_service.py:445`. Silent failure when trying to boost vendor recommendations. Low priority — falls back gracefully.

### 5. CLI timeout on Sonnet findings generation

Sonnet consistently times out at 600s for findings generation (45K char prompt). Falls back to Opus successfully. Consider either:
- Increasing the CLI timeout for this specific call
- Reducing the prompt size for findings generation

---

## How to re-run

```bash
cd backend && source venv/bin/activate

# Full run (Opus, ~75 min with dev-mode)
python generate_and_review.py --industry professional-services --dev-mode

# Quick run (Sonnet, ~20 min)
python generate_and_review.py --industry professional-services --dev-mode --quick
```

## Key files for remaining fixes

| File | Why |
|------|-----|
| `services/report_service.py` | Cost aggregation (search `year_one_total`), exec summary generation |
| `services/validation_service.py` | Cost validation logic |
| `skills/report-generation/three_options.py` | How AIOS options structure costs |
| `skills/analysis/net_score_calculator.py` | NET score + cost estimation |

## Changes not yet committed

All fixes are unstaged. Run `git diff` to see them. Consider committing the 4 bug fixes before continuing.
