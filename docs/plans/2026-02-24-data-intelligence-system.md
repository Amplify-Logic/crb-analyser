# Data Intelligence System — Master Improvement Prompt

> **Date**: 2026-02-24
> **Context**: CRB Analyser needs world-class industry databases for Professional Services, Dental, and E-commerce — with auto-updating pipelines that keep data fresh.
> **Vision**: Become the AI Transformation Partner (AITP) for mid-market businesses. The data moat grows with every report. The system must learn, update, and improve autonomously.

---

## THE PROMPT

You are the world's leading expert in AI & Automation potential assessment for SMBs across three verticals: **Professional Services**, **Dental Practices**, and **E-commerce**. You have deep expertise in:

- Every SaaS tool, AI platform, and automation framework relevant to these industries (2024-2026)
- Real-world implementation patterns, failure modes, and ROI benchmarks
- The shift from Era 2 (SaaS + SOPs) to Era 3 (AI Operating Systems + Agentic workflows)
- How Claude Code, MCP servers, and agentic systems are transforming business operations
- Vendor pricing, integration capabilities, and suitability by company size

Your task is to design and populate the data intelligence layer of the CRB Analyser — a system that assesses businesses' AI & automation readiness, recommends specific tools and strategies, and generates implementation roadmaps.

---

### PART 1: INDUSTRY DATABASE POPULATION

For each of the three industries, generate comprehensive, accurate data for these categories:

#### A. Pain Points (10-15 per industry)

For each pain point:
```json
{
  "id": "snake_case_identifier",
  "name": "Human-readable name",
  "frequency": 0.0-1.0,          // How often seen in businesses of this type
  "avg_impact": 1-10,             // Business impact severity
  "typical_causes": ["cause1", "cause2"],
  "effective_solutions": [
    {
      "solution": "Description",
      "tools": ["tool1", "tool2"],
      "implementation_effort": "low|medium|high",
      "time_to_value": "days|weeks|months"
    }
  ],
  "ai_automation_potential": 0.0-1.0,  // How automatable with current AI (Feb 2026)
  "era3_relevance": "How this changes with agentic AI systems"
}
```

**Professional Services** focus areas:
- Client intake & qualification, proposal generation, time tracking & billing
- Document review & creation, compliance monitoring, knowledge management
- Client communication, project scoping, resource allocation, reporting
- CRM data hygiene, lead nurturing, meeting scheduling, follow-ups

**Dental** focus areas:
- Patient scheduling & no-shows, insurance verification & claims
- Treatment plan presentation, patient communication & recalls
- Inventory management, staff scheduling, new patient acquisition
- Clinical documentation, billing & collections, referral management

**E-commerce** focus areas:
- Order processing & fulfillment, inventory forecasting
- Customer support ticket volume, returns/exchanges processing
- Product listing optimization, pricing strategy, abandoned carts
- Email/SMS marketing automation, supplier management, fraud detection

#### B. Processes (8-12 per industry)

For each process:
```json
{
  "id": "snake_case_identifier",
  "process_name": "Name",
  "current_state": "How most businesses handle this today",
  "automation_potential": 0.0-1.0,
  "ai_potential": 0.0-1.0,         // Beyond simple automation — AI judgment needed
  "common_tools_used": ["tool1", "tool2"],
  "best_in_class_tools_2026": ["tool1", "tool2"],  // Current best options
  "common_blockers": ["blocker1", "blocker2"],
  "quick_win_potential": true|false,
  "estimated_hours_saved_monthly": {
    "small": 5-20,     // 1-10 employees
    "medium": 20-80,   // 11-50 employees
    "large": 80-200    // 51-200 employees
  },
  "agentic_opportunity": "How AI agents could handle this end-to-end by 2026-2027"
}
```

#### C. Effective Patterns (5-8 per industry)

Real-world patterns that work. Example format:
```json
{
  "pattern": "Start with customer-facing automation before back-office",
  "why_it_works": "Immediate ROI visibility, builds internal buy-in",
  "typical_roi": "2-4x within 90 days",
  "prerequisites": ["CRM in place", "Basic email marketing"],
  "company_sizes": ["1-10", "11-50"],
  "examples": ["Dental: automated recall → 15% fewer no-shows", "E-com: chatbot → 40% ticket deflection"]
}
```

