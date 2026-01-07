# Prompt Engineering Audit

**Date:** 2026-01-07
**Auditor:** Claude Code
**Scope:** All prompts in `backend/src/skills/report-generation/`

---

## Executive Summary

This audit evaluates all LLM prompts used in report generation against the quality criteria from the master roadmap. The goal is to eliminate "AI slop" and ensure outputs are specific, traceable, and actionable.

**Files Audited:**
- `exec_summary.py` (lines 178-224) - Executive summary generation
- `finding_generation.py` (lines 325-484) - Finding generation with Connect vs Replace
- `three_options.py` (lines 187-282) - Three options recommendation format
- `verdict.py` (lines 275-350) - Go/Caution/Wait/No verdict

**Summary of Issues Found:**
| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 8 | Core quality requirements missing |
| HIGH | 5 | Significant gaps enabling generic output |
| MEDIUM | 4 | Polish and consistency issues |

---

## Audit Findings by File

---

### 1. exec_summary.py

**Location:** Lines 178-224 (main prompt), Lines 244-261 (system prompt)

#### CRITICAL: Key Insight Can Be Generic

**Current Prompt (line 192):**
```
"key_insight": "<one compelling sentence - the main takeaway>",
```

**Problem:** No constraints prevent generic statements like "Strong opportunity for AI adoption."

**Fixed Version:**
```
"key_insight": "<MUST include at least one specific number from quiz or benchmark. MUST be falsifiable. Examples:
  GOOD: 'Your 18% no-show rate costs ~€3,600/month; automated reminders typically reduce this to 8%'
  BAD: 'Strong opportunity for AI adoption'
  BAD: 'Well-positioned for digital transformation'>",
```

#### CRITICAL: No Buzzword Blocking

**Problem:** System prompt says "Be specific" but doesn't ban generic language.

**Current System Prompt (lines 246-261):**
```python
"""You are an expert AI business consultant...
Key principles:
1. HONEST ASSESSMENT: Never oversell. If AI isn't a good fit, say so.
2. SPECIFIC INSIGHTS: Generic insights are useless. Be specific to their situation.
...
"""
```

**Fixed System Prompt:**
```python
"""You are an expert AI business consultant generating executive summaries for CRB Analysis reports.

Your role is to be an honest advisor - tell clients what they need to hear, not what they want to hear.

BANNED LANGUAGE - Using any of these invalidates your output:
- "well-positioned", "strong foundations", "significant opportunity"
- "leverage", "optimize", "streamline", "transform", "revolutionize"
- "best practice", "industry-leading", "cutting-edge", "robust", "seamless"
- "drive growth", "unlock value", "accelerate"

Instead of buzzwords, use SPECIFIC NUMBERS:
- BAD: "Optimize your customer support"
- GOOD: "Reduce response time from 4 hours to 15 minutes"

Key principles:
1. EVIDENCE-BASED: Every claim must cite quiz answer or benchmark
2. NUMBERS REQUIRED: Key insight must include at least one quantified metric
3. HONEST: If AI isn't a good fit, say so - don't oversell
4. FALSIFIABLE: Insights must be specific enough to prove wrong
5. INCLUDE WARNINGS: Always include what they should NOT do

Score Guidelines:
- AI Readiness (0-100): Current state, not potential. 70+ = AI-ready, 50-69 = needs prep, <50 = significant gaps
- Customer Value (1-10): Direct customer experience improvement. 8+ = transformative
- Business Health (1-10): Operational/financial improvement. 8+ = significant impact"""
```

#### HIGH: Value Potential Without Calculation Chain

**Current (line 193-196):**
```
"total_value_potential": {
    "min": <conservative estimate in euros>,
    "max": <optimistic estimate in euros>,
    "projection_years": 3
},
```

**Problem:** No requirement to show HOW these numbers were calculated.

