# Finding Quality - Depth, Specificity, Honesty

## Context
Read CLAUDE.md and docs/plans/2024-12-20-crb-philosophy-framework.md first for full project context.

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
- Include industry benchmark comparisons
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

### 4. Source Quality
- Every finding cites its source
- External research clearly attributed
- Internal reasoning explained
- Distinguish between data, inference, and assumption

### 5. Finding Structure
- Clear category (Opportunity, Risk, Consideration)
- Impact level (High, Medium, Low) with justification
- Confidence level with explanation
- Two Pillars scores with reasoning

## Acceptance Criteria
- [ ] Findings reference specific intake data
- [ ] Dollar amounts calculated from actual business data
- [ ] At least some findings say "not recommended" or "wait"
- [ ] All findings have sources
- [ ] Confidence levels vary based on data quality
- [ ] Generic findings are eliminated

## Files to Modify
- `backend/src/tools/report_tools.py`
- `backend/src/tools/analysis_tools.py`
- `backend/src/tools/discovery_tools.py`
- `backend/src/agents/crb_agent.py`
- `backend/src/prompts/*.py` or equivalent

## Framework Reference
- Findings must pass Two Pillars test
- Three categories: Opportunity (green), Risk (red), Consideration (yellow)
- Confidence: High (80%+), Medium (60-80%), Low (<60%)
