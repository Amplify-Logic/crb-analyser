# Quiz Question Quality Audit

**Date:** 2026-01-07
**Auditor:** Claude Code (Workstream 6)
**Status:** Complete

---

## Executive Summary

The current quiz system is **sophisticated but has critical gaps** that prevent high-quality CRB analysis. The main issues:

1. **We ask for ranges, not exact numbers** - Can't calculate precise ROI
2. **We don't ask about past automation failures** - Miss learning from their experience
3. **Budget questions are too vague** - Can't recommend appropriate solutions
4. **Technical capability is assumed**, not measured

**Impact:** Reports feel generic because we're inferring rather than knowing.

---

## Current Quiz Architecture

### Data Collection Flow

```
Website URL → PreResearchAgent (scrape) → Company Profile
                     ↓
              Existing Stack Selection (software picker)
                     ↓
              Dynamic Questions (AI-generated OR industry bank)
                     ↓
              [Optional] Voice Interview
                     ↓
              Report Generation
```

### Question Sources (4 systems)

| Source | Location | Questions |
|--------|----------|-----------|
| Static Questionnaire | `backend/src/config/questionnaire.py` | ~25 generic questions |
| Industry Banks | `backend/src/knowledge/industry_questions/*.json` | 15-20 per industry |
| Dynamic Questions | `PreResearchAgent._generate_questionnaire()` | AI-generated from research |
| Adaptive Quiz | `quiz_engine.py` | Confidence-gap-driven |

### Currently Supported Industries

- Dental (comprehensive bank)
- Recruiting (comprehensive bank)
- Professional Services (basic bank)
- Coaching (basic bank)
- Home Services (basic bank)
- Veterinary (basic bank)

---

## Current Questions Analysis

### Section 1: Company Overview (questionnaire.py)

| Question ID | Question | Used In Report? | Gap |
|-------------|----------|-----------------|-----|
| `company_description` | Describe what your company does | Yes, for context | **Underutilized** - could extract pain points |
| `employee_count` | How many employees? | Yes | Good - but ranges, not exact |
| `annual_revenue` | Approximate annual revenue | Partially | **Optional** - should be required for ROI |
| `primary_goals` | Business goals for next 12 months | Partially | **Underutilized** - not tied to finding priority |

### Section 2: Current Operations

| Question ID | Question | Used In Report? | Gap |
|-------------|----------|-----------------|-----|
| `main_processes` | Main business processes | Yes | Good but open-ended |
| `repetitive_tasks` | What repetitive tasks? | Yes | Good |
| `biggest_bottlenecks` | Operational bottlenecks | Yes | Good |
| `time_on_admin` | Hours/week on admin tasks | **Critical** | **Exact number** - this is gold! More like this |
| `manual_data_entry` | Manual data entry between systems? | Yes | Good with follow-up |

### Section 3: Technology & Tools

| Question ID | Question | Used In Report? | Gap |
|-------------|----------|-----------------|-----|
| `current_tools` | Software tools used | Partially | **Superseded** by existing_stack picker |
| `tool_pain_points` | Frustrations with tools | Yes | Good |
| `integration_issues` | Do tools integrate? (1-10) | Partially | **Vague** - what does "7" mean? |
| `technology_comfort` | Team comfort with new tech (1-10) | Partially | **Too subjective** |
| `ai_tools_used` | AI tools used | Partially | **Good for segmentation** |

### Section 4: Pain Points & Challenges

| Question ID | Question | Used In Report? | Gap |
|-------------|----------|-----------------|-----|
| `biggest_challenge` | Single biggest challenge | Yes | Good |
| `time_wasters` | Tasks that feel like waste | Yes | Good |
| `missed_opportunities` | Opportunities missed | Optional | **Should be required** |
| `cost_concerns` | Which costs concern most | Partially | Good for prioritization |
| `quality_issues` | Experience quality issues? | Yes | Good with follow-up |

### Section 5: AI & Automation Readiness

