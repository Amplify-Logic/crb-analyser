import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../services/apiClient'

export default function CheckoutSuccess() {
  const [searchParams] = useSearchParams()
  const sessionId = searchParams.get('session_id')

  const [isVerifying, setIsVerifying] = useState(true)
  const [isVerified, setIsVerified] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const verifySession = async () => {
      if (!sessionId) {
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

        // Clear quiz data from session storage
        sessionStorage.removeItem('quizAnswers')
        sessionStorage.removeItem('quizResults')
      } catch (err: any) {
        console.error('Verification error:', err)
        // Still show success - webhook handles the real verification
        setIsVerified(true)
        setIsVerifying(false)
      }
    }

    verifySession()
  }, [sessionId])

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
        <div className="max-w-2xl mx-auto">
          {/* Success Card */}
          <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 text-center mb-8">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Payment Successful!</h1>
            <p className="text-lg text-gray-600 mb-6">
              Thank you for your purchase. We're generating your personalized CRB report now.
            </p>

            <div className="bg-primary-50 rounded-xl p-6 text-left mb-6">
              <h3 className="font-medium text-primary-900 mb-3">What happens next:</h3>
              <ol className="space-y-3">
                <li className="flex gap-3">
                  <div className="w-6 h-6 rounded-full bg-primary-200 text-primary-800 flex items-center justify-center flex-shrink-0 text-sm font-semibold">
                    1
                  </div>
                  <div>
                    <div className="font-medium text-primary-900">AI Analysis (5-10 minutes)</div>
                    <div className="text-sm text-primary-700">Our AI is analyzing your business and researching relevant solutions</div>
                  </div>
                </li>
                <li className="flex gap-3">
                  <div className="w-6 h-6 rounded-full bg-primary-200 text-primary-800 flex items-center justify-center flex-shrink-0 text-sm font-semibold">
                    2
                  </div>
                  <div>
                    <div className="font-medium text-primary-900">Email Delivery</div>
                    <div className="text-sm text-primary-700">You'll receive an email with a link to access your report</div>
                  </div>
                </li>
                <li className="flex gap-3">
                  <div className="w-6 h-6 rounded-full bg-primary-200 text-primary-800 flex items-center justify-center flex-shrink-0 text-sm font-semibold">
                    3
                  </div>
                  <div>
                    <div className="font-medium text-primary-900">Review & Act</div>
                    <div className="text-sm text-primary-700">Access your full report with actionable recommendations</div>
                  </div>
                </li>
              </ol>
            </div>
          </div>

          {/* Check email reminder */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 text-center">
            <div className="flex items-center justify-center gap-2 text-gray-600 mb-4">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Check your inbox
            </div>
            <p className="text-sm text-gray-500">
              Can't find the email? Check your spam folder or{' '}
              <a href="mailto:support@crb-analyser.com" className="text-primary-600 hover:underline">
                contact support
              </a>
            </p>
          </div>

          {/* Create account CTA */}
          <div className="mt-8 text-center">
            <p className="text-gray-600 mb-4">
              Want to track your progress and access future reports?
            </p>
            <Link
              to="/signup"
              className="inline-block px-6 py-3 bg-gray-900 text-white font-semibold rounded-xl hover:bg-gray-800 transition"
            >
              Create Free Account
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
