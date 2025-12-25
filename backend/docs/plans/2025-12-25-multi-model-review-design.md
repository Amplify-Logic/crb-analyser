# Multi-Model Review Pipeline Design

**Date:** 2025-12-25
**Status:** Implemented

## Overview

Adds a multi-model review and refinement step to CRB report generation to ensure:
- Quote accuracy against interview transcripts
- Calculation verification
- Grounding in first-party knowledge base data
- Scientific rigor in all claims

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    REPORT GENERATION FLOW                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Load Data                                               │
│     ├── Quiz answers                                        │
│     ├── Interview transcript (NEW)                          │
│     └── Industry knowledge                                  │
│                                                             │
│  2. Generate Findings (existing)                            │
│     └── Single Claude call                                  │
│                                                             │
│  3. Review & Refine (NEW - ReviewService)                   │
│     ├── Review with Opus                                    │
│     │   ├── Verify quotes against transcript                │
│     │   ├── Check calculations                              │
│     │   └── Identify unused insights                        │
│     │                                                       │
│     ├── Load KB Data                                        │
│     │   ├── Industry benchmarks                             │
│     │   ├── Vendor pricing                                  │
│     │   └── Expertise (past learnings)                      │
│     │                                                       │
│     └── Refine with Opus                                    │
│         ├── Fix errors                                      │
│         ├── Add missing findings                            │
│         └── Ground claims in KB data                        │
│                                                             │
│  4. Generate Recommendations (existing)                     │
│                                                             │
│  5. Generate Roadmap (existing)                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Data Source Hierarchy

```
1. INTERVIEW QUOTES     (Customer's actual words)
2. QUIZ DATA            (Customer's stated facts)
3. KNOWLEDGE BASE       (Verified industry data)
   └── expertise/       (Learnings from past reports)
   └── knowledge/vendors/   (Curated vendor pricing)
   └── knowledge/{industry} (Industry benchmarks)
4. EXTERNAL RESEARCH    (Only to fill gaps)
```

## Files Changed

| File | Change |
|------|--------|
| `src/services/review_service.py` | NEW - ReviewService class |
| `src/services/report_service.py` | Import ReviewService, load interview data, call review_and_refine |

## ReviewService Methods

- `review_and_refine()` - Main entry point
- `_review()` - Review content against sources (Opus)
- `_load_knowledge_base()` - Load benchmarks, vendors, expertise
- `_refine()` - Apply corrections and add findings (Opus)
- `_update_expertise()` - Log learnings for future

## Quality Metrics

Review phase outputs quality scores:
- `quote_accuracy`: 0-10 (are quotes exact?)
- `calculation_accuracy`: 0-10 (is math correct?)
- `interview_coverage`: 0-10 (are all insights used?)
- `source_grounding`: 0-10 (are claims verified?)
- `overall`: 0-10

## Progress Stream Updates

New phase added to SSE progress:
```json
{
  "phase": "review",
  "step": "Validated: 8/10 quality, +3 findings",
  "progress": 58,
  "quality_scores": {"overall": 8, "quote_accuracy": 9, ...}
}
```

## Error Handling

If review fails, falls back to original findings:
```python
except Exception as review_error:
    logger.warning(f"Review step failed, using original findings: {review_error}")
    yield {"phase": "review", "step": "Review skipped (using original)", "progress": 58}
```

## Performance

- Adds ~90-120s to report generation (2 Opus calls)
- Justified by quality improvement (7/10 → 8/10 in testing)
- All tiers get review (not just premium)

## Testing

Validated with German HVAC company example:
- Before: 5 findings, dropped 3 during refinement
- After: 12 findings, none dropped, 4 added from unused insights
- Quote accuracy: 9/10
- Calculation accuracy: 8/10
