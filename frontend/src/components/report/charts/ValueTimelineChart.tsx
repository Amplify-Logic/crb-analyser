import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'

interface ValueTimelineChartProps {
  valueSaved: { min: number; max: number }
  valueCreated: { min: number; max: number }
  totalInvestment?: number
}

export default function ValueTimelineChart({ valueSaved, valueCreated, totalInvestment = 0 }: ValueTimelineChartProps) {
  // Generate 3-year projection data
  const generateData = () => {
    const data = []
    const months = 36 // 3 years

    for (let month = 0; month <= months; month += 6) {
      const progress = month / months
      // S-curve adoption: slow start, accelerate, plateau
      const adoption = 1 / (1 + Math.exp(-10 * (progress - 0.3)))

      const savedMin = Math.round((valueSaved.min / 3) * progress * adoption)
      const savedMax = Math.round((valueSaved.max / 3) * progress * adoption)
      const createdMin = Math.round((valueCreated.min / 3) * progress * adoption)
      const createdMax = Math.round((valueCreated.max / 3) * progress * adoption)

      // Investment happens early
      const investmentSpent = month <= 12 ? totalInvestment * (month / 12) : totalInvestment

      data.push({
        month,
        label: month === 0 ? 'Now' : `${month}mo`,
        valueSavedMin: savedMin,
        valueSavedMax: savedMax,
        valueCreatedMin: createdMin,
        valueCreatedMax: createdMax,
        totalMin: savedMin + createdMin,
        totalMax: savedMax + createdMax,
        investment: Math.round(investmentSpent),
        netMin: savedMin + createdMin - Math.round(investmentSpent),
        netMax: savedMax + createdMax - Math.round(investmentSpent)
      })
    }

    return data
  }

  const data = generateData()

  const formatCurrency = (value: number) => {
    if (value >= 1000000) return `€${(value / 1000000).toFixed(1)}M`
    if (value >= 1000) return `€${(value / 1000).toFixed(0)}K`
    return `€${value}`
  }

  // Find break-even point
  const breakEvenMonth = data.find(d => d.netMin > 0)?.month || null

  return (
    <div className="w-full">
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorInvestment" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="label"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: '#6b7280' }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: '#6b7280' }}
              tickFormatter={formatCurrency}
              width={60}
            />
            <Tooltip
              formatter={(value: number, name: string) => [formatCurrency(value), name]}
              labelFormatter={(label) => `Timeline: ${label}`}
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '12px'
              }}
            />
            {breakEvenMonth && (
              <ReferenceLine
                x={`${breakEvenMonth}mo`}
                stroke="#9333ea"
                strokeDasharray="5 5"
                label={{
                  value: 'Break-even',
                  position: 'top',
                  fill: '#9333ea',
                  fontSize: 10
                }}
              />
            )}
            <Area
              type="monotone"
              dataKey="totalMax"
              stroke="#22c55e"
              fill="url(#colorValue)"
              strokeWidth={2}
              name="Total Value (High)"
            />
            <Area
              type="monotone"
              dataKey="totalMin"
              stroke="#22c55e"
              fill="transparent"
              strokeWidth={1}
              strokeDasharray="3 3"
              name="Total Value (Low)"
            />
            <Area
              type="monotone"
              dataKey="investment"
              stroke="#ef4444"
              fill="url(#colorInvestment)"
              strokeWidth={2}
              name="Investment"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="flex justify-center gap-6 mt-2 text-xs">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-green-500 rounded" />
          <span className="text-gray-600">Cumulative Value</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-red-500 rounded" />
          <span className="text-gray-600">Investment</span>
        </div>
        {breakEvenMonth && (
          <div className="flex items-center gap-1">
            <div className="w-3 h-0.5 bg-purple-500" />
            <span className="text-gray-600">Break-even ~{breakEvenMonth}mo</span>
          </div>
        )}
      </div>
    </div>
  )
}
