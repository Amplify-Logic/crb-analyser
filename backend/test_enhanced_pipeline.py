#!/usr/bin/env python3
"""
Enhanced CRB Report Pipeline: Gemini → Opus → Refinement

Quality improvements:
1. Rich knowledge base context in prompts
2. Gemini 3 Pro generates initial report
3. Opus 4.5 reviews and identifies issues
4. Gemini applies corrections
5. Validation pass (math + sources)
"""

import json
import time
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, "/Users/larsmusic/CRB Analyser/crb-analyser/backend")

from src.config.llm_client import get_llm_client
from src.config.model_routing import CLAUDE_MODELS, GEMINI_MODELS

# Load knowledge base for richer context
KB_PATH = Path("/Users/larsmusic/CRB Analyser/crb-analyser/backend/src/knowledge")

def load_knowledge_base():
    """Load relevant knowledge base files for home-services."""
    kb_context = {}

    # Load home-services specific data
    hs_path = KB_PATH / "home-services"
    if hs_path.exists():
        for file in ["processes.json", "opportunities.json", "benchmarks.json", "vendors.json"]:
            fp = hs_path / file
            if fp.exists():
                with open(fp) as f:
                    kb_context[file.replace(".json", "")] = json.load(f)

    # Load vendor data
    vendors_path = KB_PATH / "vendors"
    if vendors_path.exists():
        for file in ["scheduling.json", "crm.json", "automation.json"]:
            fp = vendors_path / file
            if fp.exists():
                with open(fp) as f:
                    kb_context[f"vendors_{file.replace('.json', '')}"] = json.load(f)

    return kb_context


def format_kb_context(kb_data: dict) -> str:
    """Format knowledge base data for prompt injection."""
    sections = []

    if "benchmarks" in kb_data:
        benchmarks = kb_data["benchmarks"]
        if isinstance(benchmarks, dict):
            sections.append("VERIFIED INDUSTRY BENCHMARKS (Home Services HVAC):")
            for category, items in benchmarks.items():
                if isinstance(items, list):
                    for item in items[:3]:  # Limit to avoid token explosion
                        if isinstance(item, dict):
                            sections.append(f"  - {item.get('metric', 'N/A')}: {item.get('value', 'N/A')} (Source: {item.get('source', 'Industry data')})")

    if "opportunities" in kb_data:
        opps = kb_data["opportunities"]
        if isinstance(opps, list):
            sections.append("\nKNOWN HIGH-VALUE OPPORTUNITIES:")
            for opp in opps[:5]:
                if isinstance(opp, dict):
                    sections.append(f"  - {opp.get('title', 'N/A')}: {opp.get('typical_savings', 'N/A')}")

    if "vendors_scheduling" in kb_data:
        vendors = kb_data["vendors_scheduling"]
        if isinstance(vendors, list):
            sections.append("\nVERIFIED FSM VENDOR PRICING:")
            for v in vendors[:4]:
                if isinstance(v, dict):
                    sections.append(f"  - {v.get('name', 'N/A')}: {v.get('pricing', 'N/A')} - {v.get('best_for', 'N/A')}")

    return "\n".join(sections) if sections else ""


# Quiz data (same as before)
QUIZ_DATA = {
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
    "growth_goals": "Want to grow from €2M to €4M in next 2 years",
    "repeat_customer_rate": "35%",
    "review_collection": "rarely"
}

SYSTEM_PROMPT = """You are an expert AI business analyst specializing in operational efficiency for service businesses.
You provide actionable, specific recommendations based on evidence and industry benchmarks.
Your analysis is professional, clear, and focuses on ROI and practical implementation.
IMPORTANT: All calculations must be verifiable. Show your math."""


def get_generation_prompt(kb_context: str) -> str:
    return f"""You are analyzing a home services HVAC company for AI/automation opportunities.

Generate a comprehensive CRB (Cost/Risk/Benefit) analysis.

COMPANY DATA:
{json.dumps(QUIZ_DATA, indent=2)}

{kb_context}

ADDITIONAL BENCHMARKS:
- AI call handling captures 85%+ of after-hours leads vs 0% with voicemail
- FSM software improves dispatch efficiency from 55% to 65-75%
- Leads contacted within 5 minutes are 21x more likely to convert
- Automated invoicing reduces collection time by 70%
- Revenue per technician: median €200,000, this company: €133,333
- Membership customer lifetime value €3,000-€10,000 vs €200-€500 one-time

Generate JSON with:
1. executive_summary (headline, key_insight, ai_readiness_score 0-100, value_potential min/max, top_opportunities array, not_recommended array with 3 items)
2. findings array (8-12 items with: id, title, category, confidence, description, current_state citing quiz answer, sources array, value_saved object, value_created object, customer_value_score, business_health_score, is_not_recommended, recommendation with vendor names and pricing)

REQUIREMENTS:
- SHOW ALL MATH: For every € figure, show the calculation (e.g., "25 hrs/week × €25/hr × 50 weeks = €31,250")
- Cite specific quiz answers as sources
- Include 3 "not recommended" items with alternatives
- Specific vendors with verified pricing
- Stay within €5K-15K budget constraint
- All findings must have verifiable calculations"""