#### D. Anti-Patterns (5-8 per industry)

What NOT to do:
```json
{
  "anti_pattern": "Automating a broken process",
  "why_it_fails": "Automation amplifies dysfunction — garbage in, garbage out faster",
  "what_to_do_instead": "Map and fix the process first, then automate",
  "real_world_example": "Dental practice automated appointment reminders without fixing scheduling logic — doubled patient confusion"
}
```

#### E. Size-Specific Benchmarks

For each company size segment (1-10, 11-50, 51-200):
```json
{
  "count": "number of businesses analyzed",
  "avg_readiness": 0-100,
  "avg_potential_savings_eur": 0,
  "typical_priorities": ["priority1", "priority2", "priority3"],
  "common_stack": ["tool1", "tool2", "tool3"],
  "avg_monthly_software_spend_eur": 0,
  "biggest_automation_gap": "description",
  "quick_wins": ["win1", "win2"],
  "ai_readiness_blockers": ["blocker1", "blocker2"]
}
```

---

### PART 2: VENDOR INTELLIGENCE (Per Industry)

For each industry, identify the **top 30-50 vendors** across these categories:

| Category | Examples |
|----------|---------|
| CRM | HubSpot, Salesforce, Dentally, Shopify CRM |
| Scheduling | Calendly, Dentrix, Acuity |
| Automation | Zapier, Make, n8n, ActivePieces |
| AI Agents | Claude, ChatGPT, custom agents |
| Communication | Intercom, Front, Podium |
| Industry-Specific | Dentrix, Shopify, Clio, Practice Panther |
| Analytics | Mixpanel, Looker, industry-specific |
| Marketing | Mailchimp, Klaviyo, ActiveCampaign |
| Finance | Xero, QuickBooks, Stripe |

For each vendor:
```json
{
  "slug": "vendor-name",
  "name": "Vendor Name",
  "website": "https://...",
  "category": "crm|scheduling|automation|...",
  "industries": ["dental", "professional-services", "ecommerce"],
  "pricing": {
    "model": "per_seat|flat|usage_based|freemium|custom",
    "currency": "EUR",
    "tiers": [
      {"name": "Free/Starter", "price": 0, "billing": "monthly", "features": ["..."]},
      {"name": "Professional", "price": 49, "billing": "monthly", "features": ["..."]},
      {"name": "Enterprise", "price": null, "billing": "custom", "features": ["..."]}
    ],
    "has_free_tier": true|false
  },
  "company_sizes": ["1-10", "11-50"],
  "integration_score": 1-5,       // API quality, webhooks, Zapier/Make support
  "ai_features": ["feature1"],    // Built-in AI capabilities
  "ai_readiness": 1-5,            // How well it works with external AI/automation
  "strengths": ["..."],
  "weaknesses": ["..."],
  "best_for": "Description of ideal customer",
  "alternatives": ["vendor-slug-1", "vendor-slug-2"],
  "last_verified": "2026-02-24"
}
```

**Critical**: Include integration scores and AI readiness — these are the differentiators for CRB recommendations. A tool with great features but no API is worse than a simpler tool with full API access.

---

### PART 3: AI & AUTOMATION OPPORTUNITY MAP (2026)

For each industry, create a landscape of what's possible NOW vs. what's emerging:

#### Available Now (Feb 2026)
- Proven tools with documented ROI
- Implementation playbooks that work
- Specific vendor combinations that integrate well

#### Emerging (3-6 months)
- AI agent frameworks hitting production (Claude Code + MCP, OpenAI Agents SDK)
- Vertical AI SaaS disrupting incumbents
- New integration patterns (AI middleware)

#### Horizon (6-18 months)
- Full AIOS (AI Operating System) for SMBs
- Autonomous business operations
- AI-first tools replacing legacy SaaS

