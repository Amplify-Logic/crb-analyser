# CRB Analyser - Confirmed Scope (Dec 2024)

> This document captures all decisions from the scoping session. Supersedes PRD.md where they conflict.
> Updated: Dec 14, 2024 - New funnel pricing model based on market research.

---

## Business Model

### Pricing Funnel (Validated Model)

```
┌─────────────────────────────────────────────────────────────┐
│  FREE: AI Readiness Score                                   │
│  - 2 min quiz (5 questions)                                 │
│  - Score 0-100                                              │
│  - 3 teaser findings ("You're leaving €43K on the table")   │
│  - Email capture required                                   │
│                          ↓                                  │
│  €47: Quick Report (Impulse buy)                            │
│  - Full findings (10-15)                                    │
│  - Top 3 vendor recommendations                             │
│  - Basic ROI estimate                                       │
│  - PDF download                                             │
│                          ↓                                  │
│  €297: Full CRB Analysis (Core product)                     │
│  - Everything above PLUS                                    │
│  - Detailed vendor comparisons with pricing                 │
│  - Implementation roadmap                                   │
│  - 30-min call with AI consultant                           │
│  - 90-day email support                                     │
│                          ↓                                  │
│  €2,000+: Done-For-You Implementation (Services)            │
│  - We help you actually implement                           │
│  - Hands-on guidance                                        │
│  - Partner referral fees from vendors                       │
└─────────────────────────────────────────────────────────────┘
```

### Why This Pricing

| Tier | Purpose | Psychology |
|------|---------|------------|
| **Free** | Volume + Lead capture | Curiosity: "What's my score?" |
| **€47** | Qualify serious buyers | Below €50 = no approval needed, impulse buy |
| **€297** | Real revenue + trust | Human call makes it legitimate |
| **€2K+** | Learn customer needs | Services reveal what to productize next |

### Key Insight
- €47 is the magic number: credit card impulse territory
- €297 with a call solves the trust problem ("Why trust AI about AI?")
- Services tier = learning what customers actually need

### Payment Flow
- Free quiz → email capture → score + teaser
- €47 one-click Stripe checkout (no friction)
- €297 includes Calendly booking for 30-min call
- Services: Manual scoping call first

### Guarantees
- €47: No refund (low risk impulse buy)
- €297: 7-day refund if call doesn't happen
- Services: Scope-based, no blanket guarantee

---

## Target Market

### Company Size
- SMBs (1-50 employees)
- Mid-Market (50-200 employees)

### Verticals (MVP - 5 industries)
1. Marketing/Creative Agencies
2. Retailers
3. E-Commerce
4. Tech Companies
5. Music Companies/Studios

---

## Intake System

### MVP Features
- **Questionnaire only** (form-based)
- **Save progress** - Users can leave and resume later
- Single user fills intake (no collaboration for MVP)

### Future Features (Post-MVP)
- Real-time AI voice interview
- Invite collaborators (multiple departments)
- Human interview option (premium)

---

## Reports & Output

### Formats Available
- **Web view** - Interactive report in browser
- **PDF download** - Professional PDF document
- **Raw data export** - JSON/CSV for further analysis

### Report Sections
- Executive Summary with AI Readiness Score (0-100)
- Findings (verified vs. AI-estimated in separate sections)
- Recommendations with ROI calculations
- Vendor comparisons
- Implementation timeline
- Assumptions clearly stated

### Data Retention
- Reports accessible for **1 year** after generation

---

## Free Tier (Lead Capture)

### What Free Users Get
- AI Readiness Score (0-100)
- 3 finding titles only (no details)
- Teaser showing what full report contains
- CTA to upgrade to Professional

### Lead Capture Flow
1. Landing page with prominent "Free AI Readiness Quiz" CTA
2. 5-question quick assessment
3. Email required for results
4. Show score + teaser
5. Upsell to full audit

---

## Data Sources

### Vendor Database
- **Pre-built database** with manually curated data
- ~30-50 vendors across categories
- Pricing verified and dated
- Categories: CRM, Automation, Analytics, AI Tools, Project Management, Customer Service

### Industry Benchmarks
- Need to research and curate
- Will build database over time
- Clear sourcing for all claims

### Uncertainty Handling
- **Separate sections** for verified findings vs. AI-estimated findings
- Confidence levels noted
- Sources cited for all claims

---

## Technical Architecture

### Stack
| Component | Technology |
|-----------|------------|
| Backend | FastAPI + Python 3.12 (port 8383) |
| Frontend | React 18 + Vite + TypeScript (port 5174) |
| Database | Supabase (PostgreSQL) - **New project** |
| Auth | Supabase Auth (Email/password + Google OAuth) |
| Cache | Redis |
| AI | Anthropic Claude API (model TBD after testing) |
| Payments | Stripe (account exists, needs products) |
| Email | SendGrid (needs configuration) |
| Deployment | Railway |

### Source Code
- Adapt proven infrastructure from MMAI codebase
- Located at `/Users/larsmusic/Music Manager AI/`

---

## User Management

### Authentication
- Email + password signup/login
- Google OAuth ("Sign in with Google")
- Supabase Auth handles JWT

### Workspaces
- **Yes, from MVP** - Users belong to workspaces
- Can invite team members (future)
- Multi-tenant data isolation via RLS

### Admin Dashboard
- **Yes, MVP requirement**
- View all audits, users, revenue
- Manual intervention for failed analyses

