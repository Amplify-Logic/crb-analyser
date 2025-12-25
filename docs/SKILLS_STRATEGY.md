# Skills System Strategy

## Why Skills Exist

Skills are **NOT** about development workflow. They're about **production efficiency at scale**.

Every paying customer triggers report generation → API calls → costs money.

```
Customer Journey:
Quiz → Interview → Report Generation → Web UI Display
                   ↑
                   Skills run HERE (in production, per customer)
```

---

## Core Benefits

### 1. Lower Cost Per Report

| Without Skills | With Skills | Savings |
|---------------|-------------|---------|
| ~8000 tokens/report | ~4000 tokens/report | 50% |
| €0.12/report | €0.06/report | €0.06/customer |

At 1000 customers/month = €60 saved/month
At 10,000 customers/month = €600 saved/month

### 2. Consistent Quality

Every customer gets identical methodology:
- Same Two Pillars scoring logic
- Same Three Options structure
- Same confidence adjustments
- Same verdict thresholds

No quality drift from prompt variations.

### 3. Faster Generation

Skills = optimized code paths, not giant prompts to parse.
- Faster response times
- Better UX
- Fewer timeouts

### 4. Expertise Compounds

```python
# Customer 50 in dental gets benefit of customers 1-49
expertise = expertise_store.get_expertise("dental")
# Contains: common pain points, effective solutions, anti-patterns
```

Product gets smarter with each customer, automatically.

### 5. Easier Iteration

Change ROI calculation? Edit one skill file, not hunt through 1500-line services.

---

## Current Skills (Built)

### Report Generation
| Skill | Purpose | Status |
|-------|---------|--------|
| `exec-summary` | AI readiness scores, executive summary | ✅ Integrated |
| `finding-generation` | Two Pillars findings with sources | ✅ Integrated |
| `three-options` | Off-shelf/Best-in-class/Custom recs | ✅ Integrated |
| `verdict` | Go/Caution/Wait/No decision | ✅ Integrated |

### Interview
| Skill | Purpose | Status |
|-------|---------|--------|
| `followup-question` | Adaptive interview questions | ✅ Integrated |
| `pain-extraction` | Extract pain points from transcript | ✅ Integrated |

---

## Future Skills to Build

### High Priority (Direct Revenue Impact)

#### `vendor-matching`
Match findings to specific vendors from knowledge base.
```python
# Input: finding about "scheduling issues"
# Output: {
#   "off_the_shelf": {"vendor": "Calendly", "price": "€12/mo", ...},
#   "best_in_class": {"vendor": "Acuity", "price": "€25/mo", ...},
#   "custom": {"approach": "Claude API + calendar integration", ...}
# }
```
**Impact**: Better recommendations = higher customer satisfaction

#### `roi-calculator`
Standardized ROI math with transparent assumptions.
```python
# Input: finding + recommendation + company context
# Output: {
#   "roi_percentage": 180,
#   "payback_months": 4,
#   "confidence": "medium",
#   "assumptions": ["40 hrs/mo saved", "€50/hr labor cost", ...],
#   "sensitivity": {"best_case": 250, "worst_case": 120}
# }
```
**Impact**: Credible numbers = trust = conversions

#### `quick-win-identifier`
Identify low-effort, high-impact opportunities.
```python
# Input: all findings
# Output: top 3 quick wins with:
#   - implementation_hours < 20
#   - roi > 150%
#   - risk = "low"
```
**Impact**: Actionable reports = customer success stories

### Medium Priority (Quality Improvement)

#### `source-validator`
Validate claims against knowledge base, flag unverified data.
```python
# Input: finding with claims
# Output: {
#   "verified_claims": [...],
#   "unverified_claims": [...],
#   "suggested_sources": [...],
#   "confidence_adjustment": -0.15
# }
```
**Impact**: Honest reports = brand trust

#### `industry-benchmarker`
Compare company to industry benchmarks.
```python
# Input: company metrics + industry
# Output: {
#   "ai_readiness_percentile": 72,
#   "compared_to": "dental practices in Netherlands",
#   "strengths": ["tech adoption", "data quality"],
#   "gaps": ["process documentation"]
# }
```
**Impact**: Context = perceived value

#### `competitor-analyzer`
Identify what competitors are doing with AI.
```python
# Input: industry + company size
# Output: {
#   "ai_adoption_rate": "35%",
#   "common_implementations": ["chatbots", "scheduling"],
#   "leaders": ["Company X uses...", ...],
#   "risk_of_falling_behind": "medium"
# }
```
**Impact**: Urgency = faster decisions

