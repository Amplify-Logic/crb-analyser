# Two-Panel Report Layout Design

**Date:** 2026-01-21
**Status:** Ready for implementation
**Problem:** Current scroll-based report causes context loss and poor wayfinding for users who return repeatedly

---

## Problem Statement

The current ReportViewer uses a long-scroll layout with a sticky header nav. Users reported two main frustrations:

1. **Context loss** - Scrolling past sections means losing sight of previous content
2. **Poor wayfinding** - Difficult to jump back to specific findings or recommendations

The report is primarily used as an **ongoing reference** (users return over weeks/months during implementation), not a one-time read. This means navigation speed and findability matter more than narrative flow.

---

## Solution: Two-Panel Layout

A fixed sidebar for navigation + a scrollable content panel for detail.

```
┌─────────────────┬────────────────────────────────────┐
│                 │                                    │
│   [Sidebar]     │   [Content Panel]                  │
│   Fixed         │   Scrolls independently            │
│   ~280px        │   Remaining width                  │
│                 │                                    │
└─────────────────┴────────────────────────────────────┘
```

**Why this works:**
- Navigation always visible (solves context loss)
- One-click access to any item (solves wayfinding)
- Progress tracking visible at a glance
- Familiar pattern (docs sites, email clients, VS Code)

---

## Sidebar Design

### Structure

```
┌─────────────────────┐
│ Company Name        │  ← Header
│ Industry            │
│ Score: 72/100       │
├─────────────────────┤
│ ▾ Overview          │  ← Collapsible sections
│     Verdict         │
│     Your Story      │
│                     │
│ ▾ Findings (6)      │  ← Count badge
│   ● Manual Invoicing│  ← Active item highlighted
│   ○ Appointment Gaps│
│   ○ Follow-up Chaos │
│   ○ Quote Delays    │
│   ◐ Paper Forms     │  ← ◐ = partially addressed
│   ○ Inventory       │
│                     │
│ ▾ Actions (4)       │
│   1. Automate Inv...│  ← Numbered for reference
│   2. Smart Sched... │
│   3. ...            │
│                     │
│ ▾ Playbook          │
│     Phase 1 (2/5)   │  ← Progress inline
│     Phase 2 (0/3)   │
│                     │
│ ▾ Tools             │  ← Collapsed by default
│     ROI Calculator  │
│     Stack Analysis  │
└─────────────────────┘
```

### Specifications

| Property | Value |
|----------|-------|
| Width | 280px fixed |
| Background | White (light) / Gray-900 (dark) |
| Border | 1px right border, gray-200/gray-700 |
| Scrolling | None - content must fit viewport |
| Section collapse | Remembers state in localStorage |

### Status Indicators

| Icon | Meaning |
|------|---------|
| ● | Fully addressed / completed |
| ◐ | Partially addressed / in progress |
| ○ | Not started / pending |

### Interaction

- Click any item → content panel updates
- Active item gets highlighted background + left border accent
- Collapse/expand sections with ▾/▸ toggle
- Hover state on items for affordance

---

## Content Panel Design

### General Layout

```
┌──────────────────────────────────────────────────────┐
│ Findings > Manual Invoicing              [breadcrumb]│
├──────────────────────────────────────────────────────┤
│                                                      │
│ [Full content here - scrolls as needed]              │
│                                                      │
│                                                      │
├──────────────────────────────────────────────────────┤
│ [← Prev: Overview]              [Next: Appointment →]│
└──────────────────────────────────────────────────────┘
```

### Specifications

| Property | Value |
|----------|-------|
| Padding | 32-48px |
| Max width | Content area, no max (fills space) |
| Scrolling | Independent vertical scroll |
| Breadcrumb | Top left, shows hierarchy |
| Prev/Next | Bottom, sticky or at content end |

---

## View Templates

### Overview View

Displays when "Overview" or "Verdict" selected.

**Contains:**
- Verdict card (recommendation + color status)
- AI Readiness gauge (72/100)
- Two Pillars chart (Customer Value / Business Health)
- Key insight quote
- Value potential range

