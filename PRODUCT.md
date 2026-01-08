# CRB Analyser - Product Domain

> This document describes WHAT the product does and its domain model.
> For HOW to develop, see [CLAUDE.md](./CLAUDE.md).
> For WHY we're building this, see [STRATEGY.md](./STRATEGY.md).

---

## Product Overview

**CRB Analyser** delivers AI-powered Cost/Risk/Benefit analysis for businesses considering AI implementation. We help passion-driven service professionals get clarity on AI opportunities without expensive consultants.

### Core Promise

> "The analysis makes the best option obvious."

We don't just list pros and cons. Our CRB framework scores every option across multiple dimensions so the right choice emerges clearly - with confidence levels and trade-offs explicitly stated.

---

## Three Options Model (3O)

Every recommendation presents three options to give clients real choice:

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A: Off-the-Shelf** | Fastest to deploy, lowest risk, proven solution | Less customization |
| **B: Best-in-Class** | Premium vendor, full features, better support | Higher cost |
| **C: Custom Build** | Full control, competitive advantage potential | Needs technical capability |

### Custom Solution Details
When recommending Option C, include:
- **Build tools:** Claude Code, Cursor, VS Code
- **Model recommendation:** Which Claude model and why
- **Skills required:** Python, API integration, frontend, etc.
- **Dev hours estimate:** Realistic range
- **Recommended stack:** e.g., FastAPI + React + Supabase + Railway
- **Key APIs:** Specific integrations needed

---

## CRB Framework (Core Methodology)

The Cost-Risk-Benefit framework analyzes every opportunity across **10 dimensions** to make the best option obvious.

### The Six Dimensions of Cost

Cost is NOT just money. We analyze what the customer will actually spend:

| Dimension | What We Measure | Customer Question |
|-----------|-----------------|-------------------|
| **Financial** | Subscription, setup, hidden fees | "What will this cost me per month/year?" |
| **Time** | Implementation, learning curve, maintenance | "How long until I see value? How much ongoing effort?" |
| **Opportunity** | What they can't do if they do this | "What else could I spend this budget/time on?" |
| **Complexity** | Systems touched, training needed | "How much will this disrupt my business?" |
| **Risk** | What could go wrong, reversibility | "What if it doesn't work? Can I undo this?" |
| **Brand/Trust** | Customer perception, team morale | "Will my customers/team notice? For better or worse?" |

### The Four Dimensions of Benefit

| Dimension | What We Measure | Customer Question |
|-----------|-----------------|-------------------|
| **Financial** | Revenue increase, cost savings | "How much will I save or earn?" |
| **Time** | Hours freed, speed improvements | "How much time do I get back?" |
| **Strategic** | Market position, competitive edge | "Does this help me stand out or grow?" |
| **Quality** | Customer experience, team satisfaction | "Will my customers and team be happier?" |

### Risk Analysis

Every recommendation includes explicit risk assessment:

| Risk Type | What Could Go Wrong | How We Address It |
|-----------|---------------------|-------------------|
| **Implementation** | Tool doesn't work as expected | Recommend pilots, phased rollout |
| **Adoption** | Team doesn't use it | Flag training needs, change management |
| **Vendor** | Company disappears, prices spike | Note vendor stability, exit strategies |
| **Security** | Data exposure, compliance issues | Flag security concerns, certifications |
| **Integration** | Breaks existing systems | Identify integration complexity |

### Scoring & Comparison

Each option receives a **NET SCORE** that makes comparison objective:

```
NET SCORE = Benefit Score - Cost Score - (Risk Score ÷ 10)
```

The comparison summary shows:
- **Winner** with clear reasoning
- **Trade-offs** of the recommended option
- **When to choose alternatives** (e.g., "Choose Option B if budget is not a constraint")

### Prioritization Output

Findings are prioritized by combining scores with business impact:

| Priority | Criteria | Action |
|----------|----------|--------|
| **Quick Win** | High benefit, low cost, low risk | Do this week |
| **Strategic** | High benefit, medium cost/risk | Plan for next quarter |
| **Consider** | Medium benefit, varies | Evaluate when capacity allows |
| **Defer** | Low benefit or high risk | Revisit in 6-12 months |

---

## Connect vs Replace Strategy

For every automation opportunity, we present two paths:

| Strategy | When We Recommend | Example |
|----------|-------------------|---------|
| **Connect** | Current tools work well, just need automation | "Keep Dentrix, add n8n for appointment reminders" |
| **Replace** | Current tools are fundamentally limiting | "Move from spreadsheets to HubSpot CRM" |

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

### Confidence Levels

Every estimate in the report - financial, time, or otherwise - carries a confidence level:

| Level | Distribution | Factor | Criteria |
|-------|-------------|--------|----------|
| HIGH | ~30% | 1.0 | Quiz directly mentions issue, user-provided numbers, verified benchmark |
| MEDIUM | ~50% | 0.85 | Quiz implies issue, industry pattern likely applies, one strong data point |
| LOW | ~20% | 0.70 | Industry pattern suggests possibility, significant assumptions required |

### Applying Confidence to All Dimensions

