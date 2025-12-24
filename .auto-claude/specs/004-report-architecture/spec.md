# Report Architecture - Component Structure & Data Flow

## Context
Read CLAUDE.md and docs/plans/2024-12-20-crb-philosophy-framework.md first for full project context.

The report architecture should be clean, performant, and maintainable. Data should flow efficiently from backend to frontend.

## Objective
Refactor the report architecture for better performance, cleaner component structure, and optimal data flow.

## Current State
- ReportViewer.tsx is a large component with 8 tabs
- Data fetched on page load
- Some components tightly coupled
- React Query available but may be underutilized

## Deliverables

### 1. Component Structure
- Break ReportViewer into focused, single-responsibility components
- Create shared component library for report elements
- Implement proper component composition patterns
- Lazy load tabs that aren't immediately visible

### 2. Data Flow Optimization
- Implement React Query caching strategy
- Add optimistic updates for user interactions
- Minimize unnecessary re-renders
- Add proper loading and error states per section

### 3. State Management
- Clean separation between server state and UI state
- Proper context usage without prop drilling
- Report state persistence (restore scroll position, active tab)

### 4. Performance
- Lazy load heavy components (charts, diagrams)
- Implement virtualization for long lists (findings, recommendations)
- Add skeleton loading for each section
- Optimize bundle size

### 5. Type Safety
- Strong TypeScript types for all report data
- Zod validation for API responses
- Shared types between frontend and backend models

## Acceptance Criteria
- [ ] Lighthouse performance score 90+
- [ ] No unnecessary re-renders (verify with React DevTools)
- [ ] Clean component hierarchy
- [ ] All components properly typed
- [ ] Loading states for every async operation
- [ ] Error boundaries for graceful failures

## Files to Modify
- `frontend/src/pages/ReportViewer.tsx`
- `frontend/src/components/report/*.tsx`
- `frontend/src/services/apiClient.ts`
- `frontend/src/hooks/` (add report-specific hooks)

## Technical Notes
- Use React.lazy() for code splitting
- Use @tanstack/react-query for server state
- Consider using Zustand if complex client state needed
