"""
Generate a Full Mock CRB Report

This script creates a complete mock report for a home services company
to test the full agent logic and report generation pipeline.

Usage:
    cd backend
    source venv/bin/activate
    python generate_mock_report.py
"""

import asyncio
import json
import sys
import uuid
from datetime import datetime

sys.path.insert(0, '/Users/larsmusic/CRB Analyser/crb-analyser/backend')

from src.config.supabase_client import get_async_supabase


# Mock quiz session data for "ComfortAir HVAC" - a home services company
MOCK_QUIZ_DATA = {
    "company_name": "ComfortAir HVAC Services",
    "website": "https://comfortairhvac.com",
    "industry": "home-services",
    "company_size": "11-50",
    "annual_revenue": "1.5M-3M",
    "email": "test@comfortairhvac.com",
    "answers": {
        "industry": "home-services",
        "company_name": "ComfortAir HVAC Services",
        "company_size": "11-50",
        "annual_revenue": "1.5M-3M",
        "employee_count": "25",
        "technician_count": "15",
        "office_staff_count": "10",

        # Pain points
        "pain_points": [
            "scheduling",
            "customer_communication",
            "lead_management",
            "invoicing",
            "technician_efficiency"
        ],
        "biggest_time_waste": "Manually scheduling technicians and handling customer callbacks",
        "hours_wasted_weekly": "25",

        # Current tools
        "current_tools": [
            "quickbooks",
            "google_calendar",
            "excel",
            "paper_forms"
        ],
        "using_fsm_software": "basic",
        "fsm_software_name": "Basic Google Calendar + spreadsheets",

        # Operations
        "jobs_per_day": "15-25",
        "average_job_value": "350",
        "service_area_miles": "50",
        "call_volume_daily": "40-60",
        "missed_call_percentage": "25",
        "lead_response_time": "2-4 hours",

        # Customer service
        "customer_follow_up": "manual",
        "review_collection": "rarely",
        "repeat_customer_rate": "35%",

        # Quotes and invoicing
        "quote_creation_time": "20-30 minutes",
        "quote_to_close_rate": "45%",
        "invoicing_method": "manual",
        "payment_collection_days": "30-45",

        # AI readiness
        "ai_tools_used": ["chatgpt_basic"],
        "technology_comfort": "7",
        "ai_budget": "5000-15000",
        "ai_goals": [
            "reduce_admin_time",
            "improve_customer_response",
            "grow_revenue",
            "better_scheduling"
        ],
        "timeline_preference": "3-6 months",

        # Team
        "decision_maker": "owner",
        "team_tech_savvy": "6",
        "training_capacity": "willing",

        # Specific pain details
        "scheduling_pain": "Technicians often double-booked, customers wait too long, route planning is guesswork",
        "communication_pain": "Customers call repeatedly asking for ETA, office staff overwhelmed with calls",
        "lead_pain": "Miss calls after hours, leads go cold before we can respond",
        "growth_goals": "Want to grow from €2M to €4M in next 2 years without doubling office staff",
    }
}


