# Report Refiner — Design Document

**Date:** 2026-02-21
**Status:** Design complete, ready for implementation
**Phase:** Pre-implementation

---

## Overview

An AI agent sidebar that lives inside every delivered CRB report. Users can ask questions, explore recommendations, and — when they provide new business context — receive suggested enhancements to their analysis.

The agent is a **knowledgeable companion**, not an editor. Conversation is free and unlimited. Suggestions only emerge when the user reveals information the original analysis didn't have.

### Core Philosophy

> Refinement has diminishing returns. The best report is one that gets acted on.

An **Energy Meter** nudges users from refining toward implementing. It's not a paywall — it's a coach.

---

## User Experience

### Entry Point

Floating button (bottom-right of report viewer): **"Ask your report"**. Opens a sidebar panel that slides in from the right. Desktop: pushes report content left. Tablet: overlays with backdrop blur. Mobile: full-screen takeover.

### First Interaction

Short greeting: *"I have full context on your analysis. Ask me anything."*

Below it, 3 dynamic starter prompts generated from the specific report:
- *"Why was customer support automation your top-scored finding?"*
- *"Break down the $411K value potential — what's realistic for year 1?"*
- *"What should I implement first with a team of 3?"*

These are **understanding questions**, not change requests. Trust first.

### Agent Capabilities

| Capability | Example | Triggers suggestion? |
|---|---|---|
| **Explain** | "Why did you score this finding 8/10?" | No |
| **Clarify** | "What does Connect vs Replace mean for us?" | No |
| **Deep-dive** | "Tell me more about the Gorgias integration" | No |
| **Compare** | "How does Option A compare to Option B?" | No |
| **Prioritize** | "I can only do one thing this quarter" | No |
| **Enhance** | User provides new context → agent proposes change | Yes |

### Agent Boundaries

- Cannot remove findings entirely
- Cannot change CRB methodology or scoring formula
- Cannot invent vendors or benchmarks not in the knowledge base
- Cannot generate entirely new report sections from scratch

### The Context Trigger

The agent distinguishes three message types:

| Type | Example | Response |
|------|---------|----------|
| **Understanding** | "Explain the ROI on rec #3" | Explain. No suggestion. |
| **Exploration** | "What if we went with Zendesk?" | Discuss tradeoffs. Hypothetical — no suggestion. |
| **New context** | "We already have a Zendesk license" | New information. Propose suggestion. |

Decision framework enforced in system prompt:
1. Did the user share information not in the original quiz?
2. Would this information have changed the analysis if known earlier?
3. Is the user stating a fact, not asking a hypothetical?

All three must be YES to propose a change.

---

## Suggestions Mechanism

### Suggestion Cards

Appear inline in chat when agent proposes a change. User explicitly accepts or dismisses.

```
+---------------------------------------------+
|  * Moderate refinement  .  +15% energy       |
|                                              |
|  Recommendation #2: Support Automation       |
|                                              |
|  Replace Gorgias recommendation with         |
|  Zendesk Connect path (existing license)     |
|                                              |
|  +- What changes -------------------------+  |
|  |  . Vendor: Gorgias -> Zendesk          |  |
|  |  . Monthly cost: $89 -> $0 (owned)     |  |
|  |  . ROI: 180% -> 340%                   |  |
|  |  . Verdict: REPLACE -> CONNECT         |  |
|  +-----------------------------------------+  |
|                                              |
|  [ Preview full diff ]                       |
|                                              |
|  [ Accept ]                   [ Dismiss ]    |
+----------------------------------------------+
```

### Impact Scaling

Suggestions scale with the significance of new context:

| Impact | Trigger example | Behavior |
|---|---|---|
| **Minor** | "Our support volume is 200/day not 50" | Single suggestion card — ROI recalc |
| **Moderate** | "We have no dev resources" | Multi-suggestion — grouped cards |
| **Major** | "We're B2B wholesale, not DTC" | Preview-first — full diff overlay |

Major changes always require preview confirmation before applying.

### Report Mutations

The agent can modify any section of the report when the user provides new context that warrants it. Minor tweaks produce single suggestion cards. Major context shifts can trigger section rewrites across findings, recommendations, and roadmap. The scope of changes matches the scope of new information.

---

## Energy Meter

### Visual Design

Horizontal bar in sidebar header. Hidden until first suggestion is accepted. Smooth animated fill. Color gradient: green -> amber -> red.

### Cost Per Refinement

| Impact level | Energy cost | Rough capacity |
|---|---|---|
| Minor | 0.08 (8%) | ~12 per report |
| Moderate | 0.15 (15%) | ~6 per report |
| Major | 0.30 (30%) | ~3 per report |

Typical session: 1-2 moderate + 3-4 minor = ~50-60% energy.

### Zone Behavior

