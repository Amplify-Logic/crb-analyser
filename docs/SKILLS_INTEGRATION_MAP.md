# Skills Integration Map

> How to integrate the Skills layer with existing CRB Analyser code.

## Overview

This document maps every integration point between the new Skills system and existing services.

---

## Integration Points

### 1. Report Service (`report_service.py`)

**Current Location:** `backend/src/services/report_service.py`

| Method | Line | Current Approach | Skills Integration |
|--------|------|------------------|-------------------|
| `_generate_executive_summary()` | ~621 | Prompt from scratch | Use `ExecSummarySkill` |
| `_generate_findings()` | ~696 | Prompt from scratch | Use `FindingGenerationSkill` |
| `_generate_recommendations()` | ~800+ | Prompt from scratch | Use `ThreeOptionsSkill` |
| `_generate_verdict()` | ~1100+ | Logic in method | Use `VerdictSkill` |
| `_generate_roadmap()` | ~1200+ | Prompt from scratch | Use `RoadmapSkill` |

#### Example Integration

**Before:**
```python
async def _generate_executive_summary(self) -> Dict[str, Any]:
    answers = self.context.get("answers", {})
    prompt = f"""Based on the following quiz responses..."""
    content = self._call_claude("generate_executive_summary", prompt)
    return safe_parse_json(content, default_summary)
```

**After:**
```python
from src.skills import get_skill, SkillContext
from src.expertise import get_expertise_store

async def _generate_executive_summary(self) -> Dict[str, Any]:
    # Load expertise (Layer 2)
    expertise = get_expertise_store().get_all_expertise_context(self.context["industry"])

    # Build skill context
    context = SkillContext(
        industry=self.context["industry"],
        quiz_answers=self.context.get("answers", {}),
        interview_data=self.context.get("interview_data"),
        expertise=expertise,
    )

    # Execute skill (Layer 3)
    skill = get_skill("report-generation/exec-summary", client=self.client)
    result = await skill.run(context)

    if result.success:
        return result.data
    else:
        # Fallback to default
        logger.warning(f"Skill failed: {result.warnings}")
        return self._get_default_summary()
```

---

### 2. Interview Routes (`interview.py`)

**Current Location:** `backend/src/routes/interview.py`

| Endpoint | Current Approach | Skills Integration |
|----------|------------------|-------------------|
| `respond()` | Static topic questions | Use `InterviewFollowupSkill` |
| `get_next_question()` | Predefined list | Use `AdaptiveQuestionSkill` |

#### Example Integration

**Before:**
```python
def get_next_question(context: InterviewContext) -> tuple:
    topics_covered = context.topics_covered or ["introduction"]
    # Static logic to pick next topic
    ...
```

**After:**
```python
from src.skills import get_skill, SkillContext
from src.expertise import get_expertise_store

async def get_next_question(context: InterviewContext, industry: str) -> tuple:
    # Load expertise for industry-specific probing
    expertise = get_expertise_store().get_industry_expertise(industry)

    skill_context = SkillContext(
        industry=industry,
        interview_data={
            "topics_covered": context.topics_covered,
            "messages": context.previous_messages,
        },
        expertise={"industry_expertise": expertise.model_dump()},
    )

    skill = get_skill("interview/followup")
    result = await skill.run(skill_context)

    if result.success:
        return (result.data["question"], result.data["topics"], result.data["progress"])
    else:
        # Fallback to original static logic
        return _static_next_question(context)
```

---

### 3. Playbook Generator (`playbook_generator.py`)

**Current Location:** `backend/src/services/playbook_generator.py`

| Method | Skills Integration |
|--------|-------------------|
| `generate_playbook()` | Use `PlaybookGenerationSkill` |
| Task generation | Use `TaskStructureSkill` |

---

### 4. Chart Service (`chart_service.py`)

| Method | Skills Integration |
|--------|-------------------|
| Chart data generation | Use `ChartDataSkill` for consistent formatting |
| ROI calculations | Use `ROICalculationSkill` with confidence adjustment |

---

