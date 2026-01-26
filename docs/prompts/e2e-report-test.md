# E2E Report Generation Test

> **Purpose:** Generate a full report via CLI and validate quality
> **Target:** 100% valuable and accurate output
> **Industry:** Dental (strongest knowledge base)

---

## Test Business: Smile Dental Auckland

**Real-world basis:** Typical NZ dental practice pattern

| Field | Value |
|-------|-------|
| Name | Smile Dental Auckland |
| Website | smiledentalauckland.co.nz |
| Location | Ponsonby, Auckland, New Zealand |
| Team | 3 dentists, 2 hygienists, 4 front desk/admin |
| Annual Revenue | ~$1.2M NZD |
| Years Operating | 8 years |
| Current Software | EXACT (accounting), Google Workspace, Dental4Windows (old PM) |

---

## Step 1: Generate Test Report

Create the test script:

```bash
cd /Users/larsmusic/CRB\ Analyser/crb-analyser/backend
cat > scripts/test_smile_dental.py << 'PYTHON_EOF'
#!/usr/bin/env python3
"""
E2E Report Generation Test - Smile Dental Auckland
Uses EXACT question IDs from questionnaire.py and dental.json
"""

import asyncio
import json
import uuid
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def run_test():
    from src.config.supabase_client import get_async_supabase
    from src.services.report_service import generate_report_streaming

    # =========================================================================
    # QUIZ ANSWERS - Exact question IDs from questionnaire.py
    # =========================================================================
    quiz_answers = {
        # Section 1: Company Overview
        "company_description": "Family dental practice in Ponsonby, Auckland. 3 dentists, 2 hygienists, 4 admin/front desk staff. We focus on preventive care, cosmetic dentistry, and orthodontics. Been operating for 8 years with a loyal patient base of about 3,000 active patients.",
        "employee_count": "2-10",  # Options: "1", "2-10", "11-50", "51-200", "200+"
        "annual_revenue": "1m_5m",  # Options: "under_100k", "100k_500k", "500k_1m", "1m_5m", "5m_plus", "prefer_not_say"
        "primary_goals": ["increase_revenue", "improve_efficiency", "improve_customer_experience"],

        # Section 2: Current Operations
        "main_processes": "Patient scheduling and appointment management takes up most time. Insurance verification before appointments is a huge bottleneck - Sarah spends 2-3 hours every morning on the phone. Patient recalls for 6-month checkups, billing and payment collection, inventory management for supplies.",
        "repetitive_tasks": "Sending appointment reminders manually, calling to confirm appointments, following up on missed appointments, verifying insurance eligibility, collecting outstanding payments, ordering supplies when we notice we're running low.",
        "biggest_bottlenecks": "No-shows are killing us - about 18% rate which costs maybe $8-10k per month. Insurance verification is painful and slow. After-hours calls go to voicemail and we lose potential new patients. Recall compliance is only about 40%.",
        "time_on_admin": 25,  # Number: hours per week
        "manual_data_entry": "yes",
        "manual_data_entry_details": "We have to enter patient info into both Dental4Windows and our accounting system EXACT. Insurance claim info gets entered multiple times. Referral tracking is all on spreadsheets.",

        # Section 3: Technology & Tools
        "current_tools": ["accounting", "spreadsheets", "communication", "other"],
        "tool_pain_points": "Dental4Windows is ancient and doesn't integrate with anything. We can't do online booking. The built-in reminder system is clunky so we end up calling patients manually. No good way to see practice analytics.",
        "integration_issues": 3,  # Scale 1-10 (1=not at all, 10=perfectly)
        "technology_comfort": 7,  # Scale 1-10 (1=resistant, 10=eager)
        "ai_tools_used": ["chatgpt"],

        # Section 4: Implementation Preferences
        "implementation_capability": "automation_user",  # Options: "non_technical", "tutorial_follower", "automation_user", "ai_coder", "has_developers"
        "implementation_preference": "buy",  # Options: "buy", "connect", "build", "hire"
        "budget_comfort": "comfortable",  # Options: "low", "moderate", "comfortable", "high"
        "implementation_urgency": "this_month",  # Options: "this_week", "this_month", "this_quarter", "no_rush"

        # Section 5: Pain Points & Challenges
        "biggest_challenge": "Reducing no-shows and improving patient communication efficiency. We're leaving money on the table with poor recall compliance and missed after-hours calls. Admin work is burning out the front desk team.",
        "time_wasters": "Phone tag with patients to confirm appointments. Manually checking insurance eligibility. Chasing overdue payments. Re-entering data between systems. Trying to track recalls in spreadsheets.",
        "missed_opportunities": "We could probably see 10-15% more patients if we had better scheduling efficiency. After-hours calls represent maybe 5-10 potential new patients per week we're losing. Better recall compliance could add significant hygiene revenue.",
        "cost_concerns": ["labor", "software", "overhead"],
        "quality_issues": "yes",
        "quality_issues_details": "Inconsistent reminder timing means patients forget appointments. Sometimes insurance verification is missed and patients are surprised by costs. Recall letters go out late or not at all sometimes.",

        # Section 6: AI & Automation Readiness
        "ai_interest_areas": ["customer_service", "operations", "analytics"],
        "budget_for_solutions": "500_1000",  # Options: "under_100", "100_500", "500_1000", "1000_5000", "5000_plus", "not_sure"
        "implementation_timeline": "1_3_months",  # Options: "asap", "1_3_months", "3_6_months", "6_12_months", "no_rush"
        "decision_makers": "me_input",  # Options: "me", "me_input", "team", "other"
        "additional_context": "I'm the practice owner and really want to modernize but worried about disruption. The team is pretty tech-comfortable - everyone uses smartphones and we have iPads in operatories. Main concern is finding tools that actually work with Dental4Windows or can replace it without a painful migration.",
    }

    # =========================================================================
    # INDUSTRY-SPECIFIC ANSWERS - Exact question IDs from dental.json
    # =========================================================================
    industry_answers = {
        "patient_volume_weekly": 120,  # Number
        "no_show_rate": "10_20",  # Options: "under_5", "5_10", "10_20", "20_30", "over_30"
        "scheduling_method": ["phone", "email"],  # Multi-select: "phone", "online_portal", "third_party", "walk_in", "email"
        "insurance_verification": "Sarah our office manager spends 2-3 hours every morning calling insurance companies to verify eligibility. Half the time she can't get through or is on hold forever. We use a fax for some and an online portal for others but it's all manual.",
        "practice_locations": "1",  # Options: "1", "2_3", "4_10", "more_than_10"
        "front_desk_staff": 4,  # Number
        "after_hours_calls": "25_50",  # Options: "under_10", "10_25", "25_50", "over_50", "not_tracked"
        "practice_management_system": "other",  # Options: "dentrix", "eaglesoft", "open_dental", "curve", "denticon", "other"
        "patient_communication_tools": ["manual", "builtin_pm"],  # Multi-select: "weave", "solutionreach", "lighthouse", "revenuewell", "builtin_pm", "manual", "none"
        "biggest_admin_challenge": "Insurance verification without a doubt. It takes 20-30 minutes per patient when you include the hold time. We try to do it the day before but sometimes patients book same-day and we scramble. The worst is when insurance denies something we thought was covered.",
        "recall_compliance": "40_60",  # Options: "over_80", "60_80", "40_60", "under_40", "not_tracked"
        "growth_priority": "efficiency",  # Options: "more_patients", "efficiency", "case_acceptance", "reduce_costs", "expand", "quality_of_life"
        "case_acceptance_rate": "60_80",  # Options: "over_80", "60_80", "40_60", "under_40", "not_tracked"
        "ai_readiness": "some",  # Options: "none", "exploring", "some", "advanced"
        "budget_timeline": "3_months",  # Options: "immediately", "3_months", "6_months", "next_year", "just_exploring"
    }

    # =========================================================================
    # INTERVIEW DATA - Simulates voice/chat interview responses
    # =========================================================================
    interview_data = {
        "messages": [
            {
                "role": "assistant",
                "content": "What's your approximate patient no-show rate?"
            },
            {
                "role": "user",
                "content": "It's around 18% which is honestly embarrassing to admit. On a typical day with 40 scheduled patients, we might have 7 or 8 no-shows. That's easily $1,500-2,000 in lost production per day."
            },
            {
                "role": "assistant",
                "content": "That's a common challenge. Walk me through what happens when a patient doesn't show - how does your team currently handle it?"
            },
            {
                "role": "user",
                "content": "When someone no-shows, the front desk tries to call them right away to reschedule. Problem is they're also trying to handle check-ins, answer phones, and deal with the next patients. So follow-up calls get pushed to end of day or next morning. By then the patient has often forgotten why they needed the appointment."
            },
            {
                "role": "assistant",
                "content": "What tools do you use for patient reminders and communication?"
            },
            {
                "role": "user",
                "content": "Just what's built into Dental4Windows - an automated text the day before. It goes out at like 7am which patients complain about. No confirmation required, just a one-way reminder. We tried calling everyone manually but it was too time consuming."
            },
            {
                "role": "assistant",
                "content": "Approximately how many patient calls go to voicemail after hours each week?"
            },
            {
                "role": "user",
                "content": "I'd guess 25-40 calls a week after we close at 5pm. We know because our voicemail fills up. Maybe half are existing patients with questions but the other half are potential new patients who found us online. Those are the ones that hurt because they probably just call the next dentist on the list."
            },
            {
                "role": "assistant",
                "content": "That's a lot of potential patients reaching out. What happens to those calls - do you try to follow up the next day?"
            },
            {
                "role": "user",
                "content": "We try but honestly a lot slip through the cracks. Sarah listens to voicemails first thing but she's also doing insurance verification. If it's a new patient inquiry from 6pm the night before, by the time we call back at 10am they've often already booked somewhere else."
            },
            {
                "role": "assistant",
                "content": "What's the most time-consuming administrative task for your staff?"
            },
            {
                "role": "user",
                "content": "Hands down insurance verification. It's a black hole of time. Every patient we need to call or check online portal - different process for every insurance company. Some you can do online in 2 minutes, others require 20 minutes on hold. We probably spend 15-20 hours a week total just on insurance."
            },
            {
                "role": "assistant",
                "content": "What percentage of patients return for their 6-month checkups as scheduled?"
            },
            {
                "role": "user",
                "content": "Maybe 40-45% come back when they're supposed to. Another 20% we have to chase and eventually get back in. The rest just disappear until they have a problem. We send recall postcards and make calls but it's hit or miss. That's probably $15-20k per month in hygiene production we're missing."
            },
            {
                "role": "assistant",
                "content": "If you found a solution that could save significant time or grow revenue, when would you want to implement it?"
            },
            {
                "role": "user",
                "content": "Yesterday! Seriously though, within 3 months would be ideal. We're heading into our busy season and I'd love to have something in place. Budget-wise, if it saves us even half of our no-show losses, I'd happily pay $500-1000 per month. The ROI is obvious."
            }
        ],
        "confidence_scores": {
            "pain_points": 92,
            "operations": 88,
            "tech_stack": 75,
            "quantifiable_metrics": 85,
            "buying_signals": 90,
            "industry_context": 80
        }
    }

    # =========================================================================
    # COMPANY PROFILE - Structured company data
    # =========================================================================
    company_profile = {
        "basics": {
            "name": {"value": "Smile Dental Auckland", "confidence": 1.0},
            "website": {"value": "smiledentalauckland.co.nz", "confidence": 0.9},
            "description": {"value": "Family dental practice in Ponsonby serving Auckland for 8 years. General dentistry, cosmetics, orthodontics.", "confidence": 0.95}
        },
        "industry": {
            "primary_industry": {"value": "dental", "confidence": 1.0},
            "sub_industry": {"value": "general_dentistry", "confidence": 0.9}
        },
        "size": {
            "employee_range": {"value": "2-10", "confidence": 1.0},
            "employee_count": {"value": 9, "confidence": 0.95}
        },
        "location": {
            "city": {"value": "Auckland", "confidence": 1.0},
            "country": {"value": "New Zealand", "confidence": 1.0},
            "region": {"value": "North Island", "confidence": 0.9}
        },
        "financials": {
            "revenue_range": {"value": "1m_5m", "confidence": 0.8},
            "currency": {"value": "NZD", "confidence": 1.0}
        }
    }

    # =========================================================================
    # EXISTING TECH STACK
    # =========================================================================
    existing_stack = [
        {
            "name": "Dental4Windows",
            "category": "practice_management",
            "satisfaction": 4,  # 1-10
            "notes": "Old, doesn't integrate well, no online booking"
        },
        {
            "name": "EXACT",
            "category": "accounting",
            "satisfaction": 7,
            "notes": "Works well for accounting, NZ-specific"
        },
        {
            "name": "Google Workspace",
            "category": "communication",
            "satisfaction": 8,
            "notes": "Email, calendar, basic docs"
        }
    ]

    # =========================================================================
    # CREATE SESSION AND GENERATE REPORT
    # =========================================================================
    supabase = await get_async_supabase()
    session_id = str(uuid.uuid4())

    # Merge quiz and industry answers
    all_answers = {**quiz_answers, **industry_answers, "industry": "dental"}

    session_data = {
        "id": session_id,
        "email": "test-smile-dental@crb-test.local",
        "tier": "quick",
        "status": "paid",
        "current_section": 5,
        "current_question": 25,
        "answers": all_answers,
        "company_name": "Smile Dental Auckland",
        "company_website": "smiledentalauckland.co.nz",
        "company_profile": company_profile,
        "interview_data": interview_data,
        "existing_stack": existing_stack,
    }

    await supabase.table("quiz_sessions").insert(session_data).execute()
    print(f"Session: {session_id}")
    print("Generating report (60-120 seconds)...")
    print()

    report_id = None
    async for event in generate_report_streaming(session_id, "quick"):
        if event.startswith("data: "):
            try:
                data = json.loads(event[6:].strip())
                if data.get("step"):
                    progress = data.get("progress", 0)
                    step = data.get("step")
                    print(f"  {progress:3d}% - {step}")
                    sys.stdout.flush()
                if data.get("report_id"):
                    report_id = data["report_id"]
                if data.get("phase") == "error":
                    print(f"ERROR: {data.get('error')}")
            except json.JSONDecodeError:
                pass

    if report_id:
        print()
        print(f"Report generated: {report_id}")
        print(f"View at: http://localhost:5174/report/{report_id}")

        result = await supabase.table("reports").select("*").eq("id", report_id).single().execute()
        if result.data:
            output_path = "/tmp/smile-dental-report.json"
            with open(output_path, "w") as f:
                json.dump(result.data, f, indent=2)
            print(f"Saved to: {output_path}")

            # Print summary
            report = result.data
            print()
            print("=" * 60)
            print("REPORT SUMMARY")
            print("=" * 60)

            if "executive_summary" in report:
                es = report["executive_summary"]
                print(f"AI Readiness Score: {es.get('ai_readiness_score', 'N/A')}")
                if es.get("key_insight"):
                    print(f"Key Insight: {es.get('key_insight')[:150]}...")

            if "findings" in report and report["findings"]:
                print(f"\nFindings: {len(report['findings'])}")
                for i, f in enumerate(report["findings"][:5], 1):
                    title = f.get("title", f.get("name", "Untitled"))
                    print(f"  {i}. {title}")

            if "recommendations" in report and report["recommendations"]:
                print(f"\nRecommendations: {len(report['recommendations'])}")
                for i, r in enumerate(report["recommendations"][:3], 1):
                    title = r.get("title", r.get("name", "Untitled"))
                    print(f"  {i}. {title}")

    else:
        print("ERROR: No report_id returned")

    return report_id


if __name__ == "__main__":
    report_id = asyncio.run(run_test())
PYTHON_EOF
```