| Zone | Range | Color | Tone | Example message |
|---|---|---|---|---|
| Sharpen | 0-40% | Green | Data-driven | "3 refinements applied. Reports with 3-5 refinements see 2x higher implementation rates." |
| Strong | 40-70% | Amber | Coach | "Your report is sharp. 5 of 7 findings refined. What's the one action you'll take this week?" |
| Ship it | 70-100% | Red | Playful | "Perfectionism detected! Your competitors aren't refining — they're implementing." |

### At 100%: Implementation Mode

The agent doesn't shut down. It transforms. Suggestions stop. Conversation pivots to implementation coaching:

*"You've refined enough. Let's plan your first week. Which recommendation are you starting with?"*

If the user pushes for more changes: *"I could tweak that, but honestly — the current recommendation is solid. The bigger win is getting Gorgias set up this week."*

### Reset Policy

Never resets. One energy budget per report, for the life of the report. If business context changes fundamentally, that's a new analysis.

### Pricing

Included in the EUR 147 report price. Cost per report's agent usage: ~EUR 0.50-1.00 (well under 1% of revenue).

---

## Architecture

### Principles

1. **Original report is immutable** — never modified after generation
2. **Snapshots for fast rendering** — materialize on write, not on read
3. **Structured refinements** — typed, targeted, with dependencies
4. **Conversations as first-class entities** — multiple, persistent

### New Tables

```sql
-- Materialized report state at each version
report_snapshots (
  id              UUID PRIMARY KEY,
  report_id       UUID REFERENCES reports(id),
  version         INT NOT NULL,              -- 0 = original
  data            JSONB NOT NULL,            -- full report at this version
  energy_level    FLOAT DEFAULT 0.0,         -- 0.0 to 1.0
  created_at      TIMESTAMPTZ DEFAULT now(),
  created_by      TEXT DEFAULT 'system',     -- 'system' | 'refinement'
  UNIQUE(report_id, version)
);

-- Structured change log with dependency tracking
report_refinements (
  id              UUID PRIMARY KEY,
  report_id       UUID REFERENCES reports(id),
  from_version    INT NOT NULL,              -- snapshot applied to
  to_version      INT NOT NULL,              -- snapshot created
  refinement_type TEXT NOT NULL,             -- vendor_swap, roi_update, section_rewrite,
                                             -- priority_shift, constraint_update, context_enrichment
  target_section  TEXT NOT NULL,             -- findings, recommendations, playbooks,
                                             -- executive_summary, roadmap
  target_ids      TEXT[] DEFAULT '{}',       -- finding-001, rec-003, etc.
  change_summary  TEXT NOT NULL,             -- human-readable description
  original_data   JSONB,                     -- what was there before
  refined_data    JSONB,                     -- what it became
  impact_level    TEXT NOT NULL,             -- minor, moderate, major
  energy_cost     FLOAT NOT NULL,
  depends_on      UUID[] DEFAULT '{}',       -- other refinement IDs
  message_id      UUID REFERENCES report_messages(id),
  status          TEXT DEFAULT 'accepted',   -- accepted, undone
  created_at      TIMESTAMPTZ DEFAULT now()
);

-- Persistent chat threads per report
report_conversations (
  id              UUID PRIMARY KEY,
  report_id       UUID REFERENCES reports(id),
  title           TEXT,                      -- auto-generated from first message
  started_at      TIMESTAMPTZ DEFAULT now(),
  last_message_at TIMESTAMPTZ,
  status          TEXT DEFAULT 'active'      -- active, archived
);

-- Individual messages with optional suggestions
report_messages (
  id              UUID PRIMARY KEY,
  conversation_id UUID REFERENCES report_conversations(id),
  role            TEXT NOT NULL,             -- user, assistant
  content         TEXT NOT NULL,
  suggestions     JSONB,                     -- suggestion cards proposed
  model_used      TEXT,
  tokens_used     INT,
  created_at      TIMESTAMPTZ DEFAULT now()
);
```

### Data Flow

1. Report generated and released -> version 0 snapshot auto-created (copy of report data)
2. User opens sidebar, asks questions -> messages stored, no snapshots, no energy cost
3. Agent detects new context -> proposes suggestion in message `suggestions` field
4. User accepts -> refinement record created -> new snapshot materialized -> energy updated
5. User undoes -> refinement marked `undone` -> snapshot recomputed from last good state
6. Frontend renders -> GET /api/reports/{id} returns latest snapshot (same shape as today)

### API Endpoints

```
Conversations
  POST   /api/reports/{id}/conversations                    Start new conversation
  GET    /api/reports/{id}/conversations                    List all conversations

Messages
  POST   /api/reports/{id}/conversations/{cid}/messages     Send message, get response
  GET    /api/reports/{id}/conversations/{cid}/messages      Load history

Refinements
  POST   /api/reports/{id}/refinements                      Accept a suggestion
  DELETE /api/reports/{id}/refinements/{rid}                 Undo a refinement
  GET    /api/reports/{id}/refinements                      List refinements + energy

Report (modified)
  GET    /api/reports/public/{id}                           Returns latest snapshot
  GET    /api/reports/public/{id}?version=0                 Returns original
```

