/**
 * Vendor Research Buttons
 *
 * Refresh Stale, Discover New, and Scout Emerging buttons
 * with preview modals for the vendor research agent.
 */

import { useState, useEffect } from 'react'
import apiClient from '../../services/apiClient'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8383'

// Types
interface FieldChange {
  field: string
  old_value: string | number | boolean | null
  new_value: string | number | boolean | null
  is_significant: boolean
}

interface VendorUpdate {
  vendor_slug: string
  vendor_name: string
  source_url: string
  changes: FieldChange[]
  has_significant_changes?: boolean
  extracted_data?: Record<string, unknown>
}

interface DiscoveredVendor {
  name: string
  slug: string
  website: string
  description?: string
  category?: string
  sources: string[]
  relevance_score: number
  warning?: string
}

interface ResearchButtonsProps {
  category?: string
  industry?: string
  onComplete?: () => void
}

export default function VendorResearchButtons({
  category,
  industry,
  onComplete,
}: ResearchButtonsProps) {
  const [staleCount, setStaleCount] = useState<number>(0)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [isDiscovering, setIsDiscovering] = useState(false)
  const [showRefreshModal, setShowRefreshModal] = useState(false)
  const [showDiscoverModal, setShowDiscoverModal] = useState(false)

  // Refresh modal state
  const [refreshProgress, setRefreshProgress] = useState<string>('')
  const [refreshUpdates, setRefreshUpdates] = useState<VendorUpdate[]>([])
  const [refreshErrors, setRefreshErrors] = useState<string[]>([])
  const [selectedUpdates, setSelectedUpdates] = useState<Set<string>>(new Set())

  // Discover modal state
  const [discoverProgress, setDiscoverProgress] = useState<string>('')
  const [discoveredVendors, setDiscoveredVendors] = useState<DiscoveredVendor[]>([])
  const [selectedDiscoveries, setSelectedDiscoveries] = useState<Set<string>>(new Set())

  // Fetch stale count on mount and when filters change
  useEffect(() => {
    fetchStaleCount()
  }, [category, industry])

  const fetchStaleCount = async () => {
    try {
      const params = new URLSearchParams()
      if (category) params.set('category', category)
      if (industry) params.set('industry', industry)

      console.log('[VendorResearch] Fetching stale count...', { category, industry })
      const response = await apiClient.get<{ count: number }>(`/api/admin/research/stale-count?${params}`)
      console.log('[VendorResearch] Stale count:', response.data.count)
      setStaleCount(response.data.count)
    } catch (error) {
      console.error('[VendorResearch] Failed to fetch stale count:', error)
    }
  }

  // Start refresh with SSE
  const startRefresh = async () => {
    setShowRefreshModal(true)
    setIsRefreshing(true)
    setRefreshUpdates([])
    setRefreshErrors([])
    setRefreshProgress('Starting...')

    try {
      const response = await fetch(`${API_BASE}/api/admin/research/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          scope: 'stale',
          category,
          industry,
        }),
      })

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No response stream')
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const text = decoder.decode(value)
        const lines = text.split('\n').filter(line => line.startsWith('data: '))

        for (const line of lines) {
          try {
            const data = JSON.parse(line.slice(6))
            handleRefreshUpdate(data)
          } catch (e) {
            // Skip parse errors
          }
        }
      }
    } catch (error) {
      console.error('Refresh failed:', error)
      setRefreshProgress('Error: ' + (error as Error).message)
    } finally {
      setIsRefreshing(false)
    }
  }

  const handleRefreshUpdate = (data: Record<string, unknown>) => {
    const type = data.type as string

    if (type === 'started') {
      setRefreshProgress(`Scanning ${data.total} vendors...`)
    } else if (type === 'progress') {
      setRefreshProgress(`${data.current}/${data.total} - ${data.vendor}`)
    } else if (type === 'update') {
      const update = data as unknown as VendorUpdate
      setRefreshUpdates(prev => [...prev, update])
      // Pre-select non-significant updates
      if (!update.has_significant_changes) {
        setSelectedUpdates(prev => new Set([...prev, update.vendor_slug]))
      }
    } else if (type === 'error') {
      setRefreshErrors(prev => [...prev, `${data.vendor_name}: ${data.error}`])
    } else if (type === 'completed') {
      setRefreshProgress(`Complete: ${data.updates} updates, ${data.errors} errors`)
    }
  }

  // Start discover with SSE
  const startDiscover = async () => {
    if (!category) {
      alert('Please select a category first')
      return
    }

    setShowDiscoverModal(true)
    setIsDiscovering(true)
    setDiscoveredVendors([])
    setDiscoverProgress('Searching...')

    try {
      const response = await fetch(`${API_BASE}/api/admin/research/discover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          category,
          industry,
          limit: 20,
        }),
      })

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No response stream')
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const text = decoder.decode(value)
        const lines = text.split('\n').filter(line => line.startsWith('data: '))

        for (const line of lines) {
          try {
            const data = JSON.parse(line.slice(6))
            handleDiscoverUpdate(data)
          } catch (e) {
            // Skip parse errors
          }
        }
      }
    } catch (error) {
      console.error('Discover failed:', error)
      setDiscoverProgress('Error: ' + (error as Error).message)
    } finally {
      setIsDiscovering(false)
    }
  }

  const handleDiscoverUpdate = (data: Record<string, unknown>) => {
    const type = data.type as string

    if (type === 'searching') {
      setDiscoverProgress(`Searching ${data.category}...`)
    } else if (type === 'found') {
      setDiscoverProgress(`Found ${data.raw_results} results, filtering...`)
    } else if (type === 'validating') {
      setDiscoverProgress(`Validating ${data.current}/${data.total}: ${data.vendor}`)
    } else if (type === 'candidate') {
      const vendor = data.vendor as DiscoveredVendor
      setDiscoveredVendors(prev => [...prev, vendor])
      // Pre-select high relevance vendors without warnings
      if (vendor.relevance_score >= 0.7 && !vendor.warning) {
        setSelectedDiscoveries(prev => new Set([...prev, vendor.slug]))
      }
    } else if (type === 'completed') {
      setDiscoverProgress(`Complete: ${data.candidates} candidates found`)
    }
  }

  // Apply selected updates
  const applyUpdates = async () => {
    if (selectedUpdates.size === 0) return

    try {
      await apiClient.post('/api/admin/research/apply-updates', {
        task_id: 'manual',
        approved_slugs: Array.from(selectedUpdates),
        updates: refreshUpdates.filter(u => selectedUpdates.has(u.vendor_slug)),
      })

      alert(`Applied ${selectedUpdates.size} updates`)
      setShowRefreshModal(false)
      fetchStaleCount()
      onComplete?.()
    } catch (error) {
      console.error('Failed to apply updates:', error)
      alert('Failed to apply updates')
    }
  }

  // Add selected discoveries
  const addDiscoveries = async () => {
    if (selectedDiscoveries.size === 0) return

    try {
      await apiClient.post('/api/admin/research/apply-discoveries', {
        task_id: 'manual',
        approved_vendors: discoveredVendors.filter(v => selectedDiscoveries.has(v.slug)),
      })

      alert(`Added ${selectedDiscoveries.size} vendors`)
      setShowDiscoverModal(false)
      onComplete?.()
    } catch (error) {
      console.error('Failed to add vendors:', error)
      alert('Failed to add vendors')
    }
  }

  const toggleUpdate = (slug: string) => {
    setSelectedUpdates(prev => {
      const next = new Set(prev)
      if (next.has(slug)) {
        next.delete(slug)
      } else {
        next.add(slug)
      }
      return next
    })
  }

  const toggleDiscovery = (slug: string) => {
    setSelectedDiscoveries(prev => {
      const next = new Set(prev)
      if (next.has(slug)) {
        next.delete(slug)
      } else {
        next.add(slug)
      }
      return next
    })
  }

  return (
    <>
      {/* Buttons */}
      <div className="flex items-center gap-2">
        <button
          onClick={startRefresh}
          disabled={staleCount === 0 || isRefreshing}
          className={`px-3 py-2 text-sm font-medium rounded-lg border transition-colors flex items-center gap-2 ${
            staleCount > 0
              ? 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100'
              : 'bg-gray-50 text-gray-400 border-gray-200 cursor-not-allowed'
          }`}
        >
          <span>Refresh Stale</span>
          {staleCount > 0 && (
            <span className={`px-1.5 py-0.5 text-xs rounded-full ${
              staleCount > 10 ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
            }`}>
              {staleCount}
            </span>
          )}
        </button>

        <button
          onClick={startDiscover}
          disabled={isDiscovering}
          className="px-3 py-2 text-sm font-medium rounded-lg border bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100 transition-colors"
        >
          Discover New
        </button>
      </div>

      {/* Refresh Modal */}
      {showRefreshModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col">
            <div className="p-4 border-b flex items-center justify-between">
              <h3 className="text-lg font-semibold">Refresh Stale Vendors</h3>
              <button
                onClick={() => setShowRefreshModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="p-4 border-b bg-gray-50">
              <div className="text-sm text-gray-600">{refreshProgress}</div>
              {isRefreshing && (
                <div className="mt-2 h-1 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 animate-pulse w-full" />
                </div>
              )}
            </div>

            <div className="flex-1 overflow-auto p-4">
              {refreshUpdates.length === 0 && !isRefreshing && (
                <div className="text-center text-gray-500 py-8">
                  No updates found
                </div>
              )}

              {refreshUpdates.map(update => (
                <div
                  key={update.vendor_slug}
                  className={`p-3 mb-2 rounded-lg border ${
                    update.has_significant_changes ? 'border-amber-200 bg-amber-50' : 'border-gray-200'
                  }`}
                >
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedUpdates.has(update.vendor_slug)}
                      onChange={() => toggleUpdate(update.vendor_slug)}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <div className="font-medium flex items-center gap-2">
                        {update.vendor_name}
                        {update.has_significant_changes && (
                          <span className="text-xs text-amber-600">significant changes</span>
                        )}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        {update.changes.map((change, i) => (
                          <div key={i} className="flex items-center gap-2">
                            <span className="text-gray-500">{change.field}:</span>
                            <span className="text-red-600 line-through">
                              {String(change.old_value ?? 'null')}
                            </span>
                            <span>→</span>
                            <span className="text-green-600">
                              {String(change.new_value ?? 'null')}
                            </span>
                            {change.is_significant && <span className="text-amber-500">⚠️</span>}
                          </div>
                        ))}
                      </div>
                    </div>
                  </label>
                </div>
              ))}

              {refreshErrors.length > 0 && (
                <div className="mt-4 p-3 bg-red-50 rounded-lg">
                  <div className="font-medium text-red-700 mb-2">Errors</div>
                  {refreshErrors.map((error, i) => (
                    <div key={i} className="text-sm text-red-600">{error}</div>
                  ))}
                </div>
              )}
            </div>

            <div className="p-4 border-t flex justify-between items-center">
              <div className="text-sm text-gray-500">
                {selectedUpdates.size} of {refreshUpdates.length} selected
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowRefreshModal(false)}
                  className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  onClick={applyUpdates}
                  disabled={selectedUpdates.size === 0 || isRefreshing}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  Apply {selectedUpdates.size} Updates
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Discover Modal */}
      {showDiscoverModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col">
            <div className="p-4 border-b flex items-center justify-between">
              <h3 className="text-lg font-semibold">Discover New Vendors</h3>
              <button
                onClick={() => setShowDiscoverModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="p-4 border-b bg-gray-50">
              <div className="text-sm text-gray-600">{discoverProgress}</div>
              {isDiscovering && (
                <div className="mt-2 h-1 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 animate-pulse w-full" />
                </div>
              )}
            </div>

            <div className="flex-1 overflow-auto p-4">
              {discoveredVendors.length === 0 && !isDiscovering && (
                <div className="text-center text-gray-500 py-8">
                  No new vendors found
                </div>
              )}

              {discoveredVendors.map(vendor => (
                <div
                  key={vendor.slug}
                  className={`p-3 mb-2 rounded-lg border ${
                    vendor.warning ? 'border-amber-200 bg-amber-50' : 'border-gray-200'
                  }`}
                >
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedDiscoveries.has(vendor.slug)}
                      onChange={() => toggleDiscovery(vendor.slug)}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <div className="font-medium flex items-center gap-2">
                        {vendor.name}
                        <span className={`text-xs px-1.5 py-0.5 rounded ${
                          vendor.relevance_score >= 0.7
                            ? 'bg-green-100 text-green-700'
                            : vendor.relevance_score >= 0.5
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-gray-100 text-gray-600'
                        }`}>
                          {Math.round(vendor.relevance_score * 100)}% relevant
                        </span>
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        {vendor.description}
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        {vendor.website} • Sources: {vendor.sources.join(', ')}
                      </div>
                      {vendor.warning && (
                        <div className="text-xs text-amber-600 mt-1">
                          ⚠️ {vendor.warning}
                        </div>
                      )}
                    </div>
                  </label>
                </div>
              ))}
            </div>

            <div className="p-4 border-t flex justify-between items-center">
              <div className="text-sm text-gray-500">
                {selectedDiscoveries.size} of {discoveredVendors.length} selected
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowDiscoverModal(false)}
                  className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  onClick={addDiscoveries}
                  disabled={selectedDiscoveries.size === 0 || isDiscovering}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  Add {selectedDiscoveries.size} Vendors
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
