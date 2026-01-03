import { motion } from 'framer-motion'

interface Verdict {
  recommendation: 'proceed' | 'proceed_cautiously' | 'wait' | 'not_recommended'
  headline: string
  subheadline: string
  reasoning: string[]
  when_to_revisit: string
  what_to_do_instead?: string[]
  recommended_approach?: string[]
  confidence: 'high' | 'medium' | 'low'
  color: 'green' | 'yellow' | 'orange' | 'gray'
}

interface VerdictCardProps {
  verdict: Verdict
}

export default function VerdictCard({ verdict }: VerdictCardProps) {
  const colorStyles = {
    green: {
      border: 'border-l-emerald-500',
      icon: 'bg-emerald-500',
      badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      accent: 'text-emerald-600',
      dot: 'bg-emerald-500'
    },
    yellow: {
      border: 'border-l-amber-500',
      icon: 'bg-amber-500',
      badge: 'bg-amber-50 text-amber-700 border-amber-200',
      accent: 'text-amber-600',
      dot: 'bg-amber-500'
    },
    orange: {
      border: 'border-l-orange-500',
      icon: 'bg-orange-500',
      badge: 'bg-orange-50 text-orange-700 border-orange-200',
      accent: 'text-orange-600',
      dot: 'bg-orange-500'
    },
    gray: {
      border: 'border-l-gray-400',
      icon: 'bg-gray-500',
      badge: 'bg-gray-100 text-gray-700 border-gray-200',
      accent: 'text-gray-600',
      dot: 'bg-gray-400'
    }
  }

  const icons = {
    proceed: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    proceed_cautiously: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
    wait: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    not_recommended: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
      </svg>
    )
  }

  const styles = colorStyles[verdict.color]
  const actionList = verdict.what_to_do_instead || verdict.recommended_approach || []

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
      className={`
        bg-white dark:bg-gray-800
        border border-gray-200 dark:border-gray-700
        border-l-4 ${styles.border}
        rounded-xl p-6 md:p-8 mb-8
        shadow-sm
      `}
    >
      <div className="flex items-start gap-5">
        {/* Icon */}
        <div className={`flex-shrink-0 p-3 rounded-lg ${styles.icon} text-white`}>
          {icons[verdict.recommendation]}
        </div>

        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex flex-wrap items-center gap-3 mb-2">
            <h2 className="text-xl md:text-2xl font-semibold text-gray-900 dark:text-white">
              {verdict.headline}
            </h2>
            <span className={`inline-flex items-center gap-1.5 ${styles.badge} text-xs font-medium px-2.5 py-1 rounded-full border`}>
              <span className={`w-1.5 h-1.5 rounded-full ${styles.dot}`} />
              {verdict.confidence} confidence
            </span>
          </div>

          <p className="text-gray-600 dark:text-gray-400 mb-6">
            {verdict.subheadline}
          </p>

          {/* Reasoning */}
          <div className="mb-5">
            <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 flex items-center gap-2">
              <span className={`w-1 h-3 rounded-full ${styles.dot}`} />
              Why we say this
            </h4>
            <ul className="space-y-1.5 pl-3">
              {verdict.reasoning.map((reason, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <span className="text-gray-400 mt-1">•</span>
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Actions */}
          {actionList.length > 0 && (
            <div className="mb-5">
              <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 flex items-center gap-2">
                <span className="w-1 h-3 rounded-full bg-blue-500" />
                {verdict.what_to_do_instead ? 'Recommended approach' : 'Recommended approach'}
              </h4>
              <ol className="space-y-1.5 pl-3">
                {actionList.map((action, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <span className="flex-shrink-0 w-5 h-5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 flex items-center justify-center text-xs font-medium">
                      {i + 1}
                    </span>
                    <span>{action}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* When to revisit */}
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center flex-shrink-0">
              <svg className="w-4 h-4 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
                When to revisit
              </p>
              <p className="text-sm text-gray-700 dark:text-gray-300">
                {verdict.when_to_revisit}
              </p>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
