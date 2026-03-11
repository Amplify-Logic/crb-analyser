import React, { useState, useEffect, useRef, useCallback, Suspense } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { formatCompanyName } from '../lib/formatCompanyName'
import { logger } from '../utils/logger'
import { API_BASE } from '../services/apiClient'
import StoreDataStep from '../components/quiz/StoreDataStep'

const DevModeTestGenerator = React.lazy(() => import('./quiz/DevModeTestGenerator'))

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Map technical research step names to user-friendly descriptions
 */
const formatResearchStep = (step: string): string => {
  if (!step) return 'Initializing research...'

  const stepMappings: Record<string, string> = {
    // Tool names from backend
    'scrape_website': 'Scanning website...',
    'web_search': 'Searching the web...',
    'search_web': 'Searching the web...',
    'search_linkedin': 'Looking up LinkedIn profile...',
    'search_linkedin_company': 'Looking up LinkedIn profile...',
    'search_crunchbase': 'Finding company data...',
    'search_news': 'Finding recent news...',
    'search_company_news': 'Finding recent news...',
    'search_jobs': 'Analyzing job postings...',
    'analyze_tech_stack': 'Analyzing technology stack...',
  }

  // Check if step contains a tool name pattern like "Researching search_company_news..."
  const toolMatch = step.match(/(?:Researching|Executing|Running)\s+(\w+)/i)
  if (toolMatch) {
    const toolName = toolMatch[1].toLowerCase()
    if (stepMappings[toolName]) {
      return stepMappings[toolName]
    }
  }

  // Direct match
  const lowerStep = step.toLowerCase()
  for (const [key, value] of Object.entries(stepMappings)) {
    if (lowerStep.includes(key)) {
      return value
    }
  }

  // Return original if no match (but capitalize nicely)
  return step.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

// ============================================================================
// Types
// ============================================================================

interface ResearchFinding {
  field: string
  value: string | number | string[]
  confidence: 'high' | 'medium' | 'low'
  source?: string
}

// Existing Stack Types (for Connect vs Replace feature)
interface SoftwareOption {
  slug: string
  name: string
  category: string
}

interface ExistingStackItem {
  slug: string
  source: 'selected' | 'free_text'
  name?: string
}

interface DynamicQuestion {
  id: string
  question: string
  type: 'text' | 'textarea' | 'select' | 'multiselect' | 'yes_no' | 'number'
  purpose: 'confirm' | 'clarify' | 'discover' | 'deep_dive'
  rationale: string
  prefilled_value?: string | string[]
  options?: { value: string; label: string }[]
  required: boolean
  section: string
  priority: number
}

interface ResearchResult {
  company_profile: {
    basics?: {
      name?: { value: string; confidence: string }
      description?: { value: string; confidence: string }
      founded_year?: { value: string; confidence: string }
      headquarters?: { value: string; confidence: string }
    }
    size?: {
      employee_count?: { value: number; confidence: string }
      employee_range?: { value: string; confidence: string }
      revenue_estimate?: { value: string; confidence: string }
      funding_raised?: { value: string; confidence: string }
    }
    industry?: {
      primary_industry?: { value: string; confidence: string }
      business_model?: { value: string; confidence: string }
      target_market?: { value: string; confidence: string }
    }
    products?: {
      main_products?: Array<{ value: string; confidence: string }>
      services?: Array<{ value: string; confidence: string }>
      pricing_model?: { value: string; confidence: string }
    }
    tech_stack?: {
      technologies_detected?: Array<{ value: string; confidence: string }>
      platforms_used?: Array<{ value: string; confidence: string }>
    }
    research_quality_score?: number
    sources_used?: string[]
  }
  questionnaire: {
    research_summary: string
    confirmed_facts: Array<{ fact: string; confidence: string }>
    questions: DynamicQuestion[]
    sections: Array<{ id: number; title: string; description: string; question_ids: string[] }>
    total_questions: number
    estimated_time_minutes: number
  }
}

type QuizPhase = 'website' | 'researching' | 'findings' | 'teaser' | 'pricing' | 'email_capture' | 'questions' | 'complete'

// Validate URL format — must look like a domain (contains a dot)
const isValidUrl = (url: string): boolean => {
  const trimmed = url.trim()
  if (trimmed.length < 4) return false
  // Must contain at least one dot to be a valid domain
  const normalized = trimmed.startsWith('http') ? trimmed : `https://${trimmed}`
  try {
    const parsed = new URL(normalized)
    return parsed.hostname.includes('.')
  } catch {
    return false
  }
}

// Helper to format any value (handles objects, arrays, primitives)
const formatValue = (value: unknown): string => {
  if (value === null || value === undefined) return ''
  if (typeof value === 'string') return value
  if (typeof value === 'number') return String(value)
  if (Array.isArray(value)) return value.map(formatValue).join(', ')
  if (typeof value === 'object') {
    // Handle objects like {city: "Amsterdam", country: "Netherlands"}
    const obj = value as Record<string, unknown>
    const parts = Object.values(obj).filter(v => v && typeof v === 'string')
    if (parts.length > 0) return parts.join(', ')
    // Fallback: try to get meaningful values
    return Object.entries(obj)
      .filter(([k, v]) => v && !k.includes('confidence'))
      .map(([_, v]) => formatValue(v))
      .join(', ')
  }
  return String(value)
}

interface TeaserReport {
  ai_readiness_score: number
  score_breakdown: Record<string, { score: number; max: number; factors: string[] }>
  score_interpretation: { level: string; summary: string; recommendation: string }
  revealed_findings: Array<{
    title: string
    category: string
    summary: string
    impact: string
    roi_estimate?: { min: number; max: number; currency: string }
  }>
  blurred_findings: Array<{ title: string; category: string; blurred: boolean }>
  total_findings_available: number
  company_name: string
  industry: string
}

const INDUSTRY_COPY: Record<string, { heading: string; subheading: string }> = {
  ecommerce: {
    heading: "Let's analyze your store",
    subheading: "We'll scan your store, detect your platform and tools, and find where AI can boost revenue and cut costs.",
  },
}

// ============================================================================
// Component
// ============================================================================

export default function Quiz() {
  const navigate = useNavigate()
  const eventSourceRef = useRef<EventSource | null>(null)

  // Core state
  const [phase, setPhase] = useState<QuizPhase>('website')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [sessionError, setSessionError] = useState<string | null>(null)
  const [websiteUrl, setWebsiteUrl] = useState('')
  const [companyName, setCompanyName] = useState('')
  const [userEmail, setUserEmail] = useState('')
  const [emailSubmitting, setEmailSubmitting] = useState(false)
  const [urlIndustry, setUrlIndustry] = useState<string | null>(null)

  // Research state
  const [researchProgress, setResearchProgress] = useState(0)
  const [researchStep, setResearchStep] = useState('')
  const [researchResult, setResearchResult] = useState<ResearchResult | null>(null)
  const [researchError, setResearchError] = useState<string | null>(null)

  // Extracted findings for display
  const [findings, setFindings] = useState<ResearchFinding[]>([])
  const [_gaps, setGaps] = useState<string[]>([])

  // Questions state
  const [questions, setQuestions] = useState<DynamicQuestion[]>([])
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({})

  // Knowledge completeness
  const [knowledgeScore, setKnowledgeScore] = useState(0)

  // Existing Stack State (Connect vs Replace feature)
  const [softwareOptions, setSoftwareOptions] = useState<Record<string, SoftwareOption[]>>({})
  const [softwareCategories, setSoftwareCategories] = useState<string[]>([])
  const [selectedSoftware, setSelectedSoftware] = useState<Set<string>>(new Set())
  const [otherSoftware, setOtherSoftware] = useState('')
  const [existingStackSaved, setExistingStackSaved] = useState(false)

  // Store data collection state
  const [showStoreDataStep, setShowStoreDataStep] = useState(false)
  const [storeDataCompleted, setStoreDataCompleted] = useState(false)

  // Teaser report state (TODO: implement teaser API when backend is ready)
  // Using void to suppress unused setter warning - will be used when teaser API is implemented
  const [teaserReport, setTeaserReport] = useState<TeaserReport | null>(null)
  void setTeaserReport // Suppress unused warning until teaser feature is complete

  // ============================================================================
  // LocalStorage Persistence for Quiz Progress
  // ============================================================================

  const QUIZ_STORAGE_KEY = 'crb_quiz_progress'
  const savedPhaseRef = useRef<QuizPhase | null>(null)

  // Load saved progress on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(QUIZ_STORAGE_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)
        // Only restore if session matches or no session yet
        if (!sessionId || parsed.sessionId === sessionId) {
          if (parsed.answers) setAnswers(parsed.answers)
          if (typeof parsed.currentQuestionIndex === 'number') {
            setCurrentQuestionIndex(parsed.currentQuestionIndex)
          }
          if (parsed.userEmail) setUserEmail(parsed.userEmail)
          if (parsed.companyName) setCompanyName(parsed.companyName)
          if (parsed.selectedSoftware?.length) {
            setSelectedSoftware(new Set(parsed.selectedSoftware))
          }
          if (parsed.otherSoftware) setOtherSoftware(parsed.otherSoftware)
          if (parsed.phase && parsed.phase !== 'website' && parsed.phase !== 'researching') {
            // Store saved phase to apply after session restore
            savedPhaseRef.current = parsed.phase
          }
        }
      }
    } catch (e) {
      logger.warn('Failed to load quiz progress from localStorage:', e)
    }
  }, [])

  // Debounced save to localStorage
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    // Debounce save by 500ms to avoid excessive writes
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current)
    }

    saveTimeoutRef.current = setTimeout(() => {
      try {
        const progress = {
          sessionId,
          phase,
          answers,
          currentQuestionIndex,
          userEmail,
          companyName,
          selectedSoftware: Array.from(selectedSoftware),
          otherSoftware,
          savedAt: new Date().toISOString(),
        }
        localStorage.setItem(QUIZ_STORAGE_KEY, JSON.stringify(progress))
      } catch (e) {
        logger.warn('Failed to save quiz progress to localStorage:', e)
      }
    }, 500)

    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current)
      }
    }
  }, [answers, currentQuestionIndex, userEmail, companyName, sessionId, phase, selectedSoftware, otherSoftware])

  // Clear saved progress on quiz completion
  const clearSavedProgress = useCallback(() => {
    localStorage.removeItem(QUIZ_STORAGE_KEY)
  }, [])

  // ============================================================================
  // Helper Functions (defined before useEffect that uses them)
  // ============================================================================

  const extractFindingsFromProfile = useCallback((profile: ResearchResult['company_profile']) => {
    const extracted: ResearchFinding[] = []
    const missingFields: string[] = []

    // Helper to check if a value is effectively "unknown" or uninformative
    const isUnknownValue = (value: string | undefined | null): boolean => {
      if (!value) return true
      const lower = String(value).toLowerCase().trim()
      const unknownPatterns = [
        'unknown', 'not available', 'not publicly available', 'n/a', 'none',
        'none identified', 'not found', 'not specified', 'undisclosed',
        'no venture capital', 'no funding', 'bootstrapped'
      ]
      return unknownPatterns.some(pattern => lower.includes(pattern))
    }

    // Helper to check if this is a small business (skip irrelevant enterprise fields)
    const isSmallBusiness = (): boolean => {
      const size = profile.size?.employee_range?.value?.toLowerCase() || ''
      return size.includes('1-10') || size.includes('1-5') || size.includes('small') ||
             size.includes('family') || size.includes('solo')
    }

    // Extract basics
    if (profile.basics?.description?.value && !isUnknownValue(profile.basics.description.value)) {
      extracted.push({
        field: 'Company Description',
        value: profile.basics.description.value,
        confidence: profile.basics.description.confidence as 'high' | 'medium' | 'low',
      })
    } else {
      missingFields.push('Company description')
    }

    if (profile.basics?.founded_year?.value && !isUnknownValue(profile.basics.founded_year.value)) {
      extracted.push({
        field: 'Founded',
        value: profile.basics.founded_year.value,
        confidence: profile.basics.founded_year.confidence as 'high' | 'medium' | 'low',
      })
    }

    if (profile.basics?.headquarters?.value && !isUnknownValue(profile.basics.headquarters.value)) {
      extracted.push({
        field: 'Headquarters',
        value: profile.basics.headquarters.value,
        confidence: profile.basics.headquarters.confidence as 'high' | 'medium' | 'low',
      })
    }

    // Extract size
    if (profile.size?.employee_range?.value && !isUnknownValue(profile.size.employee_range.value)) {
      extracted.push({
        field: 'Team Size',
        value: profile.size.employee_range.value,
        confidence: profile.size.employee_range.confidence as 'high' | 'medium' | 'low',
      })
    } else {
      missingFields.push('Team size')
    }

    // Only show revenue if it's a meaningful value (not "unknown" variants)
    if (profile.size?.revenue_estimate?.value && !isUnknownValue(profile.size.revenue_estimate.value)) {
      extracted.push({
        field: 'Revenue',
        value: profile.size.revenue_estimate.value,
        confidence: profile.size.revenue_estimate.confidence as 'high' | 'medium' | 'low',
      })
    }

    // Skip funding for small businesses - it's irrelevant noise
    // Only show if it's a meaningful positive value (actual funding raised)
    if (profile.size?.funding_raised?.value &&
        !isUnknownValue(profile.size.funding_raised.value) &&
        !isSmallBusiness()) {
      extracted.push({
        field: 'Funding',
        value: profile.size.funding_raised.value,
        confidence: profile.size.funding_raised.confidence as 'high' | 'medium' | 'low',
      })
    }

    // Extract industry
    if (profile.industry?.primary_industry?.value) {
      extracted.push({
        field: 'Industry',
        value: profile.industry.primary_industry.value,
        confidence: profile.industry.primary_industry.confidence as 'high' | 'medium' | 'low',
      })
    } else {
      missingFields.push('Industry classification')
    }

    if (profile.industry?.business_model?.value) {
      extracted.push({
        field: 'Business Model',
        value: profile.industry.business_model.value,
        confidence: profile.industry.business_model.confidence as 'high' | 'medium' | 'low',
      })
    } else {
      missingFields.push('Business model')
    }

    // Extract products/services
    if (profile.products?.main_products && profile.products.main_products.length > 0) {
      extracted.push({
        field: 'Products/Services',
        value: profile.products.main_products.map(p => p.value).join(', '),
        confidence: profile.products.main_products[0].confidence as 'high' | 'medium' | 'low',
      })
    } else {
      missingFields.push('Products and services')
    }

    // Extract tech stack
    if (profile.tech_stack?.technologies_detected && profile.tech_stack.technologies_detected.length > 0) {
      extracted.push({
        field: 'Technology Stack',
        value: profile.tech_stack.technologies_detected.map(t => t.value).join(', '),
        confidence: profile.tech_stack.technologies_detected[0].confidence as 'high' | 'medium' | 'low',
      })
    } else {
      missingFields.push('Technology stack')
    }

    // Ecommerce-specific signals
    const detectedIndustry = profile.industry?.primary_industry?.value?.toLowerCase() || ''
    if (detectedIndustry === 'ecommerce' || detectedIndustry === 'e-commerce') {
      // Extract ecommerce platform from tech stack
      const allTech = [
        ...(profile.tech_stack?.technologies_detected || []).map(t => t.value),
        ...(profile.tech_stack?.platforms_used || []).map(p => p.value),
      ]
      const ecommercePlatforms = ['Shopify', 'WooCommerce', 'Magento', 'BigCommerce', 'Squarespace', 'Wix']
      const detectedPlatform = allTech.find(t =>
        ecommercePlatforms.some(p => t.toLowerCase().includes(p.toLowerCase()))
      )
      if (detectedPlatform) {
        extracted.push({
          field: 'Ecommerce Platform',
          value: detectedPlatform,
          confidence: 'high',
        })
      }

      // Detect payment providers
      const paymentProviders = ['Stripe', 'Klarna', 'PayPal', 'Adyen', 'Mollie']
      const detectedPayments = allTech.filter(t =>
        paymentProviders.some(p => t.toLowerCase().includes(p.toLowerCase()))
      )
      if (detectedPayments.length > 0) {
        extracted.push({
          field: 'Payment Providers',
          value: detectedPayments.join(', '),
          confidence: 'medium',
        })
      }

      // Detect sales channels from tech
      const channelIndicators = ['Amazon', 'eBay', 'Etsy', 'Instagram', 'TikTok', 'Facebook']
      const detectedChannels = allTech.filter(t =>
        channelIndicators.some(c => t.toLowerCase().includes(c.toLowerCase()))
      )
      if (detectedChannels.length > 0) {
        extracted.push({
          field: 'Sales Channels Detected',
          value: detectedChannels.join(', '),
          confidence: 'medium',
        })
      }
    }

    // Always need these for a good report
    missingFields.push('Current pain points and challenges')
    missingFields.push('AI/automation experience')
    missingFields.push('Budget and timeline expectations')
    missingFields.push('Success criteria')

    setFindings(extracted)
    setGaps(missingFields)

    // Calculate knowledge score
    const score = Math.min(100, Math.round((extracted.length / 12) * 100))
    setKnowledgeScore(score)
  }, [])

  // ============================================================================
  // Session Management
  // ============================================================================

  useEffect(() => {
    const initSession = async () => {
      try {
        // Check if user wants a fresh start
        const urlParams = new URLSearchParams(window.location.search)
        const forceNew = urlParams.get('new') === 'true'
        const industryParam = urlParams.get('industry')
        if (industryParam) {
          setUrlIndustry(industryParam)
        }

        if (forceNew) {
          // Clear all previous session data
          localStorage.removeItem('crb_session_id')
          sessionStorage.removeItem('quizSessionId')
          sessionStorage.removeItem('quizAnswers')
          sessionStorage.removeItem('researchFindings')
          sessionStorage.removeItem('companyProfile')
          sessionStorage.removeItem('knowledgeScore')
          // Clean up URL — preserve industry param if present
          const cleanUrl = industryParam ? `/quiz?industry=${industryParam}` : '/quiz'
          window.history.replaceState({}, '', cleanUrl)
        }

        // Check for existing session
        const savedSession = localStorage.getItem('crb_session_id')
        if (savedSession && !forceNew) {
          // Verify the session still exists
          const checkResponse = await fetch(`${API_BASE}/api/quiz/sessions/${savedSession}/research/status`)
          if (checkResponse.ok) {
            const data = await checkResponse.json()
            setSessionId(savedSession)

            if (data.status === 'complete' && data.dynamic_questionnaire) {
              // Resume from findings phase
              setCompanyName(data.company_name || '')
              setWebsiteUrl(data.company_website || '')
              setResearchResult({
                company_profile: data.company_profile || {},
                questionnaire: data.dynamic_questionnaire,
              })
              extractFindingsFromProfile(data.company_profile || {})
              setQuestions(data.dynamic_questionnaire.questions || [])
              // Restore to furthest phase if user had progressed beyond findings
              const validResumablePhases: QuizPhase[] = ['findings', 'questions', 'email_capture', 'pricing', 'teaser']
              if (savedPhaseRef.current && validResumablePhases.includes(savedPhaseRef.current)) {
                setPhase(savedPhaseRef.current)
              } else {
                setPhase('findings')
              }
              savedPhaseRef.current = null
            }
            return
          } else {
            // Session no longer valid, clear it
            localStorage.removeItem('crb_session_id')
          }
        }

        // Create new session with temporary email
        const tempEmail = `quiz_${Date.now()}@example.com`
        const response = await fetch(`${API_BASE}/api/quiz/sessions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: tempEmail, tier: 'ai' }),
        })

        if (response.ok) {
          const data = await response.json()
          setSessionId(data.session_id)
          localStorage.setItem('crb_session_id', data.session_id)
        } else {
          logger.error('Failed to create session:', await response.text())
        }
      } catch (error) {
        logger.error('Session init error:', error)
        // Clear bad session data
        localStorage.removeItem('crb_session_id')
        setSessionError('Unable to connect to the server. Please check your connection and try again.')
      }
    }

    initSession()
  }, [])

  // Fetch software options when we have research results with an industry
  useEffect(() => {
    const fetchSoftwareOptions = async () => {
      // Prefer URL industry param (user came from industry page) over research-detected industry
      const industry = urlIndustry || researchResult?.company_profile?.industry?.primary_industry?.value || 'ecommerce'

      try {
        const response = await fetch(
          `${API_BASE}/api/quiz/software-options?industry=${encodeURIComponent(industry)}`
        )
        if (response.ok) {
          const data = await response.json()
          setSoftwareOptions(data.options_by_category || {})
          setSoftwareCategories(data.categories || [])
        }
      } catch (error) {
        logger.error('Failed to fetch software options:', error)
      }
    }

    if (researchResult && phase === 'findings') {
      fetchSoftwareOptions()
    }
  }, [researchResult, phase, urlIndustry])

  // Save existing stack to session
  const saveExistingStack = useCallback(async () => {
    if (!sessionId) return

    const existingStack: ExistingStackItem[] = []

    // Add selected software
    selectedSoftware.forEach(slug => {
      existingStack.push({ slug, source: 'selected' })
    })

    // Add other/custom software
    if (otherSoftware.trim()) {
      otherSoftware.split(',').forEach(name => {
        const trimmed = name.trim()
        if (trimmed) {
          existingStack.push({
            slug: trimmed.toLowerCase().replace(/\s+/g, '-'),
            source: 'free_text',
            name: trimmed
          })
        }
      })
    }

    try {
      const response = await fetch(`${API_BASE}/api/quiz/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ existing_stack: existingStack }),
      })

      if (response.ok) {
        setExistingStackSaved(true)
        logger.log('Saved existing stack:', existingStack.length, 'tools')
      }
    } catch (error) {
      logger.error('Failed to save existing stack:', error)
    }
  }, [sessionId, selectedSoftware, otherSoftware])

  // ============================================================================
  // Research Functions
  // ============================================================================

  const startResearch = useCallback(async () => {
    if (!sessionId || !websiteUrl) return

    setPhase('researching')
    setResearchProgress(0)
    setResearchStep('Initializing research...')
    setResearchError(null)

    try {
      // Normalize URL
      let normalizedUrl = websiteUrl.trim()
      if (!normalizedUrl.startsWith('http')) {
        normalizedUrl = `https://${normalizedUrl}`
      }

      // Start research
      const response = await fetch(`${API_BASE}/api/quiz/sessions/${sessionId}/research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ website_url: normalizedUrl }),
      })

      if (!response.ok) {
        throw new Error('Failed to start research')
      }

      const data = await response.json()
      setCompanyName(data.company_name || '')

      // Connect to SSE stream
      const eventSource = new EventSource(
        `${API_BASE}/api/quiz/sessions/${sessionId}/research/stream`
      )
      eventSourceRef.current = eventSource

      // Timeout: if no progress update in 3 minutes, treat as stalled
      let lastActivityTime = Date.now()
      const RESEARCH_TIMEOUT_MS = 3 * 60 * 1000
      const timeoutInterval = setInterval(() => {
        if (Date.now() - lastActivityTime > RESEARCH_TIMEOUT_MS) {
          clearInterval(timeoutInterval)
          eventSource.close()
          eventSourceRef.current = null
          setResearchError('Research is taking longer than expected. Please try again.')
        }
      }, 10_000)

      eventSource.onmessage = async (event) => {
        lastActivityTime = Date.now()
        try {
          const update = JSON.parse(event.data)

          setResearchProgress(update.progress || 0)
          setResearchStep(update.step || '')

          if (update.status === 'ready' && update.result) {
            clearInterval(timeoutInterval)
            eventSource.close()
            eventSourceRef.current = null

            // Save results
            await fetch(`${API_BASE}/api/quiz/sessions/${sessionId}/research/save`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(update.result),
            })

            setResearchResult(update.result)
            extractFindingsFromProfile(update.result.company_profile || {})

            // Set up dynamic questions
            if (update.result.questionnaire?.questions) {
              setQuestions(update.result.questionnaire.questions)
            }

            setPhase('findings')
          }

          if (update.status === 'failed') {
            clearInterval(timeoutInterval)
            eventSource.close()
            eventSourceRef.current = null
            setResearchError(update.error || 'Research failed')
          }
        } catch (e) {
          logger.error('Parse error:', e)
        }
      }

      eventSource.onerror = () => {
        clearInterval(timeoutInterval)
        eventSource.close()
        eventSourceRef.current = null
        if (researchProgress < 100) {
          setResearchError('Connection lost during research. Please try again.')
        }
      }
    } catch (error) {
      logger.error('Research error:', error)
      setResearchError('Failed to start research. Please try again.')
    }
  }, [sessionId, websiteUrl, extractFindingsFromProfile, researchProgress])

  // Cleanup
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  // ============================================================================
  // Tier Selection
  // ============================================================================

  const handleTierSelect = (tier: 'report_only' | 'report_plus_call') => {
    // Store session data for checkout
    sessionStorage.setItem('quizSessionId', sessionId || '')
    sessionStorage.setItem('selectedTier', tier)
    sessionStorage.setItem('companyName', companyName)
    if (researchResult) {
      sessionStorage.setItem('companyProfile', JSON.stringify(researchResult.company_profile))
    }

    // Clear saved progress before navigating
    clearSavedProgress()

    // Navigate to checkout with tier
    const tierParam = tier === 'report_only' ? 'ai' : 'human'
    navigate(`/checkout?tier=${tierParam}&session_id=${sessionId}`)
  }

  // ============================================================================
  // Question Handling
  // ============================================================================

  const currentQuestion = questions[currentQuestionIndex]

  const handleAnswer = (value: string | string[]) => {
    if (!currentQuestion) return
    setAnswers(prev => ({ ...prev, [currentQuestion.id]: value }))
  }

  const getCurrentAnswer = (): string | string[] => {
    if (!currentQuestion) return ''
    return answers[currentQuestion.id] || (currentQuestion.type === 'multiselect' ? [] : '')
  }

  const canProceed = () => {
    const current = getCurrentAnswer()
    if (!currentQuestion) return false
    if (!currentQuestion.required) return true
    if (currentQuestion.type === 'multiselect') return (current as string[]).length > 0
    return current !== ''
  }

  const handleStoreDataComplete = async (data: {
    source: 'manual_entry' | 'skip'
    store_metrics: { monthly_revenue: string; average_order_value: string; cart_abandonment_rate: string; repeat_customer_rate: string; email_list_size: string }
  }) => {
    try {
      const platform = answers.sales_channels
        ? (Array.isArray(answers.sales_channels) ? answers.sales_channels : []).find(
            (c: string) => ['shopify', 'woocommerce', 'bigcommerce'].includes(c.toLowerCase())
          ) || 'unknown'
        : 'unknown'

      await fetch(`${API_BASE}/api/quiz/sessions/${sessionId}/store-profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source: data.source,
          store_metrics: data.store_metrics,
          platform,
          currency: 'EUR',
          ecommerce_sub_type: (answers.ecommerce_sub_type as string) || '',
          sales_channels: (answers.sales_channels as string[]) || [],
          monthly_orders: answers.monthly_orders ? parseInt(answers.monthly_orders as string) : undefined,
        }),
      })
    } catch (err) {
      logger.warn('Failed to save store profile', { error: err })
      // Non-blocking — continue quiz even if save fails
    }

    setStoreDataCompleted(true)
    setShowStoreDataStep(false)
  }

  const handleNextQuestion = () => {
    // After answering sales_channels, show store data step
    if (currentQuestion?.id === 'sales_channels' && !storeDataCompleted) {
      setShowStoreDataStep(true)
      return
    }

    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1)
    } else {
      // All questions answered
      finishQuiz()
    }
  }

  const handlePrevQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1)
    }
  }

  const finishQuiz = () => {
    // Calculate final knowledge score
    const researchScore = findings.length * 8
    const questionScore = Object.keys(answers).length * 5
    const finalScore = Math.min(100, researchScore + questionScore)
    setKnowledgeScore(finalScore)

    // Save to session storage for checkout
    sessionStorage.setItem('quizSessionId', sessionId || '')
    sessionStorage.setItem('quizAnswers', JSON.stringify(answers))
    sessionStorage.setItem('researchFindings', JSON.stringify(findings))
    sessionStorage.setItem('knowledgeScore', String(finalScore))

    if (researchResult) {
      sessionStorage.setItem('companyProfile', JSON.stringify(researchResult.company_profile))
    }

    setPhase('complete')
  }

  // ============================================================================
  // Render: Website Entry Phase
  // ============================================================================

  if (phase === 'website') {
    return (
      <div className="min-h-screen bg-white selection:bg-primary-100 selection:text-primary-900">
        {/* Background elements */}
        <div className="fixed inset-0 bg-mesh-light opacity-60 pointer-events-none" />
        {/* Navigation */}
        <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200">
          <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center text-white shadow-lg shadow-primary-500/30">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div className="flex flex-col">
                <span className="text-xl font-bold text-gray-900 tracking-tight leading-tight">Ready<span className="text-primary-600">Path</span></span>
                <span className="text-[10px] text-gray-400 font-medium -mt-0.5">by Amplify Logic AI</span>
              </div>
            </Link>
          </div>
        </nav>

        <div className="relative pt-28 pb-20 px-4 flex items-center justify-center min-h-screen">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className="max-w-xl w-full relative z-10"
          >
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-primary-100 to-primary-200 rounded-2xl mb-4 shadow-lg shadow-primary-500/20">
                <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3 tracking-tight">
                {INDUSTRY_COPY['ecommerce'].heading}
              </h1>
              <p className="text-gray-600 text-lg">
                {INDUSTRY_COPY['ecommerce'].subheading}
              </p>
            </div>

            <div className="rounded-2xl border border-gray-200 bg-white p-8">
              <label htmlFor="company-website" className="block text-sm font-medium text-gray-700 mb-2">
                Your store website
              </label>
              <input
                id="company-website"
                type="text"
                value={websiteUrl}
                onChange={(e) => setWebsiteUrl(e.target.value)}
                placeholder="www.yourstore.com"
                className="w-full px-4 py-4 text-lg border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all bg-white"
                onKeyDown={(e) => e.key === 'Enter' && isValidUrl(websiteUrl) && startResearch()}
              />

              <div className="mt-4 p-4 bg-gradient-to-br from-gray-50 to-primary-50/30 rounded-xl border border-gray-100">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-primary-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="text-sm text-gray-600">
                    <p className="font-medium text-gray-900 mb-1">What we'll look for:</p>
                    <ul className="space-y-1">
                      <li>• Company size, industry & business model</li>
                      <li>• Products, services & pricing</li>
                      <li>• Technology stack & tools</li>
                      <li>• Recent news & growth signals</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Inline validation message */}
              {websiteUrl.trim().length > 0 && !isValidUrl(websiteUrl) && (
                <p className="mt-2 text-sm text-amber-600">
                  Please enter a valid website URL (e.g. www.yourcompany.com)
                </p>
              )}

              {sessionError ? (
                <div className="mt-6">
                  <p className="text-sm text-red-600 mb-3">{sessionError}</p>
                  <button
                    onClick={() => {
                      setSessionError(null)
                      window.location.reload()
                    }}
                    className="w-full py-4 font-semibold rounded-xl text-lg bg-accent-500 hover:bg-accent-600 text-white hover:shadow-lg transition-all"
                  >
                    Retry Connection
                  </button>
                </div>
              ) : isValidUrl(websiteUrl) && sessionId ? (
                <button
                  onClick={startResearch}
                  className="w-full mt-6 py-4 font-semibold rounded-xl text-lg bg-accent-500 hover:bg-accent-600 text-white hover:shadow-lg transition-all"
                >
                  Start Research →
                </button>
              ) : (
                <button
                  disabled
                  className="w-full mt-6 py-4 font-semibold rounded-xl text-lg bg-gray-200 text-gray-400 cursor-not-allowed"
                >
                  {!sessionId ? 'Connecting...' : 'Start Research'}
                </button>
              )}
            </div>

            {/* Start fresh option */}
            <div className="text-center mt-6">
              <button
                onClick={() => {
                  localStorage.removeItem('crb_session_id')
                  window.location.reload()
                }}
                className="text-sm text-gray-500 hover:text-gray-700 transition"
              >
                Start a new analysis
              </button>
            </div>

            {/* DEV MODE: Generate test report */}
            {import.meta.env.DEV && (
              <Suspense fallback={null}>
                <DevModeTestGenerator navigate={navigate} />
              </Suspense>
            )}
          </motion.div>
        </div>
      </div>
    )
  }

  // ============================================================================
  // Render: Researching Phase
  // ============================================================================

  if (phase === 'researching') {
    const researchSteps = [
      { label: 'Scanning your store', icon: '🌐', done: researchProgress >= 20, active: researchProgress > 0 && researchProgress < 20 },
      { label: 'Researching your brand', icon: '💼', done: researchProgress >= 40, active: researchProgress >= 20 && researchProgress < 40 },
      { label: 'Finding news & updates', icon: '📰', done: researchProgress >= 60, active: researchProgress >= 40 && researchProgress < 60 },
      { label: 'Detecting your stack', icon: '⚙️', done: researchProgress >= 80, active: researchProgress >= 60 && researchProgress < 80 },
      { label: 'Building your questions', icon: '✨', done: researchProgress >= 95, active: researchProgress >= 80 && researchProgress < 95 },
    ]

    return (
      <div className="min-h-screen bg-white flex items-center justify-center px-4 selection:bg-primary-100 selection:text-primary-900">
        {/* Background elements - consistent with landing */}
        <div className="fixed inset-0 bg-mesh-light opacity-60 pointer-events-none" />
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="max-w-md w-full relative"
        >
          <div className="bg-white rounded-3xl p-8 shadow-depth border border-gray-200">
            {researchError ? (
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="text-center"
              >
                <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-red-50 to-rose-100 rounded-2xl flex items-center justify-center shadow-lg shadow-red-500/10">
                  <svg className="w-10 h-10 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">Research Failed</h2>
                <p className="text-gray-500 mb-6">{researchError}</p>
                <button
                  onClick={() => { setPhase('website'); setResearchError(null); }}
                  className="px-8 py-3 bg-accent-500 hover:bg-accent-600 text-white font-semibold rounded-xl hover:shadow-lg transition-all duration-300"
                >
                  Try Again
                </button>
              </motion.div>
            ) : (
              <>
                {/* Animated Icon */}
                <div className="relative w-28 h-28 mx-auto mb-8">
                  {/* Outer glow ring */}
                  <motion.div
                    animate={{
                      scale: [1, 1.15, 1],
                      opacity: [0.3, 0.1, 0.3],
                    }}
                    transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                    className="absolute inset-0 bg-gradient-to-r from-primary-400 to-primary-500 rounded-full blur-xl"
                  />
                  {/* Middle ring */}
                  <motion.div
                    animate={{
                      scale: [1, 1.08, 1],
                      opacity: [0.5, 0.2, 0.5],
                    }}
                    transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut", delay: 0.2 }}
                    className="absolute inset-2 bg-gradient-to-br from-primary-300 to-primary-400 rounded-full"
                  />
                  {/* Inner circle with icon */}
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
                    className="absolute inset-4 bg-gradient-to-br from-primary-700 to-primary-900 rounded-full shadow-lg"
                  />
                  <div className="absolute inset-5 bg-white rounded-full flex items-center justify-center shadow-inner">
                    <motion.svg
                      className="w-10 h-10 text-primary-700"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      animate={{ scale: [1, 1.1, 1] }}
                      transition={{ duration: 2, repeat: Infinity }}
                    >
                      <circle cx="11" cy="11" r="8" strokeWidth={2} />
                      <motion.path
                        strokeLinecap="round"
                        strokeWidth={2}
                        d="M21 21l-4.35-4.35"
                        animate={{ pathLength: [0, 1, 0] }}
                        transition={{ duration: 1.5, repeat: Infinity }}
                      />
                    </motion.svg>
                  </div>
                </div>

                {/* Title & Status */}
                <div className="text-center mb-8">
                  <h2 className="text-2xl font-bold text-gray-900 mb-1">
                    {companyName ? (
                      <>Analyzing <span className="text-accent-600 font-bold">{formatCompanyName(companyName)}</span></>
                    ) : (
                      'Analyzing your company'
                    )}
                  </h2>
                  <motion.p
                    key={researchStep}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-gray-500 text-sm mt-2"
                  >
                    {formatResearchStep(researchStep)}
                  </motion.p>
                </div>

                {/* Progress Section */}
                <div className="mb-8">
                  {/* Progress bar */}
                  <div className="relative h-2 bg-gray-100 rounded-full overflow-hidden mb-3">
                    <motion.div
                      className="absolute inset-y-0 left-0 bg-gradient-to-r from-accent-400 via-accent-500 to-accent-600 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${researchProgress}%` }}
                      transition={{ duration: 0.5, ease: "easeOut" }}
                    />
                    {/* Shimmer effect */}
                    <motion.div
                      className="absolute inset-y-0 w-20 bg-gradient-to-r from-transparent via-white/40 to-transparent"
                      animate={{ x: [-80, 400] }}
                      transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                    />
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-400 uppercase tracking-wider font-medium">Progress</span>
                    <span className="text-sm font-semibold text-accent-600">{researchProgress}%</span>
                  </div>
                </div>

                {/* Steps */}
                <div className="space-y-3">
                  {researchSteps.map((step, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className={`flex items-center gap-4 p-3 rounded-xl transition-all duration-300 ${
                        step.done
                          ? 'bg-green-50/80'
                          : step.active
                            ? 'bg-accent-50 ring-1 ring-accent-200'
                            : 'bg-gray-50/50'
                      }`}
                    >
                      {/* Status indicator */}
                      <div className={`relative w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-300 ${
                        step.done
                          ? 'bg-gradient-to-br from-green-400 to-emerald-500 shadow-md shadow-green-500/20'
                          : step.active
                            ? 'bg-gradient-to-br from-accent-400 to-accent-500 shadow-md shadow-accent-500/20'
                            : 'bg-gray-200'
                      }`}>
                        {step.done ? (
                          <motion.svg
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            className="w-4 h-4 text-white"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                          </motion.svg>
                        ) : step.active ? (
                          <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                            className="w-4 h-4 border-2 border-white border-t-transparent rounded-full"
                          />
                        ) : (
                          <span className="text-sm grayscale opacity-50">{step.icon}</span>
                        )}
                      </div>

                      {/* Label */}
                      <span className={`flex-1 text-sm font-medium transition-colors ${
                        step.done
                          ? 'text-green-700'
                          : step.active
                            ? 'text-accent-700'
                            : 'text-gray-400'
                      }`}>
                        {step.label}
                      </span>

                      {/* Status text */}
                      {step.done && (
                        <motion.span
                          initial={{ opacity: 0, scale: 0.8 }}
                          animate={{ opacity: 1, scale: 1 }}
                          className="text-xs text-green-600 font-medium"
                        >
                          Done
                        </motion.span>
                      )}
                      {step.active && (
                        <motion.span
                          animate={{ opacity: [1, 0.5, 1] }}
                          transition={{ duration: 1.5, repeat: Infinity }}
                          className="text-xs text-accent-600 font-medium"
                        >
                          In progress...
                        </motion.span>
                      )}
                    </motion.div>
                  ))}
                </div>

                {/* Footer note */}
                <p className="text-center text-xs text-gray-400 mt-6">
                  This usually takes 30-60 seconds
                </p>
              </>
            )}
          </div>
        </motion.div>
      </div>
    )
  }

  // ============================================================================
  // Render: Findings Phase - Redesigned for clarity
  // ============================================================================

  if (phase === 'findings') {
    // Extract key company info for display
    const profile = researchResult?.company_profile
    const description = profile?.basics?.description?.value || ''
    const detectedIndustry = profile?.industry?.primary_industry?.value?.toLowerCase() || ''

    // Industry-specific verified stats for the value hook
    // All stats verified against actual source URLs
    const industryHooks: Record<string, { stat: string; source: string; sourceUrl: string; cta: string }> = {
      'ecommerce': {
        stat: 'AI-powered product recommendations drive up to 35% of e-commerce revenue',
        source: 'McKinsey Digital Commerce',
        sourceUrl: 'https://www.mckinsey.com/capabilities/growth-marketing-and-sales/our-insights/the-value-of-getting-personalization-right-or-wrong-is-multiplying',
        cta: 'Complete the interview to find your revenue growth opportunities'
      },
      'b2b-platforms': {
        stat: 'B2B companies using AI see 50% more leads and 60% lower costs',
        source: 'Harvard Business Review',
        sourceUrl: 'https://hbr.org/2023/04/how-b2b-businesses-can-get-ai-right',
        cta: 'Complete the interview to find your platform growth opportunities'
      }
    }

    // Industry-specific hook (may be null if industry not recognized)
    const industryHook = industryHooks[detectedIndustry] || null

    // General stat that always applies
    const generalHook = {
      stat: '88% of organizations now use AI regularly — is yours capturing full value?',
      source: 'McKinsey State of AI 2026',
      sourceUrl: 'https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai',
      cta: 'Complete the interview to discover your specific opportunities'
    }

    const nextSteps = [
      {
        num: 1,
        title: 'AI-powered interview',
        description: 'Quick conversation to understand your pain points, goals, and priorities',
        active: true,
        icon: '💬'
      },
      {
        num: 2,
        title: 'See your AI Readiness Score',
        description: 'Get an instant preview of your top opportunities for automation',
        active: false,
        icon: '📊'
      },
      {
        num: 3,
        title: '90-minute AI workshop',
        description: 'Deep-dive session to gather the context needed for an impactful report',
        active: false,
        icon: '🎯'
      },
      {
        num: 4,
        title: 'Receive your full report',
        description: 'Personalized AI analysis with actionable recommendations, delivered within 24-48 hours',
        active: false,
        icon: '📋'
      }
    ]

    return (
      <div className="min-h-screen bg-white selection:bg-primary-100 selection:text-primary-900">
        {/* Background elements - consistent with landing */}
        <div className="fixed inset-0 bg-mesh-light opacity-60 pointer-events-none" />
        {/* Navigation */}
        <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200">
          <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center text-white shadow-lg shadow-primary-500/30">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div className="flex flex-col">
                <span className="text-xl font-bold text-gray-900 tracking-tight leading-tight">Ready<span className="text-primary-600">Path</span></span>
                <span className="text-[10px] text-gray-400 font-medium -mt-0.5">by Amplify Logic AI</span>
              </div>
            </Link>
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-2 text-sm font-medium text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-full"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", delay: 0.3 }}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
              </motion.div>
              Research complete
            </motion.div>
          </div>
        </nav>

        <div className="relative pt-28 pb-20 px-4">
          <div className="max-w-2xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              {/* Success Header */}
              <div className="text-center mb-10">
                {/* Animated Success Icon */}
                <div className="relative w-24 h-24 mx-auto mb-8">
                  <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
                    className="absolute inset-0"
                  >
                    {/* Outer glow */}
                    <motion.div
                      animate={{ scale: [1, 1.1, 1], opacity: [0.3, 0.1, 0.3] }}
                      transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                      className="absolute inset-0 bg-gradient-to-r from-emerald-400 to-teal-400 rounded-full blur-xl"
                    />
                    {/* Middle ring */}
                    <div className="absolute inset-2 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-full shadow-lg shadow-emerald-500/30" />
                    {/* Inner white circle with checkmark */}
                    <div className="absolute inset-4 bg-white rounded-full flex items-center justify-center shadow-inner">
                      <motion.svg
                        className="w-10 h-10 text-emerald-500"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        initial={{ pathLength: 0 }}
                        animate={{ pathLength: 1 }}
                        transition={{ delay: 0.5, duration: 0.5 }}
                      >
                        <motion.path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2.5}
                          d="M5 13l4 4L19 7"
                          initial={{ pathLength: 0 }}
                          animate={{ pathLength: 1 }}
                          transition={{ delay: 0.5, duration: 0.5 }}
                        />
                      </motion.svg>
                    </div>
                  </motion.div>
                </div>

                <motion.h1
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4"
                >
                  Great news, <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-600 to-teal-600">{formatCompanyName(companyName)}</span>!
                </motion.h1>
                <motion.p
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                  className="text-lg text-gray-500 max-w-md mx-auto"
                >
                  We've gathered enough information to create your personalized AI opportunity analysis.
                </motion.p>
              </div>

              {/* Value Hook Teasers */}
              <div className="space-y-3 mb-6">
                {/* Industry-specific stat (if available) */}
                {industryHook && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.45 }}
                    className="bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200/50 rounded-2xl p-4 flex items-center gap-4"
                  >
                    <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg shadow-emerald-500/20">
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-emerald-800">
                        {industryHook.stat}
                      </p>
                      <a
                        href={industryHook.sourceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[10px] text-emerald-500/70 hover:text-emerald-600 hover:underline mt-1 inline-block"
                      >
                        Source: {industryHook.source} ↗
                      </a>
                    </div>
                  </motion.div>
                )}

                {/* General stat (always shown) */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: industryHook ? 0.55 : 0.45 }}
                  className="bg-blue-50 border border-blue-200/50 rounded-2xl p-4 flex items-center gap-4"
                >
                  <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg shadow-blue-500/20">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-blue-800">
                      {generalHook.stat}
                    </p>
                    <p className="text-xs text-blue-600 mt-0.5">
                      {generalHook.cta}
                    </p>
                    <a
                      href={generalHook.sourceUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[10px] text-blue-500/70 hover:text-blue-600 hover:underline mt-1 inline-block"
                    >
                      Source: {generalHook.source} ↗
                    </a>
                  </div>
                </motion.div>
              </div>

              {/* Research Findings - Prominent Display */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="bg-white rounded-3xl p-6 shadow-card border border-gray-200 mb-6"
              >
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-primary-800 rounded-xl flex items-center justify-center shadow-md">
                      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="font-bold text-gray-900">What we discovered</h3>
                      <p className="text-sm text-gray-500">{findings.length} insights gathered</p>
                    </div>
                  </div>
                  <div className="group relative">
                    <span className={`text-sm font-bold px-3 py-1 rounded-full cursor-help ${
                      knowledgeScore >= 60
                        ? 'text-emerald-700 bg-emerald-100'
                        : knowledgeScore >= 30
                          ? 'text-amber-700 bg-amber-100'
                          : 'text-orange-700 bg-orange-100'
                    }`}>
                      {knowledgeScore >= 60 ? 'Good coverage' : knowledgeScore >= 30 ? 'Basic coverage' : 'Building profile'}
                    </span>
                    <div className="absolute right-0 top-full mt-2 w-64 p-3 bg-gray-900 text-white text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 shadow-xl">
                      <p className="font-medium mb-1">{knowledgeScore}% of profile complete</p>
                      <p className="text-gray-300">
                        {knowledgeScore >= 60
                          ? "We have enough to generate valuable insights. The interview will fill in the rest."
                          : "The AI interview will gather the remaining context needed for a personalized analysis."}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Findings Grid */}
                <div className="space-y-2">
                  {findings.map((finding, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.6 + i * 0.05 }}
                      className="flex items-start gap-3 p-3 rounded-xl bg-gray-50/80 hover:bg-gray-100/80 transition-colors"
                    >
                      <div className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-100 flex items-center justify-center mt-0.5">
                        <svg className="w-3.5 h-3.5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-xs text-gray-400 uppercase tracking-wider font-medium mb-0.5">{finding.field}</div>
                        <div className="text-sm font-medium text-gray-900">{formatValue(finding.value)}</div>
                      </div>
                    </motion.div>
                  ))}
                </div>

                {/* Description if available */}
                {description && (
                  <div className="mt-4 pt-4 border-t border-gray-100">
                    <div className="text-xs text-gray-400 uppercase tracking-wider font-medium mb-2">Company Overview</div>
                    <p className="text-sm text-gray-600 leading-relaxed">{formatValue(description)}</p>
                  </div>
                )}
              </motion.div>

              {/* What happens next */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
                className="bg-primary-50 rounded-3xl p-6 border border-primary-200 mb-8"
              >
                <h3 className="font-bold text-gray-900 mb-5 flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-primary-800 flex items-center justify-center shadow-md">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  What happens next
                </h3>

                <div className="space-y-3">
                  {nextSteps.map((step, i) => (
                    <motion.div
                      key={step.num}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.7 + i * 0.1 }}
                      className={`flex gap-4 p-4 rounded-2xl transition-all duration-300 ${
                        step.active
                          ? 'bg-white shadow-lg ring-1 ring-primary-200'
                          : 'bg-white/50'
                      }`}
                    >
                      <div className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm transition-all ${
                        step.active
                          ? 'bg-primary-800 text-white shadow-md'
                          : 'bg-gray-100 text-gray-400'
                      }`}>
                        {step.num}
                      </div>
                      <div className="flex-1">
                        <div className={`font-semibold mb-0.5 transition-colors ${step.active ? 'text-gray-900' : 'text-gray-400'}`}>
                          {step.title}
                        </div>
                        <div className={`text-sm transition-colors ${step.active ? 'text-gray-600' : 'text-gray-400'}`}>
                          {step.description}
                        </div>
                      </div>
                      {step.active && (
                        <motion.div
                          animate={{ scale: [1, 1.1, 1] }}
                          transition={{ duration: 2, repeat: Infinity }}
                          className="flex-shrink-0 w-8 h-8 rounded-lg bg-accent-100 flex items-center justify-center"
                        >
                          <span className="text-lg">{step.icon}</span>
                        </motion.div>
                      )}
                    </motion.div>
                  ))}
                </div>
              </motion.div>

              {/* Existing Stack Question - Connect vs Replace */}
              {softwareCategories.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.7 }}
                  className="bg-white rounded-3xl p-6 shadow-card border border-gray-200 mb-6"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-xl flex items-center justify-center shadow-md shadow-blue-500/20">
                      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="font-bold text-gray-900">What software do you currently use?</h3>
                      <p className="text-sm text-gray-500">We'll show you how to automate your existing tools</p>
                    </div>
                  </div>

                  {/* Software Categories */}
                  <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
                    {softwareCategories.map(category => (
                      <div key={category}>
                        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                          {category}
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {(softwareOptions[category] || []).map(option => {
                            const isSelected = selectedSoftware.has(option.slug)
                            return (
                              <button
                                key={option.slug}
                                onClick={() => {
                                  setSelectedSoftware(prev => {
                                    const next = new Set(prev)
                                    if (next.has(option.slug)) {
                                      next.delete(option.slug)
                                    } else {
                                      next.add(option.slug)
                                    }
                                    return next
                                  })
                                  setExistingStackSaved(false)
                                }}
                                className={`px-3 py-1.5 text-sm rounded-lg border transition-all ${
                                  isSelected
                                    ? 'bg-blue-100 border-blue-300 text-blue-700 font-medium'
                                    : 'bg-white border-gray-200 text-gray-700 hover:border-gray-300 hover:bg-gray-50'
                                }`}
                              >
                                {isSelected && (
                                  <span className="mr-1">✓</span>
                                )}
                                {option.name}
                              </button>
                            )
                          })}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Other/Custom Software Input */}
                  <div className="mt-4 pt-4 border-t border-gray-100">
                    <label htmlFor="other-software" className="block text-sm font-medium text-gray-700 mb-2">
                      Other software not listed?
                    </label>
                    <input
                      id="other-software"
                      type="text"
                      value={otherSoftware}
                      onChange={(e) => {
                        setOtherSoftware(e.target.value)
                        setExistingStackSaved(false)
                      }}
                      placeholder="e.g., CustomPMS, Internal Tool (comma-separated)"
                      className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  {/* Selection Summary */}
                  {(selectedSoftware.size > 0 || otherSoftware.trim()) && (
                    <div className="mt-4 p-3 bg-blue-50 rounded-xl">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-blue-700">
                          <span className="font-semibold">{selectedSoftware.size + (otherSoftware.trim() ? otherSoftware.split(',').filter(s => s.trim()).length : 0)}</span> tools selected
                        </span>
                        {existingStackSaved && (
                          <span className="text-xs text-green-600 flex items-center gap-1">
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            Saved
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </motion.div>
              )}

              {/* Time estimate */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.9 }}
                className="text-center mb-6"
              >
                <div className="inline-flex items-center gap-2 text-sm text-gray-500 bg-white px-4 py-2.5 rounded-full border border-gray-200 shadow-sm">
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="font-medium">Takes about 5-10 minutes</span>
                </div>
              </motion.div>

              {/* Primary CTA - Go to AI Interview */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 1 }}
                className="text-center"
              >
                <motion.button
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={async () => {
                    // Save existing stack if user selected any tools
                    if (selectedSoftware.size > 0 || otherSoftware.trim()) {
                      await saveExistingStack()
                    }
                    // Save session data for interview
                    sessionStorage.setItem('quizSessionId', sessionId || '')
                    sessionStorage.setItem('companyName', companyName)
                    if (researchResult) {
                      sessionStorage.setItem('companyProfile', JSON.stringify(researchResult.company_profile))
                    }
                    // Navigate to AI interview
                    navigate(`/quiz/interview?session_id=${sessionId}`)
                  }}
                  className="group w-full sm:w-auto px-10 py-4 bg-accent-500 hover:bg-accent-600 text-white font-semibold rounded-2xl hover:shadow-xl transition-all duration-300 text-lg flex items-center justify-center gap-3 mx-auto"
                >
                  Start AI Interview
                  <motion.svg
                    className="w-5 h-5 transition-transform group-hover:translate-x-1"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </motion.svg>
                </motion.button>

                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 1.1 }}
                  className="mt-4 text-sm text-gray-400 flex items-center justify-center gap-2"
                >
                  <span className="flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    5-7 quick questions
                  </span>
                  <span className="text-gray-300">•</span>
                  <span className="text-emerald-500 font-medium">Free</span>
                  <span className="text-gray-300">•</span>
                  <span>No payment required</span>
                </motion.p>
              </motion.div>

            </motion.div>
          </div>
        </div>
      </div>
    )
  }

  // ============================================================================
  // Render: Teaser Phase (AI Readiness Score + 2 Findings)
  // ============================================================================

  if (phase === 'teaser' && teaserReport) {
    const score = teaserReport.ai_readiness_score
    const scoreColor = score >= 70 ? 'text-green-600' : score >= 40 ? 'text-yellow-600' : 'text-red-600'
    const scoreBgColor = score >= 70 ? 'from-green-500 to-emerald-600' : score >= 40 ? 'from-yellow-500 to-orange-500' : 'from-red-500 to-rose-600'

    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-primary-50">
        <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200">
          <div className="max-w-6xl mx-auto px-4 py-4">
            <Link to="/" className="flex flex-col">
              <span className="text-xl font-bold text-gray-900 leading-tight">Ready<span className="text-primary-600">Path</span></span>
              <span className="text-[10px] text-gray-400 font-medium -mt-0.5">by Amplify Logic AI</span>
            </Link>
          </div>
        </nav>

        <div className="pt-24 pb-20 px-4">
          <div className="max-w-3xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              {/* Score Header */}
              <div className="text-center mb-8">
                <h1 className="text-2xl font-bold text-gray-900 mb-4">
                  Your AI Readiness Score
                </h1>

                {/* Big Score Circle */}
                <div className={`inline-flex items-center justify-center w-40 h-40 rounded-full bg-gradient-to-br ${scoreBgColor} shadow-2xl mb-4`}>
                  <div className="bg-white rounded-full w-32 h-32 flex items-center justify-center">
                    <span className={`text-5xl font-bold ${scoreColor}`}>{score}</span>
                  </div>
                </div>

                <p className={`text-xl font-semibold ${scoreColor} mb-2`}>
                  {teaserReport.score_interpretation.level}
                </p>
                <p className="text-gray-600 max-w-md mx-auto">
                  {teaserReport.score_interpretation.summary}
                </p>
              </div>

              {/* Score Breakdown */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 mb-6">
                <h3 className="font-semibold text-gray-900 mb-4">Score Breakdown</h3>
                <div className="space-y-4">
                  {Object.entries(teaserReport.score_breakdown).map(([key, data]) => (
                    <div key={key}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-700 capitalize">{key.replace(/_/g, ' ')}</span>
                        <span className="font-medium text-gray-900">{data.score}/{data.max}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-primary-600 h-2 rounded-full transition-all"
                          style={{ width: `${(data.score / data.max) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Revealed Findings */}
              <div className="mb-6">
                <h3 className="font-semibold text-gray-900 mb-4">Your Top Opportunities</h3>
                <div className="space-y-4">
                  {teaserReport.revealed_findings.map((finding, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <h4 className="font-semibold text-gray-900">{finding.title}</h4>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          finding.impact === 'high' ? 'bg-green-100 text-green-700' :
                          finding.impact === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {finding.impact} impact
                        </span>
                      </div>
                      <p className="text-gray-600 mb-3">{finding.summary}</p>
                      {finding.roi_estimate && (
                        <div className="flex items-center gap-2 text-green-600 font-semibold">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Potential: €{finding.roi_estimate.min.toLocaleString()} - €{finding.roi_estimate.max.toLocaleString()}/year
                        </div>
                      )}
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* Blurred Findings Preview */}
              {teaserReport.blurred_findings.length > 0 && (
                <div className="mb-8">
                  <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                    {teaserReport.blurred_findings.length} More Findings in Full Report
                  </h3>
                  <div className="space-y-3">
                    {teaserReport.blurred_findings.map((finding, index) => (
                      <div
                        key={index}
                        className="bg-gray-100 rounded-xl p-4 relative overflow-hidden"
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/60 to-transparent backdrop-blur-sm" />
                        <div className="relative blur-[2px] select-none">
                          <h4 className="font-medium text-gray-700">{finding.title}</h4>
                          <p className="text-sm text-gray-500 mt-1">Detailed analysis with ROI calculations...</p>
                        </div>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="bg-primary-600 text-white text-xs font-medium px-3 py-1 rounded-full">
                            Unlock in full report
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* CTA to Pricing */}
              <div className="text-center">
                <p className="text-gray-600 mb-4">
                  Unlock your complete report with {teaserReport.total_findings_available}+ findings, implementation roadmap, and vendor recommendations.
                </p>
                <button
                  onClick={() => setPhase('pricing')}
                  className="px-8 py-4 bg-accent-500 text-white font-semibold rounded-xl hover:bg-accent-600 transition shadow-lg text-lg"
                >
                  Get Full Report →
                </button>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    )
  }

  // ============================================================================
  // Render: Pricing Phase
  // ============================================================================

  if (phase === 'pricing') {
    const reportOnlyFeatures = [
      '15-20 AI opportunities analyzed',
      'Honest verdicts: Go / Caution / Wait / No',
      'Real vendor pricing (not guesses)',
      'ROI calculations with visible assumptions',
      'Three options per recommendation',
      '"Don\'t do this" section included',
      '90-minute AI workshop interview',
    ]

    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-primary-50">
        <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200">
          <div className="max-w-6xl mx-auto px-4 py-4">
            <Link to="/" className="flex flex-col">
              <span className="text-xl font-bold text-gray-900 leading-tight">Ready<span className="text-primary-600">Path</span></span>
              <span className="text-[10px] text-gray-400 font-medium -mt-0.5">by Amplify Logic AI</span>
            </Link>
          </div>
        </nav>

        <div className="pt-24 pb-20 px-4">
          <div className="max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              {/* Header */}
              <div className="text-center mb-12">
                <h1 className="text-3xl font-bold text-gray-900 mb-4">
                  Choose Your Report Package
                </h1>
                <p className="text-lg text-gray-600">
                  Both options include the full AI analysis. Add expert guidance if you need it.
                </p>
              </div>

              {/* Pricing Cards */}
              <div className="grid md:grid-cols-2 gap-8 max-w-3xl mx-auto">
                {/* Tier 1: Report Only */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="bg-white rounded-3xl p-8 shadow-lg border border-gray-200"
                >
                  <div className="text-center mb-6">
                    <div className="inline-block px-4 py-1 bg-gray-100 text-gray-700 rounded-full text-sm font-medium mb-4">
                      Readiness Report
                    </div>
                    <div className="flex items-baseline justify-center gap-2 mb-2">
                      <span className="text-4xl font-bold text-gray-900">€147</span>
                      <span className="text-gray-500">one-time</span>
                    </div>
                    <p className="text-gray-500 text-sm">
                      Self-service analysis
                    </p>
                  </div>

                  <ul className="space-y-3 mb-8">
                    {reportOnlyFeatures.map((feature, index) => (
                      <li key={index} className="flex items-center gap-3">
                        <svg className="w-5 h-5 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span className="text-gray-700 text-sm">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <button
                    onClick={() => handleTierSelect('report_only')}
                    className="w-full py-3 border-2 border-gray-300 text-gray-700 font-semibold rounded-xl hover:border-gray-400 hover:bg-gray-50 transition text-lg"
                  >
                    Get Report Only
                  </button>
                </motion.div>

                {/* Tier 2: Report + Call (Recommended) */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="bg-white rounded-3xl p-8 shadow-xl border-2 border-primary-500 relative"
                >
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <span className="bg-primary-600 text-white text-sm font-medium px-4 py-1 rounded-full">
                      Most Popular
                    </span>
                  </div>

                  <div className="text-center mb-6">
                    <div className="inline-block px-4 py-1 bg-primary-100 text-primary-700 rounded-full text-sm font-medium mb-4">
                      Readiness Report + Strategy Call
                    </div>
                    <div className="flex items-baseline justify-center gap-2 mb-2">
                      <span className="text-4xl font-bold text-gray-900">€497</span>
                      <span className="text-gray-500">one-time</span>
                    </div>
                    <p className="text-gray-500 text-sm">
                      Expert-guided analysis
                    </p>
                  </div>

                  <ul className="space-y-3 mb-8">
                    {reportOnlyFeatures.map((feature, index) => (
                      <li key={index} className="flex items-center gap-3">
                        <svg className="w-5 h-5 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span className="text-gray-700 text-sm">{feature}</span>
                      </li>
                    ))}
                    <li className="flex items-center gap-3 pt-2 border-t border-gray-100">
                      <svg className="w-5 h-5 text-primary-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-gray-900 font-medium text-sm">60-minute strategy call with expert</span>
                    </li>
                    <li className="flex items-center gap-3">
                      <svg className="w-5 h-5 text-primary-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-gray-900 font-medium text-sm">Live Q&A on your specific situation</span>
                    </li>
                  </ul>

                  <button
                    onClick={() => handleTierSelect('report_plus_call')}
                    className="w-full py-3 bg-accent-500 text-white font-semibold rounded-xl hover:bg-accent-600 transition shadow-lg text-lg"
                  >
                    Get Report + Strategy Call
                  </button>
                </motion.div>
              </div>

              <p className="text-center text-sm text-gray-500 mt-8">
                14-day money-back guarantee on both options.
              </p>

              {/* Back button */}
              <div className="text-center mt-6">
                <button
                  onClick={() => setPhase('teaser')}
                  className="text-gray-500 hover:text-gray-700 text-sm"
                >
                  ← Back to your score
                </button>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    )
  }

  // ============================================================================
  // Render: Email Capture Phase
  // ============================================================================

  if (phase === 'email_capture') {
    const detectedIndustry = researchResult?.company_profile?.industry?.primary_industry?.value || ''

    const handleEmailSubmit = async (e: React.FormEvent) => {
      e.preventDefault()
      if (!userEmail || !sessionId) return

      setEmailSubmitting(true)
      try {
        // Save email to session via API
        const response = await fetch(`${API_BASE}/api/quiz/sessions/${sessionId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: userEmail,
            industry: detectedIndustry,
          }),
        })

        if (!response.ok) {
          throw new Error('Failed to save email')
        }

        // Save to session storage for checkout
        sessionStorage.setItem('userEmail', userEmail)
        sessionStorage.setItem('companyProfile', JSON.stringify(researchResult?.company_profile || {}))
        sessionStorage.setItem('quizSessionId', sessionId)
        sessionStorage.setItem('companyName', companyName)

        // Navigate to voice interview
        navigate(`/quiz/interview?session_id=${sessionId}`)
      } catch (error) {
        logger.error('Email save error:', error)
        // Still proceed even if save fails
        navigate(`/quiz/interview?session_id=${sessionId}`)
      } finally {
        setEmailSubmitting(false)
      }
    }

    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-primary-50">
        <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200">
          <div className="max-w-6xl mx-auto px-4 py-4">
            <Link to="/" className="flex flex-col">
              <span className="text-xl font-bold text-gray-900 leading-tight">Ready<span className="text-primary-600">Path</span></span>
              <span className="text-[10px] text-gray-400 font-medium -mt-0.5">by Amplify Logic AI</span>
            </Link>
          </div>
        </nav>

        <div className="pt-24 pb-20 px-4 flex items-center justify-center min-h-screen">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-md w-full"
          >
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-2xl mb-4">
                <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                Save your progress
              </h1>
              <p className="text-gray-600">
                Enter your email to save your analysis and receive your personalized report.
              </p>
            </div>

            <form onSubmit={handleEmailSubmit} className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
              <label htmlFor="work-email" className="block text-sm font-medium text-gray-700 mb-2">
                Work email
              </label>
              <input
                id="work-email"
                type="email"
                value={userEmail}
                onChange={(e) => setUserEmail(e.target.value)}
                placeholder="you@company.com"
                required
                className="w-full px-4 py-4 text-lg border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent mb-4"
              />

              {detectedIndustry && (
                <div className="mb-6 p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Industry detected:</span> {detectedIndustry}
                  </p>
                </div>
              )}

              <button
                type="submit"
                disabled={!userEmail || emailSubmitting}
                className={`w-full py-4 font-semibold rounded-xl transition text-lg flex items-center justify-center gap-2 ${
                  userEmail && !emailSubmitting
                    ? 'bg-accent-500 text-white hover:bg-accent-600 shadow-lg'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                }`}
              >
                {emailSubmitting ? (
                  <>
                    <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Saving...
                  </>
                ) : 'Continue to Interview'}
              </button>

              <p className="text-xs text-gray-500 text-center mt-4">
                We'll send your report here. No spam, ever.
              </p>
            </form>

            {/* Skip option - goes to form instead */}
            <button
              onClick={() => setPhase('questions')}
              className="w-full mt-4 text-sm text-gray-500 hover:text-gray-700"
            >
              Skip and answer questions manually instead
            </button>
          </motion.div>
        </div>
      </div>
    )
  }

  // ============================================================================
  // Render: Questions Phase
  // ============================================================================

  if (phase === 'questions' && currentQuestion) {
    const progress = ((currentQuestionIndex + 1) / questions.length) * 100

    return (
      <div className="min-h-screen bg-gray-50">
        <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200">
          <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
            <Link to="/" className="flex flex-col">
              <span className="text-xl font-bold text-gray-900 leading-tight">Ready<span className="text-primary-600">Path</span></span>
              <span className="text-[10px] text-gray-400 font-medium -mt-0.5">by Amplify Logic AI</span>
            </Link>
            <div className="text-sm text-gray-500">
              Question {currentQuestionIndex + 1} of {questions.length}
            </div>
          </div>
        </nav>

        {/* Progress bar */}
        <div className="fixed top-16 left-0 right-0 h-1 bg-gray-200 z-40">
          <motion.div
            className="h-full bg-primary-600"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>

        <div className="pt-24 pb-20 px-4">
          <div className="max-w-2xl mx-auto">
            {/* Store data collection step — shows after ecommerce questions answered */}
            {showStoreDataStep && !storeDataCompleted ? (
              <StoreDataStep
                currency="EUR"
                onComplete={handleStoreDataComplete}
                onBack={() => setShowStoreDataStep(false)}
              />
            ) : (
            <AnimatePresence mode="wait">
              <motion.div
                key={currentQuestion.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
              >
                {/* Question purpose badge */}
                <div className="mb-4">
                  <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                    currentQuestion.purpose === 'confirm' ? 'bg-yellow-100 text-yellow-800' :
                    currentQuestion.purpose === 'clarify' ? 'bg-blue-100 text-blue-800' :
                    currentQuestion.purpose === 'discover' ? 'bg-primary-100 text-primary-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {currentQuestion.purpose === 'confirm' ? 'Confirming our research' :
                     currentQuestion.purpose === 'clarify' ? 'Need more detail' :
                     currentQuestion.purpose === 'discover' ? 'Can\'t find publicly' :
                     'Deep dive'}
                  </span>
                </div>

                <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
                  <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                    {currentQuestion.question}
                  </h2>
                  {currentQuestion.rationale && (
                    <p className="text-gray-500 text-sm mb-6">{currentQuestion.rationale}</p>
                  )}

                  {/* Text input */}
                  {currentQuestion.type === 'text' && (
                    <input
                      type="text"
                      value={getCurrentAnswer() as string}
                      onChange={(e) => handleAnswer(e.target.value)}
                      placeholder="Type your answer..."
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent text-lg"
                    />
                  )}

                  {/* Textarea */}
                  {currentQuestion.type === 'textarea' && (
                    <textarea
                      value={getCurrentAnswer() as string}
                      onChange={(e) => handleAnswer(e.target.value)}
                      placeholder="Type your answer..."
                      rows={4}
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent text-lg resize-none"
                    />
                  )}

                  {/* Number */}
                  {currentQuestion.type === 'number' && (
                    <input
                      type="number"
                      value={getCurrentAnswer() as string}
                      onChange={(e) => handleAnswer(e.target.value)}
                      placeholder="Enter a number..."
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent text-lg"
                    />
                  )}

                  {/* Yes/No */}
                  {currentQuestion.type === 'yes_no' && (
                    <div className="flex gap-4">
                      {['Yes', 'No'].map((opt) => (
                        <button
                          key={opt}
                          onClick={() => handleAnswer(opt.toLowerCase())}
                          className={`flex-1 p-4 rounded-xl border-2 transition font-medium ${
                            getCurrentAnswer() === opt.toLowerCase()
                              ? 'border-primary-600 bg-primary-50 text-primary-700'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Select */}
                  {currentQuestion.type === 'select' && currentQuestion.options && (
                    <div className="space-y-3">
                      {currentQuestion.options.map((opt) => (
                        <button
                          key={opt.value}
                          onClick={() => handleAnswer(opt.value)}
                          className={`w-full p-4 text-left rounded-xl border-2 transition ${
                            getCurrentAnswer() === opt.value
                              ? 'border-primary-600 bg-primary-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <span className="font-medium text-gray-900">{opt.label}</span>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Multiselect */}
                  {currentQuestion.type === 'multiselect' && currentQuestion.options && (
                    <div className="space-y-3">
                      {currentQuestion.options.map((opt) => {
                        const selected = (getCurrentAnswer() as string[]).includes(opt.value)
                        return (
                          <button
                            key={opt.value}
                            onClick={() => {
                              const current = getCurrentAnswer() as string[]
                              handleAnswer(
                                selected
                                  ? current.filter(v => v !== opt.value)
                                  : [...current, opt.value]
                              )
                            }}
                            className={`w-full p-4 text-left rounded-xl border-2 transition flex items-center gap-3 ${
                              selected ? 'border-primary-600 bg-primary-50' : 'border-gray-200 hover:border-gray-300'
                            }`}
                          >
                            <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                              selected ? 'border-primary-600 bg-primary-600' : 'border-gray-300'
                            }`}>
                              {selected && (
                                <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                </svg>
                              )}
                            </div>
                            <span className="font-medium text-gray-900">{opt.label}</span>
                          </button>
                        )
                      })}
                    </div>
                  )}

                  {/* Prefilled hint */}
                  {currentQuestion.prefilled_value && (
                    <div className="mt-4 p-3 bg-blue-50 rounded-xl">
                      <p className="text-sm text-blue-800">
                        <span className="font-medium">From our research: </span>
                        {Array.isArray(currentQuestion.prefilled_value)
                          ? currentQuestion.prefilled_value.join(', ')
                          : currentQuestion.prefilled_value}
                      </p>
                    </div>
                  )}
                </div>

                {/* Navigation */}
                <div className="flex justify-between mt-6">
                  <button
                    onClick={handlePrevQuestion}
                    disabled={currentQuestionIndex === 0}
                    className={`px-6 py-3 font-medium rounded-xl transition ${
                      currentQuestionIndex === 0
                        ? 'text-gray-400 cursor-not-allowed'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    Back
                  </button>
                  <button
                    onClick={handleNextQuestion}
                    disabled={!canProceed()}
                    className={`px-8 py-3 font-semibold rounded-xl transition ${
                      canProceed()
                        ? 'bg-accent-500 text-white hover:bg-accent-600'
                        : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    {currentQuestionIndex === questions.length - 1 ? 'Finish' : 'Continue'}
                  </button>
                </div>
              </motion.div>
            </AnimatePresence>
            )}
          </div>
        </div>
      </div>
    )
  }

  // ============================================================================
  // Render: Complete Phase
  // ============================================================================

  if (phase === 'complete') {
    return (
      <div className="min-h-screen bg-gray-50">
        <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200">
          <div className="max-w-6xl mx-auto px-4 py-4">
            <Link to="/" className="flex flex-col">
              <span className="text-xl font-bold text-gray-900 leading-tight">Ready<span className="text-primary-600">Path</span></span>
              <span className="text-[10px] text-gray-400 font-medium -mt-0.5">by Amplify Logic AI</span>
            </Link>
          </div>
        </nav>

        <div className="pt-24 pb-20 px-4">
          <div className="max-w-3xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center"
            >
              <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-2xl mb-6">
                <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>

              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                We have everything we need!
              </h1>

              {/* Knowledge completeness */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 mb-8 max-w-md mx-auto">
                <div className="flex items-center justify-between mb-3">
                  <span className="font-medium text-gray-700">Knowledge Completeness</span>
                  <span className="text-2xl font-bold text-green-600">{knowledgeScore}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-green-500 h-3 rounded-full"
                    style={{ width: `${knowledgeScore}%` }}
                  />
                </div>
                <p className="text-sm text-gray-500 mt-3">
                  {knowledgeScore >= 70
                    ? 'Excellent! We have comprehensive data for a high-quality report.'
                    : knowledgeScore >= 50
                    ? 'Good foundation. Your report will include actionable insights.'
                    : 'We have enough to get started. Your answers filled crucial gaps.'}
                </p>
              </div>

              {/* What's in the report */}
              <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 mb-8 text-left">
                <h3 className="font-semibold text-gray-900 mb-4">Your report will include:</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  {[
                    { icon: '🎯', title: 'AI Opportunities', desc: 'Specific use cases for your store' },
                    { icon: '💰', title: 'ROI Projections', desc: 'Cost savings and efficiency gains' },
                    { icon: '🛠️', title: 'Tool Recommendations', desc: 'Real vendors with pricing' },
                    { icon: '📋', title: 'Implementation Roadmap', desc: 'Step-by-step action plan' },
                    { icon: '⚠️', title: 'Risk Assessment', desc: 'What to watch out for' },
                    { icon: '🚫', title: '"Don\'t Do This"', desc: 'AI traps to avoid' },
                  ].map((item, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
                      <span className="text-2xl">{item.icon}</span>
                      <div>
                        <div className="font-medium text-gray-900">{item.title}</div>
                        <div className="text-sm text-gray-500">{item.desc}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* CTA */}
              <div className="bg-white rounded-2xl p-8 shadow-sm border-2 border-primary-200">
                <div className="text-4xl font-bold text-gray-900 mb-2">€147</div>
                <p className="text-gray-500 mb-6">One-time payment • Delivered within 24 hours</p>

                <button
                  onClick={() => navigate('/checkout?tier=ai')}
                  className="w-full py-4 bg-accent-500 text-white font-semibold rounded-xl hover:bg-accent-600 transition shadow-lg text-lg"
                >
                  Get Your Report →
                </button>

                <p className="text-sm text-gray-500 mt-4">
                  14-day money-back guarantee if you're not satisfied
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    )
  }

  // Fallback
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin w-8 h-8 border-4 border-accent-500 border-t-transparent rounded-full" />
    </div>
  )
}
