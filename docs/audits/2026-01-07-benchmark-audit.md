# Industry Benchmarks Audit

**Date:** 2026-01-07
**Auditor:** Claude Code
**Scope:** All benchmark files in `backend/src/knowledge/`

---

## Executive Summary

The benchmark knowledge base is **largely well-maintained** with verification dates and sources. However, several issues require attention:

1. **Missing Industries:** Physical-therapy and medspa have no benchmark data
2. **Vague Sources:** Many benchmarks cite "Industry benchmarks" without specific citations
3. **Inflated ROI:** Opportunity files contain ROI percentages (800-3100%) that lack credibility checks
4. **Inconsistent Source Specificity:** Some files have excellent source URLs, others have vague citations

**Overall Quality Score:** 7/10 - Good foundation, needs source specificity improvements

---

## Audit by Industry

### 1. Dental (`dental/benchmarks.json`)

**Status:** VERIFIED (2025-12-24)
**Overall Quality:** Good

| Metric Category | Source Quality | Issues |
|-----------------|----------------|--------|
| Financial | Good | "Dental Economics benchmarks" lacks year/URL |
| Operational | Mixed | "Journal of Dental Hygiene, 2024" is good; "Industry benchmarks" is vague |
| AI Adoption | Good | "Dental technology surveys, 2024" lacks specific source name |
| Patient Metrics | Mixed | "Practice analytics data" is vague |
| Staffing | Mixed | "ADA practice surveys" good, but "Dental HR data, 2024" lacks source |

**Specific Issues:**
- `overhead_percentage.source`: "Dental Economics benchmarks" - needs year and URL
- `hygiene_recare_rate.source`: "Industry benchmarks" - needs specific citation
- `new_patients_per_month.source`: "Practice management benchmarks" - vague
- `phone_to_appointment_rate.source`: "Call tracking data, 2024" - which provider?
- `chair_utilization.source`: "Dental practice optimization data" - vague
- `patient_lifetime_value.source`: "Practice analytics data" - vague
- `patient_retention_rate.source`: "Industry benchmarks" - vague
- `front_office_time_on_phone.source`: "Practice efficiency studies" - vague

**ROI Factors:** Good - has realistic ranges

---

### 2. Recruiting (`recruiting/benchmarks.json`)

**Status:** VERIFIED (2025-12-24)
**Overall Quality:** Good

**Positive Notes:**
- Excellent correction note: "Corrected from 87% - actual adoption is 61-67% depending on segment"
- Good specific sources: StaffingHub 2025, LinkedIn Global Talent Intelligence

**Specific Issues:**
- `submit_to_interview_ratio.source`: "Industry benchmarks" - vague
- `interview_to_offer_ratio.source`: "Industry benchmarks" - vague
- `placements_per_recruiter_month.source`: "Industry benchmarks" - vague
- `qualified_candidates_per_req.source`: "Industry data" - vague
- `recruiter_to_coordinator_ratio.source`: "Industry practice" - vague
- `recruiter_turnover.source`: "Staffing Industry Analysts" - good, but needs year

---

### 3. Home Services (`home-services/benchmarks.json`)

**Status:** VERIFIED (2025-12-24)
**Overall Quality:** Good

**Positive Notes:**
- Good verification sources with URLs
- ServiceTitan benchmarks are credible

**Specific Issues:**
- `average_ticket.source`: "Industry averages, 2024" - which industry report?
- `labor_cost_percentage.source`: "Contractor business benchmarks" - vague
- `call_booking_rate.source`: "Industry benchmarks" - vague
- `dispatch_efficiency.source`: "FSM industry data" - vague
- `repeat_customer_rate.source`: "Industry benchmarks" - vague
- `customer_acquisition_cost.source`: "Industry estimates, 2024" - vague
- `fully_loaded_tech_cost.source`: "Industry compensation studies" - vague

---

### 4. Professional Services (`professional-services/benchmarks.json`)

**Status:** VERIFIED (2025-12-27)
**Overall Quality:** Excellent

**Strengths:**
- Detailed verification_sources with name, URL, and accessed date
- Segment-specific benchmarks (legal, accounting, consulting)
- Source URLs for AI adoption rates (ABA, Karbon, McKinsey)
- Regional notes included

**Minor Issues:**
- `billable_hours_target.source`: "Industry standard" - could cite AICPA or ABA directly
- Some `source` fields say "Industry surveys" or "Industry standard"

---

### 5. Coaching (`coaching/benchmarks.json`)

**Status:** VERIFIED (2025-12-24)
**Overall Quality:** Good

**Positive Notes:**
- Good verification sources (ICF Global Coaching Study)
- Market size data is well-sourced

**Specific Issues:**
- `client_retention.source`: "Coaching industry surveys" - vague
- `session_completion.source`: "Scheduling platform data" - which platform?
- `client_lifetime_value.source`: "Industry benchmarks" - vague
- `client_acquisition_cost.source`: "Marketing benchmarks" - vague
- `satisfaction_metrics.source`: "Coaching outcome studies" - vague
- `time_allocation.source`: "Coach productivity studies" - vague

---

### 6. Veterinary (`veterinary/benchmarks.json`)

**Status:** VERIFIED (2025-12-24)
**Overall Quality:** Good

**Positive Notes:**
- Good verification sources (AAHA/Digitail 2024 survey)
- Specific AI adoption percentage (39.2%)

**Specific Issues:**
- `no_show_rate.source`: "Veterinary scheduling studies" - vague
- `client_retention.source`: "Industry benchmarks" - vague
- `new_clients_per_month.source`: "Practice management data" - vague
- `phone_time_daily.source`: "Practice efficiency studies" - vague
- `wellness_compliance.source`: "Veterinary compliance studies" - vague
- `staff_turnover.source`: "Veterinary HR data" - vague
- `new_client_acquisition_cost.source`: "Marketing benchmarks" - vague
- `pet_insurance_penetration.source`: "Insurance industry data, 2024" - which report?

