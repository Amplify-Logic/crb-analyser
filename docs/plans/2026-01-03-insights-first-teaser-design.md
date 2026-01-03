# Insights-First Teaser Report Redesign

**Date:** 2026-01-03
**Status:** Draft - Awaiting Approval

## Problem Statement

The current teaser report (generated post-quiz, pre-payment) shows **specific recommendations with ROI estimates**. This creates a risk of contradiction when the full report is generated after the 90-minute workshop.

### Current Flow
```
Quiz (5-7 Qs) → Teaser (2 specific findings + ROI) → Payment → Workshop (90 min) → Full Report
                 ↑ PROBLEM: Promises specific recommendations
                            before workshop validates anything
```

### Risk Scenario
```
Teaser shows:    "Lead Follow-up Automation" as #1 recommendation (€25K ROI)
Workshop finds:  "Actually we spend 2% of time on leads, 40% on data entry"
Full Report:     "Data Integration" is #1, "Lead Follow-up" is #15
Customer:        "Why did you change your recommendation?"
```

### Root Cause
- Teaser uses Claude Haiku with limited KB data (top 5 opportunities, top 8 vendors)
- Full report uses Opus with comprehensive KB + RAG + workshop milestones
- No consistency validation between teaser and final report
- Workshop deep-dive fundamentally changes understanding of priorities

---

## Solution: Insights-First Teaser

**Principle:** Show diagnostic insights that cannot contradict, not prescriptive recommendations that might.

### New Teaser Content Model

| Category | What It Shows | Source | Can Contradict? |
|----------|---------------|--------|-----------------|
| User Reflections | "You mentioned X as a pain point" | Quiz answers (verbatim) | NO - we're quoting them |
| Industry Benchmarks | "34% of dental practices use AI for scheduling" | KB with verified source | NO - it's published data |
| Opportunity Areas | "Customer communication shows high potential" | Pain point → category mapping | LOW - direction not prescription |
| What's Next | "Workshop will validate and prioritize" | Static content | NO - it's process description |

### What We Remove

| Current Content | Why It's Risky | Replacement |
|-----------------|----------------|-------------|
| "Finding #1: Lead Follow-up Automation" | May not be #1 after workshop | Opportunity area: "Customer Communication" |
| "ROI: €25,000 - €45,000/year" | Based on unvalidated assumptions | Industry benchmark: "Practices report 25-40% time savings" |
| "Top Recommendation: Start with X" | Specific prescription pre-validation | "Workshop will identify your priority starting point" |
| Blurred findings (titles visible) | Implies these ARE the findings | "X+ opportunities to explore in full report" |

---

## New Teaser Schema

```typescript
interface TeaserReport {
  // Metadata
  generated_at: string           // ISO timestamp
  session_id: string
  company_name: string
  industry: string               // Normalized slug from KB

  // Section 1: AI Readiness Score (keep - it's diagnostic)
  ai_readiness: {
    score: number                // 0-100
    breakdown: {
      tech_maturity: ScoreComponent
      process_clarity: ScoreComponent
      data_readiness: ScoreComponent
      ai_experience: ScoreComponent
    }
    interpretation: {
      level: "Early Stage" | "Developing" | "Good" | "Excellent"
      summary: string            // General interpretation, not prescription
    }
  }

  // Section 2: Diagnostic Insights
  diagnostics: {
    // What they told us - direct reflections (cannot be wrong)
    user_reflections: Array<{
      type: "pain_point" | "goal" | "current_state"
      what_you_told_us: string   // Direct quote or paraphrase
      source: string             // "quiz_question_3", "company_website"
    }>

    // Industry data - FROM KB WITH VERIFIED SOURCES ONLY
    industry_benchmarks: Array<{
      metric: string             // "AI adoption in dental practices"
      value: string              // "34% currently use AI-powered tools"
      source: {
        name: string             // "ADA Technology Survey 2024"
        url?: string
        verified_date: string    // "YYYY-MM" format
      }
      relevance: string          // How this relates to them (factual)
    }>

    // Peer comparison (only if verified data exists)
    peer_comparison?: {
      statement: string
      source: { name: string; verified_date: string }
      confidence: "VERIFIED"     // Only display if verified
    }
  }

  // Section 3: Opportunity Areas (categories, not prescriptions)
  opportunity_areas: Array<{
    category: string             // Fixed category ID from KB
    label: string                // "Customer Communication"
    potential: "high" | "medium"
    matched_because: string      // "You mentioned patient follow-up"
    in_full_report: string[]     // What full report reveals for this area
  }>

  // Section 4: What Comes Next
  next_steps: {
    workshop: {
      what_it_is: string         // "AI-powered deep-dive conversation"
      duration: string           // "~90 minutes (can pause/resume)"
      phases: Array<{
        name: string             // "Confirmation" | "Deep-Dive" | "Synthesis"
        description: string
      }>
      outcome: string            // "Validated priorities and personalized findings"
    }
    full_report_includes: Array<{
      icon: string
      title: string
      description: string
    }>
    pricing: {
      amount: number
      currency: string
      tier_name: string
    }
  }
}

interface ScoreComponent {
  score: number
  max: number                    // Always 25
  label: string                  // "Developing" | "Established" | "Advanced"
  observation: string            // Factual observation about their input
}
```

