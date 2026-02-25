# CRB Living System — Design Document

> **Origin:** AIOS opportunity analysis (Liam Ottley webinar, Feb 2025)
> **Date:** 2026-02-25
> **Status:** Approved design, pending implementation planning

---

## Vision

Transform CRB Analyser from a one-shot €147 report into an ongoing AI operating system for clients — building recurring revenue and a data moat that compounds with every analysis.

Inspired by Ottley's AIOS architecture (Context → Data → Intelligence → Automation → Output) but applied to OUR model: we don't teach clients to build their own system, we build it for them, backed by structured CRB analysis.

---

## Revenue Ladder

```
€0        Weekly AI Brief (free)          ← Lead magnet
  ↓
€147      CRB Report                      ← One-time analysis
  ↓
€29/mo    CRB Monitor                     ← Ongoing alerts + bot
  ↓
€79/mo    CRB Advisor                     ← Personalized briefs + meeting intel
  ↓
€497      Strategy Call                   ← Human 1:1, implementation planning
  ↓
€5K-20K   AIOS Build-Out                  ← We build their living system
```

---

## Phase Model (Revenue-Gated)

```
Phase 0: ACQUIRE          (Now → first 10 paid reports)
Phase 1: RETAIN           (10 → 50 paid reports)
Phase 2: COMPOUND         (50 → 200 reports)
Phase 3: SCALE            (200+ reports)
```

Each phase funds the next. Hard gates — do NOT start next phase until entry criteria met.

---

## Phase 0: ACQUIRE (Now → 10 Paid Reports)

**Goal:** Use AIOS-inspired ideas to drive traffic and convert to paid reports.

### Feature 0.1: Weekly Industry AI Brief (Lead Magnet)

**What:** Weekly email per vertical — "What changed in AI for [industry] this week." Vendor price changes, new tools, adoption trends, one actionable insight.

**Conversion path:** Email signup → weekly brief → CTA at bottom ("Want to know which tools fit YOUR business? Take the 5-min quiz") → quiz → report → €147

**Build:**
- Automated weekly job via APScheduler pulling from KB vendor data + curated trends
- Claude generates short, opinionated brief per industry (Haiku — fast/cheap)
- Brevo sends it, segmented by vertical (dental, ecommerce, professional-services)
- Landing page with email signup per vertical
- Each brief auto-published as blog post (SEO)

**Existing infra:** KB data, vendor refresh agent, Brevo integration, APScheduler, model routing

**Files to create/modify:**
- `backend/src/services/brief_generator.py` — new service
- `backend/src/jobs/weekly_brief.py` — new scheduled job
- `frontend/src/pages/industries/*.tsx` — add email signup component
- `frontend/src/pages/Blog.tsx` — new page (simple, renders brief as article)

### Feature 0.2: AI Stack Score (Lightweight Lead Capture)

**What:** "Enter the 5 tools you use → get an instant AI readiness score." No signup for score. Email required for detailed breakdown.

**Build:**
- Single-page tool using existing `existing_stack.py` tool mappings
- Simplified scoring from `ai_readiness_calculator.py`
- Email gate for detailed results → Brevo nurture sequence → quiz
- Track which tools people enter (market intelligence)

**Files to create/modify:**
- `frontend/src/pages/StackScore.tsx` — new page
- `backend/src/routes/stack_score.py` — new route (lightweight, no auth)
- `backend/src/services/stack_score_service.py` — new service (simplified readiness calc)

### Feature 0.3: Polish Core Conversion Path

- Landing page copy sharpened per vertical
- Quiz → teaser → payment flow tested end-to-end
- Workshop scheduling (Cal.com embed)
- Report delivery + PDF download confirmed working

### Phase 0 Exit Criteria
- [ ] 10 paid reports delivered
- [ ] Email list 200+ subscribers across verticals
- [ ] One vertical clearly leading in conversion
- [ ] Workshop completion rate >80%

---

## Phase 1: RETAIN (10 → 50 Paid Reports)

**Goal:** Keep clients engaged after the report. Start recurring revenue.

**Entry gate:** 10 paid reports delivered, at least one vertical >5% conversion.

### Feature 1.1: Persistent Client Context

**What:** Client's company profile, quiz answers, workshop transcript, report findings become a persistent, updatable record that enriches over time.

