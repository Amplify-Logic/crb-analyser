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

interface SystemArchitectureDiagramProps {
  architecture: {
    existing_tools: { id: string; name: string; category: string; monthly_cost?: number }[]
    ai_layer: { id: string; name: string; category?: string }[]
    automations: { id: string; name: string; trigger: string; action: string; tools_used?: string[] }[]
    connections: { id: string; from_node: string; to_node: string; data_flow: string; integration_type: string }[]
  }
}

const NODE_WIDTH = 150
const NODE_HEIGHT = 60

function buildDiagram(architecture: SystemArchitectureDiagramProps['architecture']): { nodes: Node[]; edges: Edge[] } {
  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: 'TB', nodesep: 40, ranksep: 80 })

  // Row 1: Existing tools
  for (const tool of architecture.existing_tools) {
    g.setNode(tool.id, { width: NODE_WIDTH, height: NODE_HEIGHT })
  }

  // Row 2: AI layer + automations
  for (const ai of architecture.ai_layer) {
    g.setNode(ai.id, { width: NODE_WIDTH, height: NODE_HEIGHT })
  }
  for (const auto of architecture.automations) {
    g.setNode(auto.id, { width: NODE_WIDTH, height: NODE_HEIGHT })
  }

  // Row 3: Outputs derived from automations
  const outputNodes: { id: string; label: string }[] = architecture.automations.map((auto, i) => ({
    id: `output-${auto.id}-${i}`,
    label: auto.action,
  }))
  for (const out of outputNodes) {
    g.setNode(out.id, { width: NODE_WIDTH, height: NODE_HEIGHT })
  }

  // Edges from connections
  for (const conn of architecture.connections) {
    g.setEdge(conn.from_node, conn.to_node)
  }

  // Connect automations to their outputs
  architecture.automations.forEach((auto, i) => {
    g.setEdge(auto.id, outputNodes[i].id)
  })

  dagre.layout(g)

  // Build ReactFlow nodes
  const nodes: Node[] = [
    ...architecture.existing_tools.map((tool) => {
      const pos = g.node(tool.id)
      if (!pos) return null
      return {
        id: tool.id,
        type: 'flowNodeTB',
        position: { x: pos.x - NODE_WIDTH / 2, y: pos.y - NODE_HEIGHT / 2 },
        data: {
          label: tool.name,
          nodeType: 'existing_tool',
          description: tool.category,
        },
      }
    }),
    ...architecture.ai_layer.map((ai) => {
      const pos = g.node(ai.id)
      if (!pos) return null
      return {
        id: ai.id,
        type: 'flowNodeTB',
        position: { x: pos.x - NODE_WIDTH / 2, y: pos.y - NODE_HEIGHT / 2 },
        data: {
          label: ai.name,
          nodeType: 'ai_layer',
          description: ai.category,
        },
      }
    }),
    ...architecture.automations.map((auto) => {
      const pos = g.node(auto.id)
      if (!pos) return null
      return {
        id: auto.id,
        type: 'flowNodeTB',
        position: { x: pos.x - NODE_WIDTH / 2, y: pos.y - NODE_HEIGHT / 2 },
        data: {
          label: auto.name,
          nodeType: 'automation_platform',
          description: auto.trigger,
        },
      }
    }),
    ...outputNodes.map((out) => {
      const pos = g.node(out.id)
      if (!pos) return null
      return {
        id: out.id,
        type: 'flowNodeTB',
        position: { x: pos.x - NODE_WIDTH / 2, y: pos.y - NODE_HEIGHT / 2 },
        data: {
          label: out.label,
          nodeType: 'output',
        },
      }
    }),
  ].filter(Boolean) as Node[]

  // Build edges from connections
  const edges: Edge[] = [
    ...architecture.connections.map((conn, i) => {
      const isApi = conn.integration_type === 'api'
      const isWebhook = conn.integration_type === 'webhook'
      const isMcp = conn.integration_type === 'mcp'

      return {
        id: `conn-${conn.id}-${i}`,
        source: conn.from_node,
        target: conn.to_node,
        label: conn.data_flow,
        type: ConnectionLineType.SmoothStep,
        animated: isMcp,
        style: {
          stroke: isMcp ? '#6366f1' : '#94a3b8',
          strokeWidth: 1.5,
          strokeDasharray: isWebhook ? '5 5' : isApi ? undefined : undefined,
        },
        labelStyle: { fontSize: 9, fill: '#6b7280' },
        markerEnd: { type: MarkerType.ArrowClosed, width: 12, height: 12, color: isMcp ? '#6366f1' : '#94a3b8' },
      }
    }),
    // Automation -> output edges
    ...architecture.automations.map((auto, i) => ({
      id: `auto-out-${auto.id}-${i}`,
      source: auto.id,
      target: `output-${auto.id}-${i}`,
      type: ConnectionLineType.SmoothStep,
      animated: false,
      style: { stroke: '#94a3b8', strokeWidth: 1.5 },
      markerEnd: { type: MarkerType.ArrowClosed, width: 12, height: 12, color: '#94a3b8' },
    })),
  ]

  return { nodes, edges }
}

export default function SystemArchitectureDiagram({ architecture }: SystemArchitectureDiagramProps) {
  const { nodes, edges } = useMemo(() => buildDiagram(architecture), [architecture])

  const proOptions = useMemo(() => ({ hideAttribution: true }), [])
  const onInit = useCallback((instance: { fitView: () => void }) => {
    setTimeout(() => instance.fitView(), 50)
  }, [])

  if (!nodes.length) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 overflow-hidden"
    >
      <div className="px-3 py-2 border-b border-gray-200 dark:border-gray-700">
        <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
          Your AIOS Blueprint
        </p>
      </div>
      <div style={{ height: 500 }}>
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
      <div className="px-3 pb-2">
        <FlowLegend />
      </div>
    </motion.div>
  )
}
