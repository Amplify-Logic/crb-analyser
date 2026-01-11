import { cn } from '../../lib/utils'

interface BorderBeamProps {
  className?: string
  duration?: number
  colorFrom?: string
  colorTo?: string
}

// Animated gradient glow around the border
export function BorderBeam({
  className,
  duration = 3,
  colorFrom = '#7c3aed',
  colorTo = '#6366f1',
}: BorderBeamProps) {
  return (
    <>
      {/* Animated glow layer */}
      <div
        className={cn(
          'pointer-events-none absolute -inset-0.5 rounded-[inherit] opacity-75 blur-sm',
          className
        )}
        style={{
          background: `linear-gradient(135deg, ${colorFrom}, ${colorTo}, ${colorFrom})`,
          backgroundSize: '400% 400%',
          animation: `gradient-xy ${duration}s ease infinite`,
        }}
      />
      {/* Inner white background to create border effect */}
      <div className="absolute inset-0 rounded-[inherit] bg-white" />
    </>
  )
}

// Pulsing glow border that's more subtle
export function GlowingBorder({
  className,
  color = '#7c3aed',
}: {
  className?: string
  color?: string
}) {
  return (
    <div
      className={cn(
        'pointer-events-none absolute -inset-px rounded-[inherit] animate-glow opacity-60',
        className
      )}
      style={{
        boxShadow: `0 0 25px -5px ${color}, 0 0 40px -10px ${color}`,
      }}
    />
  )
}
