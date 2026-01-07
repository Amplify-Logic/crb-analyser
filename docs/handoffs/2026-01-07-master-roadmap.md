# CRB Analyser — Master Improvement Roadmap

**Date:** 2026-01-07
**Goal:** Make reports genuinely useful, not AI slop. Real insights with Cost-Risk-Benefit analysis.

---

## The Problem

AI-generated reports often feel generic:
- Vague recommendations ("consider implementing automation")
- No real numbers (or made-up ones)
- Missing context about the user's specific situation
- No clear decision framework

**Our standard:** Every recommendation must include:
- **Cost:** Real implementation cost + ongoing cost
- **Risk:** What could go wrong, migration pain, learning curve
- **Benefit:** Quantified impact with reasoning
- **Recommendation:** Clear verdict with confidence level

---

## Parallel Workstreams

These can run independently. Start multiple sessions with these prompts.

---

### Workstream 1: Verify Implementation
**Priority:** HIGH — Do first
**Can parallelize:** No (blocking)

```
Read docs/handoffs/2026-01-07-connect-vs-replace-handoff.md

Run the verification checklist:
1. Backend starts without errors
2. Frontend compiles
3. Quiz captures existing_stack
4. Report generates with Connect vs Replace
5. Automation summary appears

Document any issues found. Fix critical blockers.
```

---

### Workstream 2: Output Quality Audit
**Priority:** HIGH
**Can parallelize:** Yes (after Workstream 1)

```
# Report Quality Audit

Audit the current report output for quality issues.

## Task
1. Generate a test report (dental practice, mid-size, with existing stack)
2. Review each section critically:
   - Are findings specific or generic?
   - Are numbers real or made up?
   - Do recommendations have clear reasoning?
   - Is the Connect vs Replace analysis actually useful?

## Red Flags to Look For
- Generic statements: "AI can help streamline operations"
- Unsubstantiated numbers: "Save 40% on costs" (where did 40% come from?)
- Missing context: Recommendations that ignore their existing stack
- No trade-offs: Everything sounds positive, no risks mentioned
- Buzzword soup: "leverage", "optimize", "streamline" without specifics

## Output
Create docs/audits/2026-01-07-report-quality-audit.md with:
- Screenshot/excerpt of each problematic section
- What's wrong with it
- How it should look instead
- Priority (critical/high/medium)

## Files to Review
- backend/src/skills/report-generation/*.py
- backend/src/prompts/ (if exists)
- Any finding/recommendation generation code
```

---

### Workstream 3: CRB Framework for Findings
**Priority:** HIGH
**Can parallelize:** Yes

```
# Implement Cost-Risk-Benefit Framework

Every finding recommendation must include CRB analysis.

## The Framework

For each recommendation (Connect or Replace):

### COST
- Implementation cost (one-time)
  - DIY: hours × assumed rate (€50/hr for business owner time)
  - Professional: actual service costs
- Ongoing cost (monthly)
  - Software subscriptions
  - API usage (estimate based on volume)
  - Maintenance time
- Hidden costs
  - Training time
  - Productivity dip during transition

### RISK
- Implementation risk (1-5)
  - 1 = Plug and play
  - 5 = Complex migration, data loss possible
- Dependency risk
  - What if the vendor goes down?
  - What if API changes?
- Reversal difficulty
  - How hard to undo if it doesn't work?

### BENEFIT
- Primary metric improved (quantified)
  - "Reduce no-shows from 18% to 6%" not "reduce no-shows"
- Monthly value (€)
  - Show the math: "12% reduction × €350/appointment × 100 appointments = €4,200"
- Time savings (hours/month)
- Qualitative benefits (customer satisfaction, staff morale)

### RECOMMENDATION
- Clear verdict: "We recommend X"
- Confidence: High/Medium/Low based on:
  - Data quality (did they give us real numbers?)
  - Stack compatibility (do we know their tools?)
  - Industry benchmarks (do we have comparison data?)
- Caveat if confidence is low

## Implementation

1. Update finding generation prompts to require CRB sections
2. Create CRB calculation helpers:
   - estimate_implementation_cost(approach, complexity)
   - estimate_ongoing_cost(tools, volume)
   - calculate_benefit(metric, baseline, improvement, value_per_unit)
3. Add risk scoring logic
4. Update report templates to display CRB clearly

## Files to Modify
- backend/src/skills/report-generation/finding_generation.py
- backend/src/models/report.py (add CRB models)
- frontend report components (display CRB)

## Example Output

FINDING: High No-Show Rate (18%)

CONNECT PATH: Open Dental → n8n → Twilio

┌─────────────────────────────────────────────────────────┐
│ COST                                                    │
├─────────────────────────────────────────────────────────┤
│ Implementation: €400 (8 hrs × €50/hr DIY)              │
│ Monthly: €32 (Twilio ~€25 + n8n cloud €7)              │
│ Hidden: 2 hrs/month monitoring                          │
├─────────────────────────────────────────────────────────┤
│ RISK                                                    │
├─────────────────────────────────────────────────────────┤
│ Implementation: 2/5 (API well-documented)               │
│ Dependency: Low (can switch SMS providers)              │
│ Reversal: Easy (just disable workflow)                  │
├─────────────────────────────────────────────────────────┤
│ BENEFIT                                                 │
├─────────────────────────────────────────────────────────┤
│ No-show reduction: 18% → 8% (industry benchmark)        │
│ Monthly value: €3,500 (10% × €350 × 100 appointments)  │
│ ROI: 109x (€3,500 benefit ÷ €32 cost)                  │
├─────────────────────────────────────────────────────────┤
│ RECOMMENDATION: CONNECT ✓                               │
│ Confidence: HIGH                                        │
│ Your stack supports this. Low risk, high ROI.           │
└─────────────────────────────────────────────────────────┘
```

