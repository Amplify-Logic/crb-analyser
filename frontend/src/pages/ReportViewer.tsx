import { useState, useEffect, useCallback, useMemo } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import apiClient from '../services/apiClient'
import {
  AIReadinessGauge,
  TwoPillarsChart,
  ValueTimelineChart,
  VerdictCard,
  YourStorySection,
  TieredFindings,
  NumberedRecommendations,
  ValueSummary,
  UpgradeCTA,
} from '../components/report'
import PlaybookTab from '../components/report/PlaybookTab'
import StackTab from '../components/report/StackTab'
import ROICalculator from '../components/report/ROICalculator'
import InsightsTab from '../components/report/InsightsTab'
import DevModePanel from '../components/report/DevModePanel'
import AutomationRoadmap from '../components/report/AutomationRoadmap'
import usePlaybookProgress from '../hooks/usePlaybookProgress'
import { Sidebar, SidebarItem } from '../components/report/Sidebar/Sidebar'
import { ContentPanel } from '../components/report/ContentPanel/ContentPanel'
import { logger } from '../utils/logger'

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

interface AIReadinessComponent {
  score: number
  max: number
  label: string
  description: string
  factors?: string[]
}

interface AIReadinessBreakdown {
  total_score: number
  components: {
    tech_stack: AIReadinessComponent
    data_readiness: AIReadinessComponent
    team_readiness: AIReadinessComponent
    process_maturity: AIReadinessComponent
  }
  improvement_suggestions: string[]
}

interface ExecutiveSummary {
  ai_readiness_score: number
  ai_readiness_breakdown?: AIReadinessBreakdown
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

interface CompanyProfile {
  company_name: string
  industry: string
  industry_display: string
  team_size: string
  tech_level: string
  budget_range: string
  existing_tools?: string[]
  location?: string
}

interface Report {
  id: string
  tier: string
  status: string
  company_profile?: CompanyProfile
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
  const [activeItem, setActiveItem] = useState<SidebarItem>({ type: 'overview', id: null })

