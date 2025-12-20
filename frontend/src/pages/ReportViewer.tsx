import { useState, useEffect } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import apiClient from '../services/apiClient'
import {
  AIReadinessGauge,
  TwoPillarsChart,
  ValueTimelineChart,
  ROIComparisonChart,
  VerdictCard,
  fadeInUp,
  staggerContainer,
  staggerItem
} from '../components/report'
import PlaybookTab from '../components/report/PlaybookTab'
import StackTab from '../components/report/StackTab'
import ROICalculator from '../components/report/ROICalculator'
import InsightsTab from '../components/report/InsightsTab'

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

  useEffect(() => {
    loadReport()
  }, [reportId, quizSessionId])

  async function loadReport() {
    setLoading(true)
    setError(null)

    try {
      let response
      if (reportId) {
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
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading your report...</p>
        </div>
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Report Not Found</h2>
          <p className="text-gray-600 mb-4">{error || 'This report may not exist or is still being generated.'}</p>
          <a href="/" className="text-primary-600 hover:underline">Go to Home</a>
        </div>
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
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900">CRB Analysis Report</h1>
              <p className="text-sm text-gray-500">{report.tier === 'quick' ? 'Quick Report' : 'Full Analysis'}</p>
            </div>
            <button
              onClick={() => window.print()}
              className="px-4 py-2 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Print / PDF
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Verdict Card - The Honest Assessment */}
        {summary?.verdict && (
          <VerdictCard verdict={summary.verdict} />
        )}

        {/* Score Dashboard with Charts */}
        <motion.div
          initial="initial"
          animate="animate"
          variants={fadeInUp}
          className="bg-white rounded-2xl shadow-sm p-6 mb-8"
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* AI Readiness Gauge */}
            <div className="text-center">
              <p className="text-sm text-gray-500 mb-4">AI Readiness Score</p>
              <AIReadinessGauge score={summary?.ai_readiness_score || 0} size="md" />
            </div>

            {/* Two Pillars Chart */}
            <div className="md:col-span-2">
              <p className="text-sm text-gray-500 mb-4 text-center">The Two Pillars</p>
              <TwoPillarsChart
                customerValue={summary?.customer_value_score || 0}
                businessHealth={summary?.business_health_score || 0}
              />
            </div>
          </div>

          {/* Key Insight */}
          {summary?.key_insight && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="mt-6 pt-6 border-t border-gray-100"
            >
              <p className="text-sm text-gray-500 mb-1">Key Insight</p>
              <p className="text-lg text-gray-800">{summary.key_insight}</p>
            </motion.div>
          )}
        </motion.div>

        {/* Value Projection Chart */}
        <motion.div
          initial="initial"
          animate="animate"
          variants={fadeInUp}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-2xl shadow-sm p-6 mb-8"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">3-Year Value Projection</h3>
          <ValueTimelineChart
            valueSaved={value_summary?.value_saved?.subtotal || { min: 0, max: 0 }}
            valueCreated={value_summary?.value_created?.subtotal || { min: 0, max: 0 }}
            totalInvestment={totalInvestment}
          />
          <div className="grid grid-cols-3 gap-4 mt-6 pt-4 border-t border-gray-100">
            <div className="text-center">
              <p className="text-xs text-gray-500">Value Saved</p>
              <p className="text-lg font-bold text-green-600">
                {formatCurrency(value_summary?.value_saved?.subtotal?.min || 0)} - {formatCurrency(value_summary?.value_saved?.subtotal?.max || 0)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-gray-500">Value Created</p>
              <p className="text-lg font-bold text-blue-600">
                {formatCurrency(value_summary?.value_created?.subtotal?.min || 0)} - {formatCurrency(value_summary?.value_created?.subtotal?.max || 0)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-gray-500">Total Potential</p>
              <p className="text-lg font-bold text-purple-600">
                {formatCurrency(value_summary?.total?.min || 0)} - {formatCurrency(value_summary?.total?.max || 0)}
              </p>
            </div>
          </div>
        </motion.div>

        {/* Navigation Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 rounded-xl font-medium transition whitespace-nowrap ${
                activeTab === tab.key
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          {activeTab === 'summary' && (
            <motion.div
              key="summary"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-6"
            >
              {/* ROI Comparison Chart */}
              {recommendations && recommendations.length > 0 && (
                <div className="bg-white rounded-2xl p-6 shadow-sm">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">ROI by Recommendation</h3>
                  <ROIComparisonChart recommendations={recommendations} />
                </div>
              )}

              {/* Top Opportunities */}
              {summary?.top_opportunities && summary.top_opportunities.length > 0 && (
                <motion.div
                  variants={staggerContainer}
                  initial="initial"
                  animate="animate"
                  className="bg-white rounded-2xl p-6 shadow-sm"
                >
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Opportunities</h3>
                  <div className="space-y-3">
                    {summary.top_opportunities.map((opp, i) => (
                      <motion.div
                        key={i}
                        variants={staggerItem}
                        className="flex items-center justify-between p-4 bg-green-50 rounded-xl"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-green-100 text-green-600 rounded-full flex items-center justify-center font-bold">
                            {i + 1}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900">{opp.title}</p>
                            <p className="text-sm text-gray-500">
                              {opp.time_horizon === 'short' ? '0-6 months' : opp.time_horizon === 'mid' ? '6-18 months' : '18+ months'}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-green-600">{opp.value_potential}</p>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Not Recommended */}
              {summary?.not_recommended && summary.not_recommended.length > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-2xl p-6">
                  <h3 className="text-lg font-semibold text-red-800 mb-4">Not Recommended</h3>
                  <div className="space-y-3">
                    {summary.not_recommended.map((item, i) => (
                      <div key={i} className="bg-white rounded-xl p-4">
                        <p className="font-medium text-gray-900">{item.title}</p>
                        <p className="text-sm text-gray-600 mt-1">{item.reason}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {activeTab === 'findings' && (
            <motion.div
              key="findings"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-4"
            >
              {findings?.map((finding, index) => (
                <motion.div
                  key={finding.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="bg-white rounded-2xl p-6 shadow-sm"
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
                </motion.div>
              ))}
            </motion.div>
          )}

          {activeTab === 'recommendations' && (
            <motion.div
              key="recommendations"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-4"
            >
              {recommendations?.map((rec, index) => (
                <motion.div
                  key={rec.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="bg-white rounded-2xl shadow-sm overflow-hidden"
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
                </motion.div>
              ))}
            </motion.div>
          )}

          {activeTab === 'playbook' && report.playbooks && (
            <motion.div
              key="playbook"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <PlaybookTab playbooks={report.playbooks} />
            </motion.div>
          )}

          {activeTab === 'stack' && report.system_architecture && (
            <motion.div
              key="stack"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <StackTab architecture={report.system_architecture} />
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
                valueSummary={value_summary}
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

        {/* Footer */}
        <div className="mt-12 pt-6 border-t text-center text-sm text-gray-500">
          <p>Report generated by CRB Analyser</p>
          <p className="mt-1">This report contains estimates based on provided data and industry benchmarks.</p>
        </div>
      </div>

      {/* Print styles */}
      <style>{`
        @media print {
          .sticky { position: relative !important; }
          button { display: none !important; }
        }
      `}</style>
    </div>
  )
}
