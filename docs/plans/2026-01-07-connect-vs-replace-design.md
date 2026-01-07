# Connect vs Replace: Automation-First Recommendations

**Date:** 2026-01-07
**Status:** Approved
**Replaces:** Phase 2-4 of `docs/handoffs/2026-01-04-ai-automation-layer-design.md`

---

## Overview

Shift CRB Analyser reports from "buy this software" recommendations to "connect what you have vs replace if necessary." This leverages the API openness scoring from Phase 1 to provide genuinely differentiated, actionable recommendations.

### Business Value

- **Differentiation:** Most reports say "use HubSpot." We show Connect vs Replace paths.
- **Actionable:** DIY customers can implement Connect paths themselves.
- **Natural upsell:** Complexity of implementation drives Sprint tier conversions.
- **Trust:** Acknowledging existing stack makes customers feel understood.

---

## Design

### 1. Quiz — Existing Stack Capture

Add a new question after industry/company size:

> **What software does your business currently use?** *(Select all that apply)*

Options are industry-filtered:

| Industry | Options Shown |
|----------|---------------|
| Dental | Open Dental, Dentrix, Eaglesoft, Curve, + generic options |
| Recruiting | Bullhorn, Greenhouse, Lever, Manatal, + generic options |
| All | CRM, Scheduling, Email Marketing, Support, Accounting, Phone/SMS |

Include "Other: [free text]" for unlisted software.

#### Data Model

```sql
-- Add to quiz_sessions table
ALTER TABLE quiz_sessions ADD COLUMN existing_stack JSONB DEFAULT '[]';

-- Structure:
-- [
--   {"slug": "hubspot", "source": "selected"},
--   {"slug": "calendly", "source": "selected"},
--   {"name": "CustomPMS", "source": "free_text", "researched": true, "api_score": 3}
-- ]
```

---

### 2. Unknown Software Research

When user enters software not in our vendor database:

```python
async def research_unknown_software(name: str) -> SoftwareCapabilities:
    """
    Web search to determine API/integration capabilities.

    Searches:
    - "{name} API documentation"
    - "{name} Zapier integration"
    - "{name} webhooks developer"

    Returns:
    - estimated_api_score: 1-5
    - has_api: bool
    - has_webhooks: bool
    - has_zapier: bool
    - reasoning: str (why this score)
    - source_urls: List[str]
    """
```

Results cached in session. Optionally upsert to vendors table as `status: "unverified"` for future use.

---

### 3. Finding Format — Connect vs Replace

Each finding includes both paths:

```markdown
## Finding: High No-Show Rate (18%)

**Impact:** €4,200/month in lost revenue

**Your Stack:** Open Dental (API: 4/5) + Google Calendar (API: 4/5)

---

### Option A: Connect ✓ Recommended

Build automation with your existing tools:

```
Open Dental → n8n → Twilio SMS
      ↓
Claude API (risk scoring)
```

- **What it does:** AI predicts no-show risk, sends personalized reminders
- **Monthly cost:** ~€30 (Twilio + API calls)
- **Setup effort:** 6-8 hours
- **Why this works:** Open Dental's API exposes appointment + patient history

---

### Option B: Replace

Switch to all-in-one solution:

- **Weave:** €250/month
- **Setup:** 2-3 weeks, requires data migration
- **Trade-off:** Less flexible, but zero technical effort

---

### Our Verdict: Connect

Your stack supports automation. Replacing would cost €220/month more
with less customization potential.
```

#### When to Recommend Replace

If existing stack average API score < 3, recommend Replace with reasoning:

```markdown
### Why we recommend switching from Dentrix

- **API Score:** 2/5 (Zapier only, no direct API access)
- **No webhook support** limits real-time automation
- **Cannot build:** predictive no-show alerts, AI-powered scheduling
- **Long-term impact:** You'll hit automation ceilings as you grow

**Recommended alternative:** Open Dental (API: 4/5)
- Full REST API with webhooks
- Enables: custom integrations, AI tools, workflow automation
- Migration effort: ~2-4 weeks
```

#### Recommendation Logic

```python
def get_recommendation(finding: Finding, stack: List[Software]) -> str:
    relevant_tools = get_relevant_tools_for_finding(finding, stack)
    avg_score = mean([t.api_openness_score for t in relevant_tools])

    if avg_score >= 3.5:
        return "CONNECT"  # Strong recommendation
    elif avg_score >= 2.5:
        return "EITHER"   # Show trade-offs equally
    else:
        return "REPLACE"  # Explain why existing limits growth
```

