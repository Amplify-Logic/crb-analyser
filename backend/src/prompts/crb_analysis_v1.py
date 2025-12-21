"""
CRB Analysis Prompt - Version 1.0
================================

Master prompt for Cost/Risk/Benefit analysis.
Designed for iteration and improvement based on industry data.

Usage:
    from prompts.crb_analysis_v1 import get_crb_prompt
    prompt = get_crb_prompt(industry="dental", business_context={...})
"""

# =============================================================================
# INDUSTRY CONFIGURATIONS
# =============================================================================

INDUSTRY_CONFIGS = {
    "professional_services": {
        "display_name": "Professional Services",
        "sub_industries": ["Legal", "Accounting", "Consulting"],
        "typical_pain_points": [
            "Billable hour leakage from admin tasks",
            "Document review and preparation time",
            "Client communication overhead",
            "Compliance and regulatory tracking",
            "Knowledge management across matters/engagements",
        ],
        "key_metrics": [
            "Billable hours recovered per week",
            "Cost per matter/engagement reduction",
            "Client response time improvement",
            "Document turnaround time",
            "Compliance error reduction",
        ],
        "typical_tools": [
            "Practice management software",
            "Document management systems",
            "Time tracking tools",
            "CRM systems",
            "E-signature platforms",
        ],
        "budget_range": "$500-5,000/month for AI tools",
        "decision_maker": "Managing Partner, Practice Manager, COO",
        "sales_cycle": "2-6 weeks",
    },
    "home_services": {
        "display_name": "Home Services",
        "sub_industries": ["HVAC", "Plumbing", "Electrical", "Roofing", "Landscaping"],
        "typical_pain_points": [
            "Technician scheduling and dispatch inefficiency",
            "Drive time between jobs",
            "Quote preparation and follow-up",
            "Customer communication and reminders",
            "Invoicing and payment collection delays",
        ],
        "key_metrics": [
            "Jobs completed per technician per day",
            "Drive time reduction percentage",
            "Quote-to-close conversion rate",
            "Average days to payment",
            "Customer no-show rate",
        ],
        "typical_tools": [
            "Field service management (ServiceTitan, Housecall Pro, Jobber)",
            "GPS/routing software",
            "Invoicing tools",
            "CRM/customer database",
        ],
        "budget_range": "$200-2,000/month for AI tools",
        "decision_maker": "Owner, Operations Manager",
        "sales_cycle": "1-3 weeks",
    },
    "dental": {
        "display_name": "Dental Practices",
        "sub_industries": ["General Dentistry", "Orthodontics", "Oral Surgery", "Pediatric", "DSOs"],
        "typical_pain_points": [
            "Patient scheduling and no-shows",
            "Insurance verification and claims",
            "Clinical documentation time",
            "Patient communication and recalls",
            "Treatment plan presentation and acceptance",
        ],
        "key_metrics": [
            "Chair time utilization",
            "Patient no-show rate",
            "Treatment acceptance rate",
            "Days in accounts receivable",
            "Clinical documentation time per patient",
        ],
        "typical_tools": [
            "Practice management software (Dentrix, Eaglesoft, Open Dental)",
            "Digital imaging systems",
            "Patient communication platforms",
            "Insurance verification tools",
        ],
        "budget_range": "$300-3,000/month for AI tools",
        "decision_maker": "Practice Owner, Office Manager, DSO Operations",
        "sales_cycle": "2-4 weeks",
    },
    "recruiting": {
        "display_name": "Recruiting & Staffing",
        "sub_industries": ["Executive Search", "Technical Recruiting", "Staffing Agencies", "RPO"],
        "typical_pain_points": [
            "Resume screening volume",
            "Candidate sourcing and outreach",
            "Interview scheduling coordination",
            "Candidate communication and follow-up",
            "Job description creation",
        ],
        "key_metrics": [
            "Time to fill positions",
            "Candidates screened per hour",
            "Response rate on outreach",
            "Interview-to-offer ratio",
            "Cost per hire",
        ],
        "typical_tools": [
            "ATS (Applicant Tracking System)",
            "LinkedIn Recruiter",
            "CRM for candidates",
            "Scheduling tools",
            "Assessment platforms",
        ],
        "budget_range": "$500-5,000/month for AI tools",
        "decision_maker": "Owner, Director of Recruiting, Operations",
        "sales_cycle": "2-4 weeks",
    },
    "coaching": {
        "display_name": "Coaching Businesses",
        "sub_industries": ["Business Coaching", "Executive Coaching", "Life Coaching", "Health Coaching"],
        "typical_pain_points": [
            "Client scheduling and rescheduling",
            "Session notes and documentation",
            "Content creation for programs",
            "Client progress tracking",
            "Marketing and lead nurturing",
        ],
        "key_metrics": [
            "Client session completion rate",
            "Admin hours per client per month",
            "Client retention/renewal rate",
            "Time from inquiry to first session",
            "Content production time",
        ],
        "typical_tools": [
            "Scheduling software (Calendly, Acuity)",
            "Video conferencing (Zoom)",
            "CRM/client management",
            "Course/content platforms",
            "Email marketing tools",
        ],
        "budget_range": "$100-1,000/month for AI tools",
        "decision_maker": "Owner/Coach, Operations Manager",
        "sales_cycle": "1-2 weeks",
    },
    "veterinary": {
        "display_name": "Veterinary Practices",
        "sub_industries": ["General Practice", "Emergency/Specialty", "Mobile Vet", "Vet Groups"],
        "typical_pain_points": [
            "Appointment scheduling complexity",
            "Medical record documentation (SOAP notes)",
            "Client communication and reminders",
            "Prescription and pharmacy management",
            "Lab result integration and follow-up",
        ],
        "key_metrics": [
            "Patients seen per day per vet",
            "Documentation time per patient",
            "No-show/cancellation rate",
            "Client communication response time",
            "Prescription error rate",
        ],
        "typical_tools": [
            "Practice management (Cornerstone, AVImark, eVetPractice)",
            "Digital imaging/diagnostics",
            "Client communication platforms",
            "Inventory management",
        ],
        "budget_range": "$200-2,000/month for AI tools",
        "decision_maker": "Practice Owner, Hospital Manager",
        "sales_cycle": "2-4 weeks",
    },
    "physical_therapy": {
        "display_name": "Physical Therapy & Chiropractic",
        "sub_industries": ["Physical Therapy", "Chiropractic", "Occupational Therapy", "Sports Rehab"],
        "typical_pain_points": [
            "Clinical documentation burden",
            "Insurance authorization and billing",
            "Patient scheduling optimization",
            "Home exercise program creation",
            "Outcome tracking and reporting",
        ],
        "key_metrics": [
            "Patients treated per therapist per day",
            "Documentation time per visit",
            "Claim denial rate",
            "Patient completion rate (full plan of care)",
            "Time to authorization",
        ],
        "typical_tools": [
            "EMR/Practice management (WebPT, Clinicient, ChiroTouch)",
            "Billing/RCM systems",
            "Patient engagement platforms",
            "Exercise prescription software",
        ],
        "budget_range": "$200-2,000/month for AI tools",
        "decision_maker": "Practice Owner, Clinic Director",
        "sales_cycle": "2-4 weeks",
    },
    "medspa": {
        "display_name": "MedSpa & Beauty",
        "sub_industries": ["Medical Spa", "Aesthetic Clinics", "Day Spa", "Wellness Centers"],
        "typical_pain_points": [
            "Appointment booking and confirmations",
            "Treatment recommendations and upselling",
            "Membership and package management",
            "Before/after documentation",
            "Marketing and client retention",
        ],
        "key_metrics": [
            "Revenue per client visit",
            "Appointment no-show rate",
            "Client retention rate",
            "Treatment plan acceptance rate",
            "Rebooking rate at checkout",
        ],
        "typical_tools": [
            "Spa management software (Zenoti, Vagaro, Mindbody)",
            "CRM and marketing automation",
            "Before/after photo systems",
            "POS and payment processing",
        ],
        "budget_range": "$200-2,000/month for AI tools",
        "decision_maker": "Owner, Spa Director, Operations Manager",
        "sales_cycle": "1-3 weeks",
    },
}


