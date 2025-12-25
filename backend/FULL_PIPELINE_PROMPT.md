# Full CRB Pipeline - All Data Sources

Run in separate Claude Code terminal.

## Data Sources (All Required)

```
┌─────────────────────────────────────────────────────────────┐
│  1. QUIZ (structured)     →  Company basics, pain points   │
│  2. RESEARCH (scraped)    →  Website, industry, context    │
│  3. INTERVIEW (AI chat)   →  Deep discovery, nuances       │
└─────────────────────────────────────────────────────────────┘
                              ↓
                         CRB REPORT
```

---

## Quick Start

```bash
cd /Users/larsmusic/CRB\ Analyser/crb-analyser/backend && source venv/bin/activate
```

```python
python - << 'EOF'
import json
import time
from datetime import datetime
import sys
sys.path.insert(0, "/Users/larsmusic/CRB Analyser/crb-analyser/backend")

from src.config.llm_client import get_llm_client
from src.config.model_routing import CLAUDE_MODELS, GEMINI_MODELS

# ============================================================================
# 1. QUIZ DATA (from quiz form)
# ============================================================================
QUIZ_DATA = {
    # BASICS
    "company_name": "",
    "website": "",
    "industry": "",  # home-services, dental, recruiting, coaching, veterinary, professional-services
    "company_size": "",  # 1-10, 11-50, 51-200
    "annual_revenue": "",
    "employee_count": "",

    # OPERATIONS (if service business)
    "technician_count": "",
    "office_staff_count": "",
    "jobs_per_day": "",
    "average_job_value": "",
    "service_area": "",

    # PAIN POINTS
    "pain_points": [],  # ["scheduling", "invoicing", "customer_communication", "lead_management"]
    "biggest_time_waste": "",
    "hours_wasted_weekly": "",

    # CURRENT TOOLS
    "current_tools": [],
    "crm_name": "",
    "fsm_software": "",

    # METRICS
    "call_volume_daily": "",
    "missed_call_percentage": "",
    "lead_response_time": "",
    "quote_to_close_rate": "",
    "payment_collection_days": "",
    "repeat_customer_rate": "",
    "review_collection": "",

    # AI READINESS
    "ai_tools_used": [],
    "technology_comfort": "",  # 1-10
    "ai_budget": "",
    "ai_goals": [],
    "timeline_preference": "",
    "team_tech_savvy": "",  # 1-10
}

# ============================================================================
# 2. RESEARCH DATA (from website scraping + industry lookup)
# ============================================================================
RESEARCH_DATA = {
    "company_profile": {
        "name": "",
        "website": "",
        "description": "",  # What they do, from their site
        "services": [],  # List of services offered
        "locations": [],  # Where they operate
        "team_size_indicator": "",  # What the website suggests
        "years_in_business": "",
        "certifications": [],
        "unique_selling_points": [],
    },
    "online_presence": {
        "google_reviews_count": "",
        "google_rating": "",
        "social_media": [],
        "website_quality": "",  # basic, professional, modern
        "has_online_booking": False,
        "has_chat_widget": False,
    },
    "industry_context": {
        "industry": "",
        "market_position": "",  # local, regional, multi-location
        "competitors_mentioned": [],
        "industry_trends": [],
    },
    "technology_signals": {
        "detected_tools": [],  # Tools found on website
        "integration_needs": [],
        "digitization_level": "",  # low, medium, high
    },
}

# ============================================================================
# 3. INTERVIEW DATA (from AI conversation)
# ============================================================================
INTERVIEW_DATA = {
    "transcript": [
        # Paste actual interview messages here
        # {"role": "assistant", "content": "..."},
        # {"role": "user", "content": "..."},
    ],
    "topics_covered": [],
    "key_quotes": [
        # Extract important quotes from the interview
        # {"topic": "pain_point", "quote": "We lose at least 5 calls a day..."},
    ],
    "summary": {
        "main_challenges": [],
        "stated_goals": [],
        "budget_signals": "",
        "urgency_level": "",  # low, medium, high
        "decision_maker": "",  # yes, needs_approval, committee
        "implementation_capacity": "",
    },
}

# ============================================================================
# VALIDATION
# ============================================================================
def validate_data():
    errors = []
    if not QUIZ_DATA.get("company_name"):
        errors.append("Missing: company_name in QUIZ_DATA")
    if not QUIZ_DATA.get("industry"):
        errors.append("Missing: industry in QUIZ_DATA")
    if not QUIZ_DATA.get("pain_points"):
        errors.append("Missing: pain_points in QUIZ_DATA")
    if not RESEARCH_DATA.get("company_profile", {}).get("description"):
        errors.append("Missing: company description in RESEARCH_DATA")
    if not INTERVIEW_DATA.get("transcript"):
        errors.append("Missing: interview transcript in INTERVIEW_DATA")

    if errors:
        print("❌ VALIDATION FAILED:")
        for e in errors:
            print(f"   - {e}")
        print("\nFill in the data above before running.")
        return False
    return True

if not validate_data():
    sys.exit(1)

# ============================================================================
# PROMPTS
# ============================================================================

SYSTEM_PROMPT = """You are an expert AI business analyst creating CRB (Cost/Risk/Benefit) reports.

You have THREE data sources:
1. QUIZ - Structured answers from the client
2. RESEARCH - Information scraped from their website + industry data
3. INTERVIEW - Natural conversation transcript with deeper insights

Your job is to synthesize ALL THREE into actionable recommendations.

Key principles:
- Quote specific sources (Quiz: "...", Research: "...", Interview: "...")
- Show all calculations with formulas
- Be conservative with estimates
- Flag where data is incomplete or contradictory
- Prioritize insights from the INTERVIEW - that's where the real pain is revealed"""


GENERATION_PROMPT = f"""Create a comprehensive CRB report from these three data sources:

═══════════════════════════════════════════════════════════════════════════════
SOURCE 1: QUIZ RESPONSES
═══════════════════════════════════════════════════════════════════════════════
{json.dumps(QUIZ_DATA, indent=2)}

═══════════════════════════════════════════════════════════════════════════════
SOURCE 2: RESEARCH (Website + Industry)
═══════════════════════════════════════════════════════════════════════════════
{json.dumps(RESEARCH_DATA, indent=2)}

═══════════════════════════════════════════════════════════════════════════════
SOURCE 3: INTERVIEW TRANSCRIPT
═══════════════════════════════════════════════════════════════════════════════
{json.dumps(INTERVIEW_DATA, indent=2)}

═══════════════════════════════════════════════════════════════════════════════
OUTPUT REQUIREMENTS
═══════════════════════════════════════════════════════════════════════════════

Generate JSON:
{{
  "executive_summary": {{
    "headline": "One compelling sentence for THIS specific company",
    "key_insight": "The most important finding (often from interview)",
    "ai_readiness_score": 0-100,
    "ai_readiness_breakdown": {{
      "technology_foundation": 0-100,
      "team_readiness": 0-100,
      "budget_alignment": 0-100,
      "process_maturity": 0-100
    }},
    "total_value_potential": {{"min": 0, "max": 0, "currency": "EUR", "confidence": "high|medium|low"}},
    "top_opportunities": [
      {{"rank": 1, "title": "...", "value": "€X-Y", "source": "Quiz|Research|Interview"}}
    ],
    "not_recommended": [
      {{"title": "...", "reason": "...", "what_instead": "...", "source": "..."}}
    ],
    "data_quality": {{
      "quiz_completeness": "high|medium|low",
      "research_depth": "high|medium|low",
      "interview_depth": "high|medium|low",
      "conflicting_data": ["List any contradictions between sources"]
    }}
  }},
  "findings": [
    {{
      "id": "finding-001",
      "title": "...",
      "category": "efficiency|growth|customer_experience|risk",
      "confidence": "high|medium|low",
      "sources_used": ["Quiz: field=value", "Research: ...", "Interview: quote"],
      "description": "...",
      "calculation": {{
        "formula": "...",
        "inputs": {{}},
        "result": "€X",
        "assumptions": []
      }},
      "value_saved": {{"annual": 0, "hours_weekly": 0}},
      "value_created": {{"annual": 0, "description": "..."}},
      "recommendation": {{
        "action": "...",
        "vendors": [{{"name": "...", "price": "€X/mo", "why": "..."}}],
        "implementation_weeks": 0,
        "fits_budget": true
      }},
      "is_not_recommended": false
    }}
  ]
}}

CRITICAL:
- Every finding must cite at least 2 sources
- Interview quotes > Quiz answers > Research data (trust hierarchy)
- If Interview contradicts Quiz, note it and trust Interview
- 8-12 findings, including 3 "not recommended"
- All € figures need calculation with formula
"""

REVIEW_PROMPT = """Review this CRB report against the original data sources.

REPORT:
{report}

ORIGINAL QUIZ:
{quiz}

ORIGINAL RESEARCH:
{research}

ORIGINAL INTERVIEW:
{interview}

Check:
1. Does every finding cite actual source data correctly?
2. Are calculations mathematically correct?
3. Are interview quotes used where they should be?
4. Are there insights from interview that were missed?
5. Do any sources contradict each other without acknowledgment?
6. Are recommendations within stated budget?

Return JSON:
{{
  "source_citation_errors": [...],
  "calculation_errors": [...],
  "missed_interview_insights": [...],
  "unacknowledged_contradictions": [...],
  "budget_violations": [...],
  "quality_scores": {{
    "source_usage": 0-10,
    "calculation_accuracy": 0-10,
    "interview_utilization": 0-10,
    "overall": 0-10
  }},
  "critical_fixes": [...],
  "summary": "..."
}}"""

REFINE_PROMPT = """Refine this CRB report based on review feedback.

ORIGINAL REPORT:
{original}

REVIEW FEEDBACK:
{review}

═══════════════════════════════════════════════════════════════════════════════
CRITICAL REFINEMENT RULES
═══════════════════════════════════════════════════════════════════════════════

1. PRESERVE ALL ORIGINAL FINDINGS
   - Do NOT drop any findings from the original report
   - Every finding (F01, F02, F03, etc.) must appear in the refined output
   - If the original has 8 findings, the refined must have at least 8

2. ADD FINDINGS FROM MISSED INSIGHTS
   - Review feedback contains "missed_interview_insights" or "unused_insights"
   - Create NEW findings from these missed insights
   - Target: 8-12 total findings (including 2-3 "not recommended")

3. FIX ALL IDENTIFIED ERRORS
   - Correct any calculation errors noted in review
   - Fix quote accuracy issues
   - Update executive summary totals to match finding sums

4. REQUIRED FINDINGS (must include):
   - Primary revenue/efficiency opportunities from interview
   - LTV impact if customer lifetime value was mentioned
   - Cash flow improvement if payment delays mentioned
   - Lead response time if speed-to-lead discussed
   - Implementation risk if tech resistance mentioned

5. EXECUTIVE SUMMARY VALIDATION
   - total_value_potential MUST equal sum of all positive findings
   - If findings sum to €346k, summary MUST reflect €346k

Return the complete, refined JSON with ALL findings preserved and new ones added."""


# ============================================================================
# PIPELINE
# ============================================================================

def safe_generate(client, model, system, messages, max_tokens, temperature, retries=3):
    for attempt in range(retries):
        try:
            return client.generate(model=model, system=system, messages=messages,
                                   max_tokens=max_tokens, temperature=temperature)
        except Exception as e:
            if attempt < retries - 1:
                print(f"  Retry {attempt+1}...")
                time.sleep(10 * (attempt + 1))
            else:
                raise

def extract_json(content):
    if "```json" in content:
        return content.split("```json")[1].split("```")[0]
    elif "```" in content:
        return content.split("```")[1].split("```")[0]
    return content

