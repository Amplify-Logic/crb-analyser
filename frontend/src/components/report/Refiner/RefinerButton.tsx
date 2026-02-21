import { MessageCircle } from 'lucide-react'
import { motion } from 'framer-motion'

interface RefinerButtonProps {
  onClick: () => void
  isOpen: boolean
  hasUnread?: boolean
}

export default function RefinerButton({ onClick, isOpen, hasUnread }: RefinerButtonProps) {
  if (isOpen) return null

  return (
    <motion.button
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
      onClick={onClick}
      className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-full shadow-lg transition-colors print:hidden"
      title="Ask your report"
    >
      <MessageCircle className="w-5 h-5" />
      <span className="text-sm font-medium">Ask your report</span>
      {hasUnread && (
        <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full" />
      )}
    </motion.button>
  )
}
