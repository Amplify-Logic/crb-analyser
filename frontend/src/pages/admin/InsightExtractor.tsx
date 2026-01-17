/**
 * Insight Extractor Page
 *
 * UI for extracting insights from raw content using AI.
 * Flow: Paste content -> AI extracts -> Review/Edit -> Save
 */

import { useState } from 'react'
import { Link } from 'react-router-dom'
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

interface ExtractedInsight {
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
  // UI state
  selected?: boolean
}

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

function ExtractedInsightCard({
  insight,
  onToggle,
  onEdit,
}: {
  insight: ExtractedInsight
  onToggle: () => void
  onEdit: () => void
}) {
  return (
    <div
      className={`bg-white rounded-xl p-4 border transition-all ${
        insight.selected
          ? 'border-blue-300 ring-2 ring-blue-100'
          : 'border-gray-100 hover:border-gray-200'
      }`}
    >
      <div className="flex items-start gap-3">
        {/* Checkbox */}
        <div className="pt-1">
          <input
            type="checkbox"
            checked={insight.selected}
            onChange={onToggle}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <TypeBadge type={insight.type} />
            {insight.tags.use_in.map((use) => (
              <span key={use} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                {use}
              </span>
            ))}
          </div>
          <h3 className="font-medium text-gray-900">{insight.title}</h3>
          <p className="text-sm text-gray-600 mt-1 line-clamp-2">{insight.content}</p>

          {/* Supporting Data */}
          {insight.supporting_data.length > 0 && (
            <div className="mt-2 space-y-1">
              {insight.supporting_data.slice(0, 2).map((sd, i) => (
                <p key={i} className="text-xs text-gray-500">
                  <span className="font-medium">{sd.source}:</span> {sd.claim.slice(0, 100)}
                  {sd.claim.length > 100 && '...'}
                </p>
              ))}
            </div>
          )}

          {insight.actionable_insight && (
            <p className="text-xs text-blue-600 mt-2">
              Actionable: {insight.actionable_insight.slice(0, 80)}...
            </p>
          )}
        </div>

        {/* Edit Button */}
        <button
          onClick={(e) => {
            e.stopPropagation()
            onEdit()
          }}
          className="text-gray-400 hover:text-gray-600 p-1"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
            />
          </svg>
        </button>
      </div>
    </div>
  )
}