Then run:

```bash
source venv/bin/activate
python scripts/test_smile_dental.py
```

---

## Step 2: Quality Checklist

After generation, evaluate against these criteria:

### Executive Summary
- [ ] AI readiness score present and justified (not arbitrary)
- [ ] Score reflects their mixed tech situation (old PM, willing team)
- [ ] Top opportunities match their stated pain points
- [ ] Key insight mentions specific issues (18% no-shows, $8-10k/month loss)
- [ ] Clear verdict: Proceed / Caution / Wait

### Findings Must Address These Specific Pain Points
From interview data, the report MUST address:

| Pain Point | Specific Data | Expected Finding |
|------------|---------------|------------------|
| No-shows | 18% rate, $1,500-2,000/day loss | Patient communication automation |
| Insurance verification | 2-3 hours/day, 15-20 hrs/week | Insurance verification tools |
| After-hours calls | 25-40 calls/week, new patients lost | AI receptionist / after-hours answering |
| Recall compliance | 40-45%, missing $15-20k/month hygiene | Recall automation system |
| Dental4Windows | Old, no integrations | PM system recommendation or integration workaround |

### Vendor Recommendations
- [ ] Vendors are dental-specific (not generic CRM)
- [ ] NZ/AU available (not US-only vendors)
- [ ] Pricing is current (verified within last 90 days)
- [ ] Each recommendation has 3-4 options:
  - Off-the-shelf (easy, quick)
  - Best-in-class (optimal)
  - Custom/build option (if applicable)
  - "Do nothing" with honest cost

