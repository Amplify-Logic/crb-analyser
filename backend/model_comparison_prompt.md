# Model Comparison Prompt - CRB Report Generation

**Test Date:** December 25, 2025
**Purpose:** Compare GPT-5.2, Gemini 3 Pro, and Claude Opus 4.5 for CRB report generation

---

## SYSTEM PROMPT

```
You are an expert AI business analyst specializing in operational efficiency for service businesses.
You provide actionable, specific recommendations based on evidence and industry benchmarks.
Your analysis is professional, clear, and focuses on ROI and practical implementation.
```

---

## USER PROMPT (Full Version)

Copy this entire block:

```
You are analyzing a home services HVAC company for AI/automation opportunities.

Generate a comprehensive CRB (Cost/Risk/Benefit) analysis with:
1. Executive summary with AI readiness score (0-100)
2. 8-12 findings across efficiency, growth, and customer experience categories
3. 3 "not recommended" items (things they should NOT do)
4. Specific vendor recommendations with pricing

FULL QUIZ DATA:
{
  "company_name": "ComfortAir HVAC Services",
  "website": "https://comfortairhvac.com",
  "industry": "home-services",
  "company_size": "11-50",
  "annual_revenue": "1.5M-3M (approx €2M)",
  "employee_count": "25",
  "technician_count": "15",
  "office_staff_count": "10",

  "pain_points": ["scheduling", "customer_communication", "lead_management", "invoicing", "technician_efficiency"],
  "biggest_time_waste": "Manually scheduling technicians and handling customer callbacks",
  "hours_wasted_weekly": "25",

  "current_tools": ["quickbooks", "google_calendar", "excel", "paper_forms"],
  "using_fsm_software": "basic",
  "fsm_software_name": "Basic Google Calendar + spreadsheets",

  "jobs_per_day": "15-25",
  "average_job_value": "€350",
  "service_area_miles": "50",
  "call_volume_daily": "40-60",
  "missed_call_percentage": "25%",
  "lead_response_time": "2-4 hours",

  "customer_follow_up": "manual",
  "review_collection": "rarely",
  "repeat_customer_rate": "35%",

  "quote_creation_time": "20-30 minutes",
  "quote_to_close_rate": "45%",
  "invoicing_method": "manual",
  "payment_collection_days": "30-45",

  "ai_tools_used": ["chatgpt_basic"],
  "technology_comfort": "7/10",
  "ai_budget": "€5,000-15,000",
  "ai_goals": ["reduce_admin_time", "improve_customer_response", "grow_revenue", "better_scheduling"],
  "timeline_preference": "3-6 months",

  "team_tech_savvy": "6/10",
  "training_capacity": "willing",

  "scheduling_pain": "Technicians often double-booked, customers wait too long, route planning is guesswork",
  "communication_pain": "Customers call repeatedly asking for ETA, office staff overwhelmed with calls",
  "lead_pain": "Miss calls after hours, leads go cold before we can respond",
  "growth_goals": "Want to grow from €2M to €4M in next 2 years without doubling office staff"
}

INDUSTRY BENCHMARKS (Home Services HVAC):
- AI call handling captures 85%+ of after-hours leads vs 0% with voicemail
- FSM software improves dispatch efficiency from 55% average to 65-75%
- Automated reminders reduce no-show rate from 15% to 8%
- Leads contacted within 5 minutes are 21x more likely to convert
- Good-better-best pricing increases average ticket by 20-40%
- Membership customer lifetime value €3,000-€10,000 vs €200-€500 one-time
- Automated invoicing reduces collection time by 70%
- Review automation: 2 reviews per 100 jobs → 15 reviews per 100 jobs
- Revenue per technician: median €200,000, this company: €133,333
- Time on admin: average 2.5 hours/day reduces to 1 hour with FSM software

Generate a JSON response with this structure:
{
  "executive_summary": {
    "headline": "One compelling sentence",
    "key_insight": "Most important takeaway",
    "ai_readiness_score": 65,
    "customer_value_score": 8,
    "business_health_score": 7,
    "total_value_potential": {"min": 75000, "max": 150000},
    "top_opportunities": [
      {"title": "...", "value_potential": "€30K-50K annually"}
    ],
    "not_recommended": [
      {"title": "...", "reason": "Why they should not do this"}
    ]
  },
  "findings": [
    {
      "id": "finding-001",
      "title": "Finding title",
      "category": "efficiency|growth|customer_experience|risk",
      "confidence": "high|medium|low",
      "description": "Detailed description with specific numbers",
      "current_state": "Based on quiz answer: '...'",
      "sources": ["Quiz answer", "Industry benchmark with source"],
      "value_saved": {"annual_savings": 20000, "hours_per_week": 8},
      "value_created": {"potential_revenue": 50000, "description": "How this creates value"},
      "customer_value_score": 8,
      "business_health_score": 9,
      "is_not_recommended": false,
      "why_not": null,
      "what_instead": null
    }
  ]
}

REQUIREMENTS:
- Every finding must cite specific quiz answers as sources
- Include industry benchmarks with source attribution
- Calculate specific € amounts based on their data
- 30% HIGH confidence, 50% MEDIUM, 20% LOW
- Include 3 "not recommended" findings (is_not_recommended: true) with alternatives
- Be specific about vendors (Housecall Pro, ServiceTitan, Jobber, etc.)
- Focus on practical, implementable recommendations within their €5K-15K budget
```

---

