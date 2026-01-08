import { useState, useEffect, useCallback } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import apiClient from '../services/apiClient'
import {
  AIReadinessGauge,
  TwoPillarsChart,
  ValueTimelineChart,
  ROIComparisonChart,
  VerdictCard,
} from '../components/report'
import PlaybookTab from '../components/report/PlaybookTab'
import StackTab from '../components/report/StackTab'
import ROICalculator from '../components/report/ROICalculator'
import InsightsTab from '../components/report/InsightsTab'
import DevModePanel from '../components/report/DevModePanel'
import AutomationRoadmap from '../components/report/AutomationRoadmap'
import usePlaybookProgress from '../hooks/usePlaybookProgress'

// Premium skeleton loading component
function SkeletonPulse({ className = '' }: { className?: string }) {
  return (
    <div className={`relative overflow-hidden bg-gray-200 dark:bg-gray-700 ${className}`}>
      <motion.div
        className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/40 to-transparent"
        animate={{ x: ['0%', '200%'] }}
        transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
      />
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-primary-50/20 dark:from-gray-900 dark:via-gray-900 dark:to-primary-950/20">
      <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
        {/* Verdict skeleton */}
        <div className="rounded-3xl p-8 bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl shadow-glass-lg border border-gray-200/50">
          <div className="flex items-start gap-5">
            <SkeletonPulse className="w-16 h-16 rounded-2xl" />
            <div className="flex-1 space-y-3">
              <SkeletonPulse className="h-8 w-2/3 rounded-lg" />
              <SkeletonPulse className="h-4 w-1/2 rounded" />
              <div className="space-y-2 pt-4">
                <SkeletonPulse className="h-3 w-full rounded" />
                <SkeletonPulse className="h-3 w-5/6 rounded" />
                <SkeletonPulse className="h-3 w-4/6 rounded" />
              </div>
            </div>
          </div>
        </div>

        {/* Score dashboard skeleton */}
        <div className="rounded-3xl p-8 bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl shadow-glass border border-gray-200/50">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="flex flex-col items-center space-y-4">
              <SkeletonPulse className="h-4 w-32 rounded" />
              <SkeletonPulse className="w-44 h-28 rounded-full" />
            </div>
            <div className="md:col-span-2 space-y-4">
              <SkeletonPulse className="h-4 w-24 rounded mx-auto" />
              <div className="grid grid-cols-2 gap-4">
                <SkeletonPulse className="h-32 rounded-2xl" />
                <SkeletonPulse className="h-32 rounded-2xl" />
              </div>
            </div>
          </div>
        </div>

        {/* Chart skeleton */}
        <div className="rounded-3xl p-8 bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl shadow-glass border border-gray-200/50">
          <SkeletonPulse className="h-6 w-48 rounded mb-6" />
          <SkeletonPulse className="h-64 rounded-xl" />
        </div>
      </div>
    </div>
  )
}

interface Verdict {
  recommendation: 'proceed' | 'proceed_cautiously' | 'wait' | 'not_recommended'
  headline: string
  subheadline: string
  reasoning: string[]
  when_to_revisit: string
  what_to_do_instead?: string[]
  recommended_approach?: string[]
  confidence: 'high' | 'medium' | 'low'
  color: 'green' | 'yellow' | 'orange' | 'gray'
}

interface ExecutiveSummary {
  ai_readiness_score: number
  customer_value_score: number
  business_health_score: number
  key_insight: string
  total_value_potential: { min: number; max: number }
  top_opportunities: { title: string; value_potential: string; time_horizon: string }[]
  not_recommended: { title: string; reason: string }[]
  recommended_investment: { year_1_min: number; year_1_max: number }
  verdict?: Verdict
}

interface ValueSummary {
  value_saved: { subtotal: { min: number; max: number } }
  value_created: { subtotal: { min: number; max: number } }
  total: { min: number; max: number }
}

