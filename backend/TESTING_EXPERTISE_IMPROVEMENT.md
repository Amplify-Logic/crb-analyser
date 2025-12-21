# Testing Expertise-Driven Report Improvement

## Goal
Validate that the self-improving expertise system produces better reports for similar verticals over time.

**Hypothesis:** The 10th report in an industry should be measurably better than the 1st.

---

## What "Better" Means

### Quantitative Metrics
| Metric | How to Measure | Target |
|--------|----------------|--------|
| Pain point accuracy | % of pain points confirmed by client in interview | Increase over time |
| Recommendation relevance | % of recommendations client finds valuable | Increase over time |
| Research coverage | # of findings with high confidence | Increase over time |
| Vendor fit | % of recommended vendors client considers | Increase over time |
| Time to value | Time from intake to actionable insights | Decrease over time |

### Qualitative Indicators
- Report mentions industry-specific patterns (not generic)
- Recommendations reference "we've seen in similar companies..."
- Pain points are prioritized by frequency in industry
- Vendor recommendations match company size patterns

---

## Test Plan

### Phase 1: Establish Baseline (No Expertise)

```bash
# Clear expertise data to start fresh
rm -rf backend/src/expertise/data/industries/*
rm -rf backend/src/expertise/data/records/*
rm -f backend/src/expertise/data/vendors.json
rm -f backend/src/expertise/data/execution.json
```

**Run 1st analysis for a vertical (e.g., "marketing-agencies"):**
1. Use a real or realistic test company
2. Complete full analysis flow
3. Save the generated report as `baseline_report_1.json`
4. Record: pain points found, recommendations made, confidence levels

```bash
# Check expertise state after 1st analysis
curl http://localhost:8383/api/expertise/industry/marketing-agencies
```

### Phase 2: Build Expertise (3-5 Analyses)

**Run 4 more analyses in the same vertical:**
- Use different company sizes if possible (small, medium)
- Use different sub-niches if available
- Let the expertise accumulate

```bash
# After each analysis, check what was learned
curl http://localhost:8383/api/expertise/industry/marketing-agencies

# Expected: Growing list of pain points, recommendation patterns, vendor fits
```

### Phase 3: Compare Reports

**Run 6th analysis (same vertical):**
1. Save as `expertise_report_6.json`
2. Compare against baseline

**Comparison checklist:**

| Aspect | Baseline (Report 1) | With Expertise (Report 6) |
|--------|---------------------|---------------------------|
| Pain points listed | Generic? | Industry-specific? |
| Confidence levels | Lower? | Higher? |
| Recommendations | Generic AI advice? | "Companies like yours..." |
| Vendor suggestions | Random? | Size-appropriate? |
| Prompt content | No expertise block | Has "AGENT EXPERTISE" section |

---

## Automated Comparison Script

```python
# backend/tests/test_expertise_improvement.py

import json
from pathlib import Path

def compare_reports(baseline_path: str, improved_path: str):
    """Compare two reports for expertise-driven improvements."""

    baseline = json.loads(Path(baseline_path).read_text())
    improved = json.loads(Path(improved_path).read_text())

    results = {
        "pain_points": {
            "baseline_count": len(baseline.get("pain_points", [])),
            "improved_count": len(improved.get("pain_points", [])),
        },
        "high_confidence_findings": {
            "baseline": sum(1 for f in baseline.get("findings", []) if f.get("confidence") == "high"),
            "improved": sum(1 for f in improved.get("findings", []) if f.get("confidence") == "high"),
        },
        "recommendations": {
            "baseline_count": len(baseline.get("recommendations", [])),
            "improved_count": len(improved.get("recommendations", [])),
        },
        "industry_specific_language": {
            "baseline": _count_industry_references(baseline),
            "improved": _count_industry_references(improved),
        }
    }

    return results

def _count_industry_references(report: dict) -> int:
    """Count references to industry patterns, similar companies, etc."""
    text = json.dumps(report).lower()
    patterns = [
        "similar companies",
        "we've seen",
        "in this industry",
        "companies like yours",
        "common pattern",
        "frequently",
    ]
    return sum(text.count(p) for p in patterns)
```

---

## API Endpoints for Testing

```bash
# View all expertise
GET /api/expertise/

# Industry-specific expertise
GET /api/expertise/industry/{industry-slug}

# All industries summary
GET /api/expertise/industries

# Vendor patterns
GET /api/expertise/vendors

# Execution stats (tool success rates)
GET /api/expertise/execution
```

---

## What to Look For in the Prompts

After expertise builds, the discovery prompt should include:

```
═══════════════════════════════════════════════════════════════
AGENT EXPERTISE (learned from 5 prior analyses)
Confidence level: medium
═══════════════════════════════════════════════════════════════

COMMON PAIN POINTS in marketing-agencies (from prior analyses):
[{"pain_point": "Manual client reporting", "seen_in": "4 analyses"}]
[{"pain_point": "Project tracking chaos", "seen_in": "3 analyses"}]

INSIGHTS for small companies in this industry:
- Analyzed: 3 similar companies
- Average AI readiness: 58
- Common pain points: client communication, scope creep

EFFECTIVE RECOMMENDATIONS we've made for similar companies:
[{"pattern": "For small marketing-agencies", "recommendation": "Automated reporting dashboards"}]
```

**If this block is missing or empty → expertise not being injected**

---

## Test Scenarios

### Scenario A: Same Industry, Different Size
1. Run 3 analyses for "small" marketing agencies
2. Run 1 analysis for "medium" marketing agency
3. Check: Does the medium company report benefit from small company learnings?
4. Check: Are size-specific insights separated?

### Scenario B: Similar Industries
1. Build expertise in "marketing-agencies"
2. Run analysis for "creative-agencies"
3. Check: Is there any cross-pollination? (Currently: No, industries are separate)
4. Future: Consider industry similarity mapping

### Scenario C: Tool Reliability Learning
1. Run analyses where certain tools fail
2. Check: Does execution expertise track failure rates?
3. Check: Does agent adapt tool usage based on reliability?

```bash
# Check tool reliability tracking
curl http://localhost:8383/api/expertise/execution
```

---

## Success Criteria

The expertise system is working if:

1. **Expertise accumulates**: `/api/expertise/industry/{x}` shows growing data
2. **Prompts include expertise**: Discovery prompts have "AGENT EXPERTISE" block
3. **Reports improve measurably**: Higher confidence, more specific recommendations
4. **Industry patterns emerge**: Common pain points have frequency counts
5. **Vendor patterns form**: Recommendations match company size patterns

---

## Logging & Debugging

Enable debug logging to see expertise in action:

```python
# In crb_agent.py or expertise modules
import logging
logging.getLogger("src.expertise").setLevel(logging.DEBUG)
```

Check logs for:
- "Loading expertise for {industry}"
- "Injecting expertise into prompt"
- "Learning from analysis {audit_id}"
- "Updated industry expertise: {changes}"

---

## Next Steps After Validation

1. **If working**: Run real analyses, let expertise build organically
2. **If not improving**: Check prompt injection, expertise loading
3. **If data not saving**: Check file permissions, atomic write logic
4. **Future enhancement**: Add feedback loop from client interviews to validate accuracy
