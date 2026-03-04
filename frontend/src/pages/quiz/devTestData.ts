// ============================================================================
// Industry-Specific Test Data
// Each industry has unique tech stacks, pain points, and interview responses
// ============================================================================

export interface IndustryTestData {
  description: string
  businessModel: string
  employeeRange: string
  employeeCount: number
  annualRevenue: string
  techStack: string[]
  painPoints: string[]
  biggestChallenge: string
  currentTools: string[]
  automationExperience: string
  aiBudget: string
  manualHoursWeekly: number
  interview: Array<{ role: string; content: string }>
  confidenceScores: Record<string, { score: number; evidence: string[] }>
}

export const industryTestData: Record<string, IndustryTestData> = {
  dental: {
    description: 'Multi-location dental practice offering general dentistry, orthodontics, and cosmetic procedures. Known for family-friendly care and modern treatment techniques.',
    businessModel: 'B2C Healthcare',
    employeeRange: '21-50',
    employeeCount: 35,
    annualRevenue: '\u20AC2M-5M',
    techStack: ['Dentrix', 'Eaglesoft', 'Pearl AI Imaging', 'Weave Communications', 'Open Dental'],
    painPoints: ['patient no-shows costing revenue', 'insurance verification delays', 'treatment plan follow-up gaps', 'recalls and reactivations falling through'],
    biggestChallenge: 'Patients ghost us after consultations - we present a \u20AC3,000 treatment plan and never hear from them again',
    currentTools: ['Dentrix', 'Microsoft Office', 'WhatsApp for patient comms'],
    automationExperience: 'Basic appointment reminders via text, nothing else automated',
    aiBudget: '10000-25000',
    manualHoursWeekly: 25,
    interview: [
      { role: 'user', content: 'We lose about 15-20 patients a week to no-shows. Each missed appointment costs us around \u20AC150 in chair time.' },
      { role: 'user', content: 'Insurance verification is a nightmare - we spend 2 hours every morning on hold with insurance companies before we can confirm coverage.' },
      { role: 'user', content: 'Our treatment acceptance rate is only about 40%. Patients say they\'ll think about it and we never follow up systematically.' },
      { role: 'user', content: 'I wish we had a way to automatically reach out to patients who haven\'t been in for 6 months. Right now we just hope they remember to book.' },
      { role: 'user', content: 'The front desk is overwhelmed - they\'re answering phones, checking in patients, verifying insurance, AND trying to schedule follow-ups all at once.' },
    ],
    confidenceScores: {
      operations: { score: 85, evidence: ['Detailed no-show metrics provided', 'Specific cost per missed appointment'] },
      technology: { score: 70, evidence: ['Listed current tools', 'Mentioned Dentrix usage'] },
      financials: { score: 75, evidence: ['Revenue range provided', 'Cost per no-show calculated'] },
      pain_points: { score: 90, evidence: ['Multiple specific pain points', 'Clear prioritization'] },
    },
  },

  ecommerce: {
    description: 'Growing DTC fashion brand selling sustainable clothing through Shopify. Strong social media presence with expanding product catalog and international shipping.',
    businessModel: 'B2C E-commerce',
    employeeRange: '11-25',
    employeeCount: 16,
    annualRevenue: '\u20AC2M-5M',
    techStack: ['Shopify Plus', 'Klaviyo', 'Gorgias', 'Yotpo', 'Google Analytics 4'],
    painPoints: ['high cart abandonment rate', 'customer support overwhelm', 'inventory forecasting misses', 'returns processing bottleneck'],
    biggestChallenge: 'Cart abandonment is at 72% and our recovery emails only convert 3% - we\'re leaving massive revenue on the table',
    currentTools: ['Shopify admin', 'Klaviyo for email', 'Excel for inventory planning', 'Gorgias for support tickets'],
    automationExperience: 'Basic email flows in Klaviyo, abandoned cart reminders, but personalization is minimal',
    aiBudget: '10000-25000',
    manualHoursWeekly: 30,
    interview: [
      { role: 'user', content: 'We get 200+ support tickets a day. 60% are "where is my order?" questions that could easily be automated.' },
      { role: 'user', content: 'Our product descriptions are inconsistent - some have great copy, others are just specs. It takes our team a full day to write descriptions for a new collection.' },
      { role: 'user', content: 'We overstocked winter jackets by 40% last season because our forecasting was just gut feel. That\'s \u20AC80K tied up in dead inventory.' },
      { role: 'user', content: 'Returns are killing our margins. 25% return rate and each return takes 15 minutes to process manually.' },
      { role: 'user', content: 'We know personalization drives sales but our product recommendations are just "customers also bought" - nothing truly personalized.' },
    ],
    confidenceScores: {
      operations: { score: 90, evidence: ['Ticket volume quantified', 'Return processing time detailed'] },
      technology: { score: 80, evidence: ['Modern stack listed', 'Clear integration gaps identified'] },
      financials: { score: 85, evidence: ['Dead inventory cost quantified', 'Revenue impact of abandonment clear'] },
      pain_points: { score: 90, evidence: ['Multiple revenue leaks identified', 'Specific percentages provided'] },
    },
  },

  'b2b-platforms': {
    description: 'B2B SaaS marketplace connecting suppliers and buyers in the industrial parts sector. Platform handles quoting, ordering, and logistics coordination.',
    businessModel: 'B2B Marketplace',
    employeeRange: '15-30',
    employeeCount: 24,
    annualRevenue: '\u20AC3M-8M',
    techStack: ['Custom React app', 'PostgreSQL', 'Stripe Connect', 'Algolia', 'Segment'],
    painPoints: ['supplier onboarding takes too long', 'catalog quality inconsistent', 'buyer matching inefficiency', 'manual quote aggregation'],
    biggestChallenge: 'Onboarding a new supplier takes 3 weeks of back-and-forth to get their catalog formatted correctly - we lose 40% of interested suppliers',
    currentTools: ['Custom admin panel', 'Intercom for support', 'Notion for supplier docs', 'Google Sheets for tracking'],
    automationExperience: 'Basic email notifications on orders, but supplier onboarding and catalog management is fully manual',
    aiBudget: '20000-50000',
    manualHoursWeekly: 40,
    interview: [
      { role: 'user', content: 'Each supplier sends their catalog in a different format - PDFs, Excel files, even handwritten lists. Normalizing this data is our biggest bottleneck.' },
      { role: 'user', content: 'Buyers search for parts and get 500 results with no way to know which supplier is best for their needs. Our matching is basically keyword search.' },
      { role: 'user', content: 'Quote requests go to 10 suppliers but only 3 respond. We spend hours chasing the other 7 on the phone.' },
      { role: 'user', content: 'Duplicate listings are everywhere. The same part appears under 15 different names from different suppliers. Buyers get confused and leave.' },
      { role: 'user', content: 'Our customer success team manually reviews every new supplier application. With 50 applications a week, they can\'t keep up.' },
    ],
    confidenceScores: {
      operations: { score: 90, evidence: ['Supplier onboarding time quantified', 'Response rate metrics provided'] },
      technology: { score: 75, evidence: ['Custom stack described', 'Search limitations acknowledged'] },
      financials: { score: 85, evidence: ['Supplier churn quantified', 'Revenue impact of poor matching implied'] },
      pain_points: { score: 95, evidence: ['Multiple data quality issues', 'Clear scaling bottlenecks'] },
    },
  },

  'professional-services': {
    description: 'Mid-sized accounting and advisory firm serving SMEs and owner-managed businesses. Offers audit, tax, corporate finance, and business consulting.',
    businessModel: 'B2B Services',
    employeeRange: '25-50',
    employeeCount: 38,
    annualRevenue: '\u20AC3M-6M',
    techStack: ['Xero', 'Sage', 'CCH Axcess', 'Practice Ignition', 'Karbon'],
    painPoints: ['client data chasing every month', 'compliance deadline management', 'knowledge silos between partners', 'scope creep on fixed-fee engagements'],
    biggestChallenge: 'We spend 40% of engagement time chasing clients for documents instead of doing actual advisory work',
    currentTools: ['Xero/Sage integrations', 'Outlook', 'SharePoint', 'Excel for everything else'],
    automationExperience: 'Bank feeds and some reconciliation automated, client comms and workflow still manual',
    aiBudget: '15000-35000',
    manualHoursWeekly: 45,
    interview: [
      { role: 'user', content: 'Our managers send 50 emails a day chasing bank statements, invoices, and receipts. It\'s degrading work for qualified accountants.' },
      { role: 'user', content: 'We missed a VAT deadline last quarter because the reminder got lost in email. \u20AC8,000 penalty for the client, and they blamed us.' },
      { role: 'user', content: 'Every partner has their own way of doing things. When someone\'s on holiday, their clients are stuck waiting.' },
      { role: 'user', content: 'Fixed-fee engagements are killing us. A \u20AC5,000 annual accounts job turns into \u20AC8,000 of work because the client keeps asking questions.' },
      { role: 'user', content: 'I wish we could clone our best partner. He spots tax planning opportunities others miss, but his knowledge is all in his head.' },
    ],
    confidenceScores: {
      operations: { score: 95, evidence: ['Detailed time allocation', 'Specific penalty example'] },
      technology: { score: 75, evidence: ['Listed integrations', 'Clear gaps in workflow tools'] },
      financials: { score: 90, evidence: ['Revenue range provided', 'Scope creep quantified'] },
      pain_points: { score: 95, evidence: ['Multiple partners affected', 'Emotional frustration evident'] },
    },
  },
}

