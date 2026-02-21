import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import type { Message } from '../../../services/refinerApi'

interface StarterPromptsProps {
  prompts: string[]
  onSelect: (prompt: string) => void
}

function StarterPrompts({ prompts, onSelect }: StarterPromptsProps) {
  return (
    <div className="space-y-2 px-4 py-3">
      {prompts.map((prompt, i) => (
        <button
          key={i}
          onClick={() => onSelect(prompt)}
          className="w-full text-left px-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 transition-colors"
        >
          {prompt}
        </button>
      ))}
    </div>
  )
}

interface MessageBubbleProps {
  message: Message
}

function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
          isUser
            ? 'bg-primary-600 text-white'
            : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white'
        }`}
      >
        <div className="whitespace-pre-wrap">{message.content}</div>
      </div>
    </motion.div>
  )
}

interface MessageListProps {
  messages: Message[]
  starterPrompts: string[]
  onStarterSelect: (prompt: string) => void
  isLoading?: boolean
}

export default function MessageList({
  messages,
  starterPrompts,
  onStarterSelect,
  isLoading,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, isLoading])

  const showStarters = messages.length === 0 && starterPrompts.length > 0

  return (
    <div className="flex-1 overflow-y-auto">
      {/* Greeting */}
      <div className="px-4 py-4">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          I have full context on your analysis. Ask me anything.
        </p>
      </div>

      {/* Starter prompts or messages */}
      {showStarters ? (
        <StarterPrompts prompts={starterPrompts} onSelect={onStarterSelect} />
      ) : (
        <div className="space-y-3 px-4 pb-4">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-start"
            >
              <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-3 py-2 text-sm text-gray-500">
                <span className="inline-flex gap-1">
                  <span className="animate-bounce" style={{ animationDelay: '0ms' }}>.</span>
                  <span className="animate-bounce" style={{ animationDelay: '150ms' }}>.</span>
                  <span className="animate-bounce" style={{ animationDelay: '300ms' }}>.</span>
                </span>
              </div>
            </motion.div>
          )}
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  )
}