interface Finding {
  id: string
  title: string
  description: string
  category: string
  customer_value_score: number
  business_health_score: number
  value_saved?: { hours_per_week: number; hourly_rate: number; annual_savings: number }
  value_created?: { description: string; potential_revenue: number }
  confidence: 'high' | 'medium' | 'low'
  sources: string[]
  time_horizon: 'short' | 'mid' | 'long'
}

interface Recommendation {
  id: string
  title: string
  description: string
  why_it_matters: { customer_value: string; business_health: string }
  priority: 'high' | 'medium' | 'low'
  crb_analysis: {
    cost: { short_term: any; mid_term: any; long_term: any; total: number }
    risk: { description: string; probability: string; impact: number; mitigation: string }[]
    benefit: { short_term: any; mid_term: any; long_term: any; total: number }
  }
  options: {
    off_the_shelf: { name: string; vendor: string; monthly_cost: number; implementation_weeks: number; pros: string[]; cons: string[] }
    best_in_class: { name: string; vendor: string; monthly_cost: number; implementation_weeks: number; pros: string[]; cons: string[] }
    custom_solution: { approach: string; estimated_cost: { min: number; max: number }; implementation_weeks: number; pros: string[]; cons: string[] }
  }
  our_recommendation: string
  recommendation_rationale: string
  roi_percentage: number
  payback_months: number
  assumptions: string[]
}

interface Roadmap {
  short_term: { title: string; description: string; timeline: string; expected_outcome: string }[]
  mid_term: { title: string; description: string; timeline: string; expected_outcome: string }[]
  long_term: { title: string; description: string; timeline: string; expected_outcome: string }[]
}

interface Playbook {
  id: string
  recommendation_id: string
  option_type: string
  total_weeks: number
  phases: any[]
  personalization_context: {
    team_size: string
    technical_level: number
    budget_monthly: number
  }
}

interface SystemArchitecture {
  existing_tools: any[]
  ai_layer: any[]
  automations: any[]
  connections: any[]
  cost_comparison: any
}

interface IndustryInsights {
  industry: string
  industry_display_name: string
  adoption_stats: any[]
  opportunity_map: any
  social_proof: any[]
}

interface StackAssessmentItem {
  name: string
  slug: string
  api_score: number
  category?: string
}

interface StackAssessment {
  tools: StackAssessmentItem[]
  average_score: number
  verdict: 'strong_foundation' | 'good_foundation' | 'moderate_foundation' | 'limited_foundation' | 'no_tools'
  verdict_text: string
}

interface AutomationOpportunity {
  finding_id: string
  title: string
  impact_monthly: number
  diy_effort_hours: number
  approach: 'Connect' | 'Replace' | 'Either'
  tools_involved: string[]
  category: string
}

interface NextSteps {
  tier: string
  headline: string
  message: string
  cta_text: string
  cta_url: string
}

interface AutomationSummary {
  stack_assessment: StackAssessment
  opportunities: AutomationOpportunity[]
  total_monthly_impact: number
  total_diy_hours: number
  connect_count: number
  replace_count: number
  either_count: number
  next_steps: NextSteps
}

interface Report {
  id: string
  tier: string
  status: string
  executive_summary: ExecutiveSummary
  value_summary: ValueSummary
  findings: Finding[]
  recommendations: Recommendation[]
  roadmap: Roadmap
  methodology_notes: any
  created_at: string
  playbooks?: Playbook[]
  system_architecture?: SystemArchitecture
  industry_insights?: IndustryInsights
  automation_summary?: AutomationSummary
}

