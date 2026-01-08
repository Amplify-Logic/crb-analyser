// frontend/src/components/report/CRBAnalysis.tsx
import { motion } from 'framer-motion'

// CRB Types
interface ImplementationCostDIY {
  hours: number
  hourly_rate: number
  total: number
  description?: string
}

interface ImplementationCostProfessional {
  estimate: number
  source?: string
}

interface MonthlyCostItem {
  item: string
  cost: number
}

interface MonthlyCostBreakdown {
  breakdown: MonthlyCostItem[]
  total: number
}

interface HiddenCosts {
  training_hours: number
  productivity_dip_weeks: number
  notes?: string
}

interface CostBreakdown {
  implementation_diy?: ImplementationCostDIY
  implementation_professional?: ImplementationCostProfessional
  monthly_ongoing?: MonthlyCostBreakdown
  hidden?: HiddenCosts
}

interface RiskAssessment {
  implementation_score: number
  implementation_reason: string
  dependency_risk: string
  reversal_difficulty: 'Easy' | 'Medium' | 'Hard'
  additional_risks?: string[]
  // Replace path specific
  migration_complexity?: string
  vendor_lock_in?: string
}

interface BenefitQuantification {
  primary_metric: string
  baseline: string
  target: string
  monthly_value: number
  calculation: string
  confidence?: 'HIGH' | 'MEDIUM' | 'LOW'
  confidence_reason?: string
  expected_improvement?: string
}

interface ROIAnalysis {
  conservative: number
  expected: number
  optimistic: number
  payback_months_conservative: number
  payback_months_expected: number
  sensitivity_note?: string
}

interface CRBAnalysisData {
  cost?: CostBreakdown
  risk?: RiskAssessment
  benefit?: BenefitQuantification
  roi?: ROIAnalysis
  recommendation_summary?: string
  confidence_level?: 'HIGH' | 'MEDIUM' | 'LOW'
  data_gaps?: string[]
}

interface CRBAnalysisProps {
  crb: CRBAnalysisData
  pathType: 'CONNECT' | 'REPLACE'
  title?: string
  compact?: boolean
}

const RISK_COLORS = {
  1: { bg: 'bg-green-100', text: 'text-green-700', label: 'Very Low' },
  2: { bg: 'bg-green-50', text: 'text-green-600', label: 'Low' },
  3: { bg: 'bg-yellow-50', text: 'text-yellow-700', label: 'Medium' },
  4: { bg: 'bg-orange-50', text: 'text-orange-700', label: 'High' },
  5: { bg: 'bg-red-50', text: 'text-red-700', label: 'Very High' },
}

const CONFIDENCE_COLORS = {
  HIGH: { bg: 'bg-green-100', text: 'text-green-700', dot: 'bg-green-500' },
  MEDIUM: { bg: 'bg-yellow-100', text: 'text-yellow-700', dot: 'bg-yellow-500' },
  LOW: { bg: 'bg-gray-100', text: 'text-gray-600', dot: 'bg-gray-400' },
}

const REVERSAL_COLORS = {
  Easy: { bg: 'bg-green-50', text: 'text-green-700' },
  Medium: { bg: 'bg-yellow-50', text: 'text-yellow-700' },
  Hard: { bg: 'bg-red-50', text: 'text-red-700' },
}

