# CRB Analyser - System Architecture

> Last updated: February 2026

This document describes the internal architecture of CRB Analyser — the three-layer intelligence system that powers analysis and report generation.

> For product domain → [PRODUCT.md](../../PRODUCT.md) | For infrastructure → [INFRASTRUCTURE.md](../../INFRASTRUCTURE.md) | For CRB methodology → [FRAMEWORK.md](../../FRAMEWORK.md)

---

## System Overview

CRB Analyser is an AI-native consulting agency that delivers architecture blueprints through:

1. **Quiz** — Adaptive assessment to understand business context
2. **Workshop** — 90-minute AI-assisted deep-dive gathering operational context
3. **Analysis** — AI-powered opportunity identification with CRB scoring
4. **Report** — AIOS recommendations with Connect/Enhance/Add/Replace verdicts

The intelligence behind this comes from three complementary layers:

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 3: SKILLS (Code)                                             │
│  HOW to execute — Reusable workflows, templates, proven code        │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 2: EXPERTISE (Learned Data)                                  │
│  WHAT to look for — Patterns learned from past analyses             │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 1: KNOWLEDGE (Static Data)                                   │
│  Facts and benchmarks — Curated vendor/industry data                │
└─────────────────────────────────────────────────────────────────────┘
```

| Layer | Type | Purpose | Updates |
|-------|------|---------|---------|
| **Knowledge** | Static Data | Facts, benchmarks, vendor pricing | Manually curated + research agents |
| **Expertise** | Learned Data | Patterns from past analyses | Automatic after each analysis |
| **Skills** | Reusable Code | Proven workflows and templates | Developer-maintained |

**Without Skills:** The agent regenerates prompts and logic from scratch each time.
**With Skills:** The agent executes proven code workflows, using expertise as context.

---

## Layer 1: Knowledge Base (Static Data)

**Location:** `backend/src/knowledge/`

Curated, verified data about industries and vendors. This is our data moat — it compounds with every engagement.

### Structure

```
knowledge/
├── vendors/                    # Category-based vendor database
│   ├── ai_assistants.json
│   ├── automation.json         # n8n, Make, Zapier
│   ├── crm.json
│   ├── customer_support.json
│   └── ...
│
├── ai_tools/                   # LLM provider pricing
├── aios/                       # AIOS framework data
├── benchmarks/                 # Cross-industry benchmarks
├── insights/                   # Curated trend data
├── patterns/                   # AI implementation playbooks
├── platforms/                  # Platform integration data
│
├── professional-services/      # Active vertical
├── dental/                     # Active vertical
├── ecommerce/                  # Active vertical
├── b2b-platforms/              # Active vertical
│
├── coaching/                   # Exploratory (not launched)
├── home-services/              # Exploratory (not launched)
├── recruiting/                 # Exploratory (not launched)
└── veterinary/                 # Exploratory (not launched)
```

### Key Functions

```python
from src.knowledge import (
    get_industry_context,      # Load all data for an industry
    get_relevant_opportunities, # Get AI opportunities
    get_vendor_recommendations, # Get matching vendors
    get_benchmarks_for_metrics, # Get industry benchmarks
    search_vendors,            # Search vendor database
)
```

### Data Freshness

All knowledge base data must be verified:

```json
{
  "verified_date": "2026-02",
  "source": "https://...",
  "status": "verified"
}
```

---

## Layer 2: Expertise System (Learned Data)

**Location:** `backend/src/expertise/`

Learns from each analysis to improve future recommendations. This is the compounding engine.

### How It Works

```
Analysis #1 (Dental)
    ↓
SelfImproveService.learn_from_analysis()
    ↓
Updates IndustryExpertise:
- pain_points: {"patient communication": {frequency: 1}}
- effective_patterns: ["CRM integration works well"]
    ↓
Analysis #50 (Dental)
    ↓
Agent now knows:
- Top pain points for dental
- Which recommendations work
- What to avoid (anti-patterns)
```

### Data Structures

```python
class IndustryExpertise:
    industry: str
    total_analyses: int
    confidence: str  # low/medium/high based on count

    pain_points: Dict[str, PainPointPattern]
    processes: Dict[str, ProcessInsight]
    effective_patterns: List[RecommendationPattern]
    anti_patterns: List[str]

    avg_ai_readiness: float
    avg_potential_savings: float

class VendorExpertise:
    vendors: Dict[str, VendorFit]
    category_insights: Dict[str, List[str]]

class ExecutionExpertise:
    tool_success_rates: Dict[str, float]
    failure_patterns: List[str]
    prompt_effectiveness: Dict[str, PromptEffectiveness]
