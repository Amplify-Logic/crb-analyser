/**
 * VISUAL PREVIEW ONLY - Mock Report Page
 *
 * This page displays the new narrative report UI with hardcoded sample data.
 * NOT for production use - purely for visual testing of the new design.
 *
 * Route: /preview/report
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  AIReadinessGauge,
  TwoPillarsChart,
  ValueTimelineChart,
  VerdictCard,
  PersonalizedHeader,
  YourStorySection,
  StickyNav,
  TieredFindings,
  NumberedRecommendations,
  ValueSummary,
  UpgradeCTA,
} from '../components/report'

// ============================================
// MOCK DATA - Hardcoded for visual preview
// ============================================

const MOCK_COMPANY = {
  name: 'Alpine Dental Group',
  industry: 'Dental Practice',
  teamSize: '12-25 employees',
  techLevel: 'Moderate',
  budgetRange: '€500-2,000/mo',
  existingTools: ['Dentrix', 'Mailchimp', 'QuickBooks']
}

const MOCK_VERDICT = {
  recommendation: 'proceed' as const,
  headline: 'Strong Foundation for AI Adoption',
  subheadline: 'Your practice is well-positioned to benefit from targeted automation',
  reasoning: [
    'High volume of repetitive administrative tasks',
    'Existing tech stack supports integration',
    'Staff shows readiness for new tools'
  ],
  when_to_revisit: 'Review progress in 6 months',
  confidence: 'high' as const,
  color: 'green' as const
}

const MOCK_SUMMARY = {
  ai_readiness_score: 72,
  customer_value_score: 8,
  business_health_score: 7,
  key_insight: 'Your appointment scheduling and patient follow-up processes are consuming 15+ hours weekly that could be automated, freeing your team to focus on patient care.',
  total_value_potential: { min: 45000, max: 85000 },
  recommended_investment: { year_1_min: 8000, year_1_max: 15000 }
}

const MOCK_VALUE_SUMMARY = {
  value_saved: { subtotal: { min: 25000, max: 45000 } },
  value_created: { subtotal: { min: 20000, max: 40000 } },
  total: { min: 45000, max: 85000 }
}

const MOCK_FINDINGS = [
  {
    id: 'f1',
    title: 'Appointment Scheduling Bottleneck',
    description: 'Manual appointment scheduling and rescheduling consumes 8+ hours weekly. Patients often wait on hold or don\'t get timely confirmation.',
    customer_value_score: 9,
    business_health_score: 8,
    confidence: 'high' as const,
    time_horizon: 'short' as const,
    value_saved: { hours_per_week: 8, hourly_rate: 35, annual_savings: 14560 },
    value_created: { description: 'Reduced no-shows', potential_revenue: 12000 }
  },
  {
    id: 'f2',
    title: 'Patient Recall System Gaps',
    description: 'Current recall system misses 30% of patients due to outdated contact info and manual tracking processes.',
    customer_value_score: 8,
    business_health_score: 9,
    confidence: 'high' as const,
    time_horizon: 'short' as const,
    value_saved: { hours_per_week: 4, hourly_rate: 35, annual_savings: 7280 },
    value_created: { description: 'Recovered appointments', potential_revenue: 25000 }
  },
  {
    id: 'f3',
    title: 'Insurance Verification Delays',
    description: 'Staff spends 6+ hours weekly on manual insurance verification, often causing appointment delays.',
    customer_value_score: 7,
    business_health_score: 8,
    confidence: 'medium' as const,
    time_horizon: 'mid' as const,
    value_saved: { hours_per_week: 6, hourly_rate: 35, annual_savings: 10920 }
  },
  {
    id: 'f4',
    title: 'Treatment Plan Follow-up',
    description: 'Incomplete treatment plans lack systematic follow-up, resulting in lost revenue.',
    customer_value_score: 7,
    business_health_score: 7,
    confidence: 'medium' as const,
    time_horizon: 'mid' as const,
    value_created: { description: 'Treatment completion', potential_revenue: 18000 }
  },
  {
    id: 'f5',
    title: 'Review Management Opportunity',
    description: 'No systematic process for collecting and responding to patient reviews.',
    customer_value_score: 6,
    business_health_score: 6,
    confidence: 'medium' as const,
    time_horizon: 'long' as const
  },
  {
    id: 'f6',
    title: 'Staff Scheduling Inefficiency',
    description: 'Manual staff scheduling creates occasional coverage gaps and overtime.',
    customer_value_score: 5,
    business_health_score: 6,
    confidence: 'low' as const,
    time_horizon: 'long' as const
  },
  {
    id: 'f7',
    title: 'Inventory Tracking Gaps',
    description: 'Basic inventory management leads to occasional stockouts and rush orders.',
    customer_value_score: 4,
    business_health_score: 5,
    confidence: 'low' as const,
    time_horizon: 'long' as const
  }
]

const MOCK_RECOMMENDATIONS = [
  {
    id: 'r1',
    title: 'Implement AI-Powered Appointment Scheduling',
    description: 'Deploy an intelligent scheduling system that handles booking, confirmations, and rescheduling automatically via text/email.',
    priority: 'high' as const,
    roi_percentage: 340,
    payback_months: 4,
    options: {
      off_the_shelf: { name: 'NexHealth', vendor: 'NexHealth', monthly_cost: 299, implementation_weeks: 2 },
      best_in_class: { name: 'Weave', vendor: 'Weave', monthly_cost: 449, implementation_weeks: 3 },
      custom_solution: { approach: 'Custom integration with Dentrix using AI scheduling logic', estimated_cost: { min: 5000, max: 12000 }, implementation_weeks: 8 }
    },
    our_recommendation: 'off_the_shelf',
    recommendation_rationale: 'NexHealth offers the best balance of features, Dentrix integration, and price. Quick implementation means you\'ll see ROI within 4 months.',
    assumptions: ['Current Dentrix version is compatible', 'Staff can dedicate 4 hours for training']
  },
  {
    id: 'r2',
    title: 'Automate Patient Recall & Reactivation',
    description: 'Set up automated recall sequences with personalized outreach based on patient history and preferences.',
    priority: 'high' as const,
    roi_percentage: 520,
    payback_months: 3,
    options: {
      off_the_shelf: { name: 'RevenueWell', vendor: 'RevenueWell', monthly_cost: 199, implementation_weeks: 2 },
      best_in_class: { name: 'Weave (if bundled)', vendor: 'Weave', monthly_cost: 150, implementation_weeks: 1 },
      custom_solution: { approach: 'Build custom recall automation with existing Mailchimp', estimated_cost: { min: 2000, max: 5000 }, implementation_weeks: 4 }
    },
    our_recommendation: 'best_in_class',
    recommendation_rationale: 'Bundling with Weave (if you choose that for scheduling) provides best value. Otherwise, RevenueWell is proven in dental.',
    assumptions: ['Patient contact data is >80% accurate', 'HIPAA-compliant messaging setup']
  },
  {
    id: 'r3',
    title: 'Streamline Insurance Verification',
    description: 'Implement real-time insurance eligibility verification to reduce delays and staff time.',
    priority: 'medium' as const,
    roi_percentage: 280,
    payback_months: 5,
    options: {
      off_the_shelf: { name: 'Vyne Dental', vendor: 'Vyne', monthly_cost: 149, implementation_weeks: 2 },
      best_in_class: { name: 'Dentrix Ascend', vendor: 'Henry Schein', monthly_cost: 299, implementation_weeks: 4 },
      custom_solution: { approach: 'API integration with clearinghouse', estimated_cost: { min: 8000, max: 15000 }, implementation_weeks: 10 }
    },
    our_recommendation: 'off_the_shelf',
    recommendation_rationale: 'Vyne Dental provides solid coverage verification at a reasonable price point. No need for complex custom solutions here.',
    assumptions: ['Current clearinghouse supports electronic verification']
  }
]

// ============================================
// PREVIEW COMPONENT
// ============================================

export default function ReportPreview() {
  const [activeSection, setActiveSection] = useState('story')
  const [showTools, setShowTools] = useState(false)

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

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Preview Banner */}
      <div className="bg-yellow-400 text-yellow-900 text-center py-2 text-sm font-medium">
        VISUAL PREVIEW ONLY - Mock Data - Not Connected to Backend
      </div>

      {/* Personalized Header */}
      <PersonalizedHeader
        companyName={MOCK_COMPANY.name}
        industry={MOCK_COMPANY.industry}
        teamSize={MOCK_COMPANY.teamSize}
        techLevel={MOCK_COMPANY.techLevel}
        budgetRange={MOCK_COMPANY.budgetRange}
        tier="quick"
        onExportPDF={() => alert('Export disabled in preview')}
      />

      {/* Sticky Navigation */}
      <StickyNav
        sections={sections}
        activeSection={activeSection}
        onSectionClick={scrollToSection}
      />

      <div className="max-w-4xl mx-auto px-4 py-6">

        {/* SECTION 1: Your Story */}
        <YourStorySection
          keyInsight={MOCK_SUMMARY.key_insight}
          findingsCount={MOCK_FINDINGS.length}
          mirroredStatements={[
            'We spend too much time on the phone scheduling appointments',
            'Patients often forget their recall appointments'
          ]}
          companyContext={{
            teamSize: MOCK_COMPANY.teamSize,
            techLevel: MOCK_COMPANY.techLevel,
            budget: MOCK_COMPANY.budgetRange,
            existingTools: MOCK_COMPANY.existingTools
          }}
        />

        {/* Verdict Card */}
        <div className="mb-6">
          <VerdictCard verdict={MOCK_VERDICT} />
        </div>

        {/* Score Dashboard - Compact */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wide">
                AI Readiness Score
              </p>
              <AIReadinessGauge score={MOCK_SUMMARY.ai_readiness_score} size="md" />
            </div>
            <div className="md:col-span-2">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 text-center uppercase tracking-wide">
                The Two Pillars
              </p>
              <TwoPillarsChart
                customerValue={MOCK_SUMMARY.customer_value_score}
                businessHealth={MOCK_SUMMARY.business_health_score}
              />
            </div>
          </div>
        </div>

        {/* SECTION 2: Tiered Findings */}
        <TieredFindings
          findings={MOCK_FINDINGS}
          heroCount={3}
          compactCount={4}
        />

        {/* SECTION 3: Numbered Recommendations (Actions) */}
        <NumberedRecommendations recommendations={MOCK_RECOMMENDATIONS} />

        {/* SECTION 4: Playbook (Value Projection) */}
        <section id="playbook" className="scroll-mt-20 mb-8">
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-1">
              Your Playbook
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              Investment breakdown and projected returns
            </p>
          </div>

          {/* Value Summary */}
          <div className="mb-6">
            <ValueSummary
              investment={MOCK_SUMMARY.recommended_investment.year_1_max}
              returnMin={MOCK_VALUE_SUMMARY.total.min}
              returnMax={MOCK_VALUE_SUMMARY.total.max}
            />
          </div>

          {/* Value Timeline Chart */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              3-Year Value Projection
            </h3>
            <ValueTimelineChart
              valueSaved={MOCK_VALUE_SUMMARY.value_saved.subtotal}
              valueCreated={MOCK_VALUE_SUMMARY.value_created.subtotal}
              totalInvestment={MOCK_SUMMARY.recommended_investment.year_1_max}
              showMilestones={true}
            />
          </div>

          {/* Playbook placeholder */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Interactive Playbook
              </h3>
              <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
                The full report includes step-by-step implementation phases with checkable tasks.
              </p>
            </div>
          </div>
        </section>

        {/* Expandable Tools Section */}
        <div className="mb-8">
          <button
            onClick={() => setShowTools(!showTools)}
            className="flex items-center gap-2 text-sm font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 mb-4"
          >
            {showTools ? 'Hide additional tools' : 'Show additional tools (ROI Calculator, Stack, Industry)'}
            <svg
              className={`w-4 h-4 transition-transform ${showTools ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <AnimatePresence>
            {showTools && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-6 overflow-hidden"
              >
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 text-center">
                  <p className="text-gray-500">ROI Calculator, Stack Analysis, and Industry Insights would appear here</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Upgrade CTA */}
        <UpgradeCTA currentTier="quick" reportId="preview-123" />

        {/* Footer */}
        <div className="mt-12 pt-6 border-t border-gray-200 dark:border-gray-700">
          <div className="text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Report generated by <span className="font-medium text-gray-900 dark:text-white">Ready Path</span>
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
              This report contains estimates based on provided data and industry benchmarks.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