  // Playbook progress tracking
  const {
    toggleTask,
    getCompletedTasks,
    isLoading: _progressLoading,
    isSyncing
  } = usePlaybookProgress({
    reportId: reportId || '',
    onError: (err) => logger.error('Playbook progress error:', err)
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

  // Prepare sidebar data - must be before early returns (Rules of Hooks)
  const sidebarFindings = useMemo(() =>
    (report?.findings || []).map(f => ({
      id: f.id,
      title: f.title,
      status: 'pending' as const,
    })), [report?.findings])

  const sidebarActions = useMemo(() =>
    (report?.recommendations || []).map(r => ({
      id: r.id,
      title: r.title,
      priority: r.priority,
    })), [report?.recommendations])

  const sidebarPlaybookPhases = useMemo(() => {
    if (!report?.playbooks || report.playbooks.length === 0) return []
    return report.playbooks.map((pb, index) => ({
      id: pb.id,
      title: `Phase ${index + 1}`,
      completedTasks: getCompletedTasks(pb.id).length,
      totalTasks: pb.phases?.reduce((sum: number, phase: any) => sum + (phase.tasks?.length || 0), 0) || 0,
    }))
  }, [report?.playbooks, getCompletedTasks])

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
      logger.error('Failed to load report:', err)
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

  const { executive_summary: summary, value_summary, findings, recommendations } = report

  // Calculate total investment from recommendations
  const totalInvestment = recommendations?.reduce(
    (sum, rec) => sum + (rec.crb_analysis?.cost?.total || 0),
    0
  ) || 0

  // Extract company profile data for personalization
  // Handle industry which can be a string or object {primary_industry, sub_industry}
  const INDUSTRY_DISPLAY_NAMES: Record<string, string> = {
    'home_services': 'Home Services & Trades',
    'home-services': 'Home Services & Trades',
    'professional_services': 'Professional Services',
    'healthcare': 'Healthcare',
    'dental': 'Dental Practice',
    'retail': 'Retail',
    'hospitality': 'Hospitality',
    'construction': 'Construction',
    'real_estate': 'Real Estate',
    'legal': 'Legal Services',
    'accounting': 'Accounting & Finance',
    'marketing': 'Marketing & Advertising',
    'technology': 'Technology',
    'manufacturing': 'Manufacturing',
    'general': 'General Business',
  }

  const extractIndustry = (profile: any): string => {
    if (!profile?.industry) return ''
    let industrySlug = ''
    if (typeof profile.industry === 'string') {
      industrySlug = profile.industry
    } else if (typeof profile.industry === 'object') {
      // Handle object format from company research
      const primary = profile.industry.primary_industry
      if (typeof primary === 'string') industrySlug = primary
      else if (primary?.value) industrySlug = primary.value
    }
    // Return display name if available, otherwise format the slug
    return INDUSTRY_DISPLAY_NAMES[industrySlug] ||
           industrySlug.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  }

  const rawProfile = report.company_profile
  const companyProfile = {
    company_name: rawProfile?.company_name || '',
    industry: extractIndustry(rawProfile) || report.industry_insights?.industry_display_name || '',
    industry_display: rawProfile?.industry_display || report.industry_insights?.industry_display_name || '',
    team_size: rawProfile?.team_size || '',
    tech_level: rawProfile?.tech_level || '',
    budget_range: rawProfile?.budget_range || '',
    existing_tools: rawProfile?.existing_tools || report.system_architecture?.existing_tools?.map(t => t.name) || []
  }

  // Get breadcrumb and prev/next based on active item
  const getBreadcrumb = (): string[] => {
    switch (activeItem.type) {
      case 'overview': return ['Overview']
      case 'finding': {
        const finding = findings?.find(f => f.id === activeItem.id)
        return ['Findings', finding?.title || '']
      }
      case 'action': {
        const action = recommendations?.find(r => r.id === activeItem.id)
        return ['Actions', action?.title || '']
      }
      case 'playbook': return ['Playbook', `Phase ${activeItem.id}`]
      case 'tool': {
        const toolNames: Record<string, string> = { roi: 'ROI Calculator', stack: 'Stack Analysis', insights: 'Industry Insights' }
        return ['Tools', toolNames[activeItem.id || ''] || '']
      }
      default: return ['Overview']
    }
  }

  // Navigation helpers
  const getNavigationItems = () => {
    const items: SidebarItem[] = [
      { type: 'overview', id: null },
      ...sidebarFindings.map(f => ({ type: 'finding' as const, id: f.id })),
      ...sidebarActions.map(a => ({ type: 'action' as const, id: a.id })),
      ...sidebarPlaybookPhases.map(p => ({ type: 'playbook' as const, id: p.id })),
      { type: 'tool', id: 'roi' },
      { type: 'tool', id: 'stack' },
      { type: 'tool', id: 'insights' },
    ]
    return items
  }

  const navItems = getNavigationItems()
  const currentIndex = navItems.findIndex(item => item.type === activeItem.type && item.id === activeItem.id)
  const prevItem = currentIndex > 0 ? navItems[currentIndex - 1] : null
  const nextItem = currentIndex < navItems.length - 1 ? navItems[currentIndex + 1] : null

  const getItemLabel = (item: SidebarItem | null): string | undefined => {
    if (!item) return undefined
    switch (item.type) {
      case 'overview': return 'Overview'
      case 'finding': return findings?.find(f => f.id === item.id)?.title
      case 'action': return recommendations?.find(r => r.id === item.id)?.title
      case 'playbook': return `Phase ${item.id}`
      case 'tool': {
        const toolNames: Record<string, string> = { roi: 'ROI Calculator', stack: 'Stack Analysis', insights: 'Industry Insights' }
        return toolNames[item.id || '']
      }
    }
  }

  // Render content based on active item
  const renderContent = () => {
    switch (activeItem.type) {
      case 'overview':
        return (
          <div className="space-y-6">
            {/* Your Story */}
            <YourStorySection
              keyInsight={summary?.key_insight || 'Your AI readiness analysis is complete.'}
              findingsCount={findings?.length || 0}
              mirroredStatements={[]}
              companyContext={{
                teamSize: companyProfile.team_size,
                techLevel: companyProfile.tech_level,
                budget: companyProfile.budget_range,
                existingTools: companyProfile.existing_tools
              }}
            />

            {/* Verdict Card */}
            {summary?.verdict && (
              <VerdictCard verdict={summary.verdict} />
            )}

            {/* Score Dashboard */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wide">
                    AI Readiness Score
                  </p>
                  <AIReadinessGauge
                    score={summary?.ai_readiness_score || 0}
                    size="md"
                    breakdown={summary?.ai_readiness_breakdown}
                  />
                </div>
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
            </div>

            {/* Value Summary */}
            <ValueSummary
              investment={summary?.recommended_investment?.year_1_max || totalInvestment}
              returnMin={value_summary?.total?.min || 0}
              returnMax={value_summary?.total?.max || 0}
            />
          </div>
        )

      case 'finding':
        const finding = findings?.find(f => f.id === activeItem.id)
        if (!finding) return <div>Finding not found</div>
        return (
          <div className="space-y-6">
            <TieredFindings
              findings={[finding] as any}
              heroCount={1}
              compactCount={0}
            />
          </div>
        )

      case 'action':
        const action = recommendations?.find(r => r.id === activeItem.id)
        if (!action) return <div>Action not found</div>
        return (
          <div className="space-y-6">
            <NumberedRecommendations recommendations={[action] as any} />
          </div>
        )

      case 'playbook':
        return (
          <div className="space-y-6">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-1">
                Your Playbook
              </h2>
              <p className="text-gray-600 dark:text-gray-400">
                Investment breakdown and projected returns
              </p>
            </div>

            {/* Value Timeline Chart */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                3-Year Value Projection
              </h3>
              <ValueTimelineChart
                valueSaved={value_summary?.value_saved?.subtotal || { min: 0, max: 0 }}
                valueCreated={value_summary?.value_created?.subtotal || { min: 0, max: 0 }}
                totalInvestment={totalInvestment}
                showMilestones={true}
              />
            </div>

            {/* Playbook Phases */}
            {report.playbooks && report.playbooks.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
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
              </div>
            )}
          </div>
        )

      case 'tool':
        switch (activeItem.id) {
          case 'roi':
            // Detect currency from company location (NZ = NZD, AU = AUD, default EUR)
            const location = report.company_profile?.location || ''
            const isNZ = location.toLowerCase().includes('zealand') || location.toLowerCase().includes('nz')
            const isAU = location.toLowerCase().includes('australia') || location.toLowerCase().includes('au')
            const detectedCurrency = isNZ ? 'NZD' : isAU ? 'AUD' : 'EUR'
            const detectedLocale = isNZ ? 'en-NZ' : isAU ? 'en-AU' : 'de-DE'

            return (
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">ROI Calculator</h3>
                <ROICalculator
                  recommendations={recommendations as any}
                  valueSummary={value_summary as any}
                  currency={detectedCurrency}
                  locale={detectedLocale}
                />
              </div>
            )
          case 'stack':
            if (!report.system_architecture) return <div>Stack data not available</div>
            return (
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Your Stack</h3>
                <StackTab architecture={report.system_architecture} />
              </div>
            )
          case 'insights':
            if (!report.industry_insights) return <div>Industry insights not available</div>
            return (
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Industry Insights</h3>
                <InsightsTab insights={report.industry_insights} />
              </div>
            )
        }
        return null

      default:
        return <div>Select an item from the sidebar</div>
    }
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Compact Header */}
      <header className="flex-shrink-0 h-14 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex items-center px-4 gap-4">
        <a href="/" className="text-lg font-semibold text-primary-600 dark:text-primary-400">
          Ready Path
        </a>
        <span className="text-gray-300 dark:text-gray-600">|</span>
        <span className="text-sm text-gray-600 dark:text-gray-400 truncate">
          {companyProfile.company_name || 'AI Readiness Report'}
        </span>
        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={() => window.print()}
            className="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
          >
            Export PDF
          </button>
          {reportId && (
            <UpgradeCTA
              currentTier={report.tier as 'quick' | 'full'}
              reportId={reportId}
            />
          )}
        </div>
      </header>

      {/* Two-Panel Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <Sidebar
          companyName={companyProfile.company_name || 'AI Readiness Report'}
          industry={companyProfile.industry_display || companyProfile.industry || 'Business'}
          score={summary?.ai_readiness_score || 0}
          findings={sidebarFindings}
          actions={sidebarActions}
          playbookPhases={sidebarPlaybookPhases}
          activeItem={activeItem}
          onItemClick={setActiveItem}
        />

        {/* Content Panel */}
        <ContentPanel
          breadcrumb={getBreadcrumb()}
          onPrev={() => prevItem && setActiveItem(prevItem)}
          onNext={() => nextItem && setActiveItem(nextItem)}
          prevLabel={getItemLabel(prevItem)}
          nextLabel={getItemLabel(nextItem)}
        >
          {renderContent()}

          {/* Dev Mode Panel - Only visible in dev mode */}
          {(import.meta.env.DEV || searchParams.get('dev') === 'true') && report && reportId && activeItem.type === 'overview' && (
            <div className="mt-8">
              <DevModePanel
                reportId={reportId}
                findings={findings || []}
                recommendations={recommendations || []}
              />
            </div>
          )}

          {/* Automation Roadmap Summary - show on overview */}
          {report.automation_summary && activeItem.type === 'overview' && (
            <div className="mt-8">
              <AutomationRoadmap summary={report.automation_summary} />
            </div>
          )}

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
        </ContentPanel>
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
