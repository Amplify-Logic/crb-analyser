# Real Data CRB Pipeline - Run in Separate Claude Code Instance

## Instructions

1. Copy this entire file
2. Open a new Claude Code terminal
3. Paste and run
4. Replace `REAL_QUIZ_DATA` with actual client responses

---

## The Pipeline

```bash
cd /Users/larsmusic/CRB\ Analyser/crb-analyser/backend && source venv/bin/activate
```

Then run:

```python
python - << 'PIPELINE_EOF'
#!/usr/bin/env python3
"""
REAL DATA CRB Pipeline: Gemini → Opus Review → Opus Refine → Opus Validate
"""

import json
import time
from datetime import datetime

import sys
sys.path.insert(0, "/Users/larsmusic/CRB Analyser/crb-analyser/backend")

from src.config.llm_client import get_llm_client
from src.config.model_routing import CLAUDE_MODELS, GEMINI_MODELS

# ============================================================================
# REPLACE THIS WITH REAL CLIENT QUIZ DATA
# ============================================================================
REAL_QUIZ_DATA = {
    # Company basics
    "company_name": "",  # e.g., "Smith's Plumbing & Heating"
    "website": "",  # e.g., "https://smithsplumbing.com"
    "industry": "home-services",  # or: dental, recruiting, coaching, veterinary, professional-services
    "company_size": "",  # "1-10", "11-50", "51-200"
    "annual_revenue": "",  # e.g., "€500K-1M", "€1M-3M"
    "employee_count": "",  # total
    "technician_count": "",  # field workers (if applicable)
    "office_staff_count": "",  # admin/office

    # Pain points (from quiz)
    "pain_points": [],  # ["scheduling", "invoicing", "customer_communication", "lead_management"]
    "biggest_time_waste": "",  # free text from client
    "hours_wasted_weekly": "",  # number

    # Current tools
    "current_tools": [],  # ["quickbooks", "google_calendar", "excel", "paper_forms", etc.]
    "using_crm": "",  # "none", "basic", "advanced"
    "crm_name": "",  # if using one
    "using_fsm_software": "",  # "none", "basic", "advanced" (for service businesses)
    "fsm_software_name": "",  # if using one

    # Operations metrics
    "jobs_per_day": "",  # for service businesses
    "average_job_value": "",  # e.g., "€350"
    "service_area_miles": "",  # or km
    "call_volume_daily": "",  # if applicable
    "missed_call_percentage": "",  # e.g., "20%"
    "lead_response_time": "",  # e.g., "2-4 hours", "same day", "next day"

    # Customer metrics
    "customer_follow_up": "",  # "manual", "automated", "none"
    "review_collection": "",  # "automated", "manual", "rarely", "never"
    "repeat_customer_rate": "",  # e.g., "40%"

    # Sales metrics
    "quote_creation_time": "",  # e.g., "30 minutes"
    "quote_to_close_rate": "",  # e.g., "45%"
    "invoicing_method": "",  # "manual", "semi-automated", "automated"
    "payment_collection_days": "",  # e.g., "30-45"

    # AI readiness
    "ai_tools_used": [],  # ["chatgpt", "none", etc.]
    "technology_comfort": "",  # "1-10"
    "ai_budget": "",  # e.g., "€5,000-15,000"
    "ai_goals": [],  # ["reduce_admin_time", "improve_customer_response", "grow_revenue"]
    "timeline_preference": "",  # "1-3 months", "3-6 months", "6-12 months"

    # Team
    "team_tech_savvy": "",  # "1-10"
    "training_capacity": "",  # "limited", "moderate", "willing"

    # Free text (most valuable!)
    "scheduling_pain": "",  # client's own words
    "communication_pain": "",  # client's own words
    "lead_pain": "",  # client's own words
    "growth_goals": "",  # client's own words
    "other_notes": "",  # anything else they mentioned
}
# ============================================================================

# Only proceed if we have real data
if not REAL_QUIZ_DATA.get("company_name"):
    print("ERROR: Please fill in REAL_QUIZ_DATA with actual client information")
    print("At minimum: company_name, industry, annual_revenue, pain_points")
    sys.exit(1)

# Industry benchmarks (load from KB or use defaults)
INDUSTRY_BENCHMARKS = {
    "home-services": """
- AI call handling captures 85%+ of after-hours leads vs 0% with voicemail
- FSM software improves dispatch efficiency from 55% to 65-75%
- Automated reminders reduce no-show rate from 15% to 8%
- Leads contacted within 5 minutes are 21x more likely to convert
- Good-better-best pricing increases average ticket by 20-40%
- Membership customer lifetime value €3,000-€10,000 vs €200-€500 one-time
- Automated invoicing reduces collection time by 70%
- Revenue per technician: median €200,000
- Time on admin: average 2.5 hours/day reduces to 1 hour with FSM
""",
    "dental": """
- 35% of dental practices now using AI (2025)
- AI scheduling reduces no-shows by 30-50%
- Automated patient communication saves 15-20 hours/week
- Treatment plan acceptance increases 25% with visual AI
- Revenue per operatory benchmark: €400,000-600,000/year
- Patient reactivation campaigns recover 10-15% of dormant patients
""",
    "professional-services": """
- 71% GenAI adoption in professional services (2025)
- AI document review 60-90% faster than manual
- Automated time tracking recovers 10-15% billable hours
- Client communication automation saves 5-10 hours/week
- Proposal automation reduces creation time by 70%
""",
    "recruiting": """
- 61-67% of staffing firms using AI (2025)
- AI screening reduces time-to-shortlist by 75%
- Automated candidate communication improves response rates 40%
- Time-to-hire reduced 50% with AI matching
""",
}

SYSTEM_PROMPT = """You are an expert AI business analyst specializing in operational efficiency.
You analyze REAL client data and provide specific, actionable recommendations.
All calculations must be verifiable with clear math shown.
Be honest about uncertainty - if data is incomplete, say so."""

def get_benchmarks(industry):
    return INDUSTRY_BENCHMARKS.get(industry, INDUSTRY_BENCHMARKS["home-services"])

GENERATION_PROMPT = f"""Analyze this REAL client for AI/automation opportunities.

CLIENT DATA (from intake quiz):
{json.dumps(REAL_QUIZ_DATA, indent=2)}

INDUSTRY BENCHMARKS ({REAL_QUIZ_DATA.get('industry', 'home-services')}):
{get_benchmarks(REAL_QUIZ_DATA.get('industry', 'home-services'))}

Generate a comprehensive CRB analysis with:
1. Executive summary with AI readiness score (0-100)
2. 8-12 findings with specific € calculations
3. 3 "not recommended" items
4. Vendor recommendations with pricing

OUTPUT JSON:
{{
  "executive_summary": {{
    "headline": "One compelling sentence about this specific company",
    "key_insight": "The most important finding for THIS client",
    "ai_readiness_score": 0-100,
    "ai_readiness_rationale": "Why this score",
    "customer_value_score": 1-10,
    "business_health_score": 1-10,
    "total_value_potential": {{"min": 0, "max": 0, "currency": "EUR"}},
    "top_opportunities": [
      {{"title": "...", "value_potential": "€X-Y annually", "quick_win": true/false}}
    ],
    "not_recommended": [
      {{"title": "...", "reason": "...", "what_instead": "..."}}
    ],
    "data_gaps": ["List any missing data that limits analysis accuracy"]
  }},
  "findings": [
    {{
      "id": "finding-001",
      "title": "Specific finding title",
      "category": "efficiency|growth|customer_experience|risk",
      "confidence": "high|medium|low",
      "confidence_rationale": "Why this confidence level",
      "description": "Detailed description with numbers",
      "current_state": "Quote the exact quiz answer that supports this",
      "calculation": {{
        "formula": "Show your math step by step",
        "inputs": {{"variable": "value from quiz"}},
        "result": "€X"
      }},
      "sources": ["Quiz: field_name = value", "Benchmark: source"],
      "value_saved": {{"annual_savings": 0, "hours_per_week": 0}},
      "value_created": {{"potential_revenue": 0, "description": "How"}},
      "customer_value_score": 1-10,
      "business_health_score": 1-10,
      "is_not_recommended": false,
      "recommendation": {{
        "action": "What to do",
        "vendors": [{{"name": "...", "pricing": "€X/month", "why": "..."}}],
        "implementation_weeks": 0,
        "budget_fit": "Within/exceeds €X-Y budget"
      }}
    }}
  ]
}}

REQUIREMENTS:
- Quote exact client answers as evidence
- Show ALL math with formulas
- Flag where data is missing or assumed
- 3 "not recommended" items with alternatives
- Stay within stated budget
- Be conservative with estimates (we'd rather under-promise)
"""

REVIEW_PROMPT = """Review this CRB analysis for a REAL client.

ANALYSIS:
{analysis}

ORIGINAL CLIENT DATA:
{quiz_data}

Check thoroughly:
1. MATH ACCURACY: Verify every calculation against the quiz data
2. EVIDENCE QUALITY: Does each finding cite the actual quiz answer?
3. MISSING OPPORTUNITIES: What high-value items were missed?
4. REALISTIC ESTIMATES: Are projections conservative or inflated?
5. BUDGET FIT: Do recommendations fit the stated budget?
6. DATA GAPS: What's missing that limits confidence?

OUTPUT JSON:
{{
  "math_errors": [
    {{"finding_id": "...", "stated": "...", "should_be": "...", "formula": "..."}}
  ],
  "unsupported_claims": [
    {{"finding_id": "...", "claim": "...", "missing_evidence": "..."}}
  ],
  "missing_opportunities": [
    {{"title": "...", "potential_value": "...", "evidence_from_quiz": "..."}}
  ],
  "inflated_estimates": [
    {{"finding_id": "...", "original": "...", "conservative": "...", "reason": "..."}}
  ],
  "budget_issues": [
    {{"recommendation": "...", "issue": "..."}}
  ],
  "quality_scores": {{
    "math_accuracy": 0-10,
    "evidence_quality": 0-10,
    "actionability": 0-10,
    "conservatism": 0-10,
    "overall": 0-10
  }},
  "critical_fixes": ["The 3-5 most important fixes"],
  "summary": "2-3 sentence assessment"
}}"""

REFINE_PROMPT = """You are refining a CRB analysis based on expert review.

ORIGINAL ANALYSIS:
{original}

EXPERT REVIEW (must fix all issues):
{review}

Apply ALL corrections:
1. Fix every math error
2. Add missing evidence citations
3. Add missing opportunities as new findings
4. Make inflated estimates more conservative
5. Fix budget issues
6. Note remaining data gaps

Return the COMPLETE corrected JSON (same structure as original).
Mark any remaining uncertainties clearly."""

VALIDATE_PROMPT = """Final quality check on this CRB report before client delivery.

REPORT:
{report}

CLIENT BUDGET: {budget}

Validate:
1. Every € figure has supporting calculation
2. Every finding cites specific quiz answers
3. All vendors are within budget
4. Executive summary numbers match finding totals
5. No inflated claims without evidence

OUTPUT JSON:
{{
  "validation_passed": true/false,
  "blocking_issues": ["Issues that MUST be fixed before delivery"],
  "minor_issues": ["Nice to fix but not blocking"],
  "final_quality_score": 0-10,
  "ready_for_delivery": true/false,
  "client_name": "...",
  "summary": "One sentence: ready or not ready and why"
}}"""


def safe_generate(client, model, system, messages, max_tokens, temperature, retries=3):
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
                wait = (attempt + 1) * 15
                print(f"  Retry {attempt + 1}/{retries} after {wait}s...")
                time.sleep(wait)
            else:
                raise

def extract_json(content):
    if "```json" in content:
        return content.split("```json")[1].split("```")[0]
    elif "```" in content:
        return content.split("```")[1].split("```")[0]
    return content


