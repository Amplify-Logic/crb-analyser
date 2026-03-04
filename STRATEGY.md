# CRB Analyser - Strategy

> This document describes WHY we're building this and our strategic framework.
> For WHAT the product does, see [PRODUCT.md](./PRODUCT.md).
> For HOW to develop, see [CLAUDE.md](./CLAUDE.md).

---

## Vision & Mission

**Vision:** Become the leading AI-native consulting agency for businesses building their AI Operating System — using AI to deliver enterprise-grade analysis at SMB pricing, with a compounding data moat that grows with every engagement.

**Mission:** Deliver architecture blueprints that show businesses exactly how to build AI workflows on their existing stack, at SMB pricing, in days not months — fulfilled almost entirely by AI, reviewed by humans.

---

## AI-Native Agency Positioning

> "Don't sell access to an AI tool for $50/month. Use the AI yourself and sell the finished work for $5,000." — Y Combinator, Requests for Startups 2026

### What We Are

CRB Analyser is an **AI-fulfilled consulting agency**, not a SaaS tool. The distinction matters:

| SaaS Tool | AI-Native Agency (CRB) |
|-----------|------------------------|
| Sell access to software | Sell finished consulting deliverables |
| Customer does the work | AI does the work, human reviews |
| $50-200/mo margins | €147 per engagement, 95%+ margins |
| Compete on features | Compete on output quality + data moat |
| Growth = more users | Growth = more engagements = better data = better output |

### Why This Model Wins

Y Combinator's 2026 thesis: AI-native agencies get **software-like margins on service revenue**. Growth is decoupled from headcount.

**CRB already operates this way:**
- AI-powered adaptive quiz gathers context
- AI-assisted workshop (90 minutes, AI-driven) deepens understanding
- AI generates the full report — findings, ROI models, vendor comparisons, implementation roadmaps
- Human reviews for accuracy and adds expert context
- Delivery in 24-48 hours at €147

**Cost structure per report:**
- ~€2-5 in API calls (Claude, research agents)
- ~30 min human review time
- = 90%+ gross margins at €147, scaling to 95%+ as review automates further

**Proof points in the market:**
- Harper Insurance (YC-backed): AI handles 1,000+ customers/month vs 20-30 for human brokerages. Raised $47M.
- YC RFS explicitly names design firms, ad agencies, and law firms as targets for this model.

### The Data Moat (Our Core Defensibility)

Every report compounds our advantage:

```
Report #1:     Base accuracy, generic benchmarks
Report #50:    Industry-specific patterns validated
Report #100:   Vendor pricing database unmatched
Report #500:   Competitors can't replicate our knowledge base
Report #1000:  Predictive — we know what works before we analyze
```

**What competitors (and "just use ChatGPT") can't replicate:**
- Curated vendor pricing database with verified data
- Industry-specific benchmarks from real implementations
- The CRB framework with validated scoring
- Pattern library of what actually gets implemented vs what doesn't
- Compliance-aware recommendations with proper risk context
- Trust network and referrals within professional communities
- Live vendor pricing from autonomous scraping pipeline
- The full AI-native pipeline — most competitors are pure SaaS (no consulting depth) or pure consulting (no AI leverage)

Models are commodities. Data and methodology are moats.

---

## Computer Use & Automation Strategy

> See `.claude/reference/computer-use.md` for full details on Playwright skills, Bowser QA, Cowork integration, and Computer Use API.

---

## Core Thesis

> "Most businesses don't need new software. They need an AI layer that connects what they already have."

We solve this by:
1. **Analyzing your existing stack** — what tools you have, where the gaps are, what's connected and what isn't
2. **Architecting your AIOS** — AI workflows, agents, and automations that bridge the gaps between your tools
3. **Providing a build plan** — specific, actionable steps you can execute this week with Claude Code, MCP servers, and API integrations

---

## Strategic Focus: E-commerce Lock-In

### The Decision

> "We tested four verticals. E-commerce showed the strongest signals. Now we go deep."

