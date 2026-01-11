import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface Finding {
  id: string
  title: string
  description: string
  customer_value_score: number
  business_health_score: number
  confidence: 'high' | 'medium' | 'low'
  time_horizon: 'short' | 'mid' | 'long'
  value_saved?: { hours_per_week: number; hourly_rate: number; annual_savings: number }
  value_created?: { description: string; potential_revenue: number }
}

// Derive verdict from scores - aligns with landing page promise
function getVerdict(finding: Finding): { label: string; color: string; bgColor: string } {
  const combined = finding.customer_value_score + finding.business_health_score
  if (combined >= 14) {
    return { label: 'Proceed', color: 'text-emerald-700', bgColor: 'bg-emerald-50 border-emerald-200' }
  } else if (combined >= 8) {
    return { label: 'Wait', color: 'text-amber-700', bgColor: 'bg-amber-50 border-amber-200' }
  }
  return { label: 'Skip', color: 'text-gray-600', bgColor: 'bg-gray-100 border-gray-200' }
}

interface TieredFindingsProps {
  findings: Finding[]
  heroCount?: number
  compactCount?: number
}

function HeroFindingCard({ finding, index }: { finding: Finding; index: number }) {
  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(value)
  const verdict = getVerdict(finding)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="bg-white dark:bg-gray-800 rounded-xl border-2 border-primary-200 dark:border-primary-800 p-6 shadow-sm"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={`px-2.5 py-1 text-xs font-bold rounded-full border uppercase tracking-wide ${verdict.bgColor} ${verdict.color}`}>
            {verdict.label}
          </span>
          <span className="px-2 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-xs font-medium rounded">
            Highest Impact
          </span>
        </div>
        <div className="flex gap-2">
          <span className="px-2 py-1 text-xs font-medium rounded bg-blue-100 text-blue-700 capitalize">
            {finding.time_horizon}
          </span>
        </div>
      </div>
      <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
        {finding.title}
      </h3>
      <p className="text-gray-600 dark:text-gray-400 mb-4">
        {finding.description}
      </p>
      {(finding.value_saved?.annual_savings || finding.value_created?.potential_revenue) && (
        <div className="flex gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          {finding.value_saved?.annual_savings && (
            <div>
              <p className="text-xs text-gray-500">Potential Savings</p>
              <p className="text-lg font-bold text-green-600">{formatCurrency(finding.value_saved.annual_savings)}/yr</p>
            </div>
          )}
          {finding.value_created?.potential_revenue && (
            <div>
              <p className="text-xs text-gray-500">Revenue Potential</p>
              <p className="text-lg font-bold text-blue-600">{formatCurrency(finding.value_created.potential_revenue)}</p>
            </div>
          )}
        </div>
      )}
    </motion.div>
  )
}

function CompactFindingCard({ finding }: { finding: Finding }) {
  const verdict = getVerdict(finding)
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className={`px-2 py-0.5 text-[10px] font-bold rounded-full border uppercase tracking-wide ${verdict.bgColor} ${verdict.color}`}>
          {verdict.label}
        </span>
      </div>
      <h4 className="font-medium text-gray-900 dark:text-white mb-1 line-clamp-2">
        {finding.title}
      </h4>
      <div className="flex items-center gap-2 text-xs">
        <span className="text-gray-500 capitalize">{finding.time_horizon}</span>
        <span className="text-gray-300">•</span>
        <span className={`font-medium ${finding.confidence === 'high' ? 'text-green-600' : 'text-yellow-600'}`}>
          {finding.confidence} confidence
        </span>
      </div>
    </div>
  )
}

export default function TieredFindings({ findings, heroCount = 3, compactCount = 4 }: TieredFindingsProps) {
  const [showAll, setShowAll] = useState(false)

  // Sort by combined score
  const sortedFindings = [...findings].sort(
    (a, b) => (b.customer_value_score + b.business_health_score) - (a.customer_value_score + a.business_health_score)
  )

  const heroFindings = sortedFindings.slice(0, heroCount)
  const compactFindings = sortedFindings.slice(heroCount, heroCount + compactCount)
  const remainingFindings = sortedFindings.slice(heroCount + compactCount)

  return (
    <section id="findings" className="scroll-mt-20 mb-8">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-1">
          What We Found
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          {findings.length} findings from your analysis, prioritized by impact
        </p>
      </div>

      {/* Hero Findings */}
      <div className="space-y-4 mb-6">
        {heroFindings.map((finding, i) => (
          <HeroFindingCard key={finding.id} finding={finding} index={i} />
        ))}
      </div>

      {/* Compact Findings */}
      {compactFindings.length > 0 && (
        <div className="mb-4">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
            More Findings
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {compactFindings.map((finding) => (
              <CompactFindingCard key={finding.id} finding={finding} />
            ))}
          </div>
        </div>
      )}

      {/* Remaining Findings (expandable) */}
      {remainingFindings.length > 0 && (
        <div>
          <button
            onClick={() => setShowAll(!showAll)}
            className="flex items-center gap-2 text-sm font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700"
          >
            {showAll ? 'Show less' : `+ ${remainingFindings.length} more findings`}
            <svg
              className={`w-4 h-4 transition-transform ${showAll ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <AnimatePresence>
            {showAll && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3"
              >
                {remainingFindings.map((finding) => (
                  <CompactFindingCard key={finding.id} finding={finding} />
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </section>
  )
}
