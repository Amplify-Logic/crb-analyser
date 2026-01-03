# Finding Quality - Depth, Specificity, Honesty

## Context
Read CLAUDE.md for full project context including confidence scoring and data verification requirements.

Findings are the core insights of the report. They must be deep, specific to THIS business, and honest about limitations.

## Objective
Improve finding quality to be deeply researched, highly specific to the analyzed business, and honest about when AI isn't the answer.

## Current State
- Findings generated via `backend/src/tools/report_tools.py`
- Discovery phase collects intake data
- Research phase finds benchmarks and vendors
- Some findings may be generic or lack specificity

## Deliverables

### 1. Depth of Analysis
- Each finding should reference specific intake data
- Include industry benchmark comparisons with verified sources
- Show the "why" behind each finding, not just "what"
- Support findings with evidence (metrics, comparisons, research)

### 2. Business Specificity
- Reference actual business details (size, industry, tech stack)
- Calculate specific dollar amounts using their data
- Name their actual pain points from interview
- Avoid generic statements that could apply to any business

### 3. Honesty & Calibration
- Flag findings where AI is NOT the right solution
- Include "when to wait" recommendations
- Show risks honestly, not just benefits
- Confidence levels should reflect actual certainty

### 4. Confidence Scoring (Evidence-Based)
Confidence should reflect actual data quality, not a forced distribution:

- **HIGH Confidence:**
  - Quiz answer directly mentions the issue
  - Multiple data points support the finding
  - Calculation uses user-provided numbers
  - Benchmark directly applies to their situation

- **MEDIUM Confidence:**
  - Quiz answer implies the issue
  - Industry pattern likely applies
  - Calculation with reasonable assumptions
  - One strong supporting data point

- **LOW Confidence:**
  - Industry pattern suggests possibility
  - Significant assumptions required
  - Hypothesis worth validating
  - Limited data available

**Philosophy:** Don't force a distribution - let confidence reflect actual evidence quality. If quiz data is rich, more HIGH findings is legitimate. If quiz data is sparse, more MEDIUM/LOW is honest. The goal is calibrated honesty, not hitting arbitrary ratios.

**Anti-pattern:** Forcing LOW confidence findings just to appear humble is as dishonest as inflating everything to HIGH.

### 5. Confidence-Adjusted ROI
All ROI estimates must be adjusted based on confidence:
```python
adjusted_roi = base_roi * confidence_factor
# HIGH:   confidence_factor = 1.0  (100%)
# MEDIUM: confidence_factor = 0.85 (85%)
# LOW:    confidence_factor = 0.70 (70%)
```
Always display as "Estimated ROI" with confidence level visible.

### 6. Source Quality
- Every finding cites its source with verification date
- External research clearly attributed (study name, year)
- Internal reasoning explained
- Distinguish between data, inference, and assumption
- Unverified claims marked ⚠️ and given LOW confidence

### 7. Finding Structure
- Clear category (Opportunity, Risk, Consideration)
- Impact level (High, Medium, Low) with justification
- Confidence level with explanation
- Two Pillars scores with reasoning
- Confidence-adjusted ROI where applicable

## Acceptance Criteria
- [ ] Findings reference specific intake data
- [ ] Dollar amounts calculated from actual business data
- [ ] At least some findings say "not recommended" or "wait"
- [ ] All findings have verified sources
- [ ] Confidence levels accurately reflect evidence quality (not forced distribution)
- [ ] ROI figures show confidence-adjusted values
- [ ] Generic findings are eliminated
- [ ] Unverified data flagged and given LOW confidence

## Files to Modify
- `backend/src/tools/report_tools.py`
- `backend/src/tools/analysis_tools.py`
- `backend/src/tools/discovery_tools.py`
- `backend/src/agents/crb_agent.py`
- `backend/src/services/roi_calculator.py` (confidence adjustment)
- `backend/src/models/assumptions.py`

## Framework Reference
- Findings must pass Two Pillars test (6+ on both Customer Value and Business Health)
- Three categories: Opportunity (green), Risk (red), Consideration (yellow)
- Confidence: HIGH (30%), MEDIUM (50%), LOW (20%) target distribution
- Confidence-Adjusted ROI: HIGH=100%, MEDIUM=85%, LOW=70%
