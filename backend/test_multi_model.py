#!/usr/bin/env python3
"""
Multi-Model Test: Opus 4.5 + Gemini 3 Pro Cross-Check

Strategy:
1. Claude Opus 4.5 generates the full analysis
2. Gemini 3 Pro reviews and validates the output
3. Compare quality with and without cross-check
"""

import json
import time
from datetime import datetime

import sys
sys.path.insert(0, "/Users/larsmusic/CRB Analyser/crb-analyser/backend")

from src.config.llm_client import get_llm_client
from src.config.model_routing import CLAUDE_MODELS, GEMINI_MODELS

# Same comprehensive prompt as before
SYSTEM_PROMPT = """You are an expert AI business analyst specializing in operational efficiency for service businesses.
You provide actionable, specific recommendations based on evidence and industry benchmarks.
Your analysis is professional, clear, and focuses on ROI and practical implementation."""

GENERATION_PROMPT = """You are analyzing a home services HVAC company for AI/automation opportunities.

Generate a comprehensive CRB (Cost/Risk/Benefit) analysis with:
1. Executive summary with AI readiness score (0-100)
2. 8-12 findings across efficiency, growth, and customer experience categories
3. 3 "not recommended" items (things they should NOT do)
4. Specific vendor recommendations with pricing

FULL QUIZ DATA:
{
  "company_name": "ComfortAir HVAC Services",
  "industry": "home-services",
  "annual_revenue": "€2M approx",
  "employee_count": "25",
  "technician_count": "15",
  "office_staff_count": "10",
  "pain_points": ["scheduling", "customer_communication", "lead_management", "invoicing"],
  "biggest_time_waste": "Manually scheduling technicians and handling customer callbacks",
  "hours_wasted_weekly": "25",
  "current_tools": ["quickbooks", "google_calendar", "excel", "paper_forms"],
  "jobs_per_day": "15-25",
  "average_job_value": "€350",
  "call_volume_daily": "40-60",
  "missed_call_percentage": "25%",
  "lead_response_time": "2-4 hours",
  "quote_to_close_rate": "45%",
  "payment_collection_days": "30-45",
  "ai_budget": "€5,000-15,000",
  "growth_goals": "Want to grow from €2M to €4M in next 2 years"
}

INDUSTRY BENCHMARKS:
- AI call handling captures 85%+ of after-hours leads
- FSM software improves dispatch efficiency from 55% to 65-75%
- Leads contacted within 5 minutes are 21x more likely to convert
- Automated invoicing reduces collection time by 70%
- Revenue per technician: median €200,000, this company: €133,333

Generate JSON response with executive_summary (headline, key_insight, ai_readiness_score, value_potential, top_opportunities, not_recommended) and findings array.

REQUIREMENTS:
- Cite specific quiz answers as sources
- Calculate specific € amounts
- 30% HIGH, 50% MEDIUM, 20% LOW confidence
- Include 3 "not recommended" items with alternatives
- Be specific about vendors and pricing
- Stay within €5K-15K budget"""

REVIEW_PROMPT = """You are a senior business analyst reviewing a CRB report for quality and accuracy.

Review this AI-generated analysis and provide:
1. ACCURACY CHECK: Are the calculations correct? Flag any math errors.
2. MISSING OPPORTUNITIES: What important findings were missed?
3. IMPROVED RECOMMENDATIONS: Suggest better alternatives for any weak recommendations.
4. CONFIDENCE ADJUSTMENTS: Should any confidence levels be changed?
5. FINAL QUALITY SCORE: Rate 1-10 on accuracy, actionability, and completeness.

ORIGINAL ANALYSIS TO REVIEW:
{analysis}

COMPANY CONTEXT:
- €2M revenue, 25 employees, 15 technicians
- 25% missed calls, 2-4 hour lead response
- €5K-15K budget, wants to grow to €4M

Respond with JSON:
{{
  "accuracy_issues": [
    {{"finding_id": "...", "issue": "...", "correction": "..."}}
  ],
  "missing_opportunities": [
    {{"title": "...", "potential_value": "...", "why_missed": "..."}}
  ],
  "improved_recommendations": [
    {{"original": "...", "improved": "...", "reason": "..."}}
  ],
  "confidence_adjustments": [
    {{"finding_id": "...", "original": "...", "suggested": "...", "reason": "..."}}
  ],
  "quality_scores": {{
    "accuracy": 8,
    "actionability": 7,
    "completeness": 8,
    "overall": 7.7
  }},
  "summary": "Overall assessment in 2-3 sentences"
}}"""


