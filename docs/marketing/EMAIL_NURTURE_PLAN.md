# Email Nurture Plan - Brevo Automation

> **Status:** Draft | **Tool:** Brevo (free tier) | **Last Updated:** 2024-12-30

---

## Overview

This plan covers what happens **after** someone completes the quiz and gives you their email. The cold outreach (Reply.io) gets them to the quiz. Brevo keeps them engaged forever.

```
Quiz Completed → Email Captured
         ↓
    Brevo List
         ↓
┌────────────────────────────────────┐
│  Automation Sequences              │
├────────────────────────────────────┤
│  1. Welcome + Teaser Report        │
│  2. Quick Win Follow-up            │
│  3. Weekly Industry Insights       │
│  4. Paid Report Upsell (later)     │
└────────────────────────────────────┘
```

---

## Brevo Free Tier Limits

| Feature | Limit |
|---------|-------|
| Contacts | Unlimited |
| Emails/day | 300 |
| Automation workflows | Yes |
| Transactional emails | Yes |
| Templates | Yes |

**300/day is enough for:**
- ~9,000 emails/month
- Nurturing thousands of leads
- Weekly insights to entire list (if <2,100 contacts)

---

## Setup Checklist

### 1. Account Setup
```
[ ] Create Brevo account (free)
[ ] Verify sending domain (DNS records)
[ ] Set up SPF, DKIM, DMARC
[ ] Add physical address (required for compliance)
[ ] Upload logo and brand colors
```

### 2. List Structure
```
Lists to create:
[ ] quiz_completers - Everyone who finished quiz
[ ] industry_dental - Dental practices
[ ] industry_home_services - Home services
[ ] industry_professional - Professional services
[ ] industry_recruiting - Recruiting agencies
[ ] paid_customers - People who bought full report
[ ] unsubscribed - Do not email
```

### 3. Contact Attributes
```
Custom fields to create:
[ ] first_name (text)
[ ] company_name (text)
[ ] industry (dropdown)
[ ] quiz_score (number)
[ ] ai_readiness_level (dropdown: Low/Medium/High)
[ ] report_id (text - link to their report)
[ ] signup_source (text: cold_email, organic, referral, partner)
[ ] signup_date (date)
```

### 4. Integration with Backend

**Option A: Brevo API (recommended)**

After quiz completion, backend calls Brevo API:

```python
# backend/src/services/brevo_service.py

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

class BrevoService:
    def __init__(self, api_key: str):
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = api_key
        self.api = sib_api_v3_sdk.ContactsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

    def add_quiz_completer(
        self,
        email: str,
        first_name: str,
        company_name: str,
        industry: str,
        quiz_score: int,
        report_id: str
    ):
        contact = sib_api_v3_sdk.CreateContact(
            email=email,
            attributes={
                "FIRSTNAME": first_name,
                "COMPANY_NAME": company_name,
                "INDUSTRY": industry,
                "QUIZ_SCORE": quiz_score,
                "REPORT_ID": report_id,
                "SIGNUP_DATE": datetime.now().isoformat()
            },
            list_ids=[1],  # quiz_completers list ID
            update_enabled=True
        )

        try:
            self.api.create_contact(contact)
        except ApiException as e:
            logger.error("brevo_add_contact_failed", error=str(e))
```

**Option B: Webhook/Zapier**

If you want no-code:
```
Quiz completion → Webhook to Zapier → Zapier adds to Brevo
```

---

## Automation Sequences

### Sequence 1: Welcome + Report Delivery

**Trigger:** Contact added to `quiz_completers` list

```
Immediately:     Email 1 - Report Delivered
+1 day:          Email 2 - How to Read Your Report
+3 days:         Email 3 - Your Quick Win
+7 days:         Email 4 - Industry Benchmark Comparison
```

---

#### Email 1: Report Delivered (Immediate)

```
Subject: Your AI Readiness Report is ready

Hi {{first_name}},

Your AI Readiness Report for {{company_name}} is ready.

[VIEW YOUR REPORT] → {{report_link}}

Here's a quick preview:

📊 Your AI Readiness Score: {{quiz_score}}/100
🏢 Industry Average: {{industry_average}}/100
🎯 Top Opportunity: {{top_opportunity}}

This report shows you:
- Where you're ahead of your industry
- Where you're leaving money on the table
- The #1 quick win you could implement this week

Over the next few weeks, I'll send you insights from other
{{industry}} businesses taking this assessment.

You'll see real patterns from real businesses—anonymized,
but specific enough to act on.

Talk soon,
{{sender_name}}
CRB Insights

---
[Unsubscribe] | [View in browser]
```