def run_pipeline():
    print("=" * 70)
    print(f"REAL DATA CRB PIPELINE: {REAL_QUIZ_DATA.get('company_name', 'Unknown')}")
    print("=" * 70)
    print(f"Industry: {REAL_QUIZ_DATA.get('industry', 'N/A')}")
    print(f"Revenue: {REAL_QUIZ_DATA.get('annual_revenue', 'N/A')}")
    print(f"Budget: {REAL_QUIZ_DATA.get('ai_budget', 'N/A')}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    gemini = get_llm_client("google")
    opus = get_llm_client("anthropic")

    # Phase 1: Gemini generates
    print("\n[1/4] Generating initial analysis with Gemini 3 Pro...")
    t1 = time.time()
    gen = safe_generate(gemini, GEMINI_MODELS["pro"], SYSTEM_PROMPT,
                        [{"role": "user", "content": GENERATION_PROMPT}],
                        max_tokens=6000, temperature=0.7)
    print(f"  Done in {time.time()-t1:.1f}s ({gen.get('output_tokens', '?')} tokens)")
    gen_json = extract_json(gen["content"])

    # Phase 2: Opus reviews
    print("\n[2/4] Expert review with Claude Opus 4.5...")
    t2 = time.time()
    review_prompt = REVIEW_PROMPT.format(
        analysis=gen_json[:10000],
        quiz_data=json.dumps(REAL_QUIZ_DATA, indent=2)
    )
    review = safe_generate(opus, CLAUDE_MODELS["opus"],
                           "You are a meticulous senior analyst reviewing real client work.",
                           [{"role": "user", "content": review_prompt}],
                           max_tokens=4000, temperature=0.3)
    print(f"  Done in {time.time()-t2:.1f}s")
    review_json = extract_json(review["content"])

    try:
        review_parsed = json.loads(review_json.strip())
        scores = review_parsed.get("quality_scores", {})
        print(f"  Initial quality: {scores.get('overall', '?')}/10")
        print(f"  Math errors: {len(review_parsed.get('math_errors', []))}")
        print(f"  Missing opps: {len(review_parsed.get('missing_opportunities', []))}")
    except:
        print("  Warning: Could not parse review")
        review_parsed = {}

    # Phase 3: Opus refines
    print("\n[3/4] Applying corrections with Claude Opus 4.5...")
    t3 = time.time()
    refine_prompt = REFINE_PROMPT.format(original=gen_json[:8000], review=review_json[:4000])
    refined = safe_generate(opus, CLAUDE_MODELS["opus"], SYSTEM_PROMPT,
                            [{"role": "user", "content": refine_prompt}],
                            max_tokens=6000, temperature=0.4)
    print(f"  Done in {time.time()-t3:.1f}s")
    refined_json = extract_json(refined["content"])

    # Phase 4: Opus validates
    print("\n[4/4] Final validation with Claude Opus 4.5...")
    t4 = time.time()
    val_prompt = VALIDATE_PROMPT.format(
        report=refined_json[:8000],
        budget=REAL_QUIZ_DATA.get("ai_budget", "not specified")
    )
    validated = safe_generate(opus, CLAUDE_MODELS["opus"],
                              "You are QA for client deliverables. Be strict.",
                              [{"role": "user", "content": val_prompt}],
                              max_tokens=2000, temperature=0.2)
    print(f"  Done in {time.time()-t4:.1f}s")
    val_json = extract_json(validated["content"])

    try:
        val_parsed = json.loads(val_json.strip())
        final_score = val_parsed.get("final_quality_score", "?")
        ready = val_parsed.get("ready_for_delivery", False)
        print(f"\n  FINAL SCORE: {final_score}/10")
        print(f"  READY FOR DELIVERY: {'✅ YES' if ready else '❌ NO'}")
        if not ready:
            print(f"  BLOCKING ISSUES:")
            for issue in val_parsed.get("blocking_issues", [])[:3]:
                print(f"    - {issue}")
    except:
        print("  Warning: Could not parse validation")
        val_parsed = {}

    # Save output
    output_file = f"/tmp/real_crb_{REAL_QUIZ_DATA.get('company_name', 'unknown').replace(' ', '_')}_{int(time.time())}.json"
    with open(output_file, "w") as f:
        json.dump({
            "client": REAL_QUIZ_DATA.get("company_name"),
            "timestamp": datetime.now().isoformat(),
            "phases": {
                "generation": gen["content"],
                "review": review["content"],
                "refined": refined["content"],
                "validation": validated["content"],
            },
            "quality": {
                "initial": review_parsed.get("quality_scores", {}).get("overall"),
                "final": val_parsed.get("final_quality_score"),
                "ready": val_parsed.get("ready_for_delivery"),
            }
        }, f, indent=2)

    print(f"\n{'='*70}")
    print(f"Output saved to: {output_file}")
    print(f"{'='*70}")

if __name__ == "__main__":
    run_pipeline()
PIPELINE_EOF
```

---

## How to Use with Real Data

### Option A: Copy from Supabase

```sql
SELECT quiz_responses FROM audits WHERE id = 'YOUR_AUDIT_ID';
```

Paste the JSON into `REAL_QUIZ_DATA`.

### Option B: Manual Entry

Fill in what you have. The pipeline will flag missing data.

### Option C: Test with Recent Lead

Use data from a recent intake call or form submission.

---

## Expected Output

```
REAL DATA CRB PIPELINE: Smith's Plumbing
======================================================================
Industry: home-services
Revenue: €1.5M-3M
Budget: €5,000-15,000
Started: 2025-12-25 11:30:00
======================================================================

[1/4] Generating initial analysis with Gemini 3 Pro...
  Done in 48.2s (2834 tokens)

[2/4] Expert review with Claude Opus 4.5...
  Done in 76.3s
  Initial quality: 6.2/10
  Math errors: 4
  Missing opps: 3

[3/4] Applying corrections with Claude Opus 4.5...
  Done in 82.1s

[4/4] Final validation with Claude Opus 4.5...
  Done in 28.4s

  FINAL SCORE: 8.1/10
  READY FOR DELIVERY: ✅ YES

======================================================================
Output saved to: /tmp/real_crb_Smiths_Plumbing_1766658234.json
======================================================================
```

---

## Cost Estimate

| Phase | Model | Est. Cost |
|-------|-------|-----------|
| Generation | Gemini 3 Pro | $0.03 |
| Review | Opus 4.5 | $0.10 |
| Refinement | Opus 4.5 | $0.12 |
| Validation | Opus 4.5 | $0.04 |
| **Total** | | **~$0.29** |

---

## Quality Targets

| Score | Meaning |
|-------|---------|
| < 6.0 | Not deliverable - major issues |
| 6.0-7.0 | Needs manual review before delivery |
| 7.0-8.0 | Good - minor polish recommended |
| 8.0+ | Ready for client delivery |