**Build:**
- `client_context` table in Supabase (extends quiz_sessions + reports)
- "My Profile" page in report viewer for client updates
- Context versioning (track changes over time)
- Every interaction (refiner, check-ins, alerts) enriches context

**Files to create/modify:**
- `backend/supabase/migrations/0XX_client_context.sql` — new table
- `backend/src/services/client_context_service.py` — new service
- `backend/src/routes/client_context.py` — new routes (CRUD)
- `frontend/src/pages/ClientProfile.tsx` — new page

### Feature 1.2: Vendor Monitoring + Alerts

**What:** Monitor vendors relevant to each client's report recommendations. Alert on meaningful changes.

**Triggers:** >10% price change, new tool with >80 CRB match score, feature additions addressing client pain points.

**Build:**
- Nightly cron: vendor refresh agent against client-relevant categories
- Diff detection: compare current vendor data vs what was in client's report
- Alert service via Brevo when meaningful changes detected
- Alert history in report viewer

**Files to create/modify:**
- `backend/src/jobs/vendor_monitor.py` — new scheduled job
- `backend/src/services/alert_service.py` — new service
- `backend/src/routes/alerts.py` — new routes
- `frontend/src/components/report/AlertHistory.tsx` — new component

### Feature 1.3: Telegram/WhatsApp Refiner Bot

**What:** Client messages Telegram: "What was the ROI on option 2?" Bot answers from their report context via existing refiner service.

**Build:**
- Telegram Bot API integration (webhook + message handler)
- Route messages through `refiner_service.py` with client context
- WhatsApp Business API as second channel (same backend)
- Auth: unique code links Telegram account to CRB report

**Files to create/modify:**
- `backend/src/integrations/telegram_bot.py` — new module
- `backend/src/integrations/whatsapp_bot.py` — new module (later)
- `backend/src/routes/messaging.py` — webhook endpoints
- Extend `refiner_service.py` to accept messaging channel context

### Feature 1.4: Implementation Check-ins

**What:** Automated check-ins at playbook milestone intervals. "Have you started the CRM evaluation?" Quick reply capture feeds expertise system.

**Build:**
- Scheduled check-in jobs per client based on playbook timeline
- Response capture (email reply or Telegram)
- Update client context + expertise system
- "Need help" → trigger refiner with recommendation context

**Files to create/modify:**
- `backend/src/jobs/implementation_checkins.py` — new scheduled job
- `backend/src/services/checkin_service.py` — new service
- Extend `expertise/self_improve.py` with implementation outcome data

### Phase 1 Pricing

| Tier | Price | Includes |
|------|-------|----------|
| CRB Report | €147 one-time | Quiz + workshop + report + 30 days Monitor free |
| CRB Monitor | €29/month | Vendor alerts + messaging bot + check-ins + persistent context |

### Phase 1 Exit Criteria
- [ ] 50 reports delivered
- [ ] 20%+ report clients converting to Monitor
- [ ] Expertise system has real implementation data
- [ ] Clear winning vertical doubled down on

---

## Phase 2: COMPOUND (50 → 200 Reports)

**Goal:** Data flywheel spinning. Build features only possible with aggregated cross-client data.

**Entry gate:** 50 reports, 10+ Monitor subscribers, expertise system has implementation outcomes.

### Feature 2.1: Personalized Weekly Intelligence Brief

**What:** Phase 0 generic brief evolves into personalized report for each Monitor/Advisor subscriber, using their context + report + implementation status + cross-client patterns.

**Build:**
- Personalized brief generator combining: client context, their report, vendor alerts, aggregated anonymized patterns
- Upgrade Phase 0 brief pipeline (same infra, richer data)
- Delivered via email + Telegram

**Files to modify:**
- Extend `brief_generator.py` with personalization layer
- Extend `client_context_service.py` with aggregation queries

### Feature 2.2: Client Dashboard

**What:** Logged-in page showing: implementation status per finding, projected vs actual ROI, vendor alert history, AI readiness score trending, recommended next action.

**Build:**
- New frontend route `/dashboard` (auth-gated)
- Dashboard data service pulling from client context, report, check-ins, alerts
- Quarterly AI readiness recalculation
- Simple charts (ROI tracking, readiness trend)

**Files to create/modify:**
- `frontend/src/pages/Dashboard.tsx` — new page
- `backend/src/routes/dashboard.py` — new routes
- `backend/src/services/dashboard_service.py` — new service

