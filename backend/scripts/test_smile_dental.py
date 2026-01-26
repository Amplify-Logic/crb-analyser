#!/usr/bin/env python3
"""
E2E Report Generation Test - Smile Dental Auckland
Uses EXACT question IDs from questionnaire.py and dental.json

Run with: cd backend && source venv/bin/activate && python scripts/test_smile_dental.py
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
