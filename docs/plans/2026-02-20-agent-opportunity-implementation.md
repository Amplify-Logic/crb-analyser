# Implementation Plan: Agent Opportunity in E-commerce Reports

> **Design doc:** `docs/plans/2026-02-19-product-evolution-design.md`
> **Scope:** Add "Agent Opportunity" section to e-commerce report findings
> **Context reset safe:** Yes — all file paths, schemas, and code examples included

---

## Overview

When a CRB report is generated for an e-commerce client, each relevant finding should include an optional "Agent Opportunity" section. This section describes what a CRB-managed agent could do for this finding — estimated impact, deployment timeline, and prerequisites.

This is the upsell mechanism: the report identifies the opportunity, the agent opportunity section says "we can deploy this for you."

---

## Task 1: Add AgentOpportunity Model (Backend)

**File:** `backend/src/models/recommendation.py`
**After line 182** (after `ValueCreated` class, before `Finding` class)

Add this new model:

```python
class AgentOpportunity(BaseModel):
    """What a CRB-managed agent could automate for this finding."""
    agent_type: str = Field(..., description="e.g., 'Support Agent', 'Returns Processor'")
    what_it_does: str = Field(..., description="Specific tasks the agent handles, 2-3 sentences")
    estimated_impact: Dict[str, Any] = Field(
        ...,
        description="Measurable impact: hours_saved_monthly, tickets_handled, monthly_value_eur, etc."
    )
    deployment_timeline: str = Field(..., description="e.g., '2 weeks'")
    prerequisites: List[str] = Field(
        default_factory=list,
        description="What's needed: 'Shopify store', 'Gorgias account', etc."
    )
```

**In the `Finding` class (line 185-221), add after line 221** (after `what_instead` field):

```python
    # Agent opportunity (e-commerce only)
    agent_opportunity: Optional[AgentOpportunity] = Field(
        None, description="CRB agent deployment opportunity, included for e-commerce findings"
    )
```

**Add import at top of file:**
```python
from typing import Dict, Any, List, Optional  # Dict and Any may need adding
```

**Verification:** `cd backend && python -c "from src.models.recommendation import Finding, AgentOpportunity; print('OK')"`

---

## Task 2: Add Agent Opportunity Data to E-commerce KB

**File:** `backend/src/knowledge/ecommerce/opportunities.json`

For EACH opportunity in the `ai_opportunities` array, add an `agent_opportunity` field. Only add to opportunities where a CRB agent makes sense (not all).

### Opportunities that GET agent_opportunity:

**1. `ai-customer-service-chatbot`** (this is the primary agent — the CRB Support Agent)
```json
"agent_opportunity": {
  "agent_type": "CRB Support Agent",
  "what_it_does": "Handles tier-1 support tickets: order status, return policy, shipping questions, FAQs. Pulls real-time order data from Shopify to personalize every response. Starts in draft mode (agent suggests, human approves) and graduates to autonomous for routine queries.",
  "estimated_impact": {
    "tickets_handled_monthly": "200-400",
    "hours_saved_monthly": 35,
    "monthly_value_eur": 1400,
    "response_time_reduction": "4 hours to under 15 minutes"
  },
  "deployment_timeline": "2 weeks",
  "prerequisites": ["Shopify store", "Support tool (Gorgias, Zendesk, or email inbox)", "Product catalog accessible via API"]
}
```

**2. `review-management`**
```json
"agent_opportunity": {
  "agent_type": "CRB Review Agent",
  "what_it_does": "Monitors new reviews across platforms, drafts personalized responses matching your brand voice, flags negative reviews for human attention. Runs daily review sweeps automatically.",
  "estimated_impact": {
    "reviews_responded_monthly": "50-150",
    "hours_saved_monthly": 15,
    "monthly_value_eur": 600,
    "response_rate_improvement": "From 20% to 95% of reviews responded"
  },
  "deployment_timeline": "1 week",
  "prerequisites": ["Review platform (Yotpo, Judge.me, or Google Business)", "Brand voice guidelines"]
}
```

**3. `abandoned-cart-recovery`**
```json
"agent_opportunity": {
  "agent_type": "CRB Recovery Agent",
  "what_it_does": "Monitors abandoned carts in real-time. Sends personalized recovery sequences across email and SMS with AI-optimized timing and dynamic incentives based on cart value and customer history.",
  "estimated_impact": {
    "carts_recovered_monthly": "30-80",
    "hours_saved_monthly": 10,
    "monthly_value_eur": 2500,
    "recovery_rate_improvement": "From 5% to 12-15%"
  },
  "deployment_timeline": "2 weeks",
  "prerequisites": ["Shopify store", "Email platform (Klaviyo or Omnisend)", "Customer email collection"]
}
```

### Opportunities that DO NOT get agent_opportunity:
- `ai-product-descriptions` — one-time content task, not ongoing agent work
- `personalized-recommendations` — better served by existing SaaS tools (Nosto, Rebuy)
- `inventory-forecasting` — complex ML, not a simple agent deployment
- `dynamic-pricing` — high-risk, needs human oversight, not agent territory yet
- `automated-email-marketing` — existing platforms (Klaviyo) handle this well

