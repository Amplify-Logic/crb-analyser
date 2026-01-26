#!/usr/bin/env python3
"""
E2E Report Generation Test - Dutch Home Services Business
Tests ROI calculation fixes for a cleaning/home maintenance company in Netherlands
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
    # QUIZ ANSWERS - Dutch cleaning/home services company
    # =========================================================================
    quiz_answers = {
        # Section 1: Company Overview
        "company_description": "Schoonmaakbedrijf en huishoudelijke diensten in Utrecht en omgeving. We doen reguliere schoonmaak voor particulieren en kleine kantoren, plus incidentele klussen zoals verhuisschoonmaak en raamwassen. Familie bedrijf, 8 jaar actief. Betrouwbaar en persoonlijk contact is ons kenmerk.",
        "employee_count": "2-10",  # Owner + 5-6 cleaners
        "annual_revenue": "250k_500k",  # Typical for small cleaning company
        "primary_goals": ["improve_efficiency", "increase_revenue", "improve_customer_service"],

        # Section 2: Current Operations
        "main_processes": "Planning van schoonmaakrondes is het meeste werk - wie gaat waar, hoeveel tijd per klant. Nieuwe klanten moeten we eerst bezoeken voor offerte. Facturatie doe ik maandelijks handmatig. Communicatie met klanten via WhatsApp, maar dat wordt onoverzichtelijk. Medewerkers inplannen rond hun beschikbaarheid.",
        "repetitive_tasks": "Dezelfde herinneringen sturen voor afspraken. Offertes typen die bijna identiek zijn. Facturen opmaken in Excel en dan overzetten naar boekhouder. Roosters maken en aanpassen. Nieuwe medewerkers dezelfde uitleg geven. Klachten registreren in een notitieboekje.",
        "biggest_bottlenecks": "Kan niet snel genoeg reageren op nieuwe aanvragen - soms 3-4 dagen voor offerte. Medewerkers bellen mij constant voor roosterwijzigingen. Geen overzicht van welke klant welke voorkeuren heeft. Administratie stapelt zich op tot het weekend.",
        "time_on_admin": 20,  # Hours per week
        "manual_data_entry": "yes",
        "manual_data_entry_details": "Klantgegevens in een Excel, agenda in Google Calendar, facturen in Word templates, boekhouding naar de accountant per email. Alles apart, niks gekoppeld.",

        # Section 3: Technology & Tools
        "current_tools": ["spreadsheets", "email", "communication"],
        "tool_pain_points": "WhatsApp is chaos met 6 medewerkers en 80+ klanten. Kan niet zien wie wat heeft gelezen. Excel raakt corrupt soms. Geen app voor medewerkers om uren te registreren.",
        "integration_issues": 2,  # Nothing integrates
        "technology_comfort": 5,  # Basic smartphone/computer skills
        "ai_tools_used": [],  # None yet

        # Section 4: Implementation Preferences
        "implementation_capability": "tutorial_follower",
        "implementation_preference": "buy",
        "budget_comfort": "low_moderate",  # Careful with spending
        "implementation_urgency": "this_quarter",

        # Section 5: Pain Points & Challenges
        "biggest_challenge": "Te veel tijd kwijt aan administratie en planning. Medewerkers vergeten soms afspraken of komen te laat. Klanten klagen dat ze moeilijk contact kunnen krijgen. Groei is lastig zonder betere systemen.",
        "time_wasters": "Handmatig roosters maken en aanpassen. Dezelfde vragen beantwoorden van klanten. Facturen natrekken wie wel/niet betaald heeft. Rijden naar klanten voor offertes die nergens toe leiden.",
        "missed_opportunities": "Nieuwe klanten die afhaken omdat offerte te lang duurt. Klanten die opzeggen omdat communicatie niet soepel is. Geen upsell van extra diensten. Verjaardagen/feestdagen missen voor klantcontact.",
        "cost_concerns": ["labor", "fuel", "software"],
        "quality_issues": "yes",
        "quality_issues_details": "Soms verkeerde schoonmaakmiddelen meegenomen. Medewerkers weten niet altijd de klantvoorkeuren. Incidenteel dubbele boekingen.",

        # Section 6: AI & Automation Readiness
        "ai_interest_areas": ["customer_service", "operations", "scheduling"],
        "budget_for_solutions": "50_100",  # EUR 50-100/month to start
        "implementation_timeline": "3_6_months",
        "decision_makers": "me",
        "additional_context": "We willen groeien maar niet ten koste van de persoonlijke service. Automatisering moet ons helpen, niet vervangen. Budget is beperkt maar als het echt tijd bespaart ben ik bereid te investeren.",
    }

    # =========================================================================
    # INDUSTRY-SPECIFIC ANSWERS - Home Services / Cleaning
    # =========================================================================
    industry_answers = {
        "service_calls_weekly": 40,  # Cleaning appointments per week
        "average_job_value": 85,  # EUR per cleaning session
        "emergency_vs_scheduled": "10_90",  # Mostly scheduled
        "quote_conversion_rate": "60_80",
        "team_size_field": 6,  # Cleaners
        "service_area_radius": "30km",  # Utrecht region
        "scheduling_method": ["phone", "whatsapp"],
        "payment_collection": "Maandelijkse factuur, betaling binnen 14 dagen",
        "biggest_operational_challenge": "Roosters en communicatie. Te veel handwerk, te weinig overzicht.",
    }

    # =========================================================================
    # INTERVIEW DATA - Simulates conversation with owner
    # =========================================================================
    interview_data = {
        "messages": [
            {
                "role": "assistant",
                "content": "Hoeveel tijd ben je kwijt aan het maken en aanpassen van roosters?"
            },
            {
                "role": "user",
                "content": "Minstens 5-6 uur per week. Zondag maak ik het rooster voor de week, maar dan komen er altijd wijzigingen. Zieke medewerkers, klanten die verzetten, vakanties. Elke wijziging kost minstens 15 minuten om door te voeren en iedereen te informeren."
            },
            {
                "role": "assistant",
                "content": "Hoe communiceer je nu met klanten over afspraken?"
            },
            {
                "role": "user",
                "content": "Vooral WhatsApp. Maar met 80 klanten en 6 medewerkers is dat een chaos. Berichten raken kwijt, ik weet niet meer wat ik tegen wie gezegd heb. Klanten sturen ook rechtstreeks naar medewerkers, dan mis ik informatie. Zou eigenlijk een centraal systeem moeten hebben."
            },
            {
                "role": "assistant",
                "content": "Hoe lang duurt het gemiddeld voordat een nieuwe klant een offerte krijgt?"
            },
            {
                "role": "user",
                "content": "Eerlijk gezegd 3-4 dagen. Ik moet eerst langs voor een inschatting, dan terug naar kantoor om de offerte te typen, dan versturen. Sommige klanten hebben tegen die tijd al iemand anders gebeld. Denk dat ik 20-30% verlies daardoor."
            },
            {
                "role": "assistant",
                "content": "Wat kost een gemiddelde schoonmaakbeurt en hoeveel klanten heb je?"
            },
            {
                "role": "user",
                "content": "Particulieren betalen rond de 80-90 euro voor 3 uur schoonmaak. Kleine kantoren 120-150 euro. We hebben ongeveer 60 vaste particuliere klanten die wekelijks of tweewekelijks komen, plus 15-20 zakelijke klanten. En dan nog losse klussen zoals verhuisschoonmaak."
            },
            {
                "role": "assistant",
                "content": "Hoeveel uur per week ben je kwijt aan administratie totaal?"
            },
            {
                "role": "user",
                "content": "Zeker 15-20 uur. Roosters maken, facturen, klantvragen beantwoorden, boekhouding voorbereiden, offertes. Mijn zaterdagmiddag en zondagochtend gaan er helemaal aan op. Zou liever die tijd aan acquisitie of kwaliteitscontrole besteden."
            },
            {
                "role": "assistant",
                "content": "Wat zou het meeste verschil maken in je dagelijks werk?"
            },
            {
                "role": "user",
                "content": "Als klanten zelf online konden boeken en betalen, dat zou enorm schelen. En een app voor medewerkers waar ze hun rooster zien en uren kunnen registreren. Nu bellen ze mij voor alles. En sneller kunnen offreren, liefst ter plekke met de telefoon."
            },
            {
                "role": "assistant",
                "content": "Wat is je budget voor software oplossingen?"
            },
            {
                "role": "user",
                "content": "We zijn een klein bedrijf, dus niet heel veel. Maar als iets me echt 10 uur per week bespaart, dan is 100-150 euro per maand prima. Moet wel echt werken, ik heb geen tijd om ingewikkelde systemen te leren. En het moet in het Nederlands kunnen."
            }
        ],
        "confidence_scores": {
            "pain_points": 92,
            "operations": 88,
            "tech_stack": 75,
            "quantifiable_metrics": 80,
            "buying_signals": 85,
            "industry_context": 90
        }
    }

    # =========================================================================
    # COMPANY PROFILE
    # =========================================================================
    company_profile = {
        "basics": {
            "name": {"value": "Schoonmaakservice Van Dijk", "confidence": 1.0},
            "website": {"value": "schoonmaakservicevandijk.nl", "confidence": 0.9},
            "description": {"value": "Familiebedrijf voor schoonmaakdiensten in Utrecht en omgeving. Particulieren en kleine kantoren. Persoonlijke service en betrouwbaarheid.", "confidence": 0.95}
        },
        "industry": {
            "primary_industry": {"value": "home_services", "confidence": 1.0},
            "sub_industry": {"value": "cleaning", "confidence": 1.0}
        },
        "size": {
            "employee_range": {"value": "2-10", "confidence": 0.9},
            "employee_count": {"value": 7, "confidence": 0.85}
        },
        "location": {
            "city": {"value": "Utrecht", "confidence": 1.0},
            "country": {"value": "Netherlands", "confidence": 1.0},
            "region": {"value": "Utrecht Province", "confidence": 1.0}
        },
        "financials": {
            "revenue_range": {"value": "250k_500k", "confidence": 0.7},
            "currency": {"value": "EUR", "confidence": 1.0}
        }
    }

    # =========================================================================
    # EXISTING TECH STACK
    # =========================================================================
    existing_stack = [
        {
            "name": "Excel/Google Sheets",
            "category": "customer_database",
            "satisfaction": 3,
            "notes": "Klantgegevens en roosters, raakt snel onoverzichtelijk"
        },
        {
            "name": "WhatsApp",
            "category": "communication",
            "satisfaction": 4,
            "notes": "Communicatie met klanten en team, maar chaotisch"
        },
        {
            "name": "Google Calendar",
            "category": "scheduling",
            "satisfaction": 4,
            "notes": "Basis planning, niet gedeeld met team"
        },
        {
            "name": "Word",
            "category": "invoicing",
            "satisfaction": 3,
            "notes": "Handmatige facturen, tijdrovend"
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
        "email": "test-dutch-cleaning@crb-test.local",
        "tier": "quick",
        "status": "paid",
        "current_section": 5,
        "current_question": 25,
        "answers": all_answers,
        "company_name": "Schoonmaakservice Van Dijk",
        "company_website": "schoonmaakservicevandijk.nl",
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
            output_path = "/tmp/dutch-cleaning-report.json"
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
                for i, r in enumerate(report["recommendations"][:5], 1):
                    title = r.get("title", r.get("name", "Untitled"))
                    roi = r.get("roi_percentage", "N/A")
                    payback = r.get("payback_months", "N/A")
                    print(f"  {i}. {title}")
                    print(f"     ROI: {roi}% | Payback: {payback} months")

                    # Show ROI detail if available
                    roi_detail = r.get("roi_detail", {})
                    financial = roi_detail.get("financial_impact", {})
                    if financial:
                        print(f"     Savings: EUR {financial.get('yearly_savings', 0):,.0f}/yr | Cost: EUR {financial.get('yearly_cost', 0):,.0f}/yr")

            # Validate ROI math
            print()
            print("=" * 60)
            print("ROI VALIDATION")
            print("=" * 60)

            for r in report.get("recommendations", []):
                rec_id = r.get("id", "unknown")
                roi = r.get("roi_percentage", 0)
                payback = r.get("payback_months", 0)
                roi_detail = r.get("roi_detail", {})
                financial = roi_detail.get("financial_impact", {})

                if financial:
                    yearly_savings = financial.get("yearly_savings", 0)
                    yearly_cost = financial.get("yearly_cost", 0)
                    impl_cost = financial.get("implementation_cost", 0)

                    # Canonical formula
                    net_annual = yearly_savings - yearly_cost
                    first_year_inv = impl_cost + yearly_cost

                    if first_year_inv > 0:
                        expected_roi = (net_annual / first_year_inv) * 100
                        roi_match = abs(roi - expected_roi) < (expected_roi * 0.15)  # 15% tolerance
                        status = "PASS" if roi_match else "FAIL"
                        print(f"{rec_id}: ROI {roi}% (expected ~{expected_roi:.0f}%) - {status}")

                    if net_annual > 0:
                        expected_payback = impl_cost / (net_annual / 12)
                        payback_match = abs(payback - expected_payback) < (expected_payback * 0.20)  # 20% tolerance
                        status = "PASS" if payback_match else "FAIL"
                        print(f"{rec_id}: Payback {payback} mo (expected ~{expected_payback:.1f} mo) - {status}")
                else:
                    print(f"{rec_id}: No roi_detail.financial_impact - using legacy format")

    else:
        print("ERROR: No report_id returned")

    return report_id


if __name__ == "__main__":
    report_id = asyncio.run(run_test())
