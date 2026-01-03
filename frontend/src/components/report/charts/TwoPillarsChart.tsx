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

  const springCV = useSpring(0, { stiffness: 50, damping: 20, restDelta: 0.1 })
  const springBH = useSpring(0, { stiffness: 50, damping: 20, restDelta: 0.1 })

  const displayCV = useTransform(springCV, (value) => value.toFixed(1))
  const displayBH = useTransform(springBH, (value) => value.toFixed(1))

  const [currentCV, setCurrentCV] = useState(0)
  const [currentBH, setCurrentBH] = useState(0)

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
      springCV.set(customerValue)
      springBH.set(businessHealth)
    } else if (!animated) {
      springCV.set(customerValue)
      springBH.set(businessHealth)
    }
  }, [isVisible, customerValue, businessHealth, animated, springCV, springBH])

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

  const getColor = (score: number) => {
    if (score >= 8) return '#10b981' // emerald-500
    if (score >= 6) return '#3b82f6' // blue-500
    if (score >= 4) return '#f59e0b' // amber-500
    return '#ef4444' // red-500
  }

  const pillars = [
    {
      id: 'cv',
      label: 'Customer Value',
      description: 'How AI benefits your customers',
      score: currentCV,
      color: getColor(currentCV)
    },
    {
      id: 'bh',
      label: 'Business Health',
      description: 'How AI improves operations',
      score: currentBH,
      color: getColor(currentBH)
    }
  ]

  return (
    <div ref={containerRef} className="w-full">
      <div className="grid grid-cols-2 gap-4">
        {pillars.map((pillar, index) => (
          <motion.div
            key={pillar.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: index * 0.1 }}
            className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4"
          >
            {/* Header */}
            <div className="mb-3">
              <h4 className="font-medium text-gray-900 dark:text-white text-sm">
                {pillar.label}
              </h4>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {pillar.description}
              </p>
            </div>

            {/* Score */}
            <div className="flex items-end gap-1 mb-3">
              <span
                className="text-3xl font-semibold tabular-nums"
                style={{ color: pillar.color }}
              >
                {pillar.score.toFixed(1)}
              </span>
              <span className="text-sm text-gray-400 dark:text-gray-500 mb-1">/10</span>
            </div>

            {/* Progress Bar */}
            <div className="h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
              <motion.div
                className="h-full rounded-full"
                style={{ backgroundColor: pillar.color }}
                initial={{ width: 0 }}
                animate={{ width: `${(pillar.score / 10) * 100}%` }}
                transition={{ duration: 0.8, delay: 0.2 + index * 0.1 }}
              />
            </div>

            {/* Scale labels */}
            <div className="flex justify-between mt-1.5 text-[10px] text-gray-400 dark:text-gray-500">
              <span>Low</span>
              <span>Average</span>
              <span>Excellent</span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Combined score */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="mt-4 flex items-center justify-center gap-2 text-sm"
      >
        <span className="text-gray-500 dark:text-gray-400">Combined Strength:</span>
        <span className="font-semibold text-gray-900 dark:text-white">
          {((currentCV + currentBH) / 2).toFixed(1)}
        </span>
        <span className="text-gray-400 dark:text-gray-500">/10</span>
      </motion.div>
    </div>
  )
}