REVIEW_PROMPT = """You are a senior business analyst reviewing a CRB report for quality.

ORIGINAL ANALYSIS:
{analysis}

COMPANY CONTEXT:
- €2M revenue, 25 employees, 15 technicians
- 25% missed calls, 2-4 hour lead response
- €5K-15K budget, wants to grow to €4M

Review and provide:

1. MATH VERIFICATION: Check every calculation. Flag errors with corrections.
2. MISSING OPPORTUNITIES: What high-value items were missed?
3. SOURCE GAPS: Which claims lack proper quiz/benchmark citations?
4. IMPROVED RECOMMENDATIONS: Better alternatives for weak recommendations.
5. NOT RECOMMENDED QUALITY: Are the 3 "don't do" items practical and well-reasoned?

Respond with JSON:
{{
  "math_errors": [
    {{"finding_id": "...", "stated": "...", "correct": "...", "formula": "..."}}
  ],
  "missing_opportunities": [
    {{"title": "...", "potential_value": "...", "calculation": "..."}}
  ],
  "source_gaps": [
    {{"finding_id": "...", "claim": "...", "needs": "..."}}
  ],
  "improved_recommendations": [
    {{"finding_id": "...", "original": "...", "improved": "...", "reason": "..."}}
  ],
  "not_recommended_feedback": {{
    "quality_score": 8,
    "improvements": ["..."]
  }},
  "quality_scores": {{
    "math_accuracy": 8,
    "source_citation": 7,
    "actionability": 8,
    "completeness": 7,
    "overall": 7.5
  }},
  "critical_fixes": ["List the 3-5 most important fixes needed"],
  "summary": "2-3 sentence overall assessment"
}}"""


REFINEMENT_PROMPT = """You are refining a CRB analysis based on reviewer feedback.

ORIGINAL ANALYSIS:
{original}

REVIEWER FEEDBACK:
{feedback}

Apply ALL corrections and improvements:
1. Fix every math error identified
2. Add the missing opportunities as new findings
3. Strengthen source citations
4. Improve weak recommendations
5. Keep the same JSON structure

Return the COMPLETE corrected JSON analysis (not just the changes).
Ensure all calculations are shown and verified."""


VALIDATION_PROMPT = """Perform final validation on this CRB report:

REPORT:
{report}

Check:
1. Do all € figures have supporting calculations?
2. Does every finding cite a specific quiz answer or benchmark?
3. Are vendor prices realistic and within €5K-15K budget?
4. Do the numbers in executive_summary match the findings totals?

Return JSON:
{{
  "validation_passed": true/false,
  "issues": [
    {{"type": "math|source|budget|consistency", "location": "...", "issue": "...", "fix": "..."}}
  ],
  "final_quality_score": 8.5,
  "ready_for_delivery": true/false
}}"""


def extract_json(content: str) -> str:
    """Extract JSON from markdown code blocks."""
    if "```json" in content:
        return content.split("```json")[1].split("```")[0]
    elif "```" in content:
        return content.split("```")[1].split("```")[0]
    return content


