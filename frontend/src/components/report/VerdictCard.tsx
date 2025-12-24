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
      bg: 'from-green-50 via-emerald-50/80 to-teal-50/50',
      border: 'border-green-200/70',
      icon: 'from-green-400 to-emerald-500',
      iconShadow: 'shadow-green-500/25',
      headline: 'text-green-800',
      badge: 'bg-green-100/80 text-green-700 border-green-200/50',
      glow: 'from-green-400/20 to-emerald-400/10',
      accent: '#22c55e'
    },
    yellow: {
      bg: 'from-yellow-50 via-amber-50/80 to-orange-50/50',
      border: 'border-yellow-200/70',
      icon: 'from-yellow-400 to-amber-500',
      iconShadow: 'shadow-yellow-500/25',
      headline: 'text-yellow-800',
      badge: 'bg-yellow-100/80 text-yellow-700 border-yellow-200/50',
      glow: 'from-yellow-400/20 to-amber-400/10',
      accent: '#eab308'
    },
    orange: {
      bg: 'from-orange-50 via-amber-50/80 to-yellow-50/50',
      border: 'border-orange-200/70',
      icon: 'from-orange-400 to-amber-500',
      iconShadow: 'shadow-orange-500/25',
      headline: 'text-orange-800',
      badge: 'bg-orange-100/80 text-orange-700 border-orange-200/50',
      glow: 'from-orange-400/20 to-amber-400/10',
      accent: '#f97316'
    },
    gray: {
      bg: 'from-gray-50 via-slate-50/80 to-zinc-50/50',
      border: 'border-gray-300/70',
      icon: 'from-gray-400 to-slate-500',
      iconShadow: 'shadow-gray-500/25',
      headline: 'text-gray-800',
      badge: 'bg-gray-200/80 text-gray-700 border-gray-300/50',
      glow: 'from-gray-400/20 to-slate-400/10',
      accent: '#6b7280'
    }
  }

  const icons = {
    proceed: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    proceed_cautiously: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
    wait: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    not_recommended: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
      </svg>
    )
  }

  const confidenceEmoji = {
    high: '🎯',
    medium: '📊',
    low: '🔍'
  }

  const styles = colorStyles[verdict.color]
  const actionList = verdict.what_to_do_instead || verdict.recommended_approach || []

  return (
    <motion.div
      initial={{ opacity: 0, y: 40, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        duration: 0.7,
        ease: [0.25, 0.46, 0.45, 0.94]
      }}
      whileHover={{
        y: -2,
        transition: { duration: 0.2 }
      }}
      className={`
        relative overflow-hidden
        bg-gradient-to-br ${styles.bg}
        ${styles.border} border-2
        rounded-3xl p-8 md:p-10 mb-10
        shadow-premium
        hover:shadow-premium-lg
        transition-shadow duration-500
        dark:bg-opacity-90
      `}
    >
      {/* Background glow effect */}
      <motion.div
        className={`absolute -top-20 -right-20 w-64 h-64 rounded-full bg-gradient-to-br ${styles.glow} blur-3xl`}
        animate={{
          scale: [1, 1.1, 1],
          opacity: [0.5, 0.7, 0.5]
        }}
        transition={{
          duration: 5,
          repeat: Infinity,
          ease: 'easeInOut'
        }}
      />
      <motion.div
        className={`absolute -bottom-20 -left-20 w-48 h-48 rounded-full bg-gradient-to-tr ${styles.glow} blur-3xl`}
        animate={{
          scale: [1, 1.15, 1],
          opacity: [0.3, 0.5, 0.3]
        }}
        transition={{
          duration: 6,
          repeat: Infinity,
          ease: 'easeInOut',
          delay: 1
        }}
      />

      <div className="relative z-10 flex items-start gap-6">
        {/* Icon */}
        <motion.div
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{
            type: 'spring',
            stiffness: 200,
            damping: 15,
            delay: 0.2
          }}
          whileHover={{ scale: 1.05, rotate: 5 }}
          className={`
            flex-shrink-0 p-5 rounded-3xl
            bg-gradient-to-br ${styles.icon}
            text-white
            shadow-xl ${styles.iconShadow}
            relative
          `}
        >
          {/* Icon glow ring */}
          <motion.div
            className="absolute inset-0 rounded-3xl"
            style={{ boxShadow: `0 0 30px ${styles.accent}40` }}
            animate={{
              opacity: [0.5, 0.8, 0.5]
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut'
            }}
          />
          <div className="relative z-10">
            {icons[verdict.recommendation]}
          </div>
        </motion.div>

        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex flex-wrap items-center gap-3 mb-3">
            <motion.h2
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3, duration: 0.5 }}
              className={`text-2xl md:text-3xl lg:text-4xl font-bold ${styles.headline} tracking-tight leading-tight`}
            >
              {verdict.headline}
            </motion.h2>
            <motion.span
              initial={{ opacity: 0, scale: 0.8, y: 5 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
              whileHover={{ scale: 1.05 }}
              className={`
                inline-flex items-center gap-2
                ${styles.badge}
                text-xs font-bold
                px-4 py-2
                rounded-full
                border
                backdrop-blur-md
                shadow-sm
                uppercase tracking-wider
              `}
            >
              <motion.span
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 2, repeat: Infinity, repeatDelay: 2 }}
              >
                {confidenceEmoji[verdict.confidence]}
              </motion.span>
              <span>{verdict.confidence} confidence</span>
            </motion.span>
          </div>

          <motion.p
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.45, duration: 0.4 }}
            className="text-gray-600 dark:text-gray-400 text-lg md:text-xl mb-8 leading-relaxed"
          >
            {verdict.subheadline}
          </motion.p>

          {/* Reasoning */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.4 }}
            className="mb-6"
          >
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
              <span className="w-1 h-4 rounded-full" style={{ background: styles.accent }} />
              Why we say this
            </h4>
            <ul className="space-y-2">
              {verdict.reasoning.map((reason, i) => (
                <motion.li
                  key={i}
                  initial={{ opacity: 0, x: -15 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.6 + i * 0.08, duration: 0.4 }}
                  className="flex items-start gap-3 text-sm text-gray-600 dark:text-gray-400"
                >
                  <span
                    className="mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0"
                    style={{ background: styles.accent }}
                  />
                  <span className="leading-relaxed">{reason}</span>
                </motion.li>
              ))}
            </ul>
          </motion.div>

          {/* Actions */}
          {actionList.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7, duration: 0.4 }}
              className="mb-6"
            >
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                <span className="w-1 h-4 rounded-full bg-primary-500" />
                {verdict.what_to_do_instead ? 'What to do instead' : 'Recommended approach'}
              </h4>
              <div className="space-y-2">
                {actionList.map((action, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -15 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.8 + i * 0.08, duration: 0.4 }}
                    className="flex items-start gap-3 text-sm text-gray-600 dark:text-gray-400"
                  >
                    <span className="flex-shrink-0 w-6 h-6 rounded-lg bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 flex items-center justify-center text-xs font-bold">
                      {i + 1}
                    </span>
                    <span className="leading-relaxed pt-0.5">{action}</span>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* When to revisit */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.95, duration: 0.4 }}
            whileHover={{ scale: 1.01 }}
            className="bg-white/70 dark:bg-gray-800/50 backdrop-blur-lg rounded-2xl p-5 border border-gray-200/50 dark:border-gray-700/50 shadow-card"
          >
            <div className="flex items-start gap-4">
              <motion.div
                className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-100 to-indigo-100 dark:from-blue-900/30 dark:to-indigo-900/30 flex items-center justify-center shadow-sm"
                whileHover={{ rotate: 10 }}
              >
                <span className="text-lg">🗓️</span>
              </motion.div>
              <div className="flex-1">
                <p className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5">
                  When to revisit
                </p>
                <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                  {verdict.when_to_revisit}
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </motion.div>
  )
}
