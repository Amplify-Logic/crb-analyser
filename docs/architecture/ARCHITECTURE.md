# CRB Analyser - System Architecture

> Last updated: December 2025

This document describes the core architecture of CRB Analyser, focusing on the three-layer intelligence system that powers analysis and report generation.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [The Three-Layer Intelligence System](#the-three-layer-intelligence-system)
3. [Layer 1: Knowledge Base (Static Data)](#layer-1-knowledge-base-static-data)
4. [Layer 2: Expertise System (Learned Data)](#layer-2-expertise-system-learned-data)
5. [Layer 3: Skills System (Reusable Code)](#layer-3-skills-system-reusable-code)
6. [How the Layers Work Together](#how-the-layers-work-together)
7. [Data Flow](#data-flow)
8. [Directory Structure](#directory-structure)

---

## System Overview

CRB Analyser is an AI-powered Cost/Risk/Benefit analysis platform. It helps businesses understand where AI can add value through:

1. **Quiz/Interview** - Collect business context
2. **Analysis** - AI-powered opportunity identification
3. **Report** - Actionable recommendations with ROI

The intelligence behind this comes from three complementary layers:

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  LAYER 3: SKILLS (Code)                                             │
│  HOW to execute - Reusable workflows, templates, proven code        │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  LAYER 2: EXPERTISE (Learned Data)                                  │
│  WHAT to look for - Patterns learned from past analyses             │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  LAYER 1: KNOWLEDGE (Static Data)                                   │
│  Facts and benchmarks - Curated vendor/industry data                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## The Three-Layer Intelligence System

### Why Three Layers?

Each layer serves a distinct purpose:

| Layer | Type | Purpose | Updates |
|-------|------|---------|---------|
| **Knowledge** | Static Data | Facts, benchmarks, vendor pricing | Manually curated |
| **Expertise** | Learned Data | Patterns from past analyses | Automatic after each analysis |
| **Skills** | Reusable Code | Proven workflows and templates | Developer-maintained |

### The Key Insight

From the video ["MCP Is Dead (Here's the Skills Replacement)"](https://www.youtube.com/watch?v=...):

> "Skills are a way to take something that the agent has figured out through open-ended code execution and turn it into a reusable building block."

**Without Skills:** The agent regenerates prompts and logic from scratch each time.
**With Skills:** The agent executes proven code workflows, using expertise as context.

---

## Layer 1: Knowledge Base (Static Data)

**Location:** `backend/src/knowledge/`

The Knowledge Base contains curated, verified data about industries and vendors.

### Structure

```
knowledge/
├── vendors/                    # Category-based vendor database
│   ├── ai_assistants.json
│   ├── automation.json         # n8n, Make, Zapier
│   ├── crm.json
│   ├── customer_support.json
│   ├── scheduling.json
│   └── ...
│
├── ai_tools/
│   └── llm_providers.json      # Claude, GPT pricing
│
├── dental/                     # Industry-specific
│   ├── processes.json          # Common workflows
│   ├── opportunities.json      # AI automation opportunities
│   ├── benchmarks.json         # Industry metrics
│   └── vendors.json            # Industry-relevant vendors
│
├── home-services/
├── professional-services/
├── recruiting/
├── coaching/
└── veterinary/
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
  "verified_date": "2025-12",
  "source": "https://...",
  "status": "verified"
}
```

---

## Layer 2: Expertise System (Learned Data)

**Location:** `backend/src/expertise/`

The Expertise System learns from each analysis to improve future recommendations.

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
# IndustryExpertise - Per-industry learning
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

# VendorExpertise - Cross-industry vendor learning
class VendorExpertise:
    vendors: Dict[str, VendorFit]  # What works for which use cases
    category_insights: Dict[str, List[str]]

# ExecutionExpertise - How the agent performs
class ExecutionExpertise:
    tool_success_rates: Dict[str, float]
    failure_patterns: List[str]
    prompt_effectiveness: Dict[str, PromptEffectiveness]
```

### Key Functions

```python
from src.expertise import (
    get_expertise_store,        # Get/save expertise files
    get_self_improve_service,   # Learning engine
)

# Before analysis: Load expertise
store = get_expertise_store()
expertise = store.get_all_expertise_context("dental")

# After analysis: Learn
service = get_self_improve_service()
await service.learn_from_analysis(audit_id, industry, ...)
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

### Key Distinction

| Expertise | Skills |
|-----------|--------|
| DATA layer | CODE layer |
| WHAT to look for | HOW to execute |
| Passive (injected into prompts) | Active (executes workflows) |
| Learns automatically | Maintained by developers |

### Structure

```
skills/
├── __init__.py                 # Skill loader
├── base.py                     # BaseSkill class
├── registry.py                 # Skill discovery
│
├── report-generation/          # Report skills
│   ├── skill.md                # Documentation
│   ├── exec_summary.py         # Executive summary generator
│   ├── three_options.py        # Three Options formatter
│   └── pdf_layout.py           # PDF generation
│
├── finding-generation/         # Finding skills
│   ├── skill.md
│   ├── structure.py            # Consistent finding format
│   ├── scoring.py              # Two Pillars scoring
│   └── confidence.py           # Confidence assignment
│
├── interview/                  # Interview skills
│   ├── skill.md
│   ├── followup.py             # Adaptive follow-ups
│   ├── extraction.py           # Pain point extraction
│   └── probing.py              # Deep-dive questions
│
└── industry/                   # Industry-specific skills
    ├── dental/
    │   ├── skill.md
    │   └── analysis.py
    └── home-services/
        ├── skill.md
        └── analysis.py
```

### Skill Anatomy

Each skill contains:

1. **skill.md** - When to use, how it works
2. **Scripts** - Python code that executes the workflow
3. **Templates** - Reusable output formats
4. **Examples** - Reference implementations

```python
# Example: skills/report-generation/exec_summary.py

class ExecSummarySkill(BaseSkill):
    name = "executive-summary"
    description = "Generate compelling executive summaries"

    def execute(self, report_data: dict, expertise: IndustryExpertise = None):
        """
        Generate executive summary using proven structure.

        Args:
            report_data: Full report context
            expertise: Optional industry expertise for calibration
        """
        # Proven template structure
        hook = self._generate_hook(report_data)
        comparison = self._generate_comparison(expertise)

        return {
            "headline": hook,
            "key_insight": self._extract_key_insight(report_data),
            "scores": self._format_scores(report_data, comparison),
            "verdict_summary": self._summarize_verdict(report_data)
        }
```

### Benefits of Skills

1. **Consistency** - Same output format every time
2. **Efficiency** - No regenerating logic from scratch
3. **Token Reduction** - ~50% fewer tokens per report
4. **Maintainability** - Change in one place, affects all reports

---

## How the Layers Work Together

### Analysis Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BEFORE ANALYSIS                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Knowledge provides:           Expertise provides:                  │
│  • Industry benchmarks         • Known pain points                  │
│  • Vendor database             • Effective patterns                 │
│  • Process templates           • Anti-patterns to avoid             │
│                                                                     │
│  Skills loaded:                                                     │
│  • interview/followup.py       • finding-generation/structure.py   │
│  • report-generation/*.py                                           │
│                                                                     │
└────────────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DURING ANALYSIS                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Interview Phase:                                                   │
│  • Skill: interview/followup.py generates adaptive questions        │
│  • Expertise: Injects known pain points to probe                    │
│                                                                     │
│  Finding Generation:                                                │
│  • Skill: finding-generation/structure.py ensures consistent format │
│  • Expertise: Calibrates scores to industry averages                │
│  • Knowledge: Provides benchmark data                               │
│                                                                     │
│  Recommendation Generation:                                         │
│  • Skill: report-generation/three_options.py formats options        │
│  • Expertise: Uses effective_patterns for proven recommendations    │
│  • Knowledge: Pulls vendor pricing                                  │
│                                                                     │
└────────────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         AFTER ANALYSIS                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SelfImproveService.learn_from_analysis():                          │
│  • Updates IndustryExpertise with new pain points                   │
│  • Records which vendors were recommended                           │
│  • Tracks tool success rates                                        │
│  • Optional LLM reflection for deeper insights                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Code Example: Integrated Flow

```python
# In report_service.py

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

    # After analysis: Update expertise
    await get_self_improve_service().learn_from_analysis(
        audit_id=self.audit_id,
        industry=self.industry,
        ...
    )
```

---

## Data Flow

```
                    ┌─────────────────┐
                    │   User Input    │
                    │  (Quiz/Interview)│
                    └────────┬────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │      ReportGenerator         │
              │                              │
              │  ┌────────────────────────┐  │
              │  │  Load Context          │  │
              │  │  • Knowledge (static)  │  │
              │  │  • Expertise (learned) │  │
              │  │  • Skills (code)       │  │
              │  └───────────┬────────────┘  │
              │              │               │
              │              ▼               │
              │  ┌────────────────────────┐  │
              │  │  Execute Skills        │  │
              │  │  • Interview skill     │  │
              │  │  • Finding skill       │  │
              │  │  • Report skills       │  │
              │  └───────────┬────────────┘  │
              │              │               │
              └──────────────┼───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │    SelfImproveService        │
              │    (Learn from analysis)     │
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │    Updated Expertise         │
              │    (Better next time)        │
              └──────────────────────────────┘
```

---

## Directory Structure

```
backend/
├── src/
│   ├── knowledge/              # LAYER 1: Static Data
│   │   ├── __init__.py         # Loaders and helpers
│   │   ├── schemas.py          # Data models
│   │   ├── vendors/            # Vendor database (by category)
│   │   ├── ai_tools/           # LLM provider pricing
│   │   ├── dental/             # Industry: Dental
│   │   ├── home-services/      # Industry: Home Services
│   │   ├── professional-services/
│   │   ├── recruiting/
│   │   ├── coaching/
│   │   └── veterinary/
│   │
│   ├── expertise/              # LAYER 2: Learned Data
│   │   ├── __init__.py         # Exports
│   │   ├── schemas.py          # IndustryExpertise, VendorExpertise, etc.
│   │   ├── store.py            # File-based persistence
│   │   ├── self_improve.py     # Learning engine
│   │   └── data/               # Expertise files (auto-generated)
│   │       ├── industries/     # Per-industry expertise
│   │       ├── vendors.json    # Vendor learning
│   │       ├── execution.json  # Execution learning
│   │       └── records/        # Analysis records
│   │
│   ├── skills/                 # LAYER 3: Reusable Code
│   │   ├── __init__.py         # Skill loader
│   │   ├── base.py             # BaseSkill class
│   │   ├── registry.py         # Skill discovery
│   │   ├── report-generation/  # Report skills
│   │   ├── finding-generation/ # Finding skills
│   │   ├── interview/          # Interview skills
│   │   └── industry/           # Industry-specific skills
│   │
│   ├── services/               # Business logic
│   │   ├── report_service.py   # Main report generator
│   │   ├── playbook_generator.py
│   │   └── ...
│   │
│   └── routes/                 # API endpoints
│       ├── reports.py
│       ├── interview.py
│       └── ...
│
└── docs/
    ├── ARCHITECTURE.md         # This document
    └── ...
```

---

## Related Documents

- [CLAUDE.md](../CLAUDE.md) - Development guide and shortcuts
- [TARGET_INDUSTRIES.md](TARGET_INDUSTRIES.md) - Industry prioritization
- [plans/](plans/) - Implementation plans

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-25 | Initial architecture document - Skills + Expertise integration |
