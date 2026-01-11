// frontend/src/components/report/InsightsTab.tsx
import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'

interface InsightCRB {
  typical_cost: string
  risk_level: 'low' | 'medium' | 'high'
  typical_benefit: string
}

interface AdoptionStat {
  capability: string
  adoption_percentage: number
  average_outcome: string
  crb?: InsightCRB  // Optional for backwards compatibility with legacy data
}

interface OpportunityMap {
  emerging: string[]
  growing: string[]
  established: string[]
  best_fit: 'emerging' | 'growing' | 'established'
  rationale: string
}

interface SocialProof {
  quote: string
  company_description: string
  outcome: string
  industry: string
}

interface IndustryInsights {
  industry: string
  industry_display_name: string
  adoption_stats: AdoptionStat[]
  opportunity_map: OpportunityMap
  social_proof: SocialProof[]
}

interface InsightsTabProps {
  insights: IndustryInsights
}

const OPPORTUNITY_LABELS = {
  emerging: {
    title: 'Emerging',
    description: 'Early wins, less proven',
    color: 'purple',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    textColor: 'text-purple-700',
    badgeColor: 'bg-purple-100 text-purple-700',
  },
  growing: {
    title: 'Growing',
    description: 'Sweet spot, high impact',
    color: 'green',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    textColor: 'text-green-700',
    badgeColor: 'bg-green-100 text-green-700',
  },
  established: {
    title: 'Established',
    description: 'Table stakes',
    color: 'blue',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    textColor: 'text-blue-700',
    badgeColor: 'bg-blue-100 text-blue-700',
  },
}

const RISK_COLORS = {
  low: 'text-green-600',
  medium: 'text-yellow-600',
  high: 'text-red-600',
}

