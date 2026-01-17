import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface OptionScore {
  option: 'buy' | 'connect' | 'build' | 'hire'
  score: number
  breakdown: {
    capability_match?: number
    preference_match?: number
    budget_fit?: number
    time_fit?: number
    value_ratio?: number
  }
  match_reasons: string[]
  concern_reasons: string[]
  is_recommended: boolean
}

interface BuyOption {
  vendor_slug: string
  vendor_name: string
  price: string
  setup_time: string
  pros: string[]
  cons: string[]
  website?: string
}

interface ConnectOption {
  integration_platform: string
  connects_to: string[]
  estimated_hours: number
  complexity: string
  pros: string[]
  cons: string[]
}

interface BuildOption {
  recommended_stack: string[]
  estimated_cost: string
  estimated_hours: string
  skills_needed: string[]
  ai_coding_viable: boolean
  approach?: string
  pros: string[]
  cons: string[]
}

interface HireOption {
  service_type: string
  estimated_cost: string
  estimated_timeline: string
  where_to_find: string[]
  pros: string[]
  cons: string[]
}

interface FourOptionRecommendation {
  finding_id: string
  finding_title: string
  buy: BuyOption
  connect?: ConnectOption
  build?: BuildOption
  hire?: HireOption
  scores: OptionScore[]
  recommended: 'buy' | 'connect' | 'build' | 'hire'
  recommendation_reasoning: string
  no_good_match?: boolean
  fallback_message?: string
}

interface FourOptionsProps {
  fourOptions: FourOptionRecommendation
}

const OPTION_LABELS = {
  buy: { title: 'Buy', icon: '🛒', color: 'blue' },
  connect: { title: 'Connect', icon: '🔗', color: 'purple' },
  build: { title: 'Build', icon: '🔨', color: 'orange' },
  hire: { title: 'Hire', icon: '👤', color: 'green' },
}

const getColorClasses = (_optionKey: string, isRecommended: boolean) => {
  if (isRecommended) {
    return 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 shadow-lg shadow-primary-500/20'
  }
  return 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800'
}

