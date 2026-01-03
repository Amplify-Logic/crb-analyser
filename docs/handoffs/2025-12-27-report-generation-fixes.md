# Handoff: Report Generation Flow Fixes

**Date:** 2025-12-27
**Session:** Video insights analysis + report flow audit
**Status:** Ready for implementation

---

## Context

Analyzed Jordan Platten's video "My AI Business is Boring, But Makes Me $252,000/Month" for relevant insights. Key takeaway applied:

**Lead Reactivation as Universal Quick Win** - Added to 4 industries:
- `home-services/opportunities.json` - "Reactivate past customers via SMS/email campaign"
- `professional-services/opportunities.json` - "Dormant client reactivation campaign"
- `veterinary/opportunities.json` - "Reactivate lapsed patients via SMS/email campaign"
- `recruiting/opportunities.json` - "Re-engage dormant candidates in ATS"

Then audited the entire report generation flow for logic soundness and context availability.

---

## Files Analyzed

| File | Purpose |
|------|---------|
| `backend/src/services/report_service.py` | Main report generation (2400+ lines) |
| `backend/src/agents/crb_agent.py` | CRB analysis agent |
| `backend/src/services/playbook_generator.py` | Playbook generation |
| `backend/src/services/retrieval_service.py` | RAG semantic retrieval |
| `backend/src/services/review_service.py` | Multi-model validation |

---

## 5 Fixes to Implement

### Fix 1: Add RAG Similarity Threshold

**Location:** `backend/src/services/report_service.py` lines 437-443

**Problem:** Semantic retrieval returns top N results regardless of relevance. Low-similarity results pollute context.

**Fix:**
```python
# In retrieval_service.py or report_service.py where results are processed
MIN_SIMILARITY_THRESHOLD = 0.6

# Filter results after retrieval
semantic_context.vendors = [v for v in semantic_context.vendors if v.similarity >= MIN_SIMILARITY_THRESHOLD]
semantic_context.opportunities = [o for o in semantic_context.opportunities if o.similarity >= MIN_SIMILARITY_THRESHOLD]
# etc.
```

**Also consider:** Add `min_similarity` parameter to `get_relevant_context()` method.

---

### Fix 2: Verify Confidence Distribution

**Location:** `backend/src/services/report_service.py` after `_generate_findings()` (around line 489)

**Problem:** Prompt asks for 30% HIGH / 50% MEDIUM / 20% LOW but no post-validation. LLM might output 90% HIGH.

**Fix:** Add post-processing validation:
```python
def _validate_confidence_distribution(self, findings: List[Dict]) -> List[Dict]:
    """
    Ensure findings follow 30/50/20 confidence distribution.
    Adjusts if LLM was overconfident.
    """
    total = len(findings)
    if total == 0:
        return findings

    # Count current distribution
    high_count = sum(1 for f in findings if f.get("confidence", "").lower() == "high")
    medium_count = sum(1 for f in findings if f.get("confidence", "").lower() == "medium")
    low_count = sum(1 for f in findings if f.get("confidence", "").lower() == "low")

    # Target distribution
    target_high = int(total * 0.30)
    target_medium = int(total * 0.50)
    target_low = total - target_high - target_medium

    # Log if distribution is off
    if high_count > target_high * 1.5:  # Allow some tolerance
        logger.warning(
            f"Confidence distribution skewed: HIGH={high_count}/{target_high}, "
            f"MEDIUM={medium_count}/{target_medium}, LOW={low_count}/{target_low}"
        )
        # Downgrade excess HIGH to MEDIUM based on weakest sources
        # Sort by source strength, downgrade those with weaker citations
        findings = self._rebalance_confidence(findings, target_high, target_medium, target_low)

    return findings
```

**Add to flow:** Call after findings generation, before review step.

---

### Fix 3: Pass Quiz Context to Playbook Generator

**Location:** `backend/src/services/playbook_generator.py` and `report_service.py` line 659

**Problem:** Playbooks generated from recommendations only, missing:
- Team size/capability
- Budget tier
- Technical readiness
- Existing tools

**Current call:**
```python
playbooks = await self._generate_playbooks(recommendations)
```

