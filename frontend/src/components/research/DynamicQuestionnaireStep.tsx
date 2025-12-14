import { useState, useCallback } from 'react'
import { useVoiceInput } from '../../hooks/useVoiceInput'

interface Question {
  id: string
  question: string
  type: string
  purpose: string
  rationale: string
  prefilled_value?: any
  prefilled_confidence?: string
  required: boolean
  options?: Array<{ value: string; label: string }>
  placeholder?: string
  min_value?: number
  max_value?: number
  section: string
  priority: number
}

interface Questionnaire {
  company_name: string
  research_summary: string
  confirmed_facts: Array<{ fact: string; confidence: string }>
  questions: Question[]
  total_questions: number
  estimated_time_minutes: number
  sections: Array<{ id: string; title: string; description: string }>
}

interface CompanyProfile {
  company_name: string
  website?: string
  basics?: {
    name?: { value: string }
    description?: { value: string }
    industry?: { value: string }
    founded_year?: { value: string }
    headquarters?: { value: string }
  }
  size?: {
    employee_count?: { value: number }
    employee_range?: { value: string }
  }
  products?: {
    main_products?: Array<{ value: string }>
    key_features?: string[]
  }
  research_quality_score: number
}

interface DynamicQuestionnaireStepProps {
  companyProfile: CompanyProfile
  questionnaire: Questionnaire
  onComplete: (responses: Record<string, any>) => void
  onBack: () => void
}

