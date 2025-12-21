import { useState, useEffect, useRef, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useInterviewVoice } from '../hooks/useInterviewVoice'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8383'

// ============================================================================
// Types
// ============================================================================

interface Message {
  id: string
  role: 'assistant' | 'user'
  content: string
  timestamp: Date
}

interface InterviewContext {
  companyName: string
  companyProfile: Record<string, unknown>
  researchFindings: Array<{ field: string; value: string; confidence: string }>
  quizAnswers: Record<string, string | string[]>
}

type InterviewPhase = 'loading' | 'greeting' | 'conversation' | 'summary' | 'complete'
type InputMode = 'text' | 'voice'

// ============================================================================
// Component
// ============================================================================

export default function Interview() {
  const [searchParams] = useSearchParams()
  const sessionId = searchParams.get('session_id') || sessionStorage.getItem('quizSessionId')

  // Core state
  const [phase, setPhase] = useState<InterviewPhase>('loading')
  const [context, setContext] = useState<InterviewContext | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [currentInput, setCurrentInput] = useState('')
  const [inputMode, setInputMode] = useState<InputMode>('text')
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Progress tracking
  const [questionCount, setQuestionCount] = useState(0)
  const [estimatedProgress, setEstimatedProgress] = useState(0)
  const [topicsCovered, setTopicsCovered] = useState<string[]>([])

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Voice input hook (uses interview endpoint - no auth required)
  const {
    isRecording,
    isTranscribing,
    toggleRecording,
    error: voiceError
  } = useInterviewVoice({
    sessionId: sessionId || undefined,
    onTranscript: (text) => {
      setCurrentInput(text)
      // Auto-submit after transcription
      if (text.trim()) {
        handleSendMessage(text)
      }
    },
    onError: (err) => {
      setError(err)
    }
  })

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // ============================================================================
  // Load Context
  // ============================================================================

  useEffect(() => {
    const loadContext = async () => {
      try {
        // Try to get context from session storage first
        const savedProfile = sessionStorage.getItem('companyProfile')
        const savedFindings = sessionStorage.getItem('researchFindings')
        const savedAnswers = sessionStorage.getItem('quizAnswers')

        if (savedProfile) {
          const profile = JSON.parse(savedProfile)
          const findings = savedFindings ? JSON.parse(savedFindings) : []
          const answers = savedAnswers ? JSON.parse(savedAnswers) : {}

          setContext({
            companyName: profile?.basics?.name?.value || 'your company',
            companyProfile: profile,
            researchFindings: findings,
            quizAnswers: answers,
          })

          setPhase('greeting')

          // Generate initial greeting
          setTimeout(() => {
            generateGreeting(profile, findings, answers)
          }, 500)

          return
        }

        // If no session data, try to fetch from backend
        if (sessionId) {
          const response = await fetch(`${API_BASE_URL}/api/quiz/sessions/${sessionId}/research/status`)
          if (response.ok) {
            const data = await response.json()
            if (data.company_profile) {
              setContext({
                companyName: data.company_name || 'your company',
                companyProfile: data.company_profile,
                researchFindings: [], // Would need to extract
                quizAnswers: {},
              })
              setPhase('greeting')
              setTimeout(() => {
                generateGreeting(data.company_profile, [], {})
              }, 500)
              return
            }
          }
        }

        // No context available
        setError('Unable to load interview context. Please complete the quiz first.')

      } catch (err) {
        console.error('Failed to load context:', err)
        setError('Failed to load interview context.')
      }
    }

    loadContext()
  }, [sessionId])

  // ============================================================================
  // Message Handling
  // ============================================================================

  const generateGreeting = useCallback((
    profile: Record<string, unknown>,
    _findings: Array<{ field: string; value: string; confidence: string }>,
    _answers: Record<string, string | string[]>
  ) => {
    const companyName = (profile?.basics as Record<string, { value: string }>)?.name?.value || 'your company'
    const industry = (profile?.industry as Record<string, { value: string }>)?.primary_industry?.value || 'your industry'

    const greeting: Message = {
      id: 'greeting-1',
      role: 'assistant',
      content: `Welcome! I'm excited to dive deeper into ${companyName}'s AI opportunities.

Based on our initial research, I've gathered some insights about your ${industry} business. Now I'd like to have a conversation to really understand your specific situation.

This interview will take about 60-90 minutes, but you can take breaks whenever you need. You can type your responses or click the microphone to speak - whatever feels more natural.

Let's start with the big picture: **What's the main challenge or opportunity that brought you here today?**`,
      timestamp: new Date(),
    }

    setMessages([greeting])
    setPhase('conversation')
    setTopicsCovered(['introduction'])
  }, [])

  const handleSendMessage = useCallback(async (text?: string) => {
    const messageContent = text || currentInput.trim()
    if (!messageContent || isProcessing) return

    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: messageContent,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setCurrentInput('')
    setIsProcessing(true)

    try {
      // Send to backend for AI response
      const response = await fetch(`${API_BASE_URL}/api/interview/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: messageContent,
          context: {
            company_profile: context?.companyProfile,
            previous_messages: messages.slice(-10).map(m => ({
              role: m.role,
              content: m.content,
            })),
            question_count: questionCount,
            topics_covered: topicsCovered,
          },
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to get response')
      }

      const data = await response.json()

      // Add assistant response
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
      }

      setMessages(prev => [...prev, assistantMessage])
      setQuestionCount(prev => prev + 1)

      // Update progress
      if (data.topics_covered) {
        setTopicsCovered(data.topics_covered)
      }
      if (data.progress) {
        setEstimatedProgress(data.progress)
      }

      // Check if interview is complete
      if (data.is_complete) {
        setPhase('summary')
      }

    } catch (err) {
      console.error('Message error:', err)
      // Fallback response if backend fails
      const fallbackMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: "I understand. Can you tell me more about that? What specific aspects are most important to you?",
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, fallbackMessage])
    } finally {
      setIsProcessing(false)
    }
  }, [currentInput, isProcessing, sessionId, context, messages, questionCount, topicsCovered])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const completeInterview = useCallback(async () => {
    setIsProcessing(true)
    try {
      // Save interview data
      await fetch(`${API_BASE_URL}/api/interview/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          messages: messages.map(m => ({
            role: m.role,
            content: m.content,
            timestamp: m.timestamp.toISOString(),
          })),
          topics_covered: topicsCovered,
        }),
      })

      setPhase('complete')
    } catch (err) {
      console.error('Failed to complete interview:', err)
      setPhase('complete') // Continue anyway
    } finally {
      setIsProcessing(false)
    }
  }, [sessionId, messages, topicsCovered])

  // ============================================================================
  // Render: Loading
  // ============================================================================

  if (phase === 'loading') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-12 h-12 border-4 border-primary-600 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-600">Preparing your interview...</p>
        </div>
      </div>
    )
  }

  // ============================================================================
  // Render: Error
  // ============================================================================

  if (error && !context) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="max-w-md w-full bg-white rounded-2xl p-8 shadow-sm border border-gray-100 text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h1 className="text-xl font-bold text-gray-900 mb-2">Unable to Start Interview</h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <Link
            to="/quiz"
            className="inline-block px-6 py-3 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition"
          >
            Start Quiz
          </Link>
        </div>
      </div>
    )
  }

  // ============================================================================
  // Render: Complete
  // ============================================================================

  if (phase === 'complete') {
    return (
      <div className="min-h-screen bg-gray-50">
        <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
          <div className="max-w-6xl mx-auto px-4 py-4">
            <Link to="/" className="text-xl font-bold text-gray-900">
              CRB<span className="text-primary-600">Analyser</span>
            </Link>
          </div>
        </nav>

        <div className="pt-24 pb-20 px-4">
          <div className="max-w-2xl mx-auto text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>

              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                Interview Complete!
              </h1>

              <p className="text-lg text-gray-600 mb-8">
                Thank you for sharing so much valuable information about {context?.companyName}.
                We now have everything we need to create your comprehensive CRB report.
              </p>

              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 mb-8">
                <h3 className="font-semibold text-gray-900 mb-4">Topics We Covered</h3>
                <div className="flex flex-wrap gap-2 justify-center">
                  {topicsCovered.map((topic, i) => (
                    <span
                      key={i}
                      className="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm font-medium"
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              </div>

              <div className="bg-primary-50 rounded-2xl p-6 border border-primary-200">
                <h3 className="font-medium text-primary-900 mb-3">What happens next:</h3>
                <ol className="space-y-3 text-left max-w-md mx-auto">
                  <li className="flex gap-3">
                    <div className="w-6 h-6 rounded-full bg-primary-200 text-primary-800 flex items-center justify-center flex-shrink-0 text-sm font-semibold">
                      1
                    </div>
                    <span className="text-primary-800">Our AI analyzes your interview responses</span>
                  </li>
                  <li className="flex gap-3">
                    <div className="w-6 h-6 rounded-full bg-primary-200 text-primary-800 flex items-center justify-center flex-shrink-0 text-sm font-semibold">
                      2
                    </div>
                    <span className="text-primary-800">We generate your personalized CRB report</span>
                  </li>
                  <li className="flex gap-3">
                    <div className="w-6 h-6 rounded-full bg-primary-200 text-primary-800 flex items-center justify-center flex-shrink-0 text-sm font-semibold">
                      3
                    </div>
                    <span className="text-primary-800">You'll receive an email with your report link</span>
                  </li>
                </ol>
              </div>

              <p className="mt-8 text-gray-500">
                Estimated delivery: Within 24 hours
              </p>
            </motion.div>
          </div>
        </div>
      </div>
    )
  }

  // ============================================================================
  // Render: Conversation
  // ============================================================================

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link to="/" className="text-xl font-bold text-gray-900">
            CRB<span className="text-primary-600">Analyser</span>
          </Link>

          {/* Progress indicator */}
          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2">
              <span className="text-sm text-gray-500">Progress</span>
              <div className="w-24 h-2 bg-gray-200 rounded-full">
                <div
                  className="h-full bg-primary-600 rounded-full transition-all"
                  style={{ width: `${Math.min(100, estimatedProgress)}%` }}
                />
              </div>
              <span className="text-sm font-medium text-gray-700">{estimatedProgress}%</span>
            </div>

            {phase === 'summary' && (
              <button
                onClick={completeInterview}
                disabled={isProcessing}
                className="px-4 py-2 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 transition disabled:opacity-50"
              >
                {isProcessing ? 'Saving...' : 'Finish Interview'}
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* Messages */}
      <div className="flex-1 pt-20 pb-32 px-4 overflow-y-auto">
        <div className="max-w-3xl mx-auto space-y-4">
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-5 py-4 ${
                    message.role === 'user'
                      ? 'bg-primary-600 text-white'
                      : 'bg-white border border-gray-200 text-gray-900'
                  }`}
                >
                  {message.role === 'assistant' && (
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center">
                        <svg className="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                      </div>
                      <span className="text-sm font-medium text-primary-600">CRB Analyst</span>
                    </div>
                  )}
                  <div
                    className={`whitespace-pre-wrap ${message.role === 'assistant' ? 'prose prose-sm max-w-none' : ''}`}
                    dangerouslySetInnerHTML={{
                      __html: message.content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    }}
                  />
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Processing indicator */}
          {isProcessing && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-start"
            >
              <div className="bg-white border border-gray-200 rounded-2xl px-5 py-4">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input area */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-4 py-4">
        <div className="max-w-3xl mx-auto">
          {/* Input mode toggle */}
          <div className="flex justify-center mb-3">
            <div className="inline-flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setInputMode('text')}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition ${
                  inputMode === 'text' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'
                }`}
              >
                Type
              </button>
              <button
                onClick={() => setInputMode('voice')}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition ${
                  inputMode === 'voice' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'
                }`}
              >
                Speak
              </button>
            </div>
          </div>

          {inputMode === 'text' ? (
            /* Text input */
            <div className="flex gap-3">
              <textarea
                ref={textareaRef}
                value={currentInput}
                onChange={(e) => setCurrentInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your response... (Enter to send, Shift+Enter for new line)"
                className="flex-1 px-4 py-3 border border-gray-200 rounded-xl resize-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                rows={2}
                disabled={isProcessing}
              />
              <button
                onClick={() => handleSendMessage()}
                disabled={!currentInput.trim() || isProcessing}
                className={`px-5 py-3 rounded-xl font-medium transition ${
                  currentInput.trim() && !isProcessing
                    ? 'bg-primary-600 text-white hover:bg-primary-700'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                }`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          ) : (
            /* Voice input */
            <div className="flex flex-col items-center">
              <button
                onClick={toggleRecording}
                disabled={isProcessing || isTranscribing}
                className={`w-20 h-20 rounded-full flex items-center justify-center transition-all ${
                  isRecording
                    ? 'bg-red-500 hover:bg-red-600 animate-pulse'
                    : isTranscribing
                    ? 'bg-yellow-500 cursor-wait'
                    : 'bg-primary-600 hover:bg-primary-700'
                } ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {isTranscribing ? (
                  <svg className="w-8 h-8 text-white animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                ) : (
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                )}
              </button>
              <p className="mt-3 text-sm text-gray-600">
                {isRecording
                  ? 'Recording... Click to stop'
                  : isTranscribing
                  ? 'Transcribing...'
                  : 'Click to start speaking'}
              </p>
              {voiceError && (
                <p className="mt-2 text-sm text-red-600">{voiceError}</p>
              )}
            </div>
          )}

          {/* Topics covered indicator */}
          {topicsCovered.length > 1 && (
            <div className="mt-3 flex items-center gap-2 text-sm text-gray-500">
              <span>Topics covered:</span>
              <div className="flex flex-wrap gap-1">
                {topicsCovered.slice(1).map((topic, i) => (
                  <span key={i} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full text-xs">
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
