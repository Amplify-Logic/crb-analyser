#!/usr/bin/env python3
"""
E2E Report Generation Test - Any Company URL

Usage:
    python scripts/test_company_report.py https://friendlybuildandfix.co.nz
    python scripts/test_company_report.py https://example.com --tier full

This script:
1. Researches the company from their website
2. Generates realistic quiz answers using AI
3. Creates a full report using Opus 4.5 (full tier) or Sonnet (quick tier)
4. Outputs the report URL and summary

Target markets: UK, NL, Germany, Ireland, NZ, AU
"""

import asyncio
import argparse
import json
import uuid
import sys
import os
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Currency mapping by country TLD
CURRENCY_BY_TLD = {
    ".co.nz": "NZD",
    ".nz": "NZD",
    ".com.au": "AUD",
    ".au": "AUD",
    ".co.uk": "GBP",
    ".uk": "GBP",
    ".de": "EUR",
    ".nl": "EUR",
    ".ie": "EUR",
    ".eu": "EUR",
    ".com": "USD",  # Default for .com
}

# Country mapping by TLD
COUNTRY_BY_TLD = {
    ".co.nz": "New Zealand",
    ".nz": "New Zealand",
    ".com.au": "Australia",
    ".au": "Australia",
    ".co.uk": "United Kingdom",
    ".uk": "United Kingdom",
    ".de": "Germany",
    ".nl": "Netherlands",
    ".ie": "Ireland",
    ".eu": "European Union",
    ".com": "United States",
}


def detect_country_from_url(url: str) -> tuple[str, str]:
    """Detect country and currency from URL TLD."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    for tld, currency in CURRENCY_BY_TLD.items():
        if domain.endswith(tld):
            country = COUNTRY_BY_TLD.get(tld, "Unknown")
            return country, currency

    return "Unknown", "EUR"  # Default to EUR


async def research_company(url: str) -> dict:
    """Research company from URL using web scraping and AI."""
    from anthropic import Anthropic
    from src.config.settings import settings

    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    # Extract domain for company name guess
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    company_name_guess = domain.split(".")[0].replace("-", " ").title()

    country, currency = detect_country_from_url(url)

    print(f"Researching {company_name_guess} from {url}...")
    print(f"Detected: {country} ({currency})")

    # Use Claude to research and generate quiz answers
    research_prompt = f"""Research this company and generate realistic quiz answers for an AI readiness assessment.

COMPANY URL: {url}
COMPANY NAME (guess): {company_name_guess}
DETECTED COUNTRY: {country}
CURRENCY: {currency}

Based on what you can infer from the URL and typical businesses in this industry, generate a complete company profile and quiz answers.

For a {company_name_guess} type business, consider:
- What industry they're in (home_services, professional_services, healthcare, etc.)
- Typical size for this type of business
- Common pain points and challenges
- Typical tech stack
- AI readiness level

