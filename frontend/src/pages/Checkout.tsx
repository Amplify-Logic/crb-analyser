import { useState, useEffect } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import apiClient from '../services/apiClient'
import { Logo } from '../components/Logo'

interface QuizResults {
  score: number
  opportunities: { title: string; potential: string; preview: boolean }[]
  industryInsight: string
}

interface QuizAnswer {
  questionId: string
  answer: string | string[]
}

const TIER_INFO = {
  ai: {
    name: 'Readiness Report',
    price: 147,
    description: 'Self-service analysis',
    features: [
      '15-20 AI opportunities analyzed',
      'Honest verdicts: Go / Caution / Wait / No',
      'Real vendor pricing & ROI',
      'Implementation roadmap',
      '"Don\'t do this" section',
    ],
  },
  human: {
    name: 'Readiness Report + Strategy Call',
    price: 497,
    description: 'Expert-guided analysis',
    features: [
      '15-20 AI opportunities analyzed',
      'Honest verdicts: Go / Caution / Wait / No',
      'Real vendor pricing & ROI',
      'Implementation roadmap',
      '"Don\'t do this" section',
    ],
    bonusFeatures: [
      '60-minute strategy call with expert',
      'Live Q&A on your specific situation',
    ],
  },
}

export default function Checkout() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const tier = (searchParams.get('tier') as 'ai' | 'human') || 'ai'

  const [email, setEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [quizAnswers, setQuizAnswers] = useState<QuizAnswer[]>([])
  const [quizResults, setQuizResults] = useState<QuizResults | null>(null)

  useEffect(() => {
    // DEV BYPASS: Skip payment in development mode only
    if (import.meta.env.DEV && searchParams.get('dev') === 'bypass') {
      // Get session ID from storage
      const sessionId = sessionStorage.getItem('quizSessionId')
      navigate(`/interview${sessionId ? `?session_id=${sessionId}` : ''}`)
      return
    }

    // Load quiz data from session storage
    const answersStr = sessionStorage.getItem('quizAnswers')
    const resultsStr = sessionStorage.getItem('quizResults')
    const quizCompleted = sessionStorage.getItem('quizCompleted')
    const savedEmail = sessionStorage.getItem('userEmail')

    if (answersStr) {
      setQuizAnswers(JSON.parse(answersStr))
    }
    if (resultsStr) {
      setQuizResults(JSON.parse(resultsStr))
    }
    if (savedEmail) {
      setEmail(savedEmail)
    }

    // If no quiz data at all, redirect to quiz
    // Allow through if they have quizResults OR quizCompleted flag
    if (!answersStr && !resultsStr && !quizCompleted) {
      navigate('/quiz')
    }
  }, [navigate, searchParams])

  const tierInfo = TIER_INFO[tier]

  const handleCheckout = async () => {
    if (!email) {
      setError('Please enter your email address')
      return
    }

    if (!email.includes('@')) {
      setError('Please enter a valid email address')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const response = await apiClient.post<{ checkout_url: string }>('/payments/guest-checkout', {
        tier,
        email,
        quiz_answers: quizAnswers.reduce((acc, a) => ({ ...acc, [a.questionId]: a.answer }), {}),
        quiz_results: quizResults,
      })

      // Redirect to Stripe checkout
      window.location.href = response.data.checkout_url
    } catch (err: any) {
      console.error('Checkout error:', err)
      setError(err.message || 'Failed to start checkout. Please try again.')
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
          <Logo size="sm" showIcon={false} />
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            Secure checkout
          </div>
        </div>
      </nav>

      <div className="pt-24 pb-20 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="grid md:grid-cols-2 gap-8">
            {/* Order Summary */}
            <div className="order-2 md:order-1">
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Order Summary</h2>

                {/* Your Score */}
                {quizResults && (
                  <div className="bg-gray-50 rounded-xl p-4 mb-6">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Your AI Readiness Score</span>
                      <span className="text-2xl font-bold text-primary-600">{quizResults.score}</span>
                    </div>
                  </div>
                )}

                {/* Product */}
                <div className="border-t border-gray-100 pt-4">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <div className="font-medium text-gray-900">{tierInfo.name}</div>
                      <div className="text-sm text-gray-500">{tierInfo.description}</div>
                    </div>
                    <div className="text-xl font-bold text-gray-900">€{tierInfo.price}</div>
                  </div>

                  <ul className="space-y-2 mb-4">
                    {tierInfo.features.map((feature, i) => (
                      <li key={i} className="flex items-center gap-2 text-sm text-gray-600">
                        <svg className="w-4 h-4 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        {feature}
                      </li>
                    ))}
                  </ul>

                  {/* Bonus features for human tier */}
                  {'bonusFeatures' in tierInfo && tierInfo.bonusFeatures && (
                    <ul className="space-y-2 mb-6 pt-3 border-t border-gray-100">
                      {tierInfo.bonusFeatures.map((feature, i) => (
                        <li key={i} className="flex items-center gap-2 text-sm text-gray-900 font-medium">
                          <svg className="w-4 h-4 text-primary-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          {feature}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                {/* Total */}
                <div className="border-t border-gray-100 pt-4">
                  <div className="flex justify-between items-center">
                    <span className="text-lg font-semibold text-gray-900">Total</span>
                    <span className="text-2xl font-bold text-gray-900">€{tierInfo.price}</span>
                  </div>
                </div>

                {/* Switch tier */}
                <div className="mt-4 text-center">
                  {tier === 'ai' ? (
                    <Link
                      to="/checkout?tier=human"
                      className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                    >
                      + Add Strategy Call (€497 total)
                    </Link>
                  ) : (
                    <Link
                      to="/checkout?tier=ai"
                      className="text-sm text-gray-500 hover:text-gray-700"
                    >
                      Just the report (€147)
                    </Link>
                  )}
                </div>
              </div>

              {/* Trust badges */}
              <div className="mt-6 flex flex-wrap justify-center gap-4 text-sm text-gray-500">
                <div className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  Secure payment
                </div>
                <div className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                  </svg>
                  Powered by Stripe
                </div>
              </div>
            </div>

            {/* Checkout Form */}
            <div className="order-1 md:order-2">
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Get Your Report</h2>

                {error && (
                  <div className="mb-4 p-4 bg-red-50 border border-red-100 rounded-xl text-red-700 text-sm">
                    {error}
                  </div>
                )}

                <div className="space-y-4">
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                      Email address
                    </label>
                    <input
                      type="email"
                      id="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@company.com"
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      We'll send your report to this email address
                    </p>
                  </div>

                  <button
                    onClick={handleCheckout}
                    disabled={isLoading}
                    className={`w-full py-4 font-semibold rounded-xl transition flex items-center justify-center gap-2 ${
                      isLoading
                        ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                        : 'bg-primary-600 text-white hover:bg-primary-700'
                    }`}
                  >
                    {isLoading ? (
                      <>
                        <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Processing...
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                        Pay €{tierInfo.price}
                      </>
                    )}
                  </button>
                </div>

                <div className="mt-6 text-center text-sm text-gray-500">
                  <p>By proceeding, you agree to our</p>
                  <p>
                    <Link to="/terms" className="text-primary-600 hover:underline">Terms of Service</Link>
                    {' & '}
                    <Link to="/privacy" className="text-primary-600 hover:underline">Privacy Policy</Link>
                  </p>
                </div>

                {/* Dev bypass - only in development */}
                {import.meta.env.DEV && (
                  <div className="mt-4 pt-4 border-t border-dashed border-gray-200">
                    <button
                      onClick={() => {
                        const sessionId = sessionStorage.getItem('quizSessionId')
                        navigate(`/interview${sessionId ? `?session_id=${sessionId}` : ''}`)
                      }}
                      className="w-full py-2 text-sm text-gray-500 hover:text-gray-700 bg-gray-100 rounded-lg"
                    >
                      🔓 Dev: Skip to Workshop
                    </button>
                  </div>
                )}
              </div>

              {/* What happens next */}
              <div className="mt-6 bg-primary-50 rounded-2xl p-6 border border-primary-100">
                <h3 className="font-medium text-primary-900 mb-3">What happens next?</h3>
                <ol className="space-y-2 text-sm text-primary-800">
                  <li className="flex gap-2">
                    <span className="font-semibold">1.</span>
                    Complete secure payment via Stripe
                  </li>
                  <li className="flex gap-2">
                    <span className="font-semibold">2.</span>
                    Our AI analyzes your business in depth
                  </li>
                  <li className="flex gap-2">
                    <span className="font-semibold">3.</span>
                    Receive your personalized report via email
                  </li>
                  {tier === 'human' && (
                    <li className="flex gap-2">
                      <span className="font-semibold">4.</span>
                      Book your 60-min strategy call
                    </li>
                  )}
                </ol>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
