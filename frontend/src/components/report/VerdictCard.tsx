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
      bg: 'bg-gradient-to-br from-green-50 to-emerald-50',
      border: 'border-green-200',
      icon: 'bg-green-100 text-green-600',
      headline: 'text-green-800',
      badge: 'bg-green-100 text-green-700'
    },
    yellow: {
      bg: 'bg-gradient-to-br from-yellow-50 to-amber-50',
      border: 'border-yellow-200',
      icon: 'bg-yellow-100 text-yellow-600',
      headline: 'text-yellow-800',
      badge: 'bg-yellow-100 text-yellow-700'
    },
    orange: {
      bg: 'bg-gradient-to-br from-orange-50 to-amber-50',
      border: 'border-orange-200',
      icon: 'bg-orange-100 text-orange-600',
      headline: 'text-orange-800',
      badge: 'bg-orange-100 text-orange-700'
    },
    gray: {
      bg: 'bg-gradient-to-br from-gray-50 to-slate-50',
      border: 'border-gray-300',
      icon: 'bg-gray-200 text-gray-600',
      headline: 'text-gray-800',
      badge: 'bg-gray-200 text-gray-700'
    }
  }

  const icons = {
    proceed: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    proceed_cautiously: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
    wait: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    not_recommended: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
      transition={{ duration: 0.5 }}
      className={`${styles.bg} ${styles.border} border-2 rounded-2xl p-6 mb-8`}
    >
      <div className="flex items-start gap-4">
        <div className={`${styles.icon} p-3 rounded-xl flex-shrink-0`}>
          {icons[verdict.recommendation]}
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h2 className={`text-2xl font-bold ${styles.headline}`}>
              {verdict.headline}
            </h2>
            <span className={`${styles.badge} text-xs font-medium px-2 py-1 rounded-full`}>
              {verdict.confidence} confidence
            </span>
          </div>
          <p className="text-gray-600 mb-4">{verdict.subheadline}</p>

          {/* Reasoning */}
          <div className="mb-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Why we say this:</h4>
            <ul className="space-y-1">
              {verdict.reasoning.map((reason, i) => (
                <motion.li
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 * i }}
                  className="flex items-start gap-2 text-sm text-gray-600"
                >
                  <span className="text-gray-400 mt-1">•</span>
                  <span>{reason}</span>
                </motion.li>
              ))}
            </ul>
          </div>

          {/* Actions */}
          {actionList.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">
                {verdict.what_to_do_instead ? 'What to do instead:' : 'Recommended approach:'}
              </h4>
              <ul className="space-y-1">
                {actionList.map((action, i) => (
                  <motion.li
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 + 0.1 * i }}
                    className="flex items-start gap-2 text-sm text-gray-600"
                  >
                    <span className="text-primary-500 font-bold">{i + 1}.</span>
                    <span>{action}</span>
                  </motion.li>
                ))}
              </ul>
            </div>
          )}

          {/* When to revisit */}
          <div className="bg-white/50 rounded-xl p-3 mt-4">
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">When to revisit</p>
            <p className="text-sm text-gray-700">{verdict.when_to_revisit}</p>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
