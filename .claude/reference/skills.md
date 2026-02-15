# Skills System Reference

> Load this when working on skills (creating, modifying, or debugging AI-powered capabilities).

---

## Overview

Skills are modular, testable units of AI-powered logic. They replace inline prompts with structured, reusable components.

## Structure
```
backend/src/skills/
├── base.py                    # BaseSkill, LLMSkill, SyncSkill classes
├── registry.py                # Skill discovery and registration
├── analysis/                  # Finding analysis
│   ├── vendor_matching.py     # Match findings to vendors
│   ├── quick_win_identifier.py
│   └── math_validator.py      # Validate ROI calculations
├── interview/                 # Voice interview
│   └── confidence.py          # Track interview confidence
├── workshop/                  # 90-minute workshop
│   ├── question_skill.py      # Generate contextual questions
│   ├── milestone_skill.py     # Track workshop milestones
│   └── signal_detector.py     # Detect buying signals
└── report-generation/         # Report sections
    ├── exec_summary.py
    ├── finding_generation.py
    ├── three_options.py       # Generate 3 options per finding
    └── verdict.py             # Go/No-Go recommendation
```

## Creating a Skill

```python
from src.skills.base import LLMSkill

class MySkill(LLMSkill[MyOutputModel]):
    name = "my-skill"
    description = "What this skill does"

    async def execute(self, context: SkillContext) -> MyOutputModel:
        prompt = self._build_prompt(context)
        return await self._call_llm(prompt, MyOutputModel)
```

## Skill Types

| Type | Use Case |
|------|----------|
| `LLMSkill` | Needs Claude API (generation, analysis) |
| `SyncSkill` | Pure logic, no async (validators, formatters) |
| `BaseSkill` | Custom async logic (API calls, DB queries) |

## Key Patterns
- Skills return Pydantic models (type-safe outputs)
- Skills are discovered automatically via `registry.py`
- Test skills in `tests/skills/test_<skill_name>.py`

## Agent Tools (Phase Mapping)

| Phase | Tools |
|-------|-------|
| Discovery | analyze_intake_responses, map_business_processes, identify_tech_stack |
| Research | search_industry_benchmarks, search_vendor_solutions, scrape_vendor_pricing |
| Analysis | score_automation_potential, calculate_finding_impact, identify_ai_opportunities |
| Modeling | calculate_roi, compare_vendors, generate_timeline |
| Report | generate_executive_summary, generate_full_report |

### Adding a New Agent Tool
1. Define schema in `tools/schemas.py`
2. Implement in `tools/<category>_tools.py`
3. Register in `tool_registry.py` with phase mapping
4. Add unit test for tool logic
5. Update the Agent Tools table above
