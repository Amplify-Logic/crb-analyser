import { useState, useRef, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface AutomationOpportunity {
  finding_id: string
  title: string
  impact_monthly: number
  diy_effort_hours: number
  approach: 'Connect' | 'Replace' | 'Either'
  tools_involved: string[]
  category: string
}

interface AutomationMatrixProps {
  opportunities: AutomationOpportunity[]
  companyName?: string
}

interface PositionedCard {
  opp: AutomationOpportunity
  x: number // percentage 0-100
  y: number // percentage 0-100
  color: 'green' | 'amber' | 'red'
}

const CARD_W = 140
const CARD_H = 56

function getCardColor(normalizedValue: number, normalizedEffort: number): 'green' | 'amber' | 'red' {
  const score = normalizedValue - normalizedEffort
  if (score > 0.25) return 'green'
  if (score > -0.25) return 'amber'
  return 'red'
}

const cardStyles = {
  green: {
    bg: 'bg-green-100 dark:bg-green-900/40',
    border: 'border-green-300 dark:border-green-700',
    text: 'text-green-800 dark:text-green-200',
    badge: 'bg-green-200 dark:bg-green-800/60 text-green-700 dark:text-green-300',
  },
  amber: {
    bg: 'bg-amber-100 dark:bg-amber-900/40',
    border: 'border-amber-300 dark:border-amber-700',
    text: 'text-amber-800 dark:text-amber-200',
    badge: 'bg-amber-200 dark:bg-amber-800/60 text-amber-700 dark:text-amber-300',
  },
  red: {
    bg: 'bg-red-100 dark:bg-red-900/40',
    border: 'border-red-300 dark:border-red-700',
    text: 'text-red-800 dark:text-red-200',
    badge: 'bg-red-200 dark:bg-red-800/60 text-red-700 dark:text-red-300',
  },
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(value)
}

function formatHours(hours: number) {
  if (hours === 0) return '-'
  if (hours < 1) return '<1h'
  return `${Math.round(hours)}h`
}

function resolveOverlaps(
  positions: { x: number; y: number }[],
  cardW: number,
  cardH: number,
  containerW: number,
  containerH: number,
  iterations = 8
) {
  const pxPositions = positions.map((p) => ({
    x: (p.x / 100) * containerW,
    y: (p.y / 100) * containerH,
  }))

  for (let iter = 0; iter < iterations; iter++) {
    for (let i = 0; i < pxPositions.length; i++) {
      for (let j = i + 1; j < pxPositions.length; j++) {
        const dx = pxPositions[j].x - pxPositions[i].x
        const dy = pxPositions[j].y - pxPositions[i].y
        const overlapX = cardW + 8 - Math.abs(dx)
        const overlapY = cardH + 8 - Math.abs(dy)

        if (overlapX > 0 && overlapY > 0) {
          if (overlapX < overlapY) {
            const push = overlapX / 2 + 2
            pxPositions[i].x -= Math.sign(dx || 1) * push
            pxPositions[j].x += Math.sign(dx || 1) * push
          } else {
            const push = overlapY / 2 + 2
            pxPositions[i].y -= Math.sign(dy || 1) * push
            pxPositions[j].y += Math.sign(dy || 1) * push
          }
        }
      }
    }
  }

  // Clamp to container bounds
  return pxPositions.map((p) => ({
    x: Math.max(0, Math.min(containerW - cardW, p.x)) / containerW * 100,
    y: Math.max(0, Math.min(containerH - cardH, p.y)) / containerH * 100,
  }))
}

function ApproachTag({ approach }: { approach: 'Connect' | 'Replace' | 'Either' }) {
  return (
    <span className="text-[10px] font-medium opacity-70">
      {approach === 'Connect' ? '🔗' : approach === 'Replace' ? '🔄' : '↔️'} {approach}
    </span>
  )
}

// Desktop: Positioned cards on a 2D grid
function MatrixChart({ cards }: { cards: PositionedCard[] }) {
  const [hoveredId, setHoveredId] = useState<string | null>(null)
  const [isVisible, setIsVisible] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const [containerSize, setContainerSize] = useState({ w: 700, h: 420 })

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setIsVisible(true)
      },
      { threshold: 0.2 }
    )
    if (containerRef.current) observer.observe(containerRef.current)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    if (!containerRef.current) return
    const measure = () => {
      if (!containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      setContainerSize({ w: rect.width, h: rect.height })
    }
    measure()
    window.addEventListener('resize', measure)
    return () => window.removeEventListener('resize', measure)
  }, [])

  const resolvedCards = useMemo(() => {
    if (cards.length <= 1) return cards
    const rawPositions = cards.map((c) => ({ x: c.x, y: c.y }))
    const resolved = resolveOverlaps(rawPositions, CARD_W, CARD_H, containerSize.w, containerSize.h)
    return cards.map((c, i) => ({ ...c, x: resolved[i].x, y: resolved[i].y }))
  }, [cards, containerSize])

  return (
    <div ref={containerRef} className="relative w-full" style={{ height: 420 }}>
      {/* Quadrant background zones */}
      <div className="absolute inset-0 grid grid-cols-2 grid-rows-2 pointer-events-none">
        <div className="bg-green-50/50 dark:bg-green-900/10 rounded-tl-lg" />
        <div className="bg-amber-50/50 dark:bg-amber-900/10 rounded-tr-lg" />
        <div className="bg-amber-50/30 dark:bg-amber-800/5 rounded-bl-lg" />
        <div className="bg-red-50/50 dark:bg-red-900/10 rounded-br-lg" />
      </div>

      {/* Grid lines */}
      <div className="absolute inset-0 pointer-events-none">
        {/* Vertical center */}
        <div className="absolute left-1/2 top-0 bottom-0 border-l border-dashed border-gray-300 dark:border-gray-600" />
        {/* Horizontal center */}
        <div className="absolute top-1/2 left-0 right-0 border-t border-dashed border-gray-300 dark:border-gray-600" />
        {/* Quartile lines */}
        <div className="absolute left-1/4 top-0 bottom-0 border-l border-dashed border-gray-200 dark:border-gray-700/50" />
        <div className="absolute left-3/4 top-0 bottom-0 border-l border-dashed border-gray-200 dark:border-gray-700/50" />
        <div className="absolute top-1/4 left-0 right-0 border-t border-dashed border-gray-200 dark:border-gray-700/50" />
        <div className="absolute top-3/4 left-0 right-0 border-t border-dashed border-gray-200 dark:border-gray-700/50" />
      </div>

      {/* Quadrant labels */}
      <div className="absolute top-3 left-3 text-xs font-medium text-green-600 dark:text-green-400 opacity-60">
        Quick Wins
      </div>
      <div className="absolute top-3 right-3 text-xs font-medium text-amber-600 dark:text-amber-400 opacity-60">
        Strategic Bets
      </div>
      <div className="absolute bottom-3 left-3 text-xs font-medium text-gray-500 dark:text-gray-500 opacity-60">
        Low Priority
      </div>
      <div className="absolute bottom-3 right-3 text-xs font-medium text-red-500 dark:text-red-400 opacity-60">
        Reconsider
      </div>

      {/* Cards */}
      <AnimatePresence>
        {isVisible &&
          resolvedCards.map((card, index) => {
            const style = cardStyles[card.color]
            const isHovered = hoveredId === card.opp.finding_id

            return (
              <motion.div
                key={card.opp.finding_id}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.08, type: 'spring', stiffness: 300, damping: 25 }}
                className="absolute z-10"
                style={{
                  left: `${card.x}%`,
                  top: `${card.y}%`,
                  width: CARD_W,
                  height: CARD_H,
                }}
                onMouseEnter={() => setHoveredId(card.opp.finding_id)}
                onMouseLeave={() => setHoveredId(null)}
              >
                <div
                  className={`
                    w-full h-full rounded-lg border-2 px-3 py-2 cursor-default
                    transition-shadow duration-200
                    ${style.bg} ${style.border} ${style.text}
                    ${isHovered ? 'shadow-lg ring-2 ring-offset-1 ring-gray-400/30 dark:ring-gray-500/30 z-20' : 'shadow-sm'}
                  `}
                >
                  <p className="text-xs font-semibold leading-tight line-clamp-2">
                    {card.opp.title}
                  </p>
                  <div className="mt-0.5">
                    <ApproachTag approach={card.opp.approach} />
                  </div>
                </div>

                {/* Hover tooltip */}
                <AnimatePresence>
                  {isHovered && (
                    <motion.div
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 4 }}
                      className="absolute z-50 left-1/2 -translate-x-1/2 mt-1 w-52 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 p-3"
                      style={{ top: CARD_H + 4 }}
                    >
                      <p className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                        {card.opp.title}
                      </p>
                      <div className="space-y-1.5 text-xs">
                        <div className="flex justify-between">
                          <span className="text-gray-500 dark:text-gray-400">Value/mo</span>
                          <span className="font-semibold text-green-600 dark:text-green-400">
                            {formatCurrency(card.opp.impact_monthly)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500 dark:text-gray-400">Setup effort</span>
                          <span className="font-medium text-gray-700 dark:text-gray-300">
                            {formatHours(card.opp.diy_effort_hours)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500 dark:text-gray-400">Approach</span>
                          <span className="font-medium text-gray-700 dark:text-gray-300">
                            {card.opp.approach}
                          </span>
                        </div>
                        {card.opp.tools_involved.length > 0 && (
                          <div className="pt-1.5 border-t border-gray-100 dark:border-gray-700">
                            <span className="text-gray-500 dark:text-gray-400">Tools: </span>
                            <span className="text-gray-700 dark:text-gray-300">
                              {card.opp.tools_involved.slice(0, 3).join(', ')}
                              {card.opp.tools_involved.length > 3 && ` +${card.opp.tools_involved.length - 3}`}
                            </span>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            )
          })}
      </AnimatePresence>
    </div>
  )
}

// Mobile: Sorted list of opportunity cards
function MobileList({ cards }: { cards: PositionedCard[] }) {
  const sorted = useMemo(
    () => [...cards].sort((a, b) => {
      const scoreA = a.opp.impact_monthly / Math.max(a.opp.diy_effort_hours, 1)
      const scoreB = b.opp.impact_monthly / Math.max(b.opp.diy_effort_hours, 1)
      return scoreB - scoreA
    }),
    [cards]
  )

  return (
    <div className="space-y-3">
      {sorted.map((card, index) => {
        const style = cardStyles[card.color]
        return (
          <motion.div
            key={card.opp.finding_id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className={`rounded-lg border-2 p-3 ${style.bg} ${style.border}`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-semibold ${style.text}`}>
                  {card.opp.title}
                </p>
                <div className="mt-1">
                  <ApproachTag approach={card.opp.approach} />
                </div>
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-sm font-bold text-green-600 dark:text-green-400">
                  {formatCurrency(card.opp.impact_monthly)}/mo
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {formatHours(card.opp.diy_effort_hours)} setup
                </p>
              </div>
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}

export default function AutomationMatrix({ opportunities, companyName }: AutomationMatrixProps) {
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 640)
    check()
    window.addEventListener('resize', check)
    return () => window.removeEventListener('resize', check)
  }, [])

  const cards = useMemo<PositionedCard[]>(() => {
    if (opportunities.length === 0) return []

    const maxImpact = Math.max(...opportunities.map((o) => o.impact_monthly))
    const minImpact = Math.min(...opportunities.map((o) => o.impact_monthly))
    const maxEffort = Math.max(...opportunities.map((o) => o.diy_effort_hours))
    const minEffort = Math.min(...opportunities.map((o) => o.diy_effort_hours))

    const impactRange = maxImpact - minImpact || 1
    const effortRange = maxEffort - minEffort || 1

    return opportunities.map((opp) => {
      // Normalize to 0-1, with padding so cards aren't at the very edge
      const normValue = (opp.impact_monthly - minImpact) / impactRange
      const normEffort = (opp.diy_effort_hours - minEffort) / effortRange

      // Map to chart position (percentage)
      // X: effort goes left (low=5%) to right (high=85%)
      // Y: value goes bottom (low=85%) to top (high=5%)
      const x = 5 + normEffort * 80
      const y = 85 - normValue * 80

      const color = getCardColor(normValue, normEffort)

      return { opp, x, y, color }
    })
  }, [opportunities])

  if (opportunities.length === 0) return null

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <svg className="w-5 h-5 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Automation Opportunities{companyName ? ` for ${companyName}` : ''}
          </h3>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Each card is an automation opportunity, positioned by its potential value and implementation effort.
          <span className="hidden sm:inline"> Hover for details.</span>
        </p>
      </div>

      {/* Axis labels (desktop only) */}
      {!isMobile && (
        <div className="relative">
          {/* Y-axis label */}
          <div className="absolute -left-1 top-1/2 -translate-y-1/2 -rotate-90 origin-center">
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
              Value (€/mo)
            </span>
          </div>

          {/* Chart area with left padding for Y label */}
          <div className="ml-6">
            <MatrixChart cards={cards} />

            {/* X-axis label */}
            <div className="text-center mt-2">
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Effort / Cost / Time
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Mobile list */}
      {isMobile && <MobileList cards={cards} />}

      {/* Legend */}
      <div className="flex flex-wrap justify-center gap-4 mt-5 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-sm bg-green-300 dark:bg-green-600 border border-green-400 dark:border-green-500" />
          <span className="text-xs text-gray-600 dark:text-gray-400">Quick Win</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-sm bg-amber-300 dark:bg-amber-600 border border-amber-400 dark:border-amber-500" />
          <span className="text-xs text-gray-600 dark:text-gray-400">Worth Considering</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-sm bg-red-300 dark:bg-red-600 border border-red-400 dark:border-red-500" />
          <span className="text-xs text-gray-600 dark:text-gray-400">Complex / Expensive</span>
        </div>
      </div>
    </div>
  )
}
