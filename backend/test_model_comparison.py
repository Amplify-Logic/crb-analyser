#!/usr/bin/env python3
"""
Model Comparison Test Script

Run this script with different providers to compare output quality.
Usage:
    python test_model_comparison.py --provider anthropic
    python test_model_comparison.py --provider google
    python test_model_comparison.py --provider openai
"""

import asyncio
import argparse
import json
import time
from datetime import datetime

# Add parent to path
import sys
sys.path.insert(0, "/Users/larsmusic/CRB Analyser/crb-analyser/backend")

from src.config.llm_client import get_llm_client
from src.config.model_routing import CLAUDE_MODELS, GEMINI_MODELS, OPENAI_MODELS


# The prompt we'll use to test each model
SYSTEM_PROMPT = """You are an expert AI business analyst specializing in operational efficiency for service businesses.
You provide actionable, specific recommendations based on evidence and industry benchmarks.
Your analysis is professional, clear, and focuses on ROI and practical implementation."""

USER_PROMPT = """You are analyzing a home services HVAC company for AI/automation opportunities.

Generate a comprehensive CRB (Cost/Risk/Benefit) analysis with:
1. Executive summary with AI readiness score (0-100)
2. 8-12 findings across efficiency, growth, and customer experience categories
3. 3 "not recommended" items (things they should NOT do)
4. Specific vendor recommendations with pricing

FULL QUIZ DATA:
{
  "company_name": "ComfortAir HVAC Services",
  "website": "https://comfortairhvac.com",
  "industry": "home-services",
  "company_size": "11-50",
  "annual_revenue": "1.5M-3M (approx €2M)",
  "employee_count": "25",
  "technician_count": "15",
  "office_staff_count": "10",

  "pain_points": ["scheduling", "customer_communication", "lead_management", "invoicing", "technician_efficiency"],
  "biggest_time_waste": "Manually scheduling technicians and handling customer callbacks",
  "hours_wasted_weekly": "25",

  "current_tools": ["quickbooks", "google_calendar", "excel", "paper_forms"],
  "using_fsm_software": "basic",
  "fsm_software_name": "Basic Google Calendar + spreadsheets",

  "jobs_per_day": "15-25",
  "average_job_value": "€350",
  "service_area_miles": "50",
  "call_volume_daily": "40-60",
  "missed_call_percentage": "25%",
  "lead_response_time": "2-4 hours",

  "customer_follow_up": "manual",
  "review_collection": "rarely",
  "repeat_customer_rate": "35%",

  "quote_creation_time": "20-30 minutes",
  "quote_to_close_rate": "45%",
  "invoicing_method": "manual",
  "payment_collection_days": "30-45",

  "ai_tools_used": ["chatgpt_basic"],
  "technology_comfort": "7/10",
  "ai_budget": "€5,000-15,000",
  "ai_goals": ["reduce_admin_time", "improve_customer_response", "grow_revenue", "better_scheduling"],
  "timeline_preference": "3-6 months",

  "team_tech_savvy": "6/10",
  "training_capacity": "willing",

  "scheduling_pain": "Technicians often double-booked, customers wait too long, route planning is guesswork",
  "communication_pain": "Customers call repeatedly asking for ETA, office staff overwhelmed with calls",
  "lead_pain": "Miss calls after hours, leads go cold before we can respond",
  "growth_goals": "Want to grow from €2M to €4M in next 2 years without doubling office staff"
}

INDUSTRY BENCHMARKS (Home Services HVAC):
- AI call handling captures 85%+ of after-hours leads vs 0% with voicemail
- FSM software improves dispatch efficiency from 55% average to 65-75%
- Automated reminders reduce no-show rate from 15% to 8%
- Leads contacted within 5 minutes are 21x more likely to convert
- Good-better-best pricing increases average ticket by 20-40%
- Membership customer lifetime value €3,000-€10,000 vs €200-€500 one-time
- Automated invoicing reduces collection time by 70%
- Review automation: 2 reviews per 100 jobs → 15 reviews per 100 jobs
- Revenue per technician: median €200,000, this company: €133,333
- Time on admin: average 2.5 hours/day reduces to 1 hour with FSM software

Generate a JSON response with this structure:
{
  "executive_summary": {
    "headline": "One compelling sentence",
    "key_insight": "Most important takeaway",
    "ai_readiness_score": 65,
    "customer_value_score": 8,
    "business_health_score": 7,
    "total_value_potential": {"min": 75000, "max": 150000},
    "top_opportunities": [
      {"title": "...", "value_potential": "€30K-50K annually"}
    ],
    "not_recommended": [
      {"title": "...", "reason": "Why they should not do this"}
    ]
  },
  "findings": [
    {
      "id": "finding-001",
      "title": "Finding title",
      "category": "efficiency|growth|customer_experience|risk",
      "confidence": "high|medium|low",
      "description": "Detailed description with specific numbers",
      "current_state": "Based on quiz answer: '...'",
      "sources": ["Quiz answer", "Industry benchmark with source"],
      "value_saved": {"annual_savings": 20000, "hours_per_week": 8},
      "value_created": {"potential_revenue": 50000, "description": "How this creates value"},
      "customer_value_score": 8,
      "business_health_score": 9,
      "is_not_recommended": false,
      "why_not": null,
      "what_instead": null
    }
  ]
}

REQUIREMENTS:
- Every finding must cite specific quiz answers as sources
- Include industry benchmarks with source attribution
- Calculate specific € amounts based on their data
- 30% HIGH confidence, 50% MEDIUM, 20% LOW
- Include 3 "not recommended" findings (is_not_recommended: true) with alternatives
- Be specific about vendors (Housecall Pro, ServiceTitan, Jobber, etc.)
- Focus on practical, implementable recommendations within their €5K-15K budget"""


