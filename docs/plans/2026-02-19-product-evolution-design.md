# Product Evolution: From Report to Managed Agents

> **Status:** Design approved
> **Date:** 2026-02-19
> **Context:** Inspired by OpenClaw/computer-use agent trends. CRB Analyser evolves from one-shot analysis to end-to-end partner: "We help you decide, then we help you do."

---

## Vision

CRB Analyser is the company that helps e-commerce businesses figure out which AI agents they need, then deploys and manages them.

The report is the diagnostic. The implementation is the treatment. The managed service is the ongoing care.

---

## Strategic Decisions Made

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Post-report model | "We help you decide, then we help you do" | Natural upsell, report becomes pre-qualified proposal |
| Implementation approach | Hybrid: bespoke first, productize over time | Learn what works before building templates |
| Vertical for implementation | E-commerce | Founder knows the customer, passionate about the space, ROI is directly measurable |
| Report vertical strategy | Keep parallel (all verticals) | Low cost to run, good for signal gathering |
| Implementation vertical strategy | E-commerce only | Can't go deep in 3 verticals simultaneously |

---

## The Product Ladder

### Tier 1: CRB Report — €147

- **What:** AI readiness analysis, 3-5 opportunities scored with CRB framework
- **Verticals:** All (professional services, dental, e-commerce)
- **Delivers:** Report with CRB scores, ROI estimates, tool recommendations
- **Change for e-commerce:** Findings include an "Agent Opportunity" section — what a CRB agent would do, estimated impact, deployment timeline
- **Purpose:** Signal gathering + lead generation for higher tiers

### Tier 2: CRB Report + Strategy Call — €497

- **What:** Everything in Tier 1 + 60-minute call to walk through findings
- **Delivers:** Prioritized action plan, #1 opportunity scoped for implementation
- **Purpose:** Qualifies implementation leads, builds trust, gives context for sprint
- **Note:** Already planned in CLAUDE.md as future tier. Activate after 50+ reports.

### Tier 3: Implementation Sprint — €2,500

- **What:** Deploy the CRB Support Agent on client's Shopify + support tool stack
- **Vertical:** E-commerce only
- **Timeline:** 2 weeks
- **Scope:** One automation per sprint (no scope creep)
- **Starts in:** Draft mode (agent suggests responses, human approves)
- **Includes:** 1 month of managed service free (to prove value before monthly commitment)
- **Purpose:** Land the client, prove ROI, collect deployment data

### Tier 4: Managed Agent — €750/month

- **What:** Ongoing maintenance, monitoring, tuning of deployed agents
- **Delivers:** Monthly ROI report showing tickets handled, hours saved, money saved
- **Includes:** Agent upgrades, API change handling, prompt tuning
- **Terms:** Month-to-month, no lock-in (confidence signal to clients)
- **Purpose:** Recurring revenue, retention, expansion trigger

### Expansion Path

After a managed agent proves value:
> "Your support agent saved you €800 last month. Ready to tackle opportunity #2 from your report?"

Each expansion = another sprint + another €750/mo. Clients accumulate agents over time.

---

## Pricing Philosophy

These prices are the **floor**, not the ceiling. As data compounds and case studies accumulate:

- 50+ reports → raise report price or keep as loss leader
- 10+ deployments → sprint price increases with proven track record
- "Our agents have handled 50,000 tickets with 94% satisfaction" → premium pricing justified
- Better clients come from better proof → prices follow proof

---

## First Agent: The CRB Support Agent

Start with ONE agent type. Expand only after 10+ deployments.

### Why Support Agent First

| Factor | Reasoning |
|--------|-----------|
| Universal need | Every e-commerce store has support tickets |
| Measurable ROI | Tickets resolved, hours saved, response time — all countable |
| Common stack | Gorgias/Zendesk + Shopify — standard integrations |
| Safe to start | Draft mode (agent suggests, human approves) limits blast radius |
| Visible to client | They see it working every day, reinforces value |
| Low operational risk | Bad draft = minor inconvenience, not customer-facing mistake |

### Support Agent Capabilities

1. Handle tier-1 tickets: order status, return policy, shipping questions, FAQs
2. Pull order data from Shopify to personalize responses
3. Classify ticket urgency and route complex issues to humans
4. Draft responses for human approval (Phase 1) or send autonomously (Phase 2)
5. Track resolution metrics for monthly ROI report

### Graduation Path

```
Draft Mode (default)        → Agent drafts, human approves before sending
Assisted Mode (after 2 wks) → Agent sends routine, human approves edge cases
Autonomous Mode (optional)  → Agent handles tier-1 fully, escalates tier-2+
```

Client controls the graduation. Trust is earned, not assumed.

### Future Agent Types (not now)

Only consider after Support Agent is proven and templated:

| Priority | Agent | Trigger to build |
|----------|-------|-----------------|
| 2nd | Returns Processor | 3+ clients ask for it |
| 3rd | Inventory Alert Agent | Market signal or client demand |
| 4th | Review Manager | Natural expansion from support |
| Later | Marketing Attribution | High-effort, build only with proven demand |
| Later | Content Agent | Commodity market, lower priority |

---

## Productization Timeline

### Phase 1: Bespoke (Clients 1-10)

