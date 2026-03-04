// ============================================================================
// Ecommerce-Focused Test Data
// Diverse ecommerce sub-types for thorough report quality testing
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
  // ── DTC Fashion & Apparel ──────────────────────────────────────────────
  'ecommerce-fashion': {
    description: 'Growing DTC fashion brand selling sustainable clothing through Shopify. Strong social media presence with expanding product catalog and international EU shipping.',
    businessModel: 'B2C E-commerce',
    employeeRange: '11-25',
    employeeCount: 16,
    annualRevenue: '€2M-5M',
    techStack: ['Shopify Plus', 'Klaviyo', 'Gorgias', 'Yotpo', 'Google Analytics 4'],
    painPoints: ['high cart abandonment rate', 'customer support overwhelm', 'inventory forecasting misses', 'returns processing bottleneck'],
    biggestChallenge: 'Cart abandonment is at 72% and our recovery emails only convert 3% - we\'re leaving massive revenue on the table',
    currentTools: ['Shopify admin', 'Klaviyo for email', 'Excel for inventory planning', 'Gorgias for support tickets'],
    automationExperience: 'Basic email flows in Klaviyo, abandoned cart reminders, but personalization is minimal',
    aiBudget: '10000-25000',
    manualHoursWeekly: 30,
    interview: [
      { role: 'user', content: 'We get 200+ support tickets a day. 60% are "where is my order?" questions that could easily be automated.' },
      { role: 'user', content: 'Our product descriptions are inconsistent - some have great copy, others are just specs. It takes our team a full day to write descriptions for a new collection launch of 40 SKUs.' },
      { role: 'user', content: 'We overstocked winter jackets by 40% last season because our forecasting was just gut feel. That\'s €80K tied up in dead inventory.' },
      { role: 'user', content: 'Returns are killing our margins. 25% return rate and each return takes 15 minutes to process manually. Most returns are size-related — customers can\'t figure out sizing from our product pages.' },
      { role: 'user', content: 'We know personalization drives sales but our product recommendations are just "customers also bought" - nothing truly personalized. Our AOV has been flat at €65 for two years.' },
    ],
    confidenceScores: {
      operations: { score: 90, evidence: ['Ticket volume quantified at 200+/day', 'Return processing time detailed at 15min each'] },
      technology: { score: 80, evidence: ['Modern Shopify Plus stack', 'Clear integration gaps between Klaviyo and Gorgias'] },
      financials: { score: 85, evidence: ['€80K dead inventory quantified', 'Cart abandonment rate and recovery rate specific'] },
      pain_points: { score: 90, evidence: ['Five distinct revenue leaks identified', 'Specific percentages and costs provided'] },
    },
  },

  // ── Health & Supplements ───────────────────────────────────────────────
  'ecommerce-supplements': {
    description: 'Online health supplements brand with subscription model. Sells vitamins, protein powders, and wellness products across DACH region with strong repeat purchase rate.',
    businessModel: 'B2C E-commerce / Subscription',
    employeeRange: '6-15',
    employeeCount: 11,
    annualRevenue: '€1M-3M',
    techStack: ['WooCommerce', 'Mailchimp', 'Zendesk', 'Google Ads', 'Recharge Subscriptions'],
    painPoints: ['subscription churn at 18% monthly', 'regulatory compliance for health claims', 'customer education gaps', 'CAC rising faster than LTV'],
    biggestChallenge: 'We spend €45 to acquire a customer but average LTV is only €120 because churn is so high — people sign up for a month and cancel before month 3',
    currentTools: ['WooCommerce dashboard', 'Mailchimp for newsletters', 'Google Sheets for subscription tracking', 'WhatsApp for VIP customers'],
    automationExperience: 'Post-purchase email sequence and basic subscription renewal reminders. Nothing for churn prevention or win-back.',
    aiBudget: '5000-15000',
    manualHoursWeekly: 22,
    interview: [
      { role: 'user', content: 'We lose 18% of subscribers every month. Most cancel saying "I have too much product" but we have no way to adjust delivery frequency automatically based on usage.' },
      { role: 'user', content: 'Health claim compliance is a nightmare. Every product description needs legal review which takes 2 weeks per SKU. We have 60 products and regulations change quarterly.' },
      { role: 'user', content: 'Our best customers spend €800+/year but we treat them the same as one-time buyers. No personalized bundles, no loyalty program, no VIP experience.' },
      { role: 'user', content: 'Customer questions about dosage and interactions come in constantly. Our support team aren\'t nutritionists — they copy-paste from a FAQ doc that\'s always outdated.' },
      { role: 'user', content: 'Google Ads CPC went up 35% this year. We need to get more value from existing customers instead of always paying for new ones. Our referral program is just a manual discount code.' },
    ],
    confidenceScores: {
      operations: { score: 85, evidence: ['Churn rate quantified at 18%', 'Support workflow described'] },
      technology: { score: 70, evidence: ['WooCommerce + Recharge stack identified', 'Manual tracking via Google Sheets'] },
      financials: { score: 90, evidence: ['CAC €45 and LTV €120 specified', 'CPC increase of 35% noted'] },
      pain_points: { score: 85, evidence: ['Churn root cause identified', 'Compliance bottleneck quantified at 2wk/SKU'] },
    },
  },

  // ── Home & Furniture ───────────────────────────────────────────────────
  'ecommerce-home': {
    description: 'Premium home furniture and decor brand selling through own webshop and marketplaces. High-AOV products requiring visual merchandising and configuration tools.',
    businessModel: 'B2C E-commerce / Omnichannel',
    employeeRange: '15-30',
    employeeCount: 22,
    annualRevenue: '€4M-8M',
    techStack: ['Magento 2', 'HubSpot', 'Freshdesk', 'Channable', 'Pinterest Ads'],
    painPoints: ['long sales cycles for high-ticket items', 'product visualization gaps', 'marketplace feed management chaos', 'delivery logistics complaints'],
    biggestChallenge: 'Our average order is €850 but conversion rate is only 0.8% because customers can\'t visualize products in their space — they visit 6-7 times before buying or abandoning',
    currentTools: ['Magento admin', 'HubSpot CRM', 'Channable for marketplace feeds', 'Excel for delivery scheduling', 'WeTransfer for supplier catalogs'],
    automationExperience: 'HubSpot email sequences for abandoned carts. Channable automates some marketplace listings. Everything else is manual.',
    aiBudget: '15000-40000',
    manualHoursWeekly: 35,
    interview: [
      { role: 'user', content: 'Customers email us 4-5 photos of their living room asking "will this sofa fit?" or "does this match my wall color?" Our team spends 2 hours per inquiry doing manual mockups in Photoshop.' },
      { role: 'user', content: 'We sell on Amazon, bol.com, Otto, and our own shop. Keeping product data consistent across 4 channels is a full-time job. Last month we had wrong prices on bol.com for 3 days — lost €12K in margin.' },
      { role: 'user', content: 'Delivery is our #1 complaint. We promise 2-week delivery but our suppliers are unreliable. Customers call asking for updates and we have to manually check with each supplier.' },
      { role: 'user', content: 'Product photography costs us €200 per SKU. With 300 products and seasonal refreshes, that\'s €60K a year. Lifestyle shots cost even more.' },
      { role: 'user', content: 'Returns on furniture are brutal — 15% return rate and each return costs us €120 in logistics. Most returns say "looked different than expected" which means our product pages aren\'t doing the job.' },
    ],
    confidenceScores: {
      operations: { score: 90, evidence: ['2hr/inquiry for visual requests quantified', 'Delivery complaint root cause identified'] },
      technology: { score: 80, evidence: ['Multi-channel stack described', 'Marketplace feed issues specific'] },
      financials: { score: 95, evidence: ['AOV, conversion rate, photo costs, return costs all quantified', '€12K pricing error documented'] },
      pain_points: { score: 90, evidence: ['Five specific pain points with financial impact', 'Clear connection between visualization gaps and returns'] },
    },
  },

  // ── Food & Specialty Beverages ─────────────────────────────────────────
  'ecommerce-food': {
    description: 'Artisan food and specialty coffee brand with D2C subscription and wholesale. Temperature-sensitive products with strict freshness requirements and seasonal demand spikes.',
    businessModel: 'B2C + B2B E-commerce',
    employeeRange: '8-20',
    employeeCount: 14,
    annualRevenue: '€1.5M-4M',
    techStack: ['Shopify', 'Klaviyo', 'ShipStation', 'QuickBooks', 'Instagram Shopping'],
    painPoints: ['perishable inventory waste', 'seasonal demand unpredictability', 'wholesale order management chaos', 'freshness dating and batch tracking'],
    biggestChallenge: 'We throw away 12% of inventory due to expiration dates — that\'s €150K/year in waste. Our demand forecasting is basically guessing based on last year\'s numbers',
    currentTools: ['Shopify for D2C', 'WhatsApp groups for wholesale orders', 'Excel for batch tracking', 'ShipStation for shipping'],
    automationExperience: 'Klaviyo flows for reorder reminders based on purchase cycle. ShipStation auto-selects carriers. Wholesale is 100% manual via WhatsApp and phone.',
    aiBudget: '8000-20000',
    manualHoursWeekly: 28,
    interview: [
      { role: 'user', content: 'Our wholesale customers order via WhatsApp messages. Someone has to manually type those into Shopify. Last week we shipped 50 cases of the wrong blend because of a copy-paste error.' },
      { role: 'user', content: 'Coffee beans have a 6-week freshness window. We roast based on forecast but when actual orders differ, we either run out of popular blends or waste specialty ones. Last month: €8K in expired single-origins.' },
      { role: 'user', content: 'Christmas is 40% of our revenue but we start production planning in August with zero data. We either overproduce gift sets and eat the loss, or sell out in week 2 and miss the season.' },
      { role: 'user', content: 'Our subscription customers love us — 95% say great things — but 30% of them pause or cancel because they "have too much coffee." We can\'t dynamically adjust delivery frequency.' },
      { role: 'user', content: 'B2B accounts want NET30 invoicing but Shopify only does immediate payment. So we run a parallel invoicing process in QuickBooks that doesn\'t sync with anything. AR management is a nightmare.' },
    ],
    confidenceScores: {
      operations: { score: 95, evidence: ['12% waste rate quantified at €150K/year', 'Wholesale error example documented', 'Seasonal planning timeline specific'] },
      technology: { score: 75, evidence: ['Shopify + manual wholesale stack', 'No inventory management system'] },
      financials: { score: 90, evidence: ['Waste costs, seasonal revenue split, monthly losses all quantified'] },
      pain_points: { score: 95, evidence: ['Five distinct operational bottlenecks', 'Clear financial impact on each'] },
    },
  },

  // ── Beauty & Cosmetics ─────────────────────────────────────────────────
  'ecommerce-beauty': {
    description: 'Clean beauty brand selling skincare and cosmetics direct-to-consumer. Strong Instagram/TikTok presence, influencer-driven acquisition, expanding into EU markets.',
    businessModel: 'B2C E-commerce / DTC',
    employeeRange: '10-20',
    employeeCount: 13,
    annualRevenue: '€2M-6M',
    techStack: ['Shopify Plus', 'Klaviyo', 'Loyalty Lion', 'Okendo Reviews', 'Triple Whale'],
    painPoints: ['shade matching returns', 'influencer ROI tracking chaos', 'product recommendation accuracy', 'EU regulatory expansion complexity'],
    biggestChallenge: 'Our return rate is 22% — mostly shade mismatches and "didn\'t suit my skin type." Each return costs us €18 in shipping plus the product is unsellable. That\'s €200K/year in losses',
    currentTools: ['Shopify Plus admin', 'Klaviyo for email/SMS', 'Google Sheets for influencer tracking', 'Notion for content calendar', 'Triple Whale for attribution'],
    automationExperience: 'Sophisticated Klaviyo flows (welcome, post-purchase, win-back, VIP). LoyaltyLion points program. But product recommendation and shade matching are completely manual.',
    aiBudget: '12000-30000',
    manualHoursWeekly: 25,
    interview: [
      { role: 'user', content: 'Customers message us on Instagram asking "which shade am I?" 80 times a day. Our team responds with "send us a selfie" and manually matches — takes 10 minutes per person and we still get it wrong 30% of the time.' },
      { role: 'user', content: 'We work with 40 influencers but tracking ROI is chaos. We give them unique codes but people buy without codes, share screenshots, or discover us weeks later. We have no idea which influencers actually drive profit.' },
      { role: 'user', content: 'Our skincare routine builder is just a static quiz with 5 questions. It recommends the same 3 products to everyone with dry skin. Customers tell us competitors have AI skin analysis from a photo.' },
      { role: 'user', content: 'We\'re expanding to France and Germany but EU cosmetic regulations require full INCI translations, safety assessments per market, and different claim restrictions. Our product team is drowning in compliance docs.' },
      { role: 'user', content: 'We launch new products monthly but our email list gets the same blast regardless of skin type, purchase history, or preferences. Our open rates dropped from 45% to 22% because of fatigue.' },
    ],
    confidenceScores: {
      operations: { score: 90, evidence: ['80 daily shade-match requests quantified', 'Return rate and cost per return specific'] },
      technology: { score: 85, evidence: ['Advanced Shopify Plus stack', 'Clear gaps in AI/ML capabilities'] },
      financials: { score: 90, evidence: ['€200K/year return losses', 'Email engagement decline quantified'] },
      pain_points: { score: 95, evidence: ['Five specific pain points with clear AI solutions', 'Competitive pressure from AI-enabled rivals'] },
    },
  },

  // ── B2B Industrial Parts (kept for cross-vertical testing) ─────────────
  'ecommerce-b2b': {
    description: 'B2B e-commerce platform selling industrial parts and MRO supplies. Handles complex quoting, bulk orders, and custom pricing tiers for 500+ business accounts.',
    businessModel: 'B2B E-commerce',
    employeeRange: '15-30',
    employeeCount: 24,
    annualRevenue: '€3M-8M',
    techStack: ['Custom React app', 'PostgreSQL', 'Stripe Connect', 'Algolia', 'Segment'],
    painPoints: ['supplier onboarding takes too long', 'catalog quality inconsistent', 'buyer matching inefficiency', 'manual quote aggregation'],
    biggestChallenge: 'Onboarding a new supplier takes 3 weeks of back-and-forth to get their catalog formatted correctly - we lose 40% of interested suppliers before they go live',
    currentTools: ['Custom admin panel', 'Intercom for support', 'Notion for supplier docs', 'Google Sheets for pricing'],
    automationExperience: 'Basic email notifications on orders, but supplier onboarding and catalog management is fully manual',
    aiBudget: '20000-50000',
    manualHoursWeekly: 40,
    interview: [
      { role: 'user', content: 'Each supplier sends their catalog in a different format - PDFs, Excel files, even handwritten lists. Normalizing this data is our biggest bottleneck. We process 50 catalogs a month.' },
      { role: 'user', content: 'Buyers search for parts and get 500 results with no way to know which supplier is best. Our matching is basically keyword search — no understanding of specifications or compatibility.' },
      { role: 'user', content: 'Quote requests go to 10 suppliers but only 3 respond within 24 hours. We spend hours chasing the other 7 on the phone. Buyers get frustrated and go to Amazon Business.' },
      { role: 'user', content: 'Duplicate listings are everywhere. The same bearing appears under 15 different part numbers from different suppliers. Buyers get confused, order wrong, return, and we eat the cost.' },
      { role: 'user', content: 'Our customer success team manually reviews every new supplier application. With 50 applications a week, they can\'t keep up and our approval time is killing growth.' },
    ],
    confidenceScores: {
      operations: { score: 90, evidence: ['Supplier onboarding time quantified at 3 weeks', 'Quote response rate 3/10 documented'] },
      technology: { score: 75, evidence: ['Custom stack described', 'Search limitations acknowledged'] },
      financials: { score: 85, evidence: ['40% supplier drop-off quantified', 'Revenue impact of poor matching implied'] },
      pain_points: { score: 95, evidence: ['Data quality issues across catalog', 'Clear scaling bottleneck'] },
    },
  },
}

