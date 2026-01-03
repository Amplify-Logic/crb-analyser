# Recommendation Engine - Three-Option Pattern with Real Data

## Context
Read CLAUDE.md for full project context including Solution Philosophy (Automation vs Custom) and Three Options framework.

Recommendations are what customers act on. They must follow the three-option pattern, apply the solution spectrum decision framework, and include real vendor/pricing data.

## Objective
Enhance the recommendation engine to consistently deliver the three-option pattern with real vendor data, pricing, solution spectrum analysis, and implementation guidance.

## Current State
- Recommendations generated in `backend/src/tools/report_tools.py`
- Three-option pattern documented but may not be consistent
- Vendor database at `backend/src/knowledge/vendors/`
- Some recommendations may lack real pricing

## Deliverables

### 1. Solution Spectrum Analysis (Pre-Recommendation)
Before generating options, determine the solution category:

**Automation (n8n, Make, Zapier)** - Recommend when:
- Problem is workflow coordination between existing tools
- Standard integrations exist
- Speed to deploy matters most
- Budget is constrained
- No unique data/logic requirements

**Hybrid (Automation + AI Enhancement)** - Recommend when:
- Core workflow is standard, but needs intelligent processing
- Claude API can add AI layer to automation
- Custom logic needed at specific steps
- Want benefits of both approaches

**Custom Software** - Recommend when:
- Data ownership/access is strategic
- Features need to work exactly as envisioned
- Building a competitive advantage
- Existing tools don't fit the mental model
- Long-term SaaS cost > build cost
- Integration complexity > building

### 2. Three-Option Pattern (Mandatory)
Every recommendation MUST include:
- **Off-the-shelf**: Fastest, cheapest, good-enough solution
- **Best-in-class**: Premium solution with maximum capability
- **Custom**: Build/integrate for unique requirements (include Claude Code, model recommendation, dev hours)

Each option shows: Vendor, Price range, Time to implement, Pros/Cons

### 3. Custom Solution Details
When recommending custom solutions, include:
- **Build Tools:** Claude Code, Cursor, VS Code
- **Model Recommendation:** Which Claude model and why (Opus=complex reasoning, Sonnet=balanced, Haiku=speed/cost)
- **Skills Required:** Python, API integration, frontend, etc.
- **Dev Hours Estimate:** Realistic range
- **Recommended Stack:** e.g., FastAPI + React + Supabase + Railway
- **Key APIs:** Specific integrations needed
- **Resources:** Documentation, tutorials, communities

### 4. Real Vendor Data
- Pull from `backend/src/knowledge/vendors/` for each recommendation
- Include actual pricing with `verified_date` (monthly, annual, per-user)
- Show vendor comparison matrix
- Link to vendor websites
- Flag unverified pricing with ⚠️

### 5. Implementation Reality
- Realistic implementation timelines
- Required integrations called out
- Training/change management needs
- Hidden costs identified

### 6. CRB Scoring Per Option
- Each of the 3 options has its own CRB scores (1-10)
- Cost: Total cost of ownership
- Risk: Implementation and adoption risks
- Benefit: Expected value created

### 7. Decision Support
- "Best for..." guidance (e.g., "Best for teams under 10")
- Comparison table for the 3 options
- Clear recommendation with reasoning
- "Why not" for each non-recommended option
- Solution spectrum rationale (why automation vs custom)

## Acceptance Criteria
- [ ] 100% of recommendations have all 3 options
- [ ] Solution spectrum decision documented per recommendation
- [ ] Each option has real vendor/product name
- [ ] Pricing included with verification date where available
- [ ] Custom solutions include model recommendation and dev hours
- [ ] CRB scores for each option (1-10)
- [ ] Implementation timeline for each option
- [ ] Clear "best for your situation" recommendation

## Files to Modify
- `backend/src/tools/report_tools.py`
- `backend/src/tools/modeling_tools.py`
- `backend/src/tools/research_tools.py`
- `backend/src/knowledge/vendors/*.json`
- `backend/src/knowledge/ai_tools/llm_providers.json`
- `backend/src/models/recommendation.py`

## Vendor Database Structure
```
backend/src/knowledge/
├── vendors/                    # Cross-industry
│   ├── automation.json        # n8n, Make, Zapier
│   ├── crm.json
│   ├── scheduling.json
│   └── ...
├── ai_tools/
│   └── llm_providers.json     # Claude, GPT pricing for custom solutions
└── {industry}/
    └── vendors.json           # Industry-specific vendors
```

Ensure vendor data includes:
- Pricing tiers (SMB, Mid-market, Enterprise)
- `verified_date: "YYYY-MM"`
- Implementation complexity
- Integration requirements
- Customer segments