---

## Data Sourcing Rules

### CRITICAL: No AI-Generated Industry Data

| Data Type | Source | Validation |
|-----------|--------|------------|
| User reflections | `quiz_sessions.answers` | Verbatim or close paraphrase |
| Industry benchmarks | `knowledge/{industry}/benchmarks.json` | Must have `source` + `verified_date` |
| Peer comparisons | `knowledge/{industry}/benchmarks.json` | Must have verified source |
| Opportunity categories | `knowledge/{industry}/opportunities.json` | Fixed category list |

### Validation in Code

```python
def validate_benchmark(benchmark: dict) -> bool:
    """Benchmark MUST have verified source or it gets excluded."""
    source = benchmark.get("source", {})

    # Required: source name
    if not source.get("name"):
        logger.warning(f"Excluding benchmark without source: {benchmark}")
        return False

    # Required: verification date within 18 months
    verified_date = source.get("verified_date")
    if not verified_date:
        logger.warning(f"Excluding benchmark without verified_date: {benchmark}")
        return False

    if is_stale(verified_date, months=18):
        logger.warning(f"Excluding stale benchmark: {benchmark}")
        return False

    return True

# Only include validated benchmarks
validated = [b for b in kb_benchmarks if validate_benchmark(b)]
```

### If KB Data Is Missing

If an industry doesn't have verified benchmarks in KB:

1. **Don't show that section** - better to omit than guess
2. **Show placeholder message**: "We're building industry-specific data for [industry]. Your full report will include available benchmarks."
3. **Log for KB team**: Track which industries need data population

---

## Opportunity Category Mapping

Fixed categories that pain points map to (from KB):

| Category ID | Label | Maps From Pain Points |
|-------------|-------|----------------------|
| `customer_communication` | Customer Communication | follow-up, reminders, inquiries, support |
| `document_processing` | Document & Data Handling | invoicing, data entry, forms, paperwork |
| `scheduling` | Scheduling & Coordination | appointments, calendar, booking |
| `reporting` | Reporting & Analytics | reports, dashboards, metrics |
| `sales_pipeline` | Sales & Lead Management | leads, proposals, CRM |
| `onboarding` | Client Onboarding | intake, setup, welcome |

### Mapping Logic

```python
PAIN_POINT_TO_CATEGORY = {
    # Customer Communication
    "patient follow-up": "customer_communication",
    "appointment reminders": "customer_communication",
    "client inquiries": "customer_communication",
    "email responses": "customer_communication",

    # Document Processing
    "invoicing": "document_processing",
    "data entry": "document_processing",
    "paperwork": "document_processing",
    "forms": "document_processing",

    # ... etc
}

def map_pain_points_to_categories(pain_points: list[str]) -> list[dict]:
    """Map user pain points to opportunity categories."""
    categories = {}

    for pain in pain_points:
        pain_lower = pain.lower()
        for keyword, category in PAIN_POINT_TO_CATEGORY.items():
            if keyword in pain_lower:
                if category not in categories:
                    categories[category] = {
                        "category": category,
                        "label": CATEGORY_LABELS[category],
                        "matched_because": [],
                    }
                categories[category]["matched_because"].append(pain)

    # Sort by number of matches (more matches = higher potential)
    sorted_categories = sorted(
        categories.values(),
        key=lambda c: len(c["matched_because"]),
        reverse=True
    )

    # Assign potential based on match count
    for i, cat in enumerate(sorted_categories):
        cat["potential"] = "high" if i < 2 else "medium"
        cat["matched_because"] = f"You mentioned: {', '.join(cat['matched_because'][:2])}"

    return sorted_categories[:3]  # Max 3 opportunity areas
```

---

## Frontend Changes

### Current PreviewReport.tsx Shows

