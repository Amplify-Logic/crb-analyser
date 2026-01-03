import { useEffect, useState, useRef } from 'react'
import { motion, useSpring, useTransform } from 'framer-motion'

interface AIReadinessGaugeProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
  animated?: boolean
}

export default function AIReadinessGauge({
  score,
  size = 'md',
  animated = true
}: AIReadinessGaugeProps) {
  const [isVisible, setIsVisible] = useState(false)
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

  return (
    <div ref={containerRef} className="flex flex-col items-center">
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
    </div>
  )
}
