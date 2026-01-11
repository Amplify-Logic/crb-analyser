import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface Recommendation {
  id: string
  title: string
  description: string
  priority: 'high' | 'medium' | 'low'
  roi_percentage: number
  payback_months: number
  options: {
    off_the_shelf: { name: string; vendor: string; monthly_cost: number; implementation_weeks: number }
    best_in_class: { name: string; vendor: string; monthly_cost: number; implementation_weeks: number }
    custom_solution: { approach: string; estimated_cost: { min: number; max: number }; implementation_weeks: number }
  }
  our_recommendation: string
  recommendation_rationale: string
  assumptions: string[]
}

interface NumberedRecommendationsProps {
  recommendations: Recommendation[]
}

export default function NumberedRecommendations({ recommendations }: NumberedRecommendationsProps) {
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
          {recommendations.length} recommendations prioritized by impact
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
                  {index + 1}
                </div>

                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`px-2 py-1 text-xs font-medium rounded ${
                      rec.priority === 'high' ? 'bg-red-100 text-red-700' :
                      rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {rec.priority} priority
                    </span>
                    {rec.roi_percentage && (
                      <span className="px-2 py-1 text-xs font-medium rounded bg-green-100 text-green-700">
                        {rec.roi_percentage}% ROI
                      </span>
                    )}
                    {rec.payback_months && (
                      <span className="px-2 py-1 text-xs font-medium rounded bg-blue-100 text-blue-700">
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
                    {/* Three Options with Purple Glow */}
                    {rec.options && (
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
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{rec.options.off_the_shelf.name}</p>
                            <p className="text-lg font-bold mt-2 text-gray-900 dark:text-white">
                              {formatCurrency(rec.options.off_the_shelf.monthly_cost)}/mo
                            </p>
                            <p className="text-xs text-gray-500">{rec.options.off_the_shelf.implementation_weeks} weeks</p>
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
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{rec.options.best_in_class.name}</p>
                            <p className="text-lg font-bold mt-2 text-gray-900 dark:text-white">
                              {formatCurrency(rec.options.best_in_class.monthly_cost)}/mo
                            </p>
                            <p className="text-xs text-gray-500">{rec.options.best_in_class.implementation_weeks} weeks</p>
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
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">{rec.options.custom_solution.approach}</p>
                            <p className="text-lg font-bold mt-2 text-gray-900 dark:text-white">
                              {formatCurrency(rec.options.custom_solution.estimated_cost?.min || 0)} - {formatCurrency(rec.options.custom_solution.estimated_cost?.max || 0)}
                            </p>
                            <p className="text-xs text-gray-500">{rec.options.custom_solution.implementation_weeks} weeks</p>
                          </div>
                        </div>
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
                      <div className="mt-4 text-sm text-gray-500">
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
