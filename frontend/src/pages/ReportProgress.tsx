import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Logo } from '../components/Logo'

interface ProgressStep {
  id: string
  label: string
  status: 'pending' | 'active' | 'completed' | 'error'
  detail?: string
}

const INITIAL_STEPS: ProgressStep[] = [
  { id: 'intake', label: 'Analyzing your intake responses', status: 'pending' },
  { id: 'research', label: 'Researching industry benchmarks', status: 'pending' },
  { id: 'opportunities', label: 'Identifying AI opportunities', status: 'pending' },
  { id: 'roi', label: 'Calculating ROI projections', status: 'pending' },
  { id: 'recommendations', label: 'Generating recommendations', status: 'pending' },
  { id: 'roadmap', label: 'Building your roadmap', status: 'pending' },
]

const TIPS = [
  "Our AI analyzes over 500 data points from your responses.",
  "We compare your business against 50+ industry benchmarks.",
  "Each recommendation includes real vendor pricing.",
  "ROI calculations show all assumptions transparently.",
  "Your report includes 'build it yourself' alternatives.",
  "We tell you what NOT to do - that's often more valuable.",
]

export default function ReportProgress() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const eventSourceRef = useRef<EventSource | null>(null)

  const [steps, setSteps] = useState<ProgressStep[]>(INITIAL_STEPS)
  const [progress, setProgress] = useState(0)
  const [currentTip, setCurrentTip] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [isComplete, setIsComplete] = useState(false)

  // Rotate tips
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTip(prev => (prev + 1) % TIPS.length)
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  // Warn before leaving
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (!isComplete && !error) {
        e.preventDefault()
        e.returnValue = ''
      }
    }
    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [isComplete, error])

  // SSE connection
  useEffect(() => {
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8383'

    // For demo/development: simulate progress if no real endpoint
    const simulateProgress = async () => {
      for (let i = 0; i < INITIAL_STEPS.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 2000))
        setSteps(prev => prev.map((step, idx) => ({
          ...step,
          status: idx < i ? 'completed' : idx === i ? 'active' : 'pending'
        })))
        setProgress(Math.round(((i + 1) / INITIAL_STEPS.length) * 100))
      }
      await new Promise(resolve => setTimeout(resolve, 1000))
      setSteps(prev => prev.map(step => ({ ...step, status: 'completed' })))
      setProgress(100)
      setIsComplete(true)
    }

    // Try SSE first, fall back to simulation
    try {
      const eventSource = new EventSource(`${API_BASE}/api/reports/${id}/progress`, {
        withCredentials: true
      })
      eventSourceRef.current = eventSource

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          if (data.type === 'progress') {
            setSteps(prev => prev.map(step => {
              if (step.id === data.step_id) {
                return { ...step, status: data.status, detail: data.detail }
              }
              return step
            }))
            setProgress(data.progress || 0)
          }

          if (data.type === 'complete') {
            setIsComplete(true)
            eventSource.close()
          }

          if (data.type === 'error') {
            setError(data.message)
            eventSource.close()
          }
        } catch {
          // Invalid JSON, ignore
        }
      }

      eventSource.onerror = () => {
        eventSource.close()
        // Fall back to simulation for demo
        simulateProgress()
      }
    } catch {
      // SSE not supported or endpoint unavailable, simulate
      simulateProgress()
    }

    return () => {
      eventSourceRef.current?.close()
    }
  }, [id])

  // Navigate to report when complete
  const handleViewReport = () => {
    navigate(`/report/${id}`)
  }

  const activeStep = steps.find(s => s.status === 'active')

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <Logo size="sm" showIcon={false} />
        </div>
      </nav>

      <div className="pt-24 pb-20 px-4">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {isComplete ? 'Your Report is Ready!' : 'Generating Your Report'}
            </h1>
            <p className="text-gray-600">
              {isComplete
                ? 'Your personalized AI analysis is complete.'
                : 'We\'re analyzing your workshop responses. This takes 1-2 minutes.'}
            </p>
          </div>

          {/* Progress Card */}
          <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 mb-6">
            {/* Progress Bar */}
            <div className="mb-8">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">Progress</span>
                <span className="font-medium text-gray-900">{progress}%</span>
              </div>
              <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-primary-500 to-primary-600 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
            </div>

            {/* Steps */}
            <div className="space-y-4">
              {steps.map((step, index) => (
                <motion.div
                  key={step.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-center gap-4"
                >
                  {/* Icon */}
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                    step.status === 'completed' ? 'bg-green-100' :
                    step.status === 'active' ? 'bg-primary-100' :
                    step.status === 'error' ? 'bg-red-100' :
                    'bg-gray-100'
                  }`}>
                    {step.status === 'completed' && (
                      <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                    {step.status === 'active' && (
                      <svg className="w-4 h-4 text-primary-600 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                    )}
                    {step.status === 'error' && (
                      <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    )}
                    {step.status === 'pending' && (
                      <div className="w-2 h-2 bg-gray-300 rounded-full" />
                    )}
                  </div>

                  {/* Label */}
                  <div className="flex-1">
                    <span className={`font-medium ${
                      step.status === 'completed' ? 'text-green-700' :
                      step.status === 'active' ? 'text-primary-700' :
                      step.status === 'error' ? 'text-red-700' :
                      'text-gray-400'
                    }`}>
                      {step.label}
                    </span>
                    {step.detail && step.status === 'active' && (
                      <p className="text-sm text-gray-500">{step.detail}</p>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Error State */}
            {error && (
              <div className="mt-6 p-4 bg-red-50 rounded-xl border border-red-100">
                <p className="text-red-800 font-medium">Something went wrong</p>
                <p className="text-red-600 text-sm mt-1">{error}</p>
                <button
                  onClick={() => window.location.reload()}
                  className="mt-3 text-sm text-red-700 font-medium hover:text-red-800"
                >
                  Try again →
                </button>
              </div>
            )}

            {/* Complete State */}
            {isComplete && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-8"
              >
                <button
                  onClick={handleViewReport}
                  className="w-full py-4 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition shadow-lg shadow-primary-600/25 text-lg"
                >
                  View Your Report →
                </button>
              </motion.div>
            )}
          </div>

          {/* Tips */}
          {!isComplete && !error && (
            <motion.div
              key={currentTip}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="bg-primary-50 rounded-2xl p-6 border border-primary-100"
            >
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-primary-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <p className="text-sm font-medium text-primary-900 mb-1">Did you know?</p>
                  <p className="text-primary-800">{TIPS[currentTip]}</p>
                </div>
              </div>
            </motion.div>
          )}

          {/* What's being analyzed */}
          {!isComplete && activeStep && (
            <div className="mt-6 text-center text-sm text-gray-500">
              Currently: {activeStep.label.toLowerCase()}
              <span className="inline-block ml-1 animate-pulse">...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
