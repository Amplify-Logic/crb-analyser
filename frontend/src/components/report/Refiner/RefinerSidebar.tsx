import { useState, useEffect, useCallback } from 'react'
import { X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import MessageList from './MessageList'
import MessageInput from './MessageInput'
import { refinerApi } from '../../../services/refinerApi'
import type { Message } from '../../../services/refinerApi'

interface RefinerSidebarProps {
  reportId: string
  isOpen: boolean
  onClose: () => void
}

export default function RefinerSidebar({ reportId, isOpen, onClose }: RefinerSidebarProps) {
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [starterPrompts, setStarterPrompts] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Initialize: create or load conversation
  useEffect(() => {
    if (!isOpen || conversationId) return

    const init = async () => {
      try {
        // Check for existing conversations
        const existing = await refinerApi.listConversations(reportId)
        if (existing.length > 0) {
          const conv = existing[0]
          setConversationId(conv.id)
          const msgs = await refinerApi.getMessages(reportId, conv.id)
          setMessages(msgs)
          if (conv.starter_prompts) {
            setStarterPrompts(conv.starter_prompts)
          }
        } else {
          // Create new conversation
          const conv = await refinerApi.createConversation(reportId)
          setConversationId(conv.id)
          setStarterPrompts(conv.starter_prompts || [])
        }
      } catch (err: any) {
        setError(err.message || 'Failed to start conversation')
      }
    }

    init()
  }, [isOpen, reportId, conversationId])

  const sendMessage = useCallback(async (content: string) => {
    if (!conversationId || isLoading) return

    // Optimistic: add user message
    const userMsg: Message = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])
    setIsLoading(true)
    setError(null)

    try {
      const response = await refinerApi.sendMessage(reportId, conversationId, content)
      // Replace temp + add assistant response
      setMessages(prev => [
        ...prev.filter(m => m.id !== userMsg.id),
        { ...userMsg, id: `user-${Date.now()}` },
        {
          id: response.id,
          role: 'assistant',
          content: response.content,
          model_used: response.model_used,
          tokens_used: response.tokens_used,
          created_at: new Date().toISOString(),
        },
      ])
    } catch (err: any) {
      setError(err.message || 'Failed to send message')
      // Remove optimistic user message on error
      setMessages(prev => prev.filter(m => m.id !== userMsg.id))
    } finally {
      setIsLoading(false)
    }
  }, [conversationId, reportId, isLoading])

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.aside
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="fixed right-0 top-0 h-full w-[400px] max-w-full z-40 bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-700 shadow-xl flex flex-col print:hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-sm font-semibold text-gray-900 dark:text-white">
              Report Refiner
            </h2>
            <button
              onClick={onClose}
              className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Error banner */}
          {error && (
            <div className="px-4 py-2 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-xs">
              {error}
            </div>
          )}

          {/* Messages */}
          <MessageList
            messages={messages}
            starterPrompts={starterPrompts}
            onStarterSelect={sendMessage}
            isLoading={isLoading}
          />

          {/* Input */}
          <MessageInput
            onSend={sendMessage}
            disabled={isLoading || !conversationId}
          />
        </motion.aside>
      )}
    </AnimatePresence>
  )
}
