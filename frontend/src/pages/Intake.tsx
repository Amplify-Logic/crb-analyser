import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import apiClient from '../services/apiClient'
import VoiceRecorder from '../components/VoiceRecorder'

interface Question {
  id: string
  question: string
  type: string
  required: boolean
  placeholder?: string
  options?: { value: string; label: string }[]
  min?: number
  max?: number
  scale_min?: number
  scale_max?: number
  scale_labels?: Record<string, string>
}

interface Section {
  id: number
  title: string
  description: string
  questions: Question[]
}

interface IntakeData {
  id: string
  audit_id: string
  responses: Record<string, any>
  current_section: number
  is_complete: boolean
  audit_title?: string
  client_name?: string
  client_industry?: string
}

export default function Intake() {
  const { id: auditId } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [sections, setSections] = useState<Section[]>([])
  const [currentSection, setCurrentSection] = useState(1)
  const [responses, setResponses] = useState<Record<string, any>>({})
  const [intakeData, setIntakeData] = useState<IntakeData | null>(null)

  // Load questionnaire and intake data
  useEffect(() => {
    if (auditId) {
      loadData()
    }
  }, [auditId])

  async function loadData() {
    setLoading(true)
    try {
      // Load intake data (includes client industry)
      const { data: intake } = await apiClient.get<IntakeData>(
        `/api/intake/${auditId}`
      )
      setIntakeData(intake)
      setResponses(intake.responses || {})
      setCurrentSection(intake.current_section || 1)

      // Load questionnaire with industry-specific questions
      const { data: questionnaire } = await apiClient.get<{
        sections: Section[]
      }>(`/api/intake/questionnaire?industry=${intake.client_industry || ''}`)
      setSections(questionnaire.sections)
    } catch (err: any) {
      setError(err.message || 'Failed to load intake')
    } finally {
      setLoading(false)
    }
  }

  // Auto-save responses
  const saveProgress = useCallback(async () => {
    if (!auditId) return
    setSaving(true)
    try {
      await apiClient.patch(`/api/intake/${auditId}`, {
        responses,
        current_section: currentSection,
      })
    } catch (err) {
      console.error('Failed to save progress:', err)
    } finally {
      setSaving(false)
    }
  }, [auditId, responses, currentSection])

  // Debounced auto-save
  useEffect(() => {
    const timer = setTimeout(() => {
      if (Object.keys(responses).length > 0) {
        saveProgress()
      }
    }, 2000)
    return () => clearTimeout(timer)
  }, [responses, saveProgress])

  function updateResponse(questionId: string, value: any) {
    setResponses((prev) => ({ ...prev, [questionId]: value }))
  }

  function handleNext() {
    if (currentSection < sections.length) {
      setCurrentSection(currentSection + 1)
      window.scrollTo(0, 0)
    }
  }

  function handlePrev() {
    if (currentSection > 1) {
      setCurrentSection(currentSection - 1)
      window.scrollTo(0, 0)
    }
  }

  async function handleSubmit() {
    setError('')
    setSaving(true)

    try {
      // Validate before submit
      const { data: validation } = await apiClient.post<{
        is_valid: boolean
        missing_required: string[]
      }>(`/api/intake/${auditId}/validate`)

      if (!validation.is_valid) {
        setError(
          `Please answer all required questions: ${validation.missing_required.join(', ')}`
        )
        setSaving(false)
        return
      }

      // Complete intake
      await apiClient.post(`/api/intake/${auditId}/complete`, { responses })

      // Navigate to progress view
      navigate(`/audit/${auditId}/progress`)
    } catch (err: any) {
      setError(err.message || 'Failed to submit intake')
    } finally {
      setSaving(false)
    }
  }

  const currentSectionData = sections[currentSection - 1]
  const progress = sections.length > 0 ? (currentSection / sections.length) * 100 : 0

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading questionnaire...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h1 className="text-lg font-semibold text-gray-900">
                {intakeData?.audit_title || 'CRB Intake'}
              </h1>
              <p className="text-sm text-gray-500">
                {intakeData?.client_name}
              </p>
            </div>
            <div className="text-sm text-gray-500">
              {saving ? (
                <span className="text-primary-600">Saving...</span>
              ) : (
                <span className="text-green-600">Saved</span>
              )}
            </div>
          </div>

          {/* Progress bar */}
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-600 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Section {currentSection} of {sections.length}
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-3xl mx-auto px-4 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
            {error}
          </div>
        )}

        {currentSectionData && (
          <div className="bg-white rounded-2xl shadow-sm p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              {currentSectionData.title}
            </h2>
            <p className="text-gray-600 mb-8">{currentSectionData.description}</p>

            <div className="space-y-8">
              {currentSectionData.questions.map((question) => (
                <QuestionField
                  key={question.id}
                  question={question}
                  value={responses[question.id]}
                  onChange={(value) => updateResponse(question.id, value)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex gap-3 mt-6">
          <button
            onClick={handlePrev}
            disabled={currentSection === 1}
            className="flex-1 py-3 border border-gray-300 text-gray-700 font-semibold rounded-xl hover:bg-gray-50 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>

          {currentSection < sections.length ? (
            <button
              onClick={handleNext}
              className="flex-1 py-3 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition"
            >
              Next
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={saving}
              className="flex-1 py-3 bg-green-600 text-white font-semibold rounded-xl hover:bg-green-700 transition disabled:opacity-50"
            >
              {saving ? 'Submitting...' : 'Submit & Start Analysis'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

// Question field component
interface QuestionFieldProps {
  question: Question
  value: any
  onChange: (value: any) => void
}

function QuestionField({ question, value, onChange }: QuestionFieldProps) {
  const { type, required, placeholder, options, scale_min, scale_max, scale_labels } = question

  return (
    <div>
      <label className="block text-sm font-medium text-gray-900 mb-2">
        {question.question}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>

      {type === 'text' && (
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <VoiceRecorder
            onTranscription={(text) => {
              const current = value || ''
              onChange(current ? `${current} ${text}` : text)
            }}
          />
        </div>
      )}

      {type === 'textarea' && (
        <div className="relative">
          <textarea
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            rows={4}
            className="w-full px-4 py-2 pr-12 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
          />
          <div className="absolute right-2 top-2">
            <VoiceRecorder
              onTranscription={(text) => {
                const current = value || ''
                onChange(current ? `${current} ${text}` : text)
              }}
            />
          </div>
        </div>
      )}

      {type === 'number' && (
        <input
          type="number"
          value={value || ''}
          onChange={(e) => onChange(e.target.value ? parseInt(e.target.value) : null)}
          placeholder={placeholder}
          min={question.min}
          max={question.max}
          className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
      )}

      {type === 'select' && options && (
        <select
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        >
          <option value="">Select an option</option>
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      )}

      {type === 'multi_select' && options && (
        <div className="space-y-2">
          {options.map((opt) => (
            <label
              key={opt.value}
              className="flex items-center p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50"
            >
              <input
                type="checkbox"
                checked={(value || []).includes(opt.value)}
                onChange={(e) => {
                  const current = value || []
                  if (e.target.checked) {
                    onChange([...current, opt.value])
                  } else {
                    onChange(current.filter((v: string) => v !== opt.value))
                  }
                }}
                className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
              />
              <span className="ml-3 text-gray-700">{opt.label}</span>
            </label>
          ))}
        </div>
      )}

      {type === 'yes_no' && (
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => onChange('yes')}
            className={`flex-1 py-3 rounded-xl border-2 font-medium transition ${
              value === 'yes'
                ? 'border-primary-600 bg-primary-50 text-primary-700'
                : 'border-gray-200 text-gray-700 hover:border-gray-300'
            }`}
          >
            Yes
          </button>
          <button
            type="button"
            onClick={() => onChange('no')}
            className={`flex-1 py-3 rounded-xl border-2 font-medium transition ${
              value === 'no'
                ? 'border-primary-600 bg-primary-50 text-primary-700'
                : 'border-gray-200 text-gray-700 hover:border-gray-300'
            }`}
          >
            No
          </button>
        </div>
      )}

      {type === 'scale' && (
        <div>
          <div className="flex justify-between text-xs text-gray-500 mb-2">
            <span>{scale_labels?.['1'] || scale_min}</span>
            <span>{scale_labels?.['10'] || scale_max}</span>
          </div>
          <div className="flex gap-2">
            {Array.from(
              { length: (scale_max || 10) - (scale_min || 1) + 1 },
              (_, i) => i + (scale_min || 1)
            ).map((num) => (
              <button
                key={num}
                type="button"
                onClick={() => onChange(num)}
                className={`flex-1 py-2 rounded-lg border-2 font-medium text-sm transition ${
                  value === num
                    ? 'border-primary-600 bg-primary-600 text-white'
                    : 'border-gray-200 text-gray-700 hover:border-gray-300'
                }`}
              >
                {num}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
