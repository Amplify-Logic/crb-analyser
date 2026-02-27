# Visual Workflow Builder Enhancement

> **Created:** 2026-02-27
> **Spec:** `docs/prompts/visual-workflow-builder-enhancement.md`
> **Status:** Draft

## CRB Context
- **Affected user journey stage:** Report (report viewing experience)
- **Industries impacted:** All (flows are generated per-recommendation)
- **Reference docs to load during execution:** `.claude/reference/frontend-development.md`

## Rollback Plan
All changes are frontend-only. Revert by: `git checkout main -- frontend/src/components/report/ frontend/src/pages/ReportViewer.tsx`

---

## Summary

Enhance the visual flow system in CRB reports with 6 new node types, a system architecture diagram, improved per-recommendation flows, and compact mini-flows in findings. All changes are frontend-only — no backend modifications needed.

**Key design decisions:**
- SystemArchitectureDiagram adapts the **existing** `system_architecture` field (no new backend field)
- AIOS Blueprint gets a **new sidebar section** between Findings and Actions (new `SidebarItem` type: `'blueprint'`)

---

## Tasks

### Task 1: Add 6 new node types to FlowNodes.tsx
**File:** `frontend/src/components/report/flow/FlowNodes.tsx`
**Type:** Edit existing file

**What to do:**

1. Add new lucide-react icon imports: `Cable`, `Workflow`, `Database` (already imported), `User`, `Zap`, `Terminal`

2. Expand the `FlowNodeData` union type to include the 6 new node types:
```typescript
nodeType: 'existing_tool' | 'new_tool' | 'ai_layer' | 'output'
  | 'mcp_server' | 'automation_platform' | 'data_store' | 'human_step' | 'trigger' | 'claude_code'
```

3. Add entries to `nodeConfig` for each new type:

| Key | borderColor | textColor | badge | Icon |
|-----|-------------|-----------|-------|------|
| `mcp_server` | `border-l-indigo-500` | `text-indigo-700 dark:text-indigo-400` | `MCP` | `Cable` |
| `automation_platform` | `border-l-orange-500` | `text-orange-700 dark:text-orange-400` | `Automation` | `Workflow` |
| `data_store` | `border-l-cyan-500` | `text-cyan-700 dark:text-cyan-400` | `Data` | `Database` |
| `human_step` | `border-l-amber-500` | `text-amber-700 dark:text-amber-400` | `Human` | `User` |
| `trigger` | `border-l-rose-500` | `text-rose-700 dark:text-rose-400` | `Trigger` | `Zap` |
| `claude_code` | `border-l-violet-500` | `text-violet-700 dark:text-violet-400` | `Claude Code` | `Terminal` |

Each entry follows the existing pattern: `bg: 'bg-white dark:bg-gray-800'`, `badgeBg` uses matching `bg-{color}-100 dark:bg-{color}-900/30 text-{color}-700 dark:text-{color}-400`.

4. Update `FlowLegend` to include the new node types. Add 6 new legend items with matching color dots.

**Verify:** No TypeScript errors. `pnpm run build` passes. Existing node types unchanged.

---

### Task 2: Add tooltip support to FlowNodes
**File:** `frontend/src/components/report/flow/FlowNodes.tsx`
**Type:** Edit existing file

**What to do:**

1. Extend `FlowNodeData` to accept an optional `description` field:
```typescript
interface FlowNodeData {
  label: string
  nodeType: '...'  // existing union
  description?: string
}
```

2. Add a simple CSS tooltip to the `FlowNode` component. When `description` is present, wrap the node in a `group` div and show a tooltip on hover:
```tsx
{nodeData.description && (
  <div className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-gray-900 text-white text-[10px] rounded shadow-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
    {nodeData.description}
  </div>
)}
```

3. Make the outer div `relative` and add `group` class.

**Verify:** Nodes without `description` render identically. Nodes with `description` show tooltip on hover.

---

### Task 3: Update AutomationFlowBuilder for new node types
**File:** `frontend/src/components/report/AutomationFlowBuilder.tsx`
**Type:** Edit existing file

**What to do:**

1. Update the `FlowNodeData.type` union in this file to match the expanded union from Task 1:
```typescript
type: 'existing_tool' | 'new_tool' | 'ai_layer' | 'output'
  | 'mcp_server' | 'automation_platform' | 'data_store' | 'human_step' | 'trigger' | 'claude_code'
```

2. Update the exported `AutomationFlow` interface so consumers get the expanded types.

3. Add an optional `compact` prop (default `false`). When `compact=true`:
   - Use smaller node dimensions: `NODE_WIDTH = 120`, `NODE_HEIGHT = 45`
   - Hide the badge text (just show icon + label)
   - Use smaller font sizes

4. Add an optional `direction` prop (`'LR' | 'TB'`, default `'LR'`). Pass it to dagre: `g.setGraph({ rankdir: direction, ... })`.

