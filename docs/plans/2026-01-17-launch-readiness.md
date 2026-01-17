# ReadyPath Launch Readiness

> **Goal:** First paying customer this month
> **Insight:** Your report is already anti-slop. The blocker isn't quality - it's shipping.
> **Created:** 2026-01-17

---

## Reality Check

Your sample report (`backend/src/data/sample_report.json`) is **excellent**:
- Clear verdicts with confidence levels
- 3 options per recommendation with real NZ vendor pricing
- Week-by-week playbooks with specific tasks and owners
- ROI calculations with stated assumptions
- System architecture diagrams showing integrations

**This is a finished deliverable.** A builder in Warkworth could hand this to their accountant tomorrow.

The question isn't "is the report good enough?" - it's "can someone pay for one?"

---

## Part 1: Critical Path Test

Run these manually. If any fail, that's your blocker.

### Test 1: Quiz Completion
```
1. Open http://localhost:5174/quiz?new=true (incognito)
2. Complete all questions as a test user
3. Reach the end state
```
- [ ] Quiz loads without errors
- [ ] All questions display correctly
- [ ] Progress saves between steps
- [ ] Final screen shows AI readiness score or next step

**File:** `frontend/src/pages/Quiz.tsx`

### Test 2: Report Generation
```
1. Trigger report generation for a completed quiz session
2. Wait for completion (check backend logs)
3. View the generated report
```
- [ ] Report generates without 500 errors
- [ ] All sections populate (exec summary, findings, recommendations, roadmap)
- [ ] Vendor recommendations have real pricing
- [ ] ROI calculations are present

**Files:** `backend/src/services/report_service.py`, `frontend/src/pages/ReportViewer.tsx`

### Test 3: Payment Flow
```
1. Go to checkout for a report
2. Use Stripe test card: 4242 4242 4242 4242
3. Complete payment
4. Verify redirect and access
```
- [ ] Checkout page loads with correct price
- [ ] Stripe payment modal works
- [ ] Webhook processes successfully (check backend logs)
- [ ] User gets access to report after payment

**Files:** `backend/src/routes/payments.py`, `frontend/src/pages/Checkout.tsx`

### Test 4: Post-Purchase Access
```
1. As paid user, access report URL
2. Verify full report is visible
3. Check shareable link works
```
- [ ] Report loads for paid user
- [ ] All sections accessible (not gated)
- [ ] Shareable link generates and works

---

## Part 2: Launch Pricing

### Current State
Landing page shows a multi-step flow:
1. Quick quiz (5 min)
2. Deep dive (90 min)
3. AI analysis (24-48 hrs)
4. Report delivered

### Recommendation: Single Tier Launch

| Tier | Price | Includes |
|------|-------|----------|
| **CRB Report** | €197 | Full analysis, 3 options per finding, implementation playbook |

**Why €197:**
- Low enough for impulse purchase by SMB owner
- High enough to signal value (not a gimmick)
- Round up later based on conversion data

**Changes Required:**

1. **Stripe Dashboard:**
   - Create single product: "CRB Report" at €197
   - Archive other tiers (can re-enable later)

2. **Landing Page** (`frontend/src/pages/Landing.tsx`):
   - Simplify pricing section to single CTA
   - Remove tier comparison (for now)

3. **Checkout Flow:**
   - Single price, no tier selection

---

## Part 3: Report Anti-Slop Verification

Your report already passes. Verify these remain true:

### Executive Summary
- [x] AI readiness score with clear meaning
- [x] Top opportunities with value ranges
- [x] "Not recommended" section (tells them what to skip)
- [x] Clear verdict: Proceed / Caution / Wait

### Recommendations
- [x] 3 options each: Off-the-shelf, Best-in-class, Custom
- [x] Real vendor names and pricing (Fergus $79/mo, Buildxact $129/mo)
- [x] Our recommendation with rationale
- [x] ROI % and payback months

### Playbooks
- [x] Week-by-week breakdown
- [x] Specific tasks with hours and owner
- [x] Personalized to their team size and tech level

### What to Check
- [ ] Run report generation for 3 different industries
- [ ] Verify vendor recommendations are industry-appropriate
- [ ] Confirm playbook tasks are realistic (not generic fluff)

---

## Part 4: Launch Week Schedule

