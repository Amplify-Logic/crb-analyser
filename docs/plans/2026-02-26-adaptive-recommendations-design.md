# Adaptive Recommendation Engine — Design

> Output of brainstorming session, 2026-02-26

## Problem

The AIOS pivot hardcoded `our_recommendation = "connect_and_automate"` for 90%+ of cases. This is wrong because:

- A client with no digital tools can't connect APIs that don't exist
- A client on paper needs to buy foundational software first
- A client with dead-end tools (no API, trapped data) needs to replace them before connecting
- The recommendation should adapt to where the client IS, not where we want them to be

Meanwhile, the quiz already captures rich readiness signals (implementation_capability, technology_comfort, ai_tools_used, implementation_preference, etc.) but barely passes them to the recommendation engine.

## Core Insight

Two axes determine the right recommendation:

1. **Infrastructure readiness** — Do they have digital data? API-ready tools? Or paper/spreadsheets?
2. **Build willingness** — Are they open to learning AI-assisted building? Or want turnkey?

But critically: AI-assisted building is becoming accessible to everyone. The barrier is no longer technical skill — it's mindset and infrastructure. A motivated non-technical person with Claude Code can build real integrations. So we never gate people away from the build option based on tech proficiency alone.

## Decision Logic Per Finding

```
IF no tool exists for this business function
  → our_recommendation: "targeted_upgrade"
  → rationale: "You need a digital foundation here. [Tool] gives you [function]
     with strong APIs, so once set up it becomes connectable."

IF existing tool is a dead end (no API, data trapped, fundamentally broken)
  → our_recommendation: "targeted_upgrade"
  → rationale: "Your current [tool] has no API — your data is trapped.
     [Replacement] opens up integration possibilities."

ELSE (foundation exists, tool has API or data is accessible)
  → our_recommendation: "connect_and_automate"
  → Adapt complexity and detail based on readiness profile
```

When we DO recommend buying, we always recommend API-ready tools. Every purchase is a step toward their connected future.

## What Changes

### 1. three_options.py — Prompt Rewrite

**Remove:**
```
our_recommendation MUST be "connect_and_automate" UNLESS the existing tool literally has no API
```

**Replace with:**
```
RECOMMENDATION DECISION:
Evaluate each finding against the client's readiness profile.

1. If no digital tool exists for this function → recommend "targeted_upgrade"
   (buy the foundation, always API-ready, frame as step toward connected future)
2. If existing tool is a dead end (no API, no export, data trapped) → recommend "targeted_upgrade"
   (replace with API-ready alternative)
3. Everything else → recommend "connect_and_automate"
   (adapt complexity to client readiness — simpler automations for early-stage,
    full AI workflows for mature stacks)

Always generate all three options. Always explain WHY this recommendation fits THIS client.
When recommending targeted_upgrade, frame it as the foundation for future automation.
```

**Add full readiness context to prompt:**
```
CLIENT READINESS PROFILE:
- Infrastructure: {digitized / partial / paper-based}
- Build Willingness: {eager / open / prefers-turnkey}
- AI Experience: {none / dabbled / active-user}
- Stack API Readiness: {most-apis / mixed / mostly-closed}
- Urgency: {this_week / this_month / this_quarter / no_rush}
- Preference: {buy / connect / build / hire}
```

**Add to connect_and_automate template:**
```
- prerequisite: (optional) what must be in place first
- build_time: "X weeks (solo) / Y days (guided)"
- diy_complexity: "low / moderate / high"
```

### 2. report_service.py — Readiness Profile Builder

New function: `_build_readiness_profile(quiz_answers) -> dict`

Maps raw quiz fields to clean prompt vocabulary:

| Quiz Field | Mapped To | Logic |
|---|---|---|
| `implementation_capability` + `ai_tools_used` | `ai_experience` | none/dabbled/active-user |
| `implementation_preference` | `build_willingness` | buy/hire→prefers-turnkey, connect→open, build→eager |
| `technology_comfort` (1-10) | feeds into build_willingness | <4 leans turnkey, >7 leans eager |
| `current_tools` + `integration_issues` | `infrastructure` | paper-based/partial/digitized |
| `existing_stack_api_ready` | `stack_api_readiness` | most-apis/mixed/mostly-closed |
| `implementation_urgency` | `urgency` | pass through |

This profile gets passed into the three_options skill context alongside existing fields.

### 3. NumberedRecommendations.tsx — Small Frontend Addition

- Show `prerequisite` note on connect_and_automate card when present (e.g., "First: set up digital scheduling")
- Show dual build time when both solo and guided values exist
- No structural changes to the three-card layout

### 4. Sample Reports — Update Examples

Update 1-2 findings in each sample report to demonstrate adaptive recommendations:
- One finding where connect_and_automate is recommended (client has API-ready tools)
- One finding where targeted_upgrade is recommended (no foundation or dead-end tool)
- Shows the engine adapting within a single report

## What Does NOT Change

- Quiz questions (signals already captured)
- The three option keys (connect_and_automate / enhance_with_ai / targeted_upgrade)
- Color coding (emerald / blue / amber)
- Playbook generator structure
- Teaser service
- Landing page or industry pages
- No upsell language in the report — the strategy call (€497) sells itself through report quality

## Key Principles

1. **All three options always shown** — client sees the full picture
2. **Recommendation adapts per finding** — one report can have a mix of "buy this" and "build this"
3. **Even "buy" points toward connect** — we never recommend a tool without APIs
4. **AI-assisted building is for everyone** — we never say "you're not technical enough to build"
5. **Complexity adapts, access doesn't** — simpler automations for early-stage, full AI workflows for mature stacks
6. **The report is pure analysis** — no sales language, no "contact us," the quality speaks for itself
