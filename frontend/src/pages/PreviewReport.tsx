/**
 * PreviewReport Page - Insights-First Approach
 *
 * Shows diagnostic insights after quiz completion:
 * - AI Readiness Score (diagnostic, from quiz inputs)
 * - What You Told Us (user reflections - verbatim)
 * - Industry Context (verified benchmarks with sources)
 * - High-Potential Areas (categories, not recommendations)
 * - What's Next (workshop + full report preview)
 *
 * NO SPECIFIC RECOMMENDATIONS - prevents contradictions with full report.
 * See: docs/plans/2026-01-03-insights-first-teaser-design.md
 */

import { useState, useEffect } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8383'

// New schema types
interface ScoreBreakdown {
  tech_maturity: { score: number; max: number; factors: string[] }
  process_clarity: { score: number; max: number; factors: string[] }
  data_readiness: { score: number; max: number; factors: string[] }
  ai_experience: { score: number; max: number; factors: string[] }
}

interface ScoreInterpretation {
  level: 'Early Stage' | 'Developing' | 'Good' | 'Excellent'
  summary: string
  recommendation: string
}

interface UserReflection {
  type: 'pain_point' | 'goal' | 'current_state'
  what_you_told_us: string
  source: string
}

interface Benchmark {
  metric: string
  value: string
  source: {
    name: string
    url?: string
    verified_date: string
  }
  relevance?: string
}

interface OpportunityArea {
  category: string
  label: string
  potential: 'high' | 'medium'
  matched_because: string
  in_full_report: string[]
}

interface WorkshopPhase {
  name: string
  description: string
}

interface ReportDeliverable {
  icon: string
  title: string
  description: string
}

interface PersonalizedInsight {
  headline: string
  body: string
}

interface TeaserData {
  generated_at: string
  company_name: string
  industry: string
  industry_slug: string
  personalized_insight?: PersonalizedInsight
  ai_readiness: {
    score: number
    breakdown: ScoreBreakdown
    interpretation: ScoreInterpretation
  }
  diagnostics: {
    user_reflections: UserReflection[]
    industry_benchmarks: Benchmark[]
  }
  opportunity_areas: OpportunityArea[]
  next_steps: {
    workshop: {
      what_it_is: string
      duration: string
      phases: WorkshopPhase[]
      outcome: string
    }
    full_report_includes: ReportDeliverable[]
  }
  // Legacy fields
  ai_readiness_score?: number
  score_breakdown?: ScoreBreakdown
  score_interpretation?: ScoreInterpretation
}