**Fix:** Pass full context:
```python
# In _generate_playbooks method signature
async def _generate_playbooks(self, recommendations: List[Dict]) -> List[Dict[str, Any]]:
    # Extract personalization context from quiz
    answers = self.context.get("answers", {})
    company_profile = self.context.get("company_profile", {})

    personalization = {
        "team_size": answers.get("team_size", "small"),
        "technical_capability": answers.get("tech_comfort", "basic"),
        "budget_tier": self.tier,
        "existing_tools": answers.get("current_tools", []),
        "timeline_preference": answers.get("timeline", "standard"),
        "company_size": self.context.get("company_size"),
    }

    # Pass to PlaybookGenerator
    generator = PlaybookGenerator(
        client=self.client,
        tier=self.tier,
        personalization=personalization,  # NEW
    )
```

**Also update:** `PlaybookGenerator.__init__` and `generate()` to accept and use personalization context.

---

### Fix 4: Weight Interview Data Higher

**Location:** `backend/src/services/report_service.py` - finding generation prompts

**Problem:** Interview transcript is richer data (user's own words about problems) but weighted equally with quiz multiple-choice answers.

**Fix:**
1. Parse interview for explicit pain point statements
2. Mark interview-sourced insights as higher confidence
3. Update prompt to prioritize interview quotes

```python
def _extract_interview_priorities(self) -> List[Dict]:
    """Extract prioritized pain points from interview transcript."""
    interview = self.context.get("interview", {})
    transcript = interview.get("transcript", [])

    if not transcript:
        return []

    # Extract user messages only
    user_statements = [
        msg.get("content", "")
        for msg in transcript
        if msg.get("role") == "user"
    ]

    # These are direct quotes - highest confidence source
    return {
        "statements": user_statements,
        "source_type": "direct_interview",
        "confidence_boost": True,  # Findings citing these get HIGH confidence
    }
```

**Update prompt to include:**
```
INTERVIEW INSIGHTS (HIGHEST PRIORITY - User's own words):
{interview_priorities}

When a finding is supported by interview quotes, it should be HIGH confidence.
Interview statements override quiz answers if they conflict.
```

---

### Fix 5: Show Assumption Corrections in Report

**Location:** `backend/src/services/report_service.py` lines 358-366 and report output

**Problem:** User corrections are applied internally but not shown in final report. Users don't see "We adjusted X based on your feedback."

**Current:**
```python
self.context["assumption_log"] = {
    "validated_count": len(validated_assumptions),
    "corrections_applied": list(corrected_values.keys()),
    "validation_completed": bool(validated_assumptions or corrected_values)
}
# This data exists but never surfaces in report
```

**Fix:** Add to executive summary or methodology section:
```python
# In _generate_executive_summary or final report assembly
if self.context.get("assumption_log", {}).get("validation_completed"):
    corrections = self.context["corrected_values"]
    assumption_transparency = {
        "validation_completed": True,
        "corrections_applied": [
            {
                "field": key,
                "original": corrections[key].get("original"),
                "corrected": corrections[key].get("corrected"),
                "reason": corrections[key].get("reason", "User provided correction"),
            }
            for key in corrections
        ],
        "message": f"This report reflects {len(corrections)} corrections you provided during validation."
    }
    executive_summary["assumption_transparency"] = assumption_transparency
```

**Frontend:** Display this in the methodology notes or as a callout in the report.

---

## Implementation Order

1. **Fix 1: RAG Threshold** - Quick win, prevents garbage in
2. **Fix 2: Confidence Distribution** - Ensures honest reporting
3. **Fix 5: Assumption Transparency** - Trust building, user-visible
4. **Fix 4: Interview Weighting** - Quality improvement
5. **Fix 3: Playbook Context** - Most complex, touch multiple files

---

## Testing Checklist

- [ ] Generate report with low-relevance RAG results, verify they're filtered
- [ ] Generate report, verify confidence distribution is ~30/50/20
- [ ] Generate report with interview data, verify interview citations get priority
- [ ] Generate report after user validation, verify corrections shown
- [ ] Generate playbook, verify it reflects team size/budget from quiz

---

## Related Files to Check

- `backend/src/services/retrieval_service.py` - RAG implementation
- `backend/src/services/review_service.py` - Multi-model validation
- `backend/src/skills/analysis/` - Finding generation skills
- `frontend/src/components/report/` - Report display components

---

## Questions for Implementation

1. Should RAG threshold be configurable per-tier? (stricter for premium?)
2. Should confidence rebalancing log which findings were downgraded?
3. Where should assumption transparency appear in UI? (methodology section? callout?)
