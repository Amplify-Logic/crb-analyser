# CRB Analyser - Product Domain

> This document describes WHAT the product does and its domain model.
> For HOW to develop, see [CLAUDE.md](./CLAUDE.md).
> For WHY we're building this, see [STRATEGY.md](./STRATEGY.md).

---

## Product Overview

**CRB Analyser** delivers AI-powered Cost/Risk/Benefit analysis for professional services firms considering AI implementation. We help compliance-focused businesses get clarity on AI opportunities without expensive consultants.

### Core Promise

> "The analysis makes the best option obvious."

We don't just list pros and cons. Our CRB framework scores every option across multiple dimensions so the right choice emerges clearly - with confidence levels and trade-offs explicitly stated.

### Delivery Model

| Component | Description |
|-----------|-------------|
| **Quiz** | 5-7 minute adaptive assessment to understand business context |
| **AI Workshop** | 90-minute AI-powered deep-dive gathering detailed operational context |
| **Human Review** | Every report reviewed by domain expert before delivery |
| **Report Delivery** | 24-48 hours after workshop completion |
| **Price** | €147 (enterprise-grade analysis at SMB pricing) |

---

## Messaging Pillars

Our value proposition centers on four key themes for professional services:

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
- Clear verdicts: Proceed, Wait, or Skip
- Three Options model removes analysis paralysis
- Specific tools, prices, and implementation steps

### 4. Competitive Positioning
> "Your competitors are adopting AI. Know which tools give real advantage."

- Industry-specific insights (not generic AI hype)
- Benchmarks against similar firms
- Strategic recommendations tied to business goals
- Clear differentiation opportunities

---

## Three Options Model (3O)

Every recommendation presents three options: **Off-the-Shelf** (fast, proven), **Best-in-Class** (premium, full features), **Custom Build** (full control, competitive moat).

When recommending Custom, include build tools, model choice, skills, dev hours, and stack.

