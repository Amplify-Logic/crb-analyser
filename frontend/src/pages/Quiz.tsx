import { useState, useEffect } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

interface QuizAnswer {
  questionId: string
  answer: string | string[]
}

const QUIZ_QUESTIONS = [
  {
    id: 'company_website',
    question: "What's your company website?",
    type: 'text',
    placeholder: 'www.yourcompany.com',
    helperText: "We'll research your company while you answer the quiz",
  },
  {
    id: 'industry',
    question: 'What industry are you in?',
    type: 'select',
    options: [
      { value: 'marketing', label: 'Marketing / Creative Agency' },
      { value: 'ecommerce', label: 'E-commerce / Online Retail' },
      { value: 'retail', label: 'Retail / Brick & Mortar' },
      { value: 'tech', label: 'Tech / SaaS / Software' },
      { value: 'music', label: 'Music / Audio Production' },
      { value: 'professional_services', label: 'Professional Services' },
      { value: 'healthcare', label: 'Healthcare' },
      { value: 'finance', label: 'Finance / Fintech' },
      { value: 'other', label: 'Other' },
    ],
  },
  {
    id: 'team_size',
    question: 'How many people work in your business?',
    type: 'select',
    options: [
      { value: 'solo', label: 'Just me' },
      { value: '2-5', label: '2-5 people' },
      { value: '6-20', label: '6-20 people' },
      { value: '21-50', label: '21-50 people' },
      { value: '50+', label: '50+ people' },
    ],
  },
  {
    id: 'biggest_pain',
    question: 'What takes up most of your time?',
    type: 'multiselect',
    options: [
      { value: 'admin', label: 'Admin & paperwork' },
      { value: 'client_communication', label: 'Client communication' },
      { value: 'content_creation', label: 'Creating content' },
      { value: 'data_entry', label: 'Data entry & reporting' },
      { value: 'customer_support', label: 'Customer support' },
      { value: 'scheduling', label: 'Scheduling & coordination' },
      { value: 'repetitive_tasks', label: 'Repetitive manual tasks' },
    ],
    helperText: 'Select all that apply',
  },
  {
    id: 'ai_experience',
    question: 'Have you tried using AI tools before?',
    type: 'select',
    options: [
      { value: 'none', label: "No, I haven't tried any" },
      { value: 'basic', label: 'Yes, ChatGPT or similar' },
      { value: 'some', label: "Yes, I use a few AI tools" },
      { value: 'advanced', label: 'Yes, AI is part of my workflow' },
    ],
  },
]

