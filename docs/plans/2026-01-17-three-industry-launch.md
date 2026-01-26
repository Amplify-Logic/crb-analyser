# ReadyPath Launch Plan: Three Industry Focus

> **Goal:** First paying customer within 7 days
> **Industries:** Professional Services, Dental, Home Services
> **Price:** €147 single tier
> **Created:** 2026-01-17

---

## Executive Summary

We launch with three industries where our knowledge base is strongest:

| Industry | Score | Target Customer | One Specific Benefit |
|----------|-------|-----------------|----------------------|
| **Professional Services** | 93/100 | Solo attorneys, small accounting firms | "Recover the 15% of billable time your team forgets to log" |
| **Dental** | 91/100 | Solo/group dental practices | "Capture the 25% of patient calls going to voicemail" |
| **Home Services** | 87/100 | Plumbers, electricians, HVAC (5-50 staff) | "Fit 2 more jobs per technician per day" |

**Why these three:**
- Deepest knowledge base (15+ opportunities, 70+ benchmarks each)
- Clear ROI stories with specific numbers
- Business owners who buy software (not tire-kickers)
- Different enough to test market response

**Price:** €147 single tier. No calls, no upsells. Report delivers the value.

---

## Phase 1: Critical Path (Days 1-2)

### Must Work Before Anything Else

Run these tests. Fix failures. Nothing else matters until these pass.

#### Test 1: Quiz → Completion
```
1. http://localhost:5174/quiz?new=true (incognito)
2. Complete as "dental practice owner"
3. Verify: Score shown, session saved
```

#### Test 2: Report Generation
```
1. Trigger report for completed quiz
2. Wait for generation (watch logs)
3. Verify: All sections populated, vendors have pricing
```

#### Test 3: Payment Flow
```
1. Go to checkout
2. Use test card: 4242 4242 4242 4242
3. Verify: Payment succeeds, report unlocks
```

#### Test 4: Report Access
```
1. As paid user, view full report
2. Verify: All sections visible, PDF/share works
```

**If any test fails → that's your Day 1-2 work.**

---

## Phase 2: Industry-Specific Setup (Day 3)

### 2.1 Landing Page Variants

Create three targeted entry points:

| URL | Industry | Headline |
|-----|----------|----------|
| `/quiz?industry=professional-services` | Professional Services | "AI Readiness for Law Firms & Accountants" |
| `/quiz?industry=dental` | Dental | "AI Readiness for Dental Practices" |
| `/quiz?industry=home-services` | Home Services | "AI Readiness for Trade Businesses" |

Each variant shows:
- Industry-specific pain points (from knowledge base)
- Relevant ROI example
- Testimonial placeholder (update post-launch)

### 2.2 Quiz Industry Detection

Ensure quiz detects industry from:
1. URL parameter (if provided)
2. First question response
3. Company name/description analysis

**File:** `backend/src/services/quiz_engine.py`

### 2.3 Report Industry Customization

Verify reports use correct:
- Industry benchmarks
- Industry vendors
- Industry-specific opportunities

**Test:** Generate one report per industry, verify vendors are appropriate.

---

## Phase 3: Stripe Setup (Day 3)

### Single Product Launch

| Product | Price | Description |
|---------|-------|-------------|
| **CRB Report** | €147 | AI readiness analysis with actionable recommendations |

**Stripe Dashboard Steps:**
1. Create product "CRB Report"
2. Set price €147 EUR (one-time)
3. Add description: "Complete AI readiness analysis for your business"
4. Get price ID for checkout integration
5. Configure webhook for `checkout.session.completed`

### Checkout Flow
- No tier selection (single price)
- Email capture before payment
- Redirect to report after success

---

## Phase 4: Go-to-Market by Industry (Days 4-7)

### 4.1 Professional Services

**Target:** Solo attorneys, 2-10 person accounting firms, consultants

**Where they are:**
- LinkedIn (heavy users)
- Legal/accounting industry groups
- Local bar associations
- Accounting associations

**Outreach message:**
> "I built a tool that analyzes your practice and tells you exactly which AI tools would actually save you time. For law firms, the #1 finding is usually AI time capture - most firms lose 15% of billable hours to manual tracking. Takes 5 minutes to get your personalized analysis."

**Key ROI to lead with:**
- AI Time Capture: 15% more billable hours recovered
- AI Receptionist: 20% more qualified leads captured
- Document Drafting: 8 hours/week saved

**LinkedIn Post Draft:**
```
I spent 6 months researching AI tools for professional services firms.

The #1 opportunity for most law firms and accounting practices?
AI-powered time capture.

The average professional loses 15% of billable time because they forget to log it.

Tools like Timely, Chrometa, and Clio's AI features can capture time automatically from:
- Calendar meetings
- Email correspondence
- Document editing

One solo attorney I talked to found $3,200/month in unbilled time.

I built a free quiz that analyzes your practice and tells you which AI tools would have the biggest impact.

Takes 5 minutes: [link]
```

