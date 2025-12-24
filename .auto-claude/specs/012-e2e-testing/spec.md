# E2E Testing & Iteration

## Context
Read CLAUDE.md and docs/plans/2024-12-20-crb-philosophy-framework.md first for full project context.
Read TESTING-FINDINGS.md for current test status.

Quality requires testing. This agent runs full E2E flows, validates outputs, and feeds improvements back.

## Objective
Run comprehensive E2E tests across all flows for Tier 1 industries, validate outputs against framework, and document improvements needed.

## Current State
- Most core features working per TESTING-FINDINGS.md
- Some features need verification (PDF, email, playbook persistence)
- 3 Tier 1 industries defined

## Deliverables

### 1. E2E Test Scenarios
For each Tier 1 industry (Professional Services, Home Services, Dental):
- Complete quiz flow with industry-relevant URL
- Full interview simulation
- Report generation
- Report viewing and interaction

### 2. Output Validation
- Verify findings are industry-specific
- Check recommendations follow three-option pattern
- Validate CRB scores are present and reasonable
- Confirm Two Pillars scores are 6+
- Check sources are cited

### 3. Test Documentation
- Document each test scenario
- Screenshot/capture key states
- Log any errors or issues
- Track timing and performance

### 4. Issue Catalog
- Create prioritized list of issues found
- Include reproduction steps
- Severity rating (Critical, High, Medium, Low)
- Suggested fixes where obvious

### 5. Improvement Recommendations
- Quality patterns observed
- Common failure modes
- Framework adherence gaps
- UX friction points

## Acceptance Criteria
- [ ] All 3 Tier 1 industries tested E2E
- [ ] Output validation complete with results
- [ ] Issue catalog with 0 critical issues remaining
- [ ] Performance baseline established
- [ ] Improvement recommendations documented

## Test Commands
```bash
# Start backend
cd backend && python -m uvicorn src.main:app --port 8383

# Start frontend
cd frontend && npm run dev

# Test specific industry
# Navigate to quiz with industry-specific URL
```

## Files to Create/Update
- `TESTING-FINDINGS.md` (update with new results)
- New: `tests/e2e/` test scenarios
- New: `docs/quality-report.md` with findings

## Validation Checklist
- [ ] Two Pillars: All recommendations score 6+ on both
- [ ] Three Options: Every recommendation has all 3
- [ ] CRB Scores: All present and in 1-10 range
- [ ] Sources: All findings cite sources
- [ ] Industry: Findings reference industry-specific data
- [ ] Specificity: Dollar amounts use actual business data
