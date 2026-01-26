# Sample Report Validation Prompt

Use this prompt with the sample report JSON to validate accuracy and consistency.

---

## Prompt for Codex

```
You are a senior business analyst and data quality auditor. I need you to thoroughly validate this CRB (Cost-Risk-Benefit) analysis report for a New Zealand construction business called "Friendly Build & Fix".

The report will be shown to prospective customers as a sample of our AI-powered business analysis. It must be 100% accurate, internally consistent, and realistic.

## Validation Tasks

### 1. NUMBER CONSISTENCY CHECK
Verify all numbers add up correctly:
- [ ] `value_summary.total` (min: 53000, max: 87000) should equal `value_saved.subtotal` + `value_created.subtotal`
- [ ] `total_value_potential` 3-year projection (159000-261000) should be 3x the annual total
- [ ] `hours_per_week` (12) should match sum of hours in findings (f1: 6hrs + f2: 4hrs + f3: 2.5hrs = 12.5hrs)
- [ ] Each finding's `annual_savings` should equal `hours_per_week * hourly_rate * 52`
- [ ] `top_opportunities` value ranges should align with corresponding findings
- [ ] `automation_summary.total_monthly_impact` (5925) should equal sum of all opportunity `impact_monthly` values
- [ ] ROI percentages and payback months should be mathematically correct

### 2. CRB ANALYSIS VALIDATION
For each recommendation:
- [ ] Does `crb_analysis.cost.total` match setup + (monthly * 36 months)?
- [ ] Does `crb_analysis.benefit.total` match 3 years of annual benefits?
- [ ] Is ROI percentage = (benefit.total - cost.total) / cost.total * 100?
- [ ] Does payback_months = cost.total / (benefit.short_term.annual / 12)?

### 3. NZ CONSTRUCTION CONTEXT
Verify realistic NZ market data:
- [ ] Are vendor prices (Buildxact $129/mo, Fergus $79/mo, Tradify $59/mo) accurate for NZ market 2025-2026?
- [ ] Are hourly rates ($85 builder, $65 admin) realistic for NZ small trades?
- [ ] Are the NZ-specific vendors mentioned (Fergus, Tradify, Buildxact) actually available in NZ?
- [ ] Do suppliers mentioned (PlaceMakers, ITM) exist in NZ?
- [ ] Is "Warkworth, New Zealand" a real location?
- [ ] Are industry adoption percentages (34% job management, 28% digital quoting) plausible?

### 4. CONTENT QUALITY
Review for clarity and persuasiveness:
- [ ] Is the `key_insight` compelling and specific to this business?
- [ ] Do findings tell a coherent story about the business's pain points?
- [ ] Are recommendations actionable with clear next steps?
- [ ] Does the verdict reasoning make sense given the data?
- [ ] Are social proof quotes believable and relevant?

### 5. DATA STRUCTURE COMPLETENESS
Check for missing or empty fields:
- [ ] Do all findings have: id, title, description, category, value_saved OR value_created, confidence, sources?
- [ ] Do all recommendations have: id, title, description, priority, crb_analysis, options (3), our_recommendation, assumptions?
- [ ] Do all playbook tasks have: id, title, hours/time_estimate, owner, difficulty?
- [ ] Does system_architecture have: existing_tools, ai_layer, automations, connections, cost_comparison?

### 6. LOGICAL CONSISTENCY
Check for contradictions:
- [ ] If "12+ hours weekly" is mentioned, do the findings support this?
- [ ] If verdict is "proceed" with "high confidence", does the data justify this?
- [ ] Do playbook task dependencies make sense (can't do t3 before t1)?
- [ ] Does the roadmap timeline align with playbook total_weeks?

### 7. CURRENCY CONSISTENCY
- [ ] All monetary values should be in NZD ($), not EUR (€)
- [ ] Currency symbol usage is consistent throughout

## Output Format

Please provide:

1. **PASS/FAIL** for each validation category
2. **Specific errors found** with line references
3. **Recommended fixes** for any issues
4. **Overall quality score** (1-10)
5. **Summary** of whether this report is ready for customer-facing use

---

## The Report JSON

[PASTE THE FULL JSON FROM docs/sample_report_full.json HERE]
```

---

## Quick Copy Version

For faster use, here's a condensed prompt:

```
Validate this CRB analysis report for a NZ construction business. Check:

1. NUMBER CONSISTENCY: Do all values add up? (annual savings, totals, ROI calculations)
2. CRB MATH: Are cost/benefit calculations correct over 3 years?
3. NZ CONTEXT: Are vendor prices, hourly rates, and market data realistic for NZ 2025-2026?
4. CONTENT: Is it compelling, specific, and actionable?
5. COMPLETENESS: Any missing fields or empty data?
6. LOGIC: Any contradictions between sections?
7. CURRENCY: All in NZD ($), no EUR (€)?

Provide: PASS/FAIL per category, specific errors, fixes needed, overall score (1-10).

[PASTE JSON]
```