print("=" * 70)
print(f"CRB REPORT: {QUIZ_DATA.get('company_name')}")
print("=" * 70)
print(f"Industry: {QUIZ_DATA.get('industry')}")
print(f"Sources: Quiz + Research + Interview ({len(INTERVIEW_DATA.get('transcript', []))} messages)")
print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
print("=" * 70)

gemini = get_llm_client("google")
opus = get_llm_client("anthropic")

# Phase 1: Generate
print("\n[1/3] Generating with Gemini 3 Pro...")
t1 = time.time()
gen = safe_generate(gemini, GEMINI_MODELS["pro"], SYSTEM_PROMPT,
                    [{"role": "user", "content": GENERATION_PROMPT}],
                    max_tokens=8000, temperature=0.7)
print(f"  Done in {time.time()-t1:.0f}s")
gen_json = extract_json(gen["content"])

# Phase 2: Review (with FULL interview transcript)
print("\n[2/3] Reviewing with Opus 4.5 (full transcript)...")
t2 = time.time()
# CRITICAL: Include full interview transcript, not truncated
review_prompt = REVIEW_PROMPT.format(
    report=gen_json[:12000],  # Increased from 8000
    quiz=json.dumps(QUIZ_DATA),  # Full quiz
    research=json.dumps(RESEARCH_DATA)[:2000],
    interview=json.dumps(INTERVIEW_DATA)  # FULL interview - no truncation
)
review = safe_generate(opus, CLAUDE_MODELS["opus"],
                       "You are a senior analyst reviewing client deliverables. Check EVERY interview quote against the FULL transcript.",
                       [{"role": "user", "content": review_prompt}],
                       max_tokens=6000, temperature=0.3)  # Increased from 4000
