# System Prompt Validation Layer

## Context
Read CLAUDE.md for full project context including Data Verification Policy and framework rules.

Every output from the CRB agent must align with our philosophy and framework. We need a validation layer.

## Objective
Build a validation layer that checks all agent outputs against our System Prompt, Two Pillars framework, and Data Verification Policy, ensuring consistency and quality.

## Current State
- System prompts defined but validation is manual
- Two Pillars framework documented but not enforced programmatically
- Data Verification Policy documented but not enforced
- Agent outputs may not always align with philosophy

## Deliverables

### 1. Framework Validation Rules
- Two Pillars check: Customer Value score AND Business Health score must be 6+
- Three-option pattern: Each recommendation must have Off-the-shelf, Best-in-class, Custom
- Honesty check: Flag recommendations that might not be appropriate
- CRB scoring: Every recommendation has Cost, Risk, Benefit scores (1-10)
- Solution spectrum: Validate automation vs hybrid vs custom decision logic

### 2. Data Verification Validation
- All vendor pricing must have `verified_date` within last 3 months
- All industry benchmarks must cite specific source with year
- Market size claims must link to market research report
- ROI claims must show calculation with sources
- Unverified data must be marked with `"status": "UNVERIFIED"` and ⚠️ flag
- Never present unverified data as fact in reports

### 3. Validation Engine
- Post-process agent outputs through validation layer
- Flag outputs that violate framework or data rules
- Either fix automatically or reject for regeneration
- Log validation results for quality tracking
- Apply LOW confidence automatically to unverified data

### 4. Quality Metrics
- Track % of outputs passing validation first try
- Track common validation failures
- Track data verification failures separately
- Build feedback loop for improvement

### 5. Prompt Versioning
- Version all system prompts
- Track which prompt version generated each report
- Enable A/B testing of prompt variations

### 6. Output Standardization
- Ensure all findings have required fields
- Ensure all recommendations follow the three-option pattern
- Ensure CRB scores are within valid ranges (1-10)
- Ensure sources are properly cited with verification dates
- Ensure confidence-adjusted ROI is calculated correctly

## Acceptance Criteria
- [ ] All agent outputs pass Two Pillars validation (6+ on both)
- [ ] Three-option pattern enforced on all recommendations
- [ ] CRB scores validated (1-10 range, all fields present)
- [ ] Data verification policy enforced (verified_date, sources)
- [ ] Unverified data automatically flagged ⚠️ and marked LOW confidence
- [ ] Validation failures logged with details
- [ ] Prompt versions tracked per report
- [ ] Quality metrics dashboard or logging

## Files to Modify
- `backend/src/agents/crb_agent.py`
- `backend/src/tools/report_tools.py`
- `backend/src/services/report_validator.py` (if exists, else create)
- New: `backend/src/services/validation_service.py`
- New: `backend/src/models/validation.py`
- `backend/src/config/system_prompts.py`

## Framework Reference
- Two Pillars: Customer Value (1-10) + Business Health (1-10), both must be 6+
- Three Options: Off-the-shelf, Best-in-class, Custom
- Time Horizons: Short (0-6mo), Mid (6-18mo), Long (18mo+)
- CRB: Cost, Risk, Benefit scores for each recommendation
- Data Verification: `verified_date`, source citation, UNVERIFIED marking

## Data Verification Policy Reference
| Data Type | Verification Method | Refresh Frequency |
|-----------|--------------------|--------------------|
| Vendor pricing | Check vendor website directly | Monthly |
| Industry benchmarks | Cite specific study/report with year | Quarterly |
| AI adoption stats | Link to survey/study source | Quarterly |
| Market size | Link to market research report | Annually |
| ROI claims | Must show calculation with sources | Per-use |
