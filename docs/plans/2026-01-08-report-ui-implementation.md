# Report UI/UX Redesign - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform the report from a 9-tab dashboard into a 4-section narrative scroll that guides users step-by-step to understanding.

**Architecture:** Refactor ReportViewer.tsx from tab-based navigation to single scrolling page with sticky nav. Create new components for narrative sections while reusing existing chart/card components where possible.

**Tech Stack:** React 18, TypeScript, Tailwind CSS, Framer Motion, Recharts

---

## CRB Context

- **Affected user journey stage:** Report viewing (post-payment)
- **Industries impacted:** All
- **Reference docs to load:** `.claude/reference/frontend-development.md`

## Rollback Plan

If this fails, revert by: `git checkout HEAD -- frontend/src/pages/ReportViewer.tsx frontend/src/components/report/`

---

## Task Overview

| # | Task | Effort | Dependencies |
|---|------|--------|--------------|
| 1 | Add company profile to Report type | Small | None |
| 2 | Create PersonalizedHeader component | Small | Task 1 |
| 3 | Create YourStory section component | Medium | Task 1 |
| 4 | Create StickyNav component | Small | None |
| 5 | Create TieredFindings component | Medium | None |
| 6 | Update ThreeOptions styling (purple glow) | Small | None |
| 7 | Create NumberedRecommendations component | Medium | Task 6 |
| 8 | Create ValueSummary component | Small | None |
| 9 | Improve ValueTimelineChart styling | Medium | Task 8 |
| 10 | Create UpgradeCTA component | Small | None |
| 11 | Refactor ReportViewer to narrative layout | Large | Tasks 2-10 |
| 12 | Test and polish | Medium | Task 11 |

---

## Task 1: Add Company Profile to Report Type

**Files:**
- Modify: `frontend/src/pages/ReportViewer.tsx:80-240` (interfaces)

**Step 1: Add company profile interface and extend Report type**

Add after line 212 (before Report interface):

```typescript
interface CompanyProfile {
  company_name: string
  industry: string
  industry_display: string
  team_size: string
  tech_level: string
  budget_range: string
  existing_tools?: string[]
}
```

Extend Report interface (around line 225):

```typescript
interface Report {
  id: string
  tier: string
  status: string
  company_profile?: CompanyProfile  // Add this line
  executive_summary: ExecutiveSummary
  // ... rest stays the same
}
```

**Step 2: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors related to CompanyProfile

**Step 3: Commit**

```bash
git add frontend/src/pages/ReportViewer.tsx
git commit -m "feat(report): add CompanyProfile type for personalization"
```

---

## Task 2: Create PersonalizedHeader Component

**Files:**
- Create: `frontend/src/components/report/PersonalizedHeader.tsx`

**Step 1: Create the component file**

```typescript
interface PersonalizedHeaderProps {
  companyName: string
  industry: string
  teamSize: string
  techLevel: string
  budgetRange: string
  tier: 'quick' | 'full'
  onExportPDF: () => void
}

export default function PersonalizedHeader({
  companyName,
  industry,
  teamSize,
  techLevel,
  budgetRange,
  tier,
  onExportPDF
}: PersonalizedHeaderProps) {
  return (
    <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-20">
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
              AI Readiness Report for
            </p>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-2">
              {companyName || 'Your Business'}
            </h1>
            <div className="flex flex-wrap items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              {teamSize && <span>{teamSize}</span>}
              {teamSize && industry && <span>•</span>}
              {industry && <span>{industry}</span>}
              {(teamSize || industry) && budgetRange && <span>•</span>}
              {budgetRange && <span>{budgetRange} budget</span>}
            </div>
          </div>
          <button
            onClick={onExportPDF}
            className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2 text-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            <span className="hidden sm:inline">Export PDF</span>
          </button>
        </div>
      </div>
    </div>
  )
}
```

**Step 2: Export from report index**

Add to `frontend/src/components/report/index.ts`:

```typescript
export { default as PersonalizedHeader } from './PersonalizedHeader'
```

**Step 3: Verify no TypeScript errors**

Run: `cd frontend && npx tsc --noEmit`
Expected: Clean compile