// Model strategies available for testing
export const MODEL_STRATEGIES = [
  { id: 'anthropic_quick', label: 'Claude Sonnet (Quick)', description: 'Fast, cost-effective - Sonnet for generation' },
  { id: 'anthropic_full', label: 'Claude Opus 4.5 (Full)', description: 'Premium quality - Opus 4.5 for all generation' },
  { id: 'opus46_quality', label: 'Claude Opus 4.6 (Ultra)', description: 'Latest & most capable - Opus 4.6 for everything' },
  { id: 'hybrid', label: 'Hybrid (Recommended)', description: 'Haiku \u2192 Sonnet \u2192 Opus pipeline' },
  { id: 'gemini_primary', label: 'Gemini Primary', description: 'Flash drafts, Pro final (1501 Elo)' },
  { id: 'cost_optimized', label: 'Cost Optimized', description: 'Flash \u2192 Sonnet \u2192 Opus (cheapest)' },
  { id: 'multi_provider', label: 'Multi-Provider', description: 'Opus + Gemini Pro + GPT-5.2 validation' },
  { id: 'budget', label: 'Budget (DeepSeek)', description: 'DeepSeek V3 primary (94% cheaper)' },
] as const

export const TEST_COMPANIES = [
  { name: 'Anderson & Partners LLP', industry: 'professional-services', website: 'andersonpartners.com' },
  { name: 'Nordic Dental Group', industry: 'dental', website: 'nordicdentalgroup.com' },
  { name: 'Verde Sustainable Fashion', industry: 'ecommerce', website: 'verdesustainable.com' },
  { name: 'PartsBridge Industrial', industry: 'b2b-platforms', website: 'partsbridge.io' },
] as const
