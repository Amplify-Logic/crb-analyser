# AI Engine Implementation Tickets

> Generated from AGENT-3-AI-ENGINE.md gap analysis
> Date: 2025-12-17

---

## Overview

These tickets implement the full AGENT-3 spec for the AI Engine & Report Generation system. Priority is P0 (critical), P1 (high), P2 (medium), P3 (low).

**Current State:** `backend/src/services/report_service.py` (903 lines)
- Two Pillars scoring: Working
- Basic Three Options: Partially implemented
- Progress streaming: Working
- Verdict logic: Working (4 levels)
- Industry knowledge: 5 industries supported

---

## EPIC 1: Three Options Pattern (Complete Implementation)

### TICKET-001: Create OptionDetail Data Structures
**Priority:** P0
**Effort:** 2-3 hours
**File:** `backend/src/models/recommendation.py` (new)

**Current State:**
- Recommendations use inline dict structure
- Missing: `build_tools`, `skills_required`, `dev_hours_estimate`, `model_recommendation`

**Target State:**
```python
@dataclass
class OptionDetail:
    name: str                    # "Intercom AI Bot"
    vendor: str                  # "Intercom"
    approach: str                # Brief description (for custom)
    monthly_cost: Optional[int]  # Or None for custom
    implementation_weeks: int
    implementation_cost: int     # One-time
    pros: List[str]
    cons: List[str]

    # For custom solutions only
    build_tools: Optional[List[str]]       # ["Claude API", "Cursor", "Vercel"]
    skills_required: Optional[List[str]]   # ["Python", "Basic ML"]
    dev_hours_estimate: Optional[str]      # "80-120 hours"
    model_recommendation: Optional[str]    # "Claude Sonnet 4 for X"

@dataclass
class RecommendationOptions:
    off_the_shelf: OptionDetail
    best_in_class: OptionDetail
    custom_solution: OptionDetail
    our_recommendation: str  # "off_the_shelf" | "best_in_class" | "custom_solution"
    recommendation_rationale: str
```

**Acceptance Criteria:**
- [ ] Pydantic models created with validation
- [ ] Backwards compatible with existing report structure
- [ ] Unit tests for serialization/deserialization

---

### TICKET-002: Add AI Tool Recommendations Dictionary
**Priority:** P0
**Effort:** 1-2 hours
**File:** `backend/src/config/ai_tools.py` (new)

**Current State:**
- No centralized AI tool recommendation data
- Custom solutions don't suggest specific models

**Target State:**
```python
AI_TOOL_RECOMMENDATIONS = {
    "chatbot": {
        "model": "Claude Sonnet 4 (claude-sonnet-4-20250514)",
        "why": "Best balance of quality and cost for conversational AI",
        "alternatives": ["GPT-4o for lower cost", "Gemini 2.0 for multimodal"],
        "api_cost": "~$3 per 1M input tokens",
        "cursor_compatible": True
    },
    "document_processing": {
        "model": "Claude Opus 4.5",
        "why": "Best for complex document understanding",
        "alternatives": ["GPT-4 Turbo for lower cost"],
        "api_cost": "~$15 per 1M input tokens"
    },
    "code_generation": {
        "model": "Claude Sonnet 4 via Cursor",
        "why": "Cursor IDE provides best DX with Claude",
        "alternatives": ["GitHub Copilot", "Codeium"]
    },
    "data_analysis": {
        "model": "Gemini 2.5 Pro",
        "why": "2M context window for large datasets",
        "alternatives": ["Claude with pagination", "GPT-4"]
    },
    "automation": {
        "model": "Claude Haiku 3.5",
        "why": "Fast and cheap for high-volume tasks",
        "alternatives": ["GPT-4o-mini", "Gemini Flash"]
    },
    "voice_transcription": {
        "model": "Deepgram Nova-2",
        "why": "Best accuracy/cost for real-time",
        "alternatives": ["Whisper API", "AssemblyAI"]
    }
}

DEV_TOOLS = {
    "ide": "Cursor with Claude integration",
    "hosting": ["Vercel (frontend)", "Railway (backend)", "Supabase (database)"],
    "monitoring": ["Logfire", "Langfuse"],
}
```

