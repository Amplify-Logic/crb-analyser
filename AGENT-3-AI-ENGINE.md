# AGENT 3: AI Engine & Report Generation

> **Mission:** Generate reports so valuable that customers feel guilty paying only €147. Every claim sourced, every ROI calculation transparent, every recommendation actionable with three clear paths.

---

## Context

**Product:** CRB Analyser - AI-powered Cost/Risk/Benefit analysis
**Core Differentiator vs ChatGPT:**
1. Structured methodology (Two Pillars: Customer Value + Business Health)
2. Three Options pattern (Off-the-shelf, Best-in-class, Custom)
3. Honest verdicts (tell them NO when appropriate)
4. Real vendor pricing (not hallucinated)
5. Transparent ROI (show all assumptions)

**Models Available:**
- Claude Opus 4.5 (`claude-opus-4-5-20241022`) - Strategic synthesis, complex reasoning
- Claude Sonnet 4 (`claude-sonnet-4-20250514`) - Balanced quality/speed
- Claude Haiku 3.5 (`claude-3-5-haiku-20241022`) - Fast extraction, simple tasks

---

## Current State

```
backend/src/services/report_service.py
├── ReportService class
├── generate_full_report() - Main generation
├── _generate_findings() - AI findings
├── _generate_recommendations() - AI recommendations
├── _generate_verdict() - Go/Wait/No verdict
└── _calculate_value_summary() - ROI math
```

**What Works:**
- Basic report generation with Claude
- Two Pillars scoring (Customer Value + Business Health)
- Verdict generation
- Value calculations

**What Needs Work:**
- Three Options pattern not implemented
- "Build it yourself" section missing
- Tool recommendations for custom builds missing
- Progress streaming not integrated
- Recommendation quality varies
- Sources not always cited
- Assumptions not always explicit

---

## Target State

### 1. The Two Pillars Framework

Every finding and recommendation is scored on two dimensions:

```
CUSTOMER VALUE (1-10)
"How much does this help your customers?"
- Direct customer benefit
- Customer experience improvement
- Customer retention impact
- Revenue from customer satisfaction

BUSINESS HEALTH (1-10)
"How much does this strengthen your business?"
- Operational efficiency
- Cost reduction
- Risk mitigation
- Scalability
- Team productivity
```

**Scoring Guidelines for AI:**
```python
SCORING_RUBRIC = """
CUSTOMER VALUE SCORING:
- 9-10: Direct, measurable customer benefit (faster response, better quality, lower prices)
- 7-8: Indirect customer benefit (more capacity to serve, fewer errors)
- 5-6: Marginal customer impact (internal efficiency that may improve service)
- 3-4: No customer impact, purely internal
- 1-2: Could negatively impact customer experience

BUSINESS HEALTH SCORING:
- 9-10: Major cost reduction OR revenue increase OR risk elimination
- 7-8: Significant efficiency gain OR moderate cost/risk impact
- 5-6: Helpful optimization with measurable but modest impact
- 3-4: Nice-to-have, minimal measurable impact
- 1-2: Questionable ROI, high risk, or resource drain
"""
```

### 2. The Three Options Pattern

**EVERY recommendation must include three paths:**

```python
class RecommendationOptions:
    """Structure for Three Options pattern."""

    off_the_shelf: OptionDetail
    """
    - Pre-built SaaS solution
    - Fastest to implement
    - Lowest upfront cost
    - Limited customization
    Example: "Use Intercom's AI bot"
    """

    best_in_class: OptionDetail
    """
    - Premium/enterprise solution
    - More features, better support
    - Higher cost
    - Industry-leading capabilities
    Example: "Zendesk Suite + Ultimate.ai"
    """

    custom_solution: OptionDetail
    """
    - Build with AI/APIs
    - Perfect fit for business
    - Highest upfront cost
    - Competitive advantage potential
    Example: "Custom chatbot with Claude API"
    """

    our_recommendation: str  # "off_the_shelf" | "best_in_class" | "custom_solution"
    recommendation_rationale: str  # Why we recommend this option
```