print(f"  Done in {time.time()-t2:.0f}s")
review_json = extract_json(review["content"])

try:
    r = json.loads(review_json.strip())
    print(f"  Quality: {r.get('quality_scores', {}).get('overall', '?')}/10")
    print(f"  Interview utilization: {r.get('quality_scores', {}).get('interview_utilization', '?')}/10")
except:
    pass

# Phase 3: Refine (with FULL context)
print("\n[3/3] Refining with Opus 4.5...")
t3 = time.time()

# Include interview data in refinement so new findings can cite sources
REFINE_WITH_SOURCES = REFINE_PROMPT + f"""

═══════════════════════════════════════════════════════════════════════════════
ORIGINAL INTERVIEW (for adding new findings)
═══════════════════════════════════════════════════════════════════════════════
{json.dumps(INTERVIEW_DATA)}

═══════════════════════════════════════════════════════════════════════════════
ORIGINAL QUIZ (for reference)
═══════════════════════════════════════════════════════════════════════════════
{json.dumps(QUIZ_DATA)}
"""

refine = safe_generate(opus, CLAUDE_MODELS["opus"], SYSTEM_PROMPT,
                       [{"role": "user", "content": REFINE_WITH_SOURCES.format(
                           original=gen_json, review=review_json)}],
                       max_tokens=12000, temperature=0.4)  # Increased for more findings
