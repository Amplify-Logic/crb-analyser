# Report Quality Audit

**Date:** 2026-01-07
**Auditor:** Claude Code
**Scope:** Report generation skills, prompts, and sample output

---

## Executive Summary

The current report generation system has strong foundations but suffers from several quality issues that lead to "AI slop" output. The main problems are:

1. **Numbers without backing** - ROI figures appear without traceable calculations
2. **Generic statements** - Findings and insights lack user-specific context
3. **Missing CRB structure** - Cost/Risk/Benefit not consistently applied
4. **Weak source citations** - Sources are vague or missing
5. **No buzzword enforcement** - Generic language slips through

**Priority:** 8 Critical issues, 5 High issues, 4 Medium issues

---

## Detailed Findings

### CRITICAL: Numbers Are Made Up or Unsubstantiated

**Location:** `finding_generation.py:325-485`, sample_report.json

**Problem:** ROI calculations and savings figures appear without traceable math.

**Evidence from sample report:**
```json
"value_potential": "€45K-75K/year"
"roi_percentage": 343
"payback_months": 4
```

**What's wrong:**
- Where did €45K-75K come from? No calculation shown
- 343% ROI - what's the formula?
- No link to user's actual quiz responses or industry benchmarks
- Assumptions listed but not connected to calculations

**How it should look:**
```
VALUE CALCULATION:
- User reported: 500 tier-1 tickets/month (Quiz Q5)
- Average handling time: 15 minutes (industry benchmark, Zendesk 2024)
- Hourly cost: €45/hour (user input or €28-45 industry range)
- Current cost: 500 × 15min × €45/hr = €5,625/month
- Expected deflection: 40% (conservative, industry sees 40-60%)
- Monthly savings: €5,625 × 40% = €2,250/month = €27,000/year
- Confidence: HIGH (user provided ticket volume and hourly rate)
```

**Files to fix:**
- `finding_generation.py` - Require explicit calculation chains
- `three_options.py` - Require ROI formula with inputs
- Add `src/services/calculation_service.py` - Centralized math validation

**Priority:** CRITICAL

---

### CRITICAL: Generic Findings That Don't Use User Data

**Location:** `finding_generation.py:325-340`

**Problem:** The prompt asks for specificity but doesn't enforce using actual quiz answers.

**Evidence from sample report:**
```json
"description": "Support team spends 60% of time on repetitive tier-1 questions that could be automated."
```

**What's wrong:**
- Where did "60%" come from? Not from quiz
- "could be automated" - generic AI-speak
- No reference to what the user actually said

**Current prompt says:**
```
"current_state": "How they're doing this now (from quiz answers)"
```

But doesn't enforce quoting the actual answer.

**How it should look:**
```json
"description": "You reported: 'We spend 40+ hours per week on repetitive customer support tasks' (Quiz Q5). Based on your ticket volume of 500/month, this maps to approximately 4.8 minutes per ticket for Tier-1 responses.",
"current_state": "Manual email responses to common questions, no knowledge base automation (based on your answer: 'mostly email, some phone')"
```

**Prompt fix needed:**
```
CRITICAL: For each finding, you MUST:
1. Quote the exact user response that supports this finding: "Based on your answer: '[exact quote]'"
2. If no direct quote supports it, mark confidence as LOW and explain the inference
3. NEVER make claims about percentages or metrics unless the user provided them or you cite a specific benchmark
```

**Priority:** CRITICAL

---

### CRITICAL: Executive Summary Key Insight Is Generic

**Location:** `exec_summary.py:178-224`

**Problem:** Key insights often sound like generic consulting-speak.

**Evidence from sample report:**
```json
"key_insight": "TechFlow Solutions has strong customer service foundations but is leaving €180K+ on the table annually through manual processes."
```

**What's wrong:**
- "strong customer service foundations" - based on what?
- "€180K+ on the table" - unsubstantiated large number
- Could be written for any company

**How it should look:**
```json
"key_insight": "Your 4-hour average response time and 500 monthly tier-1 tickets point to a specific automation gap: automated FAQ responses could handle 40-60% of volume, recovering ~20 hours/week for complex cases."
```

