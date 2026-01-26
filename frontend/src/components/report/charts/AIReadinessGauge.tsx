import { useEffect, useState, useRef } from 'react'
import { motion, useSpring, useTransform, AnimatePresence } from 'framer-motion'

interface AIReadinessComponent {
  score: number
  max: number
  label: string
  description: string
  factors?: string[]
}

interface AIReadinessBreakdown {
  total_score: number
  components: {
    tech_stack: AIReadinessComponent
    data_readiness: AIReadinessComponent
    team_readiness: AIReadinessComponent
    process_maturity: AIReadinessComponent
  }
  improvement_suggestions: string[]
  threshold_labels?: Record<string, { label: string; color: string }>
}

interface AIReadinessGaugeProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
  animated?: boolean
  breakdown?: AIReadinessBreakdown
  showBreakdownButton?: boolean
}

// Score meaning explanations
const SCORE_MEANINGS = {
  70: {
    label: 'AI Ready',
    meaning: 'Your business has strong foundations for AI adoption. You can implement most AI solutions with minimal preparation.',
    action: 'Focus on high-impact opportunities first',
    color: '#10b981',
  },
  50: {
    label: 'Moderate',
    meaning: 'Good potential, but some gaps need addressing. Start with simpler automations while building foundations.',
    action: 'Address data or process gaps before complex AI projects',
    color: '#f59e0b',
  },
  35: {
    label: 'Developing',
    meaning: 'Significant preparation needed before AI investment. Focus on digitizing processes and improving data quality.',
    action: 'Build foundations first: digitize records, document workflows',
    color: '#f97316',
  },
  0: {
    label: 'Early Stage',
    meaning: 'AI is not the right priority now. Focus on business fundamentals first.',
    action: 'Establish consistent processes before considering automation',
    color: '#ef4444',
  },
}

function getScoreMeaning(score: number) {
  if (score >= 70) return SCORE_MEANINGS[70]
  if (score >= 50) return SCORE_MEANINGS[50]
  if (score >= 35) return SCORE_MEANINGS[35]
  return SCORE_MEANINGS[0]
}

// Component score bar
function ComponentBar({
  component,
  delay
}: {
  component: AIReadinessComponent
  delay: number
}) {
  const percentage = (component.score / component.max) * 100

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-gray-600 dark:text-gray-400">{component.label}</span>
        <span className="font-medium text-gray-900 dark:text-white">
          {component.score}/{component.max}
        </span>
      </div>
      <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-primary-500 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.6, delay, ease: 'easeOut' }}
        />
      </div>
      {component.description && (
        <p className="text-[10px] text-gray-500 dark:text-gray-500">
          {component.description}
        </p>
      )}
    </div>
  )
}

// Breakdown panel
function BreakdownPanel({
  breakdown,
  score,
  onClose
}: {
  breakdown: AIReadinessBreakdown
  score: number
  onClose: () => void
}) {
  const meaning = getScoreMeaning(score)

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 10 }}
      className="absolute z-50 top-full left-1/2 -translate-x-1/2 mt-4 w-80 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 p-4"
    >
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-2 right-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      {/* Header */}
      <div className="mb-4">
        <h4 className="font-semibold text-gray-900 dark:text-white text-sm">
          AI Readiness Score: {score}/100
        </h4>
        <p className="text-xs mt-1" style={{ color: meaning.color }}>
          {meaning.label}
        </p>
      </div>

      {/* What it means */}
      <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
        <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
          {meaning.meaning}
        </p>
      </div>

      {/* Component breakdown */}
      <div className="space-y-3 mb-4">
        <h5 className="text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wide">
          Score Breakdown
        </h5>
        <ComponentBar component={breakdown.components.tech_stack} delay={0.1} />
        <ComponentBar component={breakdown.components.data_readiness} delay={0.2} />
        <ComponentBar component={breakdown.components.team_readiness} delay={0.3} />
        <ComponentBar component={breakdown.components.process_maturity} delay={0.4} />
      </div>

      {/* Improvement suggestions */}
      {breakdown.improvement_suggestions && breakdown.improvement_suggestions.length > 0 && (
        <div className="border-t border-gray-200 dark:border-gray-700 pt-3">
          <h5 className="text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wide mb-2">
            To Improve
          </h5>
          <ul className="space-y-1">
            {breakdown.improvement_suggestions.slice(0, 3).map((suggestion, i) => (
              <li key={i} className="text-xs text-gray-600 dark:text-gray-400 flex items-start gap-2">
                <span className="text-primary-500 mt-0.5">-</span>
                {suggestion}
              </li>
            ))}
          </ul>
        </div>
      )}
    </motion.div>
  )
}