### Lower Priority (Future Features)

#### `playbook-generator`
Generate implementation playbooks for recommendations.
```python
# Input: recommendation + option chosen
# Output: {
#   "week_1": ["Setup accounts", "Configure..."],
#   "week_2": ["Integrate with...", "Test..."],
#   "resources": ["Tutorial link", "Doc link"],
#   "success_metrics": [...]
# }
```

#### `follow-up-scheduler`
Determine optimal follow-up timing and content.
```python
# Input: report + customer engagement
# Output: {
#   "follow_up_date": "2 weeks",
#   "focus_areas": ["quick win #1 progress"],
#   "email_template": "..."
# }
```

#### `upsell-identifier`
Identify opportunities for human consulting tier.
```python
# Input: report complexity + customer signals
# Output: {
#   "upsell_recommended": true,
#   "reason": "Complex integrations need hands-on help",
#   "pitch_points": [...]
# }
```

---

## Skills by Pipeline Stage

```
┌─────────────────────────────────────────────────────────────┐
│                      CUSTOMER PIPELINE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  QUIZ STAGE                                                 │
│  └── (future) quiz-optimizer                                │
│      └── Adapt questions based on answers                   │
│                                                             │
│  INTERVIEW STAGE                                            │
│  ├── followup-question ✅                                   │
│  ├── pain-extraction ✅                                     │
│  └── (future) deep-dive-trigger                            │
│      └── Identify when to probe deeper                      │
│                                                             │
│  ANALYSIS STAGE                                             │
│  ├── finding-generation ✅                                  │
│  ├── (future) source-validator                             │
│  ├── (future) industry-benchmarker                         │
│  └── (future) competitor-analyzer                          │
│                                                             │
│  RECOMMENDATION STAGE                                       │
│  ├── three-options ✅                                       │
│  ├── (future) vendor-matching                              │
│  ├── (future) roi-calculator                               │
│  └── (future) quick-win-identifier                         │
│                                                             │
│  REPORT STAGE                                               │
│  ├── exec-summary ✅                                        │
│  ├── verdict ✅                                             │
│  └── (future) playbook-generator                           │
│                                                             │
│  POST-REPORT STAGE                                          │
│  ├── (future) follow-up-scheduler                          │
│  └── (future) upsell-identifier                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Priority

### Phase 1: ROI & Recommendations (Next)
1. `roi-calculator` - Credible numbers
2. `vendor-matching` - Specific recommendations
3. `quick-win-identifier` - Actionable outputs

### Phase 2: Quality & Trust
4. `source-validator` - Honest reporting
5. `industry-benchmarker` - Context

### Phase 3: Growth Features
6. `competitor-analyzer` - Urgency
7. `playbook-generator` - Implementation help
8. `upsell-identifier` - Revenue optimization

---

## Skill Development Pattern

```python
# 1. Create skill file
backend/src/skills/{category}/{skill_name}.py

# 2. Define output schema in docstring
"""
Output Schema:
{
    "field": "type",
    ...
}
"""

# 3. Implement with LLMSkill base class
class MySkill(LLMSkill[Dict[str, Any]]):
    name = "my-skill"
    requires_llm = True
    requires_expertise = True  # Use industry learnings

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        # Use expertise if available
        if context.expertise:
            industry_patterns = context.expertise.get("pain_points", {})

        # Call LLM with focused prompt
        result = await self.call_llm_json(prompt, system)
        return result

# 4. Add tests
backend/tests/skills/test_{skill_name}.py

# 5. Integrate into service/route
skill = get_skill("my-skill", client=self.client)
result = await skill.run(context)
```

---

## Metrics to Track

| Metric | How to Measure | Target |
|--------|---------------|--------|
| Tokens per report | Log API usage | -50% from baseline |
| Report generation time | Measure end-to-end | < 60 seconds |
| Skill success rate | `result.success` logging | > 95% |
| Expertise utilization | `result.expertise_applied` | > 80% for repeat industries |
| Customer satisfaction | Post-report survey | > 4.5/5 |

---

## Key Insight

**Skills are your consulting methodology in code.**

Once built, every customer gets the same quality analysis that would take a human consultant hours - delivered in seconds, at scale, for a fraction of the cost.

The more skills you build, the more of your expertise is codified and scalable.