async def create_mock_quiz_session():
    """Create a mock quiz session in the database."""
    supabase = await get_async_supabase()

    session_id = str(uuid.uuid4())

    session_data = {
        "id": session_id,
        "email": MOCK_QUIZ_DATA["email"],
        "tier": "full",
        "status": "paid",  # Mark as paid to allow report generation
        "current_section": 10,
        "current_question": 0,
        "answers": MOCK_QUIZ_DATA["answers"],
        "company_name": MOCK_QUIZ_DATA["company_name"],
        "company_website": MOCK_QUIZ_DATA["website"],
        "company_profile": {
            "name": MOCK_QUIZ_DATA["company_name"],
            "industry": MOCK_QUIZ_DATA["industry"],
            "size": MOCK_QUIZ_DATA["company_size"],
            "website": MOCK_QUIZ_DATA["website"],
            "description": "Full-service HVAC company serving residential and light commercial customers in the greater metro area. Specializes in heating, cooling, and indoor air quality solutions.",
        },
        "results": {
            "ai_readiness_score": 65,
            "opportunity_count": 8,
            "value_potential": {"min": 75000, "max": 150000},
            "industry": "home-services",
        },
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    result = await supabase.table("quiz_sessions").insert(session_data).execute()

    if not result.data:
        raise Exception("Failed to create quiz session")

    print(f"✓ Created quiz session: {session_id}")
    return session_id


async def generate_report(session_id: str):
    """Generate a full report for the quiz session."""
    from src.services.report_service import generate_report_streaming

    print("\n" + "="*70)
    print("GENERATING CRB REPORT")
    print("="*70)

    # Collect progress events
    async for event in generate_report_streaming(session_id, tier="full"):
        # Parse the event
        if event.startswith("data: "):
            try:
                data = json.loads(event[6:])
                phase = data.get("phase", "")
                step = data.get("step", "")
                progress = data.get("progress", 0)

                if data.get("error"):
                    print(f"  [ERROR] {data['error']}")
                elif phase == "complete":
                    print(f"\n  [{progress:3d}%] ✓ REPORT COMPLETE!")
                else:
                    print(f"  [{progress:3d}%] [{phase.upper():12s}] {step}")
            except json.JSONDecodeError:
                pass

    # Get the final report
    report = await get_final_report(session_id)
    return report


async def get_final_report(session_id: str):
    """Retrieve the generated report."""
    supabase = await get_async_supabase()

    # Get report ID from session
    session_result = await supabase.table("quiz_sessions").select(
        "report_id"
    ).eq("id", session_id).single().execute()

    if not session_result.data or not session_result.data.get("report_id"):
        print("Warning: No report_id found in session")
        return None

    report_id = session_result.data["report_id"]

    # Get full report
    report_result = await supabase.table("reports").select("*").eq(
        "id", report_id
    ).single().execute()

    if not report_result.data:
        print("Warning: Report not found")
        return None

    return report_result.data


def print_report_summary(report: dict):
    """Print a summary of the generated report."""
    print("\n" + "="*70)
    print("REPORT SUMMARY")
    print("="*70)

    if not report:
        print("No report data available")
        return

    exec_summary = report.get("executive_summary", {})

    print(f"\nCompany: ComfortAir HVAC Services")
    print(f"Industry: Home Services (HVAC)")
    print(f"Tier: {report.get('tier', 'N/A')}")
    print(f"Status: {report.get('status', 'N/A')}")

    print(f"\n--- AI Readiness ---")
    print(f"Score: {exec_summary.get('ai_readiness_score', 'N/A')}/100")
    print(f"Customer Value: {exec_summary.get('customer_value_score', 'N/A')}/10")
    print(f"Business Health: {exec_summary.get('business_health_score', 'N/A')}/10")

    verdict = exec_summary.get("verdict", {})
    print(f"\n--- Verdict ---")
    print(f"Recommendation: {verdict.get('recommendation', 'N/A').upper()}")
    print(f"Headline: {verdict.get('headline', 'N/A')}")
    print(f"Confidence: {verdict.get('confidence', 'N/A')}")

    print(f"\n--- Value Potential ---")
    value = exec_summary.get("total_value_potential", {})
    print(f"Range: €{value.get('min', 0):,} - €{value.get('max', 0):,}")
    print(f"Projection: {value.get('projection_years', 3)} years")

    print(f"\n--- Top Opportunities ---")
    for i, opp in enumerate(exec_summary.get("top_opportunities", [])[:4], 1):
        print(f"{i}. {opp.get('title', 'N/A')} ({opp.get('value_potential', 'N/A')})")

    print(f"\n--- Findings ---")
    findings = report.get("findings", [])
    print(f"Total: {len(findings)}")

    # Count by confidence
    high = sum(1 for f in findings if f.get("confidence") == "high")
    medium = sum(1 for f in findings if f.get("confidence") == "medium")
    low = sum(1 for f in findings if f.get("confidence") == "low")
    print(f"Confidence Distribution: HIGH={high}, MEDIUM={medium}, LOW={low}")

    print(f"\n--- Recommendations ---")
    recs = report.get("recommendations", [])
    print(f"Total: {len(recs)}")
    for i, rec in enumerate(recs[:5], 1):
        print(f"{i}. {rec.get('title', 'N/A')}")

    print(f"\n--- Not Recommended ---")
    for item in exec_summary.get("not_recommended", [])[:3]:
        print(f"• {item.get('title', 'N/A')}: {item.get('reason', 'N/A')}")


async def main():
    print("\n" + "="*70)
    print("CRB ANALYSER - MOCK REPORT GENERATION TEST")
    print("="*70)
    print(f"\nCompany: {MOCK_QUIZ_DATA['company_name']}")
    print(f"Industry: {MOCK_QUIZ_DATA['industry']}")
    print(f"Size: {MOCK_QUIZ_DATA['company_size']} employees")
    print(f"Revenue: {MOCK_QUIZ_DATA['annual_revenue']}")

    try:
        # Step 1: Create mock quiz session
        print("\n--- Step 1: Creating Quiz Session ---")
        session_id = await create_mock_quiz_session()

        # Step 2: Generate report
        print("\n--- Step 2: Generating Report ---")
        report = await generate_report(session_id)

        # Step 3: Print summary
        print_report_summary(report)

        # Step 4: Save full report to file
        output_file = f"mock_report_{session_id[:8]}.json"
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n" + "="*70)
        print(f"FULL REPORT SAVED TO: {output_file}")
        print(f"="*70)

        print(f"\n--- View in Frontend ---")
        print(f"1. Start frontend: cd frontend && npm run dev")
        print(f"2. Navigate to: http://localhost:5174/report/{session_id}")
        print(f"\nOr use the sample report endpoint for testing:")
        print(f"   GET http://localhost:8383/api/reports/public/{report.get('id', session_id)}")

        return report

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    report = asyncio.run(main())

    if report:
        print("\n" + "="*70)
        print("RAW REPORT OUTPUT (First 5000 chars)")
        print("="*70)
        raw_json = json.dumps(report, indent=2, default=str)
        print(raw_json[:5000])
        if len(raw_json) > 5000:
            print(f"\n... [truncated - full report saved to file] ...")
