/**
 * Knowledge Base Sidebar
 *
 * Navigation sidebar for content types with counts and stats access.
 */

interface ContentTypeInfo {
  label: string
  count: number
  categories?: string[]
  industries?: string[]
}

interface KnowledgeSidebarProps {
  contentTypes: Record<string, ContentTypeInfo>
  selectedType: string
  onTypeSelect: (type: string) => void
  onStatsClick: () => void
  showingStats: boolean
}

const CONTENT_TYPE_ORDER = [
  'vendor',
  'opportunity',
  'benchmark',
  'case_study',
  'pattern',
  'insight',
]

const CONTENT_TYPE_ICONS: Record<string, string> = {
  vendor: '🏢',
  opportunity: '💡',
  benchmark: '📊',
  case_study: '📖',
  pattern: '🔄',
  insight: '🎯',
}

export default function KnowledgeSidebar({
  contentTypes,
  selectedType,
  onTypeSelect,
  onStatsClick,
  showingStats,
}: KnowledgeSidebarProps) {
  const orderedTypes = CONTENT_TYPE_ORDER.filter((type) => type in contentTypes)

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Knowledge Base</h2>
        <p className="text-sm text-gray-500 mt-1">
          {Object.values(contentTypes).reduce((sum, t) => sum + t.count, 0)} total items
        </p>
      </div>

      {/* Content Types */}
      <nav className="flex-1 overflow-y-auto p-2">
        <div className="space-y-1">
          {orderedTypes.map((type) => {
            const info = contentTypes[type]
            const isSelected = selectedType === type && !showingStats

            return (
              <button
                key={type}
                onClick={() => onTypeSelect(type)}
                className={`w-full flex items-center justify-between px-3 py-2 text-sm rounded-lg transition-colors ${
                  isSelected
                    ? 'bg-blue-50 text-blue-700 font-medium'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <span className="flex items-center gap-2">
                  <span>{CONTENT_TYPE_ICONS[type] || '📄'}</span>
                  <span>{info?.label || type}</span>
                </span>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    isSelected ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {info?.count || 0}
                </span>
              </button>
            )
          })}
        </div>

        {/* Divider */}
        <div className="my-4 border-t border-gray-200" />

        {/* Stats & Settings */}
        <div className="space-y-1">
          <button
            onClick={onStatsClick}
            className={`w-full flex items-center gap-2 px-3 py-2 text-sm rounded-lg transition-colors ${
              showingStats
                ? 'bg-purple-50 text-purple-700 font-medium'
                : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            <span>📈</span>
            <span>Embedding Stats</span>
          </button>
        </div>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          <p>Admin Portal</p>
          <p className="mt-1">Knowledge management system</p>
        </div>
      </div>
    </aside>
  )
}
