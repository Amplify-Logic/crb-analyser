// frontend/src/components/report/AutomationRoadmap.tsx
import { motion } from 'framer-motion'

interface StackAssessmentItem {
  name: string
  slug: string
  api_score: number
  category?: string
}

interface StackAssessment {
  tools: StackAssessmentItem[]
  average_score: number
  verdict: 'strong_foundation' | 'good_foundation' | 'moderate_foundation' | 'limited_foundation' | 'no_tools'
  verdict_text: string
}

interface AutomationOpportunity {
  finding_id: string
  title: string
  impact_monthly: number
  diy_effort_hours: number
  approach: 'Connect' | 'Replace' | 'Either'
  tools_involved: string[]
  category: string
}

interface NextSteps {
  tier: string
  headline: string
  message: string
  cta_text: string
  cta_url: string
}

interface AutomationSummary {
  stack_assessment: StackAssessment
  opportunities: AutomationOpportunity[]
  total_monthly_impact: number
  total_diy_hours: number
  connect_count: number
  replace_count: number
  either_count: number
  next_steps: NextSteps
}

interface AutomationRoadmapProps {
  summary: AutomationSummary
}

function ApiScoreBar({ score }: { score: number }) {
  // Create visual bar representation (e.g., "████░░" for 4/5)
  const filledBlocks = score
  const emptyBlocks = 5 - score

  return (
    <div className="flex items-center gap-2">
      <span className="font-mono text-sm">
        <span className="text-primary-600 dark:text-primary-400">
          {'█'.repeat(filledBlocks)}
        </span>
        <span className="text-gray-300 dark:text-gray-600">
          {'░'.repeat(emptyBlocks)}
        </span>
      </span>
      <span className="text-sm text-gray-600 dark:text-gray-400">
        {score}/5
      </span>
    </div>
  )
}

function ApproachBadge({ approach }: { approach: 'Connect' | 'Replace' | 'Either' }) {
  const styles = {
    Connect: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    Replace: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    Either: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  }

  const icons = {
    Connect: (
      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
      </svg>
    ),
    Replace: (
      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    ),
    Either: (
      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
      </svg>
    ),
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${styles[approach]}`}>
      {icons[approach]}
      {approach}
    </span>
  )
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0
  }).format(value)
}

function formatHours(hours: number) {
  if (hours === 0) return '-'
  if (hours < 1) return '<1h'
  return `${Math.round(hours)}h`
}

export default function AutomationRoadmap({ summary }: AutomationRoadmapProps) {
  const { stack_assessment, opportunities, total_monthly_impact, total_diy_hours, next_steps } = summary

  const verdictStyles = {
    strong_foundation: 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20',
    good_foundation: 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20',
    moderate_foundation: 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20',
    limited_foundation: 'text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20',
    no_tools: 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800/50',
  }

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="text-center mb-8">
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 rounded-full mb-4"
        >
          <svg className="w-5 h-5 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
          <span className="text-sm font-medium text-primary-700 dark:text-primary-300">Your Automation Roadmap</span>
        </motion.div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Ready to Automate
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Based on your existing tools and opportunities identified
        </p>
      </div>

      {/* Stack Assessment */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Stack Assessment
          </h3>
          <div className={`px-3 py-1.5 rounded-lg text-sm font-medium ${verdictStyles[stack_assessment.verdict]}`}>
            {stack_assessment.verdict_text}
          </div>
        </div>

        {stack_assessment.tools.length > 0 ? (
          <>
            <div className="space-y-3">
              {stack_assessment.tools.map((tool) => (
                <div
                  key={tool.slug}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center">
                      <svg className="w-4 h-4 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                      </svg>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{tool.name}</p>
                      {tool.category && (
                        <p className="text-xs text-gray-500 dark:text-gray-400">{tool.category}</p>
                      )}
                    </div>
                  </div>
                  <ApiScoreBar score={tool.api_score} />
                </div>
              ))}
            </div>

            {/* Average Score Summary */}
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Average API Score
              </span>
              <div className="flex items-center gap-3">
                <ApiScoreBar score={Math.round(stack_assessment.average_score)} />
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  ({stack_assessment.average_score.toFixed(1)}/5)
                </span>
              </div>
            </div>
          </>
        ) : (
          <div className="text-center py-8">
            <div className="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-gray-500 dark:text-gray-400">
              No existing tools to assess
            </p>
          </div>
        )}
      </motion.div>

      {/* Opportunities Table */}
      {opportunities.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden"
        >
          <div className="p-6 pb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Opportunities Identified
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Automation opportunities from your analysis
            </p>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-t border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Automation
                  </th>
                  <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Impact/mo
                  </th>
                  <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    DIY Effort
                  </th>
                  <th className="text-center px-6 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Approach
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {opportunities.map((opp, index) => (
                  <motion.tr
                    key={opp.finding_id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.05 * index }}
                    className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">
                          {opp.title}
                        </p>
                        {opp.tools_involved.length > 0 && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            {opp.tools_involved.slice(0, 3).join(' + ')}
                            {opp.tools_involved.length > 3 && ` +${opp.tools_involved.length - 3} more`}
                          </p>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <span className="font-semibold text-green-600 dark:text-green-400">
                        {formatCurrency(opp.impact_monthly)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <span className="text-gray-600 dark:text-gray-400">
                        {formatHours(opp.diy_effort_hours)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <ApproachBadge approach={opp.approach} />
                    </td>
                  </motion.tr>
                ))}

                {/* Total Row */}
                <tr className="bg-gray-50 dark:bg-gray-800/50 font-semibold">
                  <td className="px-6 py-4">
                    <span className="text-gray-900 dark:text-white">TOTAL POTENTIAL</span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <span className="text-lg text-green-600 dark:text-green-400">
                      {formatCurrency(total_monthly_impact)}/mo
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <span className="text-gray-700 dark:text-gray-300">
                      ~{formatHours(total_diy_hours)}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {summary.connect_count} Connect / {summary.replace_count} Replace
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* Next Steps CTA */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 rounded-xl border border-primary-200 dark:border-primary-800/30 p-6"
      >
        <div className="flex flex-col md:flex-row items-start md:items-center gap-4">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900/50 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
          <div className="flex-1">
            <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
              {next_steps.headline}
            </h4>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {next_steps.message}
            </p>
          </div>
          <a
            href={next_steps.cta_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors shadow-sm hover:shadow-md"
          >
            {next_steps.cta_text}
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </a>
        </div>
      </motion.div>

      {/* Summary Stats (Small footer) */}
      <div className="flex flex-wrap justify-center gap-6 text-sm text-gray-500 dark:text-gray-400">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 bg-green-500 rounded-full"></span>
          <span>{summary.connect_count} Connect opportunities</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
          <span>{summary.replace_count} Replace opportunities</span>
        </div>
        {summary.either_count > 0 && (
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
            <span>{summary.either_count} flexible opportunities</span>
          </div>
        )}
      </div>
    </div>
  )
}