```
┌─────────────────────────────────────────┐
│ AI Readiness Score: 72                  │
│ Estimated Annual Savings: €25K-€75K     │ ← REMOVE (specific estimate)
├─────────────────────────────────────────┤
│ Finding 1: Lead Follow-up Automation    │ ← REMOVE (specific rec)
│ Finding 2: Document Processing          │ ← REMOVE (specific rec)
│ [BLURRED] Finding 3                     │ ← REMOVE (implies these ARE findings)
│ [BLURRED] Finding 4                     │
├─────────────────────────────────────────┤
│ Top Recommendation: Start with...       │ ← REMOVE (prescription)
└─────────────────────────────────────────┘
```

### New PreviewReport.tsx Shows

```
┌─────────────────────────────────────────┐
│ AI Readiness Score: 72                  │
│ Level: Good - Solid foundation          │
│ ├─ Tech Maturity: 18/25                 │
│ ├─ Process Clarity: 20/25               │
│ ├─ Data Readiness: 15/25                │
│ └─ AI Experience: 19/25                 │
├─────────────────────────────────────────┤
│ WHAT YOU TOLD US                        │
│ • "Patient follow-up takes too long"    │
│ • "Using Dentrix and manual spreadsheets│
│ • "Want to reduce admin time"           │
├─────────────────────────────────────────┤
│ INDUSTRY CONTEXT                        │
│ • 34% of dental practices use AI tools  │
│   Source: ADA Survey 2024               │
│ • Practices report 25-40% admin savings │
│   Source: Dental Economics 2024         │
├─────────────────────────────────────────┤
│ HIGH-POTENTIAL AREAS                    │
│ ○ Customer Communication (high)         │
│   You mentioned: follow-up, reminders   │
│ ○ Document Handling (medium)            │
│   You mentioned: spreadsheets           │
├─────────────────────────────────────────┤
│ WHAT'S NEXT                             │
│ 1. Workshop (90 min) - Validate & dive  │
│    deep into your specific challenges   │
│ 2. Full Report - Prioritized recs with  │
│    ROI, vendors, and implementation     │
│                                         │
│ [Get Full Report - €147] [+ Call €497]  │
└─────────────────────────────────────────┘
```

---

## Backend Changes

### teaser_service.py Modifications

```python
# BEFORE: generate_teaser_report returns findings
async def generate_teaser_report(...) -> Dict[str, Any]:
    findings = await _generate_ai_findings(...)  # ← AI-generated via Haiku
    return {
        "revealed_findings": findings[:2],
        "blurred_findings": findings[2:6],
        ...
    }

# AFTER: generate_teaser_report returns insights (NO AI generation)
async def generate_teaser_report(...) -> Dict[str, Any]:
    # User reflections - verbatim from quiz
    user_reflections = _extract_user_reflections(quiz_answers)

    # Industry benchmarks - FROM SUPABASE with verified sources
    industry_benchmarks = await _get_verified_benchmarks_from_supabase(industry)

    # Opportunity areas - category mapping from Supabase opportunities
    opportunity_areas = await _map_pain_points_to_opportunity_categories(
        quiz_answers.get("pain_points", []),
        industry
    )

    return {
        "ai_readiness": score_data,
        "diagnostics": {
            "user_reflections": user_reflections,
            "industry_benchmarks": industry_benchmarks,
        },
        "opportunity_areas": opportunity_areas,
        "next_steps": _build_next_steps(pricing_tier),
    }
```

### New Functions (Query Supabase)

