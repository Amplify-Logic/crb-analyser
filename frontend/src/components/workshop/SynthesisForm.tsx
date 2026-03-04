/**
 * SynthesisForm Component
 *
 * Phase 3: Rich report preview + final questions.
 * Shows what the report will contain, then collects last details.
 */

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { API_BASE } from '../../services/apiClient'

interface Finding {
  title: string
  savings: number
  badge: 'quick_win' | 'high_roi' | 'strategic'
  severity: string
  vendors: Array<{ name: string; slug?: string }>
}

interface Section {
  name: string
  confidence: number
  finding_count?: number
}

interface ReportPreview {
  company_name: string
  total_savings: number
  findings: Finding[]
  sections: Section[]
  duration_minutes: number | null
  pain_points_analyzed: number
}

interface SynthesisFormProps {
  sessionId: string
  onComplete: (answers: Record<string, any>) => Promise<void>
}

const badgeConfig = {
  quick_win: { label: 'Quick Win', bg: 'bg-green-100', text: 'text-green-700' },
  high_roi: { label: 'High ROI', bg: 'bg-blue-100', text: 'text-blue-700' },
  strategic: { label: 'Strategic', bg: 'bg-purple-100', text: 'text-purple-700' },
}

const staggerContainer = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.1 } },
}

const staggerItem = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
}

