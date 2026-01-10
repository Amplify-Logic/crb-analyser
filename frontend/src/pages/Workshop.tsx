/**
 * Workshop Page
 *
 * Personalized 90-minute workshop with 3 phases:
 * 1. Confirmation - Verify research findings and prioritize pain points
 * 2. Deep-Dive - Adaptive questioning for each pain point with milestones
 * 3. Synthesis - Final questions and transition to report generation
 */

import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  WorkshopConfirmation,
  WorkshopDeepDive,
  WorkshopMilestone,
  SynthesisForm,
  ConfirmationCard,
} from '../components/workshop'
import AudioUploader from '../components/voice/AudioUploader'
import { Logo } from '../components/Logo'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8383'

// =============================================================================
// Types
// =============================================================================

type WorkshopPhase = 'loading' | 'welcome' | 'confirmation' | 'deepdive' | 'milestone' | 'synthesis' | 'complete'

interface PainPoint {
  id: string
  label: string
}

interface WorkshopState {
  companyName: string
  confirmationCards: ConfirmationCard[]
  painPoints: PainPoint[]
  detectedSignals: {
    technical: boolean
    budgetReady: boolean
    decisionMaker: boolean
  }
  priorityOrder: string[]
  currentPainPointIndex: number
  milestonePainPointId: string | null
}

// =============================================================================
// Component
// =============================================================================