| Question ID | Question | Used In Report? | Gap |
|-------------|----------|-----------------|-----|
| `ai_interest_areas` | Areas to automate | Yes | Good |
| `budget_for_solutions` | Budget for new tools | **Critical** | **Too vague** - ranges too wide |
| `implementation_timeline` | How quickly want improvements | Yes | **Missing WHY** |
| `decision_makers` | Who makes tech decisions | Partially | **Missing process details** |
| `additional_context` | Anything else | Optional | Fine |

---

## Industry-Specific Questions (Dental Example)

The dental question bank is excellent. Key features:

**Strengths:**
- Asks for **exact metrics**: patient volume, no-show rate, case acceptance
- **Deep dive triggers**: If no-show > 20%, asks follow-up
- **Category targeting**: Questions map to confidence categories
- **Woven confirmations**: "Since you use [tool], how's that working?"

**Weaknesses:**
- No budget questions
- No past automation attempt questions
- No technical capability assessment

### Sample Strong Questions (dental.json)

```json
{
  "id": "patient_volume_weekly",
  "question": "How many patients does your practice see per week?",
  "input_type": "number",
  "placeholder": "e.g., 150"
}
```
This is **excellent** - exact number, not a range.

```json
{
  "id": "no_show_rate",
  "question": "What's your approximate patient no-show rate?",
  "input_type": "select",
  "deep_dive_triggers": ["20_30", "over_30"]
}
```
Good - has ranges but triggers deep dive for problem cases.

---

## Critical Gaps (Must Fix)

### Gap 1: We Don't Ask for Actual Numbers

**Problem:** Report generation needs exact numbers for ROI calculations, but we ask for ranges.

**Current:**
```
"What is your approximate annual revenue?"
Options: Under €100K, €100K-€500K, €500K-€1M, €1M-€5M, €5M+
```

**Report Needs:**
- Exact revenue for ROI percentage calculations
- Exact hours for time savings
- Exact costs for cost reduction estimates

**Fix - Add Quantifiable Questions:**

| New Question | Purpose | Priority |
|--------------|---------|----------|
| "What is your monthly revenue (approximate)?" | Calculate % impact | HIGH |
| "How many hours/week does your team spend on [task]?" | Calculate time savings | HIGH |
| "What is the average value of [customer/patient/client]?" | Calculate retention value | HIGH |
| "How many [customers/patients] do you handle per month?" | Calculate volume impact | HIGH |

**Implementation:**
1. Add to `questionnaire.py` section 2
2. Make them required (not optional)
3. Use NUMBER type, not SELECT

---

### Gap 2: No Past Automation Attempt Questions

**Problem:** We have no idea what they've tried before, what worked, and what failed. This leads to:
- Recommending tools they've already rejected
- Missing context on why simple solutions haven't worked
- Not learning from their experience

**Fix - Add These Questions:**

```python
{
    "id": "past_automation_attempts",
    "question": "Have you tried to automate any processes before?",
    "type": QuestionType.YES_NO,
    "required": True,
    "follow_up": {
        "condition": "yes",
        "question_id": "past_automation_what",
        "question": "What did you try to automate, and how did it go?",
        "type": QuestionType.TEXTAREA,
    },
},
{
    "id": "automation_failures",
    "question": "What tools or approaches didn't work out for you?",
    "type": QuestionType.TEXTAREA,
    "required": False,
    "placeholder": "E.g., 'Tried Zapier but too complex', 'Hired a consultant but too expensive'",
},
```

**Priority:** HIGH - This prevents embarrassing recommendations.

---

### Gap 3: Budget Questions Too Vague

**Problem:** Current budget question has ranges too wide to be useful.

**Current:**
```
Options: Under €100/month, €100-500/month, €500-1,000/month, €1,000-5,000/month, €5,000+/month
```

**Issues:**
- €100-500 spans 5x difference
- No distinction between tool budget and implementation budget
- No risk tolerance assessment

**Fix - Split Into Three Questions:**

