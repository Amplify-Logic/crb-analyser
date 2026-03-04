# Operator Cron Jobs — Plan Doc

> **Created:** 2026-02-28 | **Status:** Ready for implementation
> **Depends on:** Telegram bot running (polling or webhook)
> **Scheduler:** APScheduler (already in `scheduler_service.py`)

---

## Existing Jobs (for reference)

| Job | Schedule | File |
|-----|----------|------|
| Morning briefing → Telegram | Daily 7:00 UTC | scheduler_service.py |
| Follow-up emails (7d post-report) | Daily 10:00 UTC | scheduler_service.py |
| Vendor pricing refresh (50/run) | Weekly Sun 2:00 UTC | scheduler_service.py |
| Expired quiz session cleanup | Daily 4:00 UTC | scheduler_service.py |
| Old PDF storage cleanup | Daily 3:00 UTC | scheduler_service.py |

---

## New Jobs

### 1. Weekly Pipeline Report

**Schedule:** Monday 7:30 UTC (right after morning briefing)

**What it does:**
- Query `quiz_sessions` for the past 7 days: total starts, completions, payments
- Query `reports` for the past 7 days: generated, completed, failed
- Query `payments` (Stripe): revenue total, avg deal size, quick vs full tier split
- Calculate week-over-week delta for each metric
- Break down leads by industry
- Push formatted digest to Telegram

**Output example:**
```
Weekly Pipeline — Feb 21-28

Leads: 14 (+3 vs last week)
  ecommerce: 6, dental: 4, professional-services: 4
Conversions: 4 (28.6% rate)
Revenue: EUR 1,180
  Quick tier: 3 × EUR 95 = EUR 285
  Full tier: 1 × EUR 895 = EUR 895
Reports: 4 generated, 4 completed, 0 failed

Top industry: ecommerce (43% of leads)
```

**Implementation:**
- New function `generate_pipeline_report()` in `scheduler_service.py`
- Queries: `quiz_sessions` (created_at >= 7d ago), `reports` (same), Stripe via existing payment data
- W/W delta: store last week's numbers in Redis with key `pipeline:week:{iso_week}` or just query previous 7-day window
- Push via `notify_admin()` from `telegram/notifications.py`

**Files to modify:**
- `backend/src/services/scheduler_service.py` — add job
- `backend/src/telegram/notifications.py` — add `notify_pipeline_report()` (optional, can use `notify_admin`)

---

### 2. Abandoned Quiz Re-engagement

**Schedule:** Daily 11:00 UTC

**What it does:**
- Query `quiz_sessions` where status = `pending_payment` and created_at between 24-48h ago (first nudge)
- Query `quiz_sessions` where status = `pending_payment` and created_at between 72-96h ago (second nudge)
- For each, send a re-engagement email via Brevo with different templates per nudge
- Mark session with `nudge_sent_at` or `nudge_count` to avoid double-sends
- Push summary to Telegram: "Sent 3 first nudges, 1 second nudge"

**Output example:**
```
Quiz Re-engagement — Feb 28

First nudge (24h): 3 sent
  - acme@corp.com (ecommerce)
  - dental@clinic.nl (dental)
  - agency@mkt.com (professional-services)
Second nudge (72h): 1 sent
  - old-lead@shop.com (ecommerce)
Recovered this week: 1 conversion from nudge
```

**Implementation:**
- New function `send_quiz_reengagement()` in `scheduler_service.py`
- Query `quiz_sessions` with status filter + created_at window + no prior nudge
- Use existing `brevo_service.py` for email sending (new template needed)
- Track nudge state: add `nudge_count` and `last_nudge_at` columns to `quiz_sessions` (migration needed)
- Skip if email already has a completed session (they came back on their own)

**Files to modify:**
- `backend/src/services/scheduler_service.py` — add job
- `backend/src/services/brevo_service.py` — add re-engagement email template
- `backend/supabase/migrations/018_quiz_nudge_tracking.sql` — add columns

**Decision needed:** Email copy for nudge 1 vs nudge 2. Nudge 1 = "Your report is ready, complete checkout." Nudge 2 = "Last chance — your session expires in 24h."

---

### 3. Upsell Scanner

**Schedule:** Weekly Wednesday 8:00 UTC

**What it does:**
- Query `quiz_sessions` where tier = `quick` and status = `completed`
- Join with `reports` to get AI readiness score
- Filter: readiness_score >= 7 (high readiness = would benefit most from full report)
- Filter: no existing `full` tier purchase for same email
- Push candidate list to Telegram with context