## Model Settings

| Setting | Value |
|---------|-------|
| Temperature | 0.7 |
| Max Tokens | 8192 |
| Top-P | Default |

---

## Models to Test

| Provider | Model ID | Strengths |
|----------|----------|-----------|
| **Anthropic** | `claude-opus-4-5-20251101` | Deep reasoning, nuanced analysis |
| **Google** | `gemini-3-pro-preview` | Long context (1M), multimodal |
| **OpenAI** | `gpt-5.2` | Fast inference (187 tok/s), 400K context |

---

## How to Test Each Model

### GPT-5.2 (OpenAI)
1. Go to [platform.openai.com/playground](https://platform.openai.com/playground)
2. Select model: `gpt-5.2`
3. Paste SYSTEM PROMPT in System field
4. Paste USER PROMPT in User field
5. Set Temperature: 0.7, Max tokens: 8192
6. Run and save output

### Gemini 3 Pro (Google)
1. Go to [ai.google.dev/aistudio](https://ai.google.dev/aistudio)
2. Select model: `gemini-3-pro-preview`
3. Paste SYSTEM PROMPT in System Instructions
4. Paste USER PROMPT in chat
5. Run and save output

### Claude Opus 4.5 (Anthropic)
```bash
cd backend && source venv/bin/activate
python test_model_comparison.py --provider anthropic
```

---

## Evaluation Criteria

| Criterion | Weight | What to Look For |
|-----------|--------|------------------|
| **Accuracy** | 25% | Numbers match industry reality, calculations are correct |
| **Specificity** | 25% | Names vendors, gives € amounts, cites sources |
| **Actionability** | 20% | Owner could implement tomorrow |
| **ROI Clarity** | 15% | Savings/revenue calculations are clear and defensible |
| **Structure** | 15% | Follows JSON schema exactly |

---

## Results Template

```markdown
## [Model Name] Results

**Time:** X.XX seconds
**Input Tokens:** XXX
**Output Tokens:** XXXX
**Cost:** $X.XX

### Executive Summary
- **Headline:**
- **AI Readiness Score:** /100
- **Value Potential:** €XX,XXX - €XX,XXX
- **Key Insight:**

### Top Opportunities
1.
2.
3.

### Not Recommended
1.
2.
3.

### Findings Summary (X total)
- HIGH confidence: X
- MEDIUM confidence: X
- LOW confidence: X

### Sample Findings
1. **[Title]** (confidence)
   - Customer Value: X/10, Business Health: X/10
   - Annual Savings: €XX,XXX
   - Revenue Potential: €XX,XXX

### Evaluation Scores
- Accuracy: X/10
- Specificity: X/10
- Actionability: X/10
- ROI Clarity: X/10
- Structure: X/10
- **Total:** X/50

### Notes
[Any observations about quality, tone, missing elements, etc.]
```

---

## Claude Opus 4.5 Baseline (Full Report)

**Time:** ~5 minutes (full pipeline)
**Findings:** 15 total

### Executive Summary
- **Headline:** ComfortAir is leaving €75K-150K annually on the table through missed after-hours leads, inefficient scheduling, and manual processes
- **AI Readiness Score:** 65/100
- **Customer Value Score:** 8/10
- **Business Health Score:** 7/10
- **Value Potential:** €75,000 - €150,000

### Top 5 Opportunities
1. **FSM Platform Implementation** - €30K-50K annually
2. **After-Hours Lead Capture** - €25K-40K annually
3. **Automated Customer ETA Updates** - €15K-25K annually
4. **Route Optimization** - €20K-35K annually
5. **Automated Review Collection** - €10K-20K annually

### Not Recommended
1. **AI Chatbot for Complex HVAC Diagnostics** - Requires licensed technician; customers expect human expertise
2. **Building Custom AI In-House** - Beyond budget/capacity; proven platforms exist
3. **Replacing Office Staff with AI Immediately** - 25% missed call rate = process problem, not headcount

### Confidence Distribution
- HIGH: 11 findings (73%)
- MEDIUM: 4 findings (27%)
- LOW: 0 findings (0%)

### Sample HIGH Confidence Findings
1. **After-Hours Call Capture System**
   - Customer: 9/10, Business: 9/10
   - Savings: €20,800/year (8 hrs/week)
   - Revenue: €91,000 (5 extra jobs/week at €350)
   - Source: "Miss calls after hours, leads go cold" + 25% missed call rate

2. **AI-Powered Scheduling & Route Optimization**
   - Customer: 8/10, Business: 10/10
   - Savings: €65,000/year (25 hrs/week)
   - Revenue: €173,250 (1.5 extra jobs/tech/day)
   - Source: "Technicians double-booked, route planning is guesswork"

3. **Automated Invoice & Payment Collection**
   - Customer: 7/10, Business: 8/10
   - Savings: €26,000/year (10 hrs/week)
   - Revenue: €15,000 (reduced bad debt)
   - Source: "Manual invoicing, 30-45 day collection"

---

## Comparison Notes

When comparing models, pay attention to:

1. **Source Citation Quality** - Does it quote specific quiz answers?
2. **Calculation Transparency** - Can you verify the math?
3. **Vendor Specificity** - Does it name real products with pricing?
4. **"Not Recommended" Quality** - Are the warnings practical and realistic?
5. **Confidence Calibration** - Is it honest about uncertainty?
6. **Budget Awareness** - Does it respect the €5K-15K constraint?
