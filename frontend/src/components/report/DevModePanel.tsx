/**
 * DevModePanel - Admin/Dev feedback and context panel
 *
 * Shows:
 * 1. Input context (quiz answers, research, interview transcript)
 * 2. Feedback form (rate findings, recommendations, note what's missing)
 *
 * Only visible in dev mode (?dev=true or NODE_ENV=development)
 * Part of Signal Loop (SIL) - learning from every analysis
 */

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8383'

interface Finding {
  id: string
  title: string
  description: string
  confidence: string
}

interface Recommendation {
  id: string
  title: string
  description: string
  priority: string
}

interface TokenUsage {
  total_input_tokens?: number
  total_output_tokens?: number
  total_tokens?: number
  estimated_cost_usd?: number
  by_model?: Record<string, {
    input: number
    output: number
    tasks: string[]
    estimated_cost_usd?: number
  }>
  task_count?: number
}

interface LLMCallTrace {
  task: string
  model: string
  prompt_preview: string
  prompt_tokens: number
  response_preview: string
  response_tokens: number
  duration_ms: number
  timestamp: string
}

interface KnowledgeRetrievalTrace {
  source: string
  query?: string
  results_count: number
  results_preview: string[]
  duration_ms: number
  timestamp: string
}

interface DecisionTrace {
  decision_type: string
  input_factors: Record<string, any>
  outcome: string
  reasoning: string
  timestamp: string
}

interface ValidationTrace {
  validation_type: string
  items_checked: number
  issues_found: number
  adjustments_made: string[]
  timestamp: string
}

interface PhaseTrace {
  phase_name: string
  started_at: string
  completed_at?: string
  duration_ms?: number
  steps: string[]
  llm_calls: LLMCallTrace[]
  knowledge_retrievals: KnowledgeRetrievalTrace[]
  decisions: DecisionTrace[]
  validations: ValidationTrace[]
  errors: string[]
  output_summary?: string
}

interface GenerationTrace {
  report_id: string
  session_id: string
  tier: string
  started_at: string
  completed_at?: string
  total_duration_ms?: number
  total_llm_calls: number
  total_tokens_used: number
  total_knowledge_retrievals: number
  total_decisions: number
  input_summary: Record<string, any>
  phases: PhaseTrace[]
  models_used: string[]
  knowledge_sources_used: string[]
}

interface ReportContext {
  session_id: string
  email?: string
  company_name?: string
  quiz_answers: Record<string, any>
  company_profile: Record<string, any>
  interview_data: Record<string, any>
  interview_transcript: Array<{ role: string; content: string }>
  research_data: Record<string, any>
  industry_knowledge: Record<string, any>
  confidence_scores: Record<string, any>
  tokens_used?: TokenUsage
  generation_trace?: GenerationTrace
  generation_started_at?: string
  generation_completed_at?: string
}

interface FindingFeedback {
  finding_id: string
  rating: 'excellent' | 'good' | 'okay' | 'poor' | 'wrong'
  notes?: string
}

interface RecommendationFeedback {
  recommendation_id: string
  rating: 'excellent' | 'good' | 'okay' | 'poor' | 'wrong'
  notes?: string
  best_option?: string
}

interface DevModePanelProps {
  reportId: string
  findings: Finding[]
  recommendations: Recommendation[]
  onFeedbackSubmitted?: () => void
}