Confidence applies to every CRB dimension, not just financial:

| Dimension | HIGH Example | LOW Example |
|-----------|--------------|-------------|
| **Financial** | "Save €2,400/month" (user said €60/hr × 40hrs) | "Save €1,200-€2,400/month" (industry average) |
| **Time** | "Save 10 hrs/week" (user specified tasks) | "Save 5-15 hrs/week" (typical for industry) |
| **Risk** | "Low risk - team already uses similar tool" | "Medium risk - adoption uncertain" |

### ROI Calculation
```python
adjusted_estimate = base_estimate * confidence_factor
# HIGH:   €10,000 * 1.0  = €10,000
# MEDIUM: €10,000 * 0.85 = €8,500
# LOW:    €10,000 * 0.70 = €7,000
```

### Display Rules
- Always show "**Estimated**" - never claim certainty
- Show confidence level visibly next to every number
- List key assumptions explicitly
- Use ranges for LOW confidence: "€1,200-€1,800/month"
- If everything is HIGH confidence, we're being dishonest about uncertainty
- Source every benchmark (industry report, verified vendor pricing, user input)

---

## Target Industries

### Customer Profile
**Passion-driven service businesses:**
- Owner-operators who make fast decisions
- Relationship-driven (clients = humans, not logos)
- Passion/craft-based (people love what they do)
- Clear operational pain (admin eats creative/service time)
- Mid-market sweet spot ($500K - $20M revenue)
- Local/regional focus

### Primary Industries (Launch)

| Industry | Slug | Score | Key Pain |
|----------|------|-------|----------|
| Professional Services | `professional-services` | 89 | Billable hour tracking, client communication |
| Home Services | `home-services` | 85 | Scheduling, dispatch, invoicing |
| Dental | `dental` | 85 | Patient scheduling, insurance, recalls |

### Secondary Industries (Phase 2)

| Industry | Slug | Score | Key Pain |
|----------|------|-------|----------|
| Recruiting | `recruiting` | 82 | Candidate screening, job matching |
| Coaching | `coaching` | 80 | Session scheduling, client progress |
| Veterinary | `veterinary` | 80 | Appointment scheduling, records |

### Phase 3
`physical-therapy`, `medspa` - Knowledge base needed

### Dropped Industries
Music Studios (budget), Marketing Agencies (DIY), E-commerce (not service), Retail, Tech Companies (DIY), Gyms (margins), Hotels (slow decisions)

### Launch Markets
Netherlands, Germany, UK, Ireland

---

## Knowledge Base Structure

```
backend/src/knowledge/
├── vendors/           # Vendor pricing database (our moat)
│   ├── ai_assistants.json
│   ├── automation.json    # n8n, Make, Zapier
│   ├── crm.json
│   ├── scheduling.json
│   └── ...
├── ai_tools/
│   └── llm_providers.json  # Claude, GPT pricing
├── [industry]/             # Per-industry data
│   ├── processes.json      # Common workflows
│   ├── opportunities.json  # AI automation opportunities
│   ├── benchmarks.json     # Industry metrics
│   └── vendors.json        # Relevant software
└── patterns/
    └── ai_implementation_playbook.json
```

### Data Integrity Rules
- **NO MOCK DATA** - Every stat must have verifiable source
- Include: source name, URL, date, `"verified_date": "YYYY-MM"`
- Unverified data: mark `"status": "UNVERIFIED"`, apply LOW confidence, show ⚠️
- Refresh cadence: Vendor pricing monthly, benchmarks quarterly, market size annually

---

## Expertise System (Our Moat)

The agent learns from each analysis to improve future recommendations.

### Learning Loop
```
BEFORE Analysis:
└── Load industry expertise (pain_points, effective_patterns, anti_patterns)

DURING Analysis:
└── Track tools used, errors, phase completion

AFTER Analysis:
└── Update expertise with findings, recommendations, patterns

AFTER User Feedback:
└── Track implementation rates, actual vs estimated ROI

NEXT Analysis:
└── Improved prompts, faster detection, better accuracy
```

### Expertise Data
| Field | Description |
|-------|-------------|
| pain_points | Common issues + frequency + solutions that worked |
| processes | Typical workflows + automation potential |
| effective_patterns | Recommendations that succeeded |
| anti_patterns | What NOT to recommend (learned from failures) |
| size_specific | Insights by company size |
| implementation_rates | Which recs actually get implemented |
| accuracy_tracking | Estimated vs actual ROI |

### Compounding Effect
```
Analysis #1:    Base accuracy
Analysis #100:  +15% ROI accuracy (validated estimates)
Analysis #500:  +25% recommendation hit rate
Analysis #1000: Competitors can't catch up
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

## Positioning

> "We help passion-driven service professionals - from lawyers to plumbers, dentists to dog trainers - get the AI clarity they need to stop wasting time on admin and get back to the work they love."

### What We're NOT
- Not a consulting firm (we're a product)
- Not an AI vendor (we recommend, don't sell)
- Not generic (we're industry-specific)

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
| FSM | Field Service Management software |
| DSO | Dental Service Organization |
| QW | Quick Win (high benefit, low cost/risk) |
