// frontend/src/components/report/StackTab.tsx
import { useState } from 'react'
import { motion } from 'framer-motion'

interface NodeCRB {
  cost: string
  risk: string
  risk_level: 'low' | 'medium' | 'high'
  benefit: string
  powers: string[]
}

interface ToolNode {
  id: string
  name: string
  category: string
  monthly_cost: number
  one_time_cost: number
  crb: NodeCRB
  is_existing: boolean
}

interface Connection {
  id: string
  from_node: string
  to_node: string
  data_flow: string
  integration_type: string
}

interface AutomationNode {
  id: string
  name: string
  trigger: string
  action: string
  tools_used: string[]
}

interface CostItem {
  name: string
  monthly_cost: number
  one_time_cost: number
}

interface CostBreakdown {
  items: CostItem[]
  total_monthly: number
  total_one_time: number
}

interface CostComparison {
  saas_route: CostBreakdown
  diy_route: CostBreakdown
  monthly_savings: number
  savings_percentage: number
  build_cost: number
  breakeven_months: number
}

interface SystemArchitecture {
  existing_tools: ToolNode[]
  ai_layer: ToolNode[]
  automations: AutomationNode[]
  connections: Connection[]
  cost_comparison: CostComparison
}

interface StackTabProps {
  architecture: SystemArchitecture
}