Output JSON with this structure:
{{
    "company_profile": {{
        "basics": {{
            "name": {{"value": "...", "confidence": 0.9}},
            "website": {{"value": "{domain}", "confidence": 1.0}},
            "description": {{"value": "...", "confidence": 0.8}}
        }},
        "industry": {{
            "primary_industry": {{"value": "home_services|professional_services|healthcare|...", "confidence": 0.9}},
            "sub_industry": {{"value": "...", "confidence": 0.8}}
        }},
        "size": {{
            "employee_range": {{"value": "2-10|11-50|...", "confidence": 0.7}},
            "employee_count": {{"value": 5, "confidence": 0.6}}
        }},
        "location": {{
            "city": {{"value": "...", "confidence": 0.7}},
            "country": {{"value": "{country}", "confidence": 1.0}},
            "region": {{"value": "...", "confidence": 0.7}}
        }},
        "financials": {{
            "revenue_range": {{"value": "100k_500k|500k_1m|...", "confidence": 0.5}},
            "currency": {{"value": "{currency}", "confidence": 1.0}}
        }}
    }},
    "quiz_answers": {{
        "industry": "home_services|professional_services|healthcare|...",
        "company_description": "Detailed description of what they do...",
        "employee_count": "2-10",
        "annual_revenue": "500k_1m",
        "primary_goals": ["increase_revenue", "improve_efficiency", "reduce_costs"],
        "main_processes": "Description of their main business processes...",
        "repetitive_tasks": "Tasks they do repeatedly...",
        "biggest_bottlenecks": "Their main challenges...",
        "time_on_admin": 15,
        "manual_data_entry": "yes",
        "manual_data_entry_details": "What they enter manually...",
        "current_tools": ["accounting", "spreadsheets", "communication"],
        "tool_pain_points": "What frustrates them about current tools...",
        "integration_issues": 3,
        "technology_comfort": 6,
        "ai_tools_used": ["chatgpt"],
        "implementation_capability": "tutorial_follower",
        "implementation_preference": "buy",
        "budget_comfort": "moderate",
        "implementation_urgency": "this_month",
        "biggest_challenge": "Their #1 challenge...",
        "time_wasters": "What wastes their time...",
        "missed_opportunities": "Revenue they're leaving on table...",
        "cost_concerns": ["labor", "software"],
        "quality_issues": "yes",
        "quality_issues_details": "What quality issues they face...",
        "ai_interest_areas": ["customer_service", "operations", "finance"],
        "budget_for_solutions": "100_500",
        "implementation_timeline": "1_3_months",
        "decision_makers": "me",
        "additional_context": "Any other relevant info..."
    }},
    "industry_answers": {{
        "service_calls_weekly": 25,
        "average_job_value": 450,
        "emergency_vs_scheduled": "40_60",
        "quote_conversion_rate": "50_70",
        "team_size_field": 3,
        "service_area_radius": "50km",
        "scheduling_method": ["phone", "email"],
        "payment_collection": "Invoice after job, net 7-14 days",
        "vehicle_count": 3,
        "biggest_operational_challenge": "Their main operational challenge..."
    }},
    "interview_messages": [
        {{"role": "assistant", "content": "Question about their biggest pain point..."}},
        {{"role": "user", "content": "Realistic answer based on their industry..."}}
    ],
    "existing_stack": [
        {{"name": "Tool Name", "category": "category", "satisfaction": 7, "notes": "..."}}
    ]
}}

Be realistic and specific. Use {currency} for any monetary values.
Make the interview messages sound natural and specific to their business type.
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",  # Use Sonnet for research (faster, cheaper)
        max_tokens=4000,
        messages=[{"role": "user", "content": research_prompt}]
    )

    # Parse the response
    content = response.content[0].text

    # Extract JSON from response
    try:
        # Find JSON in response
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = content[start:end]
            data = json.loads(json_str)
            return data
    except json.JSONDecodeError as e:
        print(f"Failed to parse research response: {e}")
        print(f"Response: {content[:500]}...")

    return {}