**Fixed Version:**
```
"total_value_potential": {
    "min": <number>,
    "max": <number>,
    "projection_years": 3,
    "calculation": "<REQUIRED: Show the math. Example: '5 findings × €8K avg impact = €40K/year × 3 years'>"
},
```

#### MEDIUM: Top Opportunities Lack Specificity

**Current (lines 198-204):**
```
"top_opportunities": [
    {
        "title": "<specific opportunity name>",
        "value_potential": "<range like €10K-20K/year>",
        "time_horizon": "short|mid|long"
    }
],
```

**Fixed Version:**
```
"top_opportunities": [
    {
        "title": "<specific opportunity - must reference user's actual process or tool>",
        "value_potential": "<range with calculation: 'X hrs/week × €Y rate × 52 weeks = €Z'>",
        "time_horizon": "short (0-4 weeks)|mid (1-3 months)|long (3-12 months)",
        "data_source": "<quiz question or benchmark that supports this>"
    }
],
```

---

### 2. finding_generation.py

**Location:** Lines 325-484 (main prompt), Lines 506-531 (system prompt)

#### CRITICAL: Sources Can Still Be Vague

**Current (lines 388-395):**
```
SOURCE CITATION REQUIREMENTS:

Every finding MUST have at least one specific source:
1. Quiz response: "Based on your answer: '[quote from their answer]'"
2. Industry benchmark: "Industry average: X (Source: [benchmark name])"
3. Calculation: "Calculated: [formula with numbers]"
4. Industry pattern: "[Industry] businesses typically see [pattern]"
```

**Problem:** Option 4 allows vague citations. "Industry pattern" without a verifiable source.

**Fixed Version:**
```
SOURCE CITATION REQUIREMENTS - MANDATORY FOR EVERY FINDING:

Every finding MUST cite sources using ONLY these formats:

1. QUIZ RESPONSE (strongest):
   Format: "Quiz Q[N]: '[exact quote from their answer]'"
   Example: "Quiz Q5: 'We spend 40+ hours per week on repetitive customer support tasks'"

2. BENCHMARK (must include source + year):
   Format: "[Metric]: [Value] (Source: [Organization/Report Name], [Year])"
   Example: "No-show rate: 18% industry average (Journal of Dental Hygiene, 2024)"

3. CALCULATION (must show all inputs):
   Format: "Calculated: [formula] = [result] (inputs: [list sources of each input])"
   Example: "Calculated: 500 tickets × 15min × €45/hr ÷ 60 = €5,625/month (ticket count from Quiz Q3, time from Zendesk benchmark 2024)"

FORBIDDEN SOURCE FORMATS:
- "Industry average" without source name
- "Studies show" without specific study
- "Best practice" without citation
- "Typically" without data reference
```

#### CRITICAL: Confidence Enforcement Missing

**Current (lines 399-416):**
```
CONFIDENCE SCORING CRITERIA:

Rate each finding's confidence:

HIGH (~30% of findings):
...
MEDIUM (~50% of findings):
...
LOW (~20% of findings):
...
```

**Problem:** These are targets, not requirements. The LLM ignores them.

**Fixed Version:**
```
CONFIDENCE SCORING - STRICTLY ENFORCED:

You MUST rate confidence using ONLY these criteria:

HIGH (assign to exactly 3 out of 10 findings):
- REQUIRES: User explicitly stated this problem in quiz (direct quote available)
- REQUIRES: Specific benchmark with source supports the finding
- REQUIRES: ROI calculation uses user-provided numbers

MEDIUM (assign to exactly 5 out of 10 findings):
- Quiz answer implies this issue (inference, not direct statement)
- Industry benchmark likely applies but not perfectly matched
- One strong data point, some assumptions

LOW (assign to exactly 2 out of 10 findings):
- Based on industry patterns, user did not mention this
- Significant assumptions required
- Hypothesis worth validating with the user

ENFORCEMENT: I will count your confidence assignments. If distribution is wrong, output is invalid.
- Exactly 20% LOW findings required
- LOW findings MUST include explicit uncertainty: "You didn't mention this, but [industry] businesses often face..."
```

