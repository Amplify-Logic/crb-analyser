# System Evolution Log

> Track improvements to the AI coding system (rules, commands, reference docs).
> After fixing any bug, use `/evolve` to analyze and update this log.

---

## 2026-02-27 - Report Math & Quality Pipeline Hardening

**Symptom:** Generated reports had 6 critical bugs: all ROI costs were identical €500/€50, ROI exceeded 500% cap (588%), exec summary totals contradicted value summary by 3.1x, payback periods of 0.2 months (6 days), four_options scoring contradicted AIOS recommendation, and irrelevant vendors appeared (Lawmatics for accounting).

**Root cause:** The AIOS pivot introduced new option types (`connect_and_automate`, `enhance_with_ai`, `targeted_upgrade`) but the calculation pipeline (`roi_calculator.py`, `report_service.py`, `report_generation_utils.py`) was never updated to handle them. AIOS options store costs as strings ("EUR 60-100") while legacy options use numbers. The `else` fallback branch silently served hardcoded defaults.

**Bug class:** Logic (calculation pipeline didn't handle new types) + Integration (subsystems produced contradictory outputs)

**System fix:**
- `.claude/reference/report-quality.md`: Added "Calculation Pipeline Rules" section with:
  - Option Type Checklist — mandatory checks when adding/modifying option types
  - Cost Format Rules — string vs numeric parsing rules
  - Consistency Rules — reconciliation, cap ordering, vendor filtering
  - Updated Key Files table with ROI calculator and vendor utils

**Prevents:** Any future option type addition breaking the calculation pipeline. The checklist ensures all downstream consumers (ROI calculation, cap logic, reconciliation, scoring alignment, vendor filtering) are updated together.

---

## 2026-02-15 - Production Cleanup & Documentation Alignment

**Change:** Major documentation cleanup to align all docs with 3-vertical launch.

**What was done:**
- Archived 16 stale/contradictory documents to `docs/archive/`
- Updated TARGET_INDUSTRIES.md: Home Services → Phase 2, E-commerce → Primary
- Updated PRD.md: removed 3-tier pricing, aligned to single €147 tier
- Updated README.md: corrected target markets
- Fixed hardcoded localhost in payments.py (use settings.FRONTEND_URL)
- Fixed model version inconsistency in llm_client.py
- Replaced print() with structlog logging in production code
- Audited route authentication across all endpoints

**Prevents:** AI agents and developers making wrong assumptions about target markets, pricing, or deprecated features.

---

## 2026-02-14 - Audit Remediation Completed

**Change:** Fixed 8 pre-existing test failures and completed product audit remediation.

**What was done:**
- Resolved 22 findings from product audit across P0-P6 priority
- Fixed report generation issues (ROI stuck at 0%)
- Wired curated insights into reports

**Prevents:** Report quality issues reaching production users.

---

## 2026-02-14 - Production Readiness Checklist Created

**Change:** Created PRODUCTION-READY.md tracking checklist for launch readiness.

**What was done:**
- Comprehensive checklist covering code, docs, security, testing, deployment
- Tracks verification status of each item

**Prevents:** Launching with unverified components.

---

## 2026-01-26 - Multi-Vertical Architecture Implemented

**Change:** Implemented multi-vertical support with validation for 3 industries.

**What was done:**
- Architecture supports Professional Services, Dental, E-commerce
- Industry-specific knowledge bases, benchmarks, and vendor tiers
- Validation layer ensures industry-specific data quality

**Prevents:** Single-industry lock-in, enables scalable industry expansion.

---

## 2026-01-24 - Multi-Region Vendor System Planned

**Change:** Designed vendor system to support multi-region pricing and availability.

**What was done:**
- Vendor database supports regional pricing variants
- Industry-vendor tier mapping (T1/T2/T3 per industry)

**Prevents:** Vendor recommendations being US-centric or inaccurate for EU markets.

---

## 2026-01-22 - Formula Audit Completed

**Change:** Audited all ROI and financial calculation formulas.

**What was done:**
- Validated NET SCORE formula: Benefit - Cost - (Risk / 10)
- Verified 6 cost types and 4 benefit types scoring
- Added math_validator skill for ongoing validation

**Prevents:** Incorrect financial projections in customer reports.

---

## 2026-01-17 - Three-Industry Launch Architecture Decided

**Change:** Locked decision to launch with 3 verticals instead of single-industry.

**What was done:**
- Selected Professional Services, Dental, E-commerce
- Home Services moved to Phase 2
- Updated decision lock date from Dec 2024 to Jan 2026

**Prevents:** Scope confusion about which industries are in-scope for launch.

---

## 2026-01-14 - Curated Insights System Added

**Change:** Built system for extracting and managing AI/industry insights.

**What was done:**
- Insight types: trends, frameworks, case studies, statistics, quotes, predictions
- Admin UI for extraction, review, and management
- API endpoints for CRUD operations
- Insights surfaced in reports, quiz results, landing page

**Prevents:** Reports lacking current industry data and social proof.

---

## 2026-01-08 - Initial System Setup

**Change:** Implemented modular rules architecture based on agentic engineering best practices.

**What was added:**
- `.claude/reference/` folder with task-specific rule files:
  - `api-development.md` - Backend API patterns
  - `frontend-development.md` - React/frontend patterns
  - `report-quality.md` - Report generation quality standards
  - `vendor-management.md` - Vendor database patterns
  - `testing.md` - Testing patterns and anti-patterns
- `.claude/commands/` folder with project slash commands:
  - `/prime` - Load context at conversation start
  - `/plan-feature` - Create structured implementation plan
  - `/execute` - Execute plan with minimal context
  - `/create-prd` - Generate PRD from conversation
  - `/evolve` - Improve system after fixing bugs
- Updated CLAUDE.md with reference section and context reset workflow
- This evolution log

**Why:**
- Keep global rules lightweight (~200 lines of universal rules)
- Load task-specific context only when needed
- Standardize workflows with reusable commands
- Document context reset pattern (plan → reset → execute)
- Build habit of system improvement after every bug fix

---

## Template for Future Entries

```markdown
## [Date] - [Brief Issue Description]

**Symptom:** What went wrong

**Root cause:** Why it happened

**System fix:**
- [File changed]: [What was added/modified]

**Prevents:** [What class of bugs this prevents in future]
```