For each opportunity:
```json
{
  "id": "opportunity_id",
  "title": "Opportunity Name",
  "description": "What it enables",
  "timeline": "now|emerging|horizon",
  "industries": ["dental", "ecommerce", "professional-services"],
  "company_sizes": ["1-10", "11-50", "51-200"],
  "estimated_roi": "2-5x within 6 months",
  "implementation_complexity": "low|medium|high",
  "prerequisites": ["prerequisite1"],
  "recommended_tools": ["tool1", "tool2"],
  "aios_component": "operations|data|intelligence|decisions"
}
```

---

### PART 4: AUTO-UPDATING ARCHITECTURE

Design a system that keeps this data fresh automatically:

#### 4A. Scheduled Vendor Refresh Pipeline
```
CRON (weekly):
  → For each vendor in database:
    → Check if pricing page changed (HTTP ETag/Last-Modified)
    → If changed: Playwright scrape → Claude extraction → diff against stored
    → If significant change (>10% price, new tier, feature change):
      → Auto-update database
      → Flag for human review if change is major (>50% price shift)
      → Log change with timestamp + before/after
    → Update last_verified timestamp
```

#### 4B. Industry Trend Monitor
```
CRON (daily):
  → Search for "[industry] AI automation 2026" across sources:
    → TechCrunch, VentureBeat, industry publications
    → G2, Capterra new tool launches
    → Product Hunt AI category
    → Reddit r/msp, r/dentistry, r/ecommerce
  → Claude extracts: new tools, pricing changes, trend signals
  → Classify: new_vendor | pricing_change | trend | case_study
  → Route to appropriate knowledge base location
  → Daily digest email to admin for review
```

#### 4C. Competitive Intelligence Scraper
```
CRON (bi-weekly):
  → Monitor competitor pricing pages (Morningside AI, other assessment tools)
  → Track new features on G2/Capterra for monitored vendors
  → Detect vendor acquisitions, pivots, shutdowns
  → Update vendor status and notes
```

#### 4D. Report Feedback Loop (Self-Improving)
```
ON_REPORT_GENERATED:
  → SelfImproveService already extracts patterns (KEEP THIS)
  → ADD: Track which vendors were recommended
  → ADD: Track which pain points were identified
  → ADD: Track confidence delta (did we predict correctly?)

ON_WORKSHOP_COMPLETE:
  → Extract: What tools did the client actually use vs. what we assumed?
  → Extract: What pain points did they confirm/deny?
  → Feed corrections back into industry expertise store
  → Update vendor fit scores based on real-world usage
```

#### 4E. Knowledge Base Freshness Scoring
```
FOR each KB entry:
  → Calculate freshness_score:
    → data_age (days since last_updated)
    → source_reliability (human-curated > scraped > AI-generated)
    → confirmation_count (how many reports used this data successfully)
    → contradiction_count (how many times real data differed)
  → freshness_score = (reliability × confirmations) / (age_days × (1 + contradictions))
  → Flag entries below threshold for refresh
  → Prioritize refresh by impact (how often used in reports)
```

---

### PART 5: AIOS INTEGRATION — BECOMING THE TECHNOLOGY PARTNER

This is the strategic layer. The CRB Analyser isn't just an assessment tool — it's the **intelligence engine** of an AI Transformation Partner practice.

#### 5A. Context OS (Liam Ottley's Framework Applied)

Structure the CRB system as a business's Context OS:
```
For each client:
  workspace/
    claude.md            → Client profile summary
    context/
      business.md        → What they do, how they operate
      current_stack.md   → Their existing tools (from quiz/workshop)
      pain_points.md     → Confirmed pain points
      strategy.md        → Their priorities and goals
      data/              → Their metrics (if shared)
    recommendations/
      report.json        → Generated CRB report
      roadmap.md         → Implementation plan
      vendor_shortlist/  → Curated vendor options
    history/
      workshop_transcript.json
      follow_ups/
```

This means every CRB client gets a **persistent AI context** that improves over time. Second reports are smarter than first reports. Follow-up consultations have full history.

#### 5B. Data OS — Unified Intelligence Dashboard

Build aggregated intelligence across ALL clients (anonymized):
- Industry benchmarks based on REAL data (not estimates)
- Tool adoption rates by industry and company size
- Average AI readiness by segment
- Most common pain points (weighted by frequency AND impact)
- Vendor satisfaction signals (recommended → adopted → still using?)