### 4.2 Dental Practices

**Target:** Solo practitioners, group practices, DSO locations

**Where they are:**
- Dental Town forum
- State dental associations
- Dental practice management Facebook groups
- Dentalpreneur community

**Outreach message:**
> "25% of calls to dental practices go to voicemail. I built a tool that analyzes your practice and shows exactly which AI tools would help you capture more patients. Most practices can add €3,000-5,000/month just by not missing calls."

**Key ROI to lead with:**
- AI Receptionist: 15-25% more appointments captured
- Automated Reminders: 50% reduction in no-shows
- Insurance Verification: 75% time saved on eligibility

**Forum Post Draft:**
```
Title: Which AI tools actually work for dental practices? (I researched 50+)

I spent months researching AI tools specifically for dental.

Here's what actually moves the needle:

1. AI Voice/Phone Systems (Weave, RevenueWell)
   - Answer calls 24/7
   - Book appointments automatically
   - ROI: 15-25% more appointments from captured calls

2. Automated Patient Communication (Lighthouse 360, Solutionreach)
   - Text reminders reduce no-shows by 50%
   - Recall campaigns run automatically
   - ROI: 10-15% more appointments kept

3. AI Imaging Analysis (Pearl, Overjet)
   - Catch what you might miss
   - Better case presentation
   - ROI: Harder to measure, but liability reduction is real

I built a quiz that analyzes your practice and tells you which tools would have the biggest impact.

5 minutes, personalized recommendations: [link]
```

### 4.3 Home Services

**Target:** Plumbers, electricians, HVAC companies, builders (5-50 employees)

**Where they are:**
- Trade-specific Facebook groups
- Contractor forums
- Local trade associations
- Nextdoor contractor recommendations

**Outreach message:**
> "The average 5-tech HVAC company leaves €30,000/month on the table with manual scheduling. Route optimization alone lets you fit 2 more jobs per tech per day. I built a tool that shows trade businesses exactly which AI would make the biggest difference."

**Key ROI to lead with:**
- AI Dispatch: 15-25% more jobs/day (1000% ROI claim)
- AI Call Handling: 10-20% more booked jobs
- Automated Quoting: 50% faster estimates

**Facebook Post Draft:**
```
Running a trade business? Here's what AI can actually do for you in 2026:

SCHEDULING/DISPATCH:
ServiceTitan, Housecall Pro, Jobber all have AI features now.
The big win: route optimization.
5 techs × 2 extra jobs/day × €150/job = €33,000/month

PHONE HANDLING:
Miss calls after hours? AI can answer, book jobs, take payments.
Most trades lose 30% of after-hours calls to voicemail.

QUOTING:
AI can generate quotes from photos.
Turn a 30-minute estimate into 5 minutes.

I built a free quiz that analyzes YOUR business and tells you which tools would have the biggest impact.

5 minutes, completely personalized: [link]

What's your biggest time-waster right now? Scheduling? Paperwork? Something else?
```

---

## Phase 5: Soft Launch (Day 4-5)

### Test Users (5 total)

| # | Industry | Relationship | What to test |
|---|----------|--------------|--------------|
| 1 | Professional Services | Friend/contact | Full flow, honest feedback |
| 2 | Dental | Friend/contact | Full flow, honest feedback |
| 3 | Home Services | Friend/contact | Full flow, honest feedback |
| 4 | Any | Skeptical friend | "Would you pay €147 for this?" |
| 5 | Non-technical | Family member | "Where did you get confused?" |

### Feedback Questions
1. "On a scale of 1-10, how useful was the report?"
2. "What was the single most valuable insight?"
3. "What was confusing or unclear?"
4. "Would you pay €147 for this? Why/why not?"
5. "Who else should I show this to?"

### Fix Priority
Only fix things that prevent purchase or destroy value. Not:
- Minor UI issues
- "Nice to have" features
- Cosmetic improvements

---

## Phase 6: Public Launch (Days 6-7)

### Launch Sequence

**Day 6 Morning:**
1. Post on LinkedIn (personal account)
2. Post in 1 professional services community
3. Post in 1 dental community
4. Post in 1 home services community

**Day 6 Evening:**
- Monitor for questions/comments
- Respond to all engagement within 2 hours
- Track: quiz starts, completions, checkouts

**Day 7:**
- Follow up on Day 6 engagement
- Share in 1-2 more communities per industry
- Personal outreach to 5 contacts per industry

### What NOT to do
- Don't buy ads (validate organic first)
- Don't build new features (ship what you have)
- Don't write blog posts (direct outreach works faster)
- Don't create videos (text is fine for now)

---

## Success Metrics

