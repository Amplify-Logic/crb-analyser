/**
 * PreviewReport Page
 *
 * Shows a sales preview with genuine insights after the voice interview.
 * This is the "hook" that demonstrates value before payment.
 */

import { useState, useEffect } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8383'

interface CompanyProfile {
  basics?: {
    name?: { value: string }
    description?: { value: string }
  }
  industry?: {
    primary_industry?: { value: string }
  }
  size?: {
    employee_range?: { value: string }
  }
}

interface Opportunity {
  title: string
  description: string
  potential: 'High' | 'Medium' | 'Low'
  timeToValue: string
  blurred?: boolean
}

interface PreviewData {
  score: number
  opportunities: Opportunity[]
  industryInsight: string
  topRecommendation: string
  estimatedSavings: string
}

export default function PreviewReport() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const sessionId = searchParams.get('session_id') || sessionStorage.getItem('quizSessionId')

  const [isLoading, setIsLoading] = useState(true)
  const [previewData, setPreviewData] = useState<PreviewData | null>(null)
  const [companyName, setCompanyName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [devShowAll, setDevShowAll] = useState(false) // DEV: toggle to show all findings

  useEffect(() => {
    generatePreview()
  }, [])

  const generatePreview = async () => {
    try {
      setIsLoading(true)

      // Get stored data
      const companyProfileStr = sessionStorage.getItem('companyProfile')
      const answersStr = sessionStorage.getItem('quizAnswers')
      const messagesStr = sessionStorage.getItem('quizMessages')
      const storedCompanyName = sessionStorage.getItem('companyName')

      if (storedCompanyName) {
        setCompanyName(storedCompanyName)
      }

      const companyProfile: CompanyProfile = companyProfileStr ? JSON.parse(companyProfileStr) : {}
      const answers = answersStr ? JSON.parse(answersStr) : {}
      const messages = messagesStr ? JSON.parse(messagesStr) : []

      // DEV MODE: Use dev endpoint if we have stored profile data (from skip button)
      const isDev = searchParams.get('dev') === 'true' || import.meta.env.DEV
      if (isDev && companyProfileStr) {
        try {
          const response = await fetch(`${API_BASE_URL}/api/quiz/dev/preview`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              company_profile: companyProfile,
              quiz_answers: answers,
              interview_messages: messages,
            }),
          })

          if (response.ok) {
            const data = await response.json()
            setPreviewData(data)
            if (data.company_name) setCompanyName(data.company_name)
            sessionStorage.setItem('quizResults', JSON.stringify({
              score: data.score,
              opportunities: data.opportunities,
              industryInsight: data.industryInsight,
            }))
            setIsLoading(false)
            return
          }
        } catch (err) {
          console.warn('Dev preview endpoint failed:', err)
        }
      }

      // Try to get preview from backend with session
      try {
        const response = await fetch(`${API_BASE_URL}/api/quiz/sessions/${sessionId}/preview`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            company_profile: companyProfile,
            interview_answers: answers,
            interview_messages: messages,
          }),
        })

        if (response.ok) {
          const data = await response.json()
          setPreviewData(data)
          // Store for checkout
          sessionStorage.setItem('quizResults', JSON.stringify({
            score: data.score,
            opportunities: data.opportunities,
            industryInsight: data.industryInsight,
          }))
          setIsLoading(false)
          return
        }
      } catch (err) {
        console.warn('Backend preview failed, using local generation:', err)
      }

      // Fallback: Generate personalized preview based on available data
      const industry = companyProfile?.industry?.primary_industry?.value || 'your industry'
      const teamSize = companyProfile?.size?.employee_range?.value || 'your team'

      // Analyze interview answers to personalize opportunities
      const allAnswers = Object.values(answers).join(' ').toLowerCase()
      const allMessages = messages.map((m: { content: string }) => m.content).join(' ').toLowerCase()
      const combinedText = `${allAnswers} ${allMessages}`

      // Detect pain points mentioned in interview
      const painPoints = {
        customerSupport: /customer|support|ticket|inquiry|complaint|respond/i.test(combinedText),
        documents: /document|invoice|contract|paperwork|form|data entry/i.test(combinedText),
        content: /content|writing|draft|proposal|marketing|email/i.test(combinedText),
        meetings: /meeting|call|transcript|notes|summary/i.test(combinedText),
        sales: /sales|lead|prospect|crm|pipeline|outreach/i.test(combinedText),
        scheduling: /schedule|appointment|calendar|booking/i.test(combinedText),
        reporting: /report|analytics|dashboard|metric/i.test(combinedText),
        manual: /manual|repetitive|copy.paste|tedious|slow/i.test(combinedText),
      }

      // Generate personalized opportunities based on detected pain points
      const opportunities: Opportunity[] = []

      // Always show top 2 opportunities based on what they mentioned
      if (painPoints.customerSupport || painPoints.manual) {
        opportunities.push({
          title: 'Customer Support Automation',
          description: 'AI-powered chatbot and ticket routing to handle 60%+ of routine inquiries automatically.',
          potential: 'High',
          timeToValue: '2-4 weeks',
          blurred: false,
        })
      }

      if (painPoints.documents || painPoints.manual) {
        opportunities.push({
          title: 'Document Processing',
          description: 'Automate data extraction from invoices, contracts, and forms - reducing manual entry by 80%.',
          potential: 'High',
          timeToValue: '1-2 weeks',
          blurred: opportunities.length >= 2,
        })
      }

      if (painPoints.content) {
        opportunities.push({
          title: 'Content Creation Pipeline',
          description: `AI-assisted drafting for marketing, proposals, and ${industry} documentation - 70% faster first drafts.`,
          potential: 'High',
          timeToValue: '1 week',
          blurred: opportunities.length >= 2,
        })
      }

      if (painPoints.meetings) {
        opportunities.push({
          title: 'Meeting Intelligence',
          description: 'Automatic transcription, summaries, and action item extraction - save 4+ hours/week.',
          potential: 'Medium',
          timeToValue: '1-2 days',
          blurred: opportunities.length >= 2,
        })
      }

      if (painPoints.sales) {
        opportunities.push({
          title: 'Sales Intelligence',
          description: 'Lead scoring and personalized outreach recommendations to boost conversion rates.',
          potential: 'High',
          timeToValue: '2-3 weeks',
          blurred: opportunities.length >= 2,
        })
      }

      if (painPoints.scheduling) {
        opportunities.push({
          title: 'Smart Scheduling',
          description: 'AI-powered appointment booking and calendar management to eliminate back-and-forth.',
          potential: 'Medium',
          timeToValue: '1 week',
          blurred: opportunities.length >= 2,
        })
      }

      if (painPoints.reporting) {
        opportunities.push({
          title: 'Automated Reporting',
          description: 'Generate reports and dashboards automatically from your data sources.',
          potential: 'Medium',
          timeToValue: '2-3 weeks',
          blurred: opportunities.length >= 2,
        })
      }

      // Fill in with generic opportunities if we don't have enough
      const defaultOpportunities: Opportunity[] = [
        { title: 'Customer Support Automation', description: 'AI chatbot for routine inquiries.', potential: 'High', timeToValue: '2-4 weeks', blurred: false },
        { title: 'Document Processing', description: 'Extract data from documents automatically.', potential: 'High', timeToValue: '1-2 weeks', blurred: false },
        { title: 'Content Creation Pipeline', description: 'AI-assisted drafting and editing.', potential: 'Medium', timeToValue: '1 week', blurred: true },
        { title: 'Meeting Intelligence', description: 'Transcription and summaries.', potential: 'Medium', timeToValue: '1-2 days', blurred: true },
        { title: 'Workflow Automation', description: 'Connect your tools and automate handoffs.', potential: 'High', timeToValue: '2-3 weeks', blurred: true },
      ]

      while (opportunities.length < 5) {
        const missing = defaultOpportunities.find(d => !opportunities.some(o => o.title === d.title))
        if (missing) {
          opportunities.push({ ...missing, blurred: opportunities.length >= 2 })
        } else {
          break
        }
      }

      // Calculate a score based on available data and detected pain points
      const hasProfile = Object.keys(companyProfile).length > 0
      const hasAnswers = Object.keys(answers).length > 0
      const hasMessages = messages.length > 0
      const painPointCount = Object.values(painPoints).filter(Boolean).length

      const baseScore = 40 + (hasProfile ? 15 : 0) + (hasAnswers ? 15 : 0) + (hasMessages ? 10 : 0) + (painPointCount * 3)
      const score = Math.min(92, baseScore + Math.floor(Math.random() * 5))

      // Generate personalized insight
      const detectedAreas = Object.entries(painPoints)
        .filter(([_, detected]) => detected)
        .map(([area]) => area)
        .slice(0, 2)

      const areaLabels: Record<string, string> = {
        customerSupport: 'customer support',
        documents: 'document processing',
        content: 'content creation',
        meetings: 'meeting management',
        sales: 'sales processes',
        scheduling: 'scheduling',
        reporting: 'reporting',
        manual: 'manual tasks',
      }

      const focusAreas = detectedAreas.map(a => areaLabels[a] || a).join(' and ')

      const preview: PreviewData = {
        score,
        opportunities,
        industryInsight: focusAreas
          ? `Based on your interview, ${focusAreas} are clear areas for AI automation. ${industry} businesses typically see 30-50% efficiency gains when they start with focused implementations.`
          : `Based on Q4 2025 research, ${industry} businesses are seeing 30-50% efficiency gains from targeted AI automation. Companies with ${teamSize} are ideal candidates for quick-win implementations.`,
        topRecommendation: opportunities[0]
          ? `Start with ${opportunities[0].title.toLowerCase()} - it addresses the challenges you mentioned and has the fastest time to value.`
          : 'Start with customer support automation - it has the highest ROI and fastest time to value for most businesses.',
        estimatedSavings: score >= 70 ? '€25,000 - €75,000/year' : score >= 50 ? '€15,000 - €45,000/year' : '€10,000 - €30,000/year',
      }

      setPreviewData(preview)

      // Store for checkout
      sessionStorage.setItem('quizResults', JSON.stringify({
        score: preview.score,
        opportunities: preview.opportunities.map(o => ({
          title: o.title,
          potential: o.potential,
          preview: !o.blurred,
        })),
        industryInsight: preview.industryInsight,
      }))

      setIsLoading(false)
    } catch (err) {
      console.error('Preview generation error:', err)
      setError('Failed to generate preview')
      setIsLoading(false)
    }
  }

  const handleGetFullReport = () => {
    navigate(`/checkout?tier=ai`)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-50 to-purple-50 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center"
        >
          <div className="relative w-24 h-24 mx-auto mb-6">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
              className="w-24 h-24 border-4 border-primary-200 border-t-primary-600 rounded-full"
            />
            <div className="absolute inset-0 flex items-center justify-center">
              <svg className="w-10 h-10 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Generating Your Preview...</h2>
          <p className="text-gray-600">Analyzing your responses and finding opportunities</p>
        </motion.div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Something went wrong</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => navigate('/quiz')}
            className="px-6 py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700"
          >
            Start Over
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
          <Link to="/" className="text-xl font-bold text-gray-900">
            CRB<span className="text-primary-600">Analyser</span>
          </Link>
          <div className="flex items-center gap-4">
            {/* DEV MODE toggle */}
            {import.meta.env.DEV && (
              <button
                onClick={() => setDevShowAll(!devShowAll)}
                className={`px-3 py-1 text-xs font-medium rounded-full transition ${
                  devShowAll
                    ? 'bg-yellow-500 text-white'
                    : 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
                }`}
              >
                {devShowAll ? '🔓 All Visible' : '🔒 Normal View'}
              </button>
            )}
            <span className="text-sm text-gray-500">Preview Report</span>
          </div>
        </div>
      </nav>

      <div className="pt-24 pb-20 px-4">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-10"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-100 text-green-800 rounded-full text-sm font-medium mb-4">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Analysis Complete
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {companyName ? `${companyName}'s AI Opportunity Preview` : 'Your AI Opportunity Preview'}
            </h1>
            <p className="text-gray-600">
              Based on our research and your responses, here's what we found.
            </p>
          </motion.div>

          {/* Score Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-gradient-to-r from-primary-600 to-purple-600 rounded-2xl p-8 text-white mb-8"
          >
            <div className="flex flex-col md:flex-row items-center justify-between gap-6">
              <div>
                <h2 className="text-lg font-medium opacity-90 mb-1">AI Readiness Score</h2>
                <div className="text-6xl font-bold">{previewData?.score}</div>
                <p className="text-sm opacity-75 mt-2">
                  {previewData && previewData.score >= 70
                    ? 'Excellent! High potential for AI automation'
                    : previewData && previewData.score >= 50
                    ? 'Good foundation for AI implementation'
                    : 'Several opportunities identified'}
                </p>
              </div>
              <div className="bg-white/20 rounded-xl p-6 backdrop-blur-sm">
                <div className="text-sm font-medium opacity-90 mb-1">Estimated Annual Savings</div>
                <div className="text-3xl font-bold">{previewData?.estimatedSavings}</div>
                <div className="text-xs opacity-75 mt-1">Based on industry benchmarks</div>
              </div>
            </div>
          </motion.div>

          {/* Industry Insight */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-purple-50 rounded-2xl p-6 border border-purple-100 mb-8"
          >
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-purple-900 mb-1">Industry Insight</h3>
                <p className="text-purple-800">{previewData?.industryInsight}</p>
              </div>
            </div>
          </motion.div>

          {/* Opportunities */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mb-8"
          >
            <h2 className="text-xl font-semibold text-gray-900 mb-4">AI Opportunities Identified</h2>
            <div className="space-y-4">
              {previewData?.opportunities.map((opp, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.4 + index * 0.1 }}
                  className={`bg-white rounded-xl p-5 border border-gray-100 shadow-sm ${
                    opp.blurred && !devShowAll ? 'relative overflow-hidden' : ''
                  }`}
                >
                  {opp.blurred && !devShowAll && (
                    <div className="absolute inset-0 backdrop-blur-sm bg-white/60 flex items-center justify-center z-10">
                      <div className="text-center">
                        <svg className="w-8 h-8 text-gray-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                        <span className="text-sm text-gray-500">Unlock in full report</span>
                      </div>
                    </div>
                  )}
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-semibold text-gray-900">{opp.title}</h3>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          opp.potential === 'High' ? 'bg-green-100 text-green-700' :
                          opp.potential === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {opp.potential} Potential
                        </span>
                      </div>
                      <p className="text-gray-600 text-sm">{opp.description}</p>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-gray-500">Time to value</div>
                      <div className="text-sm font-medium text-gray-900">{opp.timeToValue}</div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Top Recommendation */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-2xl p-6 border border-amber-200 mb-8"
          >
            <div className="flex items-start gap-3">
              <span className="text-2xl">💡</span>
              <div>
                <h3 className="font-semibold text-amber-900 mb-1">Top Recommendation</h3>
                <p className="text-amber-800">{previewData?.topRecommendation}</p>
              </div>
            </div>
          </motion.div>

          {/* What's in the full report */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9 }}
            className="bg-white rounded-2xl p-8 border border-gray-200 mb-8"
          >
            <h2 className="text-xl font-semibold text-gray-900 mb-6 text-center">
              What's in Your Full Report
            </h2>
            <div className="grid md:grid-cols-3 gap-6">
              {[
                { icon: '📊', title: 'Detailed ROI Analysis', desc: 'Transparent calculations with assumptions' },
                { icon: '🛠️', title: 'Vendor Comparisons', desc: 'Real pricing from top AI tools' },
                { icon: '📋', title: 'Implementation Roadmap', desc: 'Step-by-step action plan' },
                { icon: '⚠️', title: 'Risk Assessment', desc: 'What to watch out for' },
                { icon: '🚫', title: '"Don\'t Do This"', desc: 'Common mistakes to avoid' },
                { icon: '🎯', title: 'Priority Matrix', desc: 'Where to start first' },
              ].map((item, i) => (
                <div key={i} className="flex items-start gap-3">
                  <span className="text-2xl">{item.icon}</span>
                  <div>
                    <div className="font-medium text-gray-900">{item.title}</div>
                    <div className="text-sm text-gray-500">{item.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* CTA */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1 }}
            className="bg-white rounded-2xl p-8 border-2 border-primary-200 text-center"
          >
            <div className="text-4xl font-bold text-gray-900 mb-2">€147</div>
            <p className="text-gray-500 mb-6">One-time payment • Includes 90-min AI Workshop</p>

            <button
              onClick={handleGetFullReport}
              className="w-full max-w-md py-4 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition shadow-lg shadow-primary-600/25 text-lg"
            >
              Get Your Full Report →
            </button>

            <p className="text-sm text-gray-500 mt-4">
              14-day money-back guarantee if you're not satisfied
            </p>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
