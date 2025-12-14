import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import apiClient from '../services/apiClient'

interface Audit {
  id: string
  title: string
  status: string
  tier: string
  client_name?: string
  client_industry?: string
  ai_readiness_score?: number
  total_findings?: number
  total_potential_savings?: number
  completed_at?: string
}

interface Finding {
  id: string
  title: string
  category: string
  priority: number
  impact_type: string
  description: string
  current_state?: string
  estimated_hours_saved?: number
  estimated_cost_saved?: number
  confidence_level?: number
  sources?: string[]
  is_ai_estimated: boolean
}

interface Recommendation {
  id: string
  finding_id: string
  title: string
  description: string
  vendor_name?: string
  vendor_category?: string
  implementation_cost?: number
  monthly_cost?: number
  roi_percentage?: number
  payback_months?: number
  implementation_timeline?: string
  priority: number
}

export default function Report() {
  const { id: auditId } = useParams<{ id: string }>()

  const [loading, setLoading] = useState(true)
  const [audit, setAudit] = useState<Audit | null>(null)
  const [findings, setFindings] = useState<Finding[]>([])
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [activeTab, setActiveTab] = useState<'summary' | 'findings' | 'recommendations'>('summary')

  useEffect(() => {
    if (auditId) {
      loadReport()
    }
  }, [auditId])

  async function loadReport() {
    setLoading(true)
    try {
      const [auditRes, findingsRes, recsRes] = await Promise.all([
        apiClient.get<Audit>(`/api/audits/${auditId}`),
        apiClient.get<{ data: Finding[] }>(`/api/audits/${auditId}/findings`),
        apiClient.get<{ data: Recommendation[] }>(`/api/audits/${auditId}/recommendations`),
      ])

      setAudit(auditRes.data)
      setFindings(findingsRes.data.data || [])
      setRecommendations(recsRes.data.data || [])
    } catch (err) {
      console.error('Failed to load report:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading report...</p>
        </div>
      </div>
    )
  }

  if (!audit) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">Report not found</p>
          <Link to="/dashboard" className="text-primary-600 hover:underline">
            Back to Dashboard
          </Link>
        </div>
      </div>
    )
  }

  const verifiedFindings = findings.filter((f) => !f.is_ai_estimated)
  const estimatedFindings = findings.filter((f) => f.is_ai_estimated)
  const totalSavings = findings.reduce((sum, f) => sum + (f.estimated_cost_saved || 0), 0)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <Link
                to="/dashboard"
                className="text-sm text-gray-500 hover:text-gray-700 mb-2 inline-block"
              >
                &larr; Back to Dashboard
              </Link>
              <h1 className="text-2xl font-bold text-gray-900">{audit.title}</h1>
              <p className="text-gray-600">
                {audit.client_name} &bull; {audit.client_industry}
              </p>
            </div>
            <button
              onClick={() => window.print()}
              className="px-4 py-2 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                />
              </svg>
              Download PDF
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* AI Readiness Score Card */}
        <div className="bg-gradient-to-br from-primary-600 to-primary-800 rounded-2xl p-8 text-white mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-medium text-primary-100 mb-1">
                AI Readiness Score
              </h2>
              <div className="text-6xl font-bold mb-2">
                {audit.ai_readiness_score || 0}
                <span className="text-2xl text-primary-200">/100</span>
              </div>
              <p className="text-primary-200">
                {(audit.ai_readiness_score || 0) >= 70
                  ? 'Great potential for AI implementation'
                  : (audit.ai_readiness_score || 0) >= 40
                  ? 'Good foundation with room for improvement'
                  : 'Significant opportunities for automation'}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold">{findings.length}</div>
                <div className="text-primary-200 text-sm">Findings</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold">{recommendations.length}</div>
                <div className="text-primary-200 text-sm">Recommendations</div>
              </div>
              <div className="text-center col-span-2">
                <div className="text-3xl font-bold text-green-300">
                  €{totalSavings.toLocaleString()}
                </div>
                <div className="text-primary-200 text-sm">Potential Annual Savings</div>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          {(['summary', 'findings', 'recommendations'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-xl font-medium transition ${
                activeTab === tab
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'summary' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Key Findings Summary */}
            <div className="bg-white rounded-2xl p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Key Findings
              </h3>
              <ul className="space-y-3">
                {findings.slice(0, 5).map((finding) => (
                  <li key={finding.id} className="flex items-start gap-3">
                    <div
                      className={`w-2 h-2 mt-2 rounded-full ${
                        finding.priority <= 2
                          ? 'bg-red-500'
                          : finding.priority <= 4
                          ? 'bg-yellow-500'
                          : 'bg-green-500'
                      }`}
                    />
                    <div>
                      <p className="font-medium text-gray-900">{finding.title}</p>
                      <p className="text-sm text-gray-500">{finding.category}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            {/* Top Recommendations */}
            <div className="bg-white rounded-2xl p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Top Recommendations
              </h3>
              <ul className="space-y-3">
                {recommendations.slice(0, 5).map((rec) => (
                  <li key={rec.id} className="flex items-start gap-3">
                    <div className="w-6 h-6 bg-green-100 text-green-600 rounded-full flex items-center justify-center flex-shrink-0">
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{rec.title}</p>
                      {rec.roi_percentage && (
                        <p className="text-sm text-green-600">
                          {rec.roi_percentage}% ROI
                        </p>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {activeTab === 'findings' && (
          <div className="space-y-6">
            {/* Verified Findings */}
            {verifiedFindings.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Verified Findings
                </h3>
                <div className="space-y-4">
                  {verifiedFindings.map((finding) => (
                    <FindingCard key={finding.id} finding={finding} />
                  ))}
                </div>
              </div>
            )}

            {/* AI-Estimated Findings */}
            {estimatedFindings.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  AI-Estimated Findings
                  <span className="text-xs font-normal text-gray-500 bg-gray-100 px-2 py-1 rounded">
                    Based on industry benchmarks
                  </span>
                </h3>
                <div className="space-y-4">
                  {estimatedFindings.map((finding) => (
                    <FindingCard key={finding.id} finding={finding} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'recommendations' && (
          <div className="space-y-4">
            {recommendations.map((rec) => (
              <RecommendationCard key={rec.id} recommendation={rec} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function FindingCard({ finding }: { finding: Finding }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span
              className={`px-2 py-1 text-xs font-medium rounded ${
                finding.priority <= 2
                  ? 'bg-red-100 text-red-700'
                  : finding.priority <= 4
                  ? 'bg-yellow-100 text-yellow-700'
                  : 'bg-green-100 text-green-700'
              }`}
            >
              {finding.priority <= 2 ? 'High' : finding.priority <= 4 ? 'Medium' : 'Low'} Priority
            </span>
            <span className="text-xs text-gray-500">{finding.category}</span>
          </div>
          <h4 className="text-lg font-semibold text-gray-900 mb-2">
            {finding.title}
          </h4>
          <p className="text-gray-600">{finding.description}</p>

          {expanded && (
            <div className="mt-4 pt-4 border-t space-y-3">
              {finding.current_state && (
                <div>
                  <p className="text-sm font-medium text-gray-700">Current State</p>
                  <p className="text-sm text-gray-600">{finding.current_state}</p>
                </div>
              )}
              {finding.estimated_hours_saved && (
                <div>
                  <p className="text-sm font-medium text-gray-700">Estimated Hours Saved</p>
                  <p className="text-sm text-gray-600">{finding.estimated_hours_saved} hours/month</p>
                </div>
              )}
              {finding.confidence_level && (
                <div>
                  <p className="text-sm font-medium text-gray-700">Confidence Level</p>
                  <p className="text-sm text-gray-600">{finding.confidence_level}%</p>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="text-right ml-6">
          {finding.estimated_cost_saved && (
            <div className="text-2xl font-bold text-green-600">
              €{finding.estimated_cost_saved.toLocaleString()}
            </div>
          )}
          <p className="text-xs text-gray-500">potential savings/year</p>
        </div>
      </div>

      <button
        onClick={() => setExpanded(!expanded)}
        className="mt-4 text-sm text-primary-600 hover:text-primary-700"
      >
        {expanded ? 'Show less' : 'Show more'}
      </button>
    </div>
  )
}

function RecommendationCard({ recommendation }: { recommendation: Recommendation }) {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h4 className="text-lg font-semibold text-gray-900 mb-2">
            {recommendation.title}
          </h4>
          <p className="text-gray-600 mb-4">{recommendation.description}</p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {recommendation.vendor_name && (
              <div>
                <p className="text-xs text-gray-500">Vendor</p>
                <p className="font-medium text-gray-900">{recommendation.vendor_name}</p>
              </div>
            )}
            {recommendation.implementation_cost && (
              <div>
                <p className="text-xs text-gray-500">Implementation Cost</p>
                <p className="font-medium text-gray-900">
                  €{recommendation.implementation_cost.toLocaleString()}
                </p>
              </div>
            )}
            {recommendation.monthly_cost && (
              <div>
                <p className="text-xs text-gray-500">Monthly Cost</p>
                <p className="font-medium text-gray-900">
                  €{recommendation.monthly_cost.toLocaleString()}/mo
                </p>
              </div>
            )}
            {recommendation.payback_months && (
              <div>
                <p className="text-xs text-gray-500">Payback Period</p>
                <p className="font-medium text-gray-900">
                  {recommendation.payback_months} months
                </p>
              </div>
            )}
          </div>
        </div>

        {recommendation.roi_percentage && (
          <div className="text-right ml-6">
            <div className="text-2xl font-bold text-green-600">
              {recommendation.roi_percentage}%
            </div>
            <p className="text-xs text-gray-500">ROI</p>
          </div>
        )}
      </div>
    </div>
  )
}