export default function DevModePanel({
  reportId,
  findings,
  recommendations,
  onFeedbackSubmitted,
}: DevModePanelProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  const [activeSection, setActiveSection] = useState<'context' | 'feedback'>('context')

  // Context state
  const [context, setContext] = useState<ReportContext | null>(null)
  const [contextLoading, setContextLoading] = useState(false)
  const [contextError, setContextError] = useState<string | null>(null)

  // Feedback state
  const [overallQuality, setOverallQuality] = useState(7)
  const [accuracyScore, setAccuracyScore] = useState(7)
  const [actionabilityScore, setActionabilityScore] = useState(7)
  const [relevanceScore, setRelevanceScore] = useState(7)
  const [verdictAppropriate, setVerdictAppropriate] = useState(true)
  const [verdictNotes, setVerdictNotes] = useState('')
  const [findingsFeedback, setFindingsFeedback] = useState<FindingFeedback[]>([])
  const [recommendationsFeedback, setRecommendationsFeedback] = useState<RecommendationFeedback[]>([])
  const [missingFindings, setMissingFindings] = useState('')
  const [missingRecommendations, setMissingRecommendations] = useState('')
  const [generalNotes, setGeneralNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  // Load context on mount
  useEffect(() => {
    loadContext()
  }, [reportId])

  async function loadContext() {
    setContextLoading(true)
    setContextError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/api/dev/reports/${reportId}/context?dev=true`)
      if (!response.ok) throw new Error('Failed to load context')
      const data = await response.json()
      setContext(data)
    } catch (err: any) {
      setContextError(err.message || 'Failed to load context')
    } finally {
      setContextLoading(false)
    }
  }

  function updateFindingFeedback(findingId: string, rating: FindingFeedback['rating']) {
    setFindingsFeedback(prev => {
      const existing = prev.find(f => f.finding_id === findingId)
      if (existing) {
        return prev.map(f => f.finding_id === findingId ? { ...f, rating } : f)
      }
      return [...prev, { finding_id: findingId, rating }]
    })
  }

  function updateRecommendationFeedback(recId: string, rating: RecommendationFeedback['rating']) {
    setRecommendationsFeedback(prev => {
      const existing = prev.find(r => r.recommendation_id === recId)
      if (existing) {
        return prev.map(r => r.recommendation_id === recId ? { ...r, rating } : r)
      }
      return [...prev, { recommendation_id: recId, rating }]
    })
  }

  async function submitFeedback() {
    setSubmitting(true)

    try {
      const feedback = {
        report_id: reportId,
        session_id: context?.session_id,
        overall_quality: overallQuality,
        accuracy_score: accuracyScore,
        actionability_score: actionabilityScore,
        relevance_score: relevanceScore,
        verdict_appropriate: verdictAppropriate,
        verdict_notes: verdictNotes || null,
        findings_feedback: findingsFeedback,
        recommendations_feedback: recommendationsFeedback,
        missing_findings: missingFindings.split('\n').filter(Boolean),
        missing_recommendations: missingRecommendations.split('\n').filter(Boolean),
        general_notes: generalNotes || null,
      }

      const response = await fetch(`${API_BASE_URL}/api/dev/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(feedback),
      })

      if (!response.ok) throw new Error('Failed to submit feedback')

      setSubmitted(true)
      onFeedbackSubmitted?.()
    } catch (err) {
      console.error('Failed to submit feedback:', err)
      alert('Failed to submit feedback')
    } finally {
      setSubmitting(false)
    }
  }

  const ratingOptions: { value: FindingFeedback['rating']; label: string; color: string }[] = [
    { value: 'excellent', label: 'Excellent', color: 'bg-green-100 text-green-800 border-green-300' },
    { value: 'good', label: 'Good', color: 'bg-blue-100 text-blue-800 border-blue-300' },
    { value: 'okay', label: 'Okay', color: 'bg-yellow-100 text-yellow-800 border-yellow-300' },
    { value: 'poor', label: 'Poor', color: 'bg-orange-100 text-orange-800 border-orange-300' },
    { value: 'wrong', label: 'Wrong', color: 'bg-red-100 text-red-800 border-red-300' },
  ]

  return (
    <div className="mt-8 border-t-4 border-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 rounded-b-xl">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-6 py-4 flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">🛠️</span>
          <div>
            <h3 className="font-bold text-yellow-800 dark:text-yellow-200">Dev Mode Panel</h3>
            <p className="text-sm text-yellow-600 dark:text-yellow-400">
              View inputs & provide feedback for Signal Loop
            </p>
          </div>
        </div>
        <motion.svg
          animate={{ rotate: isExpanded ? 180 : 0 }}
          className="w-6 h-6 text-yellow-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </motion.svg>
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="px-6 pb-6">
              {/* Section Tabs */}
              <div className="flex gap-2 mb-4">
                <button
                  onClick={() => setActiveSection('context')}
                  className={`px-4 py-2 rounded-lg font-medium text-sm transition ${
                    activeSection === 'context'
                      ? 'bg-yellow-500 text-white'
                      : 'bg-white text-yellow-700 hover:bg-yellow-100'
                  }`}
                >
                  📋 Input Context
                </button>
                <button
                  onClick={() => setActiveSection('feedback')}
                  className={`px-4 py-2 rounded-lg font-medium text-sm transition ${
                    activeSection === 'feedback'
                      ? 'bg-yellow-500 text-white'
                      : 'bg-white text-yellow-700 hover:bg-yellow-100'
                  }`}
                >
                  ✏️ Provide Feedback
                </button>
              </div>

              {/* Context Section */}
              {activeSection === 'context' && (
                <div className="space-y-4">
                  {contextLoading && (
                    <div className="text-center py-8">
                      <div className="w-8 h-8 border-2 border-yellow-500 border-t-transparent rounded-full animate-spin mx-auto" />
                      <p className="text-sm text-yellow-600 mt-2">Loading context...</p>
                    </div>
                  )}

                  {contextError && (
                    <div className="bg-red-100 text-red-700 p-4 rounded-lg">
                      {contextError}
                    </div>
                  )}

                  {context && (
                    <>
                      {/* Session Info */}
                      <div className="bg-white rounded-lg p-4 shadow-sm">
                        <h4 className="font-semibold text-gray-900 mb-2">Session Info</h4>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div><span className="text-gray-500">Company:</span> {context.company_name || 'N/A'}</div>
                          <div><span className="text-gray-500">Email:</span> {context.email || 'N/A'}</div>
                          <div><span className="text-gray-500">Session ID:</span> <code className="text-xs">{context.session_id}</code></div>
                          <div><span className="text-gray-500">Generated:</span> {context.generation_completed_at ? new Date(context.generation_completed_at).toLocaleString() : 'N/A'}</div>
                        </div>
                      </div>

                      {/* Token Usage & Cost */}
                      {context.tokens_used && (
                        <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-4 shadow-sm border border-green-200">
                          <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                            <span>💰</span> Generation Cost
                          </h4>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                            <div className="bg-white rounded-lg p-3 text-center">
                              <div className="text-2xl font-bold text-green-600">
                                €{((context.tokens_used.estimated_cost_usd || 0) * 0.92).toFixed(3)}
                              </div>
                              <div className="text-xs text-gray-500">Total Cost (EUR)</div>
                            </div>
                            <div className="bg-white rounded-lg p-3 text-center">
                              <div className="text-xl font-semibold text-gray-700">
                                {(context.tokens_used.total_tokens || 0).toLocaleString()}
                              </div>
                              <div className="text-xs text-gray-500">Total Tokens</div>
                            </div>
                            <div className="bg-white rounded-lg p-3 text-center">
                              <div className="text-xl font-semibold text-blue-600">
                                {(context.tokens_used.total_input_tokens || 0).toLocaleString()}
                              </div>
                              <div className="text-xs text-gray-500">Input Tokens</div>
                            </div>
                            <div className="bg-white rounded-lg p-3 text-center">
                              <div className="text-xl font-semibold text-purple-600">
                                {(context.tokens_used.total_output_tokens || 0).toLocaleString()}
                              </div>
                              <div className="text-xs text-gray-500">Output Tokens</div>
                            </div>
                          </div>

                          {/* Cost breakdown by model */}
                          {context.tokens_used.by_model && Object.keys(context.tokens_used.by_model).length > 0 && (
                            <div className="border-t border-green-200 pt-3">
                              <h5 className="text-sm font-medium text-gray-700 mb-2">Cost by Model</h5>
                              <div className="space-y-2">
                                {Object.entries(context.tokens_used.by_model).map(([model, data]) => (
                                  <div key={model} className="flex items-center justify-between bg-white rounded px-3 py-2 text-sm">
                                    <div className="flex-1 min-w-0">
                                      <code className="text-xs text-gray-600 truncate block">{model}</code>
                                      <span className="text-xs text-gray-400">{data.tasks?.length || 0} tasks</span>
                                    </div>
                                    <div className="text-right">
                                      <span className="font-medium text-green-600">
                                        €{((data.estimated_cost_usd || 0) * 0.92).toFixed(3)}
                                      </span>
                                      <div className="text-xs text-gray-400">
                                        {(data.input + data.output).toLocaleString()} tokens
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Quiz Answers */}
                      <CollapsibleSection title="Quiz Answers" defaultOpen>
                        <pre className="text-xs bg-gray-100 p-3 rounded overflow-auto max-h-64">
                          {JSON.stringify(context.quiz_answers, null, 2)}
                        </pre>
                      </CollapsibleSection>

                      {/* Company Profile */}
                      <CollapsibleSection title="Company Profile">
                        <pre className="text-xs bg-gray-100 p-3 rounded overflow-auto max-h-64">
                          {JSON.stringify(context.company_profile, null, 2)}
                        </pre>
                      </CollapsibleSection>

                      {/* Interview Transcript */}
                      <CollapsibleSection title={`Interview Transcript (${context.interview_transcript?.length || 0} messages)`}>
                        <div className="space-y-2 max-h-96 overflow-auto">
                          {context.interview_transcript?.map((msg, i) => (
                            <div
                              key={i}
                              className={`p-3 rounded-lg text-sm ${
                                msg.role === 'assistant'
                                  ? 'bg-blue-50 border-l-4 border-blue-400'
                                  : 'bg-gray-50 border-l-4 border-gray-400'
                              }`}
                            >
                              <span className="font-medium text-xs uppercase text-gray-500">{msg.role}</span>
                              <p className="mt-1 whitespace-pre-wrap">{msg.content}</p>
                            </div>
                          ))}
                          {(!context.interview_transcript || context.interview_transcript.length === 0) && (
                            <p className="text-gray-500 text-sm italic">No interview transcript available</p>
                          )}
                        </div>
                      </CollapsibleSection>

                      {/* Interview Data / Confidence */}
                      <CollapsibleSection title="Interview Confidence Scores">
                        <pre className="text-xs bg-gray-100 p-3 rounded overflow-auto max-h-64">
                          {JSON.stringify(context.confidence_scores, null, 2)}
                        </pre>
                      </CollapsibleSection>

                      {/* Research Data */}
                      <CollapsibleSection title="Research Data">
                        <pre className="text-xs bg-gray-100 p-3 rounded overflow-auto max-h-64">
                          {JSON.stringify(context.research_data, null, 2)}
                        </pre>
                      </CollapsibleSection>

                      {/* Industry Knowledge Retrieved */}
                      <CollapsibleSection title="Industry Knowledge (Semantic Retrieval)">
                        <pre className="text-xs bg-gray-100 p-3 rounded overflow-auto max-h-64">
                          {JSON.stringify(context.industry_knowledge, null, 2)}
                        </pre>
                      </CollapsibleSection>

                      {/* Generation Trace - Reasoning & Logic */}
                      {context.generation_trace && (
                        <CollapsibleSection
                          title={`Generation Trace (${context.generation_trace.total_llm_calls || 0} LLM calls, ${context.generation_trace.phases?.length || 0} phases)`}
                          defaultOpen
                        >
                          <div className="space-y-4">
                            {/* Trace Summary */}
                            <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg p-4 border border-purple-200">
                              <h5 className="font-semibold text-purple-900 mb-3 flex items-center gap-2">
                                <span>🔍</span> Generation Summary
                              </h5>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                                <div className="bg-white rounded p-2 text-center">
                                  <div className="text-xl font-bold text-purple-600">
                                    {context.generation_trace.total_llm_calls}
                                  </div>
                                  <div className="text-xs text-gray-500">LLM Calls</div>
                                </div>
                                <div className="bg-white rounded p-2 text-center">
                                  <div className="text-xl font-bold text-indigo-600">
                                    {context.generation_trace.total_tokens_used?.toLocaleString()}
                                  </div>
                                  <div className="text-xs text-gray-500">Tokens Used</div>
                                </div>
                                <div className="bg-white rounded p-2 text-center">
                                  <div className="text-xl font-bold text-blue-600">
                                    {context.generation_trace.total_knowledge_retrievals}
                                  </div>
                                  <div className="text-xs text-gray-500">KB Retrievals</div>
                                </div>
                                <div className="bg-white rounded p-2 text-center">
                                  <div className="text-xl font-bold text-green-600">
                                    {context.generation_trace.total_decisions}
                                  </div>
                                  <div className="text-xs text-gray-500">Decisions</div>
                                </div>
                              </div>
                              <div className="mt-3 text-xs text-gray-600">
                                <strong>Duration:</strong> {((context.generation_trace.total_duration_ms || 0) / 1000).toFixed(1)}s |
                                <strong className="ml-2">Models:</strong> {context.generation_trace.models_used?.join(', ') || 'N/A'} |
                                <strong className="ml-2">KB Sources:</strong> {context.generation_trace.knowledge_sources_used?.join(', ') || 'N/A'}
                              </div>
                            </div>

                            {/* Input Summary */}
                            {context.generation_trace.input_summary && (
                              <div className="bg-gray-50 rounded-lg p-3 border">
                                <h6 className="text-xs font-semibold text-gray-700 mb-2">Input Summary</h6>
                                <div className="grid grid-cols-2 gap-2 text-xs">
                                  <div><span className="text-gray-500">Company:</span> {context.generation_trace.input_summary.company_name}</div>
                                  <div><span className="text-gray-500">Industry:</span> {context.generation_trace.input_summary.industry}</div>
                                  <div><span className="text-gray-500">Quiz Answers:</span> {context.generation_trace.input_summary.quiz_answers_count}</div>
                                  <div><span className="text-gray-500">Interview Messages:</span> {context.generation_trace.input_summary.interview_messages}</div>
                                </div>
                              </div>
                            )}

                            {/* Phases Timeline */}
                            <div className="space-y-3">
                              <h6 className="text-sm font-semibold text-gray-700">Generation Phases</h6>
                              {context.generation_trace.phases?.map((phase, phaseIdx) => (
                                <div key={phaseIdx} className="border rounded-lg overflow-hidden">
                                  <div className="bg-gray-100 px-3 py-2 flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                      <span className={`w-2 h-2 rounded-full ${phase.errors?.length ? 'bg-red-500' : 'bg-green-500'}`} />
                                      <span className="font-medium text-sm">{phase.phase_name}</span>
                                      {phase.output_summary && (
                                        <span className="text-xs text-gray-500">- {phase.output_summary}</span>
                                      )}
                                    </div>
                                    <span className="text-xs text-gray-500">
                                      {phase.duration_ms ? `${(phase.duration_ms / 1000).toFixed(1)}s` : 'N/A'}
                                    </span>
                                  </div>

                                  <div className="p-3 space-y-2 text-xs">
                                    {/* LLM Calls */}
                                    {phase.llm_calls?.length > 0 && (
                                      <div className="space-y-1">
                                        <span className="font-medium text-blue-700">LLM Calls ({phase.llm_calls.length}):</span>
                                        {phase.llm_calls.map((call, callIdx) => (
                                          <div key={callIdx} className="ml-3 bg-blue-50 rounded p-2 border-l-2 border-blue-300">
                                            <div className="flex justify-between">
                                              <span className="font-medium">{call.task}</span>
                                              <span className="text-gray-500">{call.duration_ms.toFixed(0)}ms | {call.prompt_tokens + call.response_tokens} tokens</span>
                                            </div>
                                            <div className="text-gray-600 mt-1">
                                              <code className="text-xs">{call.model}</code>
                                            </div>
                                            <details className="mt-1">
                                              <summary className="cursor-pointer text-blue-600 hover:text-blue-800">Show prompt/response preview</summary>
                                              <div className="mt-2 space-y-2">
                                                <div className="bg-white rounded p-2">
                                                  <div className="font-medium text-gray-700 mb-1">Prompt:</div>
                                                  <pre className="whitespace-pre-wrap text-xs text-gray-600 max-h-32 overflow-auto">{call.prompt_preview}</pre>
                                                </div>
                                                <div className="bg-white rounded p-2">
                                                  <div className="font-medium text-gray-700 mb-1">Response:</div>
                                                  <pre className="whitespace-pre-wrap text-xs text-gray-600 max-h-32 overflow-auto">{call.response_preview}</pre>
                                                </div>
                                              </div>
                                            </details>
                                          </div>
                                        ))}
                                      </div>
                                    )}

                                    {/* Knowledge Retrievals */}
                                    {phase.knowledge_retrievals?.length > 0 && (
                                      <div className="space-y-1">
                                        <span className="font-medium text-green-700">Knowledge Retrievals ({phase.knowledge_retrievals.length}):</span>
                                        {phase.knowledge_retrievals.map((retrieval, retIdx) => (
                                          <div key={retIdx} className="ml-3 bg-green-50 rounded p-2 border-l-2 border-green-300">
                                            <div className="flex justify-between">
                                              <span className="font-medium">{retrieval.source}</span>
                                              <span className="text-gray-500">{retrieval.results_count} results</span>
                                            </div>
                                            {retrieval.query && (
                                              <div className="text-gray-600 truncate">Query: {retrieval.query}</div>
                                            )}
                                            <div className="text-gray-500 mt-1">
                                              Preview: {retrieval.results_preview?.join(', ') || 'N/A'}
                                            </div>
                                          </div>
                                        ))}
                                      </div>
                                    )}

                                    {/* Decisions */}
                                    {phase.decisions?.length > 0 && (
                                      <div className="space-y-1">
                                        <span className="font-medium text-amber-700">Decisions ({phase.decisions.length}):</span>
                                        {phase.decisions.map((decision, decIdx) => (
                                          <div key={decIdx} className="ml-3 bg-amber-50 rounded p-2 border-l-2 border-amber-300">
                                            <div className="font-medium">{decision.decision_type}</div>
                                            <div className="text-gray-700">
                                              <span className="font-medium">Outcome:</span> {decision.outcome}
                                            </div>
                                            <div className="text-gray-600">
                                              <span className="font-medium">Reasoning:</span> {decision.reasoning}
                                            </div>
                                            {Object.keys(decision.input_factors || {}).length > 0 && (
                                              <details className="mt-1">
                                                <summary className="cursor-pointer text-amber-600 hover:text-amber-800">Input factors</summary>
                                                <pre className="text-xs text-gray-600 mt-1">{JSON.stringify(decision.input_factors, null, 2)}</pre>
                                              </details>
                                            )}
                                          </div>
                                        ))}
                                      </div>
                                    )}

                                    {/* Validations */}
                                    {phase.validations?.length > 0 && (
                                      <div className="space-y-1">
                                        <span className="font-medium text-indigo-700">Validations ({phase.validations.length}):</span>
                                        {phase.validations.map((validation, valIdx) => (
                                          <div key={valIdx} className="ml-3 bg-indigo-50 rounded p-2 border-l-2 border-indigo-300">
                                            <div className="font-medium">{validation.validation_type}</div>
                                            <div className="text-gray-600">
                                              Checked: {validation.items_checked} |
                                              Issues: <span className={validation.issues_found > 0 ? 'text-red-600' : 'text-green-600'}>{validation.issues_found}</span>
                                            </div>
                                            {validation.adjustments_made?.length > 0 && (
                                              <div className="text-gray-500">Adjustments: {validation.adjustments_made.join(', ')}</div>
                                            )}
                                          </div>
                                        ))}
                                      </div>
                                    )}

                                    {/* Errors */}
                                    {phase.errors?.length > 0 && (
                                      <div className="space-y-1">
                                        <span className="font-medium text-red-700">Errors ({phase.errors.length}):</span>
                                        {phase.errors.map((error, errIdx) => (
                                          <div key={errIdx} className="ml-3 bg-red-50 rounded p-2 border-l-2 border-red-300 text-red-700">
                                            {error}
                                          </div>
                                        ))}
                                      </div>
                                    )}

                                    {/* Empty phase indicator */}
                                    {!phase.llm_calls?.length && !phase.knowledge_retrievals?.length && !phase.decisions?.length && !phase.validations?.length && !phase.errors?.length && (
                                      <div className="text-gray-400 italic">No detailed trace data for this phase</div>
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </CollapsibleSection>
                      )}
                    </>
                  )}
                </div>
              )}

              {/* Feedback Section */}
              {activeSection === 'feedback' && (
                <div className="space-y-6">
                  {submitted ? (
                    <div className="text-center py-8 bg-green-100 rounded-lg">
                      <span className="text-4xl mb-2 block">✅</span>
                      <h4 className="text-lg font-semibold text-green-800">Feedback Submitted!</h4>
                      <p className="text-green-600 text-sm">This will improve future analyses via the Signal Loop.</p>
                    </div>
                  ) : (
                    <>
                      {/* Overall Scores */}
                      <div className="bg-white rounded-lg p-4 shadow-sm">
                        <h4 className="font-semibold text-gray-900 mb-4">Overall Scores (1-10)</h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <ScoreInput label="Overall Quality" value={overallQuality} onChange={setOverallQuality} />
                          <ScoreInput label="Accuracy" value={accuracyScore} onChange={setAccuracyScore} />
                          <ScoreInput label="Actionability" value={actionabilityScore} onChange={setActionabilityScore} />
                          <ScoreInput label="Relevance" value={relevanceScore} onChange={setRelevanceScore} />
                        </div>
                      </div>

                      {/* Verdict Feedback */}
                      <div className="bg-white rounded-lg p-4 shadow-sm">
                        <h4 className="font-semibold text-gray-900 mb-3">Verdict Assessment</h4>
                        <label className="flex items-center gap-2 mb-3">
                          <input
                            type="checkbox"
                            checked={verdictAppropriate}
                            onChange={(e) => setVerdictAppropriate(e.target.checked)}
                            className="w-4 h-4 rounded border-gray-300"
                          />
                          <span className="text-sm">Verdict is appropriate for this business</span>
                        </label>
                        <textarea
                          value={verdictNotes}
                          onChange={(e) => setVerdictNotes(e.target.value)}
                          placeholder="Notes about the verdict..."
                          className="w-full p-2 border rounded-lg text-sm"
                          rows={2}
                        />
                      </div>

                      {/* Findings Feedback */}
                      <div className="bg-white rounded-lg p-4 shadow-sm">
                        <h4 className="font-semibold text-gray-900 mb-3">Rate Findings</h4>
                        <div className="space-y-3 max-h-64 overflow-auto">
                          {findings.map((finding) => {
                            const feedback = findingsFeedback.find(f => f.finding_id === finding.id)
                            return (
                              <div key={finding.id} className="flex items-center gap-3 p-2 bg-gray-50 rounded">
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm font-medium text-gray-900 truncate">{finding.title}</p>
                                  <p className="text-xs text-gray-500">{finding.confidence} confidence</p>
                                </div>
                                <div className="flex gap-1">
                                  {ratingOptions.map(opt => (
                                    <button
                                      key={opt.value}
                                      onClick={() => updateFindingFeedback(finding.id, opt.value)}
                                      className={`px-2 py-1 text-xs rounded border transition ${
                                        feedback?.rating === opt.value
                                          ? opt.color + ' ring-2 ring-offset-1 ring-gray-400'
                                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                      }`}
                                      title={opt.label}
                                    >
                                      {opt.label.charAt(0)}
                                    </button>
                                  ))}
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      </div>

                      {/* Recommendations Feedback */}
                      <div className="bg-white rounded-lg p-4 shadow-sm">
                        <h4 className="font-semibold text-gray-900 mb-3">Rate Recommendations</h4>
                        <div className="space-y-3 max-h-64 overflow-auto">
                          {recommendations.map((rec) => {
                            const feedback = recommendationsFeedback.find(r => r.recommendation_id === rec.id)
                            return (
                              <div key={rec.id} className="flex items-center gap-3 p-2 bg-gray-50 rounded">
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm font-medium text-gray-900 truncate">{rec.title}</p>
                                  <p className="text-xs text-gray-500">{rec.priority} priority</p>
                                </div>
                                <div className="flex gap-1">
                                  {ratingOptions.map(opt => (
                                    <button
                                      key={opt.value}
                                      onClick={() => updateRecommendationFeedback(rec.id, opt.value)}
                                      className={`px-2 py-1 text-xs rounded border transition ${
                                        feedback?.rating === opt.value
                                          ? opt.color + ' ring-2 ring-offset-1 ring-gray-400'
                                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                      }`}
                                      title={opt.label}
                                    >
                                      {opt.label.charAt(0)}
                                    </button>
                                  ))}
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      </div>

                      {/* What's Missing */}
                      <div className="bg-white rounded-lg p-4 shadow-sm">
                        <h4 className="font-semibold text-gray-900 mb-3">What's Missing?</h4>
                        <div className="grid md:grid-cols-2 gap-4">
                          <div>
                            <label className="text-sm text-gray-600 block mb-1">Missing Findings (one per line)</label>
                            <textarea
                              value={missingFindings}
                              onChange={(e) => setMissingFindings(e.target.value)}
                              placeholder="Pain points we should have found..."
                              className="w-full p-2 border rounded-lg text-sm"
                              rows={3}
                            />
                          </div>
                          <div>
                            <label className="text-sm text-gray-600 block mb-1">Missing Recommendations (one per line)</label>
                            <textarea
                              value={missingRecommendations}
                              onChange={(e) => setMissingRecommendations(e.target.value)}
                              placeholder="Solutions we should have suggested..."
                              className="w-full p-2 border rounded-lg text-sm"
                              rows={3}
                            />
                          </div>
                        </div>
                      </div>

                      {/* General Notes */}
                      <div className="bg-white rounded-lg p-4 shadow-sm">
                        <h4 className="font-semibold text-gray-900 mb-3">General Notes</h4>
                        <textarea
                          value={generalNotes}
                          onChange={(e) => setGeneralNotes(e.target.value)}
                          placeholder="Any other observations, patterns to add, anti-patterns to note..."
                          className="w-full p-2 border rounded-lg text-sm"
                          rows={4}
                        />
                      </div>

                      {/* Submit Button */}
                      <button
                        onClick={submitFeedback}
                        disabled={submitting}
                        className="w-full py-3 bg-yellow-500 hover:bg-yellow-600 text-white font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {submitting ? 'Submitting...' : 'Submit Feedback to Signal Loop'}
                      </button>
                    </>
                  )}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// Helper Components

function CollapsibleSection({
  title,
  children,
  defaultOpen = false,
}: {
  title: string
  children: React.ReactNode
  defaultOpen?: boolean
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-50"
      >
        <span className="font-medium text-gray-900">{title}</span>
        <motion.svg
          animate={{ rotate: isOpen ? 180 : 0 }}
          className="w-5 h-5 text-gray-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </motion.svg>
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function ScoreInput({
  label,
  value,
  onChange,
}: {
  label: string
  value: number
  onChange: (v: number) => void
}) {
  return (
    <div>
      <label className="text-sm text-gray-600 block mb-1">{label}</label>
      <div className="flex items-center gap-2">
        <input
          type="range"
          min={1}
          max={10}
          value={value}
          onChange={(e) => onChange(parseInt(e.target.value))}
          className="flex-1"
        />
        <span className={`w-8 text-center font-bold ${
          value >= 8 ? 'text-green-600' :
          value >= 5 ? 'text-yellow-600' :
          'text-red-600'
        }`}>
          {value}
        </span>
      </div>
    </div>
  )
}
