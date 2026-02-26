import { ReactNode } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'

export interface ContentPanelProps {
  breadcrumb: string[]
  children: ReactNode
  onPrev: () => void
  onNext: () => void
  prevLabel?: string
  nextLabel?: string
}

export function ContentPanel({
  breadcrumb,
  children,
  onPrev,
  onNext,
  prevLabel,
  nextLabel,
}: ContentPanelProps) {
  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-gray-50 dark:bg-gray-900">
      {/* Breadcrumb */}
      <div className="px-4 md:px-8 py-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <nav className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
          {breadcrumb.map((item, index) => (
            <span key={index} className="flex items-center gap-2">
              {index > 0 && <ChevronRight className="w-4 h-4" />}
              <span className={index === breadcrumb.length - 1 ? 'text-gray-900 dark:text-white font-medium' : ''}>
                {item}
              </span>
            </span>
          ))}
        </nav>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6">
        {children}
      </div>

      {/* Prev/Next Navigation */}
      {(prevLabel || nextLabel) && (
        <div className="px-4 md:px-8 py-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex justify-between">
          {prevLabel ? (
            <button
              onClick={onPrev}
              className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              <span>← Prev: {prevLabel}</span>
            </button>
          ) : (
            <div />
          )}
          {nextLabel && (
            <button
              onClick={onNext}
              className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              <span>Next: {nextLabel} →</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
        </div>
      )}
    </div>
  )
}

export default ContentPanel
