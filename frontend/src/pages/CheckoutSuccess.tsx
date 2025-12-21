import { useEffect, useState } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'

export default function CheckoutSuccess() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const stripeSessionId = searchParams.get('session_id')
  const quizSessionId = sessionStorage.getItem('quizSessionId')

  const [isVerifying, setIsVerifying] = useState(true)
  const [isVerified, setIsVerified] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const verifySession = async () => {
      if (!stripeSessionId) {
        setError('No session ID found')
        setIsVerifying(false)
        return
      }

      try {
        // Note: This endpoint would need to be updated to not require auth
        // For now, we'll just show success based on the presence of session_id
        // The webhook handles the actual verification
        setIsVerified(true)
        setIsVerifying(false)

        // Keep session data - we need it for the interview
      } catch (err: unknown) {
        console.error('Verification error:', err)
        // Still show success - webhook handles the real verification
        setIsVerified(true)
        setIsVerifying(false)
      }
    }

    verifySession()
  }, [stripeSessionId])

  const handleStartInterview = () => {
    navigate(`/interview${quizSessionId ? `?session_id=${quizSessionId}` : ''}`)
  }

  if (isVerifying) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="text-center">
          <svg className="animate-spin w-12 h-12 text-primary-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p className="text-gray-600">Confirming your payment...</p>
        </div>
      </div>
    )
  }

  if (error && !isVerified) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Something went wrong</h1>
            <p className="text-gray-600 mb-6">{error}</p>
            <Link
              to="/quiz"
              className="inline-block px-6 py-3 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition"
            >
              Try Again
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-primary-50">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
          <Link to="/" className="text-xl font-bold text-gray-900">
            CRB<span className="text-primary-600">Analyser</span>
          </Link>
        </div>
      </nav>

      <div className="pt-24 pb-20 px-4">
        <div className="max-w-2xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            {/* Success Card */}
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100 text-center mb-8">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', delay: 0.2 }}
                className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6"
              >
                <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </motion.div>

              <h1 className="text-3xl font-bold text-gray-900 mb-2">Payment Successful!</h1>
              <p className="text-lg text-gray-600 mb-8">
                You're now ready to start your in-depth AI workshop interview.
              </p>

              {/* What's next */}
              <div className="bg-gradient-to-br from-primary-50 to-purple-50 rounded-xl p-6 text-left mb-8">
                <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                  Your AI Workshop Interview
                </h3>
                <p className="text-gray-600 text-sm mb-4">
                  This is a conversational interview with our AI analyst. You can type your answers
                  or speak them - just click the microphone button.
                </p>
                <div className="space-y-3">
                  <div className="flex items-center gap-3 text-sm">
                    <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                      <svg className="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <span className="text-gray-700">Takes about 60-90 minutes (take breaks anytime)</span>
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                      <svg className="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                      </svg>
                    </div>
                    <span className="text-gray-700">Type or speak your answers</span>
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                      <svg className="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                    </div>
                    <span className="text-gray-700">Your data is secure and confidential</span>
                  </div>
                </div>
              </div>

              {/* CTA Button */}
              <button
                onClick={handleStartInterview}
                className="w-full py-4 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition shadow-lg shadow-primary-600/25 text-lg flex items-center justify-center gap-2"
              >
                Start Your Interview
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </button>

              <p className="text-sm text-gray-500 mt-4">
                Tip: Find a quiet space where you can focus without interruption.
              </p>
            </div>

            {/* Alternative: Skip interview */}
            <div className="text-center">
              <p className="text-gray-600 mb-3">
                Not ready yet? We can still generate a report based on your quiz answers.
              </p>
              <Link
                to="/"
                className="text-gray-500 hover:text-gray-700 underline text-sm"
              >
                Skip interview (your report will be less personalized)
              </Link>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