**Output example:**
```
Upsell Candidates — Week 9

3 quick-tier customers with high readiness:

1. TechFlow (ecommerce) — Readiness: 8.2/10
   Quick report delivered Feb 20. 6 tools in stack.
   Email: cto@techflow.io

2. Bright Dental (dental) — Readiness: 7.5/10
   Quick report delivered Feb 18. Low automation.
   Email: info@brightdental.nl

3. Metro Agency (professional-services) — Readiness: 7.1/10
   Quick report delivered Feb 22. Manual processes.
   Email: ops@metroagency.com
```

**Implementation:**
- New function `scan_upsell_candidates()` in `scheduler_service.py`
- Join `quiz_sessions` (tier=quick, completed) + `reports` (readiness score from results JSONB)
- Exclude emails that already have a full-tier session
- Format and push via Telegram

**Files to modify:**
- `backend/src/services/scheduler_service.py` — add job

---

### 4. Knowledge Base Freshness Audit

**Schedule:** Weekly Monday 3:00 UTC

**What it does:**
- Scan all JSON files in `backend/src/knowledge/` recursively
- Check `last_updated` or file modification time
- Classify: fresh (≤7d), aging (≤30d), stale (≤90d), critical (>90d)
- Scan `backend/src/expertise/data/` for same
- Compare against thresholds from `auto_refresh.py`
- Push alert to Telegram only if stale or critical files exist
- Optionally auto-trigger refresh for critical files

**Output example:**
```
Knowledge Base Audit — Feb 28

Fresh (≤7d): 18 files
Aging (≤30d): 6 files
Stale (≤90d): 3 files ⚠️
  - knowledge/ecommerce/benchmarks.json (42 days)
  - knowledge/dental/workflows.json (65 days)
  - expertise/data/vendors.json (88 days)
Critical (>90d): 0 files

Action: Consider refreshing 3 stale files.
Run: /code refresh the stale knowledge base files
```

**Implementation:**
- Wrap existing `auto_refresh.py` audit logic into a schedulable function
- The CLI already does the scan — extract the core logic into a reusable function
- Push results via Telegram
- Optional: auto-trigger `auto_refresh all --auto-approve` for critical files

**Files to modify:**
- `backend/src/services/scheduler_service.py` — add job
- `backend/src/cli/auto_refresh.py` — extract audit logic into importable function (currently CLI-only)

---

### 5. API Cost Tracker

**Schedule:** Daily 23:00 UTC (end of day) + Weekly summary Monday 7:15 UTC

**What it does:**
- Daily: Count API calls by provider and model from logs or usage tracking
- Track: Anthropic (Haiku classifier, Sonnet generation, Opus analysis), OpenAI (Whisper), Supabase operations
- Estimate cost using published pricing
- Store daily totals in Redis: `api_costs:{date}:{provider}`
- Alert if daily cost exceeds threshold (e.g., >EUR 10)
- Weekly: aggregate and push trend to Telegram

**Output example (daily alert):**
```
⚠️ API Cost Alert — Feb 28

Daily spend: EUR 8.42 (threshold: EUR 10)
  Anthropic: EUR 7.80
    haiku (classifier): 142 calls — EUR 0.28
    sonnet (generation): 18 calls — EUR 2.70
    opus (analysis): 4 calls — EUR 4.82
  OpenAI Whisper: 6 calls — EUR 0.04
  Telegram: free (polling)

7-day trend: EUR 5.20 → 6.10 → 7.30 → 8.42 ↑
```

**Implementation:**
- Option A (simple): Parse structured logs for API calls, estimate from token counts
- Option B (accurate): Add middleware to `anthropic` client that logs usage per call to Redis
- Pricing table: hardcode current rates, update quarterly
- Daily job: aggregate and check threshold → alert if over
- Weekly job: format 7-day trend → push to Telegram

**Files to modify:**
- `backend/src/services/scheduler_service.py` — add daily + weekly jobs
- `backend/src/services/cost_tracker.py` — new file, cost aggregation logic
- `backend/src/config/model_routing.py` — add cost-per-token constants (or separate config)

**Decision needed:** Option A (log parsing, ~80% accurate) vs Option B (middleware tracking, ~99% accurate but more invasive). Recommend Option B — add a thin wrapper around the Anthropic client that logs token usage per call.

---

### 6. Error Digest

**Schedule:** Daily 22:00 UTC

**What it does:**
- Read today's log file or Redis error buffer
- Filter for ERROR and WARNING level entries
- Deduplicate by error message pattern (group identical errors)
- Count occurrences of each unique error
- Push top 5 errors to Telegram
- If zero errors: push "Clean day — no errors"

