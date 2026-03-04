import { useState } from 'react'
import { motion } from 'framer-motion'
import { logger } from '../../utils/logger'
import { API_BASE } from '../../services/apiClient'
import { industryTestData, MODEL_STRATEGIES, TEST_COMPANIES } from './devTestData'

interface DevModeTestGeneratorProps {
  navigate: (path: string) => void
}

function DevModeTestGenerator({ navigate }: DevModeTestGeneratorProps) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [currentStep, setCurrentStep] = useState('')
  const [selectedCompany, setSelectedCompany] = useState<typeof TEST_COMPANIES[number] | null>(null)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)

  // Dev config options
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [selectedStrategy, setSelectedStrategy] = useState<string>('anthropic_quick')
  const [selectedTier, setSelectedTier] = useState<'quick' | 'full'>('quick')
  const [companyIndex, setCompanyIndex] = useState<number>(-1) // -1 = random

  const testCompanies = TEST_COMPANIES

  const steps = [
    { label: 'Creating session', icon: '\uD83D\uDCDD' },
    { label: 'Loading knowledge base', icon: '\uD83D\uDCDA' },
    { label: 'Analyzing business context', icon: '\uD83D\uDD0D' },
    { label: 'Generating findings', icon: '\uD83D\uDCA1' },
    { label: 'Building recommendations', icon: '\uD83C\uDFAF' },
    { label: 'Calculating ROI', icon: '\uD83D\uDCCA' },
    { label: 'Finalizing report', icon: '\u2728' },
  ]

  async function generateTestReport() {
    setIsGenerating(true)
    setError(null)
    setProgress(0)

    // Use selected company or random
    const testCompany = companyIndex >= 0
      ? testCompanies[companyIndex]
      : testCompanies[Math.floor(Math.random() * testCompanies.length)]
    setSelectedCompany(testCompany)

    // Get subtype-specific test data
    const industryData = industryTestData[testCompany.subtype]
    if (!industryData) {
      setError(`No test data configured for subtype: ${testCompany.subtype}`)
      setIsGenerating(false)
      return
    }

    const mockProfile = {
      basics: {
        name: { value: testCompany.name },
        description: { value: industryData.description },
        website: { value: testCompany.website }
      },
      industry: {
        primary_industry: { value: testCompany.industry },
        business_model: { value: industryData.businessModel }
      },
      size: {
        employee_range: { value: industryData.employeeRange },
        employee_count: { value: industryData.employeeCount },
        annual_revenue: { value: industryData.annualRevenue }
      },
      tech_stack: {
        technologies_detected: industryData.techStack.map(t => ({ value: t }))
      }
    }

    // Use full quiz answers if available, fall back to basic fields
    const mockAnswers = {
      ...industryData.quizAnswers,
      // Always include interview responses for report context
      interview_responses: industryData.interview
        .filter(m => m.role === 'user')
        .map(m => m.content),
      // Include workshop deep-dive transcripts if available
      ...(industryData.workshopDeepDives ? {
        workshop_deep_dives: industryData.workshopDeepDives.map(dd => ({
          pain_point: dd.painPoint,
          transcript: dd.conversation,
        })),
      } : {}),
    }

    // Full interview messages with assistant questions interspersed
    const mockInterview = industryData.interview

    try {
      // Use streaming endpoint for real-time progress updates
      const response = await fetch(`${API_BASE}/api/quiz/dev/generate-test-report/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_profile: mockProfile,
          quiz_answers: mockAnswers,
          interview_messages: mockInterview,
          confidence_scores: industryData.confidenceScores,
          tier: selectedTier,
          model_strategy: selectedStrategy,
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData?.detail || errorData?.error?.message || `Failed: ${response.statusText}`)
      }

      // Read the stream for real-time progress updates
      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response stream available')
      }

      const decoder = new TextDecoder()
      let buffer = ''
      let reportId: string | null = null

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // Process SSE events in the buffer
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              // Update progress from real backend events
              if (data.progress !== undefined) {
                setProgress(data.progress)
              }
              if (data.step) {
                setCurrentStep(data.step)
              }

              // Check for completion
              if (data.report_id) {
                reportId = data.report_id
              }

              // Check for errors
              if (data.phase === 'error') {
                throw new Error(data.error || data.step || 'Report generation failed')
              }

              // Navigate on completion
              if ((data.phase === 'done' || data.phase === 'complete') && reportId) {
                setProgress(100)
                setCurrentStep('Report ready!')
                await new Promise(r => setTimeout(r, 500))
                navigate(`/report/${reportId}?dev=true`)
                return
              }
            } catch (parseErr) {
              // Only log if it's not a JSON parse error for empty/malformed data
              if (line.trim() !== 'data: ') {
                logger.warn('Failed to parse SSE event:', line, parseErr)
              }
            }
          }
        }
      }

      // If we got here without navigating, check if we have a report_id
      if (reportId) {
        setProgress(100)
        setCurrentStep('Report ready!')
        await new Promise(r => setTimeout(r, 500))
        navigate(`/report/${reportId}?dev=true`)
      } else {
        throw new Error('Report generation completed but no report ID received')
      }
    } catch (err: any) {
      logger.error('Failed to generate test report:', err)
      setError(err.message || 'Failed to generate report')
      setIsGenerating(false)
    }
  }

  if (isGenerating) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mt-8 p-6 bg-gradient-to-br from-yellow-50 to-orange-50 border-2 border-yellow-300 rounded-2xl"
      >
        <div className="text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-yellow-200 text-yellow-800 rounded-full text-xs font-medium mb-4">
            <span className="animate-pulse">{'\u25CF'}</span> DEV MODE
          </div>

          {selectedCompany && (
            <div className="mb-4">
              <h3 className="text-lg font-bold text-gray-900">{selectedCompany.name}</h3>
              <p className="text-sm text-gray-500 capitalize">{selectedCompany.subtype.replace('ecommerce-', 'E-commerce: ')}</p>
            </div>
          )}

          {/* Progress bar */}
          <div className="w-full bg-gray-200 rounded-full h-3 mb-4 overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>

          {/* Current step */}
          <div className="flex items-center justify-center gap-2 text-gray-700">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              className="w-5 h-5 border-2 border-yellow-500 border-t-transparent rounded-full"
            />
            <span className="font-medium">{currentStep || 'Starting...'}</span>
          </div>

          {/* Steps list */}
          <div className="mt-6 grid grid-cols-2 gap-2 text-left">
            {steps.map((step, i) => {
              const stepProgress = (progress / 100) * steps.length
              const isComplete = i < stepProgress
              const isCurrent = i === Math.floor(stepProgress)
              return (
                <div
                  key={step.label}
                  className={`flex items-center gap-2 text-xs py-1 px-2 rounded ${
                    isComplete ? 'text-green-700 bg-green-50' :
                    isCurrent ? 'text-yellow-700 bg-yellow-100 font-medium' :
                    'text-gray-400'
                  }`}
                >
                  <span>{isComplete ? '\u2713' : step.icon}</span>
                  <span>{step.label}</span>
                </div>
              )
            })}
          </div>

          {error && (
            <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-lg text-sm">
              {error}
              <button
                onClick={() => { setError(null); setIsGenerating(false) }}
                className="block mt-2 text-red-800 underline text-xs"
              >
                Try again
              </button>
            </div>
          )}
        </div>
      </motion.div>
    )
  }

  return (
    <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-xl">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs text-yellow-800 font-medium">{'\uD83D\uDEE0\uFE0F'} DEV MODE</p>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-xs text-yellow-600 hover:text-yellow-800 underline"
        >
          {showAdvanced ? 'Hide options' : 'Show options'}
        </button>
      </div>

      {showAdvanced && (
        <div className="mb-4 space-y-3 p-3 bg-white/50 rounded-lg border border-yellow-200">
          {/* Model Strategy Selector */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Model Strategy
            </label>
            <select
              value={selectedStrategy}
              onChange={(e) => setSelectedStrategy(e.target.value)}
              className="w-full text-sm border border-gray-300 rounded-md px-2 py-1.5 bg-white focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500"
            >
              {MODEL_STRATEGIES.map((strategy) => (
                <option key={strategy.id} value={strategy.id}>
                  {strategy.label}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              {MODEL_STRATEGIES.find(s => s.id === selectedStrategy)?.description}
            </p>
          </div>

          {/* Tier Selector */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Report Tier
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setSelectedTier('quick')}
                className={`flex-1 py-1.5 px-3 text-xs font-medium rounded-md border transition ${
                  selectedTier === 'quick'
                    ? 'bg-yellow-500 text-white border-yellow-500'
                    : 'bg-white text-gray-700 border-gray-300 hover:border-yellow-400'
                }`}
              >
                Quick (10-15 findings)
              </button>
              <button
                onClick={() => setSelectedTier('full')}
                className={`flex-1 py-1.5 px-3 text-xs font-medium rounded-md border transition ${
                  selectedTier === 'full'
                    ? 'bg-yellow-500 text-white border-yellow-500'
                    : 'bg-white text-gray-700 border-gray-300 hover:border-yellow-400'
                }`}
              >
                Full (25-50 findings)
              </button>
            </div>
          </div>

          {/* Company Selector */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Test Company
            </label>
            <select
              value={companyIndex}
              onChange={(e) => setCompanyIndex(Number(e.target.value))}
              className="w-full text-sm border border-gray-300 rounded-md px-2 py-1.5 bg-white focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500"
            >
              <option value={-1}>{'\uD83C\uDFB2'} Random</option>
              {testCompanies.map((company, idx) => (
                <option key={company.name} value={idx}>
                  {company.name} ({company.subtype.replace('ecommerce-', '')})
                </option>
              ))}
            </select>
          </div>

          {/* Config Summary */}
          <div className="text-xs text-gray-600 bg-gray-100 rounded p-2">
            <strong>Config:</strong> {MODEL_STRATEGIES.find(s => s.id === selectedStrategy)?.label} {'\u2022'} {selectedTier} tier {'\u2022'} {companyIndex >= 0 ? testCompanies[companyIndex].name : 'Random company'}
          </div>
        </div>
      )}

      <button
        onClick={generateTestReport}
        className="w-full py-2 bg-yellow-500 text-white font-medium rounded-lg hover:bg-yellow-600 text-sm transition"
      >
        Generate Test Report
      </button>
      <p className="text-xs text-yellow-600 mt-2 text-center">
        Creates a real report with mock data for testing
      </p>
    </div>
  )
}

export default DevModeTestGenerator