**Verification:** `cd backend && python -c "import json; d=json.load(open('src/knowledge/ecommerce/opportunities.json')); agents=[o for o in d['ai_opportunities'] if 'agent_opportunity' in o]; print(f'{len(agents)} opportunities have agent data')"`

Expected: `3 opportunities have agent data`

---

## Task 3: Pass Agent Opportunity Through Finding Generation

**File:** `backend/src/skills/report-generation/finding_generation.py`

### 3a. Add agent opportunity to the LLM prompt

In the `_generate_findings` method (starts ~line 369), find the prompt string that starts with `"""Analyze the quiz responses`.

After the existing `FINDING REQUIREMENTS` section in the prompt (~line 430), add a new section:

```python
# Add this ONLY when industry is e-commerce
agent_opportunity_prompt = ""
if industry.lower() in ("ecommerce", "e-commerce", "ecom"):
    # Extract agent opportunities from the KB opportunities
    agent_opps = []
    for opp in opportunities:
        if "agent_opportunity" in opp:
            agent_opps.append({
                "opportunity_id": opp.get("id"),
                "agent_type": opp["agent_opportunity"]["agent_type"],
                "what_it_does": opp["agent_opportunity"]["what_it_does"],
                "estimated_impact": opp["agent_opportunity"]["estimated_impact"],
                "deployment_timeline": opp["agent_opportunity"]["deployment_timeline"],
                "prerequisites": opp["agent_opportunity"]["prerequisites"],
            })

    if agent_opps:
        agent_opportunity_prompt = f"""
===============================================================================
AGENT OPPORTUNITY (E-COMMERCE ONLY)
===============================================================================

For e-commerce findings, some opportunities can be handled by a CRB-managed AI agent.
When a finding matches one of the agent opportunities below, include the agent_opportunity
field in that finding's JSON output.

AVAILABLE AGENT OPPORTUNITIES:
{json.dumps(agent_opps, indent=2)}

For findings that match an agent opportunity, add this field to the finding JSON:
"agent_opportunity": {{
  "agent_type": "<from the matching opportunity>",
  "what_it_does": "<from the matching opportunity, adjusted to client context>",
  "estimated_impact": {{<adjust estimates based on quiz answers — company size, ticket volume, etc.>}},
  "deployment_timeline": "<from the matching opportunity>",
  "prerequisites": [<from matching opportunity, filtered to what client doesn't already have>]
}}

IMPORTANT:
- Only include agent_opportunity when the finding genuinely matches an available agent
- Adjust impact estimates based on the client's actual numbers from quiz answers
- Remove prerequisites the client already has (check their existing stack)
- Do NOT add agent_opportunity to every finding — only where it's genuinely applicable
"""
```

Then insert `{agent_opportunity_prompt}` into the prompt template, after `{expertise_injection}`.

### 3b. Parse agent_opportunity in validation

In the `_validate_findings` method (starts ~line 901), where findings are normalized from LLM output, add parsing for the agent_opportunity field.

Find where individual findings are processed (likely a loop over raw findings). Add:

```python
# Parse agent opportunity if present
agent_opp = raw_finding.get("agent_opportunity")
if agent_opp and isinstance(agent_opp, dict):
    finding_dict["agent_opportunity"] = {
        "agent_type": agent_opp.get("agent_type", ""),
        "what_it_does": agent_opp.get("what_it_does", ""),
        "estimated_impact": agent_opp.get("estimated_impact", {}),
        "deployment_timeline": agent_opp.get("deployment_timeline", ""),
        "prerequisites": agent_opp.get("prerequisites", []),
    }
```

### 3c. Update FindingWithPaths to carry agent_opportunity

**File:** `backend/src/models/finding_paths.py`

Find the `FindingWithPaths` class and add:

```python
    agent_opportunity: Optional[Dict[str, Any]] = Field(
        None, description="CRB agent deployment opportunity"
    )
```

Make sure when `FindingWithPaths` is constructed from a base `Finding`, the `agent_opportunity` field is carried through. Check the constructor/factory method.

**Verification:**
```bash
cd backend && python -c "
from src.models.recommendation import Finding, AgentOpportunity
f = Finding(
    id='test', title='Test', description='Test finding',
    customer_value_score=8, business_health_score=9,
    sources=['quiz'],
    agent_opportunity=AgentOpportunity(
        agent_type='Support Agent',
        what_it_does='Handles tickets',
        estimated_impact={'hours_saved': 35},
        deployment_timeline='2 weeks',
        prerequisites=['Shopify']
    )
)
print(f'Agent type: {f.agent_opportunity.agent_type}')
print('OK')
"
```

---

## Task 4: Update Frontend to Display Agent Opportunity

**File:** `frontend/src/components/report/TieredFindings.tsx`

### 4a. Update the Finding interface (line 4-14)

Add to the `Finding` interface:

```typescript
interface AgentOpportunity {
  agent_type: string
  what_it_does: string
  estimated_impact: Record<string, string | number>
  deployment_timeline: string
  prerequisites: string[]
}

interface Finding {
  // ... existing fields ...
  agent_opportunity?: AgentOpportunity
}
```