**Output example:**
```
Error Digest — Feb 28

Total: 7 errors, 12 warnings

Top errors:
1. Voice transcription failed: Attribute `text`... (3×)
2. Intent classification failed: timeout (2×)
3. Report generation timeout for session abc123 (1×)
4. Vendor refresh 404 for klaviyo.com/pricing (1×)

Top warnings:
1. Supabase query slow (>2s): vendors table (8×)
2. Redis connection retry (4×)

Trend: 7 errors (vs 3 yesterday, 5 avg this week)
```

**Implementation:**
- Option A (simple): Tail the log file, parse ERROR/WARNING lines, deduplicate
- Option B (structured): Add a `structlog` processor that pushes errors to Redis list `errors:{date}`
- Deduplication: strip variable parts (IDs, timestamps) from error messages, group by pattern
- Push via Telegram

**Files to modify:**
- `backend/src/services/scheduler_service.py` — add job
- `backend/src/services/error_digest.py` — new file, log parsing + deduplication

**Decision needed:** Option A or B. Recommend A to start (zero infrastructure change), migrate to B later.

---

### 7. DB Consistency Audit

**Schedule:** Weekly Sunday 5:00 UTC

**What it does:**
- Run existing `db_audit.py` validation checks:
  - Orphaned reports (no matching quiz_session)
  - Quiz sessions with invalid status transitions
  - Vendors with missing required fields
  - Duplicate entries
  - Schema drift detection
- Push summary to Telegram
- Auto-fix minor issues (nulls, missing defaults) if `--auto-fix` flag

**Output example:**
```
DB Audit — Feb 28

Tables checked: 6
Records scanned: 1,847

Issues found: 2
  ⚠️ 1 orphaned report (no quiz_session) — id: abc123
  ⚠️ 3 vendors missing `pricing_url` field

Auto-fixed: 0
Manual review needed: 2

Run /code investigate orphaned report abc123
```

**Implementation:**
- Extract audit logic from `backend/src/scripts/db_audit.py` into importable function
- Return structured results (not just print statements)
- Add to scheduler
- Push summary via Telegram

**Files to modify:**
- `backend/src/services/scheduler_service.py` — add job
- `backend/src/scripts/db_audit.py` — refactor to return results (currently script-only)

---

### 8. Industry Heatmap

**Schedule:** Weekly Monday 7:45 UTC (after pipeline report)

**What it does:**
- Query `quiz_sessions` for last 30 days, group by industry
- Calculate: lead count, conversion rate, avg readiness score per industry
- Compare to previous 30-day window (trend)
- Identify: hottest industry (most leads), best converting, fastest growing
- Push insights to Telegram

**Output example:**
```
Industry Heatmap — 30 Day View

          Leads  Conv%  Readiness  Trend
ecommerce   24   33%    6.8/10    ↑ +40%
dental      12   25%    7.2/10    → flat
prof-svcs    8   38%    5.9/10    ↑ +60%
b2b-plat     3   67%    8.1/10    NEW

Hottest: ecommerce (volume)
Best converting: b2b-platforms (67%)
Fastest growing: professional-services (+60%)

Action: Double down on ecommerce content. B2B platforms converting well — explore.
```

**Implementation:**
- New function `generate_industry_heatmap()` in `scheduler_service.py`
- Query `quiz_sessions` with industry extracted from `answers` JSONB
- Two windows: current 30d and previous 30d for trend
- Calculate metrics per industry
- Format and push

**Files to modify:**
- `backend/src/services/scheduler_service.py` — add job

---

### 9. Case Study Candidate Detector

**Schedule:** Weekly Friday 9:00 UTC

**What it does:**
- Query completed reports from the past 7 days
- Filter: quality_score >= 8 AND readiness_score >= 7 AND has company_name
- These are companies where our report was high quality AND they have high automation potential — perfect testimonial/case study candidates
- Push to Telegram with context for outreach

**Output example:**
```
Case Study Candidates — Week 9

1 new candidate this week:

TechFlow (ecommerce)
  Report quality: 8.4/10
  AI readiness: 8.2/10
  CRB score: 72 (strong positive)
  Key finding: 4 automatable workflows, EUR 45K annual savings
  Contact: cto@techflow.io

Action: Reach out for testimonial within 14 days of report delivery.
```

**Implementation:**
- New function `detect_case_study_candidates()` in `scheduler_service.py`
- Query `reports` joined with `quiz_sessions`
- Extract quality and readiness scores from report JSONB
- Filter by thresholds
- Push via Telegram

**Files to modify:**
- `backend/src/services/scheduler_service.py` — add job

---

### 10. Industry Trend Refresh

