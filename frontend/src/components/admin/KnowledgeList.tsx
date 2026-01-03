/**
 * Knowledge List Component
 *
 * Displays knowledge items in a list with embedding status indicators.
 */

import { useState } from 'react'
import { KnowledgeItem } from '../../pages/admin/KnowledgeBase'

interface KnowledgeListProps {
  items: KnowledgeItem[]
  loading: boolean
  onItemSelect: (item: KnowledgeItem) => void
  onReembed: (item: KnowledgeItem) => void
  onDuplicate?: (item: KnowledgeItem) => void
}

function formatDate(dateString?: string): string {
  if (!dateString) return 'Never'
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffHours / 24)

  if (diffHours < 1) return 'Just now'
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

function EmbeddingStatus({ item }: { item: KnowledgeItem }) {
  if (item.needs_update) {
    return (
      <span className="flex items-center gap-1 text-amber-600 text-xs">
        <span className="w-2 h-2 rounded-full bg-amber-500" />
        Outdated
      </span>
    )
  }
  if (item.is_embedded) {
    return (
      <span className="flex items-center gap-1 text-green-600 text-xs">
        <span className="w-2 h-2 rounded-full bg-green-500" />
        {formatDate(item.embedded_at)}
      </span>
    )
  }
  return (
    <span className="flex items-center gap-1 text-gray-400 text-xs">
      <span className="w-2 h-2 rounded-full bg-gray-300" />
      Not embedded
    </span>
  )
}

export default function KnowledgeList({
  items,
  loading,
  onItemSelect,
  onReembed,
  onDuplicate,
}: KnowledgeListProps) {
  const [jsonViewItem, setJsonViewItem] = useState<KnowledgeItem | null>(null)
  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="bg-white rounded-xl p-4 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-2" />
            <div className="h-3 bg-gray-100 rounded w-2/3" />
          </div>
        ))}
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="bg-white rounded-xl p-12 text-center">
        <div className="text-4xl mb-4">📭</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No items found</h3>
        <p className="text-gray-500">
          Try adjusting your filters or add a new item.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {items.map((item) => (
        <div
          key={item.id || `${item.content_type}-${item.content_id}`}
          className="group bg-white rounded-xl p-4 hover:shadow-md transition-shadow cursor-pointer border border-gray-100"
          onClick={() => onItemSelect(item)}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-medium text-gray-900 truncate">
                  {item.title || item.content_id}
                </h3>
                {item.industry && (
                  <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full">
                    {item.industry}
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-500 line-clamp-2">
                {item.content?.substring(0, 150)}
                {item.content && item.content.length > 150 ? '...' : ''}
              </p>
              {item.metadata && Object.keys(item.metadata).length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {Object.entries(item.metadata)
                    .slice(0, 3)
                    .map(([key, value]) => (
                      <span
                        key={key}
                        className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded"
                      >
                        {key}: {typeof value === 'string' ? value : '...'}
                      </span>
                    ))}
                  {Object.keys(item.metadata).length > 3 && (
                    <span className="text-xs text-gray-400">
                      +{Object.keys(item.metadata).length - 3} more
                    </span>
                  )}
                </div>
              )}
            </div>

            <div className="flex flex-col items-end gap-2 ml-4">
              <EmbeddingStatus item={item} />
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                {!item.is_embedded || item.needs_update ? (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onReembed(item)
                    }}
                    className="text-xs px-2 py-1 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                    title="Embed"
                  >
                    ⚡
                  </button>
                ) : null}
                {onDuplicate && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onDuplicate(item)
                    }}
                    className="text-xs px-2 py-1 text-gray-600 hover:bg-gray-100 rounded transition-colors"
                    title="Duplicate"
                  >
                    📋
                  </button>
                )}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setJsonViewItem(item)
                  }}
                  className="text-xs px-2 py-1 text-gray-600 hover:bg-gray-100 rounded transition-colors font-mono"
                  title="View JSON"
                >
                  {"{}"}
                </button>
              </div>
            </div>
          </div>
        </div>
      ))}

      {/* JSON View Modal */}
      {jsonViewItem && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={() => setJsonViewItem(null)}
        >
          <div
            className="bg-white rounded-xl w-full max-w-3xl max-h-[80vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <h3 className="font-semibold text-gray-900">
                {jsonViewItem.title || jsonViewItem.content_id}
              </h3>
              <button
                onClick={() => setJsonViewItem(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <div className="p-6 overflow-auto max-h-[calc(80vh-80px)]">
              <pre className="text-sm font-mono text-gray-700 bg-gray-50 p-4 rounded-lg overflow-x-auto">
                {JSON.stringify(jsonViewItem, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