def run_multi_model_test(mode="opus_then_gemini"):
    """Run multi-model generation + cross-check.

    Modes:
    - opus_then_gemini: Opus generates, Gemini reviews
    - gemini_then_opus: Gemini generates, Opus reviews
    """

    if mode == "opus_then_gemini":
        generator = ("anthropic", CLAUDE_MODELS["opus"], "Claude Opus 4.5")
        reviewer = ("google", GEMINI_MODELS["pro"], "Gemini 3 Pro")
    elif mode == "gemini_then_opus":
        generator = ("google", GEMINI_MODELS["pro"], "Gemini 3 Pro")
        reviewer = ("anthropic", CLAUDE_MODELS["opus"], "Claude Opus 4.5")
    else:  # opus_then_opus
        generator = ("anthropic", CLAUDE_MODELS["opus"], "Claude Opus 4.5")
        reviewer = ("anthropic", CLAUDE_MODELS["opus"], "Claude Opus 4.5 (Review)")

    print("=" * 70)
    print(f"MULTI-MODEL TEST: {generator[2]} → {reviewer[2]} Review")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Phase 1: Generate
    print(f"PHASE 1: Generating with {generator[2]}...")
    print("-" * 70)

    gen_client = get_llm_client(generator[0])

    gen_start = time.time()
    gen_response = gen_client.generate(
        model=generator[1],
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": GENERATION_PROMPT}],
        max_tokens=6000,
        temperature=0.7,
    )
    gen_time = time.time() - gen_start

    print(f"{generator[2]} completed in {gen_time:.2f}s")
    print(f"Tokens: {gen_response.get('input_tokens', 'N/A')} in / {gen_response.get('output_tokens', 'N/A')} out")

    # Extract content
    gen_content = gen_response["content"]
    if "```json" in gen_content:
        gen_json = gen_content.split("```json")[1].split("```")[0]
    elif "```" in gen_content:
        gen_json = gen_content.split("```")[1].split("```")[0]
    else:
        gen_json = gen_content

    # Try to parse for validation
    try:
        gen_parsed = json.loads(gen_json.strip())
        findings_count = len(gen_parsed.get("findings", []))
        print(f"Generated {findings_count} findings")
    except json.JSONDecodeError:
        print("Warning: Could not parse generation JSON")
        gen_parsed = None

    print()

    # Phase 2: Cross-check
    print(f"PHASE 2: Cross-checking with {reviewer[2]}...")
    print("-" * 70)

    review_client = get_llm_client(reviewer[0])

    review_prompt = REVIEW_PROMPT.format(analysis=gen_json[:8000])

    review_start = time.time()
    review_response = review_client.generate(
        model=reviewer[1],
        system="You are a meticulous business analyst who reviews reports for accuracy and completeness. Be thorough and critical.",
        messages=[{"role": "user", "content": review_prompt}],
        max_tokens=4000,
        temperature=0.5,
    )
    review_time = time.time() - review_start

    print(f"{reviewer[2]} review completed in {review_time:.2f}s")
    print(f"Tokens: {review_response.get('input_tokens', 'N/A')} in / {review_response.get('output_tokens', 'N/A')} out")

    # Extract review content
    review_content = review_response["content"]
    if "```json" in review_content:
        review_json = review_content.split("```json")[1].split("```")[0]
    elif "```" in review_content:
        review_json = review_content.split("```")[1].split("```")[0]
    else:
        review_json = review_content

    # Parse review
    try:
        review_parsed = json.loads(review_json.strip())
        print()
        print("=" * 70)
        print("CROSS-CHECK RESULTS")
        print("=" * 70)

        # Accuracy issues
        issues = review_parsed.get("accuracy_issues", [])
        print(f"\nAccuracy Issues Found: {len(issues)}")
        for issue in issues[:5]:
            print(f"  • {issue.get('finding_id', 'N/A')}: {issue.get('issue', 'N/A')[:70]}...")

        # Missing opportunities
        missing = review_parsed.get("missing_opportunities", [])
        print(f"\nMissing Opportunities: {len(missing)}")
        for opp in missing[:5]:
            print(f"  • {opp.get('title', 'N/A')} - {opp.get('potential_value', 'N/A')}")

        # Improved recommendations
        improved = review_parsed.get("improved_recommendations", [])
        print(f"\nImproved Recommendations: {len(improved)}")
        for imp in improved[:3]:
            print(f"  • {imp.get('original', 'N/A')[:40]}...")
            print(f"    → {imp.get('improved', 'N/A')[:50]}...")

        # Confidence adjustments
        adjustments = review_parsed.get("confidence_adjustments", [])
        print(f"\nConfidence Adjustments: {len(adjustments)}")
        for adj in adjustments[:5]:
            print(f"  • {adj.get('finding_id', 'N/A')}: {adj.get('original', '?')} → {adj.get('suggested', '?')}")

        # Quality scores
        scores = review_parsed.get("quality_scores", {})
        print(f"\nQuality Scores:")
        print(f"  Accuracy:      {scores.get('accuracy', 'N/A')}/10")
        print(f"  Actionability: {scores.get('actionability', 'N/A')}/10")
        print(f"  Completeness:  {scores.get('completeness', 'N/A')}/10")
        print(f"  OVERALL:       {scores.get('overall', 'N/A')}/10")

        # Summary
        print(f"\nReviewer Summary:")
        summary = review_parsed.get('summary', 'N/A')
        # Word wrap summary
        words = summary.split()
        line = "  "
        for word in words:
            if len(line) + len(word) > 75:
                print(line)
                line = "  " + word
            else:
                line += " " + word
        print(line)

    except json.JSONDecodeError:
        print("Warning: Could not parse review JSON")
        print("Raw response:")
        print(review_content[:1000])
        review_parsed = None

    # Summary stats
    print()
    print("=" * 70)
    print("PERFORMANCE SUMMARY")
    print("=" * 70)
    total_time = gen_time + review_time
    print(f"{generator[2]} Generation: {gen_time:.2f}s")
    print(f"{reviewer[2]} Review:     {review_time:.2f}s")
    print(f"Total Time:              {total_time:.2f}s")
    print(f"Overhead:                +{(review_time/gen_time)*100:.0f}% for cross-check")

    # Estimate cost (rough)
    if generator[0] == "anthropic":
        gen_cost = (gen_response.get('input_tokens', 0) * 5 + gen_response.get('output_tokens', 0) * 25) / 1_000_000
    else:
        gen_cost = (gen_response.get('input_tokens', 0) * 2 + gen_response.get('output_tokens', 0) * 12) / 1_000_000

    if reviewer[0] == "anthropic":
        review_cost = (review_response.get('input_tokens', 0) * 5 + review_response.get('output_tokens', 0) * 25) / 1_000_000
    else:
        review_cost = (review_response.get('input_tokens', 0) * 2 + review_response.get('output_tokens', 0) * 12) / 1_000_000

    print(f"\nEstimated Cost:")
    print(f"  {generator[2]}:  ${gen_cost:.4f}")
    print(f"  {reviewer[2]}:   ${review_cost:.4f}")
    print(f"  Total:           ${gen_cost + review_cost:.4f}")

    # Save full output
    output = {
        "test_type": f"multi_model_{mode}",
        "timestamp": datetime.now().isoformat(),
        "generation": {
            "provider": generator[0],
            "model": generator[1],
            "model_name": generator[2],
            "time_seconds": gen_time,
            "input_tokens": gen_response.get("input_tokens"),
            "output_tokens": gen_response.get("output_tokens"),
            "content": gen_content,
        },
        "review": {
            "provider": reviewer[0],
            "model": reviewer[1],
            "model_name": reviewer[2],
            "time_seconds": review_time,
            "input_tokens": review_response.get("input_tokens"),
            "output_tokens": review_response.get("output_tokens"),
            "content": review_content,
            "parsed": review_parsed,
        },
        "total_time_seconds": total_time,
    }

    output_file = f"/tmp/multi_model_{mode}_{int(time.time())}.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nFull output saved to: {output_file}")

    return output


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["opus_then_gemini", "gemini_then_opus", "opus_then_opus"],
                        default="opus_then_gemini",
                        help="Which model generates and which reviews")
    args = parser.parse_args()
    run_multi_model_test(mode=args.mode)
