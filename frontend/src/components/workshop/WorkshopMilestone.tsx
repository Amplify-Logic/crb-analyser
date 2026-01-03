/**
 * WorkshopMilestone - Milestone summary display
 *
 * Shows the synthesized finding, ROI calculation, and vendor recommendations
 * after completing a deep-dive conversation.
 * User can provide feedback before moving to next pain point.
 */

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8383'

// =============================================================================
// Types
// =============================================================================

interface Finding {
  title: string
  summary: string
  currentProcess: string
  painSeverity: 'low' | 'medium' | 'high'
  recommendation: string
}

interface ROI {
  hoursPerWeek: number
  hourlyRate: number
  annualCost: number
  potentialSavings: number
  savingsPercentage: number
  calculationNotes: string
}

interface Vendor {
  name: string
  fit: 'high' | 'medium' | 'low'
  reason: string
}

interface MilestoneData {
  finding: Finding
  roi: ROI
  vendors: Vendor[]
  confidence: number
  dataGaps: string[]
}

interface WorkshopMilestoneProps {
  sessionId: string
  painPointId: string
  painPointLabel: string
  isLastPainPoint: boolean
  onContinue: () => void
  onEdit?: () => void
}

// =============================================================================
// Component
// =============================================================================

export default function WorkshopMilestone({
  sessionId,
  painPointId,
  painPointLabel,
  isLastPainPoint,
  onContinue,
  onEdit,
}: WorkshopMilestoneProps) {
  const [milestone, setMilestone] = useState<MilestoneData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<'looks_good' | 'needs_edit' | null>(null)
  const [notes, setNotes] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Fetch milestone data
  useEffect(() => {
    const fetchMilestone = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const response = await fetch(`${API_BASE_URL}/api/workshop/milestone`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sessionId,
            pain_point_id: painPointId,
          }),
        })

        if (!response.ok) throw new Error('Failed to generate milestone')

        const data = await response.json()

        // Transform snake_case to camelCase
        setMilestone({
          finding: {
            title: data.finding?.title || 'Finding',
            summary: data.finding?.summary || '',
            currentProcess: data.finding?.current_process || '',
            painSeverity: data.finding?.pain_severity || 'medium',
            recommendation: data.finding?.recommendation || '',
          },
          roi: {
            hoursPerWeek: data.roi?.hours_per_week || 0,
            hourlyRate: data.roi?.hourly_rate || 75,
            annualCost: data.roi?.annual_cost || 0,
            potentialSavings: data.roi?.potential_savings || 0,
            savingsPercentage: data.roi?.savings_percentage || 0,
            calculationNotes: data.roi?.calculation_notes || '',
          },
          vendors: (data.vendors || []).map((v: any) => ({
            name: v.name,
            fit: v.fit,
            reason: v.reason,
          })),
          confidence: data.confidence || 0.5,
          dataGaps: data.data_gaps || [],
        })
      } catch (err) {
        console.error('Milestone error:', err)
        setError('Failed to generate summary. Please try again.')
      } finally {
        setIsLoading(false)
      }
    }

    fetchMilestone()
  }, [sessionId, painPointId])

  // Submit feedback and continue
  const handleContinue = async () => {
    if (!feedback) return

    setIsSubmitting(true)

    try {
      await fetch(`${API_BASE_URL}/api/workshop/milestone/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          pain_point_id: painPointId,
          feedback,
          notes: notes || null,
        }),
      })

      onContinue()
    } catch (err) {
      console.error('Feedback error:', err)
      // Continue anyway
      onContinue()
    } finally {
      setIsSubmitting(false)
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(amount)
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'text-red-600 bg-red-50'
      case 'medium': return 'text-yellow-600 bg-yellow-50'
      default: return 'text-green-600 bg-green-50'
    }
  }

  const getFitColor = (fit: string) => {
    switch (fit) {
      case 'high': return 'text-green-600 bg-green-50 border-green-200'
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
            className="w-16 h-16 border-4 border-primary-600 border-t-transparent rounded-full mx-auto mb-6"
          />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Analyzing your responses...
          </h2>
          <p className="text-gray-600">
            Creating a draft finding for {painPointLabel}
          </p>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">{error}</h2>
          <button
            onClick={() => window.location.reload()}
            className="text-primary-600 hover:text-primary-700"
          >
            Try again
          </button>
        </div>
      </div>
    )
  }

  if (!milestone) return null

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white pb-32">
      {/* Header */}
      <div className="bg-white border-b border-gray-100">
        <div className="max-w-3xl mx-auto px-4 py-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                Deep-Dive Complete
              </h1>
              <p className="text-sm text-gray-500">
                Here's what we found about {painPointLabel}
              </p>
            </div>
          </div>

          {/* Confidence indicator */}
          <div className="flex items-center gap-2 mt-4">
            <span className="text-sm text-gray-500">Analysis confidence:</span>
            <div className="flex-1 h-2 bg-gray-200 rounded-full max-w-xs">
              <div
                className="h-full bg-primary-500 rounded-full transition-all"
                style={{ width: `${milestone.confidence * 100}%` }}
              />
            </div>
            <span className="text-sm font-medium text-gray-700">
              {Math.round(milestone.confidence * 100)}%
            </span>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        {/* Finding Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden"
        >
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 className="font-semibold text-gray-900">Draft Finding</h3>
            <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(milestone.finding.painSeverity)}`}>
              {milestone.finding.painSeverity} impact
            </span>
          </div>
          <div className="px-6 py-5">
            <h4 className="text-lg font-semibold text-gray-900 mb-3">
              {milestone.finding.title}
            </h4>
            <p className="text-gray-700 mb-4">{milestone.finding.summary}</p>

            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <h5 className="text-sm font-medium text-gray-500 mb-2">Current Process</h5>
              <p className="text-gray-700">{milestone.finding.currentProcess}</p>
            </div>

            <div className="bg-primary-50 rounded-lg p-4">
              <h5 className="text-sm font-medium text-primary-600 mb-2">Recommendation</h5>
              <p className="text-gray-700">{milestone.finding.recommendation}</p>
            </div>
          </div>
        </motion.div>

        {/* ROI Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden"
        >
          <div className="px-6 py-4 border-b border-gray-100">
            <h3 className="font-semibold text-gray-900">Estimated ROI</h3>
          </div>
          <div className="px-6 py-5">
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-gray-50 rounded-xl p-4">
                <p className="text-sm text-gray-500 mb-1">Current Annual Cost</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(milestone.roi.annualCost)}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {milestone.roi.hoursPerWeek}h/week × {formatCurrency(milestone.roi.hourlyRate)}/hr × 52 weeks
                </p>
              </div>
              <div className="bg-green-50 rounded-xl p-4">
                <p className="text-sm text-green-600 mb-1">Potential Savings</p>
                <p className="text-2xl font-bold text-green-600">
                  {formatCurrency(milestone.roi.potentialSavings)}
                </p>
                <p className="text-xs text-green-500 mt-1">
                  {milestone.roi.savingsPercentage}% reduction
                </p>
              </div>
            </div>

            <p className="text-sm text-gray-500 italic">
              {milestone.roi.calculationNotes}
            </p>
          </div>
        </motion.div>

        {/* Vendors Card */}
        {milestone.vendors.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden"
          >
            <div className="px-6 py-4 border-b border-gray-100">
              <h3 className="font-semibold text-gray-900">Recommended Solutions</h3>
            </div>
            <div className="px-6 py-5 space-y-3">
              {milestone.vendors.map((vendor, i) => (
                <div
                  key={i}
                  className={`rounded-lg border p-4 ${getFitColor(vendor.fit)}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{vendor.name}</span>
                    <span className="text-xs font-medium uppercase">
                      {vendor.fit} fit
                    </span>
                  </div>
                  <p className="text-sm opacity-80">{vendor.reason}</p>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Data Gaps */}
        {milestone.dataGaps.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-yellow-50 rounded-xl p-4 border border-yellow-200"
          >
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-yellow-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <p className="text-sm font-medium text-yellow-800 mb-1">
                  Additional info would improve this estimate:
                </p>
                <ul className="text-sm text-yellow-700 list-disc list-inside">
                  {milestone.dataGaps.map((gap, i) => (
                    <li key={i}>{gap}</li>
                  ))}
                </ul>
              </div>
            </div>
          </motion.div>
        )}

        {/* Feedback Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden"
        >
          <div className="px-6 py-4 border-b border-gray-100">
            <h3 className="font-semibold text-gray-900">Does this look right?</h3>
          </div>
          <div className="px-6 py-5">
            <div className="flex gap-3 mb-4">
              <button
                onClick={() => setFeedback('looks_good')}
                className={`flex-1 px-4 py-3 rounded-xl font-medium transition ${
                  feedback === 'looks_good'
                    ? 'bg-green-100 text-green-700 ring-2 ring-green-500'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Yes, looks good
              </button>
              <button
                onClick={() => setFeedback('needs_edit')}
                className={`flex-1 px-4 py-3 rounded-xl font-medium transition ${
                  feedback === 'needs_edit'
                    ? 'bg-yellow-100 text-yellow-700 ring-2 ring-yellow-500'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Needs adjustments
              </button>
            </div>

            {feedback === 'needs_edit' && (
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="What should we adjust? (optional)"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl resize-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                rows={3}
              />
            )}
          </div>
        </motion.div>
      </div>

      {/* Footer */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4">
        <div className="max-w-3xl mx-auto flex justify-between items-center">
          {onEdit && (
            <button
              onClick={onEdit}
              className="text-gray-500 hover:text-gray-700"
            >
              Go back
            </button>
          )}
          <div className="flex-1" />
          <button
            onClick={handleContinue}
            disabled={!feedback || isSubmitting}
            className={`px-6 py-3 rounded-xl font-medium transition ${
              feedback && !isSubmitting
                ? 'bg-primary-600 text-white hover:bg-primary-700'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
          >
            {isSubmitting
              ? 'Saving...'
              : isLastPainPoint
              ? 'Finish Workshop'
              : 'Continue to Next Topic'
            }
          </button>
        </div>
      </div>
    </div>
  )
}