export default function Quiz() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const upgradeTier = searchParams.get('upgrade')

  const [currentStep, setCurrentStep] = useState(0)
  const [answers, setAnswers] = useState<QuizAnswer[]>([])
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisProgress, setAnalysisProgress] = useState(0)
  const [showResults, setShowResults] = useState(false)
  const [results, setResults] = useState<{
    score: number
    opportunities: { title: string; potential: string; preview: boolean }[]
    industryInsight: string
  } | null>(null)

  const currentQuestion = QUIZ_QUESTIONS[currentStep]
  const isLastQuestion = currentStep === QUIZ_QUESTIONS.length - 1

  const handleAnswer = (answer: string | string[]) => {
    const newAnswers = [...answers]
    const existingIndex = newAnswers.findIndex(a => a.questionId === currentQuestion.id)

    if (existingIndex >= 0) {
      newAnswers[existingIndex].answer = answer
    } else {
      newAnswers.push({ questionId: currentQuestion.id, answer })
    }

    setAnswers(newAnswers)
  }

  const getCurrentAnswer = (): string | string[] => {
    const answer = answers.find(a => a.questionId === currentQuestion.id)
    return answer?.answer || (currentQuestion.type === 'multiselect' ? [] : '')
  }

  const canProceed = () => {
    const current = getCurrentAnswer()
    if (currentQuestion.type === 'multiselect') {
      return (current as string[]).length > 0
    }
    return current !== ''
  }

  const handleNext = async () => {
    if (isLastQuestion) {
      await runAnalysis()
    } else {
      setCurrentStep(prev => prev + 1)
    }
  }

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1)
    }
  }

  const runAnalysis = async () => {
    setIsAnalyzing(true)

    // Simulate analysis with progress updates
    const progressSteps = [
      'Researching your company...',
      'Analyzing your industry...',
      'Identifying opportunities...',
      'Calculating potential...',
      'Preparing your results...',
    ]

    for (let i = 0; i < progressSteps.length; i++) {
      setAnalysisProgress((i + 1) * 20)
      await new Promise(resolve => setTimeout(resolve, 800))
    }

    // Generate mock results based on answers
    const industryAnswer = answers.find(a => a.questionId === 'industry')?.answer as string
    const painPoints = answers.find(a => a.questionId === 'biggest_pain')?.answer as string[]
    const aiExperience = answers.find(a => a.questionId === 'ai_experience')?.answer as string

    // Calculate score based on responses
    let baseScore = 50
    if (aiExperience === 'advanced') baseScore += 20
    else if (aiExperience === 'some') baseScore += 10
    else if (aiExperience === 'none') baseScore -= 10

    if (painPoints?.length >= 3) baseScore += 15
    else if (painPoints?.length >= 2) baseScore += 10

    const score = Math.min(100, Math.max(20, baseScore + Math.floor(Math.random() * 10)))

    // Generate opportunities based on pain points
    const opportunities = generateOpportunities(painPoints, industryAnswer)

    setResults({
      score,
      opportunities,
      industryInsight: getIndustryInsight(industryAnswer),
    })

    setIsAnalyzing(false)
    setShowResults(true)
  }

  const generateOpportunities = (
    painPoints: string[] | undefined,
    industry: string
  ): { title: string; potential: string; preview: boolean }[] => {
    const opportunityMap: Record<string, { title: string; potential: string }> = {
      admin: { title: 'Automated Admin Processing', potential: 'Save 5-10 hours/week' },
      client_communication: { title: 'Smart Client Communication', potential: 'Reduce response time by 60%' },
      content_creation: { title: 'AI Content Assistant', potential: 'Create content 3x faster' },
      data_entry: { title: 'Automated Data Entry', potential: 'Eliminate 80% of manual entry' },
      customer_support: { title: 'AI Customer Support', potential: '24/7 instant responses' },
      scheduling: { title: 'Intelligent Scheduling', potential: 'Save 5+ hours/week' },
      repetitive_tasks: { title: 'Task Automation', potential: 'Automate 70% of repetitive work' },
    }

    const selectedOpps = (painPoints || ['admin', 'content_creation', 'scheduling'])
      .slice(0, 5)
      .map((pain, index) => ({
        ...opportunityMap[pain] || { title: 'Process Optimization', potential: 'Significant time savings' },
        preview: index < 3, // Only first 3 are visible in free tier
      }))

    // Always show at least 5 opportunities
    while (selectedOpps.length < 5) {
      selectedOpps.push({
        title: 'Additional Opportunity',
        potential: 'Details in full report',
        preview: false,
      })
    }

    return selectedOpps
  }

  const getIndustryInsight = (industry: string): string => {
    const insights: Record<string, string> = {
      marketing: 'Marketing agencies typically save 15-20 hours/week with AI-powered content and client management.',
      ecommerce: 'E-commerce businesses see 20-40% efficiency gains with AI-powered inventory and customer service.',
      retail: 'Retail businesses report 25% reduction in operational costs with smart inventory and scheduling.',
      tech: 'Tech companies accelerate development cycles by 30% with AI-assisted coding and documentation.',
      music: 'Music studios save 5-10 hours/week on booking and cut audio cleanup time in half.',
      professional_services: 'Professional services firms reduce admin time by 40% with AI document processing.',
      healthcare: 'Healthcare practices improve patient communication and reduce admin burden by 30%.',
      finance: 'Finance teams automate 60% of reporting and compliance tasks with AI.',
      other: 'Businesses across industries are finding significant time savings with targeted AI implementation.',
    }
    return insights[industry] || insights.other
  }

  const handleGetReport = (tier: 'quick' | 'full') => {
    // Store quiz data in session and redirect to checkout
    sessionStorage.setItem('quizAnswers', JSON.stringify(answers))
    sessionStorage.setItem('quizResults', JSON.stringify(results))
    navigate(`/checkout?tier=${tier}`)
  }

  // If showing results
  if (showResults && results) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
          <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
            <Link to="/" className="text-xl font-bold text-gray-900">
              CRB<span className="text-primary-600">Analyser</span>
            </Link>
          </div>
        </nav>

        <div className="pt-24 pb-20 px-4">
          <div className="max-w-3xl mx-auto">
            {/* Score Section */}
            <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 mb-8 text-center">
              <div className="text-sm font-medium text-primary-600 mb-2">Your AI Readiness Score</div>
              <div className="relative w-40 h-40 mx-auto mb-6">
                <svg className="w-full h-full transform -rotate-90">
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    stroke="#e5e7eb"
                    strokeWidth="12"
                    fill="none"
                  />
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    stroke={results.score >= 70 ? '#22c55e' : results.score >= 40 ? '#eab308' : '#ef4444'}
                    strokeWidth="12"
                    fill="none"
                    strokeDasharray={`${(results.score / 100) * 440} 440`}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-5xl font-bold text-gray-900">{results.score}</span>
                </div>
              </div>
              <p className="text-gray-600 max-w-md mx-auto">
                {results.score >= 70
                  ? "Great news! Your business is well-positioned to benefit from AI implementation."
                  : results.score >= 40
                  ? "Good potential! There are several areas where AI could help your business."
                  : "We've identified some foundational steps before AI implementation."}
              </p>
            </div>

            {/* Industry Insight */}
            <div className="bg-primary-50 rounded-2xl p-6 mb-8 border border-primary-100">
              <div className="flex gap-3">
                <svg className="w-6 h-6 text-primary-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <div className="font-medium text-primary-900 mb-1">Industry Insight</div>
                  <p className="text-primary-800">{results.industryInsight}</p>
                </div>
              </div>
            </div>

            {/* Opportunities */}
            <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 mb-8">
              <h3 className="text-xl font-semibold text-gray-900 mb-6">
                We found {results.opportunities.length} opportunities for your business
              </h3>

              <div className="space-y-4">
                {results.opportunities.map((opp, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-xl border ${
                      opp.preview
                        ? 'border-gray-200 bg-white'
                        : 'border-gray-100 bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {opp.preview ? (
                          <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                            <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          </div>
                        ) : (
                          <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                            </svg>
                          </div>
                        )}
                        <div>
                          <div className={`font-medium ${opp.preview ? 'text-gray-900' : 'text-gray-400'}`}>
                            {opp.preview ? opp.title : 'Locked Opportunity'}
                          </div>
                          <div className={`text-sm ${opp.preview ? 'text-green-600' : 'text-gray-400'}`}>
                            {opp.preview ? opp.potential : 'Unlock with full report'}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Upgrade Options */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Quick Report */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border-2 border-primary-200">
                <div className="inline-block px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm font-medium mb-4">
                  Most Popular
                </div>
                <h4 className="text-xl font-semibold text-gray-900 mb-2">Quick Report</h4>
                <div className="text-3xl font-bold text-gray-900 mb-4">
                  €47
                </div>
                <ul className="space-y-2 mb-6">
                  <li className="flex items-center gap-2 text-gray-600">
                    <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    All {results.opportunities.length} opportunities unlocked
                  </li>
                  <li className="flex items-center gap-2 text-gray-600">
                    <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Detailed ROI calculations
                  </li>
                  <li className="flex items-center gap-2 text-gray-600">
                    <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Top 3 vendor recommendations
                  </li>
                  <li className="flex items-center gap-2 text-gray-600">
                    <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    PDF download
                  </li>
                </ul>
                <button
                  onClick={() => handleGetReport('quick')}
                  className="w-full py-3 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition"
                >
                  Get Quick Report
                </button>
              </div>

              {/* Full Analysis */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h4 className="text-xl font-semibold text-gray-900 mb-2">Full Analysis</h4>
                <div className="text-3xl font-bold text-gray-900 mb-4">
                  €297
                </div>
                <ul className="space-y-2 mb-6">
                  <li className="flex items-center gap-2 text-gray-600">
                    <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Everything in Quick Report
                  </li>
                  <li className="flex items-center gap-2 text-gray-600">
                    <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Detailed vendor comparisons
                  </li>
                  <li className="flex items-center gap-2 text-gray-600">
                    <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Implementation roadmap
                  </li>
                  <li className="flex items-center gap-2 text-gray-600">
                    <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    30-min expert consultation
                  </li>
                  <li className="flex items-center gap-2 text-gray-600">
                    <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    90-day email support
                  </li>
                </ul>
                <button
                  onClick={() => handleGetReport('full')}
                  className="w-full py-3 bg-gray-900 text-white font-semibold rounded-xl hover:bg-gray-800 transition"
                >
                  Get Full Analysis
                </button>
              </div>
            </div>

            {/* Free option */}
            <div className="text-center mt-8">
              <Link
                to="/signup"
                className="text-gray-500 hover:text-gray-700 transition"
              >
                Continue with free results (limited)
              </Link>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // If analyzing
  if (isAnalyzing) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="max-w-md w-full text-center">
          <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
            <div className="w-20 h-20 mx-auto mb-6 relative">
              <svg className="animate-spin w-full h-full text-primary-600" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Analyzing your business...
            </h2>
            <p className="text-gray-600 mb-6">
              We're researching your company and identifying AI opportunities.
            </p>
            <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
              <div
                className="bg-primary-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${analysisProgress}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-500">{analysisProgress}% complete</p>
          </div>
        </div>
      </div>
    )
  }

  // Quiz flow
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
          <Link to="/" className="text-xl font-bold text-gray-900">
            CRB<span className="text-primary-600">Analyser</span>
          </Link>
          <div className="text-sm text-gray-500">
            Question {currentStep + 1} of {QUIZ_QUESTIONS.length}
          </div>
        </div>
      </nav>

      {/* Progress bar */}
      <div className="fixed top-16 left-0 right-0 h-1 bg-gray-200 z-40">
        <div
          className="h-full bg-primary-600 transition-all duration-300"
          style={{ width: `${((currentStep + 1) / QUIZ_QUESTIONS.length) * 100}%` }}
        ></div>
      </div>

      {/* Question */}
      <div className="pt-32 pb-20 px-4">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">
              {currentQuestion.question}
            </h2>
            {currentQuestion.helperText && (
              <p className="text-gray-500 mb-6">{currentQuestion.helperText}</p>
            )}

            {/* Text input */}
            {currentQuestion.type === 'text' && (
              <input
                type="text"
                value={getCurrentAnswer() as string}
                onChange={(e) => handleAnswer(e.target.value)}
                placeholder={currentQuestion.placeholder}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent text-lg"
              />
            )}

            {/* Select */}
            {currentQuestion.type === 'select' && currentQuestion.options && (
              <div className="space-y-3">
                {currentQuestion.options.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => handleAnswer(option.value)}
                    className={`w-full p-4 text-left rounded-xl border-2 transition ${
                      getCurrentAnswer() === option.value
                        ? 'border-primary-600 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <span className="font-medium text-gray-900">{option.label}</span>
                  </button>
                ))}
              </div>
            )}

            {/* Multi-select */}
            {currentQuestion.type === 'multiselect' && currentQuestion.options && (
              <div className="space-y-3">
                {currentQuestion.options.map((option) => {
                  const selected = (getCurrentAnswer() as string[]).includes(option.value)
                  return (
                    <button
                      key={option.value}
                      onClick={() => {
                        const current = getCurrentAnswer() as string[]
                        if (selected) {
                          handleAnswer(current.filter(v => v !== option.value))
                        } else {
                          handleAnswer([...current, option.value])
                        }
                      }}
                      className={`w-full p-4 text-left rounded-xl border-2 transition flex items-center gap-3 ${
                        selected
                          ? 'border-primary-600 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300'
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
                      <span className="font-medium text-gray-900">{option.label}</span>
                    </button>
                  )
                })}
              </div>
            )}
          </div>

          {/* Navigation */}
          <div className="flex justify-between mt-6">
            <button
              onClick={handleBack}
              disabled={currentStep === 0}
              className={`px-6 py-3 font-medium rounded-xl transition ${
                currentStep === 0
                  ? 'text-gray-400 cursor-not-allowed'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Back
            </button>
            <button
              onClick={handleNext}
              disabled={!canProceed()}
              className={`px-8 py-3 font-semibold rounded-xl transition ${
                canProceed()
                  ? 'bg-primary-600 text-white hover:bg-primary-700'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
            >
              {isLastQuestion ? 'Get My Score' : 'Continue'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