---

#### Email 2: How to Read Your Report (+1 day)

```
Subject: 3 things to focus on in your report

Hi {{first_name}},

Quick note on getting the most from your AI Readiness Report.

Most people skim it once and forget it. Here's how to actually use it:

1. **Look at your "Quick Wins" section first**
   These are low-effort, high-impact opportunities.
   Pick one and do it this week.

2. **Compare to industry benchmarks**
   If you're below average somewhere, that's not bad news—
   it's where the biggest gains are hiding.

3. **Ignore the stuff you can't do yet**
   Some recommendations need budget or team you don't have.
   Skip those. Focus on what's actionable now.

[REVIEW YOUR REPORT AGAIN] → {{report_link}}

Reply to this email if you have questions. I read everything.

{{sender_name}}
```

---

#### Email 3: Your Quick Win (+3 days)

```
Subject: The one thing I'd do first at {{company_name}}

Hi {{first_name}},

If I were sitting in your chair at {{company_name}}, here's the
first thing I'd tackle based on your report:

{{personalized_quick_win}}

Why this one?
- It's doable in under a week
- It doesn't require new tools or big budget
- Other {{industry}} businesses report
  {{quick_win_impact}} from this change

[SEE THE FULL BREAKDOWN] → {{report_link}}

Next week I'll share what other {{industry}} businesses are
doing—patterns from the assessments we're running.

{{sender_name}}
```

**Note:** `{{personalized_quick_win}}` requires backend logic to pull from their report. Could be static by industry if personalization is too complex initially.

---

#### Email 4: Industry Comparison (+7 days)

```
Subject: How {{company_name}} compares to {{industry_count}} other {{industry}} businesses

Hi {{first_name}},

We've now analyzed {{industry_count}} {{industry}} businesses.

Here's how {{company_name}} stacks up:

┌─────────────────────────────────────┐
│ Your Score: {{quiz_score}}/100      │
│ Industry Avg: {{industry_avg}}/100  │
│ Top 10%: {{top_10_score}}+          │
└─────────────────────────────────────┘

**Where you're ahead:**
{{ahead_areas}}

**Where there's room:**
{{opportunity_areas}}

This isn't about being "behind." It's about knowing
where the leverage is.

[REVIEW YOUR FULL REPORT] → {{report_link}}

From now on, you'll get weekly insights from our
growing dataset. Real patterns, real numbers,
anonymized but actionable.

{{sender_name}}
```

---

### Sequence 2: Weekly Industry Insights

**Trigger:** Every Tuesday at 10am (or your preferred day)
**Audience:** All contacts in `quiz_completers` (minus unsubscribed)

This is your **ongoing value delivery**. This is why they stay subscribed.

---

#### Weekly Insight Email Template

```
Subject: [{{industry}} Insights] {{headline_of_the_week}}

Hi {{first_name}},

This week's insight from {{total_assessments}} {{industry}} businesses:

---

📊 **THE PATTERN**

{{main_insight}}

Example: "68% of dental practices still manually confirm
appointments. The 32% using automation save an average
of 8 hours/week."

---

🎯 **WHAT TOP PERFORMERS DO**

{{top_performer_behavior}}

Example: "Practices in the top 20% have automated at least
3 of these 5 workflows: appointment reminders, review requests,
recall campaigns, insurance verification, patient intake."

---

⚡ **ONE THING TO TRY THIS WEEK**

{{actionable_tip}}

Example: "If you're still doing appointment confirmations
manually, start here. It's the highest-ROI automation for
{{industry}} businesses."

---

See how you compare: [YOUR REPORT] → {{report_link}}

Reply with questions. I read every response.

{{sender_name}}
CRB Insights

---
You're receiving this because you took the AI Readiness Quiz.
[Unsubscribe] | [Update preferences]
```

---

#### Weekly Content Calendar

To send weekly insights, you need weekly content. Options:

**Option A: Manual curation (early stage)**
- Write each week's email manually
- Pull real patterns from your assessment data
- 30-60 min/week effort

**Option B: Semi-automated**
- Backend generates aggregate stats weekly
- You write narrative around the numbers
- 15-30 min/week

**Option C: Fully automated (later)**
- LLM generates insights from data
- You review and approve
- 10 min/week

**Content themes to rotate:**

| Week | Theme |
|------|-------|
| 1 | Process automation patterns |
| 2 | Tool adoption trends |
| 3 | Time savings benchmarks |
| 4 | Quick win spotlight |
| 5 | Industry comparison update |
| 6 | Case study / success story |
| 7 | Common mistakes to avoid |
| 8 | Emerging AI tools for {{industry}} |