**Prompt fix needed:**
```
KEY INSIGHT REQUIREMENTS:
- MUST reference at least one specific number from user input
- MUST NOT use phrases like "strong foundations", "well-positioned", "leaving money on the table"
- MUST be falsifiable (specific enough that we could prove it wrong)

BAD: "Strong opportunity for AI adoption"
GOOD: "Your 18% no-show rate costs €3,600/month; automated reminders reduce this to 8% (industry benchmark)"
```

**Priority:** CRITICAL

---

### CRITICAL: Connect vs Replace Missing CRB Structure

**Location:** `finding_generation.py:370-385`

**Problem:** Connect and Replace paths don't have consistent Cost/Risk/Benefit breakdowns.

**Current structure:**
```json
"connect_path": {
    "integration_flow": "Tool A -> n8n -> Tool B",
    "monthly_cost_estimate": <number>,
    "setup_effort_hours": <number>
}
```

**What's missing:**
- Implementation cost breakdown (DIY vs Professional)
- Risk assessment (implementation, dependency, reversal)
- Quantified benefit with calculation
- Hidden costs (training, productivity dip)

**How it should look:**
```json
"connect_path": {
    "integration_flow": "Open Dental -> n8n -> Twilio",
    "cost": {
        "implementation": {
            "diy": {"hours": 8, "rate": 50, "total": 400},
            "professional": {"estimate": 1500, "source": "n8n agency rates"}
        },
        "monthly": {
            "twilio_sms": 25,
            "n8n_cloud": 7,
            "total": 32
        },
        "hidden": {
            "training_hours": 2,
            "productivity_dip_weeks": 1
        }
    },
    "risk": {
        "implementation": {"score": 2, "reason": "API well-documented"},
        "dependency": "Low - can switch SMS providers easily",
        "reversal": "Easy - just disable workflow"
    },
    "benefit": {
        "metric": "no-show rate",
        "baseline": "18%",
        "target": "8%",
        "calculation": "10% reduction × €350/appt × 100 appts = €3,500/month",
        "confidence": "HIGH - industry benchmark supported"
    }
}
```

**Priority:** CRITICAL

---

### CRITICAL: Sources Are Vague or Missing

**Location:** `finding_generation.py:396-404`

**Problem:** Source citations don't meet the standard for real evidence.

**Evidence from sample report:**
```json
"sources": ["Customer support ticket analysis", "Team interviews"]
```

**What's wrong:**
- No actual data from these sources
- No specific numbers cited
- No benchmark source with date
- Could be fabricated

**Current prompt says:**
```
"sources": ["Specific citation 1", "Specific citation 2"]
```

But doesn't define what "specific" means.

**How it should look:**
```json
"sources": [
    "Quiz Q5: 'We spend 40+ hours per week on repetitive customer support tasks'",
    "Industry benchmark: Tier-1 tickets average 40-60% deflection rate with AI (Zendesk AI Report 2024)",
    "Your data: 500 tickets/month reported in quiz"
]
```

**Prompt fix needed:**
```
SOURCE REQUIREMENTS:
Each source MUST be one of:
1. QUIZ RESPONSE: "Quiz Q[N]: '[exact quote]'"
2. BENCHMARK: "[Metric]: [Value] (Source: [Name], [Year])"
3. CALCULATION: "Calculated: [formula] = [result]"
4. INTERVIEW: "Interview: '[direct quote]' - [Topic]"

NEVER use:
- "Industry benchmark" without source name and year
- "Best practice" without citation
- "Studies show" without specific study
```

**Priority:** CRITICAL

---

### CRITICAL: Confidence Levels Not Enforced

**Location:** `finding_generation.py:400-416`

**Problem:** Confidence distribution targets exist but aren't enforced in output.

**Current code:**
```python
CONFIDENCE_DISTRIBUTION = {
    "high": 0.30,    # ~30% of findings
    "medium": 0.50,  # ~50% of findings
    "low": 0.20,     # ~20% of findings
}
```

**What's wrong:**
- This is a target, not a constraint
- High confidence is assigned too liberally
- No validation that confidence matches evidence strength

**Evidence from sample report:**
All findings have HIGH or MEDIUM confidence - where's the LOW confidence finding that admits uncertainty?

