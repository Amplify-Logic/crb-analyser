# AGENT 1: Frontend & UX

> **Mission:** Create a world-class user experience that makes the €147 investment feel like stealing.

---

## Context

**Product:** CRB Analyser - AI-powered Cost/Risk/Benefit analysis for AI implementation
**Price Point:** €147 (one-time)
**Target Users:** SMB owners/operators (20-200 employees) in Tech, E-commerce, Music/Studios
**Competition:** Free ChatGPT sessions (our reports must be 10x more valuable)

---

## Current State

```
frontend/
├── src/
│   ├── pages/
│   │   ├── Landing.tsx        # Basic landing
│   │   ├── Quiz.tsx           # Multi-step quiz
│   │   ├── Checkout.tsx       # Stripe checkout
│   │   ├── ReportViewer.tsx   # Report display (enhanced with charts)
│   │   └── ...
│   ├── components/
│   │   └── report/            # Chart components (new)
│   │       ├── AIReadinessGauge.tsx
│   │       ├── TwoPillarsChart.tsx
│   │       ├── ValueTimelineChart.tsx
│   │       ├── ROIComparisonChart.tsx
│   │       └── VerdictCard.tsx
│   └── ...
```

**What Works:**
- Basic quiz flow exists
- Report viewer has charts and verdict card
- Framer Motion animations integrated
- Recharts for data visualization

**What Needs Work:**
- Quiz is too shallow - needs depth for quality analysis
- Landing page doesn't convey €147 value proposition
- Report viewer needs polish and print optimization
- No progress/loading states during report generation
- Mobile experience needs attention

---

## Target State

### 1. Landing Page That Converts

**Hero Section:**
```
Headline: "Know Exactly Where AI Will (and Won't) Help Your Business"
Subhead: "Get a consultant-quality AI roadmap in 24 hours. €147, not €15,000."

CTA: "Start Your Analysis" → Quiz
Secondary: "See Sample Report" → Demo report
```

**Value Props (3 columns):**
1. **Honest Assessment** - "We tell you what NOT to do, saving you from expensive mistakes"
2. **Real Pricing** - "Actual vendor costs, not guesses. Updated monthly."
3. **Three Options Always** - "Off-the-shelf, best-in-class, or custom AI solution"

**Social Proof:**
- Sample finding cards from real reports
- "Trusted by 50+ companies" (once we have them)
- Industry logos

**How It Works (4 steps):**
1. Take 10-minute assessment
2. AI analyzes your business
3. Review findings & recommendations
4. Get your implementation roadmap

**Pricing Section:**
```
┌─────────────────────────────────────┐
│  CRB Analysis Report                │
│  €147 one-time                      │
│                                     │
│  ✓ 15-20 AI opportunities analyzed  │
│  ✓ Real vendor pricing & comparison │
│  ✓ ROI calculations with assumptions│
│  ✓ Implementation roadmap           │
│  ✓ Honest "don't do this" section   │
│  ✓ PDF report you can share         │
│                                     │
│  [Start Your Analysis]              │
└─────────────────────────────────────┘
```

### 2. Enhanced Quiz Flow

**Current:** ~10 questions, surface-level
**Target:** 20-25 questions, deep enough for quality analysis

**Quiz Sections:**

```typescript
const QUIZ_SECTIONS = [
  {
    id: 'company',
    title: 'About Your Business',
    questions: 5,
    fields: ['industry', 'sub_industry', 'company_size', 'revenue_range', 'business_model']
  },
  {
    id: 'operations',
    title: 'Current Operations',
    questions: 6,
    fields: ['core_processes', 'biggest_time_sinks', 'tools_used', 'data_systems', 'team_structure', 'remote_hybrid']
  },
  {
    id: 'pain_points',
    title: 'Challenges & Frustrations',
    questions: 5,
    fields: ['top_frustrations', 'failed_automations', 'manual_tasks', 'error_prone_areas', 'customer_complaints']
  },
  {
    id: 'ai_readiness',
    title: 'AI & Technology',
    questions: 4,
    fields: ['ai_tools_tried', 'tech_comfort', 'data_quality', 'integration_complexity']
  },
  {
    id: 'goals',
    title: 'Goals & Constraints',
    questions: 5,
    fields: ['success_definition', 'budget_range', 'timeline', 'decision_maker', 'blockers']
  }
];
```