**Step 4: Commit**

```bash
git add frontend/src/components/report/PersonalizedHeader.tsx frontend/src/components/report/index.ts
git commit -m "feat(report): add PersonalizedHeader component with business name"
```

---

## Task 3: Create YourStory Section Component

**Files:**
- Create: `frontend/src/components/report/YourStorySection.tsx`

**Step 1: Create the component**

```typescript
import { motion } from 'framer-motion'

interface YourStorySectionProps {
  keyInsight: string
  findingsCount: number
  mirroredStatements?: string[]
  companyContext: {
    teamSize?: string
    techLevel?: string
    budget?: string
    existingTools?: string[]
  }
}

export default function YourStorySection({
  keyInsight,
  findingsCount,
  mirroredStatements = [],
  companyContext
}: YourStorySectionProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      id="story"
      className="scroll-mt-20"
    >
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 md:p-8 mb-6">
        <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-4">
          Your Story
        </h2>

        {/* The Hook */}
        <div className="bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 rounded-xl p-6 mb-6 border border-primary-200 dark:border-primary-800/30">
          <p className="text-xl md:text-2xl font-semibold text-gray-900 dark:text-white leading-relaxed">
            "{keyInsight}"
          </p>
        </div>

        {/* Journey Indicator */}
        <p className="text-gray-600 dark:text-gray-400 mb-6 flex items-center gap-2">
          <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 text-sm font-medium">
            {findingsCount}
          </span>
          <span>high-impact findings from your analysis</span>
        </p>

        {/* What You Told Us */}
        {mirroredStatements.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
              What You Told Us
            </h3>
            <div className="space-y-2">
              {mirroredStatements.map((statement, i) => (
                <p key={i} className="text-gray-700 dark:text-gray-300 italic">
                  "{statement}"
                </p>
              ))}
            </div>
          </div>
        )}

        {/* Your Context */}
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
            Your Context
          </h3>
          <div className="flex flex-wrap gap-3">
            {companyContext.teamSize && (
              <span className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm text-gray-700 dark:text-gray-300">
                {companyContext.teamSize}
              </span>
            )}
            {companyContext.techLevel && (
              <span className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm text-gray-700 dark:text-gray-300">
                {companyContext.techLevel} tech comfort
              </span>
            )}
            {companyContext.budget && (
              <span className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm text-gray-700 dark:text-gray-300">
                {companyContext.budget} budget
              </span>
            )}
            {companyContext.existingTools?.map((tool, i) => (
              <span key={i} className="px-3 py-1.5 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-sm text-blue-700 dark:text-blue-300">
                Using {tool}
              </span>
            ))}
          </div>
        </div>
      </div>
    </motion.section>
  )
}
```

**Step 2: Export from index**

Add to `frontend/src/components/report/index.ts`:

```typescript
export { default as YourStorySection } from './YourStorySection'
```

**Step 3: Verify compile**

Run: `cd frontend && npx tsc --noEmit`

**Step 4: Commit**

```bash
git add frontend/src/components/report/YourStorySection.tsx frontend/src/components/report/index.ts
git commit -m "feat(report): add YourStorySection with hook, mirror, and context"
```

---

## Task 4: Create StickyNav Component

**Files:**
- Create: `frontend/src/components/report/StickyNav.tsx`

**Step 1: Create the component**

```typescript
interface NavSection {
  id: string
  label: string
}

interface StickyNavProps {
  sections: NavSection[]
  activeSection: string
  onSectionClick: (id: string) => void
}

export default function StickyNav({ sections, activeSection, onSectionClick }: StickyNavProps) {
  return (
    <nav className="sticky top-[72px] z-10 bg-white/95 dark:bg-gray-800/95 backdrop-blur-sm border-b border-gray-200 dark:border-gray-700 -mx-4 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex gap-1 overflow-x-auto py-2 scrollbar-hide">
          {sections.map((section) => (
            <button
              key={section.id}
              onClick={() => onSectionClick(section.id)}
              className={`
                px-4 py-2 font-medium text-sm rounded-lg transition-colors whitespace-nowrap
                ${activeSection === section.id
                  ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                }
              `}
            >
              {section.label}
            </button>
          ))}
        </div>
      </div>
    </nav>
  )
}
```