```python
async def _get_verified_benchmarks_from_supabase(industry: str) -> List[Dict]:
    """
    Get verified benchmarks from knowledge_embeddings table.
    Only returns benchmarks with source.name and source.verified_date.
    """
    supabase = await get_async_supabase()

    result = await supabase.table("knowledge_embeddings").select(
        "content_id, title, content, metadata"
    ).eq("content_type", "benchmark").eq("industry", industry).execute()

    verified = []
    for row in result.data or []:
        metadata = row.get("metadata", {})
        source = metadata.get("source", {})

        # STRICT: Must have verified source
        if not source.get("name") or not source.get("verified_date"):
            continue

        # STRICT: Must be fresh (within 18 months)
        if _is_stale(source["verified_date"], months=18):
            logger.warning(f"Skipping stale benchmark: {row['content_id']}")
            continue

        verified.append({
            "metric": row["title"],
            "value": metadata.get("value", row["content"]),
            "source": {
                "name": source["name"],
                "url": source.get("url"),
                "verified_date": source["verified_date"],
            },
            "relevance": metadata.get("relevance_template"),
        })

    return verified


async def _map_pain_points_to_opportunity_categories(
    pain_points: List[str],
    industry: str
) -> List[Dict]:
    """
    Map user pain points to opportunity categories from Supabase.
    Returns categories (not specific recommendations).
    """
    supabase = await get_async_supabase()

    # Get opportunities for this industry
    result = await supabase.table("knowledge_embeddings").select(
        "content_id, title, metadata"
    ).eq("content_type", "opportunity").eq("industry", industry).execute()

    # Build category map from opportunities
    categories = {}
    for row in result.data or []:
        metadata = row.get("metadata", {})
        category = metadata.get("category")
        keywords = metadata.get("keywords", [])

        if not category:
            continue

        if category not in categories:
            categories[category] = {
                "category": category,
                "label": _category_label(category),
                "keywords": keywords,
                "matched_pain_points": [],
                "in_full_report": metadata.get("in_full_report", []),
            }
        else:
            # Merge keywords
            categories[category]["keywords"].extend(keywords)

    # Match pain points to categories
    for pain in pain_points:
        pain_lower = pain.lower()
        for cat_id, cat_data in categories.items():
            for keyword in cat_data["keywords"]:
                if keyword.lower() in pain_lower:
                    if pain not in cat_data["matched_pain_points"]:
                        cat_data["matched_pain_points"].append(pain)
                    break

    # Sort by number of matches, return top 3
    matched = [c for c in categories.values() if c["matched_pain_points"]]
    matched.sort(key=lambda c: len(c["matched_pain_points"]), reverse=True)

    result = []
    for i, cat in enumerate(matched[:3]):
        result.append({
            "category": cat["category"],
            "label": cat["label"],
            "potential": "high" if i < 2 else "medium",
            "matched_because": f"You mentioned: {', '.join(cat['matched_pain_points'][:2])}",
            "in_full_report": cat["in_full_report"],
        })

    return result
```

### Remove These Functions

- `_generate_ai_findings()` - No longer needed for teaser
- `_generate_fallback_findings()` - No longer needed
- `_load_kb_context()` - Replaced by Supabase queries
- Haiku API call for finding generation - **No more LLM calls in teaser**

### Keep These Functions

- `_calculate_ai_readiness_score()` - Still diagnostic/useful (calculated from quiz inputs)
- `_get_score_interpretation()` - Keep but make less prescriptive
- `_extract_company_name()` - Still needed

---

## Prerequisites Before Implementation

### 1. KB Benchmark Data Required (Supabase)

Benchmarks are stored in the `knowledge_embeddings` table with `content_type='benchmark'`.

**Required structure in metadata JSONB:**

```sql
-- Insert benchmark into knowledge_embeddings
INSERT INTO knowledge_embeddings (
  content_type,
  content_id,
  industry,
  title,
  content,
  metadata
) VALUES (
  'benchmark',
  'dental-ai-adoption-2024',
  'dental',
  'AI Adoption in Dental Practices',
  '34% of dental practices currently use AI-powered tools for scheduling, patient communication, or administrative tasks.',
  '{
    "metric": "ai_adoption_rate",
    "value": "34%",
    "value_numeric": 34,
    "source": {
      "name": "ADA Health Policy Institute Technology Survey",
      "url": "https://ada.org/resources/research/health-policy-institute",
      "verified_date": "2024-09",
      "verified_by": "lars"
    },
    "relevance_template": "Your practice is among the {remaining}% with untapped AI potential"
  }'
);
```

**Querying benchmarks for teaser:**

```python
async def get_verified_benchmarks(industry: str) -> List[Dict]:
    """Get verified benchmarks from Supabase."""
    supabase = await get_async_supabase()

    result = await supabase.table("knowledge_embeddings").select(
        "content_id, title, content, metadata"
    ).eq(
        "content_type", "benchmark"
    ).eq(
        "industry", industry
    ).execute()

    # Filter to only include benchmarks with verified sources
    verified = []
    for row in result.data or []:
        metadata = row.get("metadata", {})
        source = metadata.get("source", {})

        # Must have source name and verified_date
        if source.get("name") and source.get("verified_date"):
            # Check freshness (within 18 months)
            if not is_stale(source["verified_date"], months=18):
                verified.append({
                    "metric": metadata.get("metric"),
                    "value": metadata.get("value"),
                    "source": source,
                    "relevance": metadata.get("relevance_template"),
                })

    return verified
```

### 2. Opportunity Categories (Supabase)

Opportunities are stored in `knowledge_embeddings` with `content_type='opportunity'`.

**Required structure in metadata JSONB:**