---

### Sequence 3: Paid Report Upsell

**Trigger:** 14 days after quiz completion
**Condition:** Has NOT purchased paid report

```
+14 days:    Email 1 - Unlock the full picture
+21 days:    Email 2 - What you're missing
+30 days:    Email 3 - Last reminder
```

---

#### Upsell Email 1: Unlock Full Picture (+14 days)

```
Subject: Ready to go deeper?

Hi {{first_name}},

You've had your AI Readiness Teaser Report for a couple weeks now.

If you've found it useful, there's more:

**The Full Report includes:**

✅ Complete 40+ page analysis
✅ Prioritized implementation roadmap
✅ Vendor recommendations (matched to your needs)
✅ ROI projections for top 3 opportunities
✅ 90-day action plan

**Teaser Report:** What's possible
**Full Report:** Exactly how to do it

[GET THE FULL REPORT] → {{upgrade_link}}

Price: ${{price}} (one-time)

Questions? Reply to this email.

{{sender_name}}
```

---

#### Upsell Email 2: What You're Missing (+21 days)

```
Subject: The gap between knowing and doing

Hi {{first_name}},

Most businesses know they should use AI to save time.

Few actually do it.

The gap isn't awareness—it's a plan.

Your Teaser Report showed you the opportunities.
The Full Report gives you:

📋 Step-by-step implementation roadmap
🛠 Specific tools and vendors for your situation
📊 ROI math to justify the investment
📅 90-day timeline to get it done

[UNLOCK THE FULL REPORT] → {{upgrade_link}}

No pressure. The teaser is yours forever either way.

{{sender_name}}
```

---

#### Upsell Email 3: Soft Close (+30 days)

```
Subject: Quick check-in

Hi {{first_name}},

Just checking—have you had a chance to implement
anything from your AI Readiness Report?

If you're stuck on where to start, the Full Report
has the step-by-step roadmap.

If you're already making progress, I'd love to hear
what's working. Just reply.

[GET THE FULL REPORT] → {{upgrade_link}}

Either way, you'll keep getting weekly insights.

{{sender_name}}
```

---

## Brevo Automation Setup

### Workflow 1: Welcome Sequence

```
Trigger: Contact added to list "quiz_completers"

→ Send Email 1 (Report Delivered) [immediately]
→ Wait 1 day
→ Send Email 2 (How to Read)
→ Wait 2 days
→ Send Email 3 (Quick Win)
→ Wait 4 days
→ Send Email 4 (Industry Comparison)
→ End
```

### Workflow 2: Upsell Sequence

```
Trigger: Contact added to list "quiz_completers"

→ Wait 14 days
→ Condition: NOT in list "paid_customers"
  → Yes: Send Upsell Email 1
  → No: End
→ Wait 7 days
→ Condition: NOT in list "paid_customers"
  → Yes: Send Upsell Email 2
  → No: End
→ Wait 9 days
→ Condition: NOT in list "paid_customers"
  → Yes: Send Upsell Email 3
  → No: End
→ End
```

### Workflow 3: Weekly Insights (Manual Campaign)

For weekly insights, use Brevo's **Campaign** feature (not automation):

```
Every Tuesday:
1. Create new campaign
2. Select audience: quiz_completers (exclude unsubscribed)
3. Use weekly template
4. Personalize by industry (use dynamic content or segment)
5. Schedule for 10am
6. Send
```

Later, you can automate content generation, but start manual.

---

## Segmentation Strategy

### By Industry

Send industry-specific insights:

```
Segment: industry = "dental"
→ Dental-specific benchmarks and tips

Segment: industry = "home_services"
→ Home services-specific content
```

**Dynamic content blocks:**
```html
{% if contact.INDUSTRY == "dental" %}
  This week, 45 dental practices shared their data...
{% elsif contact.INDUSTRY == "home_services" %}
  This week, 32 home service companies shared their data...
{% endif %}
```

### By Engagement

```
Engaged (opened email in last 30 days):
→ Full weekly insights

Disengaged (no opens in 60+ days):
→ Re-engagement campaign, then remove if no response
```

### By Score

```
High readiness (score > 70):
→ Focus on optimization, advanced tips

Low readiness (score < 40):
→ Focus on basics, quick wins, motivation
```

---

## Metrics to Track

### Email Performance

| Metric | Target | Check |
|--------|--------|-------|
| Open rate | >25% | Weekly |
| Click rate | >3% | Weekly |
| Unsubscribe rate | <0.5% | Weekly |
| Bounce rate | <2% | Weekly |

### Funnel Performance