**Acceptance Criteria:**
- [ ] Dictionary covers all common use cases from AGENT-3 spec
- [ ] Pricing data is current (verified Dec 2024)
- [ ] Exported for use in report generation

---

### TICKET-003: Enhance Recommendation Generation Prompt
**Priority:** P0
**Effort:** 3-4 hours
**File:** `backend/src/services/report_service.py`

**Current State:**
- Prompt requests three options but structure is incomplete
- Custom solutions lack specific tool recommendations
- `our_recommendation` field exists but rationale is weak

**Target State:**
- Full OptionDetail structure in prompt
- Custom solutions MUST include:
  - Specific AI model recommendation with reasoning
  - Build tools list (Cursor, Claude API, etc.)
  - Skills required
  - Dev hours estimate (range)
- Stronger rationale for recommendation choice

**Changes Required:**
1. Update `RECOMMENDATION_PROMPT` in `_generate_recommendations()`
2. Add AI_TOOL_RECOMMENDATIONS to prompt context
3. Require model-specific recommendations for custom solutions
4. Add validation that all three options are present

**Acceptance Criteria:**
- [ ] Every recommendation has complete three options
- [ ] Custom solutions always include specific AI tools
- [ ] Rationale explains why option A vs B vs C
- [ ] Output validates against OptionDetail schema

---

## EPIC 2: Build It Yourself Section

### TICKET-004: Create Build It Yourself Template
**Priority:** P1
**Effort:** 2-3 hours
**File:** `backend/src/services/report_service.py`

**Current State:**
- Custom solutions have basic "approach" field
- No structured guidance for DIY implementation

**Target State:**
```python
BUILD_IT_YOURSELF_TEMPLATE = """
## Build It Yourself: {recommendation_title}

### Recommended Stack
- **AI Model:** {model_recommendation}
- **IDE:** Cursor with Claude integration
- **Hosting:** {hosting_recommendation}
- **Database:** {database_recommendation}

### Implementation Approach
{step_by_step_approach}

### Key APIs/Services
{api_list_with_pricing}

### Skills Required
{skills_list}

### Time Estimate
- Experienced developer: {experienced_hours} hours
- Learning while building: {learning_hours} hours

### Cost Breakdown
- Development: {dev_cost_range}
- Monthly running: {monthly_cost}
- Annual total: {annual_cost}

### Resources
- Documentation: {relevant_docs}
- Tutorials: {relevant_tutorials}
- Community: {relevant_communities}
"""
```

**Acceptance Criteria:**
- [ ] Template generates for every custom solution option
- [ ] Includes specific Cursor + Claude recommendations
- [ ] Links to real documentation (Claude API, Vercel, etc.)
- [ ] Time estimates are realistic ranges

---

### TICKET-005: Add DIY Resources Database
**Priority:** P2
**Effort:** 2 hours
**File:** `backend/src/knowledge/diy_resources.json` (new)

**Current State:**
- No curated list of resources for custom builds

**Target State:**
```json
{
  "ai_documentation": {
    "claude": {
      "api_docs": "https://docs.anthropic.com",
      "cookbook": "https://github.com/anthropics/anthropic-cookbook",
      "pricing": "https://anthropic.com/pricing"
    },
    "openai": {
      "api_docs": "https://platform.openai.com/docs",
      "cookbook": "https://cookbook.openai.com"
    }
  },
  "development_tools": {
    "cursor": {
      "docs": "https://cursor.com/docs",
      "setup_guide": "..."
    }
  },
  "hosting": {
    "vercel": { ... },
    "railway": { ... },
    "supabase": { ... }
  },
  "tutorials_by_use_case": {
    "chatbot": [...],
    "document_processing": [...],
    "automation": [...]
  }
}
```

**Acceptance Criteria:**
- [ ] All links verified working
- [ ] Covers main use cases from opportunities
- [ ] Updated quarterly

---

## EPIC 3: Model Routing

### TICKET-006: Implement Model Routing Configuration
**Priority:** P1
**Effort:** 2 hours
**File:** `backend/src/config/model_routing.py` (new)

**Current State:**
- All Claude calls use `settings.DEFAULT_MODEL`
- No differentiation by task type

