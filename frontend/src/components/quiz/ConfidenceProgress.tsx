/**
 * ConfidenceProgress Component
 *
 * Displays visual progress bars for each confidence category.
 * Shows current score, threshold, and whether the category is complete.
 */

import { motion } from 'framer-motion'

// Category display metadata
const CATEGORY_CONFIG: Record<string, { label: string; icon: string; color: string }> = {
  company_basics: {
    label: 'Company',
    icon: '🏢',
    color: 'bg-blue-500',
  },
  tech_stack: {
    label: 'Tools',
    icon: '🔧',
    color: 'bg-purple-500',
  },
  pain_points: {
    label: 'Challenges',
    icon: '🎯',
    color: 'bg-red-500',
  },
  operations: {
    label: 'Operations',
    icon: '⚙️',
    color: 'bg-orange-500',
  },
  goals_priorities: {
    label: 'Goals',
    icon: '🚀',
    color: 'bg-green-500',
  },
  quantifiable_metrics: {
    label: 'Metrics',
    icon: '📊',
    color: 'bg-cyan-500',
  },
  industry_context: {
    label: 'Industry',
    icon: '🏭',
    color: 'bg-yellow-500',
  },
  buying_signals: {
    label: 'Readiness',
    icon: '💰',
    color: 'bg-emerald-500',
  },
}

interface ConfidenceProgressProps {
  scores: Record<string, number>
  thresholds: Record<string, number>
  gaps: string[]
  compact?: boolean
  showLabels?: boolean
  animated?: boolean
}

export default function ConfidenceProgress({
  scores,
  thresholds,
  gaps,
  compact = false,
  showLabels = true,
  animated = true,
}: ConfidenceProgressProps) {
  const categories = Object.keys(CATEGORY_CONFIG)

  // Calculate overall progress
  const totalProgress = categories.reduce((sum, cat) => {
    const score = scores[cat] || 0
    const threshold = thresholds[cat] || 100
    return sum + Math.min(score / threshold, 1)
  }, 0)
  const overallPercent = Math.round((totalProgress / categories.length) * 100)

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        {categories.map((category) => {
          const config = CATEGORY_CONFIG[category]
          const score = scores[category] || 0
          const threshold = thresholds[category] || 100
          const isComplete = score >= threshold

          return (
            <div
              key={category}
              className="relative group"
              title={`${config.label}: ${score}% / ${threshold}%`}
            >
              <motion.div
                initial={animated ? { scale: 0 } : undefined}
                animate={{ scale: 1 }}
                className={`
                  w-8 h-8 rounded-full flex items-center justify-center text-sm
                  ${isComplete
                    ? 'bg-green-100 text-green-600'
                    : gaps.includes(category)
                    ? 'bg-amber-100 text-amber-600'
                    : 'bg-gray-100 text-gray-400'
                  }
                `}
              >
                {isComplete ? '✓' : config.icon}
              </motion.div>

              {/* Tooltip */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                {config.label}: {score}% / {threshold}%
              </div>
            </div>
          )
        })}

        {/* Overall progress indicator */}
        <div className="ml-2 text-sm font-medium text-gray-600">
          {overallPercent}%
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Overall progress header */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium text-gray-700">
          Discovery Progress
        </span>
        <span className={`
          text-sm font-semibold
          ${overallPercent >= 100 ? 'text-green-600' : 'text-primary-600'}
        `}>
          {overallPercent}%
        </span>
      </div>

      {/* Category progress bars */}
      <div className="space-y-2">
        {categories.map((category, index) => {
          const config = CATEGORY_CONFIG[category]
          const score = scores[category] || 0
          const threshold = thresholds[category] || 100
          const isComplete = score >= threshold
          const isCurrentGap = gaps[0] === category

          return (
            <motion.div
              key={category}
              initial={animated ? { opacity: 0, x: -20 } : undefined}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="space-y-1"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm">{config.icon}</span>
                  {showLabels && (
                    <span className={`
                      text-sm font-medium
                      ${isComplete ? 'text-green-600' : isCurrentGap ? 'text-primary-600' : 'text-gray-600'}
                    `}>
                      {config.label}
                    </span>
                  )}
                </div>
                <span className="text-xs text-gray-500">
                  {score}%{!isComplete && ` / ${threshold}%`}
                </span>
              </div>

              {/* Progress bar */}
              <div className="relative h-2 bg-gray-100 rounded-full overflow-hidden">
                {/* Threshold marker */}
                <div
                  className="absolute top-0 bottom-0 w-0.5 bg-gray-300 z-10"
                  style={{ left: `${threshold}%` }}
                />

                {/* Progress fill */}
                <motion.div
                  initial={animated ? { width: 0 } : undefined}
                  animate={{ width: `${Math.min(score, 100)}%` }}
                  transition={{ duration: 0.5, delay: index * 0.05 }}
                  className={`
                    h-full rounded-full transition-all
                    ${isComplete
                      ? 'bg-green-500'
                      : isCurrentGap
                      ? config.color
                      : 'bg-gray-300'
                    }
                  `}
                />
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Summary message */}
      {gaps.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg"
        >
          <div className="flex items-center gap-2 text-green-700">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span className="font-medium">All categories complete!</span>
          </div>
          <p className="text-sm text-green-600 mt-1">
            We have enough information for your personalized report.
          </p>
        </motion.div>
      ) : (
        <div className="mt-4 text-sm text-gray-500">
          {gaps.length} {gaps.length === 1 ? 'category' : 'categories'} remaining
        </div>
      )}
    </div>
  )
}

// Export a mini version for inline use
export function ConfidenceProgressMini({
  scores,
  thresholds,
}: Pick<ConfidenceProgressProps, 'scores' | 'thresholds'>) {
  const categories = Object.keys(CATEGORY_CONFIG)
  const completedCount = categories.filter(
    cat => (scores[cat] || 0) >= (thresholds[cat] || 100)
  ).length

  return (
    <div className="flex items-center gap-1.5">
      {categories.map((category) => {
        const score = scores[category] || 0
        const threshold = thresholds[category] || 100
        const isComplete = score >= threshold
        const percent = Math.min((score / threshold) * 100, 100)

        return (
          <div
            key={category}
            className="relative w-2 h-6 bg-gray-200 rounded-full overflow-hidden"
            title={`${CATEGORY_CONFIG[category].label}: ${score}%`}
          >
            <motion.div
              initial={{ height: 0 }}
              animate={{ height: `${percent}%` }}
              className={`
                absolute bottom-0 w-full rounded-full
                ${isComplete ? 'bg-green-500' : 'bg-primary-400'}
              `}
            />
          </div>
        )
      })}
      <span className="ml-1 text-xs text-gray-500">
        {completedCount}/{categories.length}
      </span>
    </div>
  )
}