**Schedule:** Monthly 1st @ 2:00 UTC

**What it does:**
- Read current `knowledge/insights/curated/trends.json`
- Check age of each trend entry
- Flag trends older than 60 days
- Optionally trigger Claude Code to research and update stale trends
- Push summary: what's fresh, what needs refresh

**Output example:**
```
Trend Refresh — March 2026

Current trends: 12 entries
  Fresh (<30d): 8
  Aging (30-60d): 3
  Stale (>60d): 1
    - "AI customer service adoption rates" — last updated Dec 2025

Action: Run /code update stale industry trends in knowledge base
```

**Implementation:**
- Read and parse trend files
- Check `last_updated` fields
- Push summary
- Future: auto-trigger Claude Code research agent for stale trends

**Files to modify:**
- `backend/src/services/scheduler_service.py` — add job

---

### 11. New Vendor Detection

**Schedule:** Weekly Wednesday 3:00 UTC

**What it does:**
- Read current vendor categories from `knowledge/vendors/*.json`
- Count vendors per category
- Check for categories with low coverage (<5 vendors)
- Query `vendor_audit_log` for recently failed/removed vendors
- Push gaps report to Telegram
- Future: auto-trigger research agent to find new vendors in gap categories

**Output example:**
```
Vendor Coverage — Week 9

Categories: 24
Total vendors: 244 (3 added this week, 1 removed)

Low coverage categories:
  ai_agents: 4 vendors (target: 8+)
  voice_ai: 3 vendors (target: 5+)

Recently stale (>90d, unrefreshed):
  hubspot — last verified Nov 2025
  zendesk — last verified Dec 2025

Action: Run /code research new AI agent vendors
```

**Implementation:**
- Scan vendor JSON files and Supabase vendor table
- Cross-reference with audit log
- Push gaps and staleness report

**Files to modify:**
- `backend/src/services/scheduler_service.py` — add job

---

## Schedule Overview

```
DAILY
  03:00  Storage cleanup (existing)
  04:00  Quiz session cleanup (existing)
  07:00  Morning briefing (existing)
  10:00  Follow-up emails (existing)
  11:00  [NEW] Abandoned quiz re-engagement (#2)
  22:00  [NEW] Error digest (#6)
  23:00  [NEW] API cost tracker — daily (#5)

WEEKLY
  Mon 03:00  [NEW] KB freshness audit (#4)
  Mon 07:15  [NEW] API cost tracker — weekly summary (#5)
  Mon 07:30  [NEW] Weekly pipeline report (#1)
  Mon 07:45  [NEW] Industry heatmap (#8)
  Sun 02:00  Vendor refresh (existing)
  Sun 05:00  [NEW] DB consistency audit (#7)
  Wed 03:00  [NEW] New vendor detection (#11)
  Wed 08:00  [NEW] Upsell scanner (#3)
  Fri 09:00  [NEW] Case study candidates (#9)

MONTHLY
  1st 02:00  [NEW] Industry trend refresh (#10)
```

## Implementation Priority

| Phase | Jobs | Effort | Value |
|-------|------|--------|-------|
| **A — Revenue** | #1 Pipeline report, #2 Abandoned quiz, #3 Upsell scanner | 4-5 hrs | Direct revenue impact |
| **B — Ops** | #5 API cost tracker, #6 Error digest | 3-4 hrs | Prevents surprises |
| **C — Data quality** | #4 KB freshness, #7 DB audit | 2-3 hrs | Report quality |
| **D — Growth intel** | #8 Industry heatmap, #9 Case study candidates | 2-3 hrs | Strategic decisions |
| **E — Long-term** | #10 Trend refresh, #11 Vendor detection | 2-3 hrs | Data moat |

## New Files Needed

```
backend/src/services/cost_tracker.py        # API cost aggregation (#5)
backend/src/services/error_digest.py        # Log parsing + dedup (#6)
backend/supabase/migrations/018_quiz_nudge_tracking.sql  # Nudge columns (#2)
```

## Shared Patterns

All new jobs follow the same pattern:
1. Query data source (Supabase, files, Redis, logs)
2. Compute metrics / detect conditions
3. Format Telegram message (respect 4096 char limit)
4. Push via `notify_admin()` or dedicated `notify_*()` function
5. Log job result with structlog

All jobs should:
- Be manually triggerable (add `trigger_*()` function)
- Send Telegram notification on failure
- Log execution time and result count
- Be idempotent (safe to re-run)

## Quick Start

```bash
# Load context
/prime

# Execute phase A first (revenue jobs)
/execute docs/plans/2026-02-28-cron-jobs-operator.md
```
