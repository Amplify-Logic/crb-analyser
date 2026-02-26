# Execute: Adaptive Recommendations + Visual Automation Flow

You are implementing an adaptive recommendation engine and visual automation flow builder for the CRB Analyser (product name: ReadyPath).

## Context

The AIOS pivot (completed, committed as `ded07c9`) hardcoded `our_recommendation = "connect_and_automate"` for 90%+ of cases. This is wrong — recommendations should adapt to each client's readiness level.

**Two axes determine the right recommendation:**
1. **Infrastructure readiness** — Do they have digital data and API-ready tools, or paper/spreadsheets?
2. **Build willingness** — Are they open to AI-assisted building, or want turnkey?

**Decision logic per finding:**
- No tool exists for this function → recommend `targeted_upgrade` (buy foundation, always API-ready)
- Existing tool is dead end (no API, data trapped) → recommend `targeted_upgrade` (replace)
- Everything else → recommend `connect_and_automate` (adapt complexity to readiness)

**Key principles:**
- All three options always shown — client sees the full picture
- One report can mix "buy this" and "build this" across different findings
- Even "buy" points toward connect — never recommend tools without APIs
- AI-assisted building is for everyone — never gatekeep based on tech proficiency
- Adapt the complexity of the HOW, not WHETHER they can build
- No upsell or sales language in the report — report quality sells the €497 strategy call
- The product is called **ReadyPath** (not CRB — CRB is the internal analysis framework)

**New feature — Visual Automation Flow:**
Each `connect_and_automate` option includes an `automation_flow` object with nodes and edges that gets rendered as a sleek, interactive flow diagram. Shows how existing tools connect through AI to produce the outcome. Must look professional, be immediately understandable, and make the architecture tangible.

## Plans

Read these two files before starting:
- `docs/plans/2026-02-26-adaptive-recommendations-design.md` — Design rationale and decisions
- `docs/plans/2026-02-26-adaptive-recommendations-plan.md` — Detailed implementation plan with 6 batches

## Execution Order

Execute the plan batch by batch. After each batch, verify before moving to the next.

**Batch 1:** Readiness profile builder function + tests (backend)
**Batch 2:** Prompt rewrite in three_options.py — adaptive logic + automation_flow field (backend)
**Batch 3:** Report service validation + fallback prompt updates (backend)
**Batch 4:** Install @xyflow/react + dagre, build AutomationFlowBuilder + FlowNodes components (frontend)
**Batch 5:** Integrate flow into NumberedRecommendations + TieredFindings, add prerequisite/complexity badges (frontend)
**Batch 6:** Update sample reports with adaptive examples + automation_flow data, full verification

## Reference Docs

Load only when working on the relevant batch:
- Backend batches (1-3): `.claude/reference/report-quality.md`
- Frontend batches (4-5): `.claude/reference/frontend-development.md`

## Verification

After each batch:
- Backend: `cd backend && python -m pytest tests/ -v --no-header`
- Frontend: `cd frontend && npx tsc --noEmit`
- Final: `cd frontend && pnpm build`
