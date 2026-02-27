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

## Strategic Focus: Parallel Vertical Launch

### The Bet

> "Launch three verticals simultaneously. Let the market tell us which converts best."

Instead of sequential expansion, we test all three markets at once with:
- Same core platform and CRB framework
- Same €147 price point
- Different landing pages and messaging
- Vertical-specific knowledge bases

### Why Parallel Launch?

| Factor | Advantage |
|--------|-----------|
| **Faster Signal** | Learn which market has best PMF in weeks, not years |
| **Shared Infrastructure** | 80% of platform is industry-agnostic |
| **Lower Risk** | If one vertical fails, others may succeed |
| **Compounding Data** | Cross-industry patterns emerge faster |

### Four Verticals

| Vertical | Why It Could Win | Risk |
|----------|------------------|------|
| **Professional Services** | Compliance-focused, referral-driven, budget available | Slower sales cycles |
| **Dental** | Clear processes, tech-forward, high-ticket services | Niche community |
| **E-commerce** | Volume market, automation-hungry, measurable ROI | Crowded space |
| **B2B Platforms** | Hardware-to-platform companies scaling lean, complex integrations | Niche but high-value |

### Success Signals (First 90 Days)

| Metric | Target | What It Tells Us |
|--------|--------|------------------|
| Quiz completions | 100+ per vertical | Is the message landing? |
| Quiz → Paid conversion | >5% | Is €147 the right price? |
| Workshop completion | >80% | Is the process working? |
| Best vertical gap | 2x difference | Where to double down |

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
| Scaling too fast | Quality drops, brand damage | Phase gates: 50 reports before next industry |
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
| Quiz completions (total) | 300+ | Validate traffic/messaging |
| Paid reports (total) | 15+ | Prove willingness to pay |
| Best vertical identified | Clear leader | Know where to focus |
| Workshop completion rate | 80%+ | Validate process works |
| NPS | 50+ | Quality baseline |

### Per-Vertical Tracking

| Metric | Professional Services | Dental | E-commerce |
|--------|----------------------|--------|------------|
| Quiz starts | Track | Track | Track |
| Quiz completions | Track | Track | Track |
| Conversion to paid | Track | Track | Track |
| Workshop completion | Track | Track | Track |

### Decision Point (Day 90)

After 90 days, we answer:
- [ ] Which vertical has highest conversion rate?
- [ ] Which vertical has highest NPS?
- [ ] Which vertical has best referral potential?
- [ ] Double down on winner OR pivot if all fail

---

## Before Claiming "Done"

- [ ] Does it solve a professional services firm's real pain?
- [ ] Did we ship the smallest useful version first?
- [ ] Is there a feedback mechanism built in?
- [ ] Would we be proud to show this to a managing partner?

---

## Signal Loop Gaps (Remaining)

- [ ] Expertise system updates from analyses
- [ ] 30-day follow-up mechanism
- [ ] Pattern extraction from completed reports
