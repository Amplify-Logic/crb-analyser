#!/usr/bin/env python3
"""
Run full CRB Analyser demo for Aquablu.

Creates a quiz session with Aquablu's realistic data and generates a full report.
"""

import asyncio
import httpx
import json
from datetime import datetime

API_BASE = "http://localhost:8383/api"

# Aquablu company data based on research
AQUABLU_DATA = {
    "company_name": "Aquablu",
    "email": "demo@aquablu.com",
    "industry": "home-services",  # Closest fit - B2B service company
    "website": "https://aquablu.com",

    # Quiz answers based on research
    "answers": {
        # Company basics
        "industry": "home-services",
        "company_name": "Aquablu",
        "company_size": "11-50",  # Growing startup, <100 target by 2028
        "employee_count": 35,
        "annual_revenue": "1000000-5000000",  # Profitable, 300% YoY growth
        "years_in_business": "3-5",  # Founded 2018
        "target_market": "B2B offices, hotels, public spaces",

        # Current tools
        "current_tools": [
            "CRM system",
            "IoT platform for dispensers",
            "Mobile app for customers",
            "ERP system"
        ],

        # Pain points - realistic for a scaling hardware+software company
        "pain_points": [
            "Managing field service for dispenser installation/maintenance",
            "Customer onboarding takes too long",
            "Manual data entry from dispenser sensors",
            "Scaling customer support with growth",
            "Invoice and contract management",
            "Coordinating installation schedules",
        ],

        # Processes
        "biggest_time_wasters": [
            "Scheduling technician visits",
            "Responding to customer inquiries",
            "Generating usage reports for clients",
            "Processing new customer contracts",
        ],

        "manual_processes": [
            "Customer onboarding documentation",
            "Service scheduling and dispatch",
            "Invoice generation",
            "Customer support responses",
            "Installation planning",
        ],

        # AI readiness
        "ai_experience": "some_automation",
        "ai_budget": "15000-50000",
        "tech_comfort": 8,  # Tech company
        "data_organization": "organized and structured",
        "processes_documented": "partially documented",

        # Goals
        "primary_goal": "Scale operations without proportionally scaling headcount",
        "timeline": "3-6 months",
        "decision_maker": True,

        # Specific context
        "service_types": ["Equipment installation", "Maintenance", "Customer support"],
        "customer_count": "200-500",  # Large clients like Heineken, Schiphol
        "average_ticket_value": "5000-10000",  # B2B contracts

        # Interview-style responses
        "describe_business": """
        Aquablu is a Dutch hydration technology company that provides smart water
        dispensers (REFILL+) to offices, hotels, and public spaces. Our system
        purifies tap water and adds vitamins/minerals, replacing single-use plastic
        bottles. We serve major clients like Heineken and Schiphol airport.
        We've achieved 300% annual growth for 3 years and are now expanding globally.
        """,

        "biggest_challenge": """
        Our biggest challenge is scaling our operations efficiently. We're growing
        rapidly (300% YoY) and need to handle more installations, maintenance visits,
        and customer support without proportionally increasing our team. We want to
        reach €100M revenue with fewer than 100 employees by 2028.
        """,

        "current_bottlenecks": """
        1. Field service scheduling - coordinating technician visits is manual
        2. Customer onboarding - contracts and setup take too long
        3. Support tickets - responding to maintenance requests quickly
        4. Reporting - generating usage reports for clients manually
        5. Invoice processing - billing cycles are time-consuming
        """,

        "ideal_outcome": """
        I want automated scheduling that optimizes technician routes, instant
        customer onboarding with AI-assisted contract generation, proactive
        maintenance alerts from our IoT data, and automated customer support
        for common questions. This would let us 3x our customer base without
        doubling staff.
        """,
    }
}


async def create_session(client: httpx.AsyncClient) -> str:
    """Create a quiz session."""
    print("\n📋 Creating quiz session for Aquablu...")

    response = await client.post(
        f"{API_BASE}/quiz/sessions",
        json={
            "email": AQUABLU_DATA["email"],
            "tier": "full",  # Full report tier
            "industry": AQUABLU_DATA["industry"],
        }
    )

    if response.status_code != 200:
        print(f"Error creating session: {response.text}")
        raise Exception(f"Failed to create session: {response.status_code}")

    data = response.json()
    session_id = data["session_id"]
    print(f"✅ Created session: {session_id}")
    return session_id


