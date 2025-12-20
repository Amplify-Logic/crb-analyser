# Enhanced Report System Design

**Date:** 2025-12-20
**Status:** Approved
**Goal:** Transform CRB reports from static analysis into actionable, interactive implementation guides

---

## Executive Summary

Enhance the CRB Analyser report with four major features that increase value and drive action:

1. **Personalized Playbooks** - Week-by-week implementation guides tailored to quiz responses
2. **System Architecture (Stack)** - Visual blueprints showing how AI/automation connects to existing tools
3. **Industry Insights** - What's working in their industry + opportunity mapping
4. **Live ROI Calculator** - Interactive what-if scenarios with real-time recalculation

All features reinforce the CRB (Cost/Risk/Benefit) framework throughout.

---

## Design Details

### 1. Personalized Playbooks

#### Data Model

```python
class Playbook(BaseModel):
    recommendation_id: str
    option_type: Literal["off_the_shelf", "best_in_class", "custom_solution"]
    total_weeks: int  # 6-16 weeks depending on option
    phases: list[Phase]
    personalization_context: PersonalizationContext

class Phase(BaseModel):
    title: str  # "Automate Customer Support"
    phase_number: int
    duration_weeks: int
    outcome: str  # "80% of inquiries handled automatically"
    crb_summary: CRBSummary
    weeks: list[Week]

class Week(BaseModel):
    week_number: int
    theme: str  # "Setup & Foundation"
    tasks: list[Task]
    checkpoint: str  # "Bot answering basic FAQs"

class Task(BaseModel):
    id: str
    title: str  # "Sign up for Intercom"
    description: str
    time_estimate_minutes: int
    difficulty: Literal["easy", "medium", "hard"]
    executor: Literal["owner", "team", "hire_out"]
    tools: list[str]  # ["intercom", "slack"]
    tutorial_hint: Optional[str]
    crb: TaskCRB
    completed: bool = False
    completed_at: Optional[datetime]

class TaskCRB(BaseModel):
    cost: str  # "€0 (free tier)"
    risk: Literal["low", "medium", "high"]
    benefit: str  # "Saves 2 hrs/week"

class CRBSummary(BaseModel):
    total_cost: str
    monthly_cost: str
    setup_hours: int
    risks: list[str]
    benefits: list[str]
    crb_score: float  # 0-10

class PersonalizationContext(BaseModel):
    team_size: Literal["solo", "small", "medium", "large"]
    technical_level: int  # 1-5
    budget_monthly: int
    existing_tools: list[str]
    primary_pain_point: str
    industry: str
    urgency: Literal["asap", "normal", "flexible"]
```

#### Personalization Logic

| Quiz Data | Playbook Adaptation |
|-----------|---------------------|
| Team size (1, 2-5, 6-20, 20+) | Sets executor defaults. Solo = "you". 6+ = "assign to ops lead" |
| Current tools | Skips setup steps for existing tools. Adds integration tasks instead |
| Technical comfort (1-5) | Easy = more hand-holding. Technical = link to docs |
| Budget range | Filters vendor suggestions. Flags "hire out" for budget-appropriate |
| Biggest pain points | Orders phases by impact. #1 pain = Week 1 priority |
| Industry | Injects industry-specific tips |
| Timeline urgency | Compresses or expands durations |

#### Playbook Speeds

- **ASAP mode**: 6-8 weeks, aggressive, parallel tasks where possible
- **Normal mode**: 10-12 weeks, sustainable pace
- **Flexible mode**: 14-16 weeks, buffer for learning

---

### 2. System Architecture (Stack Tab)

#### Data Model

