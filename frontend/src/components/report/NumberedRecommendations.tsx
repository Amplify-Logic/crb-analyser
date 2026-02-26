import { useState, lazy, Suspense } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { AlertTriangle } from 'lucide-react'
import type { AutomationFlow } from './AutomationFlowBuilder'

const AutomationFlowBuilder = lazy(() => import('./AutomationFlowBuilder'))

interface Recommendation {
  id: string
  title: string
  description: string
  priority: 'high' | 'medium' | 'low'
  roi_percentage: number
  roi_calculation_failed?: boolean
  roi_calculation_note?: string
  payback_months: number
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  options: Record<string, any>
  our_recommendation: string
  recommendation_rationale: string
  assumptions: string[]
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  net_scores?: Record<string, any>
}

interface NumberedRecommendationsProps {
  recommendations: Recommendation[]
  totalCount?: number
  startIndex?: number
}

/** Detect if recommendation uses AIOS option keys */
function isAIOSFormat(options: Record<string, unknown>): boolean {
  return 'connect_and_automate' in options || 'enhance_with_ai' in options || 'targeted_upgrade' in options
}

export default function NumberedRecommendations({ recommendations, totalCount, startIndex }: NumberedRecommendationsProps) {
  const [expandedId, setExpandedId] = useState<string | null>(recommendations[0]?.id || null)

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(value)

  return (
    <section id="actions" className="scroll-mt-20 mb-8">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-1">
          What To Do
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          {totalCount != null && startIndex != null
            ? `Action ${startIndex + 1} of ${totalCount}, prioritized by impact`
            : `${recommendations.length} ${recommendations.length === 1 ? 'recommendation' : 'recommendations'} prioritized by impact`
          }
        </p>
      </div>

      <div className="space-y-3">
        {recommendations.map((rec, index) => (
          <div
            key={rec.id}
            className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden"
          >
            <div
              className="p-6 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition"
              onClick={() => setExpandedId(expandedId === rec.id ? null : rec.id)}
            >
              <div className="flex items-start gap-4">
                {/* Number Badge */}
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 flex items-center justify-center font-bold text-sm">
                  {(startIndex ?? 0) + index + 1}
                </div>

                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`px-2 py-1 text-xs font-medium rounded ${
                      rec.priority === 'high' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' :
                      rec.priority === 'medium' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400' :
                      'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                    }`}>
                      {rec.priority} priority
                    </span>
                    {rec.roi_calculation_failed ? (
                      <span className="px-2 py-1 text-xs font-medium rounded bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400" title={rec.roi_calculation_note}>
                        ROI Estimated
                      </span>
                    ) : rec.roi_percentage > 0 ? (
                      <span className="px-2 py-1 text-xs font-medium rounded bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                        {rec.roi_percentage}% ROI
                      </span>
                    ) : null}
                    {rec.payback_months && (
                      <span className="px-2 py-1 text-xs font-medium rounded bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">
                        {rec.payback_months}mo payback
                      </span>
                    )}
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {rec.title}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mt-1">
                    {rec.description}
                  </p>
                </div>

                <motion.svg
                  animate={{ rotate: expandedId === rec.id ? 180 : 0 }}
                  transition={{ duration: 0.2 }}
                  className="w-6 h-6 text-gray-400 flex-shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </motion.svg>
              </div>
            </div>

            <AnimatePresence>
              {expandedId === rec.id && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className="overflow-hidden"
                >
                  <div className="px-6 pb-6 border-t border-gray-200 dark:border-gray-700">
                    {rec.options && isAIOSFormat(rec.options) ? (
                      /* ============ AIOS OPTIONS LAYOUT ============ */
                      <div className="mt-4">
                        <h5 className="font-semibold text-gray-900 dark:text-white mb-3">Your Options</h5>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          {/* Connect & Automate */}
                          {rec.options.connect_and_automate && (
                            <div className={`p-4 rounded-xl border-2 transition relative ${
                              rec.our_recommendation === 'connect_and_automate'
                                ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20 shadow-lg shadow-emerald-500/20'
                                : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800'
                            }`}>
                              {rec.our_recommendation === 'connect_and_automate' && (
                                <span className="absolute -top-2 left-4 px-2 py-0.5 bg-emerald-600 text-white text-xs font-bold rounded uppercase">
                                  Recommended
                                </span>
                              )}
                              <p className="font-semibold mt-1 text-emerald-700 dark:text-emerald-300">Connect & Automate</p>
                              {rec.options.connect_and_automate.prerequisite && (
                                <div className="flex items-center gap-2 px-3 py-2 mt-2 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg text-xs text-amber-800 dark:text-amber-300">
                                  <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                                  <span>First: {rec.options.connect_and_automate.prerequisite}</span>
                                </div>
                              )}
                              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-3">{rec.options.connect_and_automate.approach}</p>
                              {rec.options.connect_and_automate.build_time && (
                                <div className="flex items-center gap-2 mt-2">
                                  <p className="text-lg font-bold text-gray-900 dark:text-white">
                                    {rec.options.connect_and_automate.build_time}
                                  </p>
                                  {rec.options.connect_and_automate.diy_complexity && (
                                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                                      rec.options.connect_and_automate.diy_complexity === 'low' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' :
                                      rec.options.connect_and_automate.diy_complexity === 'moderate' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400' :
                                      'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                                    }`}>
                                      {rec.options.connect_and_automate.diy_complexity}
                                    </span>
                                  )}
                                </div>
                              )}
                              {rec.options.connect_and_automate.monthly_cost && (
                                <p className="text-xs text-gray-500">{rec.options.connect_and_automate.monthly_cost}</p>
                              )}
                              {rec.options.connect_and_automate.automation_flow?.nodes?.length > 0 && (
                                <div className="mt-3">
                                  <Suspense fallback={<div className="h-[200px] animate-pulse bg-gray-100 dark:bg-gray-700 rounded-xl" />}>
                                    <AutomationFlowBuilder
                                      flow={rec.options.connect_and_automate.automation_flow as AutomationFlow}
                                      title="How it connects"
                                      height={200}
                                    />
                                  </Suspense>
                                </div>
                              )}
                              {rec.options.connect_and_automate.tools_used?.length > 0 && (
                                <div className="mt-2 flex flex-wrap gap-1">
                                  {rec.options.connect_and_automate.tools_used.map((tool: string, i: number) => (
                                    <span key={i} className="px-1.5 py-0.5 text-xs rounded bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400">{tool}</span>
                                  ))}
                                </div>
                              )}
                              {(rec.options.connect_and_automate.pros?.length || rec.options.connect_and_automate.cons?.length) && (
                                <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600 space-y-2 text-xs">
                                  {rec.options.connect_and_automate.pros?.slice(0, 3).map((pro: string, i: number) => (
                                    <p key={i} className="text-green-600 dark:text-green-400">+ {pro}</p>
                                  ))}
                                  {rec.options.connect_and_automate.cons?.slice(0, 2).map((con: string, i: number) => (
                                    <p key={i} className="text-red-500 dark:text-red-400">- {con}</p>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                          {/* Enhance with AI */}
                          {rec.options.enhance_with_ai && (
                            <div className={`p-4 rounded-xl border-2 transition relative ${
                              rec.our_recommendation === 'enhance_with_ai'
                                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-lg shadow-blue-500/20'
                                : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800'
                            }`}>
                              {rec.our_recommendation === 'enhance_with_ai' && (
                                <span className="absolute -top-2 left-4 px-2 py-0.5 bg-blue-600 text-white text-xs font-bold rounded uppercase">
                                  Recommended
                                </span>
                              )}
                              <p className="font-semibold mt-1 text-blue-700 dark:text-blue-300">Enhance with AI</p>
                              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-3">{rec.options.enhance_with_ai.approach}</p>
                              {rec.options.enhance_with_ai.build_time && (
                                <p className="text-lg font-bold mt-2 text-gray-900 dark:text-white">
                                  {rec.options.enhance_with_ai.build_time}
                                </p>
                              )}
                              {rec.options.enhance_with_ai.monthly_cost && (
                                <p className="text-xs text-gray-500">{rec.options.enhance_with_ai.monthly_cost}</p>
                              )}
                              {(rec.options.enhance_with_ai.pros?.length || rec.options.enhance_with_ai.cons?.length) && (
                                <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600 space-y-2 text-xs">
                                  {rec.options.enhance_with_ai.pros?.slice(0, 3).map((pro: string, i: number) => (
                                    <p key={i} className="text-green-600 dark:text-green-400">+ {pro}</p>
                                  ))}
                                  {rec.options.enhance_with_ai.cons?.slice(0, 2).map((con: string, i: number) => (
                                    <p key={i} className="text-red-500 dark:text-red-400">- {con}</p>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                          {/* Targeted Upgrade */}
                          {rec.options.targeted_upgrade && (
                            <div className={`p-4 rounded-xl border-2 transition relative ${
                              rec.our_recommendation === 'targeted_upgrade'
                                ? 'border-amber-500 bg-amber-50 dark:bg-amber-900/20 shadow-lg shadow-amber-500/20'
                                : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800'
                            }`}>
                              {rec.our_recommendation === 'targeted_upgrade' && (
                                <span className="absolute -top-2 left-4 px-2 py-0.5 bg-amber-600 text-white text-xs font-bold rounded uppercase">
                                  Recommended
                                </span>
                              )}
                              <p className="font-semibold mt-1 text-amber-700 dark:text-amber-300">Targeted Upgrade</p>
                              {rec.options.targeted_upgrade.when_needed && (
                                <p className="text-xs text-amber-600 dark:text-amber-400 mt-1 italic">{rec.options.targeted_upgrade.when_needed}</p>
                              )}
                              {rec.options.targeted_upgrade.tools?.length > 0 && (
                                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{rec.options.targeted_upgrade.tools.join(', ')}</p>
                              )}
                              {rec.options.targeted_upgrade.cost_range && (
                                <p className="text-lg font-bold mt-2 text-gray-900 dark:text-white">
                                  {rec.options.targeted_upgrade.cost_range}
                                </p>
                              )}
                              {rec.options.targeted_upgrade.migration_time && (
                                <p className="text-xs text-gray-500">{rec.options.targeted_upgrade.migration_time}</p>
                              )}
                              {(rec.options.targeted_upgrade.pros?.length || rec.options.targeted_upgrade.cons?.length) && (
                                <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600 space-y-2 text-xs">
                                  {rec.options.targeted_upgrade.pros?.slice(0, 3).map((pro: string, i: number) => (
                                    <p key={i} className="text-green-600 dark:text-green-400">+ {pro}</p>
                                  ))}
                                  {rec.options.targeted_upgrade.cons?.slice(0, 2).map((con: string, i: number) => (
                                    <p key={i} className="text-red-500 dark:text-red-400">- {con}</p>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    ) : rec.options ? (
                      /* ============ LEGACY OPTIONS LAYOUT ============ */
                      <div className="mt-4">
                        <h5 className="font-semibold text-gray-900 dark:text-white mb-3">Three Options</h5>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          {/* Off-the-shelf */}
                          <div className={`p-4 rounded-xl border-2 transition relative ${
                            rec.our_recommendation === 'off_the_shelf'
                              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 shadow-lg shadow-primary-500/20'
                              : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800'
                          }`}>
                            {rec.our_recommendation === 'off_the_shelf' && (
                              <span className="absolute -top-2 left-4 px-2 py-0.5 bg-primary-600 text-white text-xs font-bold rounded uppercase">
                                Recommended
                              </span>
                            )}
                            <p className="font-semibold mt-1 text-gray-700 dark:text-gray-300">Option A: Off-the-Shelf</p>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{rec.options.off_the_shelf?.name}</p>
                            {rec.options.off_the_shelf?.vendor_verified === true && (
                              <span className="inline-block mt-1 px-2 py-0.5 text-xs font-medium rounded bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">Verified vendor</span>
                            )}
                            {rec.options.off_the_shelf?.vendor_verified === false && (
                              <span className="inline-block mt-1 px-2 py-0.5 text-xs font-medium rounded bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400">Unverified vendor</span>
                            )}
                            <p className="text-lg font-bold mt-2 text-gray-900 dark:text-white">
                              {formatCurrency(rec.options.off_the_shelf?.monthly_cost || 0)}/mo
                            </p>
                            <p className="text-xs text-gray-500">{rec.options.off_the_shelf?.implementation_weeks} weeks</p>
                            {(rec.options.off_the_shelf?.pros?.length || rec.options.off_the_shelf?.cons?.length) && (
                              <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600 space-y-2 text-xs">
                                {rec.options.off_the_shelf?.pros?.slice(0, 3).map((pro: string, i: number) => (
                                  <p key={i} className="text-green-600 dark:text-green-400">+ {pro}</p>
                                ))}
                                {rec.options.off_the_shelf?.cons?.slice(0, 2).map((con: string, i: number) => (
                                  <p key={i} className="text-red-500 dark:text-red-400">- {con}</p>
                                ))}
                              </div>
                            )}
                          </div>
                          {/* Best-in-class */}
                          <div className={`p-4 rounded-xl border-2 transition relative ${
                            rec.our_recommendation === 'best_in_class'
                              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 shadow-lg shadow-primary-500/20'
                              : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800'
                          }`}>
                            {rec.our_recommendation === 'best_in_class' && (
                              <span className="absolute -top-2 left-4 px-2 py-0.5 bg-primary-600 text-white text-xs font-bold rounded uppercase">
                                Recommended
                              </span>
                            )}
                            <p className="font-semibold mt-1 text-gray-700 dark:text-gray-300">Option B: Best-in-Class</p>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{rec.options.best_in_class?.name}</p>
                            {rec.options.best_in_class?.vendor_verified === true && (
                              <span className="inline-block mt-1 px-2 py-0.5 text-xs font-medium rounded bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">Verified vendor</span>
                            )}
                            {rec.options.best_in_class?.vendor_verified === false && (
                              <span className="inline-block mt-1 px-2 py-0.5 text-xs font-medium rounded bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400">Unverified vendor</span>
                            )}
                            <p className="text-lg font-bold mt-2 text-gray-900 dark:text-white">
                              {formatCurrency(rec.options.best_in_class?.monthly_cost || 0)}/mo
                            </p>
                            <p className="text-xs text-gray-500">{rec.options.best_in_class?.implementation_weeks} weeks</p>
                            {(rec.options.best_in_class?.pros?.length || rec.options.best_in_class?.cons?.length) && (
                              <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600 space-y-2 text-xs">
                                {rec.options.best_in_class?.pros?.slice(0, 3).map((pro: string, i: number) => (
                                  <p key={i} className="text-green-600 dark:text-green-400">+ {pro}</p>
                                ))}
                                {rec.options.best_in_class?.cons?.slice(0, 2).map((con: string, i: number) => (
                                  <p key={i} className="text-red-500 dark:text-red-400">- {con}</p>
                                ))}
                              </div>
                            )}
                          </div>
                          {/* Custom */}
                          <div className={`p-4 rounded-xl border-2 transition relative ${
                            rec.our_recommendation === 'custom_solution'
                              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 shadow-lg shadow-primary-500/20'
                              : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800'
                          }`}>
                            {rec.our_recommendation === 'custom_solution' && (
                              <span className="absolute -top-2 left-4 px-2 py-0.5 bg-primary-600 text-white text-xs font-bold rounded uppercase">
                                Recommended
                              </span>
                            )}
                            <p className="font-semibold mt-1 text-gray-700 dark:text-gray-300">Option C: Custom AI</p>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">{rec.options.custom_solution?.approach}</p>
                            <p className="text-lg font-bold mt-2 text-gray-900 dark:text-white">
                              {formatCurrency(rec.options.custom_solution?.estimated_cost?.min || 0)} - {formatCurrency(rec.options.custom_solution?.estimated_cost?.max || 0)}
                            </p>
                            <p className="text-xs text-gray-500">{rec.options.custom_solution?.implementation_weeks} weeks</p>
                            {(rec.options.custom_solution?.pros?.length || rec.options.custom_solution?.cons?.length) && (
                              <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600 space-y-2 text-xs">
                                {rec.options.custom_solution?.pros?.slice(0, 3).map((pro: string, i: number) => (
                                  <p key={i} className="text-green-600 dark:text-green-400">+ {pro}</p>
                                ))}
                                {rec.options.custom_solution?.cons?.slice(0, 2).map((con: string, i: number) => (
                                  <p key={i} className="text-red-500 dark:text-red-400">- {con}</p>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ) : null}

                    {/* NET SCORE display */}
                    {rec.net_scores && (
                      <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                        <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">NET Score (Benefit - Cost - Risk/10)</p>
                        <div className="flex gap-4 text-sm">
                          {/* AIOS scores */}
                          {rec.net_scores.connect_and_automate != null && (
                            <span className={rec.our_recommendation === 'connect_and_automate' ? 'font-bold text-emerald-700 dark:text-emerald-300' : 'text-gray-600 dark:text-gray-400'}>
                              Connect: {rec.net_scores.connect_and_automate.toFixed(1)}
                            </span>
                          )}
                          {rec.net_scores.enhance_with_ai != null && (
                            <span className={rec.our_recommendation === 'enhance_with_ai' ? 'font-bold text-blue-700 dark:text-blue-300' : 'text-gray-600 dark:text-gray-400'}>
                              Enhance: {rec.net_scores.enhance_with_ai.toFixed(1)}
                            </span>
                          )}
                          {rec.net_scores.targeted_upgrade != null && (
                            <span className={rec.our_recommendation === 'targeted_upgrade' ? 'font-bold text-amber-700 dark:text-amber-300' : 'text-gray-600 dark:text-gray-400'}>
                              Upgrade: {rec.net_scores.targeted_upgrade.toFixed(1)}
                            </span>
                          )}
                          {/* Legacy scores */}
                          {rec.net_scores.off_the_shelf != null && (
                            <span className={rec.our_recommendation === 'off_the_shelf' ? 'font-bold text-primary-700 dark:text-primary-300' : 'text-gray-600 dark:text-gray-400'}>
                              A: {rec.net_scores.off_the_shelf.toFixed(1)}
                            </span>
                          )}
                          {rec.net_scores.best_in_class != null && (
                            <span className={rec.our_recommendation === 'best_in_class' ? 'font-bold text-primary-700 dark:text-primary-300' : 'text-gray-600 dark:text-gray-400'}>
                              B: {rec.net_scores.best_in_class.toFixed(1)}
                            </span>
                          )}
                          {rec.net_scores.custom_solution != null && (
                            <span className={rec.our_recommendation === 'custom_solution' ? 'font-bold text-primary-700 dark:text-primary-300' : 'text-gray-600 dark:text-gray-400'}>
                              C: {rec.net_scores.custom_solution.toFixed(1)}
                            </span>
                          )}
                        </div>
                        {rec.net_scores.comparison_summary && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{rec.net_scores.comparison_summary}</p>
                        )}
                      </div>
                    )}

                    {/* Why we recommend */}
                    {rec.recommendation_rationale && (
                      <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl">
                        <p className="font-semibold text-green-800 dark:text-green-300">Why we recommend this option:</p>
                        <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">{rec.recommendation_rationale}</p>
                      </div>
                    )}

                    {/* Assumptions */}
                    {rec.assumptions && rec.assumptions.length > 0 && (
                      <div className="mt-4 text-sm text-gray-500 dark:text-gray-400">
                        <p className="font-medium mb-1">Assumptions:</p>
                        <ul className="list-disc list-inside space-y-1">
                          {rec.assumptions.map((assumption, i) => (
                            <li key={i}>{assumption}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>
    </section>
  )
}