**Step 2: Export from index**

Add to `frontend/src/components/report/index.ts`:

```typescript
export { default as StickyNav } from './StickyNav'
```

**Step 3: Commit**

```bash
git add frontend/src/components/report/StickyNav.tsx frontend/src/components/report/index.ts
git commit -m "feat(report): add StickyNav for narrative section navigation"
```

---

## Task 5: Create TieredFindings Component

**Files:**
- Create: `frontend/src/components/report/TieredFindings.tsx`

**Step 1: Create the component**

```typescript
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface Finding {
  id: string
  title: string
  description: string
  customer_value_score: number
  business_health_score: number
  confidence: 'high' | 'medium' | 'low'
  time_horizon: 'short' | 'mid' | 'long'
  value_saved?: { hours_per_week: number; hourly_rate: number; annual_savings: number }
  value_created?: { description: string; potential_revenue: number }
}

interface TieredFindingsProps {
  findings: Finding[]
  heroCount?: number
  compactCount?: number
}

function HeroFindingCard({ finding, index }: { finding: Finding; index: number }) {
  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(value)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="bg-white dark:bg-gray-800 rounded-xl border-2 border-primary-200 dark:border-primary-800 p-6 shadow-sm"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="px-2 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-xs font-bold rounded uppercase">
            Highest Impact
          </span>
        </div>
        <div className="flex gap-2">
          <span className="px-2 py-1 text-xs font-medium rounded bg-green-100 text-green-700">
            {finding.customer_value_score + finding.business_health_score > 15 ? '500%+ ROI' : 'High ROI'}
          </span>
          <span className="px-2 py-1 text-xs font-medium rounded bg-blue-100 text-blue-700 capitalize">
            {finding.time_horizon}
          </span>
        </div>
      </div>
      <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
        {finding.title}
      </h3>
      <p className="text-gray-600 dark:text-gray-400 mb-4">
        {finding.description}
      </p>
      {(finding.value_saved?.annual_savings || finding.value_created?.potential_revenue) && (
        <div className="flex gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          {finding.value_saved?.annual_savings && (
            <div>
              <p className="text-xs text-gray-500">Potential Savings</p>
              <p className="text-lg font-bold text-green-600">{formatCurrency(finding.value_saved.annual_savings)}/yr</p>
            </div>
          )}
          {finding.value_created?.potential_revenue && (
            <div>
              <p className="text-xs text-gray-500">Revenue Potential</p>
              <p className="text-lg font-bold text-blue-600">{formatCurrency(finding.value_created.potential_revenue)}</p>
            </div>
          )}
        </div>
      )}
    </motion.div>
  )
}

function CompactFindingCard({ finding }: { finding: Finding }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <h4 className="font-medium text-gray-900 dark:text-white mb-1 line-clamp-2">
        {finding.title}
      </h4>
      <div className="flex items-center gap-2 text-xs">
        <span className="text-gray-500 capitalize">{finding.time_horizon}</span>
        <span className="text-gray-300">•</span>
        <span className={`font-medium ${finding.confidence === 'high' ? 'text-green-600' : 'text-yellow-600'}`}>
          {finding.confidence} confidence
        </span>
      </div>
    </div>
  )
}

export default function TieredFindings({ findings, heroCount = 3, compactCount = 4 }: TieredFindingsProps) {
  const [showAll, setShowAll] = useState(false)

  // Sort by combined score
  const sortedFindings = [...findings].sort(
    (a, b) => (b.customer_value_score + b.business_health_score) - (a.customer_value_score + a.business_health_score)
  )

  const heroFindings = sortedFindings.slice(0, heroCount)
  const compactFindings = sortedFindings.slice(heroCount, heroCount + compactCount)
  const remainingFindings = sortedFindings.slice(heroCount + compactCount)

  return (
    <section id="findings" className="scroll-mt-20 mb-8">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-1">
          What We Found
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          {findings.length} findings from your analysis, prioritized by impact
        </p>
      </div>

      {/* Hero Findings */}
      <div className="space-y-4 mb-6">
        {heroFindings.map((finding, i) => (
          <HeroFindingCard key={finding.id} finding={finding} index={i} />
        ))}
      </div>

      {/* Compact Findings */}
      {compactFindings.length > 0 && (
        <div className="mb-4">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
            More Findings
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {compactFindings.map((finding) => (
              <CompactFindingCard key={finding.id} finding={finding} />
            ))}
          </div>
        </div>
      )}

      {/* Remaining Findings (expandable) */}
      {remainingFindings.length > 0 && (
        <div>
          <button
            onClick={() => setShowAll(!showAll)}
            className="flex items-center gap-2 text-sm font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700"
          >
            {showAll ? 'Show less' : `+ ${remainingFindings.length} more findings`}
            <svg
              className={`w-4 h-4 transition-transform ${showAll ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <AnimatePresence>
            {showAll && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3"
              >
                {remainingFindings.map((finding) => (
                  <CompactFindingCard key={finding.id} finding={finding} />
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </section>
  )
}
```

**Step 2: Export from index**

Add to `frontend/src/components/report/index.ts`:

```typescript
export { default as TieredFindings } from './TieredFindings'
```

**Step 3: Commit**

```bash
git add frontend/src/components/report/TieredFindings.tsx frontend/src/components/report/index.ts
git commit -m "feat(report): add TieredFindings with hero and compact cards"
```

---

## Task 6: Update Three Options Styling (Purple Glow)

**Files:**
- Modify: `frontend/src/pages/ReportViewer.tsx:698-738` (Three Options section)

**Step 1: Update the option card styling**

Find the Three Options grid (around line 700-738) and replace with:

```typescript
{/* Three Options */}
{rec.options && (
  <div className="mt-4">
    <h5 className="font-semibold text-gray-900 mb-3">Three Options</h5>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {rec.options.off_the_shelf && (
        <div className={`p-4 rounded-xl border-2 transition relative ${
          rec.our_recommendation === 'off_the_shelf'
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 shadow-lg shadow-primary-500/20 ring-2 ring-primary-200'
            : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800'
        }`}>
          {rec.our_recommendation === 'off_the_shelf' && (
            <span className="absolute -top-2 left-4 px-2 py-0.5 bg-primary-600 text-white text-xs font-bold rounded uppercase">
              Recommended
            </span>
          )}
          <p className={`font-semibold mt-1 ${rec.our_recommendation === 'off_the_shelf' ? 'text-primary-800 dark:text-primary-200' : 'text-gray-700 dark:text-gray-300'}`}>
            Option A: Off-the-Shelf
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{rec.options.off_the_shelf.name}</p>
          <p className={`text-lg font-bold mt-2 ${rec.our_recommendation === 'off_the_shelf' ? 'text-primary-600' : 'text-gray-900 dark:text-white'}`}>
            {formatCurrency(rec.options.off_the_shelf.monthly_cost)}/mo
          </p>
          <p className="text-xs text-gray-500">{rec.options.off_the_shelf.implementation_weeks} weeks to implement</p>
        </div>
      )}
      {rec.options.best_in_class && (
        <div className={`p-4 rounded-xl border-2 transition relative ${
          rec.our_recommendation === 'best_in_class'
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 shadow-lg shadow-primary-500/20 ring-2 ring-primary-200'
            : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800'
        }`}>
          {rec.our_recommendation === 'best_in_class' && (
            <span className="absolute -top-2 left-4 px-2 py-0.5 bg-primary-600 text-white text-xs font-bold rounded uppercase">
              Recommended
            </span>
          )}
          <p className={`font-semibold mt-1 ${rec.our_recommendation === 'best_in_class' ? 'text-primary-800 dark:text-primary-200' : 'text-gray-700 dark:text-gray-300'}`}>
            Option B: Best-in-Class
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{rec.options.best_in_class.name}</p>
          <p className={`text-lg font-bold mt-2 ${rec.our_recommendation === 'best_in_class' ? 'text-primary-600' : 'text-gray-900 dark:text-white'}`}>
            {formatCurrency(rec.options.best_in_class.monthly_cost)}/mo
          </p>
          <p className="text-xs text-gray-500">{rec.options.best_in_class.implementation_weeks} weeks to implement</p>
        </div>
      )}
      {rec.options.custom_solution && (
        <div className={`p-4 rounded-xl border-2 transition relative ${
          rec.our_recommendation === 'custom_solution'
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 shadow-lg shadow-primary-500/20 ring-2 ring-primary-200'
            : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800'
        }`}>
          {rec.our_recommendation === 'custom_solution' && (
            <span className="absolute -top-2 left-4 px-2 py-0.5 bg-primary-600 text-white text-xs font-bold rounded uppercase">
              Recommended
            </span>
          )}
          <p className={`font-semibold mt-1 ${rec.our_recommendation === 'custom_solution' ? 'text-primary-800 dark:text-primary-200' : 'text-gray-700 dark:text-gray-300'}`}>
            Option C: Custom AI
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{rec.options.custom_solution.approach?.substring(0, 60)}...</p>
          <p className={`text-lg font-bold mt-2 ${rec.our_recommendation === 'custom_solution' ? 'text-primary-600' : 'text-gray-900 dark:text-white'}`}>
            {formatCurrency(rec.options.custom_solution.estimated_cost?.min || 0)} - {formatCurrency(rec.options.custom_solution.estimated_cost?.max || 0)}
          </p>
          <p className="text-xs text-gray-500">{rec.options.custom_solution.implementation_weeks} weeks to implement</p>
        </div>
      )}
    </div>
  </div>
)}
```

**Step 2: Test the styling**

Run: `cd frontend && npm run dev`
Visit a report page and expand a recommendation to verify purple glow on recommended option.

**Step 3: Commit**

```bash
git add frontend/src/pages/ReportViewer.tsx
git commit -m "style(report): add purple glow to recommended Three Options card"
```

---

## Task 7: Create NumberedRecommendations Component

**Files:**
- Create: `frontend/src/components/report/NumberedRecommendations.tsx`

**Step 1: Create the component**

This component wraps recommendations with numbered labels and handles expansion state. Create a new file with the recommendations display logic extracted from ReportViewer.tsx but with numbered headers and first-expanded-by-default behavior.

```typescript
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface Recommendation {
  id: string
  title: string
  description: string
  priority: 'high' | 'medium' | 'low'
  roi_percentage: number
  payback_months: number
  options: {
    off_the_shelf: { name: string; vendor: string; monthly_cost: number; implementation_weeks: number }
    best_in_class: { name: string; vendor: string; monthly_cost: number; implementation_weeks: number }
    custom_solution: { approach: string; estimated_cost: { min: number; max: number }; implementation_weeks: number }
  }
  our_recommendation: string
  recommendation_rationale: string
  assumptions: string[]
}

interface NumberedRecommendationsProps {
  recommendations: Recommendation[]
}

export default function NumberedRecommendations({ recommendations }: NumberedRecommendationsProps) {
  const [expandedId, setExpandedId] = useState<string | null>(recommendations[0]?.id || null)

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(value)

  return (
    <section id="actions" className="scroll-mt-20 mb-8">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-1">
          What To Do
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          {recommendations.length} recommendations prioritized by impact
        </p>
      </div>

      <div className="space-y-3">
        {recommendations.map((rec, index) => (
          <div
            key={rec.id}
            className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden"
          >
            <div
              className="p-6 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition"
              onClick={() => setExpandedId(expandedId === rec.id ? null : rec.id)}
            >
              <div className="flex items-start gap-4">
                {/* Number Badge */}
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 flex items-center justify-center font-bold text-sm">
                  {index + 1}
                </div>

                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`px-2 py-1 text-xs font-medium rounded ${
                      rec.priority === 'high' ? 'bg-red-100 text-red-700' :
                      rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {rec.priority} priority
                    </span>
                    {rec.roi_percentage && (
                      <span className="px-2 py-1 text-xs font-medium rounded bg-green-100 text-green-700">
                        {rec.roi_percentage}% ROI
                      </span>
                    )}
                    {rec.payback_months && (
                      <span className="px-2 py-1 text-xs font-medium rounded bg-blue-100 text-blue-700">
                        {rec.payback_months}mo payback
                      </span>
                    )}
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {rec.title}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mt-1">
                    {rec.description}
                  </p>
                </div>

                <motion.svg
                  animate={{ rotate: expandedId === rec.id ? 180 : 0 }}
                  transition={{ duration: 0.2 }}
                  className="w-6 h-6 text-gray-400 flex-shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </motion.svg>
              </div>
            </div>

            <AnimatePresence>
              {expandedId === rec.id && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className="overflow-hidden"
                >
                  <div className="px-6 pb-6 border-t border-gray-200 dark:border-gray-700">
                    {/* Three Options with Purple Glow */}
                    {rec.options && (
                      <div className="mt-4">
                        <h5 className="font-semibold text-gray-900 dark:text-white mb-3">Three Options</h5>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          {/* Off-the-shelf */}
                          <div className={`p-4 rounded-xl border-2 transition relative ${
                            rec.our_recommendation === 'off_the_shelf'
                              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 shadow-lg shadow-primary-500/20'
                              : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800'
                          }`}>
                            {rec.our_recommendation === 'off_the_shelf' && (
                              <span className="absolute -top-2 left-4 px-2 py-0.5 bg-primary-600 text-white text-xs font-bold rounded uppercase">
                                Recommended
                              </span>
                            )}
                            <p className="font-semibold mt-1 text-gray-700 dark:text-gray-300">Option A: Off-the-Shelf</p>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{rec.options.off_the_shelf.name}</p>
                            <p className="text-lg font-bold mt-2 text-gray-900 dark:text-white">
                              {formatCurrency(rec.options.off_the_shelf.monthly_cost)}/mo
                            </p>
                            <p className="text-xs text-gray-500">{rec.options.off_the_shelf.implementation_weeks} weeks</p>
                          </div>
                          {/* Best-in-class */}
                          <div className={`p-4 rounded-xl border-2 transition relative ${
                            rec.our_recommendation === 'best_in_class'
                              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 shadow-lg shadow-primary-500/20'
                              : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800'
                          }`}>
                            {rec.our_recommendation === 'best_in_class' && (
                              <span className="absolute -top-2 left-4 px-2 py-0.5 bg-primary-600 text-white text-xs font-bold rounded uppercase">
                                Recommended
                              </span>
                            )}
                            <p className="font-semibold mt-1 text-gray-700 dark:text-gray-300">Option B: Best-in-Class</p>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{rec.options.best_in_class.name}</p>
                            <p className="text-lg font-bold mt-2 text-gray-900 dark:text-white">
                              {formatCurrency(rec.options.best_in_class.monthly_cost)}/mo
                            </p>
                            <p className="text-xs text-gray-500">{rec.options.best_in_class.implementation_weeks} weeks</p>
                          </div>
                          {/* Custom */}
                          <div className={`p-4 rounded-xl border-2 transition relative ${
                            rec.our_recommendation === 'custom_solution'
                              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 shadow-lg shadow-primary-500/20'
                              : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800'
                          }`}>
                            {rec.our_recommendation === 'custom_solution' && (
                              <span className="absolute -top-2 left-4 px-2 py-0.5 bg-primary-600 text-white text-xs font-bold rounded uppercase">
                                Recommended
                              </span>
                            )}
                            <p className="font-semibold mt-1 text-gray-700 dark:text-gray-300">Option C: Custom AI</p>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">{rec.options.custom_solution.approach}</p>
                            <p className="text-lg font-bold mt-2 text-gray-900 dark:text-white">
                              {formatCurrency(rec.options.custom_solution.estimated_cost?.min || 0)} - {formatCurrency(rec.options.custom_solution.estimated_cost?.max || 0)}
                            </p>
                            <p className="text-xs text-gray-500">{rec.options.custom_solution.implementation_weeks} weeks</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Why we recommend */}
                    {rec.recommendation_rationale && (
                      <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl">
                        <p className="font-semibold text-green-800 dark:text-green-300">Why we recommend this option:</p>
                        <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">{rec.recommendation_rationale}</p>
                      </div>
                    )}

                    {/* Assumptions */}
                    {rec.assumptions && rec.assumptions.length > 0 && (
                      <div className="mt-4 text-sm text-gray-500">
                        <p className="font-medium mb-1">Assumptions:</p>
                        <ul className="list-disc list-inside space-y-1">
                          {rec.assumptions.map((assumption, i) => (
                            <li key={i}>{assumption}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>
    </section>
  )
}
```

**Step 2: Export from index**

Add to `frontend/src/components/report/index.ts`:

```typescript
export { default as NumberedRecommendations } from './NumberedRecommendations'
```

**Step 3: Commit**

```bash
git add frontend/src/components/report/NumberedRecommendations.tsx frontend/src/components/report/index.ts
git commit -m "feat(report): add NumberedRecommendations with first-expanded default"
```

---

## Task 8: Create ValueSummary Component

**Files:**
- Create: `frontend/src/components/report/ValueSummary.tsx`

**Step 1: Create the component**

```typescript
interface ValueSummaryProps {
  investment: number
  returnMin: number
  returnMax: number
}

export default function ValueSummary({ investment, returnMin, returnMax }: ValueSummaryProps) {
  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(value)

  const roi = investment > 0 ? Math.round(((returnMin + returnMax) / 2) / investment) : 0

  return (
    <div className="bg-gradient-to-r from-primary-50 to-green-50 dark:from-primary-900/20 dark:to-green-900/20 rounded-xl p-6 border border-primary-200 dark:border-primary-800/30">
      <div className="flex flex-col md:flex-row items-center justify-center gap-6 md:gap-12 text-center">
        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
            Your Investment
          </p>
          <p className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white">
            {formatCurrency(investment)}
          </p>
          <p className="text-xs text-gray-500">first year</p>
        </div>

        <div className="text-3xl text-primary-400">→</div>

        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
            Your Return
          </p>
          <p className="text-2xl md:text-3xl font-bold text-green-600 dark:text-green-400">
            {formatCurrency(returnMin)} - {formatCurrency(returnMax)}
          </p>
          <p className="text-xs text-gray-500">3-year value</p>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-primary-200 dark:border-primary-800/30 text-center">
        <span className="text-lg font-semibold text-primary-700 dark:text-primary-300">
          {roi}x ROI
        </span>
      </div>
    </div>
  )
}
```

**Step 2: Export from index**

Add to `frontend/src/components/report/index.ts`:

```typescript
export { default as ValueSummary } from './ValueSummary'
```

**Step 3: Commit**

```bash
git add frontend/src/components/report/ValueSummary.tsx frontend/src/components/report/index.ts
git commit -m "feat(report): add ValueSummary component with investment -> return display"
```

---

## Task 9: Improve ValueTimelineChart Styling

**Files:**
- Modify: `frontend/src/components/report/charts/ValueTimelineChart.tsx`

**Step 1: Update chart styling for bolder appearance**

Update the chart colors and add milestone boxes below. Key changes:
- Thicker stroke lines (strokeWidth={3})
- Add milestone summary boxes component
- More prominent break-even marker

Replace the existing component with improved version that includes:
- Bolder colors (use primary purple and green)
- Larger break-even label
- Milestone summary boxes below chart

**Step 2: Test chart renders correctly**

Run: `cd frontend && npm run dev`
Check report page chart styling.

**Step 3: Commit**

```bash
git add frontend/src/components/report/charts/ValueTimelineChart.tsx
git commit -m "style(report): make ValueTimelineChart bolder with milestone callouts"
```

---

## Task 10: Create UpgradeCTA Component

**Files:**
- Create: `frontend/src/components/report/UpgradeCTA.tsx`

**Step 1: Create the component**

```typescript
interface UpgradeCTAProps {
  currentTier: 'quick' | 'full'
  reportId: string
}

export default function UpgradeCTA({ currentTier, reportId }: UpgradeCTAProps) {
  const upgradePrice = currentTier === 'quick' ? 350 : 0 // €497 - €147 = €350

  if (upgradePrice === 0) return null

  return (
    <section className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-700">
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 md:p-8 text-center">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          Ready to Move Forward?
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-lg mx-auto">
          Add a 60-minute strategy call to review your results and create an action plan with a CRB specialist.
        </p>

        <a
          href={`/checkout/upgrade?report=${reportId}&tier=call`}
          className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-xl font-medium transition-colors shadow-lg shadow-primary-500/25"
        >
          Add Strategy Call • €{upgradePrice}
        </a>

        <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
            Need implementation help?
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            We can connect you with vetted partners who specialize in your industry.
          </p>
          <span className="inline-block mt-2 text-xs text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
            Coming soon
          </span>
        </div>
      </div>
    </section>
  )
}
```

**Step 2: Export from index**

Add to `frontend/src/components/report/index.ts`:

```typescript
export { default as UpgradeCTA } from './UpgradeCTA'
```

**Step 3: Commit**

```bash
git add frontend/src/components/report/UpgradeCTA.tsx frontend/src/components/report/index.ts
git commit -m "feat(report): add UpgradeCTA component for strategy call upsell"
```

---

## Task 11: Refactor ReportViewer to Narrative Layout

**Files:**
- Modify: `frontend/src/pages/ReportViewer.tsx` (major refactor)

This is the main integration task. The goal is to:
1. Replace tab navigation with single scrolling page
2. Add sticky nav for jumping between sections
3. Integrate all new components
4. Remove old tab-based structure

**Step 1: Update imports**

Add to existing imports:

```typescript
import {
  PersonalizedHeader,
  YourStorySection,
  StickyNav,
  TieredFindings,
  NumberedRecommendations,
  ValueSummary,
  UpgradeCTA,
  // ... existing imports
} from '../components/report'
```

**Step 2: Add section tracking state**

Replace `activeTab` state with section tracking:

```typescript
const [activeSection, setActiveSection] = useState('story')

const sections = [
  { id: 'story', label: 'Your Story' },
  { id: 'findings', label: 'Findings' },
  { id: 'actions', label: 'Actions' },
  { id: 'playbook', label: 'Playbook' },
]

const scrollToSection = (id: string) => {
  const element = document.getElementById(id)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth' })
    setActiveSection(id)
  }
}
```

**Step 3: Replace the render structure**

Replace the main render return with narrative layout:
1. PersonalizedHeader at top
2. StickyNav below header
3. YourStorySection
4. TieredFindings
5. NumberedRecommendations
6. Playbook section (ValueSummary + chart + phases)
7. Optional tools section (ROI Calculator, Industry, Stack)
8. UpgradeCTA
9. Footer

**Step 4: Remove old tab navigation**

Delete the tabs array and tab button rendering.

**Step 5: Test the full narrative flow**

Run: `cd frontend && npm run dev`
Visit `/report/sample` and verify:
- Scrolling works
- Sticky nav highlights correct section
- All sections render
- Data flows correctly

**Step 6: Commit**

```bash
git add frontend/src/pages/ReportViewer.tsx
git commit -m "refactor(report): convert to narrative scroll layout with 4 sections"
```

---

## Task 12: Test and Polish

**Files:**
- Various - fix any issues found

**Step 1: Test all report scenarios**

Test cases:
- [ ] Sample report loads correctly
- [ ] Real report with full data
- [ ] Report with minimal data (missing fields)
- [ ] Mobile responsiveness
- [ ] Dark mode
- [ ] Export PDF still works

**Step 2: Fix any visual issues**

- Spacing consistency
- Color consistency (purple/green system)
- Typography hierarchy
- Card shadow/border consistency

**Step 3: Performance check**

Run: `cd frontend && npm run build`
Verify no build errors and bundle size is reasonable.

**Step 4: Final commit**

```bash
git add .
git commit -m "polish(report): fix visual issues and test edge cases"
```

---

## Summary

This plan transforms the report from a 9-tab dashboard into a guided narrative experience:

**Before:** Dashboard with 9 tabs, information overload
**After:** Single scrolling narrative with 4 sections, clear hierarchy

**New components created:**
- PersonalizedHeader
- YourStorySection
- StickyNav
- TieredFindings
- NumberedRecommendations
- ValueSummary
- UpgradeCTA

**Estimated implementation:** 12 tasks, can be done in batches with review checkpoints.