### Week 1 Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Quiz starts | 30+ | `quiz_sessions` count |
| Quiz completions | 15+ | `quiz_sessions` where status='completed' |
| Checkout initiated | 5+ | Stripe dashboard |
| **Payments** | **1+** | Stripe dashboard |

### By Industry (nice to track)

| Industry | Quiz Starts | Completions | Payments |
|----------|-------------|-------------|----------|
| Professional Services | 10+ | 5+ | 1 |
| Dental | 10+ | 5+ | 0 |
| Home Services | 10+ | 5+ | 0 |

### Month 1 Targets

| Metric | Target |
|--------|--------|
| Revenue | €500+ (3 sales) |
| Reports delivered | 5+ |
| Customer feedback | 3+ responses |
| Testimonial | 1 usable |

---

## Post-Launch Iteration

### Only Build What Customers Request

| Customer says... | Then build... |
|------------------|---------------|
| "I want to discuss findings" | €497 tier with 30-min call |
| "Help me implement" | €997 tier with support |
| "Vendor recs were wrong" | Improve that industry's vendor data |
| "Report was too long" | Executive summary PDF |
| "I want to compare myself" | Interactive ROI calculator |

### Don't Build Yet
- Voice interview
- Mobile app
- Team features
- API access
- White-label

---

## Industry-Specific Knowledge Gaps

### Professional Services (33 vendors, 15 opportunities)
**Strong:** Time tracking, document drafting, client intake
**Gaps:** More case study examples, specific legal document templates

### Dental (19 vendors, 7 opportunities)
**Strong:** Patient communication, insurance verification, AI imaging
**Gaps:** More DSO-specific content, multi-location scenarios

### Home Services (15 vendors, 5 opportunities)
**Strong:** Dispatch optimization, call handling, quoting
**Gaps:** Fewer vendors than competitors, need more trade-specific examples

### Quick Fixes (if time)
1. Add 2-3 more home services vendors
2. Add 1 case study per industry
3. Verify all pricing is current (check vendor websites)

---

## Technical Checklist

### Before Launch

```bash
# Backend
cd backend && source venv/bin/activate
uvicorn src.main:app --port 8383  # Starts without errors

# Frontend
cd frontend && npm run build     # Builds successfully

# Tests
cd backend && pytest             # All pass

# Services
redis-cli ping                   # PONG
curl http://localhost:8383/api/health  # {"status": "ok"}
```

### Environment Variables (Production)
```
SUPABASE_URL=✓
SUPABASE_SERVICE_KEY=✓
ANTHROPIC_API_KEY=✓
STRIPE_SECRET_KEY=✓
STRIPE_WEBHOOK_SECRET=✓
SECRET_KEY=✓
```

### Stripe Webhook
- Endpoint configured
- Recent successful deliveries in dashboard
- `checkout.session.completed` event enabled

---

## Daily Checklist

### Day 1-2: Critical Path
- [ ] Run all 4 tests from Phase 1
- [ ] Fix any failures
- [ ] Re-test until all pass

### Day 3: Setup
- [ ] Create Stripe product (€147)
- [ ] Test payment end-to-end
- [ ] Verify industry detection in quiz
- [ ] Generate test report for each industry

### Day 4: Soft Launch
- [ ] Send to 5 test users
- [ ] Collect feedback
- [ ] Fix critical issues only

### Day 5: Prepare
- [ ] Write LinkedIn post
- [ ] Write 3 industry community posts
- [ ] Identify 5 personal contacts per industry

### Day 6: Launch
- [ ] Post on LinkedIn
- [ ] Post in 3 communities (1 per industry)
- [ ] Monitor and respond to all engagement

### Day 7: Follow-up
- [ ] Respond to Day 6 comments
- [ ] Personal outreach to 15 contacts
- [ ] Track metrics

---

## The One Question

Before doing anything, ask:

> "Does this help a stranger pay €147 for a report in the next 7 days?"

If no, don't do it.

---

## Appendix: Industry Hooks Summary

### Professional Services
- **Pain:** Manual time tracking loses 15% of billable hours
- **Solution:** AI time capture + document drafting
- **ROI:** $3,200/month in recovered billable time
- **Vendors:** Timely, Chrometa, Clio, Smokeball

### Dental
- **Pain:** 25% of calls go to voicemail
- **Solution:** AI receptionist + automated reminders
- **ROI:** 15-25% more appointments, 50% fewer no-shows
- **Vendors:** Weave, Lighthouse 360, RevenueWell

### Home Services
- **Pain:** Manual scheduling leaves money on table
- **Solution:** AI dispatch + route optimization
- **ROI:** 2 more jobs/tech/day = €33,000/month (5 techs)
- **Vendors:** ServiceTitan, Housecall Pro, Jobber

---

## Next Action

**Open an incognito browser and run Test 1 from Phase 1.**

That's it. Start there.