**Option Detail Structure:**
```python
@dataclass
class OptionDetail:
    name: str                    # "Intercom AI Bot"
    vendor: str                  # "Intercom"
    approach: str                # Brief description for custom
    monthly_cost: int            # Or None for custom
    implementation_weeks: int
    implementation_cost: int     # One-time
    pros: list[str]
    cons: list[str]

    # For custom solutions only
    build_tools: list[str]       # ["Claude API", "Cursor", "Vercel"]
    skills_required: list[str]   # ["Python", "Basic ML"]
    dev_hours_estimate: str      # "80-120 hours"
```

### 3. Build It Yourself Section

For EVERY custom solution option, include actionable guidance:

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

**AI Tool Recommendations:**
```python
AI_TOOL_RECOMMENDATIONS = {
    "chatbot": {
        "model": "Claude Sonnet 4 (claude-sonnet-4-20250514)",
        "why": "Best balance of quality and cost for conversational AI",
        "alternatives": ["GPT-4o for lower cost", "Gemini 2.0 for multimodal"]
    },
    "document_processing": {
        "model": "Claude Opus 4.5 (claude-opus-4-5-20250514)",
        "why": "Best for complex document understanding and extraction",
        "alternatives": ["GPT-4 Turbo for lower cost"]
    },
    "code_generation": {
        "model": "Claude Sonnet 4 via Cursor",
        "why": "Cursor IDE provides best developer experience with Claude",
        "alternatives": ["GitHub Copilot", "Codeium"]
    },
    "data_analysis": {
        "model": "Gemini 2.5 Pro",
        "why": "2M context window for large datasets",
        "alternatives": ["Claude with pagination", "GPT-4 for smaller datasets"]
    },
    "automation": {
        "model": "Claude Haiku 3.5",
        "why": "Fast and cheap for high-volume automation tasks",
        "alternatives": ["GPT-4o-mini", "Gemini Flash"]
    }
}
```

### 4. Verdict Logic

```python
def generate_verdict(
    ai_readiness_score: int,
    customer_value_avg: float,
    business_health_avg: float,
    total_value_potential: int,
    high_risk_count: int,
    budget_range: str
) -> Verdict:
    """
    Generate honest verdict based on analysis.

    Verdicts:
    - proceed: Strong case, clear ROI, manageable risk
    - proceed_cautiously: Good potential but significant considerations
    - wait: Not ready yet, specific blockers identified
    - not_recommended: Poor fit, high risk, or negative ROI
    """

    # NOT RECOMMENDED: Clear red flags
    if ai_readiness_score < 35:
        return Verdict(
            recommendation="not_recommended",
            headline="Focus on Foundations First",
            subheadline="AI implementation would be premature",
            color="gray",
            reasoning=[
                f"AI readiness score of {ai_readiness_score} indicates significant gaps",
                "Data infrastructure needs strengthening before AI can add value",
                "Risk of failed implementation is high at current maturity"
            ],
            what_to_do_instead=[
                "Consolidate your core business systems",
                "Implement basic automation (Zapier, Make) first",
                "Build data collection practices",
                "Revisit AI in 6-12 months"
            ],
            when_to_revisit="6-12 months after addressing foundation gaps"
        )

    # WAIT: Significant blockers
    if ai_readiness_score < 50 or high_risk_count >= 5:
        return Verdict(
            recommendation="wait",
            headline="Good Potential, But Not Yet",
            subheadline="Address key blockers before proceeding",
            color="orange",
            reasoning=[...],
            what_to_do_instead=[...],
            when_to_revisit="3-6 months after addressing blockers"
        )

    # PROCEED CAUTIOUSLY: Mixed signals
    if ai_readiness_score < 70 or customer_value_avg < 6 or business_health_avg < 6:
        return Verdict(
            recommendation="proceed_cautiously",
            headline="Proceed with Focused Approach",
            subheadline="Start small, measure, then expand",
            color="yellow",
            reasoning=[...],
            recommended_approach=[
                "Start with 1-2 highest-ROI recommendations only",
                "Set clear success metrics before implementation",
                "Plan for 3-month pilot before full rollout"
            ],
            when_to_revisit="Quarterly check-ins to assess progress"
        )

    # PROCEED: Strong case
    return Verdict(
        recommendation="proceed",
        headline="Go For It - AI Will Accelerate Your Business",
        subheadline="Strong fundamentals, clear opportunity",
        color="green",
        reasoning=[
            f"AI readiness score of {ai_readiness_score} puts you in the top tier",
            f"Projected 3-year value of €{total_value_potential:,}",
            f"Average ROI of {avg_roi}% across recommendations"
        ],
        recommended_approach=[
            "Implement top 2-3 recommendations in parallel",
            "Assign internal AI champion to drive adoption",
            "Measure ROI monthly and share wins with team"
        ],
        when_to_revisit="Quarterly to assess progress and plan next phase"
    )
```