5. When `direction === 'TB'`, change Handle positions to `Top`/`Bottom` instead of `Left`/`Right`. Pass this as data to nodes or use a second node type registration.

**Implementation approach for direction-aware handles:** Create a second node component `FlowNodeTB` that uses Top/Bottom handles, and register it as `flowNodeTB`. In `layoutNodes`, use `type: direction === 'TB' ? 'flowNodeTB' : 'flowNode'`.

**Verify:** Existing flows render identically. New compact mode works. TB layout works.

---

### Task 4: Create SystemArchitectureDiagram component
**File:** `frontend/src/components/report/SystemArchitectureDiagram.tsx` (NEW)
**Type:** Create new file

**What to do:**

Create a ReactFlow-based system architecture diagram that adapts the existing `system_architecture` data.

1. **Interface** — accept the existing `SystemArchitecture` type from StackTab:
```typescript
interface SystemArchitectureDiagramProps {
  architecture: {
    existing_tools: { id: string; name: string; category: string; monthly_cost?: number }[]
    ai_layer: { id: string; name: string; category?: string }[]
    automations: { id: string; name: string; trigger: string; action: string; tools_used?: string[] }[]
    connections: { id: string; from_node: string; to_node: string; data_flow: string; integration_type: string }[]
  }
}
```

2. **Layout** — use dagre with `rankdir: 'TB'` (top-to-bottom). Create 3 visual rows:
   - **Row 1 (top):** Existing tools → use `existing_tool` node type
   - **Row 2 (middle):** AI layer + automations → use `ai_layer` and `automation_platform` node types
   - **Row 3 (bottom):** Derive outcomes from automations (action descriptions) → use `output` node type

3. **Edges** — map `connections` array to edges. Use `integration_type` to set edge style:
   - `'api'` → solid line
   - `'webhook'` → dashed line
   - `'mcp'` → animated line (indigo color)
   - Default → smooth step

4. **Container** — match the style from `AutomationFlowBuilder`: rounded border, header, footer legend. Title: "Your AIOS Blueprint".

5. **Height** — default 500px, auto-fit.

6. Import and use `flowNodeTypes` from `./flow/FlowNodes` (reuse existing node renderer). Also register the `flowNodeTB` type from Task 3.

7. Lazy-load this component.

**Verify:** Component renders with sample data. TB layout shows 3 clear layers. Dark mode works. No console errors.

---

### Task 5: Wire Blueprint into Sidebar
**File:** `frontend/src/components/report/Sidebar/Sidebar.tsx`
**Type:** Edit existing file

**What to do:**

1. Add `'blueprint'` to the `SidebarItem.type` union:
```typescript
type: 'overview' | 'finding' | 'action' | 'blueprint' | 'playbook' | 'tool'
```

2. Add `hasBlueprint` boolean prop to `SidebarProps`:
```typescript
interface SidebarProps {
  // ... existing
  hasBlueprint?: boolean
}
```

3. Add `blueprint: boolean` to `SectionState`, default `true`.

4. Add a "Blueprint" section between Findings and Actions in the nav:
```tsx
{/* Blueprint Section */}
{hasBlueprint && (
  <div className="mb-2">
    <button
      onClick={() => onItemClick({ type: 'blueprint', id: null })}
      className={itemClasses('blueprint', null)}
    >
      <span className="flex items-center gap-1">
        <Cable className="w-4 h-4" />
        AIOS Blueprint
      </span>
    </button>
  </div>
)}
```

Import `Cable` from lucide-react.

**Verify:** Blueprint item appears in sidebar when `hasBlueprint=true`. Clicking it sets activeItem correctly. Hidden when `hasBlueprint=false`.

---

### Task 6: Wire Blueprint into ReportViewer
**File:** `frontend/src/pages/ReportViewer.tsx`
**Type:** Edit existing file

**What to do:**

1. Add lazy import for SystemArchitectureDiagram:
```typescript
const SystemArchitectureDiagram = lazy(() => import('../components/report/SystemArchitectureDiagram'))
```

2. Pass `hasBlueprint` to Sidebar:
```typescript
hasBlueprint={!!report.system_architecture}
```

3. Add `'blueprint'` case to `renderContent()`:
```typescript
case 'blueprint':
  if (!report.system_architecture) return <div>Architecture data not available</div>
  return (
    <div className="space-y-6">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-1">
          Your AIOS Blueprint
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          How your tools connect into an AI-powered system
        </p>
      </div>
      <Suspense fallback={<div className="h-[500px] animate-pulse bg-gray-100 dark:bg-gray-700 rounded-xl" />}>
        <SystemArchitectureDiagram architecture={report.system_architecture} />
      </Suspense>
    </div>
  )
```

4. Update `getBreadcrumb()` to handle `'blueprint'` type.

5. Update navigation (prev/next) logic to include blueprint in the item sequence.

