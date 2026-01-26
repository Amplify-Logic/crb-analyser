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