```python
class SystemArchitecture(BaseModel):
    report_id: str
    existing_tools: list[ToolNode]
    ai_layer: list[ToolNode]
    automations: list[AutomationNode]
    connections: list[Connection]
    cost_comparison: CostComparison

class ToolNode(BaseModel):
    id: str
    name: str  # "Claude Sonnet 4.5"
    category: str  # "ai_brain", "existing", "automation"
    monthly_cost: float
    one_time_cost: float
    crb: NodeCRB
    position: Position  # For diagram layout

class NodeCRB(BaseModel):
    cost: str
    risk: str
    risk_level: Literal["low", "medium", "high"]
    benefit: str
    powers: list[str]  # ["Lead scoring", "Support bot"]

class Connection(BaseModel):
    from_node: str
    to_node: str
    data_flow: str  # "Customer inquiries"
    integration_type: str  # "API", "Webhook", "Zapier"

class AutomationNode(BaseModel):
    id: str
    name: str  # "Lead Score Auto-tag"
    trigger: str  # "New lead in HubSpot"
    action: str  # "Score with Claude, tag in CRM"
    tools_used: list[str]

class CostComparison(BaseModel):
    saas_route: CostBreakdown
    diy_route: CostBreakdown
    monthly_savings: float
    savings_percentage: float
    build_cost: float
    breakeven_months: float

class CostBreakdown(BaseModel):
    items: list[CostItem]
    total_monthly: float

class CostItem(BaseModel):
    name: str
    monthly_cost: float
    category: str  # "saas" or "diy"
```

#### Toggle Views

- **SaaS Route**: Shows recommended SaaS tools with subscription costs
- **DIY Route**: Shows build-it-yourself with API costs + one-time build
- Both show same automations/outcomes, different implementation paths

---

### 3. Industry Insights

#### Data Model

```python
class IndustryInsights(BaseModel):
    industry: str
    adoption_stats: list[AdoptionStat]
    opportunity_map: OpportunityMap
    social_proof: list[SocialProof]

class AdoptionStat(BaseModel):
    capability: str  # "Content automation"
    adoption_percentage: int  # 62
    average_outcome: str  # "12 hrs/week saved"
    crb: InsightCRB

class InsightCRB(BaseModel):
    typical_cost: str  # "€50-200/mo"
    risk_level: Literal["low", "medium", "high"]
    typical_benefit: str  # "12 hrs/wk saved"

class OpportunityMap(BaseModel):
    emerging: list[str]  # Early wins, less proven
    growing: list[str]  # Sweet spot, high impact
    established: list[str]  # Table stakes
    best_fit: str  # "growing"
    rationale: str

class SocialProof(BaseModel):
    quote: str
    company_description: str  # "8-person agency, similar size"
    outcome: str
```

#### Tone Guidelines

- Focus on "What's working" not "What you're missing"
- "Opportunity map" not "competitive position"
- Show paths to success, not fear of falling behind
- Social proof from similar businesses (size, industry)

---

### 4. Live ROI Calculator

#### Data Model

```python
class ROICalculator(BaseModel):
    report_id: str
    inputs: ROIInputs
    results: ROIResults  # Computed
    scenarios: list[SavedScenario]

class ROIInputs(BaseModel):
    hours_weekly: float  # Pre-filled from quiz
    hourly_rate: float
    automation_rate: float  # 0.5-0.9 slider
    implementation_approach: Literal["diy", "saas", "freelancer"]

class ROIResults(BaseModel):
    # Time
    hours_saved_weekly: float
    hours_saved_monthly: float
    hours_saved_yearly: float

    # Cost
    implementation_cost: float  # One-time
    monthly_cost: float  # Ongoing

    # Benefit
    monthly_savings: float
    yearly_savings: float

    # Analysis
    roi_percentage: float
    breakeven_months: float
    three_year_net: float

    # CRB Display
    crb_summary: CalculatorCRB

class CalculatorCRB(BaseModel):
    cost_display: str  # "€150/mo + €2,400 build"
    risk_display: str  # "Low (proven pattern)"
    risk_bar: float  # 0-1 for visual
    benefit_display: str  # "€3,150/mo saved"
    time_benefit: str  # "10.5 hrs/wk freed"

class SavedScenario(BaseModel):
    id: str
    name: str  # "Conservative" / "Aggressive"
    inputs: ROIInputs
    results: ROIResults
    created_at: datetime
```

