import { useEffect, useState } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'

interface AIReadinessGaugeProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
  animated?: boolean
}

export default function AIReadinessGauge({ score, size = 'md', animated = true }: AIReadinessGaugeProps) {
  const [displayScore, setDisplayScore] = useState(animated ? 0 : score)

  useEffect(() => {
    if (!animated) return

    const duration = 1500
    const steps = 60
    const increment = score / steps
    let current = 0

    const timer = setInterval(() => {
      current += increment
      if (current >= score) {
        setDisplayScore(score)
        clearInterval(timer)
      } else {
        setDisplayScore(Math.round(current))
      }
    }, duration / steps)

    return () => clearInterval(timer)
  }, [score, animated])

  // Calculate gauge data (semi-circle)
  const gaugeData = [
    { value: displayScore, name: 'score' },
    { value: 100 - displayScore, name: 'remaining' }
  ]

  // Color based on score
  const getColor = (score: number) => {
    if (score >= 70) return '#22c55e' // green-500
    if (score >= 50) return '#eab308' // yellow-500
    if (score >= 35) return '#f97316' // orange-500
    return '#ef4444' // red-500
  }

  const getLabel = (score: number) => {
    if (score >= 70) return 'AI Ready'
    if (score >= 50) return 'Moderate'
    if (score >= 35) return 'Developing'
    return 'Early Stage'
  }

  const scoreColor = getColor(displayScore)

  const dimensions = {
    sm: { width: 120, height: 70, fontSize: 24, labelSize: 10 },
    md: { width: 180, height: 100, fontSize: 36, labelSize: 12 },
    lg: { width: 240, height: 130, fontSize: 48, labelSize: 14 }
  }

  const dim = dimensions[size]

  return (
    <div className="flex flex-col items-center">
      <div style={{ width: dim.width, height: dim.height }} className="relative">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={gaugeData}
              cx="50%"
              cy="100%"
              startAngle={180}
              endAngle={0}
              innerRadius="60%"
              outerRadius="100%"
              paddingAngle={0}
              dataKey="value"
              stroke="none"
            >
              <Cell fill={scoreColor} />
              <Cell fill="#e5e7eb" />
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div
          className="absolute inset-0 flex flex-col items-center justify-end pb-1"
          style={{ bottom: '10%' }}
        >
          <span
            className="font-bold"
            style={{ fontSize: dim.fontSize, color: scoreColor }}
          >
            {displayScore}
          </span>
        </div>
      </div>
      <span
        className="font-medium text-gray-600 -mt-2"
        style={{ fontSize: dim.labelSize }}
      >
        {getLabel(displayScore)}
      </span>
    </div>
  )
}