### 4b. Add AgentOpportunityCard component

Add this component before the `HeroFindingCard` function (before line 33):

```typescript
function AgentOpportunityCard({ opportunity }: { opportunity: AgentOpportunity }) {
  return (
    <div className="mt-4 p-4 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg">
      <div className="flex items-center gap-2 mb-2">
        <span className="px-2 py-0.5 bg-indigo-600 text-white text-[10px] font-bold rounded uppercase tracking-wide">
          Agent Available
        </span>
        <span className="text-sm font-medium text-indigo-700 dark:text-indigo-300">
          {opportunity.agent_type}
        </span>
      </div>
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
        {opportunity.what_it_does}
      </p>
      <div className="flex flex-wrap gap-4 text-sm">
        {opportunity.estimated_impact.monthly_value_eur && (
          <div>
            <span className="text-gray-500">Est. monthly value</span>
            <p className="font-semibold text-indigo-700 dark:text-indigo-300">
              {new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(Number(opportunity.estimated_impact.monthly_value_eur))}
            </p>
          </div>
        )}
        {opportunity.estimated_impact.hours_saved_monthly && (
          <div>
            <span className="text-gray-500">Hours saved</span>
            <p className="font-semibold text-indigo-700 dark:text-indigo-300">
              {opportunity.estimated_impact.hours_saved_monthly}h/month
            </p>
          </div>
        )}
        <div>
          <span className="text-gray-500">Deployment</span>
          <p className="font-semibold text-indigo-700 dark:text-indigo-300">
            {opportunity.deployment_timeline}
          </p>
        </div>
      </div>
    </div>
  )
}
```

### 4c. Render in HeroFindingCard

In the `HeroFindingCard` component, add after the value metrics section (after the closing `)}` of the value_saved/value_created conditional block, around line 81):

```tsx
      {finding.agent_opportunity && (
        <AgentOpportunityCard opportunity={finding.agent_opportunity} />
      )}
```

### 4d. Add subtle indicator in CompactFindingCard

In `CompactFindingCard` (line 86-107), add after the confidence span (around line 103):

```tsx
        {finding.agent_opportunity && (
          <>
            <span className="text-gray-300">•</span>
            <span className="font-medium text-indigo-600">Agent available</span>
          </>
        )}
```

**Verification:** `cd frontend && npx tsc --noEmit` (TypeScript check)

---

## Task 5: Verify E-commerce Benchmarks

**File:** `backend/src/knowledge/ecommerce/benchmarks.json`

The benchmarks file is marked UNVERIFIED. Review the data and either:
- Verify against sources and update `verified_at` dates
- Mark specific metrics with source URLs
- Flag any obviously wrong numbers

This is a data quality task, not a code task. Read the file, cross-reference key metrics:
- Cart abandonment rate (should be ~70% industry standard)
- Average conversion rate (should be 1-3%)
- Return rate (should be 15-30% depending on category)
- Average order value (varies widely by niche)

Update `"status": "UNVERIFIED"` to `"status": "VERIFIED"` for metrics you confirm, and add `"source"` fields where possible.

**Verification:** `cd backend && python -c "import json; d=json.load(open('src/knowledge/ecommerce/benchmarks.json')); print('Benchmarks loaded OK')"`

---

## Execution Order

```
Task 1 (model)  →  Task 2 (KB data)  →  Task 3 (generation)  →  Task 4 (frontend)  →  Task 5 (benchmarks)
     |                    |                      |                      |
   No deps           Needs Task 1           Needs Task 1+2          Needs Task 1
                     for schema ref         for data + model        for interface
```

Tasks 1 and 2 can be done in parallel.
Task 4 can start as soon as Task 1 is done.
Task 3 depends on both Task 1 and Task 2.
Task 5 is independent and can be done anytime.

---

## Files Modified (Summary)

| File | Change |
|------|--------|
| `backend/src/models/recommendation.py` | Add `AgentOpportunity` model + field on `Finding` |
| `backend/src/models/finding_paths.py` | Add `agent_opportunity` field to `FindingWithPaths` |
| `backend/src/knowledge/ecommerce/opportunities.json` | Add `agent_opportunity` to 3 opportunities |
| `backend/src/skills/report-generation/finding_generation.py` | Add agent prompt section + parse agent data |
| `frontend/src/components/report/TieredFindings.tsx` | Add `AgentOpportunity` interface + card + rendering |
| `backend/src/knowledge/ecommerce/benchmarks.json` | Verify data, update status |

---

## What This Does NOT Include

- Stripe changes (€2,500 sprint, €750/mo subscription) — no clients yet
- Agent deployment system — no clients yet
- Monthly ROI report — no managed clients yet
- Client dashboard — Phase 2+
- Changes to other verticals — e-commerce only

---

## Commit Message When Done

```
feat: add Agent Opportunity section to e-commerce report findings

E-commerce CRB reports now show which findings can be handled by a
CRB-managed agent, with estimated impact and deployment timeline.
This is the upsell mechanism from report to implementation sprint.
```