> **Full three-options methodology** → [FRAMEWORK.md](./FRAMEWORK.md#the-three-options-pattern)

---

## CRB Framework (Core Methodology)

The Cost-Risk-Benefit framework analyzes every opportunity across **10 dimensions**:

- **6 Costs**: Financial, Time, Opportunity, Complexity, Risk, Brand/Trust
- **4 Benefits**: Financial, Time, Strategic, Quality
- **NET SCORE** = Benefit - Cost - (Risk / 10)

Findings are prioritized as: **Quick Win** → **Strategic** → **Consider** → **Defer**

> **Full CRB methodology, scoring, evidence requirements, and time horizons** → [FRAMEWORK.md](./FRAMEWORK.md)

---

## Connect vs Replace Strategy

For every automation opportunity, we present two paths:

| Strategy | When We Recommend | Example |
|----------|-------------------|---------|
| **Connect** | Current tools work well, just need automation | "Keep Clio, add n8n for client intake automation" |
| **Replace** | Current tools are fundamentally limiting | "Move from spreadsheets to Karbon for workflow" |

### Decision Factors We Analyze

| Factor | Favors Connect | Favors Replace |
|--------|----------------|----------------|
| Current tool quality | Works well | Fundamentally broken |
| Team size | Large (change is risky) | Small (can adapt quickly) |
| Data complexity | High (migration risk) | Low (easy to move) |
| Budget | Limited | Available for investment |
| Technical capability | Low | Has dev resources |

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

## Target Industries

### Parallel Launch Strategy

> **Same platform. Same price. Same framework. Different landing pages.**
> Let the market tell us which vertical converts best.

We launch all three verticals simultaneously with:
- Shared CRB analysis engine
- Vertical-specific knowledge bases
- Industry-tailored landing pages and messaging
- Common €147 price point

---

### Vertical 1: Professional Services

**Slug:** `professional-services`

**Customer Profile:**
- Partners/principals who make technology decisions
- Compliance-aware (understand risk, value documentation)
- Time-pressured (billable hours matter)
- Mid-market sweet spot (€500K - €20M revenue)

**Segments:** Accounting, Legal, Consulting, Architecture/Engineering, Financial Advisory

**Key Pain Points:**
| Pain Point | Impact |
|------------|--------|
| Client Onboarding | 3-5 hours per client in manual intake |
| Time Tracking | 10-20% revenue leakage from unbilled work |
| Document Management | Version chaos, compliance gaps |
| Client Communication | Update requests eat billable time |

**Software Ecosystem:**
| Category | Key Vendors |
|----------|-------------|
| Practice Management | Clio, Karbon, Practice Ignition, Canopy |
| Time & Billing | Harvest, Toggl, FreshBooks, Xero |
| Automation | n8n, Make, Zapier |
| AI Tools | Claude, ChatGPT, Harvey (legal) |

---

### Vertical 2: Dental Practices

**Slug:** `dental`

**Customer Profile:**
- Practice owners and office managers
- Solo practices, group practices, DSOs
- Already using practice management software
- High-ticket services support tool investment

**Key Pain Points:**
| Pain Point | Impact |
|------------|--------|
| Patient Recall | No-shows cost €200-500 per missed appointment |
| Insurance Verification | 15-30 min per patient, delays treatment |
| Treatment Planning | Manual case presentation, low acceptance rates |
| No-Show Management | 10-15% no-show rate typical |

**Software Ecosystem:**
| Category | Key Vendors |
|----------|-------------|
| Practice Management | Dentrix, Open Dental, Curve Dental, Eaglesoft |
| Patient Communication | Weave, RevenueWell, Lighthouse 360 |
| Insurance | Vyne Dental, DentalXChange |
| AI Tools | Pearl, Overjet, VideaHealth |

---

### Vertical 3: E-commerce

**Slug:** `ecommerce`

**Customer Profile:**
- DTC brands, marketplace sellers, B2B wholesale
- €500K - €10M annual revenue
- Already on Shopify/WooCommerce
- Scaling operations, feeling pain

**Key Pain Points:**
| Pain Point | Impact |
|------------|--------|
| Customer Support | Repetitive queries consume 40%+ of support time |
| Inventory Forecasting | Stockouts and overstock eat margins |
| Returns Processing | Manual handling costs €5-15 per return |
| Marketing Attribution | Can't tell what's working |

**Software Ecosystem:**
| Category | Key Vendors |
|----------|-------------|
| Platform | Shopify, WooCommerce, BigCommerce |
| Customer Support | Gorgias, Zendesk, Intercom |
| Email/SMS | Klaviyo, Omnisend, Postscript |
| Analytics | Triple Whale, Northbeam, Lifetimely |

---

### Launch Markets

| Market | Currency | Priority Verticals |
|--------|----------|-------------------|
| Netherlands | EUR | Professional Services, E-commerce |
| UK | GBP | All three |
| Australia | AUD | Dental, Professional Services |
| USA | USD | E-commerce, Dental |

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
├── professional-services/  # Phase 1 industry data
│   ├── processes.json      # Common workflows
│   ├── opportunities.json  # AI automation opportunities
│   ├── benchmarks.json     # Industry metrics
│   └── vendors.json        # Relevant software
├── dental/                 # Phase 2 (build when entering)
│   └── ...
├── ecommerce/              # Phase 3 (build when entering)
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
90-Minute AI Workshop
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

> "We help professional services firms figure out which AI tools are worth their time - and which to skip."

### The Promise
- You get a personalised report with specific tools, prices, and implementation steps
- No generic advice - we know your industry (Clio, Karbon, not Salesforce)
- Clear verdicts: Proceed, Wait, or Skip
- Enterprise-quality analysis at €147, not €15,000

### What We're NOT
- Not a consulting firm (we're a product)
- Not an AI vendor (we recommend, don't sell)
- Not generic (we're industry-specific)

---

## Report Structure

Executive Summary → Detailed Findings (3-5) → Implementation Roadmap → Appendices

Each finding includes: Problem Statement, Opportunity, Three Options with CRB Analysis, Verdict, and Implementation Path.

> **Full report structure with CRB table format** → [FRAMEWORK.md](./FRAMEWORK.md#report-structure)

---

## Shortcuts

| Short | Meaning |
|-------|---------|
| CRB | Cost-Risk-Benefit (the core framework) |
| 3O | Three Options model (Off-the-Shelf, Best-in-Class, Custom) |
| 6C | Six Costs (Financial, Time, Opportunity, Complexity, Risk, Brand) |
| 4B | Four Benefits (Financial, Time, Strategic, Quality) |
| C/R | Connect vs Replace strategy |
| ROI-CA | ROI Confidence-Adjusted |
| KB | Knowledge Base |
| PM | Practice Management software |
| PS | Professional Services |
| QW | Quick Win (high benefit, low cost/risk) |