export default function StackTab({ architecture }: StackTabProps) {
  const [viewMode, setViewMode] = useState<'saas' | 'diy'>('diy')
  const [selectedNode, setSelectedNode] = useState<ToolNode | null>(null)

  if (!architecture) {
    return (
      <div className="bg-white rounded-2xl p-8 text-center">
        <p className="text-gray-500">System architecture not available.</p>
      </div>
    )
  }

  const { existing_tools, ai_layer, automations, cost_comparison } = architecture

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0
    }).format(value)
  }

  const riskColor = {
    low: 'text-green-600 bg-green-100',
    medium: 'text-yellow-600 bg-yellow-100',
    high: 'text-red-600 bg-red-100',
  }

  return (
    <div className="space-y-6">
      {/* Toggle */}
      <div className="flex justify-center">
        <div className="bg-gray-100 p-1 rounded-xl inline-flex">
          <button
            onClick={() => setViewMode('diy')}
            className={`px-6 py-2 rounded-lg font-medium transition ${
              viewMode === 'diy'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            DIY Route: {formatCurrency(cost_comparison.diy_route.total_monthly)}/mo
          </button>
          <button
            onClick={() => setViewMode('saas')}
            className={`px-6 py-2 rounded-lg font-medium transition ${
              viewMode === 'saas'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            SaaS Route: {formatCurrency(cost_comparison.saas_route.total_monthly)}/mo
          </button>
        </div>
      </div>

      {/* Architecture Diagram */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-white rounded-2xl p-6 shadow-sm"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-6 text-center">
          Your AI-Powered Business System
        </h3>

        <div className="grid grid-cols-3 gap-8">
          {/* Existing Tools Column */}
          <div>
            <h4 className="text-sm font-medium text-gray-500 mb-4 text-center">YOUR TOOLS</h4>
            <div className="space-y-3">
              {existing_tools.map((tool) => (
                <motion.div
                  key={tool.id}
                  whileHover={{ scale: 1.02 }}
                  onClick={() => setSelectedNode(tool)}
                  className="p-4 bg-gray-50 rounded-xl border-2 border-gray-200 cursor-pointer hover:border-primary-300 transition"
                >
                  <p className="font-medium text-gray-900">{tool.name}</p>
                  <p className="text-xs text-gray-500">Already owned</p>
                </motion.div>
              ))}
            </div>
          </div>

          {/* AI Layer Column */}
          <div>
            <h4 className="text-sm font-medium text-gray-500 mb-4 text-center">AI BRAIN</h4>
            <div className="space-y-3">
              {ai_layer.map((tool) => (
                <motion.div
                  key={tool.id}
                  whileHover={{ scale: 1.02 }}
                  onClick={() => setSelectedNode(tool)}
                  className="p-4 bg-purple-50 rounded-xl border-2 border-purple-200 cursor-pointer hover:border-purple-400 transition"
                >
                  <p className="font-medium text-purple-900">{tool.name}</p>
                  <p className="text-sm text-purple-600 font-medium">
                    {formatCurrency(tool.monthly_cost)}/mo
                  </p>
                </motion.div>
              ))}

              {/* Connection arrows */}
              <div className="flex justify-center py-2">
                <svg className="w-8 h-8 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
              </div>
            </div>
          </div>

          {/* Automations Column */}
          <div>
            <h4 className="text-sm font-medium text-gray-500 mb-4 text-center">AUTOMATIONS</h4>
            <div className="space-y-3">
              {automations.slice(0, 4).map((auto) => (
                <div
                  key={auto.id}
                  className="p-4 bg-green-50 rounded-xl border-2 border-green-200"
                >
                  <p className="font-medium text-green-900 text-sm">{auto.name}</p>
                  <p className="text-xs text-green-600 mt-1">{auto.trigger}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Selected Node Detail */}
      {selectedNode && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl p-6 shadow-sm"
        >
          <div className="flex items-start justify-between mb-4">
            <h4 className="text-lg font-semibold text-gray-900">{selectedNode.name}</h4>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 bg-gray-50 rounded-xl">
              <p className="text-xs text-gray-500 mb-1">COST</p>
              <p className="font-medium text-gray-900">{selectedNode.crb.cost}</p>
            </div>
            <div className={`p-4 rounded-xl ${riskColor[selectedNode.crb.risk_level]}`}>
              <p className="text-xs opacity-75 mb-1">RISK</p>
              <p className="font-medium">{selectedNode.crb.risk}</p>
            </div>
            <div className="p-4 bg-green-50 rounded-xl">
              <p className="text-xs text-green-600 mb-1">BENEFIT</p>
              <p className="font-medium text-green-800">{selectedNode.crb.benefit}</p>
            </div>
          </div>

          {selectedNode.crb.powers.length > 0 && (
            <div className="mt-4">
              <p className="text-sm text-gray-500 mb-2">Powers these automations:</p>
              <div className="flex flex-wrap gap-2">
                {selectedNode.crb.powers.map((power, i) => (
                  <span key={i} className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">
                    {power}
                  </span>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* Cost Comparison */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-2xl p-6 shadow-sm"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Cost Comparison</h3>

        <div className="grid grid-cols-3 gap-6">
          <div className="p-4 bg-gray-50 rounded-xl">
            <p className="text-sm text-gray-500 mb-1">SaaS Stack</p>
            <p className="text-2xl font-bold text-gray-900">
              {formatCurrency(cost_comparison.saas_route.total_monthly)}
              <span className="text-sm font-normal text-gray-500">/mo</span>
            </p>
            <div className="mt-3 space-y-1">
              {cost_comparison.saas_route.items.map((item, i) => (
                <div key={i} className="flex justify-between text-sm">
                  <span className="text-gray-600">{item.name}</span>
                  <span className="text-gray-900">{formatCurrency(item.monthly_cost)}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="p-4 bg-primary-50 rounded-xl border-2 border-primary-200">
            <p className="text-sm text-primary-600 mb-1">DIY Stack</p>
            <p className="text-2xl font-bold text-primary-700">
              {formatCurrency(cost_comparison.diy_route.total_monthly)}
              <span className="text-sm font-normal text-primary-500">/mo</span>
            </p>
            <p className="text-sm text-primary-600 mt-1">
              + {formatCurrency(cost_comparison.build_cost)} build cost
            </p>
            <div className="mt-3 space-y-1">
              {cost_comparison.diy_route.items.map((item, i) => (
                <div key={i} className="flex justify-between text-sm">
                  <span className="text-gray-600">{item.name}</span>
                  <span className="text-gray-900">{formatCurrency(item.monthly_cost)}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="p-4 bg-green-50 rounded-xl">
            <p className="text-sm text-green-600 mb-1">You Save</p>
            <p className="text-2xl font-bold text-green-700">
              {formatCurrency(cost_comparison.monthly_savings)}
              <span className="text-sm font-normal text-green-500">/mo</span>
            </p>
            <p className="text-lg font-bold text-green-600 mt-1">
              ({Math.round(cost_comparison.savings_percentage)}%)
            </p>
            <p className="text-sm text-green-600 mt-2">
              Breakeven: {cost_comparison.breakeven_months} months
            </p>
          </div>
        </div>
      </motion.div>

      {/* Actions */}
      <div className="flex gap-4">
        <button className="flex-1 px-6 py-3 bg-white border border-gray-200 rounded-xl font-medium text-gray-700 hover:bg-gray-50 transition flex items-center justify-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Download Architecture PDF
        </button>
        <button className="flex-1 px-6 py-3 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition flex items-center justify-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
          </svg>
          Share with Developer
        </button>
      </div>
    </div>
  )
}