export default function ReportViewer() {
  const { id: reportId } = useParams<{ id: string }>()
  const [searchParams] = useSearchParams()
  const quizSessionId = searchParams.get('quiz')

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [report, setReport] = useState<Report | null>(null)
  const [activeTab, setActiveTab] = useState<'summary' | 'findings' | 'recommendations' | 'playbook' | 'stack' | 'roi' | 'insights' | 'roadmap'>('summary')
  const [expandedRec, setExpandedRec] = useState<string | null>(null)

  // Playbook progress tracking
  const {
    toggleTask,
    getCompletedTasks,
    isLoading: _progressLoading,
    isSyncing
  } = usePlaybookProgress({
    reportId: reportId || '',
    onError: (err) => console.error('Playbook progress error:', err)
  })

  // Build initial completed tasks map for PlaybookTab
  const getInitialCompletedTasks = useCallback(() => {
    if (!report?.playbooks) return {}
    const result: Record<string, string[]> = {}
    for (const pb of report.playbooks) {
      result[pb.id] = getCompletedTasks(pb.id)
    }
    return result
  }, [report?.playbooks, getCompletedTasks])

  // Handle task completion from PlaybookTab
  const handleTaskComplete = useCallback(async (playbookId: string, taskId: string, _completed: boolean) => {
    await toggleTask(playbookId, taskId)
  }, [toggleTask])

  useEffect(() => {
    loadReport()
  }, [reportId, quizSessionId])

  async function loadReport() {
    setLoading(true)
    setError(null)

    try {
      let response
      if (reportId === 'sample') {
        // Load sample demo report
        response = await apiClient.get<Report>(`/api/reports/sample`)
      } else if (reportId) {
        response = await apiClient.get<Report>(`/api/reports/public/${reportId}`)
      } else if (quizSessionId) {
        response = await apiClient.get<{ id: string }>(`/api/reports/by-quiz/${quizSessionId}`)
        if (response.data.id) {
          response = await apiClient.get<Report>(`/api/reports/public/${response.data.id}`)
        }
      }

      if (response?.data) {
        setReport(response.data as Report)
      }
    } catch (err: any) {
      console.error('Failed to load report:', err)
      setError(err.response?.data?.detail || 'Failed to load report')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <LoadingSkeleton />
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-red-50/20 dark:from-gray-900 dark:via-gray-900 dark:to-red-950/20 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center max-w-md bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl rounded-3xl p-8 shadow-premium border border-gray-200/50 dark:border-gray-700/50"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 200, damping: 15, delay: 0.2 }}
            className="w-20 h-20 bg-gradient-to-br from-red-400 to-red-500 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-red-500/25"
          >
            <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </motion.div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">Report Not Found</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6 leading-relaxed">{error || 'This report may not exist or is still being generated.'}</p>
          <motion.a
            href="/"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-xl font-medium shadow-lg shadow-primary-500/25 hover:shadow-xl hover:shadow-primary-500/30 transition-shadow"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Go to Home
          </motion.a>
        </motion.div>
      </div>
    )
  }

  const { executive_summary: summary, value_summary, findings, recommendations, roadmap } = report

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(value)
  }

  // Calculate total investment from recommendations
  const totalInvestment = recommendations?.reduce(
    (sum, rec) => sum + (rec.crb_analysis?.cost?.total || 0),
    0
  ) || 0

  const tabs = [
    { key: 'summary' as const, label: 'Summary' },
    { key: 'findings' as const, label: `Findings (${findings?.length || 0})` },
    { key: 'recommendations' as const, label: `Recommendations (${recommendations?.length || 0})` },
    { key: 'playbook' as const, label: 'Playbook' },
    { key: 'stack' as const, label: 'Stack' },
    { key: 'roi' as const, label: 'ROI Calculator' },
    { key: 'insights' as const, label: 'Industry' },
    { key: 'roadmap' as const, label: 'Roadmap' }
  ]

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">

      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-20">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-primary-600 flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div>
                <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
                  AI Readiness Report
                </h1>
                <span className={`
                  inline-flex items-center gap-1.5 text-xs font-medium
                  ${report.tier === 'quick'
                    ? 'text-blue-600 dark:text-blue-400'
                    : 'text-purple-600 dark:text-purple-400'
                  }
                `}>
                  <span className="w-1.5 h-1.5 rounded-full bg-current" />
                  {report.tier === 'quick' ? 'Quick Report' : 'Full Analysis'}
                </span>
              </div>
            </div>
            <button
              onClick={() => window.print()}
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

      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Verdict Card - The Honest Assessment */}
        {summary?.verdict && (
          <VerdictCard verdict={summary.verdict} />
        )}

        {/* Score Dashboard with Charts */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* AI Readiness Gauge */}
            <div className="text-center">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wide">
                AI Readiness Score
              </p>
              <AIReadinessGauge score={summary?.ai_readiness_score || 0} size="md" />
            </div>

            {/* Two Pillars Chart */}
            <div className="md:col-span-2">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 text-center uppercase tracking-wide">
                The Two Pillars
              </p>
              <TwoPillarsChart
                customerValue={summary?.customer_value_score || 0}
                businessHealth={summary?.business_health_score || 0}
              />
            </div>
          </div>

          {/* Key Insight */}
          {summary?.key_insight && (
            <div className="mt-6 pt-5 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center">
                  <svg className="w-4 h-4 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                    Key Insight
                  </p>
                  <p className="text-gray-700 dark:text-gray-300">
                    {summary.key_insight}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Value Projection Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            3-Year Value Projection
          </h3>
          <ValueTimelineChart
            valueSaved={value_summary?.value_saved?.subtotal || { min: 0, max: 0 }}
            valueCreated={value_summary?.value_created?.subtotal || { min: 0, max: 0 }}
            totalInvestment={totalInvestment}
          />
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6 pt-5 border-t border-gray-200 dark:border-gray-700">
            <div className="text-center p-3 rounded-lg bg-emerald-50 dark:bg-emerald-900/20">
              <p className="text-xs font-medium text-emerald-600 dark:text-emerald-400 uppercase tracking-wide mb-1">Value Saved</p>
              <p className="text-base font-semibold text-emerald-700 dark:text-emerald-300">
                {formatCurrency(value_summary?.value_saved?.subtotal?.min || 0)} - {formatCurrency(value_summary?.value_saved?.subtotal?.max || 0)}
              </p>
            </div>
            <div className="text-center p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20">
              <p className="text-xs font-medium text-blue-600 dark:text-blue-400 uppercase tracking-wide mb-1">Value Created</p>
              <p className="text-base font-semibold text-blue-700 dark:text-blue-300">
                {formatCurrency(value_summary?.value_created?.subtotal?.min || 0)} - {formatCurrency(value_summary?.value_created?.subtotal?.max || 0)}
              </p>
            </div>
            <div className="text-center p-3 rounded-lg bg-purple-50 dark:bg-purple-900/20">
              <p className="text-xs font-medium text-purple-600 dark:text-purple-400 uppercase tracking-wide mb-1">Total Potential</p>
              <p className="text-base font-semibold text-purple-700 dark:text-purple-300">
                {formatCurrency(value_summary?.total?.min || 0)} - {formatCurrency(value_summary?.total?.max || 0)}
              </p>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="mb-6">
          <div className="flex gap-1 overflow-x-auto pb-2 scrollbar-hide border-b border-gray-200 dark:border-gray-700">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`
                  px-4 py-2 font-medium text-sm transition-colors whitespace-nowrap border-b-2 -mb-[2px]
                  ${activeTab === tab.key
                    ? 'border-primary-600 text-primary-600 dark:text-primary-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                  }
                `}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          {activeTab === 'summary' && (
            <div className="space-y-4">
              {/* ROI Comparison Chart */}
              {recommendations && recommendations.length > 0 && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">ROI by Recommendation</h3>
                  <ROIComparisonChart recommendations={recommendations} />
                </div>
              )}

              {/* Top Opportunities */}
              {summary?.top_opportunities && summary.top_opportunities.length > 0 && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Top Opportunities
                  </h3>
                  <div className="space-y-2">
                    {summary.top_opportunities.map((opp, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 rounded-lg flex items-center justify-center font-semibold text-sm">
                            {i + 1}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900 dark:text-white">{opp.title}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              {opp.time_horizon === 'short' ? '0-6 months' : opp.time_horizon === 'mid' ? '6-18 months' : '18+ months'}
                            </p>
                          </div>
                        </div>
                        <p className="font-semibold text-emerald-600 dark:text-emerald-400">{opp.value_potential}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Not Recommended */}
              {summary?.not_recommended && summary.not_recommended.length > 0 && (
                <div className="bg-red-50 dark:bg-red-900/10 rounded-xl border border-red-200 dark:border-red-800/30 p-6">
                  <h3 className="text-lg font-semibold text-red-800 dark:text-red-300 mb-4 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    Not Recommended
                  </h3>
                  <div className="space-y-2">
                    {summary.not_recommended.map((item, i) => (
                      <div
                        key={i}
                        className="bg-white dark:bg-gray-800 rounded-lg p-4"
                      >
                        <p className="font-medium text-gray-900 dark:text-white">{item.title}</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{item.reason}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'findings' && (
            <div className="space-y-3">
              {findings?.map((finding) => (
                <div
                  key={finding.id}
                  className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5"
                >
                  <div className="flex items-start justify-between mb-3">
                    <h4 className="text-lg font-semibold text-gray-900">{finding.title}</h4>
                    <div className="flex gap-2">
                      <span className="px-2 py-1 text-xs font-medium rounded bg-blue-100 text-blue-700">
                        CV: {finding.customer_value_score}
                      </span>
                      <span className="px-2 py-1 text-xs font-medium rounded bg-green-100 text-green-700">
                        BH: {finding.business_health_score}
                      </span>
                      <span className={`px-2 py-1 text-xs font-medium rounded ${
                        finding.confidence === 'high' ? 'bg-green-100 text-green-700' :
                        finding.confidence === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-gray-100 text-gray-600'
                      }`}>
                        {finding.confidence}
                      </span>
                    </div>
                  </div>
                  <p className="text-gray-600 mb-4">{finding.description}</p>
                  <div className="flex flex-wrap gap-4 pt-4 border-t">
                    {finding.value_saved?.annual_savings && (
                      <div>
                        <p className="text-xs text-gray-500">Value Saved</p>
                        <p className="text-lg font-bold text-green-600">{formatCurrency(finding.value_saved.annual_savings)}/yr</p>
                        <p className="text-xs text-gray-400">{finding.value_saved.hours_per_week}h/week</p>
                      </div>
                    )}
                    {finding.value_created?.potential_revenue && (
                      <div>
                        <p className="text-xs text-gray-500">Value Created</p>
                        <p className="text-lg font-bold text-blue-600">{formatCurrency(finding.value_created.potential_revenue)}</p>
                      </div>
                    )}
                    <div className="ml-auto text-right">
                      <p className="text-xs text-gray-500">Time Horizon</p>
                      <p className="font-medium text-gray-900 capitalize">{finding.time_horizon}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'recommendations' && (
            <div className="space-y-3">
              {recommendations?.map((rec) => (
                <div
                  key={rec.id}
                  className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden"
                >
                  <div
                    className="p-6 cursor-pointer hover:bg-gray-50 transition"
                    onClick={() => setExpandedRec(expandedRec === rec.id ? null : rec.id)}
                  >
                    <div className="flex items-start justify-between">
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
                        <h4 className="text-lg font-semibold text-gray-900">{rec.title}</h4>
                        <p className="text-gray-600 mt-1">{rec.description}</p>
                      </div>
                      <motion.svg
                        animate={{ rotate: expandedRec === rec.id ? 180 : 0 }}
                        transition={{ duration: 0.2 }}
                        className="w-6 h-6 text-gray-400 flex-shrink-0 ml-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </motion.svg>
                    </div>
                  </div>

                  <AnimatePresence>
                    {expandedRec === rec.id && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="overflow-hidden"
                      >
                        <div className="px-6 pb-6 border-t">
                          {/* Three Options */}
                          {rec.options && (
                            <div className="mt-4">
                              <h5 className="font-semibold text-gray-900 mb-3">Three Options</h5>
                              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {rec.options.off_the_shelf && (
                                  <div className={`p-4 rounded-xl border-2 transition ${rec.our_recommendation === 'off_the_shelf' ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-200' : 'border-blue-200 bg-blue-50'}`}>
                                    {rec.our_recommendation === 'off_the_shelf' && (
                                      <span className="text-xs font-bold text-primary-600 uppercase">Recommended</span>
                                    )}
                                    <p className="font-semibold text-blue-800">Option A: Off-the-Shelf</p>
                                    <p className="text-sm text-gray-700 mt-1">{rec.options.off_the_shelf.name}</p>
                                    <p className="text-lg font-bold text-blue-600 mt-2">{formatCurrency(rec.options.off_the_shelf.monthly_cost)}/mo</p>
                                    <p className="text-xs text-gray-500">{rec.options.off_the_shelf.implementation_weeks} weeks to implement</p>
                                  </div>
                                )}
                                {rec.options.best_in_class && (
                                  <div className={`p-4 rounded-xl border-2 transition ${rec.our_recommendation === 'best_in_class' ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-200' : 'border-green-200 bg-green-50'}`}>
                                    {rec.our_recommendation === 'best_in_class' && (
                                      <span className="text-xs font-bold text-primary-600 uppercase">Recommended</span>
                                    )}
                                    <p className="font-semibold text-green-800">Option B: Best-in-Class</p>
                                    <p className="text-sm text-gray-700 mt-1">{rec.options.best_in_class.name}</p>
                                    <p className="text-lg font-bold text-green-600 mt-2">{formatCurrency(rec.options.best_in_class.monthly_cost)}/mo</p>
                                    <p className="text-xs text-gray-500">{rec.options.best_in_class.implementation_weeks} weeks to implement</p>
                                  </div>
                                )}
                                {rec.options.custom_solution && (
                                  <div className={`p-4 rounded-xl border-2 transition ${rec.our_recommendation === 'custom_solution' ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-200' : 'border-purple-200 bg-purple-50'}`}>
                                    {rec.our_recommendation === 'custom_solution' && (
                                      <span className="text-xs font-bold text-primary-600 uppercase">Recommended</span>
                                    )}
                                    <p className="font-semibold text-purple-800">Option C: Custom AI</p>
                                    <p className="text-sm text-gray-700 mt-1">{rec.options.custom_solution.approach?.substring(0, 60)}...</p>
                                    <p className="text-lg font-bold text-purple-600 mt-2">
                                      {formatCurrency(rec.options.custom_solution.estimated_cost?.min || 0)} - {formatCurrency(rec.options.custom_solution.estimated_cost?.max || 0)}
                                    </p>
                                    <p className="text-xs text-gray-500">{rec.options.custom_solution.implementation_weeks} weeks to implement</p>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}

                          {/* Our Recommendation */}
                          {rec.recommendation_rationale && (
                            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-xl">
                              <p className="font-semibold text-green-800">Why we recommend this option:</p>
                              <p className="text-sm text-gray-600 mt-1">{rec.recommendation_rationale}</p>
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
          )}

          {activeTab === 'playbook' && report.playbooks && (
            <motion.div
              key="playbook"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              {isSyncing && (
                <div className="fixed bottom-4 right-4 bg-primary-600 text-white px-3 py-2 rounded-lg text-sm flex items-center gap-2 shadow-lg z-50">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Saving progress...
                </div>
              )}
              <PlaybookTab
                playbooks={report.playbooks}
                reportId={reportId}
                onTaskComplete={handleTaskComplete}
                initialCompletedTasks={getInitialCompletedTasks()}
              />
            </motion.div>
          )}

          {activeTab === 'stack' && (
            <motion.div
              key="stack"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              {report.system_architecture &&
               report.system_architecture.cost_comparison &&
               (report.system_architecture.existing_tools?.length > 0 ||
                report.system_architecture.ai_layer?.length > 0) ? (
                <StackTab architecture={report.system_architecture} />
              ) : (
                <div className="bg-white rounded-2xl p-8 shadow-sm text-center">
                  <div className="text-4xl mb-4">🔧</div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Stack Architecture Not Available</h3>
                  <p className="text-gray-500 max-w-md mx-auto">
                    The system architecture diagram is generated as part of the full analysis.
                    This section will show your existing tools, AI layer, and recommended automations
                    once the full report is generated.
                  </p>
                </div>
              )}
            </motion.div>
          )}

          {activeTab === 'roi' && (
            <motion.div
              key="roi"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <ROICalculator
                recommendations={recommendations}
                valueSummary={value_summary as any}
              />
            </motion.div>
          )}

          {activeTab === 'insights' && report.industry_insights && (
            <motion.div
              key="insights"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <InsightsTab insights={report.industry_insights} />
            </motion.div>
          )}

          {activeTab === 'roadmap' && (
            <motion.div
              key="roadmap"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-6"
            >
              {/* Short Term */}
              {roadmap?.short_term && roadmap.short_term.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="bg-white rounded-2xl p-6 shadow-sm"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-green-100 text-green-600 rounded-full flex items-center justify-center">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">Phase 1: Quick Wins</h3>
                      <p className="text-sm text-gray-500">0-6 months</p>
                    </div>
                  </div>
                  <div className="space-y-3">
                    {roadmap.short_term.map((item, i) => (
                      <div key={i} className="border-l-4 border-green-400 pl-4 py-2">
                        <p className="font-medium text-gray-900">{item.title}</p>
                        <p className="text-sm text-gray-600">{item.description}</p>
                        <p className="text-xs text-gray-400 mt-1">Timeline: {item.timeline}</p>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Mid Term */}
              {roadmap?.mid_term && roadmap.mid_term.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 }}
                  className="bg-white rounded-2xl p-6 shadow-sm"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">Phase 2: Foundation</h3>
                      <p className="text-sm text-gray-500">6-18 months</p>
                    </div>
                  </div>
                  <div className="space-y-3">
                    {roadmap.mid_term.map((item, i) => (
                      <div key={i} className="border-l-4 border-blue-400 pl-4 py-2">
                        <p className="font-medium text-gray-900">{item.title}</p>
                        <p className="text-sm text-gray-600">{item.description}</p>
                        <p className="text-xs text-gray-400 mt-1">Timeline: {item.timeline}</p>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Long Term */}
              {roadmap?.long_term && roadmap.long_term.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 }}
                  className="bg-white rounded-2xl p-6 shadow-sm"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">Phase 3: Transformation</h3>
                      <p className="text-sm text-gray-500">18+ months</p>
                    </div>
                  </div>
                  <div className="space-y-3">
                    {roadmap.long_term.map((item, i) => (
                      <div key={i} className="border-l-4 border-purple-400 pl-4 py-2">
                        <p className="font-medium text-gray-900">{item.title}</p>
                        <p className="text-sm text-gray-600">{item.description}</p>
                        <p className="text-xs text-gray-400 mt-1">Timeline: {item.timeline}</p>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Dev Mode Panel - Only visible in dev mode */}
        {(import.meta.env.DEV || searchParams.get('dev') === 'true') && report && reportId && (
          <DevModePanel
            reportId={reportId}
            findings={findings || []}
            recommendations={recommendations || []}
          />
        )}

        {/* Automation Roadmap Summary - Phase 2D */}
        {report.automation_summary && (
          <div className="mt-8">
            <AutomationRoadmap summary={report.automation_summary} />
          </div>
        )}

        {/* Implementation Help CTA */}
        <div className="mt-8 bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 rounded-xl border border-primary-200 dark:border-primary-800/30 p-6">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-10 h-10 bg-primary-100 dark:bg-primary-900/50 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                Need help implementing these recommendations?
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                Our team can connect you with vetted implementation partners who specialize in your industry.
              </p>
              <a
                href={`mailto:help@crbanalyser.com?subject=Implementation%20Help%20Request&body=Report%20ID:%20${reportId}%0A%0AI%20need%20help%20implementing:%0A`}
                className="inline-flex items-center gap-2 text-sm font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 transition-colors"
              >
                Reply to get connected
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </a>
            </div>
          </div>
        </div>

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

      {/* Print styles */}
      <style>{`
        @media print {
          .sticky { position: relative !important; }
          button { display: none !important; }
          .backdrop-blur-xl { backdrop-filter: none !important; }
        }
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
    </div>
  )
}
