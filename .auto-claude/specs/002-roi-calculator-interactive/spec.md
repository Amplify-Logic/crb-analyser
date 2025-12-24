# ROI Calculator - Deep Interactive Experience

## Context
Read CLAUDE.md and docs/plans/2024-12-20-crb-philosophy-framework.md first for full project context.

The ROI Calculator is a key value driver. Customers should be able to model scenarios, adjust assumptions, and see real-time impact on their investment decision.

## Objective
Create a deeply interactive ROI calculator with scenario modeling, adjustable assumptions, and compelling visualizations that help customers understand their potential return.

## Current State
- Basic ROI Calculator component in `frontend/src/components/report/`
- ROI data models in `backend/src/models/roi_calculator.py`
- Static calculations with limited interactivity

## Deliverables

### 1. Scenario Modeling
- Allow customers to create "Conservative", "Moderate", "Aggressive" scenarios
- Enable comparison view between scenarios
- Persist scenarios to backend for future visits

### 2. Adjustable Assumptions
- Time to implement (weeks/months)
- Adoption rate (% of team using the solution)
- Efficiency gain multiplier
- Cost of implementation
- Hourly cost of employee time
- Show how each assumption affects final ROI

### 3. Interactive Visualizations
- ROI over time chart (break-even point highlighted)
- Value Saved vs Value Created breakdown
- Payback period visualization
- Cumulative benefit curve

### 4. What-If Analysis
- "What if adoption is only 50%?"
- "What if implementation takes 2x longer?"
- Real-time recalculation as sliders move

### 5. Export & Share
- Generate shareable ROI summary
- PDF-ready view
- Copy-to-clipboard for stakeholder sharing

## Acceptance Criteria
- [ ] 3+ scenario comparison working
- [ ] All assumptions adjustable with real-time recalculation
- [ ] Charts update smoothly without flicker
- [ ] Break-even point clearly visualized
- [ ] Mobile-friendly sliders and controls
- [ ] Scenarios persist on page reload

## Files to Modify
- `frontend/src/components/report/ROICalculator.tsx`
- `backend/src/models/roi_calculator.py`
- `backend/src/routes/reports.py` (add scenario persistence endpoints)
- New: scenario comparison components

## Framework Integration
- Value Saved = Efficiency, cost reduction (Hours saved × hourly cost × 52 weeks)
- Value Created = Growth, new revenue, capabilities
- Both short-term (0-6mo), mid-term (6-18mo), long-term (18mo+) horizons