#### Interactive Features

- Sliders update results in real-time (client-side calculation)
- Toggle DIY/SaaS/Freelancer to compare approaches
- Save scenarios for comparison
- "Add to Plan" links scenario to playbook

---

### 5. AI Model Recommendations

#### Current Models (Dec 2025)

| Model | Best For | API Cost (1M tokens) | When to Recommend |
|-------|----------|---------------------|-------------------|
| Claude Opus 4.5 | Complex agents, coding | $5 / $25 | High-complexity custom builds |
| Claude Sonnet 4.5 | Coding, daily driver | $3 / $15 | Default recommendation |
| Gemini 3 Pro | Math, research, multimodal | $2 / $12 | Data analysis, long context |
| Gemini 3 Flash | Fast, cheap, quality | $0.50 / $3 | Budget builds, high volume |
| GPT-5.2 | Reasoning, writing | $1.25 / $10 | Content generation |
| DeepSeek V3.2 | Budget builds | Cheapest | Cost-sensitive clients |

#### Model Freshness System

```python
# Weekly job (Sunday night)
class ModelFreshnessJob:
    sources = [
        "ai.google.dev/pricing",
        "anthropic.com/pricing",
        "openai.com/pricing",
        "lmarena.ai",  # Benchmark Elo
        "artificialanalysis.ai"  # Speed benchmarks
    ]

    def run(self):
        current = load_knowledge_base()
        scraped = scrape_all_sources()

        changes = []
        for model in scraped:
            if price_changed(model, current, threshold=0.10):  # >10%
                changes.append(Change("price", model))
            if new_model(model, current):
                changes.append(Change("new_model", model))
            if benchmark_shifted(model, current):
                changes.append(Change("benchmark", model))
            if deprecated(model, current):
                changes.append(Change("deprecated", model))

        if changes:
            send_notification(changes)  # Email/Slack
            create_admin_review(changes)

# Admin dashboard
# - Review each change
# - One-click approve → Updates knowledge base
# - Dismiss → Ignores until next significant change

# Future (Phase C)
# - Auto-approve price changes < 20%
# - Auto-approve benchmark shifts if ranking unchanged
# - Only flag major events (new model, deprecation)
```

---

### 6. CRB Integration

CRB (Cost/Risk/Benefit) appears consistently throughout:

#### Task Level
```
☐ Set up Claude API for lead scoring
  ⏱ 45 min  │  💰 €0 (free tier)  │  ⚠️ Low  │  📈 High
            │     COST            │   RISK   │   BENEFIT
```

#### Phase Level
```
PHASE 2: Lead Scoring System
────────────────────────────────────
COST        │ RISK           │ BENEFIT
€70/mo      │ Low            │ 2x conversion
8 hrs setup │ • API learning │ €4,200/mo revenue
            │ • Data quality │ 5 hrs/week saved

CRB Score: ████████░░ 8.2/10
```

#### Stack Level
Each node shows CRB on click/hover. Total stack CRB summarized.

#### ROI Calculator
Explicit CRB columns in results display.

#### New Chart: CRB Portfolio
```
Benefit ▲
        │         ● Lead Scoring (High B, Low R, Med C)
        │    ● Support Bot (High B, Low R, Low C)
        │              ○ Custom Analytics (Med B, High R, High C)
        └──────────────────────────────────────▶ Risk
          Low            Medium           High

Circle size = Cost    ● Do first   ○ Consider later
```

---

### 7. UI Structure

#### Report Tabs (Web App)

```
[Summary] [Findings] [Recommendations] [Playbook] [Stack] [ROI] [Insights]
```

#### Playbook Tab
- Phase accordion (expandable)
- Week-by-week task lists
- Interactive checkboxes (persisted to DB)
- Progress bar at top
- Filter by executor (Owner/Team/Hire Out)

