import { useEffect, useState, useRef } from 'react'
import { motion, useSpring, useTransform } from 'framer-motion'

interface AIReadinessGaugeProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
  animated?: boolean
  showGlow?: boolean
}

export default function AIReadinessGauge({
  score,
  size = 'md',
  animated = true,
  showGlow = true
}: AIReadinessGaugeProps) {
  const [isVisible, setIsVisible] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  // Spring animation for smooth score counting
  const springScore = useSpring(0, {
    stiffness: 50,
    damping: 20,
    restDelta: 0.5
  })

  const displayScore = useTransform(springScore, (value) => Math.round(value))
  const [currentScore, setCurrentScore] = useState(0)

  // Observe visibility for animation trigger
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

  // Animate score when visible
  useEffect(() => {
    if (isVisible && animated) {
      springScore.set(score)
    } else if (!animated) {
      springScore.set(score)
    }
  }, [isVisible, score, animated, springScore])

  // Subscribe to spring value changes
  useEffect(() => {
    const unsubscribe = displayScore.on('change', (value) => {
      setCurrentScore(value)
    })
    return unsubscribe
  }, [displayScore])

  // Color based on score with gradient support
  const getColors = (score: number) => {
    if (score >= 70) return {
      primary: '#22c55e',
      secondary: '#16a34a',
      glow: 'rgba(34, 197, 94, 0.3)',
      bg: 'from-green-500/10 to-emerald-500/5'
    }
    if (score >= 50) return {
      primary: '#eab308',
      secondary: '#ca8a04',
      glow: 'rgba(234, 179, 8, 0.3)',
      bg: 'from-yellow-500/10 to-amber-500/5'
    }
    if (score >= 35) return {
      primary: '#f97316',
      secondary: '#ea580c',
      glow: 'rgba(249, 115, 22, 0.3)',
      bg: 'from-orange-500/10 to-amber-500/5'
    }
    return {
      primary: '#ef4444',
      secondary: '#dc2626',
      glow: 'rgba(239, 68, 68, 0.3)',
      bg: 'from-red-500/10 to-rose-500/5'
    }
  }

  const getLabel = (score: number) => {
    if (score >= 70) return { text: 'AI Ready', emoji: '🚀' }
    if (score >= 50) return { text: 'Moderate', emoji: '📈' }
    if (score >= 35) return { text: 'Developing', emoji: '🌱' }
    return { text: 'Early Stage', emoji: '🔍' }
  }

  const colors = getColors(currentScore)
  const label = getLabel(currentScore)

  const dimensions = {
    sm: {
      width: 140,
      height: 85,
      strokeWidth: 10,
      fontSize: 28,
      labelSize: 11,
      radius: 50
    },
    md: {
      width: 200,
      height: 115,
      strokeWidth: 14,
      fontSize: 42,
      labelSize: 13,
      radius: 70
    },
    lg: {
      width: 280,
      height: 155,
      strokeWidth: 18,
      fontSize: 56,
      labelSize: 15,
      radius: 100
    }
  }

  const dim = dimensions[size]
  const circumference = Math.PI * dim.radius
  const strokeDashoffset = circumference - (currentScore / 100) * circumference

  return (
    <div
      ref={containerRef}
      className="flex flex-col items-center"
    >
      {/* Gauge Container */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
        className="relative"
        style={{ width: dim.width, height: dim.height }}
      >
        {/* Outer glow ring effect */}
        {showGlow && (
          <motion.div
            className="absolute -inset-4 rounded-full"
            style={{
              background: `radial-gradient(ellipse at center, ${colors.glow}, transparent 60%)`,
              filter: 'blur(20px)'
            }}
            animate={{
              opacity: [0.3, 0.6, 0.3],
              scale: [0.95, 1.05, 0.95],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: 'easeInOut'
            }}
          />
        )}

        {/* Inner ambient glow */}
        {showGlow && (
          <motion.div
            className="absolute inset-0 rounded-full blur-xl"
            style={{
              background: `radial-gradient(ellipse at center bottom, ${colors.glow}, transparent 70%)`,
              transform: 'translateY(10%)'
            }}
            animate={{
              opacity: [0.5, 0.8, 0.5],
            }}
            transition={{
              duration: 2.5,
              repeat: Infinity,
              ease: 'easeInOut',
              delay: 0.5
            }}
          />
        )}

        {/* SVG Gauge */}
        <svg
          width={dim.width}
          height={dim.height}
          viewBox={`0 0 ${dim.width} ${dim.height}`}
          className="relative z-10"
        >
          <defs>
            {/* Gradient for the arc */}
            <linearGradient id={`gauge-gradient-${size}`} x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor={colors.secondary} />
              <stop offset="100%" stopColor={colors.primary} />
            </linearGradient>

            {/* Shadow filter */}
            <filter id={`gauge-shadow-${size}`} x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor={colors.primary} floodOpacity="0.3"/>
            </filter>
          </defs>

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

          {/* Foreground arc with animation */}
          <motion.path
            d={`M ${dim.width * 0.1} ${dim.height - 5}
                A ${dim.radius} ${dim.radius} 0 0 1 ${dim.width * 0.9} ${dim.height - 5}`}
            fill="none"
            stroke={`url(#gauge-gradient-${size})`}
            strokeWidth={dim.strokeWidth}
            strokeLinecap="round"
            filter={`url(#gauge-shadow-${size})`}
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset }}
            transition={{
              duration: 1.5,
              ease: [0.25, 0.46, 0.45, 0.94],
              delay: 0.2
            }}
          />

          {/* Tick marks */}
          {[0, 25, 50, 75, 100].map((tick) => {
            const angle = (tick / 100) * Math.PI
            const x1 = dim.width / 2 - (dim.radius - dim.strokeWidth) * Math.cos(angle)
            const y1 = dim.height - 5 - (dim.radius - dim.strokeWidth) * Math.sin(angle)
            const x2 = dim.width / 2 - (dim.radius - dim.strokeWidth - 8) * Math.cos(angle)
            const y2 = dim.height - 5 - (dim.radius - dim.strokeWidth - 8) * Math.sin(angle)

            return (
              <line
                key={tick}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke="#9ca3af"
                strokeWidth={1.5}
                className="dark:stroke-gray-600"
              />
            )
          })}
        </svg>

        {/* Score Display */}
        <div
          className="absolute inset-0 flex flex-col items-center justify-end"
          style={{ paddingBottom: dim.height * 0.08 }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="relative"
          >
            {/* Score number with gradient */}
            <span
              className="font-bold tabular-nums tracking-tight relative"
              style={{
                fontSize: dim.fontSize,
                background: `linear-gradient(135deg, ${colors.primary} 0%, ${colors.secondary} 100%)`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                textShadow: 'none',
                filter: `drop-shadow(0 2px 8px ${colors.glow})`
              }}
            >
              {currentScore}
            </span>
            {/* Subtle shine effect on the number */}
            <motion.div
              className="absolute inset-0 pointer-events-none"
              style={{
                background: 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.15) 50%, transparent 100%)',
                backgroundSize: '200% 100%'
              }}
              animate={{
                backgroundPosition: ['200% 0', '-200% 0']
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                repeatDelay: 5,
                ease: 'easeInOut'
              }}
            />
          </motion.div>
        </div>
      </motion.div>

      {/* Label with premium badge style */}
      <motion.div
        initial={{ opacity: 0, y: 8, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ delay: 0.9, duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
        whileHover={{ scale: 1.03, y: -1 }}
        className={`
          mt-3 px-5 py-2 rounded-full
          bg-gradient-to-r ${colors.bg}
          border border-gray-200/50 dark:border-gray-700/50
          backdrop-blur-md
          shadow-card
          cursor-default
          transition-shadow duration-300
          hover:shadow-card-hover
        `}
      >
        <span
          className="font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2"
          style={{ fontSize: dim.labelSize }}
        >
          <motion.span
            animate={{ scale: [1, 1.15, 1] }}
            transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
          >
            {label.emoji}
          </motion.span>
          <span className="tracking-wide">{label.text}</span>
        </span>
      </motion.div>
    </div>
  )
}