#### CRITICAL: Connect vs Replace Missing CRB Structure

**Current Connect Path (lines 445-453):**
```
"connect_path": {
    "integration_flow": "Tool A -> n8n -> Tool B",
    "flow_steps": ["Step 1", "Step 2"],
    "what_it_does": "Brief description",
    "monthly_cost_estimate": <number>,
    "setup_effort_hours": <number>,
    "why_this_works": "API capabilities that enable this",
    "tools_used": ["n8n", "Twilio", "Claude API"]
},
```

**Problem:** Missing CRB structure - no implementation cost breakdown, no risk assessment, no benefit quantification.

**Fixed Version:**
```
"connect_path": {
    "integration_flow": "Tool A -> n8n -> Tool B",
    "flow_steps": ["Step 1 with specific action", "Step 2 with specific action"],
    "what_it_does": "Brief description",

    "cost": {
        "implementation_diy": {
            "hours": <number>,
            "hourly_rate": 50,
            "total": <hours × 50>,
            "description": "What work is required"
        },
        "implementation_professional": {
            "estimate": <number>,
            "source": "n8n agency rates / freelancer market"
        },
        "monthly_ongoing": {
            "breakdown": [
                {"item": "n8n cloud", "cost": <number>},
                {"item": "Twilio", "cost": <number>}
            ],
            "total": <sum>
        },
        "hidden": {
            "training_hours": <number>,
            "productivity_dip_weeks": <number>
        }
    },

    "risk": {
        "implementation_score": <1-5>,
        "implementation_reason": "Why this score",
        "dependency_risk": "What happens if [tool] goes down or changes API",
        "reversal_difficulty": "Easy|Medium|Hard - how hard to undo"
    },

    "benefit": {
        "primary_metric": "What improves",
        "baseline": "Current state (from quiz)",
        "target": "Expected state (from benchmark)",
        "monthly_value": <number>,
        "calculation": "Show the math with inputs cited"
    },

    "tools_used": ["n8n", "Twilio", "Claude API"],
    "why_this_works": "Specific API capabilities that enable this"
},
```

#### HIGH: No Buzzword Blocking in Finding Generation

**Current System Prompt (lines 506-531):** Contains good principles but no explicit buzzword ban.

**Add to System Prompt:**
```
BANNED LANGUAGE - Using any of these invalidates the finding:
- "streamline operations", "optimize workflow", "enhance efficiency"
- "drive growth", "unlock potential", "accelerate transformation"
- "seamless integration", "robust solution", "cutting-edge"
- "leverage AI", "harness the power of"

INSTEAD OF: "Streamline your customer support operations"
USE: "Reduce average response time from 4 hours to 15 minutes"

INSTEAD OF: "Leverage AI to optimize scheduling"
USE: "Automate 80% of appointment confirmations, saving 6 hours/week"
```

#### HIGH: ROI Not Validated for Reasonableness

**Problem:** Finding generation doesn't check if ROI/savings claims are realistic.

**Add to Prompt:**
```
ROI REALITY CHECK - APPLY TO EVERY FINDING:

Before outputting a finding, validate:

1. If annual_savings > €50,000:
   - MUST explain why this is credible for a small/medium business
   - MUST show detailed calculation with verifiable inputs

2. If hours_per_week saved > 20:
   - MUST explain what activity currently takes this much time
   - MUST cite quiz answer proving this time investment

3. If ROI > 300%:
   - MUST include sensitivity analysis: "If benefits are 50% lower, still X% ROI"
   - MUST explain why this finding is exceptional

4. DEFAULT TO CONSERVATIVE:
   - When uncertain, use lower end of estimate
   - Better to under-promise than over-deliver
```

---

### 3. three_options.py