Expected vendors for dental practice:
- Patient communication: Weave, RevenueWell, Lighthouse 360
- Insurance verification: Vyne Dental, Dental Intelligence
- Practice management: Open Dental, Curve Dental (as D4W replacement)
- AI receptionist: Ruby, Smith.ai, or dental-specific option

### ROI Calculations
- [ ] Based on their stated numbers, not generic
- [ ] No-show reduction: Based on $8-10k/month current loss
- [ ] Recall improvement: Based on $15-20k/month potential
- [ ] After-hours capture: Based on 25-40 calls × conversion rate
- [ ] Assumptions stated explicitly

### Implementation Roadmap
- [ ] Phased approach (they said "phased" preference)
- [ ] Considers D4W integration constraints
- [ ] Quick wins first (team is willing but worried about disruption)
- [ ] Realistic timelines for 9-person team

### Anti-Slop Verification
- [ ] No vague platitudes ("leverage AI to transform...")
- [ ] No made-up statistics (all numbers from their interview)
- [ ] No generic advice (specific to THIS dental practice)
- [ ] Addresses D4W constraint honestly (integrate or replace)
- [ ] Honest "don't do this" where appropriate
- [ ] NZ market context (not US-centric advice)

---

## Step 3: Quality Analysis Prompt

After reviewing the generated report, use this prompt for analysis:

```markdown
I generated a CRB report for "Smile Dental Auckland" with this specific context:

**Business Profile:**
- 3 dentists, 2 hygienists, 4 admin staff (9 total)
- Auckland, New Zealand
- ~$1.2M NZD annual revenue
- 8 years operating, 3,000 active patients
- Using Dental4Windows (old, poor integrations) + EXACT accounting

**Stated Pain Points (from interview):**
1. 18% no-show rate = $8-10k/month lost revenue
2. Insurance verification = 15-20 hours/week (2-3 hrs/day)
3. After-hours calls = 25-40/week going to voicemail, losing new patients
4. Recall compliance = 40-45%, missing $15-20k/month hygiene revenue
5. Dental4Windows doesn't integrate with anything modern

**Their Preferences:**
- Budget: $500-1000/month for right solution
- Timeline: Within 3 months
- Approach: Prefer buying ready-made solutions
- Tech comfort: Team is 7/10, willing to adopt
- Concern: Worried about disruption during busy season

Review the attached report and answer:

1. **ACCURACY**: Are vendor recommendations correct for NZ dental market? Is pricing current?

2. **RELEVANCE**: Does every finding directly address one of their 5 stated pain points?

3. **SPECIFICITY**: Do recommendations reference their actual numbers ($8-10k no-show cost, 40% recall rate, etc.)?

4. **VALUE**: Would this practice owner know exactly what to do Monday morning after reading?

5. **HONESTY**: Any exaggerated claims? Missing caveats about D4W integration challenges?

6. **GAPS**: What did the report miss that should have been included?

7. **NZ CONTEXT**: Does advice make sense for New Zealand market (not US-centric)?

8. **SCORE**: Rate 1-10 for each dimension. What's needed to reach 10/10?
```

---

## Step 4: Common Issues and Fixes

| Issue | Likely Cause | Fix Location |
|-------|--------------|--------------|
| Wrong/generic vendors | Vendor knowledge outdated | `backend/src/knowledge/dental/vendors.json` |
| Missing pain point | Opportunity not in KB | `backend/src/knowledge/dental/opportunities.json` |
| US-only vendors | NZ market not considered | Add NZ availability to vendor data |
| Generic ROI numbers | Not using interview data | `backend/src/skills/report-generation/` prompts |
| D4W constraint ignored | Integration analysis missing | `backend/src/skills/analysis/vendor_matching.py` |
| Wrong benchmarks | Outdated industry data | `backend/src/knowledge/dental/benchmarks.json` |

---

## Success Criteria

Report is launch-ready when:

1. Every recommendation ties to a stated pain point with their actual numbers
2. All vendors are available in NZ with verified current pricing
3. ROI calculations use their data ($8-10k no-show, $15-20k recall, etc.)
4. D4W constraint is addressed honestly (integrate workarounds OR replace path)
5. Implementation plan matches their preferences (phased, buy not build)
6. A dental practice owner would pay €147 for this insight
7. Zero generic AI slop - everything specific to Smile Dental Auckland

---
---

# E2E Report Generation Test - Plumbing Business

> **Purpose:** Test report quality for trades/physical service business
> **Target:** Recommendations focused on back-office efficiency, NOT "transformation"
> **Industry:** Home Services / Plumbing (local physical business)

---

## Test Business: Mount Eden Plumbing & Gas

**Real business:** [mountedenplumbing.co.nz](https://www.mountedenplumbing.co.nz/)

| Field | Value |
|-------|-------|
| Name | Mount Eden Plumbing & Gas |
| Website | mountedenplumbing.co.nz |
| Location | Auckland, New Zealand (services Auckland-wide) |
| Owner | Eamon Tolhurst |
| Team | Small team (estimated 2-4 tradies + admin support) |
| Experience | 12+ years plumbing, 5 years high-spec residential |
| Services | Emergency plumbing, hot water cylinders, gas fitting, residential & commercial |
| Service Area | Auckland-wide: Omaha to Waiuku, Beachlands to Kumeu |

---

## Step 1: Generate Test Report

Create the test script:

```bash
cd /Users/larsmusic/CRB\ Analyser/crb-analyser/backend
cat > scripts/test_mount_eden_plumbing.py << 'PYTHON_EOF'
#!/usr/bin/env python3
"""
E2E Report Generation Test - Mount Eden Plumbing & Gas
Tests report quality for a local trades business (physical service, local market)
"""

import asyncio
import json
import uuid
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def run_test():
    from src.config.supabase_client import get_async_supabase
    from src.services.report_service import generate_report_streaming

    # =========================================================================
    # QUIZ ANSWERS - Typical small plumbing business
    # =========================================================================
    quiz_answers = {
        # Section 1: Company Overview
        "company_description": "Family-owned plumbing and gas fitting business based in Mount Eden, Auckland. We handle everything from emergency repairs to new builds. Fully certified plumbers and gasfitters. Been in the trade 12 years, running this business for 5. We cover all of Auckland - North Shore to South Auckland.",
        "employee_count": "2-10",  # Eamon + 2-3 plumbers + part-time admin
        "annual_revenue": "500k_1m",  # Typical for small plumbing operation
        "primary_goals": ["increase_revenue", "improve_efficiency", "reduce_costs"],

        # Section 2: Current Operations
        "main_processes": "Job scheduling and dispatch is the big one - coordinating where everyone needs to be each day. Quoting takes time because I often need to visit the site first. Invoicing happens at night after jobs. Parts ordering when we notice stock is low. Customer calls come in all day, hard to answer when you're under a sink.",
        "repetitive_tasks": "Writing up quotes after site visits. Sending invoices manually. Following up on unpaid invoices. Scheduling confirmation texts to customers. Ordering the same common parts over and over. Logging job details for compliance.",
        "biggest_bottlenecks": "Can't answer phone when on a job - probably lose 5-10 potential customers per week to voicemail. Quoting takes too long - sometimes 2-3 days to get back to people. End up doing admin at night which burns me out. Hard to know if jobs are profitable until months later.",
        "time_on_admin": 15,  # Hours per week, mostly evenings
        "manual_data_entry": "yes",
        "manual_data_entry_details": "Job details go into a spreadsheet, then into Xero for invoicing, then into a compliance log. Triple entry basically. Customer info lives in my phone contacts, email, and the spreadsheet - never synced.",

        # Section 3: Technology & Tools
        "current_tools": ["accounting", "spreadsheets", "communication"],
        "tool_pain_points": "Everything is disconnected. Xero is fine for accounting but doesn't help with job management. Google Calendar for scheduling but it's manual. No way for customers to book online. Can't see job profitability easily.",
        "integration_issues": 3,  # Scale 1-10 (nothing integrates)
        "technology_comfort": 6,  # Comfortable with basics, not a tech person
        "ai_tools_used": ["chatgpt"],  # Might use for drafting emails/quotes

        # Section 4: Implementation Preferences
        "implementation_capability": "tutorial_follower",  # Can follow setup guides, not technical
        "implementation_preference": "buy",  # Just want something that works
        "budget_comfort": "moderate",  # €50-200/month is reasonable
        "implementation_urgency": "this_month",  # Pain is real, want solution soon

        # Section 5: Pain Points & Challenges
        "biggest_challenge": "Missing calls while on jobs. By the time I call back, they've found another plumber. Also spending 2+ hours every night on paperwork instead of with family.",
        "time_wasters": "Driving to quote jobs that go nowhere. Chasing unpaid invoices. Manually texting appointment confirmations. Rewriting the same job descriptions. Looking for customer history in different places.",
        "missed_opportunities": "Definitely losing jobs from missed calls - emergency plumbing, people call the first 3 plumbers they find. Could do more jobs if quoting was faster. Repeat customers forget to call us for maintenance.",
        "cost_concerns": ["labor", "software", "outsourcing"],
        "quality_issues": "yes",
        "quality_issues_details": "Sometimes forget to follow up on quotes. Occasionally double-book because calendar isn't synced between team. Parts ordering is reactive - sometimes have to make extra supplier runs.",

        # Section 6: AI & Automation Readiness
        "ai_interest_areas": ["customer_service", "operations", "finance"],
        "budget_for_solutions": "100_500",  # €100-500/month
        "implementation_timeline": "1_3_months",
        "decision_makers": "me",  # Owner decides
        "additional_context": "I'm not a tech person but I know we're leaving money on the table with manual processes. Main thing is it needs to be simple - I don't have time to learn complicated systems. If it saves me the evening admin work and helps catch more calls, I'd pay for it.",
    }

    # =========================================================================
    # INDUSTRY-SPECIFIC ANSWERS - Home Services / Plumbing
    # =========================================================================
    industry_answers = {
        "service_calls_weekly": 25,  # Approximate jobs per week
        "average_job_value": 450,  # NZD average job
        "emergency_vs_scheduled": "40_60",  # 40% emergency, 60% scheduled
        "quote_conversion_rate": "50_70",  # Rough estimate
        "team_size_field": 3,  # Tradies in the field
        "service_area_radius": "50km",  # Auckland-wide
        "scheduling_method": ["phone", "email"],
        "payment_collection": "Invoice after job, net 7-14 days",
        "vehicle_count": 3,
        "biggest_operational_challenge": "Missed calls and slow quoting. Also cashflow - waiting 2-3 weeks for payment while paying suppliers upfront.",
    }

    # =========================================================================
    # INTERVIEW DATA - Simulates conversation with plumber owner
    # =========================================================================
    interview_data = {
        "messages": [
            {
                "role": "assistant",
                "content": "How many customer calls would you estimate you miss while working on jobs?"
            },
            {
                "role": "user",
                "content": "Honestly, probably 8-10 a day go to voicemail. Maybe half call back, half don't. For emergency plumbing, if you don't answer, they just call the next guy. I reckon that's 5 lost jobs a week at $400-500 each. That's $2000 a week walking away."
            },
            {
                "role": "assistant",
                "content": "That's significant. What happens with those voicemails - do you try to follow up?"
            },
            {
                "role": "user",
                "content": "I try to call back end of day but by then emergency jobs are gone. The scheduled work sometimes comes back but people are annoyed they had to wait. My wife helps when she can but she's got her own job."
            },
            {
                "role": "assistant",
                "content": "Walk me through how you currently handle a new job request."
            },
            {
                "role": "user",
                "content": "Phone rings, I answer if I can or it goes to voicemail. If I answer I write details on whatever paper I have. Later I put it in Google Calendar. For bigger jobs I need to visit to quote - might be a few days before I get there. Then I write up the quote in Word, email it. Wait for approval. Schedule the job. Do the job. Write up invoice in Xero. Send it. Chase payment if needed. Whole thing is manual."
            },
            {
                "role": "assistant",
                "content": "How much time do you spend on admin work outside of actual plumbing?"
            },
            {
                "role": "user",
                "content": "Two hours minimum every night after the kids go to bed. Invoicing, quoting, scheduling for tomorrow, ordering parts, answering emails. Weekends too - probably 4-5 hours on Sunday doing the week's books. My wife's not happy about it and honestly neither am I."
            },
            {
                "role": "assistant",
                "content": "What tools are you currently using to run the business?"
            },
            {
                "role": "user",
                "content": "Xero for invoicing and accounts - that works fine. Google Calendar for scheduling but only I can see it, the other guys just get texts. Spreadsheet for job tracking. Word for quotes. Phone contacts for customers. Nothing talks to anything else. I looked at Tradify and Fergus but seemed complicated and expensive."
            },
            {
                "role": "assistant",
                "content": "What would make the biggest difference to your day-to-day?"
            },
            {
                "role": "user",
                "content": "If someone could answer my phone and book jobs while I'm working, that'd be massive. Or at least capture the leads so I don't lose them. After that, faster quoting - if I could quote on the spot from my phone that'd save hours. And getting paid faster would help cashflow heaps."
            },
            {
                "role": "assistant",
                "content": "What's your budget comfort for tools that would save you this time?"
            },
            {
                "role": "user",
                "content": "If something genuinely saved me 10 hours a week and helped catch those lost jobs, I'd pay $200-300 a month easy. The lost revenue from missed calls alone is way more than that. But it needs to actually work and be simple - I've wasted money on software I never used before."
            }
        ],
        "confidence_scores": {
            "pain_points": 90,
            "operations": 85,
            "tech_stack": 80,
            "quantifiable_metrics": 75,
            "buying_signals": 88,
            "industry_context": 82
        }
    }

    # =========================================================================
    # COMPANY PROFILE
    # =========================================================================
    company_profile = {
        "basics": {
            "name": {"value": "Mount Eden Plumbing & Gas", "confidence": 1.0},
            "website": {"value": "mountedenplumbing.co.nz", "confidence": 1.0},
            "description": {"value": "Family-owned plumbing and gas fitting business serving Auckland. Emergency repairs, hot water, gas fitting, residential and commercial.", "confidence": 0.95}
        },
        "industry": {
            "primary_industry": {"value": "home_services", "confidence": 1.0},
            "sub_industry": {"value": "plumbing", "confidence": 1.0}
        },
        "size": {
            "employee_range": {"value": "2-10", "confidence": 0.9},
            "employee_count": {"value": 4, "confidence": 0.8}
        },
        "location": {
            "city": {"value": "Auckland", "confidence": 1.0},
            "country": {"value": "New Zealand", "confidence": 1.0},
            "region": {"value": "North Island", "confidence": 1.0}
        },
        "financials": {
            "revenue_range": {"value": "500k_1m", "confidence": 0.7},
            "currency": {"value": "NZD", "confidence": 1.0}
        }
    }

    # =========================================================================
    # EXISTING TECH STACK
    # =========================================================================
    existing_stack = [
        {
            "name": "Xero",
            "category": "accounting",
            "satisfaction": 7,
            "notes": "Works well for invoicing and accounts, NZ standard"
        },
        {
            "name": "Google Calendar",
            "category": "scheduling",
            "satisfaction": 4,
            "notes": "Basic, not shared properly with team"
        },
        {
            "name": "Google Sheets",
            "category": "job_tracking",
            "satisfaction": 3,
            "notes": "Manual job log, not connected to anything"
        },
        {
            "name": "Microsoft Word",
            "category": "quoting",
            "satisfaction": 3,
            "notes": "Manual quote creation, slow"
        }
    ]

    # =========================================================================
    # CREATE SESSION AND GENERATE REPORT
    # =========================================================================
    supabase = await get_async_supabase()
    session_id = str(uuid.uuid4())

    all_answers = {**quiz_answers, **industry_answers, "industry": "home_services"}

    session_data = {
        "id": session_id,
        "email": "test-mount-eden-plumbing@crb-test.local",
        "tier": "quick",
        "status": "paid",
        "current_section": 5,
        "current_question": 25,
        "answers": all_answers,
        "company_name": "Mount Eden Plumbing & Gas",
        "company_website": "mountedenplumbing.co.nz",
        "company_profile": company_profile,
        "interview_data": interview_data,
        "existing_stack": existing_stack,
    }

    await supabase.table("quiz_sessions").insert(session_data).execute()
    print(f"Session: {session_id}")
    print("Generating report (60-120 seconds)...")
    print()

    report_id = None
    async for event in generate_report_streaming(session_id, "quick"):
        if event.startswith("data: "):
            try:
                data = json.loads(event[6:].strip())
                if data.get("step"):
                    progress = data.get("progress", 0)
                    step = data.get("step")
                    print(f"  {progress:3d}% - {step}")
                    sys.stdout.flush()
                if data.get("report_id"):
                    report_id = data["report_id"]
                if data.get("phase") == "error":
                    print(f"ERROR: {data.get('error')}")
            except json.JSONDecodeError:
                pass

    if report_id:
        print()
        print(f"Report generated: {report_id}")
        print(f"View at: http://localhost:5174/report/{report_id}")

        result = await supabase.table("reports").select("*").eq("id", report_id).single().execute()
        if result.data:
            output_path = "/tmp/mount-eden-plumbing-report.json"
            with open(output_path, "w") as f:
                json.dump(result.data, f, indent=2)
            print(f"Saved to: {output_path}")

            report = result.data
            print()
            print("=" * 60)
            print("REPORT SUMMARY")
            print("=" * 60)

            if "executive_summary" in report:
                es = report["executive_summary"]
                print(f"AI Readiness Score: {es.get('ai_readiness_score', 'N/A')}")
                if es.get("key_insight"):
                    print(f"Key Insight: {es.get('key_insight')[:150]}...")

            if "findings" in report and report["findings"]:
                print(f"\nFindings: {len(report['findings'])}")
                for i, f in enumerate(report["findings"][:5], 1):
                    title = f.get("title", f.get("name", "Untitled"))
                    print(f"  {i}. {title}")

            if "recommendations" in report and report["recommendations"]:
                print(f"\nRecommendations: {len(report['recommendations'])}")
                for i, r in enumerate(report["recommendations"][:3], 1):
                    title = r.get("title", r.get("name", "Untitled"))
                    print(f"  {i}. {title}")

    else:
        print("ERROR: No report_id returned")

    return report_id


if __name__ == "__main__":
    report_id = asyncio.run(run_test())
PYTHON_EOF
```

Then run:

```bash
source venv/bin/activate
python scripts/test_mount_eden_plumbing.py
```

---

## Step 2: Quality Checklist

### Key Principle: Efficiency, Not Transformation

This is a **local physical service business**. AI won't disrupt their market - you can't outsource a plumber to India. Recommendations should focus on:
- Back-office efficiency (scheduling, invoicing, customer comms)
- Capturing leads they're currently losing
- Reducing evening admin work
- NOT "AI transformation" or "revolutionary" solutions

### Executive Summary
- [ ] AI readiness score reflects practical tech comfort (not high, not transformation-ready)
- [ ] Recognizes this is a local trades business (different from digital businesses)
- [ ] Top opportunities match operational efficiency, not business model change
- [ ] Key insight mentions specific issues ($2k/week lost calls, 15+ hrs/week admin)

### Findings Must Address These Specific Pain Points

| Pain Point | Specific Data | Expected Finding |
|------------|---------------|------------------|
| Missed calls | 8-10/day to voicemail, ~$2k/week lost | Call answering / AI receptionist solution |
| Evening admin | 2+ hours every night, 4-5 hrs Sunday | Job management software to reduce manual work |
| Slow quoting | Days to quote, manual Word docs | Mobile quoting / field service app |
| Payment delays | Net 7-14 days, cashflow issues | Faster payment collection, on-site payment |
| Disconnected tools | Xero, Calendar, Sheets don't sync | Integrated job management that connects to Xero |

### Vendor Recommendations - Must Be Trades-Appropriate
- [ ] Vendors are trades/field-service specific (not generic CRM)
- [ ] Available in NZ market
- [ ] Appropriate for small team (not enterprise solutions)
- [ ] Integrates with Xero (their accounting system)

Expected vendors for NZ plumbing business:
- Job management: **Tradify**, **Fergus**, **ServiceM8**, **Jobber**
- Call answering: **OfficeHQ**, **Ruby** (if NZ available), or NZ-specific virtual receptionist
- Payment: **Stripe**, **Xero payments**, or trade-specific invoicing
- NOT: Salesforce, HubSpot, enterprise solutions

### ROI Calculations
- [ ] Based on their stated numbers, not generic
- [ ] Missed call recovery: Based on $2k/week = $8k/month potential
- [ ] Admin time savings: Based on 15+ hrs/week × hourly value
- [ ] Faster quoting: Based on current quote conversion rate
- [ ] Assumptions stated explicitly with sources

### Anti-Transformation Verification
This is critical - report should NOT recommend:
- [ ] No "digital transformation" language
- [ ] No "AI-powered business revolution"
- [ ] No complex multi-system implementations
- [ ] No solutions requiring technical skills beyond "tutorial follower"
- [ ] No enterprise-grade tools for a 4-person operation
- [ ] Honest about what AI CAN'T do for a plumber (can't fix pipes remotely)