export default function InsightsTab({ insights }: InsightsTabProps) {
  const [selectedStat, setSelectedStat] = useState<AdoptionStat | null>(null)

  if (!insights) {
    return (
      <div className="bg-white rounded-2xl p-8 text-center">
        <p className="text-gray-500">Industry insights not available.</p>
      </div>
    )
  }

  const { adoption_stats, opportunity_map, social_proof, industry_display_name } = insights

  // Validate data shape - old sample data uses different schema
  const hasValidStats = adoption_stats?.length > 0 &&
    adoption_stats[0]?.capability !== undefined &&
    adoption_stats[0]?.adoption_percentage !== undefined

  if (!hasValidStats) {
    return (
      <div className="bg-white rounded-2xl p-8 text-center">
        <p className="text-gray-500">Industry insights data format not supported.</p>
      </div>
    )
  }

  // Prepare chart data
  const chartData = adoption_stats.map((stat) => ({
    name: stat.capability,
    adoption: stat.adoption_percentage,
    outcome: stat.average_outcome,
    crb: stat.crb,
  }))

  // Sort by adoption percentage for better visualization
  chartData.sort((a, b) => b.adoption - a.adoption)

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl p-6 shadow-sm"
      >
        <div className="flex items-center gap-3 mb-2">
          <span className="text-2xl">📊</span>
          <h3 className="text-lg font-semibold text-gray-900">
            {industry_display_name} Industry Insights
          </h3>
        </div>
        <p className="text-gray-500">
          AI adoption trends and opportunities in your industry based on aggregated data
        </p>
      </motion.div>

      {/* Adoption Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white rounded-2xl p-6 shadow-sm"
      >
        <h4 className="text-md font-semibold text-gray-900 mb-6">AI Adoption by Capability</h4>

        {/* Horizontal Bar Chart */}
        <div className="h-80 mb-6">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={true} vertical={false} />
              <XAxis
                type="number"
                domain={[0, 100]}
                tickFormatter={(value) => `${value}%`}
                tick={{ fontSize: 12 }}
              />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fontSize: 12 }}
                width={90}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload
                    return (
                      <div className="bg-white p-4 rounded-xl shadow-lg border border-gray-100">
                        <p className="font-semibold text-gray-900">{data.name}</p>
                        <p className="text-primary-600 font-bold">{data.adoption}% adoption</p>
                        <p className="text-sm text-gray-500 mt-1">{data.outcome}</p>
                        {data.crb && (
                          <div className="mt-2 pt-2 border-t border-gray-100 text-xs space-y-1">
                            <p className="text-gray-600">Cost: {data.crb.typical_cost}</p>
                            <p className={RISK_COLORS[data.crb.risk_level as keyof typeof RISK_COLORS]}>
                              Risk: {data.crb.risk_level}
                            </p>
                            <p className="text-green-600">Benefit: {data.crb.typical_benefit}</p>
                          </div>
                        )}
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Bar dataKey="adoption" radius={[0, 4, 4, 0]}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={getAdoptionColor(entry.adoption)}
                    cursor="pointer"
                    onClick={() => setSelectedStat(adoption_stats.find(s => s.capability === entry.name) || null)}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Adoption Stats Cards */}
        <div className="grid grid-cols-2 gap-4">
          {adoption_stats.map((stat, index) => (
            <motion.div
              key={stat.capability}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * index }}
              className={`p-4 rounded-xl border-2 cursor-pointer transition ${
                selectedStat?.capability === stat.capability
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setSelectedStat(stat)}
            >
              <div className="flex items-start justify-between mb-2">
                <h5 className="font-medium text-gray-900">{stat.capability}</h5>
                <span className={`text-lg font-bold ${getAdoptionTextColor(stat.adoption_percentage)}`}>
                  {stat.adoption_percentage}%
                </span>
              </div>

              {/* Adoption bar */}
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden mb-2">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${stat.adoption_percentage}%` }}
                  transition={{ duration: 0.5, delay: 0.1 * index }}
                  className="h-full rounded-full"
                  style={{ backgroundColor: getAdoptionColor(stat.adoption_percentage) }}
                />
              </div>

              <p className="text-sm text-gray-500">{stat.average_outcome}</p>

              {/* CRB Mini Display */}
              {stat.crb && (
                <div className="flex gap-2 mt-2 text-xs">
                  <span className="px-2 py-0.5 bg-gray-100 rounded text-gray-600">
                    {stat.crb.typical_cost}
                  </span>
                  <span className={`px-2 py-0.5 rounded ${
                    stat.crb.risk_level === 'low' ? 'bg-green-100 text-green-700' :
                    stat.crb.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {stat.crb.risk_level} risk
                  </span>
                </div>
              )}
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Opportunity Map */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-2xl p-6 shadow-sm"
      >
        <h4 className="text-md font-semibold text-gray-900 mb-2">Opportunity Map</h4>
        <p className="text-sm text-gray-500 mb-6">
          Where to focus based on your readiness level
        </p>

        <div className="grid grid-cols-3 gap-4 mb-6">
          {(['emerging', 'growing', 'established'] as const).map((category) => {
            const config = OPPORTUNITY_LABELS[category]
            const items = opportunity_map[category]
            const isBestFit = opportunity_map.best_fit === category

            return (
              <motion.div
                key={category}
                whileHover={{ scale: 1.02 }}
                className={`p-4 rounded-xl border-2 ${config.bgColor} ${
                  isBestFit ? 'border-primary-500 ring-2 ring-primary-200' : config.borderColor
                }`}
              >
                <div className="flex items-center gap-2 mb-3">
                  <h5 className={`font-semibold ${config.textColor}`}>{config.title}</h5>
                  {isBestFit && (
                    <span className="px-2 py-0.5 bg-primary-100 text-primary-700 text-xs font-medium rounded-full">
                      Best Fit
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500 mb-3">{config.description}</p>

                <ul className="space-y-2">
                  {items.map((item, i) => (
                    <motion.li
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.3 + 0.1 * i }}
                      className="flex items-center gap-2 text-sm"
                    >
                      <span className={`w-1.5 h-1.5 rounded-full ${
                        category === 'emerging' ? 'bg-purple-400' :
                        category === 'growing' ? 'bg-green-400' :
                        'bg-blue-400'
                      }`} />
                      <span className="text-gray-700">{item}</span>
                    </motion.li>
                  ))}
                </ul>
              </motion.div>
            )
          })}
        </div>

        {/* Best Fit Rationale */}
        <div className="p-4 bg-primary-50 rounded-xl border border-primary-200">
          <div className="flex items-start gap-3">
            <span className="text-xl">💡</span>
            <div>
              <p className="font-medium text-primary-800">Our Recommendation</p>
              <p className="text-sm text-primary-700 mt-1">{opportunity_map.rationale}</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Social Proof */}
      {social_proof && social_proof.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-2xl p-6 shadow-sm"
        >
          <h4 className="text-md font-semibold text-gray-900 mb-6">What Others Are Saying</h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {social_proof.map((proof, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 + 0.1 * index }}
                className="p-5 bg-gray-50 rounded-xl relative"
              >
                {/* Quote mark */}
                <span className="absolute top-3 left-4 text-4xl text-gray-200 font-serif">"</span>

                <blockquote className="relative z-10 pt-4">
                  <p className="text-gray-700 italic mb-4">{proof.quote}</p>

                  <footer className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {proof.company_description}
                      </p>
                    </div>
                    <div className="text-right">
                      <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 text-sm font-medium rounded-full">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                        </svg>
                        {proof.outcome}
                      </span>
                    </div>
                  </footer>
                </blockquote>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* CTA */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-2xl p-6 text-white"
      >
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-lg font-semibold mb-1">Ready to Get Ahead?</h4>
            <p className="text-primary-100 text-sm">
              Your competitors are already adopting these capabilities. Start with our recommended playbook.
            </p>
          </div>
          <button className="px-6 py-3 bg-white text-primary-600 rounded-xl font-medium hover:bg-primary-50 transition flex items-center gap-2">
            View Playbook
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </button>
        </div>
      </motion.div>
    </div>
  )
}

// Helper function to get color based on adoption percentage
function getAdoptionColor(percentage: number): string {
  if (percentage >= 60) return '#10b981' // green-500
  if (percentage >= 40) return '#6366f1' // indigo-500
  if (percentage >= 20) return '#f59e0b' // amber-500
  return '#94a3b8' // slate-400
}

function getAdoptionTextColor(percentage: number): string {
  if (percentage >= 60) return 'text-green-600'
  if (percentage >= 40) return 'text-indigo-600'
  if (percentage >= 20) return 'text-amber-600'
  return 'text-slate-500'
}