export default function Workshop() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const sessionId = searchParams.get('session_id') || sessionStorage.getItem('quizSessionId')

  // Phase state
  const [phase, setPhase] = useState<WorkshopPhase>('loading')
  const [error, setError] = useState<string | null>(null)

  // Workshop state
  const [state, setState] = useState<WorkshopState>({
    companyName: '',
    confirmationCards: [],
    painPoints: [],
    detectedSignals: { technical: false, budgetReady: false, decisionMaker: false },
    priorityOrder: [],
    currentPainPointIndex: 0,
    milestonePainPointId: null,
  })

  // Upload modal
  const [showUploader, setShowUploader] = useState(false)

  // Initialize workshop
  useEffect(() => {
    if (!sessionId) {
      navigate('/quiz')
      return
    }

    initializeWorkshop()
  }, [sessionId])

  const initializeWorkshop = async () => {
    try {
      // Try to get existing workshop state
      const stateResponse = await fetch(`${API_BASE_URL}/api/workshop/state/${sessionId}`)

      if (stateResponse.ok) {
        const existingState = await stateResponse.json()

        if (existingState.phase && existingState.phase !== 'confirmation') {
          // Resume existing workshop
          const workshopData = existingState.workshop_data || {}

          setState(prev => ({
            ...prev,
            companyName: existingState.company_name,
            priorityOrder: workshopData.deep_dive_order || [],
            currentPainPointIndex: workshopData.current_deep_dive_index || 0,
            painPoints: (workshopData.deep_dive_order || []).map((id: string, i: number) => ({
              id,
              label: `Pain Point ${i + 1}`,
            })),
          }))

          setPhase(existingState.phase as WorkshopPhase)
          return
        }
      }

      // Start new workshop
      setPhase('welcome')
    } catch (err) {
      console.error('Initialize error:', err)
      setPhase('welcome')
    }
  }

  // Start workshop (called from welcome screen)
  const startWorkshop = async () => {
    setPhase('loading')
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/api/workshop/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId }),
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Failed to start workshop')
      }

      const data = await response.json()

      // Transform API response
      const cards: ConfirmationCard[] = (data.confirmation_cards || []).map((card: any) => ({
        category: card.category,
        title: card.title,
        items: card.items,
        sourceCount: card.source_count,
        editable: card.editable,
      }))

      const painPoints: PainPoint[] = (data.pain_points || []).map((pp: any) => ({
        id: pp.id,
        label: pp.label,
      }))

      setState(prev => ({
        ...prev,
        companyName: data.company_name,
        confirmationCards: cards,
        painPoints,
        detectedSignals: {
          technical: data.detected_signals?.technical || false,
          budgetReady: data.detected_signals?.budget_ready || false,
          decisionMaker: data.detected_signals?.decision_maker || false,
        },
      }))

      setPhase('confirmation')
    } catch (err: any) {
      console.error('Start error:', err)
      setError(err.message || 'Failed to start workshop')
      setPhase('welcome')
    }
  }

  // Handle confirmation complete
  const handleConfirmationComplete = async (data: {
    ratings: Record<string, string>
    corrections: any[]
    priorityOrder: string[]
  }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/workshop/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          ratings: data.ratings,
          corrections: data.corrections,
          priority_order: data.priorityOrder,
        }),
      })

      if (!response.ok) throw new Error('Failed to save confirmation')

      // Update pain points based on priority order
      const orderedPainPoints = data.priorityOrder.map((id, index) => {
        const existing = state.painPoints.find(pp => pp.id === id)
        return existing || { id, label: `Pain Point ${index + 1}` }
      })

      setState(prev => ({
        ...prev,
        priorityOrder: data.priorityOrder,
        painPoints: orderedPainPoints,
        currentPainPointIndex: 0,
      }))

      setPhase('deepdive')
    } catch (err) {
      console.error('Confirm error:', err)
    }
  }

  // Handle milestone ready
  const handleMilestoneReady = (painPointId: string) => {
    setState(prev => ({
      ...prev,
      milestonePainPointId: painPointId,
    }))
    setPhase('milestone')
  }

  // Handle milestone continue
  const handleMilestoneContinue = () => {
    const nextIndex = state.currentPainPointIndex + 1

    if (nextIndex >= state.painPoints.length) {
      // All pain points done, go to synthesis
      setPhase('synthesis')
    } else {
      setState(prev => ({
        ...prev,
        currentPainPointIndex: nextIndex,
        milestonePainPointId: null,
      }))
      setPhase('deepdive')
    }
  }

  // Handle deep-dive complete
  const handleDeepDiveComplete = () => {
    setPhase('synthesis')
  }

  // Handle workshop complete
  const handleComplete = async (finalAnswers: Record<string, any>) => {
    setPhase('loading')

    try {
      const response = await fetch(`${API_BASE_URL}/api/workshop/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          final_answers: finalAnswers,
        }),
      })

      if (!response.ok) throw new Error('Failed to complete workshop')

      setPhase('complete')

      // Navigate to report after delay
      setTimeout(() => {
        navigate(`/report/${sessionId}/progress`)
      }, 3000)
    } catch (err) {
      console.error('Complete error:', err)
    }
  }

  // Handle audio upload (bypass workshop)
  const handleAudioUpload = async (audioBlob: Blob) => {
    setShowUploader(false)
    setPhase('loading')

    try {
      const formData = new FormData()
      formData.append('audio', audioBlob, 'upload.mp3')
      if (sessionId) formData.append('session_id', sessionId)

      const response = await fetch(`${API_BASE_URL}/api/interview/transcribe`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) throw new Error('Transcription failed')

      // Complete workshop with uploaded audio
      await handleComplete({ audio_upload: true })
    } catch (err) {
      console.error('Upload error:', err)
      setPhase('welcome')
    }
  }

  // ==========================================================================
  // Render: Loading
  // ==========================================================================

  if (phase === 'loading') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
            className="w-16 h-16 border-4 border-primary-600 border-t-transparent rounded-full mx-auto mb-6"
          />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Preparing your workshop...
          </h2>
        </div>
      </div>
    )
  }

  // ==========================================================================
  // Render: Welcome
  // ==========================================================================

  if (phase === 'welcome') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
          <div className="max-w-4xl mx-auto px-4 py-4 flex justify-between items-center">
            <Logo size="sm" showIcon={false} />
            <span className="text-sm text-gray-500">Workshop</span>
          </div>
        </nav>

        <div className="pt-32 pb-20 px-4">
          <div className="max-w-2xl mx-auto text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="w-20 h-20 bg-primary-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <svg className="w-10 h-10 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              </div>

              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                Your Personalized Workshop
              </h1>
              <p className="text-lg text-gray-600 mb-8">
                A 90-minute deep dive to create your AI implementation roadmap.
              </p>

              {error && (
                <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg mb-6">
                  {error}
                </div>
              )}

              {/* Workshop phases preview */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 mb-8 text-left">
                <h2 className="font-semibold text-gray-900 mb-4">What we'll do:</h2>
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center text-sm font-medium text-primary-600">
                      1
                    </div>
                    <div>
                      <span className="font-medium text-gray-900">Confirm our research</span>
                      <p className="text-sm text-gray-500">Verify what we know and prioritize your challenges</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center text-sm font-medium text-primary-600">
                      2
                    </div>
                    <div>
                      <span className="font-medium text-gray-900">Deep-dive each pain point</span>
                      <p className="text-sm text-gray-500">Explore costs, attempts, and ideal outcomes</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center text-sm font-medium text-primary-600">
                      3
                    </div>
                    <div>
                      <span className="font-medium text-gray-900">Generate your roadmap</span>
                      <p className="text-sm text-gray-500">Personalized recommendations with ROI</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Start button */}
              <button
                onClick={startWorkshop}
                className="px-8 py-4 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition shadow-lg shadow-primary-600/25 text-lg flex items-center gap-3 mx-auto"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Begin Workshop
              </button>

              {/* Upload option */}
              <div className="mt-8">
                <p className="text-gray-500 text-sm mb-3">Already had a discovery call?</p>
                <button
                  onClick={() => setShowUploader(true)}
                  className="text-primary-600 hover:text-primary-700 font-medium text-sm"
                >
                  Upload your meeting recording instead
                </button>
              </div>
            </motion.div>
          </div>
        </div>

        {/* Upload modal */}
        <AnimatePresence>
          {showUploader && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
              onClick={() => setShowUploader(false)}
            >
              <motion.div
                initial={{ scale: 0.95 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0.95 }}
                className="bg-white rounded-2xl p-6 max-w-md w-full"
                onClick={e => e.stopPropagation()}
              >
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Upload Meeting Recording
                </h3>
                <p className="text-gray-600 text-sm mb-6">
                  Upload a recording of your discovery call. Our AI will extract the key insights.
                </p>
                <AudioUploader
                  onAudioReady={(blob) => handleAudioUpload(blob)}
                  onCancel={() => setShowUploader(false)}
                  maxDurationMinutes={120}
                />
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    )
  }

  // ==========================================================================
  // Render: Confirmation (Phase 1)
  // ==========================================================================

  if (phase === 'confirmation') {
    return (
      <WorkshopConfirmation
        companyName={state.companyName}
        cards={state.confirmationCards}
        painPoints={state.painPoints}
        onComplete={handleConfirmationComplete}
      />
    )
  }

  // ==========================================================================
  // Render: Deep-Dive (Phase 2)
  // ==========================================================================

  if (phase === 'deepdive') {
    return (
      <WorkshopDeepDive
        sessionId={sessionId!}
        companyName={state.companyName}
        painPoints={state.painPoints}
        currentPainPointIndex={state.currentPainPointIndex}
        onMilestoneReady={handleMilestoneReady}
        onComplete={handleDeepDiveComplete}
      />
    )
  }

  // ==========================================================================
  // Render: Milestone
  // ==========================================================================

  if (phase === 'milestone' && state.milestonePainPointId) {
    const currentPainPoint = state.painPoints.find(pp => pp.id === state.milestonePainPointId)
    const isLast = state.currentPainPointIndex >= state.painPoints.length - 1

    return (
      <WorkshopMilestone
        sessionId={sessionId!}
        painPointId={state.milestonePainPointId}
        painPointLabel={currentPainPoint?.label || 'Pain Point'}
        isLastPainPoint={isLast}
        onContinue={handleMilestoneContinue}
        onEdit={() => setPhase('deepdive')}
      />
    )
  }

  // ==========================================================================
  // Render: Synthesis (Phase 3)
  // ==========================================================================

  if (phase === 'synthesis') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white pb-32">
        <div className="bg-white border-b border-gray-100">
          <div className="max-w-3xl mx-auto px-4 py-6">
            <h1 className="text-xl font-bold text-gray-900">Final Questions</h1>
            <p className="text-sm text-gray-500">Just a few more details for your report</p>
          </div>
        </div>

        <div className="max-w-3xl mx-auto px-4 py-8">
          <SynthesisForm onComplete={handleComplete} />
        </div>
      </div>
    )
  }

  // ==========================================================================
  // Render: Complete
  // ==========================================================================

  if (phase === 'complete') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Workshop Complete!</h2>
          <p className="text-gray-600 mb-4">Thank you for the deep insights.</p>
          <div className="animate-pulse text-primary-600">Generating your personalized report...</div>
        </motion.div>
      </div>
    )
  }

  // Fallback
  return null
}
