# Recommendation Engine - Three-Option Pattern with Real Data

## Context
Read CLAUDE.md and docs/plans/2024-12-20-crb-philosophy-framework.md first for full project context.

Recommendations are what customers act on. They must follow the three-option pattern and include real vendor/pricing data.

## Objective
Enhance the recommendation engine to consistently deliver the three-option pattern with real vendor data, pricing, and implementation guidance.

## Current State
- Recommendations generated in `backend/src/tools/report_tools.py`
- Three-option pattern documented but may not be consistent
- Vendor database at `backend/src/knowledge/vendors/`
- Some recommendations may lack real pricing

## Deliverables

### 1. Three-Option Pattern (Mandatory)
Every recommendation MUST include:
- **Off-the-shelf**: Fastest, cheapest, good-enough solution
- **Best-in-class**: Premium solution with maximum capability
- **Custom**: Build/integrate for unique requirements

Each option shows: Vendor, Price range, Time to implement, Pros/Cons

### 2. Real Vendor Data
- Pull from vendor database for each recommendation
- Include actual pricing (monthly, annual, per-user)
- Show vendor comparison matrix
- Link to vendor websites

### 3. Implementation Reality
- Realistic implementation timelines
- Required integrations called out
- Training/change management needs
- Hidden costs identified

### 4. CRB Scoring Per Option
- Each of the 3 options has its own CRB scores
- Cost: Total cost of ownership
- Risk: Implementation and adoption risks
- Benefit: Expected value created

### 5. Decision Support
- "Best for..." guidance (e.g., "Best for teams under 10")
- Comparison table for the 3 options
- Clear recommendation with reasoning
- "Why not" for each non-recommended option

## Acceptance Criteria
- [ ] 100% of recommendations have all 3 options
- [ ] Each option has real vendor/product name
- [ ] Pricing included where available
- [ ] CRB scores for each option
- [ ] Implementation timeline for each option
- [ ] Clear "best for your situation" recommendation

## Files to Modify
- `backend/src/tools/report_tools.py`
- `backend/src/tools/modeling_tools.py`
- `backend/src/tools/research_tools.py`
- `backend/src/knowledge/vendors/*.json`
- `backend/src/models/recommendation.py`

## Vendor Database
Ensure these are populated:
- Pricing tiers (SMB, Mid-market, Enterprise)
- Implementation complexity
- Integration requirements
- Customer segments