### 5. Report Generation Pipeline

```python
async def generate_report_with_progress(
    quiz_session: QuizSession,
    progress_callback: Callable
) -> Report:
    """
    Full report generation with progress updates.

    Yields progress events for SSE streaming.
    """

    # Phase 1: Parse & Understand (10%)
    await progress_callback({"step": "parsing", "percent": 10})
    business_context = await parse_quiz_responses(quiz_session.answers)

    # Phase 2: Industry Research (20%)
    await progress_callback({"step": "benchmarks", "percent": 20})
    benchmarks = await get_industry_benchmarks(
        industry=business_context.industry,
        company_size=business_context.size
    )

    # Phase 3: Identify Opportunities (35%)
    await progress_callback({"step": "opportunities", "percent": 35})
    findings = await generate_findings(
        context=business_context,
        benchmarks=benchmarks,
        target_count=15
    )
    for finding in findings:
        await progress_callback({
            "step": "finding",
            "data": {"title": finding.title, "category": finding.category}
        })

    # Phase 4: Research Vendors (50%)
    await progress_callback({"step": "vendors", "percent": 50})
    vendor_options = await research_vendor_options(findings)

    # Phase 5: Calculate ROI (65%)
    await progress_callback({"step": "roi", "percent": 65})
    for finding in findings:
        finding.roi = await calculate_roi(finding, business_context)

    # Phase 6: Generate Recommendations (80%)
    await progress_callback({"step": "recommendations", "percent": 80})
    recommendations = await generate_recommendations(
        findings=findings,
        vendor_options=vendor_options,
        budget=business_context.budget_range
    )
    for rec in recommendations:
        await progress_callback({
            "step": "recommendation",
            "data": {"title": rec.title, "roi": rec.roi_percentage}
        })

    # Phase 7: Build Roadmap (90%)
    await progress_callback({"step": "roadmap", "percent": 90})
    roadmap = await generate_roadmap(recommendations)

    # Phase 8: Generate Verdict & Finalize (95%)
    await progress_callback({"step": "finalizing", "percent": 95})
    verdict = generate_verdict(
        ai_readiness_score=calculate_ai_readiness(business_context, findings),
        customer_value_avg=avg([f.customer_value_score for f in findings]),
        business_health_avg=avg([f.business_health_score for f in findings]),
        total_value_potential=sum_value_potential(recommendations),
        high_risk_count=count_high_risks(recommendations),
        budget_range=business_context.budget_range
    )

    # Complete
    await progress_callback({"step": "complete", "percent": 100})

    return Report(
        executive_summary={
            "verdict": verdict,
            "key_insight": generate_key_insight(business_context, findings),
            "ai_readiness_score": ai_readiness_score,
            "customer_value_score": int(customer_value_avg),
            "business_health_score": int(business_health_avg),
            "top_opportunities": get_top_opportunities(recommendations),
            "not_recommended": get_not_recommended(findings),
            "total_value_potential": calculate_total_value(recommendations),
            "recommended_investment": calculate_recommended_investment(recommendations)
        },
        findings=findings,
        recommendations=recommendations,
        roadmap=roadmap,
        methodology_notes=METHODOLOGY_NOTES
    )
```

### 6. Finding Generation Prompt