This is the **data moat**. Every report makes the system smarter.

#### 5C. Intelligence OS — Automated Insights

```
DAILY:
  → Scan for industry news affecting clients
  → Check if any recommended vendor had pricing/feature changes
  → Generate proactive alerts: "Your client [X] uses [Vendor Y] which just raised prices 30%"

WEEKLY:
  → Generate industry intelligence brief per vertical
  → Identify cross-client patterns ("3 dental practices this month struggled with same insurance claim issue")
  → Surface new vendor alternatives for commonly recommended tools

MONTHLY:
  → Full industry landscape update
  → Benchmark refresh
  → Trend validation (did our predictions from last month hold?)
```

#### 5D. Decision OS — Recommendation Engine

Evolve from static recommendations to dynamic, confidence-weighted decisions:
```python
def recommend_vendor(industry, pain_point, company_size, budget, existing_stack):
    # 1. Static knowledge base (curated)
    kb_vendors = load_vendor_category(pain_point.category)

    # 2. Expertise store (learned from reports)
    expertise_vendors = get_vendor_patterns(industry, pain_point)

    # 3. Integration compatibility (does it work with their stack?)
    compatible = filter_by_integration(kb_vendors, existing_stack)

    # 4. Freshness-weighted scoring
    scored = score_vendors(compatible, expertise_vendors, freshness_weights)

    # 5. Confidence level
    confidence = calculate_confidence(
        n_analyses=industry_data.total_analyses,
        n_vendor_recommendations=expertise_vendors.count,
        data_age=days_since_last_update
    )

    return RankedRecommendations(vendors=scored, confidence=confidence)
```

---

### PART 6: IMPLEMENTATION PRIORITIES

#### Phase 1 — Data Foundation (Week 1-2)
1. **Populate dental & professional-services pain points/processes** using this prompt's output
2. **Run SelfImproveService backfill** on existing 17 analysis records to populate vendor expertise
3. **Seed vendor knowledge** for all three industries (top 30 per industry)
4. **Add freshness metadata** to all KB entries

#### Phase 2 — Auto-Update Pipeline (Week 3-4)
5. **Build scheduled vendor refresh** (cron job → research agent CLI)
6. **Build trend monitor** (daily web search → Claude extraction → KB update)
7. **Add feedback loop** to report generation (track what's recommended, what's adopted)
8. **Implement freshness scoring** for KB entries

#### Phase 3 — Intelligence Layer (Week 5-8)
9. **Build aggregated benchmarks** from real client data
10. **Create proactive alert system** for vendor changes affecting clients
11. **Implement confidence-weighted recommendations**
12. **Build Context OS per client** (persistent workspace)

#### Phase 4 — AIOS (Month 3+)
13. **Daily intelligence briefs** per industry
14. **Cross-client pattern detection**
15. **Autonomous vendor discovery** (continuously scanning for new tools)
16. **Client-facing dashboard** showing their AI readiness evolution over time

---

### CONSTRAINTS & QUALITY STANDARDS

- All pricing in EUR (convert from USD at current rates)
- All vendor data must include `last_verified` date
- Confidence levels: low (<5 data points), medium (5-20), high (20+)
- Pain point frequency based on industry research, not assumption
- Tool recommendations must account for EU/GDPR compliance
- Integration scores must be verified (check actual API docs, not marketing claims)
- Benchmarks must cite sources or be clearly marked as "estimated from [N] analyses"
- No hallucinated vendor features — if unsure, mark as "unverified"

---

### OUTPUT FORMAT

Generate the complete data as structured JSON files ready to be placed in:
- `backend/src/expertise/data/industries/{industry}.json` — pain points, processes, patterns
- `backend/src/knowledge/{industry}/` — benchmarks, opportunities, processes, vendors
- `backend/src/knowledge/vendors/{category}.json` — vendor details
- `backend/src/knowledge/insights/curated/trends.json` — updated trends

Each file must match the existing schema exactly (see current files for reference).

---

*This prompt is designed to be used with Claude Opus or equivalent frontier model. For best results, process one industry at a time and validate output against real vendor websites before committing to the database.*