After parallel testing, we locked in on e-commerce because:
- **Measurable ROI** — store owners track every automation's impact
- **Volume market** — millions of Shopify/WooCommerce stores globally
- **Automation-hungry** — most e-commerce operations are repetitive and rule-based
- **EU advantage** — deep knowledge of EU tools (Mollie, Sendcloud, Channable) and regulations (AI Act, DSA, EAA) is a genuine moat

### What Lock-In Means

| Area | Before (Parallel) | After (Lock-In) |
|------|-------------------|-----------------|
| Landing page | 4 industry pages | Single e-commerce page (/ redirects to /ecommerce) |
| Quiz defaults | Generic | E-commerce language ("your store", "your stack") |
| Knowledge base | Thin across 4 | Deep on 1 (16 pain points, 12 processes, 50+ vendors) |
| Hourly rate | €35 default | €55 ecommerce default |
| Workshop | Generic questions | E-commerce probes (returns, inventory, attribution) |
| Expertise data | Low confidence | High confidence (23 analyses) |

### Success Signals

| Metric | Target | What It Tells Us |
|--------|--------|------------------|
| Quiz completions | 100+ | Is the e-commerce message landing? |
| Quiz → Paid conversion | >5% | Is €147 right for e-commerce? |
| Workshop completion | >80% | Does the e-commerce workshop flow? |
| **"Disappointment test"** | **10+ store owners** | **Would they be massively disappointed if CRB disappeared?** |

> Other verticals (dental, professional-services, b2b-platforms) remain accessible for existing sessions and bookmarks, but receive no new investment until e-commerce PMF is proven.

---

## Go-to-Market Engine

> Source: Priestley's LAPS framework — Leads, Appointments, Presentations, Sales.

The strategy has metrics, but metrics don't generate revenue — a **weekly sales rhythm** does. This is the engine that turns parallel vertical testing into actual cashflow.

### The LAPS Cadence

```
LEADS → APPOINTMENTS → PRESENTATIONS → SALES
  ↑                                        |
  └────── Referrals + repeat ──────────────┘
```

| Step | What It Means for CRB | Weekly Target (per vertical) |
|------|----------------------|------------------------------|
| **Leads** | Quiz starts, landing page visits, content clicks | 50+ |
| **Appointments** | Quiz completions (our "appointment" is the quiz) | 25+ |
| **Presentations** | Report previews shown, workshop invites sent | 10+ |
| **Sales** | Paid reports at €147 | 2-3 |

### Weekly Rhythm

| Day | Action |
|-----|--------|
| Monday | Review last week's LAPS numbers per vertical. What converted, what didn't? |
| Tue-Thu | Execute: content, outreach, partnerships that generate leads |
| Friday | Review pipeline. How many leads became appointments? Appointments became sales? |

**The discipline:** Every week, same rhythm. Don't skip the tracking. Don't skip the review. The rhythm compounds — one good week teaches you what to repeat next week.

### Why This Matters

Most AI startups build product and wait for organic growth. The 99% who fail are the ones who skip the sales rhythm. CRB's advantage is that the **quiz IS the sales funnel** — completing it is both the appointment and the product demo. But we still need to drive leads into the top of the funnel, every single week.

---

## Product as Proof

> "CRB is the thesis it sells."

We don't just analyze whether companies should restructure around AI. We *are* the demonstration. We are the AI-native agency we recommend our clients become.

**What this means:**

| Old Model (Consulting Firm) | CRB Model (AI-Native Agency) |
|-----------------------------|------------------------------|
| Analysts researching industry | Knowledge base + AI research agents |
| Consultants conducting interviews | Adaptive quiz + AI-assisted workshop |
| Report writers drafting findings | AI-generated, human-reviewed reports |
| Account managers coordinating | Self-serve flow |
| Manual vendor research | Playwright + Computer Use autonomous scraping |
| 6-week engagement, €15k+ | 90 minutes + 24-48hr delivery, €147 |
| Revenue scales with headcount | Revenue scales with compute |

**The AI-fulfilled pipeline:**

```
Quiz (AI-adaptive) → Workshop (AI-assisted, 90 min) → Research (AI agents)
    → Analysis (AI scoring) → Report (AI-generated) → Review (Human, shrinking)
```