```python
{
    "id": "monthly_tool_budget",
    "question": "What's your budget for new software subscriptions? (per month)",
    "type": QuestionType.NUMBER,
    "required": True,
    "placeholder": "e.g., 200",
},
{
    "id": "implementation_budget",
    "question": "What one-time budget could you allocate for setup and integration?",
    "type": QuestionType.SELECT,
    "required": True,
    "options": [
        {"value": "under_500", "label": "Under €500 (DIY only)"},
        {"value": "500_2000", "label": "€500-2,000 (some help)"},
        {"value": "2000_10000", "label": "€2,000-10,000 (professional setup)"},
        {"value": "10000_plus", "label": "€10,000+ (full implementation)"},
    ],
},
{
    "id": "risk_tolerance",
    "question": "How would you describe your appetite for change?",
    "type": QuestionType.SELECT,
    "required": True,
    "options": [
        {"value": "conservative", "label": "Conservative - proven solutions only"},
        {"value": "moderate", "label": "Moderate - willing to try new things with support"},
        {"value": "aggressive", "label": "Aggressive - happy to experiment and iterate"},
    ],
},
```

**Priority:** HIGH - Directly affects recommendations.

---

### Gap 4: Technical Capability Not Assessed

**Problem:** We recommend n8n workflows to people who can't use them.

**Current:**
```
"technology_comfort" (1-10 scale) - Too vague
```

**Fix - Add Specific Assessment:**

```python
{
    "id": "tech_resources",
    "question": "Who would implement new technology solutions?",
    "type": QuestionType.SELECT,
    "required": True,
    "options": [
        {"value": "self_technical", "label": "I would - I'm comfortable with technology"},
        {"value": "self_non_technical", "label": "I would - but I'd need simple/guided solutions"},
        {"value": "internal_it", "label": "Our internal IT team"},
        {"value": "external", "label": "We'd hire someone"},
    ],
},
{
    "id": "integration_capability",
    "question": "Have you or your team used any automation/integration tools?",
    "type": QuestionType.MULTI_SELECT,
    "required": True,
    "options": [
        {"value": "zapier", "label": "Zapier"},
        {"value": "make", "label": "Make (Integromat)"},
        {"value": "n8n", "label": "n8n"},
        {"value": "power_automate", "label": "Power Automate"},
        {"value": "native", "label": "Built-in integrations only"},
        {"value": "none", "label": "None"},
    ],
},
```

**Priority:** HIGH - Affects Connect vs Replace recommendations.

---

### Gap 5: Timeline Without Context

**Problem:** We know they want results "ASAP" but not why.

**Fix - Add Context Questions:**

```python
{
    "id": "timeline_driver",
    "question": "What's driving your timeline?",
    "type": QuestionType.SELECT,
    "required": False,
    "condition": {"question": "implementation_timeline", "values": ["asap", "1_3_months"]},
    "options": [
        {"value": "pain_severe", "label": "Current pain is severe - need relief"},
        {"value": "growth", "label": "We're growing and need to scale"},
        {"value": "leaving_staff", "label": "Key person leaving / knowledge loss"},
        {"value": "budget_expiring", "label": "Budget available now"},
        {"value": "competitor", "label": "Competition is pulling ahead"},
        {"value": "other", "label": "Other reason"},
    ],
},
```

**Priority:** MEDIUM - Helps prioritize recommendations.

---

## Questions Asked But Not Used Effectively

### `primary_goals` (underutilized)

**Current Usage:** Stored but not weighted in finding generation.

**Should:**
- Weight findings that align with stated goals higher
- Add to finding generation prompt: "Their primary goals are: {goals}. Prioritize findings that directly serve these goals."

### `missed_opportunities` (optional)

**Current:** Optional, often skipped.

**Should:**
- Make required (rich source of pain points)
- Use in finding generation as direct opportunities

### `integration_issues` scale

**Problem:** A "7" means different things to different people.

**Fix:** Replace with concrete question:
```
"Which of these integration challenges do you face?"
- Manual copy/paste between systems
- Data doesn't sync automatically
- Have to export/import files
- Different data in different systems
- None - everything flows smoothly
```

---