---

### 7. Physical Therapy

**Status:** MISSING
**Action Required:** Create `physical-therapy/benchmarks.json`

Suggested sources to research:
- APTA (American Physical Therapy Association) practice benchmarks
- WebPT industry reports
- Physical therapy billing/revenue cycle benchmarks

---

### 8. Medspa

**Status:** MISSING
**Action Required:** Create `medspa/benchmarks.json`

Suggested sources to research:
- American Med Spa Association (AmSpa) reports
- Medspa revenue and treatment benchmarks
- Aesthetic industry growth data

---

## General Benchmarks (`benchmarks/` directory)

### ecommerce.json
**Status:** Excellent - 2025-12-17
**Quality:** Very High
- Every metric has specific source name, URL, and year
- Well-segmented by company size
- Methodology section included

### tech_saas.json
**Status:** Excellent - 2025-12-17
**Quality:** Very High
- Comprehensive sources (Benchmarkit, High Alpha, SaaS Capital, McKinsey)
- All sources have URLs
- Usage notes included

### professional_services.json (in benchmarks/)
**Status:** Excellent - 2025-01-15
**Quality:** Very High
- Detailed sources with URLs
- Multi-size segmentation
- Industry trends section

---

## Opportunities Files - ROI Analysis

### dental/opportunities.json

**CRITICAL ISSUE:** ROI percentages are extremely high and likely inflated.

| Opportunity | ROI Claimed | Payback | Assessment |
|-------------|-------------|---------|------------|
| AI Voice Receptionist | 837% | 0.5 months | INFLATED - assumes 100% conversion of captured calls |
| Patient Communication | 800% | 0.5 months | INFLATED - 50% no-show reduction is optimistic |
| Insurance Verification | 614% | 1 month | PLAUSIBLE - time savings calculation is reasonable |
| Online Scheduling | 500% | 1 month | NEEDS RANGE - depends heavily on current volume |
| AI Treatment Planning | 2400% | 0.5 months | INFLATED - 10% acceptance increase is assumption |
| Patient Financing | 3100% | 0.5 months | INFLATED - assumes 50% conversion |
| Reputation Management | 1500% | 1 month | NEEDS RANGE - new patient attribution unclear |

**Recommendation:** Add conservative/expected/optimistic ranges, cite industry studies for improvement rates

---

## Red Flags Summary

### 1. Vague Source Pattern
The phrase "Industry benchmarks" or "Industry [X]" appears 25+ times without specific citations.

### 2. Missing Source Years
Several sources cite organizations without years, making freshness impossible to verify.

### 3. Inflated ROI Claims
Opportunity files show ROI percentages of 800-3100% without sensitivity analysis or ranges.

### 4. Geographic Assumptions
Most benchmarks are US-centric but applied to EU clients without adjustment notes.

---

## Recommendations

### Priority 1: Fix Vague Sources (Do Now)
For each "Industry benchmarks" citation:
1. Find a specific source (industry report, survey, or vendor study)
2. Add year and URL where possible
3. If no source exists, mark as "ESTIMATE" with reasoning

### Priority 2: Add ROI Ranges (Do Now)
Change opportunity ROI from single numbers to ranges:
```json
"roi_analysis": {
    "conservative": {"roi_percentage": 150, "payback_months": 12},
    "expected": {"roi_percentage": 280, "payback_months": 6},
    "optimistic": {"roi_percentage": 400, "payback_months": 4}
}
```

### Priority 3: Create Missing Industries (Next Sprint)
- Create `physical-therapy/benchmarks.json`
- Create `medspa/benchmarks.json`
- Use the excellent structure from `professional-services/benchmarks.json` as template

### Priority 4: Add Geographic Context (Future)
- Add `region` field to benchmarks where US/EU differs significantly
- Note currency conversion assumptions

---

## Source Quality Legend

| Rating | Definition | Example |
|--------|------------|---------|
| Excellent | Specific report + year + URL | "ABA TechReport 2024: https://..." |
| Good | Organization + year | "Staffing Industry Analysts, 2024" |
| Acceptable | Organization only | "APTA benchmarks" |
| Poor | Vague category | "Industry benchmarks" |
| Missing | No source | - |

---

## Files Changed in This Audit

**Audited:**
- `backend/src/knowledge/dental/benchmarks.json` - Good, needs source cleanup
- `backend/src/knowledge/recruiting/benchmarks.json` - Good, needs source cleanup
- `backend/src/knowledge/home-services/benchmarks.json` - Good, needs source cleanup
- `backend/src/knowledge/professional-services/benchmarks.json` - Excellent
- `backend/src/knowledge/coaching/benchmarks.json` - Good, needs source cleanup
- `backend/src/knowledge/veterinary/benchmarks.json` - Good, needs source cleanup
- `backend/src/knowledge/benchmarks/ecommerce.json` - Excellent
- `backend/src/knowledge/benchmarks/tech_saas.json` - Excellent
- `backend/src/knowledge/benchmarks/professional_services.json` - Excellent
- `backend/src/knowledge/dental/opportunities.json` - Needs ROI ranges

**To Create:**
- `backend/src/knowledge/physical-therapy/` (missing industry)
- `backend/src/knowledge/medspa/` (missing industry)

---

## Next Steps

1. [ ] Fix vague sources in industry benchmark files
2. [ ] Add ROI ranges to opportunity files
3. [ ] Mark unverified estimates clearly
4. [ ] Create physical-therapy and medspa directories
5. [ ] Add geographic context where applicable
