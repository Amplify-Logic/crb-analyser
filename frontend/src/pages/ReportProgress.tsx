import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Logo } from '../components/Logo'
import { API_BASE } from '../services/apiClient'

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

const STEP_ORDER: ProgressStep['id'][] = ['intake', 'research', 'opportunities', 'roi', 'recommendations', 'roadmap']

const PHASE_TO_STEP: Record<string, ProgressStep['id']> = {
  loading: 'intake',
  waiting: 'intake',
  research: 'research',
  analysis: 'opportunities',
  findings: 'opportunities',
  review: 'opportunities',
  validation: 'roi',
  recommendations: 'recommendations',
  quick_wins: 'recommendations',
  roadmap: 'roadmap',
  playbooks: 'roadmap',
  architecture: 'roadmap',
  insights: 'roadmap',
  automation_summary: 'roadmap',
  post_report: 'roadmap',
  finalizing: 'roadmap',
}

const TIPS = [
  'Our AI analyzes over 500 data points from your responses.',
  'We compare your business against 50+ industry benchmarks.',
  'Each recommendation includes real vendor pricing.',
  'ROI calculations show all assumptions transparently.',
  "Your report includes 'build it yourself' alternatives.",
  'We tell you what NOT to do - that is often more valuable.',
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
  const [reportId, setReportId] = useState<string | null>(null)

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTip(prev => (prev + 1) % TIPS.length)
    }, 5000)
    return () => clearInterval(interval)
  }, [])

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

  const updateStepsFromPhase = (phase?: string, detail?: string) => {
    if (!phase) return
    const stepId = PHASE_TO_STEP[phase]
    if (!stepId) return

    const activeIndex = STEP_ORDER.indexOf(stepId)
    if (activeIndex < 0) return

    setSteps(prev =>
      prev.map((step, index) => {
        if (index < activeIndex) return { ...step, status: 'completed', detail: undefined }
        if (index === activeIndex) return { ...step, status: 'active', detail }
        return { ...step, status: 'pending', detail: undefined }
      })
    )
  }

  useEffect(() => {
    if (!id) {
      setError('Missing quiz session ID for report generation.')
      return
    }

    const checkStatusFallback = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/reports/status/${id}`, {
          credentials: 'include',
        })

        if (!response.ok) {
          throw new Error('Could not fetch report status')
        }

        const data = await response.json()
        if (typeof data.progress === 'number') {
          setProgress(data.progress)
        }

        if (data.report_id && ['completed', 'qa_pending', 'released'].includes(data.report_status)) {
          setReportId(data.report_id)
          setProgress(100)
          setSteps(prev => prev.map(step => ({ ...step, status: 'completed', detail: undefined })))
          setIsComplete(true)
          setError(null)
          return
        }

        updateStepsFromPhase(data.report_status || data.status, 'Live stream disconnected. Waiting for updates...')
        setError('Live update connection dropped. Your report is still processing; refresh to reconnect.')
      } catch {
        setError('Unable to connect to report updates. Please retry in a moment.')
      }
    }

    const eventSource = new EventSource(`${API_BASE}/api/reports/stream/${id}`, {
      withCredentials: true,
    })
    eventSourceRef.current = eventSource

    eventSource.onmessage = event => {
      try {
        const data = JSON.parse(event.data)
        const phase = data.phase as string | undefined
        const detail = data.step as string | undefined

        if (typeof data.progress === 'number') {
          setProgress(data.progress)
        }

        if (phase === 'complete') {
          setReportId(data.report_id || null)
          setProgress(100)
          setSteps(prev => prev.map(step => ({ ...step, status: 'completed', detail: undefined })))
          setIsComplete(true)
          setError(null)
          eventSource.close()
          return
        }

        if (phase === 'error') {
          setError(detail || 'Report generation failed.')
          setSteps(prev =>
            prev.map(step => {
              if (step.status === 'active') {
                return { ...step, status: 'error', detail: detail || step.detail }
              }
              return step
            })
          )
          eventSource.close()
          return
        }

        updateStepsFromPhase(phase, detail)
      } catch {
        setError('Received malformed progress update from server.')
        eventSource.close()
      }
    }

    eventSource.onerror = () => {
      eventSource.close()
      void checkStatusFallback()
    }

    return () => {
      eventSourceRef.current?.close()
    }
  }, [id])

  const handleViewReport = () => {
    navigate(`/report/${reportId || id}`)
  }

  const activeStep = steps.find(s => s.status === 'active')

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <Logo size="sm" showIcon={false} />
        </div>
      </nav>

      <div className="pt-24 pb-20 px-4">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {isComplete ? 'Your Report is Ready!' : 'Generating Your Report'}
            </h1>
            <p className="text-gray-600">
              {isComplete
                ? 'Your personalized AI analysis is complete.'
                : 'We are analyzing your workshop responses. This takes 1-2 minutes.'}
            </p>
          </div>

          <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 mb-6">
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

            <div className="space-y-4">
              {steps.map((step, index) => (
                <motion.div
                  key={step.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-center gap-4"
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      step.status === 'completed'
                        ? 'bg-green-100'
                        : step.status === 'active'
                          ? 'bg-primary-100'
                          : step.status === 'error'
                            ? 'bg-red-100'
                            : 'bg-gray-100'
                    }`}
                  >
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
                    {step.status === 'pending' && <div className="w-2 h-2 bg-gray-300 rounded-full" />}
                  </div>

                  <div className="flex-1">
                    <span
                      className={`font-medium ${
                        step.status === 'completed'
                          ? 'text-green-700'
                          : step.status === 'active'
                            ? 'text-primary-700'
                            : step.status === 'error'
                              ? 'text-red-700'
                              : 'text-gray-400'
                      }`}
                    >
                      {step.label}
                    </span>
                    {step.detail && step.status === 'active' && <p className="text-sm text-gray-500">{step.detail}</p>}
                  </div>
                </motion.div>
              ))}
            </div>

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

            {isComplete && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-8">
                <button
                  onClick={handleViewReport}
                  className="w-full py-4 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition shadow-lg shadow-primary-600/25 text-lg"
                >
                  View Your Report →
                </button>
              </motion.div>
            )}
          </div>

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
