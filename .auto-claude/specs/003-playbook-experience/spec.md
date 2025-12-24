# Playbook Experience - Implementation Guidance

## Context
Read CLAUDE.md and docs/plans/2024-12-20-crb-philosophy-framework.md first for full project context.

The Playbook is where strategy becomes action. It should feel like having a consultant guide customers through implementation step-by-step.

## Objective
Create a playbook experience that drives action, tracks progress, and provides clear implementation guidance that customers actually follow.

## Current State
- PlaybookTab component in `frontend/src/components/report/`
- Playbook models in `backend/src/models/playbook.py`
- Basic progress tracking UI ready, backend ~80% complete

## Deliverables

### 1. Interactive Roadmap
- Visual timeline with phases and milestones
- Expand/collapse task details
- Dependencies shown between tasks
- Critical path highlighted

### 2. Progress Tracking
- Checkbox completion for tasks
- Progress percentage per phase and overall
- Persist progress to backend
- Visual progress indicators (progress bars, completion badges)

### 3. Task Details
- Each task shows: Description, Estimated effort, Dependencies, Resources
- CRB breakdown visible (Cost, Risk, Benefit for each task)
- Links to recommended vendors/tools
- Success criteria for each task

### 4. Implementation Guidance
- Step-by-step instructions for each task
- Common pitfalls and how to avoid them
- "Quick Start" vs "Complete" implementation options
- Checklists within tasks

### 5. Export & Print
- Print-friendly view
- Export as checklist
- Email implementation plan

## Acceptance Criteria
- [ ] Progress persists across sessions
- [ ] Tasks have clear dependencies visualization
- [ ] CRB breakdown visible for each recommendation
- [ ] Mobile-friendly touch interactions
- [ ] Progress updates in real-time
- [ ] Print view is clean and useful

## Files to Modify
- `frontend/src/components/report/PlaybookTab.tsx`
- `backend/src/models/playbook.py`
- `backend/src/routes/playbook.py` (progress persistence)
- New: task detail components, progress tracking hooks

## Framework Integration
- Three-option pattern: Off-the-shelf, Best-in-class, Custom
- Time horizons: Short (0-6mo), Mid (6-18mo), Long (18mo+)
- CRB scoring visible on each recommendation
