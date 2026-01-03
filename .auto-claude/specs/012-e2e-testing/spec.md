# E2E Testing & Iteration

## Context
Read CLAUDE.md for full project context including target industries, framework rules, and data verification policy.

Quality requires testing. This agent runs full E2E flows, validates outputs, and feeds improvements back.

## Objective
Run comprehensive E2E tests across all flows for all 6 primary industries, validate outputs against framework and data verification policy, and document improvements needed.

## Current State
- Most core features working
- Some features need verification (PDF, email, playbook persistence)
- 6 primary industries complete in knowledge base

## Target Industries

### Primary Industries (All Must Pass E2E)
| Industry | Slug | Test URL Example |
|----------|------|------------------|
| Professional Services | `professional-services` | Law firm, accounting practice |
| Home Services | `home-services` | HVAC company, plumbing business |
| Dental | `dental` | Dental practice, DSO |
| Recruiting | `recruiting` | Staffing agency |
| Coaching | `coaching` | Business coaching firm |
| Veterinary | `veterinary` | Vet clinic, pet care |

### Expansion Industries (Fallback Testing)
- `physical-therapy` - Should gracefully fallback
- `medspa` - Should gracefully fallback

## Deliverables

### 1. E2E Test Scenarios
For each of the 6 primary industries:
- Complete quiz flow with industry-relevant URL
- Full interview simulation
- Report generation
- Report viewing and interaction
- PDF export verification

### 2. Output Validation
- Verify findings are industry-specific (reference industry knowledge base)
- Check recommendations follow three-option pattern
- Validate CRB scores are present and reasonable (1-10)
- Confirm Two Pillars scores are 6+ on both dimensions
- Check sources are cited with verification dates
- Verify confidence distribution (~30% HIGH, ~50% MEDIUM, ~20% LOW)
- Confirm confidence-adjusted ROI is calculated correctly

### 3. Data Verification Validation
- All vendor pricing has `verified_date` within last 3 months
- All benchmarks cite specific source with year
- No unverified data presented as fact
- Unverified data marked ⚠️ with LOW confidence

### 4. Test Documentation
- Document each test scenario
- Screenshot/capture key states
- Log any errors or issues
- Track timing and performance

### 5. Issue Catalog
- Create prioritized list of issues found
- Include reproduction steps
- Severity rating (Critical, High, Medium, Low)
- Suggested fixes where obvious

### 6. Improvement Recommendations
- Quality patterns observed
- Common failure modes
- Framework adherence gaps
- UX friction points
- Data verification gaps

## Acceptance Criteria
- [ ] All 6 primary industries tested E2E
- [ ] Expansion industries tested for graceful fallback
- [ ] Output validation complete with results
- [ ] Data verification policy compliance validated
- [ ] Issue catalog with 0 critical issues remaining
- [ ] Performance baseline established
- [ ] Improvement recommendations documented

## Test Commands
```bash
# Start backend
cd backend && source venv/bin/activate && uvicorn src.main:app --reload --port 8383

# Start frontend
cd frontend && npm run dev

# Ensure Redis is running
brew services start redis

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
- [ ] Sources: All findings cite sources with verification date
- [ ] Industry: Findings reference industry-specific data
- [ ] Specificity: Dollar amounts use actual business data
- [ ] Confidence: Distribution matches ~30/50/20 target
- [ ] ROI: Confidence-adjusted values displayed
- [ ] Verification: All data complies with verification policy
- [ ] Solution Spectrum: Automation vs Custom decision documented