### Day 1-2: Fix Critical Path Failures
From Part 1 tests - fix anything that doesn't work.

Priority order:
1. Payment flow (no payment = no revenue)
2. Report generation (no report = no value)
3. Quiz completion (no quiz = no leads)

### Day 3: Pricing Simplification
1. Create €197 Stripe product
2. Update landing page
3. Test checkout end-to-end with real €1 charge

### Day 4: Soft Launch
Share with 5 people:
- 2 in target industries (dental, home services, professional services)
- 2 who will give honest feedback
- 1 who's not technical (tests clarity)

Ask them:
- "Did you understand what you'd get?"
- "Where did you get confused?"
- "Would you pay €197 for this?"

### Day 5: Fix Soft Launch Issues
Address friction points. Don't gold-plate - fix blockers only.

### Day 6-7: Public Launch
- [ ] LinkedIn post announcing ReadyPath
- [ ] Share in 2-3 relevant communities
- [ ] Enable basic analytics (quiz starts, completions, checkouts)

---

## Part 5: Technical Checklist

### Must Work

| Component | Test Command | Expected |
|-----------|--------------|----------|
| Backend starts | `cd backend && uvicorn src.main:app --port 8383` | No errors |
| Frontend builds | `cd frontend && npm run build` | Build succeeds |
| Tests pass | `cd backend && pytest` | All green |
| Redis connected | `redis-cli ping` | PONG |
| Supabase connected | Check `/api/health` | `{"status": "ok"}` |
| Stripe webhook | Check Stripe dashboard → Webhooks | Recent successful deliveries |

### Environment Variables (Production)
```bash
# Verify these are set in production
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
ANTHROPIC_API_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
SECRET_KEY=
```

### Database Migrations
```bash
# Ensure all migrations applied
cd backend && supabase db push
```

---

## Part 6: Success Metrics

### Week 1
| Metric | Target | How to Measure |
|--------|--------|----------------|
| Landing page visits | 100+ | Analytics |
| Quiz starts | 20+ | `quiz_sessions` where status != 'created' |
| Quiz completions | 10+ | `quiz_sessions` where status = 'completed' |
| Checkouts initiated | 3+ | Stripe dashboard |
| Payments completed | 1+ | Stripe dashboard |

### Month 1
| Metric | Target | How to Measure |
|--------|--------|----------------|
| Revenue | €500+ | Stripe |
| Completed reports | 5+ | `reports` table |
| Customer feedback | 3+ responses | Manual follow-up |
| Testimonial | 1 usable | Ask satisfied customers |

---

## Part 7: Post-Launch Iteration

### Only Build What Customers Request

| If customers say... | Then build... |
|---------------------|---------------|
| "I want to discuss the findings" | €497 tier with 30-min call |
| "Can you help me implement?" | €997 tier with implementation support |
| "The vendor recs were wrong" | Improve vendor matching for that industry |
| "Report was too long" | Add executive summary PDF export |
| "I want to compare options myself" | Interactive ROI calculator |

### Don't Build (Yet)
- Voice interview (optional, not blocking value)
- Mobile app
- Team collaboration features
- API access
- White-label version

---

## Part 8: Commands Reference

### Start Development
```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate && uvicorn src.main:app --reload --port 8383

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Redis (if not running)
brew services start redis
```

### Generate Test Report
```bash
cd backend && python -c "
from src.services.report_service import ReportService
# Trigger report for existing quiz session
"
```

### Check Logs for Errors
```bash
# Recent backend errors
cd backend && grep -r "ERROR\|Exception" logs/ 2>/dev/null | tail -20

# Stripe webhook logs
# Check: https://dashboard.stripe.com/webhooks
```

### Deploy
```bash
# Railway (if configured)
railway up
```

---

## Decision Log

| Decision | Rationale | Date |
|----------|-----------|------|
| Single €197 tier | Reduce friction, test pricing | 2026-01-17 |
| Skip voice interview for launch | Not blocking core value delivery | 2026-01-17 |
| Focus on 3 industries | Dental, home services, professional services have best KB data | 2026-01-17 |

---

## The One Question

Before adding any feature, ask:

> "Does this help a stranger pay €197 for a report this week?"

If no, don't build it.

---

## Next Action

**Run Part 1: Critical Path Test**

Open incognito browser. Complete quiz. Attempt payment. See what breaks.

That's your blocker list.
