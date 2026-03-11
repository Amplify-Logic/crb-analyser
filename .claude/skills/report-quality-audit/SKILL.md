---
name: report-quality-audit
description: Audit report output quality and generation pipeline health for the CRB Analyser. Generates or loads a test report, runs anti-slop scans, validates structure and financials, checks connect-first ordering, and grades specificity. Also checks pipeline health (do validators block? are sample reports clean?). Use this skill whenever someone mentions report quality, slop, generic findings, auditing reports, checking report output, or shipping changes to report generation code. Even if the request seems simple ("do reports look ok?"), use this skill — it catches issues that quick checks miss.
---

# Report Quality Audit

## Purpose

This skill audits CRB reports at two levels:
1. **Output quality** — is the generated report specific, accurate, and credible?
2. **Pipeline health** — does the generation system enforce its own rules?

Both matter. A report can pass output checks while the pipeline silently lets bad reports through. Conversely, the pipeline can be sound while a specific report has issues.

## Phase 1: Load Report Data

Try to generate a fresh report first. If the backend isn't running, use existing reports.

### Generate (preferred)
```bash
cd backend && python -m src.cli generate-report --industry ecommerce --tier quick 2>&1 | tail -50
```

Or use the fabricator:
```bash
cd backend && python -m src.cli fabricator --industry ecommerce 2>&1 | tail -50
```

### Use existing reports (fallback)
Look in these locations for generated report JSON:
- `backend/reports/ecommerce/` — generated ecommerce reports
- `backend/aquablu_report_*.json` — generated Aquablu reports
- `backend/bonbon_report.json` — generated Bonbon report
- `backend/src/data/sample_report_ecommerce.json` — sample fixture

Audit at least 2 reports if available — one sample and one generated — to catch discrepancies between fixtures and real output.

## Phase 2: Anti-Slop Scan

Search the report JSON for banned phrases. Any match in customer-facing text is a FAIL.

### Core Banned List
```
streamline operations, enhance efficiency, leverage AI capabilities,
transform your business, unlock potential, optimize workflows,
drive growth, best-in-class, consider migrating, we recommend [Tool]
```

### Extended Banned List (from generation prompts)
```
well-positioned, well-suited, strong foundations, industry-leading,
best practice, accelerate, optimize, streamline, transform
```

Read the report JSON and search for these terms. Note WHERE each match appears — benchmark citations quoting external data are less severe than finding descriptions or exec summary text.

**Verdict:** PASS (zero matches in customer-facing text), WARN (matches in metadata/citations only), FAIL (matches in descriptions, exec_summary, or recommendations).

## Phase 3: Structure Validation

### Required Top-Level Fields
- [ ] `exec_summary` (or `executive_summary`) — exists, non-empty
- [ ] `findings` — array with 3+ items (0 findings = generation failure, not a valid report)
- [ ] `ai_readiness_score` — number between 0-100
- [ ] `value_summary` — has `total` with `min` and `max`
- [ ] `automation_summary` — exists if tier is "full"

### Per-Finding Checks
The actual schema groups options at the recommendation level (not per-finding). Check:
- [ ] Each finding has `title`, `description`, `category`
- [ ] Each finding has `value_saved` and/or `value_created` with financial data
- [ ] Each finding has `confidence` (values: "high", "medium", "low")
- [ ] Confidence distribution isn't all HIGH — if >60% are high, flag it

### Per-Recommendation Checks
- [ ] Has `title`, `description`, `options` (3 items)
- [ ] Has `crb_analysis` with cost/benefit/risk breakdown
- [ ] Has `roi_percentage` and `payback_months`
- [ ] Options use AIOS format: `connect_and_automate`, `enhance_with_ai`, `targeted_upgrade`
  - If options use legacy keys (`off_the_shelf`, `best_in_class`, `custom_solution`), flag as AIOS migration issue

## Phase 4: Financial Consistency

These are the checks that catch credibility-destroying errors:

- [ ] `exec_summary.total_value_potential` matches `value_summary.total` (should be equal or within 5% — a 5x-25x mismatch means reconciliation is broken)
- [ ] ROI percentages are <= 500% (the cap exists for credibility — higher values mean the cap isn't being enforced)
- [ ] Payback periods are >= 1 month (sub-month payback is not credible)
- [ ] All monetary values use consistent currency
- [ ] Spot-check 2-3 finding calculations (e.g., "X hrs/week x EUR Y x 52 = Z") — verify the math

## Phase 5: Specificity & Grounding

This is where generic AI output gets caught. For each finding, check:

- [ ] References actual quiz answers (look for "Quiz Q", "you mentioned", "based on your answer", direct quotes from user)
- [ ] ROI figures have source + calculation + confidence level
- [ ] Sources are specific and falsifiable — "ADA Health Policy Institute, 2024" is good; "industry benchmarks" is bad
- [ ] Time estimates reference similar implementations, not just round numbers
- [ ] Vendor names are real products (not placeholders)
- [ ] Pricing is present and plausible on vendor recommendations
- [ ] Recommendations are actionable within a week, not multi-month projects

Score specificity 1-10:
- 9-10: Every finding feels custom-written for this company
- 7-8: Most findings are specific, a few generic edges
- 5-6: Mix of specific and generic
- 3-4: Mostly generic with a few specific numbers
- 1-2: Could apply to any company in any industry

## Phase 6: Connect-First Verification

The CRB philosophy: wire existing tools before buying new ones.

- [ ] Option A is Connect & Automate (wires existing tools with AI workflows)
- [ ] Option B is Enhance with AI (adds AI on top of current stack)
- [ ] Replace/targeted_upgrade only appears when Connect is genuinely impossible
- [ ] If Replace appears, there's an explicit reason documented
- [ ] Recommendations reference the customer's existing stack (not just generic SaaS suggestions)
- [ ] Build time estimates mention Claude Code hours and/or MCP servers needed

## Phase 7: Pipeline Health Check

This catches systemic issues that let bad reports through. Check the generation code:

### Do validators block or just warn?
Read `backend/src/services/report_service.py` around validation logic. If validators only log warnings without triggering re-generation or blocking delivery, that's a CRITICAL finding — it means every other quality check is advisory-only.

### Are sample reports clean?
Spot-check `backend/src/data/sample_report_ecommerce.json` for banned phrases. Sample reports set the implicit quality bar — if they contain slop, generated reports will too.

### Confidence distribution in samples
Check if any sample report has LOW confidence findings. If all samples are medium/high only, the LLM never sees a LOW example and won't generate them.

### Verdict diversity
Check if sample reports show non-"proceed" verdicts. If every sample is green/GO, the system structurally biases toward GO regardless of readiness.

## Phase 8: Report Card

Present a structured summary:

```
Report Quality Audit
====================
Industry: ecommerce
Tier: [tier]
Reports Audited: [count and filenames]
Date: [today]

OUTPUT QUALITY
Anti-Slop:        PASS/WARN/FAIL  [details]
Structure:        PASS/FAIL       [missing fields or empty sections]
Financials:       PASS/FAIL       [mismatches, cap breaches]
Specificity:      X/10            [generic findings listed]
Connect-First:    PASS/FAIL       [violations]

PIPELINE HEALTH
Validators:       BLOCKING/ADVISORY  [do they actually block bad reports?]
Sample Quality:   CLEAN/DIRTY        [banned phrases in sample data?]
Confidence Dist:  BALANCED/SKEWED    [are LOW findings represented?]
Verdict Diversity: YES/NO            [do non-GO samples exist?]

Overall: PASS / NEEDS WORK / FAIL

Priority Fixes:
1. [highest impact fix]
2. [next fix]
...
```

## Phase 9: Fix and Re-Audit

If the audit reveals issues:
1. Identify which file generates the failing section
2. Fix the generation logic (not the report JSON — fix the source)
3. Re-generate a test report
4. Re-run this audit to verify the fix

## Rules

- **Read the actual report data** — never assess quality from code alone
- **Check both output AND pipeline** — a clean report doesn't mean the pipeline is healthy
- **Load `.claude/reference/report-quality.md`** for the full quality standards if needed
- **Focus on ecommerce** — this is our primary industry vertical
- **Flag credibility destroyers loudly** — value mismatches, impossible ROI, wrong vendors