**Location:** Lines 187-282 (main prompt), Lines 297-312 (system prompt)

#### CRITICAL: ROI Percentages Can Be Inflated

**Current (lines 269-274):**
```
"roi_percentage": <calculated ROI>,
"payback_months": <months to recover investment>,
"assumptions": [
    "<assumption with specific numbers>",
    "<assumption with specific numbers>"
]
```

**Problem:** No bounds or reality checks on ROI.

**Fixed Version:**
```
"roi_analysis": {
    "conservative": {
        "roi_percentage": <lower bound - use 70% of expected>,
        "payback_months": <conservative estimate>
    },
    "expected": {
        "roi_percentage": <base calculation>,
        "payback_months": <base estimate>
    },
    "optimistic": {
        "roi_percentage": <upper bound - only if everything goes right>,
        "payback_months": <best case>
    },
    "show_by_default": "conservative",
    "sensitivity": "If benefits are 50% lower than expected, payback extends to [X] months"
},
"assumptions": [
    "<assumption 1 - with specific number and source: 'Response time 4hrs (Quiz Q3)'>",
    "<assumption 2 - with specific number and source: 'Ticket volume 500/month (industry avg for this size)'>"
]
```

**Add validation rule:**
```
ROI GUARDRAILS:
- If roi_percentage > 500%: You MUST add explanation of why this is credible
- If payback_months < 3: You MUST note this is exceptional and explain why
- ALWAYS show conservative estimate by default
- ALWAYS include sensitivity analysis for recommendations > €10K investment
```

#### HIGH: Missing Comparison Table

**Problem:** Options are listed separately, no side-by-side comparison for decision-making.

**Add to output structure:**
```
"comparison_summary": {
    "table": [
        {"aspect": "Monthly cost", "off_the_shelf": "€X", "best_in_class": "€Y", "custom": "€Z"},
        {"aspect": "Setup cost", "off_the_shelf": "€X", "best_in_class": "€Y", "custom": "€Z"},
        {"aspect": "Time to value", "off_the_shelf": "X weeks", "best_in_class": "Y weeks", "custom": "Z weeks"},
        {"aspect": "Customization", "off_the_shelf": "Low", "best_in_class": "Medium", "custom": "High"},
        {"aspect": "Maintenance", "off_the_shelf": "None", "best_in_class": "Low", "custom": "High"}
    ],
    "winner_for_this_company": "off_the_shelf|best_in_class|custom",
    "why_winner": "<1-2 sentences explaining why this option wins GIVEN THIS COMPANY'S specific context from quiz>"
}
```

#### HIGH: Buzzword Blocking Missing

**Add to system prompt:**
```
BANNED LANGUAGE:
- "seamless integration", "robust", "scalable", "enterprise-grade"
- "unlock value", "drive efficiency", "optimize"

INSTEAD OF: "Seamlessly integrate with your existing tools"
USE: "Connects to HubSpot via native integration, syncs in <5 minutes"
```

#### MEDIUM: Model Recommendations Outdated

**Current (lines 325-330):**
```
MODEL RECOMMENDATIONS:
- Claude Opus 4.5: Complex reasoning, highest quality ($15/$75 per MTok)
- Claude Sonnet 4: Balanced quality/cost, best for most use cases ($3/$15 per MTok)
- Claude Haiku 3.5: Speed-critical, high volume ($0.80/$4 per MTok)
```

**Keep Updated:** These prices should be verified against current Anthropic pricing.

---

### 4. verdict.py

**Location:** Lines 275-350 (main prompt), Lines 394-412 (system prompt)

#### HIGH: Reasoning Can Still Be Generic

**Current (lines 326-330):**
```
"reasoning": [
    "<key reason 1>",
    "<key reason 2>",
    "<key reason 3>"
],
```

**Problem:** No requirement to include specific numbers or finding references.

