# Adaptive Recommendations + Visual Automation Flow — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the recommendation engine adapt to each client's readiness level (infrastructure + build willingness), and add a visual automation flow builder to the report that maps out the recommended architecture in a clear, visual way.

**Design doc:** `docs/plans/2026-02-26-adaptive-recommendations-design.md`

**Tech Stack:** Python (FastAPI), React/TypeScript, @xyflow/react (new dependency), Tailwind CSS, framer-motion

## CRB Context
- Affected user journey stage: Report Viewer (primary), Quiz → Report pipeline (secondary)
- Reference docs to load during execution: `report-quality.md`, `frontend-development.md`
- Key principle: AI-assisted building is for everyone — never gatekeep based on tech proficiency. Adapt complexity, not access.
- No upsell language in the report. The strategy call (€497) sells itself through report quality.

## Rollback Plan
`git revert` the merge commit. New dependency (@xyflow/react) removed via `pnpm remove`. No database migrations.

---

## Batch 1: Readiness Profile Builder (Backend Foundation)

Everything else depends on this — the readiness profile feeds into the prompt and determines recommendations.

### Task 1.1: Create readiness profile builder function

**File:** `backend/src/services/report_service.py`

**Add function** `_build_readiness_profile(quiz_answers: dict) -> dict` that maps raw quiz fields to clean prompt vocabulary:

```python
def _build_readiness_profile(quiz_answers: dict) -> dict:
    """Map quiz signals into readiness profile for recommendation engine."""

    # Infrastructure readiness
    current_tools = quiz_answers.get("current_tools", [])
    integration_score = quiz_answers.get("integration_issues", 5)
    manual_entry = quiz_answers.get("manual_data_entry", False)

    if not current_tools or len(current_tools) <= 1:
        infrastructure = "paper-based"
    elif integration_score < 4 or manual_entry:
        infrastructure = "partial"
    else:
        infrastructure = "digitized"

    # Build willingness (from preference + tech comfort)
    preference = quiz_answers.get("implementation_preference", "buy")
    tech_comfort = quiz_answers.get("technology_comfort", 5)

    if preference in ("build", "connect") or tech_comfort >= 7:
        build_willingness = "eager"
    elif preference == "hire" or tech_comfort <= 3:
        build_willingness = "prefers-turnkey"
    else:
        build_willingness = "open"

    # AI experience
    ai_tools = quiz_answers.get("ai_tools_used", [])
    if not ai_tools or ai_tools == ["none"]:
        ai_experience = "none"
    elif len(ai_tools) >= 3 or "automation" in ai_tools:
        ai_experience = "active-user"
    else:
        ai_experience = "dabbled"

    # Stack API readiness
    api_ready = quiz_answers.get("existing_stack_api_ready", False)
    stack_api = "most-apis" if api_ready else "mixed"

    # Urgency + preference pass through
    urgency = quiz_answers.get("implementation_urgency", "this_quarter")

    return {
        "infrastructure": infrastructure,
        "build_willingness": build_willingness,
        "ai_experience": ai_experience,
        "stack_api_readiness": stack_api,
        "urgency": urgency,
        "preference": preference,
    }
```

**Verification:** Write a quick test in `backend/tests/services/test_readiness_profile.py` with 3-4 cases:
- Paper-based non-technical client → infrastructure="paper-based", build_willingness="prefers-turnkey"
- Digitized eager builder → infrastructure="digitized", build_willingness="eager"
- Partial with some AI experience → infrastructure="partial", ai_experience="dabbled"

### Task 1.2: Pass readiness profile to three_options skill

**File:** `backend/src/services/report_service.py`

Find where the three_options skill is invoked (search for `three_options` or `ThreeOptionsSkill`). Add the readiness profile to the context passed to the skill:

```python
readiness_profile = _build_readiness_profile(quiz_answers)
# Add to whatever context object is passed to the skill
context.readiness_profile = readiness_profile
```

**Verification:** Add a log line: `logger.info("readiness_profile", **readiness_profile)` and confirm it logs when generating a report.

---

## Batch 2: Prompt Rewrite (Backend Core Logic)

### Task 2.1: Rewrite three_options.py system prompt

**File:** `backend/src/skills/report-generation/three_options.py`

**Read the full file first.** Then make these changes:

**Replace** the hardcoded recommendation rule. Find:
```
our_recommendation MUST be "connect_and_automate" UNLESS
```

**Replace with adaptive decision logic:**
```
RECOMMENDATION DECISION (evaluate per finding):

1. If no digital tool exists for this business function → recommend "targeted_upgrade"
   Buy the foundation. ALWAYS recommend tools with strong APIs so they become
   connectable later. Frame as: "This is your foundation — once set up, we can
   wire AI workflows on top."

2. If existing tool is a dead end (no API, no data export, fundamentally broken)
   → recommend "targeted_upgrade"
   Replace with API-ready alternative. Frame as: "Your current tool traps your
   data. [Replacement] opens up integration possibilities."

3. Everything else → recommend "connect_and_automate"
   Adapt the complexity based on the client's readiness profile.
   - Paper-based infrastructure: acknowledge the gap, show simpler automation paths
   - Digitized with APIs: show full Claude Code / MCP integration workflows
   - Low build willingness: emphasize managed tools (Zapier, Make) over raw APIs
   - High build willingness: show Claude Code workflows with specific build steps

Always generate ALL THREE options regardless of recommendation.
Always explain WHY this recommendation fits THIS client's readiness level.
Never say "you're not technical enough" — AI-assisted building is accessible to everyone.
Adapt the HOW, not the WHETHER.
```

**Add readiness profile to the prompt context block.** Find where company context is injected and add:
```
CLIENT READINESS PROFILE:
- Infrastructure: {readiness_profile.infrastructure}
- Build Willingness: {readiness_profile.build_willingness}
- AI Experience: {readiness_profile.ai_experience}
- Stack API Readiness: {readiness_profile.stack_api_readiness}
- Urgency: {readiness_profile.urgency}
- Preference: {readiness_profile.preference}
```

### Task 2.2: Add new fields to connect_and_automate template

**File:** `backend/src/skills/report-generation/three_options.py`

Find the connect_and_automate option template/schema. Add these optional fields:

```python
"prerequisite": "(optional) what must be in place first, e.g. 'digital scheduling tool'",
"build_time": "X weeks (solo) / Y days (guided)",
"diy_complexity": "low | moderate | high",
```

Update the prompt instructions to say:
```
For connect_and_automate options:
- Include "prerequisite" when the recommendation depends on infrastructure
  that doesn't exist yet
- Include "build_time" with both solo and guided estimates
  (guided = working with an expert, approximately 3-5x faster)
- Include "diy_complexity" to set expectations
```

### Task 2.3: Add automation_flow field to connect_and_automate

**File:** `backend/src/skills/report-generation/three_options.py`

Add to the connect_and_automate template:

```python
"automation_flow": {
    "nodes": [
        {"id": "n1", "label": "Google Calendar", "type": "existing_tool"},
        {"id": "n2", "label": "Claude API", "type": "ai_layer"},
        {"id": "n3", "label": "Clio", "type": "existing_tool"},
        {"id": "n4", "label": "Time Entry Created", "type": "output"}
    ],
    "edges": [
        {"from": "n1", "to": "n2", "label": "Calendar events"},
        {"from": "n2", "to": "n3", "label": "Classified time entry"},
        {"from": "n3", "to": "n4", "label": "Auto-saved"}
    ]
}
```

Add prompt instruction:
```
For EVERY connect_and_automate option, include an "automation_flow" object that
maps the data flow visually:
- nodes: each tool, API, AI layer, or output in the workflow
  - type: "existing_tool" (green, already in their stack),
          "new_tool" (blue, needs to be added),
          "ai_layer" (purple, Claude/AI processing),
          "output" (gray, the end result)
- edges: connections between nodes with a short label describing what data flows

Keep it simple — 3-6 nodes max per flow. This gets rendered as a visual diagram.
```

**Verification:** Run `cd backend && python -m pytest tests/ -v --no-header` — all tests pass.

---

## Batch 3: Validation & Report Service Updates (Backend)

### Task 3.1: Update report validation for new fields

**File:** `backend/src/services/report_service.py`

Find the validation logic for recommendation options (search for `has_aios_keys` or the validation section). Update to accept the new optional fields:

- `prerequisite` (optional string on connect_and_automate)
- `build_time` (string, can include dual format)
- `diy_complexity` (optional: "low" | "moderate" | "high")
- `automation_flow` (optional object with nodes and edges arrays)

