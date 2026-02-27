# Visual Workflow Builder Enhancement — Terminal Prompt

> Copy-paste this entire prompt into a new Claude Code terminal.
> Run from: `/Users/larsmusic/CRB Analyser/crb-analyser`

---

## Context

We have a visual automation flow builder that renders flow diagrams inside CRB report recommendations. It uses `@xyflow/react` + `dagre` for layout.

**Existing components:**
- `frontend/src/components/report/AutomationFlowBuilder.tsx` — Main flow renderer (ReactFlow + dagre layout)
- `frontend/src/components/report/flow/FlowNodes.tsx` — Node types (existing_tool, new_tool, ai_layer, output)
- `frontend/src/components/report/NumberedRecommendations.tsx` — Already renders flows when `automation_flow` data exists on `connect_and_automate` options
- Backend generates `automation_flow: { nodes: [], edges: [] }` via `three_options.py` prompt

**Current node types:** `existing_tool` (green), `new_tool` (blue), `ai_layer` (purple), `output` (gray)

## What Needs Enhancement

### 1. Add New Node Types for AIOS Architecture

The current 4 node types are too basic for showing real AIOS architectures. Add these:

| Node Type | Color | Icon | Badge | Use For |
|-----------|-------|------|-------|---------|
| `mcp_server` | Indigo | `Cable` | "MCP" | MCP server connections (e.g., "HubSpot MCP", "Stripe MCP") |
| `automation_platform` | Orange | `Workflow` | "Automation" | Make, n8n, Zapier orchestration nodes |
| `data_store` | Cyan | `Database` | "Data" | Databases, spreadsheets, data warehouses |
| `human_step` | Amber | `User` | "Human" | Steps requiring human input/review |
| `trigger` | Rose | `Zap` | "Trigger" | Webhooks, scheduled triggers, events |
| `claude_code` | Violet | `Terminal` | "Claude Code" | Claude Code agent tasks |

Keep existing 4 types unchanged for backward compat.

### 2. Add System Architecture Diagram (New Component)

Create `frontend/src/components/report/SystemArchitectureDiagram.tsx`:

- Renders the **overall recommended AIOS architecture** for the client (not per-recommendation, but the big picture)
- Shows their existing stack on the left, the AI/automation layer in the middle, the outcomes on the right
- Uses the same ReactFlow/dagre stack but with a top-to-bottom layout (`rankdir: 'TB'`)
- Data comes from `report.system_architecture` field (already exists in DB as JSONB)

Structure:
```typescript
interface SystemArchitecture {
  layers: {
    existing_tools: { id: string; name: string; category: string }[]
    integration_layer: { id: string; name: string; type: 'mcp' | 'api' | 'webhook' | 'automation' }[]
    ai_layer: { id: string; name: string; type: 'agent' | 'workflow' | 'model' }[]
    outcomes: { id: string; name: string; value: string }[]
  }
  connections: { from: string; to: string; label?: string }[]
}
```

### 3. Enhance Per-Recommendation Flows

In `NumberedRecommendations.tsx`, improve the flow display:
- Show build time estimate next to the flow title ("How it connects — ~2 weeks")
- Add a "What you need" prerequisites chip list above the flow
- Show monthly cost badge inside the flow container
- Make flows collapsible (expanded by default for the recommended option)
- Add tooltip on nodes showing more detail on hover

### 4. Add Flow to TieredFindings (Compact Version)

In `TieredFindings.tsx`, when a finding has a linked recommendation with an automation_flow:
- Show a compact mini-flow (height: 120px, simplified labels)
- This gives users an immediate visual of "this is buildable" when scanning findings

### 5. Wire System Architecture into Report

In `ReportViewer.tsx`:
- Add a new tab or section called "Your AIOS Blueprint" between Findings and Recommendations
- Render the `SystemArchitectureDiagram` component
- If no `system_architecture` data exists, don't show the section

## Technical Constraints

- Use pnpm (not npm)
- @xyflow/react is already installed
- dagre is already installed
- Use lucide-react for icons (already in project)
- Follow existing dark mode patterns (dark: classes)
- Use framer-motion for animations (already in project)
- Keep bundle size small — lazy load the flow components (already done for AutomationFlowBuilder)

## Testing

After changes:
```bash
cd frontend && pnpm run dev
```

Load a sample report at `http://localhost:5174/report/sample` or use dev mode to see the flows render.

Check:
- Dark mode works
- Flow renders with proper layout
- New node types display correctly
- System architecture diagram renders
- Compact flow in findings works
- No console errors

## Files to Modify

1. `frontend/src/components/report/flow/FlowNodes.tsx` — Add new node types
2. `frontend/src/components/report/AutomationFlowBuilder.tsx` — Support new node types, add tooltips
3. **NEW:** `frontend/src/components/report/SystemArchitectureDiagram.tsx` — Full system architecture view
4. `frontend/src/components/report/NumberedRecommendations.tsx` — Enhanced flow display
5. `frontend/src/components/report/TieredFindings.tsx` — Compact mini-flow
6. `frontend/src/pages/ReportViewer.tsx` — Wire in SystemArchitectureDiagram
7. `frontend/src/components/report/index.ts` — Export new component

## Priority

Start with #1 (node types) and #2 (system architecture diagram) — these deliver the most visual impact. Then #3, #4, #5 in order.
