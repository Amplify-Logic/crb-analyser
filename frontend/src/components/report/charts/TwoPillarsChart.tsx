import { useEffect, useState, useRef } from 'react'
import { motion, useSpring, useTransform } from 'framer-motion'

interface TwoPillarsChartProps {
  customerValue: number
  businessHealth: number
  animated?: boolean
}

export default function TwoPillarsChart({
  customerValue,
  businessHealth,
  animated = true
}: TwoPillarsChartProps) {
  const [isVisible, setIsVisible] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  // Spring animations for smooth counting
  const springCV = useSpring(0, { stiffness: 50, damping: 20, restDelta: 0.1 })
  const springBH = useSpring(0, { stiffness: 50, damping: 20, restDelta: 0.1 })

  const displayCV = useTransform(springCV, (value) => value.toFixed(1))
  const displayBH = useTransform(springBH, (value) => value.toFixed(1))

  const [currentCV, setCurrentCV] = useState(0)
  const [currentBH, setCurrentBH] = useState(0)

  // Observe visibility
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

  // Animate when visible
  useEffect(() => {
    if (isVisible && animated) {
      springCV.set(customerValue)
      springBH.set(businessHealth)
    } else if (!animated) {
      springCV.set(customerValue)
      springBH.set(businessHealth)
    }
  }, [isVisible, customerValue, businessHealth, animated, springCV, springBH])

  // Subscribe to spring value changes
  useEffect(() => {
    const unsubscribeCV = displayCV.on('change', (value) => {
      setCurrentCV(parseFloat(value))
    })
    const unsubscribeBH = displayBH.on('change', (value) => {
      setCurrentBH(parseFloat(value))
    })
    return () => {
      unsubscribeCV()
      unsubscribeBH()
    }
  }, [displayCV, displayBH])

  const getScoreColor = (score: number) => {
    if (score >= 8) return { primary: '#22c55e', secondary: '#16a34a', bg: 'from-green-500/20 to-green-500/5' }
    if (score >= 6) return { primary: '#3b82f6', secondary: '#2563eb', bg: 'from-blue-500/20 to-blue-500/5' }
    if (score >= 4) return { primary: '#eab308', secondary: '#ca8a04', bg: 'from-yellow-500/20 to-yellow-500/5' }
    return { primary: '#ef4444', secondary: '#dc2626', bg: 'from-red-500/20 to-red-500/5' }
  }

  const cvColors = getScoreColor(currentCV)
  const bhColors = getScoreColor(currentBH)

  const pillars = [
    {
      id: 'cv',
      label: 'Customer Value',
      description: 'How AI benefits your customers',
      icon: '💎',
      score: currentCV,
      colors: cvColors
    },
    {
      id: 'bh',
      label: 'Business Health',
      description: 'How AI improves operations',
      icon: '⚡',
      score: currentBH,
      colors: bhColors
    }
  ]

  return (
    <div ref={containerRef} className="w-full">
      <div className="grid grid-cols-2 gap-6">
        {pillars.map((pillar, index) => (
          <motion.div
            key={pillar.id}
            initial={{ opacity: 0, y: 25, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{
              duration: 0.6,
              delay: index * 0.15,
              ease: [0.25, 0.46, 0.45, 0.94]
            }}
            whileHover={{
              y: -3,
              transition: { duration: 0.2 }
            }}
            className={`
              relative overflow-hidden
              p-6 rounded-3xl
              bg-gradient-to-br ${pillar.colors.bg}
              border border-gray-200/50 dark:border-gray-700/50
              backdrop-blur-md
              shadow-card-premium
              hover:shadow-card-premium-hover
              transition-shadow duration-300
              group
            `}
          >
            {/* Background glow */}
            <motion.div
              className="absolute -bottom-10 -right-10 w-32 h-32 rounded-full blur-3xl"
              style={{ background: pillar.colors.primary, opacity: 0.1 }}
              animate={{
                opacity: [0.05, 0.15, 0.05],
                scale: [1, 1.1, 1]
              }}
              transition={{
                duration: 4,
                repeat: Infinity,
                ease: 'easeInOut',
                delay: index * 0.5
              }}
            />

            {/* Header */}
            <div className="flex items-center gap-3 mb-5">
              <motion.div
                className="w-11 h-11 rounded-2xl flex items-center justify-center text-xl shadow-lg"
                style={{
                  background: `linear-gradient(135deg, ${pillar.colors.primary}20, ${pillar.colors.secondary}10)`,
                  boxShadow: `0 4px 12px ${pillar.colors.primary}20`
                }}
                whileHover={{ scale: 1.05, rotate: 5 }}
                transition={{ duration: 0.2 }}
              >
                {pillar.icon}
              </motion.div>
              <div>
                <h4 className="font-bold text-gray-900 dark:text-gray-100 text-sm tracking-tight">
                  {pillar.label}
                </h4>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  {pillar.description}
                </p>
              </div>
            </div>

            {/* Score Display */}
            <div className="flex items-end justify-between mb-4">
              <motion.div
                initial={{ opacity: 0, scale: 0.8, y: 10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                transition={{ delay: 0.3 + index * 0.15, duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
              >
                <span
                  className="text-5xl font-bold tabular-nums tracking-tighter"
                  style={{
                    background: `linear-gradient(135deg, ${pillar.colors.primary}, ${pillar.colors.secondary})`,
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                    filter: `drop-shadow(0 2px 4px ${pillar.colors.primary}30)`
                  }}
                >
                  {pillar.score.toFixed(1)}
                </span>
                <span className="text-lg font-medium text-gray-400 dark:text-gray-500 ml-1">/10</span>
              </motion.div>

              {/* Mini rating indicator */}
              <motion.div
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.5 + index * 0.15, duration: 0.4 }}
                className="flex gap-0.5"
              >
                {[...Array(5)].map((_, i) => (
                  <motion.div
                    key={i}
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.6 + index * 0.15 + i * 0.05, duration: 0.2 }}
                    className={`w-2 h-2 rounded-full ${
                      i < Math.round(pillar.score / 2)
                        ? ''
                        : 'bg-gray-200 dark:bg-gray-600'
                    }`}
                    style={{
                      background: i < Math.round(pillar.score / 2)
                        ? pillar.colors.primary
                        : undefined
                    }}
                  />
                ))}
              </motion.div>
            </div>

            {/* Progress Bar */}
            <div className="relative h-4 bg-gray-200/70 dark:bg-gray-700/50 rounded-full overflow-hidden shadow-inner">
              {/* Track markers */}
              <div className="absolute inset-0 flex">
                {[...Array(10)].map((_, i) => (
                  <div
                    key={i}
                    className="flex-1 border-r border-gray-300/20 dark:border-gray-600/20 last:border-r-0"
                  />
                ))}
              </div>

              {/* Animated fill */}
              <motion.div
                className="absolute inset-y-0 left-0 rounded-full"
                style={{
                  background: `linear-gradient(90deg, ${pillar.colors.secondary}, ${pillar.colors.primary})`,
                  boxShadow: `0 0 20px ${pillar.colors.primary}40, inset 0 1px 0 rgba(255,255,255,0.3)`
                }}
                initial={{ width: 0 }}
                animate={{ width: `${(pillar.score / 10) * 100}%` }}
                transition={{
                  duration: 1.2,
                  delay: 0.4 + index * 0.15,
                  ease: [0.25, 0.46, 0.45, 0.94]
                }}
              />

              {/* Shimmer effect */}
              <motion.div
                className="absolute inset-y-0 w-24 bg-gradient-to-r from-transparent via-white/40 to-transparent"
                animate={{
                  x: ['-100%', '500%']
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  repeatDelay: 4,
                  ease: 'easeInOut',
                  delay: 1.5 + index * 0.5
                }}
              />

              {/* Score indicator dot */}
              <motion.div
                className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-white shadow-md border-2"
                style={{ borderColor: pillar.colors.primary }}
                initial={{ left: 0, opacity: 0 }}
                animate={{
                  left: `calc(${(pillar.score / 10) * 100}% - 6px)`,
                  opacity: 1
                }}
                transition={{
                  duration: 1.2,
                  delay: 0.4 + index * 0.15,
                  ease: [0.25, 0.46, 0.45, 0.94]
                }}
              />
            </div>

            {/* Score scale */}
            <div className="flex justify-between mt-2.5 text-[10px] font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wider">
              <span>Low</span>
              <span>Average</span>
              <span>Excellent</span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Combined score indicator */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.9, duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
        className="mt-6 text-center"
      >
        <motion.div
          whileHover={{ scale: 1.02, y: -1 }}
          className="inline-flex items-center gap-3 px-6 py-3 bg-gradient-to-r from-gray-50 to-gray-100/80 dark:from-gray-800/60 dark:to-gray-800/40 rounded-2xl backdrop-blur-md border border-gray-200/50 dark:border-gray-700/50 shadow-card"
        >
          <div className="flex items-center gap-2">
            <motion.div
              className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center shadow-lg shadow-primary-500/20"
              animate={{ rotate: [0, 360] }}
              transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
            >
              <span className="text-white text-sm">⚡</span>
            </motion.div>
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Combined Strength</span>
          </div>
          <div className="h-6 w-px bg-gray-200 dark:bg-gray-700" />
          <div className="flex items-center gap-2">
            <span
              className="text-xl font-bold"
              style={{
                background: 'linear-gradient(135deg, #9333ea, #7c3aed)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}
            >
              {((currentCV + currentBH) / 2).toFixed(1)}
            </span>
            <span className="text-sm text-gray-400 dark:text-gray-500">/10</span>
            <motion.div
              className="w-2 h-2 rounded-full bg-gradient-to-r from-primary-500 to-purple-500"
              animate={{
                scale: [1, 1.3, 1],
                opacity: [0.7, 1, 0.7]
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut'
              }}
            />
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}