### Feature 2.3: Meeting Intelligence

**What:** Monitor subscribers record team meetings about AI implementation. We transcribe, match against report findings, surface insights.

**Build:**
- Audio upload endpoint (or Telegram voice note)
- Transcription via Deepgram (existing)
- Analysis matching transcript against client's report context
- Insight delivery via email/Telegram

**Files to create/modify:**
- `backend/src/services/meeting_intelligence_service.py` — new service
- `backend/src/routes/meetings.py` — new routes
- Extend Telegram bot with voice note handling

### Feature 2.4: Content Pipeline from Aggregated Data

**What:** Auto-generate marketing content from anonymized aggregated analysis data. "State of AI in Dental Q2 2026," case studies, trend pieces.

**Build:**
- Content generation service querying aggregated expertise data
- Template-based drafts (Claude generates, human reviews)
- Auto-schedule to blog + email list

**Files to create/modify:**
- `backend/src/services/content_pipeline_service.py` — new service
- `backend/src/jobs/content_generation.py` — new scheduled job

### Phase 2 Pricing

| Tier | Price | Includes |
|------|-------|----------|
| CRB Report | €147 one-time | Quiz + workshop + report + 30 days Monitor free |
| CRB Monitor | €29/month | Vendor alerts, bot, check-ins, dashboard |
| CRB Advisor | €79/month | Monitor + personalized brief + meeting intel (4/month) |

### Phase 2 Exit Criteria
- [ ] 200 reports delivered
- [ ] €2,000+/month recurring subscription revenue
- [ ] Aggregated data producing publishable insights
- [ ] Expertise system ROI accuracy within 20% of actual

---

## Phase 3: SCALE (200+ Reports)

**Goal:** Become a full-service AI implementation partner. The report is the wedge, the build-out is the payday.

**Entry gate:** 200+ reports, recurring > one-time revenue, winning vertical(s) clear.

### Feature 3.1: Strategy Call (€497)

**What:** 60-minute 1:1 post-report. Client has the analysis, wants help planning execution.

**Build:**
- Cal.com booking page embed
- Pre-call brief auto-generated from client context + report + implementation status
- Post-call: transcribe (Deepgram), extract action items, update context
- Upsell path to build-out

**Files to create/modify:**
- `backend/src/services/strategy_call_service.py` — new service
- `frontend/src/pages/BookStrategy.tsx` — new page
- Extend `client_context_service.py` with call brief generation

### Feature 3.2: AIOS Build-Out Service (€5K-20K)

**What:** Build the client's AI operating system — custom implementation of their CRB report recommendations.

**Tiers:**
| Tier | Price | Scope |
|------|-------|-------|
| Quick Win Sprint | €5,000 | Top recommendation, 2 weeks remote |
| Full Stack Build | €10-15K | All findings, 4-6 weeks remote |
| On-Site AIOS | €15-20K | 2-day on-site + 4 weeks remote |

**Build:**
- Quote generator from report recommendations + CRB analysis
- Build-out project templates per finding type (extends playbook generator)
- Client portal for tracking build-out progress (extends dashboard)
- Post-build monitoring (extends vendor alerts + check-ins)

**Files to create/modify:**
- `backend/src/services/quote_generator.py` — new service
- `frontend/src/pages/BuildOutPortal.tsx` — new page
- Extend `playbook_generator.py` with project template generation

### Feature 3.3: Consultant/Partner Tier

**What:** Other consultants use CRB for their clients.

| Model | Price | They Get | We Get |
|-------|-------|----------|--------|
| Referral Partner | Free | 20% commission | Clients + data |
| Consultant License | €199/month | White-label reports, unlimited analyses | Revenue + data |

**Build:**
- White-label report template system
- Partner dashboard (clients, reports, commissions)
- API endpoints for programmatic report generation
- Consultant onboarding flow

**Files to create/modify:**
- `backend/src/services/partner_service.py` — new service
- `backend/src/routes/partners.py` — new routes
- `frontend/src/pages/PartnerDashboard.tsx` — new page
- Report template system with configurable branding

### Feature 3.4: Industry Benchmark Reports

**What:** Quarterly published reports from anonymized aggregated data. €49/report or included with Advisor.

**Build:**
- Benchmark report generator querying aggregated expertise data
- PDF generation (extends existing `pdf_generator.py`)
- Purchase flow (extends Stripe integration)

