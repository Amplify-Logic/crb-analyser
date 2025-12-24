# Report Visual Polish

## Context
Read CLAUDE.md and docs/plans/2024-12-20-crb-philosophy-framework.md first for full project context.

The CRB Analyser delivers a €147 interactive AI report that competes with €5,000+ consulting. The report viewer at `frontend/src/pages/ReportViewer.tsx` is the main product customers receive. It must feel premium.

## Objective
Transform the 8-tab report into a visually stunning, premium experience that justifies the price and creates "wow" moments.

## Current State
- ReportViewer.tsx with 8 tabs: Summary, Findings, Recommendations, Playbook, Stack, ROI, Insights, Roadmap
- Basic Recharts visualizations
- Tailwind CSS styling
- Framer Motion available but underutilized

## Deliverables

### 1. Typography & Spacing
- Implement consistent typographic hierarchy (headings, body, captions)
- Improve whitespace and breathing room between sections
- Add subtle background textures or gradients for depth

### 2. Chart Upgrades
- Enhance AIReadinessGauge with smooth animations
- Improve TwoPillarsChart with better visual metaphor
- Add micro-interactions on hover/focus
- Implement skeleton loading states

### 3. Card & Component Polish
- Add subtle shadows and depth
- Implement glass-morphism or modern card styles
- Add entrance animations for sections
- Create visual hierarchy between primary and secondary content

### 4. Color & Branding
- Ensure semantic color usage (blue=primary, green=success, yellow=warning, red=error, purple=AI)
- Add gradient accents for premium feel
- Implement dark mode support if not present

### 5. Micro-interactions
- Button hover/click feedback
- Tab transitions
- Scroll-triggered animations
- Loading states and skeletons

## Acceptance Criteria
- [ ] Report feels premium and polished
- [ ] All charts have smooth animations
- [ ] Consistent typography throughout
- [ ] No visual glitches or layout shifts
- [ ] Works on mobile and desktop
- [ ] Dark mode supported

## Files to Modify
- `frontend/src/pages/ReportViewer.tsx`
- `frontend/src/components/report/*.tsx`
- `frontend/src/components/ui/*.tsx`
- CSS/Tailwind configuration as needed

## Technical Notes
- Use Framer Motion for animations
- Use Recharts customization for chart styling
- Maintain existing data contracts with backend
