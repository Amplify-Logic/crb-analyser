/**
 * Knowledge Base Admin Page
 *
 * Admin UI for managing vendors, opportunities, benchmarks,
 * case studies, patterns, and insights.
 */

import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import apiClient from '../../services/apiClient'
import KnowledgeSidebar from '../../components/admin/KnowledgeSidebar'
import KnowledgeList from '../../components/admin/KnowledgeList'
import KnowledgeEditor from '../../components/admin/KnowledgeEditor'
import KnowledgeStats from '../../components/admin/KnowledgeStats'

// Types
export interface KnowledgeItem {
  id?: string
  content_type: string
  content_id: string
  industry?: string
  title: string
  content: string
  metadata: Record<string, any>
  source_file?: string
  embedded_at?: string
  content_hash?: string
  is_embedded: boolean
  needs_update: boolean
}

export interface ContentTypeInfo {
  label: string
  count: number
  categories?: string[]
  industries?: string[]
}

export default function KnowledgeBase() {
  const [searchParams, setSearchParams] = useSearchParams()

  // State
  const [contentTypes, setContentTypes] = useState<Record<string, ContentTypeInfo>>({})
  const [items, setItems] = useState<KnowledgeItem[]>([])
  const [selectedItem, setSelectedItem] = useState<KnowledgeItem | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [showEditor, setShowEditor] = useState(false)
  const [showStats, setShowStats] = useState(false)

  // Refs
  const searchInputRef = useRef<HTMLInputElement>(null)

  // Keyboard shortcut: Cmd+K to focus search
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        searchInputRef.current?.focus()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  // Get current filters from URL
  const currentType = searchParams.get('type') || 'vendor'
  const currentIndustry = searchParams.get('industry') || ''
  const currentPage = parseInt(searchParams.get('page') || '1', 10)

  // Load content types on mount
  useEffect(() => {
    loadContentTypes()
  }, [])

  // Load items when filters change
  useEffect(() => {
    if (!showStats) {
      loadItems()
    }
  }, [currentType, currentIndustry, currentPage, showStats])

  async function loadContentTypes() {
    try {
      const { data } = await apiClient.get<{ types: Record<string, ContentTypeInfo> }>('/api/admin/knowledge/types')
      setContentTypes(data.types || {})
    } catch (err) {
      console.error('Failed to load content types:', err)
    }
  }

  async function loadItems() {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (currentType) params.set('content_type', currentType)
      if (currentIndustry) params.set('industry', currentIndustry)
      params.set('page', currentPage.toString())
      params.set('page_size', '50')

      const { data } = await apiClient.get<{ items: KnowledgeItem[] }>(`/api/admin/knowledge/?${params}`)
      setItems(data.items || [])
    } catch (err) {
      console.error('Failed to load items:', err)
    } finally {
      setLoading(false)
    }
  }

  async function handleSearch(query: string) {
    if (!query.trim()) {
      loadItems()
      return
    }

    setLoading(true)
    try {
      const params = new URLSearchParams({ q: query })
      if (currentType) params.set('content_type', currentType)
      if (currentIndustry) params.set('industry', currentIndustry)

      interface SearchResult {
        id: string
        content_type: string
        content_id: string
        industry?: string
        title: string
        preview: string
        metadata?: Record<string, any>
      }
      const { data } = await apiClient.get<{ results: SearchResult[] }>(`/api/admin/knowledge/search?${params}`)
      // Transform search results to match KnowledgeItem structure
      setItems(
        data.results?.map((r) => ({
          id: r.id,
          content_type: r.content_type,
          content_id: r.content_id,
          industry: r.industry,
          title: r.title,
          content: r.preview,
          metadata: r.metadata || {},
          is_embedded: true,
          needs_update: false,
        })) || []
      )
    } catch (err) {
      console.error('Search failed:', err)
    } finally {
      setLoading(false)
    }
  }

  function handleTypeSelect(type: string) {
    setShowStats(false)
    setSearchParams({ type })
  }

  function handleStatsClick() {
    setShowStats(true)
    setSelectedItem(null)
    setShowEditor(false)
  }

  function handleItemSelect(item: KnowledgeItem) {
    setSelectedItem(item)
    setShowEditor(true)
  }

  function handleCreateNew() {
    setSelectedItem({
      content_type: currentType,
      content_id: '',
      title: '',
      content: '',
      metadata: {},
      is_embedded: false,
      needs_update: false,
    })
    setShowEditor(true)
  }

  async function handleSave(item: KnowledgeItem) {
    try {
      if (item.id) {
        // Update existing
        await apiClient.put(`/api/admin/knowledge/${item.content_type}/${item.content_id}`, {
          title: item.title,
          content: item.content,
          industry: item.industry,
          metadata: item.metadata,
        })
      } else {
        // Create new
        await apiClient.post(`/api/admin/knowledge/${item.content_type}`, {
          content_id: item.content_id,
          title: item.title,
          content: item.content,
          industry: item.industry,
          metadata: item.metadata,
        })
      }
      setShowEditor(false)
      setSelectedItem(null)
      loadItems()
      loadContentTypes()
    } catch (err) {
      console.error('Save failed:', err)
      throw err
    }
  }

  function handleDuplicate(item: KnowledgeItem) {
    // Create a copy with a new content_id
    const duplicatedItem: KnowledgeItem = {
      ...item,
      id: undefined,
      content_id: `${item.content_id}-copy-${Date.now().toString(36)}`,
      title: `${item.title} (Copy)`,
      is_embedded: false,
      needs_update: false,
    }
    setSelectedItem(duplicatedItem)
    setShowEditor(true)
  }

  async function handleDelete(item: KnowledgeItem) {
    if (!confirm(`Delete "${item.title}"? This cannot be undone.`)) return

    try {
      await apiClient.delete(`/api/admin/knowledge/${item.content_type}/${item.content_id}`)
      setShowEditor(false)
      setSelectedItem(null)
      loadItems()
      loadContentTypes()
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  async function handleReembed(item: KnowledgeItem) {
    try {
      await apiClient.post(`/api/admin/knowledge/embed/${item.content_type}/${item.content_id}`)
      loadItems()
    } catch (err) {
      console.error('Re-embed failed:', err)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <KnowledgeSidebar
        contentTypes={contentTypes}
        selectedType={currentType}
        onTypeSelect={handleTypeSelect}
        onStatsClick={handleStatsClick}
        showingStats={showStats}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-semibold text-gray-900">
                {showStats ? 'Embedding Statistics' : contentTypes[currentType]?.label || 'Knowledge Base'}
              </h1>
              {!showStats && (
                <span className="text-sm text-gray-500">
                  {contentTypes[currentType]?.count || 0} items
                </span>
              )}
            </div>

            <div className="flex items-center gap-4">
              {/* Search */}
              <div className="relative">
                <input
                  ref={searchInputRef}
                  type="text"
                  placeholder="Search... (⌘K)"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch(searchQuery)}
                  className="w-64 px-4 py-2 pl-10 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <svg
                  className="absolute left-3 top-2.5 h-4 w-4 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </div>

              {!showStats && (
                <button
                  onClick={handleCreateNew}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
                >
                  + Add New
                </button>
              )}
            </div>
          </div>
        </header>

        {/* Content Area */}
        <main className="flex-1 overflow-auto p-6">
          {showStats ? (
            <KnowledgeStats />
          ) : showEditor && selectedItem ? (
            <KnowledgeEditor
              item={selectedItem}
              onSave={handleSave}
              onCancel={() => {
                setShowEditor(false)
                setSelectedItem(null)
              }}
              onDelete={handleDelete}
              onReembed={handleReembed}
            />
          ) : (
            <KnowledgeList
              items={items}
              loading={loading}
              onItemSelect={handleItemSelect}
              onDuplicate={handleDuplicate}
              onReembed={handleReembed}
            />
          )}
        </main>
      </div>
    </div>
  )
}