These should be pass-through — validate structure if present, don't reject if absent (backward compat).

### Task 3.2: Update report_service fallback prompt

**File:** `backend/src/services/report_service.py`

Search for the fallback recommendation prompt (used when three_options skill fails or for inline generation). Update it with the same adaptive logic from Task 2.1 — don't leave the old hardcoded "MUST be connect_and_automate" in the fallback path.

**Verification:** Run backend tests. Verify JSON validation passes with both old-format and new-format sample data.

---

## Batch 4: Install React Flow & Build Automation Flow Component (Frontend Core)

### Task 4.1: Install @xyflow/react

```bash
cd frontend && pnpm add @xyflow/react
```

**Verification:** `pnpm ls @xyflow/react` shows installed version.

### Task 4.2: Create AutomationFlowBuilder component

**File:** `frontend/src/components/report/AutomationFlowBuilder.tsx` (NEW)

Build a React Flow-based component that renders the `automation_flow` data from a finding's connect_and_automate option.

**Node types (custom rendered):**
- `existing_tool` — Emerald/green rounded card with tool icon. Label: tool name. Subtle "In your stack" badge.
- `new_tool` — Blue rounded card. Label: tool name. "Add this" badge.
- `ai_layer` — Purple rounded card with sparkle/brain icon. Label: "Claude API" or similar.
- `output` — Gray rounded card with check icon. Label: the outcome.

**Edge styling:**
- Animated dashed lines (React Flow supports this natively)
- Small label on each edge showing what data flows
- Directional arrows

**Layout:**
- Left-to-right horizontal flow (dagre auto-layout or manual positioning)
- Clean white/dark background with subtle grid
- Smooth zoom/pan (React Flow default)
- Responsive — stacks vertically on mobile

**Component interface:**
```typescript
interface FlowNode {
  id: string
  label: string
  type: 'existing_tool' | 'new_tool' | 'ai_layer' | 'output'
}

interface FlowEdge {
  from: string
  to: string
  label?: string
}

interface AutomationFlow {
  nodes: FlowNode[]
  edges: FlowEdge[]
}

interface AutomationFlowBuilderProps {
  flow: AutomationFlow
  title?: string  // e.g. "How it connects"
}
```

**Styling:**
- Use Tailwind for the wrapper
- Custom node components with Tailwind classes
- Match existing report aesthetic (rounded-xl, border-gray-200, shadow-sm)
- Framer-motion for entrance animation of the whole flow container

**Key implementation notes:**
- Import `@xyflow/react` styles in the component or in `index.css`
- Use `dagre` layout algorithm (comes with examples in React Flow docs) for auto-positioning
- Set `fitView` prop so the flow always fits the container
- Disable editing (nodesDraggable=false, nodesConnectable=false) — this is read-only
- Add a subtle legend below: green = existing tool, blue = new, purple = AI, gray = result

```bash
cd frontend && pnpm add dagre @types/dagre
```

### Task 4.3: Create custom node components

**File:** `frontend/src/components/report/flow/FlowNodes.tsx` (NEW)

Create 4 custom node components matching the node types. Each should be a small card (~120px wide) with:
- Colored left border (emerald/blue/purple/gray)
- Icon (from lucide-react: Database, Plus, Sparkles, CheckCircle)
- Label text
- Small type badge

Keep them minimal and elegant — the flow should be immediately readable.

**Verification:** Frontend builds cleanly: `cd frontend && npx tsc --noEmit`

---

## Batch 5: Integrate Flow Into Report Viewer (Frontend Integration)

### Task 5.1: Embed flow in NumberedRecommendations

**File:** `frontend/src/components/report/NumberedRecommendations.tsx`

When rendering a connect_and_automate option that has `automation_flow` data, render the `AutomationFlowBuilder` component inside the card, below the approach description and above the pros/cons.

```tsx
{option.automation_flow && (
  <div className="mt-4 mb-4">
    <AutomationFlowBuilder
      flow={option.automation_flow}
      title="How it connects"
    />
  </div>
)}
```

Size: constrain to ~300px height within the card. The flow auto-fits via React Flow's `fitView`.

### Task 5.2: Add prerequisite and dual build time display

