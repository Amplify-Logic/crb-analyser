/**
 * Workshop Page
 *
 * 90-minute deep voice interview after payment.
 * Structured sections with progress tracking and break functionality.
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
  section?: string
}

interface WorkshopSection {
  id: string
  title: string
  description: string
  estimatedMinutes: number
  topics: string[]
  completed: boolean
}

type InputMode = 'voice' | 'text'
type WorkshopPhase = 'welcome' | 'active' | 'paused' | 'processing-upload' | 'complete'

const WORKSHOP_SECTIONS: WorkshopSection[] = [
  {
    id: 'intro',
    title: 'Introduction',
    description: 'Confirm research findings and set the stage',
    estimatedMinutes: 10,
    topics: ['Company overview', 'Research validation', 'Goals for today'],
    completed: false,
  },
  {
    id: 'operations',
    title: 'Operations',
    description: 'Deep dive into day-to-day processes',
    estimatedMinutes: 20,
    topics: ['Daily workflows', 'Pain points', 'Time sinks', 'Manual tasks'],
    completed: false,
  },
  {
    id: 'technology',
    title: 'Technology',
    description: 'Current tools, integrations, and data',
    estimatedMinutes: 15,
    topics: ['Current tools', 'Integrations', 'Data sources', 'Technical debt'],
    completed: false,
  },
  {
    id: 'goals',
    title: 'Goals & Vision',
    description: 'What success looks like',
    estimatedMinutes: 15,
    topics: ['Business goals', 'Success metrics', 'Priorities', 'Timeline'],
    completed: false,
  },
  {
    id: 'budget',
    title: 'Budget & Resources',
    description: 'Investment capacity and constraints',
    estimatedMinutes: 15,
    topics: ['Budget range', 'Team capacity', 'Decision process', 'Constraints'],
    completed: false,
  },
  {
    id: 'wrapup',
    title: 'Wrap-up',
    description: 'Final thoughts and next steps',
    estimatedMinutes: 15,
    topics: ['Open questions', 'Priorities', 'Concerns', 'Excitement'],
    completed: false,
  },
]

// ============================================================================
// Component
// ============================================================================

export default function Workshop() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const sessionId = searchParams.get('session_id') || sessionStorage.getItem('quizSessionId')

  // Core state
  const [phase, setPhase] = useState<WorkshopPhase>('welcome')
  const [inputMode, setInputMode] = useState<InputMode>('voice')
  const [messages, setMessages] = useState<Message[]>([])
  const [currentInput, setCurrentInput] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [showUploader, setShowUploader] = useState(false)

  // Workshop state
  const [sections, setSections] = useState<WorkshopSection[]>(WORKSHOP_SECTIONS)
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0)
  const [startTime, setStartTime] = useState<Date | null>(null)
  const [elapsedMinutes, setElapsedMinutes] = useState(0)
  const [questionCount, setQuestionCount] = useState(0)

  // Context
  const [companyName, setCompanyName] = useState('')

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  const currentSection = sections[currentSectionIndex]

  // Load context from session storage
  useEffect(() => {
    const name = sessionStorage.getItem('companyName')
    if (name) setCompanyName(name)
  }, [])

  // Timer for elapsed time
  useEffect(() => {
    if (phase === 'active' && startTime) {
      timerRef.current = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime.getTime()) / 60000)
        setElapsedMinutes(elapsed)
      }, 60000)
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [phase, startTime])

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Calculate remaining time
  const totalEstimatedMinutes = sections.reduce((sum, s) => sum + s.estimatedMinutes, 0)
  const remainingMinutes = Math.max(0, totalEstimatedMinutes - elapsedMinutes)

  // Start workshop
  const startWorkshop = useCallback(() => {
    setPhase('active')
    setStartTime(new Date())

    const greeting: Message = {
      id: 'greeting-1',
      role: 'assistant',
      content: `Welcome to your CRB Workshop, ${companyName ? `I'm excited to dive deep into ${companyName}` : "I'm excited to learn more about your business"}.

We'll cover 6 areas over the next 90 minutes:
• Your operations and daily workflows
• Current technology and tools
• Goals and what success looks like
• Budget and resource considerations

**Let's start with the basics.** Can you give me a quick overview of what ${companyName || 'your company'} does and who your customers are?`,
      timestamp: new Date(),
      section: 'intro',
    }
    setMessages([greeting])
  }, [companyName])

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

      if (!transcribeResponse.ok) throw new Error('Transcription failed')

      const { text } = await transcribeResponse.json()
      if (text?.trim()) {
        await processUserMessage(text)
      } else {
        setIsProcessing(false)
      }
    } catch (err) {
      console.error('Voice processing error:', err)
      setIsProcessing(false)
    }
  }

  // Handle text submit
  const handleTextSubmit = async () => {
    const text = currentInput.trim()
    if (!text || isProcessing) return
    setCurrentInput('')
    await processUserMessage(text)
  }

  // Process user message
  const processUserMessage = async (text: string) => {
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
      section: currentSection.id,
    }
    setMessages(prev => [...prev, userMessage])
    setIsProcessing(true)

    try {
      const response = await fetch(`${API_BASE_URL}/api/interview/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: text,
          context: {
            company_name: companyName,
            current_section: currentSection.id,
            section_topics: currentSection.topics,
            previous_messages: messages.slice(-8).map(m => ({
              role: m.role,
              content: m.content,
            })),
            question_count: questionCount,
            is_workshop: true,
            elapsed_minutes: elapsedMinutes,
          },
        }),
      })

      if (!response.ok) throw new Error('Failed to get response')

      const data = await response.json()

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
        section: currentSection.id,
      }
      setMessages(prev => [...prev, assistantMessage])
      setQuestionCount(prev => prev + 1)

      // Check for section transition (every ~5 questions or explicit signal)
      if (data.section_complete || (questionCount > 0 && questionCount % 5 === 0)) {
        if (currentSectionIndex < sections.length - 1) {
          // Mark current section complete and move to next
          setTimeout(() => {
            advanceSection()
          }, 2000)
        }
      }

      // Check if workshop is complete
      if (data.is_complete || currentSectionIndex >= sections.length - 1 && questionCount > 3) {
        setTimeout(() => completeWorkshop(), 3000)
      }

    } catch (err) {
      console.error('Message error:', err)
      const fallback: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: "Thanks for sharing that. Tell me more about this area of your business.",
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, fallback])
    } finally {
      setIsProcessing(false)
    }
  }

  // Advance to next section
  const advanceSection = () => {
    setSections(prev =>
      prev.map((s, i) => (i === currentSectionIndex ? { ...s, completed: true } : s))
    )

    if (currentSectionIndex < sections.length - 1) {
      const nextIndex = currentSectionIndex + 1
      setCurrentSectionIndex(nextIndex)
      setQuestionCount(0)

      const nextSection = sections[nextIndex]
      const transitionMessage: Message = {
        id: `transition-${Date.now()}`,
        role: 'assistant',
        content: `Great progress! We've covered ${currentSection.title}.

**Now let's talk about ${nextSection.title}** - ${nextSection.description.toLowerCase()}.

${getOpeningQuestion(nextSection.id)}`,
        timestamp: new Date(),
        section: nextSection.id,
      }
      setMessages(prev => [...prev, transitionMessage])
    }
  }

  // Get opening question for each section
  const getOpeningQuestion = (sectionId: string): string => {
    const questions: Record<string, string> = {
      operations: "Walk me through a typical day at your company. What are the main activities your team does?",
      technology: "What tools and software does your team use daily? Any frustrations with your current setup?",
      goals: "Looking ahead 12 months, what does success look like for your business?",
      budget: "When it comes to investing in new tools or improvements, what's your typical decision-making process?",
      wrapup: "We've covered a lot of ground. What questions do you have, or what did we miss?",
    }
    return questions[sectionId] || "What else should I know about this area?"
  }

  // Handle audio upload
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
      sessionStorage.setItem('workshopTranscript', text)

      completeWorkshop()
    } catch (err) {
      console.error('Upload error:', err)
      setPhase('active')
    }
  }

  // Pause workshop
  const pauseWorkshop = () => {
    setPhase('paused')
    // Save state to session storage
    sessionStorage.setItem('workshopState', JSON.stringify({
      messages,
      currentSectionIndex,
      questionCount,
      elapsedMinutes,
      sections,
    }))
  }

  // Resume workshop
  const resumeWorkshop = () => {
    setPhase('active')
    const resumeMessage: Message = {
      id: `resume-${Date.now()}`,
      role: 'assistant',
      content: "Welcome back! Let's continue where we left off. What would you like to share next?",
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, resumeMessage])
  }

  // Complete workshop
  const completeWorkshop = () => {
    // Save all workshop data
    sessionStorage.setItem('workshopMessages', JSON.stringify(messages))
    sessionStorage.setItem('workshopCompleted', 'true')
    sessionStorage.setItem('workshopDuration', String(elapsedMinutes))

    setPhase('complete')

    // Navigate to report progress after brief delay
    setTimeout(() => {
      navigate(`/report/${sessionId}/progress`)
    }, 3000)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleTextSubmit()
    }
  }

  // ============================================================================
  // Render: Welcome
  // ============================================================================

  if (phase === 'welcome') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
          <div className="max-w-4xl mx-auto px-4 py-4 flex justify-between items-center">
            <Link to="/" className="text-xl font-bold text-gray-900">
              CRB<span className="text-primary-600">Analyser</span>
            </Link>
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
                Your CRB Workshop
              </h1>
              <p className="text-lg text-gray-600 mb-8">
                A 90-minute deep dive into {companyName || 'your business'} to create your personalized AI implementation roadmap.
              </p>

              {/* Workshop sections preview */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 mb-8 text-left">
                <h2 className="font-semibold text-gray-900 mb-4">What we'll cover:</h2>
                <div className="grid gap-3">
                  {sections.map((section, i) => (
                    <div key={section.id} className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center text-sm font-medium text-gray-600">
                        {i + 1}
                      </div>
                      <div>
                        <span className="font-medium text-gray-900">{section.title}</span>
                        <span className="text-gray-500 text-sm ml-2">~{section.estimatedMinutes} min</span>
                      </div>
                    </div>
                  ))}
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
                  Upload a recording of your discovery call or business discussion. Our AI will extract the key insights.
                </p>
                <AudioUploader
                  onAudioReady={handleAudioUpload}
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
          <p className="text-gray-600">This may take a few minutes for longer recordings.</p>
        </div>
      </div>
    )
  }

  // ============================================================================
  // Render: Paused
  // ============================================================================

  if (phase === 'paused') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="w-20 h-20 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Workshop Paused</h2>
          <p className="text-gray-600 mb-6">
            Take your time. Your progress has been saved and you can resume whenever you're ready.
          </p>
          <p className="text-sm text-gray-500 mb-8">
            Completed: {currentSectionIndex} of {sections.length} sections
            <br />
            Time elapsed: {elapsedMinutes} minutes
          </p>
          <button
            onClick={resumeWorkshop}
            className="px-8 py-4 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition"
          >
            Resume Workshop
          </button>
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
          <p className="text-gray-600 mb-4">Thank you for sharing so much about your business.</p>
          <div className="animate-pulse text-primary-600">Generating your personalized report...</div>
        </motion.div>
      </div>
    )
  }

  // ============================================================================
  // Render: Active Workshop
  // ============================================================================

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between mb-2">
            <Link to="/" className="text-xl font-bold text-gray-900">
              CRB<span className="text-primary-600">Analyser</span>
            </Link>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-500">
                ⏱️ ~{remainingMinutes} min left
              </span>
            </div>
          </div>

          {/* Section progress */}
          <div className="flex items-center gap-1">
            {sections.map((section, i) => (
              <div key={section.id} className="flex-1 flex items-center">
                <div
                  className={`h-1.5 flex-1 rounded-full transition-colors ${
                    section.completed
                      ? 'bg-green-500'
                      : i === currentSectionIndex
                      ? 'bg-primary-600'
                      : 'bg-gray-200'
                  }`}
                />
                {i < sections.length - 1 && <div className="w-1" />}
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-xs text-gray-500">{currentSection.title}</span>
            <span className="text-xs text-gray-500">
              {currentSectionIndex + 1}/{sections.length}
            </span>
          </div>
        </div>
      </nav>

      {/* Messages */}
      <div className="flex-1 pt-28 pb-48 px-4 overflow-y-auto">
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
          {/* Mode toggle and actions */}
          <div className="flex justify-between items-center mb-4">
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

            <div className="flex items-center gap-3">
              <button
                onClick={pauseWorkshop}
                className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Take a break
              </button>
              <button
                onClick={() => setShowUploader(true)}
                className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                Upload audio
              </button>
            </div>
          </div>

          {inputMode === 'voice' ? (
            <div className="flex flex-col items-center">
              <VoiceRecorder
                onRecordingComplete={handleVoiceRecording}
                size="medium"
                disabled={isProcessing}
              />
            </div>
          ) : (
            <div className="flex gap-3">
              <textarea
                ref={textareaRef}
                value={currentInput}
                onChange={(e) => setCurrentInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your response..."
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
                Upload Recording
              </h3>
              <p className="text-gray-600 text-sm mb-6">
                Have additional context from a call or meeting? Upload it here.
              </p>
              <AudioUploader
                onAudioReady={handleAudioUpload}
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