### 5. PDF Generator (`pdf_generator.py`)

| Method | Skills Integration |
|--------|-------------------|
| Layout generation | Use `PDFLayoutSkill` for consistent templates |
| Section formatting | Use individual section skills |

---

## Skills to Build (Priority Order)

### Phase 1: Report Core (High Impact)
1. ✅ `ExecSummarySkill` - DONE
2. `ThreeOptionsSkill` - Format recommendations
3. `FindingGenerationSkill` - Consistent finding structure
4. `VerdictSkill` - Go/Caution/Wait/No generation

### Phase 2: Analysis Enhancement
5. `ConfidenceScoringSkill` - Assign confidence levels
6. `ROICalculationSkill` - Confidence-adjusted ROI
7. `IndustryAnalysisSkill` - Per-industry patterns

### Phase 3: Interview/Intake
8. `InterviewFollowupSkill` - Adaptive follow-ups
9. `PainExtractionSkill` - Extract pain points
10. `QuizOptimizationSkill` - Question selection

### Phase 4: Output Polish
11. `PDFLayoutSkill` - Professional PDF templates
12. `ChartDataSkill` - Consistent chart formatting
13. `PlaybookGenerationSkill` - Week-by-week playbooks

---

## Integration Pattern

Every integration should follow this pattern:

```python
from src.skills import get_skill, SkillContext
from src.expertise import get_expertise_store

async def some_generation_method(self):
    # 1. Load expertise (Layer 2)
    expertise = get_expertise_store().get_all_expertise_context(industry)

    # 2. Build context with all needed data
    context = SkillContext(
        industry=industry,
        quiz_answers=answers,
        expertise=expertise,
        # Add other relevant data
    )

    # 3. Get and run skill (Layer 3)
    skill = get_skill("skill-name", client=self.client)
    result = await skill.run(context)

    # 4. Handle result with fallback
    if result.success:
        return result.data
    else:
        logger.warning(f"Skill failed: {result.warnings}")
        return fallback_result
```

---

## Testing Skills

Each skill should have tests in `backend/tests/skills/`:

```python
# tests/skills/test_exec_summary.py

import pytest
from src.skills import SkillContext
from src.skills.report_generation import ExecSummarySkill

@pytest.mark.asyncio
async def test_exec_summary_basic():
    skill = ExecSummarySkill(client=mock_client)

    context = SkillContext(
        industry="dental",
        quiz_answers={"company_size": "10-50", "main_challenge": "scheduling"},
    )

    result = await skill.run(context)

    assert result.success
    assert "ai_readiness_score" in result.data
    assert 0 <= result.data["ai_readiness_score"] <= 100

@pytest.mark.asyncio
async def test_exec_summary_with_expertise():
    skill = ExecSummarySkill(client=mock_client)

    context = SkillContext(
        industry="dental",
        quiz_answers={"company_size": "10-50"},
        expertise={
            "industry_expertise": {
                "total_analyses": 25,
                "confidence": "high",
                "avg_ai_readiness": 65,
            }
        },
    )

    result = await skill.run(context)

    assert result.success
    assert result.expertise_applied
```

---

## Gradual Migration

Skills can be integrated gradually:

1. **Week 1:** Integrate `ExecSummarySkill` into `report_service.py`
2. **Week 2:** Add `ThreeOptionsSkill` and `FindingGenerationSkill`
3. **Week 3:** Add interview skills
4. **Week 4:** Add remaining skills

Each integration:
- Keeps original code as fallback
- Logs skill usage and fallback events
- Measures token reduction

---

## Metrics to Track

After integration, track:

| Metric | How to Measure |
|--------|----------------|
| Token usage per report | TokenTracker before/after |
| Report consistency | Manual review of output variance |
| Generation time | Timing logs |
| Fallback rate | Log when skills fail |
| Expertise utilization | Track `expertise_applied` in results |

---

## Related Documents

- [ARCHITECTURE.md](ARCHITECTURE.md) - Full system architecture
- [CLAUDE.md](../CLAUDE.md) - Development guide