```python
FINDING_GENERATION_PROMPT = """
You are a senior AI consultant analyzing a business for AI implementation opportunities.

## Business Context
{business_context}

## Industry Benchmarks
{benchmarks}

## Your Task
Generate {target_count} findings - specific, actionable AI/automation opportunities for this business.

## Two Pillars Scoring
For EACH finding, score on two dimensions (1-10):

CUSTOMER VALUE: How much does this help their customers?
- 9-10: Direct, measurable customer benefit
- 7-8: Indirect customer benefit
- 5-6: Marginal customer impact
- 3-4: No customer impact
- 1-2: Could hurt customer experience

BUSINESS HEALTH: How much does this strengthen their business?
- 9-10: Major cost/revenue/risk impact
- 7-8: Significant efficiency gain
- 5-6: Helpful optimization
- 3-4: Nice-to-have
- 1-2: Questionable ROI

## Finding Categories
- efficiency: Time/cost savings through automation
- growth: Revenue increase opportunities
- risk: Risk reduction through AI
- customer_experience: Direct customer-facing improvements

## Output Format (JSON)
{
  "findings": [
    {
      "id": "finding-001",
      "category": "efficiency",
      "title": "Specific, actionable title",
      "description": "What this opportunity is and why it matters",
      "current_state": "How they're doing it now (based on intake)",
      "customer_value_score": 8,
      "business_health_score": 9,
      "confidence": "high|medium|low",
      "time_horizon": "short|mid|long",
      "value_saved": {
        "hours_per_week": 10,
        "hourly_rate": 50,
        "annual_savings": 26000
      },
      "value_created": {
        "description": "What new value this creates",
        "potential_revenue": 50000
      },
      "sources": ["Industry benchmark source", "Their intake response reference"]
    }
  ]
}

## Critical Requirements
1. Every finding must be SPECIFIC to this business (not generic)
2. Every finding must cite evidence from their intake OR industry benchmarks
3. Scores must be justified (don't just give everything 8s)
4. Include at least 3 findings where you recommend NOT implementing (low scores)
5. Time horizons: short (0-3mo), mid (3-12mo), long (12mo+)
"""
```

### 7. Recommendation Generation Prompt

```python
RECOMMENDATION_PROMPT = """
You are a senior AI consultant creating implementation recommendations.

## Finding to Address
{finding}

## Available Vendor Options
{vendor_options}

## Business Context
- Budget: {budget_range}
- Tech comfort: {tech_comfort}/5
- Team size: {team_size}
- Timeline preference: {timeline}

## Your Task
Create a recommendation with THREE OPTIONS:

### Option A: Off-the-Shelf
- Fastest, cheapest to start
- Use existing SaaS tools
- Limited customization

### Option B: Best-in-Class
- Premium solution
- More features, better support
- Higher cost

### Option C: Custom Solution
- Build with AI/APIs
- Perfect fit for their needs
- Higher upfront investment
- Include specific tools: Cursor, Claude API, etc.

## Output Format (JSON)
{
  "id": "rec-001",
  "finding_id": "finding-001",
  "title": "Actionable recommendation title",
  "description": "What we recommend and why",
  "priority": "high|medium|low",
  "options": {
    "off_the_shelf": {
      "name": "Product Name",
      "vendor": "Vendor Name",
      "monthly_cost": 99,
      "implementation_weeks": 2,
      "implementation_cost": 500,
      "pros": ["Quick to deploy", "Proven solution"],
      "cons": ["Limited customization", "Vendor lock-in"]
    },
    "best_in_class": {
      "name": "Premium Product",
      "vendor": "Premium Vendor",
      "monthly_cost": 299,
      "implementation_weeks": 6,
      "implementation_cost": 3000,
      "pros": ["Full features", "Great support"],
      "cons": ["Higher cost", "Longer setup"]
    },
    "custom_solution": {
      "approach": "Build custom solution using...",
      "build_tools": ["Claude API", "Cursor IDE", "Vercel"],
      "model_recommendation": "Claude Sonnet 4 for X because Y",
      "skills_required": ["Python", "Basic API integration"],
      "dev_hours_estimate": "40-60 hours",
      "estimated_cost": {"min": 5000, "max": 10000},
      "monthly_running_cost": 100,
      "pros": ["Perfect fit", "Competitive advantage", "Full control"],
      "cons": ["Longer to build", "Needs maintenance"]
    }
  },
  "our_recommendation": "off_the_shelf",
  "recommendation_rationale": "Given your budget and timeline, starting with X makes sense. Graduate to custom once you've validated the approach.",
  "crb_analysis": {
    "cost": {
      "short_term": {"implementation": 500, "software": 297, "training": 200},
      "mid_term": {"software": 1188, "maintenance": 300},
      "long_term": {"software": 2376, "upgrades": 500},
      "total": 5361
    },
    "risk": [
      {
        "description": "Vendor may change pricing or features",
        "probability": "medium",
        "impact": 2000,
        "mitigation": "Negotiate annual contract with price lock"
      }
    ],
    "benefit": {
      "short_term": {"value_saved": 6500, "value_created": 5000},
      "mid_term": {"value_saved": 26000, "value_created": 20000},
      "long_term": {"value_saved": 52000, "value_created": 40000},
      "total": 149500
    }
  },
  "roi_percentage": 2789,
  "payback_months": 2,
  "assumptions": [
    "10 hours/week time savings at €50/hour",
    "Current volume of 100 tasks/week",
    "80% adoption rate by team"
  ],
  "why_it_matters": {
    "customer_value": "How this helps their customers",
    "business_health": "How this strengthens the business"
  }
}

## Critical Requirements
1. ALL THREE OPTIONS must be provided
2. Custom option MUST include specific AI tools (Claude, GPT-4, Cursor, etc.)
3. Assumptions must be explicit and adjustable
4. ROI calculation must be transparent
5. "Why it matters" must connect to Two Pillars
"""
```

