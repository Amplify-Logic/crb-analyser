import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import { Database, Plus, Sparkles, CheckCircle } from 'lucide-react'

interface FlowNodeData {
  label: string
  nodeType: 'existing_tool' | 'new_tool' | 'ai_layer' | 'output'
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
} as const

function FlowNode({ data }: NodeProps) {
  const nodeData = data as unknown as FlowNodeData
  const config = nodeConfig[nodeData.nodeType] || nodeConfig.output
  const { Icon } = config

  return (
    <div
      className={`
        px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600
        border-l-4 ${config.borderColor} ${config.bg}
        shadow-sm min-w-[120px] max-w-[160px]
      `}
    >
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

export const flowNodeTypes = {
  flowNode: memo(FlowNode),
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
    </div>
  )
}