export default function SynthesisForm({ sessionId, onComplete }: SynthesisFormProps) {
  const [preview, setPreview] = useState<ReportPreview | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [stakeholders, setStakeholders] = useState('')
  const [timeline, setTimeline] = useState('')
  const [additions, setAdditions] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  useEffect(() => {
    const fetchPreview = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/workshop/preview/${sessionId}`)
        if (res.ok) {
          const data = await res.json()
          setPreview(data)
        }
      } catch {
        // Preview is enhancement — form still works without it
      } finally {
        setIsLoading(false)
      }
    }
    fetchPreview()
  }, [sessionId])

  const handleSubmit = async () => {
    setIsSubmitting(true)
    setSubmitError(null)
    try {
      await onComplete({
        stakeholders: stakeholders.split(',').map(s => s.trim()).filter(Boolean),
        timeline,
        additions: additions || null,
      })
    } catch (err: any) {
      setSubmitError(err?.message || 'Failed to submit workshop answers. Please retry.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const formatCurrency = (amount: number) =>
    new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(amount)

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="show"
      className="space-y-8"
    >
      {/* Hero: Total Savings */}
      {preview && !isLoading && (
        <motion.div
          variants={staggerItem}
          className="bg-gradient-to-br from-primary-600 to-primary-700 rounded-2xl p-8 text-white text-center"
        >
          <p className="text-primary-200 text-sm font-medium uppercase tracking-wider mb-2">
            Your analysis is ready
          </p>
          <p className="text-5xl font-bold mb-2">
            {formatCurrency(preview.total_savings)}
          </p>
          <p className="text-primary-200">
            estimated annual savings across {preview.pain_points_analyzed} areas
          </p>
        </motion.div>
      )}

      {/* Findings Grid */}
      {preview && preview.findings.length > 0 && (
        <motion.div variants={staggerItem} className="space-y-3">
          <h3 className="text-lg font-semibold text-gray-900">Key Findings</h3>
          <div className="grid gap-3">
            {preview.findings.map((finding, i) => {
              const badge = badgeConfig[finding.badge]
              return (
                <motion.div
                  key={i}
                  variants={staggerItem}
                  className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${badge.bg} ${badge.text}`}>
                          {badge.label}
                        </span>
                      </div>
                      <h4 className="font-medium text-gray-900">{finding.title}</h4>
                      {finding.vendors.length > 0 && (
                        <p className="text-xs text-gray-500 mt-1">
                          Recommended: {finding.vendors.map(v => v.name).join(', ')}
                        </p>
                      )}
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-lg font-bold text-green-600">
                        {formatCurrency(finding.savings)}
                      </p>
                      <p className="text-xs text-gray-500">/year</p>
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </div>
        </motion.div>
      )}

      {/* Report Sections with Confidence */}
      {preview && (
        <motion.div variants={staggerItem} className="space-y-3">
          <h3 className="text-lg font-semibold text-gray-900">Your Report Will Include</h3>
          <div className="bg-white rounded-xl border border-gray-100 divide-y divide-gray-50">
            {preview.sections.map((section, i) => (
              <div key={i} className="px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-primary-500" />
                  <span className="text-sm text-gray-900">{section.name}</span>
                  {section.finding_count !== undefined && (
                    <span className="text-xs text-gray-400">
                      ({section.finding_count} findings)
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-500 rounded-full transition-all duration-500"
                      style={{ width: `${section.confidence}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-400 w-8">{section.confidence}%</span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Workshop Stats */}
      {preview && (
        <motion.div variants={staggerItem} className="flex gap-4 text-center">
          <div className="flex-1 bg-gray-50 rounded-xl p-3">
            <p className="text-2xl font-bold text-gray-900">{preview.pain_points_analyzed}</p>
            <p className="text-xs text-gray-500">Areas Analyzed</p>
          </div>
          <div className="flex-1 bg-gray-50 rounded-xl p-3">
            <p className="text-2xl font-bold text-gray-900">{preview.findings.length}</p>
            <p className="text-xs text-gray-500">Findings</p>
          </div>
          {preview.duration_minutes && (
            <div className="flex-1 bg-gray-50 rounded-xl p-3">
              <p className="text-2xl font-bold text-gray-900">{preview.duration_minutes}</p>
              <p className="text-xs text-gray-500">Minutes</p>
            </div>
          )}
        </motion.div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="bg-white rounded-xl border border-gray-100 p-8 text-center">
          <p className="text-gray-500">Loading your analysis preview...</p>
        </div>
      )}

      {/* Divider */}
      <motion.div variants={staggerItem} className="border-t border-gray-200 pt-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">A few final details</h3>
      </motion.div>

      {/* Final Questions (kept from original, styled as cards) */}
      <motion.div variants={staggerItem} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <label className="block text-sm font-medium text-gray-900 mb-2">
          Who else needs to be involved in this decision?
        </label>
        <input
          type="text"
          value={stakeholders}
          onChange={(e) => setStakeholders(e.target.value)}
          placeholder="e.g., CEO, CFO, IT Manager (comma separated)"
          className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
      </motion.div>

      <motion.div variants={staggerItem} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <label className="block text-sm font-medium text-gray-900 mb-2">
          What's your ideal timeline for making changes?
        </label>
        <select
          value={timeline}
          onChange={(e) => setTimeline(e.target.value)}
          className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        >
          <option value="">Select timeline...</option>
          <option value="immediate">Immediately (next 30 days)</option>
          <option value="quarter">This quarter</option>
          <option value="half">Next 6 months</option>
          <option value="year">Within a year</option>
          <option value="exploring">Just exploring options</option>
        </select>
      </motion.div>

      <motion.div variants={staggerItem} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <label className="block text-sm font-medium text-gray-900 mb-2">
          Anything else we should know?
        </label>
        <textarea
          value={additions}
          onChange={(e) => setAdditions(e.target.value)}
          placeholder="Any additional context, concerns, or priorities..."
          className="w-full px-4 py-3 border border-gray-200 rounded-xl resize-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          rows={4}
        />
      </motion.div>

      <motion.div variants={staggerItem}>
        {submitError && (
          <p className="text-sm text-red-600 mb-3 text-center">{submitError}</p>
        )}
        <button
          onClick={handleSubmit}
          disabled={!timeline || isSubmitting}
          className={`w-full px-6 py-4 rounded-xl font-semibold text-lg transition ${
            timeline && !isSubmitting
              ? 'bg-primary-600 text-white hover:bg-primary-700 shadow-lg shadow-primary-600/25'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          }`}
        >
          {isSubmitting ? 'Generating Report...' : 'Generate My Report'}
        </button>
      </motion.div>
    </motion.div>
  )
}
