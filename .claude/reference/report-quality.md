# Report Quality Reference

> Load this when working on report generation, findings, or any user-facing analysis output.

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

## Three Options Format

Every recommendation presents 3 options:

```
Option A: [Off-the-Shelf]     NET: +4.1  ◀ RECOMMENDED
Option B: [Best-in-Class]     NET: +2.8
Option C: [Custom Build]      NET: +1.2

WHY OPTION A WINS:
✓ Lowest time-to-value
✓ Free tier covers current needs
✓ Team already familiar

TRADE-OFFS:
△ Less customization
△ May outgrow in 12-18 months
```

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

## Key Files

| File | Purpose |
|------|---------|
| `skills/report-generation/` | Report section generators |
| `services/report_service.py` | Orchestrates generation |
| `services/teaser_service.py` | Pre-payment preview |
| `components/report/` | Frontend report components |