---

## Specific Tasks

### Phase 1: Core Structure
- [ ] Refactor report_service.py with progress callbacks
- [ ] Implement Three Options structure in recommendations
- [ ] Add "build it yourself" section generation
- [ ] Integrate AI tool recommendations

### Phase 2: Quality Improvements
- [ ] Improve finding generation prompt for specificity
- [ ] Add source citation requirements
- [ ] Implement assumption transparency
- [ ] Add "not recommended" findings generation

### Phase 3: Verdict Logic
- [ ] Refine verdict thresholds
- [ ] Add industry-specific verdict adjustments
- [ ] Include "what to do instead" for negative verdicts
- [ ] Add confidence scoring to verdicts

### Phase 4: Progress Streaming
- [ ] Add progress callback throughout generation
- [ ] Emit finding/recommendation previews during generation
- [ ] Handle errors gracefully with recovery options
- [ ] Test SSE integration end-to-end

### Phase 5: Model Optimization
- [ ] Route different tasks to appropriate models
- [ ] Use Haiku for extraction tasks
- [ ] Use Sonnet for main generation
- [ ] Reserve Opus for complex strategic synthesis
- [ ] Track and optimize token usage

---

## Dependencies

**Needs from Agent 2 (Backend):**
- SSE endpoint infrastructure
- Progress callback mechanism

**Needs from Agent 4 (Data):**
- Vendor database for Three Options
- Industry benchmarks for context
- AI tool/model pricing data

---

## Deliverables

1. `report_service.py` - Complete rewrite with Three Options
2. `prompts/` - All prompt templates
3. `verdict_engine.py` - Verdict generation logic
4. `roi_calculator.py` - Transparent ROI calculations
5. Progress streaming integration
6. Model routing configuration

---

## Quality Criteria

- [ ] Every finding cites a source
- [ ] Every recommendation has Three Options
- [ ] Every ROI shows assumptions
- [ ] Custom options always include specific tools
- [ ] Verdicts are honest (includes "no" recommendations)
- [ ] Progress events fire correctly during generation

---

## Model Usage Guidelines

```python
MODEL_ROUTING = {
    # Fast extraction tasks
    "parse_quiz": "claude-3-5-haiku-20241022",
    "extract_pricing": "claude-3-5-haiku-20241022",

    # Main generation (quality + speed balance)
    "generate_findings": "claude-sonnet-4-20250514",
    "generate_recommendations": "claude-sonnet-4-20250514",
    "generate_roadmap": "claude-sonnet-4-20250514",

    # Strategic synthesis (highest quality)
    "generate_verdict": "claude-sonnet-4-20250514",
    "executive_summary": "claude-sonnet-4-20250514",

    # Complex edge cases (reserve for special needs)
    "complex_analysis": "claude-opus-4-5-20250514"
}
```
