import { useState, useEffect, useRef } from 'react'

interface CompanyResearchStepProps {
  onComplete: (data: {
    researchId: string
    companyProfile: any
    questionnaire: any
  }) => void
  initialData?: {
    companyName: string
    websiteUrl: string
  }
}

interface ResearchUpdate {
  research_id?: string
  status: string
  step: string
  progress: number
  result?: {
    company_profile: any
    questionnaire: any
  }
  error?: string
}

export default function CompanyResearchStep({ onComplete, initialData }: CompanyResearchStepProps) {
  const [companyName, setCompanyName] = useState(initialData?.companyName || '')
  const [websiteUrl, setWebsiteUrl] = useState(initialData?.websiteUrl || '')
  const [isResearching, setIsResearching] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState('')
  const [error, setError] = useState('')
  const eventSourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    return () => {
      // Cleanup EventSource on unmount
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  const startResearch = async () => {
    if (!companyName.trim()) {
      setError('Please enter a company name')
      return
    }

    setIsResearching(true)
    setError('')
    setProgress(0)
    setCurrentStep('Initiating research...')

    try {
      // Step 1: Create research record via POST
      const token = localStorage.getItem('crb_auth_token')
      const startResponse = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/research/start`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { Cookie: `crb_auth_token=${token}` }),
          },
          credentials: 'include',
          body: JSON.stringify({
            company_name: companyName.trim(),
            website_url: websiteUrl.trim() || null,
          }),
        }
      )

      if (!startResponse.ok) {
        const errorData = await startResponse.json()
        throw new Error(errorData.detail || 'Failed to start research')
      }

      const { research_id } = await startResponse.json()
      setCurrentStep('Connecting to research stream...')

      // Step 2: Connect to SSE stream with credentials
      // Note: EventSource doesn't support credentials, so we'll use fetch for streaming
      const streamResponse = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/research/${research_id}/stream`,
        {
          credentials: 'include',
        }
      )

      if (!streamResponse.ok) {
        throw new Error('Failed to connect to research stream')
      }

      const reader = streamResponse.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No response body')
      }

      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // Process complete SSE messages
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const update: ResearchUpdate = JSON.parse(line.slice(6))

              setProgress(update.progress || 0)
              setCurrentStep(update.step || '')

              if (update.status === 'ready' && update.result) {
                setIsResearching(false)
                onComplete({
                  researchId: research_id,
                  companyProfile: update.result.company_profile,
                  questionnaire: update.result.questionnaire,
                })
                return
              } else if (update.status === 'failed') {
                setIsResearching(false)
                setError(update.error || 'Research failed')
                return
              }
            } catch (e) {
              console.error('Failed to parse research update:', e, line)
            }
          }
        }
      }
    } catch (err: any) {
      setIsResearching(false)
      setError(err.message || 'Failed to start research')
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-2">
        Let's Learn About Your Company
      </h2>
      <p className="text-gray-600 mb-6">
        We'll research your company from public sources to prepare tailored questions.
        This saves you time and makes our analysis more accurate.
      </p>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
          {error}
        </div>
      )}

      {!isResearching ? (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Company Name *
            </label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="e.g., Aquablu"
              className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Website URL (optional, but recommended)
            </label>
            <input
              type="url"
              value={websiteUrl}
              onChange={(e) => setWebsiteUrl(e.target.value)}
              placeholder="e.g., https://www.aquablu.com"
              className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition"
            />
            <p className="mt-1 text-sm text-gray-500">
              Providing your website helps us gather more accurate information
            </p>
          </div>

          <button
            onClick={startResearch}
            className="w-full mt-4 py-3 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Research My Company
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Progress indicator */}
          <div className="relative pt-1">
            <div className="flex mb-2 items-center justify-between">
              <div>
                <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-primary-600 bg-primary-100">
                  Researching
                </span>
              </div>
              <div className="text-right">
                <span className="text-xs font-semibold inline-block text-primary-600">
                  {progress}%
                </span>
              </div>
            </div>
            <div className="overflow-hidden h-2 text-xs flex rounded-full bg-primary-100">
              <div
                style={{ width: `${progress}%` }}
                className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-primary-600 transition-all duration-300"
              />
            </div>
          </div>

          {/* Current step */}
          <div className="text-center">
            <div className="animate-pulse inline-flex items-center gap-2 text-gray-600">
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              {currentStep}
            </div>
          </div>

          {/* What we're doing */}
          <div className="bg-gray-50 rounded-xl p-4">
            <h4 className="font-medium text-gray-900 mb-2">What we're looking for:</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-center gap-2">
                <svg className={`w-4 h-4 ${progress >= 20 ? 'text-green-500' : 'text-gray-300'}`} fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Company website and services
              </li>
              <li className="flex items-center gap-2">
                <svg className={`w-4 h-4 ${progress >= 35 ? 'text-green-500' : 'text-gray-300'}`} fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Company size and industry
              </li>
              <li className="flex items-center gap-2">
                <svg className={`w-4 h-4 ${progress >= 50 ? 'text-green-500' : 'text-gray-300'}`} fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Technology stack and tools
              </li>
              <li className="flex items-center gap-2">
                <svg className={`w-4 h-4 ${progress >= 65 ? 'text-green-500' : 'text-gray-300'}`} fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Recent news and activity
              </li>
              <li className="flex items-center gap-2">
                <svg className={`w-4 h-4 ${progress >= 80 ? 'text-green-500' : 'text-gray-300'}`} fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Generating tailored questions
              </li>
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
