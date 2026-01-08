# CRB Analyser - Strategy

> This document describes WHY we're building this and our strategic framework.
> For WHAT the product does, see [PRODUCT.md](./PRODUCT.md).
> For HOW to develop, see [CLAUDE.md](./CLAUDE.md).

---

## Core Principle

> "Don't chase billion-dollar markets. Fix thousand-dollar frustrations that happen a million times."

We target passion-driven service businesses because their pain is:
- **Urgent** (happens daily)
- **Frequent** (every client interaction)
- **Painful** (admin steals time from craft)

---

## Product as Proof

> "CRB is the thesis it sells."

We don't just analyze whether companies should restructure around AI. We *are* the demonstration.

**What this means:**

| Old Model (Consulting Firm) | CRB Model |
|-----------------------------|-----------|
| Analysts researching industry | Knowledge base + AI |
| Consultants conducting interviews | Adaptive quiz + voice interview |
| Report writers drafting findings | AI-generated reports |
| Account managers coordinating | Self-serve flow |
| 6-week engagement, €15k+ | 15 minutes, €147 |

**Structural discipline:**

1. **Stay small longer than feels comfortable** - Headcount is not progress. Leverage is.
2. **Hire for outcomes, not functions** - Only when AI is exhausted for a specific result.
3. **No coordination overhead** - If you need meetings to align, you're already too big.
4. **The €147 tier proves the model** - Enterprise-level analysis at SMB pricing only works with AI leverage.

**The uncomfortable implication:**

If CRB succeeds, it makes the same argument to its customers: you probably don't need that analyst, that researcher, that report writer. The product is a demonstration of its own thesis.

This isn't positioning. It's identity.

---

## The Four Loops

### 1. Balance Loop (BL)

Walk a tightrope between two forces:

| Your Asymmetric Advantage | Their Acute Pain |
|---------------------------|------------------|
| Industry knowledge base | Drowning in admin |
| AI/automation expertise | No time for craft |
| Compounding expertise system | Confused by AI hype |
| Three Options framework | Analysis paralysis |

**Warning Signs:**
- Leaning too far into advantage → "Cool AI but why pay?"
- Leaning too far into pain → Commoditized, no edge

**For every feature, ask:**
1. Does this leverage our asymmetric advantage?
2. Does this solve an acute, urgent, frequent pain?
3. What are we assuming? Can we test it in hours, not months?

---

### 2. Speed to Revenue Loop (STR)

> "Product-market fit is not a destination. It's a moving target. You chase it daily."

```
LAUNCH → LEARN → LEVEL UP → repeat
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
- Industry-specific knowledge that compounds
- Expertise system that learns from every analysis
- Trust relationships with passion-driven owners

**Dogfooding:** Run CRB analysis on ourselves monthly.

---

### 3. Signal to Innovation Loop (SIL)

> "Your product can be cloned. Your landing page can be copied. But if you're addicted to a strong signal loop... that is hard to copy."

```
Analysis Complete
    ↓
Extract Patterns (which findings resonated? what got implemented?)
    ↓
Update Knowledge Base (add patterns, mark anti-patterns, refine benchmarks)
    ↓
Better Next Analysis
    ↓
Higher Customer Trust
    ↓
More Analyses → Compounding
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
└── "Passion-driven professionals deserve AI clarity, not expensive consultants"
        ↓
OBSESSIVE GRIT
└── Report quality matters. ROI accuracy matters. Vendor freshness matters.
        ↓
STAYING POWER
└── Stay in the game when 99% would quit
        ↓
COMPOUNDING NET WORTH
└── Unseen work becomes visible results
```

**Wisdom Loop:** Even if we fail, we create:
- Proven industry knowledge base
- Validated expertise system architecture
- Trust with target customers

These become foundation for the next thing.

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

| Question | If "No" → Don't Build |
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

## Before Claiming "Done"

- [ ] Does it solve a thousand-dollar frustration that happens a million times?
- [ ] Did we ship the smallest useful version first?
- [ ] Is there a feedback mechanism built in?
- [ ] Would we be proud to show this to a passion-driven professional?

---

## MVP Checklist

### Backend
- [ ] Auth (signup, login, logout)
- [ ] Clients CRUD
- [ ] Audits CRUD with status
- [ ] Intake submission
- [ ] Agent analysis
- [ ] Findings + Recommendations with ROI
- [ ] PDF report
- [ ] Stripe checkout + webhooks

### Frontend
- [ ] Landing page
- [ ] Auth flow
- [ ] Dashboard
- [ ] Intake wizard
- [ ] Progress streaming
- [ ] Report viewer + PDF download
- [ ] Payment flow

### Signal Loop (Critical)
- [ ] Post-report feedback ("Which recs will you implement?")
- [ ] Expertise system updates from analyses
- [ ] Analytics on key behaviors
- [ ] 30-day follow-up mechanism
- [ ] Pattern extraction from completed reports

---

## Shortcuts

| Short | Meaning |
|-------|---------|
| BL | Balance Loop |
| STR | Speed to Revenue Loop |
| SIL | Signal to Innovation Loop |
| SEL | Sweat Equity Loop |
| PMF | Product-Market Fit |
| DF | Dogfooding |
