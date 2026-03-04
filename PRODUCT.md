# CRB Analyser - Product Domain

> This document describes WHAT the product does and its domain model.
> For HOW to develop, see [CLAUDE.md](./CLAUDE.md).
> For WHY we're building this, see [STRATEGY.md](./STRATEGY.md).

---

## Product Overview

**CRB Analyser** delivers AI-powered architecture blueprints that show businesses how to build their AI Operating System (AIOS) on top of their existing tools. We help companies get clarity on what to connect, what to automate, and what to build — without ripping out what already works.

### Core Promise

> "Connect what you have. Automate what slows you down. Build what doesn't exist."

We don't just list software recommendations. Our CRB framework analyzes your existing stack, identifies the gaps between systems, and architects an AI layer that connects everything — with specific workflows, agents, and integrations you can build this week.

### Delivery Model

| Component | Description |
|-----------|-------------|
| **Quiz** | 5-7 minute adaptive assessment to understand business context |
| **AI-Assisted Workshop** | 90-minute AI-driven deep-dive — AI conducts the session, gathering detailed operational context |
| **Human Review** | Every report reviewed by domain expert before delivery |
| **Report Delivery** | 24-48 hours after workshop completion |
| **Price** | €147 (enterprise-grade analysis at SMB pricing) |

---

## Messaging Pillars

Our value proposition centers on four key themes:

### 1. Compliance & Risk Management
> "Make AI decisions with the same rigor you apply to client work."

- Structured framework reduces adoption risk
- Clear documentation for internal governance
- Vendor vetting includes security and compliance assessment
- Recommendations include risk mitigation strategies

### 2. Operational Efficiency
> "Every hour on admin is an hour not billing."

- Focus on high-ROI automation opportunities
- Quantified time savings with confidence levels
- Integration with existing practice management tools
- Realistic implementation timelines

### 3. Rapid Decision-Making
> "From confusion to clarity in 48 hours, not 6 weeks."

- Enterprise-quality analysis at a fraction of consulting costs
- Clear verdicts: Connect, Enhance, Replace, or Add
- AIOS Options model removes analysis paralysis
- Specific tools, prices, and implementation steps
- Breaks "AI tool hell" — stop evaluating, start implementing

### 4. Competitive Positioning
> "Your competitors are adopting AI. Know which tools give real advantage."

- Industry-specific insights (not generic AI hype)
- Benchmarks against similar firms
- Strategic recommendations tied to business goals
- Clear differentiation opportunities
- 84% of people have never used AI — early movers in your industry win disproportionately

---

## AIOS Options Model

Every recommendation presents options prioritized by implementation speed and disruption:

| Priority | Option | When We Recommend | Example |
|----------|--------|-------------------|---------|
| 1st | **Connect & Automate** | Tool works, just needs wiring | "Keep HubSpot + Exact, build Claude workflow to sync deals → invoices" |
| 2nd | **Enhance with AI** | Need intelligence on top of existing data | "Build an AI agent that monitors IoT usage data and flags churn risk" |
| 3rd | **Add to Stack** | Gap where no tool exists | "Add Klaviyo for email automation — nothing in your stack covers this" |
| 4th | **Targeted Upgrade** | Tool is a dead end — no API, fundamentally broken | "Migrate from spreadsheets to Odoo for inventory tracking" |

**Connect-first philosophy:** We never recommend replacing software unless the existing tool genuinely cannot be integrated (no API, fundamentally broken, blocking growth). Most businesses can get 80% of the value by connecting what they have.

### Decision Factors

| Factor | Favors Connect/Enhance | Favors Replace |
|--------|------------------------|----------------|
| Tool has API | Yes — wire it up | - |
| Tool fundamentally broken | - | Yes — it's blocking you |
| Team already trained | Yes — don't retrain | - |
| Data is trapped | - | Yes — if no export path |
| Budget constrained | Yes — build, don't buy | - |
| Technical capability | Yes — build workflows | Low — may need turnkey |

