"""
Test script to run full CRB report generation for Aquablu using the quiz-based flow.

Usage:
    cd backend
    source venv/bin/activate
    python test_aquablu_report.py
"""
import asyncio
import json
import sys
from datetime import datetime

sys.path.insert(0, '/Users/larsmusic/CRB Analyser/crb-analyser/backend')

from src.config.supabase_client import get_supabase
from src.services.report_service import generate_report_for_quiz, get_report


# Aquablu quiz answers - converted from intake format to quiz format
AQUABLU_QUIZ_ANSWERS = {
    # Question 1: Industry
    "industry": "tech-companies",

    # Question 2: Company size
    "company_size": "51-200",

    # Question 3: Main challenges (multi-select)
    "main_challenges": [
        "manual_processes",
        "scaling_operations",
        "data_disconnected",
        "reporting_time_consuming"
    ],

    # Question 4: Time spent on admin tasks
    "admin_time_percentage": 80,

    # Question 5: AI readiness
    "ai_tools_used": ["chatgpt", "writing_tools"],
    "technology_comfort": 7,

    # Extended context (from intake)
    "company_description": """Aquablu manufactures smart water dispensing systems for commercial spaces.
Our flagship product, the REFILL+ Series 2, provides filtered water with customizable flavoring,
carbonation, and vitamin/mineral enhancement options. We serve enterprise clients like Intel, Microsoft,
Heineken, EY, and Pfizer across 10+ European cities, reaching over 100,000 employees.
Our mission is to eliminate 1 billion plastic bottles by 2030.""",

    "main_processes": """Our main processes include:
1. Manufacturing and assembly of water dispensers in our production facility
2. Installation and onboarding of new enterprise clients
3. Ongoing maintenance and filter replacement scheduling across 10+ cities
4. Cartridge/consumables supply chain management and logistics
5. Customer success management for enterprise accounts
6. Sales pipeline management for new B2B opportunities
7. Sustainability reporting and plastic bottle reduction tracking""",

    "biggest_bottlenecks": """Our biggest bottlenecks are:
1. Predicting when filters need replacement - currently reactive rather than proactive
2. Coordinating service technicians across multiple cities efficiently
3. Manual sustainability report generation for enterprise clients takes days
4. Sales team spends too much time on admin vs. actual selling
5. No real-time visibility into machine performance across our fleet""",

    "time_wasters": """Tasks that feel like a waste:
- Manually compiling monthly sustainability reports (8+ hours per enterprise client)
- Reactive maintenance - technicians traveling to sites only to find minor issues
- Sales team manually researching prospects when data is available
- Re-entering the same data in multiple systems
- Creating custom presentations for each sales pitch""",

    "missed_opportunities": """We're missing:
- Upselling opportunities based on usage patterns (could recommend premium flavors)
- Faster lead response time (currently 24-48 hours, should be instant)
- Proactive customer success interventions (churn prediction)
- Real-time sustainability dashboards that clients can share with their employees
- Geographic expansion held back by operational complexity""",

    "integration_issues": 4,
    "budget_range": "1000_5000",
    "timeline": "1_3_months",
}

# Preliminary quiz results (would normally be calculated from answers)
AQUABLU_QUIZ_RESULTS = {
    "ai_readiness_score": 68,
    "industry": "tech-companies",
    "company_size": "51-200",
    "automation_potential": "high",
    "opportunity_preview": [
        {
            "title": "Predictive Maintenance System",
            "description": "AI-powered filter replacement prediction based on usage patterns",
            "potential_savings": "€25,000-40,000/year",
            "time_horizon": "short"
        },
        {
            "title": "Automated Sustainability Reporting",
            "description": "Generate client sustainability reports in minutes instead of hours",
            "potential_savings": "€15,000-25,000/year",
            "time_horizon": "short"
        },
        {
            "title": "Sales Intelligence & Lead Scoring",
            "description": "AI-powered prospect research and lead prioritization",
            "potential_savings": "€20,000-35,000/year",
            "time_horizon": "mid"
        }
    ],
    "top_challenges": [
        "Reactive maintenance instead of predictive",
        "Manual reporting takes days per client",
        "Disconnected systems requiring duplicate data entry"
    ]
}