**Target State:**
```python
MODEL_ROUTING = {
    # Fast extraction tasks
    "parse_quiz": "claude-3-5-haiku-20241022",
    "extract_pricing": "claude-3-5-haiku-20241022",
    "validate_json": "claude-3-5-haiku-20241022",

    # Main generation (quality + speed)
    "generate_findings": "claude-sonnet-4-20250514",
    "generate_recommendations": "claude-sonnet-4-20250514",
    "generate_roadmap": "claude-sonnet-4-20250514",

    # Strategic synthesis
    "generate_verdict": "claude-sonnet-4-20250514",
    "executive_summary": "claude-sonnet-4-20250514",

    # Complex edge cases (reserve for special needs)
    "complex_analysis": "claude-opus-4-5-20250514"
}

def get_model_for_task(task: str) -> str:
    return MODEL_ROUTING.get(task, settings.DEFAULT_MODEL)
```

**Acceptance Criteria:**
- [ ] Config file with all task mappings
- [ ] Helper function to retrieve model
- [ ] Fallback to DEFAULT_MODEL if task not found

---

### TICKET-007: Apply Model Routing to Report Service
**Priority:** P1
**Effort:** 2-3 hours
**File:** `backend/src/services/report_service.py`

**Current State:**
```python
response = self.client.messages.create(
    model=settings.DEFAULT_MODEL,  # Always same model
    ...
)
```

**Target State:**
```python
from src.config.model_routing import get_model_for_task

response = self.client.messages.create(
    model=get_model_for_task("generate_findings"),
    ...
)
```

**Changes Required:**
1. Import model routing
2. Update `_generate_executive_summary()` - use "executive_summary"
3. Update `_generate_findings()` - use "generate_findings"
4. Update `_generate_recommendations()` - use "generate_recommendations"
5. Update `_generate_roadmap()` - use "generate_roadmap"
6. Add logging for model usage (for cost tracking)

**Acceptance Criteria:**
- [ ] Each generation step uses appropriate model
- [ ] Model usage logged for monitoring
- [ ] No breaking changes to output format

---

### TICKET-008: Add Token Usage Tracking
**Priority:** P2
**Effort:** 2 hours
**File:** `backend/src/services/report_service.py`

**Current State:**
- No tracking of token usage per report

**Target State:**
```python
class ReportGenerator:
    def __init__(self, ...):
        self.token_usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "by_task": {}
        }

    async def _call_claude(self, task: str, prompt: str, ...) -> str:
        model = get_model_for_task(task)
        response = self.client.messages.create(model=model, ...)

        # Track usage
        self.token_usage["input_tokens"] += response.usage.input_tokens
        self.token_usage["output_tokens"] += response.usage.output_tokens
        self.token_usage["by_task"][task] = {
            "model": model,
            "input": response.usage.input_tokens,
            "output": response.usage.output_tokens
        }
        return response.content[0].text
```

**Acceptance Criteria:**
- [ ] Token usage tracked per task
- [ ] Total usage stored with report
- [ ] Enables cost analysis per report tier

---

## EPIC 4: Finding Quality Improvements

### TICKET-009: Enhance Finding Generation with Sources
**Priority:** P1
**Effort:** 2-3 hours
**File:** `backend/src/services/report_service.py`

**Current State:**
- Prompt asks for sources but they're often generic
- No validation that sources are provided

**Target State:**
- Every finding MUST have at least one source
- Sources reference either:
  - Quiz answer: "Based on your response about X"
  - Industry benchmark: "Industry average is Y (Source: Z)"
  - Calculation: "Calculated from: [formula]"

**Changes Required:**
1. Update `FINDING_GENERATION_PROMPT` with stricter source requirements
2. Add post-processing validation
3. Inject benchmark data into prompt with source attribution

**Acceptance Criteria:**
- [ ] Every finding has minimum 1 source
- [ ] Sources are specific (not "industry benchmark")
- [ ] Validation fails if sources missing

---

### TICKET-010: Add Explicit Not-Recommended Generation
**Priority:** P1
**Effort:** 2 hours
**File:** `backend/src/services/report_service.py`

**Current State:**
- Prompt mentions "not recommended" but doesn't enforce
- No structured not_recommended items with scoring

