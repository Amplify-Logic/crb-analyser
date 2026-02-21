# Skills System Reference

> Load this when working on skills (creating, modifying, or debugging AI-powered capabilities).
> NOT here: API routes that call skills → `api-development.md` | report generation quality rules → `report-quality.md`

---

## Tools vs Skills vs Agents

Understanding these three concepts is essential:

| Concept | What It Is | Discovery | Example |
|---------|-----------|-----------|---------|
| **Skill** | Reusable code component that does one thing well | Auto-discovered by `registry.py` | `finding_generation.py` — generates findings from context |
| **Tool** | Agent action registered per phase (OpenAI function-calling schema) | Registered in `tool_registry.py` by phase | `search_vendor_solutions` — called by agent during research |
| **Agent** | Orchestrator that runs phases, calling tools and skills | Manually imported, hand-crafted | `CRBAgent` — runs discovery→research→analysis→modeling→report |

**How they relate:**
- An **Agent** orchestrates phases, calling **Tools** as Claude function calls
- **Tools** may internally use **Skills** for their implementation
- **Skills** are also called directly by services (e.g., `report_service.py` calls skills without going through an agent)

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
from src.skills.base import LLMSkill, SkillContext

class MySkill(LLMSkill[MyOutputModel]):
    name = "my-skill"
    description = "What this skill does"
    default_task = "generate_findings"  # Routes to correct model via model_routing.py
    default_tier = "quick"              # "quick" = Sonnet, "full" = Opus

    async def execute(self, context: SkillContext) -> MyOutputModel:
        prompt = f"Analyze {context.industry} data..."
        response = await self.call_llm_json(prompt)
        return MyOutputModel(**response)
```

### Skill Registration
Skills are auto-discovered. Place your file in a subdirectory under `backend/src/skills/`:
```
backend/src/skills/analysis/my_new_skill.py  → registered as "analysis/my_new_skill"
```

You can also register manually with the `@skill` decorator:
```python
from src.skills.registry import skill

@skill("my-custom-name")
class MySkill(LLMSkill[...]):
    ...
```

### Using Skills

```python
# Via global helpers
from src.skills.registry import get_skill, run_skill

skill = get_skill("report-generation/exec-summary", client=anthropic_client)
result = await skill.run(context)

# One-liner
result = await run_skill("analysis/vendor_matching", context, client=anthropic_client)
```

## Skill Types

| Type | Use Case | Key Methods |
|------|----------|-------------|
| `LLMSkill[T]` | Needs Claude API (generation, analysis) | `call_llm()`, `call_llm_json()` |
| `SyncSkill[T]` | Pure logic, no async (validators, formatters) | `execute_sync()` |
| `BaseSkill[T]` | Custom async logic (API calls, DB queries) | `execute()` |

All skills:
- Accept `SkillContext` (industry, company info, quiz answers, expertise, knowledge)
- Return `SkillResult` (success, data, execution_time_ms, tokens_used, warnings)
- Are type-safe via Generic[T] — return Pydantic models

## Key Patterns
- Skills return Pydantic models (type-safe outputs)
- Skills are discovered automatically via `registry.py`
- Skills are stateless — all context passed in, results passed out
- Skills can compose — one skill can call another
- Test skills in `tests/skills/test_<skill_name>.py`
- Model routing: set `default_task` and `default_tier`, never hardcode model names

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

---

## Adding a New Agent

Agents are hand-crafted orchestrators in `backend/src/agents/`. There is no base class or auto-discovery (unlike skills).

### Current Agents
| Agent | File | Purpose |
|-------|------|---------|
| `CRBAgent` | `agents/crb_agent.py` | Main 5-phase analysis (discovery → report) |
| `PreResearchAgent` | `agents/pre_research_agent.py` | Pre-analysis research |
| Research agents | `agents/research/` | Vendor discovery and refresh |

### Pattern for a New Agent
```python
class MyAgent:
    PHASES = ["phase1", "phase2"]

    def __init__(self, client: Anthropic):
        self.client = client

    async def run(self, input_data: dict) -> AsyncGenerator[dict, None]:
        for phase in self.PHASES:
            model = get_model_for_task(PHASE_TASKS[phase], tier)
            # Execute phase with tools
            yield {"phase": phase, "status": "complete", "data": result}
```

Key conventions:
- Use `get_model_for_task()` for model selection per phase
- Yield progress updates for SSE streaming
- Register tools per phase in `tool_registry.py`
- Manually import agent where needed (no registry)
