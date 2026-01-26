# System Audit Prompts

Use these prompts in separate Claude Code sessions to audit different parts of the CRB Analyser system for flaws, inconsistencies, and bugs.

---

## 1. ROI & Math Calculations Audit

**Context to load:** `backend/src/skills/analysis/roi_calculator.py`, `backend/src/services/report_service.py`

```
Audit the ROI and math calculation system in CRB Analyser.

KNOWN ISSUE: The LLM prompt at line ~2059 in report_service.py asks the LLM to generate roi_percentage without providing a formula. This causes inconsistent values.

Your task:
1. Read roi_calculator.py completely - document the exact formulas used
2. Search report_service.py for ALL places where roi_percentage or payback_months are set
3. Identify every code path that generates ROI values
4. Check if the ROI Calculator Skill is always called, or only sometimes
5. Document the correct formulas that SHOULD be used everywhere:
   - annual_savings = hours_per_week × hourly_rate × 52
   - roi_percentage = (net_annual / first_year_investment) × 100
   - payback_months = implementation_cost / (net_annual / 12)

FIX REQUIRED:
- Remove roi_percentage and payback_months from LLM prompts
- Ensure ROI Calculator Skill is called for EVERY recommendation
- Update validators to match the canonical formulas

Output: List of all files changed and the specific fixes made.
```

---

## 2. Finding Generation Audit

**Context to load:** `backend/src/skills/report-generation/finding_generation.py`, `backend/src/services/report_service.py`

```
Audit the finding generation system in CRB Analyser.

Questions to answer:
1. How are findings generated? (LLM prompt? Skill? Both?)
2. Where does value_saved.hours_per_week come from? Is it calculated or LLM-generated?
3. Where does value_saved.hourly_rate come from? Is it from quiz answers or assumed?
4. Is value_saved.annual_savings calculated deterministically or LLM-generated?
5. Are finding categories validated against the allowed list?
6. Are confidence levels validated?

Check for:
- LLM prompts asking for numeric values without formulas
- Missing validation of required fields
- Inconsistent category names
- Duplicate finding IDs

Expected structure for each finding:
{
  "id": "unique",
  "title": "string",
  "description": "string",
  "category": "operations|sales|customer_experience|finance|marketing|hr|compliance|technology",
  "value_saved": {
    "hours_per_week": <from quiz or calculated>,
    "hourly_rate": <from quiz or default>,
    "annual_savings": <MUST be hours × rate × 52>
  },
  "confidence": "high|medium|low",
  "sources": ["at least one source"]
}

Output: List of issues found and recommended fixes.
```

---

## 3. Three Options Generation Audit

**Context to load:** `backend/src/skills/report-generation/three_options.py`, `backend/src/skills/report-generation/four_options.py`

```
Audit the options generation system in CRB Analyser.

Each recommendation should have 3 options:
1. off_the_shelf - Quick, cheap, good enough
2. best_in_class - Premium, more features
3. custom_solution - Build it yourself

Questions to answer:
1. How are vendor names selected? From knowledge base or LLM hallucination?
2. How is pricing determined? Real data or LLM-generated?
3. Are implementation_weeks realistic?
4. Is the custom_solution properly structured with build_tools, skills_required, etc?

Check for:
- Vendors that don't exist in our knowledge base
- Pricing that seems made up (round numbers like $100, $200, $500)
- Missing required fields in options
- Inconsistent structure between off_the_shelf and best_in_class

Validate against vendor database at: backend/src/knowledge/*/vendors.json

Output: List of issues and recommendations for improving vendor/pricing accuracy.
```

---

## 4. Executive Summary Generation Audit

**Context to load:** `backend/src/skills/report-generation/exec_summary.py`, `backend/src/services/report_service.py`

```
Audit the executive summary generation in CRB Analyser.

Required fields:
- ai_readiness_score (0-100)
- customer_value_score
- business_health_score
- key_insight
- total_value_potential (min, max, projection_years)
- top_opportunities (array)
- not_recommended (array)
- recommended_investment (year_1_min, year_1_max)
- verdict (recommendation, headline, reasoning, confidence)

Questions to answer:
1. How is ai_readiness_score calculated? Formula or LLM guess?
2. How is total_value_potential derived? Sum of findings or separate calculation?
3. Is verdict.recommendation one of: proceed|proceed_with_caution|wait|not_recommended?
4. Are the top_opportunities actually the top ones by value?
5. Does recommended_investment match the sum of recommendation costs?

Check for:
- Scores outside valid ranges
- total_value_potential that doesn't match sum of findings
- Inconsistent verdict reasoning
- Missing required fields

Output: Validation rules that should be added and any bugs found.
```

