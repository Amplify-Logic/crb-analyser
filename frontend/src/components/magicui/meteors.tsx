import { cn } from '../../lib/utils'
import { useEffect, useState } from 'react'

interface MeteorsProps {
  number?: number
  className?: string
}

export function Meteors({ number = 20, className }: MeteorsProps) {
  const [meteorStyles, setMeteorStyles] = useState<Array<React.CSSProperties>>([])

  useEffect(() => {
    const styles = [...new Array(number)].map(() => ({
      top: -5,
      left: `${Math.random() * 100}%`,
      animationDelay: `${Math.random() * 1}s`,
      animationDuration: `${Math.random() * 8 + 2}s`,
    }))
    setMeteorStyles(styles)
  }, [number])

  return (
    <>
      {meteorStyles.map((style, idx) => (
        <span
          key={idx}
          className={cn(
            'pointer-events-none absolute left-1/2 top-1/2 h-0.5 w-0.5 rotate-[215deg] animate-meteor rounded-[9999px] bg-primary-500 shadow-[0_0_0_1px_#ffffff10]',
            "before:absolute before:top-1/2 before:h-[1px] before:w-[50px] before:-translate-y-1/2 before:transform before:bg-gradient-to-r before:from-primary-400 before:to-transparent before:content-['']",
            className
          )}
          style={style}
        />
      ))}
    </>
  )
}