**How it should be enforced:**
```
CONFIDENCE RULES:
- HIGH: Only if user provided specific numbers AND benchmark exists
- MEDIUM: User implied issue OR benchmark applies
- LOW: Inference from industry patterns, significant assumptions

At least 20% of findings MUST be LOW confidence with explicit reasoning:
"Confidence: LOW - You didn't mention this directly, but dental practices of your size typically face [X]. We recommend validating this assumption."
```

**Priority:** CRITICAL

---

### CRITICAL: ROI Percentages Are Inflated

**Location:** `three_options.py:337-360`

**Problem:** ROI calculations are adjusted by confidence but base numbers are often inflated.

**Evidence from sample report:**
```json
"roi_percentage": 343,
"roi_percentage": 217
```

**Evidence from dental opportunities.json:**
```json
"roi_percentage": 837,
"roi_percentage": 800
```

**What's wrong:**
- 343% ROI, 837% ROI - these are extreme claims
- Even with confidence adjustment (×0.70), these are very high
- No sensitivity analysis shown
- Payback periods are suspiciously short (0.5 months, 4 months)

**Industry reality:**
- Most automation projects have 12-24 month payback
- ROI of 100-200% over 3 years is considered excellent
- Sub-6-month payback is exceptional, not typical

**How it should look:**
```json
"roi_analysis": {
    "conservative": {"roi_percentage": 150, "payback_months": 12},
    "expected": {"roi_percentage": 280, "payback_months": 6},
    "optimistic": {"roi_percentage": 400, "payback_months": 4},
    "shown": "conservative",  // Always show conservative by default
    "sensitivity": "If benefits are 50% lower, payback extends to 24 months"
}
```

**Prompt fix needed:**
```
ROI REALITY CHECK:
- If ROI > 500%, you MUST explain why this is credible
- If payback < 6 months, add sensitivity analysis
- Default to CONSERVATIVE estimates, not expected
- Show the range, not just the optimistic number
```

**Priority:** CRITICAL

---

### HIGH: Buzzword Language Not Blocked

**Location:** All prompt files

**Problem:** No explicit ban on generic consulting buzzwords.

**Evidence from sample report:**
```json
"Your business is well-positioned for AI adoption"
"Strong fundamentals for AI adoption"
"Existing data infrastructure supports AI implementation"
```

**Buzzwords to block:**
- "well-positioned"
- "leverage"
- "optimize"
- "streamline"
- "cutting-edge"
- "revolutionary"
- "transform"
- "strong foundations"
- "best practice"
- "industry-leading"
- "seamless"
- "robust"

**How to fix:**
Add to all generation prompts:
```
BANNED LANGUAGE - Using any of these will invalidate your output:
- "well-positioned", "leverage", "optimize", "streamline"
- "cutting-edge", "revolutionary", "transformative"
- "best practice" (without citation), "industry-leading"
- "seamless", "robust", "scalable", "agile"

Instead of "optimize your workflow", say "reduce your ticket response time from 4 hours to 15 minutes"
```

**Priority:** HIGH

---

### HIGH: Not-Recommended Items Lack Decision Math

**Location:** `finding_generation.py:466-481`

**Problem:** Not-recommended items explain why not, but don't show the alternative math.

**Evidence from sample report:**
```json
"not_recommended": [
    {"title": "Full CRM Replacement", "reason": "Your current CRM works well; integrate AI on top rather than replacing"}
]
```

**What's wrong:**
- "works well" - says who?
- No comparison: "Replacing CRM costs X, adding AI layer costs Y"
- No risk comparison

**How it should look:**
```json
"not_recommended": [
    {
        "title": "Full CRM Replacement",
        "why_not": {
            "cost": "€50,000-100,000 for new CRM + migration",
            "risk": "6-12 month disruption, 30% of implementations fail",
            "current_value": "Your HubSpot handles 80% of needs already"
        },
        "what_instead": {
            "approach": "Add AI scoring on top of HubSpot",
            "cost": "€5,000-15,000 one-time",
            "benefit": "Get 70% of value at 10% of cost"
        },
        "decision_math": "ROI of integration: 450%. ROI of replacement: 50% (after accounting for switching costs)"
    }
]
```

