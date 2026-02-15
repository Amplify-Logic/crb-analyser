# Cold Outreach Plan - 10,000 Lead Burn Campaign

> **Status:** Draft | **Risk Level:** Medium-High | **Last Updated:** 2024-12-30

---

## Honest Assessment

**What you're doing:** Cold emailing 10,000 scraped leads with a free offer.

**Why it might work:**
- Offer is genuinely free (no pitch, just value)
- Industry insights are legitimately useful
- Low commitment ask (take quiz, get free stuff forever)

**Risks:**
- Domain blacklisting if done wrong
- Low open/reply rates (2-10% typical for cold)
- Tools may shut you down if you trigger spam flags
- Wasted effort if targeting is off

**Mitigation:** Use separate domain, warm properly, clean list, go slow.

---

## Tool Stack

| Tool | Purpose | Free Tier Limits |
|------|---------|------------------|
| Apollo.io | Lead sourcing | 10,000 leads/month, limited emails |
| Axiom.ai | Browser automation | 100 runs/month (free) |
| Reply.io | Email sending | 200 emails/month (very limited) |
| Brevo | Backup sending | 300 emails/day |
| Hunter.io | Email verification | 25 verifications/month (free) |
| NeverBounce | Email verification | Pay-as-you-go (~$0.003/email) |

**Reality check on Reply.io:** The free tier is 200 emails/month, not unlimited. You'll need to either:
- Pay for Reply.io ($59/month for 1,000 emails)
- Use Brevo/Mailgun/SMTP directly
- Use multiple accounts (risky, may get banned)

---

## Phase 1: Infrastructure Setup (Day 1-3)

### 1.1 Domain Setup

**DO NOT use your main domain (crbanalyser.com)**

Buy a separate domain for cold outreach:
- `crbinsights.com`
- `aibenchmarks.io`
- `[industry]aiready.com`

**Why:** If domain gets burned, your main brand is protected.

```
Setup checklist:
[ ] Buy domain (~$12/year)
[ ] Set up Google Workspace or Zoho Mail ($6/user/month or free)
[ ] Configure SPF, DKIM, DMARC records
[ ] Create 2-3 email addresses (insights@, research@, [yourname]@)
```

### 1.2 Email Warming

**Critical:** New domains have zero reputation. Send cold emails day 1 = straight to spam.

**Option A: Manual warming (free, slow)**
- Send 10-20 emails/day to real people you know
- Have them reply, mark as important, move from spam
- Do this for 2-3 weeks minimum

**Option B: Warming service (paid, faster)**
- Warmup Inbox, Lemwarm, or Mailreach (~$29/month)
- Automatically sends/receives emails to build reputation
- 2 weeks minimum before sending cold

**Warming schedule:**
```
Week 1: 10-20 emails/day (manual or warming service)
Week 2: 30-50 emails/day
Week 3: 50-100 emails/day (can start light cold outreach)
Week 4+: Scale to 100-200/day max per inbox
```

### 1.3 Tool Accounts

```
[ ] Apollo.io - Sign up, verify account
[ ] Axiom.ai - Install Chrome extension
[ ] Reply.io OR Brevo - Set up, connect domain
[ ] NeverBounce - Account for verification ($30 for 10k verifications)
```

---

## Phase 2: Lead Sourcing (Day 4-7)

### 2.1 Apollo.io Direct Export

Apollo free tier allows exporting leads with emails (limited).

**Filters to use:**
```
Job Titles: Owner, CEO, COO, Founder, Managing Director, General Manager
Company Size: 2-200 employees
Industries: [Your target - dental, home services, professional services, etc.]
Location: [Your target geography]
```

**Process:**
1. Build saved search in Apollo
2. Export up to limits (10k leads/month on free)
3. Download CSV with: Name, Email, Company, Title, Industry

**If Apollo gives you emails directly → Skip to Phase 3**

### 2.2 Apollo + Axiom Workaround (If Email Limited)

