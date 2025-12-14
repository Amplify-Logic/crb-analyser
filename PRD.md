# CRB Analyser - Product Requirements Document (Final)

> **All decisions pre-filled with recommended defaults. Adjust as needed.**

---

## 1. Product Definition

### Vision
AI-powered business audit service delivering Cost/Risk/Benefit analysis for AI implementation and process automation. Consultant-quality reports at 1/10th the cost.

### Target Market
**Primary:** Mid-market professional services (agencies, legal, accounting, recruitment)
- Company size: 20-200 employees
- Revenue: €1M-50M
- Decision maker: Founder, CEO, COO, or Operations Manager
- Pain: Know AI could help but don't know where to start

### Value Proposition
| For Customer | For Us |
|--------------|--------|
| Specific, actionable AI roadmap | €500-3000 per report |
| Real vendor pricing (not guesses) | 85%+ margin |
| Transparent ROI calculations | Scalable (AI-driven) |
| Professional PDF they can share | Recurring re-audit potential |

---

## 2. Product Tiers

### Pricing Structure

| Tier | Price | Delivery | Findings | Report | Best For |
|------|-------|----------|----------|--------|----------|
| **Starter** | €147 | Instant | 5 | Summary PDF | Testing the water |
| **Professional** | €697 | 24h | 15-20 | Full PDF + data | Most customers |
| **Enterprise** | €2,997 | 1 week | 30+ | Full + call | Complex businesses |

### MVP Launch
**Launch with:** Professional tier only
**Rationale:** Higher value, better margins, forces quality

### Early Adopter Pricing
- Professional: €497 (first 20 customers)
- Then: €697 standard

---

## 3. User Journey

### Acquisition
```
Landing Page → Free AI Readiness Score (lead capture) → Email nurture → Paid audit
```

### Free Lead Magnet: "AI Readiness Score"
- 5 questions (2 minutes)
- Instant score (0-100)
- Email required for results
- Upsell to full audit

### Paid Flow
```
1. Select tier + pay (Stripe)
2. Complete intake questionnaire (10 min)
3. AI analysis runs (show progress)
4. Review findings (optional)
5. Download report (PDF)
6. Follow-up email (7 days): "Ready to implement?"
```

---

## 4. Intake Questionnaire

### Structure: 25 questions, ~10 minutes

**Section 1: Company Profile (5 questions)**
1. Company name
2. Industry (dropdown)
3. Number of employees (ranges)
4. Annual revenue range
5. Website URL

**Section 2: Current Operations (8 questions)**
6. Main service/product offerings
7. Describe your typical customer journey
8. What tools do you currently use? (multi-select + other)
9. Which processes take the most time?
10. What tasks feel repetitive?
11. Where do errors/mistakes happen most?
12. How do you currently handle customer inquiries?
13. What reporting/analytics do you do?

**Section 3: Pain Points (5 questions)**
14. Top 3 operational frustrations
15. What have you tried to automate before?
16. What stopped those efforts?
17. How much time per week is spent on admin tasks?
18. Rate your team's comfort with new technology (1-5)

**Section 4: Goals & Constraints (7 questions)**
19. What would success look like in 12 months?
20. Budget for new tools/implementation (ranges)
21. Timeline expectations (ASAP / 3 months / 6 months / exploring)
22. Who makes technology decisions?
23. Any compliance requirements? (GDPR, HIPAA, etc.)
24. Existing contracts/commitments to consider?
25. Anything else we should know? (open text)

---

## 5. CRB Analysis Engine

### Phase 1: Discovery (Automated)
- Parse intake responses
- Identify tech stack
- Map core processes
- Extract pain points

### Phase 2: Research (AI + Database)
- Pull industry benchmarks
- Search relevant vendors
- Find comparable case studies
- Validate with web search

### Phase 3: Analysis (AI)
- Score automation potential per process
- Calculate current cost of inefficiency
- Identify AI/automation opportunities
- Assess implementation complexity

### Phase 4: Modeling (AI + Calculator)
- ROI calculation per recommendation
- Vendor comparison matrix
- Implementation timeline
- Risk assessment