---

### 4. Automation Summary Section

At end of report, aggregate all opportunities:

```markdown
## Your Automation Roadmap

### Stack Assessment

Your software is automation-ready.

| Tool        | API Score |
|-------------|-----------|
| Open Dental | ████████░░ 4/5 |
| Google Cal  | ████████░░ 4/5 |
| Mailchimp   | ██████████ 5/5 |

**Average: 4.3/5** — Strong foundation for automation

---

### Opportunities Identified

| Automation            | Impact/mo | DIY Effort | Approach |
|-----------------------|-----------|------------|----------|
| No-show prevention    | €4,200    | 8 hours    | Connect  |
| Appointment reminders | €1,800    | 4 hours    | Connect  |
| Review requests       | €900      | 3 hours    | Connect  |
| **TOTAL POTENTIAL**   | **€6,900/mo** | **~15 hours** |    |

---

### Next Steps

Each finding above includes step-by-step Connect guides
you can implement yourself.

Need a hand? Book an implementation scope call:
→ [Schedule Call](calendly.com/crb/implementation)
```

#### Tier-Aware Messaging

| Tier | "Next Steps" Message |
|------|---------------------|
| €147 | "Need a hand? Book an implementation scope call" |
| €497 | "Your strategy call is included — we'll discuss implementation" |
| €1,997 | "Your Sprint includes full implementation of these automations" |

---

## Implementation Phases

### Phase 2A: Quiz — Existing Stack Capture
**Effort:** ~4 hours

1. Add `existing_stack` column to `quiz_sessions` table
2. Create industry-specific software options (mapped to vendor slugs)
3. Add "Other" free-text field with validation
4. Update `Quiz.tsx` with multi-select UI component
5. Store selected tools + free-text entries in session

**Files:**
- `backend/supabase/migrations/016_existing_stack.sql`
- `backend/src/routes/quiz.py`
- `frontend/src/pages/Quiz.tsx`

---

### Phase 2B: Unknown Software Research
**Effort:** ~6 hours

1. Create `SoftwareResearchService` with web search
2. Search for API docs, Zapier listings, webhook mentions
3. Use Claude to summarize → estimated API score + reasoning
4. Cache in session, optionally upsert to vendors as "unverified"

**Files:**
- `backend/src/services/software_research_service.py`
- `backend/src/routes/quiz.py` (trigger research on submit)

---

### Phase 2C: Finding Generation — Connect vs Replace
**Effort:** ~8 hours

1. Pass `existing_stack` + API scores to report generation
2. Update finding prompt to generate Connect path (tools, flow, cost, effort)
3. Generate Replace path as alternative
4. Add verdict logic based on average API score
5. Include "why replace" reasoning when score < 3

**Files:**
- `backend/src/services/report_service.py`
- `backend/src/skills/report-generation/finding_generation.py`
- `backend/src/prompts/finding_with_paths.py` (new)

---

### Phase 2D: Automation Summary Section
**Effort:** ~4 hours

1. Create `AutomationSummary` model
2. Aggregate opportunities from findings
3. Calculate total impact + DIY hours
4. Stack assessment with visual scores
5. Tier-aware next steps messaging

**Files:**
- `backend/src/models/report.py`
- `backend/src/skills/report-generation/automation_summary.py` (new)
- `frontend/src/components/report/AutomationRoadmap.tsx` (new)

---

## Dependency Graph

```
Phase 2A (Quiz)
     │
     ▼
Phase 2B (Research)
     │
     ▼
Phase 2C (Findings)
     │
     ▼
Phase 2D (Summary)
```

**Total Effort:** ~22 hours

---

## Success Metrics

- % of reports with Connect recommendations (target: >60%)
- Sprint tier conversion rate from report viewers
- Time-to-implementation for DIY customers (survey)
- Customer feedback: "felt understood" / "actionable recommendations"

---

## Open Questions

1. Should we auto-add researched software to vendor DB for future users?
2. How detailed should Connect paths be? (High-level vs step-by-step)
3. Should we show estimated implementation cost for "Done-For-You"?

---

## Supersedes

This design replaces the original Phase 2-4 from the AI Automation Layer design:
- ~~Phase 2: Create Automation Templates~~ (n8n templates nobody would use)
- ~~Phase 3: Update Recommendation Engine~~ (merged into Phase 2C)
- ~~Phase 4: Report Format Changes~~ (merged into Phase 2C + 2D)