```sql
INSERT INTO knowledge_embeddings (
  content_type,
  content_id,
  industry,
  title,
  content,
  metadata
) VALUES (
  'opportunity',
  'dental-patient-communication',
  'dental',
  'Patient Communication Automation',
  'Automate patient follow-up, appointment reminders, and recall notifications...',
  '{
    "category": "customer_communication",
    "keywords": ["follow-up", "reminders", "recalls", "confirmations", "patient"],
    "in_full_report": [
      "Specific automation tools with pricing",
      "ROI calculation based on your patient volume",
      "Implementation timeline"
    ],
    "business_health_score": 8,
    "customer_value_score": 9
  }'
);
```

### 3. Current Data Status

Check what benchmark data exists:

```sql
-- Count benchmarks per industry
SELECT industry, COUNT(*) as benchmark_count
FROM knowledge_embeddings
WHERE content_type = 'benchmark'
  AND metadata->'source'->>'verified_date' IS NOT NULL
GROUP BY industry;
```

| Industry | Verified Benchmarks | Status |
|----------|---------------------|--------|
| dental | ? | Check Supabase |
| professional-services | ? | Check Supabase |
| home-services | ? | Check Supabase |

### 4. Data Population Task

Before implementing, run this audit:

```bash
# Check existing benchmark data
python -c "
from src.config.supabase_client import get_async_supabase
import asyncio

async def audit():
    supabase = await get_async_supabase()
    result = await supabase.table('knowledge_embeddings').select(
        'industry, content_id, metadata'
    ).eq('content_type', 'benchmark').execute()

    for row in result.data or []:
        source = row.get('metadata', {}).get('source', {})
        verified = '✓' if source.get('verified_date') else '✗'
        print(f'{verified} {row[\"industry\"]}: {row[\"content_id\"]}')
        if source.get('name'):
            print(f'   Source: {source[\"name\"]}')

asyncio.run(audit())
"
```

---

## Migration Plan

### Phase 1: Backend Changes
1. Create new teaser schema types (`TeaserReportV2`)
2. Implement `_extract_user_reflections()`
3. Implement `_get_validated_benchmarks()`
4. Implement `_map_pain_points_to_categories()`
5. Create `/sessions/{id}/teaser-v2` endpoint (parallel to existing)
6. Add tests for new functions

### Phase 2: KB Data Population
1. Research and add verified benchmarks for dental
2. Research and add verified benchmarks for professional-services
3. Research and add verified benchmarks for home-services
4. Define opportunity categories per industry

### Phase 3: Frontend Changes
1. Create `PreviewReportV2.tsx` component
2. Update UI to display new schema
3. Update `/quiz/preview` route to use new endpoint
4. A/B test if needed

### Phase 4: Deprecate Old Flow
1. Remove old teaser generation code
2. Remove Haiku API call for findings
3. Update CLAUDE.md documentation

---

## Success Criteria

1. **No contradictions**: Teaser content cannot be invalidated by workshop/report
2. **Trust maintained**: Users feel the teaser "gets them" through reflections
3. **Curiosity created**: Users want to see what the workshop reveals
4. **Data integrity**: All industry stats have verified sources
5. **Conversion maintained**: Teaser → payment rate doesn't drop

---

## Open Questions

1. **A/B test?** Should we test new teaser against old for conversion impact?
2. **Fallback for missing KB data?** What to show if industry has no benchmarks yet?
3. **Email teaser format?** Does the email teaser also need redesign?

---

## Appendix: Current vs New Comparison

### Before (Risky)
```json
{
  "revealed_findings": [
    {
      "title": "Lead Follow-up Automation",
      "category": "efficiency",
      "summary": "Automate patient follow-up...",
      "roi_estimate": {"min": 25000, "max": 45000},
      "vendor_recommendation": "HubSpot"
    }
  ],
  "blurred_findings": [
    {"title": "Invoice Processing", "blurred": true}
  ],
  "total_findings_available": 8
}
```

### After (Safe)
```json
{
  "diagnostics": {
    "user_reflections": [
      {
        "type": "pain_point",
        "what_you_told_us": "Patient follow-up takes too much time",
        "source": "quiz_question_3"
      }
    ],
    "industry_benchmarks": [
      {
        "metric": "AI adoption in dental practices",
        "value": "34% currently use AI-powered tools",
        "source": {
          "name": "ADA Technology Survey 2024",
          "verified_date": "2024-09"
        },
        "relevance": "Your practice is among the 66% with untapped potential"
      }
    ]
  },
  "opportunity_areas": [
    {
      "category": "customer_communication",
      "label": "Patient Communication",
      "potential": "high",
      "matched_because": "You mentioned: follow-up, reminders",
      "in_full_report": ["Specific tools", "Your ROI", "Implementation plan"]
    }
  ]
}
```

---

**Next Steps:** Review and approve this design, then prioritize KB data population before implementation.