---

### Workstream 4: Industry Benchmarks Audit
**Priority:** MEDIUM
**Can parallelize:** Yes

```
# Audit Industry Benchmarks

Our recommendations need real data, not made-up numbers.

## Task
1. Review backend/src/knowledge/ for industry benchmarks
2. For each industry we support:
   - dental
   - recruiting
   - home-services
   - professional-services
   - coaching
   - veterinary
   - physical-therapy
   - medspa

3. Check each benchmark:
   - Does it have a source?
   - Is the source credible?
   - Is it dated? (data from 2020 is stale)
   - Is it specific enough?

## Red Flags
- "Industry average is 15%" (source?)
- Old data (pre-2024)
- US-only data applied to EU clients
- Aggregated data that hides variation

## Output
Create docs/audits/2026-01-07-benchmark-audit.md:
- List all benchmarks used
- Source status: Verified / Unverified / Missing
- Recommendations for each (find better source, mark as estimate, remove)

## Improvement
For unverified benchmarks, either:
1. Find real source (industry reports, studies)
2. Mark clearly as "estimate" in reports
3. Use ranges instead of specific numbers
4. Ask user for their actual numbers in quiz
```

---

### Workstream 5: Populate Vendor API Scores
**Priority:** MEDIUM
**Can parallelize:** Yes

```
# Populate Vendor API Openness Scores

188 vendors need API scores for Connect vs Replace to work properly.

## Task
1. Run audit to see current state:
   cd backend && source venv/bin/activate
   python -m src.scripts.audit_vendor_apis stats

2. Prioritize vendors by:
   - Most recommended in reports
   - Most common in user stacks
   - Industry-specific tools (dental PMS, recruiting ATS)

3. Research and rate each vendor:
   - Check their API documentation
   - Look for Zapier/Make/n8n integrations
   - Check for webhooks, OAuth support
   - Rate 1-5 based on criteria in design doc

## Rating Criteria
5 = Full REST API + webhooks + OAuth (Stripe, Twilio, HubSpot)
4 = Good API, some limitations (Salesforce, Zendesk)
3 = Basic API, limited endpoints (many dental PMS)
2 = Zapier/Make only, no direct API
1 = Closed system, no integrations

## Commands
# Rate a vendor
python -m src.scripts.audit_vendor_apis rate <slug> <score>

# Or use Admin UI
/admin/vendors → Edit → API & Integration section

## Goal
Get to 80%+ coverage (160+ vendors rated)
Prioritize industry-specific vendors first
```

---

### Workstream 6: Quiz Question Quality
**Priority:** MEDIUM
**Can parallelize:** Yes