- Every implementation is custom
- Hand-crafted Python integration per client
- Slow and manual — that's the point
- **Focus:** Collect patterns, document everything, build case studies
- **Collect:** Which Shopify setups are common? Which support tools? What edge cases? What breaks?

### Phase 2: Templated (Clients 11-30)

- Reusable agent templates emerge from Phase 1 patterns
- "Support Agent for Shopify + Gorgias" is a package, not a project
- Setup drops from 2 weeks to 3-5 days
- Sprint pricing can decrease (less effort) while volume increases
- Report recommends specific packages by name
- Monthly ROI report is standardized

### Phase 3: Emerges naturally (if ever)

- Do NOT plan or build a self-serve platform
- Do NOT think about dashboards, multi-tenancy, or onboarding flows
- If Phase 2 templates become so standardized that deployment is mechanical, self-serve might make sense
- Let it happen. Don't force it.

---

## Capacity & Unit Economics

### One-Person Ceiling

- ~10-15 managed clients before operational burden is too high
- Each client = 1-2 agents needing monitoring, maintenance, API changes
- Monthly maintenance per client: ~2-4 hours (monitoring, tuning, ROI report)

### Target Monthly Revenue (~12 months in)

```
Reports:  20/month × €147 avg  = €2,940
Sprints:  2/month  × €2,500    = €5,000
Managed:  10 clients × €750    = €7,500
                                --------
Gross:                           €15,440
Costs:    Infrastructure + APIs  -€2,000
                                --------
Net:                             ~€13,000/month
```

### Growth Beyond One Person

- First hire (if ever): agent maintenance/monitoring — frees capacity for more sprints
- Don't hire until managed base exceeds 12-15 clients consistently
- Every hire should unlock more managed slots, not more complexity

---

## Operational Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Agent gives wrong answer to customer | Client trust damage | Start in draft mode always. Graduate only with client approval. |
| Shopify/Gorgias API changes | Agent breaks | Monthly maintenance in managed fee covers this. Monitor API changelogs. |
| Client expects 24/7 uptime | Burnout, over-promising | Clear SLA: business-hours monitoring. Agent runs 24/7 but maintenance is business hours. |
| Scope creep during sprint | Unprofitable, delayed | One automation per sprint, scoped in strategy call. No exceptions. |
| Too many managed clients | Quality drops | Hard cap at 15 until you hire or automate monitoring. |

---

## What Changes in the Existing Platform

### Modified (extend, don't rebuild)

| Component | Current | Change |
|-----------|---------|--------|
| Report Service (`report_service.py`) | Generates findings with CRB scores | E-commerce findings get "Agent Opportunity" section: what agent would do, estimated impact, deployment timeline |
| Knowledge Base (`backend/src/knowledge/`) | E-commerce directory planned but empty | Build out with Shopify ecosystem data, support tool integrations, benchmark metrics |
| Stripe Integration | Single €147 product | Add €497 (report + call), €2,500 (sprint) products. €750/mo subscription for managed tier. |

### New (build when needed, not before)

| Component | When to build | What it is |
|-----------|--------------|------------|
| Strategy call booking | After first €497 purchase | Calendar integration (Calendly or similar) |
| Support Agent codebase | When first sprint client signs | Python + Shopify API + Gorgias/Zendesk API |
| Agent monitoring | When first agent is deployed | Health checks, error alerting |
| Monthly ROI report | When first managed month starts | Template pulling agent metrics into formatted report |
| Client dashboard | Phase 2 at earliest | Agent performance visible to client |

---

## Immediate Next Steps

| Priority | Action | Effort |
|----------|--------|--------|
| 1 | Build out e-commerce knowledge base (Shopify ecosystem, support tools, benchmarks) | 1-2 weeks |
| 2 | Add €497 Stripe product and strategy call booking flow | 2-3 days |
| 3 | Modify report template: add "Agent Opportunity" section for e-commerce findings | 1 week |
| 4 | Sell 50+ reports across all verticals to validate the wedge | Ongoing |
| 5 | First sprint client: build Support Agent bespoke | When client appears |

**Do not build the agent platform before you have a paying sprint client.**

---

## Success Metrics

### Phase 1 Signals (First 6 months)

| Metric | Target | What it tells you |
|--------|--------|-------------------|
| Reports sold (all verticals) | 50+ | Is the wedge working? |
| E-commerce report % | Track | Is e-commerce converting? |
| Report → call conversion | >10% | Are e-commerce clients interested in more? |
| Call → sprint conversion | >30% | Is the implementation pitch landing? |
| Sprint → managed conversion | >70% | Does the free month prove enough value? |
| Managed churn (monthly) | <10% | Is the monthly ROI report retaining? |

### Compounding Indicators

- Knowledge base entries growing after each report
- Support Agent deployment time decreasing per client
- Monthly ROI reports showing improving agent performance
- Case studies accumulating for sales conversations

---

## What This Means for CRB Analyser's Identity

**Before:** "We help professional services firms figure out which AI tools are worth their time."

**After:** "We help e-commerce businesses figure out which AI agents they need — then we deploy and manage them."

The CRB framework stays. The analysis rigor stays. The report stays. What changes is that the report is no longer the destination. It's the beginning of a relationship.

> The report is the diagnostic. The implementation is the treatment. The managed service is the ongoing care.