def get_model_for_provider(provider: str) -> tuple[str, str]:
    """Get the premium model for each provider."""
    if provider == "anthropic":
        return CLAUDE_MODELS["opus"], "Claude Opus 4.5"
    elif provider == "google":
        return GEMINI_MODELS["pro"], "Gemini 3 Pro"
    elif provider == "openai":
        return OPENAI_MODELS["gpt52"], "GPT-5.2"
    else:
        raise ValueError(f"Unknown provider: {provider}")


def run_test(provider: str):
    """Run the comparison test for a specific provider."""
    model_id, model_name = get_model_for_provider(provider)

    print("=" * 70)
    print(f"MODEL COMPARISON TEST")
    print(f"=" * 70)
    print(f"Provider: {provider.upper()}")
    print(f"Model: {model_name} ({model_id})")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

    # Get client
    client = get_llm_client(provider)
    print(f"Client initialized: {client.get_provider()}")
    print()

    # Run generation
    print("Generating executive summary and findings...")
    print("-" * 70)

    start_time = time.time()

    try:
        response = client.generate(
            model=model_id,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": USER_PROMPT}],
            max_tokens=8192,
            temperature=0.7,
        )

        elapsed = time.time() - start_time

        print()
        print("=" * 70)
        print("RESULTS")
        print("=" * 70)
        print(f"Time: {elapsed:.2f}s")
        print(f"Input tokens: {response.get('input_tokens', 'N/A')}")
        print(f"Output tokens: {response.get('output_tokens', 'N/A')}")
        print()
        print("-" * 70)
        print("GENERATED CONTENT:")
        print("-" * 70)
        print()
        print(response["content"])
        print()
        print("=" * 70)

        # Try to parse and pretty-print JSON
        try:
            # Extract JSON from response (handle markdown code blocks)
            content = response["content"]
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            parsed = json.loads(content.strip())

            print("PARSED SUMMARY:")
            print("-" * 70)
            if "executive_summary" in parsed:
                es = parsed["executive_summary"]
                print(f"Headline: {es.get('headline', 'N/A')}")
                print(f"AI Readiness: {es.get('ai_readiness_score', 'N/A')}/100")
                print(f"Customer Value: {es.get('customer_value_score', 'N/A')}/10")
                print(f"Business Health: {es.get('business_health_score', 'N/A')}/10")
                vp = es.get('total_value_potential', {})
                if vp:
                    print(f"Value Potential: €{vp.get('min', '?'):,} - €{vp.get('max', '?'):,}")
                print(f"Key Insight: {es.get('key_insight', 'N/A')}")

                # Top opportunities
                if es.get('top_opportunities'):
                    print()
                    print("Top Opportunities:")
                    for opp in es['top_opportunities'][:5]:
                        print(f"  • {opp.get('title', 'N/A')} - {opp.get('value_potential', 'N/A')}")

                # Not recommended
                if es.get('not_recommended'):
                    print()
                    print("Not Recommended:")
                    for nr in es['not_recommended']:
                        print(f"  ✗ {nr.get('title', 'N/A')}")
                        print(f"    Reason: {nr.get('reason', 'N/A')}")

            if "findings" in parsed:
                print()
                # Count by confidence
                high = sum(1 for f in parsed['findings'] if f.get('confidence') == 'high')
                med = sum(1 for f in parsed['findings'] if f.get('confidence') == 'medium')
                low = sum(1 for f in parsed['findings'] if f.get('confidence') == 'low')
                print(f"Findings ({len(parsed['findings'])} total): HIGH={high}, MEDIUM={med}, LOW={low}")
                print()
                for i, f in enumerate(parsed["findings"], 1):
                    cat = f.get('category', '?')
                    conf = f.get('confidence', '?')
                    is_not_rec = f.get('is_not_recommended', False)
                    marker = "✗ NOT REC:" if is_not_rec else f"  {i}."
                    print(f"{marker} [{cat.upper()}] {f.get('title', 'Untitled')} [{conf}]")
                    if f.get('value_saved'):
                        vs = f['value_saved']
                        print(f"     Saves: €{vs.get('annual_savings', 0):,}/yr, {vs.get('hours_per_week', 0)} hrs/wk")
                    if f.get('value_created'):
                        vc = f['value_created']
                        print(f"     Creates: €{vc.get('potential_revenue', 0):,} potential")
                    print(f"     Scores: Customer={f.get('customer_value_score', '?')}/10, Business={f.get('business_health_score', '?')}/10")

            print("=" * 70)

        except json.JSONDecodeError:
            print("(Could not parse JSON from response)")

        # Save full output
        output_file = f"/tmp/model_comparison_{provider}_{int(time.time())}.json"
        with open(output_file, "w") as f:
            json.dump({
                "provider": provider,
                "model": model_id,
                "model_name": model_name,
                "elapsed_seconds": elapsed,
                "input_tokens": response.get("input_tokens"),
                "output_tokens": response.get("output_tokens"),
                "content": response["content"],
                "timestamp": datetime.now().isoformat(),
            }, f, indent=2)
        print(f"Full output saved to: {output_file}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test LLM model for report generation")
    parser.add_argument(
        "--provider",
        choices=["anthropic", "google", "openai"],
        required=True,
        help="Which provider to test"
    )
    args = parser.parse_args()

    run_test(args.provider)