#### Stack Tab
- Interactive diagram (click nodes for details)
- Toggle: SaaS Route / DIY Route
- Cost comparison table
- "Share with Developer" export button

#### ROI Tab
- Input sliders (pre-filled from quiz)
- Live-updating results
- Scenario save/compare
- "Add to Plan" action

#### Insights Tab
- Adoption statistics (horizontal bars)
- Opportunity map (Emerging/Growing/Established)
- Social proof cards

---

### 8. PDF Export

Summary versions included in PDF export:

- **Playbook**: Phase overview + first 2 weeks detail
- **Stack**: Static diagram + cost comparison table
- **ROI**: Default scenario results
- **Insights**: Key stats + opportunity summary

Full interactive versions remain web-only.

---

### 9. Database Changes

#### New Tables

```sql
-- Playbook progress tracking
CREATE TABLE playbook_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID REFERENCES reports(id),
    task_id TEXT NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMPTZ,
    completed_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(report_id, task_id)
);

-- ROI scenarios
CREATE TABLE roi_scenarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID REFERENCES reports(id),
    name TEXT NOT NULL,
    inputs JSONB NOT NULL,
    results JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Model freshness tracking
CREATE TABLE model_updates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_slug TEXT NOT NULL,
    change_type TEXT NOT NULL,  -- 'price', 'new', 'benchmark', 'deprecated'
    old_value JSONB,
    new_value JSONB,
    status TEXT DEFAULT 'pending',  -- 'pending', 'approved', 'dismissed'
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 10. Implementation Priority

| Phase | Feature | Effort | Value | Dependencies |
|-------|---------|--------|-------|--------------|
| 1 | Playbook generation + UI | 2-3 weeks | Highest | None |
| 2 | Stack diagram + DIY costs | 2 weeks | High | Phase 1 |
| 3 | ROI calculator (interactive) | 1-2 weeks | High | None |
| 4 | Industry insights | 1 week | Medium | Knowledge base |
| 5 | Model freshness system | 1 week | Long-term | Admin dashboard |
| 6 | CRB portfolio chart | 3 days | Medium | Chart service |
| 7 | PDF export enhancements | 1 week | Medium | Phases 1-4 |

---

## Success Metrics

- **Playbook engagement**: % of tasks marked complete
- **Time in report**: Average session duration (target: 5+ min)
- **ROI calculator usage**: % of reports with saved scenarios
- **Return visits**: Users coming back to check playbook progress
- **PDF downloads**: Conversion from view to download

---

## Open Questions (Resolved)

1. ~~Playbook detail level~~ → Phase + week-by-week (fast-paced)
2. ~~Personalization depth~~ → Quiz-response tailored, growing to fully custom
3. ~~Competitive framing~~ → Inspiring "what's working", not fear-based
4. ~~Model recommendations~~ → Claude primary, Gemini 3 Flash budget option
5. ~~Freshness automation~~ → Semi-automated with review, growing to auto

---

## Appendix: Model Pricing (Dec 2025)

| Model | Input/1M | Output/1M | Notes |
|-------|----------|-----------|-------|
| Claude Opus 4.5 | $5 | $25 | Best coding, 30hr autonomous |
| Claude Sonnet 4.5 | $3 | $15 | Sweet spot |
| Gemini 3 Pro | $2 | $12 | Best math, 1501 Elo |
| Gemini 3 Flash | $0.50 | $3 | NEW Dec 17, 4x cheaper |
| GPT-5.2 | $1.25 | $10 | Best writing |
| DeepSeek V3.2 | ~$0.14 | ~$0.28 | Budget king |

Sources: [Google](https://blog.google/products/gemini/gemini-3-flash/), [LM Council](https://lmcouncil.ai/benchmarks), [IntuitionLabs](https://intuitionlabs.ai/articles/llm-api-pricing-comparison-2025)
