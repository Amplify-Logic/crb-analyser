import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import apiClient from '../services/apiClient'
import CompanyResearchStep from '../components/research/CompanyResearchStep'
import DynamicQuestionnaireStep from '../components/research/DynamicQuestionnaireStep'

type Step = 'research' | 'questionnaire' | 'tier'

interface Tier {
  id: string
  name: string
  price: number
  description: string
  features: string[]
}

const TIERS: Tier[] = [
  {
    id: 'free',
    name: 'Free Assessment',
    price: 0,
    description: 'Get your AI Readiness Score',
    features: [
      'AI Readiness Score (0-100)',
      '3 finding titles (preview)',
      'Upgrade path to full report',
    ],
  },
  {
    id: 'professional',
    name: 'Professional Audit',
    price: 497,
    description: 'Complete AI readiness analysis with actionable insights',
    features: [
      'Full AI Readiness Score',
      '15-20 detailed findings',
      'ROI calculations for each recommendation',
      'Vendor comparisons',
      'Implementation roadmap',
      'PDF + Web report',
      'Raw data export',
    ],
  },
]

export default function NewAuditV2() {
  const navigate = useNavigate()
  const [step, setStep] = useState<Step>('research')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Research data
  const [researchId, setResearchId] = useState<string | null>(null)
  const [companyProfile, setCompanyProfile] = useState<any>(null)
  const [questionnaire, setQuestionnaire] = useState<any>(null)

  // Questionnaire responses
  const [responses, setResponses] = useState<Record<string, any>>({})

  // Tier selection
  const [selectedTier, setSelectedTier] = useState<string>('professional')

  const handleResearchComplete = (data: {
    researchId: string
    companyProfile: any
    questionnaire: any
  }) => {
    setResearchId(data.researchId)
    setCompanyProfile(data.companyProfile)
    setQuestionnaire(data.questionnaire)
    setStep('questionnaire')
  }

  const handleQuestionnaireComplete = (responses: Record<string, any>) => {
    setResponses(responses)
    setStep('tier')
  }

  const handleBackFromQuestionnaire = () => {
    setStep('research')
  }

  const handleCreateAudit = async () => {
    if (!researchId) {
      setError('Research data missing')
      return
    }

    setLoading(true)
    setError('')

    try {
      // Save questionnaire answers and create client + audit
      const { data } = await apiClient.post<{ audit_id: string; client_id: string }>(
        `/api/research/${researchId}/answers`,
        {
          answers: responses,
          tier: selectedTier,
        }
      )

      // Navigate to audit progress or intake based on tier
      navigate(`/audit/${data.audit_id}/progress`)
    } catch (err: any) {
      setError(err.message || 'Failed to create audit')
    } finally {
      setLoading(false)
    }
  }

  // Calculate step number for progress indicator
  const stepNumber = step === 'research' ? 1 : step === 'questionnaire' ? 2 : 3

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-3xl mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">New AI Readiness Analysis</h1>
          <p className="text-gray-600 mt-2">
            Let's start by learning about your company
          </p>
        </div>

        {/* Progress indicator */}
        <div className="flex items-center mb-8">
          {['Research', 'Questions', 'Start'].map((label, i) => (
            <div key={label} className="flex items-center">
              <div
                className={`flex items-center justify-center w-10 h-10 rounded-full transition-colors ${
                  stepNumber > i + 1
                    ? 'bg-green-500 text-white'
                    : stepNumber === i + 1
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-200 text-gray-400'
                }`}
              >
                {stepNumber > i + 1 ? (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                ) : (
                  i + 1
                )}
              </div>
              <span
                className={`ml-2 text-sm ${
                  stepNumber === i + 1 ? 'text-gray-900 font-medium' : 'text-gray-500'
                }`}
              >
                {label}
              </span>
              {i < 2 && (
                <div
                  className={`flex-1 h-1 mx-4 w-16 ${
                    stepNumber > i + 1 ? 'bg-green-500' : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
            {error}
          </div>
        )}

        {/* Step 1: Research */}
        {step === 'research' && (
          <CompanyResearchStep onComplete={handleResearchComplete} />
        )}

        {/* Step 2: Dynamic Questionnaire */}
        {step === 'questionnaire' && companyProfile && questionnaire && (
          <DynamicQuestionnaireStep
            companyProfile={companyProfile}
            questionnaire={questionnaire}
            onComplete={handleQuestionnaireComplete}
            onBack={handleBackFromQuestionnaire}
          />
        )}

        {/* Step 3: Select Tier */}
        {step === 'tier' && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Choose Your Analysis Depth
              </h2>
              <p className="text-gray-600 mb-6">
                Select the level of analysis that fits your needs
              </p>

              <div className="space-y-4">
                {TIERS.map((tier) => (
                  <label
                    key={tier.id}
                    className={`block p-6 rounded-xl border-2 cursor-pointer transition ${
                      selectedTier === tier.id
                        ? 'border-primary-600 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="tier"
                      value={tier.id}
                      checked={selectedTier === tier.id}
                      onChange={() => setSelectedTier(tier.id)}
                      className="sr-only"
                    />

                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-semibold text-gray-900">{tier.name}</h3>
                        <p className="text-gray-600 text-sm mt-1">{tier.description}</p>
                      </div>
                      <div className="text-right">
                        <span className="text-2xl font-bold text-gray-900">
                          {tier.price === 0 ? 'Free' : `€${tier.price}`}
                        </span>
                      </div>
                    </div>

                    <ul className="mt-4 space-y-2">
                      {tier.features.map((feature, i) => (
                        <li key={i} className="flex items-center gap-2 text-sm text-gray-600">
                          <svg
                            className={`w-4 h-4 ${
                              selectedTier === tier.id ? 'text-primary-600' : 'text-gray-400'
                            }`}
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                              clipRule="evenodd"
                            />
                          </svg>
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </label>
                ))}
              </div>
            </div>

            <div className="flex justify-between">
              <button
                onClick={() => setStep('questionnaire')}
                className="px-6 py-2 text-gray-600 hover:text-gray-900 transition"
              >
                Back
              </button>
              <button
                onClick={handleCreateAudit}
                disabled={loading}
                className="px-8 py-3 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Starting Analysis...
                  </>
                ) : (
                  <>
                    Start Analysis
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 7l5 5m0 0l-5 5m5-5H6"
                      />
                    </svg>
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
