/**
 * Knowledge Stats Component
 *
 * Dashboard showing embedding statistics and similarity testing.
 */

import { useState, useEffect } from 'react'
import apiClient from '../../services/apiClient'

interface EmbeddingStats {
  total_items: number
  embedded_count: number
  needs_update_count: number
  by_type: Record<
    string,
    {
      total: number
      embedded: number
      needs_update: number
    }
  >
  last_sync?: string
}

interface SearchResult {
  content_type: string
  content_id: string
  title: string
  preview: string
  industry?: string
  similarity: number
}

const CONTENT_TYPE_LABELS: Record<string, string> = {
  vendor: 'Vendors',
  opportunity: 'Opportunities',
  benchmark: 'Benchmarks',
  case_study: 'Case Studies',
  pattern: 'Patterns',
  insight: 'Insights',
}

export default function KnowledgeStats() {
  const [stats, setStats] = useState<EmbeddingStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchIndustry, setSearchIndustry] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [searching, setSearching] = useState(false)
  const [reembedding, setReembedding] = useState<string | null>(null)

  useEffect(() => {
    loadStats()
  }, [])

  async function loadStats() {
    try {
      const { data } = await apiClient.get<EmbeddingStats>('/api/admin/knowledge/stats/embeddings')
      setStats(data)
    } catch (err) {
      console.error('Failed to load stats:', err)
    } finally {
      setLoading(false)
    }
  }

  async function handleSearch() {
    if (!searchQuery.trim()) return

    setSearching(true)
    try {
      const params = new URLSearchParams({ q: searchQuery })
      if (searchIndustry) params.set('industry', searchIndustry)

      const { data } = await apiClient.get<{ results: SearchResult[] }>(`/api/admin/knowledge/test-search?${params}`)
      setSearchResults(data.results || [])
    } catch (err) {
      console.error('Search failed:', err)
    } finally {
      setSearching(false)
    }
  }

  async function handleReembedAll() {
    if (!confirm('Re-embed all items? This may take a while and use API credits.')) return

    setReembedding('all')
    try {
      await apiClient.post('/api/admin/knowledge/embed/all')
      await loadStats()
    } catch (err) {
      console.error('Re-embed failed:', err)
    } finally {
      setReembedding(null)
    }
  }

  async function handleReembedOutdated() {
    setReembedding('outdated')
    try {
      await apiClient.post('/api/admin/knowledge/embed/outdated')
      await loadStats()
    } catch (err) {
      console.error('Re-embed failed:', err)
    } finally {
      setReembedding(null)
    }
  }

  async function handleReembedType(type: string) {
    setReembedding(type)
    try {
      await apiClient.post(`/api/admin/knowledge/embed/type/${type}`)
      await loadStats()
    } catch (err) {
      console.error('Re-embed failed:', err)
    } finally {
      setReembedding(null)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-xl p-6 animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4" />
          <div className="grid grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-100 rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="bg-white rounded-xl p-12 text-center">
        <div className="text-4xl mb-4">⚠️</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Failed to load statistics
        </h3>
        <button
          onClick={loadStats}
          className="text-blue-600 hover:text-blue-700"
        >
          Try again
        </button>
      </div>
    )
  }

  const embeddedPercent = stats.total_items
    ? Math.round((stats.embedded_count / stats.total_items) * 100)
    : 0

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-5">
          <div className="text-sm text-gray-500 mb-1">Total Items</div>
          <div className="text-2xl font-semibold text-gray-900">
            {stats.total_items}
          </div>
        </div>
        <div className="bg-white rounded-xl p-5">
          <div className="text-sm text-gray-500 mb-1">Embedded</div>
          <div className="text-2xl font-semibold text-green-600">
            {stats.embedded_count}
            <span className="text-sm font-normal text-gray-400 ml-1">
              ({embeddedPercent}%)
            </span>
          </div>
        </div>
        <div className="bg-white rounded-xl p-5">
          <div className="text-sm text-gray-500 mb-1">Needs Update</div>
          <div className="text-2xl font-semibold text-amber-600">
            {stats.needs_update_count}
          </div>
        </div>
        <div className="bg-white rounded-xl p-5">
          <div className="text-sm text-gray-500 mb-1">Vector Index</div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-green-500" />
            <span className="text-lg font-medium text-gray-900">Healthy</span>
          </div>
        </div>
      </div>

      {/* Bulk Actions */}
      <div className="bg-white rounded-xl p-5">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Bulk Actions</h3>
        <div className="flex items-center gap-3">
          <button
            onClick={handleReembedOutdated}
            disabled={!!reembedding || stats.needs_update_count === 0}
            className="px-4 py-2 text-sm font-medium text-amber-700 bg-amber-50 hover:bg-amber-100 rounded-lg transition-colors disabled:opacity-50"
          >
            {reembedding === 'outdated' ? 'Processing...' : `Re-embed Outdated (${stats.needs_update_count})`}
          </button>
          <button
            onClick={handleReembedAll}
            disabled={!!reembedding}
            className="px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors disabled:opacity-50"
          >
            {reembedding === 'all' ? 'Processing...' : 'Re-embed All'}
          </button>
        </div>
      </div>

      {/* By Content Type */}
      <div className="bg-white rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h3 className="font-medium text-gray-900">By Content Type</h3>
        </div>
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Total
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Embedded
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Needs Update
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Action
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {Object.entries(stats.by_type).map(([type, data]) => (
              <tr key={type} className="hover:bg-gray-50">
                <td className="px-5 py-4 text-sm text-gray-900">
                  {CONTENT_TYPE_LABELS[type] || type}
                </td>
                <td className="px-5 py-4 text-sm text-gray-600 text-right">
                  {data.total}
                </td>
                <td className="px-5 py-4 text-sm text-right">
                  <span className="text-green-600">{data.embedded}</span>
                  {data.total > 0 && (
                    <span className="text-gray-400 ml-1">
                      ({Math.round((data.embedded / data.total) * 100)}%)
                    </span>
                  )}
                </td>
                <td className="px-5 py-4 text-sm text-right">
                  {data.needs_update > 0 ? (
                    <span className="text-amber-600">{data.needs_update}</span>
                  ) : (
                    <span className="text-gray-400">0</span>
                  )}
                </td>
                <td className="px-5 py-4 text-sm text-right">
                  <button
                    onClick={() => handleReembedType(type)}
                    disabled={!!reembedding}
                    className="text-blue-600 hover:text-blue-700 disabled:opacity-50"
                  >
                    {reembedding === type ? 'Processing...' : 'Re-embed'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Similarity Testing */}
      <div className="bg-white rounded-xl p-5">
        <h3 className="font-medium text-gray-900 mb-4">Similarity Testing</h3>
        <div className="flex items-center gap-3 mb-4">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Enter a test query..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <select
            value={searchIndustry}
            onChange={(e) => setSearchIndustry(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Industries</option>
            <option value="dental">Dental</option>
            <option value="home-services">Home Services</option>
            <option value="professional-services">Professional Services</option>
            <option value="recruiting">Recruiting</option>
            <option value="coaching">Coaching</option>
            <option value="veterinary">Veterinary</option>
          </select>
          <button
            onClick={handleSearch}
            disabled={searching || !searchQuery.trim()}
            className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {searching ? 'Searching...' : 'Search'}
          </button>
        </div>

        {searchResults.length > 0 && (
          <div className="space-y-2">
            {searchResults.map((result) => (
              <div
                key={`${result.content_type}-${result.content_id}`}
                className="flex items-start gap-4 p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex-shrink-0 w-12 text-right">
                  <span
                    className={`text-sm font-mono ${
                      result.similarity >= 0.8
                        ? 'text-green-600'
                        : result.similarity >= 0.6
                        ? 'text-amber-600'
                        : 'text-gray-500'
                    }`}
                  >
                    {result.similarity.toFixed(2)}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900 truncate">
                      {result.title}
                    </span>
                    <span className="text-xs px-1.5 py-0.5 bg-gray-200 text-gray-600 rounded">
                      {result.content_type}
                    </span>
                    {result.industry && (
                      <span className="text-xs px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded">
                        {result.industry}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 mt-1 line-clamp-1">
                    {result.preview}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}

        {searchResults.length === 0 && searchQuery && !searching && (
          <div className="text-center py-8 text-gray-500">
            No results found. Try a different query or embed more content.
          </div>
        )}
      </div>
    </div>
  )
}