print(f"  Done in {time.time()-t3:.0f}s")

# Validate finding count
refined_json = extract_json(refine["content"])
try:
    refined = json.loads(refined_json.strip())
    finding_count = len(refined.get("findings", []))
    print(f"  Findings: {finding_count}")
    if finding_count < 8:
        print(f"  ⚠️  WARNING: Only {finding_count} findings (target: 8-10)")
except:
    pass

# Save
output_file = f"/tmp/crb_{QUIZ_DATA.get('company_name', 'unknown').replace(' ', '_')}_{int(time.time())}.json"
with open(output_file, "w") as f:
    json.dump({
        "company": QUIZ_DATA.get("company_name"),
        "generated": gen["content"],
        "review": review["content"],
        "refined": refine["content"],
    }, f, indent=2)

# Summary
print(f"\n{'='*70}")
print(f"✅ PIPELINE COMPLETE")
print(f"{'='*70}")
total_time = time.time() - t1 + (t2 - time.time()) if 't2' in dir() else time.time() - t1
print(f"Total time: {int(time.time() - t1 + (time.time() - t2) + (time.time() - t3))}s")

try:
    r = json.loads(review_json.strip())
    refined = json.loads(refined_json.strip())
    exec_summary = refined.get("executive_summary", {})
    findings = refined.get("findings", [])

    print(f"\n📊 QUALITY SCORES (from review):")
    qs = r.get("quality_scores", {})
    print(f"   Quote accuracy:        {qs.get('quote_accuracy', '?')}/10")
    print(f"   Calculation accuracy:  {qs.get('calculation_accuracy', '?')}/10")
    print(f"   Interview coverage:    {qs.get('interview_utilization', qs.get('interview_coverage', '?'))}/10")
    print(f"   Overall:               {qs.get('overall', '?')}/10")

    print(f"\n📋 REFINED REPORT:")
    print(f"   Headline: {exec_summary.get('headline', 'N/A')[:60]}...")
    print(f"   AI Readiness: {exec_summary.get('ai_readiness_score', '?')}/100")
    print(f"   Findings: {len(findings)}")

    # Sum values
    total_saves = sum(f.get("value", {}).get("saves", 0) for f in findings)
    total_creates = sum(f.get("value", {}).get("creates", 0) for f in findings)
    print(f"   Value potential: €{total_saves + total_creates:,.0f}")

    print(f"\n   Finding breakdown:")
    for f in findings[:5]:
        saves = f.get("value", {}).get("saves", 0)
        creates = f.get("value", {}).get("creates", 0)
        conf = f.get("confidence", "?")
        print(f"   - {f.get('title', 'N/A')[:40]}: €{saves + creates:,.0f} ({conf})")
    if len(findings) > 5:
        print(f"   ... and {len(findings) - 5} more")