export default function DynamicQuestionnaireStep({
  companyProfile,
  questionnaire,
  onComplete,
  onBack,
}: DynamicQuestionnaireStepProps) {
  const [responses, setResponses] = useState<Record<string, any>>(() => {
    // Pre-fill with values from research
    const initial: Record<string, any> = {}
    questionnaire.questions.forEach((q) => {
      if (q.prefilled_value !== undefined && q.prefilled_value !== null) {
        initial[q.id] = q.prefilled_value
      }
    })
    return initial
  })
  const [currentSection, setCurrentSection] = useState(0)
  const [showProfile, setShowProfile] = useState(true)
  const [recordingQuestionId, setRecordingQuestionId] = useState<string | null>(null)
  const [voiceError, setVoiceError] = useState<string | null>(null)

  const { state: voiceState, toggleRecording } = useVoiceInput({
    onTranscript: useCallback((text: string) => {
      if (recordingQuestionId) {
        setResponses((prev) => ({
          ...prev,
          [recordingQuestionId]: prev[recordingQuestionId]
            ? `${prev[recordingQuestionId]} ${text}`
            : text,
        }))
      }
      setRecordingQuestionId(null)
    }, [recordingQuestionId]),
    onError: useCallback((error: string) => {
      setVoiceError(error)
      setRecordingQuestionId(null)
      // Auto-clear error after 3 seconds
      setTimeout(() => setVoiceError(null), 3000)
    }, []),
  })

  // Group questions by section using question_ids from sections
  const sections = questionnaire.sections.map((section: any) => ({
    ...section,
    questions: section.question_ids
      ? questionnaire.questions.filter((q: Question) => section.question_ids.includes(q.id))
      : questionnaire.questions.filter((q: Question) => q.section === section.id || q.section === section.title?.toLowerCase()),
  }))

  const currentQuestions = sections[currentSection]?.questions || []
  const isLastSection = currentSection === sections.length - 1

  const updateResponse = (questionId: string, value: any) => {
    setResponses((prev) => ({ ...prev, [questionId]: value }))
  }

  const handleVoiceToggle = async (questionId: string) => {
    if (recordingQuestionId === questionId) {
      // Stop recording current question
      await toggleRecording()
    } else if (recordingQuestionId === null) {
      // Start recording for this question
      setRecordingQuestionId(questionId)
      await toggleRecording()
    }
    // If recording another question, ignore (must stop current first)
  }

  const VoiceInputButton = ({ questionId }: { questionId: string }) => {
    const isThisRecording = recordingQuestionId === questionId
    const isTranscribing = isThisRecording && voiceState === 'transcribing'
    const isRecording = isThisRecording && voiceState === 'recording'
    const isOtherRecording = recordingQuestionId !== null && recordingQuestionId !== questionId

    return (
      <button
        type="button"
        onClick={() => handleVoiceToggle(questionId)}
        disabled={isTranscribing || isOtherRecording}
        className={`p-2 rounded-lg transition-all ${
          isRecording
            ? 'bg-red-100 text-red-600 animate-pulse'
            : isTranscribing
            ? 'bg-purple-100 text-purple-600'
            : isOtherRecording
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        }`}
        title={
          isRecording
            ? 'Click to stop recording'
            : isTranscribing
            ? 'Transcribing...'
            : 'Click to start voice input'
        }
      >
        {isTranscribing ? (
          <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        ) : (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
          </svg>
        )}
      </button>
    )
  }

  const handleNext = () => {
    if (isLastSection) {
      onComplete(responses)
    } else {
      setCurrentSection((prev) => prev + 1)
      setShowProfile(false)
    }
  }

  const handleBack = () => {
    if (currentSection > 0) {
      setCurrentSection((prev) => prev - 1)
    } else {
      onBack()
    }
  }

  const renderQuestion = (question: Question) => {
    const value = responses[question.id]
    const isPrefilled = question.prefilled_value !== undefined && question.prefilled_value !== null

    return (
      <div key={question.id} className="space-y-2">
        <label className="block">
          <span className="text-sm font-medium text-gray-700">
            {question.question}
            {question.required && <span className="text-red-500 ml-1">*</span>}
          </span>
          {question.rationale && (
            <span className="block text-xs text-gray-500 mt-1">
              {question.rationale}
            </span>
          )}
        </label>

        {isPrefilled && (
          <div className="flex items-center gap-2 text-xs text-primary-600 bg-primary-50 px-2 py-1 rounded">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            Pre-filled from our research - please verify
          </div>
        )}

        {question.type === 'text' && (
          <div className="flex gap-2">
            <input
              type="text"
              value={value || ''}
              onChange={(e) => updateResponse(question.id, e.target.value)}
              placeholder={question.placeholder}
              className="flex-1 px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition"
            />
            <VoiceInputButton questionId={question.id} />
          </div>
        )}

        {question.type === 'textarea' && (
          <div className="relative">
            <textarea
              value={value || ''}
              onChange={(e) => updateResponse(question.id, e.target.value)}
              placeholder={question.placeholder}
              rows={4}
              className="w-full px-4 py-3 pr-12 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition resize-none"
            />
            <div className="absolute bottom-3 right-3">
              <VoiceInputButton questionId={question.id} />
            </div>
          </div>
        )}

        {question.type === 'select' && question.options && (
          <select
            value={value || ''}
            onChange={(e) => updateResponse(question.id, e.target.value)}
            className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition"
          >
            <option value="">Select an option...</option>
            {question.options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        )}

        {question.type === 'multi_select' && question.options && (
          <div className="space-y-2">
            {question.options.map((opt) => (
              <label
                key={opt.value}
                className="flex items-center gap-3 p-3 rounded-xl border border-gray-200 hover:bg-gray-50 cursor-pointer transition"
              >
                <input
                  type="checkbox"
                  checked={Array.isArray(value) && value.includes(opt.value)}
                  onChange={(e) => {
                    const currentValues = Array.isArray(value) ? value : []
                    if (e.target.checked) {
                      updateResponse(question.id, [...currentValues, opt.value])
                    } else {
                      updateResponse(
                        question.id,
                        currentValues.filter((v: string) => v !== opt.value)
                      )
                    }
                  }}
                  className="w-5 h-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-gray-700">{opt.label}</span>
              </label>
            ))}
          </div>
        )}

        {question.type === 'yes_no' && (
          <div className="flex gap-4">
            {['yes', 'no'].map((opt) => (
              <label
                key={opt}
                className={`flex-1 p-4 rounded-xl border-2 cursor-pointer transition text-center ${
                  value === opt
                    ? 'border-primary-600 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <input
                  type="radio"
                  name={question.id}
                  value={opt}
                  checked={value === opt}
                  onChange={() => updateResponse(question.id, opt)}
                  className="sr-only"
                />
                <span className="font-medium capitalize">{opt}</span>
              </label>
            ))}
          </div>
        )}

        {question.type === 'scale' && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">{question.min_value || 1}</span>
            <input
              type="range"
              min={question.min_value || 1}
              max={question.max_value || 10}
              value={value || question.min_value || 1}
              onChange={(e) => updateResponse(question.id, parseInt(e.target.value))}
              className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
            />
            <span className="text-sm text-gray-500">{question.max_value || 10}</span>
            <span className="ml-4 text-lg font-semibold text-primary-600 w-8 text-center">
              {value || question.min_value || 1}
            </span>
          </div>
        )}

        {question.type === 'number' && (
          <input
            type="number"
            value={value || ''}
            onChange={(e) => updateResponse(question.id, e.target.value ? parseInt(e.target.value) : null)}
            placeholder={question.placeholder}
            min={question.min_value}
            max={question.max_value}
            className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition"
          />
        )}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Voice Error Toast */}
      {voiceError && (
        <div className="fixed top-4 right-4 z-50 bg-red-100 border border-red-200 text-red-700 px-4 py-3 rounded-xl shadow-lg flex items-center gap-2 animate-in fade-in slide-in-from-top-2">
          <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <span className="text-sm">{voiceError}</span>
          <button
            onClick={() => setVoiceError(null)}
            className="ml-2 text-red-500 hover:text-red-700"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      )}

      {/* Research Summary (collapsed after first section) */}
      {showProfile && (
        <div className="bg-gradient-to-br from-primary-50 to-white rounded-2xl shadow-sm p-6 border border-primary-100">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                What We Found About {companyProfile.company_name || questionnaire.company_name}
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Research Quality Score: {companyProfile.research_quality_score}%
              </p>
            </div>
            <button
              onClick={() => setShowProfile(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {questionnaire.research_summary && (
            <p className="text-gray-700 mb-4">{questionnaire.research_summary}</p>
          )}

          {questionnaire.confirmed_facts && questionnaire.confirmed_facts.length > 0 && (
            <div className="grid grid-cols-2 gap-3">
              {questionnaire.confirmed_facts.slice(0, 6).map((fact, i) => (
                <div key={i} className="bg-white rounded-lg p-3 border border-gray-100">
                  <p className="text-sm font-medium text-gray-900">{fact.fact}</p>
                  <span className={`text-xs ${
                    fact.confidence === 'high' ? 'text-green-600' :
                    fact.confidence === 'medium' ? 'text-yellow-600' : 'text-gray-400'
                  }`}>
                    {fact.confidence} confidence
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Section Progress */}
      <div className="flex items-center gap-2">
        {sections.map((section, i) => (
          <div
            key={section.id}
            className={`flex-1 h-2 rounded-full transition-colors ${
              i < currentSection
                ? 'bg-primary-600'
                : i === currentSection
                ? 'bg-primary-400'
                : 'bg-gray-200'
            }`}
          />
        ))}
      </div>

      {/* Current Section */}
      <div className="bg-white rounded-2xl shadow-sm p-6">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900">
            {sections[currentSection]?.title || `Section ${currentSection + 1}`}
          </h3>
          {sections[currentSection]?.description && (
            <p className="text-gray-600 mt-1">{sections[currentSection].description}</p>
          )}
          <p className="text-sm text-gray-500 mt-2">
            {currentQuestions.length} questions in this section
          </p>
        </div>

        <div className="space-y-6">
          {currentQuestions.map(renderQuestion)}
        </div>

        {/* Navigation */}
        <div className="flex justify-between mt-8 pt-6 border-t border-gray-100">
          <button
            onClick={handleBack}
            className="px-6 py-2 text-gray-600 hover:text-gray-900 transition"
          >
            Back
          </button>
          <button
            onClick={handleNext}
            className="px-6 py-3 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition"
          >
            {isLastSection ? 'Complete Questionnaire' : 'Next Section'}
          </button>
        </div>
      </div>

      {/* Estimated time */}
      <p className="text-center text-sm text-gray-500">
        Estimated time remaining: ~{Math.ceil(questionnaire.estimated_time_minutes * (1 - currentSection / sections.length))} minutes
      </p>
    </div>
  )
}
