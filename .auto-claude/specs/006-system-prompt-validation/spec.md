# System Prompt Validation Layer

## Context
Read CLAUDE.md and docs/plans/2024-12-20-crb-philosophy-framework.md first for full project context.
Read docs/SYSTEM-PROMPT-PROPOSAL.md for the system prompt framework.

Every output from the CRB agent must align with our philosophy and framework. We need a validation layer.

## Objective
Build a validation layer that checks all agent outputs against our System Prompt and Two Pillars framework, ensuring consistency and quality.

## Current State
- System prompts defined but validation is manual
- Two Pillars framework documented but not enforced programmatically
- Agent outputs may not always align with philosophy

## Deliverables

### 1. Framework Validation Rules
- Two Pillars check: Customer Value score AND Business Health score must be 6+
- Three-option pattern: Each recommendation must have Off-the-shelf, Best-in-class, Custom
- Honesty check: Flag recommendations that might not be appropriate
- CRB scoring: Every recommendation has Cost, Risk, Benefit scores

### 2. Validation Engine
- Post-process agent outputs through validation layer
- Flag outputs that violate framework rules
- Either fix automatically or reject for regeneration
- Log validation results for quality tracking

### 3. Quality Metrics
- Track % of outputs passing validation first try
- Track common validation failures
- Build feedback loop for improvement

### 4. Prompt Versioning
- Version all system prompts
- Track which prompt version generated each report
- Enable A/B testing of prompt variations

### 5. Output Standardization
- Ensure all findings have required fields
- Ensure all recommendations follow the pattern
- Ensure CRB scores are within valid ranges
- Ensure sources are properly cited

## Acceptance Criteria
- [ ] All agent outputs pass Two Pillars validation
- [ ] Three-option pattern enforced on all recommendations
- [ ] CRB scores validated (1-10 range, all fields present)
- [ ] Validation failures logged with details
- [ ] Prompt versions tracked per report
- [ ] Quality metrics dashboard or logging

## Files to Modify
- `backend/src/agents/crb_agent.py`
- `backend/src/tools/report_tools.py`
- New: `backend/src/services/validation_service.py`
- New: `backend/src/models/validation.py`
- `backend/src/config/system_prompts.py`

## Framework Reference
- Two Pillars: Customer Value (1-10) + Business Health (1-10), both must be 6+
- Three Options: Off-the-shelf, Best-in-class, Custom
- Time Horizons: Short (0-6mo), Mid (6-18mo), Long (18mo+)
- CRB: Cost, Risk, Benefit scores for each recommendation