### Phase 5: Report Generation
- Executive summary
- Findings matrix (effort vs impact)
- Detailed recommendations
- Appendix (sources, methodology)

---

## 6. Report Structure

### Executive Summary (1 page)
- AI Readiness Score (0-100)
- Top 3 opportunities with € impact
- Recommended first action
- Total potential annual savings
- Investment required

### Findings Overview (1-2 pages)
- Impact/Effort matrix visualization
- Category breakdown (process, technology, cost, risk)
- Priority ranking

### Detailed Recommendations (1 page each)
For each finding:
```
TITLE: [Clear, actionable title]

THE PROBLEM
- Current state description
- Cost of inaction (€/year)
- Evidence from your intake

THE SOLUTION
- Recommended approach
- Why this works
- Alternative approaches considered

IMPLEMENTATION
- Steps to implement
- Timeline (weeks)
- Resources needed
- Risks and mitigations

VENDORS (if applicable)
| Vendor | Price | Pros | Cons | Our Take |
|--------|-------|------|------|----------|
| Option A | €X/mo | ... | ... | Best for... |
| Option B | €Y/mo | ... | ... | Best if... |

ROI ANALYSIS
- Implementation cost: €X
- Annual savings: €Y
- Payback period: Z months
- 3-year ROI: X%

ASSUMPTIONS
- [List all assumptions explicitly]
- [If assumption wrong, impact is...]

CONFIDENCE: [High/Medium/Low] - [Why]

SOURCES
- [Citation 1]
- [Citation 2]
```

### Appendix
- Full methodology explanation
- Data sources
- Glossary of terms
- About CRB Analyser

---

## 7. Vendor Database (MVP)

### Categories (6)
1. **CRM** - HubSpot, Pipedrive, Salesforce, Zoho, Freshsales
2. **Project Management** - Asana, Monday, ClickUp, Notion, Trello
3. **Automation** - Zapier, Make, n8n, Workato
4. **AI Tools** - ChatGPT/OpenAI, Claude, Jasper, Copy.ai
5. **Customer Service** - Intercom, Zendesk, Freshdesk, HelpScout
6. **Analytics** - Mixpanel, Amplitude, Hotjar, Google Analytics

### Per Vendor Data
```json
{
  "name": "HubSpot",
  "category": "crm",
  "pricing": {
    "model": "per_seat",
    "tiers": [
      {"name": "Free", "price": 0, "limits": "..."},
      {"name": "Starter", "price": 20, "per": "user/month"},
      {"name": "Professional", "price": 100, "per": "user/month"}
    ],
    "verified_date": "2024-12-01"
  },
  "best_for": ["agencies", "saas", "services"],
  "avoid_if": ["enterprise", "complex_sales"],
  "implementation": {
    "avg_weeks": 4,
    "avg_cost_smb": 3000
  },
  "ratings": {
    "g2": 4.4,
    "capterra": 4.5
  }
}
```

### MVP Scope
- 30 vendors total (5 per category)
- Manual curation initially
- Pricing verified monthly

---

## 8. Industry Benchmarks (MVP)

### Industries Covered
1. Marketing/Creative Agencies
2. Accounting/Bookkeeping
3. Legal Services
4. Recruitment/Staffing

### Metrics Per Industry
```json
{
  "industry": "marketing_agency",
  "company_size": "11-50",
  "metrics": {
    "labor_cost_ratio": 0.65,
    "admin_time_waste_percent": 35,
    "billable_utilization": 0.60,
    "avg_project_margin": 0.40,
    "client_acquisition_cost": 2500,
    "client_lifetime_months": 18
  },
  "automation_potential": {
    "reporting": 0.80,
    "scheduling": 0.70,
    "invoicing": 0.90,
    "client_comms": 0.40,
    "content_creation": 0.50
  },
  "sources": [
    {"name": "SoDA Report 2024", "url": "..."},
    {"name": "Agency Management Institute", "url": "..."}
  ]
}
```

### MVP Scope
- 4 industries
- 3 company sizes each (small, medium, large)
- 10 metrics per combination
- Manual curation from public reports