**Verify:** Blueprint section shows in sidebar when `system_architecture` exists. Clicking it renders the diagram. Navigation prev/next works through blueprint.

---

### Task 7: Enhance per-recommendation flow display
**File:** `frontend/src/components/report/NumberedRecommendations.tsx`
**Type:** Edit existing file

**What to do:**

1. **Flow title with build time:** Change the flow title to include build time when available:
```tsx
<AutomationFlowBuilder
  flow={rec.options.connect_and_automate.automation_flow}
  title={`How it connects${rec.options.connect_and_automate.build_time ? ` — ${rec.options.connect_and_automate.build_time}` : ''}`}
  height={200}
/>
```

2. **Prerequisites chip list:** Above the flow, show prerequisites if they exist:
```tsx
{rec.options.connect_and_automate.prerequisites?.length > 0 && (
  <div className="flex flex-wrap gap-1.5 mt-2 mb-2">
    <span className="text-xs text-gray-500 font-medium">Needs:</span>
    {rec.options.connect_and_automate.prerequisites.map((p: string, i: number) => (
      <span key={i} className="px-2 py-0.5 text-xs rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
        {p}
      </span>
    ))}
  </div>
)}
```

3. **Monthly cost badge inside flow container:** Show cost as a badge in the flow area header:
```tsx
{rec.options.connect_and_automate.monthly_cost && (
  <span className="text-xs font-medium text-gray-500">
    {rec.options.connect_and_automate.monthly_cost}
  </span>
)}
```

4. **Collapsible flows:** Wrap the automation flow in a collapsible section. Default expanded for the recommended option, collapsed for others:
```tsx
const [flowExpanded, setFlowExpanded] = useState(rec.our_recommendation === 'connect_and_automate')
```
Add a toggle button: "Show/Hide flow diagram".

**Verify:** Build time shows next to flow title. Prerequisites render as chips. Monthly cost appears. Flows are collapsible. Recommended option flow is expanded by default.

---

### Task 8: Add compact mini-flow to TieredFindings
**File:** `frontend/src/components/report/TieredFindings.tsx`
**Type:** Edit existing file

**What to do:**

1. In `HeroFindingCard`, the automation flow already renders at full height (200px). Keep this as-is.

2. In `CompactFindingCard`, add a compact mini-flow when `automation_flow` data exists:
```tsx
{finding.automation_flow?.nodes?.length > 0 && (
  <div className="mt-2">
    <Suspense fallback={<div className="h-[100px] animate-pulse bg-gray-100 dark:bg-gray-700 rounded-lg" />}>
      <AutomationFlowBuilder
        flow={finding.automation_flow as AutomationFlow}
        title=""
        height={100}
        compact
      />
    </Suspense>
  </div>
)}
```

This uses the `compact` prop added in Task 3 to render a simplified view (smaller nodes, no legend, reduced spacing).

**Verify:** Compact findings with `automation_flow` data show a mini flow. Compact findings without flow data render unchanged. Layout doesn't break with the extra height.

---

### Task 9: Export new component from index
**File:** `frontend/src/components/report/index.ts`
**Type:** Edit existing file

**What to do:**

Add the export for the new SystemArchitectureDiagram (lazy-loaded, so just the type/reference):
```typescript
export { default as SystemArchitectureDiagram } from './SystemArchitectureDiagram'
```

**Verify:** Import works from other files.

---

### Task 10: Final verification
**Type:** Manual testing

**What to check:**
1. `cd frontend && pnpm run build` — no TypeScript errors
2. `cd frontend && pnpm run dev` — app loads
3. Dark mode works on all new components
4. Existing flows render identically (no regression)
5. New node types display with correct colors/icons
6. System architecture diagram renders with TB layout
7. Blueprint appears in sidebar when data exists
8. Compact flows in findings work
9. No console errors
10. `pnpm run lint` passes

---

## Execution Order

```
Task 1 (new node types) ──→ Task 2 (tooltips) ──→ Task 3 (flow builder updates)
                                                        │
Task 5 (sidebar) ──→ Task 6 (ReportViewer wiring) ←────┤
                                                        │
Task 4 (SystemArchitectureDiagram) ────────────────────→┤
                                                        │
Task 7 (recommendation flows) ─────────────────────────→┤
                                                        │
Task 8 (compact mini-flows) ───────────────────────────→┤
                                                        │
Task 9 (exports) ←─────────────────────────────────────→┘
                                                        │
Task 10 (verification) ←───────────────────────────────→┘
```

**Parallelizable after Task 3:** Tasks 4, 5, 7, and 8 can run independently.

---

## Dependencies

- `@xyflow/react` — already installed
- `dagre` — already installed
- `lucide-react` — already installed (verify `Cable`, `Workflow`, `Terminal`, `Zap` icons exist)
- `framer-motion` — already installed

No new dependencies needed.