**File:** `frontend/src/components/report/NumberedRecommendations.tsx`

In the connect_and_automate card rendering:

**Prerequisite** — show as a subtle amber banner at top of card when present:
```tsx
{option.prerequisite && (
  <div className="flex items-center gap-2 px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
    <AlertTriangle className="w-4 h-4" />
    <span>First: {option.prerequisite}</span>
  </div>
)}
```

**Dual build time** — show as-is (the string already contains both):
```
"3 weeks (solo) / 1 week (guided)"
```

**DIY complexity** — show as a small badge next to build time:
```tsx
{option.diy_complexity && (
  <span className={`text-xs px-2 py-0.5 rounded-full ${
    option.diy_complexity === 'low' ? 'bg-green-100 text-green-700' :
    option.diy_complexity === 'moderate' ? 'bg-yellow-100 text-yellow-700' :
    'bg-red-100 text-red-700'
  }`}>
    {option.diy_complexity} complexity
  </span>
)}
```

### Task 5.3: Add flow to TieredFindings expand view

**File:** `frontend/src/components/report/TieredFindings.tsx`

When a finding is expanded and has a connect_and_automate option with automation_flow, show a compact version of the flow below the finding details. Use the same `AutomationFlowBuilder` component but at smaller height (~200px).

**Verification:** `cd frontend && npx tsc --noEmit` passes. Start dev server and visually verify with sample report data.

---

## Batch 6: Sample Reports & Verification

### Task 6.1: Update sample_report.json with adaptive examples

**File:** `backend/src/data/sample_report.json`

Update 2-3 findings to demonstrate the adaptive pattern:

**Finding 1 (connect recommendation):** Client has API-ready tools
- `our_recommendation: "connect_and_automate"`
- Include `automation_flow` with 4-5 nodes showing the data flow
- Include `build_time: "2 weeks (solo) / 4 days (guided)"`
- Include `diy_complexity: "moderate"`

**Finding 2 (buy recommendation):** No tool exists for this function
- `our_recommendation: "targeted_upgrade"`
- `recommendation_rationale` explains this is the foundation, mentions API-readiness
- connect_and_automate option has `prerequisite: "Requires [tool] to be set up first"`
- Still includes `automation_flow` showing what becomes possible AFTER buying

**Finding 3 (connect with prerequisite):** Tool exists but partial infrastructure
- `our_recommendation: "connect_and_automate"`
- `prerequisite: "Digitize patient intake forms first"`
- Shows simpler automation flow (3 nodes)

### Task 6.2: Update one industry sample report

**File:** `backend/src/data/sample_report_ecommerce.json`

Update 1-2 findings with the same pattern — automation_flow data, adaptive recommendation, prerequisite where relevant.

### Task 6.3: Full verification

Run in sequence:
```bash
# Backend tests
cd backend && python -m pytest tests/ -v --no-header

# Validate all JSON
python -c "import json, glob; [json.load(open(f)) for f in glob.glob('src/data/sample_report*.json')]"

# Frontend type check
cd ../frontend && npx tsc --noEmit

# Frontend builds
cd ../frontend && pnpm build
```

All must pass.

---

## Files Changed Summary

| File | Change Type |
|------|-------------|
| `backend/src/services/report_service.py` | Edit — add `_build_readiness_profile()`, pass to skill, update validation |
| `backend/src/skills/report-generation/three_options.py` | Edit — rewrite prompt, add adaptive logic, add automation_flow |
| `backend/tests/services/test_readiness_profile.py` | NEW — readiness profile unit tests |
| `backend/src/data/sample_report.json` | Edit — update 2-3 findings with adaptive + flow data |
| `backend/src/data/sample_report_ecommerce.json` | Edit — update 1-2 findings |
| `frontend/package.json` | Edit — add @xyflow/react, dagre |
| `frontend/src/components/report/AutomationFlowBuilder.tsx` | NEW — main flow visualization component |
| `frontend/src/components/report/flow/FlowNodes.tsx` | NEW — custom node renderers |
| `frontend/src/components/report/NumberedRecommendations.tsx` | Edit — embed flow, prerequisite, dual build time |
| `frontend/src/components/report/TieredFindings.tsx` | Edit — compact flow in expanded view |

**No changes to:** Quiz, teaser, playbook generator, landing pages, industry pages, auth, payments.