function formatEuro(amount: number): string {
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

export default function CRBAnalysis({ crb, pathType, title, compact = false }: CRBAnalysisProps) {
  if (!crb) return null

  const { cost, risk, benefit, roi, confidence_level, data_gaps } = crb
  const confidenceStyle = CONFIDENCE_COLORS[confidence_level || 'MEDIUM']

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden ${
        compact ? 'text-sm' : ''
      }`}
    >
      {/* Header */}
      <div className={`px-4 py-3 border-b border-gray-200 dark:border-gray-700 ${
        pathType === 'CONNECT' ? 'bg-blue-50 dark:bg-blue-900/20' : 'bg-purple-50 dark:bg-purple-900/20'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {pathType === 'CONNECT' ? (
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
            ) : (
              <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            )}
            <h4 className={`font-semibold ${
              pathType === 'CONNECT' ? 'text-blue-700 dark:text-blue-300' : 'text-purple-700 dark:text-purple-300'
            }`}>
              {title || (pathType === 'CONNECT' ? 'Connect Path Analysis' : 'Replace Path Analysis')}
            </h4>
          </div>
          {confidence_level && (
            <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${confidenceStyle.bg} ${confidenceStyle.text}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${confidenceStyle.dot}`} />
              {confidence_level} confidence
            </span>
          )}
        </div>
      </div>

      <div className="divide-y divide-gray-100 dark:divide-gray-700">
        {/* COST Section */}
        {cost && (
          <div className="p-4">
            <h5 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-amber-500" />
              COST
            </h5>
            <div className="space-y-2">
              {/* Implementation Cost */}
              {(cost.implementation_diy || cost.implementation_professional) && (
                <div className="flex justify-between items-start">
                  <span className="text-gray-600 dark:text-gray-400">Implementation:</span>
                  <div className="text-right">
                    {cost.implementation_diy && (
                      <div className="text-gray-900 dark:text-white font-medium">
                        {formatEuro(cost.implementation_diy.total)}
                        <span className="text-xs text-gray-500 ml-1">
                          ({cost.implementation_diy.hours} hrs DIY)
                        </span>
                      </div>
                    )}
                    {cost.implementation_professional && (
                      <div className="text-xs text-gray-500">
                        or {formatEuro(cost.implementation_professional.estimate)} professional
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Monthly Costs */}
              {cost.monthly_ongoing && cost.monthly_ongoing.total > 0 && (
                <div className="flex justify-between items-start">
                  <span className="text-gray-600 dark:text-gray-400">Monthly:</span>
                  <div className="text-right">
                    <div className="text-gray-900 dark:text-white font-medium">
                      {formatEuro(cost.monthly_ongoing.total)}/month
                    </div>
                    {cost.monthly_ongoing.breakdown.length > 0 && (
                      <div className="text-xs text-gray-500">
                        {cost.monthly_ongoing.breakdown.map(item => `${item.item}: ${formatEuro(item.cost)}`).join(', ')}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Hidden Costs */}
              {cost.hidden && (cost.hidden.training_hours > 0 || cost.hidden.productivity_dip_weeks > 0) && (
                <div className="flex justify-between items-start text-xs">
                  <span className="text-gray-500">Hidden:</span>
                  <span className="text-gray-600 dark:text-gray-400">
                    {cost.hidden.training_hours > 0 && `${cost.hidden.training_hours} hrs training`}
                    {cost.hidden.training_hours > 0 && cost.hidden.productivity_dip_weeks > 0 && ', '}
                    {cost.hidden.productivity_dip_weeks > 0 && `${cost.hidden.productivity_dip_weeks} wks ramp-up`}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* RISK Section */}
        {risk && (
          <div className="p-4">
            <h5 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-orange-500" />
              RISK
            </h5>
            <div className="space-y-2">
              {/* Implementation Risk Score */}
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400">Implementation:</span>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    RISK_COLORS[risk.implementation_score as keyof typeof RISK_COLORS]?.bg || 'bg-gray-100'
                  } ${RISK_COLORS[risk.implementation_score as keyof typeof RISK_COLORS]?.text || 'text-gray-600'}`}>
                    {risk.implementation_score}/5 - {RISK_COLORS[risk.implementation_score as keyof typeof RISK_COLORS]?.label || 'Unknown'}
                  </span>
                </div>
              </div>
              {risk.implementation_reason && (
                <p className="text-xs text-gray-500 pl-0">{risk.implementation_reason}</p>
              )}

              {/* Dependency Risk */}
              {risk.dependency_risk && (
                <div className="flex justify-between items-start text-sm">
                  <span className="text-gray-600 dark:text-gray-400">Dependency:</span>
                  <span className="text-gray-700 dark:text-gray-300 text-right max-w-[60%]">
                    {risk.dependency_risk}
                  </span>
                </div>
              )}

              {/* Reversal Difficulty */}
              {risk.reversal_difficulty && (
                <div className="flex justify-between items-center">
                  <span className="text-gray-600 dark:text-gray-400">Reversal:</span>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    REVERSAL_COLORS[risk.reversal_difficulty]?.bg || 'bg-gray-100'
                  } ${REVERSAL_COLORS[risk.reversal_difficulty]?.text || 'text-gray-600'}`}>
                    {risk.reversal_difficulty}
                  </span>
                </div>
              )}

              {/* Vendor Lock-in (Replace path) */}
              {risk.vendor_lock_in && (
                <div className="flex justify-between items-start text-sm">
                  <span className="text-gray-600 dark:text-gray-400">Lock-in:</span>
                  <span className="text-gray-700 dark:text-gray-300 text-right max-w-[60%]">
                    {risk.vendor_lock_in}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* BENEFIT Section */}
        {benefit && (
          <div className="p-4">
            <h5 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500" />
              BENEFIT
            </h5>
            <div className="space-y-2">
              {/* Primary Metric */}
              {benefit.primary_metric && (
                <div className="flex justify-between items-center">
                  <span className="text-gray-600 dark:text-gray-400">{benefit.primary_metric}:</span>
                  <span className="text-gray-900 dark:text-white font-medium">
                    {benefit.baseline} &rarr; {benefit.target}
                  </span>
                </div>
              )}

              {/* Monthly Value */}
              {benefit.monthly_value > 0 && (
                <div className="flex justify-between items-center">
                  <span className="text-gray-600 dark:text-gray-400">Monthly value:</span>
                  <span className="text-green-600 dark:text-green-400 font-semibold">
                    {formatEuro(benefit.monthly_value)}/month
                  </span>
                </div>
              )}

              {/* Calculation */}
              {benefit.calculation && (
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-2 mt-2">
                  <p className="text-xs text-gray-600 dark:text-gray-400 font-mono">
                    {benefit.calculation}
                  </p>
                </div>
              )}

              {/* Benefit Confidence */}
              {benefit.confidence && (
                <div className="flex justify-between items-center text-xs">
                  <span className="text-gray-500">Confidence:</span>
                  <span className={`px-2 py-0.5 rounded font-medium ${
                    CONFIDENCE_COLORS[benefit.confidence]?.bg || 'bg-gray-100'
                  } ${CONFIDENCE_COLORS[benefit.confidence]?.text || 'text-gray-600'}`}>
                    {benefit.confidence}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ROI Section */}
        {roi && (
          <div className="p-4 bg-gray-50 dark:bg-gray-700/30">
            <h5 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-blue-500" />
              ROI ANALYSIS
            </h5>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-xs text-gray-500 mb-1">Conservative</p>
                <p className="text-lg font-semibold text-gray-700 dark:text-gray-300">
                  {roi.conservative > 0 ? '+' : ''}{roi.conservative.toFixed(0)}%
                </p>
                <p className="text-xs text-gray-400">
                  {roi.payback_months_conservative < 999 ? `${roi.payback_months_conservative.toFixed(1)} mo` : '-'}
                </p>
              </div>
              <div className="border-x border-gray-200 dark:border-gray-600">
                <p className="text-xs text-gray-500 mb-1">Expected</p>
                <p className={`text-lg font-bold ${
                  roi.expected > 100 ? 'text-green-600 dark:text-green-400' : 'text-gray-900 dark:text-white'
                }`}>
                  {roi.expected > 0 ? '+' : ''}{roi.expected.toFixed(0)}%
                </p>
                <p className="text-xs text-gray-400">
                  {roi.payback_months_expected < 999 ? `${roi.payback_months_expected.toFixed(1)} mo payback` : '-'}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-1">Optimistic</p>
                <p className="text-lg font-semibold text-gray-700 dark:text-gray-300">
                  {roi.optimistic > 0 ? '+' : ''}{roi.optimistic.toFixed(0)}%
                </p>
                <p className="text-xs text-gray-400">best case</p>
              </div>
            </div>
            {roi.sensitivity_note && (
              <p className="text-xs text-gray-500 mt-3 italic">
                {roi.sensitivity_note}
              </p>
            )}
          </div>
        )}

        {/* Data Gaps */}
        {data_gaps && data_gaps.length > 0 && (
          <div className="p-4 bg-amber-50 dark:bg-amber-900/20">
            <h5 className="text-xs font-semibold text-amber-700 dark:text-amber-400 uppercase tracking-wide mb-2 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              What We Don't Know
            </h5>
            <ul className="text-xs text-amber-800 dark:text-amber-300 space-y-1">
              {data_gaps.map((gap, i) => (
                <li key={i} className="flex items-start gap-1">
                  <span className="text-amber-500">-</span>
                  <span>{gap}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </motion.div>
  )
}

// Compact version for side-by-side comparison
export function CRBComparisonTable({
  connectCRB,
  replaceCRB,
  winner,
}: {
  connectCRB?: CRBAnalysisData
  replaceCRB?: CRBAnalysisData
  winner?: 'CONNECT' | 'REPLACE' | 'EITHER'
}) {
  if (!connectCRB && !replaceCRB) return null

  const aspects = [
    {
      label: 'Implementation',
      connect: connectCRB?.cost?.implementation_diy
        ? formatEuro(connectCRB.cost.implementation_diy.total)
        : '-',
      replace: replaceCRB?.cost?.implementation_professional
        ? formatEuro(replaceCRB.cost.implementation_professional.estimate)
        : '-',
    },
    {
      label: 'Monthly cost',
      connect: connectCRB?.cost?.monthly_ongoing?.total
        ? formatEuro(connectCRB.cost.monthly_ongoing.total)
        : '-',
      replace: replaceCRB?.cost?.monthly_ongoing?.total
        ? formatEuro(replaceCRB.cost.monthly_ongoing.total)
        : '-',
    },
    {
      label: 'Risk',
      connect: connectCRB?.risk?.implementation_score
        ? `${connectCRB.risk.implementation_score}/5`
        : '-',
      replace: replaceCRB?.risk?.implementation_score
        ? `${replaceCRB.risk.implementation_score}/5`
        : '-',
    },
    {
      label: 'Monthly benefit',
      connect: connectCRB?.benefit?.monthly_value
        ? formatEuro(connectCRB.benefit.monthly_value)
        : '-',
      replace: replaceCRB?.benefit?.monthly_value
        ? formatEuro(replaceCRB.benefit.monthly_value)
        : '-',
    },
    {
      label: 'ROI (expected)',
      connect: connectCRB?.roi?.expected
        ? `${connectCRB.roi.expected.toFixed(0)}%`
        : '-',
      replace: replaceCRB?.roi?.expected
        ? `${replaceCRB.roi.expected.toFixed(0)}%`
        : '-',
    },
  ]

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
      <div className="px-4 py-3 bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700">
        <h4 className="font-semibold text-gray-900 dark:text-white">Path Comparison</h4>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 dark:border-gray-700">
            <th className="px-4 py-2 text-left text-gray-500 dark:text-gray-400 font-medium">Aspect</th>
            <th className={`px-4 py-2 text-center font-medium ${
              winner === 'CONNECT' ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20' : 'text-gray-700 dark:text-gray-300'
            }`}>
              Connect
              {winner === 'CONNECT' && <span className="ml-1">*</span>}
            </th>
            <th className={`px-4 py-2 text-center font-medium ${
              winner === 'REPLACE' ? 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20' : 'text-gray-700 dark:text-gray-300'
            }`}>
              Replace
              {winner === 'REPLACE' && <span className="ml-1">*</span>}
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
          {aspects.map((aspect) => (
            <tr key={aspect.label}>
              <td className="px-4 py-2 text-gray-600 dark:text-gray-400">{aspect.label}</td>
              <td className="px-4 py-2 text-center text-gray-900 dark:text-white">{aspect.connect}</td>
              <td className="px-4 py-2 text-center text-gray-900 dark:text-white">{aspect.replace}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {winner && (
        <div className={`px-4 py-3 border-t border-gray-200 dark:border-gray-700 text-sm ${
          winner === 'CONNECT' ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300' :
          winner === 'REPLACE' ? 'bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300' :
          'bg-gray-50 dark:bg-gray-700/50 text-gray-700 dark:text-gray-300'
        }`}>
          <strong>Recommendation:</strong> {
            winner === 'CONNECT' ? 'Connect - Use your existing tools' :
            winner === 'REPLACE' ? 'Replace - Switch to new software' :
            'Either path is viable'
          }
        </div>
      )}
    </div>
  )
}
