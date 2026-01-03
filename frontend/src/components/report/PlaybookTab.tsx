/**
 * PlaybookTab Component
 *
 * Interactive implementation playbook with:
 * - Visual timeline roadmap with phases/milestones
 * - Progress tracking with backend persistence
 * - Task details with CRB breakdown, resources, success criteria
 * - Implementation guidance with steps and pitfalls
 * - Print/export functionality
 */

import { useState, useMemo, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

// ============================================================================
// Helpers
// ============================================================================

/** Format option_type to proper display name */
function formatOptionType(optionType: string): string {
  const displayNames: Record<string, string> = {
    'off_the_shelf': 'Off-the-Shelf',
    'best_in_class': 'Best-in-Class',
    'custom_solution': 'Custom Solution',
  }
  return displayNames[optionType] || optionType.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

// ============================================================================
// Types
// ============================================================================

interface TaskCRB {
  cost: string
  risk: 'low' | 'medium' | 'high'
  benefit: string
}

interface PlaybookTask {
  id: string
  title: string
  description?: string
  time_estimate_minutes?: number
  hours?: number  // Alternative time field
  difficulty?: 'easy' | 'medium' | 'hard'
  executor?: 'owner' | 'team' | 'hire_out'
  owner?: string  // Alternative executor field
  tools?: string[]
  tutorial_hint?: string
  crb?: TaskCRB
  completed?: boolean
  // Enhanced fields
  success_criteria?: string[]
  common_pitfalls?: string[]
  resources?: { title: string; url?: string; type: 'doc' | 'video' | 'tool' }[]
  steps?: string[]
  dependencies?: string[] // Task IDs this depends on
}

interface Week {
  week_number: number
  theme: string
  tasks: PlaybookTask[]
  checkpoint: string
}

interface PhaseCRBSummary {
  total_cost: string
  monthly_cost: string
  setup_hours: number
  risks: string[]
  benefits: string[]
  crb_score: number
}

interface Phase {
  phase_number?: number
  title?: string
  name?: string  // Alternative to title in simpler format
  duration_weeks?: number
  outcome?: string
  crb_summary?: PhaseCRBSummary
  weeks?: Week[]  // Complex format with weeks
  tasks?: PlaybookTask[]  // Simple format with tasks directly on phase
  week?: number  // Simple format: which week this phase is
}

interface Playbook {
  id: string
  recommendation_id: string
  option_type: string
  total_weeks: number
  phases: Phase[]
  personalization_context: {
    team_size: string
    technical_level: number
    budget_monthly: number
  }
}

interface PlaybookTabProps {
  playbooks: Playbook[]
  reportId?: string
  onTaskComplete?: (playbookId: string, taskId: string, completed: boolean) => void
  /** Controlled mode: pass completed tasks from parent (usePlaybookProgress hook) */
  completedTasks?: Record<string, string[]> // playbookId -> taskIds
  /** @deprecated Use completedTasks for controlled mode. Only used as fallback for initial state. */
  initialCompletedTasks?: Record<string, string[]> // playbookId -> taskIds
}

// ============================================================================
// Sub-components
// ============================================================================

function TimelineRoadmap({
  phases,
  completedTasks,
  onPhaseClick,
  activePhase
}: {
  phases: Phase[]
  completedTasks: Set<string>
  onPhaseClick: (phaseNumber: number) => void
  activePhase: number | null
}) {
  // Helper to get tasks from phase (handles both data structures)
  const getTasksFromPhase = (phase: Phase) => {
    if (phase.weeks && Array.isArray(phase.weeks)) {
      return phase.weeks.flatMap(w => w.tasks || [])
    }
    return phase.tasks || []
  }

  // Calculate phase progress
  const phaseProgress = phases.map(phase => {
    const allTasks = getTasksFromPhase(phase)
    const completed = allTasks.filter(t => completedTasks.has(t.id)).length
    return { total: allTasks.length, completed, percent: allTasks.length ? Math.round((completed / allTasks.length) * 100) : 0 }
  })

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-md rounded-3xl p-6 shadow-card-premium mb-6 print:shadow-none print:border border border-gray-200/50 dark:border-gray-700/50"
    >
      <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-5 tracking-tight flex items-center gap-2">
        <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center text-white text-sm shadow-lg shadow-primary-500/20">🗺️</span>
        Implementation Timeline
      </h3>

      {/* Desktop timeline */}
      <div className="hidden md:block">
        <div className="relative">
          {/* Connector line */}
          <div className="absolute top-6 left-0 right-0 h-1 bg-gray-200 rounded" />
          <div
            className="absolute top-6 left-0 h-1 bg-primary-500 rounded transition-all duration-500"
            style={{
              width: `${(phaseProgress.reduce((sum, p) => sum + p.percent, 0) / phases.length)}%`
            }}
          />

          {/* Phase nodes */}
          <div className="relative flex justify-between">
            {phases.map((phase, i) => {
              const phaseNum = phase.phase_number ?? i + 1
              const progress = phaseProgress[i]
              const isComplete = progress.percent === 100
              const isActive = activePhase === phaseNum

              return (
                <button
                  key={phaseNum}
                  onClick={() => onPhaseClick(phaseNum)}
                  className="flex flex-col items-center group"
                >
                  <div
                    className={`w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold transition-all ${
                      isComplete
                        ? 'bg-green-500 text-white'
                        : isActive
                        ? 'bg-primary-600 text-white ring-4 ring-primary-200'
                        : progress.completed > 0
                        ? 'bg-primary-100 text-primary-600'
                        : 'bg-gray-100 text-gray-400'
                    }`}
                  >
                    {isComplete ? (
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      phaseNum
                    )}
                  </div>

                  <div className="mt-3 text-center">
                    <p className={`font-semibold text-sm ${isActive ? 'text-primary-600 dark:text-primary-400' : 'text-gray-900 dark:text-white'}`}>
                      {phase.title}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{phase.duration_weeks} weeks</p>
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                      {progress.completed}/{progress.total} tasks
                    </p>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* Mobile timeline */}
      <div className="md:hidden space-y-3">
        {phases.map((phase, i) => {
          const phaseNum = phase.phase_number ?? i + 1
          const progress = phaseProgress[i]
          const isComplete = progress.percent === 100

          return (
            <motion.button
              key={phaseNum}
              onClick={() => onPhaseClick(phaseNum)}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              className={`w-full flex items-center gap-4 p-4 rounded-2xl transition-all ${
                activePhase === phaseNum
                  ? 'bg-primary-50 dark:bg-primary-900/20 border-2 border-primary-300 dark:border-primary-600 shadow-sm'
                  : 'bg-gray-50 dark:bg-gray-800/50 border-2 border-transparent hover:border-gray-200 dark:hover:border-gray-700'
              }`}
            >
              <div
                className={`w-11 h-11 rounded-xl flex items-center justify-center font-bold flex-shrink-0 shadow-sm ${
                  isComplete
                    ? 'bg-gradient-to-br from-green-400 to-green-500 text-white'
                    : progress.completed > 0
                    ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                }`}
              >
                {isComplete ? '✓' : phaseNum}
              </div>

              <div className="flex-1 text-left">
                <p className="font-semibold text-gray-900 dark:text-white">{phase.title}</p>
                <div className="flex items-center gap-2 mt-1.5">
                  <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                    <motion.div
                      className="bg-gradient-to-r from-primary-500 to-primary-400 rounded-full h-2"
                      initial={{ width: 0 }}
                      animate={{ width: `${progress.percent}%` }}
                      transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
                    />
                  </div>
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400">{progress.percent}%</span>
                </div>
              </div>
            </motion.button>
          )
        })}
      </div>
    </motion.div>
  )
}

function TaskCard({
  task,
  isCompleted,
  onToggle,
  isBlocked,
  blockedBy,
  isCriticalPath = false
}: {
  task: PlaybookTask
  isCompleted: boolean
  onToggle: () => void
  isBlocked: boolean
  blockedBy?: string[]
  isCriticalPath?: boolean
}) {
  const [expanded, setExpanded] = useState(false)

  const difficultyConfig = {
    easy: { bg: 'bg-green-100', text: 'text-green-700', label: 'Easy' },
    medium: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'Medium' },
    hard: { bg: 'bg-red-100', text: 'text-red-700', label: 'Hard' }
  }

  const executorConfig = {
    owner: { label: 'You', icon: '👤' },
    team: { label: 'Team', icon: '👥' },
    hire_out: { label: 'Outsource', icon: '🔧' }
  }

  const riskConfig = {
    low: { bg: 'bg-green-100', text: 'text-green-700' },
    medium: { bg: 'bg-yellow-100', text: 'text-yellow-700' },
    high: { bg: 'bg-red-100', text: 'text-red-700' }
  }

  const formatTime = (minutes: number) => {
    if (minutes < 60) return `${minutes}min`
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return mins ? `${hours}h ${mins}m` : `${hours}h`
  }

  return (
    <motion.div
      layout
      whileHover={{ y: isBlocked ? 0 : -2 }}
      transition={{ duration: 0.2 }}
      className={`rounded-2xl border-2 transition-all relative ${
        isCompleted
          ? 'bg-green-50/80 dark:bg-green-900/20 border-green-200 dark:border-green-700/50'
          : isBlocked
          ? 'bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700 opacity-60'
          : isCriticalPath
          ? 'bg-white dark:bg-gray-800/80 border-purple-300 dark:border-purple-600/50 shadow-md shadow-purple-100/50 dark:shadow-purple-900/20 hover:border-purple-400 dark:hover:border-purple-500 hover:shadow-lg'
          : 'bg-white dark:bg-gray-800/80 border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-600 hover:shadow-md'
      }`}
    >
      {/* Critical path badge */}
      {isCriticalPath && !isCompleted && (
        <motion.div
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="absolute -top-2.5 -right-2.5 bg-gradient-to-r from-purple-500 to-purple-600 text-white text-xs px-3 py-1 rounded-full font-bold shadow-lg shadow-purple-500/30 print:hidden flex items-center gap-1"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
          Critical
        </motion.div>
      )}
      {/* Main row */}
      <div className="p-5">
        <div className="flex items-start gap-4">
          {/* Checkbox */}
          <motion.button
            onClick={onToggle}
            disabled={isBlocked}
            whileHover={!isBlocked ? { scale: 1.1 } : undefined}
            whileTap={!isBlocked ? { scale: 0.95 } : undefined}
            className={`w-7 h-7 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition-all shadow-sm ${
              isCompleted
                ? 'bg-gradient-to-br from-green-400 to-green-500 border-green-500 text-white shadow-green-500/25'
                : isBlocked
                ? 'border-gray-300 dark:border-gray-600 cursor-not-allowed bg-gray-100 dark:bg-gray-700'
                : 'border-gray-300 dark:border-gray-600 hover:border-primary-500 dark:hover:border-primary-400 hover:shadow-md bg-white dark:bg-gray-800'
            }`}
            title={isBlocked ? `Blocked by: ${blockedBy?.join(', ')}` : undefined}
          >
            {isCompleted && (
              <motion.svg
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 400, damping: 15 }}
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
              </motion.svg>
            )}
          </motion.button>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <span className={`font-medium ${isCompleted ? 'line-through text-gray-400' : 'text-gray-900'}`}>
                {task.title}
              </span>
              {task.time_estimate_minutes && (
                <span className="text-xs text-gray-400">{formatTime(task.time_estimate_minutes)}</span>
              )}
              {task.difficulty && (
                <span className={`text-xs px-2 py-0.5 rounded ${difficultyConfig[task.difficulty].bg} ${difficultyConfig[task.difficulty].text}`}>
                  {difficultyConfig[task.difficulty].label}
                </span>
              )}
              {task.executor && (
                <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">
                  {executorConfig[task.executor].icon} {executorConfig[task.executor].label}
                </span>
              )}
            </div>

            {task.description && (
              <p className="text-sm text-gray-500 mb-2">{task.description}</p>
            )}

            {/* CRB mini-display */}
            {task.crb && (
              <div className="flex gap-4 text-xs">
                <span className="text-gray-500">💰 {task.crb.cost}</span>
                <span className={riskConfig[task.crb.risk].text}>
                  ⚠️ {task.crb.risk} risk
                </span>
                <span className="text-green-600">✨ {task.crb.benefit}</span>
              </div>
            )}

            {/* Blocked indicator with dependency details */}
            {isBlocked && blockedBy && blockedBy.length > 0 && (
              <div className="mt-3 p-2 bg-orange-50 border border-orange-200 rounded-lg">
                <p className="text-xs font-medium text-orange-700 mb-1 flex items-center gap-1">
                  <span>🔒</span>
                  Blocked by {blockedBy.length} prerequisite task{blockedBy.length > 1 ? 's' : ''}:
                </p>
                <div className="text-xs text-orange-600 ml-4 space-y-0.5">
                  {blockedBy.slice(0, 3).map(depId => (
                    <div key={depId} className="flex items-center gap-1">
                      <span className="text-orange-400">→</span>
                      <span className="font-mono">{depId}</span>
                    </div>
                  ))}
                  {blockedBy.length > 3 && (
                    <p className="text-orange-500 italic">+ {blockedBy.length - 3} more</p>
                  )}
                </div>
              </div>
            )}

            {/* Tutorial hint */}
            {task.tutorial_hint && !expanded && (
              <p className="text-xs text-primary-600 mt-2 italic">
                💡 {task.tutorial_hint}
              </p>
            )}

            {/* Expand button for details */}
            {(task.steps?.length || task.success_criteria?.length || task.common_pitfalls?.length || task.resources?.length) && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="text-xs text-primary-600 hover:text-primary-700 mt-2 flex items-center gap-1"
              >
                {expanded ? 'Hide' : 'Show'} details
                <svg
                  className={`w-3 h-3 transition-transform ${expanded ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Expanded details */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden border-t border-gray-100"
          >
            <div className="p-4 pt-3 space-y-4 bg-gray-50">
              {/* Implementation Steps */}
              {task.steps && task.steps.length > 0 && (
                <div>
                  <h5 className="text-sm font-medium text-gray-900 mb-2">📋 Implementation Steps</h5>
                  <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600">
                    {task.steps.map((step, i) => (
                      <li key={i}>{step}</li>
                    ))}
                  </ol>
                </div>
              )}

              {/* Success Criteria */}
              {task.success_criteria && task.success_criteria.length > 0 && (
                <div>
                  <h5 className="text-sm font-medium text-gray-900 mb-2">✅ Success Criteria</h5>
                  <ul className="space-y-1">
                    {task.success_criteria.map((criteria, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                        <span className="text-green-500 mt-0.5">○</span>
                        {criteria}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Common Pitfalls */}
              {task.common_pitfalls && task.common_pitfalls.length > 0 && (
                <div>
                  <h5 className="text-sm font-medium text-gray-900 mb-2">⚠️ Common Pitfalls</h5>
                  <ul className="space-y-1">
                    {task.common_pitfalls.map((pitfall, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-orange-700 bg-orange-50 rounded px-2 py-1">
                        <span className="mt-0.5">!</span>
                        {pitfall}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Resources */}
              {task.resources && task.resources.length > 0 && (
                <div>
                  <h5 className="text-sm font-medium text-gray-900 mb-2">📚 Resources</h5>
                  <div className="flex flex-wrap gap-2">
                    {task.resources.map((resource, i) => {
                      const typeConfig = {
                        doc: { icon: '📄', bg: 'bg-blue-50', text: 'text-blue-700' },
                        video: { icon: '🎥', bg: 'bg-red-50', text: 'text-red-700' },
                        tool: { icon: '🔧', bg: 'bg-purple-50', text: 'text-purple-700' }
                      }
                      const config = typeConfig[resource.type]

                      return resource.url ? (
                        <a
                          key={i}
                          href={resource.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs ${config.bg} ${config.text} hover:opacity-80`}
                        >
                          {config.icon} {resource.title}
                        </a>
                      ) : (
                        <span
                          key={i}
                          className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs ${config.bg} ${config.text}`}
                        >
                          {config.icon} {resource.title}
                        </span>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Tools */}
              {task.tools && task.tools.length > 0 && (
                <div>
                  <h5 className="text-sm font-medium text-gray-900 mb-2">🛠️ Tools Needed</h5>
                  <div className="flex flex-wrap gap-2">
                    {task.tools.map((tool, i) => (
                      <span key={i} className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-700">
                        {tool}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

function PhaseCard({
  phase,
  completedTasks,
  onTaskToggle,
  expanded,
  onToggleExpand
}: {
  phase: Phase
  completedTasks: Set<string>
  onTaskToggle: (taskId: string) => void
  expanded: boolean
  onToggleExpand: () => void
}) {
  // Handle both data structures (phases.weeks.tasks or phases.tasks)
  const allTasks = (phase.weeks && Array.isArray(phase.weeks))
    ? phase.weeks.flatMap(w => w.tasks || [])
    : (phase.tasks || [])
  const completedCount = allTasks.filter(t => completedTasks.has(t.id)).length
  const progressPercent = allTasks.length ? Math.round((completedCount / allTasks.length) * 100) : 0
  const isComplete = progressPercent === 100

  // Build dependency map
  const getBlockedBy = (task: PlaybookTask): string[] => {
    if (!task.dependencies?.length) return []
    return task.dependencies.filter(depId => !completedTasks.has(depId))
  }

  // Identify critical path tasks (tasks that have dependents)
  const criticalPathTasks = new Set<string>()
  for (const task of allTasks) {
    if (task.dependencies?.length) {
      task.dependencies.forEach(depId => criticalPathTasks.add(depId))
    }
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-2xl shadow-sm overflow-hidden print:shadow-none print:border"
    >
      {/* Phase header */}
      <button
        onClick={onToggleExpand}
        className="w-full p-6 text-left hover:bg-gray-50 transition print:hover:bg-white"
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <span
                className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                  isComplete
                    ? 'bg-green-100 text-green-600'
                    : completedCount > 0
                    ? 'bg-primary-100 text-primary-600'
                    : 'bg-gray-100 text-gray-500'
                }`}
              >
                {isComplete ? '✓' : phase.phase_number}
              </span>
              <div>
                <h4 className="text-lg font-semibold text-gray-900">{phase.title}</h4>
                <p className="text-sm text-gray-500">
                  {phase.duration_weeks} weeks • {completedCount}/{allTasks.length} tasks
                </p>
              </div>
            </div>

            <p className="text-gray-600 ml-13 mb-3">{phase.outcome}</p>

            {/* Progress bar */}
            <div className="ml-13 flex items-center gap-3">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${progressPercent}%` }}
                  className={`h-2 rounded-full ${isComplete ? 'bg-green-500' : 'bg-primary-500'}`}
                />
              </div>
              <span className="text-sm font-medium text-gray-600">{progressPercent}%</span>
            </div>

            {/* Phase CRB summary */}
            {phase.crb_summary && (
              <div className="flex gap-4 mt-3 ml-13 text-sm">
                <span className="text-gray-600">💰 {phase.crb_summary.total_cost}</span>
                <span className="text-gray-600">⏱️ {phase.crb_summary.setup_hours}h</span>
                <span className="text-primary-600 font-medium">
                  CRB: {phase.crb_summary.crb_score}/10
                </span>
              </div>
            )}
          </div>

          <motion.svg
            animate={{ rotate: expanded ? 180 : 0 }}
            className="w-6 h-6 text-gray-400 print:hidden"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </motion.svg>
        </div>
      </button>

      {/* Expanded weeks/tasks */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden border-t print:border-t-0"
          >
            <div className="p-6 space-y-6">
              {/* Handle both data structures: weeks array or direct tasks */}
              {phase.weeks && Array.isArray(phase.weeks) ? (
                // Structure with weeks
                phase.weeks.map(week => {
                  const weekTasks = week.tasks || []
                  const weekCompleted = weekTasks.filter(t => completedTasks.has(t.id)).length

                  return (
                    <div key={week.week_number}>
                      <div className="flex items-center justify-between mb-3">
                        <h5 className="font-semibold text-gray-900">
                          Week {week.week_number}: {week.theme}
                        </h5>
                        <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-600">
                          {weekCompleted}/{weekTasks.length} complete
                        </span>
                      </div>

                      <div className="space-y-3">
                        {weekTasks.map(task => {
                          const blockedBy = getBlockedBy(task)
                          return (
                            <TaskCard
                              key={task.id}
                              task={task}
                              isCompleted={completedTasks.has(task.id)}
                              onToggle={() => onTaskToggle(task.id)}
                              isBlocked={blockedBy.length > 0}
                              blockedBy={blockedBy}
                              isCriticalPath={criticalPathTasks.has(task.id)}
                            />
                          )
                        })}
                      </div>

                      {/* Week checkpoint */}
                      {week.checkpoint && (
                        <div className="mt-4 p-3 bg-primary-50 rounded-lg border border-primary-100">
                          <p className="text-sm text-primary-700">
                            <span className="font-medium">🎯 Checkpoint:</span> {week.checkpoint}
                          </p>
                        </div>
                      )}
                    </div>
                  )
                })
              ) : (
                // Simple structure with tasks directly on phase
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h5 className="font-semibold text-gray-900">
                      {phase.name}
                    </h5>
                    <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-600">
                      {allTasks.filter(t => completedTasks.has(t.id)).length}/{allTasks.length} complete
                    </span>
                  </div>
                  <div className="space-y-3">
                    {allTasks.map(task => {
                      const blockedBy = getBlockedBy(task)
                      return (
                        <TaskCard
                          key={task.id}
                          task={task}
                          isCompleted={completedTasks.has(task.id)}
                          onToggle={() => onTaskToggle(task.id)}
                          isBlocked={blockedBy.length > 0}
                          blockedBy={blockedBy}
                          isCriticalPath={criticalPathTasks.has(task.id)}
                        />
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export default function PlaybookTab({
  playbooks,
  reportId: _reportId, // Reserved for future use with direct API calls
  onTaskComplete,
  completedTasks: controlledCompletedTasks,
  initialCompletedTasks = {}
}: PlaybookTabProps) {
  const [selectedPlaybook, setSelectedPlaybook] = useState(0)
  const [expandedPhase, setExpandedPhase] = useState<number | null>(1)
  // Internal state only used when not in controlled mode
  const [internalCompletedTasks, setInternalCompletedTasks] = useState<Record<string, Set<string>>>(() => {
    const initial: Record<string, Set<string>> = {}
    // Use controlledCompletedTasks if available, otherwise initialCompletedTasks
    const source = controlledCompletedTasks || initialCompletedTasks
    for (const [pbId, taskIds] of Object.entries(source)) {
      initial[pbId] = new Set(taskIds)
    }
    return initial
  })
  const [viewMode, setViewMode] = useState<'full' | 'quick'>('full')
  const printRef = useRef<HTMLDivElement>(null)

  // Determine if we're in controlled mode
  const isControlled = controlledCompletedTasks !== undefined

  if (!playbooks || playbooks.length === 0) {
    return (
      <div className="bg-white rounded-2xl p-8 text-center">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        </div>
        <p className="text-gray-500">No playbooks available yet.</p>
        <p className="text-sm text-gray-400 mt-1">Playbooks are generated after analysis is complete.</p>
      </div>
    )
  }

  const playbook = playbooks[selectedPlaybook]
  const playbookId = playbook.id

  // Get completed tasks - use controlled state if available, otherwise internal state
  const getCompletedTasksSet = (): Set<string> => {
    if (isControlled && controlledCompletedTasks) {
      return new Set(controlledCompletedTasks[playbookId] || [])
    }
    return internalCompletedTasks[playbookId] || new Set<string>()
  }
  const completedTasks = getCompletedTasksSet()

  // Calculate totals - handle both data structures (phases.weeks.tasks or phases.tasks)
  const allTasks = useMemo(() => {
    if (!playbook?.phases) return []
    return playbook.phases.flatMap(p => {
      // If phase has weeks array, use that
      if (p.weeks && Array.isArray(p.weeks)) {
        return p.weeks.flatMap(w => w.tasks || [])
      }
      // Otherwise tasks are directly on the phase
      return p.tasks || []
    })
  }, [playbook])
  const completedCount = allTasks.filter(t => completedTasks.has(t.id) || t.completed).length
  const progressPercent = Math.round((completedCount / allTasks.length) * 100)

  // Filter to only essential tasks for "quick" mode
  const quickTasks = useMemo(() => {
    if (viewMode === 'full') return null
    return allTasks.filter(t => t.difficulty === 'easy' || t.difficulty === 'medium')
  }, [allTasks, viewMode])

  const handleTaskToggle = (taskId: string) => {
    const isNowCompleted = !completedTasks.has(taskId)

    // In controlled mode, don't update internal state - parent manages state via onTaskComplete
    // In uncontrolled mode, update internal state for immediate feedback
    if (!isControlled) {
      setInternalCompletedTasks(prev => {
        const newSet = new Set(prev[playbookId] || [])
        if (isNowCompleted) {
          newSet.add(taskId)
        } else {
          newSet.delete(taskId)
        }
        return { ...prev, [playbookId]: newSet }
      })
    }

    // Always call the callback so parent can sync to backend
    onTaskComplete?.(playbookId, taskId, isNowCompleted)
  }

  const handlePrint = () => {
    window.print()
  }

  const handleExportChecklist = () => {
    let checklist = `# ${formatOptionType(playbook.option_type || 'implementation')} Checklist\n\n`
    checklist += `Total: ${allTasks.length} tasks | Completed: ${completedCount}\n\n`

    for (const phase of playbook.phases || []) {
      checklist += `## Phase ${phase.phase_number || ''}: ${phase.title || phase.name || ''}\n\n`

      // Handle both data structures
      if (phase.weeks && Array.isArray(phase.weeks)) {
        for (const week of phase.weeks) {
          checklist += `### Week ${week.week_number}: ${week.theme}\n\n`

          for (const task of week.tasks || []) {
            const checked = completedTasks.has(task.id) ? 'x' : ' '
            checklist += `- [${checked}] ${task.title} (${task.time_estimate_minutes || task.hours || '?'}min, ${task.difficulty || 'medium'})\n`
            if (task.description) {
              checklist += `  - ${task.description}\n`
            }
          }
          checklist += '\n'
        }
      } else {
        // Tasks directly on phase
        for (const task of phase.tasks || []) {
          const checked = completedTasks.has(task.id) ? 'x' : ' '
          checklist += `- [${checked}] ${task.title} (${task.time_estimate_minutes || task.hours || '?'}min, ${task.difficulty || 'medium'})\n`
          if (task.description) {
            checklist += `  - ${task.description}\n`
          }
        }
        checklist += '\n'
      }
    }

    // Download as file
    const blob = new Blob([checklist], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `playbook-checklist-${playbook.option_type}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6 print:space-y-4" ref={printRef}>
      {/* Playbook selector & controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 print:hidden">
        {/* Playbook tabs */}
        {playbooks.length > 1 && (
          <div className="flex gap-2 overflow-x-auto pb-2">
            {playbooks.map((pb, i) => (
              <button
                key={pb.id}
                onClick={() => setSelectedPlaybook(i)}
                className={`px-4 py-2 rounded-xl whitespace-nowrap transition font-medium ${
                  i === selectedPlaybook
                    ? 'bg-primary-600 text-white'
                    : 'bg-white border border-gray-200 hover:bg-gray-50 text-gray-700'
                }`}
              >
                {formatOptionType(pb.option_type)}
              </button>
            ))}
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode(v => v === 'full' ? 'quick' : 'full')}
            className="px-3 py-2 text-sm rounded-xl bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 flex items-center gap-2"
          >
            {viewMode === 'full' ? '⚡ Quick Start' : '📋 Full Guide'}
          </button>
          <button
            onClick={handleExportChecklist}
            className="px-3 py-2 text-sm rounded-xl bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 flex items-center gap-2"
          >
            📥 Export
          </button>
          <button
            onClick={handlePrint}
            className="px-3 py-2 text-sm rounded-xl bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 flex items-center gap-2"
          >
            🖨️ Print
          </button>
        </div>
      </div>

      {/* Header with progress */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl p-6 shadow-sm print:shadow-none print:border"
      >
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Your {playbook.total_weeks}-Week Implementation Playbook
            </h3>
            <p className="text-sm text-gray-500">
              {playbook.personalization_context.team_size} team •
              Tech level {playbook.personalization_context.technical_level}/5 •
              €{playbook.personalization_context.budget_monthly}/mo budget
            </p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold text-primary-600">{progressPercent}%</p>
            <p className="text-sm text-gray-500">{completedCount}/{allTasks.length} tasks</p>
          </div>
        </div>

        {/* Visual indicators legend */}
        <div className="flex flex-wrap gap-3 text-xs text-gray-600 pt-3 border-t border-gray-100 print:hidden">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 border-2 border-purple-300 rounded" />
            <span>Critical path</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 border-2 border-gray-200 rounded bg-gray-50 opacity-60" />
            <span>Blocked</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 border-2 border-green-200 rounded bg-green-50" />
            <span>Completed</span>
          </div>
        </div>

        {/* Progress bar */}
        <div className="w-full bg-gray-200 rounded-full h-3">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progressPercent}%` }}
            transition={{ duration: 0.5 }}
            className={`h-3 rounded-full ${progressPercent === 100 ? 'bg-green-500' : 'bg-primary-600'}`}
          />
        </div>

        {/* Milestone indicator */}
        {progressPercent > 0 && progressPercent < 100 && (
          <p className="text-sm text-gray-500 mt-2">
            {progressPercent < 25 && '🚀 Just getting started!'}
            {progressPercent >= 25 && progressPercent < 50 && '💪 Making good progress!'}
            {progressPercent >= 50 && progressPercent < 75 && '⭐ Halfway there!'}
            {progressPercent >= 75 && progressPercent < 100 && '🎯 Almost done!'}
          </p>
        )}
        {progressPercent === 100 && (
          <p className="text-sm text-green-600 font-medium mt-2">
            🎉 Congratulations! You've completed all tasks!
          </p>
        )}
      </motion.div>

      {/* Visual Timeline Roadmap */}
      <TimelineRoadmap
        phases={playbook.phases}
        completedTasks={completedTasks}
        onPhaseClick={(num) => setExpandedPhase(expandedPhase === num ? null : num)}
        activePhase={expandedPhase}
      />

      {/* Quick Start Mode */}
      {viewMode === 'quick' && quickTasks && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-2xl p-6">
          <h3 className="font-semibold text-yellow-800 mb-2">⚡ Quick Start Mode</h3>
          <p className="text-sm text-yellow-700 mb-4">
            Showing {quickTasks.length} essential tasks (easy & medium difficulty). Switch to Full Guide for all {allTasks.length} tasks.
          </p>
          <div className="space-y-3">
            {quickTasks.map(task => (
              <TaskCard
                key={task.id}
                task={task}
                isCompleted={completedTasks.has(task.id)}
                onToggle={() => handleTaskToggle(task.id)}
                isBlocked={false}
              />
            ))}
          </div>
        </div>
      )}

      {/* Full Phases (hidden in quick mode) */}
      {viewMode === 'full' && (
        <div className="space-y-4">
          {playbook.phases.map((phase, idx) => {
            const phaseNum = phase.phase_number ?? idx + 1
            return (
              <PhaseCard
                key={phaseNum}
                phase={phase}
                completedTasks={completedTasks}
                onTaskToggle={handleTaskToggle}
                expanded={expandedPhase === phaseNum}
                onToggleExpand={() => setExpandedPhase(
                  expandedPhase === phaseNum ? null : phaseNum
                )}
              />
            )
          })}
        </div>
      )}

      {/* Print styles */}
      <style>{`
        @media print {
          .print\\:hidden { display: none !important; }
          .print\\:shadow-none { box-shadow: none !important; }
          .print\\:border { border: 1px solid #e5e7eb !important; }
          .print\\:space-y-4 > * + * { margin-top: 1rem !important; }
          .print\\:hover\\:bg-white:hover { background-color: white !important; }
          .print\\:border-t-0 { border-top: none !important; }
        }
      `}</style>
    </div>
  )
}