**Quiz UX Requirements:**
- Progress bar showing section & overall completion
- Save progress (localStorage + backend)
- "Why we ask this" tooltips on complex questions
- Smart branching (skip irrelevant questions based on industry)
- Estimated time remaining
- Mobile-optimized (thumb-friendly buttons)

### 3. Report Generation Progress

**While report generates (60-120 seconds):**

```
┌─────────────────────────────────────────────────┐
│  Generating Your CRB Analysis...                │
│                                                 │
│  [████████████░░░░░░░░] 62%                    │
│                                                 │
│  ✓ Analyzing your intake responses              │
│  ✓ Researching industry benchmarks              │
│  ● Identifying AI opportunities...              │
│  ○ Calculating ROI projections                  │
│  ○ Generating recommendations                   │
│  ○ Building your roadmap                        │
│                                                 │
│  💡 Did you know?                               │
│  "Companies that implement AI strategically     │
│   see 3-5x ROI vs those that adopt randomly"   │
└─────────────────────────────────────────────────┘
```

**Requirements:**
- Real-time SSE updates from backend
- Animated step transitions
- Interesting facts/tips while waiting
- Don't let them navigate away (warn on close)

### 4. Report Viewer Excellence

**Structure:**
```
1. VERDICT CARD (top)
   - Green/Yellow/Orange/Gray based on recommendation
   - "Go For It" / "Proceed Cautiously" / "Wait" / "Not Yet"
   - Key reasoning bullets
   - What to do instead (if negative)

2. SCORE DASHBOARD
   - AI Readiness Gauge (0-100)
   - Two Pillars Chart (Customer Value + Business Health)
   - Key Insight quote

3. VALUE PROJECTION
   - 3-year timeline chart
   - Value Saved vs Value Created
   - Total potential range

4. TABS:
   - Summary (default)
     - ROI Comparison Chart
     - Top Opportunities cards
     - Not Recommended section
   - Findings (15-20)
     - Filterable by category, confidence, time horizon
     - Each finding shows CV/BH scores
   - Recommendations (5-10)
     - Expandable cards with Three Options
     - Highlighted "Our Recommendation"
     - Assumptions listed
   - Roadmap
     - Phase 1: Quick Wins (0-3 months)
     - Phase 2: Foundation (3-9 months)
     - Phase 3: Transformation (9-18 months)

5. FOOTER
   - Download PDF button
   - "Need help implementing?" CTA
   - Methodology notes link
```

**Print/PDF Optimization:**
```css
@media print {
  /* Hide navigation, buttons */
  /* Page breaks before major sections */
  /* Ensure charts render properly */
  /* Include methodology notes */
}
```

### 5. Three Options Pattern (Critical)

Every recommendation MUST show three paths:

