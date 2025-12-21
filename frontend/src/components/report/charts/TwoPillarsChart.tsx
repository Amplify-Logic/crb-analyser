import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, LabelList } from 'recharts'

interface TwoPillarsChartProps {
  customerValue: number
  businessHealth: number
  animated?: boolean
}

export default function TwoPillarsChart({ customerValue, businessHealth, animated = true }: TwoPillarsChartProps) {
  const [displayCV, setDisplayCV] = useState(animated ? 0 : customerValue)
  const [displayBH, setDisplayBH] = useState(animated ? 0 : businessHealth)

  useEffect(() => {
    if (!animated) return

    const duration = 1200
    const steps = 40
    const cvIncrement = customerValue / steps
    const bhIncrement = businessHealth / steps
    let current = 0

    const timer = setInterval(() => {
      current++
      if (current >= steps) {
        setDisplayCV(customerValue)
        setDisplayBH(businessHealth)
        clearInterval(timer)
      } else {
        setDisplayCV(Math.min(Math.round(cvIncrement * current), customerValue))
        setDisplayBH(Math.min(Math.round(bhIncrement * current), businessHealth))
      }
    }, duration / steps)

    return () => clearInterval(timer)
  }, [customerValue, businessHealth, animated])

  const data = [
    { name: 'Customer Value', value: displayCV, fullName: 'Customer Value Score' },
    { name: 'Business Health', value: displayBH, fullName: 'Business Health Score' }
  ]

  const getColor = (score: number) => {
    if (score >= 8) return '#22c55e' // green
    if (score >= 6) return '#3b82f6' // blue
    if (score >= 4) return '#eab308' // yellow
    return '#ef4444' // red
  }

  return (
    <div className="w-full">
      <div className="h-32">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <XAxis type="number" domain={[0, 10]} hide />
            <YAxis
              type="category"
              dataKey="name"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fill: '#6b7280' }}
              width={100}
            />
            <Bar
              dataKey="value"
              radius={[0, 4, 4, 0]}
              barSize={24}
            >
              {data.map((entry, index) => (
                <Cell key={index} fill={getColor(entry.value)} />
              ))}
              <LabelList
                dataKey="value"
                position="right"
                formatter={(value: number) => `${value}/10`}
                style={{ fontSize: 14, fontWeight: 600, fill: '#374151' }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="flex justify-around text-xs text-gray-500 mt-1">
        <span>How AI benefits your customers</span>
        <span>How AI improves operations</span>
      </div>
    </div>
  )
}