### NZ Context
- [ ] Vendors available in New Zealand
- [ ] Xero integration (NZ accounting standard)
- [ ] Pricing in NZD or clearly converted
- [ ] Understands Auckland service area context

---

## Step 3: Quality Analysis Prompt

After reviewing the generated report, use this prompt for analysis:

```markdown
I generated a CRB report for "Mount Eden Plumbing & Gas" with this specific context:

**Business Profile:**
- Owner-operator + 3 field staff (4 total)
- Auckland, New Zealand - services entire Auckland region
- ~$500k-1M NZD annual revenue
- 12+ years trade experience, 5 years running business
- Currently using: Xero (happy), Google Calendar (basic), spreadsheets (manual)

**Stated Pain Points (from interview):**
1. Missed calls = 8-10/day to voicemail, estimates $2k/week in lost jobs
2. Evening admin = 2+ hours every night, 4-5 hours Sunday
3. Slow quoting = days to get quotes out, manual Word documents
4. Disconnected tools = triple-entering job data across systems
5. Payment delays = cashflow strain from net 14 day invoices

**Their Preferences:**
- Budget: $200-300/month for right solution
- Timeline: Within 1-3 months
- Tech comfort: 6/10 - "tutorial follower", wants simple
- Key requirement: "Needs to actually work and be simple"
- Concern: "Wasted money on software I never used before"

**Critical Test - Appropriate Advice for Trades Business:**
This is a LOCAL PHYSICAL service business. Recommendations should be:
- Back-office efficiency focused
- Simple to implement (not technical)
- Trades-specific tools (Tradify, Fergus, ServiceM8)
- NOT "AI transformation" or "revolutionary"

Review the attached report and answer:

1. **APPROPRIATENESS**: Are recommendations suitable for a small trades business? Or is it giving "digital business" advice?

2. **SIMPLICITY**: Could a non-technical plumber actually implement these recommendations?

3. **RELEVANCE**: Does every finding address their actual pain points (missed calls, admin time, slow quoting)?

4. **SPECIFICITY**: Do recommendations use their actual numbers ($2k/week lost, 15+ hrs admin)?

5. **VENDOR FIT**: Are recommended vendors trades-appropriate and NZ-available? Do they integrate with Xero?

6. **ANTI-SLOP CHECK**: Any "leverage AI to transform your business" nonsense? Any enterprise tools for a 4-person shop?

7. **ACTIONABILITY**: Would Eamon know exactly what to sign up for Monday morning?

8. **HONEST LIMITATIONS**: Does it acknowledge what AI CAN'T do for a plumber?

9. **SCORE**: Rate 1-10. What's needed to reach 10/10?
```