If Apollo restricts email access on free tier:

**Axiom workflow:**
```
1. Log into Apollo
2. Navigate to saved search results
3. For each page:
   - Scroll to load all results
   - Extract: Name, Company, LinkedIn URL, Title
   - Save to Google Sheet
4. Repeat for X pages
```

**Axiom setup:**
- Record the workflow manually first
- Set up loop for pagination
- Export to Google Sheets

**Email finding (after extraction):**
```
Method A: Hunter.io domain search
- Input company domain → Get email pattern
- 25 free/month (need to pay for volume)

Method B: Email pattern guessing
- Common patterns: first@company.com, first.last@company.com
- Use tool like Email Permutator to generate guesses
- Verify with NeverBounce before sending

Method C: LinkedIn + Axiom
- Visit LinkedIn profiles
- Extract any visible email
- Most won't have public email (low yield)
```

### 2.3 Email Verification

**Do not skip this.** Sending to bad emails = instant reputation damage.

```
1. Upload CSV to NeverBounce (or ZeroBounce, Hunter)
2. Remove: invalid, catch-all (risky), disposable
3. Keep only: valid, accept-all (with caution)
4. Target: <5% bounce rate
```

**Cost:** ~$30 for 10,000 verifications on NeverBounce

---

## Phase 3: List Segmentation (Day 8)

### 3.1 Segment by Industry

Create separate lists for each industry you support:
```
- dental_practices.csv (X leads)
- home_services.csv (X leads)
- professional_services.csv (X leads)
- recruiting_agencies.csv (X leads)
- etc.
```

**Why:** Personalization by industry dramatically improves open rates.

### 3.2 Segment by Title

```
- owners_founders.csv (highest authority)
- c_suite.csv (CEO, COO, CFO)
- operations.csv (Ops Manager, etc.)
```

---

## Phase 4: Email Copy (Day 9-10)

### 4.1 The Offer

**What they get:**
1. Free AI Readiness Teaser Report (immediate)
2. Weekly industry insights from aggregated data (ongoing)
3. Nothing to buy, no pitch

**Positioning:**
- "We're building the largest AI readiness benchmark for [industry]"
- "Contribute your data, get insights from hundreds of peers"
- "100% free, we're in research mode"

### 4.2 Email Sequence

**Email 1: Initial outreach**

```
Subject: Quick question about [Company Name]

Hi [First Name],

I'm building an AI readiness benchmark specifically for [industry] businesses.

We're analyzing how companies like [Company Name] are (or aren't) using AI
to save time and cut costs.

Would you be open to a 5-minute quiz? In return:
- You get a free AI Readiness Report for your business
- You get weekly insights from [X] other [industry] businesses
- No sales pitch, no cost, ever

[LINK TO QUIZ]

The data stays anonymous. You just see how you compare.

Interested?

[Your name]
[Your title], CRB Insights
```

**Email 2: Follow-up (3 days later)**

```
Subject: Re: Quick question about [Company Name]

Hi [First Name],

Quick follow-up on my note about the AI readiness benchmark.

We've already had [X] [industry] businesses complete it. Early findings:
- [Insight 1 - e.g., "67% are still doing X manually"]
- [Insight 2 - e.g., "Top performers save 12 hours/week on Y"]

Takes 5 minutes, completely free: [LINK]

[Your name]
```

**Email 3: Break-up (5 days later)**

```
Subject: Closing the loop

Hi [First Name],

Last note from me on this.

If AI readiness isn't on your radar right now, totally understand.

If you want the free benchmark report later, link stays live: [LINK]

Either way, good luck with [Company Name].

[Your name]
```

### 4.3 Personalization Variables

```
{{first_name}} - First name
{{company_name}} - Company name
{{industry}} - Their industry
{{title}} - Their job title
```

**Extra personalization (higher effort, higher response):**
- Reference their website
- Reference recent news/LinkedIn post
- Reference specific pain point for their role

---

