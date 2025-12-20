// frontend/src/components/report/PlaybookTab.tsx
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface TaskCRB {
  cost: string
  risk: 'low' | 'medium' | 'high'
  benefit: string
}

interface PlaybookTask {
  id: string
  title: string
  description: string
  time_estimate_minutes: number
  difficulty: 'easy' | 'medium' | 'hard'
  executor: 'owner' | 'team' | 'hire_out'
  tools: string[]
  tutorial_hint?: string
  crb: TaskCRB
  completed: boolean
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
  phase_number: number
  title: string
  duration_weeks: number
  outcome: string
  crb_summary: PhaseCRBSummary
  weeks: Week[]
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
  onTaskComplete?: (playbookId: string, taskId: string, completed: boolean) => void
}

export default function PlaybookTab({ playbooks, onTaskComplete }: PlaybookTabProps) {
  const [selectedPlaybook, setSelectedPlaybook] = useState(0)
  const [expandedPhase, setExpandedPhase] = useState<number | null>(1)
  const [taskState, setTaskState] = useState<Record<string, boolean>>({})

  if (!playbooks || playbooks.length === 0) {
    return (
      <div className="bg-white rounded-2xl p-8 text-center">
        <p className="text-gray-500">No playbooks available yet.</p>
      </div>
    )
  }

  const playbook = playbooks[selectedPlaybook]

  // Calculate progress
  const allTasks = playbook.phases.flatMap(p => p.weeks.flatMap(w => w.tasks))
  const completedTasks = allTasks.filter(t => taskState[t.id] || t.completed).length
  const progressPercent = Math.round((completedTasks / allTasks.length) * 100)

  const handleTaskToggle = (taskId: string) => {
    const newState = !taskState[taskId]
    setTaskState(prev => ({ ...prev, [taskId]: newState }))
    onTaskComplete?.(playbook.id, taskId, newState)
  }

  const difficultyColor = {
    easy: 'bg-green-100 text-green-700',
    medium: 'bg-yellow-100 text-yellow-700',
    hard: 'bg-red-100 text-red-700',
  }

  const executorLabel = {
    owner: 'You',
    team: 'Team',
    hire_out: 'Hire out',
  }

  const riskColor = {
    low: 'text-green-600',
    medium: 'text-yellow-600',
    high: 'text-red-600',
  }

  return (
    <div className="space-y-6">
      {/* Playbook selector */}
      {playbooks.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-2">
          {playbooks.map((pb, i) => (
            <button
              key={pb.id}
              onClick={() => setSelectedPlaybook(i)}
              className={`px-4 py-2 rounded-xl whitespace-nowrap transition ${
                i === selectedPlaybook
                  ? 'bg-primary-600 text-white'
                  : 'bg-white border border-gray-200 hover:bg-gray-50'
              }`}
            >
              {pb.option_type.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
            </button>
          ))}
        </div>
      )}

      {/* Header with progress */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl p-6 shadow-sm"
      >
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Your {playbook.total_weeks}-Week Implementation Playbook
            </h3>
            <p className="text-sm text-gray-500">
              Based on: {playbook.personalization_context.team_size} team •
              Tech level {playbook.personalization_context.technical_level}/5 •
              €{playbook.personalization_context.budget_monthly}/mo budget
            </p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-primary-600">{progressPercent}%</p>
            <p className="text-xs text-gray-500">{completedTasks}/{allTasks.length} tasks</p>
          </div>
        </div>

        {/* Progress bar */}
        <div className="w-full bg-gray-200 rounded-full h-3">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progressPercent}%` }}
            transition={{ duration: 0.5 }}
            className="bg-primary-600 h-3 rounded-full"
          />
        </div>
      </motion.div>

      {/* Phases */}
      <div className="space-y-4">
        {playbook.phases.map((phase) => (
          <motion.div
            key={phase.phase_number}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: phase.phase_number * 0.1 }}
            className="bg-white rounded-2xl shadow-sm overflow-hidden"
          >
            {/* Phase header */}
            <div
              className="p-6 cursor-pointer hover:bg-gray-50 transition"
              onClick={() => setExpandedPhase(
                expandedPhase === phase.phase_number ? null : phase.phase_number
              )}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="w-8 h-8 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center font-bold">
                      {phase.phase_number}
                    </span>
                    <h4 className="text-lg font-semibold text-gray-900">{phase.title}</h4>
                    <span className="text-sm text-gray-500">
                      Weeks {phase.weeks[0]?.week_number}-{phase.weeks[phase.weeks.length - 1]?.week_number}
                    </span>
                  </div>
                  <p className="text-gray-600 ml-11">{phase.outcome}</p>

                  {/* Phase CRB summary */}
                  <div className="flex gap-4 mt-3 ml-11 text-sm">
                    <span className="text-gray-600">
                      Cost: {phase.crb_summary.total_cost}
                    </span>
                    <span className="text-gray-600">
                      Time: {phase.crb_summary.setup_hours} hrs
                    </span>
                    <span className="text-primary-600 font-medium">
                      CRB: {phase.crb_summary.crb_score}/10
                    </span>
                  </div>
                </div>

                <motion.svg
                  animate={{ rotate: expandedPhase === phase.phase_number ? 180 : 0 }}
                  className="w-6 h-6 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </motion.svg>
              </div>
            </div>

            {/* Expanded weeks/tasks */}
            <AnimatePresence>
              {expandedPhase === phase.phase_number && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden border-t"
                >
                  <div className="p-6 space-y-6">
                    {phase.weeks.map((week) => (
                      <div key={week.week_number}>
                        <div className="flex items-center gap-2 mb-3">
                          <h5 className="font-semibold text-gray-900">
                            Week {week.week_number}: {week.theme}
                          </h5>
                          <span className="text-xs text-gray-500">
                            {week.tasks.filter(t => taskState[t.id] || t.completed).length}/{week.tasks.length} complete
                          </span>
                        </div>

                        <div className="space-y-2">
                          {week.tasks.map((task) => (
                            <div
                              key={task.id}
                              className={`p-4 rounded-xl border transition ${
                                taskState[task.id] || task.completed
                                  ? 'bg-green-50 border-green-200'
                                  : 'bg-gray-50 border-gray-200 hover:border-primary-300'
                              }`}
                            >
                              <div className="flex items-start gap-3">
                                <button
                                  onClick={() => handleTaskToggle(task.id)}
                                  className={`w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition ${
                                    taskState[task.id] || task.completed
                                      ? 'bg-green-500 border-green-500 text-white'
                                      : 'border-gray-300 hover:border-primary-500'
                                  }`}
                                >
                                  {(taskState[task.id] || task.completed) && (
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                    </svg>
                                  )}
                                </button>

                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 flex-wrap">
                                    <span className={`font-medium ${taskState[task.id] || task.completed ? 'line-through text-gray-400' : 'text-gray-900'}`}>
                                      {task.title}
                                    </span>
                                    <span className="text-xs text-gray-400">
                                      {task.time_estimate_minutes} min
                                    </span>
                                    <span className={`text-xs px-2 py-0.5 rounded ${difficultyColor[task.difficulty]}`}>
                                      {task.difficulty}
                                    </span>
                                    <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">
                                      {executorLabel[task.executor]}
                                    </span>
                                  </div>

                                  {task.description && (
                                    <p className="text-sm text-gray-500 mt-1">{task.description}</p>
                                  )}

                                  {/* Task CRB */}
                                  <div className="flex gap-4 mt-2 text-xs">
                                    <span className="text-gray-500">Cost: {task.crb.cost}</span>
                                    <span className={riskColor[task.crb.risk]}>Risk: {task.crb.risk}</span>
                                    <span className="text-green-600">Benefit: {task.crb.benefit}</span>
                                  </div>

                                  {task.tutorial_hint && (
                                    <p className="text-xs text-primary-600 mt-2">
                                      Tip: {task.tutorial_hint}
                                    </p>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>

                        {/* Week checkpoint */}
                        <div className="mt-3 p-3 bg-primary-50 rounded-lg">
                          <p className="text-sm text-primary-700">
                            <span className="font-medium">Checkpoint:</span> {week.checkpoint}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