function InsightEditModal({
  insight,
  onSave,
  onCancel,
}: {
  insight: ExtractedInsight
  onSave: (updated: ExtractedInsight) => void
  onCancel: () => void
}) {
  const [title, setTitle] = useState(insight.title)
  const [content, setContent] = useState(insight.content)
  const [actionable, setActionable] = useState(insight.actionable_insight || '')
  const [useIn, setUseIn] = useState<string[]>(insight.tags.use_in)
  const [topics, setTopics] = useState(insight.tags.topics.join(', '))

  const handleSave = () => {
    onSave({
      ...insight,
      title,
      content,
      actionable_insight: actionable || undefined,
      tags: {
        ...insight.tags,
        use_in: useIn,
        topics: topics.split(',').map((t) => t.trim()).filter(Boolean),
      },
    })
  }

  const toggleUseIn = (value: string) => {
    setUseIn((prev) =>
      prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value]
    )
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TypeBadge type={insight.type} />
              <span className="text-sm text-gray-500">Edit Insight</span>
            </div>
            <button onClick={onCancel} className="text-gray-400 hover:text-gray-600">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>

        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Content</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Actionable Insight
            </label>
            <textarea
              value={actionable}
              onChange={(e) => setActionable(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

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

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Topics (comma-separated)
            </label>
            <input
              type="text"
              value={topics}
              onChange={(e) => setTopics(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// Main Component
// ============================================================================

type Step = 'input' | 'extracting' | 'review' | 'saving' | 'done'

// API Response types
interface ExtractionResponse {
  success: boolean
  data: {
    source: InsightSource
    extracted_at: string
    insights: ExtractedInsight[]
    extraction_notes: string | null
  }
  message: string
}

interface SaveResponse {
  success: boolean
  data: { added: number; skipped: number }
  message: string
}

export default function InsightExtractor() {
  const [step, setStep] = useState<Step>('input')

  // Input state
  const [rawContent, setRawContent] = useState('')
  const [sourceTitle, setSourceTitle] = useState('')
  const [sourceAuthor, setSourceAuthor] = useState('')
  const [sourceUrl, setSourceUrl] = useState('')
  const [sourceDate, setSourceDate] = useState('')
  const [sourceType, setSourceType] = useState('article')

  // Extraction state
  const [insights, setInsights] = useState<ExtractedInsight[]>([])
  const [extractionNotes, setExtractionNotes] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Edit state
  const [editingInsight, setEditingInsight] = useState<ExtractedInsight | null>(null)

  // Save state
  const [saveResult, setSaveResult] = useState<{ added: number; skipped: number } | null>(null)

  const handleExtract = async () => {
    if (!rawContent.trim() || !sourceTitle.trim()) {
      setError('Please provide content and a source title')
      return
    }

    setStep('extracting')
    setError(null)

    try {
      const response = await apiClient.post<ExtractionResponse>(
        '/api/admin/insights/extract',
        {
          raw_content: rawContent,
          source_title: sourceTitle,
          source_author: sourceAuthor || undefined,
          source_url: sourceUrl || undefined,
          source_date: sourceDate || undefined,
          source_type: sourceType,
        },
        { timeout: 120000 } // 2 minute timeout for AI extraction
      )

      const extracted = response.data.data.insights.map((i) => ({
        ...i,
        selected: true,
      }))

      setInsights(extracted)
      setExtractionNotes(response.data.data.extraction_notes)
      setStep('review')
    } catch (err: unknown) {
      console.error('Extraction failed:', err)
      // Handle both Error instances and ApiError objects from apiClient
      const message =
        (err as { message?: string })?.message ||
        (err instanceof Error ? err.message : 'Failed to extract insights')
      setError(message)
      setStep('input')
    }
  }

  const handleToggle = (id: string) => {
    setInsights((prev) =>
      prev.map((i) => (i.id === id ? { ...i, selected: !i.selected } : i))
    )
  }

  const handleEditSave = (updated: ExtractedInsight) => {
    setInsights((prev) => prev.map((i) => (i.id === updated.id ? updated : i)))
    setEditingInsight(null)
  }

  const handleSave = async () => {
    const selected = insights.filter((i) => i.selected)
    if (selected.length === 0) {
      setError('Please select at least one insight to save')
      return
    }

    setStep('saving')
    setError(null)

    try {
      const response = await apiClient.post<SaveResponse>('/api/admin/insights/save-extracted', selected)
      setSaveResult(response.data.data)
      setStep('done')
    } catch (err: unknown) {
      console.error('Save failed:', err)
      // Handle both Error instances and ApiError objects from apiClient
      const message =
        (err as { message?: string })?.message ||
        (err instanceof Error ? err.message : 'Failed to save insights')
      setError(message)
      setStep('review')
    }
  }

  const selectedCount = insights.filter((i) => i.selected).length

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center gap-4">
            <Link to="/admin/insights" className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Extract Insights</h1>
              <p className="text-gray-500 text-sm mt-0.5">
                Paste content and let AI extract structured insights
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-2xl text-red-700 flex items-center gap-3">
            <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {error}
          </div>
        )}

        {/* Step: Input */}
        {step === 'input' && (
          <div className="space-y-6">
            {/* Source Info */}
            <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 mb-5 flex items-center gap-2">
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
                Source Information
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Title *
                  </label>
                  <input
                    type="text"
                    value={sourceTitle}
                    onChange={(e) => setSourceTitle(e.target.value)}
                    placeholder="e.g., Top 6 AI Trends for 2026"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Author</label>
                  <input
                    type="text"
                    value={sourceAuthor}
                    onChange={(e) => setSourceAuthor(e.target.value)}
                    placeholder="e.g., Jeff Su"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">URL</label>
                  <input
                    type="text"
                    value={sourceUrl}
                    onChange={(e) => setSourceUrl(e.target.value)}
                    placeholder="https://..."
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div className="flex gap-4">
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                    <input
                      type="date"
                      value={sourceDate}
                      onChange={(e) => setSourceDate(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                    <select
                      value={sourceType}
                      onChange={(e) => setSourceType(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="article">Article</option>
                      <option value="youtube">YouTube</option>
                      <option value="report">Report</option>
                      <option value="podcast">Podcast</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="bg-white rounded-xl border border-gray-100 p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Content *</h2>
              <textarea
                value={rawContent}
                onChange={(e) => setRawContent(e.target.value)}
                rows={16}
                placeholder="Paste the transcript, article text, or report content here..."
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              />
              <p className="text-xs text-gray-400 mt-2">
                {rawContent.length.toLocaleString()} characters
              </p>
            </div>

            {/* Extract Button */}
            <div className="flex justify-end">
              <button
                onClick={handleExtract}
                disabled={!rawContent.trim() || !sourceTitle.trim()}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Extract Insights with AI
              </button>
            </div>
          </div>
        )}

        {/* Step: Extracting */}
        {step === 'extracting' && (
          <div className="bg-white rounded-2xl border border-gray-100 p-16 text-center shadow-sm">
            <div className="relative w-16 h-16 mx-auto mb-6">
              <div className="absolute inset-0 rounded-full bg-gradient-to-r from-violet-500 to-blue-500 animate-spin" style={{ clipPath: 'polygon(50% 0%, 100% 0%, 100% 100%, 50% 100%)' }} />
              <div className="absolute inset-1 rounded-full bg-white" />
              <div className="absolute inset-3 rounded-full bg-gradient-to-br from-violet-100 to-blue-100 flex items-center justify-center">
                <span className="text-2xl">✨</span>
              </div>
            </div>
            <h2 className="text-xl font-semibold text-gray-900">Extracting Insights...</h2>
            <p className="text-gray-500 mt-2 max-w-sm mx-auto">
              AI is analyzing the content and identifying valuable insights. This may take 30-60 seconds.
            </p>
            <div className="mt-6 flex items-center justify-center gap-1">
              <div className="w-2 h-2 bg-violet-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 bg-violet-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 bg-violet-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        )}

        {/* Step: Review */}
        {step === 'review' && (
          <div className="space-y-6">
            {/* Summary */}
            <div className="bg-white rounded-xl border border-gray-100 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-medium text-gray-900">
                    Found {insights.length} Insights
                  </h2>
                  <p className="text-gray-500 mt-1">
                    {selectedCount} selected for saving
                  </p>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={() => setInsights((prev) => prev.map((i) => ({ ...i, selected: true })))}
                    className="text-sm text-blue-600 hover:text-blue-700"
                  >
                    Select All
                  </button>
                  <button
                    onClick={() => setInsights((prev) => prev.map((i) => ({ ...i, selected: false })))}
                    className="text-sm text-gray-500 hover:text-gray-700"
                  >
                    Deselect All
                  </button>
                </div>
              </div>
              {extractionNotes && (
                <p className="text-sm text-gray-500 mt-3 p-3 bg-gray-50 rounded-lg">
                  Notes: {extractionNotes}
                </p>
              )}
            </div>

            {/* Insights List */}
            <div className="space-y-3">
              {insights.map((insight) => (
                <ExtractedInsightCard
                  key={insight.id}
                  insight={insight}
                  onToggle={() => handleToggle(insight.id)}
                  onEdit={() => setEditingInsight(insight)}
                />
              ))}
            </div>

            {/* Actions */}
            <div className="flex justify-between items-center pt-4">
              <button
                onClick={() => setStep('input')}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                Back to Edit
              </button>
              <button
                onClick={handleSave}
                disabled={selectedCount === 0}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Save {selectedCount} Insight{selectedCount !== 1 ? 's' : ''}
              </button>
            </div>
          </div>
        )}

        {/* Step: Saving */}
        {step === 'saving' && (
          <div className="bg-white rounded-2xl border border-gray-100 p-16 text-center shadow-sm">
            <div className="relative w-16 h-16 mx-auto mb-6">
              <div className="absolute inset-0 rounded-full border-4 border-emerald-100" />
              <div className="absolute inset-0 rounded-full border-4 border-emerald-500 border-t-transparent animate-spin" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900">Saving Insights...</h2>
          </div>
        )}

        {/* Step: Done */}
        {step === 'done' && saveResult && (
          <div className="bg-white rounded-2xl border border-gray-100 p-16 text-center shadow-sm">
            <div className="w-20 h-20 bg-gradient-to-br from-emerald-100 to-emerald-200 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <svg className="w-10 h-10 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900">Insights Saved!</h2>
            <p className="text-gray-500 mt-3 text-lg">
              Added <span className="font-semibold text-emerald-600">{saveResult.added}</span> insight{saveResult.added !== 1 ? 's' : ''}
              {saveResult.skipped > 0 && (
                <span className="text-gray-400"> ({saveResult.skipped} skipped as duplicates)</span>
              )}
            </p>
            <div className="mt-8 flex justify-center gap-4">
              <button
                onClick={() => {
                  setStep('input')
                  setRawContent('')
                  setSourceTitle('')
                  setSourceAuthor('')
                  setSourceUrl('')
                  setSourceDate('')
                  setInsights([])
                  setSaveResult(null)
                }}
                className="px-5 py-2.5 border border-gray-200 rounded-xl hover:bg-gray-50 font-medium transition-colors"
              >
                Extract More
              </button>
              <Link
                to="/admin/insights"
                className="px-5 py-2.5 bg-gradient-to-r from-violet-600 to-blue-600 text-white rounded-xl hover:from-violet-700 hover:to-blue-700 font-medium shadow-lg shadow-violet-200 transition-all"
              >
                View All Insights
              </Link>
            </div>
          </div>
        )}

        {/* Edit Modal */}
        {editingInsight && (
          <InsightEditModal
            insight={editingInsight}
            onSave={handleEditSave}
            onCancel={() => setEditingInsight(null)}
          />
        )}
      </div>
    </div>
  )
}