def safe_generate(client, model, system, messages, max_tokens, temperature, retries=3):
    """Generate with retry logic."""
    for attempt in range(retries):
        try:
            return client.generate(
                model=model,
                system=system,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception as e:
            if attempt < retries - 1:
                wait = (attempt + 1) * 10
                print(f"  Retry {attempt + 1}/{retries} after {wait}s: {str(e)[:50]}...")
                time.sleep(wait)
            else:
                raise


def run_enhanced_pipeline():
    """Run the full enhanced pipeline."""

    print("=" * 70)
    print("ENHANCED CRB PIPELINE: Gemini → Opus Review → Refinement → Validation")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    total_start = time.time()
    results = {"phases": []}

    # Phase 0: Load Knowledge Base
    print("PHASE 0: Loading Knowledge Base...")
    print("-" * 70)
    kb_data = load_knowledge_base()
    kb_context = format_kb_context(kb_data)
    print(f"Loaded {len(kb_data)} knowledge base sections")
    print(f"Context size: {len(kb_context)} chars")
    print()

    # Phase 1: Generate with Gemini (with rich context)
    print("PHASE 1: Generating with Gemini 3 Pro (+ KB context)...")
    print("-" * 70)

    gemini_client = get_llm_client("google")
    gen_prompt = get_generation_prompt(kb_context)

    gen_start = time.time()
    gen_response = safe_generate(
        gemini_client,
        model=GEMINI_MODELS["pro"],
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": gen_prompt}],
        max_tokens=6000,
        temperature=0.7,
    )
    gen_time = time.time() - gen_start

    print(f"Generated in {gen_time:.2f}s")
    print(f"Tokens: {gen_response.get('input_tokens', 'N/A')} → {gen_response.get('output_tokens', 'N/A')}")

    gen_json = extract_json(gen_response["content"])
    try:
        gen_parsed = json.loads(gen_json.strip())
        print(f"Findings: {len(gen_parsed.get('findings', []))}")
    except:
        print("Warning: Could not parse initial generation")
        gen_parsed = None

    results["phases"].append({
        "name": "generation",
        "model": "gemini-3-pro",
        "time": gen_time,
        "tokens_in": gen_response.get("input_tokens"),
        "tokens_out": gen_response.get("output_tokens"),
    })
    print()

    # Phase 2: Review with Opus
    print("PHASE 2: Reviewing with Claude Opus 4.5...")
    print("-" * 70)

    opus_client = get_llm_client("anthropic")
    review_prompt = REVIEW_PROMPT.format(analysis=gen_json[:10000])

    review_start = time.time()
    review_response = opus_client.generate(
        model=CLAUDE_MODELS["opus"],
        system="You are a meticulous senior analyst. Be thorough and critical.",
        messages=[{"role": "user", "content": review_prompt}],
        max_tokens=4000,
        temperature=0.3,
    )
    review_time = time.time() - review_start

    print(f"Reviewed in {review_time:.2f}s")
    print(f"Tokens: {review_response.get('input_tokens', 'N/A')} → {review_response.get('output_tokens', 'N/A')}")

    review_json = extract_json(review_response["content"])
    try:
        review_parsed = json.loads(review_json.strip())
        math_errors = len(review_parsed.get("math_errors", []))
        missing = len(review_parsed.get("missing_opportunities", []))
        print(f"Found: {math_errors} math errors, {missing} missing opportunities")
        print(f"Quality: {review_parsed.get('quality_scores', {}).get('overall', 'N/A')}/10")
    except:
        print("Warning: Could not parse review")
        review_parsed = None

    results["phases"].append({
        "name": "review",
        "model": "claude-opus-4.5",
        "time": review_time,
        "tokens_in": review_response.get("input_tokens"),
        "tokens_out": review_response.get("output_tokens"),
    })
    print()

    # Phase 3: Refine with Gemini (apply corrections)
    print("PHASE 3: Applying corrections with Gemini 3 Pro...")
    print("-" * 70)

    refine_prompt = REFINEMENT_PROMPT.format(
        original=gen_json[:8000],
        feedback=review_json[:4000]
    )

    refine_start = time.time()
    refine_response = gemini_client.generate(
        model=GEMINI_MODELS["pro"],
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": refine_prompt}],
        max_tokens=6000,
        temperature=0.5,
    )
    refine_time = time.time() - refine_start

    print(f"Refined in {refine_time:.2f}s")
    print(f"Tokens: {refine_response.get('input_tokens', 'N/A')} → {refine_response.get('output_tokens', 'N/A')}")

    refined_json = extract_json(refine_response["content"])
    try:
        refined_parsed = json.loads(refined_json.strip())
        print(f"Refined findings: {len(refined_parsed.get('findings', []))}")
    except:
        print("Warning: Could not parse refined output")
        refined_parsed = None

    results["phases"].append({
        "name": "refinement",
        "model": "gemini-3-pro",
        "time": refine_time,
        "tokens_in": refine_response.get("input_tokens"),
        "tokens_out": refine_response.get("output_tokens"),
    })
    print()

    # Phase 4: Final Validation (with Opus for reliability)
    print("PHASE 4: Final validation with Opus...")
    print("-" * 70)

    # Use Opus for validation - more reliable
    validation_prompt = VALIDATION_PROMPT.format(report=refined_json[:8000] if refined_json else gen_json[:8000])

    val_start = time.time()
    try:
        val_response = opus_client.generate(
            model=CLAUDE_MODELS["opus"],
            system="You are a QA analyst. Be precise and thorough.",
            messages=[{"role": "user", "content": validation_prompt}],
            max_tokens=2000,
            temperature=0.2,
        )
        val_time = time.time() - val_start

        print(f"Validated in {val_time:.2f}s")

        val_json = extract_json(val_response["content"])
        try:
            val_parsed = json.loads(val_json.strip())
            issues = len(val_parsed.get("issues", []))
            final_score = val_parsed.get("final_quality_score", "N/A")
            ready = val_parsed.get("ready_for_delivery", False)
            print(f"Issues: {issues}")
            print(f"Final Score: {final_score}/10")
            print(f"Ready for delivery: {'✓ YES' if ready else '✗ NO'}")
        except:
            print("Warning: Could not parse validation")
            val_parsed = {"final_quality_score": "N/A", "ready_for_delivery": False}

        results["phases"].append({
            "name": "validation",
            "model": "claude-opus-4.5",
            "time": val_time,
            "tokens_in": val_response.get("input_tokens"),
            "tokens_out": val_response.get("output_tokens"),
        })
    except Exception as e:
        print(f"Validation error: {e}")
        val_time = 0
        val_response = {"content": ""}
        val_parsed = {"final_quality_score": "N/A", "ready_for_delivery": False}
        results["phases"].append({
            "name": "validation",
            "model": "claude-opus-4.5",
            "time": 0,
            "error": str(e),
        })

    # Summary
    total_time = time.time() - total_start

    print()
    print("=" * 70)
    print("PIPELINE SUMMARY")
    print("=" * 70)

    print(f"\nPhase Breakdown:")
    print(f"  1. Generation (Gemini):   {gen_time:.1f}s")
    print(f"  2. Review (Opus):         {review_time:.1f}s")
    print(f"  3. Refinement (Gemini):   {refine_time:.1f}s")
    print(f"  4. Validation (Gemini):   {val_time:.1f}s")
    print(f"  ─────────────────────────────")
    print(f"  TOTAL:                    {total_time:.1f}s")

    # Cost estimate
    gemini_tokens_in = sum(p.get("tokens_in", 0) or 0 for p in results["phases"] if "gemini" in p.get("model", ""))
    gemini_tokens_out = sum(p.get("tokens_out", 0) or 0 for p in results["phases"] if "gemini" in p.get("model", ""))
    opus_tokens_in = sum(p.get("tokens_in", 0) or 0 for p in results["phases"] if "opus" in p.get("model", ""))
    opus_tokens_out = sum(p.get("tokens_out", 0) or 0 for p in results["phases"] if "opus" in p.get("model", ""))

    gemini_calls = sum(1 for p in results["phases"] if "gemini" in p.get("model", ""))
    opus_calls = sum(1 for p in results["phases"] if "opus" in p.get("model", ""))

    gemini_cost = (gemini_tokens_in * 2 + gemini_tokens_out * 12) / 1_000_000
    opus_cost = (opus_tokens_in * 5 + opus_tokens_out * 25) / 1_000_000

    print(f"\nCost Breakdown:")
    print(f"  Gemini ({gemini_calls} calls): ${gemini_cost:.4f}")
    print(f"  Opus ({opus_calls} calls):   ${opus_cost:.4f}")
    print(f"  TOTAL:              ${gemini_cost + opus_cost:.4f}")

    # Quality comparison
    print(f"\nQuality Progression:")
    if review_parsed:
        initial = review_parsed.get("quality_scores", {}).get("overall", "?")
        print(f"  After Generation:  {initial}/10")
    if val_parsed:
        final = val_parsed.get("final_quality_score", "?")
        print(f"  After Refinement:  {final}/10")
        if review_parsed and isinstance(initial, (int, float)) and isinstance(final, (int, float)):
            improvement = final - initial
            print(f"  Improvement:       +{improvement:.1f} points")

    # Save output
    output = {
        "pipeline": "enhanced_gemini_opus",
        "timestamp": datetime.now().isoformat(),
        "total_time_seconds": total_time,
        "phases": results["phases"],
        "initial_generation": gen_response["content"],
        "review": review_response["content"],
        "refined_report": refine_response["content"],
        "validation": val_response["content"],
        "parsed": {
            "initial": gen_parsed,
            "review": review_parsed,
            "refined": refined_parsed,
            "validation": val_parsed,
        }
    }

    output_file = f"/tmp/enhanced_pipeline_{int(time.time())}.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nFull output saved to: {output_file}")

    return output


if __name__ == "__main__":
    run_enhanced_pipeline()