```
# Audit Quiz Questions

Better input = better output. Are we asking the right questions?

## Task
1. Review current quiz flow (frontend/src/pages/Quiz.tsx)
2. Map each question to how it's used in report generation
3. Identify gaps:
   - What do we assume that we should ask?
   - What do we ask that we don't use?
   - Are questions clear to non-technical users?

## Key Questions to Evaluate
- Do we ask about their ACTUAL metrics? (not just "how's your no-show rate" but "what % is your no-show rate")
- Do we ask about budget constraints?
- Do we ask about technical capability? (can they use n8n or need no-code)
- Do we ask about timeline? (urgent vs planning ahead)
- Do we ask about past automation attempts? (what failed before)

## Output
Create docs/audits/2026-01-07-quiz-audit.md:
- Current questions list
- Gap analysis
- Recommended additions/changes
- Priority for each change

## Principle
Every question should either:
1. Directly improve report quality
2. Personalize recommendations
3. Qualify the lead for tier recommendation

No vanity questions.
```

---

### Workstream 7: Prompt Engineering Audit
**Priority:** HIGH
**Can parallelize:** Yes (after Workstream 2)

```
# Audit and Improve Generation Prompts

The prompts determine output quality. Make them rigorous.

## Task
1. Find all prompts used in report generation:
   - backend/src/skills/report-generation/*.py
   - backend/src/prompts/ (if exists)
   - Inline prompts in services

2. For each prompt, evaluate:
   - Does it demand specificity? ("provide exact numbers" vs "estimate")
   - Does it require sources/reasoning?
   - Does it prevent generic output?
   - Does it use the user's actual data?

## Anti-Patterns to Fix
- "Generate recommendations for..." (too open)
- No constraints on format
- No requirement to use provided data
- No instruction to admit uncertainty

## Good Patterns to Implement
- "Use ONLY the following data: {data}. Do not make up numbers."
- "If you cannot calculate a specific value, say 'insufficient data' and explain what's needed"
- "For each recommendation, you MUST include: [cost breakdown], [risk assessment], [quantified benefit]"
- "Do not use these words: leverage, optimize, streamline, cutting-edge, revolutionary"

## Output
Create docs/audits/2026-01-07-prompt-audit.md:
- List of all prompts
- Issues found
- Rewritten versions
- Test results (before/after comparison)
```

---

## Dependency Graph

```
                    ┌─────────────────┐
                    │ 1. Verify       │
                    │ Implementation  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │ 2. Output  │  │ 5. Vendor  │  │ 6. Quiz    │
     │ Quality    │  │ API Scores │  │ Questions  │
     │ Audit      │  │            │  │            │
     └─────┬──────┘  └────────────┘  └────────────┘
           │
           ▼
     ┌────────────┐
     │ 7. Prompt  │
     │ Audit      │
     └─────┬──────┘
           │
           ▼
     ┌────────────┐
     │ 3. CRB     │
     │ Framework  │
     └────────────┘
           │
           ▼
     ┌────────────┐
     │ 4. Industry│
     │ Benchmarks │
     └────────────┘
```

**Can run in parallel:**
- 5, 6 (independent data tasks)
- 2, then 7 → 3 → 4 (quality improvement chain)

---

## Success Criteria

A report is NOT AI slop when:

1. **Numbers are real or clearly marked as estimates**
   - ✓ "Based on your 18% no-show rate..."
   - ✗ "Typically businesses see 15-20% improvement..."

2. **Recommendations reference their actual stack**
   - ✓ "Since you use Open Dental (API 4/5), you can..."
   - ✗ "Consider implementing a modern PMS..."

3. **Trade-offs are explicit**
   - ✓ "Risk: 3/5 — requires API knowledge, 4 hrs if issues"
   - ✗ "Easy to implement with minimal effort"

4. **Confidence is stated**
   - ✓ "Confidence: MEDIUM — based on industry benchmarks, not your data"
   - ✗ "You will definitely see results"

5. **CRB is complete**
   - ✓ Cost breakdown, risk assessment, quantified benefit
   - ✗ "This will save you time and money"

---

## Quick Start

**Session 1 (do first):**
```
Read docs/handoffs/2026-01-07-master-roadmap.md
Execute Workstream 1: Verify Implementation
Report any blockers.
```

**Sessions 2-4 (parallel):**
```
Read docs/handoffs/2026-01-07-master-roadmap.md
Execute Workstream [2|5|6] (pick one not being worked on)
```

**Sessions 5-7 (after audits complete):**
```
Read docs/handoffs/2026-01-07-master-roadmap.md
Execute Workstream [3|4|7] based on audit findings
```
