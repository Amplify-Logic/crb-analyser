# E-Commerce Report Generator — Handoff Document

**Date:** 2026-02-21
**Status:** Phase 1 Complete — CLI tool built, first report generated successfully
**Previous plan:** `docs/plans/2026-02-20-ecommerce-report-generator.md`

---

## What Was Built

A CLI tool that generates full CRB reports for real e-commerce businesses through the complete Supabase pipeline.

### Files Created

| File | Purpose |
|------|---------|
| `backend/src/expertise/data/industries/ecommerce.json` | Curated e-commerce expertise baseline (6 pain points, 6 processes, 5 patterns, 6 anti-patterns) |
| `backend/src/cli/__init__.py` | CLI module init |
| `backend/src/cli/seeds/ecommerce.json` | 29 real e-commerce businesses across 3 tiers (10 small, 9 mid, 10 scaling) |
| `backend/src/cli/fabricator.py` | Converts seed profiles into quiz_session data |
| `backend/src/cli/scraper.py` | Lightweight website scraper for tech detection |
| `backend/src/cli/generate_report.py` | Main CLI entry point (single + batch modes) |
| `backend/src/cli/__main__.py` | Module invocation support |
| `backend/tests/cli/test_fabricator.py` | 5 unit tests for fabricator |
| `backend/tests/cli/test_scraper.py` | 3 unit tests for scraper |

### Files Modified

| File | Change |
|------|--------|
| `backend/src/config/model_routing.py` | Upgraded to Sonnet 4.6 (generation) + Opus 4.6 (review/checks) |
| `backend/src/services/report_service.py` | Fixed SkillError fallback in `_generate_findings`, updated model docstrings |
| `backend/src/services/quiz_engine.py` | Updated hardcoded model to `claude-sonnet-4-6` |
| `backend/src/config/llm_client.py` | Updated example model to `claude-opus-4-6` |
| `Makefile` | Added `generate-report` target |

### Commits (9 total on main)

```
0df4bec feat: add curated e-commerce expertise baseline
e46ad2c feat: add e-commerce seed list with 29 real businesses
0ee9ccb feat: add quiz answer fabricator with tests
8de81f5 feat: add lightweight e-commerce site scraper with tests
22e0edb feat: add CLI report generator with single and batch modes
8f74226 feat: add generate-report target to Makefile
9933987 fix: catch SkillError in finding generation fallback
df048ae feat: upgrade model routing to Sonnet 4.6 + Opus 4.6
0af9cd0 chore: update ecommerce expertise after first report generation
```

---

## How to Use

```bash
# Single report from seed (random pick)
cd backend && python -m src.cli.generate_report --tier small

# Filter by tier
python -m src.cli.generate_report --tier mid --report-tier quick
python -m src.cli.generate_report --tier scaling --report-tier full

# Custom URL
python -m src.cli.generate_report --url https://example-store.com --country NL --staff 11-50

# Batch mode
python -m src.cli.generate_report --batch --count 5 --tier mid

# Via Makefile
make generate-report ARGS="--tier small"
make generate-report ARGS="--batch --count 3"
```

### Viewing Reports

- **Report viewer:** `http://localhost:5174/report/<report-id>`
- **Admin dashboard:** `http://localhost:5174/admin`
- **First generated report:** `http://localhost:5174/report/579e62bd-139d-4e58-b3df-442425c427e9`

---

## First Report Results

**Company:** Dandelion Jewelry (US, small tier, 1-10 staff)
**Report ID:** `579e62bd-139d-4e58-b3df-442425c427e9`
**Session ID:** `9e76e7d5-d193-4364-8f4e-399c673f5991`

| Metric | Value |
|--------|-------|
| Findings | 10 |
| Recommendations | 5 (with CRB three-options) |
| Quick wins | 3 |
| Playbooks | 3 |
| AI readiness | 44/100 (35th percentile) |
| Total value potential | $411K - $710K |
| Token usage | 24,466 tokens (~$0.16) |
| Generation time | ~156 min |

---

## Model Routing (Updated)

| Tier | Generation Tasks | Review/Synthesis |  Extraction |
|------|-----------------|------------------|-------------|
| Quick | Sonnet 4.6 | Opus 4.6 | Haiku 4.5 |
| Full | Opus 4.6 | Opus 4.6 | Haiku 4.5 |

---

## Known Issues & Observations

### 1. Finding generation skill returns empty JSON (non-blocking)
- The `finding-generation` skill's `call_llm_json` gets empty responses from Sonnet 4.6
- **Workaround in place:** Falls back to legacy `_generate_findings_legacy()` which works
- **Fix needed:** Investigate why the skill-based finding generation gets empty responses — likely a prompt or max_tokens issue

### 2. Review service logging bug (non-blocking)
- `review_service.py` has `Logger._log() got an unexpected keyword argument 'error'`
- Uses stdlib logging instead of structlog — structlog uses kwargs, stdlib doesn't
- Review/validation proceeds but produces 0/10 quality scores

### 3. Generation time is long (~156 min for quick tier)
- Most time spent in three-options generation (sequential, 1 LLM call per finding)
- Batch mode will be very slow without parallelization
- Consider: parallel three-options generation, or reducing finding count for quick tier

### 4. Playbook phase duration warnings
- Playbook model validates total_weeks vs sum of phase durations
- LLM output doesn't always match — produces warnings but doesn't break

### 5. Some DB columns missing
- `math_validation` and `follow_up_schedule` columns referenced but don't exist in schema
- Non-blocking — the report still saves successfully

---

## Suggested Next Phases

### Phase 2: Quality Improvements
- Fix finding-generation skill empty response issue
- Fix review_service structlog compatibility
- Tune prompts for e-commerce domain (user data quoting, confidence distribution)
- Add e-commerce-specific vendor matching

### Phase 3: Performance
- Parallelize three-options generation (biggest time saver)
- Add `--no-review` flag to skip validation step for faster iteration
- Consider reducing quick-tier findings from 10 to 6-7

### Phase 4: Batch Operations
- Generate 10-30 reports across all tiers
- Analyze report quality patterns
- Feed results back into expertise baseline
- Build a report quality scoring dashboard

### Phase 5: Report Quality Review
- Human review of 5-10 generated reports
- Compare against existing marketing-agency reports
- Refine expertise baseline based on review findings
- Adjust CRB scoring parameters for e-commerce

---

## Context for Next Session

```
/execute docs/plans/[next-phase-plan].md
```

Key context to carry forward:
- CLI is at `backend/src/cli/generate_report.py`
- Seeds at `backend/src/cli/seeds/ecommerce.json` (29 businesses)
- Model routing at `backend/src/config/model_routing.py` (Sonnet 4.6 + Opus 4.6)
- Expertise baseline at `backend/src/expertise/data/industries/ecommerce.json` (1 analysis done)
- 8 unit tests in `backend/tests/cli/`
