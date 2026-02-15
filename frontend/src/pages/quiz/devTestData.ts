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

  'home-services': {
    description: 'Residential and light commercial construction company specializing in renovations, extensions, and new builds. 15 years in business with strong local reputation.',
    businessModel: 'B2C/B2B Services',
    employeeRange: '11-25',
    employeeCount: 18,
    annualRevenue: '\u20AC1.5M-3M',
    techStack: ['BuilderTrend', 'QuickBooks', 'Jobber', 'CoConstruct', 'Housecall Pro'],
    painPoints: ['estimating takes too long', 'job scheduling conflicts', 'material cost tracking', 'customer communication gaps during projects'],
    biggestChallenge: 'Creating accurate estimates takes 4-5 hours per job and we still sometimes get it wrong, eating into profits',
    currentTools: ['Excel for estimates', 'Google Calendar', 'WhatsApp groups with crews'],
    automationExperience: 'Tried a few apps but the lads on site don\'t use them consistently',
    aiBudget: '5000-15000',
    manualHoursWeekly: 30,
    interview: [
      { role: 'user', content: 'Every estimate takes me a full evening. I\'m measuring, calculating materials, checking supplier prices - it\'s exhausting.' },
      { role: 'user', content: 'Last month we had three crews show up at the wrong job. The scheduling mix-up cost us \u20AC2,000 in wasted travel and delays.' },
      { role: 'user', content: 'Customers constantly ask "when will you be done?" and I have no good answer because we don\'t track progress properly.' },
      { role: 'user', content: 'Material costs have gone up 30% but we\'re still quoting based on old prices. By the time we finish a job, our margins are gone.' },
      { role: 'user', content: 'I spend half my Sundays doing invoices instead of being with my family. There has to be a better way.' },
    ],
    confidenceScores: {
      operations: { score: 90, evidence: ['Detailed estimating process described', 'Scheduling issues quantified'] },
      technology: { score: 60, evidence: ['Using basic tools', 'Mentioned failed app adoption'] },
      financials: { score: 80, evidence: ['Material cost impact stated', 'Revenue range clear'] },
      pain_points: { score: 95, evidence: ['Emotional response about work-life balance', 'Specific cost examples'] },
    },
  },

  recruiting: {
    description: 'Boutique recruitment agency specializing in tech and finance placements. Works with both startups and established enterprises across the DACH region.',
    businessModel: 'B2B Services',
    employeeRange: '6-15',
    employeeCount: 12,
    annualRevenue: '\u20AC800K-1.5M',
    techStack: ['Bullhorn', 'LinkedIn Recruiter', 'Greenhouse', 'Lever', 'HireVue'],
    painPoints: ['sourcing quality candidates takes forever', 'candidate ghosting after interviews', 'client relationship management', 'ATS data is a mess'],
    biggestChallenge: 'We spend 70% of our time sourcing, only 30% actually talking to candidates and clients - the ratio should be reversed',
    currentTools: ['Bullhorn ATS', 'LinkedIn Recruiter', 'Gmail', 'Google Sheets for pipeline tracking'],
    automationExperience: 'We have some email sequences in Bullhorn but they feel generic',
    aiBudget: '8000-20000',
    manualHoursWeekly: 35,
    interview: [
      { role: 'user', content: 'I spend 3 hours a day on LinkedIn just trying to find candidates. Boolean searches only get me so far.' },
      { role: 'user', content: 'Our response rate to outreach is maybe 5%. Most candidates ignore our messages because they\'re getting 20 others just like it.' },
      { role: 'user', content: 'We had a perfect candidate ghost us at the final round last week. \u20AC15,000 placement fee gone because we didn\'t nurture the relationship.' },
      { role: 'user', content: 'Client updates are embarrassing - I have to manually check Bullhorn before every call to remember where each search stands.' },
      { role: 'user', content: 'Our database has 50,000 candidates but half the data is outdated. People have moved jobs 3 times since we last spoke.' },
    ],
    confidenceScores: {
      operations: { score: 85, evidence: ['Time allocation breakdown provided', 'Specific metrics on response rates'] },
      technology: { score: 75, evidence: ['Listed ATS and tools', 'Understood limitations'] },
      financials: { score: 80, evidence: ['Placement fee mentioned', 'Revenue impact clear'] },
      pain_points: { score: 90, evidence: ['Quantified lost revenue', 'Emotional frustration evident'] },
    },
  },

  veterinary: {
    description: 'Full-service veterinary hospital offering wellness care, surgery, emergency services, and boarding. Serves companion animals in a busy suburban area.',
    businessModel: 'B2C Healthcare',
    employeeRange: '15-30',
    employeeCount: 22,
    annualRevenue: '\u20AC1M-2.5M',
    techStack: ['eVetPractice', 'Idexx VetLab', 'Covetrus Pulse', 'PetDesk', 'Vetter Software'],
    painPoints: ['prescription refill requests pile up', 'lab result communication delays', 'inventory management chaos', 'after-hours emergency coordination'],
    biggestChallenge: 'Pet owners expect instant communication but our vets are in surgery or consultations - we can\'t respond fast enough',
    currentTools: ['eVetPractice', 'Paper charts for some legacy records', 'Phone calls for everything'],
    automationExperience: 'Appointment reminders are automated, rest is manual',
    aiBudget: '8000-18000',
    manualHoursWeekly: 28,
    interview: [
      { role: 'user', content: 'We get 40+ phone calls a day just for prescription refills. Each one takes 5 minutes because we have to pull records and verify.' },
      { role: 'user', content: 'Lab results sit in our inbox for hours before someone has time to call the owner. Meanwhile they\'re anxiously waiting for news about their pet.' },
      { role: 'user', content: 'Our vaccine reminder system is a joke - we mail postcards. Half get returned, the other half ignored. Revenue walks out the door.' },
      { role: 'user', content: 'Inventory counts don\'t match what we actually have. Last week we had to send a pet home and reschedule surgery because we were out of anesthesia.' },
      { role: 'user', content: 'After-hours emergencies go to an answering service that can\'t help. By the time we call back, the owner went to a competitor.' },
    ],
    confidenceScores: {
      operations: { score: 90, evidence: ['Call volume quantified', 'Specific time per task'] },
      technology: { score: 65, evidence: ['Mixed paper/digital workflow', 'Legacy systems mentioned'] },
      financials: { score: 70, evidence: ['Revenue impact implied', 'Lost client examples'] },
      pain_points: { score: 95, evidence: ['Life-or-death urgency conveyed', 'Multiple concrete examples'] },
    },
  },

  coaching: {
    description: 'Executive and leadership coaching practice working with C-suite leaders and high-potential managers. Combines 1:1 coaching with group workshops.',
    businessModel: 'B2B/B2C Services',
    employeeRange: '3-10',
    employeeCount: 6,
    annualRevenue: '\u20AC400K-800K',
    techStack: ['Calendly', 'Zoom', 'Notion', 'CoachAccountable', 'Kajabi'],
    painPoints: ['session prep takes too long', 'tracking client progress manually', 'content creation for workshops', 'scaling beyond 1:1 sessions'],
    biggestChallenge: 'I can only coach 20 clients at once. To grow revenue, I need to scale but I don\'t want to sacrifice quality.',
    currentTools: ['Calendly', 'Zoom', 'Google Docs for session notes', 'Stripe for payments'],
    automationExperience: 'Calendar booking is automated, but session prep and follow-up is all manual',
    aiBudget: '3000-8000',
    manualHoursWeekly: 15,
    interview: [
      { role: 'user', content: 'Before each session, I spend 30 minutes reviewing notes from our last 5 conversations. I can\'t remember every client\'s journey.' },
      { role: 'user', content: 'My clients want homework and exercises between sessions. Creating personalized materials for 20 people is impossible.' },
      { role: 'user', content: 'I\'ve thought about group programs but the admin of managing 30 people through a 12-week program terrifies me.' },
      { role: 'user', content: 'Clients cancel last-minute constantly. I lose \u20AC500/hour slots because there\'s no consequence for late cancellations.' },
      { role: 'user', content: 'My best insights happen in sessions but I forget to write them down. Two weeks later, I can\'t remember what breakthrough we had.' },
    ],
    confidenceScores: {
      operations: { score: 80, evidence: ['Session prep time detailed', 'Client capacity stated'] },
      technology: { score: 70, evidence: ['Current stack listed', 'Clear gaps identified'] },
      financials: { score: 85, evidence: ['Hourly rate implied', 'Scaling constraints clear'] },
      pain_points: { score: 85, evidence: ['Capacity constraints', 'Quality vs scale tension'] },
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
  { name: 'Nordic Dental Group', industry: 'dental', website: 'nordicdentalgroup.com' },
  { name: 'Green Oak Construction', industry: 'home-services', website: 'greenoakconstruction.com' },
  { name: 'Swift Recruit Partners', industry: 'recruiting', website: 'swiftrecruit.io' },
  { name: 'Cascade Veterinary Clinic', industry: 'veterinary', website: 'cascadevet.com' },
  { name: 'Summit Coaching Academy', industry: 'coaching', website: 'summitcoaching.co' },
  { name: 'Anderson & Partners LLP', industry: 'professional-services', website: 'andersonpartners.com' },
] as const