---

## Step 4: Common Issues and Fixes (Trades Business)

| Issue | Likely Cause | Fix Location |
|-------|--------------|--------------|
| Generic CRM recommendations | No trades-specific vendors in KB | Add Tradify, Fergus, ServiceM8, Jobber to vendor data |
| "Transformation" language | Prompts don't consider business type | Adjust prompts to recognize physical service businesses |
| Enterprise tools suggested | Size/complexity mismatch | Add business size filtering to recommendations |
| Missing Xero integration | NZ accounting context not considered | Add Xero integration as requirement for NZ trades |
| Unrealistic implementation | Tech comfort not respected | Filter by implementation complexity |
| US-only vendors | Market availability not checked | Add NZ/AU availability to vendor data |

---

## Success Criteria

Report is successful when:

1. **Efficiency focus**: Recommendations are about operational efficiency, NOT business transformation
2. **Trades-appropriate**: Vendors like Tradify/Fergus/ServiceM8, not Salesforce/HubSpot
3. **Simple to implement**: A non-technical plumber could follow the advice
4. **Uses their numbers**: $2k/week missed calls, 15+ hrs/week admin, $200-300 budget
5. **Xero integration**: All recommendations work with their existing accounting
6. **NZ market**: Vendors available in New Zealand
7. **Honest about AI**: Acknowledges AI helps with admin, can't fix pipes
8. **Actionable Monday morning**: Clear first step to take immediately
