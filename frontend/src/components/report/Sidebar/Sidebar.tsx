import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'

export interface SidebarItem {
  type: 'overview' | 'finding' | 'action' | 'playbook' | 'tool'
  id: string | null
}

export interface FindingItem {
  id: string
  title: string
  status: 'pending' | 'in_progress' | 'completed'
}

export interface ActionItem {
  id: string
  title: string
  priority: 'high' | 'medium' | 'low'
}

export interface PlaybookPhase {
  id: string
  title: string
  completedTasks: number
  totalTasks: number
}

export interface SidebarProps {
  companyName: string
  industry: string
  score: number
  findings: FindingItem[]
  actions: ActionItem[]
  playbookPhases: PlaybookPhase[]
  activeItem: SidebarItem
  onItemClick: (item: SidebarItem) => void
  className?: string
}

interface SectionState {
  overview: boolean
  findings: boolean
  actions: boolean
  playbook: boolean
  tools: boolean
}

const StatusIcon = ({ status }: { status: 'pending' | 'in_progress' | 'completed' }) => {
  const icons = {
    completed: (
      <span className="w-3 h-3 rounded-full bg-green-500 flex items-center justify-center">
        <span className="text-white text-[8px]">●</span>
      </span>
    ),
    in_progress: (
      <span className="w-3 h-3 rounded-full border-2 border-yellow-500 bg-yellow-500/30" />
    ),
    pending: (
      <span className="w-3 h-3 rounded-full border-2 border-gray-300 dark:border-gray-600" />
    ),
  }
  return icons[status]
}

export function Sidebar({
  companyName,
  industry,
  score,
  findings,
  actions,
  playbookPhases,
  activeItem,
  onItemClick,
  className = '',
}: SidebarProps) {
  const [expanded, setExpanded] = useState<SectionState>({
    overview: true,
    findings: true,
    actions: true,
    playbook: true,
    tools: false,
  })

  const toggleSection = (section: keyof SectionState) => {
    setExpanded(prev => ({ ...prev, [section]: !prev[section] }))
  }

  const isActive = (type: SidebarItem['type'], id: string | null) => {
    return activeItem.type === type && activeItem.id === id
  }

  const itemClasses = (type: SidebarItem['type'], id: string | null) => {
    const base = 'w-full text-left px-3 py-2 text-sm rounded-lg transition-colors flex items-center gap-2'
    if (isActive(type, id)) {
      return `${base} bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 border-l-2 border-primary-500`
    }
    return `${base} hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300`
  }

  return (
    <aside className={`w-[280px] h-full border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 flex flex-col overflow-hidden ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <h2 className="font-semibold text-gray-900 dark:text-white truncate">
          {companyName}
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400">{industry}</p>
        <div className="mt-2 flex items-center gap-2">
          <span className="text-sm text-gray-500 dark:text-gray-400">Score:</span>
          <span className="text-lg font-bold text-primary-600 dark:text-primary-400">
            {score}
          </span>
          <span className="text-sm text-gray-400">/100</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-2">
        {/* Overview Section */}
        <div className="mb-2">
          <button
            onClick={() => {
              onItemClick({ type: 'overview', id: null })
              if (!expanded.overview) toggleSection('overview')
            }}
            className="w-full flex items-center justify-between px-2 py-1.5 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          >
            <span className="flex items-center gap-1">
              {expanded.overview ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              Overview
            </span>
          </button>
          {expanded.overview && (
            <div className="ml-2 space-y-0.5">
              <button
                onClick={() => onItemClick({ type: 'overview', id: null })}
                className={itemClasses('overview', null)}
              >
                Verdict
              </button>
            </div>
          )}
        </div>

        {/* Findings Section */}
        <div className="mb-2">
          <button
            onClick={() => toggleSection('findings')}
            className="w-full flex items-center justify-between px-2 py-1.5 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          >
            <span className="flex items-center gap-1">
              {expanded.findings ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              Findings
            </span>
            <span className="text-xs text-gray-400">({findings.length})</span>
          </button>
          {expanded.findings && (
            <div className="ml-2 space-y-0.5">
              {findings.map(finding => (
                <button
                  key={finding.id}
                  onClick={() => onItemClick({ type: 'finding', id: finding.id })}
                  className={itemClasses('finding', finding.id)}
                >
                  <StatusIcon status={finding.status} />
                  <span className="truncate">{finding.title}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Actions Section */}
        <div className="mb-2">
          <button
            onClick={() => toggleSection('actions')}
            className="w-full flex items-center justify-between px-2 py-1.5 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          >
            <span className="flex items-center gap-1">
              {expanded.actions ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              Actions
            </span>
            <span className="text-xs text-gray-400">({actions.length})</span>
          </button>
          {expanded.actions && (
            <div className="ml-2 space-y-0.5">
              {actions.map((action, index) => (
                <button
                  key={action.id}
                  onClick={() => onItemClick({ type: 'action', id: action.id })}
                  className={itemClasses('action', action.id)}
                >
                  <span className="text-xs font-medium text-gray-400 w-4">{index + 1}.</span>
                  <span className="truncate">{action.title}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Playbook Section */}
        <div className="mb-2">
          <button
            onClick={() => toggleSection('playbook')}
            className="w-full flex items-center justify-between px-2 py-1.5 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          >
            <span className="flex items-center gap-1">
              {expanded.playbook ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              Playbook
            </span>
          </button>
          {expanded.playbook && (
            <div className="ml-2 space-y-0.5">
              {playbookPhases.map(phase => (
                <button
                  key={phase.id}
                  onClick={() => onItemClick({ type: 'playbook', id: phase.id })}
                  className={itemClasses('playbook', phase.id)}
                >
                  <span className="truncate flex-1">{phase.title}</span>
                  <span className="text-xs text-gray-400">
                    ({phase.completedTasks}/{phase.totalTasks})
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Tools Section */}
        <div className="mb-2">
          <button
            onClick={() => toggleSection('tools')}
            className="w-full flex items-center justify-between px-2 py-1.5 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          >
            <span className="flex items-center gap-1">
              {expanded.tools ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              Tools
            </span>
          </button>
          {expanded.tools && (
            <div className="ml-2 space-y-0.5">
              <button
                onClick={() => onItemClick({ type: 'tool', id: 'roi' })}
                className={itemClasses('tool', 'roi')}
              >
                ROI Calculator
              </button>
              <button
                onClick={() => onItemClick({ type: 'tool', id: 'stack' })}
                className={itemClasses('tool', 'stack')}
              >
                Stack Analysis
              </button>
              <button
                onClick={() => onItemClick({ type: 'tool', id: 'insights' })}
                className={itemClasses('tool', 'insights')}
              >
                Industry Insights
              </button>
            </div>
          )}
        </div>
      </nav>
    </aside>
  )
}

export default Sidebar
