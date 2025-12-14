import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import apiClient from '../services/apiClient'

interface Audit {
  id: string
  title: string
  status: string
  current_phase: string
  progress_percent: number
  client_name?: string
  ai_readiness_score?: number
  total_findings?: number
}

interface ProgressUpdate {
  phase: string
  step: string
  progress: number
  message?: string
  tool?: string
}

const PHASE_INFO: Record<string, { title: string; description: string; icon: string }> = {
  discovery: {
    title: 'Discovery',
    description: 'Analyzing your intake responses and mapping business processes',
    icon: '1',
  },
  research: {
    title: 'Research',
    description: 'Researching industry benchmarks and vendor solutions',
    icon: '2',
  },
  analysis: {
    title: 'Analysis',
    description: 'Scoring automation potential and identifying opportunities',
    icon: '3',
  },
  modeling: {
    title: 'Modeling',
    description: 'Calculating ROI and building recommendations',
    icon: '4',
  },
  report: {
    title: 'Report Generation',
    description: 'Creating your comprehensive CRB report',
    icon: '5',
  },
}

export default function AuditProgress() {
  const { id: auditId } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [audit, setAudit] = useState<Audit | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [currentPhase, setCurrentPhase] = useState('discovery')
  const [progress, setProgress] = useState(0)
  const [steps, setSteps] = useState<string[]>([])

  const eventSourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (auditId) {
      loadAudit()
      connectSSE()
    }

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [auditId])

  async function loadAudit() {
    try {
      const { data } = await apiClient.get<Audit>(`/api/audits/${auditId}`)
      setAudit(data)
      setCurrentPhase(data.current_phase)
      setProgress(data.progress_percent)

      // If already completed, redirect to report
      if (data.status === 'completed') {
        navigate(`/audit/${auditId}/report`)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load audit')
    } finally {
      setLoading(false)
    }
  }

  function connectSSE() {
    const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8383'
    const eventSource = new EventSource(
      `${apiBase}/api/audits/${auditId}/stream`,
      { withCredentials: true }
    )

    eventSource.onmessage = (event) => {
      try {
        const data: ProgressUpdate = JSON.parse(event.data)

        if (data.phase) {
          setCurrentPhase(data.phase)
        }

        if (data.progress !== undefined) {
          setProgress(data.progress)
        }

        if (data.step) {
          setSteps((prev) => [...prev.slice(-9), data.step])
        }

        // Handle completion
        if (data.phase === 'complete') {
          eventSource.close()
          navigate(`/audit/${auditId}/report`)
        }
      } catch (err) {
        console.error('Failed to parse SSE data:', err)
      }
    }

    eventSource.onerror = () => {
      // Retry connection after delay
      setTimeout(() => {
        if (eventSourceRef.current) {
          connectSSE()
        }
      }, 5000)
    }

    eventSourceRef.current = eventSource
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <Link to="/dashboard" className="text-primary-600 hover:underline">
            Back to Dashboard
          </Link>
        </div>
      </div>
    )
  }

  const phaseInfo = PHASE_INFO[currentPhase] || PHASE_INFO.discovery

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-900 via-primary-800 to-primary-900">
      <div className="max-w-2xl mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center text-white mb-12">
          <h1 className="text-3xl font-bold mb-2">Analyzing Your Business</h1>
          <p className="text-primary-200">
            {audit?.client_name} - {audit?.title}
          </p>
        </div>

        {/* Progress card */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
          {/* Phase indicator */}
          <div className="flex items-center justify-center mb-8">
            <div className="flex items-center">
              {Object.entries(PHASE_INFO).map(([key, info], index) => (
                <div key={key} className="flex items-center">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                      key === currentPhase
                        ? 'bg-primary-600 text-white'
                        : Object.keys(PHASE_INFO).indexOf(key) <
                          Object.keys(PHASE_INFO).indexOf(currentPhase)
                        ? 'bg-green-500 text-white'
                        : 'bg-gray-200 text-gray-500'
                    }`}
                  >
                    {Object.keys(PHASE_INFO).indexOf(key) <
                    Object.keys(PHASE_INFO).indexOf(currentPhase) ? (
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    ) : (
                      info.icon
                    )}
                  </div>
                  {index < Object.keys(PHASE_INFO).length - 1 && (
                    <div
                      className={`w-8 h-1 ${
                        Object.keys(PHASE_INFO).indexOf(key) <
                        Object.keys(PHASE_INFO).indexOf(currentPhase)
                          ? 'bg-green-500'
                          : 'bg-gray-200'
                      }`}
                    />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Current phase info */}
          <div className="text-center mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              {phaseInfo.title}
            </h2>
            <p className="text-gray-600">{phaseInfo.description}</p>
          </div>

          {/* Progress bar */}
          <div className="mb-8">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>Progress</span>
              <span>{progress}%</span>
            </div>
            <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-primary-500 to-primary-600 transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Activity log */}
          <div className="bg-gray-50 rounded-xl p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-3">
              Activity Log
            </h3>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {steps.length === 0 ? (
                <div className="flex items-center text-sm text-gray-500">
                  <div className="w-2 h-2 bg-primary-600 rounded-full animate-pulse mr-2" />
                  Initializing analysis...
                </div>
              ) : (
                steps.map((step, i) => (
                  <div
                    key={i}
                    className={`flex items-center text-sm ${
                      i === steps.length - 1
                        ? 'text-gray-900 font-medium'
                        : 'text-gray-500'
                    }`}
                  >
                    {i === steps.length - 1 && (
                      <div className="w-2 h-2 bg-primary-600 rounded-full animate-pulse mr-2" />
                    )}
                    {i !== steps.length - 1 && (
                      <svg
                        className="w-4 h-4 text-green-500 mr-2"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}
                    {step}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Tip */}
        <div className="text-center text-primary-200 text-sm">
          <p>
            This typically takes 3-5 minutes. You can leave this page and we'll
            email you when it's ready.
          </p>
        </div>
      </div>
    </div>
  )
}
