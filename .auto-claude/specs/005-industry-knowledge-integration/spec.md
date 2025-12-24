# Industry Knowledge Integration

## Context
Read CLAUDE.md and docs/plans/2024-12-20-crb-philosophy-framework.md first for full project context.
Read docs/plans/2024-12-20-target-industries.md for target industries.

We have rich industry-specific knowledge bases that need to be wired into the CRB agent.

## Objective
Integrate Tier 1 industry knowledge bases (Professional Services, Home Services, Dental) into the CRB agent so analysis is deeply industry-specific.

## Current State
- Knowledge bases at `backend/src/knowledge/`:
  - `benchmarks/` - Industry metrics
  - `vendors/` - Vendor pricing database
  - `patterns/` - AI implementation playbooks
  - `case_studies/` - Reference implementations
- CRB Agent at `backend/src/agents/crb_agent.py`
- Industry-specific prompts exist but may not be fully wired

## Deliverables

### 1. Industry Detection
- Auto-detect industry from intake/quiz data
- Map to appropriate knowledge base
- Fallback to general knowledge if no match

### 2. Knowledge Injection
- Load relevant benchmarks for detected industry
- Include industry-specific vendor recommendations
- Apply industry patterns to analysis
- Reference relevant case studies

### 3. Tier 1 Industries Complete
- Professional Services (Legal/Accounting/Consulting)
- Home Services (HVAC/Plumbing/Electrical)
- Dental (Practices & DSOs)

### 4. Benchmark Integration
- Industry-specific efficiency metrics
- Revenue/employee benchmarks
- AI adoption rates by industry
- Competitive landscape data

### 5. Vendor Matching
- Match recommendations to industry-specific vendors
- Include pricing data where available
- Consider business size when recommending

## Acceptance Criteria
- [ ] Industry auto-detected from intake data
- [ ] All 3 Tier 1 industries have complete knowledge integration
- [ ] Benchmarks appear in report with industry context
- [ ] Vendor recommendations are industry-appropriate
- [ ] Case studies referenced where relevant
- [ ] Fallback works for unrecognized industries

## Files to Modify
- `backend/src/agents/crb_agent.py`
- `backend/src/tools/discovery_tools.py`
- `backend/src/tools/research_tools.py`
- `backend/src/knowledge/*.json`
- `backend/src/config/system_prompts.py` or equivalent

## Knowledge Files to Review
- `backend/src/knowledge/benchmarks/`
- `backend/src/knowledge/vendors/`
- `backend/src/knowledge/patterns/`