except Exception as e:
    print(f"Could not parse summary: {e}")

print(f"\n📁 Output: {output_file}")
print(f"{'='*70}")
EOF
```

---

## How to Get Real Data

### Option 1: Fill Quiz Yourself (5 min)
Pretend you're a client. Use a real business you know.

### Option 2: Use Existing Session
```sql
SELECT quiz_data, research_data, interview_data
FROM quiz_sessions
WHERE company_name IS NOT NULL
ORDER BY created_at DESC
LIMIT 1;
```

### Option 3: Run Full Flow
1. Go to your frontend
2. Complete quiz as test client
3. Do the AI interview
4. Copy data from Supabase

---

## Example: Realistic Test Data

```python
QUIZ_DATA = {
    "company_name": "Müller Heizung & Sanitär",
    "website": "https://mueller-heizung.de",
    "industry": "home-services",
    "company_size": "11-50",
    "annual_revenue": "€1.5M-2M",
    "employee_count": "18",
    "technician_count": "12",
    "office_staff_count": "6",
    "jobs_per_day": "12-18",
    "average_job_value": "€420",
    "service_area": "50km around Munich",
    "pain_points": ["scheduling", "customer_communication", "invoicing", "lead_management"],
    "biggest_time_waste": "Hin und her mit Kunden wegen Terminen",
    "hours_wasted_weekly": "30",
    "current_tools": ["excel", "outlook", "paper_forms", "whatsapp"],
    "crm_name": "",
    "fsm_software": "none",
    "call_volume_daily": "25-40",
    "missed_call_percentage": "20-25%",
    "lead_response_time": "same day, sometimes next day",
    "quote_to_close_rate": "50%",
    "payment_collection_days": "45-60",
    "repeat_customer_rate": "40%",
    "review_collection": "rarely",
    "ai_tools_used": ["chatgpt"],
    "technology_comfort": "6",
    "ai_budget": "€8,000-12,000",
    "ai_goals": ["reduce_admin", "faster_response", "grow_without_hiring"],
    "timeline_preference": "3-6 months",
    "team_tech_savvy": "5",
}

RESEARCH_DATA = {
    "company_profile": {
        "name": "Müller Heizung & Sanitär GmbH",
        "website": "https://mueller-heizung.de",
        "description": "Family-owned heating and plumbing company serving Munich area since 1987. Specializes in Viessmann and Vaillant installations.",
        "services": ["Heating installation", "Bathroom renovation", "Emergency repairs", "Maintenance contracts"],
        "locations": ["Munich", "Freising", "Dachau"],
        "years_in_business": "37",
        "certifications": ["Viessmann Partner", "Vaillant ProfiPartner"],
        "unique_selling_points": ["24h emergency service", "Family business", "Local expertise"],
    },
    "online_presence": {
        "google_reviews_count": "47",
        "google_rating": "4.6",
        "social_media": ["facebook"],
        "website_quality": "basic",
        "has_online_booking": False,
        "has_chat_widget": False,
    },
    "industry_context": {
        "industry": "home-services",
        "market_position": "regional",
        "competitors_mentioned": [],
        "industry_trends": ["Heat pump demand increasing", "Labor shortage"],
    },
    "technology_signals": {
        "detected_tools": [],
        "integration_needs": ["Calendar", "Invoicing", "Customer database"],
        "digitization_level": "low",
    },
}