```
┌──────────────────────────────────────────────────────┐
│ Overview                                             │
├──────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────┐ │
│ │ VERDICT: Proceed with Confidence        ✓ GREEN │ │
│ │ Your practice is well-positioned for AI...      │ │
│ └──────────────────────────────────────────────────┘ │
│                                                      │
│ ┌─────────────┐  ┌─────────────────────────────────┐ │
│ │   72/100    │  │ Customer Value   ████████░░ 78 │ │
│ │   [Gauge]   │  │ Business Health  ██████░░░░ 65 │ │
│ └─────────────┘  └─────────────────────────────────┘ │
│                                                      │
│ Key Insight                                          │
│ "Your biggest bottleneck is manual invoicing..."    │
│                                                      │
│ Total Value Potential: €45,000 - €62,000/year       │
└──────────────────────────────────────────────────────┘
```

---

### Finding Detail View

Displays when a specific finding is selected.

**Contains:**
- Title + confidence badge
- Problem description
- Impact metrics (3-column cards)
- Why it matters (Customer Value + Business Health)
- Sources
- Related Action link (prominent card)

```
┌──────────────────────────────────────────────────────┐
│ Findings > Manual Invoicing                          │
├──────────────────────────────────────────────────────┤
│ Manual Invoice Entry                          HIGH   │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                      │
│ THE PROBLEM                                          │
│ You're spending 8+ hours per week on manual          │
│ invoice entry, with a 12% error rate causing         │
│ payment delays and client friction.                  │
│                                                      │
│ IMPACT                                               │
│ ┌────────────┐ ┌────────────┐ ┌────────────┐        │
│ │ €24,000/yr │ │ 8 hrs/week │ │ 12% errors │        │
│ │ potential  │ │ recovered  │ │ eliminated │        │
│ └────────────┘ └────────────┘ └────────────┘        │
│                                                      │
│ WHY THIS MATTERS                                     │
│ • Customer Value: Faster invoices = faster payment  │
│ • Business Health: Reduces admin burden on staff    │
│                                                      │
│ SOURCES                                              │
│ Quiz response, Industry benchmark (Dental AI 2025)  │
│                                                      │
│ ┌──────────────────────────────────────────────────┐ │
│ │ RELATED ACTION                                   │ │
│ │ #1 Automate Invoice Generation              [→] │ │
│ │ ROI: 340% · Payback: 2.3 months                 │ │
│ └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

**Note:** The Related Action link should be a prominent card, not a footnote. This relationship is core to the report's value.

---

### Action Detail View

Displays when an action is selected. This is the deepest view - scrolling is expected.

**Contains:**
- Title + priority + ROI + payback period
- Why it matters
- Three Options (Off-the-Shelf / Best-in-Class / Custom)
- Our Recommendation with rationale
- Full CRB Analysis (Cost-Risk-Benefit breakdown)
- Assumptions list

```
┌──────────────────────────────────────────────────────┐
│ Actions > #1 Automate Invoicing                      │
├──────────────────────────────────────────────────────┤
│ 1. Automate Invoice Generation                       │
│ Priority: HIGH    ROI: 340%    Payback: 2.3 months  │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                      │
│ WHY IT MATTERS                                       │
│ • Customer Value: [explanation]                      │
│ • Business Health: [explanation]                     │
│                                                      │
│ ─────────────────────────────────────────────────── │
│ YOUR THREE OPTIONS                                   │
│ ─────────────────────────────────────────────────── │
│                                                      │
│ ┌─ OPTION A: Off-the-Shelf ─────────────────────┐   │
│ │ Xero + Dext Integration                       │   │
│ │ €49/month · 2 weeks to implement              │   │
│ │                                               │   │
│ │ ✓ Quick to deploy                             │   │
│ │ ✓ No technical expertise needed               │   │
│ │ ✗ Limited customization                       │   │
│ └───────────────────────────────────────────────┘   │
│                                                      │
│ ┌─ OPTION B: Best-in-Class ─────────────────────┐   │
│ │ Dentally + AI Receipt Processing              │   │
│ │ €129/month · 4 weeks to implement             │   │
│ │                                               │   │
│ │ ✓ Deep integration with your PMS              │   │
│ │ ✓ AI-powered receipt matching                 │   │
│ │ ✗ Higher monthly cost                         │   │
│ └───────────────────────────────────────────────┘   │
│                                                      │
│ ┌─ OPTION C: Custom Build ──────────────────────┐   │
│ │ Custom integration with your PMS              │   │
│ │ €2,000-4,000 one-time · 6-8 weeks             │   │
│ │                                               │   │
│ │ ✓ Exactly what you need                       │   │
│ │ ✓ No ongoing subscription                     │   │
│ │ ✗ Longer implementation time                  │   │
│ │ ✗ Maintenance responsibility                  │   │
│ └───────────────────────────────────────────────┘   │
│                                                      │
│ ─────────────────────────────────────────────────── │
│ OUR RECOMMENDATION                                   │
│ ─────────────────────────────────────────────────── │
│ Option B (Dentally + AI) because your practice      │
│ already uses Dentally and this builds on your       │
│ existing workflow without disruption.               │
│                                                      │
│ ─────────────────────────────────────────────────── │
│ COST-RISK-BENEFIT ANALYSIS                          │
│ ─────────────────────────────────────────────────── │
│                                                      │
│ COSTS                                                │
│ ┌─────────────┬─────────────┬─────────────┐        │
│ │ Short-term  │ Mid-term    │ Long-term   │        │
│ │ €1,500      │ €1,548/yr   │ €1,548/yr   │        │
│ └─────────────┴─────────────┴─────────────┘        │
│                                                      │
│ BENEFITS                                             │
│ ┌─────────────┬─────────────┬─────────────┐        │
│ │ Short-term  │ Mid-term    │ Long-term   │        │
│ │ €6,000      │ €24,000     │ €24,000     │        │
│ └─────────────┴─────────────┴─────────────┘        │
│                                                      │
│ RISKS                                                │
│ • Staff adoption resistance (Medium probability)    │
│   Impact: €2,000 · Mitigation: Training plan       │
│                                                      │
│ ─────────────────────────────────────────────────── │
│ ASSUMPTIONS                                          │
│ ─────────────────────────────────────────────────── │
│ • Current invoice volume: 200/month                 │
│ • Hourly rate used: €35                             │
│ • Error rate reduction: 12% → 2%                    │
│                                                      │
│ [← Prev: Action Overview]       [Next: Action #2 →] │
└──────────────────────────────────────────────────────┘
```

---

### Playbook View

Displays when a playbook phase is selected. This is a working checklist.

**Contains:**
- Phase title + progress (2/5 done)
- Timeline (Weeks 1-4)
- Tasks with checkboxes
- Subtasks (expandable)
- Notes field (user can add)
- Links to related Actions

```
┌──────────────────────────────────────────────────────┐
│ Playbook > Phase 1: Quick Wins                       │
├──────────────────────────────────────────────────────┤
│ Phase 1: Quick Wins                         2/5 done │
│ Timeline: Weeks 1-4                                  │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                      │
│ ┌────────────────────────────────────────────────┐   │
│ │ ✓  Set up Xero integration                     │   │
│ │    Week 1 · Connected to Action #1             │   │
│ │    ──────────────────────────────────────────  │   │
│ │    Notes: Completed Jan 15, took 2 hours       │   │
│ └────────────────────────────────────────────────┘   │
│                                                      │
│ ┌────────────────────────────────────────────────┐   │
│ │ ✓  Configure invoice templates                 │   │
│ │    Week 1-2 · Connected to Action #1           │   │
│ └────────────────────────────────────────────────┘   │
│                                                      │
│ ┌────────────────────────────────────────────────┐   │
│ │ ○  Train staff on new workflow                 │   │
│ │    Week 2 · Connected to Action #1             │   │
│ │    ──────────────────────────────────────────  │   │
│ │    Subtasks:                                   │   │
│ │    ○ Create training doc                       │   │
│ │    ○ Schedule 30-min session                   │   │
│ │    ○ Run first supervised invoice batch        │   │
│ └────────────────────────────────────────────────┘   │
│                                                      │
│ ┌────────────────────────────────────────────────┐   │
│ │ ○  Set up automated reminders                  │   │
│ │    Week 3 · Connected to Action #2             │   │
│ └────────────────────────────────────────────────┘   │
│                                                      │
│ ┌────────────────────────────────────────────────┐   │
│ │ ○  Review first month metrics                  │   │
│ │    Week 4 · Milestone                          │   │
│ │    ──────────────────────────────────────────  │   │
│ │    Expected: 50% reduction in invoice time     │   │
│ └────────────────────────────────────────────────┘   │
│                                                      │
│ [← Phase Overview]                [Next: Phase 2 →]  │
└──────────────────────────────────────────────────────┘
```

**Interactions:**
- Click checkbox → marks complete, syncs to backend
- Click task → expands to show subtasks/notes
- "Connected to Action #X" → links to that action
- Progress auto-updates in sidebar

---

### Tools Views

ROI Calculator, Stack Analysis, and Industry Insights each get their own content panel view when selected from the sidebar. These remain largely unchanged from current implementation, just displayed in the content panel instead of inline.

---

## Mobile Design

On screens < 768px, the sidebar becomes an overlay.

### Default State (Content Only)

```
┌─────────────────────────┐
│ ☰  Manual Invoicing     │  ← Hamburger + current item title
├─────────────────────────┤
│                         │
│ [Full content panel     │
│  takes entire screen]   │
│                         │
│                         │
├─────────────────────────┤
│ [←]    2 of 6    [→]    │  ← Bottom nav for prev/next
└─────────────────────────┘
```

### Sidebar Open (Overlay)

```
┌─────────────────────────┐
│ ✕ Close         Score:72│
├─────────────────────────┤
│ ▾ Overview              │
│ ▾ Findings (6)          │
│   ● Manual Invoicing ◄──│── Current highlighted
│   ○ Appointment Gaps    │
│   ○ Follow-up Chaos     │
│   ...                   │
│ ▾ Actions (4)           │
│   1. Automate Inv...    │
│   ...                   │
│ ▾ Playbook              │
│   Phase 1 (2/5)         │
│   Phase 2 (0/3)         │
│ ▾ Tools                 │
└─────────────────────────┘
```

**Behavior:**
- Hamburger tap → sidebar slides in from left
- Tap item → sidebar closes, content updates
- Tap outside or ✕ → sidebar closes
- Bottom bar always visible for sequential nav

---

## State Management

### URL Routing

Each view should have a URL for direct linking and browser back/forward:

```
/report/:id                     → Overview
/report/:id/verdict             → Verdict detail
/report/:id/finding/:findingId  → Finding detail
/report/:id/action/:actionId    → Action detail
/report/:id/playbook/:phaseId   → Playbook phase
/report/:id/tools/roi           → ROI Calculator
/report/:id/tools/stack         → Stack Analysis
/report/:id/tools/insights      → Industry Insights
```

### Local Storage

- Sidebar collapse states (which sections are expanded)
- Last viewed item (to restore on return)

### Backend Sync

- Playbook task completion status (already exists via `usePlaybookProgress`)

---

## Component Structure

```
ReportViewer/
├── ReportViewer.tsx           # Main layout, routing
├── Sidebar/
│   ├── Sidebar.tsx            # Container
│   ├── SidebarHeader.tsx      # Company name, score
│   ├── SidebarSection.tsx     # Collapsible section
│   └── SidebarItem.tsx        # Individual nav item
├── ContentPanel/
│   ├── ContentPanel.tsx       # Container with scroll
│   ├── Breadcrumb.tsx         # Navigation breadcrumb
│   └── PrevNextNav.tsx        # Bottom navigation
├── Views/
│   ├── OverviewView.tsx       # Verdict + scores
│   ├── FindingView.tsx        # Single finding detail
│   ├── ActionView.tsx         # Single action detail
│   ├── PlaybookView.tsx       # Playbook phase
│   ├── ROICalculatorView.tsx  # ROI tool
│   ├── StackView.tsx          # Stack analysis
│   └── InsightsView.tsx       # Industry insights
└── MobileSidebar.tsx          # Overlay for mobile
```

---

## Migration Strategy

### Phase 1: Layout Shell
- Create two-panel layout structure
- Move existing components into content panel views
- Implement basic sidebar navigation

### Phase 2: Sidebar Polish
- Add progress indicators
- Implement collapse/expand with localStorage
- Style active states

### Phase 3: URL Routing
- Add routes for each view
- Handle deep linking
- Browser back/forward support

### Phase 4: Mobile
- Implement overlay sidebar
- Add bottom prev/next nav
- Test touch interactions

### Phase 5: Polish
- Cross-links between Findings ↔ Actions
- Smooth transitions between views
- Loading states for view switches

---

## Success Metrics

After implementation, validate with users:

1. **Time to find specific item** - Should be < 3 seconds (one click)
2. **Context retention** - Users can describe what's in the sidebar while reading content
3. **Return visits** - Track if users return more frequently (indicates usefulness as reference)
4. **Playbook completion** - More tasks checked off (indicates working document, not just read-once)

---

## Open Questions

1. **Print/PDF export** - How should two-panel layout translate to PDF? Likely: linearize into single column for print.

2. **Keyboard navigation** - Should arrow keys move through sidebar items? (Nice to have for power users)

3. **Search** - Add Cmd+K search to jump to any finding/action by name? (Future enhancement)