**Priority:** HIGH

---

### HIGH: Three Options Missing Comparison Table

**Location:** `three_options.py`

**Problem:** Options are listed but not compared side-by-side for decision-making.

**Current structure shows each option separately. Missing:**
```
COMPARISON SUMMARY:
| Aspect          | Off-the-Shelf | Best-in-Class | Custom    |
|-----------------|---------------|---------------|-----------|
| Monthly cost    | €199          | €299          | €50       |
| Setup cost      | €500          | €2,000        | €15-25K   |
| Time to value   | 2 weeks       | 3 weeks       | 8 weeks   |
| Customization   | Low           | Medium        | High      |
| Maintenance     | None          | Low           | High      |
| RECOMMENDATION  | ★★★           | ★★            | ★         |

WHY OFF-THE-SHELF WINS FOR YOU:
- Your ticket volume (500/month) is below the threshold where custom pays off
- Your team's tech comfort (medium) suggests avoiding maintenance burden
- Time to value matters: you need results in Q1, not Q2
```

**Priority:** HIGH

---

### HIGH: Dental Benchmarks Not Enforced in Prompts

**Location:** `finding_generation.py:330-338` vs `dental/benchmarks.json`

**Problem:** Excellent benchmark data exists but prompts don't enforce using it.

**We have this data:**
```json
"no_show_rate": {
    "industry_average": 18,
    "with_reminders": 10,
    "best_in_class": 5,
    "source": "Journal of Dental Hygiene, 2024"
}
```

**But the prompt just says:**
```
INDUSTRY BENCHMARKS:
{json.dumps(benchmarks, indent=2) if benchmarks else "Use general industry standards"}
```

**No enforcement to actually USE these benchmarks.**

**Fix needed:**
```
BENCHMARK USAGE REQUIREMENT:
For each finding in dental practices, you MUST reference at least one of these benchmarks:
- No-show rate: 18% average, 10% with reminders, 5% best-in-class (Journal of Dental Hygiene, 2024)
- Treatment acceptance: 40% average, 60% good, 80% excellent (Dental Intelligence, 2024)
- [etc.]

If the user's data differs significantly from benchmark, CALL IT OUT:
"Your 25% no-show rate is 7 points above industry average of 18%, suggesting high-impact automation opportunity."
```

**Priority:** HIGH

---

### MEDIUM: Verdict Reasoning Too Generic

**Location:** `verdict.py:276-292`

**Problem:** Verdict reasoning summarizes but doesn't prove.

**Evidence from sample report:**
```json
"reasoning": [
    "Clear ROI opportunity with 6-month payback potential",
    "Existing data infrastructure supports AI implementation",
    "Team shows willingness to adopt new tools"
]
```

**What's wrong:**
- "Clear ROI opportunity" - not proven in reasoning
- "Existing data infrastructure" - what infrastructure?
- "Team shows willingness" - based on what evidence?

**How it should look:**
```json
"reasoning": [
    "ROI calculation: €35K annual savings ÷ €10K year-1 cost = 350% (confidence: HIGH)",
    "Your HubSpot CRM + Zendesk stack scores 4.2/5 on API openness = automation-ready",
    "Quiz Q8: You rated tech comfort as 'high' and mentioned 'eager to try new tools'"
]
```

**Priority:** MEDIUM

---

### MEDIUM: Time Horizons Undefined

**Location:** `finding_generation.py:80`

**Problem:** "short", "mid", "long" are used but not defined.

```python
"time_horizon": "short|mid|long"
```

**What do these mean?**
- short = 1 week? 1 month? 1 quarter?
- mid = 3 months? 6 months? 1 year?
- long = 1 year? 2 years? 5 years?

**How to fix:**
```python
TIME_HORIZONS = {
    "short": {"weeks": 4, "label": "0-4 weeks", "description": "Quick wins"},
    "mid": {"weeks": 12, "label": "1-3 months", "description": "Core implementations"},
    "long": {"weeks": 52, "label": "3-12 months", "description": "Strategic initiatives"}
}
```

**Priority:** MEDIUM

---

### MEDIUM: Missing "What We Don't Know" Section

**Location:** All report sections

