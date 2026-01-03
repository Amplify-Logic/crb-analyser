/**
 * AdaptiveQuiz Page
 *
 * The main adaptive quiz experience that:
 * - Displays confidence-based progress
 * - Renders dynamic questions (voice, text, structured)
 * - Adapts based on answers and research gaps
 * - Ends when confidence thresholds are met
 * - Supports resume from interrupted sessions
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import VoiceRecorder from '../components/voice/VoiceRecorder'
import StructuredInput from '../components/quiz/StructuredInput'
import ConfidenceProgress, { ConfidenceProgressMini } from '../components/quiz/ConfidenceProgress'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8383'

// Storage key for quiz state
const QUIZ_STATE_KEY = 'adaptiveQuizState'

// ============================================================================
// Types
// ============================================================================

interface AdaptiveQuestion {
  id: string
  question: string
  acknowledgment?: string
  question_type: 'structured' | 'voice'
  input_type: 'text' | 'number' | 'select' | 'multi_select' | 'scale' | 'voice'
  options?: Array<{ value: string; label: string; description?: string }>
  placeholder?: string
  target_categories: string[]
  is_deep_dive: boolean
  rationale?: string
}

interface ConfidenceData {
  scores: Record<string, number>
  thresholds: Record<string, number>
  gaps: string[]
  ready_for_teaser: boolean
  questions_asked: number
  facts_collected: number
}

interface AnalysisHint {
  detected_signals: string[]
  is_deep_dive: boolean
}

interface SavedQuizState {
  sessionId: string
  phase: Phase
  currentQuestion: AdaptiveQuestion | null
  confidence: ConfidenceData | null
  answeredQuestions: number
  companyName: string
  savedAt: number
}

type Phase = 'loading' | 'intro' | 'conversation' | 'complete' | 'resuming'
type InputMode = 'voice' | 'text' | 'structured'

// ============================================================================
// Utilities
// ============================================================================

// Retry wrapper for API calls
async function fetchWithRetry(
  url: string,
  options: RequestInit,
  maxRetries = 3,
  delayMs = 1000
): Promise<Response> {
  let lastError: Error | null = null

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await fetch(url, options)
      if (response.ok || response.status < 500) {
        return response
      }
      lastError = new Error(`Server error: ${response.status}`)
    } catch (err) {
      lastError = err instanceof Error ? err : new Error('Network error')
    }

    if (attempt < maxRetries - 1) {
      await new Promise(resolve => setTimeout(resolve, delayMs * (attempt + 1)))
    }
  }

  throw lastError || new Error('Request failed after retries')
}

// Save quiz state to sessionStorage
function saveQuizState(state: SavedQuizState) {
  try {
    sessionStorage.setItem(QUIZ_STATE_KEY, JSON.stringify(state))
  } catch (err) {
    console.warn('Failed to save quiz state:', err)
  }
}

// Load quiz state from sessionStorage
function loadQuizState(sessionId: string): SavedQuizState | null {
  try {
    const saved = sessionStorage.getItem(QUIZ_STATE_KEY)
    if (!saved) return null

    const state = JSON.parse(saved) as SavedQuizState

    // Only restore if same session and not too old (30 minutes)
    if (state.sessionId !== sessionId) return null
    if (Date.now() - state.savedAt > 30 * 60 * 1000) return null

    return state
  } catch (err) {
    console.warn('Failed to load quiz state:', err)
    return null
  }
}

// Clear saved quiz state
function clearQuizState() {
  try {
    sessionStorage.removeItem(QUIZ_STATE_KEY)
  } catch (err) {
    console.warn('Failed to clear quiz state:', err)
  }
}

// ============================================================================
// Component
// ============================================================================

export default function AdaptiveQuiz() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const sessionId = searchParams.get('session_id') || sessionStorage.getItem('quizSessionId')

  // Core state
  const [phase, setPhase] = useState<Phase>('loading')
  const [inputMode, setInputMode] = useState<InputMode>('voice')
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isSpeaking, setIsSpeaking] = useState(false)

  // Question state
  const [currentQuestion, setCurrentQuestion] = useState<AdaptiveQuestion | null>(null)
  const [inputValue, setInputValue] = useState<string | string[] | number>('')
  const [answeredQuestions, setAnsweredQuestions] = useState<number>(0)

  // Confidence state
  const [confidence, setConfidence] = useState<ConfidenceData | null>(null)
  const [lastAnalysis, setLastAnalysis] = useState<AnalysisHint | null>(null)

  // Context
  const [companyName, setCompanyName] = useState('')
  const [_industry, setIndustry] = useState('')

  // Resume state
  const [hasSavedState, setHasSavedState] = useState(false)
  const [savedState, setSavedState] = useState<SavedQuizState | null>(null)

  // Mobile UI state
  const [showMobileProgress, setShowMobileProgress] = useState(false)

  // Refs
  const audioRef = useRef<HTMLAudioElement | null>(null)

  // ============================================================================
  // State Persistence
  // ============================================================================

  // Save state whenever it changes
  useEffect(() => {
    if (sessionId && phase === 'conversation' && currentQuestion) {
      saveQuizState({
        sessionId,
        phase,
        currentQuestion,
        confidence,
        answeredQuestions,
        companyName,
        savedAt: Date.now(),
      })
    }
  }, [sessionId, phase, currentQuestion, confidence, answeredQuestions, companyName])

  // Check for saved state on mount
  useEffect(() => {
    if (!sessionId) return

    const savedState = loadQuizState(sessionId)
    if (savedState && savedState.phase === 'conversation' && savedState.currentQuestion) {
      setPhase('resuming')
      setHasSavedState(true)
      setSavedState(savedState)
    }
  }, [sessionId])

  // Resume from saved state
  const resumeFromSavedState = useCallback(() => {
    if (!savedState) return

    setCurrentQuestion(savedState.currentQuestion)
    setConfidence(savedState.confidence)
    setAnsweredQuestions(savedState.answeredQuestions)
    setCompanyName(savedState.companyName)
    setPhase('conversation')
    setHasSavedState(false)

    // Set input mode based on question type
    if (savedState.currentQuestion) {
      if (savedState.currentQuestion.input_type === 'voice') {
        setInputMode('voice')
      } else if (['select', 'multi_select', 'number', 'scale'].includes(savedState.currentQuestion.input_type)) {
        setInputMode('structured')
      } else {
        setInputMode('text')
      }
    }
  }, [savedState])

  // Start fresh (clear saved state)
  const startFresh = useCallback(() => {
    clearQuizState()
    setHasSavedState(false)
    setSavedState(null)
    setPhase('intro')
  }, [])

  // ============================================================================
  // API Calls
  // ============================================================================

  // Start the adaptive quiz
  const startAdaptiveQuiz = useCallback(async () => {
    if (!sessionId) {
      setError('No session found. Please start from the beginning.')
      return
    }

    try {
      setIsProcessing(true)
      setError(null)

      const response = await fetchWithRetry(
        `${API_BASE_URL}/api/quiz/adaptive/start`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionId }),
        }
      )

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to start quiz')
      }

      const data = await response.json()

      setCurrentQuestion(data.question)
      setConfidence(data.confidence)
      setCompanyName(data.company_name || sessionStorage.getItem('companyName') || '')
      setIndustry(data.industry || '')
      setPhase('conversation')

      // Determine initial input mode based on question type
      if (data.question.input_type === 'voice') {
        setInputMode('voice')
      } else if (['select', 'multi_select', 'number', 'scale'].includes(data.question.input_type)) {
        setInputMode('structured')
      } else {
        setInputMode('text')
      }

      // Speak the first question
      if (data.question.question) {
        await speakText(data.question.question)
      }

    } catch (err) {
      console.error('Start quiz error:', err)
      setError(err instanceof Error ? err.message : 'Failed to start quiz. Please try again.')
    } finally {
      setIsProcessing(false)
    }
  }, [sessionId])

  // Submit an answer and get next question
  const submitAnswer = useCallback(async (answer: string) => {
    if (!sessionId || !currentQuestion) return

    try {
      setIsProcessing(true)
      setError(null)

      const response = await fetchWithRetry(
        `${API_BASE_URL}/api/quiz/adaptive/answer`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sessionId,
            question_id: currentQuestion.id,
            answer: answer,
            answer_type: inputMode === 'voice' ? 'voice' : currentQuestion.input_type,
          }),
        }
      )

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to submit answer')
      }

      const data = await response.json()

      setConfidence(data.confidence)
      setAnsweredQuestions(prev => prev + 1)
      setInputValue('')

      if (data.complete) {
        // Quiz complete - clear saved state and go to preview
        clearQuizState()
        setPhase('complete')
        sessionStorage.setItem('quizCompleted', 'true')

        // Speak completion message
        await speakText("I have everything I need. Let me show you what AI opportunities we found for your business.")

        setTimeout(() => {
          navigate(data.redirect || `/quiz/preview?session_id=${sessionId}`)
        }, 2500)
      } else {
        // Set next question
        setCurrentQuestion(data.question)
        setLastAnalysis(data.analysis_hint)

        // Update input mode based on question type
        if (data.question.input_type === 'voice') {
          setInputMode('voice')
        } else if (['select', 'multi_select', 'number', 'scale'].includes(data.question.input_type)) {
          setInputMode('structured')
        } else {
          setInputMode('text')
        }

        // Speak acknowledgment + question
        const textToSpeak = data.question.acknowledgment
          ? `${data.question.acknowledgment} ${data.question.question}`
          : data.question.question
        await speakText(textToSpeak)
      }

    } catch (err) {
      console.error('Submit answer error:', err)
      setError(err instanceof Error ? err.message : 'Failed to submit answer. Please try again.')
    } finally {
      setIsProcessing(false)
    }
  }, [sessionId, currentQuestion, inputMode, navigate])

  // ============================================================================
  // TTS
  // ============================================================================

  const speakText = useCallback(async (text: string) => {
    try {
      setIsSpeaking(true)

      const response = await fetch(`${API_BASE_URL}/api/interview/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })

      if (!response.ok) {
        console.warn('TTS not available')
        setIsSpeaking(false)
        return
      }

      const data = await response.json()
      const audioSrc = `data:audio/mp3;base64,${data.audio}`

      if (audioRef.current) {
        audioRef.current.src = audioSrc
        audioRef.current.onended = () => setIsSpeaking(false)
        audioRef.current.onerror = () => setIsSpeaking(false)
        await audioRef.current.play()
      }
    } catch (err) {
      console.warn('TTS error:', err)
      setIsSpeaking(false)
    }
  }, [])

  // ============================================================================
  // Handlers
  // ============================================================================

  // Handle voice recording
  const handleVoiceRecording = async (audioBlob: Blob) => {
    setIsProcessing(true)

    try {
      const formData = new FormData()
      formData.append('audio', audioBlob, 'recording.webm')
      if (sessionId) formData.append('session_id', sessionId)

      const response = await fetch(`${API_BASE_URL}/api/interview/transcribe`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Transcription failed')
      }

      const { text } = await response.json()

      if (text?.trim()) {
        await submitAnswer(text)
      } else {
        setIsProcessing(false)
        setError('Could not understand. Please try again.')
      }
    } catch (err) {
      console.error('Voice processing error:', err)
      setError('Voice processing failed. Try typing instead.')
      setIsProcessing(false)
    }
  }

  // Handle structured input submit
  const handleStructuredSubmit = () => {
    if (!inputValue && inputValue !== 0) return

    const answer = Array.isArray(inputValue)
      ? inputValue.join(', ')
      : String(inputValue)

    submitAnswer(answer)
  }

  // Handle text input submit
  const handleTextSubmit = () => {
    if (typeof inputValue !== 'string' || !inputValue.trim()) return
    submitAnswer(inputValue.trim())
  }

  // Handle keyboard
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (inputMode === 'text') {
        handleTextSubmit()
      }
    }
  }

  // Skip to preview
  const skipToPreview = () => {
    sessionStorage.setItem('quizCompleted', 'partial')
    navigate(`/quiz/preview?session_id=${sessionId}`)
  }

  // ============================================================================
  // Effects
  // ============================================================================

  // Load context on mount
  useEffect(() => {
    const name = sessionStorage.getItem('companyName')
    if (name) setCompanyName(name)
  }, [])

  // Start quiz when session is ready (only if no saved state check is pending)
  useEffect(() => {
    if (sessionId && phase === 'loading' && !hasSavedState) {
      // Give time for the saved state check to complete
      const timer = setTimeout(() => {
        if (phase === 'loading') {
          setPhase('intro')
        }
      }, 100)
      return () => clearTimeout(timer)
    }
  }, [sessionId, phase, hasSavedState])

  // ============================================================================
  // Render: Loading
  // ============================================================================

  if (phase === 'loading') {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Skeleton header */}
        <div className="bg-white border-b border-gray-200 px-4 py-4">
          <div className="max-w-4xl mx-auto flex items-center justify-between">
            <div className="h-6 w-32 bg-gray-200 rounded animate-pulse" />
            <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
          </div>
        </div>

        {/* Skeleton content */}
        <div className="pt-16 pb-20 px-4">
          <div className="max-w-xl mx-auto text-center">
            <div className="w-20 h-20 bg-gray-200 rounded-full mx-auto mb-6 animate-pulse" />
            <div className="h-8 w-3/4 bg-gray-200 rounded mx-auto mb-4 animate-pulse" />
            <div className="h-4 w-full bg-gray-200 rounded mx-auto mb-2 animate-pulse" />
            <div className="h-4 w-5/6 bg-gray-200 rounded mx-auto mb-8 animate-pulse" />
            <div className="h-14 w-48 bg-gray-200 rounded-2xl mx-auto animate-pulse" />
          </div>
        </div>
      </div>
    )
  }

  // ============================================================================
  // Render: Resuming (offer to continue or start fresh)
  // ============================================================================

  if (phase === 'resuming' && hasSavedState && savedState) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        <audio ref={audioRef} className="hidden" />

        <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
          <div className="max-w-4xl mx-auto px-4 py-4 flex justify-between items-center">
            <Link to="/" className="text-xl font-bold text-gray-900">
              CRB<span className="text-primary-600">Analyser</span>
            </Link>
            <span className="text-sm text-gray-500">Resume Quiz</span>
          </div>
        </nav>

        <div className="pt-32 pb-20 px-4">
          <div className="max-w-xl mx-auto text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="w-20 h-20 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <svg className="w-10 h-10 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>

              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                Welcome back!
              </h1>

              <p className="text-lg text-gray-600 mb-8">
                You have an unfinished quiz for{' '}
                <span className="font-medium text-gray-900">{savedState.companyName || 'your company'}</span>.
                Would you like to continue where you left off?
              </p>

              {/* Progress summary */}
              {savedState.confidence && (
                <div className="bg-gray-50 rounded-xl p-6 mb-8">
                  <div className="text-sm text-gray-600 mb-3">
                    {savedState.answeredQuestions} questions answered
                  </div>
                  <ConfidenceProgressMini
                    scores={savedState.confidence.scores}
                    thresholds={savedState.confidence.thresholds}
                  />
                </div>
              )}

              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <button
                  onClick={resumeFromSavedState}
                  className="px-8 py-4 bg-primary-600 text-white text-lg font-semibold rounded-xl hover:bg-primary-700 transition shadow-lg shadow-primary-600/25"
                >
                  Continue Quiz
                </button>
                <button
                  onClick={startFresh}
                  className="px-8 py-4 bg-white text-gray-700 text-lg font-medium rounded-xl border-2 border-gray-200 hover:border-gray-300 transition"
                >
                  Start Over
                </button>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    )
  }

  // ============================================================================
  // Render: Intro
  // ============================================================================

  if (phase === 'intro') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        <audio ref={audioRef} className="hidden" />

        <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
          <div className="max-w-4xl mx-auto px-4 py-4 flex justify-between items-center">
            <Link to="/" className="text-xl font-bold text-gray-900">
              CRB<span className="text-primary-600">Analyser</span>
            </Link>
            <span className="text-sm text-gray-500">Adaptive Discovery</span>
          </div>
        </nav>

        <div className="pt-32 pb-20 px-4">
          <div className="max-w-xl mx-auto text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <svg className="w-10 h-10 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>

              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                {companyName
                  ? `Let's learn about ${companyName}`
                  : "Let's learn about your business"
                }
              </h1>

              <p className="text-lg text-gray-600 mb-8">
                I'll ask a few questions to understand your specific situation.
                The conversation adapts based on what matters most for your AI opportunities.
              </p>

              <div className="bg-gray-50 rounded-xl p-6 mb-8 text-left">
                <h3 className="font-semibold text-gray-900 mb-3">What to expect:</h3>
                <ul className="space-y-2 text-gray-600">
                  <li className="flex items-start gap-2">
                    <svg className="w-5 h-5 text-green-500 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span>5-10 questions (depends on your answers)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <svg className="w-5 h-5 text-green-500 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span>Mix of voice and quick-select questions</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <svg className="w-5 h-5 text-green-500 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span>Personalized based on what we already researched</span>
                  </li>
                </ul>
              </div>

              <button
                onClick={startAdaptiveQuiz}
                disabled={isProcessing}
                className="px-10 py-5 bg-primary-600 text-white text-xl font-semibold rounded-2xl hover:bg-primary-700 transition shadow-lg shadow-primary-600/25 flex items-center gap-4 mx-auto disabled:opacity-50"
              >
                {isProcessing ? (
                  <>
                    <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin" />
                    Starting...
                  </>
                ) : (
                  <>
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Start Discovery
                  </>
                )}
              </button>

              {error && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="mt-4 text-red-600"
                >
                  {error}
                </motion.p>
              )}
            </motion.div>
          </div>
        </div>
      </div>
    )
  }

  // ============================================================================
  // Render: Complete
  // ============================================================================

  if (phase === 'complete') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <audio ref={audioRef} className="hidden" />
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center px-4"
        >
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>

          <h2 className="text-2xl font-bold text-gray-900 mb-2">Discovery Complete!</h2>
          <p className="text-gray-600 mb-4">
            I've gathered everything I need about {companyName || 'your business'}.
          </p>

          {confidence && (
            <div className="max-w-sm mx-auto mb-6">
              <ConfidenceProgress
                scores={confidence.scores}
                thresholds={confidence.thresholds}
                gaps={[]}
                animated={false}
              />
            </div>
          )}

          <div className="animate-pulse text-primary-600">
            Generating your personalized report...
          </div>
        </motion.div>
      </div>
    )
  }

  // ============================================================================
  // Render: Conversation
  // ============================================================================

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <audio ref={audioRef} className="hidden" />

      {/* Header */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between mb-2">
            <Link to="/" className="text-xl font-bold text-gray-900">
              CRB<span className="text-primary-600">Analyser</span>
            </Link>

            <div className="flex items-center gap-4">
              {confidence && (
                <ConfidenceProgressMini
                  scores={confidence.scores}
                  thresholds={confidence.thresholds}
                />
              )}
              <button
                onClick={skipToPreview}
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                Skip to results
              </button>
            </div>
          </div>

          {/* Progress bar */}
          {confidence && (
            <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-primary-600 rounded-full"
                initial={{ width: 0 }}
                animate={{
                  width: `${Math.min(
                    (Object.values(confidence.scores).reduce((a, b) => a + b, 0) /
                    Object.values(confidence.thresholds).reduce((a, b) => a + b, 0)) * 100,
                    100
                  )}%`,
                }}
              />
            </div>
          )}
        </div>
      </nav>

      {/* Main content */}
      <div className="flex-1 pt-24 pb-48 px-4 overflow-y-auto">
        <div className="max-w-2xl mx-auto">
          {/* Current Question */}
          <AnimatePresence mode="wait">
            {currentQuestion && (
              <motion.div
                key={currentQuestion.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100 mb-6"
              >
                {/* Question metadata */}
                <div className="flex items-center gap-2 mb-4">
                  {currentQuestion.is_deep_dive && (
                    <span className="text-sm font-medium text-amber-600 bg-amber-50 px-3 py-1 rounded-full">
                      Follow-up
                    </span>
                  )}
                  {lastAnalysis?.detected_signals?.includes('pain_signal') && (
                    <span className="text-sm font-medium text-red-600 bg-red-50 px-3 py-1 rounded-full">
                      Pain point detected
                    </span>
                  )}
                  {isSpeaking && (
                    <span className="flex items-center gap-1 text-sm text-gray-500 ml-auto">
                      <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                      Speaking...
                    </span>
                  )}
                </div>

                {/* Acknowledgment */}
                {currentQuestion.acknowledgment && (
                  <p className="text-gray-600 mb-4 italic">
                    "{currentQuestion.acknowledgment}"
                  </p>
                )}

                {/* Question */}
                <h2 className="text-2xl font-semibold text-gray-900 leading-relaxed">
                  {currentQuestion.question}
                </h2>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Confidence sidebar on larger screens */}
          {confidence && (
            <div className="hidden lg:block fixed right-8 top-32 w-64 bg-white rounded-xl p-4 shadow-lg border border-gray-100">
              <ConfidenceProgress
                scores={confidence.scores}
                thresholds={confidence.thresholds}
                gaps={confidence.gaps}
                showLabels={true}
                animated={true}
              />
            </div>
          )}

          {/* Mobile progress toggle */}
          {confidence && (
            <div className="lg:hidden mb-4">
              <button
                onClick={() => setShowMobileProgress(!showMobileProgress)}
                className="w-full flex items-center justify-between bg-white rounded-xl p-4 border border-gray-200"
              >
                <span className="text-sm font-medium text-gray-700">
                  Discovery Progress
                </span>
                <div className="flex items-center gap-2">
                  <ConfidenceProgressMini
                    scores={confidence.scores}
                    thresholds={confidence.thresholds}
                  />
                  <svg
                    className={`w-5 h-5 text-gray-400 transition-transform ${showMobileProgress ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </button>

              <AnimatePresence>
                {showMobileProgress && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="bg-white border border-t-0 border-gray-200 rounded-b-xl p-4">
                      <ConfidenceProgress
                        scores={confidence.scores}
                        thresholds={confidence.thresholds}
                        gaps={confidence.gaps}
                        showLabels={true}
                        animated={false}
                      />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}

          {/* Error display with retry */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6"
              >
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-red-500 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="flex-1">
                    <p className="text-red-700">{error}</p>
                    <div className="flex gap-3 mt-3">
                      <button
                        onClick={() => {
                          setError(null)
                          // Retry the last action
                          if (currentQuestion) {
                            // Re-speak the question
                            speakText(currentQuestion.question)
                          }
                        }}
                        className="text-sm font-medium text-red-600 hover:text-red-700"
                      >
                        Try Again
                      </button>
                      <button
                        onClick={() => setError(null)}
                        className="text-sm text-red-500 hover:text-red-600"
                      >
                        Dismiss
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Input area */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200">
        <div className="max-w-2xl mx-auto px-4 py-4">
          {/* Mode toggle (only show if question allows multiple modes) */}
          {currentQuestion?.input_type === 'voice' && (
            <div className="flex justify-center mb-4">
              <div className="inline-flex bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setInputMode('voice')}
                  className={`px-4 py-1.5 rounded-md text-sm font-medium transition ${
                    inputMode === 'voice' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'
                  }`}
                >
                  Voice
                </button>
                <button
                  onClick={() => setInputMode('text')}
                  className={`px-4 py-1.5 rounded-md text-sm font-medium transition ${
                    inputMode === 'text' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'
                  }`}
                >
                  Type
                </button>
              </div>
            </div>
          )}

          {/* Voice input */}
          {inputMode === 'voice' && currentQuestion?.input_type === 'voice' && (
            <div className="flex flex-col items-center">
              <VoiceRecorder
                onRecordingComplete={handleVoiceRecording}
                size="medium"
                disabled={isProcessing || isSpeaking}
              />
              {isSpeaking && (
                <p className="mt-2 text-sm text-gray-500">Wait for the question to finish...</p>
              )}
              {isProcessing && (
                <p className="mt-2 text-sm text-primary-600">Processing your answer...</p>
              )}
            </div>
          )}

          {/* Text input */}
          {inputMode === 'text' && currentQuestion?.input_type === 'voice' && (
            <div className="flex gap-3">
              <textarea
                value={typeof inputValue === 'string' ? inputValue : ''}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your answer..."
                className="flex-1 px-4 py-3 border border-gray-200 rounded-xl resize-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                rows={2}
                disabled={isProcessing}
              />
              <button
                onClick={handleTextSubmit}
                disabled={!inputValue || isProcessing}
                className={`px-5 py-3 rounded-xl font-medium transition ${
                  inputValue && !isProcessing
                    ? 'bg-primary-600 text-white hover:bg-primary-700'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                }`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          )}

          {/* Structured input */}
          {(inputMode === 'structured' || (currentQuestion && ['select', 'multi_select', 'number', 'scale', 'text'].includes(currentQuestion.input_type) && currentQuestion.input_type !== 'voice')) && currentQuestion && (
            <StructuredInput
              inputType={currentQuestion.input_type as 'select' | 'multi_select' | 'number' | 'scale' | 'text'}
              options={currentQuestion.options}
              placeholder={currentQuestion.placeholder}
              value={inputValue}
              onChange={setInputValue}
              onSubmit={handleStructuredSubmit}
              disabled={isProcessing}
            />
          )}

          {/* Question count */}
          {confidence && (
            <div className="mt-4 text-center text-sm text-gray-500">
              {answeredQuestions} {answeredQuestions === 1 ? 'question' : 'questions'} answered
              {confidence.facts_collected > 0 && ` · ${confidence.facts_collected} insights gathered`}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
