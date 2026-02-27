import { useMemo, useCallback } from 'react'
import {
  ReactFlow,
  type Node,
  type Edge,
  ConnectionLineType,
  MarkerType,
} from '@xyflow/react'
import dagre from 'dagre'
import { motion } from 'framer-motion'
import { flowNodeTypes, FlowLegend } from './flow/FlowNodes'

import '@xyflow/react/dist/style.css'

interface FlowNodeData {
  id: string
  label: string
  type: 'existing_tool' | 'new_tool' | 'ai_layer' | 'output'
    | 'mcp_server' | 'automation_platform' | 'data_store' | 'human_step' | 'trigger' | 'claude_code'
  description?: string
}

interface FlowEdgeData {
  from: string
  to: string
  label?: string
}

export interface AutomationFlow {
  nodes: FlowNodeData[]
  edges: FlowEdgeData[]
}

interface AutomationFlowBuilderProps {
  flow: AutomationFlow
  title?: string
  height?: number
  compact?: boolean
  direction?: 'LR' | 'TB'
}

const NODE_WIDTH = 150
const NODE_HEIGHT = 60
const COMPACT_NODE_WIDTH = 120
const COMPACT_NODE_HEIGHT = 45

function layoutNodes(
  flowData: AutomationFlow,
  options: { direction?: 'LR' | 'TB'; compact?: boolean } = {}
): { nodes: Node[]; edges: Edge[] } {
  const { direction = 'LR', compact = false } = options
  const nodeWidth = compact ? COMPACT_NODE_WIDTH : NODE_WIDTH
  const nodeHeight = compact ? COMPACT_NODE_HEIGHT : NODE_HEIGHT

  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: direction, nodesep: compact ? 25 : 40, ranksep: compact ? 35 : 60 })

  for (const node of flowData.nodes) {
    g.setNode(node.id, { width: nodeWidth, height: nodeHeight })
  }

  for (const edge of flowData.edges) {
    g.setEdge(edge.from, edge.to)
  }

  dagre.layout(g)

  const nodeType = direction === 'TB' ? 'flowNodeTB' : 'flowNode'

  const nodes: Node[] = flowData.nodes.map((node) => {
    const pos = g.node(node.id)
    return {
      id: node.id,
      type: nodeType,
      position: {
        x: pos.x - nodeWidth / 2,
        y: pos.y - nodeHeight / 2,
      },
      data: { label: node.label, nodeType: node.type, description: node.description },
    }
  })

  const edges: Edge[] = flowData.edges.map((edge, i) => ({
    id: `e-${edge.from}-${edge.to}-${i}`,
    source: edge.from,
    target: edge.to,
    label: edge.label,
    type: ConnectionLineType.SmoothStep,
    animated: true,
    style: { stroke: '#94a3b8', strokeWidth: 1.5 },
    labelStyle: { fontSize: compact ? 8 : 10, fill: '#6b7280' },
    markerEnd: { type: MarkerType.ArrowClosed, width: 12, height: 12, color: '#94a3b8' },
  }))

  return { nodes, edges }
}

export default function AutomationFlowBuilder({
  flow,
  title = 'How it connects',
  height = 300,
  compact = false,
  direction = 'LR',
}: AutomationFlowBuilderProps) {
  const { nodes, edges } = useMemo(
    () => layoutNodes(flow, { direction, compact }),
    [flow, direction, compact]
  )

  const proOptions = useMemo(() => ({ hideAttribution: true }), [])
  const onInit = useCallback((instance: { fitView: () => void }) => {
    setTimeout(() => instance.fitView(), 50)
  }, [])

  if (!flow.nodes.length) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 overflow-hidden"
    >
      {title && (
        <div className="px-3 py-2 border-b border-gray-200 dark:border-gray-700">
          <p className={`font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide ${compact ? 'text-[10px]' : 'text-xs'}`}>
            {title}
          </p>
        </div>
      )}
      <div style={{ height }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={flowNodeTypes}
          proOptions={proOptions}
          fitView
          onInit={onInit}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          panOnDrag={false}
          zoomOnScroll={false}
          zoomOnPinch={false}
          zoomOnDoubleClick={false}
          preventScrolling={false}
          className="bg-gray-50 dark:bg-gray-900/50"
        />
      </div>
      {!compact && (
        <div className="px-3 pb-2">
          <FlowLegend />
        </div>
      )}
    </motion.div>
  )
}