**Target State:**
```python
# In finding generation prompt
"""
IMPORTANT: Generate at least 3 findings where you recommend NOT implementing:
- Score below 6 on either dimension
- Include clear reasoning why not
- Suggest what to do instead

Example not-recommended finding:
{
    "id": "finding-not-001",
    "title": "Full AI Customer Service Replacement",
    "category": "customer_experience",
    "customer_value_score": 3,  # LOW - customers prefer humans
    "business_health_score": 4, # LOW - high implementation risk
    "recommendation": "not_recommended",
    "why_not": "Customer satisfaction drops 40% with full AI replacement",
    "what_instead": "Implement AI-assisted human support instead"
}
"""
```

**Acceptance Criteria:**
- [ ] Minimum 3 not-recommended items per report
- [ ] Each has `why_not` and `what_instead` fields
- [ ] Scores are realistically low (not just 5s)

---

### TICKET-011: Add Confidence Scoring Logic
**Priority:** P2
**Effort:** 1-2 hours
**File:** `backend/src/services/report_service.py`

**Current State:**
- Confidence is "high/medium/low" but criteria unclear

**Target State:**
```python
CONFIDENCE_CRITERIA = """
CONFIDENCE SCORING:
- HIGH: Multiple data points support this
  - Quiz answer directly mentions this problem
  - Industry benchmark confirms the pattern
  - Calculation based on provided numbers

- MEDIUM: Reasonable inference from available data
  - Quiz answer implies this issue
  - Industry pattern applies to their profile
  - Calculation uses assumed values

- LOW: Hypothesis requiring validation
  - No direct quiz support
  - Industry pattern may not apply
  - Significant assumptions made
"""
```

**Acceptance Criteria:**
- [ ] Confidence criteria in prompt
- [ ] Post-generation validation of distribution
- [ ] At least one HIGH, some MEDIUM, few LOW per report

---

## EPIC 5: Verdict Logic Refinements

### TICKET-012: Add Industry-Specific Verdict Adjustments
**Priority:** P2
**Effort:** 2-3 hours
**File:** `backend/src/services/report_service.py`

**Current State:**
- Verdict thresholds are universal
- No industry context considered

**Target State:**
```python
INDUSTRY_VERDICT_ADJUSTMENTS = {
    "marketing-agencies": {
        "ai_readiness_boost": 5,  # Already using AI tools
        "risk_tolerance": "medium"
    },
    "retail": {
        "ai_readiness_boost": 0,
        "risk_tolerance": "low"  # More conservative
    },
    "tech-companies": {
        "ai_readiness_boost": 10,  # High baseline
        "risk_tolerance": "high"
    }
}

def _generate_verdict(self, ...):
    # Apply industry adjustment
    adjustment = INDUSTRY_VERDICT_ADJUSTMENTS.get(
        self.context.get("industry"),
        {"ai_readiness_boost": 0, "risk_tolerance": "medium"}
    )
    adjusted_score = ai_score + adjustment["ai_readiness_boost"]
    ...
```

**Acceptance Criteria:**
- [ ] Each supported industry has adjustments
- [ ] Verdicts reflect industry context
- [ ] Rationale mentions industry factors

---

### TICKET-013: Enhance Verdict Reasoning
**Priority:** P2
**Effort:** 1-2 hours
**File:** `backend/src/services/report_service.py`

**Current State:**
- Verdict reasoning is generic
- "what_to_do_instead" could be more specific

**Target State:**
- Reasoning references specific findings
- "what_to_do_instead" includes actual quick wins from industry data
- Add "estimated_time_to_ready" for wait/not_recommended verdicts

**Acceptance Criteria:**
- [ ] Reasoning cites 2-3 specific findings
- [ ] Alternatives come from industry knowledge base
- [ ] Timeline to readiness is specific

---

## EPIC 6: Progress Streaming Enhancements

### TICKET-014: Add Finding/Recommendation Previews
**Priority:** P2
**Effort:** 2-3 hours
**File:** `backend/src/services/report_service.py`

**Current State:**
```python
yield {"phase": "findings", "step": f"Generated {len(findings)} findings", "progress": 55}
```