**Problem:** Reports present certainty, never acknowledge gaps.

**Should add:**
```json
"data_gaps": [
    {
        "what": "Actual ticket response time",
        "why_it_matters": "Affects baseline for improvement calculation",
        "assumed": "4 hours (industry average)",
        "to_validate": "Export from Zendesk → average first response time"
    },
    {
        "what": "Staff hourly cost",
        "why_it_matters": "Directly impacts ROI calculation",
        "assumed": "€45/hour",
        "to_validate": "Check with HR for fully-loaded cost"
    }
]
```

**Priority:** MEDIUM

---

### MEDIUM: Playbook Tasks Too Vague

**Location:** `sample_report.json:166-178`

**Problem:** Playbook tasks are generic, not personalized.

**Evidence:**
```json
{"id": "t2", "title": "Import knowledge base articles (50-100 articles)", "hours": 4, "owner": "Support Lead"}
```

**What's wrong:**
- "50-100 articles" - based on what?
- How do we know they have a knowledge base to import?
- No link to their actual content

**How it should look:**
```json
{
    "id": "t2",
    "title": "Import your FAQ content into Intercom",
    "context": "Based on your quiz, you mentioned having 'a basic FAQ page'. This task imports that content.",
    "hours": 4,
    "hours_if": {
        "have_structured_faq": 2,
        "have_scattered_docs": 6,
        "starting_fresh": 8
    },
    "owner": "Support Lead",
    "deliverable": "All common questions from Quiz Q12 are in Intercom with responses"
}
```

**Priority:** MEDIUM

---

## Summary by Priority

### CRITICAL (Fix First)
1. Numbers without calculation chains
2. Generic findings not using quiz data
3. Key insight is generic consulting-speak
4. Connect vs Replace missing CRB structure
5. Sources are vague or missing
6. Confidence levels not enforced
7. ROI percentages are inflated
8. No buzzword blocking

### HIGH (Fix Next)
1. Not-recommended items lack decision math
2. Three options missing comparison table
3. Dental benchmarks not enforced in prompts
4. Missing explicit calculation validation

### MEDIUM (Polish)
1. Verdict reasoning too generic
2. Time horizons undefined
3. Missing "What We Don't Know" section
4. Playbook tasks too vague

---

## Recommended Fix Order

1. **Add calculation service** (`src/services/calculation_service.py`)
   - All ROI/savings must go through validated formulas
   - Must show input source (quiz, benchmark, assumption)
   - Must show confidence level

2. **Update finding_generation.py prompt**
   - Require quiz quotes
   - Require benchmark citations
   - Ban buzzwords
   - Enforce confidence distribution

3. **Add CRB structure to Connect/Replace paths**
   - Cost: implementation, ongoing, hidden
   - Risk: implementation, dependency, reversal
   - Benefit: metric, calculation, confidence

4. **Update exec_summary.py prompt**
   - Key insight must be falsifiable
   - Must reference specific numbers
   - Ban generic praise

5. **Add validation service**
   - Check all findings have real sources
   - Check ROI calculations are traceable
   - Check no buzzwords present

---

## Files Changed/Created

**To Create:**
- `backend/src/services/calculation_service.py` - Validated calculation functions
- `backend/src/services/quality_validator.py` - Output quality checks

**To Modify:**
- `backend/src/skills/report-generation/finding_generation.py`
- `backend/src/skills/report-generation/exec_summary.py`
- `backend/src/skills/report-generation/three_options.py`
- `backend/src/skills/report-generation/verdict.py`
- `backend/src/prompts/crb_analysis_v1.py`

---

## Success Criteria

A report passes quality audit when:

1. **Every number is traceable**
   - Quiz input → calculation → result
   - Or benchmark source with date

2. **Every finding quotes user data**
   - "Based on your answer: '[quote]'"
   - Or explicit inference with LOW confidence

3. **No buzzwords present**
   - grep for banned terms returns empty

4. **CRB is complete for each recommendation**
   - Cost breakdown present
   - Risk assessment present
   - Benefit calculation present

5. **Confidence matches evidence**
   - HIGH: user data + benchmark
   - MEDIUM: inference from data
   - LOW: industry pattern only