async def create_quiz_session():
    """Create a quiz session with Aquablu data."""
    supabase = get_supabase()

    quiz_data = {
        "email": "test@aquablu.com",
        "tier": "full",
        "answers": AQUABLU_QUIZ_ANSWERS,
        "results": AQUABLU_QUIZ_RESULTS,
        "status": "paid",  # Skip payment for test
        "created_at": datetime.utcnow().isoformat(),
        "payment_completed_at": datetime.utcnow().isoformat(),
    }

    result = supabase.table("quiz_sessions").insert(quiz_data).execute()
    return result.data[0]["id"]


async def main():
    print("=" * 70)
    print("CRB ANALYSER - AQUABLU TEST REPORT GENERATION")
    print("=" * 70)

    # Step 1: Create quiz session
    print("\n[1/3] Creating quiz session with Aquablu data...")
    quiz_session_id = await create_quiz_session()
    print(f"      Quiz session created: {quiz_session_id}")

    # Step 2: Generate report
    print("\n[2/3] Generating full CRB report...")
    print("      This may take 1-2 minutes (multiple Claude API calls)...")
    print()

    report_id = await generate_report_for_quiz(quiz_session_id, "full")

    if not report_id:
        print("\n❌ ERROR: Report generation failed!")
        return

    print(f"\n      Report generated: {report_id}")

    # Step 3: Fetch and display report summary
    print("\n[3/3] Fetching report summary...")
    report = await get_report(report_id)

    if report:
        print("\n" + "=" * 70)
        print("REPORT GENERATED SUCCESSFULLY")
        print("=" * 70)

        exec_summary = report.get("executive_summary", {})
        print(f"\n📊 AI Readiness Score: {exec_summary.get('ai_readiness_score', 'N/A')}")
        print(f"💰 Customer Value Score: {exec_summary.get('customer_value_score', 'N/A')}/10")
        print(f"🏢 Business Health Score: {exec_summary.get('business_health_score', 'N/A')}/10")
        print(f"\n📝 Key Insight: {exec_summary.get('key_insight', 'N/A')}")

        top_opps = exec_summary.get("top_opportunities", [])
        if top_opps:
            print("\n🎯 Top Opportunities:")
            for opp in top_opps[:3]:
                print(f"   - {opp.get('title', 'N/A')}: {opp.get('value_potential', 'N/A')}")

        not_rec = exec_summary.get("not_recommended", [])
        if not_rec:
            print("\n⚠️  Not Recommended:")
            for item in not_rec[:2]:
                print(f"   - {item.get('title', 'N/A')}: {item.get('reason', 'N/A')}")

        findings = report.get("findings", [])
        recommendations = report.get("recommendations", [])

        print(f"\n📋 Report Contents:")
        print(f"   - Findings: {len(findings)}")
        print(f"   - Recommendations: {len(recommendations)}")

        value_summary = report.get("value_summary", {})
        if value_summary:
            total = value_summary.get("total", {})
            print(f"\n💵 Total Value Potential (3 years):")
            print(f"   €{total.get('min', 0):,} - €{total.get('max', 0):,}")

        print("\n" + "-" * 70)
        print("VIEW FULL REPORT:")
        print(f"   API: GET /api/reports/public/{report_id}")
        print(f"   Frontend: http://localhost:5174/report/{report_id}")
        print("-" * 70)

        # Also save full report to JSON for inspection
        output_file = f"/Users/larsmusic/CRB Analyser/crb-analyser/backend/aquablu_report_{report_id[:8]}.json"
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n📁 Full report saved to: {output_file}")

    else:
        print("\n❌ ERROR: Could not fetch report!")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