```

### Confidence Levels

| Analyses | Confidence | Meaning |
|----------|------------|---------|
| < 5 | Low | Limited data, use cautiously |
| 5-19 | Medium | Emerging patterns, reasonable confidence |
| 20+ | High | Reliable patterns, use confidently |

---

## Layer 3: Skills System (Reusable Code)

**Location:** `backend/src/skills/`

Skills are reusable code workflows that execute specific tasks consistently.

| Expertise | Skills |
|-----------|--------|
| DATA layer | CODE layer |
| WHAT to look for | HOW to execute |
| Passive (injected into prompts) | Active (executes workflows) |
| Learns automatically | Maintained by developers |

### Structure

```
skills/
├── base.py                         # BaseSkill / SyncSkill classes
├── registry.py                     # Auto-discovery
├── report_generation_utils.py      # Shared report utilities
│
├── analysis/                       # Scoring & validation (16 skills)
│   ├── net_score_calculator.py     # NET SCORE = Benefit - Cost - (Risk/10)
│   ├── math_validator.py           # ROI/financial validation
│   ├── vendor_matching.py          # Match vendors to opportunities
│   ├── platform_consolidation.py   # Stack consolidation analysis
│   ├── roi_calculator.py           # ROI with confidence adjustment
│   ├── ai_readiness_calculator.py  # AI readiness scoring
│   ├── industry_benchmarker.py     # Benchmark comparisons
│   ├── quick_win_identifier.py     # Find quick wins
│   ├── source_validator.py         # Verify data sources
│   └── ...
│
├── report-generation/              # Report output (9 skills)
│   ├── exec_summary.py             # Executive summary
│   ├── four_options.py             # AIOS options (Connect/Enhance/Add/Replace)
│   ├── three_options.py            # Legacy 3-option format (fallback)
│   ├── automation_summary.py       # Automation roadmap
│   ├── system_architecture.py      # AIOS architecture diagram
│   ├── verdict.py                  # Final verdict generation
│   ├── roadmap.py                  # Implementation roadmap
│   └── finding_generation.py       # Finding structure
│
├── browser/                        # Web scraping (3 skills)
│   ├── playwright_browser.py       # Core browser automation
│   ├── enhanced_scraper.py         # Playwright + httpx fallback
│   └── vendor_scraper.py           # Vendor pricing extraction
│
├── workshop/                       # AI-assisted workshop (3 skills)
│   ├── question_skill.py           # Adaptive questions
│   ├── signal_detector.py          # Detect buying signals
│   └── milestone_skill.py          # Track workshop progress
│
├── interview/                      # Interview phase
│   ├── followup.py                 # Adaptive follow-ups
│   ├── extraction.py               # Pain point extraction
│   └── probing.py                  # Deep-dive questions
│
├── extraction/                     # Data extraction
│   └── insight_extraction.py       # Extract insights from analysis
│
└── industry/                       # Industry-specific skills
    ├── dental/
    └── ...
```

### Skill Anatomy

```python
class ExecSummarySkill(SyncSkill):
    name = "executive-summary"
    description = "Generate compelling executive summaries"

    def execute(self, report_data: dict, expertise: IndustryExpertise = None):
        # Proven template structure
        hook = self._generate_hook(report_data)
        return {
            "headline": hook,
            "key_insight": self._extract_key_insight(report_data),
            "scores": self._format_scores(report_data),
            "verdict_summary": self._summarize_verdict(report_data)
        }
```

---

## How the Layers Work Together

### Analysis Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BEFORE ANALYSIS                             │
├─────────────────────────────────────────────────────────────────────┤
│  Knowledge provides:           Expertise provides:                  │
│  • Industry benchmarks         • Known pain points                  │
│  • Vendor database             • Effective patterns                 │
│  • Process templates           • Anti-patterns to avoid             │
│                                                                     │
│  Skills loaded:                                                     │
│  • workshop/question_skill.py  • analysis/net_score_calculator.py  │
│  • report-generation/*.py      • analysis/vendor_matching.py       │
└────────────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DURING ANALYSIS                             │
├─────────────────────────────────────────────────────────────────────┤
│  Workshop Phase:                                                    │
│  • Skill: workshop/question_skill.py generates adaptive questions   │
│  • Skill: workshop/signal_detector.py detects buying signals        │
│  • Expertise: Injects known pain points to probe                    │
│                                                                     │
│  Finding Generation:                                                │
│  • Skill: report-generation/finding_generation.py structures output │
│  • Expertise: Calibrates scores to industry averages                │
│  • Knowledge: Provides benchmark data                               │
│                                                                     │
│  Recommendation Generation:                                         │
│  • Skill: report-generation/four_options.py formats AIOS options    │
│  • Skill: analysis/net_score_calculator.py computes NET SCORE       │
│  • Expertise: Uses effective_patterns for proven recommendations    │
│  • Knowledge: Pulls vendor pricing                                  │
└────────────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         AFTER ANALYSIS                              │
├─────────────────────────────────────────────────────────────────────┤
│  SelfImproveService.learn_from_analysis():                          │
│  • Updates IndustryExpertise with new pain points                   │
│  • Records which vendors were recommended                           │
│  • Tracks tool success rates                                        │
│  • Optional LLM reflection for deeper insights                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Code Example: Integrated Flow

```python
async def generate_report(self):
    # LAYER 1: Load knowledge
    industry_knowledge = get_industry_context(self.industry)

    # LAYER 2: Load expertise
    expertise = get_expertise_store().get_industry_expertise(self.industry)

    # LAYER 3: Load and execute skills
    exec_summary_skill = load_skill("report-generation/exec-summary")

    # Skills execute with knowledge + expertise context
    executive_summary = exec_summary_skill.execute(
        report_data=self.context,
        expertise=expertise,
        knowledge=industry_knowledge
    )

    # After analysis: Update expertise (compounding loop)
    await get_self_improve_service().learn_from_analysis(
        audit_id=self.audit_id,
        industry=self.industry,
        ...
    )
```

---

## Related Documents

- [CLAUDE.md](../../CLAUDE.md) — Development guide
- [PRODUCT.md](../../PRODUCT.md) — Product domain, verticals, user journey
- [INFRASTRUCTURE.md](../../INFRASTRUCTURE.md) — Deployment, services, operations
- [FRAMEWORK.md](../../FRAMEWORK.md) — CRB methodology, AIOS options, scoring
- [SKILLS_STRATEGY.md](./SKILLS_STRATEGY.md) — Skills design philosophy
- [SKILLS_INTEGRATION_MAP.md](./SKILLS_INTEGRATION_MAP.md) — How skills connect to services