---

## 9. Technical Decisions

### Infrastructure
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Database | Separate Supabase project | Isolation, clean data |
| Backend port | 8383 | Avoid MMAI conflict (8282) |
| Frontend port | 5174 | Avoid MMAI conflict (5173) |
| Hosting | Railway | Proven with MMAI |
| PDF generation | Server-side (Python) | Consistent output |

### AI Model Routing
| Query Type | Model | Cost |
|------------|-------|------|
| Simple lookups | Haiku | $0.001 |
| Multi-tool research | Sonnet | $0.01 |
| Strategic synthesis | Sonnet | $0.01 |
| Report generation | Sonnet | $0.02 |

**Estimated cost per audit:** €2-5

### Caching Strategy
- Tool results: 24h TTL
- Vendor pricing: 7 days TTL
- Benchmarks: 30 days TTL
- User sessions: 8 hours TTL

---

## 10. Launch Plan

### Week 1-2: Build MVP
- Foundation + Auth
- Intake system
- Basic CRB agent
- PDF report generation
- Stripe integration

### Week 3: Beta
- 5 free audits to network
- Collect feedback
- Fix critical issues
- Refine report quality

### Week 4: Soft Launch
- Open paid tier
- €497 early adopter price
- Target: 10 paying customers
- LinkedIn/Twitter announcements

### Month 2: Marketing
- Content marketing (blog posts)
- Case studies from beta
- Consider paid ads
- Referral program

---

## 11. Success Metrics

### MVP (Month 1)
| Metric | Target |
|--------|--------|
| Paying customers | 10 |
| Revenue | €5,000 |
| Report completion rate | >90% |
| Avg report quality (self-assessed) | >4/5 |

### Growth (Month 3)
| Metric | Target |
|--------|--------|
| Paying customers | 50 |
| Revenue | €25,000 |
| Customer satisfaction (NPS) | >50 |
| Referral rate | >20% |

---

## 12. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| AI hallucinations | Medium | High | Source validation, confidence scores, human review option |
| Low conversion | Medium | Medium | Strong lead magnet, case studies, money-back guarantee |
| Report quality variance | Medium | High | Templates, quality checklist, beta testing |
| Vendor data stale | High | Medium | "Last verified" dates, automated alerts |
| Competitor copies | Medium | Low | Speed to market, brand building, data moat |

---

## 13. Out of Scope (MVP)

- Interactive web dashboard (PDF only for MVP)
- Multiple languages (English only)
- White-label/API access
- Team collaboration features
- Re-audit comparisons
- Integrations (Notion, Slack, etc.)

---

## 14. Definition of Done

### Report is "Done" when:
- [ ] All findings have sources cited
- [ ] All ROI calculations show assumptions
- [ ] Vendor recommendations use verified pricing
- [ ] PDF renders correctly
- [ ] No placeholder text remains
- [ ] Confidence scores assigned

### Feature is "Done" when:
- [ ] Works in production environment
- [ ] Error handling in place
- [ ] Logged and monitored
- [ ] Basic test coverage
- [ ] Documentation updated

---

## Appendix: Decision Log

| # | Decision | Choice | Date |
|---|----------|--------|------|
| 1 | Target vertical | Professional services (agencies first) | Dec 2024 |
| 2 | Launch tier | Professional only | Dec 2024 |
| 3 | Starter price | €147 | Dec 2024 |
| 4 | Professional price | €697 (€497 early) | Dec 2024 |
| 5 | Lead gen | Free AI readiness score | Dec 2024 |
| 6 | Intake depth | 25 questions (~10 min) | Dec 2024 |
| 7 | Human review | Automated (human optional later) | Dec 2024 |
| 8 | Vendor DB scope | 30 vendors (6 categories) | Dec 2024 |
| 9 | Report format | PDF only (MVP) | Dec 2024 |
| 10 | Infrastructure | Separate Supabase | Dec 2024 |
| 11 | Beta target | 5 users (network) | Dec 2024 |
| 12 | Brand name | CRB Analyser | Dec 2024 |

---

**PRD Status:** APPROVED - Ready to build