---

## AI Agent

### Progress Display
- **Step-by-step with live updates** (SSE streaming)
- Show what agent is currently doing
- Summarized steps (not full reasoning)

### Model Selection
- Needs testing to determine best approach
- Possibly Opus 4.5 with subagents
- Balance quality vs. cost

### Context Validation
- Agent must ensure sufficient intake data before generating
- Can request more information if needed

### Error Handling
- Auto-retry 3x on failure
- If still fails, automatic refund
- Flag for manual review

---

## Design & UX

### Visual Style
- Similar to MMAI but **less colorful**
- More personality, professional feel
- Cater to business/SMB market

### Color Scheme
- **Primary: Purple** (AI/innovation theme)
- Secondary: Professional neutrals
- Semantic colors for status (green=savings, red=costs, etc.)

### Landing Page
- Free AI Readiness Quiz as **main CTA**
- Clear value proposition
- Pricing visible
- Trust signals (testimonials when available)

---

## Analytics & Monitoring

### User Analytics
- **Full tracking** - user behavior, funnel conversion
- Tools: Likely Mixpanel, Amplitude, or similar

### System Monitoring
- Logfire for backend observability
- Langfuse for LLM tracing
- Error tracking (Sentry or similar)

---

## Roadmap

### Phase 1: MVP - Free Quiz + €47 Report (Current)
**Goal:** Validate demand with minimal viable funnel

| Task | Status | Notes |
|------|--------|-------|
| Pre-research agent (scrapes company) | ✅ Done | Website, LinkedIn, news |
| Dynamic questionnaire generation | ✅ Done | Only asks what we don't know |
| Voice input for questions | ✅ Done | Deepgram integration |
| Basic report generation | 🔄 In Progress | Findings + recommendations |
| Stripe checkout (€47) | ⬚ Todo | One-click payment |
| Email delivery of report | ⬚ Todo | SendGrid |
| Landing page with free quiz | ⬚ Todo | Main CTA |
| PDF export | ⬚ Todo | Professional download |

**Success Metric:** 10 paying customers at €47

---

### Phase 2: €297 Tier with Call
**Goal:** Add human element for trust + higher revenue

| Task | Status | Notes |
|------|--------|-------|
| Calendly integration | ⬚ Todo | 30-min call booking |
| Enhanced report (vendor comparisons) | ⬚ Todo | Side-by-side pricing |
| Implementation roadmap generator | ⬚ Todo | Timeline with milestones |
| 90-day email support system | ⬚ Todo | Ticketing or simple email |
| Upsell flow from €47 → €297 | ⬚ Todo | Post-purchase offer |

**Success Metric:** 20% of €47 buyers upgrade to €297

---

### Phase 3: Services Discovery (€2,000+)
**Goal:** Learn what customers actually need through hands-on work

| Task | Status | Notes |
|------|--------|-------|
| Services landing page | ⬚ Todo | "Done-for-you implementation" |
| Scoping call process | ⬚ Todo | Manual discovery |
| Vendor partner program | ⬚ Todo | Referral fees |
| Implementation playbooks | ⬚ Todo | Document what works |

**Success Metric:** 5 services clients, patterns identified

---

### Phase 4: Scale (Future)
**Goal:** Productize learnings from services

| Opportunity | Trigger |
|-------------|---------|
| White-label for consultants | If consultants keep asking |
| Industry-specific versions | If one vertical dominates |
| Subscription model | If customers want ongoing advice |
| API access | If agencies want to integrate |

---

## Revenue Projections

### Conservative (1,000 visitors/month to quiz)
```
1,000 take free quiz
  → 600 complete (60%)
  → 300 give email (50%)
  → 30 buy €47 report (10%) = €1,410
  → 6 upgrade to €297 (20%) = €1,782
  → 1 buys services €2,000 = €2,000
                              ─────────
               Monthly Total: €5,192
                Annual Total: ~€62K
```

### Growth (5,000 visitors/month)
```
Monthly: €26,000
Annual: ~€310K
```

---

## Infrastructure Setup Needed

### Before Launch
- [ ] Domain (crb-analyser.com or similar)
- [ ] Stripe products: €47 Quick Report, €297 Full Analysis
- [ ] SendGrid for email delivery
- [ ] Calendly for €297 call booking
- [ ] Railway deployment

### Environment Variables
See `backend/.env.example` and `frontend/.env.example`

---

## What's NOT in MVP

- AI voice interview (nice to have later)
- Collaborator invites
- White-label (Phase 4 if demand)
- Multiple languages (English only)
- Re-audit comparisons
- Integrations (Notion, Slack)

---

## Competitor Landscape (Dec 2024 Research)

**Key Finding:** No one has productized AI consulting for SMBs

| What Exists | Gap |
|-------------|-----|
| Free readiness quizzes | Lead-gen only, no actionable output |
| Expensive consulting ($5K-50K) | Not accessible to SMBs |
| Vendor-specific ROI tools | Only push their own products |
| No-code AI builders (Levity, Akkio) | Help BUILD AI, don't advise WHAT to build |

**Our Position:** "AI Consultant in a Box" - self-serve, vendor-agnostic, transparent ROI

**Moat:**
1. Pre-research agent (auto-scrapes company data)
2. Vendor database with real pricing
3. Industry benchmarks
4. Transparent ROI calculations
