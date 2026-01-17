/**
 * Insights Admin Page
 *
 * Admin UI for managing curated insights.
 * Features: list, filter, review, edit, delete.
 */

import { useState, useEffect, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import apiClient from '../../services/apiClient'

// Types
interface SupportingData {
  claim: string
  source: string
  source_url?: string
  date?: string
  credibility: string
}

interface InsightTags {
  topics: string[]
  industries: string[]
  use_in: string[]
  user_stages: string[]
}

interface InsightSource {
  title: string
  author?: string
  url?: string
  date?: string
  type?: string
}

interface Insight {
  id: string
  type: string
  title: string
  content: string
  supporting_data: SupportingData[]
  actionable_insight?: string
  tags: InsightTags
  source: InsightSource
  extracted_at: string
  reviewed: boolean
}

const INSIGHT_TYPES = ['trend', 'framework', 'case_study', 'statistic', 'quote', 'prediction']
const USE_IN_OPTIONS = ['report', 'quiz_results', 'landing', 'email']

// ============================================================================
// Components
// ============================================================================

function TypeBadge({ type }: { type: string }) {
  const colors: Record<string, string> = {
    trend: 'bg-violet-100 text-violet-700 ring-violet-200',
    framework: 'bg-blue-100 text-blue-700 ring-blue-200',
    case_study: 'bg-emerald-100 text-emerald-700 ring-emerald-200',
    statistic: 'bg-amber-100 text-amber-700 ring-amber-200',
    quote: 'bg-pink-100 text-pink-700 ring-pink-200',
    prediction: 'bg-indigo-100 text-indigo-700 ring-indigo-200',
  }

  const icons: Record<string, string> = {
    trend: '📈',
    framework: '🔧',
    case_study: '📋',
    statistic: '📊',
    quote: '💬',
    prediction: '🔮',
  }

  return (
    <span className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg font-medium ring-1 ring-inset ${colors[type] || 'bg-gray-100 text-gray-700 ring-gray-200'}`}>
      <span className="text-[10px]">{icons[type]}</span>
      {type.replace('_', ' ')}
    </span>
  )
}

function ReviewedBadge({ reviewed }: { reviewed: boolean }) {
  return reviewed ? (
    <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-medium">
      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
      </svg>
      Reviewed
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 font-medium">
      <span className="w-1.5 h-1.5 bg-amber-500 rounded-full animate-pulse" />
      Pending
    </span>
  )
}

function InsightList({
  insights,
  loading,
  onSelect,
  onReview,
}: {
  insights: Insight[]
  loading: boolean
  onSelect: (insight: Insight) => void
  onReview: (insight: Insight) => void
}) {
  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="bg-white rounded-2xl p-5 animate-pulse border border-gray-100">
            <div className="flex gap-3 mb-3">
              <div className="h-6 w-20 bg-gray-200 rounded-lg" />
              <div className="h-6 w-16 bg-gray-100 rounded-lg" />
            </div>
            <div className="h-5 bg-gray-200 rounded w-2/3 mb-2" />
            <div className="h-4 bg-gray-100 rounded w-full mb-1" />
            <div className="h-4 bg-gray-100 rounded w-3/4" />
          </div>
        ))}
      </div>
    )
  }

  if (insights.length === 0) {
    return (
      <div className="bg-white rounded-2xl p-16 text-center border border-gray-100">
        <div className="w-16 h-16 bg-gradient-to-br from-violet-100 to-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-5">
          <span className="text-3xl">💡</span>
        </div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">No insights found</h3>
        <p className="text-gray-500 mb-6 max-w-sm mx-auto">
          Try adjusting your filters or extract new insights from content.
        </p>
        <Link
          to="/admin/insights/extract"
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-violet-600 to-blue-600 text-white rounded-xl hover:from-violet-700 hover:to-blue-700 font-medium shadow-lg shadow-violet-200 transition-all"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Extract Insights
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {insights.map((insight) => (
        <div
          key={insight.id}
          onClick={() => onSelect(insight)}
          className="group bg-white rounded-2xl p-5 hover:shadow-lg hover:shadow-gray-100 transition-all duration-200 cursor-pointer border border-gray-100 hover:border-gray-200"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-3 flex-wrap">
                <TypeBadge type={insight.type} />
                <ReviewedBadge reviewed={insight.reviewed} />
                {insight.tags.use_in.slice(0, 2).map((use) => (
                  <span key={use} className="text-xs px-2 py-0.5 bg-gray-50 text-gray-500 rounded-md border border-gray-100">
                    {use.replace('_', ' ')}
                  </span>
                ))}
                {insight.tags.use_in.length > 2 && (
                  <span className="text-xs text-gray-400">+{insight.tags.use_in.length - 2} more</span>
                )}
              </div>
              <h3 className="font-semibold text-gray-900 group-hover:text-violet-700 transition-colors">
                {insight.title}
              </h3>
              <p className="text-sm text-gray-500 line-clamp-2 mt-1.5 leading-relaxed">
                {insight.content}
              </p>
              <div className="mt-3 flex items-center gap-2 text-xs text-gray-400">
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
                <span className="truncate max-w-xs">
                  {insight.source.title}
                  {insight.source.author && ` • ${insight.source.author}`}
                </span>
              </div>
            </div>
            <div className="flex flex-col items-end gap-2 shrink-0">
              {!insight.reviewed && (
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onReview(insight)
                  }}
                  className="text-xs px-3 py-1.5 bg-emerald-50 text-emerald-600 hover:bg-emerald-100 rounded-lg font-medium transition-colors flex items-center gap-1.5"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Approve
                </button>
              )}
              <div className="text-gray-300 group-hover:text-gray-400 transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function InsightEditor({
  insight,
  onSave,
  onDelete,
  onCancel,
}: {
  insight: Insight
  onSave: (updates: Partial<Insight>) => void
  onDelete: () => void
  onCancel: () => void
}) {
  const [title, setTitle] = useState(insight.title)
  const [content, setContent] = useState(insight.content)
  const [actionable, setActionable] = useState(insight.actionable_insight || '')
  const [useIn, setUseIn] = useState<string[]>(insight.tags.use_in)
  const [topics, setTopics] = useState(insight.tags.topics.join(', '))
  const [reviewed, setReviewed] = useState(insight.reviewed)
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    await onSave({
      title,
      content,
      actionable_insight: actionable || undefined,
      tags: {
        ...insight.tags,
        use_in: useIn,
        topics: topics.split(',').map((t) => t.trim()).filter(Boolean),
      },
      reviewed,
    })
    setSaving(false)
  }

  const toggleUseIn = (value: string) => {
    setUseIn((prev) =>
      prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value]
    )
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TypeBadge type={insight.type} />
            <span className="text-sm text-gray-500">ID: {insight.id}</span>
          </div>
          <button onClick={onCancel} className="text-gray-400 hover:text-gray-600">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Title */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Content */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Content</label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={4}
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Actionable Insight */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Actionable Insight (optional)
          </label>
          <textarea
            value={actionable}
            onChange={(e) => setActionable(e.target.value)}
            rows={2}
            placeholder="What should the reader do with this information?"
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Supporting Data (read-only) */}
        {insight.supporting_data.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Supporting Data</label>
            <div className="space-y-2">
              {insight.supporting_data.map((sd, i) => (
                <div key={i} className="p-3 bg-gray-50 rounded-lg text-sm">
                  <p className="font-medium text-gray-700">{sd.claim}</p>
                  <p className="text-gray-500 mt-1">
                    Source: {sd.source}
                    {sd.date && ` (${sd.date})`}
                    <span className="ml-2 text-xs px-2 py-0.5 bg-gray-200 rounded">{sd.credibility}</span>
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Use In */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Show In</label>
          <div className="flex flex-wrap gap-2">
            {USE_IN_OPTIONS.map((option) => (
              <button
                key={option}
                onClick={() => toggleUseIn(option)}
                className={`px-3 py-1 rounded-full text-sm transition-colors ${
                  useIn.includes(option)
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {option.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Topics */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Topics (comma-separated)
          </label>
          <input
            type="text"
            value={topics}
            onChange={(e) => setTopics(e.target.value)}
            placeholder="e.g., workflows, roi, automation"
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Reviewed Toggle */}
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            id="reviewed"
            checked={reviewed}
            onChange={(e) => setReviewed(e.target.checked)}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <label htmlFor="reviewed" className="text-sm font-medium text-gray-700">
            Mark as reviewed
          </label>
        </div>

        {/* Source Info (read-only) */}
        <div className="p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-500">
            <span className="font-medium">Source:</span> {insight.source.title}
            {insight.source.author && ` by ${insight.source.author}`}
            {insight.source.date && ` (${insight.source.date})`}
          </p>
          {insight.source.url && (
            <a
              href={insight.source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:underline mt-1 block"
            >
              View source
            </a>
          )}
          <p className="text-xs text-gray-400 mt-2">Extracted: {insight.extracted_at}</p>
        </div>
      </div>

      {/* Actions */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
        <button
          onClick={onDelete}
          className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
        >
          Delete
        </button>
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// Main Component
// ============================================================================

// API Response types
interface InsightsListResponse {
  success: boolean
  data: Insight[]
  total: number
}

export default function InsightsAdmin() {
  const [searchParams] = useSearchParams()
  const [insights, setInsights] = useState<Insight[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedInsight, setSelectedInsight] = useState<Insight | null>(null)
  const [filterType, setFilterType] = useState<string>(searchParams.get('type') || '')
  const [filterReviewed, setFilterReviewed] = useState<string>(
    searchParams.get('filter') === 'unreviewed' ? 'false' : ''
  )

  const fetchInsights = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filterType) params.set('type', filterType)
      if (filterReviewed === 'false') params.set('reviewed_only', 'false')

      const response = await apiClient.get<InsightsListResponse>(`/api/admin/insights/list?${params.toString()}`)
      setInsights(response.data.data)
    } catch (err) {
      console.error('Failed to fetch insights:', err)
    } finally {
      setLoading(false)
    }
  }, [filterType, filterReviewed])

  useEffect(() => {
    fetchInsights()
  }, [fetchInsights])

  const handleReview = async (insight: Insight) => {
    try {
      await apiClient.post(`/api/admin/insights/${insight.id}/review?reviewed=true`)
      fetchInsights()
    } catch (err) {
      console.error('Failed to mark as reviewed:', err)
    }
  }

  const handleSave = async (updates: Partial<Insight>) => {
    if (!selectedInsight) return

    try {
      await apiClient.put(`/api/admin/insights/${selectedInsight.id}`, updates)
      setSelectedInsight(null)
      fetchInsights()
    } catch (err) {
      console.error('Failed to save insight:', err)
    }
  }

  const handleDelete = async () => {
    if (!selectedInsight) return
    if (!confirm('Are you sure you want to delete this insight?')) return

    try {
      await apiClient.delete(`/api/admin/insights/${selectedInsight.id}`)
      setSelectedInsight(null)
      fetchInsights()
    } catch (err) {
      console.error('Failed to delete insight:', err)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link to="/admin" className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Curated Insights</h1>
                <p className="text-gray-500 text-sm mt-0.5">
                  {loading ? 'Loading...' : `${insights.length} insights`}
                  {filterType && ` • ${filterType.replace('_', ' ')}`}
                  {filterReviewed === 'false' && ' • unreviewed only'}
                </p>
              </div>
            </div>
            <Link
              to="/admin/insights/extract"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-violet-600 to-blue-600 text-white rounded-xl hover:from-violet-700 hover:to-blue-700 font-medium shadow-lg shadow-violet-200 transition-all"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Extract New
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8">
          {/* Filters Sidebar */}
          <div className="w-64 flex-shrink-0 hidden lg:block">
            <div className="bg-white rounded-2xl border border-gray-100 p-5 sticky top-24 shadow-sm">
              <h3 className="font-semibold text-gray-900 mb-5 flex items-center gap-2">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                </svg>
                Filters
              </h3>

              {/* Type Filter */}
              <div className="mb-5">
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Type</label>
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-xl text-sm bg-gray-50/50 focus:bg-white focus:border-violet-300 focus:ring-2 focus:ring-violet-100 transition-all"
                >
                  <option value="">All Types</option>
                  {INSIGHT_TYPES.map((type) => (
                    <option key={type} value={type}>
                      {type.replace('_', ' ')}
                    </option>
                  ))}
                </select>
              </div>

              {/* Reviewed Filter */}
              <div className="mb-5">
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Status</label>
                <select
                  value={filterReviewed}
                  onChange={(e) => setFilterReviewed(e.target.value)}
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-xl text-sm bg-gray-50/50 focus:bg-white focus:border-violet-300 focus:ring-2 focus:ring-violet-100 transition-all"
                >
                  <option value="">All</option>
                  <option value="true">Reviewed</option>
                  <option value="false">Pending Review</option>
                </select>
              </div>

              {/* Clear Filters */}
              {(filterType || filterReviewed) && (
                <button
                  onClick={() => {
                    setFilterType('')
                    setFilterReviewed('')
                  }}
                  className="w-full text-sm text-violet-600 hover:text-violet-700 font-medium py-2 hover:bg-violet-50 rounded-lg transition-colors"
                >
                  Clear all filters
                </button>
              )}
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1 min-w-0">
            {selectedInsight ? (
              <InsightEditor
                insight={selectedInsight}
                onSave={handleSave}
                onDelete={handleDelete}
                onCancel={() => setSelectedInsight(null)}
              />
            ) : (
              <InsightList
                insights={insights}
                loading={loading}
                onSelect={setSelectedInsight}
                onReview={handleReview}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