## Questions That Are Unclear to Users

### Problem Questions

1. **"Integration issues" scale (1-10)**
   - Non-technical users don't know what "integrated" means
   - Replace with concrete examples (above)

2. **"AI tools used"**
   - Users don't know ChatGPT in browser counts
   - Add examples: "E.g., ChatGPT, Grammarly, autocomplete features"

3. **"Technology comfort" scale**
   - Too abstract
   - Replace with "What's the most complex tool you've set up yourself?"

### Improvement Principle

Every question should either:
1. **Directly provide data for ROI calculations**
2. **Personalize recommendations to their situation**
3. **Qualify them for the right service tier**

No vanity questions. No abstract scales.

---

## Recommendations Summary

### Priority: CRITICAL (Do First)

| Change | Impact | Effort |
|--------|--------|--------|
| Add exact revenue/hours questions | Precise ROI | Low |
| Add past automation attempt questions | Avoid bad recommendations | Low |
| Split budget into 3 specific questions | Right-sized recommendations | Low |

### Priority: HIGH

| Change | Impact | Effort |
|--------|--------|--------|
| Add technical capability assessment | Better Connect vs Replace | Medium |
| Use `primary_goals` in finding generation | Aligned recommendations | Low |
| Make `missed_opportunities` required | More pain points | Low |

### Priority: MEDIUM

| Change | Impact | Effort |
|--------|--------|--------|
| Add timeline context question | Better prioritization | Low |
| Replace scale questions with concrete options | Clearer data | Medium |
| Expand industry question banks | Better industry fit | High |

---

## Implementation Files to Modify

| File | Change |
|------|--------|
| `backend/src/config/questionnaire.py` | Add new questions |
| `backend/src/knowledge/industry_questions/*.json` | Add missing questions to all banks |
| `backend/src/skills/report-generation/finding_generation.py` | Use goals/past attempts in prompt |
| `frontend/src/pages/Quiz.tsx` | No changes needed (already flexible) |

---

## Verification Checklist

After implementing changes:

- [ ] New questions appear in quiz flow
- [ ] Answers are saved to quiz_sessions
- [ ] Report generation uses new data points
- [ ] ROI calculations use exact numbers when available
- [ ] Past automation attempts influence recommendations
- [ ] Technical capability affects Connect vs Replace

---

## Appendix: Full Question Inventory

### questionnaire.py - 25 questions

1. company_description (textarea, required)
2. employee_count (select, required)
3. annual_revenue (select, optional)
4. primary_goals (multi_select, required)
5. main_processes (textarea, required)
6. repetitive_tasks (textarea, required)
7. biggest_bottlenecks (textarea, required)
8. time_on_admin (number, required)
9. manual_data_entry (yes_no, required)
10. manual_data_entry_details (textarea, conditional)
11. current_tools (multi_select, required)
12. tool_pain_points (textarea, optional)
13. integration_issues (scale, required)
14. technology_comfort (scale, required)
15. ai_tools_used (multi_select, optional)
16. biggest_challenge (textarea, required)
17. time_wasters (textarea, required)
18. missed_opportunities (textarea, optional)
19. cost_concerns (multi_select, required)
20. quality_issues (yes_no, required)
21. quality_issues_details (textarea, conditional)
22. ai_interest_areas (multi_select, required)
23. budget_for_solutions (select, required)
24. implementation_timeline (select, required)
25. decision_makers (select, required)
26. additional_context (textarea, optional)

### dental.json - 15 questions

1. patient_volume_weekly (number)
2. no_show_rate (select + deep dive)
3. scheduling_method (multi_select)
4. insurance_verification (voice)
5. practice_locations (select)
6. front_desk_staff (number)
7. after_hours_calls (select + deep dive)
8. practice_management_system (select)
9. patient_communication_tools (multi_select)
10. biggest_admin_challenge (voice)
11. recall_compliance (select)
12. growth_priority (select)
13. case_acceptance_rate (select + deep dive)
14. ai_readiness (select)
15. budget_timeline (select)

---

*End of Audit*
