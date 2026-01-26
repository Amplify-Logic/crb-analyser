# Multi-Vertical Architecture Design

> Created: 2026-01-26
> Status: Approved design, not yet implemented

## Overview

Run 3 verticals in parallel to validate market fit faster:
- **Professional Services** (accounting, legal, consulting)
- **Dental Practices**
- **E-commerce**

Each vertical gets a tailored landing page and messaging while sharing core infrastructure.

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Differentiation level | Tailored messaging | Enough to feel "for me" without 3x maintenance |
| URL structure | Path-based (`/dental`, `/ecommerce`, `/professional-services`) | Simplest, one deployment, can migrate to subdomains later |
| Quiz flow | Industry pre-set from landing page | No redundant "what industry" question |
| Pricing | Same €147 all verticals | Simpler, validate model first |
| Implementation | Config-driven components | One codebase, content varies by config |

---

## URL Structure

```
readypath.ai/                           → Generic landing or redirect
readypath.ai/professional-services      → Pro Services landing
readypath.ai/professional-services/quiz → Quiz with industry pre-set
readypath.ai/professional-services/checkout
readypath.ai/professional-services/workshop

readypath.ai/dental                     → Dental landing
readypath.ai/dental/quiz
readypath.ai/dental/checkout
readypath.ai/dental/workshop

readypath.ai/ecommerce                  → Ecommerce landing
readypath.ai/ecommerce/quiz
readypath.ai/ecommerce/checkout
readypath.ai/ecommerce/workshop

readypath.ai/report/:id                 → Shared (industry in report data)
readypath.ai/dashboard                  → Shared
readypath.ai/admin/*                    → Shared
```

---

## Vertical Configuration System

```typescript
// frontend/src/config/verticals.ts

export type VerticalSlug = 'dental' | 'ecommerce' | 'professional-services'

export interface VerticalConfig {
  slug: VerticalSlug
  name: string
  tagline: string
  headline: string
  subheadline: string
  painPoints: Array<{ title: string; description: string; icon: string }>
  sampleFindings: Array<{ title: string; verdict: string; potential: string }>
  testimonials: Array<{ quote: string; author: string; company: string }>
  industryQuestions: string[]  // IDs of extra questions to include
  knowledgeBase: string        // backend path
  ctaText: string
  metaDescription: string
}

export const VERTICALS: Record<VerticalSlug, VerticalConfig> = {
  'dental': { /* ... */ },
  'ecommerce': { /* ... */ },
  'professional-services': { /* ... */ },
}
```

---

## Component Architecture

```
frontend/src/
├── pages/
│   ├── VerticalLanding.tsx      # Single component, reads config
│   ├── VerticalQuiz.tsx         # Wraps Quiz with vertical context
│   └── ... (existing pages)
├── config/
│   └── verticals.ts             # All vertical configs
├── contexts/
│   └── VerticalContext.tsx      # Provides vertical to children
├── components/
│   └── landing/
│       ├── HeroSection.tsx      # Config-driven
│       ├── PainPointsSection.tsx
│       ├── SampleFindings.tsx
│       ├── Testimonials.tsx
│       ├── HowItWorks.tsx       # Shared, no config
│       └── PricingSection.tsx   # Shared (€147)
```

### Shared (no vertical awareness)
- ReportViewer - industry from report data
- Dashboard - shows all reports
- Checkout - same price, same flow
- Workshop - questions from backend
- All admin pages

### Vertical-aware (read from config/context)
- Landing page sections
- Quiz entry (sets industry on session)
- Meta tags / SEO

---

## Backend Changes

### Knowledge Base Structure
```
backend/src/knowledge/
├── dental/                    # Exists
├── professional-services/     # Exists
├── ecommerce/                 # NEW - needs creation
│   ├── processes.json
│   ├── opportunities.json
│   ├── benchmarks.json
│   └── vendors.json
```

### API Changes
```python
# POST /api/quiz/start - accept industry param
{
  "industry": "dental"  # Pre-set from frontend URL
}
```

### What already works
- Report generation reads industry from session
- Vendor matching filters by industry
- Knowledge base loading by industry slug

---

## Content Per Vertical

### What differs:
- Landing page headline, subheadline, tagline
- Pain points (3-4 per vertical)
- Sample findings
- Testimonials / social proof
- 2-3 industry-specific quiz questions
- Meta description / SEO tags

### What's shared:
- "How it works" section
- Pricing (€147)
- CRB framework explanation
- Quiz core questions (5-6)
- Report structure and viewer
- Checkout and payment flow

---

## Vertical Content Needs

### Professional Services
- **Pain points:** Client onboarding, time tracking leakage, document chaos, client communication
- **Sample findings:** Intake automation, billing optimization, document management
- **Testimonials:** Accounting firm, law firm, consulting firm

### Dental
- **Pain points:** Patient recall, insurance verification, treatment planning, no-show management
- **Sample findings:** Recall automation, insurance pre-auth, patient communication
- **Testimonials:** Solo practice, group practice, DSO

### E-commerce
- **Pain points:** Inventory forecasting, customer support volume, returns processing, marketing attribution
- **Sample findings:** Support automation, inventory AI, personalization
- **Testimonials:** DTC brand, marketplace seller, B2B ecommerce

---

## Implementation Order (Future)

1. Create `frontend/src/config/verticals.ts` with all configs
2. Create `VerticalContext.tsx`
3. Create `VerticalLanding.tsx` component
4. Update React Router with nested vertical routes
5. Create `backend/src/knowledge/ecommerce/` knowledge base
6. Update quiz session creation to accept industry param
7. Test all 3 flows end-to-end

---

## Success Metrics

Track per vertical:
- Landing page → Quiz start rate
- Quiz completion rate
- Quiz → Checkout conversion
- Report satisfaction (NPS)

Compare across verticals to identify which resonates strongest.
