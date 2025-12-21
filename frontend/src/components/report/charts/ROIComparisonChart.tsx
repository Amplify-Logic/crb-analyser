import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, Tooltip, LabelList } from 'recharts'

interface Recommendation {
  id: string
  title: string
  roi_percentage?: number
  payback_months?: number
  priority: 'high' | 'medium' | 'low'
}

interface ROIComparisonChartProps {
  recommendations: Recommendation[]
  maxItems?: number
}

export default function ROIComparisonChart({ recommendations, maxItems = 5 }: ROIComparisonChartProps) {
  // Sort by ROI and take top items
  const sortedRecs = [...recommendations]
    .filter(r => r.roi_percentage && r.roi_percentage > 0)
    .sort((a, b) => (b.roi_percentage || 0) - (a.roi_percentage || 0))
    .slice(0, maxItems)

  const data = sortedRecs.map(rec => ({
    name: rec.title.length > 30 ? rec.title.substring(0, 30) + '...' : rec.title,
    fullName: rec.title,
    roi: rec.roi_percentage || 0,
    payback: rec.payback_months || 0,
    priority: rec.priority
  }))

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return '#22c55e'
      case 'medium': return '#3b82f6'
      case 'low': return '#9ca3af'
      default: return '#6b7280'
    }
  }

  if (data.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        <p>No ROI data available for recommendations</p>
      </div>
    )
  }

  return (
    <div className="w-full">
      <div style={{ height: Math.max(200, data.length * 50) }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 5, right: 60, left: 10, bottom: 5 }}
          >
            <XAxis
              type="number"
              domain={[0, 'auto']}
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: '#6b7280' }}
              tickFormatter={(value) => `${value}%`}
            />
            <YAxis
              type="category"
              dataKey="name"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: '#374151' }}
              width={180}
            />
            <Tooltip
              formatter={(value: number) => [`${value}%`, 'ROI']}
              labelFormatter={(label: string, payload: any[]) => {
                if (payload && payload[0]) {
                  const item = payload[0].payload
                  return `${item.fullName}\nPayback: ${item.payback} months`
                }
                return label
              }}
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '12px',
                whiteSpace: 'pre-line'
              }}
            />
            <Bar
              dataKey="roi"
              radius={[0, 4, 4, 0]}
              barSize={20}
            >
              {data.map((entry, index) => (
                <Cell key={index} fill={getPriorityColor(entry.priority)} />
              ))}
              <LabelList
                dataKey="roi"
                position="right"
                formatter={(value: number) => `${value}%`}
                style={{ fontSize: 12, fontWeight: 600, fill: '#374151' }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="flex justify-center gap-4 mt-3 text-xs">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-green-500 rounded" />
          <span className="text-gray-600">High Priority</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-blue-500 rounded" />
          <span className="text-gray-600">Medium Priority</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-gray-400 rounded" />
          <span className="text-gray-600">Low Priority</span>
        </div>
      </div>
    </div>
  )
}
