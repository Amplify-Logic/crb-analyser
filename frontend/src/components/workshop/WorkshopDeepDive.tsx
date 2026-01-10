/**
 * WorkshopDeepDive - Phase 2 of the personalized workshop
 *
 * Handles adaptive deep-dive conversations for each pain point.
 * Shows progress through pain points and conversation stages.
 * Triggers milestone summary when a deep-dive is complete.
 */

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import VoiceRecorder from '../voice/VoiceRecorder'
import { sanitizeHtml } from '../../utils/sanitize'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8383'

// =============================================================================
// Types
// =============================================================================

interface Message {
  id: string
  role: 'assistant' | 'user'
  content: string
  timestamp: Date
}

interface PainPoint {
  id: string
  label: string
}

interface ConfidenceUpdate {
  currentPainPoint: string
  messages: number
  stage: string
  estimatedCompleteness: number
}

interface WorkshopDeepDiveProps {
  sessionId: string
  companyName: string
  painPoints: PainPoint[]
  currentPainPointIndex: number
  onMilestoneReady: (painPointId: string) => void
  onComplete: () => void
}

type InputMode = 'voice' | 'text'

// =============================================================================
// Component
// =============================================================================

export default function WorkshopDeepDive({
  sessionId,
  companyName,
  painPoints,
  currentPainPointIndex: initialIndex,
  onMilestoneReady,
  // onComplete is available for future use when deep-dive naturally ends
}: WorkshopDeepDiveProps) {
  const [currentIndex] = useState(initialIndex)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMode, setInputMode] = useState<InputMode>('voice')
  const [currentInput, setCurrentInput] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [confidence, setConfidence] = useState<ConfidenceUpdate | null>(null)
  const [estimatedRemaining, setEstimatedRemaining] = useState('')

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const currentPainPoint = painPoints[currentIndex]

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Initialize with greeting for current pain point
  useEffect(() => {
    const greeting: Message = {
      id: `greeting-${currentIndex}`,
      role: 'assistant',
      content: `Great, let's talk about **${currentPainPoint?.label}**.

I want to understand exactly how this affects your day-to-day operations at ${companyName}.

Walk me through how this works today - what's the current process?`,
      timestamp: new Date(),
    }
    setMessages([greeting])
    setConfidence(null)
  }, [currentIndex, currentPainPoint?.label, companyName])

  // Handle voice recording
  const handleVoiceRecording = async (audioBlob: Blob) => {
    setIsProcessing(true)

    try {
      const formData = new FormData()
      formData.append('audio', audioBlob, 'recording.webm')
      formData.append('session_id', sessionId)

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
    }
    setMessages(prev => [...prev, userMessage])
    setIsProcessing(true)

    try {
      const response = await fetch(`${API_BASE_URL}/api/workshop/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: text,
          current_pain_point: currentPainPoint.id,
        }),
      })

      if (!response.ok) throw new Error('Failed to get response')

      const data = await response.json()

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, assistantMessage])

      // Update confidence
      if (data.confidence_update) {
        setConfidence(data.confidence_update)
      }

      // Update remaining time estimate
      if (data.estimated_remaining) {
        setEstimatedRemaining(data.estimated_remaining)
      }

      // Check if we should show milestone
      if (data.should_show_milestone) {
        onMilestoneReady(currentPainPoint.id)
      }

    } catch (err) {
      console.error('Message error:', err)
      const fallback: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: "Thank you for sharing that. Can you tell me more about how this impacts your day-to-day?",
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, fallback])
    } finally {
      setIsProcessing(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleTextSubmit()
    }
  }

  // Get stage label
  const getStageLabel = (stage?: string) => {
    const labels: { [key: string]: string } = {
      current_state: 'Understanding current process',
      failed_attempts: 'What you\'ve tried',
      cost_impact: 'Measuring the impact',
      ideal_state: 'Defining success',
      stakeholders: 'Who\'s involved',
      complete: 'Wrapping up',
    }
    return labels[stage || 'current_state'] || 'Exploring'
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 py-3">
          {/* Pain point progress */}
          <div className="flex items-center gap-2 mb-3">
            {painPoints.map((pp, i) => (
              <div
                key={pp.id}
                className={`h-1.5 flex-1 rounded-full transition-colors ${
                  i < currentIndex
                    ? 'bg-green-500'
                    : i === currentIndex
                    ? 'bg-primary-600'
                    : 'bg-gray-200'
                }`}
              />
            ))}
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-gray-900">
                {currentPainPoint?.label}
              </h2>
              <p className="text-sm text-gray-500">
                {getStageLabel(confidence?.stage)} • {currentIndex + 1} of {painPoints.length}
              </p>
            </div>
            {estimatedRemaining && (
              <span className="text-sm text-gray-400">
                ~{estimatedRemaining} left
              </span>
            )}
          </div>

          {/* Confidence bar */}
          {confidence && (
            <div className="mt-3">
              <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-primary-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${confidence.estimatedCompleteness}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto pb-48">
        <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">
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
                      <span className="text-sm font-medium text-primary-600">Workshop Analyst</span>
                    </div>
                  )}
                  <div
                    className="whitespace-pre-wrap"
                    dangerouslySetInnerHTML={{
                      __html: sanitizeHtml(message.content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>'))
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
        <div className="max-w-3xl mx-auto px-4 py-4">
          {/* Mode toggle */}
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

            {/* Skip button (dev only) */}
            {import.meta.env.DEV && (
              <button
                onClick={() => onMilestoneReady(currentPainPoint.id)}
                className="text-sm text-gray-400 hover:text-gray-600"
              >
                Skip to summary
              </button>
            )}
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
    </div>
  )
}