export default function PreviewReport() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const sessionId = searchParams.get('session_id') || sessionStorage.getItem('quizSessionId')

  const [isLoading, setIsLoading] = useState(true)
  const [teaserData, setTeaserData] = useState<TeaserData | null>(null)
  const [companyName, setCompanyName] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    generatePreview()
  }, [])

  const generatePreview = async () => {
    try {
      setIsLoading(true)

      // Get stored data
      const companyProfileStr = sessionStorage.getItem('companyProfile')
      const answersStr = sessionStorage.getItem('quizAnswers')
      const messagesStr = sessionStorage.getItem('quizMessages')
      const storedCompanyName = sessionStorage.getItem('companyName')

      if (storedCompanyName) {
        setCompanyName(storedCompanyName)
      }

      const companyProfile = companyProfileStr ? JSON.parse(companyProfileStr) : {}
      const answers = answersStr ? JSON.parse(answersStr) : {}
      const messages = messagesStr ? JSON.parse(messagesStr) : []

      // DEV MODE: Use dev endpoint if available
      const isDev = searchParams.get('dev') === 'true' || import.meta.env.DEV
      if (isDev && companyProfileStr) {
        try {
          const response = await fetch(`${API_BASE_URL}/api/quiz/dev/preview`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              company_profile: companyProfile,
              quiz_answers: answers,
              interview_messages: messages,
            }),
          })

          if (response.ok) {
            const data = await response.json()
            setTeaserData(data)
            if (data.company_name) setCompanyName(data.company_name)
            setIsLoading(false)
            return
          }
        } catch (err) {
          console.warn('Dev preview endpoint failed:', err)
        }
      }

      // Try to get preview from backend with session
      if (sessionId) {
        try {
          const response = await fetch(`${API_BASE_URL}/api/quiz/sessions/${sessionId}/preview`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              company_profile: companyProfile,
              interview_answers: answers,
              interview_messages: messages,
            }),
          })

          if (response.ok) {
            const data = await response.json()
            setTeaserData(data)
            if (data.company_name) setCompanyName(data.company_name)
            setIsLoading(false)
            return
          }
        } catch (err) {
          console.warn('Backend preview failed:', err)
        }
      }

      // Fallback: Show minimal data if backend unavailable
      setError('Unable to generate preview. Please try again.')
      setIsLoading(false)
    } catch (err) {
      console.error('Preview generation error:', err)
      setError('Failed to generate preview')
      setIsLoading(false)
    }
  }

  const handleGetFullReport = () => {
    navigate(`/checkout?tier=ai`)
  }

  const getScoreColor = (level: string) => {
    switch (level) {
      case 'Excellent': return 'from-green-500 to-emerald-600'
      case 'Good': return 'from-primary-500 to-purple-600'
      case 'Developing': return 'from-amber-500 to-orange-600'
      default: return 'from-gray-500 to-gray-600'
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-50 to-purple-50 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center"
        >
          <div className="relative w-24 h-24 mx-auto mb-6">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
              className="w-24 h-24 border-4 border-primary-200 border-t-primary-600 rounded-full"
            />
            <div className="absolute inset-0 flex items-center justify-center">
              <svg className="w-10 h-10 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Generating Your Insights...</h2>
          <p className="text-gray-600">Analyzing your responses</p>
        </motion.div>
      </div>
    )
  }

  if (error || !teaserData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Something went wrong</h2>
          <p className="text-gray-600 mb-6">{error || 'Unable to load preview'}</p>
          <button
            onClick={() => navigate('/quiz')}
            className="px-6 py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700"
          >
            Start Over
          </button>
        </div>
      </div>
    )
  }

  const { ai_readiness, diagnostics, opportunity_areas, next_steps } = teaserData

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
          <Link to="/" className="text-xl font-bold text-gray-900">
            Ready<span className="text-primary-600">Path</span>
          </Link>
          <span className="text-sm text-gray-500">Your AI Readiness Insights</span>
        </div>
      </nav>

      <div className="pt-24 pb-20 px-4">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-10"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-100 text-green-800 rounded-full text-sm font-medium mb-4">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Analysis Complete
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {companyName ? `${companyName}'s AI Readiness Insights` : 'Your AI Readiness Insights'}
            </h1>
            <p className="text-gray-600">
              Here's what we learned from your responses. The workshop will dive deeper.
            </p>
          </motion.div>

          {/* AI Readiness Score Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className={`bg-gradient-to-r ${getScoreColor(ai_readiness.interpretation.level)} rounded-2xl p-8 text-white mb-8`}
          >
            <div className="flex flex-col md:flex-row items-center justify-between gap-6">
              <div>
                <h2 className="text-lg font-medium opacity-90 mb-1">AI Readiness Score</h2>
                <div className="text-6xl font-bold">{ai_readiness.score}</div>
                <p className="text-lg opacity-90 mt-2">{ai_readiness.interpretation.level}</p>
                <p className="text-sm opacity-75 mt-1">{ai_readiness.interpretation.summary}</p>
              </div>
              <div className="bg-white/20 rounded-xl p-6 backdrop-blur-sm w-full md:w-auto">
                <div className="text-sm font-medium opacity-90 mb-3">Score Breakdown</div>
                <div className="space-y-2">
                  {Object.entries(ai_readiness.breakdown).map(([key, data]) => (
                    <div key={key} className="flex items-center justify-between gap-4">
                      <span className="text-sm opacity-90 capitalize">{key.replace('_', ' ')}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-20 h-2 bg-white/30 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-white rounded-full"
                            style={{ width: `${(data.score / data.max) * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium w-10 text-right">{data.score}/{data.max}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>

          {/* Personalized Insight */}
          {teaserData.personalized_insight && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
              className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-2xl p-6 border border-amber-200 mb-8"
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-amber-100 flex items-center justify-center flex-shrink-0">
                  <span className="text-2xl">💡</span>
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-amber-900 mb-2">
                    {teaserData.personalized_insight.headline}
                  </h2>
                  <p className="text-amber-800 leading-relaxed">
                    {teaserData.personalized_insight.body}
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {/* What You Told Us */}
          {diagnostics.user_reflections.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white rounded-2xl p-6 border border-gray-200 mb-8"
            >
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <span className="text-2xl">💬</span>
                What You Told Us
              </h2>
              <div className="space-y-3">
                {diagnostics.user_reflections.map((reflection, index) => (
                  <div key={index} className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      reflection.type === 'pain_point' ? 'bg-red-100 text-red-600' :
                      reflection.type === 'goal' ? 'bg-green-100 text-green-600' :
                      'bg-blue-100 text-blue-600'
                    }`}>
                      {reflection.type === 'pain_point' ? '🎯' :
                       reflection.type === 'goal' ? '🚀' : '💼'}
                    </div>
                    <div>
                      <p className="text-gray-800">{reflection.what_you_told_us}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        Source: {reflection.source.replace('_', ' ')}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Industry Context (Benchmarks) */}
          {diagnostics.industry_benchmarks.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-purple-50 rounded-2xl p-6 border border-purple-100 mb-8"
            >
              <h2 className="text-xl font-semibold text-purple-900 mb-4 flex items-center gap-2">
                <span className="text-2xl">📊</span>
                Industry Context
              </h2>
              <div className="space-y-4">
                {diagnostics.industry_benchmarks.map((benchmark, index) => (
                  <div key={index} className="bg-white rounded-xl p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h3 className="font-medium text-gray-900">{benchmark.metric}</h3>
                        <p className="text-2xl font-bold text-purple-600 mt-1">{benchmark.value}</p>
                        {benchmark.relevance && (
                          <p className="text-sm text-gray-600 mt-2">{benchmark.relevance}</p>
                        )}
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-gray-500">Source</p>
                        {benchmark.source.url ? (
                          <a
                            href={benchmark.source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-purple-600 hover:underline"
                          >
                            {benchmark.source.name}
                          </a>
                        ) : (
                          <p className="text-sm text-gray-700">{benchmark.source.name}</p>
                        )}
                        <p className="text-xs text-gray-400 mt-1">
                          Verified: {benchmark.source.verified_date}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* High-Potential Areas */}
          {opportunity_areas.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="bg-white rounded-2xl p-6 border border-gray-200 mb-8"
            >
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <span className="text-2xl">🎯</span>
                High-Potential Areas
              </h2>
              <p className="text-gray-600 mb-4">
                Based on what you shared, these areas show opportunity. The workshop will validate and prioritize.
              </p>
              <div className="space-y-4">
                {opportunity_areas.map((area, index) => (
                  <div key={index} className="border border-gray-100 rounded-xl p-4">
                    <div className="flex items-start justify-between gap-4 mb-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-gray-900">{area.label}</h3>
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            area.potential === 'high' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                          }`}>
                            {area.potential === 'high' ? 'High' : 'Medium'} Potential
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">{area.matched_because}</p>
                      </div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs font-medium text-gray-500 mb-2">Full report will reveal:</p>
                      <ul className="space-y-1">
                        {area.in_full_report.map((item, i) => (
                          <li key={i} className="text-sm text-gray-700 flex items-center gap-2">
                            <svg className="w-4 h-4 text-primary-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4" />
                            </svg>
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* What's Next: Workshop */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-2xl p-6 border border-amber-200 mb-8"
          >
            <h2 className="text-xl font-semibold text-amber-900 mb-4 flex items-center gap-2">
              <span className="text-2xl">🎓</span>
              What Happens Next: {next_steps.workshop.what_it_is}
            </h2>
            <p className="text-amber-800 mb-4">
              Duration: {next_steps.workshop.duration}
            </p>
            <div className="grid md:grid-cols-3 gap-4 mb-4">
              {next_steps.workshop.phases.map((phase, index) => (
                <div key={index} className="bg-white rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-6 h-6 bg-amber-100 rounded-full flex items-center justify-center text-amber-700 text-sm font-bold">
                      {index + 1}
                    </div>
                    <h3 className="font-semibold text-gray-900">{phase.name}</h3>
                  </div>
                  <p className="text-sm text-gray-600">{phase.description}</p>
                </div>
              ))}
            </div>
            <p className="text-amber-700 font-medium">
              Outcome: {next_steps.workshop.outcome}
            </p>
          </motion.div>

          {/* What's in the Full Report */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="bg-white rounded-2xl p-8 border border-gray-200 mb-8"
          >
            <h2 className="text-xl font-semibold text-gray-900 mb-6 text-center">
              What Your Full Report Includes
            </h2>
            <div className="grid md:grid-cols-2 gap-4">
              {next_steps.full_report_includes.map((item, i) => (
                <div key={i} className="flex items-start gap-3 p-4 bg-gray-50 rounded-xl">
                  <span className="text-2xl">{item.icon}</span>
                  <div>
                    <div className="font-medium text-gray-900">{item.title}</div>
                    <div className="text-sm text-gray-500">{item.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* CTA */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
            className="bg-white rounded-2xl p-8 border-2 border-primary-200 text-center"
          >
            <div className="text-4xl font-bold text-gray-900 mb-2">€147</div>
            <p className="text-gray-500 mb-6">Workshop + Full Personalized Report</p>

            <button
              onClick={handleGetFullReport}
              className="w-full max-w-md py-4 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition shadow-lg shadow-primary-600/25 text-lg"
            >
              Start Your Workshop →
            </button>

            <p className="text-sm text-gray-500 mt-4">
              14-day money-back guarantee if you're not satisfied
            </p>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
