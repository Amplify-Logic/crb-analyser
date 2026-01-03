/**
 * VoiceQuizInterview Page
 *
 * Voice-first ~5 minute interview with:
 * - Prominent question display that cycles
 * - AI voice responses (TTS)
 * - Visual progress through questions
 * - Summary phase with "anything else" opportunity
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import VoiceRecorder from '../components/voice/VoiceRecorder'
import AudioUploader from '../components/voice/AudioUploader'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8383'

// ============================================================================
// Types & Constants
// ============================================================================

interface Message {
  id: string
  role: 'assistant' | 'user'
  content: string
  timestamp: Date
}

interface QuizQuestion {
  id: number
  question: string
  topic: string
  followUp?: string // Optional follow-up based on answer
}

interface CompanyProfile {
  basics?: { name?: { value: string }; description?: { value: string } }
  industry?: { primary_industry?: { value: string }; business_model?: { value: string } }
  size?: { employee_range?: { value: string }; employee_count?: { value: string } }
}

// Dynamic question generator based on company profile
const generateQuestions = (profile: CompanyProfile | null, companyName: string): QuizQuestion[] => {
  const industry = profile?.industry?.primary_industry?.value || ''
  const teamSize = profile?.size?.employee_range?.value || profile?.size?.employee_count?.value || ''

  // Base questions - personalized where possible
  const questions: QuizQuestion[] = [
    {
      id: 1,
      question: companyName
        ? `I've done some research on ${companyName}. What brought you here today - what's the main thing you're hoping AI could help with?`
        : "What brought you here today? What's the main thing you're hoping AI could help with?",
      topic: "Goals"
    },
    {
      id: 2,
      question: teamSize
        ? `With a team of ${teamSize}, what's the biggest bottleneck or time-sink that slows you down?`
        : "What's the biggest bottleneck or time-sink that slows your team down?",
      topic: "Challenges"
    },
    {
      id: 3,
      question: "Walk me through a typical week - where does most of your team's time go?",
      topic: "Operations"
    },
    {
      id: 4,
      question: industry
        ? `In ${industry}, what software tools are essential for your day-to-day operations?`
        : "What software tools does your team rely on daily?",
      topic: "Technology"
    },
    {
      id: 5,
      question: "If you could wave a magic wand and automate one thing tomorrow, what would have the biggest impact?",
      topic: "Automation"
    },
  ]

  return questions
}

// Smart acknowledgments based on answer content
const getSmartAcknowledgment = (answer: string, topic: string): string => {
  const lowerAnswer = answer.toLowerCase()

  // Topic-specific acknowledgments
  if (topic === 'Challenges' || topic === 'Goals') {
    if (lowerAnswer.includes('time') || lowerAnswer.includes('hours') || lowerAnswer.includes('slow')) {
      return "Time is definitely one of the biggest constraints I hear about."
    }
    if (lowerAnswer.includes('manual') || lowerAnswer.includes('repetitive')) {
      return "Manual work is exactly the kind of thing AI excels at handling."
    }
    if (lowerAnswer.includes('customer') || lowerAnswer.includes('client') || lowerAnswer.includes('support')) {
      return "Customer-facing processes are often great candidates for AI assistance."
    }
  }

  if (topic === 'Technology') {
    if (lowerAnswer.includes('spreadsheet') || lowerAnswer.includes('excel') || lowerAnswer.includes('google sheet')) {
      return "Spreadsheets are a common starting point - there's usually a lot of room for automation there."
    }
    if (lowerAnswer.includes('crm') || lowerAnswer.includes('hubspot') || lowerAnswer.includes('salesforce')) {
      return "Good, CRM data is valuable for AI-powered insights."
    }
  }

  // Generic acknowledgments
  const acknowledgments = [
    "That's really helpful context.",
    "I see, that makes sense.",
    "Thanks for sharing that.",
    "Got it, that's useful to know.",
    "Interesting, I can see how that would be a priority.",
  ]
  return acknowledgments[Math.floor(Math.random() * acknowledgments.length)]
}

type Phase = 'intro' | 'conversation' | 'summary' | 'processing-upload' | 'complete'
type InputMode = 'voice' | 'text' | 'upload'

// ============================================================================
// Component
// ============================================================================

export default function VoiceQuizInterview() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const sessionId = searchParams.get('session_id') || sessionStorage.getItem('quizSessionId')

  // Core state
  const [phase, setPhase] = useState<Phase>('intro')
  const [inputMode, setInputMode] = useState<InputMode>('voice')
  const [messages, setMessages] = useState<Message[]>([])
  const [currentInput, setCurrentInput] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [showUploader, setShowUploader] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)

  // Question state
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<number, string>>({})

  // Context
  const [companyName, setCompanyName] = useState('')
  const [_companyProfile, setCompanyProfile] = useState<CompanyProfile | null>(null)
  const [questions, setQuestions] = useState<QuizQuestion[]>([])

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const currentQuestion = questions[currentQuestionIndex]
  const isLastQuestion = currentQuestionIndex >= questions.length - 1
  const progress = questions.length > 0
    ? ((currentQuestionIndex + 1) / (questions.length + 1)) * 100
    : 0

  // Load context and generate personalized questions
  useEffect(() => {
    const name = sessionStorage.getItem('companyName')
    const profileStr = sessionStorage.getItem('companyProfile')

    if (name) setCompanyName(name)

    let profile: CompanyProfile | null = null
    if (profileStr) {
      try {
        profile = JSON.parse(profileStr)
        setCompanyProfile(profile)
      } catch (e) {
        console.warn('Failed to parse company profile:', e)
      }
    }

    // Generate personalized questions
    const generatedQuestions = generateQuestions(profile, name || '')
    setQuestions(generatedQuestions)
  }, [])

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Speak text using ElevenLabs TTS API
  const speakText = useCallback(async (text: string) => {
    try {
      setIsSpeaking(true)

      const response = await fetch(`${API_BASE_URL}/api/interview/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // Uses ElevenLabs "Sarah" voice by default (conversational)
        // Other options: 21m00Tcm4TlvDq8ikWAM (Rachel), TxGEqnHWrfWFTfGW9XjX (Josh)
        body: JSON.stringify({ text }),
      })

      if (!response.ok) {
        console.warn('TTS not available, skipping voice')
        setIsSpeaking(false)
        return
      }

      const data = await response.json()

      // Create audio element and play
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

  // Start conversation with first question
  const startConversation = useCallback(async () => {
    if (questions.length === 0) return

    setPhase('conversation')

    const greeting = companyName
      ? `Thanks for sharing about ${companyName}. I have a few quick questions to understand your situation better.`
      : "Let's have a quick conversation to understand your business needs."
    const firstQuestion = questions[0].question

    const greetingMessage: Message = {
      id: 'greeting-1',
      role: 'assistant',
      content: `${greeting}\n\n**${firstQuestion}**`,
      timestamp: new Date(),
    }
    setMessages([greetingMessage])

    // Speak the greeting and question
    await speakText(`${greeting} ${firstQuestion}`)
  }, [companyName, questions, speakText])

  // Handle voice recording
  const handleVoiceRecording = async (audioBlob: Blob) => {
    setIsProcessing(true)

    try {
      const formData = new FormData()
      formData.append('audio', audioBlob, 'recording.webm')
      if (sessionId) formData.append('session_id', sessionId)

      const transcribeResponse = await fetch(`${API_BASE_URL}/api/interview/transcribe`, {
        method: 'POST',
        body: formData,
      })

      if (!transcribeResponse.ok) {
        const error = await transcribeResponse.json()
        console.error('Transcription error:', error)
        throw new Error('Transcription failed')
      }

      const { text } = await transcribeResponse.json()

      if (text?.trim()) {
        await processUserAnswer(text)
      } else {
        setIsProcessing(false)
      }
    } catch (err) {
      console.error('Voice processing error:', err)
      setIsProcessing(false)
    }
  }

  // Handle text submission
  const handleTextSubmit = async () => {
    const text = currentInput.trim()
    if (!text || isProcessing) return
    setCurrentInput('')
    await processUserAnswer(text)
  }

  // Process user answer and move to next question
  const processUserAnswer = async (text: string) => {
    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMessage])

    // Save answer
    setAnswers(prev => ({ ...prev, [currentQuestionIndex]: text }))

    // Check if we're in summary phase
    if (phase === 'summary') {
      await finishInterview(text)
      return
    }

    // Move to next question or summary
    if (isLastQuestion) {
      // Go to summary phase
      setPhase('summary')
      setIsProcessing(true)

      const summaryPrompt = "Thanks for sharing all that! Before we finish, is there anything else you'd like to add about your situation or goals?"

      const summaryMessage: Message = {
        id: `summary-${Date.now()}`,
        role: 'assistant',
        content: `**${summaryPrompt}**`,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, summaryMessage])
      setIsProcessing(false)

      // Speak summary prompt
      await speakText(summaryPrompt)
    } else {
      // Get AI acknowledgment and next question
      setIsProcessing(true)

      try {
        // Fire-and-forget: send message to backend for logging
        void fetch(`${API_BASE_URL}/api/interview/respond`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sessionId,
            message: text,
            context: {
              company_name: companyName,
              question_count: currentQuestionIndex,
              topics_covered: questions.slice(0, currentQuestionIndex + 1).map(q => q.topic),
              is_quiz: true,
            },
          }),
        })

        // Move to next question
        const nextIndex = currentQuestionIndex + 1
        setCurrentQuestionIndex(nextIndex)

        const nextQuestion = questions[nextIndex]

        // Generate smart acknowledgment based on what they said
        const ack = getSmartAcknowledgment(text, currentQuestion?.topic || '')

        const assistantMessage: Message = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: `${ack}\n\n**${nextQuestion.question}**`,
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, assistantMessage])

        // Speak acknowledgment and next question
        await speakText(`${ack} ${nextQuestion.question}`)

      } catch (err) {
        console.error('Response error:', err)
      } finally {
        setIsProcessing(false)
      }
    }
  }

  // Finish interview and go to preview
  const finishInterview = async (_finalAnswer?: string) => {
    setIsProcessing(true)

    // Save all data
    sessionStorage.setItem('quizAnswers', JSON.stringify(answers))
    sessionStorage.setItem('quizMessages', JSON.stringify(messages))
    sessionStorage.setItem('quizCompleted', 'true')

    // Add final message
    const finalMessage: Message = {
      id: `final-${Date.now()}`,
      role: 'assistant',
      content: "Excellent! I have everything I need. Let me analyze this and show you what AI opportunities we found...",
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, finalMessage])

    await speakText("Excellent! I have everything I need. Let me analyze this and show you what AI opportunities we found.")

    setPhase('complete')

    // Navigate to preview report
    setTimeout(() => {
      navigate(`/quiz/preview${sessionId ? `?session_id=${sessionId}` : ''}`)
    }, 2500)
  }

  // Handle uploaded audio
  const handleAudioUpload = async (audioBlob: Blob, source: 'upload' | 'recording') => {
    setShowUploader(false)
    setPhase('processing-upload')

    try {
      const formData = new FormData()
      formData.append('audio', audioBlob, source === 'upload' ? 'upload.mp3' : 'recording.webm')
      if (sessionId) formData.append('session_id', sessionId)

      const response = await fetch(`${API_BASE_URL}/api/interview/transcribe`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) throw new Error('Transcription failed')

      const { text } = await response.json()
      sessionStorage.setItem('quizTranscript', text)

      await finishInterview()
    } catch (err) {
      console.error('Upload error:', err)
      setPhase('conversation')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleTextSubmit()
    }
  }

  // Skip remaining questions
  const skipToPreview = () => {
    sessionStorage.setItem('quizAnswers', JSON.stringify(answers))
    sessionStorage.setItem('quizMessages', JSON.stringify(messages))
    sessionStorage.setItem('quizCompleted', 'true')
    navigate(`/quiz/preview${sessionId ? `?session_id=${sessionId}` : ''}`)
  }

  // ============================================================================
  // Render: Intro
  // ============================================================================

  if (phase === 'intro') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        {/* Hidden audio element for TTS */}
        <audio ref={audioRef} className="hidden" />

        <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
          <div className="max-w-4xl mx-auto px-4 py-4 flex justify-between items-center">
            <Link to="/" className="text-xl font-bold text-gray-900">
              CRB<span className="text-primary-600">Analyser</span>
            </Link>
            <span className="text-sm text-gray-500">~5 min interview</span>
          </div>
        </nav>

        <div className="pt-32 pb-20 px-4">
          <div className="max-w-xl mx-auto text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                We found a lot about {companyName || 'your company'}
              </h1>
              <p className="text-lg text-gray-600 mb-12">
                Now let's have a quick conversation to understand your specific situation.
              </p>

              {/* Main CTA */}
              <button
                onClick={startConversation}
                className="px-10 py-5 bg-primary-600 text-white text-xl font-semibold rounded-2xl hover:bg-primary-700 transition shadow-lg shadow-primary-600/25 flex items-center gap-4 mx-auto"
              >
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
                Start Voice Interview
              </button>

              {/* Alternative options */}
              <div className="mt-8">
                <button
                  onClick={() => {
                    setInputMode('text')
                    startConversation()
                  }}
                  className="text-gray-500 hover:text-gray-700 text-sm"
                >
                  prefer to type instead?
                </button>
              </div>

              {/* Divider */}
              <div className="flex items-center gap-4 my-10">
                <div className="flex-1 h-px bg-gray-200" />
                <span className="text-gray-400 text-sm">or</span>
                <div className="flex-1 h-px bg-gray-200" />
              </div>

              {/* Upload options */}
              <div className="flex justify-center gap-4">
                <button
                  onClick={() => setShowUploader(true)}
                  className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  Upload a recording
                </button>
                <button
                  onClick={() => setShowUploader(true)}
                  className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition"
                >
                  <div className="w-3 h-3 bg-red-500 rounded-full" />
                  Record a conversation
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
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Upload or Record a Meeting
                </h3>
                <AudioUploader
                  onAudioReady={handleAudioUpload}
                  onCancel={() => setShowUploader(false)}
                  maxDurationMinutes={30}
                />
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    )
  }

  // ============================================================================
  // Render: Processing Upload
  // ============================================================================

  if (phase === 'processing-upload') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
            className="w-16 h-16 border-4 border-primary-600 border-t-transparent rounded-full mx-auto mb-6"
          />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Processing your recording...</h2>
          <p className="text-gray-600">Our AI is transcribing and extracting insights.</p>
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
          className="text-center"
        >
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Great conversation!</h2>
          <p className="text-gray-600 mb-4">Let's see what opportunities we found...</p>
          <div className="animate-pulse text-primary-600">Generating your preview...</div>
        </motion.div>
      </div>
    )
  }

  // ============================================================================
  // Render: Conversation / Summary
  // ============================================================================

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Hidden audio element for TTS */}
      <audio ref={audioRef} className="hidden" />

      {/* Header with progress */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between mb-2">
            <Link to="/" className="text-xl font-bold text-gray-900">
              CRB<span className="text-primary-600">Analyser</span>
            </Link>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-500">
                {phase === 'summary' ? 'Final thoughts' : `Question ${currentQuestionIndex + 1} of ${questions.length}`}
              </span>
              <button
                onClick={skipToPreview}
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                Skip to results
              </button>
            </div>
          </div>

          {/* Progress bar */}
          <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-primary-600 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </nav>

      {/* Current Question - Prominent Display */}
      <div className="pt-24 px-4">
        <div className="max-w-2xl mx-auto">
          <motion.div
            key={currentQuestionIndex}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100 mb-6"
          >
            <div className="flex items-center gap-2 mb-4">
              <span className="text-sm font-medium text-primary-600 bg-primary-50 px-3 py-1 rounded-full">
                {phase === 'summary' ? 'Final Question' : currentQuestion?.topic}
              </span>
              {isSpeaking && (
                <span className="flex items-center gap-1 text-sm text-gray-500">
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  Speaking...
                </span>
              )}
            </div>
            <h2 className="text-2xl font-semibold text-gray-900 leading-relaxed">
              {phase === 'summary'
                ? "Is there anything else you'd like to add about your situation or goals?"
                : currentQuestion?.question}
            </h2>
          </motion.div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 px-4 pb-48 overflow-y-auto">
        <div className="max-w-2xl mx-auto space-y-4">
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
                  <div
                    className="whitespace-pre-wrap"
                    dangerouslySetInnerHTML={{
                      __html: message.content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    }}
                  />
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

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
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200">
        <div className="max-w-2xl mx-auto px-4 py-4">
          {/* Mode toggle */}
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

          {inputMode === 'voice' ? (
            <div className="flex flex-col items-center">
              <VoiceRecorder
                onRecordingComplete={handleVoiceRecording}
                size="medium"
                disabled={isProcessing || isSpeaking}
              />
              {isSpeaking && (
                <p className="mt-2 text-sm text-gray-500">Wait for the question to finish...</p>
              )}
            </div>
          ) : (
            <div className="flex gap-3">
              <textarea
                ref={textareaRef}
                value={currentInput}
                onChange={(e) => setCurrentInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your answer..."
                className="flex-1 px-4 py-3 border border-gray-200 rounded-xl resize-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                rows={2}
                disabled={isProcessing}
              />
              <button
                onClick={handleTextSubmit}
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
          )}

          {/* Finish button in summary phase */}
          {phase === 'summary' && (
            <div className="mt-4 text-center">
              <button
                onClick={() => finishInterview()}
                className="text-primary-600 hover:text-primary-700 font-medium"
              >
                Nothing else, let's see my results
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
