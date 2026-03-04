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
import { logger } from '../../utils/logger'
import { API_BASE } from '../../services/apiClient'

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
  const [suggestions, setSuggestions] = useState<string[]>([])

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const currentPainPoint = painPoints[currentIndex]

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Initialize: restore existing conversation or show greeting
  useEffect(() => {
    const loadExistingConversation = async () => {
      try {
        const res = await fetch(
          `${API_BASE}/api/workshop/deepdive/${sessionId}/${currentIndex}`
        )
        const data = await res.json()

        if (data.exists && data.transcript?.length > 0) {
          // Restore conversation from server
          const restored: Message[] = data.transcript.map((msg: { role: string; content: string }, i: number) => ({
            id: `restored-${i}`,
            role: msg.role as 'assistant' | 'user',
            content: msg.content,
            timestamp: new Date(),
          }))
          setMessages(restored)
          setConfidence(data.confidence ?? null)
          return
        }
      } catch {
        // Fall through to greeting on error
      }

      // Fresh start — no existing conversation
      const greeting: Message = {
        id: `greeting-${currentIndex}`,
        role: 'assistant',
        content: `Great, let's talk about **${currentPainPoint?.label}**.

I want to understand exactly how this affects your day-to-day operations at ${companyName}.

Walk me through how this works today — what's the current process?`,
        timestamp: new Date(),
      }
      setMessages([greeting])
      setConfidence(null)
      // Show initial suggestions matching the opening question
      setSuggestions([
        "It's mostly manual — someone handles it each time",
        "We have a tool but still do a lot by hand",
        "Multiple people are involved and it's messy",
      ])
    }

    loadExistingConversation()
  }, [currentIndex, currentPainPoint?.label, companyName, sessionId])

  // Handle voice recording
  const handleVoiceRecording = async (audioBlob: Blob) => {
    setIsProcessing(true)

    try {
      const formData = new FormData()
      formData.append('audio', audioBlob, 'recording.webm')
      formData.append('session_id', sessionId)

      const transcribeResponse = await fetch(`${API_BASE}/api/interview/transcribe`, {
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
      logger.error('Voice processing error:', err)
      setIsProcessing(false)
    }
  }

  // Handle text submit
  const handleTextSubmit = async () => {
    const text = currentInput.trim()
    if (!text || isProcessing) return
    setCurrentInput('')
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = '44px'
    }
    await processUserMessage(text)
  }

  // Process user message
  // Non-streaming fallback
  const processUserMessageFallback = async (text: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/workshop/respond`, {
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

      if (data.confidence_update) setConfidence(data.confidence_update)
      if (data.estimated_remaining) setEstimatedRemaining(data.estimated_remaining)
      setSuggestions(data.suggestions || [])
      if (data.should_show_milestone) onMilestoneReady(currentPainPoint.id)
    } catch (err) {
      logger.error('Fallback message error:', err)
      setMessages(prev => [...prev, {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: "Thank you for sharing that. Can you tell me more about how this impacts your day-to-day?",
        timestamp: new Date(),
      }])
    }
  }

  const processUserMessage = async (text: string) => {
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMessage])
    setIsProcessing(true)
    setSuggestions([])

    // Create placeholder assistant message for streaming
    const assistantId = `assistant-${Date.now()}`

    try {
      const res = await fetch(`${API_BASE}/api/workshop/respond/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: text,
          current_pain_point: currentPainPoint.id,
        }),
      })

      if (!res.ok || !res.body) {
        // Fallback to non-streaming
        await processUserMessageFallback(text)
        return
      }

      // Add empty assistant message to stream into
      setMessages(prev => [...prev, { id: assistantId, role: 'assistant', content: '', timestamp: new Date() }])

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let accumulated = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const data = JSON.parse(line.slice(6))

            if (data.type === 'token') {
              accumulated += data.content
              setMessages(prev => prev.map(m =>
                m.id === assistantId ? { ...m, content: accumulated } : m
              ))
            } else if (data.type === 'complete') {
              setSuggestions(data.suggestions || [])
              if (data.confidence_update) setConfidence(data.confidence_update)
              if (data.estimated_remaining) setEstimatedRemaining(data.estimated_remaining)
              if (data.should_show_milestone) onMilestoneReady(currentPainPoint.id)
            }
          } catch {
            // Skip malformed SSE lines
          }
        }
      }
    } catch (err) {
      logger.error('Streaming error, falling back:', err)
      // Remove the empty placeholder if it exists
      setMessages(prev => prev.filter(m => m.id !== assistantId || m.content !== ''))
      await processUserMessageFallback(text)
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
      <div className="bg-white/95 backdrop-blur-sm border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 py-3">
          {/* Pain point progress */}
          <div className="flex items-center gap-1.5 mb-3">
            {painPoints.map((pp, i) => (
              <div
                key={pp.id}
                className={`h-1 flex-1 rounded-full transition-all duration-300 ${
                  i < currentIndex
                    ? 'bg-primary-600'
                    : i === currentIndex
                    ? 'bg-primary-500'
                    : 'bg-gray-200'
                }`}
              />
            ))}
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-gray-900 text-base">
                {currentPainPoint?.label}
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">
                {getStageLabel(confidence?.stage)} &middot; {currentIndex + 1} of {painPoints.length}
              </p>
            </div>
            {estimatedRemaining && (
              <span className="text-xs text-gray-400 bg-gray-50 px-2.5 py-1 rounded-full">
                ~{estimatedRemaining} left
              </span>
            )}
          </div>

          {/* Confidence bar */}
          {confidence && (
            <div className="mt-2.5">
              <div className="h-0.5 bg-gray-100 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-primary-400 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${confidence.estimatedCompleteness}%` }}
                  transition={{ duration: 0.5, ease: 'easeOut' }}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto pb-36">
        <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">
          <AnimatePresence>
            {messages.map((message, idx) => {
              // Only show analyst badge on first assistant message
              const isFirstAssistant = message.role === 'assistant' &&
                messages.findIndex(m => m.role === 'assistant') === idx
              // Check if previous message was from the same role (for tighter grouping)
              const prevMsg = idx > 0 ? messages[idx - 1] : null
              const isSameRole = prevMsg?.role === message.role

              return (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2 }}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} ${
                    isSameRole ? '-mt-1' : ''
                  }`}
                >
                  <div
                    className={`max-w-[80%] px-4 py-3 ${
                      message.role === 'user'
                        ? 'bg-primary-600 text-white rounded-2xl rounded-br-md'
                        : 'bg-white border border-gray-100 text-gray-800 rounded-2xl rounded-bl-md'
                    }`}
                  >
                    {isFirstAssistant && (
                      <div className="flex items-center gap-1.5 mb-2">
                        <div className="w-4 h-4 bg-primary-50 rounded-full flex items-center justify-center">
                          <svg className="w-2.5 h-2.5 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                          </svg>
                        </div>
                        <span className="text-xs font-medium text-primary-400">Workshop Analyst</span>
                      </div>
                    )}
                    <div
                      className={`whitespace-pre-wrap leading-relaxed text-[15px] ${
                        message.role === 'user' ? '' : 'text-gray-700'
                      }`}
                      dangerouslySetInnerHTML={{
                        __html: sanitizeHtml(message.content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>'))
                      }}
                    />
                  </div>
                </motion.div>
              )
            })}
          </AnimatePresence>

          {isProcessing && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-start"
            >
              <div className="bg-white border border-gray-100 rounded-2xl rounded-bl-md px-4 py-3">
                <div className="flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-1.5 h-1.5 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-1.5 h-1.5 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input area */}
      <div className="fixed bottom-0 left-0 right-0 bg-white/95 backdrop-blur-sm border-t border-gray-100">
        <div className="max-w-3xl mx-auto px-4">
          {/* Suggestion chips — horizontal scroll, single line */}
          <AnimatePresence>
            {suggestions.length > 0 && !isProcessing && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="flex gap-2 overflow-x-auto pt-3 pb-2 scrollbar-hide">
                  {suggestions.map((suggestion, i) => (
                    <motion.button
                      key={i}
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                      onClick={() => {
                        setSuggestions([])
                        setCurrentInput('')
                        processUserMessage(suggestion)
                      }}
                      className="px-3 py-1.5 text-sm bg-gray-50 border border-gray-200 rounded-full
                                 hover:border-primary-400 hover:bg-primary-50 transition-all
                                 text-gray-600 hover:text-primary-700 active:scale-95
                                 whitespace-nowrap flex-shrink-0"
                    >
                      {suggestion}
                    </motion.button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Input row */}
          <div className="flex items-end gap-2 py-3">
            {/* Mic / keyboard toggle button */}
            <button
              onClick={() => setInputMode(inputMode === 'voice' ? 'text' : 'voice')}
              className="p-2.5 rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-all flex-shrink-0"
              title={inputMode === 'voice' ? 'Switch to typing' : 'Switch to voice'}
            >
              {inputMode === 'voice' ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              )}
            </button>

            {inputMode === 'voice' ? (
              <div className="flex-1 flex items-center justify-center">
                <VoiceRecorder
                  onRecordingComplete={handleVoiceRecording}
                  size="small"
                  disabled={isProcessing}
                />
              </div>
            ) : (
              <>
                <textarea
                  ref={textareaRef}
                  value={currentInput}
                  onChange={(e) => {
                    setCurrentInput(e.target.value)
                    const el = e.target
                    el.style.height = 'auto'
                    el.style.height = Math.min(el.scrollHeight, 120) + 'px'
                  }}
                  onKeyDown={handleKeyDown}
                  placeholder="Type your response..."
                  className="flex-1 px-4 py-2.5 border border-gray-200 rounded-2xl resize-none
                             focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors
                             text-[15px] placeholder:text-gray-400"
                  rows={1}
                  style={{ minHeight: '42px', maxHeight: '120px' }}
                  disabled={isProcessing}
                />
                <button
                  onClick={handleTextSubmit}
                  disabled={!currentInput.trim() || isProcessing}
                  className={`p-2.5 rounded-full font-medium transition-all flex-shrink-0 ${
                    currentInput.trim() && !isProcessing
                      ? 'bg-primary-600 text-white hover:bg-primary-700 active:scale-95'
                      : 'bg-gray-100 text-gray-300 cursor-not-allowed'
                  }`}
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.5 10.5L12 3m0 0l7.5 7.5M12 3v18" />
                  </svg>
                </button>
              </>
            )}

            {/* Dev skip button */}
            {import.meta.env.DEV && (
              <button
                onClick={() => onMilestoneReady(currentPainPoint.id)}
                className="text-xs text-gray-300 hover:text-gray-500 flex-shrink-0 px-1"
                title="Skip to summary"
              >
                skip
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