Every step except final review is AI-fulfilled. The human review step exists for quality assurance and trust — it will shrink as confidence in AI output grows, but may never fully disappear (and that's fine — it's a feature, not a bottleneck).

**Structural discipline:**

1. **Stay small longer than feels comfortable** - Headcount is not progress. Leverage is.
2. **Hire for outcomes, not functions** - Only when AI is exhausted for a specific result.
3. **No coordination overhead** - If you need meetings to align, you're already too big.
4. **The €147 tier proves the model** - Enterprise-level analysis at SMB pricing only works with AI leverage.
5. **Use AI to build AI** - Claude Code builds the platform. Cowork handles research tasks. Computer Use powers the scraping pipeline. We eat our own cooking at every layer.

**The uncomfortable implication:**

If CRB succeeds, it makes the same argument to its customers: you probably don't need that analyst, that researcher, that report writer. The product is a demonstration of its own thesis.

This isn't positioning. It's identity.

---

## The Four Loops

### 1. Balance Loop (BL)

Walk a tightrope between two forces:

| Your Asymmetric Advantage | Their Acute Pain |
|---------------------------|------------------|
| Professional services knowledge base | Compliance anxiety around AI adoption |
| AI/automation expertise | Time lost to admin vs billable work |
| Compounding expertise system | Confusion about which AI tools to trust |
| CRB framework with clear verdicts | Analysis paralysis on tech decisions |

**Warning Signs:**
- Leaning too far into advantage - "Cool AI but why pay?"
- Leaning too far into pain - Commoditized, no edge

**For every feature, ask:**
1. Does this leverage our asymmetric advantage?
2. Does this solve an acute, urgent, frequent pain?
3. What are we assuming? Can we test it in hours, not months?

---

### 2. Speed to Revenue Loop (STR)

> "Product-market fit is not a destination. It's a moving target. You chase it daily."

```
LAUNCH -> LEARN -> LEVEL UP -> repeat
```

**Cadence:**
| Frequency | Action |
|-----------|--------|
| Daily | Fix user-reported friction |
| Weekly | Ship report improvements |
| Monthly | Update knowledge base, review expertise data |
| Quarterly | Verify all benchmarks against sources |

**Critical Warning:**
> "When ChatGPT-6 or Gemini-4 drops, your product's value could evaporate overnight."

We don't compete with foundation models. We USE them. Our moat is:
- **Industry-specific knowledge** that compounds with each analysis
- **Expertise system** that learns from every report
- **Trust relationships** with professional services decision-makers
- **Compliance context** that generic AI tools can't replicate

**Dogfooding:** Run CRB analysis on ourselves monthly.

---

### 3. Signal to Innovation Loop (SIL)

> "Your product can be cloned. Your landing page can be copied. But if you're addicted to a strong signal loop... that is hard to copy."

```
Analysis Complete
    |
Extract Patterns (which findings resonated? what got implemented?)
    |
Update Knowledge Base (add patterns, mark anti-patterns, refine benchmarks)
    |
Better Next Analysis
    |
Higher Customer Trust
    |
More Analyses -> Compounding
```

**Three Questions:**
1. Where are my signals coming from? (surveys, implementation tracking, support)
2. How often do I look at them? (daily errors, weekly usage, monthly success rates)
3. What signal loops am I building into features?

**Anti-Quibi Mindset:**
- NEVER assume we know what customers want
- NEVER defend features when data says otherwise
- NEVER ignore when trial users disappear

---

### 4. Sweat Equity Loop (SEL)

> "The popular advice 'hire the best people and get out of their way' will be completely fatal for AI-native founders."

```
DEEPEST CONVICTION
    "Professional services firms deserve AI clarity, not expensive consultants"
        |
OBSESSIVE GRIT
    Report quality matters. ROI accuracy matters. Compliance context matters.
        |
STAYING POWER
    Stay in the game when 99% would quit
        |
COMPOUNDING NET WORTH
    Unseen work becomes visible results
```

**Wisdom Loop:** Even if we fail, we create:
- Proven professional services knowledge base
- Validated expertise system architecture
- Trust with target customers

These become foundation for the next thing.

---

## Risk Management

