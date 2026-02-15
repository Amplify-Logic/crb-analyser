# Dev Mode Feedback Collection - Design Document

**Date:** 2025-12-27
**Status:** Implemented
**Author:** Claude + Lars

## Overview

This feature enables dev/admin feedback collection on generated reports to power the Signal Loop (SIL) - the core mechanism for improving report quality over time.

## Problem Statement

We needed a way to:
1. View all input data (quiz, research, interview) that went into a report
2. Rate and provide feedback on individual findings and recommendations
3. Note missing items and anti-patterns
4. Feed this back into the expertise system for continuous improvement

## Solution

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND                                │
│  ReportViewer.tsx                                           │
│  └── DevModePanel.tsx (visible when ?dev=true or DEV env)   │
│      ├── Input Context Tab (quiz, research, interview)      │
│      └── Feedback Form Tab (ratings, missing items, notes)  │
├─────────────────────────────────────────────────────────────┤
│                      BACKEND                                 │
│  /api/dev/reports/{id}/context - GET input data             │
│  /api/dev/feedback - POST feedback                          │
│  /api/dev/feedback/{id} - GET existing feedback             │
│  /api/dev/feedback/stats - GET aggregate stats              │
├─────────────────────────────────────────────────────────────┤
│                   EXPERTISE SYSTEM                           │
│  SelfImproveService.learn_from_feedback()                   │
│  └── Updates industry expertise based on feedback           │
│      ├── Reinforces excellent patterns                      │
│      ├── Demotes poor/wrong patterns                        │
│      ├── Adds anti-patterns                                 │
│      └── Notes missing findings/recommendations             │
└─────────────────────────────────────────────────────────────┘
```

### Components Created

#### Backend

| File | Purpose |
|------|---------|
| `src/models/feedback.py` | Data models: `ReportFeedback`, `FindingFeedback`, `RecommendationFeedback`, `ReportContext` |
| `src/routes/dev_feedback.py` | API routes for context view and feedback submission |
| `src/expertise/self_improve.py` | Added `learn_from_feedback()` method |

#### Frontend

| File | Purpose |
|------|---------|
| `src/components/report/DevModePanel.tsx` | Collapsible panel with context viewer and feedback form |

### Data Flow

```
1. User views report with ?dev=true
2. DevModePanel loads context from /api/dev/reports/{id}/context
3. User reviews input data (quiz answers, interview transcript, research)
4. User rates findings/recommendations (Excellent/Good/Okay/Poor/Wrong)
5. User notes what's missing or wrong
6. User submits feedback
7. Backend stores feedback in reports.dev_feedback
8. Backend triggers SelfImproveService.learn_from_feedback()
9. Expertise system updates:
   - Reinforced patterns get +5 frequency
   - Poor/wrong patterns get demoted or added to anti_patterns
   - Missing items added to pain_points or effective_patterns
```

### Feedback Model

```typescript
interface ReportFeedback {
  // Overall scores (1-10)
  overall_quality: number
  accuracy_score: number
  actionability_score: number
  relevance_score: number

  // Verdict
  verdict_appropriate: boolean
  verdict_notes?: string

  // Individual ratings
  findings_feedback: FindingFeedback[]
  recommendations_feedback: RecommendationFeedback[]

  // What's missing
  missing_findings: string[]
  missing_recommendations: string[]

  // Patterns learned
  industry_patterns_observed: string[]
  industry_anti_patterns: string[]

  // Notes
  general_notes?: string
}
```

### Access Control

- **Dev mode only**: All endpoints check `is_dev_mode()` or `?dev=true` param
- **Production**: Endpoints return 403 Forbidden
- This is intentional - feedback is for internal QA only

### UI Features

1. **Collapsible sections**: Quiz answers, company profile, interview transcript, research data
2. **One-click rating**: E/G/O/P/W buttons for each finding/recommendation
3. **Score sliders**: 1-10 scales with color coding
4. **Text areas**: For missing items and notes
5. **Success state**: Clear confirmation after submission

## Testing

To test:

1. Generate a report via the quiz flow
2. Navigate to `/report/{id}?dev=true`
3. Scroll down to see the yellow "Dev Mode Panel"
4. Click "Input Context" to see what went into the report
5. Click "Provide Feedback" to rate and submit

## Future Improvements

1. **Follow-up tracking**: 30/60/90 day surveys on implementation
2. **Actual ROI tracking**: Compare estimated vs actual results
3. **A/B testing**: Track which patterns lead to better outcomes
4. **Aggregate dashboards**: Visualize feedback trends over time

## Signal Loop Impact

This feature closes the loop:

```
Analysis #1:    Base accuracy
+ Feedback →    Identify weak patterns
Analysis #2:    +5% improvement (learned from feedback)
+ Feedback →    Reinforce what works
Analysis #N:    Compounding improvement
```

Every piece of feedback makes the next analysis better.