## Phase 5: Sending (Day 11+)

### 5.1 Reply.io Setup (If Using)

```
1. Connect your warmed email account
2. Create campaign with 3-email sequence
3. Set delays: Email 2 at +3 days, Email 3 at +5 days
4. Set daily limits: 50-100 emails/day max per inbox
5. Enable tracking (opens, clicks)
```

**Free tier limit:** 200 emails/month
**Paid tier:** $59/month for 1,000 emails

### 5.2 Brevo Alternative (Higher Volume)

If Reply.io limits are too restrictive:

```
1. Import verified list to Brevo
2. Create automation workflow
3. Set sending limits: 300/day (free tier)
4. Segment sends across days

10,000 leads ÷ 300/day = 34 days to send initial email
```

**Note:** Brevo is more email marketing than cold outreach. Deliverability may be lower for cold lists.

### 5.3 Sending Schedule

```
Week 1:  500 leads (test batch - measure opens, replies, bounces)
Week 2:  1,500 leads (if Week 1 looks good)
Week 3:  3,000 leads (scale if metrics hold)
Week 4:  5,000 leads (remaining)
```

**Stop immediately if:**
- Bounce rate > 5%
- Spam complaints appear
- Open rate < 10%
- Getting blacklist warnings

### 5.4 Monitoring

Check daily:
```
[ ] Bounce rate (must stay <5%)
[ ] Spam complaints (must stay near 0)
[ ] Open rate (target >20%)
[ ] Reply rate (target >2%)
[ ] Quiz completions (ultimate goal)
```

**Tools:**
- Reply.io dashboard
- Google Postmaster Tools (see domain reputation)
- MXToolbox (check blacklists)

---

## Phase 6: Response Handling

### 6.1 Positive Responses

```
"Sure, I'll take the quiz" → Send quiz link, thank them
"Tell me more" → Brief explanation, link to quiz
"This is interesting" → Engage, answer questions, soft push to quiz
```

### 6.2 Negative Responses

```
"Not interested" → "No problem, thanks for letting me know. Good luck with [Company]."
"Remove me" → Remove immediately, reply confirming
"How did you get my email?" → "From Apollo/LinkedIn. Happy to remove you."
```

**Never argue. Always remove if asked.**

### 6.3 Unsubscribe Handling

Add unsubscribe link to emails (legally required in many jurisdictions):
```
[Unsubscribe from future emails]
```

Manage unsubs in your sending tool.

---

## Cost Breakdown

### Free/Minimal Path

| Item | Cost |
|------|------|
| New domain | $12 |
| Zoho Mail (free tier) | $0 |
| Apollo (free tier) | $0 |
| Axiom (free tier) | $0 |
| NeverBounce (10k verifications) | $30 |
| Brevo (free tier) | $0 |
| **Total** | **~$42** |

### Realistic Path (Better Deliverability)

| Item | Cost |
|------|------|
| New domain | $12 |
| Google Workspace | $6/month |
| Email warming (Warmup Inbox) | $29/month |
| Apollo (free tier) | $0 |
| NeverBounce | $30 |
| Reply.io (paid) | $59/month |
| **Total** | **~$136 first month** |

---

## Axiom Automation Workflows

### Workflow 1: Apollo Lead Scraping

```yaml
name: Apollo Lead Scraper
steps:
  - navigate: https://app.apollo.io/
  - wait: 3 seconds
  - login: (manual first time, then cookies persist)
  - navigate: saved_search_url
  - loop:
      count: 100 (pages)
      steps:
        - scroll: to_bottom
        - wait: 2 seconds
        - extract:
            selector: ".contact-row"
            fields:
              - name: ".contact-name"
              - company: ".company-name"
              - title: ".job-title"
              - linkedin: ".linkedin-link @href"
        - click: ".next-page"
        - wait: 3 seconds
  - export: google_sheets
```

### Workflow 2: Email Pattern Finding