### Strategic Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| AI commoditization | Models get cheap, our value drops | Moat is knowledge + expertise, not AI itself |
| Competitor with more capital | Outspend on marketing/features | Stay focused, compound faster in our niche |
| Regulation changes | New compliance requirements | Feature, not bug — we help navigate change |
| Economic downturn | Firms cut discretionary spend | Position as cost-saving, not discretionary |
| AI-native agency competitors | YC-funded agencies enter our verticals | Data moat + vertical depth. They start from zero knowledge |
| Computer Use disruption | Clients use Cowork to DIY their own analysis | Our framework + data is the value, not the execution. Offer "bring your own Cowork" tier |
| Platform risk (Anthropic) | Claude API changes, pricing shifts | Multi-model support already built (Gemini fallback). Stay model-agnostic |

### Execution Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Report quality issues | Reputation damage | Human review on every report |
| Data accuracy problems | Wrong recommendations | Source verification, confidence levels |
| Scaling too fast | Quality drops, brand damage | Quality gates: 50 reports per vertical before reducing human review |
| Scope creep | Lose focus, burn resources | Strict feature prioritization |

---

## Decision Framework

**Before making any product decision:**

| Loop | Question |
|------|----------|
| BL | Does this leverage our advantage AND solve acute pain? |
| STR | Can we ship this in days, not months? What's the MVP? |
| SIL | How will we learn from users after we ship? |
| SEL | Are we sweating the details that matter? |

**Before building any feature:**

| Question | If "No" -> Don't Build |
|----------|----------------------|
| Does this leverage our asymmetric advantage? | Competitors copy easily |
| Does this solve acute, urgent, frequent pain? | Nobody pays |
| Can we validate in < 1 week? | Too risky |
| Will this generate learnable signals? | Flying blind |

**Fastest validation methods:**
1. User interview (30 min call)
2. Landing page test (does anyone click?)
3. Wizard of Oz (manual behind the scenes)
4. Beta with 5 users, collect feedback

---

## Success Metrics

### Launch Phase (First 90 Days)

| KPI | Target | Purpose |
|-----|--------|---------|
| Quiz completions (total) | 400+ | Validate traffic/messaging |
| Paid reports (total) | 30+ | Real PMF requires 30-150 paying customers, not 15 |
| Best vertical identified | Clear leader | Know where to focus |
| Workshop completion rate | 80%+ | Validate process works |
| NPS | 50+ | Quality baseline |
| "Would be disappointed" users | 10+ per vertical | The PMF signal that matters most |

### Per-Vertical Tracking

| Metric | Professional Services | Dental | E-commerce | B2B Platforms |
|--------|----------------------|--------|------------|---------------|
| Quiz starts | Track | Track | Track | Track |
| Quiz completions | Track | Track | Track | Track |
| Conversion to paid | Track | Track | Track | Track |
| Workshop completion | Track | Track | Track | Track |

### Decision Point (Day 90)

After 90 days, we answer:
- [ ] Which vertical has highest conversion rate?
- [ ] Which vertical has highest NPS?
- [ ] Which vertical has best referral potential?
- [ ] Double down on winner OR pivot if all fail

---

## Before Claiming "Done"

- [ ] Does it solve a real pain for our target verticals?
- [ ] Did we ship the smallest useful version first?
- [ ] Is there a feedback mechanism built in?
- [ ] Would we be proud to show this to a managing partner?

---

## Market Validation: The Adoption Gap (Feb 2026)

Source: Stacked Podcast analysis — AI adoption data + practitioner sentiment.

### The Numbers

- **84%** of the global population has **never used AI**
- **~16%** have used free tools (free ChatGPT, Google AI in search)
- **0.3%** pay for AI services (~$20/mo plans)
- **0.04%** use AI for advanced tasks like coding

**Implication:** CRB's customers sit in the 84-99.96%. We're not selling to AI-native people — we're selling clarity to the overwhelmed majority. €147 is their entry point into structured AI adoption.

### Validated Messaging Angles