// Map old industry keys to new ecommerce sub-types for backwards compatibility
export const INDUSTRY_TO_SUBTYPE: Record<string, string> = {
  'ecommerce': 'ecommerce-fashion',
  'dental': 'ecommerce-supplements', // fallback: health-adjacent
  'b2b-platforms': 'ecommerce-b2b',
  'professional-services': 'ecommerce-home', // fallback: high-AOV complex sales
}

// Model strategies — only models we actually support
export const MODEL_STRATEGIES = [
  { id: 'anthropic_quick', label: 'Claude Sonnet (Quick)', description: 'Fast, cost-effective — Sonnet for generation' },
  { id: 'anthropic_full', label: 'Claude Opus 4.5 (Full)', description: 'Premium quality — Opus for all generation' },
  { id: 'hybrid', label: 'Hybrid (Recommended)', description: 'Haiku extraction → Sonnet generation → Opus analysis' },
] as const

// Ecommerce-focused test companies
export const TEST_COMPANIES = [
  { name: 'Verde Sustainable Fashion', industry: 'ecommerce', subtype: 'ecommerce-fashion', website: 'verdesustainable.com' },
  { name: 'PureVital Supplements', industry: 'ecommerce', subtype: 'ecommerce-supplements', website: 'purevital.de' },
  { name: 'Nordic Living Interiors', industry: 'ecommerce', subtype: 'ecommerce-home', website: 'nordicliving.eu' },
  { name: 'Kaffee Handwerk', industry: 'ecommerce', subtype: 'ecommerce-food', website: 'kaffeehandwerk.de' },
  { name: 'Glow Republic Beauty', industry: 'ecommerce', subtype: 'ecommerce-beauty', website: 'glowrepublic.com' },
  { name: 'PartsBridge Industrial', industry: 'ecommerce', subtype: 'ecommerce-b2b', website: 'partsbridge.io' },
] as const
