import { cn } from '../../lib/utils'
import { ReactNode } from 'react'

interface AnimatedGradientTextProps {
  children: ReactNode
  className?: string
}

export function AnimatedGradientText({
  children,
  className,
}: AnimatedGradientTextProps) {
  return (
    <span
      className={cn(
        'inline-flex animate-gradient bg-gradient-to-r from-primary-600 via-purple-500 to-indigo-600 bg-[length:200%_auto] bg-clip-text text-transparent pb-1',
        className
      )}
    >
      {children}
    </span>
  )
}