```
┌─────────────────────────────────────────────────────────────────┐
│ Recommendation: Automated Customer Support                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  OPTION A: Off-the-Shelf          [RECOMMENDED]                │
│  ─────────────────────────────                                  │
│  Intercom with AI Bot                                           │
│  €89/month + €500 setup                                         │
│  4 weeks to implement                                           │
│  ✓ Quick to deploy  ✓ Proven solution  ✗ Limited customization │
│                                                                 │
│  OPTION B: Best-in-Class                                        │
│  ─────────────────────────────                                  │
│  Zendesk Suite + Ultimate.ai                                    │
│  €250/month + €2,000 setup                                      │
│  8 weeks to implement                                           │
│  ✓ Full features  ✓ Advanced AI  ✗ Higher cost  ✗ Complex      │
│                                                                 │
│  OPTION C: Custom AI Solution                                   │
│  ─────────────────────────────                                  │
│  Build with Claude API + your data                              │
│  €5,000-15,000 one-time + €200/month                           │
│  12-16 weeks to implement                                       │
│  ✓ Perfect fit  ✓ Competitive moat  ✗ Needs dev team           │
│                                                                 │
│  💡 Why we recommend Option A:                                  │
│  "Your support volume (50 tickets/week) doesn't justify         │
│   custom development yet. Start with Intercom, graduate         │
│   to custom when you hit 200+ tickets/week."                    │
│                                                                 │
│  🛠️ Build it yourself?                                          │
│  Tools: Claude API, Cursor IDE, Vercel                          │
│  Skills needed: Python/TypeScript, basic ML understanding       │
│  Time estimate: 80-120 hours for experienced developer          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6. Mobile Experience

**Requirements:**
- Quiz must be fully mobile-optimized (most users start on phone)
- Report viewer: horizontal scroll for charts on mobile
- Touch-friendly expandable sections
- Bottom sheet for filters instead of dropdowns
- Swipe between tabs

---

## Specific Tasks

### Phase 1: Core Fixes (Do First)
- [ ] Fix white screen issue (debug React rendering)
- [ ] Fix TypeScript errors blocking build
- [ ] Ensure report loads from API correctly
- [ ] Test all chart components render

### Phase 2: Landing Page
- [ ] Redesign hero section with value prop
- [ ] Add "How it works" section
- [ ] Create pricing card component
- [ ] Add sample report preview
- [ ] Mobile optimize

### Phase 3: Quiz Enhancement
- [ ] Expand to 25 questions across 5 sections
- [ ] Add progress indicator with sections
- [ ] Implement smart branching logic
- [ ] Add "why we ask" tooltips
- [ ] Save progress to localStorage
- [ ] Add estimated time remaining

### Phase 4: Report Generation UX
- [ ] Create progress page with SSE integration
- [ ] Add step-by-step status updates
- [ ] Include loading tips/facts
- [ ] Handle errors gracefully
- [ ] Prevent accidental navigation away

### Phase 5: Report Viewer Polish
- [ ] Implement Three Options pattern for recommendations
- [ ] Add "Build it yourself" section with tools
- [ ] Create filterable findings view
- [ ] Optimize for print/PDF
- [ ] Add "Need help implementing?" CTA
- [ ] Mobile optimize all components

### Phase 6: Final Polish
- [ ] Animation refinements
- [ ] Loading states everywhere
- [ ] Error boundaries
- [ ] Accessibility audit (WCAG 2.1 AA)
- [ ] Performance audit (Core Web Vitals)

---

## Dependencies

**Needs from Agent 2 (Backend):**
- SSE endpoint for report generation progress
- Quiz save/resume endpoints
- Report PDF generation endpoint

**Needs from Agent 3 (AI Engine):**
- Report structure with Three Options pattern
- Verdict generation logic
- "Build it yourself" recommendations

**Needs from Agent 4 (Data):**
- Industry-specific question branching rules
- Vendor data for Three Options

---

## Deliverables

1. `Landing.tsx` - Conversion-optimized landing page
2. `Quiz.tsx` - Enhanced 25-question flow with sections
3. `ReportProgress.tsx` - Generation progress with SSE
4. `ReportViewer.tsx` - Polished report with Three Options
5. `components/report/*` - All chart and card components
6. Mobile-responsive across all pages
7. Print-optimized report styles

---

## Quality Criteria

- [ ] Lighthouse Performance > 90
- [ ] Lighthouse Accessibility > 95
- [ ] All TypeScript errors resolved
- [ ] Works on Chrome, Firefox, Safari
- [ ] Mobile experience is excellent
- [ ] Report prints cleanly to PDF
- [ ] No console errors in production

---

## Tech Stack Reference

```
React 18 + TypeScript
Vite for bundling
TailwindCSS for styling
Framer Motion for animations
Recharts for data visualization
React Router for navigation
React Hook Form for quiz
```

---

## File Locations

```
frontend/src/
├── pages/
│   ├── Landing.tsx
│   ├── Quiz.tsx
│   ├── Checkout.tsx
│   ├── ReportProgress.tsx (new)
│   └── ReportViewer.tsx
├── components/
│   ├── report/
│   │   ├── VerdictCard.tsx
│   │   ├── ThreeOptionsCard.tsx (new)
│   │   ├── BuildItYourself.tsx (new)
│   │   └── charts/
│   ├── quiz/
│   │   ├── QuizSection.tsx
│   │   ├── ProgressBar.tsx
│   │   └── QuestionTypes/
│   └── landing/
│       ├── Hero.tsx
│       ├── HowItWorks.tsx
│       ├── PricingCard.tsx
│       └── SampleReport.tsx
└── hooks/
    ├── useQuizProgress.ts
    └── useReportStream.ts
```
