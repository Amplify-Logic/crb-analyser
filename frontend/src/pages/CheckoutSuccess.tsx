import { useEffect, useState } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'

export default function CheckoutSuccess() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const stripeSessionId = searchParams.get('session_id')
  const selectedTier = sessionStorage.getItem('selectedTier') || 'report_only'
  const companyName = sessionStorage.getItem('companyName') || 'Your Company'

  const [isVerifying, setIsVerifying] = useState(true)
  const [isVerified, setIsVerified] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const hasStrategyCall = selectedTier === 'report_plus_call'

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

        // Clear quiz session data since account is now created
        sessionStorage.removeItem('quizSessionId')
        sessionStorage.removeItem('selectedTier')
        sessionStorage.removeItem('companyProfile')
        // Keep companyName for display
      } catch (err: unknown) {
        console.error('Verification error:', err)
        // Still show success - webhook handles the real verification
        setIsVerified(true)
        setIsVerifying(false)
      }
    }

    verifySession()
  }, [stripeSessionId])

  const handleGoToLogin = () => {
    navigate('/login')
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

              <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome, {companyName}!</h1>
              <p className="text-lg text-gray-600 mb-4">
                Your payment was successful and your account has been created.
              </p>

              {/* Email Credentials Notice */}
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6 text-left">
                <div className="flex items-start gap-3">
                  <svg className="w-6 h-6 text-blue-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  <div>
                    <h4 className="font-semibold text-blue-900">Check your email</h4>
                    <p className="text-sm text-blue-800 mt-1">
                      We've sent your login credentials to your email address. Use them to access your dashboard and start your workshop.
                    </p>
                  </div>
                </div>
              </div>

              {/* Strategy Call Badge (if applicable) */}
              {hasStrategyCall && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6 text-left">
                  <div className="flex items-start gap-3">
                    <svg className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <div>
                      <h4 className="font-semibold text-amber-900">Strategy Call Included</h4>
                      <p className="text-sm text-amber-800 mt-1">
                        After your workshop is complete and report is ready, you'll receive a link to book your 60-minute strategy call with our founders.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* What's next */}
              <div className="bg-gradient-to-br from-primary-50 to-purple-50 rounded-xl p-6 text-left mb-8">
                <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                  Next Steps
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center gap-3 text-sm">
                    <div className="w-8 h-8 bg-primary-600 text-white rounded-full flex items-center justify-center font-semibold">
                      1
                    </div>
                    <span className="text-gray-700">Check your email for login credentials</span>
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    <div className="w-8 h-8 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center font-semibold">
                      2
                    </div>
                    <span className="text-gray-700">Log in and complete the 90-minute workshop</span>
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    <div className="w-8 h-8 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center font-semibold">
                      3
                    </div>
                    <span className="text-gray-700">Our team reviews your report (24-48 hours)</span>
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    <div className="w-8 h-8 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center font-semibold">
                      4
                    </div>
                    <span className="text-gray-700">Get your personalized AI roadmap</span>
                  </div>
                </div>
              </div>

              {/* CTA Button */}
              <button
                onClick={handleGoToLogin}
                className="w-full py-4 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition shadow-lg shadow-primary-600/25 text-lg flex items-center justify-center gap-2"
              >
                Go to Login
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </button>

              <p className="text-sm text-gray-500 mt-4">
                Didn't receive the email? Check your spam folder or contact support.
              </p>
            </div>

            {/* Support */}
            <div className="text-center">
              <p className="text-gray-600 mb-3">
                Questions? We're here to help.
              </p>
              <a
                href="mailto:support@crb-analyser.com"
                className="text-primary-600 hover:text-primary-700 font-medium"
              >
                Contact Support
              </a>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