**Fixed Version:**
```
"reasoning": [
    "<reason 1 - MUST include specific metric: 'ROI calculation shows €X savings at Y% confidence'>",
    "<reason 2 - MUST reference finding: 'Finding #3 (no-show reduction) alone justifies investment'>",
    "<reason 3 - MUST cite quiz data: 'Tech comfort rated HIGH supports custom solution adoption'>"
],
```

**Add constraint:**
```
REASONING REQUIREMENTS:
Each reason MUST contain at least one of:
- A specific number (€, %, hours)
- A reference to a specific finding by title or ID
- A quote or paraphrase from quiz answers

INVALID: "Clear ROI opportunity with strong potential"
VALID: "€35K annual savings ÷ €10K year-1 investment = 350% ROI (Finding #1-3)"

INVALID: "Team shows readiness to adopt AI"
VALID: "Quiz Q8: Tech comfort rated 'high' + 'eager to try new tools' indicates strong adoption likelihood"
```

#### MEDIUM: Buzzword Blocking Missing

**Current subheadline templates (lines 82-109):**
```python
"go": {
    "subheadline": "Strong fundamentals for AI adoption",
    ...
},
```

**Problem:** The default template itself contains buzzwords.

**Fixed Templates:**
```python
VERDICT_TEMPLATES = {
    "go": {
        "recommendation": "proceed",
        "color": "green",
        "headline": "Go For It",
        "subheadline": "Your data shows clear ROI opportunity",  # Removed "strong fundamentals"
        "when_to_revisit": "Quarterly check-ins to measure progress",
    },
    "caution": {
        "recommendation": "proceed_cautiously",
        "color": "yellow",
        "headline": "Proceed with Caution",
        "subheadline": "ROI potential exists but risks need monitoring",  # More specific
        "when_to_revisit": "Re-evaluate after first pilot (3-6 months)",
    },
    ...
}
```

#### MEDIUM: "What To Do Instead" Often Empty

**Problem:** For non-GO verdicts, alternatives are critical but often skipped.

**Add enforcement:**
```
ENFORCEMENT FOR wait/not_recommended:
If recommendation is "wait" or "not_recommended", you MUST provide:
- At least 2 specific alternative actions in "what_to_do_instead"
- Each action must be concrete: "Implement CRM data cleanup (Finding #7)" not "Focus on data quality"
- Each action must reference a finding or quiz answer
```

---

## Implementation Summary

### Files to Modify

| File | Changes Required |
|------|------------------|
| `exec_summary.py` | Add buzzword blocking, require calculation chains, enforce falsifiable key insights |
| `finding_generation.py` | Strengthen source citations, enforce confidence distribution, add full CRB structure, add ROI validation |
| `three_options.py` | Add ROI guardrails, add comparison table, add buzzword blocking |
| `verdict.py` | Require specific reasoning, fix template buzzwords, enforce alternatives |

### Priority Order

1. **finding_generation.py** - Most impact, generates core content
2. **exec_summary.py** - User sees first, sets expectations
3. **three_options.py** - Drives purchasing decisions
4. **verdict.py** - Summary, depends on above being fixed

### Success Criteria

After implementation, a generated report should pass these checks:

1. **Buzzword Check:** `grep -E "(leverage|streamline|optimize|robust|seamless)" report.json` returns empty
2. **Source Check:** Every finding has at least one source matching allowed formats
3. **Confidence Check:** Exactly 20% of findings have LOW confidence
4. **ROI Check:** No ROI > 500% without explicit justification
5. **Number Check:** Key insight contains at least one € or % value
6. **Calculation Check:** Value potential shows formula, not just result

---

## Appendix: Full Improved Prompts

See implementation in:
- `backend/src/skills/report-generation/exec_summary.py`
- `backend/src/skills/report-generation/finding_generation.py`
- `backend/src/skills/report-generation/three_options.py`
- `backend/src/skills/report-generation/verdict.py`
