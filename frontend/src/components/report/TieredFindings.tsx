import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface AgentOpportunity {
  agent_type: string
  what_it_does: string
  estimated_impact: Record<string, string | number>
  deployment_timeline: string
  prerequisites: string[]
}

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
  agent_opportunity?: AgentOpportunity
  connect_path?: string
  replace_path?: string
}

// Derive verdict from scores - aligns with landing page promise
function getVerdict(finding: Finding): { label: string; color: string; bgColor: string } {
  const combined = finding.customer_value_score + finding.business_health_score
  if (combined >= 14) {
    return { label: 'Proceed', color: 'text-emerald-700 dark:text-emerald-400', bgColor: 'bg-emerald-50 dark:bg-emerald-900/30 border-emerald-200 dark:border-emerald-800' }
  } else if (combined >= 8) {
    return { label: 'Wait', color: 'text-amber-700 dark:text-amber-400', bgColor: 'bg-amber-50 dark:bg-amber-900/30 border-amber-200 dark:border-amber-800' }
  }
  return { label: 'Skip', color: 'text-gray-600 dark:text-gray-400', bgColor: 'bg-gray-100 dark:bg-gray-700 border-gray-200 dark:border-gray-600' }
}

// Derive severity tier from combined scores for color-coded display
function getSeverityTier(finding: Finding): { label: string; color: string; bgColor: string; icon: string } {
  const combined = finding.customer_value_score + finding.business_health_score
  if (combined >= 16) {
    return { label: 'Critical', color: 'text-red-700 dark:text-red-400', bgColor: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400', icon: '!!' }
  } else if (combined >= 14) {
    return { label: 'High', color: 'text-orange-700 dark:text-orange-400', bgColor: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400', icon: '!' }
  } else if (combined >= 10) {
    return { label: 'Medium', color: 'text-yellow-700 dark:text-yellow-400', bgColor: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400', icon: '~' }
  }
  return { label: 'Low', color: 'text-blue-700 dark:text-blue-400', bgColor: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400', icon: '-' }
}

interface TieredFindingsProps {
  findings: Finding[]
  heroCount?: number
  compactCount?: number
  totalCount?: number
  currentIndex?: number
}

function AgentOpportunityCard({ opportunity }: { opportunity: AgentOpportunity }) {
  return (
    <div className="mt-4 p-4 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg">
      <div className="flex items-center gap-2 mb-2">
        <span className="px-2 py-0.5 bg-indigo-600 text-white text-[10px] font-bold rounded uppercase tracking-wide">
          Agent Available
        </span>
        <span className="text-sm font-medium text-indigo-700 dark:text-indigo-300">
          {opportunity.agent_type}
        </span>
      </div>
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
        {opportunity.what_it_does}
      </p>
      <div className="flex flex-wrap gap-4 text-sm">
        {opportunity.estimated_impact.monthly_value_eur && (
          <div>
            <span className="text-gray-500">Est. monthly value</span>
            <p className="font-semibold text-indigo-700 dark:text-indigo-300">
              {new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(Number(opportunity.estimated_impact.monthly_value_eur))}
            </p>
          </div>
        )}
        {opportunity.estimated_impact.hours_saved_monthly && (
          <div>
            <span className="text-gray-500">Hours saved</span>
            <p className="font-semibold text-indigo-700 dark:text-indigo-300">
              {opportunity.estimated_impact.hours_saved_monthly}h/month
            </p>
          </div>
        )}
        <div>
          <span className="text-gray-500">Deployment</span>
          <p className="font-semibold text-indigo-700 dark:text-indigo-300">
            {opportunity.deployment_timeline}
          </p>
        </div>
      </div>
    </div>
  )
}

function getImpactLabel(globalIndex: number): string {
  if (globalIndex <= 1) return 'Highest Impact'
  if (globalIndex <= 3) return 'High Impact'
  return 'Moderate Impact'
}

function HeroFindingCard({ finding, index, globalIndex }: { finding: Finding; index: number; globalIndex: number }) {
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
          <span className={`px-2 py-1 text-xs font-bold rounded ${getSeverityTier(finding).bgColor}`}>
            {getSeverityTier(finding).label}
          </span>
          <span className="px-2 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-xs font-medium rounded">
            {getImpactLabel(globalIndex)}
          </span>
        </div>
        <div className="flex gap-2">
          {finding.connect_path && finding.replace_path ? (
            <span className="px-2 py-1 text-xs font-medium rounded bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400">Either</span>
          ) : finding.connect_path ? (
            <span className="px-2 py-1 text-xs font-medium rounded bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-400">Buildable on your stack</span>
          ) : finding.replace_path ? (
            <span className="px-2 py-1 text-xs font-medium rounded bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400">Replace</span>
          ) : null}
          <span className="px-2 py-1 text-xs font-medium rounded bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 capitalize">
            {finding.time_horizon}
          </span>
          <span className={`px-2 py-1 text-xs font-medium rounded ${
            finding.confidence === 'high' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
            finding.confidence === 'medium' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
            'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
          }`}>
            {finding.confidence} confidence
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
      {finding.agent_opportunity && (
        <AgentOpportunityCard opportunity={finding.agent_opportunity} />
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
        <span className={`px-1.5 py-0.5 text-[10px] font-bold rounded ${getSeverityTier(finding).bgColor}`}>
          {getSeverityTier(finding).label}
        </span>
        {finding.connect_path && finding.replace_path ? (
          <span className="px-1.5 py-0.5 text-[10px] font-medium rounded bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400">Either</span>
        ) : finding.connect_path ? (
          <span className="px-1.5 py-0.5 text-[10px] font-medium rounded bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-400">Connect</span>
        ) : finding.replace_path ? (
          <span className="px-1.5 py-0.5 text-[10px] font-medium rounded bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400">Replace</span>
        ) : null}
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
        {finding.agent_opportunity && (
          <>
            <span className="text-gray-300">•</span>
            <span className="font-medium text-indigo-600">Agent available</span>
          </>
        )}
      </div>
    </div>
  )
}

export default function TieredFindings({ findings, heroCount = 3, compactCount = 4, totalCount, currentIndex }: TieredFindingsProps) {
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
          {totalCount != null && currentIndex != null
            ? `Finding ${currentIndex + 1} of ${totalCount}, prioritized by impact`
            : `${findings.length} ${findings.length === 1 ? 'finding' : 'findings'} from your analysis, prioritized by impact`
          }
        </p>
      </div>

      {/* Hero Findings */}
      <div className="space-y-4 mb-6">
        {heroFindings.map((finding, i) => (
          <HeroFindingCard key={finding.id} finding={finding} index={i} globalIndex={currentIndex ?? i} />
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