export default function FourOptions({ fourOptions }: FourOptionsProps) {
  const [expandedOption, setExpandedOption] = useState<string | null>(fourOptions.recommended)

  const getScoreForOption = (option: 'buy' | 'connect' | 'build' | 'hire'): OptionScore | undefined => {
    return fourOptions.scores.find(s => s.option === option)
  }

  const renderScoreBar = (score: number) => (
    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mt-1">
      <div
        className={`h-2 rounded-full transition-all ${
          score >= 80 ? 'bg-green-500' :
          score >= 60 ? 'bg-yellow-500' :
          score >= 40 ? 'bg-orange-500' :
          'bg-red-500'
        }`}
        style={{ width: `${Math.min(score, 100)}%` }}
      />
    </div>
  )

  const renderOptionCard = (
    optionKey: 'buy' | 'connect' | 'build' | 'hire',
    option: BuyOption | ConnectOption | BuildOption | HireOption | undefined | null
  ) => {
    if (!option) return null

    const { title, icon } = OPTION_LABELS[optionKey]
    const score = getScoreForOption(optionKey)
    const isRecommended = fourOptions.recommended === optionKey
    const isExpanded = expandedOption === optionKey

    return (
      <div
        key={optionKey}
        className={`rounded-xl border-2 transition cursor-pointer ${getColorClasses(optionKey, isRecommended)}`}
        onClick={() => setExpandedOption(isExpanded ? null : optionKey)}
      >
        {/* Header */}
        <div className="p-4 relative">
          {isRecommended && (
            <span className="absolute -top-2 left-4 px-2 py-0.5 bg-primary-600 text-white text-xs font-bold rounded uppercase">
              Best Match
            </span>
          )}

          <div className="flex items-center justify-between mt-1">
            <div className="flex items-center gap-2">
              <span className="text-xl">{icon}</span>
              <span className="font-semibold text-gray-900 dark:text-white">{title}</span>
            </div>
            {score && (
              <span className={`text-sm font-bold ${
                score.score >= 80 ? 'text-green-600' :
                score.score >= 60 ? 'text-yellow-600' :
                'text-gray-500'
              }`}>
                {Math.round(score.score)}%
              </span>
            )}
          </div>

          {score && renderScoreBar(score.score)}

          {/* Quick summary */}
          <div className="mt-3 text-sm text-gray-600 dark:text-gray-400">
            {optionKey === 'buy' && (option as BuyOption).vendor_name && (
              <p>{(option as BuyOption).vendor_name} - {(option as BuyOption).price}</p>
            )}
            {optionKey === 'connect' && (option as ConnectOption).integration_platform && (
              <p>via {(option as ConnectOption).integration_platform}</p>
            )}
            {optionKey === 'build' && (option as BuildOption).estimated_cost && (
              <p>{(option as BuildOption).estimated_cost}</p>
            )}
            {optionKey === 'hire' && (option as HireOption).service_type && (
              <p>{(option as HireOption).service_type} - {(option as HireOption).estimated_cost}</p>
            )}
          </div>
        </div>

        {/* Expanded details */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <div className="px-4 pb-4 border-t border-gray-200 dark:border-gray-700">
                {/* Match reasons */}
                {score && score.match_reasons.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-semibold text-green-700 dark:text-green-400 mb-1">Why it fits:</p>
                    <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                      {score.match_reasons.map((reason, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-green-500 mt-0.5">+</span>
                          {reason}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Concerns */}
                {score && score.concern_reasons.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-semibold text-orange-700 dark:text-orange-400 mb-1">Considerations:</p>
                    <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                      {score.concern_reasons.map((reason, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-orange-500 mt-0.5">-</span>
                          {reason}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Pros/Cons */}
                {'pros' in option && option.pros.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Pros:</p>
                    <ul className="text-sm text-gray-600 dark:text-gray-400">
                      {option.pros.map((pro, i) => (
                        <li key={i}>• {pro}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {'cons' in option && option.cons.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Cons:</p>
                    <ul className="text-sm text-gray-600 dark:text-gray-400">
                      {option.cons.map((con, i) => (
                        <li key={i}>• {con}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Option-specific details */}
                {optionKey === 'buy' && (
                  <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-sm">
                    <p><strong>Setup:</strong> {(option as BuyOption).setup_time}</p>
                    {(option as BuyOption).website && (
                      <a
                        href={(option as BuyOption).website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline mt-1 inline-block"
                      >
                        Visit website →
                      </a>
                    )}
                  </div>
                )}

                {optionKey === 'connect' && (
                  <div className="mt-3 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg text-sm">
                    <p><strong>Connects:</strong> {(option as ConnectOption).connects_to?.join(', ')}</p>
                    <p><strong>Time:</strong> ~{(option as ConnectOption).estimated_hours} hours</p>
                    <p><strong>Complexity:</strong> {(option as ConnectOption).complexity}</p>
                  </div>
                )}

                {optionKey === 'build' && (
                  <div className="mt-3 p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg text-sm">
                    {(option as BuildOption).approach && (
                      <p className="mb-2">{(option as BuildOption).approach}</p>
                    )}
                    <p><strong>Stack:</strong> {(option as BuildOption).recommended_stack?.join(', ')}</p>
                    <p><strong>Time:</strong> {(option as BuildOption).estimated_hours}</p>
                    {(option as BuildOption).ai_coding_viable && (
                      <p className="text-green-600 mt-1">AI coding tools can help!</p>
                    )}
                  </div>
                )}

                {optionKey === 'hire' && (
                  <div className="mt-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg text-sm">
                    <p><strong>Timeline:</strong> {(option as HireOption).estimated_timeline}</p>
                    <p><strong>Find on:</strong> {(option as HireOption).where_to_find?.join(', ')}</p>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    )
  }

  // No good match warning
  if (fourOptions.no_good_match && fourOptions.fallback_message) {
    return (
      <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl">
        <p className="font-semibold text-yellow-800 dark:text-yellow-300">No Clear Match</p>
        <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">{fourOptions.fallback_message}</p>
      </div>
    )
  }

  return (
    <div className="mt-4">
      <h5 className="font-semibold text-gray-900 dark:text-white mb-3">Your Options</h5>

      {/* Recommendation reasoning */}
      {fourOptions.recommendation_reasoning && (
        <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
          <p className="text-sm text-gray-700 dark:text-gray-300">{fourOptions.recommendation_reasoning}</p>
        </div>
      )}

      {/* Four options grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {renderOptionCard('buy', fourOptions.buy)}
        {renderOptionCard('connect', fourOptions.connect)}
        {renderOptionCard('build', fourOptions.build)}
        {renderOptionCard('hire', fourOptions.hire)}
      </div>
    </div>
  )
}