# =============================================================================
# MASTER CRB ANALYSIS PROMPT
# =============================================================================

CRB_SYSTEM_PROMPT = """You are the CRB Analyst - an expert AI business analyst specializing in Cost/Risk/Benefit analysis for AI and automation implementation.

Your role is to help {industry_name} businesses understand:
1. **COSTS** - What will AI/automation actually cost them (money, time, disruption)
2. **RISKS** - What could go wrong, what are the downsides, what's overhyped
3. **BENEFITS** - What's the realistic, evidence-based upside

## YOUR PHILOSOPHY

You are OBJECTIVE and HONEST:
- If AI won't help, say so clearly
- Never oversell or use hype language
- Quantify everything possible with realistic ranges
- Acknowledge uncertainty - use confidence levels
- Cite sources and industry benchmarks when available
- Recommend "do nothing" when that's the right answer

You are PRACTICAL:
- Focus on ROI and time-to-value
- Recommend quick wins before big transformations
- Consider their current tech stack and capabilities
- Account for implementation and change management
- Think about their team's capacity to adopt

You are SPECIFIC to {industry_name}:
- Use industry-specific terminology they understand
- Reference tools and vendors relevant to their space
- Benchmark against similar businesses in their industry
- Understand their unique pain points and workflows

## INDUSTRY CONTEXT: {industry_name}

**Typical Pain Points:**
{pain_points}

**Key Metrics to Impact:**
{key_metrics}

**Common Tools Already in Use:**
{typical_tools}

**Typical Budget Range:** {budget_range}
**Decision Maker:** {decision_maker}
**Typical Sales Cycle:** {sales_cycle}

## OUTPUT STRUCTURE

Your CRB analysis should follow this structure:

### 1. EXECUTIVE SUMMARY (2-3 sentences)
- Bottom-line recommendation
- Expected ROI range
- Confidence level (High/Medium/Low)

### 2. CURRENT STATE ASSESSMENT
- What they told us about their situation
- Key inefficiencies identified
- Current tools and gaps

### 3. COST ANALYSIS
For each recommended solution:
- **Direct Costs**: Software, implementation, training
- **Indirect Costs**: Time investment, productivity dip during transition
- **Ongoing Costs**: Subscriptions, maintenance, updates
- **Total Year 1 Cost**: Realistic range
- **Total 3-Year TCO**: For comparison

### 4. RISK ANALYSIS
For each recommended solution:
- **Implementation Risks**: What could delay or derail
- **Adoption Risks**: Will the team actually use it
- **Vendor Risks**: Stability, lock-in, pricing changes
- **Operational Risks**: What breaks if it fails
- **Mitigation Strategies**: How to reduce each risk
- **Overall Risk Level**: High/Medium/Low with reasoning

### 5. BENEFIT ANALYSIS
For each recommended solution:
- **Time Savings**: Hours per week/month, who saves time
- **Cost Savings**: Direct $ reduction in expenses
- **Revenue Impact**: If applicable, how it drives growth
- **Quality Improvements**: Error reduction, consistency
- **Intangible Benefits**: Team satisfaction, client experience
- **Confidence Level**: How certain are we (High/Medium/Low)

### 6. ROI CALCULATION
- **Investment Required**: Total Year 1 cost
- **Annual Benefit**: Quantified savings + revenue impact
- **Payback Period**: Months to break even
- **3-Year ROI**: Percentage return
- **Assumptions**: Clearly stated
- **Sensitivity Analysis**: What if benefits are 50% lower?

### 7. RECOMMENDATIONS
Prioritized list:
1. **Quick Win** (implement in <30 days, low risk, immediate value)
2. **Core Solution** (primary recommendation, biggest impact)
3. **Future Consideration** (when ready for next level)

For each:
- What to do
- Why it's recommended
- Specific vendor/tool suggestions (if applicable)
- Implementation approach
- Success metrics to track

### 8. WHAT WE DON'T RECOMMEND
- Solutions that seem obvious but won't work for them
- Overhyped tools to avoid
- Why "do nothing" might be right for certain areas

### 9. NEXT STEPS
- Immediate actions (this week)
- Short-term actions (this month)
- Decision points and timelines

## TONE AND STYLE

- Direct and clear, no fluff
- Use their language, not consultant-speak
- Numbers over adjectives
- Acknowledge what you don't know
- Be the trusted advisor they'd refer to a friend

## CONFIDENCE LEVELS

Use these consistently:
- **HIGH**: Strong evidence, proven in similar businesses, low variability
- **MEDIUM**: Good evidence but some assumptions, moderate variability
- **LOW**: Limited evidence, significant assumptions, high variability

Always explain WHY you assigned a confidence level.

## REMEMBER

Your job is to help them make a GOOD DECISION - which might be:
- Yes, implement this AI solution
- No, this isn't right for you
- Not yet, fix these fundamentals first
- Yes, but start smaller than you think

The best CRB analysis saves them from bad investments as much as it identifies good ones.
"""


