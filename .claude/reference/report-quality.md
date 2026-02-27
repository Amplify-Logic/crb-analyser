# Report Quality Reference

> Load this when working on report generation, findings, or any user-facing analysis output.
> NOT here: report UI components → `frontend-development.md` | report API routes → `api-development.md` | CRB methodology → `FRAMEWORK.md`

---

## Core Principle

> "The analysis makes the best option obvious."

Reports must be specific, actionable, and grounded in data. Generic AI output is worthless.

## Anti-Slop Rules

These phrases are BANNED. Replace with specifics:

| BANNED Phrase | Replace With |
|---------------|--------------|
| "Streamline operations" | "Reduce invoice processing from 4 hours to 30 minutes" |
| "Enhance efficiency" | "Save €2,400/month on manual data entry" |
| "Leverage AI capabilities" | "Use Claude to draft client emails (€15/month)" |
| "Transform your business" | "Free up 10 hours/week for billable work" |
| "Unlock potential" | "Increase capacity from 40 to 55 clients/month" |
| "Optimize workflows" | "Cut appointment scheduling from 15 to 2 minutes" |
| "Drive growth" | "Add €4,200/month revenue with automated follow-ups" |
| "Consider migrating to X" | "Connect HubSpot to Exact with a Claude workflow that syncs deals → invoices" |
| "We recommend Tool X" | "Build an AI agent that monitors your IoT data and flags churn risk" |
| "Best-in-class solution" | "Wire your existing CRM + ERP + IoT data into a unified context layer" |

## Specificity Requirements

Every claim needs backing:

| Element | Required |
|---------|----------|
| ROI figures | Source + calculation + confidence level |
| Vendor recommendations | Pricing verified within 90 days |
| Benchmarks | Source URL + date + industry specificity |
| Time estimates | Based on similar implementations |
| Ranges over false precision | "€1,200-€1,800/month" not "€1,547/month" |

## CRB Framework Output

Each finding must include:

### Costs (6 Dimensions)
- Financial: Direct €, ongoing €
- Time: Implementation hours, learning curve
- Opportunity: What else could this fund?
- Complexity: Systems touched, training needed
- Risk: What if it fails? Reversibility?
- Brand/Trust: Customer/team perception

### Benefits (4 Dimensions)
- Financial: Revenue increase, cost savings
- Time: Hours freed, speed improvements
- Strategic: Market position, competitive edge
- Quality: Customer experience, team satisfaction

### Risk Assessment
- Implementation risk
- Adoption risk
- Vendor risk
- Security risk
- Integration risk

### NET SCORE
```
NET SCORE = Benefit Score - Cost Score - (Risk Score ÷ 10)
```

## Confidence Levels

| Level | Factor | Criteria |
|-------|--------|----------|
| HIGH | 1.0 | User-provided numbers, verified benchmark |
| MEDIUM | 0.85 | Industry pattern, one strong data point |
| LOW | 0.70 | Significant assumptions required |

### Display Rules
- Always show "**Estimated**" - never claim certainty
- Show confidence level next to EVERY number
- Use ranges for LOW confidence
- If everything is HIGH, you're being dishonest

## AIOS Options Format

Every recommendation presents options in connect-first priority:

```
Option A: [Connect & Automate]   NET: +5.2  ◀ RECOMMENDED
Option B: [Enhance with AI]      NET: +3.8
Option C: [Targeted Upgrade]     NET: +1.5

WHY OPTION A WINS:
✓ Uses your existing HubSpot + Exact stack
✓ Claude workflow ships in 8 hours
✓ Zero disruption, zero migration

TRADE-OFFS:
△ Requires API access to both tools
△ Custom workflow needs maintenance
```

### Connect-First Rules
1. **Always lead with Connect** — show how to wire existing tools with AI
2. **Enhance second** — add AI agents/workflows on top of existing data
3. **Replace ONLY when** — tool has no API, is fundamentally broken, or data is trapped
4. **Never recommend Replace** just because a "better" tool exists
5. **Include build time** — "Ship in 8 hours with Claude Code" not "6-month migration"

## Teaser vs Full Report

| Element | Teaser (Free) | Full (€147+) |
|---------|---------------|--------------|
| AI Readiness Score | Full | Full |
| Top 3 Opportunities | Headlines only | Full CRB analysis |
| Vendor Recommendations | "We found 5 tools" | Names + pricing + comparison |
| Implementation Roadmap | Hidden | Full with timeline |
| Quick Wins | Count only | Detailed steps |
| ROI Calculations | Total only | Per-finding breakdown |

## Quality Checklist

Before shipping any report:

- [ ] Search output for banned phrases (grep -i "streamline\|leverage\|enhance")
- [ ] Every ROI figure has confidence level
- [ ] Vendor pricing is < 90 days old
- [ ] All benchmarks have sources
- [ ] Best option emerges obviously from scoring
- [ ] Would a dentist/plumber/lawyer understand without jargon?
- [ ] Recommendations are actionable THIS WEEK
- [ ] €147 price is clearly justified by value shown
- [ ] First recommendation is CONNECT, not REPLACE
- [ ] Every finding explains what can be built on existing stack
- [ ] Custom build estimates include Claude Code hours and MCP servers needed
- [ ] "Replace" option only appears when Connect is genuinely impossible (document why)

## Calculation Pipeline Rules

When adding or modifying option types (e.g., AIOS types like `connect_and_automate`), ALL downstream consumers must be updated:

### Option Type Checklist
When a new option type is added to the recommendation model:
- [ ] `roi_calculator.py:_calculate_financials()` handles the new type's cost format
- [ ] `report_service.py` confidence adjustment re-applies ROI cap (500%) after adjustment
- [ ] `report_service.py:_finalize_report()` reconciles exec summary totals with value_summary
- [ ] `four_options.py` scoring aligns with AIOS recommendation (not contradicting it)
- [ ] `report_generation_utils.py` vendor filtering respects industry boundaries
- [ ] Payback period has minimum 1-month floor (sub-month payback is not credible)

### Cost Format Rules
- **AIOS options** store costs as strings: `"EUR 60-100"`, `"2 weeks"` — must be parsed
- **Legacy options** store costs as numbers: `implementation_cost: 500`, `monthly_cost: 50`
- **Never assume** cost fields are numeric — always check and parse if string
- **String cost parsing**: extract numbers with regex, use midpoint for ranges

### Consistency Rules
- Exec summary `total_value_potential` MUST equal `value_summary.total` (not LLM-estimated separately)
- ROI cap (500%) must be applied AFTER any confidence adjustments, not before
- `four_options.recommended` must not contradict `our_recommendation` without an explicit override note
- Vendors must be filtered by industry — no legal CRMs for accounting firms

## Key Files

| File | Purpose |
|------|---------|
| `skills/report-generation/` | Report section generators |
| `skills/analysis/roi_calculator.py` | ROI calculation with AIOS cost extraction |
| `skills/report_generation_utils.py` | Vendor loading with industry filtering |
| `services/report_service.py` | Orchestrates generation, confidence adjustment, reconciliation |
| `services/teaser_service.py` | Pre-payment preview |
| `components/report/` | Frontend report components |
