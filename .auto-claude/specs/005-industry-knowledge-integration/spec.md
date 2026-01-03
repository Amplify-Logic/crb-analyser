# Industry Knowledge Integration

## Context
Read CLAUDE.md for full project context including target industries and knowledge base structure.

We have rich industry-specific knowledge bases that need to be wired into the CRB agent.

## Objective
Integrate all 6 primary industry knowledge bases into the CRB agent so analysis is deeply industry-specific.

## Current State
- Knowledge bases at `backend/src/knowledge/`:
  - `vendors/` - Cross-industry vendor pricing database (ai_assistants, automation, crm, scheduling, etc.)
  - `ai_tools/` - LLM provider pricing for custom solution estimates
  - `{industry}/` - Industry-specific folders with processes, opportunities, benchmarks, vendors
  - `patterns/` - AI implementation playbooks
- CRB Agent at `backend/src/agents/crb_agent.py`
- Expertise system at `backend/src/expertise/` for self-improving recommendations

## Deliverables

### 1. Industry Detection
- Auto-detect industry from intake/quiz data
- Map to appropriate knowledge base folder
- Fallback to general patterns if no match

### 2. Knowledge Injection
- Load from `backend/src/knowledge/{industry}/`:
  - `processes.json` - Common workflows and pain points
  - `opportunities.json` - AI automation opportunities
  - `benchmarks.json` - Industry-specific metrics (verified Dec 2025)
  - `vendors.json` - Relevant software for that industry
- Apply industry patterns to analysis
- Reference expertise system learnings

### 3. All 6 Primary Industries Complete
| Industry | Slug | Status |
|----------|------|--------|
| Professional Services | `professional-services` | ✅ Complete |
| Home Services | `home-services` | ✅ Complete |
| Dental | `dental` | ✅ Complete |
| Recruiting | `recruiting` | ✅ Complete |
| Coaching | `coaching` | ✅ Complete |
| Veterinary | `veterinary` | ✅ Complete |

### 4. Benchmark Integration
- Industry-specific efficiency metrics with `verified_date`
- Revenue/employee benchmarks from verified sources
- AI adoption rates by industry (see CLAUDE.md Key Sources)
- All benchmarks must cite source and verification date

### 5. Vendor Matching
- Match recommendations to industry-specific vendors
- Include pricing data with `verified_date`
- Consider business size when recommending (SMB, Mid-market, Enterprise)
- Cross-reference with `vendors/` category files

### 6. Data Verification Compliance
- All vendor pricing needs `verified_date: "YYYY-MM"`
- Industry benchmarks need source citations
- Unverified data marked `"status": "UNVERIFIED"` and flagged ⚠️
- Never present unverified data as fact

## Acceptance Criteria
- [ ] Industry auto-detected from intake data
- [ ] All 6 primary industries have complete knowledge integration
- [ ] Benchmarks appear in report with source and verification date
- [ ] Vendor recommendations are industry-appropriate with pricing
- [ ] Expertise system learnings applied where available
- [ ] Fallback works for unrecognized industries (expansion: physical-therapy, medspa)
- [ ] All data passes verification policy requirements

## Files to Modify
- `backend/src/agents/crb_agent.py`
- `backend/src/tools/discovery_tools.py`
- `backend/src/tools/research_tools.py`
- `backend/src/knowledge/{industry}/*.json`
- `backend/src/expertise/__init__.py` (expertise integration)

## Knowledge Base Structure
```
backend/src/knowledge/
├── vendors/                    # Cross-industry vendor database
├── ai_tools/llm_providers.json # For custom solution cost estimates
├── professional-services/      # Each has: processes, opportunities, benchmarks, vendors
├── home-services/
├── dental/
├── recruiting/
├── coaching/
├── veterinary/
├── physical-therapy/           # 🚧 Expansion - TODO
├── medspa/                     # 🚧 Expansion - TODO
└── patterns/ai_implementation_playbook.json
```