INTERVIEW_DATA = {
    "transcript": [
        {"role": "assistant", "content": "Thanks for taking the time today. Tell me, what's the biggest operational headache you're dealing with right now?"},
        {"role": "user", "content": "Honestly, it's the phone. We miss so many calls because my office staff is already on the phone or doing paperwork. I tried to count last week - we probably missed 8-10 calls a day. That's money walking out the door."},
        {"role": "assistant", "content": "8-10 calls a day is significant. Do you know roughly what those calls could be worth?"},
        {"role": "user", "content": "Well, about half would be existing customers calling about their heating service. The other half are new inquiries. A new customer is worth maybe €2000-3000 over time with maintenance and all that. So yeah, it hurts."},
        {"role": "assistant", "content": "And when you do reach those leads, how quickly are you getting back to them?"},
        {"role": "user", "content": "Same day usually, sometimes next morning if it comes in late. But I know that's too slow. The young generation wants everything immediately. My nephew told me people expect a response in like 5 minutes now. We can't do that."},
        {"role": "assistant", "content": "What's stopping you from responding faster?"},
        {"role": "user", "content": "We're drowning in WhatsApp messages, phone calls, and the technicians calling in with questions. My office manager Marina spends half her day just coordinating who goes where. She still uses a paper calendar, can you believe it? I bought her a computer but she says Excel is too complicated."},
        {"role": "assistant", "content": "How does the scheduling actually work right now?"},
        {"role": "user", "content": "Marina writes everything in a big paper calendar. Then she calls or WhatsApps each technician in the morning with their jobs. If something changes during the day, chaos. Last week we had a technician drive 40km to a job that was cancelled. Nobody told him."},
        {"role": "assistant", "content": "That sounds frustrating. What about invoicing - how does that work?"},
        {"role": "user", "content": "Don't get me started. The technicians write the job details on paper. Sometimes I can't read their handwriting. Then Marina types it into Excel, then into our accounting software for invoices. A job from Monday might get invoiced on Friday. Some jobs, honestly, I think we forget to invoice completely."},
        {"role": "assistant", "content": "If you could fix one thing tomorrow, what would it be?"},
        {"role": "user", "content": "The phone situation. If we could just not miss calls, that would be huge. Maybe one of those AI receptionists? My friend in Stuttgart has one for his dental practice, he loves it."},
    ],
    "topics_covered": ["Current Challenges", "Team & Operations", "Technology & Tools", "Budget & Timeline"],
    "key_quotes": [
        {"topic": "missed_calls", "quote": "we probably missed 8-10 calls a day. That's money walking out the door"},
        {"topic": "lead_value", "quote": "A new customer is worth maybe €2000-3000 over time"},
        {"topic": "response_time", "quote": "people expect a response in like 5 minutes now. We can't do that"},
        {"topic": "scheduling", "quote": "Marina writes everything in a big paper calendar"},
        {"topic": "invoicing", "quote": "Some jobs, honestly, I think we forget to invoice completely"},
        {"topic": "priority", "quote": "The phone situation. If we could just not miss calls, that would be huge"},
    ],
    "summary": {
        "main_challenges": ["Missed calls", "Paper-based scheduling", "Slow invoicing", "WhatsApp chaos"],
        "stated_goals": ["Stop missing calls", "Modernize scheduling", "Invoice faster"],
        "budget_signals": "€8-12K confirmed, willing if ROI clear",
        "urgency_level": "high",
        "decision_maker": "yes (owner)",
        "implementation_capacity": "needs_hand_holding",
    },
}
```

---

## Quality Targets

| Score | Meaning |
|-------|---------|
| < 6.0 | Not deliverable |
| 6.0-7.0 | Needs human review |
| 7.0-8.0 | Good, minor polish |
| 8.0+ | Ready for client |

**Interview utilization should be 8+** - that's where the gold is.