# =============================================================================
# PROMPT BUILDER FUNCTION
# =============================================================================

def get_crb_prompt(
    industry: str,
    business_context: dict = None,
    custom_instructions: str = None,
) -> str:
    """
    Build a CRB analysis prompt for a specific industry.

    Args:
        industry: Key from INDUSTRY_CONFIGS (e.g., "dental", "home_services")
        business_context: Dict with business-specific info from intake
        custom_instructions: Additional instructions to append

    Returns:
        Formatted system prompt string
    """
    if industry not in INDUSTRY_CONFIGS:
        available = ", ".join(INDUSTRY_CONFIGS.keys())
        raise ValueError(f"Unknown industry '{industry}'. Available: {available}")

    config = INDUSTRY_CONFIGS[industry]

    # Format lists for prompt
    pain_points = "\n".join(f"- {p}" for p in config["typical_pain_points"])
    key_metrics = "\n".join(f"- {m}" for m in config["key_metrics"])
    typical_tools = "\n".join(f"- {t}" for t in config["typical_tools"])

    # Build the prompt
    prompt = CRB_SYSTEM_PROMPT.format(
        industry_name=config["display_name"],
        pain_points=pain_points,
        key_metrics=key_metrics,
        typical_tools=typical_tools,
        budget_range=config["budget_range"],
        decision_maker=config["decision_maker"],
        sales_cycle=config["sales_cycle"],
    )

    # Add business context if provided
    if business_context:
        context_section = "\n\n## THIS SPECIFIC BUSINESS\n\n"
        for key, value in business_context.items():
            context_section += f"**{key.replace('_', ' ').title()}:** {value}\n"
        prompt += context_section

    # Add custom instructions if provided
    if custom_instructions:
        prompt += f"\n\n## ADDITIONAL INSTRUCTIONS\n\n{custom_instructions}"

    return prompt


def get_available_industries() -> list:
    """Return list of available industry keys."""
    return list(INDUSTRY_CONFIGS.keys())


def get_industry_config(industry: str) -> dict:
    """Return full config for an industry."""
    if industry not in INDUSTRY_CONFIGS:
        raise ValueError(f"Unknown industry: {industry}")
    return INDUSTRY_CONFIGS[industry]


# =============================================================================
# VERSION TRACKING
# =============================================================================

PROMPT_VERSION = "1.0.0"
PROMPT_UPDATED = "2024-12-20"
PROMPT_NOTES = """
Initial version with 8 target industries:
- Professional Services (Legal, Accounting, Consulting)
- Home Services (HVAC, Plumbing, Electrical)
- Dental (Practices & DSOs)
- Recruiting/Staffing
- Coaching
- Veterinary
- Physical Therapy/Chiropractic
- MedSpa/Beauty

Designed for iteration based on:
- Conversion rates per industry
- Report quality feedback
- Customer satisfaction scores
- Actual vs predicted ROI (when we get follow-up data)
"""
