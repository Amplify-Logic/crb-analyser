import { useState, useEffect, useRef, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8383'

// ============================================================================
// Types
// ============================================================================

interface ResearchFinding {
  field: string
  value: string | number | string[]
  confidence: 'high' | 'medium' | 'low'
  source?: string
}

interface DynamicQuestion {
  id: string
  question: string
  type: 'text' | 'textarea' | 'select' | 'multiselect' | 'yes_no' | 'number'
  purpose: 'confirm' | 'clarify' | 'discover' | 'deep_dive'
  rationale: string
  prefilled_value?: string | string[]
  options?: { value: string; label: string }[]
  required: boolean
  section: string
  priority: number
}

interface ResearchResult {
  company_profile: {
    basics?: {
      name?: { value: string; confidence: string }
      description?: { value: string; confidence: string }
      founded_year?: { value: string; confidence: string }
      headquarters?: { value: string; confidence: string }
    }
    size?: {
      employee_count?: { value: number; confidence: string }
      employee_range?: { value: string; confidence: string }
      revenue_estimate?: { value: string; confidence: string }
      funding_raised?: { value: string; confidence: string }
    }
    industry?: {
      primary_industry?: { value: string; confidence: string }
      business_model?: { value: string; confidence: string }
      target_market?: { value: string; confidence: string }
    }
    products?: {
      main_products?: Array<{ value: string; confidence: string }>
      services?: Array<{ value: string; confidence: string }>
      pricing_model?: { value: string; confidence: string }
    }
    tech_stack?: {
      technologies_detected?: Array<{ value: string; confidence: string }>
      platforms_used?: Array<{ value: string; confidence: string }>
    }
    research_quality_score?: number
    sources_used?: string[]
  }
  questionnaire: {
    research_summary: string
    confirmed_facts: Array<{ fact: string; confidence: string }>
    questions: DynamicQuestion[]
    sections: Array<{ id: number; title: string; description: string; question_ids: string[] }>
    total_questions: number
    estimated_time_minutes: number
  }
}

type QuizPhase = 'website' | 'researching' | 'findings' | 'questions' | 'complete'

// ============================================================================
// Component
// ============================================================================

export default function Quiz() {
  const navigate = useNavigate()
  const eventSourceRef = useRef<EventSource | null>(null)

  // Core state
  const [phase, setPhase] = useState<QuizPhase>('website')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [websiteUrl, setWebsiteUrl] = useState('')
  const [companyName, setCompanyName] = useState('')

  // Research state
  const [researchProgress, setResearchProgress] = useState(0)
  const [researchStep, setResearchStep] = useState('')
  const [researchResult, setResearchResult] = useState<ResearchResult | null>(null)
  const [researchError, setResearchError] = useState<string | null>(null)

  // Extracted findings for display
  const [findings, setFindings] = useState<ResearchFinding[]>([])
  const [gaps, setGaps] = useState<string[]>([])

  // Questions state
  const [questions, setQuestions] = useState<DynamicQuestion[]>([])
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({})

  // Knowledge completeness
  const [knowledgeScore, setKnowledgeScore] = useState(0)

  // ============================================================================
  // Helper Functions (defined before useEffect that uses them)
  // ============================================================================

  const extractFindingsFromProfile = useCallback((profile: ResearchResult['company_profile']) => {
    const extracted: ResearchFinding[] = []
    const missingFields: string[] = []

    // Extract basics
    if (profile.basics?.description?.value) {
      extracted.push({
        field: 'Company Description',
        value: profile.basics.description.value,
        confidence: profile.basics.description.confidence as 'high' | 'medium' | 'low',
      })
    } else {
      missingFields.push('Company description')
    }

    if (profile.basics?.founded_year?.value) {
      extracted.push({
        field: 'Founded',
        value: profile.basics.founded_year.value,
        confidence: profile.basics.founded_year.confidence as 'high' | 'medium' | 'low',
      })
    }

    if (profile.basics?.headquarters?.value) {
      extracted.push({
        field: 'Headquarters',
        value: profile.basics.headquarters.value,
        confidence: profile.basics.headquarters.confidence as 'high' | 'medium' | 'low',
      })
    }

    // Extract size
    if (profile.size?.employee_range?.value) {
      extracted.push({
        field: 'Team Size',
        value: profile.size.employee_range.value,
        confidence: profile.size.employee_range.confidence as 'high' | 'medium' | 'low',
      })
    } else {
      missingFields.push('Team size')
    }

    if (profile.size?.revenue_estimate?.value) {
      extracted.push({
        field: 'Revenue',
        value: profile.size.revenue_estimate.value,
        confidence: profile.size.revenue_estimate.confidence as 'high' | 'medium' | 'low',
      })
    } else {
      missingFields.push('Revenue information')
    }

    if (profile.size?.funding_raised?.value) {
      extracted.push({
        field: 'Funding',
        value: profile.size.funding_raised.value,
        confidence: profile.size.funding_raised.confidence as 'high' | 'medium' | 'low',
      })
    }

    // Extract industry
    if (profile.industry?.primary_industry?.value) {
      extracted.push({
        field: 'Industry',
        value: profile.industry.primary_industry.value,
        confidence: profile.industry.primary_industry.confidence as 'high' | 'medium' | 'low',
      })
    } else {
      missingFields.push('Industry classification')
    }

    if (profile.industry?.business_model?.value) {
      extracted.push({
        field: 'Business Model',
        value: profile.industry.business_model.value,
        confidence: profile.industry.business_model.confidence as 'high' | 'medium' | 'low',
      })
    } else {
      missingFields.push('Business model')
    }

    // Extract products/services
    if (profile.products?.main_products && profile.products.main_products.length > 0) {
      extracted.push({
        field: 'Products/Services',
        value: profile.products.main_products.map(p => p.value).join(', '),
        confidence: profile.products.main_products[0].confidence as 'high' | 'medium' | 'low',
      })
    } else {
      missingFields.push('Products and services')
    }

    // Extract tech stack
    if (profile.tech_stack?.technologies_detected && profile.tech_stack.technologies_detected.length > 0) {
      extracted.push({
        field: 'Technology Stack',
        value: profile.tech_stack.technologies_detected.map(t => t.value).join(', '),
        confidence: profile.tech_stack.technologies_detected[0].confidence as 'high' | 'medium' | 'low',
      })
    } else {
      missingFields.push('Technology stack')
    }

    // Always need these for a good report
    missingFields.push('Current pain points and challenges')
    missingFields.push('AI/automation experience')
    missingFields.push('Budget and timeline expectations')
    missingFields.push('Success criteria')

    setFindings(extracted)
    setGaps(missingFields)

    // Calculate knowledge score
    const score = Math.min(100, Math.round((extracted.length / 12) * 100))
    setKnowledgeScore(score)
  }, [])

  // ============================================================================
  // Session Management
  // ============================================================================

  useEffect(() => {
    const initSession = async () => {
      try {
        // Check if user wants a fresh start
        const urlParams = new URLSearchParams(window.location.search)
        const forceNew = urlParams.get('new') === 'true'

        if (forceNew) {
          // Clear all previous session data
          localStorage.removeItem('crb_session_id')
          sessionStorage.removeItem('quizSessionId')
          sessionStorage.removeItem('quizAnswers')
          sessionStorage.removeItem('researchFindings')
          sessionStorage.removeItem('companyProfile')
          sessionStorage.removeItem('knowledgeScore')
          // Clean up URL
          window.history.replaceState({}, '', '/quiz')
        }

        // Check for existing session
        const savedSession = localStorage.getItem('crb_session_id')
        if (savedSession && !forceNew) {
          // Verify the session still exists
          const checkResponse = await fetch(`${API_BASE_URL}/api/quiz/sessions/${savedSession}/research/status`)
          if (checkResponse.ok) {
            const data = await checkResponse.json()
            setSessionId(savedSession)

            if (data.status === 'complete' && data.dynamic_questionnaire) {
              // Resume from findings phase
              setCompanyName(data.company_name || '')
              setWebsiteUrl(data.company_website || '')
              setResearchResult({
                company_profile: data.company_profile || {},
                questionnaire: data.dynamic_questionnaire,
              })
              extractFindingsFromProfile(data.company_profile || {})
              setQuestions(data.dynamic_questionnaire.questions || [])
              setPhase('findings')
            }
            return
          } else {
            // Session no longer valid, clear it
            localStorage.removeItem('crb_session_id')
          }
        }

        // Create new session with temporary email
        const tempEmail = `quiz_${Date.now()}@example.com`
        const response = await fetch(`${API_BASE_URL}/api/quiz/sessions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: tempEmail, tier: 'full' }),
        })

        if (response.ok) {
          const data = await response.json()
          setSessionId(data.session_id)
          localStorage.setItem('crb_session_id', data.session_id)
        } else {
          console.error('Failed to create session:', await response.text())
        }
      } catch (error) {
        console.error('Session init error:', error)
        // Clear bad session data
        localStorage.removeItem('crb_session_id')
      }
    }

    initSession()
  }, [])

  // ============================================================================
  // Research Functions
  // ============================================================================

  const startResearch = useCallback(async () => {
    if (!sessionId || !websiteUrl) return

    setPhase('researching')
    setResearchProgress(0)
    setResearchStep('Initializing research...')
    setResearchError(null)

    try {
      // Normalize URL
      let normalizedUrl = websiteUrl.trim()
      if (!normalizedUrl.startsWith('http')) {
        normalizedUrl = `https://${normalizedUrl}`
      }

      // Start research
      const response = await fetch(`${API_BASE_URL}/api/quiz/sessions/${sessionId}/research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ website_url: normalizedUrl }),
      })

      if (!response.ok) {
        throw new Error('Failed to start research')
      }

      const data = await response.json()
      setCompanyName(data.company_name || '')

      // Connect to SSE stream
      const eventSource = new EventSource(
        `${API_BASE_URL}/api/quiz/sessions/${sessionId}/research/stream`
      )
      eventSourceRef.current = eventSource

      eventSource.onmessage = async (event) => {
        try {
          const update = JSON.parse(event.data)

          setResearchProgress(update.progress || 0)
          setResearchStep(update.step || '')

          if (update.status === 'ready' && update.result) {
            eventSource.close()
            eventSourceRef.current = null

            // Save results
            await fetch(`${API_BASE_URL}/api/quiz/sessions/${sessionId}/research/save`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(update.result),
            })

            setResearchResult(update.result)
            extractFindingsFromProfile(update.result.company_profile || {})

            // Set up dynamic questions
            if (update.result.questionnaire?.questions) {
              setQuestions(update.result.questionnaire.questions)
            }

            setPhase('findings')
          }

          if (update.status === 'failed') {
            eventSource.close()
            eventSourceRef.current = null
            setResearchError(update.error || 'Research failed')
          }
        } catch (e) {
          console.error('Parse error:', e)
        }
      }

      eventSource.onerror = () => {
        eventSource.close()
        eventSourceRef.current = null
        if (researchProgress < 100) {
          setResearchError('Connection lost during research')
        }
      }
    } catch (error) {
      console.error('Research error:', error)
      setResearchError('Failed to start research. Please try again.')
    }
  }, [sessionId, websiteUrl, extractFindingsFromProfile, researchProgress])

  // Cleanup
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  // ============================================================================
  // Question Handling
  // ============================================================================

  const currentQuestion = questions[currentQuestionIndex]

  const handleAnswer = (value: string | string[]) => {
    if (!currentQuestion) return
    setAnswers(prev => ({ ...prev, [currentQuestion.id]: value }))
  }

  const getCurrentAnswer = (): string | string[] => {
    if (!currentQuestion) return ''
    return answers[currentQuestion.id] || (currentQuestion.type === 'multiselect' ? [] : '')
  }

  const canProceed = () => {
    const current = getCurrentAnswer()
    if (!currentQuestion) return false
    if (!currentQuestion.required) return true
    if (currentQuestion.type === 'multiselect') return (current as string[]).length > 0
    return current !== ''
  }

  const handleNextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1)
    } else {
      // All questions answered
      finishQuiz()
    }
  }

  const handlePrevQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1)
    }
  }

  const finishQuiz = () => {
    // Calculate final knowledge score
    const researchScore = findings.length * 8
    const questionScore = Object.keys(answers).length * 5
    const finalScore = Math.min(100, researchScore + questionScore)
    setKnowledgeScore(finalScore)

    // Save to session storage for checkout
    sessionStorage.setItem('quizSessionId', sessionId || '')
    sessionStorage.setItem('quizAnswers', JSON.stringify(answers))
    sessionStorage.setItem('researchFindings', JSON.stringify(findings))
    sessionStorage.setItem('knowledgeScore', String(finalScore))

    if (researchResult) {
      sessionStorage.setItem('companyProfile', JSON.stringify(researchResult.company_profile))
    }

    setPhase('complete')
  }

  // ============================================================================
  // Render: Website Entry Phase
  // ============================================================================

  if (phase === 'website') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-primary-50">
        <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
          <div className="max-w-6xl mx-auto px-4 py-4">
            <Link to="/" className="text-xl font-bold text-gray-900">
              CRB<span className="text-primary-600">Analyser</span>
            </Link>
          </div>
        </nav>

        <div className="pt-24 pb-20 px-4 flex items-center justify-center min-h-screen">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-xl w-full"
          >
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-2xl mb-4">
                <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Let's research your business</h1>
              <p className="text-gray-600">
                We'll analyze publicly available information about your company to provide personalized insights.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your company website
              </label>
              <input
                type="text"
                value={websiteUrl}
                onChange={(e) => setWebsiteUrl(e.target.value)}
                placeholder="www.yourcompany.com"
                className="w-full px-4 py-4 text-lg border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                onKeyDown={(e) => e.key === 'Enter' && websiteUrl.length > 3 && startResearch()}
              />

              <div className="mt-4 p-4 bg-gray-50 rounded-xl">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-primary-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="text-sm text-gray-600">
                    <p className="font-medium text-gray-900 mb-1">What we'll look for:</p>
                    <ul className="space-y-1">
                      <li>• Company size, industry & business model</li>
                      <li>• Products, services & pricing</li>
                      <li>• Technology stack & tools</li>
                      <li>• Recent news & growth signals</li>
                    </ul>
                  </div>
                </div>
              </div>

              <button
                onClick={startResearch}
                disabled={websiteUrl.length < 4 || !sessionId}
                className={`w-full mt-6 py-4 font-semibold rounded-xl transition text-lg ${
                  websiteUrl.length >= 4 && sessionId
                    ? 'bg-primary-600 text-white hover:bg-primary-700 shadow-lg shadow-primary-600/25'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                }`}
              >
                {!sessionId ? 'Loading...' : 'Start Research'}
              </button>
            </div>

            {/* Start fresh option */}
            <button
              onClick={() => {
                localStorage.removeItem('crb_session_id')
                window.location.reload()
              }}
              className="mt-4 text-sm text-gray-500 hover:text-gray-700 underline"
            >
              Start a new analysis
            </button>
          </motion.div>
        </div>
      </div>
    )
  }

  // ============================================================================
  // Render: Researching Phase
  // ============================================================================

  if (phase === 'researching') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-purple-50 flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="max-w-lg w-full"
        >
          <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100 text-center">
            {researchError ? (
              <>
                <div className="w-20 h-20 mx-auto mb-6 bg-red-100 rounded-full flex items-center justify-center">
                  <svg className="w-10 h-10 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">Research Failed</h2>
                <p className="text-gray-600 mb-6">{researchError}</p>
                <button
                  onClick={() => { setPhase('website'); setResearchError(null); }}
                  className="px-6 py-3 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition"
                >
                  Try Again
                </button>
              </>
            ) : (
              <>
                <div className="relative w-32 h-32 mx-auto mb-6">
                  {/* Animated rings */}
                  <motion.div
                    animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0.2, 0.5] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="absolute inset-0 bg-purple-200 rounded-full"
                  />
                  <motion.div
                    animate={{ scale: [1, 1.1, 1], opacity: [0.7, 0.3, 0.7] }}
                    transition={{ duration: 2, repeat: Infinity, delay: 0.3 }}
                    className="absolute inset-2 bg-purple-300 rounded-full"
                  />
                  <div className="absolute inset-4 bg-white rounded-full flex items-center justify-center shadow-lg">
                    <svg className="w-12 h-12 text-purple-600" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <motion.path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                        initial={{ pathLength: 0 }}
                        animate={{ pathLength: 1 }}
                        transition={{ duration: 2, repeat: Infinity }}
                      />
                    </svg>
                  </div>
                </div>

                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Researching {companyName || 'your company'}...
                </h2>
                <p className="text-gray-600 mb-6">{researchStep}</p>

                {/* Progress bar */}
                <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
                  <motion.div
                    className="bg-gradient-to-r from-purple-500 to-primary-600 h-3 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${researchProgress}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
                <p className="text-sm text-gray-500">{researchProgress}% complete</p>

                {/* What we're doing */}
                <div className="mt-8 text-left">
                  <div className="space-y-3">
                    {[
                      { label: 'Scanning website', done: researchProgress >= 20 },
                      { label: 'Searching LinkedIn', done: researchProgress >= 40 },
                      { label: 'Finding news & updates', done: researchProgress >= 60 },
                      { label: 'Analyzing tech stack', done: researchProgress >= 80 },
                      { label: 'Generating questions', done: researchProgress >= 95 },
                    ].map((step, i) => (
                      <div key={i} className="flex items-center gap-3">
                        <div className={`w-5 h-5 rounded-full flex items-center justify-center ${
                          step.done ? 'bg-green-500' : 'bg-gray-200'
                        }`}>
                          {step.done && (
                            <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                            </svg>
                          )}
                        </div>
                        <span className={step.done ? 'text-gray-900' : 'text-gray-400'}>
                          {step.label}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        </motion.div>
      </div>
    )
  }

  // ============================================================================
  // Render: Findings Phase (What we know / What we need)
  // ============================================================================

  if (phase === 'findings') {
    const highConfidence = findings.filter(f => f.confidence === 'high')
    const mediumConfidence = findings.filter(f => f.confidence === 'medium')
    const lowConfidence = findings.filter(f => f.confidence === 'low')

    return (
      <div className="min-h-screen bg-gray-50">
        <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
          <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
            <Link to="/" className="text-xl font-bold text-gray-900">
              CRB<span className="text-primary-600">Analyser</span>
            </Link>
            <div className="text-sm text-gray-500">
              Research complete
            </div>
          </div>
        </nav>

        <div className="pt-24 pb-20 px-4">
          <div className="max-w-3xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              {/* Header */}
              <div className="text-center mb-8">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-2xl mb-4">
                  <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h1 className="text-2xl font-bold text-gray-900 mb-2">
                  Here's what we found about {companyName}
                </h1>
                <p className="text-gray-600">
                  {researchResult?.questionnaire?.research_summary ||
                   'We gathered public information about your business. Review what we found and help us fill in the gaps.'}
                </p>
              </div>

              {/* Research Quality Score */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 mb-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-semibold text-gray-900">Research Coverage</h2>
                  <span className={`text-2xl font-bold ${
                    knowledgeScore >= 60 ? 'text-green-600' : knowledgeScore >= 30 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {knowledgeScore}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all ${
                      knowledgeScore >= 60 ? 'bg-green-500' : knowledgeScore >= 30 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${knowledgeScore}%` }}
                  />
                </div>
                <p className="text-sm text-gray-500 mt-2">
                  {knowledgeScore >= 60
                    ? 'Good foundation! A few more questions will complete the picture.'
                    : knowledgeScore >= 30
                    ? 'We found some useful info. Let\'s fill in the important gaps.'
                    : 'Limited public info found. Your answers are crucial for a quality report.'}
                </p>
              </div>

              {/* What we found - High Confidence */}
              {highConfidence.length > 0 && (
                <div className="bg-green-50 rounded-2xl p-6 border border-green-200 mb-4">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-3 h-3 bg-green-500 rounded-full" />
                    <h3 className="font-semibold text-green-900">Confirmed Information</h3>
                  </div>
                  <div className="grid gap-3">
                    {highConfidence.map((finding, i) => (
                      <div key={i} className="flex justify-between items-start bg-white/50 rounded-xl p-3">
                        <span className="text-sm text-green-800 font-medium">{finding.field}</span>
                        <span className="text-sm text-green-900 text-right max-w-[60%]">
                          {Array.isArray(finding.value) ? finding.value.join(', ') : String(finding.value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Medium Confidence */}
              {mediumConfidence.length > 0 && (
                <div className="bg-yellow-50 rounded-2xl p-6 border border-yellow-200 mb-4">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-3 h-3 bg-yellow-500 rounded-full" />
                    <h3 className="font-semibold text-yellow-900">Needs Confirmation</h3>
                    <span className="text-xs text-yellow-700 bg-yellow-200 px-2 py-0.5 rounded-full">
                      We'll ask about these
                    </span>
                  </div>
                  <div className="grid gap-3">
                    {mediumConfidence.map((finding, i) => (
                      <div key={i} className="flex justify-between items-start bg-white/50 rounded-xl p-3">
                        <span className="text-sm text-yellow-800 font-medium">{finding.field}</span>
                        <span className="text-sm text-yellow-900 text-right max-w-[60%]">
                          {Array.isArray(finding.value) ? finding.value.join(', ') : String(finding.value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Low Confidence */}
              {lowConfidence.length > 0 && (
                <div className="bg-orange-50 rounded-2xl p-6 border border-orange-200 mb-4">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-3 h-3 bg-orange-500 rounded-full" />
                    <h3 className="font-semibold text-orange-900">Low Confidence</h3>
                  </div>
                  <div className="grid gap-3">
                    {lowConfidence.map((finding, i) => (
                      <div key={i} className="flex justify-between items-start bg-white/50 rounded-xl p-3">
                        <span className="text-sm text-orange-800 font-medium">{finding.field}</span>
                        <span className="text-sm text-orange-900 text-right max-w-[60%]">
                          {Array.isArray(finding.value) ? finding.value.join(', ') : String(finding.value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Initial AI Insights - Real Value */}
              <div className="bg-gradient-to-br from-purple-50 to-primary-50 rounded-2xl p-6 border border-purple-200 mb-6">
                <div className="flex items-center gap-2 mb-4">
                  <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <h3 className="font-semibold text-purple-900">Initial AI Analysis</h3>
                </div>
                <p className="text-purple-800 text-sm mb-4">
                  Based on what we found, here are some initial observations for {companyName}:
                </p>
                <ul className="space-y-2 text-sm text-purple-900">
                  {findings.slice(0, 3).map((f, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-purple-500 mt-1">→</span>
                      <span>
                        {f.field === 'Business Model' && `Your ${f.value} model has specific automation opportunities`}
                        {f.field === 'Industry' && `Companies in ${f.value} typically see 20-40% efficiency gains with AI`}
                        {f.field === 'Team Size' && `With ${f.value}, you're at a sweet spot for AI implementation`}
                        {f.field === 'Products/Services' && `Your offerings could benefit from AI-powered optimization`}
                        {f.field === 'Technology Stack' && `Your tech stack has good AI integration potential`}
                        {!['Business Model', 'Industry', 'Team Size', 'Products/Services', 'Technology Stack'].includes(f.field) && `${f.field}: ${f.value}`}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* What full report reveals - Genuine teasers */}
              <div className="bg-white rounded-2xl p-6 border border-gray-200 mb-8">
                <h3 className="font-semibold text-gray-900 mb-4">What we'll analyze in your full report</h3>
                <div className="grid gap-3">
                  <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
                    <span className="text-xl">🎯</span>
                    <div>
                      <div className="font-medium text-gray-900">Specific AI Opportunities</div>
                      <div className="text-sm text-gray-500">Tailored to your {findings.find(f => f.field === 'Industry')?.value || 'industry'} and business model</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
                    <span className="text-xl">💰</span>
                    <div>
                      <div className="font-medium text-gray-900">ROI Projections</div>
                      <div className="text-sm text-gray-500">Based on your team size and current operations</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
                    <span className="text-xl">🛠️</span>
                    <div>
                      <div className="font-medium text-gray-900">Tool Recommendations</div>
                      <div className="text-sm text-gray-500">Real vendors with pricing that fit your budget</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
                    <span className="text-xl">⚠️</span>
                    <div>
                      <div className="font-medium text-gray-900">"Don't Do This" Section</div>
                      <div className="text-sm text-gray-500">AI pitfalls specific to your situation</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Natural CTA */}
              <div className="text-center">
                <p className="text-gray-600 mb-2">
                  To create your personalized report, we need a few more details.
                </p>
                <p className="text-sm text-gray-500 mb-6">
                  {questions.length} quick questions • Takes about {Math.max(2, Math.ceil(questions.length * 0.5))} minutes
                </p>
                <button
                  onClick={() => setPhase('questions')}
                  className="px-8 py-4 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition shadow-lg shadow-primary-600/25 text-lg"
                >
                  Continue →
                </button>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    )
  }

  // ============================================================================
  // Render: Questions Phase
  // ============================================================================

  if (phase === 'questions' && currentQuestion) {
    const progress = ((currentQuestionIndex + 1) / questions.length) * 100

    return (
      <div className="min-h-screen bg-gray-50">
        <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
          <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
            <Link to="/" className="text-xl font-bold text-gray-900">
              CRB<span className="text-primary-600">Analyser</span>
            </Link>
            <div className="text-sm text-gray-500">
              Question {currentQuestionIndex + 1} of {questions.length}
            </div>
          </div>
        </nav>

        {/* Progress bar */}
        <div className="fixed top-16 left-0 right-0 h-1 bg-gray-200 z-40">
          <motion.div
            className="h-full bg-primary-600"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>

        <div className="pt-24 pb-20 px-4">
          <div className="max-w-2xl mx-auto">
            <AnimatePresence mode="wait">
              <motion.div
                key={currentQuestion.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
              >
                {/* Question purpose badge */}
                <div className="mb-4">
                  <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                    currentQuestion.purpose === 'confirm' ? 'bg-yellow-100 text-yellow-800' :
                    currentQuestion.purpose === 'clarify' ? 'bg-blue-100 text-blue-800' :
                    currentQuestion.purpose === 'discover' ? 'bg-purple-100 text-purple-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {currentQuestion.purpose === 'confirm' ? 'Confirming our research' :
                     currentQuestion.purpose === 'clarify' ? 'Need more detail' :
                     currentQuestion.purpose === 'discover' ? 'Can\'t find publicly' :
                     'Deep dive'}
                  </span>
                </div>

                <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
                  <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                    {currentQuestion.question}
                  </h2>
                  {currentQuestion.rationale && (
                    <p className="text-gray-500 text-sm mb-6">{currentQuestion.rationale}</p>
                  )}

                  {/* Text input */}
                  {currentQuestion.type === 'text' && (
                    <input
                      type="text"
                      value={getCurrentAnswer() as string}
                      onChange={(e) => handleAnswer(e.target.value)}
                      placeholder="Type your answer..."
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent text-lg"
                    />
                  )}

                  {/* Textarea */}
                  {currentQuestion.type === 'textarea' && (
                    <textarea
                      value={getCurrentAnswer() as string}
                      onChange={(e) => handleAnswer(e.target.value)}
                      placeholder="Type your answer..."
                      rows={4}
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent text-lg resize-none"
                    />
                  )}

                  {/* Number */}
                  {currentQuestion.type === 'number' && (
                    <input
                      type="number"
                      value={getCurrentAnswer() as string}
                      onChange={(e) => handleAnswer(e.target.value)}
                      placeholder="Enter a number..."
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent text-lg"
                    />
                  )}

                  {/* Yes/No */}
                  {currentQuestion.type === 'yes_no' && (
                    <div className="flex gap-4">
                      {['Yes', 'No'].map((opt) => (
                        <button
                          key={opt}
                          onClick={() => handleAnswer(opt.toLowerCase())}
                          className={`flex-1 p-4 rounded-xl border-2 transition font-medium ${
                            getCurrentAnswer() === opt.toLowerCase()
                              ? 'border-primary-600 bg-primary-50 text-primary-700'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Select */}
                  {currentQuestion.type === 'select' && currentQuestion.options && (
                    <div className="space-y-3">
                      {currentQuestion.options.map((opt) => (
                        <button
                          key={opt.value}
                          onClick={() => handleAnswer(opt.value)}
                          className={`w-full p-4 text-left rounded-xl border-2 transition ${
                            getCurrentAnswer() === opt.value
                              ? 'border-primary-600 bg-primary-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <span className="font-medium text-gray-900">{opt.label}</span>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Multiselect */}
                  {currentQuestion.type === 'multiselect' && currentQuestion.options && (
                    <div className="space-y-3">
                      {currentQuestion.options.map((opt) => {
                        const selected = (getCurrentAnswer() as string[]).includes(opt.value)
                        return (
                          <button
                            key={opt.value}
                            onClick={() => {
                              const current = getCurrentAnswer() as string[]
                              handleAnswer(
                                selected
                                  ? current.filter(v => v !== opt.value)
                                  : [...current, opt.value]
                              )
                            }}
                            className={`w-full p-4 text-left rounded-xl border-2 transition flex items-center gap-3 ${
                              selected ? 'border-primary-600 bg-primary-50' : 'border-gray-200 hover:border-gray-300'
                            }`}
                          >
                            <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                              selected ? 'border-primary-600 bg-primary-600' : 'border-gray-300'
                            }`}>
                              {selected && (
                                <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                </svg>
                              )}
                            </div>
                            <span className="font-medium text-gray-900">{opt.label}</span>
                          </button>
                        )
                      })}
                    </div>
                  )}

                  {/* Prefilled hint */}
                  {currentQuestion.prefilled_value && (
                    <div className="mt-4 p-3 bg-blue-50 rounded-xl">
                      <p className="text-sm text-blue-800">
                        <span className="font-medium">From our research: </span>
                        {Array.isArray(currentQuestion.prefilled_value)
                          ? currentQuestion.prefilled_value.join(', ')
                          : currentQuestion.prefilled_value}
                      </p>
                    </div>
                  )}
                </div>

                {/* Navigation */}
                <div className="flex justify-between mt-6">
                  <button
                    onClick={handlePrevQuestion}
                    disabled={currentQuestionIndex === 0}
                    className={`px-6 py-3 font-medium rounded-xl transition ${
                      currentQuestionIndex === 0
                        ? 'text-gray-400 cursor-not-allowed'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    Back
                  </button>
                  <button
                    onClick={handleNextQuestion}
                    disabled={!canProceed()}
                    className={`px-8 py-3 font-semibold rounded-xl transition ${
                      canProceed()
                        ? 'bg-primary-600 text-white hover:bg-primary-700'
                        : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    {currentQuestionIndex === questions.length - 1 ? 'Finish' : 'Continue'}
                  </button>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    )
  }

  // ============================================================================
  // Render: Complete Phase
  // ============================================================================

  if (phase === 'complete') {
    return (
      <div className="min-h-screen bg-gray-50">
        <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
          <div className="max-w-6xl mx-auto px-4 py-4">
            <Link to="/" className="text-xl font-bold text-gray-900">
              CRB<span className="text-primary-600">Analyser</span>
            </Link>
          </div>
        </nav>

        <div className="pt-24 pb-20 px-4">
          <div className="max-w-3xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center"
            >
              <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-2xl mb-6">
                <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>

              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                We have everything we need!
              </h1>

              {/* Knowledge completeness */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 mb-8 max-w-md mx-auto">
                <div className="flex items-center justify-between mb-3">
                  <span className="font-medium text-gray-700">Knowledge Completeness</span>
                  <span className="text-2xl font-bold text-green-600">{knowledgeScore}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-green-500 h-3 rounded-full"
                    style={{ width: `${knowledgeScore}%` }}
                  />
                </div>
                <p className="text-sm text-gray-500 mt-3">
                  {knowledgeScore >= 70
                    ? 'Excellent! We have comprehensive data for a high-quality report.'
                    : knowledgeScore >= 50
                    ? 'Good foundation. Your report will include actionable insights.'
                    : 'We have enough to get started. Your answers filled crucial gaps.'}
                </p>
              </div>

              {/* What's in the report */}
              <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 mb-8 text-left">
                <h3 className="font-semibold text-gray-900 mb-4">Your report will include:</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  {[
                    { icon: '🎯', title: 'AI Opportunities', desc: 'Specific use cases for your business' },
                    { icon: '💰', title: 'ROI Projections', desc: 'Cost savings and efficiency gains' },
                    { icon: '🛠️', title: 'Tool Recommendations', desc: 'Real vendors with pricing' },
                    { icon: '📋', title: 'Implementation Roadmap', desc: 'Step-by-step action plan' },
                    { icon: '⚠️', title: 'Risk Assessment', desc: 'What to watch out for' },
                    { icon: '🚫', title: '"Don\'t Do This"', desc: 'AI traps to avoid' },
                  ].map((item, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
                      <span className="text-2xl">{item.icon}</span>
                      <div>
                        <div className="font-medium text-gray-900">{item.title}</div>
                        <div className="text-sm text-gray-500">{item.desc}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* CTA */}
              <div className="bg-white rounded-2xl p-8 shadow-sm border-2 border-primary-200">
                <div className="text-4xl font-bold text-gray-900 mb-2">€147</div>
                <p className="text-gray-500 mb-6">One-time payment • Delivered within 24 hours</p>

                <button
                  onClick={() => navigate('/checkout?tier=full')}
                  className="w-full py-4 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition shadow-lg shadow-primary-600/25 text-lg"
                >
                  Get Your Report →
                </button>

                <p className="text-sm text-gray-500 mt-4">
                  14-day money-back guarantee if you're not satisfied
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    )
  }

  // Fallback
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full" />
    </div>
  )
}