---

## 5. Playbook Generation Audit

**Context to load:** `backend/src/services/playbook_generator.py`, `backend/src/skills/analysis/playbook_generator.py`

```
Audit the playbook generation system in CRB Analyser.

Expected structure:
- playbook has phases
- each phase has tasks
- each task has: id, title, hours, owner, difficulty, dependencies
- dependencies reference existing task IDs
- no circular dependencies

Questions to answer:
1. How are task hours estimated? Formula or LLM guess?
2. Are dependencies validated to reference existing tasks?
3. Is there cycle detection for dependencies?
4. Do phase durations match the sum of task hours?
5. Are owner assignments realistic for the company's team size?

Check for:
- Tasks with 0 hours or negative hours
- Tasks with > 40 hours (should be broken down)
- Invalid dependency references
- Circular dependencies
- Phase duration mismatches

Output: List of validation rules needed and any bugs in generation.
```

---

## 6. Knowledge Base Consistency Audit

**Context to load:** `backend/src/knowledge/__init__.py`

```
Audit the knowledge base for consistency and completeness.

For each industry folder (dental, home-services, veterinary, coaching, recruiting, professional-services):
1. Check required files exist: vendors.json, processes.json, benchmarks.json, opportunities.json
2. Check "industry" field matches folder name in all files
3. Check all benchmarks have "source" fields
4. Check vendors have: name, website, pricing, best_for
5. Check pricing has verification dates < 90 days old
6. Check opportunities match the expected categories

Cross-reference:
- Vendors mentioned in reports should exist in knowledge base
- Industry categories should be consistent
- Pricing should be realistic for the market

Run these bash commands to check:
- List all industries: ls backend/src/knowledge/
- Check for missing files in each
- Grep for "source" fields in benchmarks
- Check verification_status fields

Output: List of missing data, stale data, and inconsistencies.
```

---

## 7. Quiz → Report Data Flow Audit

**Context to load:** `backend/src/services/report_service.py`, `backend/src/routes/quiz.py`

```
Audit how quiz answers flow into report generation.

Data should flow:
quiz_answers → company_profile → findings → recommendations → playbooks

Questions to answer:
1. Which quiz answers are actually used in report generation?
2. Is team_size/employee_count used to validate hours saved?
3. Is budget_range used to filter recommendations?
4. Is tech_level used to adjust complexity of suggestions?
5. Are existing_tools checked against our vendor database?
6. Is industry properly normalized and matched?

Check for:
- Quiz answers that are collected but never used
- Missing validation of quiz answer formats
- Industry names that don't match knowledge base folders
- Existing tools that should influence recommendations but don't

Output: Map of quiz fields → where they're used → validation needed.
```

---

## 8. Vendor Matching Audit

**Context to load:** `backend/src/skills/analysis/vendor_matching.py`, `backend/src/services/vendor_service.py`

```
Audit the vendor matching system.

When generating recommendations, vendors should be:
1. Selected from knowledge base (not hallucinated)
2. Appropriate for the industry
3. Appropriate for company size
4. Within budget range
5. Compatible with existing tools

Questions to answer:
1. Does vendor_matching actually query the knowledge base?
2. Are tier rankings (T1/T2/T3) used correctly?
3. Is pricing accurate and from verified sources?
4. Are competitors avoided when existing_tools are specified?
5. Are integrations checked for compatibility?

Check for:
- Vendors recommended that don't exist in our database
- Wrong tier vendors for company size
- Pricing that doesn't match knowledge base
- Missing integration compatibility checks

Output: List of improvements needed for vendor selection accuracy.
```

---

## Usage Instructions

1. Start a new Claude Code session
2. Copy ONE prompt above
3. Run `/prime` first if needed for context
4. Paste the prompt
5. Let Claude investigate and fix issues
6. Document findings in the same session

**Important:** Run these in separate sessions to keep context focused. Each audit may require reading multiple files.