| Metric | Target | Check |
|--------|--------|-------|
| Quiz → Email capture | >80% | Weekly |
| Email → Report view | >50% | Weekly |
| Free → Paid conversion | >5% | Monthly |
| List growth rate | +50/week | Weekly |

### Engagement Trends

| Metric | Watch For |
|--------|-----------|
| Open rate declining | Content fatigue, send too often |
| Unsubscribes spiking | Too salesy, irrelevant content |
| Clicks dropping | CTAs unclear, content not actionable |

---

## Content Calendar Template

| Week | Insight Topic | Industry Focus | Upsell Mention |
|------|---------------|----------------|----------------|
| W1 | Process automation wins | All | Soft (in PS) |
| W2 | Time savings benchmarks | Dental | None |
| W3 | Tool adoption patterns | Home Services | None |
| W4 | Quick win spotlight | All | Medium |
| W5 | Industry comparison update | Professional | Soft |
| W6 | Case study | Recruiting | None |
| W7 | Common mistakes | All | None |
| W8 | Full report deep-dive | All | Hard |

**Cadence:**
- Weeks 1-4: Value-heavy, minimal selling
- Weeks 5-8: Balanced value + occasional upsell
- Repeat with new content

---

## Backend Integration Points

### Quiz Completion Hook

```python
# When quiz is completed, add to Brevo

async def on_quiz_completed(quiz_result: QuizResult):
    # Save to database
    await save_quiz_result(quiz_result)

    # Generate teaser report
    report = await generate_teaser_report(quiz_result)

    # Add to Brevo
    brevo = BrevoService(settings.BREVO_API_KEY)
    brevo.add_quiz_completer(
        email=quiz_result.email,
        first_name=quiz_result.first_name,
        company_name=quiz_result.company_name,
        industry=quiz_result.industry,
        quiz_score=quiz_result.score,
        report_id=report.id
    )

    # Trigger welcome email (or let Brevo automation handle it)
```

### Purchase Hook

```python
# When full report is purchased, update Brevo

async def on_report_purchased(purchase: Purchase):
    brevo = BrevoService(settings.BREVO_API_KEY)

    # Move to paid_customers list
    brevo.update_contact(
        email=purchase.email,
        list_ids_to_add=[PAID_CUSTOMERS_LIST_ID],
        attributes={"PAID_DATE": datetime.now().isoformat()}
    )

    # This stops upsell sequence automatically (via workflow conditions)
```

---

## Checklist

### Setup
- [ ] Create Brevo account
- [ ] Verify domain (SPF, DKIM, DMARC)
- [ ] Create lists (quiz_completers, industries, paid_customers)
- [ ] Create custom attributes
- [ ] Design email templates (brand colors, logo)

### Automations
- [ ] Build Welcome sequence (4 emails)
- [ ] Build Upsell sequence (3 emails)
- [ ] Test with your own email
- [ ] Verify personalization works

### Integration
- [ ] Add Brevo API key to backend settings
- [ ] Create BrevoService class
- [ ] Hook quiz completion → Brevo
- [ ] Hook purchase → Brevo
- [ ] Test full flow

### Content
- [ ] Write first 4 weekly insight emails
- [ ] Create content calendar for 8 weeks
- [ ] Set up process to generate insights from data

### Monitoring
- [ ] Set up weekly metrics review
- [ ] Create dashboard (Brevo built-in or custom)
- [ ] Define alert thresholds (unsubs, bounces)

---

## File Structure

```
backend/
├── src/
│   ├── services/
│   │   └── brevo_service.py    # Brevo API integration
│   ├── config/
│   │   └── settings.py         # Add BREVO_API_KEY
│   └── routes/
│       └── quiz.py             # Call brevo on completion

docs/
├── COLD_OUTREACH_PLAN.md       # Getting them to quiz
└── EMAIL_NURTURE_PLAN.md       # After quiz (this file)
```

---

## Summary

```
Cold Lead (Reply.io)
     ↓ Takes quiz
Quiz Completer (Brevo)
     ↓ Day 0: Report delivered
     ↓ Day 1: How to read it
     ↓ Day 3: Quick win
     ↓ Day 7: Industry comparison
     ↓ Day 14+: Upsell sequence (if not paid)
     ↓ Weekly: Industry insights forever
Paid Customer
     ↓ Upsell stops
     ↓ Weekly insights continue
     ↓ (Future: premium content, referral program)
```

**The loop:**
- Cold outreach → Quiz → Brevo
- Brevo nurtures → Some convert to paid
- Weekly insights keep everyone engaged
- Engaged list = asset for future launches

---

*Start with manual weekly emails. Automate once you have 500+ contacts and proven content.*
