# Sample Report Generation Prompt

Use this prompt to generate new sample reports that follow the AIOS connect-first methodology.

## Usage

```bash
# Generate from seed (recommended)
cd backend && source venv/bin/activate
python -m src.cli.generate_report --industry ecommerce --tier small
python -m src.cli.generate_report --industry dental --tier small
python -m src.cli.generate_report --industry professional-services --tier small

# Generate batch across industries
python -m src.cli.generate_report --batch --all-industries
```

## What the pipeline does

1. **Fabricator** picks a seed, builds quiz answers (now including readiness profile fields)
2. **Report service** generates findings, then feeds each into the **ThreeOptionsSkill**
3. **ThreeOptionsSkill** uses the AIOS connect-first prompt to generate recommendations
4. Output is a complete report JSON matching the schema below

## If you need to generate a STATIC sample report manually

Use the following prompt with Claude to generate a complete report JSON. Fill in the `[PLACEHOLDERS]` with real business data from one of the seed profiles.

---

## PROMPT

You are generating a sample CRB Analysis report for **[COMPANY_NAME]**, a **[INDUSTRY]** business.

### Company Profile

```json
{
  "company_name": "[COMPANY_NAME]",
  "industry": "[INDUSTRY]",
  "industry_display": "[Industry Display Name]",
  "team_size": "[STAFF_SIZE]",
  "tech_level": "[low|medium|high]",
  "budget_range": "[BUDGET]",
  "existing_tools": ["[tool1]", "[tool2]", "[tool3]"],
  "location": "[COUNTRY]"
}
```

### Client Readiness Profile

```json
{
  "infrastructure": "[paper-based|partial|digitized]",
  "build_willingness": "[prefers-turnkey|open|eager]",
  "ai_experience": "[none|dabbled|active-user]",
  "stack_api_readiness": "[mixed|most-apis]",
  "urgency": "[this_week|this_month|this_quarter|no_rush]",
  "preference": "[buy|build|connect|hire]"
}
```

### Generation Rules — AIOS Connect-First Philosophy

**Core Principle:**
> "Connect what you have. Automate what slows you down. Build what doesn't exist."

**NEVER recommend replacing software unless the existing tool genuinely cannot be integrated (no API, fundamentally broken, blocking growth).** Most businesses can get 80% of the value by connecting what they have.

#### Recommendation Decision Logic (evaluate per finding):

1. **No digital tool exists** for this function → recommend `targeted_upgrade`
   - Buy the foundation with strong APIs so it becomes connectable later
   - Frame as: "This is your foundation — once set up, we can wire AI workflows on top."

2. **Existing tool is a dead end** (no API, no export, data trapped) → recommend `targeted_upgrade`
   - Replace with API-ready alternative
   - Frame as: "Your current tool traps your data. [Replacement] opens integration."

3. **Everything else** → recommend `connect_and_automate`
   - Adapt complexity to client readiness profile
   - Paper-based: acknowledge gap, show simpler paths (Zapier, Make)
   - Digitized + eager: show Claude Code / MCP workflows with specific steps
   - Low willingness: emphasize managed tools over raw APIs
   - High urgency: fastest option (usually connect, not replace)

#### Adapt the HOW, not the WHETHER
- Never say "you're not technical enough"
- AI-assisted building is accessible to everyone
- Always explain WHY this recommendation fits THIS client's readiness level

#### Banned Language
Do NOT use: "seamless", "robust", "scalable", "enterprise-grade", "unlock value", "drive efficiency", "optimize", "streamline", "cutting-edge", "revolutionary", "consider migrating to"

Instead, be specific:
> "Build a Claude workflow connecting Shopify orders to your accounting — ships in 8 hours"

### Required Report Schema

Generate a complete JSON object with this structure:

```json
{
  "id": "sample-[industry]-report",
  "tier": "full",
  "status": "completed",
  "created_at": "2026-02-26T10:00:00Z",
  "company_profile": {
    "company_name": "",
    "industry": "",
    "industry_display": "",
    "team_size": "",
    "tech_level": "",
    "budget_range": "",
    "existing_tools": [],
    "location": ""
  },
  "executive_summary": {
    "ai_readiness_score": 0,
    "customer_value_score": 0,
    "business_health_score": 0,
    "key_insight": "One sentence summary of the biggest opportunity.",
    "total_value_potential": { "annual_savings": 0, "revenue_growth": 0 },
    "top_opportunities": [
      { "title": "", "impact": "", "timeline": "short|mid|long" }
    ],
    "not_recommended": [
      { "area": "", "reason": "" }
    ],
    "recommended_investment": { "monthly": 0, "currency": "EUR" }
  },
  "value_summary": {
    "value_saved": { "hours_per_week": 0, "annual_euros": 0 },
    "value_created": { "annual_euros": 0, "description": "" },
    "total": { "annual_euros": 0 }
  },
  "findings": [
    "SEE FINDING SCHEMA BELOW — generate 5-7 findings"
  ],
  "recommendations": [
    "SEE RECOMMENDATION SCHEMA BELOW — generate 3-5 recommendations"
  ],
  "roadmap": {
    "short_term": [{ "action": "", "timeline": "", "impact": "" }],
    "mid_term": [{ "action": "", "timeline": "", "impact": "" }],
    "long_term": [{ "action": "", "timeline": "", "impact": "" }]
  },
  "playbooks": [
    {
      "id": "playbook-001",
      "title": "",
      "finding_ids": [],
      "steps": [
        { "step": 1, "title": "", "description": "", "tools": [], "duration": "" }
      ],
      "total_duration": "",
      "expected_outcome": ""
    }
  ],
  "system_architecture": {
    "existing_tools": [{ "name": "", "category": "", "api_quality": "good|fair|poor" }],
    "ai_layer": [{ "name": "", "purpose": "", "connects_to": [] }],
    "automations": [{ "name": "", "trigger": "", "action": "", "tools": [] }],
    "connections": [{ "from": "", "to": "", "type": "api|webhook|mcp|manual" }],
    "cost_comparison": {
      "current_monthly": 0,
      "proposed_monthly": 0,
      "roi_months": 0
    }
  },
  "industry_insights": {
    "industry": "",
    "industry_display_name": "",
    "adoption_stats": { "ai_adoption_rate": "", "top_use_case": "" },
    "opportunity_map": [{ "area": "", "maturity": "emerging|growing|mature" }],
    "social_proof": [{ "company_type": "", "result": "", "timeline": "" }]
  },
  "automation_summary": {
    "stack_assessment": "",
    "opportunities": [
      {
        "name": "",
        "category": "connect|enhance|replace",
        "monthly_impact_eur": 0,
        "diy_hours": 0,
        "tools_involved": []
      }
    ],
    "total_monthly_impact": 0,
    "total_diy_hours": 0,
    "connect_count": 0,
    "replace_count": 0,
    "either_count": 0,
    "next_steps": [""]
  },
  "methodology_notes": {
    "data_sources": ["Quiz responses", "Workshop transcript", "Industry benchmarks"],
    "assumptions": [""],
    "confidence_level": "high|medium|low",
    "last_updated": "2026-02-26"
  }
}
```

### Finding Schema

Each finding describes a gap or opportunity discovered in the analysis.

```json
{
  "id": "f1",
  "title": "Clear, specific title (e.g., '65% of Support Tickets Are Repetitive WISMO Queries')",
  "description": "2-3 sentences explaining the finding with specific numbers from the business.",
  "customer_value_score": 8,
  "business_health_score": 7,
  "confidence": "high|medium|low",
  "time_horizon": "short|mid|long",
  "value_saved": {
    "hours_per_week": 0,
    "hourly_rate": 0,
    "annual_savings": 0
  },
  "value_created": {
    "description": "",
    "potential_revenue": 0
  },
  "connect_path": "Brief description of how to solve by connecting existing tools (or null if not applicable)",
  "replace_path": "Brief description of replacement option (or null if connecting works fine)",
  "agent_opportunity": {
    "agent_type": "e.g., Customer Support Agent",
    "what_it_does": "Specific description of what the AI agent handles",
    "estimated_impact": { "monthly_value_eur": 0, "hours_saved_monthly": 0 },
    "deployment_timeline": "e.g., 2 weeks",
    "prerequisites": ["What must exist first"]
  },
  "automation_flow": {
    "nodes": [
      { "id": "n1", "label": "Tool Name", "type": "existing_tool" },
      { "id": "n2", "label": "AI Processing", "type": "ai_layer" },
      { "id": "n3", "label": "Result", "type": "output" }
    ],
    "edges": [
      { "from": "n1", "to": "n2", "label": "data flow description" },
      { "from": "n2", "to": "n3", "label": "processed output" }
    ]
  }
}
```