```yaml
name: Hunter Domain Search
steps:
  - input: company_domain (from sheet)
  - navigate: https://hunter.io/search/{company_domain}
  - extract:
      - email_pattern: ".email-pattern"
      - confidence: ".confidence-score"
  - export: append_to_sheet
  - wait: 5 seconds (rate limit)
```

---

## Legal Considerations

### CAN-SPAM (US)

- Include physical address in emails
- Include unsubscribe link
- Honor opt-outs within 10 days
- Don't use deceptive subject lines

### GDPR (EU)

- Need legitimate interest or consent
- Must provide way to opt out
- Must delete data on request
- **Risk:** Cold emailing EU contacts without consent is technically non-compliant

### Recommendation

- Focus on US/non-EU leads initially
- Include clear unsubscribe
- Honor all removal requests immediately
- Keep records of consent/opt-outs

---

## Success Metrics

### Target Funnel

```
10,000 leads sent
    ↓ 25% open (2,500 opens)
    ↓ 3% click (300 quiz starts)
    ↓ 60% complete (180 completed quizzes)
    ↓ 30% email verified (54 quality leads)
```

**Realistic expectation:** 50-200 completed quizzes from 10,000 cold emails.

### What "Success" Looks Like

- 50+ completed quizzes
- 0 major deliverability issues
- <5% bounce rate maintained
- Handful of warm responses to nurture
- Data to improve targeting/copy

---

## Abort Criteria

**Stop the campaign if:**

| Signal | Threshold | Action |
|--------|-----------|--------|
| Bounce rate | >5% | Stop, clean list, reassess |
| Spam complaints | >0.1% | Stop immediately |
| Open rate | <10% after 500 sends | Stop, fix subject lines |
| Blacklist warning | Any | Stop, check MXToolbox, remediate |
| Tool account suspended | Any | Stop, assess why |

---

## Timeline

```
Days 1-3:   Infrastructure (domain, warming starts, tool setup)
Days 4-7:   Lead sourcing and cleaning
Days 8-10:  List segmentation + email copy
Day 11:     Send test batch (100 leads)
Day 12-13:  Analyze test results
Day 14+:    Scale sending (if metrics are good)
Days 14-45: Full send + response handling
Day 46+:    Analyze results, decide next steps
```

---

## Post-Campaign

### If It Works

- Refine targeting based on who responded
- Improve copy based on open/reply rates
- Scale to next 10k with learnings
- Build nurture sequence for quiz completers

### If It Doesn't Work

- Analyze where funnel broke (opens? clicks? completions?)
- Consider: was targeting wrong? copy wrong? offer unclear?
- Pivot to warmer channels (LinkedIn, partnerships)
- Don't burn more leads with same broken approach

---

## Checklist

### Setup
- [ ] Buy separate domain
- [ ] Set up email (Google Workspace or Zoho)
- [ ] Configure SPF, DKIM, DMARC
- [ ] Start email warming
- [ ] Create Apollo account
- [ ] Create Axiom account
- [ ] Create Reply.io or Brevo account
- [ ] Create NeverBounce account

### Lead Sourcing
- [ ] Define ICP filters in Apollo
- [ ] Export/scrape leads
- [ ] Verify emails with NeverBounce
- [ ] Remove invalid/catch-all
- [ ] Segment by industry
- [ ] Segment by title

### Email Prep
- [ ] Write 3-email sequence
- [ ] Set up personalization variables
- [ ] Add unsubscribe link
- [ ] Test emails to yourself
- [ ] Check spam score (Mail Tester)

### Sending
- [ ] Send test batch (100)
- [ ] Check metrics after 24-48 hours
- [ ] Adjust if needed
- [ ] Scale to full list
- [ ] Monitor daily

### Response Handling
- [ ] Set up response templates
- [ ] Check inbox 2x daily
- [ ] Remove opt-outs immediately
- [ ] Forward positive responses to quiz

---

*This plan carries real risks. Protect your main domain. Go slow. Stop if signals are bad.*