> **Full AIOS methodology** → [FRAMEWORK.md](./FRAMEWORK.md#aios-options-model)

---

## CRB Framework (Core Methodology)

The Cost-Risk-Benefit framework analyzes every opportunity across **10 dimensions**:

- **6 Costs**: Financial, Time, Opportunity, Complexity, Risk, Brand/Trust
- **4 Benefits**: Financial, Time, Strategic, Quality
- **NET SCORE** = Benefit - Cost - (Risk / 10)

Findings are prioritized as: **Quick Win** → **Strategic** → **Consider** → **Defer**

> **Full CRB methodology, scoring, evidence requirements, and time horizons** → [FRAMEWORK.md](./FRAMEWORK.md)

---

## Confidence & ROI

Every estimate carries a confidence level that adjusts the reported value:

| Level | Factor | Criteria |
|-------|--------|----------|
| HIGH | 1.0 | User-provided numbers, verified benchmark |
| MEDIUM | 0.85 | Industry pattern likely applies, one strong data point |
| LOW | 0.70 | Significant assumptions required |

`adjusted_estimate = base_estimate * confidence_factor`

**Display rules:** Always show "Estimated", always show confidence level, use ranges for LOW confidence, source every benchmark.

> **Full confidence methodology and evidence requirements** → [FRAMEWORK.md](./FRAMEWORK.md#quality-standards)

---

## Target Industry: E-commerce

### E-commerce Lock-In

> **One vertical. Deep expertise. Win the niche before expanding.**

We focus exclusively on e-commerce with:
- Deep ecommerce knowledge base (16 pain points, 12 processes, 50+ vendor entries)
- EU-focused tooling: Mollie, Sendcloud, Channable, Picqer, Bol.com integrations
- Industry-specific landing page, quiz copy, and workshop questions
- €147 price point for full CRB report

**Why e-commerce first:**
- Measurable ROI — store owners can track the impact of every automation
- Volume market — millions of Shopify/WooCommerce stores globally
- Automation-hungry — most operations are repetitive and rule-based
- EU advantage — our deep knowledge of EU tools and regulations is a moat

---

### Customer Profile

**Slug:** `ecommerce`

- DTC brands, marketplace sellers, B2B wholesale
- €500K - €10M annual revenue
- Already on Shopify/WooCommerce/Magento
- Scaling operations, feeling pain
- EU-based or EU-selling (our primary strength)

### Key Pain Points

| Pain Point | Impact | Frequency |
|------------|--------|-----------|
| Customer Support | Repetitive queries consume 40%+ of support time | Very high |
| Abandoned Carts | 70% average abandonment rate | Very high |
| Returns Processing | Manual handling costs €5-15 per return | High |
| Inventory Forecasting | Stockouts and overstock eat margins | High |
| Marketing Attribution | Can't tell what's working post-iOS | High |
| Multi-channel Sync | Inconsistent inventory/pricing across channels | Medium-high |
| EU Compliance | AI Act, DSA, EAA, GDPR, VAT complexity | Medium-high |

### Software Ecosystem

| Category | Key Vendors |
|----------|-------------|
| Platform | Shopify, WooCommerce, BigCommerce, Magento |
| Customer Support | Gorgias, Tidio, Zendesk |
| Email/SMS | Klaviyo, Omnisend |
| Payments | Mollie (EU), Stripe, Adyen |
| Shipping | Sendcloud, ShipStation, Monta |
| Feed Management | Channable, ChannelEngine |
| Returns | Loop Returns, ReturnGO |
| Analytics | Triple Whale, Lifetimely, Polar Analytics |

### Launch Markets

| Market | Currency | Notes |
|--------|----------|-------|
| Netherlands | EUR | Home market, deepest knowledge |
| DACH (DE/AT/CH) | EUR | Largest EU e-commerce market |
| UK | GBP | Strong Shopify penetration |
| Nordics | EUR/SEK/DKK/NOK | High digital adoption |

---

## Knowledge Base Structure

```
backend/src/knowledge/
├── vendors/                # Vendor pricing database (our moat)
│   ├── ai_assistants.json
│   ├── automation.json     # n8n, Make, Zapier
│   ├── crm.json
│   ├── scheduling.json
│   └── ...
├── ai_tools/
│   └── llm_providers.json  # Claude, GPT pricing
├── professional-services/  # Industry data
│   ├── processes.json      # Common workflows
│   ├── opportunities.json  # AI automation opportunities
│   ├── benchmarks.json     # Industry metrics
│   └── vendors.json        # Relevant software
├── dental/                 # Industry data
│   └── ...
├── ecommerce/              # Industry data
│   └── ...
└── patterns/
    └── ai_implementation_playbook.json
```

### Data Integrity Rules
- **NO MOCK DATA** - Every stat must have verifiable source
- Include: source name, URL, date, `"verified_date": "YYYY-MM"`
- Unverified data: mark `"status": "UNVERIFIED"`, apply LOW confidence, show warning
- Refresh cadence: Vendor pricing monthly, benchmarks quarterly, market size annually

---

## Expertise System (Our Moat)

The agent learns from each analysis to improve future recommendations.

### Learning Loop
```
BEFORE Analysis:
    Load industry expertise (pain_points, effective_patterns, anti_patterns)

DURING Analysis:
    Track tools used, errors, phase completion

AFTER Analysis:
    Update expertise with findings, recommendations, patterns

AFTER User Feedback:
    Track implementation rates, actual vs estimated ROI

NEXT Analysis:
    Improved prompts, faster detection, better accuracy
```

### Expertise Data
| Field | Description |
|-------|-------------|
| pain_points | Common issues + frequency + solutions that worked |
| processes | Typical workflows + automation potential |
| effective_patterns | Recommendations that succeeded |
| anti_patterns | What NOT to recommend (learned from failures) |
| size_specific | Insights by firm size |
| implementation_rates | Which recs actually get implemented |
| accuracy_tracking | Estimated vs actual ROI |

### Compounding Effect
```
Analysis #1:    Base accuracy
Analysis #50:   +10% ROI accuracy (validated estimates)
Analysis #100:  +20% recommendation hit rate
Analysis #500:  Competitors can't catch up
```

---

## Agent Phases

| Phase | Model | Purpose |
|-------|-------|---------|
| Discovery | Haiku 4.5 | Parse intake, extract pain points, identify tech stack |
| Research | Haiku 4.5 / Gemini Flash | Find benchmarks, match vendors, validate pricing |
| Analysis | Sonnet 4.5 | Score automation potential, calculate impact, find AI opportunities |
| Modeling | Sonnet 4.5 | Calculate ROI, compare vendors, generate timeline |
| Report | Tier-based (Opus for premium) | Executive summary, full report, PDF |

---

## User Journey

### Quiz to Report Flow

```
Landing Page
    |
    v
Quiz (5-7 minutes)
    - Industry identification
    - Business context
    - Current tech stack
    - Pain point ranking
    - AI readiness signals
    |
    v
AI Readiness Score + Teaser
    - Personalized preview
    - Top 2-3 opportunities identified
    - "Full report shows X more findings"
    |
    v
Stripe Checkout (€147)
    |
    v
AI Workshop Scheduling
    - Calendar integration
    - Prep questions sent
    |
    v
90-Minute AI-Assisted Workshop
    - AI drives the conversation
    - Deep-dive on operations
    - Current workflow mapping
    - Tool usage patterns
    - Decision criteria gathering
    |
    v
Human Review (Internal)
    - Domain expert validates
    - Ensures accuracy
    - Adds context where needed
    |
    v
Report Delivery (24-48 hours)
    - Email notification
    - Report viewer access
    - PDF download
    |
    v
30-Day Follow-up
    - Implementation check
    - Feedback collection
    - Referral ask
```

---

## Positioning

> "We help businesses build their AI Operating System — connecting what they have, automating what slows them down."

### The Promise
- You get an architecture blueprint specific to YOUR stack
- No generic "buy this tool" advice — we show what to build and connect
- Clear verdicts: Connect, Enhance, Replace, or Add
- Enterprise-quality analysis at €147, not €15,000

### What We're NOT
- Not a software comparison site (we're an architecture firm)
- Not an AI vendor (we recommend, don't sell)
- Not generic (we know your industry and your stack)

---

## Report Structure

Executive Summary → Strategic Overview → Findings → Recommendations (with AIOS Options + CRB Analysis) → Implementation Roadmap → Appendix

Each recommendation includes: Problem Statement, Opportunity, AIOS Options (Connect/Enhance/Add/Replace) with CRB Analysis, NET SCORE, Verdict, and Implementation Path.

> **Full report structure with CRB table format** → [FRAMEWORK.md](./FRAMEWORK.md#report-structure)