export default function AIReadinessGauge({
  score,
  size = 'md',
  animated = true,
  breakdown,
  showBreakdownButton = true,
}: AIReadinessGaugeProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [showBreakdown, setShowBreakdown] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const springScore = useSpring(0, {
    stiffness: 50,
    damping: 20,
    restDelta: 0.5
  })

  const displayScore = useTransform(springScore, (value) => Math.round(value))
  const [currentScore, setCurrentScore] = useState(0)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true)
        }
      },
      { threshold: 0.3 }
    )

    if (containerRef.current) {
      observer.observe(containerRef.current)
    }

    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    if (isVisible && animated) {
      springScore.set(score)
    } else if (!animated) {
      springScore.set(score)
    }
  }, [isVisible, score, animated, springScore])

  useEffect(() => {
    const unsubscribe = displayScore.on('change', (value) => {
      setCurrentScore(value)
    })
    return unsubscribe
  }, [displayScore])

  const getColor = (score: number) => {
    if (score >= 70) return '#10b981' // emerald-500
    if (score >= 50) return '#f59e0b' // amber-500
    if (score >= 35) return '#f97316' // orange-500
    return '#ef4444' // red-500
  }

  const getLabel = (score: number) => {
    if (score >= 70) return 'AI Ready'
    if (score >= 50) return 'Moderate'
    if (score >= 35) return 'Developing'
    return 'Early Stage'
  }

  const color = getColor(currentScore)
  const label = getLabel(currentScore)

  const dimensions = {
    sm: { width: 140, height: 85, strokeWidth: 8, fontSize: 28, radius: 50 },
    md: { width: 180, height: 100, strokeWidth: 10, fontSize: 36, radius: 65 },
    lg: { width: 240, height: 130, strokeWidth: 12, fontSize: 48, radius: 90 }
  }

  const dim = dimensions[size]
  const circumference = Math.PI * dim.radius
  const strokeDashoffset = circumference - (currentScore / 100) * circumference

  // Close breakdown when clicking outside
  useEffect(() => {
    if (!showBreakdown) return

    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowBreakdown(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showBreakdown])

  return (
    <div ref={containerRef} className="flex flex-col items-center relative">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4 }}
        className="relative"
        style={{ width: dim.width, height: dim.height }}
      >
        <svg
          width={dim.width}
          height={dim.height}
          viewBox={`0 0 ${dim.width} ${dim.height}`}
        >
          {/* Background arc */}
          <path
            d={`M ${dim.width * 0.1} ${dim.height - 5}
                A ${dim.radius} ${dim.radius} 0 0 1 ${dim.width * 0.9} ${dim.height - 5}`}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth={dim.strokeWidth}
            strokeLinecap="round"
            className="dark:stroke-gray-700"
          />

          {/* Foreground arc */}
          <motion.path
            d={`M ${dim.width * 0.1} ${dim.height - 5}
                A ${dim.radius} ${dim.radius} 0 0 1 ${dim.width * 0.9} ${dim.height - 5}`}
            fill="none"
            stroke={color}
            strokeWidth={dim.strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1, ease: [0.25, 0.46, 0.45, 0.94] }}
          />

          {/* Tick marks */}
          {[0, 25, 50, 75, 100].map((tick) => {
            const angle = (tick / 100) * Math.PI
            const x1 = dim.width / 2 - (dim.radius - dim.strokeWidth) * Math.cos(angle)
            const y1 = dim.height - 5 - (dim.radius - dim.strokeWidth) * Math.sin(angle)
            const x2 = dim.width / 2 - (dim.radius - dim.strokeWidth - 6) * Math.cos(angle)
            const y2 = dim.height - 5 - (dim.radius - dim.strokeWidth - 6) * Math.sin(angle)

            return (
              <line
                key={tick}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke="#9ca3af"
                strokeWidth={1}
                className="dark:stroke-gray-600"
              />
            )
          })}
        </svg>

        {/* Score Display */}
        <div
          className="absolute inset-0 flex flex-col items-center justify-end"
          style={{ paddingBottom: dim.height * 0.05 }}
        >
          <motion.span
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="font-semibold tabular-nums text-gray-900 dark:text-white"
            style={{ fontSize: dim.fontSize }}
          >
            {currentScore}
          </motion.span>
        </div>
      </motion.div>

      {/* Label */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="mt-2 px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-700"
      >
        <span
          className="text-sm font-medium"
          style={{ color }}
        >
          {label}
        </span>
      </motion.div>

      {/* "What's this?" button */}
      {showBreakdownButton && (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          onClick={() => setShowBreakdown(!showBreakdown)}
          className="mt-2 text-xs text-gray-500 hover:text-primary-600 dark:text-gray-400 dark:hover:text-primary-400 underline underline-offset-2 transition-colors"
        >
          {showBreakdown ? 'Hide details' : "What's this?"}
        </motion.button>
      )}

      {/* Breakdown panel */}
      <AnimatePresence>
        {showBreakdown && breakdown && (
          <BreakdownPanel
            breakdown={breakdown}
            score={score}
            onClose={() => setShowBreakdown(false)}
          />
        )}
      </AnimatePresence>

      {/* Simple tooltip if no breakdown data */}
      <AnimatePresence>
        {showBreakdown && !breakdown && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="absolute z-50 top-full left-1/2 -translate-x-1/2 mt-4 w-64 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 p-4"
          >
            <button
              onClick={() => setShowBreakdown(false)}
              className="absolute top-2 right-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            <h4 className="font-semibold text-gray-900 dark:text-white text-sm mb-2">
              AI Readiness Score
            </h4>

            <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed mb-3">
              {getScoreMeaning(score).meaning}
            </p>

            <div className="text-xs font-medium" style={{ color: getScoreMeaning(score).color }}>
              {getScoreMeaning(score).action}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