**Finding Rules:**
- `customer_value_score` + `business_health_score`: each 1-10, combined determines severity tier
- Combined >= 16: Critical | >= 14: High | >= 10: Medium | < 10: Low
- Combined >= 14: verdict = "Proceed" | >= 8: "Wait" | < 8: "Skip"
- Use specific numbers from the business, not vague claims
- Include `connect_path` for most findings (it's the default)
- Only include `replace_path` when the existing tool is genuinely a dead end
- `automation_flow` is optional but recommended for high-priority findings
- Node types: `existing_tool` (green), `new_tool` (blue), `ai_layer` (purple), `output` (gray)
- Keep flows to 3-6 nodes max

### Recommendation Schema (AIOS Options)

Each recommendation maps to one or more findings and presents three options.

```json
{
  "id": "rec-001",
  "finding_id": "f1",
  "title": "Actionable title (e.g., 'Deploy AI Customer Support on Existing Gorgias')",
  "description": "What to do and why, referencing the client's actual stack.",
  "why_it_matters": {
    "customer_value": "Specific benefit to their customers",
    "business_health": "Specific benefit to the business"
  },
  "priority": "high|medium|low",
  "options": {
    "connect_and_automate": {
      "approach": "Specific: 'Build Claude API workflow connecting Gorgias webhooks to auto-response engine for WISMO, sizing, and returns queries'",
      "build_time": "e.g., 2 weeks (solo) / 4 days (guided)",
      "tools_used": ["Claude Code", "existing_tool_1", "existing_tool_2"],
      "mcp_servers": ["mcp-server-name if applicable"],
      "monthly_cost": "e.g., EUR 50-150 (API usage)",
      "prerequisite": "What must exist first (or omit if nothing needed)",
      "diy_complexity": "low|moderate|high",
      "automation_flow": {
        "nodes": [
          { "id": "n1", "label": "Source Tool", "type": "existing_tool" },
          { "id": "n2", "label": "Claude Workflow", "type": "ai_layer" },
          { "id": "n3", "label": "Target Tool", "type": "existing_tool" },
          { "id": "n4", "label": "Output", "type": "output" }
        ],
        "edges": [
          { "from": "n1", "to": "n2", "label": "trigger data" },
          { "from": "n2", "to": "n3", "label": "processed action" },
          { "from": "n3", "to": "n4", "label": "result" }
        ]
      },
      "pros": ["Uses your existing stack", "Ships this week", "Fully customized"],
      "cons": ["Requires API monitoring", "Custom code maintenance"]
    },
    "enhance_with_ai": {
      "approach": "What the AI agent/intelligence layer does",
      "build_time": "e.g., 3-4 weeks",
      "tools_used": ["Claude API", "data_source", "dashboard"],
      "monthly_cost": "e.g., EUR 200-400",
      "pros": ["Autonomous handling", "Learns from patterns"],
      "cons": ["More complex setup", "Needs training data"]
    },
    "targeted_upgrade": {
      "when_needed": "ONLY if existing tool is dead end — explain specifically why",
      "tools": ["vendor1", "vendor2"],
      "cost_range": "e.g., EUR 200-500/month",
      "migration_time": "e.g., 4-6 weeks",
      "pros": ["Pre-built solution", "Vendor support"],
      "cons": ["Monthly SaaS cost", "Less customization", "Vendor lock-in"]
    }
  },
  "our_recommendation": "connect_and_automate",
  "recommendation_rationale": "Reference the client's readiness profile: their infrastructure level, build willingness, existing API-ready stack. Explain why connect fits better than replace for THIS client.",
  "net_scores": {
    "connect_and_automate": 7.5,
    "enhance_with_ai": 5.2,
    "targeted_upgrade": 3.1
  },
  "comparison_summary": {
    "table": [
      { "aspect": "Monthly cost", "connect_and_automate": "EUR X", "enhance_with_ai": "EUR Y", "targeted_upgrade": "EUR Z" },
      { "aspect": "Time to value", "connect_and_automate": "Days", "enhance_with_ai": "Weeks", "targeted_upgrade": "Months" },
      { "aspect": "Disruption", "connect_and_automate": "Zero", "enhance_with_ai": "Low", "targeted_upgrade": "High" }
    ]
  },
  "roi_percentage": 250,
  "payback_months": 2,
  "assumptions": [
    "Each assumption MUST include a specific number AND source",
    "e.g., 'Average WISMO ticket takes 4 minutes (Gorgias benchmark data)'",
    "e.g., 'Customer support handles 200 tickets/month (workshop data)'"
  ]
}
```

**Recommendation Rules:**
- `our_recommendation` should be `connect_and_automate` for ~80% of recommendations
- Only use `targeted_upgrade` when a tool genuinely has no API or is fundamentally broken
- `automation_flow` is REQUIRED for every `connect_and_automate` option
- `diy_complexity`: low = use Zapier/Make, moderate = API + Claude, high = custom code
- `prerequisite`: include when the client lacks a foundation (e.g., "digital scheduling tool")
- `net_scores`: NET = Benefit - Cost - (Risk / 10), connect should usually score highest
- ROI > 500% requires explicit justification in assumptions
- `recommendation_rationale` MUST reference the readiness profile dimensions

### Quality Checklist

Before finalizing the report, verify:

- [ ] **Connect-first**: At least 60% of recommendations use `connect_and_automate`
- [ ] **No phantom replacements**: No `targeted_upgrade` recommended unless tool is genuinely a dead end
- [ ] **Specific numbers**: Every finding has real EUR/hours numbers, not vague claims
- [ ] **Readiness-adapted**: Rationale references the client's infrastructure, willingness, and AI experience
- [ ] **Automation flows**: Every connect option has a valid `automation_flow` with 3-6 nodes
- [ ] **No banned language**: No "seamless", "robust", "scalable", "enterprise-grade", etc.
- [ ] **Honest tradeoffs**: Every option has both pros AND cons (no option is perfect)
- [ ] **Assumptions sourced**: Every assumption includes a number and a source
- [ ] **Playbooks actionable**: Step-by-step with tools, duration, and expected outcome
- [ ] **NET scores consistent**: connect_and_automate scores highest when recommended
- [ ] **Findings scored**: customer_value_score + business_health_score = 2-20 range
- [ ] **Value math adds up**: value_summary totals match sum of finding values

### Example: Ecommerce (BonBon Boutique)

**Readiness:** paper-based infrastructure, prefers-turnkey, no AI experience, mixed APIs

**Finding:** "No email marketing despite 4,000 subscriber list — estimated EUR 3,000-5,000/month in missed revenue"

**Recommendation (connect_and_automate):**
```
"Deploy Klaviyo on Shopify with AI-generated welcome series and abandoned cart flows.
Shopify's native Klaviyo integration handles the connection — no custom code needed.
Claude generates email copy tailored to your brand voice from your Instagram content."

Build time: 1 week (solo) / 2 days (guided)
Tools: Klaviyo (free tier up to 500 contacts), Shopify, Claude API
DIY complexity: low
Monthly cost: EUR 0-45 (Klaviyo scales with list size)
```

**Why connect, not replace:** "Your Shopify store already has the customer data and order events that Klaviyo needs. Installing Klaviyo is a 1-click Shopify integration — no migration, no disruption. Given your preference for turnkey solutions, this is the fastest path to revenue recovery."

### Example: Dental (Solo Tandarts)

**Readiness:** paper-based, prefers-turnkey, no AI, mixed APIs

**Finding:** "15% no-show rate costs EUR 5,000/month — manual phone reminders reach voicemail 50% of the time"

**Recommendation (targeted_upgrade — justified because paper-based):**
```
"Your current scheduling is paper + phone. There's no digital system to connect TO.
Start with an online booking tool (Doctolib or NexHealth) that includes SMS reminders.
This becomes your foundation — once digital, we can layer AI on top."

When needed: "No digital scheduling exists — can't automate what isn't digital"
Tools: Doctolib (EUR 129/mo), NexHealth (EUR 199/mo)
Migration: 2-3 weeks
```

**Why replace here:** "You can't connect tools that don't exist. Your scheduling is entirely paper-based and phone-based, so the first step is establishing a digital foundation. We specifically recommend Doctolib because its API enables future automation — SMS reminders, online booking, and eventually AI-powered schedule optimization."
