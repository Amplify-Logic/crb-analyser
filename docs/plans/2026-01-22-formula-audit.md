# Formula & Calculation Audit - FIX ROI GENERATION

## Problem Statement (CONFIRMED)

**Root cause identified:** Multiple inconsistent sources of ROI values:

1. **LLM-generated (line ~2059)** - Prompt asks LLM to "calculate ROI" with NO FORMULA
2. **Hardcoded (line ~1747)** - Platform recommendations get `roi_percentage: 200`
3. **ROI Calculator Skill (line ~1840)** - Proper formula, but only called sometimes
4. **Capping (lines ~1864-1877)** - Values capped between 0% and 500%

The sample report was hand-crafted (git commit f1a1338) with made-up numbers.

## Root Cause

In `report_service.py` around line 2059, the prompt tells the LLM:
```
"roi_percentage": <calculated ROI>,
"payback_months": <months until investment recovered>,
```

**No formula is given!** The LLM makes up numbers that "sound reasonable."

## Canonical Formulas (Use These Everywhere)

```python
# From roi_calculator.py lines 398-430

# Time Savings
annual_savings = hours_per_week × hourly_rate × 52

# Financials
monthly_savings = hours_per_month × hourly_rate
yearly_savings = hours_per_year × hourly_rate
yearly_cost = monthly_cost × 12
net_annual = yearly_savings - yearly_cost
first_year_investment = implementation_cost + yearly_cost

# ROI (first year basis)
roi_percentage = (net_annual / first_year_investment) × 100

# Payback
payback_months = implementation_cost / (net_annual / 12)

# Three Year
three_year_net = (yearly_savings × 3) - implementation_cost - (monthly_cost × 36)
```

---

## Fix Steps

### Step 1: Remove ROI from LLM Prompts

**File:** `backend/src/services/report_service.py`

Find the recommendation generation prompt (~line 2057-2065) and REMOVE:
```
"roi_percentage": <calculated ROI>,
"payback_months": <months until investment recovered>,
```

Replace with a placeholder that will be filled by the ROI Calculator Skill:
```
"roi_percentage": null,  // Calculated by ROI Calculator Skill
"payback_months": null,  // Calculated by ROI Calculator Skill
```

### Step 2: Always Call ROI Calculator Skill

**File:** `backend/src/services/report_service.py`

Find where recommendations are processed and ensure ROI Calculator Skill is called for EVERY recommendation, not just some.

Current code (~line 1840):
```python
roi_result = await roi_skill.run(roi_context)
```

Make sure this runs for ALL recommendations, including platform recommendations.

### Step 3: Remove Hardcoded ROI Values

**File:** `backend/src/services/report_service.py`

Find (~line 1747):
```python
"roi_percentage": 200,  # Conservative estimate
```

Remove hardcoded values. Let the ROI Calculator Skill handle all calculations.

### Step 4: Update Validators to Match

**Files:**
- `backend/src/services/validation_service.py`
- `.claude/hooks/validators/roi_math_validator.py`

Ensure validators use the SAME formulas as roi_calculator.py.

Current validator formula may differ - align them.

### Step 5: Regenerate Sample Report

Either:
1. Run actual report generation for a test company, or
2. Manually fix sample_report.json numbers to match formulas

### Step 6: Verify All Validators Pass

```bash
cd backend
python3 ../.claude/hooks/validators/roi_math_validator.py src/data/sample_report.json
python3 ../.claude/hooks/validators/report_validator.py src/data/sample_report.json
```

---

## Files to Modify

| File | Change |
|------|--------|
| `backend/src/services/report_service.py` | Remove ROI from prompts, ensure skill always called |
| `backend/src/services/validation_service.py` | Align formulas with roi_calculator.py |
| `.claude/hooks/validators/roi_math_validator.py` | Align formulas with roi_calculator.py |
| `backend/src/data/sample_report.json` | Fix numbers or regenerate |

---

## Success Criteria

1. [ ] No LLM prompts ask for ROI/payback values
2. [ ] ROI Calculator Skill called for every recommendation
3. [ ] No hardcoded ROI values in code
4. [ ] Validators use same formula as ROI Calculator Skill
5. [ ] Sample report passes all validators
6. [ ] Real generated reports pass all validators

---

## Execution

Run in new Claude Code session:
```
/execute docs/plans/2026-01-22-formula-audit.md
```

Or paste the Step 1-6 instructions directly.