async def submit_answers(client: httpx.AsyncClient, session_id: str):
    """Submit all quiz answers."""
    print("\n📝 Submitting Aquablu quiz answers...")

    response = await client.patch(
        f"{API_BASE}/quiz/sessions/{session_id}",
        json={
            "answers": AQUABLU_DATA["answers"],
            "current_section": 5,
            "current_question": 20,
        }
    )

    if response.status_code != 200:
        print(f"Error submitting answers: {response.text}")
        raise Exception(f"Failed to submit answers: {response.status_code}")

    data = response.json()
    print(f"✅ Submitted {data['answers_count']} answers ({data['completion_percent']}% complete)")
    return data


async def bypass_payment(session_id: str):
    """Bypass payment for demo - directly update database."""
    print("\n💳 Bypassing payment for demo mode...")

    import sys
    sys.path.insert(0, '/Users/larsmusic/CRB Analyser/crb-analyser/backend')

    from src.config.supabase_client import get_async_supabase

    supabase = await get_async_supabase()

    # Update session to paid status (use only existing columns)
    await supabase.table("quiz_sessions").update({
        "status": "paid",
        "updated_at": datetime.now().isoformat(),
    }).eq("id", session_id).execute()

    print("✅ Payment bypassed - session marked as paid")


async def generate_report(client: httpx.AsyncClient, session_id: str) -> str:
    """Generate the full report."""
    print("\n🚀 Generating full CRB Analysis report...")
    print("   This will take 1-2 minutes...\n")

    # Use streaming endpoint
    async with client.stream(
        "GET",
        f"{API_BASE}/reports/stream/{session_id}",
        params={"tier": "full"},
        timeout=300.0,  # 5 minute timeout
    ) as response:
        report_id = None

        async for line in response.aiter_lines():
            if line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    phase = data.get("phase", "")
                    step = data.get("step", "")
                    progress = data.get("progress", 0)

                    # Print progress
                    print(f"   [{progress:3d}%] {phase}: {step}")

                    if data.get("report_id"):
                        report_id = data["report_id"]

                    if phase == "complete":
                        break

                except json.JSONDecodeError:
                    pass

    if report_id:
        print(f"\n✅ Report generated: {report_id}")
        return report_id
    else:
        raise Exception("Report generation failed - no report_id received")


async def get_report_url(session_id: str, report_id: str) -> str:
    """Get the report viewer URL."""
    return f"http://localhost:5174/report/{report_id}?session={session_id}"


async def main():
    """Run the full demo."""
    print("=" * 60)
    print("🌊 AQUABLU CRB ANALYSIS DEMO")
    print("=" * 60)
    print(f"\nCompany: {AQUABLU_DATA['company_name']}")
    print(f"Industry: {AQUABLU_DATA['industry']}")
    print(f"Size: {AQUABLU_DATA['answers']['company_size']} employees")
    print(f"Pain points: {len(AQUABLU_DATA['answers']['pain_points'])}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Create session
        session_id = await create_session(client)

        # Step 2: Submit answers
        await submit_answers(client, session_id)

        # Step 3: Bypass payment (demo mode)
        await bypass_payment(session_id)

        # Step 4: Generate report
        report_id = await generate_report(client, session_id)

        # Step 5: Get URLs
        report_url = await get_report_url(session_id, report_id)

        print("\n" + "=" * 60)
        print("✅ DEMO COMPLETE!")
        print("=" * 60)
        print(f"\n📊 View your report at:")
        print(f"\n   {report_url}")
        print(f"\n📱 Or open in browser:")
        print(f"   Session ID: {session_id}")
        print(f"   Report ID:  {report_id}")
        print("\n" + "=" * 60)

        return report_url


if __name__ == "__main__":
    url = asyncio.run(main())
