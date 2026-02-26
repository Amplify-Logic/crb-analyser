// frontend/src/components/report/ROICalculator.tsx
import { useState, useMemo, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'

interface ROIInputs {
  hoursWeekly: number
  hourlyRate: number
  automationRate: number
  implementationApproach: 'diy' | 'saas' | 'custom'
}

interface ROIResults {
  hoursSavedWeekly: number
  hoursSavedMonthly: number
  hoursSavedYearly: number
  implementationCost: number
  monthlyCost: number
  monthlySavings: number
  yearlySavings: number
  roiPercentage: number
  breakevenMonths: number
  threeYearNet: number
}

interface SavedScenario {
  id: string
  name: string
  inputs: ROIInputs
  results: ROIResults
  createdAt: Date
}

// Actual recommendation structure from report
interface ReportRecommendation {
  id: string
  title: string
  priority: 'high' | 'medium' | 'low'
  roi_percentage: number
  payback_months: number
  crb_analysis: {
    cost: { short_term: any; mid_term: any; long_term: any; total: number }
    risk: { description: string; probability: string; impact: number; mitigation: string }[]
    benefit: { short_term: any; mid_term: any; long_term: any; total: number }
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  options: Record<string, any>
  our_recommendation: string
  assumptions: string[]
}

// Actual value summary structure from report
interface ReportValueSummary {
  value_saved?: { subtotal: { min: number; max: number }; hours_per_week?: number; hourly_rate?: number }
  value_created?: { subtotal: { min: number; max: number } }
  total: { min: number; max: number }
}

interface ROICalculatorProps {
  recommendations: ReportRecommendation[]
  valueSummary?: ReportValueSummary
  reportId?: string
  locale?: string // 'en-NZ', 'en-AU', 'de-DE', etc.
  currency?: string // 'NZD', 'AUD', 'EUR', etc.
  onSaveScenario?: (scenario: SavedScenario) => void
}

// Cost assumptions by approach - will be overridden by report data
const DEFAULT_APPROACH_COSTS = {
  diy: { implementation: 0, monthly: 50 },
  saas: { implementation: 500, monthly: 150 },
  custom: { implementation: 3000, monthly: 50 },
}

const APPROACH_LABELS = {
  diy: 'DIY Setup',
  saas: 'SaaS Tools (Recommended)',
  custom: 'Custom Build',
}

const APPROACH_RISK = {
  diy: { level: 'medium', bar: 0.5, display: 'Medium (learning curve)' },
  saas: { level: 'low', bar: 0.2, display: 'Low (proven solutions)' },
  custom: { level: 'high', bar: 0.7, display: 'Higher (maintenance burden)' },
}

export default function ROICalculator({
  recommendations,
  valueSummary,
  locale = 'en-NZ',
  currency = 'NZD',
  onSaveScenario,
}: ROICalculatorProps) {
  // Extract actual values from report data
  const reportDefaults = useMemo(() => {
    // Calculate total hours from value_saved
    const hoursPerWeek = valueSummary?.value_saved?.hours_per_week || 12
    const hourlyRate = valueSummary?.value_saved?.hourly_rate || 85

    // Calculate costs from recommendations
    const totalMonthlyCost = recommendations.reduce((sum, rec) => {
      const option = rec.options?.connect_and_automate || rec.options?.enhance_with_ai || rec.options?.best_in_class || rec.options?.off_the_shelf
      const cost = typeof option?.monthly_cost === 'number' ? option.monthly_cost : 0
      return sum + cost
    }, 0)

    const totalImplementationCost = recommendations.reduce((sum, rec) => {
      return sum + (rec.crb_analysis?.cost?.total || 0)
    }, 0)

    // Calculate benefits
    const totalAnnualBenefit = recommendations.reduce((sum, rec) => {
      return sum + (rec.crb_analysis?.benefit?.total || 0)
    }, 0)

    // Average ROI and payback from recommendations
    const avgRoi = recommendations.length > 0
      ? recommendations.reduce((sum, rec) => sum + (rec.roi_percentage || 0), 0) / recommendations.length
      : 300

    const avgPayback = recommendations.length > 0
      ? recommendations.reduce((sum, rec) => sum + (rec.payback_months || 0), 0) / recommendations.length
      : 3

    return {
      hoursPerWeek,
      hourlyRate,
      totalMonthlyCost,
      totalImplementationCost,
      totalAnnualBenefit,
      avgRoi: Math.round(avgRoi),
      avgPayback: Math.round(avgPayback * 10) / 10,
    }
  }, [recommendations, valueSummary])

  // Dynamic approach costs based on report data
  const approachCosts = useMemo(() => {
    const saasMonthly = recommendations.reduce((sum, rec) => {
      const option = rec.options?.enhance_with_ai || rec.options?.targeted_upgrade || rec.options?.best_in_class || rec.options?.off_the_shelf
      const cost = typeof option?.monthly_cost === 'number' ? option.monthly_cost : 0
      return sum + cost
    }, 0) || DEFAULT_APPROACH_COSTS.saas.monthly

    const saasImplementation = recommendations.reduce((sum, rec) => {
      const weeks = rec.options?.enhance_with_ai?.implementation_weeks || rec.options?.targeted_upgrade?.implementation_weeks || rec.options?.best_in_class?.implementation_weeks || rec.options?.off_the_shelf?.implementation_weeks || 2
      return sum + (weeks * 200) // Rough estimate: €200 per week of setup time
    }, 0) || DEFAULT_APPROACH_COSTS.saas.implementation

    const customMin = recommendations.reduce((sum, rec) => {
      return sum + (rec.options?.connect_and_automate?.estimated_cost?.min || rec.options?.custom_solution?.estimated_cost?.min || 0)
    }, 0) || DEFAULT_APPROACH_COSTS.custom.implementation

    return {
      diy: { implementation: 0, monthly: Math.round(saasMonthly * 0.5) },
      saas: { implementation: saasImplementation, monthly: saasMonthly },
      custom: { implementation: customMin, monthly: 50 },
    }
  }, [recommendations])

  const [inputs, setInputs] = useState<ROIInputs>({
    hoursWeekly: reportDefaults.hoursPerWeek,
    hourlyRate: reportDefaults.hourlyRate,
    automationRate: 0.7,
    implementationApproach: 'saas',
  })

  const [savedScenarios, setSavedScenarios] = useState<SavedScenario[]>([])
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [scenarioName, setScenarioName] = useState('')
  const [compareMode, setCompareMode] = useState(false)
  const [selectedScenarios, setSelectedScenarios] = useState<string[]>([])

  // Format currency based on locale
  const formatCurrency = useCallback((value: number): string => {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: currency,
      maximumFractionDigits: 0,
    }).format(value)
  }, [locale, currency])

  // Calculate results based on inputs
  const results = useMemo((): ROIResults => {
    const approach = approachCosts[inputs.implementationApproach]

    const hoursSavedWeekly = inputs.hoursWeekly * inputs.automationRate
    const hoursSavedMonthly = hoursSavedWeekly * 4.33
    const hoursSavedYearly = hoursSavedMonthly * 12

    const monthlySavings = hoursSavedMonthly * inputs.hourlyRate
    const yearlySavings = monthlySavings * 12

    const implementationCost = approach.implementation
    const monthlyCost = approach.monthly

    const netMonthlySavings = monthlySavings - monthlyCost
    const breakevenMonths = implementationCost > 0 && netMonthlySavings > 0
      ? implementationCost / netMonthlySavings
      : 0

    const threeYearNet = (yearlySavings - monthlyCost * 12) * 3 - implementationCost
    const roiPercentage = implementationCost > 0
      ? ((yearlySavings - monthlyCost * 12) / implementationCost) * 100
      : 999

    return {
      hoursSavedWeekly: Math.round(hoursSavedWeekly * 10) / 10,
      hoursSavedMonthly: Math.round(hoursSavedMonthly * 10) / 10,
      hoursSavedYearly: Math.round(hoursSavedYearly),
      implementationCost,
      monthlyCost,
      monthlySavings: Math.round(monthlySavings),
      yearlySavings: Math.round(yearlySavings),
      roiPercentage: Math.round(roiPercentage),
      breakevenMonths: Math.max(0, parseFloat(breakevenMonths.toFixed(1))),
      threeYearNet: Math.round(threeYearNet),
    }
  }, [inputs, approachCosts])

  // CRB summary for display
  const crbSummary = useMemo(() => {
    const approach = approachCosts[inputs.implementationApproach]
    const risk = APPROACH_RISK[inputs.implementationApproach]

    return {
      costDisplay: approach.implementation > 0
        ? `${formatCurrency(approach.monthly)}/mo + ${formatCurrency(approach.implementation)} setup`
        : `${formatCurrency(approach.monthly)}/mo`,
      riskDisplay: risk.display,
      riskBar: risk.bar,
      benefitDisplay: `${formatCurrency(results.monthlySavings)}/mo saved`,
      timeBenefit: `${results.hoursSavedWeekly.toFixed(1)} hrs/wk freed`,
    }
  }, [inputs.implementationApproach, results, approachCosts, formatCurrency])

  // Chart data for comparison
  const chartData = useMemo(() => {
    const currentData = {
      name: 'Current',
      value: results.yearlySavings - results.monthlyCost * 12,
    }

    if (!compareMode || selectedScenarios.length === 0) {
      return [currentData]
    }

    const scenarioData = savedScenarios
      .filter(s => selectedScenarios.includes(s.id))
      .map(s => ({
        name: s.name,
        value: s.results.yearlySavings - s.results.monthlyCost * 12,
      }))

    return [currentData, ...scenarioData]
  }, [results, compareMode, selectedScenarios, savedScenarios])

  // Handlers
  const handleInputChange = useCallback((field: keyof ROIInputs, value: number | string) => {
    setInputs(prev => ({ ...prev, [field]: value }))
  }, [])

  const handleSaveScenario = useCallback(() => {
    if (!scenarioName.trim()) return

    const newScenario: SavedScenario = {
      id: `scenario-${Date.now()}`,
      name: scenarioName.trim(),
      inputs: { ...inputs },
      results: { ...results },
      createdAt: new Date(),
    }

    setSavedScenarios(prev => [...prev, newScenario])
    onSaveScenario?.(newScenario)
    setShowSaveModal(false)
    setScenarioName('')
  }, [scenarioName, inputs, results, onSaveScenario])

  const handleDeleteScenario = useCallback((id: string) => {
    setSavedScenarios(prev => prev.filter(s => s.id !== id))
    setSelectedScenarios(prev => prev.filter(sid => sid !== id))
  }, [])

  const handleLoadScenario = useCallback((scenario: SavedScenario) => {
    setInputs(scenario.inputs)
  }, [])

  const toggleScenarioComparison = useCallback((id: string) => {
    setSelectedScenarios(prev =>
      prev.includes(id)
        ? prev.filter(sid => sid !== id)
        : [...prev, id]
    )
  }, [])

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl p-6 shadow-sm"
      >
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Interactive ROI Calculator
            </h3>
            <p className="text-sm text-gray-500">
              Adjust the sliders to see how different scenarios affect your ROI
            </p>
          </div>
          <div className="flex gap-2">
            {savedScenarios.length > 0 && (
              <button
                onClick={() => setCompareMode(!compareMode)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition ${
                  compareMode
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {compareMode ? 'Exit Compare' : 'Compare Scenarios'}
              </button>
            )}
            <button
              onClick={() => setShowSaveModal(true)}
              className="px-4 py-2 bg-primary-600 text-white rounded-xl text-sm font-medium hover:bg-primary-700 transition"
            >
              Save Scenario
            </button>
          </div>
        </div>

        {/* CRB Summary Cards */}
        <div className="grid grid-cols-3 gap-4">
          <div className="p-4 bg-gray-50 rounded-xl">
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Cost</p>
            <p className="text-lg font-semibold text-gray-900">{crbSummary.costDisplay}</p>
          </div>
          <div className="p-4 bg-yellow-50 rounded-xl">
            <p className="text-xs text-yellow-600 uppercase tracking-wide mb-1">Risk</p>
            <p className="text-lg font-semibold text-yellow-800">{crbSummary.riskDisplay}</p>
            <div className="mt-2 h-2 bg-yellow-200 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${crbSummary.riskBar * 100}%` }}
                className="h-full bg-yellow-500 rounded-full"
              />
            </div>
          </div>
          <div className="p-4 bg-green-50 rounded-xl">
            <p className="text-xs text-green-600 uppercase tracking-wide mb-1">Benefit</p>
            <p className="text-lg font-semibold text-green-800">{crbSummary.benefitDisplay}</p>
            <p className="text-sm text-green-600">{crbSummary.timeBenefit}</p>
          </div>
        </div>
      </motion.div>

      {/* Sliders */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white rounded-2xl p-6 shadow-sm"
      >
        <h4 className="text-md font-semibold text-gray-900 mb-6">Adjust Your Inputs</h4>

        <div className="space-y-8">
          {/* Hours per week slider */}
          <div>
            <div className="flex justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">
                Hours Spent on Manual Tasks (Weekly)
              </label>
              <span className="text-sm font-bold text-primary-600">
                {inputs.hoursWeekly} hrs/week
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="40"
              step="1"
              value={inputs.hoursWeekly}
              onChange={(e) => handleInputChange('hoursWeekly', parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider-primary"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>1 hr</span>
              <span>20 hrs</span>
              <span>40 hrs</span>
            </div>
          </div>

          {/* Hourly rate slider */}
          <div>
            <div className="flex justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">
                Your Hourly Rate (or Value)
              </label>
              <span className="text-sm font-bold text-primary-600">
                {formatCurrency(inputs.hourlyRate)}/hr
              </span>
            </div>
            <input
              type="range"
              min="20"
              max="300"
              step="5"
              value={inputs.hourlyRate}
              onChange={(e) => handleInputChange('hourlyRate', parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider-primary"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>20</span>
              <span>100</span>
              <span>200</span>
              <span>300</span>
            </div>
          </div>

          {/* Automation rate slider */}
          <div>
            <div className="flex justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">
                Expected Automation Rate
              </label>
              <span className="text-sm font-bold text-primary-600">
                {Math.round(inputs.automationRate * 100)}%
              </span>
            </div>
            <input
              type="range"
              min="0.2"
              max="0.95"
              step="0.05"
              value={inputs.automationRate}
              onChange={(e) => handleInputChange('automationRate', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider-primary"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>20%</span>
              <span>50%</span>
              <span>70%</span>
              <span>95%</span>
            </div>
          </div>

          {/* Implementation approach selector */}
          <div>
            <label className="text-sm font-medium text-gray-700 mb-3 block">
              Implementation Approach
            </label>
            <div className="grid grid-cols-3 gap-3">
              {(Object.keys(APPROACH_LABELS) as Array<keyof typeof APPROACH_LABELS>).map((approach) => (
                <button
                  key={approach}
                  onClick={() => handleInputChange('implementationApproach', approach)}
                  className={`p-4 rounded-xl border-2 transition ${
                    inputs.implementationApproach === approach
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <p className={`font-medium ${
                    inputs.implementationApproach === approach
                      ? 'text-primary-700'
                      : 'text-gray-900'
                  }`}>
                    {APPROACH_LABELS[approach]}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {formatCurrency(approachCosts[approach].monthly)}/mo
                    {approachCosts[approach].implementation > 0 &&
                      ` + ${formatCurrency(approachCosts[approach].implementation)}`}
                  </p>
                </button>
              ))}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Results */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-2xl p-6 shadow-sm"
      >
        <h4 className="text-md font-semibold text-gray-900 mb-6">Your ROI Results</h4>

        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="p-4 bg-green-50 rounded-xl text-center">
            <p className="text-xs text-green-600 uppercase tracking-wide mb-1">Monthly Savings</p>
            <p className="text-2xl font-bold text-green-700">
              {formatCurrency(results.monthlySavings - results.monthlyCost)}
            </p>
            <p className="text-xs text-green-600">net of costs</p>
          </div>
          <div className="p-4 bg-blue-50 rounded-xl text-center">
            <p className="text-xs text-blue-600 uppercase tracking-wide mb-1">Yearly Savings</p>
            <p className="text-2xl font-bold text-blue-700">
              {formatCurrency(results.yearlySavings - results.monthlyCost * 12)}
            </p>
          </div>
          <div className="p-4 bg-purple-50 rounded-xl text-center">
            <p className="text-xs text-purple-600 uppercase tracking-wide mb-1">ROI</p>
            <p className="text-2xl font-bold text-purple-700">
              {results.roiPercentage > 999 ? '999+' : results.roiPercentage}%
            </p>
            <p className="text-xs text-purple-600">first year</p>
          </div>
          <div className="p-4 bg-orange-50 rounded-xl text-center">
            <p className="text-xs text-orange-600 uppercase tracking-wide mb-1">Breakeven</p>
            <p className="text-2xl font-bold text-orange-700">
              {results.breakevenMonths === 0 ? 'Immediate' : `${results.breakevenMonths} mo`}
            </p>
          </div>
        </div>

        {/* 3-Year Projection */}
        <div className="bg-gradient-to-r from-primary-50 to-green-50 rounded-xl p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">3-Year Net Value</p>
              <p className="text-3xl font-bold text-primary-700">
                {formatCurrency(results.threeYearNet)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600">Time Reclaimed</p>
              <p className="text-2xl font-bold text-green-700">
                {Math.round(results.hoursSavedYearly * 3)} hrs
              </p>
              <p className="text-xs text-green-600">over 3 years</p>
            </div>
          </div>
        </div>

        {/* Comparison Chart */}
        {chartData.length > 0 && (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => formatCurrency(value)}
                />
                <Tooltip
                  formatter={(value: number) => [formatCurrency(value), 'Net Yearly Value']}
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                />
                <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                  {chartData.map((_, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={index === 0 ? '#6366f1' : '#a5b4fc'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </motion.div>

      {/* Saved Scenarios */}
      {savedScenarios.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-2xl p-6 shadow-sm"
        >
          <h4 className="text-md font-semibold text-gray-900 mb-4">Saved Scenarios</h4>
          <div className="space-y-3">
            {savedScenarios.map((scenario) => (
              <div
                key={scenario.id}
                className={`p-4 rounded-xl border-2 transition ${
                  compareMode && selectedScenarios.includes(scenario.id)
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    {compareMode && (
                      <input
                        type="checkbox"
                        checked={selectedScenarios.includes(scenario.id)}
                        onChange={() => toggleScenarioComparison(scenario.id)}
                        className="w-5 h-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      />
                    )}
                    <div>
                      <p className="font-medium text-gray-900">{scenario.name}</p>
                      <p className="text-sm text-gray-500">
                        {scenario.inputs.hoursWeekly}hrs @ {formatCurrency(scenario.inputs.hourlyRate)}/hr •
                        {Math.round(scenario.inputs.automationRate * 100)}% automation •
                        {APPROACH_LABELS[scenario.inputs.implementationApproach]}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-lg font-bold text-green-600">
                        {formatCurrency(scenario.results.yearlySavings - scenario.results.monthlyCost * 12)}/yr
                      </p>
                      <p className="text-xs text-gray-500">
                        {scenario.results.roiPercentage}% ROI
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleLoadScenario(scenario)}
                        className="p-2 text-gray-400 hover:text-primary-600 transition"
                        title="Load scenario"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleDeleteScenario(scenario.id)}
                        className="p-2 text-gray-400 hover:text-red-600 transition"
                        title="Delete scenario"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Save Modal */}
      <AnimatePresence>
        {showSaveModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowSaveModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl"
              onClick={(e) => e.stopPropagation()}
            >
              <h4 className="text-lg font-semibold text-gray-900 mb-4">Save Scenario</h4>
              <input
                type="text"
                value={scenarioName}
                onChange={(e) => setScenarioName(e.target.value)}
                placeholder="e.g., Conservative Estimate"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent mb-4"
                autoFocus
              />
              <div className="flex gap-3">
                <button
                  onClick={() => setShowSaveModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-200 rounded-xl text-gray-600 hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveScenario}
                  disabled={!scenarioName.trim()}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Save
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Custom slider styles */}
      <style>{`
        .slider-primary::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: #6366f1;
          cursor: pointer;
          border: 3px solid white;
          box-shadow: 0 2px 6px rgba(99, 102, 241, 0.4);
        }
        .slider-primary::-moz-range-thumb {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: #6366f1;
          cursor: pointer;
          border: 3px solid white;
          box-shadow: 0 2px 6px rgba(99, 102, 241, 0.4);
        }
      `}</style>
    </div>
  )
}