| Insight | Messaging Angle | Where to Use |
|---------|----------------|--------------|
| **AI made everything suboptimal** | **"AI just made every business on earth inefficient overnight. The question isn't whether to optimize — it's what to optimize first."** | **Hero copy, keynotes, thought leadership** |
| **Easily quantifiable = easy sale** | **"We don't sell vague 'AI transformation'. We show you exactly how much you save, with which tools, in which workflows."** | **Sales conversations, objection handling** |
| Businesses automate the wrong things | "Most businesses work hard on the wrong automation. We show you which 20% of your stack delivers 80% of the AI value." | Landing pages, quiz intro |
| AI tool overwhelm = "tutorial hell" | "Stop evaluating AI tools. Start implementing the right ones." | Ad copy, email sequences |
| DIY with ChatGPT is inconsistent | "Generic AI gives you genius one day, garbage the next. Our framework delivers consistent, reliable results." | Objection handling, FAQ |
| Trust breaks instantly | "AI generates. Humans verify. One wrong recommendation erodes trust faster than ten good ones build it." | Workshop positioning, report delivery |
| Data/distribution is the only moat | Reinforces our compounding expertise strategy — models are commodities, methodology + data is the moat | Internal strategy alignment |
| People know what to do but don't act | "You already know AI matters. We give you the blueprint to actually do something about it." | CTA copy, follow-up emails |
| "You're already paying for AI" | "You're already paying for AI tools. We make sure they actually work together." | Pricing page, conversion copy |

### Positioning Refinement

**Against DIY/ChatGPT:** Higher floor wins. CRB delivers consistent 8/10 results, not a coin flip between 10/10 and 2/10. Framework-driven analysis removes the variance.

**Against traditional consulting:** 48 hours and €147 vs 6 weeks and €15K. Same rigour, AI-fulfilled, human-reviewed.

**Against doing nothing:** The 0.04% stat. Your competitors who figure this out first win. The gap between "aware of AI" and "implementing AI" is where money is made — or lost.

---

## Long-term: Asset Formalization & Exit

> Source: Priestley's 6-step entrepreneurial journey — Steps 5 & 6.

Even pre-PMF, the decisions we make now shape what's acquirable later. Think about it early, execute on it later.

### Formalizable Assets

Every engagement compounds these assets. Track and formalize them deliberately:

| Asset | Current State | Formalized State |
|-------|---------------|------------------|
| CRB Framework | Code + scoring logic | Registered IP, published methodology |
| Vendor Database | JSON files, growing | Proprietary dataset with verified pricing |
| Industry Benchmarks | Per-vertical knowledge base | Cross-industry benchmark database |
| Case Studies | None yet | 50+ with before/after metrics |
| Content Library | Landing pages, quiz copy | Brand book, video explainers, training materials |
| Customer Data | Quiz responses, reports | Anonymized adoption patterns dataset |

### Quality of Earnings (Shape Revenue Early)

| Revenue Type | Value to Acquirer | CRB Path |
|-------------|-------------------|----------|
| Recurring subscription | Highest | Post-report monitoring, quarterly re-analysis |
| Repeatable product | High | €147 reports (scalable, predictable) |
| One-off services | Low | Avoid — workshops should lead to reports, not standalone |

**Decisions this shapes now:**
- Prioritize the €147 report as the core revenue unit (repeatable, scalable)
- Build toward a subscription layer (quarterly re-analysis, implementation tracking)
- Resist custom consulting engagements that don't scale
- Track EBITDA from day one, not just revenue

### Exit Thinking (Not Yet, But Shape For It)

Three buyer types to keep in mind:

| Buyer Type | Why They'd Want CRB | What They Value |
|-----------|---------------------|-----------------|
| **Strategic** | Consulting firm wanting AI-native capability | Methodology + customer base + data moat |
| **Financial** | PE/VC wanting recurring revenue at 95% margins | Quality of earnings + growth trajectory |
| **Trophy** | AI company wanting credibility in consulting | Brand + case studies + framework IP |

**We don't need to pursue exit now.** But every decision should leave the door open: clean financials, documented IP, formalized assets, recurring revenue. Companies that build with exit hygiene from day one sell for multiples of those that scramble to formalize later.

---

## Signal Loop Gaps (Remaining)

- [ ] Expertise system updates from analyses
- [ ] 30-day follow-up mechanism
- [ ] Pattern extraction from completed reports