### Phase 3 Revenue Projection (Year 2)

| Stream | Assumption | Annual |
|--------|-----------|--------|
| CRB Reports | 400/yr × €147 | €58,800 |
| Monitor subs | 80 × €29 × 12 | €27,840 |
| Advisor subs | 40 × €79 × 12 | €37,920 |
| Strategy Calls | 60/yr × €497 | €29,820 |
| Build-Outs | 20/yr × €10K avg | €200,000 |
| Consultant Licenses | 10 × €199 × 12 | €23,880 |
| Benchmark Reports | 500 × €49 | €24,500 |
| **Total** | | **~€403,000** |

### Phase 3 Exit Criteria
- [ ] Recurring revenue > one-time revenue
- [ ] 5+ consultant partners actively generating reports
- [ ] Build-out pipeline filling from strategy calls
- [ ] Publishable industry benchmark reports

---

## Architecture Overview

```
Phase 0 Additions:
  brief_generator.py → APScheduler → Brevo (email)
  stack_score_service.py → StackScore.tsx

Phase 1 Additions:
  client_context_service.py → Supabase (client_context table)
  alert_service.py → vendor refresh agent → Brevo
  telegram_bot.py → refiner_service.py
  checkin_service.py → APScheduler → client_context + expertise

Phase 2 Additions:
  brief_generator.py (personalized) → client_context + aggregated data
  dashboard_service.py → Dashboard.tsx
  meeting_intelligence_service.py → Deepgram + refiner
  content_pipeline_service.py → aggregated expertise → blog

Phase 3 Additions:
  strategy_call_service.py → Cal.com + Deepgram
  quote_generator.py → playbook_generator + CRB analysis
  partner_service.py → white-label + API
```

---

## Tech Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Messaging | Telegram first, WhatsApp second | Telegram Bot API free + simple. WhatsApp needs approval + per-message cost. |
| Scheduling | APScheduler → Celery if needed | Don't over-engineer. APScheduler handles crons until volume demands queues. |
| Client context | Supabase (new tables) | Same infrastructure, no new dependencies. |
| Dashboard | Extend React app (new routes) | Not a new app. |
| Email delivery | Brevo (existing) | Already integrated and segmented. |
| Transcription | Deepgram (existing) | Already integrated for voice interview. |
| Calendar | Cal.com embed | Simple, no custom build. |
| Payments | Extend Stripe (existing) | Add subscription product for Monitor/Advisor. |

---

## What We're NOT Building

| Ottley Feature | Why We Skip |
|----------------|-------------|
| AI video editing | Not a content business |
| AI thumbnail generation | Not relevant to our audience |
| GTD productivity system | Clients need implementation help, not productivity tools |
| Programmatic SEO module | Maybe as build-out deliverable, not platform feature |
| Physical voice capture button | Gimmicky for our B2B audience |
| Full business data connections | That's the build-out SERVICE, not our product |

---

## Risks

| Risk | Mitigation |
|------|------------|
| Building Phase 1 before proving Phase 0 | Hard gate: no Phase 1 until 10 paid reports |
| Vendor monitoring spam | Threshold: >10% price change or >80 CRB match for new tools |
| Telegram bot quality | Beta with 5 clients first. Refiner already works. |
| Build-out doesn't scale | High-ticket, low-volume. 20/year × €10K = €200K. |
| Consultant tier cannibalizes | Consultants reach unreachable clients. Net positive. |
| Scope creep within phases | Each feature has specific files listed. Build only what's listed. |

---

## CRB Context

- **Affected journey stages:** All (new stages added post-report)
- **Industries impacted:** All verticals equally
- **Reference docs for execution:** `api-development.md`, `frontend-development.md`, `vendor-management.md`, `report-quality.md`

## Rollback Plan

Each phase is independent. If a phase fails:
- Phase 0: Remove brief/stack-score pages, revert to current state
- Phase 1: Disable subscriptions, keep report-only model
- Phase 2: Downgrade Advisor to Monitor features
- Phase 3: Don't offer build-outs, stay as analysis product

---

## Next Steps

1. **Now:** Start Phase 0 execution — build weekly brief + stack score
2. **Gate:** Wait for 10 paid reports before Phase 1
3. **Each phase:** `/execute docs/plans/2026-02-25-crb-living-system-phase-N.md`

Individual phase execution plans should be created when entering each phase.
