/**
 * SynthesisForm Component
 *
 * Final questions form for Phase 3 of the workshop.
 * Collects stakeholder info, timeline, and additional context.
 */

import { useState } from 'react'

interface SynthesisFormProps {
  onComplete: (answers: Record<string, any>) => void
}

export default function SynthesisForm({ onComplete }: SynthesisFormProps) {
  const [stakeholders, setStakeholders] = useState('')
  const [timeline, setTimeline] = useState('')
  const [additions, setAdditions] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = () => {
    setIsSubmitting(true)
    onComplete({
      stakeholders: stakeholders.split(',').map(s => s.trim()).filter(Boolean),
      timeline,
      additions: additions || null,
    })
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
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
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
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
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
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
      </div>

      <button
        onClick={handleSubmit}
        disabled={!timeline || isSubmitting}
        className={`w-full px-6 py-4 rounded-xl font-semibold transition ${
          timeline && !isSubmitting
            ? 'bg-primary-600 text-white hover:bg-primary-700'
            : 'bg-gray-200 text-gray-400 cursor-not-allowed'
        }`}
      >
        {isSubmitting ? 'Generating Report...' : 'Generate My Report'}
      </button>
    </div>
  )
}