**Target State:**
```python
# Emit each finding as discovered
for i, finding in enumerate(findings):
    yield {
        "phase": "findings",
        "step": f"Found: {finding['title']}",
        "progress": 40 + (i * 15 // len(findings)),
        "preview": {
            "title": finding["title"],
            "category": finding["category"],
            "scores": {
                "customer_value": finding["customer_value_score"],
                "business_health": finding["business_health_score"]
            }
        }
    }
```

**Acceptance Criteria:**
- [ ] Each finding emitted individually
- [ ] Preview includes key fields
- [ ] Progress updates smoothly

---

### TICKET-015: Add Error Recovery
**Priority:** P2
**Effort:** 2-3 hours
**File:** `backend/src/services/report_service.py`

**Current State:**
- Single try/catch, report fails completely

**Target State:**
- Retry logic for transient failures
- Partial report saved if late-stage failure
- Clear error categorization for frontend

```python
async def _generate_with_retry(self, task: str, generator_fn, max_retries=2):
    for attempt in range(max_retries + 1):
        try:
            return await generator_fn()
        except RateLimitError:
            if attempt < max_retries:
                await asyncio.sleep(2 ** attempt)
                continue
            raise
        except APIError as e:
            logger.error(f"API error on {task}: {e}")
            raise
```

**Acceptance Criteria:**
- [ ] Retry on rate limits
- [ ] Partial results saved
- [ ] Error types categorized

---

## EPIC 7: Testing & Validation

### TICKET-016: Add Report Validation Schema
**Priority:** P1
**Effort:** 2 hours
**File:** `backend/src/models/report_schema.py` (new)

**Current State:**
- No validation of generated report structure

**Target State:**
- Pydantic models for full report structure
- Validation that required fields present
- Type checking for all nested objects

**Acceptance Criteria:**
- [ ] Full report validates against schema
- [ ] Missing fields raise clear errors
- [ ] Schema matches frontend expectations

---

### TICKET-017: Add Report Generation Tests
**Priority:** P1
**Effort:** 3-4 hours
**File:** `backend/tests/test_report_service.py` (new)

**Current State:**
- No automated tests for report generation

**Target State:**
- Unit tests for each generation method
- Integration test for full report flow
- Mock Claude responses for deterministic testing

**Test Cases:**
1. `test_three_options_complete` - All options present
2. `test_custom_solution_has_tools` - Custom includes build tools
3. `test_sources_present` - All findings have sources
4. `test_not_recommended_included` - Min 3 not-recommended
5. `test_verdict_thresholds` - Each verdict level triggers correctly
6. `test_model_routing` - Correct model per task

**Acceptance Criteria:**
- [ ] >80% code coverage on report_service.py
- [ ] All critical paths tested
- [ ] CI pipeline runs tests

---

## Summary

| Epic | Tickets | Priority | Total Effort |
|------|---------|----------|--------------|
| Three Options Pattern | 001-003 | P0 | 6-9 hours |
| Build It Yourself | 004-005 | P1-P2 | 4-5 hours |
| Model Routing | 006-008 | P1-P2 | 6-7 hours |
| Finding Quality | 009-011 | P1-P2 | 5-7 hours |
| Verdict Refinements | 012-013 | P2 | 3-5 hours |
| Progress Streaming | 014-015 | P2 | 4-6 hours |
| Testing | 016-017 | P1 | 5-6 hours |

**Total: 17 tickets, ~33-45 hours of work**

---

## Implementation Order (Recommended)

### Phase 1: Core Structure (P0)
1. TICKET-001: OptionDetail data structures
2. TICKET-002: AI Tool Recommendations dict
3. TICKET-003: Enhanced recommendation prompt

### Phase 2: Quality (P1)
4. TICKET-009: Source citations
5. TICKET-010: Not-recommended generation
6. TICKET-006: Model routing config
7. TICKET-007: Apply model routing
8. TICKET-016: Validation schema

### Phase 3: Enhancements (P1-P2)
9. TICKET-004: Build It Yourself template
10. TICKET-017: Tests
11. TICKET-011: Confidence scoring
12. TICKET-012: Industry verdict adjustments

### Phase 4: Polish (P2)
13. TICKET-005: DIY resources
14. TICKET-008: Token tracking
15. TICKET-013: Verdict reasoning
16. TICKET-014: Preview streaming
17. TICKET-015: Error recovery
