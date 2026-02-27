import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import { Database, Plus, Sparkles, CheckCircle, Cable, Workflow, User, Zap, Terminal } from 'lucide-react'

interface FlowNodeData {
  label: string
  nodeType: 'existing_tool' | 'new_tool' | 'ai_layer' | 'output'
    | 'mcp_server' | 'automation_platform' | 'data_store' | 'human_step' | 'trigger' | 'claude_code'
  description?: string
}

const nodeConfig = {
  existing_tool: {
    borderColor: 'border-l-emerald-500',
    bg: 'bg-white dark:bg-gray-800',
    textColor: 'text-emerald-700 dark:text-emerald-400',
    badge: 'In your stack',
    badgeBg: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400',
    Icon: Database,
  },
  new_tool: {
    borderColor: 'border-l-blue-500',
    bg: 'bg-white dark:bg-gray-800',
    textColor: 'text-blue-700 dark:text-blue-400',
    badge: 'Add this',
    badgeBg: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
    Icon: Plus,
  },
  ai_layer: {
    borderColor: 'border-l-purple-500',
    bg: 'bg-white dark:bg-gray-800',
    textColor: 'text-purple-700 dark:text-purple-400',
    badge: 'AI',
    badgeBg: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400',
    Icon: Sparkles,
  },
  output: {
    borderColor: 'border-l-gray-400',
    bg: 'bg-white dark:bg-gray-800',
    textColor: 'text-gray-700 dark:text-gray-300',
    badge: 'Result',
    badgeBg: 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400',
    Icon: CheckCircle,
  },
  mcp_server: {
    borderColor: 'border-l-indigo-500',
    bg: 'bg-white dark:bg-gray-800',
    textColor: 'text-indigo-700 dark:text-indigo-400',
    badge: 'MCP',
    badgeBg: 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400',
    Icon: Cable,
  },
  automation_platform: {
    borderColor: 'border-l-orange-500',
    bg: 'bg-white dark:bg-gray-800',
    textColor: 'text-orange-700 dark:text-orange-400',
    badge: 'Automation',
    badgeBg: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400',
    Icon: Workflow,
  },
  data_store: {
    borderColor: 'border-l-cyan-500',
    bg: 'bg-white dark:bg-gray-800',
    textColor: 'text-cyan-700 dark:text-cyan-400',
    badge: 'Data',
    badgeBg: 'bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-400',
    Icon: Database,
  },
  human_step: {
    borderColor: 'border-l-amber-500',
    bg: 'bg-white dark:bg-gray-800',
    textColor: 'text-amber-700 dark:text-amber-400',
    badge: 'Human',
    badgeBg: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400',
    Icon: User,
  },
  trigger: {
    borderColor: 'border-l-rose-500',
    bg: 'bg-white dark:bg-gray-800',
    textColor: 'text-rose-700 dark:text-rose-400',
    badge: 'Trigger',
    badgeBg: 'bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-400',
    Icon: Zap,
  },
  claude_code: {
    borderColor: 'border-l-violet-500',
    bg: 'bg-white dark:bg-gray-800',
    textColor: 'text-violet-700 dark:text-violet-400',
    badge: 'Claude Code',
    badgeBg: 'bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-400',
    Icon: Terminal,
  },
} as const

function FlowNode({ data }: NodeProps) {
  const nodeData = data as unknown as FlowNodeData
  const config = nodeConfig[nodeData.nodeType] || nodeConfig.output
  const { Icon } = config

  return (
    <div
      className={`
        relative group
        px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600
        border-l-4 ${config.borderColor} ${config.bg}
        shadow-sm min-w-[120px] max-w-[160px]
      `}
    >
      {nodeData.description && (
        <div className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-gray-900 text-white text-[10px] rounded shadow-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
          {nodeData.description}
        </div>
      )}
      <Handle type="target" position={Position.Left} className="!w-2 !h-2 !bg-gray-400 !border-0" />
      <div className="flex items-center gap-2">
        <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${config.textColor}`} />
        <span className="text-xs font-medium text-gray-900 dark:text-white truncate">
          {nodeData.label}
        </span>
      </div>
      <span className={`inline-block mt-1 px-1.5 py-0.5 text-[10px] rounded ${config.badgeBg}`}>
        {config.badge}
      </span>
      <Handle type="source" position={Position.Right} className="!w-2 !h-2 !bg-gray-400 !border-0" />
    </div>
  )
}

function FlowNodeTB({ data }: NodeProps) {
  const nodeData = data as unknown as FlowNodeData
  const config = nodeConfig[nodeData.nodeType] || nodeConfig.output
  const { Icon } = config

  return (
    <div
      className={`
        relative group
        px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600
        border-l-4 ${config.borderColor} ${config.bg}
        shadow-sm min-w-[120px] max-w-[160px]
      `}
    >
      {nodeData.description && (
        <div className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-gray-900 text-white text-[10px] rounded shadow-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
          {nodeData.description}
        </div>
      )}
      <Handle type="target" position={Position.Top} className="!w-2 !h-2 !bg-gray-400 !border-0" />
      <div className="flex items-center gap-2">
        <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${config.textColor}`} />
        <span className="text-xs font-medium text-gray-900 dark:text-white truncate">
          {nodeData.label}
        </span>
      </div>
      <span className={`inline-block mt-1 px-1.5 py-0.5 text-[10px] rounded ${config.badgeBg}`}>
        {config.badge}
      </span>
      <Handle type="source" position={Position.Bottom} className="!w-2 !h-2 !bg-gray-400 !border-0" />
    </div>
  )
}

export const flowNodeTypes = {
  flowNode: memo(FlowNode),
  flowNodeTB: memo(FlowNodeTB),
}

export function FlowLegend() {
  return (
    <div className="flex flex-wrap gap-3 mt-2 text-[10px] text-gray-500 dark:text-gray-400">
      <span className="flex items-center gap-1">
        <span className="w-2 h-2 rounded-sm bg-emerald-500" /> Existing tool
      </span>
      <span className="flex items-center gap-1">
        <span className="w-2 h-2 rounded-sm bg-blue-500" /> New tool
      </span>
      <span className="flex items-center gap-1">
        <span className="w-2 h-2 rounded-sm bg-purple-500" /> AI layer
      </span>
      <span className="flex items-center gap-1">
        <span className="w-2 h-2 rounded-sm bg-gray-400" /> Result
      </span>
      <span className="flex items-center gap-1">
        <span className="w-2 h-2 rounded-sm bg-indigo-500" /> MCP
      </span>
      <span className="flex items-center gap-1">
        <span className="w-2 h-2 rounded-sm bg-orange-500" /> Automation
      </span>
      <span className="flex items-center gap-1">
        <span className="w-2 h-2 rounded-sm bg-cyan-500" /> Data
      </span>
      <span className="flex items-center gap-1">
        <span className="w-2 h-2 rounded-sm bg-amber-500" /> Human
      </span>
      <span className="flex items-center gap-1">
        <span className="w-2 h-2 rounded-sm bg-rose-500" /> Trigger
      </span>
      <span className="flex items-center gap-1">
        <span className="w-2 h-2 rounded-sm bg-violet-500" /> Claude Code
      </span>
    </div>
  )
}