### Model Routing

| Task | Model | Reasoning |
|---|---|---|
| Conversation (understand, explore) | Sonnet 4.6 | Fast, cheap, good at following instructions |
| Suggestion generation | Sonnet 4.6 | Needs to compute changes accurately |
| Major section rewrite | Opus 4.6 | Complex multi-finding reasoning |
| Starter prompt generation | Haiku 4.5 | Simple extraction from report data |

### Agent System Prompt Structure

```
Layer 1: Role & Boundaries
  Purpose, tone, what you can/cannot do

Layer 2: Report Context (injected per-report)
  Company profile, findings, recommendations, quiz answers,
  benchmarks, current energy level, refinement history

Layer 3: Behavioral Rules
  Context trigger detection, suggestion protocol, energy zone behavior
```

---

## Frontend Components

```
ReportViewer.tsx (existing)
|-- ... existing report sections ...
|
|-- RefinerButton              Floating trigger (bottom-right)
|
+-- RefinerSidebar             Slides in from right
    |-- RefinerHeader
    |   |-- Title
    |   |-- EnergyMeter        Visible after first accepted suggestion
    |   +-- ConversationSwitcher
    |
    |-- MessageList
    |   |-- StarterPrompts     Shown at conversation start
    |   |-- MessageBubble      User and assistant messages
    |   |   +-- SuggestionCard Inline when agent proposes changes
    |   +-- ...
    |
    |-- RefinementPreview      Full-screen overlay for major changes
    |   |-- DiffView (before/after)
    |   +-- [ Apply changes ] [ Dismiss ]
    |
    +-- MessageInput
        |-- TextArea
        +-- SendButton
```

### Responsive Behavior

- **Desktop (>1200px)**: Sidebar pushes report left. Both visible.
- **Tablet (768-1200px)**: Overlay with backdrop blur.
- **Mobile (<768px)**: Full-screen takeover.

### Report Integration

On accepted suggestion, the corresponding report section shows:
- Subtle amber glow animation (fades after 2s)
- Small "Refined" badge with tooltip showing what changed
- Original value preserved in expandable detail

---

## Implementation Phases

### Phase 1: Conversation (1-2 weeks)

Foundation. User can chat with their report. No suggestions, no meter.

- `report_conversations` + `report_messages` tables + RLS policies
- `POST /messages` endpoint with Sonnet 4.6
- Agent system prompt with report context injection
- `RefinerButton` + `RefinerSidebar` + `MessageList` + `MessageInput`
- Dynamic starter prompts (Haiku-generated)

**Signal**: Do users open this? What do they ask? What types of refinements would they want?

### Phase 2: Suggestions + Snapshots (1-2 weeks)

The agent can propose changes. Users can accept them.

- `report_snapshots` + `report_refinements` tables + RLS policies
- Snapshot v0 auto-created on report release
- Context trigger detection in agent logic
- `SuggestionCard` component with accept/dismiss
- Report public endpoint returns latest snapshot
- Undo support

**Signal**: Do users accept suggestions? Which types? How many?

### Phase 3: Energy Meter (3-5 days)

Behavioral nudge layer.

- `EnergyMeter` component with zone-based styling
- Energy cost classification per refinement type
- Zone-based agent tone shifting
- Implementation mode after 1.0
- Meter message progression (data -> coach -> playful)

**Signal**: Does the meter change behavior? Do users implement more?

### Phase 4: Major Rewrites + Polish (1 week)

Premium capability and polish.

- `RefinementPreview` overlay with diff view
- Multi-section cascade detection
- Opus 4.6 escalation for section rewrites
- Conversation switcher for returning users
- "Refined" badges on report sections
- Report-sidebar highlight animation

**Total**: ~4-6 weeks. Phase 1 alone is shippable and generates signal.

---

## Cost Analysis

| Component | Per-report cost |
|---|---|
| Typical agent conversation (8-12 messages) | EUR 0.30-0.60 |
| Suggestion generation (1-3 suggestions) | EUR 0.10-0.20 |
| Major rewrite (Opus, if triggered) | EUR 0.15-0.30 |
| **Total typical usage** | **EUR 0.50-1.00** |
| **As % of EUR 147 price** | **0.3-0.7%** |

---

## Success Metrics

| Metric | Target | What it tells us |
|---|---|---|
| Sidebar open rate | >30% of report viewers | Is the feature discoverable? |
| Messages per session | 4-8 | Are users engaging meaningfully? |
| Suggestion accept rate | >50% | Are suggestions relevant? |
| Average energy level | 30-60% | Right balance of refinement and action |
| Implementation rate (30-day) | 2x vs non-refiner users | Does refining drive action? |