async def run_test(url: str, tier: str = "full"):
    """Run the full test for a company URL."""
    from src.config.supabase_client import get_async_supabase
    from src.services.report_service import generate_report_streaming

    # Research the company
    research_data = await research_company(url)

    if not research_data:
        print("ERROR: Failed to research company")
        return None

    company_profile = research_data.get("company_profile", {})
    quiz_answers = research_data.get("quiz_answers", {})
    industry_answers = research_data.get("industry_answers", {})
    interview_messages = research_data.get("interview_messages", [])
    existing_stack = research_data.get("existing_stack", [])

    # Get company name
    company_name = company_profile.get("basics", {}).get("name", {}).get("value", "Unknown Company")
    industry = quiz_answers.get("industry", "general")

    print(f"\nCompany: {company_name}")
    print(f"Industry: {industry}")
    print(f"Tier: {tier} ({'Opus 4.5' if tier == 'full' else 'Sonnet 4.5'})")
    print()

    # Create quiz session
    supabase = await get_async_supabase()
    session_id = str(uuid.uuid4())

    # Merge all answers
    all_answers = {**quiz_answers, **industry_answers}

    # Build interview data
    interview_data = {
        "messages": interview_messages,
        "confidence_scores": {
            "pain_points": 85,
            "operations": 80,
            "tech_stack": 75,
            "quantifiable_metrics": 70,
            "buying_signals": 80,
            "industry_context": 85
        }
    }

    # Extract domain for email
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")

    session_data = {
        "id": session_id,
        "email": f"test-{domain.replace('.', '-')}@crb-test.local",
        "tier": tier,
        "status": "paid",
        "current_section": 5,
        "current_question": 25,
        "answers": all_answers,
        "company_name": company_name,
        "company_website": domain,
        "company_profile": company_profile,
        "interview_data": interview_data,
        "existing_stack": existing_stack,
    }

    await supabase.table("quiz_sessions").insert(session_data).execute()
    print(f"Session: {session_id}")
    print(f"Generating report with {tier} tier (this may take 2-4 minutes for Opus)...")
    print()

    report_id = None
    async for event in generate_report_streaming(session_id, tier):
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

        # Fetch and save report
        result = await supabase.table("reports").select("*").eq("id", report_id).single().execute()
        if result.data:
            # Save to /tmp with company name
            safe_name = company_name.lower().replace(" ", "-").replace("&", "and")[:30]
            output_path = f"/tmp/{safe_name}-report.json"
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
                print(f"AI Readiness Score: {es.get('ai_readiness_score', 'N/A')}/100")
                print(f"Customer Value: {es.get('customer_value_score', 'N/A')}/10")
                print(f"Business Health: {es.get('business_health_score', 'N/A')}/10")
                if es.get("key_insight"):
                    print(f"\nKey Insight: {es.get('key_insight')[:200]}...")

            if "findings" in report and report["findings"]:
                print(f"\nFindings: {len(report['findings'])}")
                for i, f in enumerate(report["findings"][:5], 1):
                    title = f.get("title", f.get("name", "Untitled"))
                    print(f"  {i}. {title}")

            if "recommendations" in report and report["recommendations"]:
                print(f"\nRecommendations: {len(report['recommendations'])}")
                for i, r in enumerate(report["recommendations"][:3], 1):
                    title = r.get("title", r.get("name", "Untitled"))
                    roi = r.get("roi_percentage", "N/A")
                    print(f"  {i}. {title} (ROI: {roi}%)")

            # Token usage
            if "token_usage" in report:
                usage = report["token_usage"]
                total_tokens = usage.get('total_tokens')
                cost = usage.get('estimated_cost_usd')
                print(f"\nToken Usage:")
                if total_tokens and isinstance(total_tokens, (int, float)):
                    print(f"  Total: {int(total_tokens):,}")
                else:
                    print("  Total: N/A")
                if cost and isinstance(cost, (int, float)):
                    print(f"  Cost: ${float(cost):.2f}")
                else:
                    print("  Cost: N/A")
    else:
        print("ERROR: No report_id returned")

    return report_id


def main():
    parser = argparse.ArgumentParser(
        description="Generate AI Readiness Report for any company URL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/test_company_report.py https://friendlybuildandfix.co.nz
  python scripts/test_company_report.py https://example.co.uk --tier quick
  python scripts/test_company_report.py https://plumber-amsterdam.nl --tier full

Supported TLDs (auto-detects currency):
  .co.nz, .nz     -> NZD (New Zealand)
  .com.au, .au    -> AUD (Australia)
  .co.uk, .uk     -> GBP (United Kingdom)
  .de             -> EUR (Germany)
  .nl             -> EUR (Netherlands)
  .ie             -> EUR (Ireland)
  .com            -> USD (default)
"""
    )
    parser.add_argument("url", help="Company website URL")
    parser.add_argument(
        "--tier",
        choices=["quick", "full"],
        default="full",
        help="Report tier: 'quick' uses Sonnet 4.5, 'full' uses Opus 4.5 (default: full)"
    )

    args = parser.parse_args()

    # Validate URL
    if not args.url.startswith("http"):
        args.url = "https://" + args.url

    print("=" * 60)
    print("CRB ANALYSER - Company Report Generator")
    print("=" * 60)
    print()

    asyncio.run(run_test(args.url, args.tier))


if __name__ == "__main__":
    main()
