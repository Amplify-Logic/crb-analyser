# CRB Analyser - Product Domain

> This document describes WHAT the product does and its domain model.
> For HOW to develop, see [CLAUDE.md](./CLAUDE.md).
> For WHY we're building this, see [STRATEGY.md](./STRATEGY.md).

---

## Product Overview

**CRB Analyser** delivers AI-powered Cost/Risk/Benefit analysis for businesses considering AI implementation. We help passion-driven service professionals get clarity on AI opportunities without expensive consultants.

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

## Two Pillars Assessment (2P)

Each finding is scored on two dimensions:

| Pillar | Question | Score |
|--------|----------|-------|
| **Customer Value** | How does this help their customers? | 1-10 |
| **Business Health** | How does this strengthen the business? | 1-10 |

### Prioritization Matrix
- High on both → **Urgent** (do first)
- High on one → **Important** (do soon)
- Low on both → **Deprioritize** (do later or never)

---

## Confidence & ROI

### Confidence Levels

| Level | Distribution | Factor | Criteria |
|-------|-------------|--------|----------|
| HIGH | ~30% | 1.0 | Quiz directly mentions issue, multiple data points, user-provided numbers |
| MEDIUM | ~50% | 0.85 | Quiz implies issue, industry pattern likely applies, one strong data point |
| LOW | ~20% | 0.70 | Industry pattern suggests possibility, significant assumptions required |

### ROI Calculation
```python
adjusted_roi = base_roi * confidence_factor
# HIGH:   10000 * 1.0  = 10000
# MEDIUM: 10000 * 0.85 = 8500
# LOW:    10000 * 0.70 = 7000
```

### Display Rules
- Always show "**Estimated** ROI" - never claim certainty
- Show confidence level visibly
- List key assumptions
- If everything is HIGH confidence, we're not being honest about uncertainty

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
| 3O | Three Options model |
| 2P | Two Pillars (Customer Value + Business Health) |
| ROI-CA | ROI Confidence-Adjusted |
| KB | Knowledge Base |
| PM | Practice Management software |
| FSM | Field Service Management software |
| DSO | Dental Service Organization |
