# AGENT 4: Data & Knowledge Base

> **Mission:** Build the data moat that makes CRB Analyser impossible to replicate with ChatGPT. Verified vendor pricing, industry benchmarks with sources, AI tool intelligence - all kept fresh and accurate.

---

## Context

**Product:** CRB Analyser - AI-powered Cost/Risk/Benefit analysis
**Key Differentiator:** Real, verified data that ChatGPT cannot hallucinate
**Target Industries:** Tech/SaaS, E-commerce, Music/Studios, SMB Services

**The Moat:**
1. Vendor pricing verified monthly (not hallucinated)
2. Industry benchmarks with cited sources
3. AI tool landscape intelligence (models, pricing, capabilities)
4. Implementation cost data from real projects

---

## Current State

```
backend/src/knowledge/
├── tech-companies/
│   ├── benchmarks.json
│   ├── opportunities.json
│   └── vendors.json
```

**What Exists:**
- Basic JSON files with some industry data
- Manual updates only
- No pricing verification system
- No AI tool database

**What's Missing:**
- Comprehensive vendor database (100+ vendors)
- Industry benchmarks for all target verticals
- AI model comparison data
- Auto-refresh infrastructure
- Source citations for everything

---

## Target State

### 1. Vendor Database Structure

**Categories (12):**
```
1. crm                 - HubSpot, Salesforce, Pipedrive, etc.
2. project_management  - Asana, Monday, ClickUp, Notion
3. automation          - Zapier, Make, n8n, Workato
4. ai_assistants       - ChatGPT, Claude, Gemini, Perplexity
5. customer_support    - Intercom, Zendesk, Freshdesk
6. analytics           - Mixpanel, Amplitude, PostHog
7. ecommerce           - Shopify, WooCommerce, BigCommerce
8. marketing           - Mailchimp, Klaviyo, HubSpot Marketing
9. finance             - QuickBooks, Xero, FreshBooks
10. hr_payroll         - Gusto, Rippling, BambooHR
11. dev_tools          - GitHub, GitLab, Vercel, Railway
12. ai_development     - OpenAI API, Anthropic API, Cursor, etc.
```

**Vendor Data Schema:**
```json
{
  "slug": "intercom",
  "name": "Intercom",
  "category": "customer_support",
  "subcategory": "ai_chatbot",
  "website": "https://intercom.com",
  "pricing_url": "https://intercom.com/pricing",

  "description": "Customer messaging platform with AI-powered chatbot",
  "tagline": "The AI-first customer service solution",

  "pricing": {
    "model": "per_seat",
    "currency": "USD",
    "billing_options": ["monthly", "annual"],
    "annual_discount_percent": 20,
    "tiers": [
      {
        "name": "Essential",
        "price": 39,
        "per": "seat/month",
        "billing": "annual",
        "features": [
          "Shared inbox",
          "Basic chatbot",
          "1,000 contacts"
        ],
        "limits": {
          "contacts": 1000,
          "custom_bots": 1
        }
      },
      {
        "name": "Advanced",
        "price": 99,
        "per": "seat/month",
        "billing": "annual",
        "features": [
          "Everything in Essential",
          "AI chatbot (Fin)",
          "Automation workflows",
          "5,000 contacts"
        ]
      },
      {
        "name": "Expert",
        "price": 139,
        "per": "seat/month",
        "billing": "annual",
        "features": [
          "Everything in Advanced",
          "Workload management",
          "SLA rules",
          "Unlimited contacts"
        ]
      }
    ],
    "custom_pricing": true,
    "free_trial_days": 14,
    "money_back_days": 0,
    "startup_discount": "Up to 95% off for early-stage startups"
  },

  "best_for": [
    "saas_companies",
    "tech_startups",
    "ecommerce",
    "support_heavy_businesses"
  ],

  "industries": [
    "tech",
    "ecommerce",
    "fintech",
    "healthcare"
  ],

  "company_sizes": ["startup", "smb", "mid_market"],

  "avoid_if": [
    "very_low_volume",
    "simple_email_only",
    "strict_budget_under_50"
  ],

  "implementation": {
    "avg_weeks": 3,
    "complexity": "medium",
    "requires_developer": false,
    "cost_range": {
      "diy": {"min": 0, "max": 500},
      "with_help": {"min": 1500, "max": 5000},
      "full_service": {"min": 5000, "max": 15000}
    }
  },

  "ratings": {
    "g2": {"score": 4.5, "reviews": 3200, "url": "https://g2.com/products/intercom"},
    "capterra": {"score": 4.5, "reviews": 1000},
    "trustpilot": {"score": 3.8, "reviews": 500},
    "our_rating": 4.3,
    "our_notes": "Great for tech companies, can get expensive at scale"
  },

  "integrations": [
    "slack", "salesforce", "hubspot", "segment", "zapier"
  ],

  "api": {
    "available": true,
    "quality": "good",
    "docs_url": "https://developers.intercom.com"
  },

  "competitors": ["zendesk", "freshdesk", "helpscout", "crisp"],

  "verified_at": "2025-12-15T10:00:00Z",
  "verified_by": "manual",
  "source_url": "https://intercom.com/pricing",
  "notes": "Pricing verified Dec 2025. Fin AI costs extra ($0.99/resolution)."
}
```

### 2. AI Tool Database

**Critical for "Build It Yourself" recommendations:**

```json
{
  "slug": "claude-api",
  "name": "Claude API",
  "provider": "Anthropic",
  "category": "ai_development",
  "subcategory": "llm_api",

  "models": [
    {
      "name": "Claude Opus 4.5",
      "model_id": "claude-opus-4-5-20250514",
      "description": "Most capable model for complex reasoning",
      "best_for": ["complex_analysis", "creative_writing", "research"],
      "context_window": 200000,
      "pricing": {
        "input_per_1m": 15.00,
        "output_per_1m": 75.00,
        "cached_input_per_1m": 1.50
      },
      "speed": "slower",
      "quality": "highest"
    },
    {
      "name": "Claude Sonnet 4",
      "model_id": "claude-sonnet-4-20250514",
      "description": "Best balance of intelligence and speed",
      "best_for": ["coding", "analysis", "general_tasks"],
      "context_window": 200000,
      "pricing": {
        "input_per_1m": 3.00,
        "output_per_1m": 15.00,
        "cached_input_per_1m": 0.30
      },
      "speed": "fast",
      "quality": "very_high"
    },
    {
      "name": "Claude Haiku 3.5",
      "model_id": "claude-3-5-haiku-20241022",
      "description": "Fast and affordable for simple tasks",
      "best_for": ["extraction", "classification", "high_volume"],
      "context_window": 200000,
      "pricing": {
        "input_per_1m": 0.80,
        "output_per_1m": 4.00,
        "cached_input_per_1m": 0.08
      },
      "speed": "fastest",
      "quality": "good"
    }
  ],

  "use_cases": {
    "chatbot": {
      "recommended_model": "claude-sonnet-4-20250514",
      "monthly_cost_estimate": {
        "low_volume": 50,
        "medium_volume": 200,
        "high_volume": 1000
      },
      "implementation_hours": "40-80"
    },
    "document_processing": {
      "recommended_model": "claude-opus-4-5-20250514",
      "monthly_cost_estimate": {
        "low_volume": 100,
        "medium_volume": 500,
        "high_volume": 2000
      }
    },
    "code_assistant": {
      "recommended_model": "claude-sonnet-4-20250514",
      "note": "Use via Cursor IDE for best experience"
    }
  },

  "compared_to": {
    "gpt-4": "More nuanced writing, better at following complex instructions",
    "gemini": "Smaller context window but higher quality reasoning"
  },

  "verified_at": "2025-12-15",
  "pricing_url": "https://anthropic.com/pricing"
}
```

**Other AI Tools to Include:**
```
LLM APIs:
- OpenAI (GPT-4, GPT-4o, GPT-4o-mini)
- Google (Gemini 2.0, Gemini 2.5 Pro)
- Anthropic (Claude models)
- Mistral
- Cohere

Development Tools:
- Cursor (AI IDE)
- GitHub Copilot
- Codeium
- Tabnine
- Replit AI

No-Code AI:
- Relevance AI
- Flowise
- Langflow
- Dify

Hosting/Deployment:
- Vercel
- Railway
- Render
- Fly.io
- AWS Lambda/Bedrock
```

### 3. Industry Benchmarks

**Structure:**
```json
{
  "industry": "tech_saas",
  "company_size": "20-50",

  "operational_metrics": {
    "labor_cost_ratio": {
      "value": 0.65,
      "description": "Labor as % of revenue",
      "percentiles": {"p25": 0.55, "p50": 0.65, "p75": 0.75},
      "source": "SaaS Capital Annual Survey 2024",
      "source_url": "https://saas-capital.com/survey"
    },
    "admin_overhead_percent": {
      "value": 25,
      "description": "Time spent on non-core activities",
      "source": "McKinsey Digital Operations Study 2024"
    },
    "customer_support_cost_per_ticket": {
      "value": 15,
      "currency": "USD",
      "source": "Zendesk Benchmark Report 2024"
    },
    "avg_sales_cycle_days": {
      "value": 45,
      "source": "Gartner B2B Sales Study 2024"
    }
  },

  "ai_adoption_metrics": {
    "ai_tools_in_use": {
      "value": 3.2,
      "description": "Average AI tools per company",
      "source": "CB Insights AI Adoption Report 2024"
    },
    "ai_budget_percent": {
      "value": 5,
      "description": "AI spend as % of tech budget",
      "source": "Gartner IT Spending Forecast 2025"
    }
  },

  "automation_potential": {
    "customer_support": {
      "automatable_percent": 65,
      "typical_savings": "40-60%",
      "implementation_difficulty": "medium"
    },
    "data_entry": {
      "automatable_percent": 90,
      "typical_savings": "70-85%",
      "implementation_difficulty": "low"
    },
    "reporting": {
      "automatable_percent": 80,
      "typical_savings": "60-75%",
      "implementation_difficulty": "medium"
    },
    "lead_qualification": {
      "automatable_percent": 70,
      "typical_savings": "50-65%",
      "implementation_difficulty": "medium"
    }
  },

  "verified_at": "2025-12-01"
}
```

**Industries to Cover:**
```
1. tech_saas          - SaaS companies, software
2. tech_hardware      - Hardware, IoT, devices
3. ecommerce_retail   - Online stores, D2C
4. ecommerce_marketplace - Marketplaces, platforms
5. music_production   - Studios, producers, labels
6. music_distribution - Distribution, streaming
7. creative_agencies  - Marketing, design, content
8. professional_services - Consulting, legal, accounting
9. healthcare_clinics - Medical practices
10. real_estate       - Agencies, property management
```

**Company Sizes:**
```
- solo (1 person)
- micro (2-10)
- small (11-50)
- medium (51-200)
- mid_market (201-500)
```

### 4. Opportunity Templates

**Pre-built finding templates by industry:**

```json
{
  "industry": "tech_saas",
  "opportunities": [
    {
      "id": "saas-support-ai",
      "title": "AI-Powered Customer Support Triage",
      "category": "customer_experience",
      "typical_findings": {
        "hours_saved_weekly": {"min": 10, "max": 40},
        "cost_reduction_percent": {"min": 30, "max": 60},
        "customer_satisfaction_improvement": {"min": 10, "max": 25}
      },
      "relevant_if": [
        "support_volume > 50/week",
        "current_response_time > 4 hours",
        "team_size >= 2 support"
      ],
      "recommended_solutions": {
        "off_the_shelf": ["intercom", "zendesk"],
        "best_in_class": ["zendesk_ultimate", "ada"],
        "custom": ["claude_api_chatbot"]
      },
      "implementation_notes": "Start with FAQ automation, expand to ticket classification"
    },
    {
      "id": "saas-churn-prediction",
      "title": "AI Churn Prediction & Prevention",
      "category": "growth",
      "typical_findings": {
        "churn_reduction_percent": {"min": 15, "max": 35},
        "revenue_impact": {"min": 50000, "max": 500000}
      },
      "relevant_if": [
        "mrr > 50000",
        "churn_rate > 5%",
        "has_usage_data"
      ]
    }
  ]
}
```

### 5. Data Refresh System

**Refresh Schedule:**
```python
REFRESH_SCHEDULE = {
    "vendor_pricing": {
        "frequency": "weekly",
        "priority_vendors": ["intercom", "zendesk", "hubspot"],  # Daily
        "method": "ai_extraction",
        "fallback": "manual_review"
    },
    "ai_model_pricing": {
        "frequency": "weekly",
        "method": "api_check",  # Most have pricing APIs or docs
        "alert_on_change": True
    },
    "industry_benchmarks": {
        "frequency": "quarterly",
        "method": "manual_research",
        "sources": ["gartner", "mckinsey", "industry_reports"]
    },
    "competitor_tracking": {
        "frequency": "monthly",
        "method": "web_scraping",
        "track": ["new_features", "pricing_changes"]
    }
}
```

**Freshness Indicators:**
```python
def get_freshness_status(verified_at: datetime) -> str:
    days_old = (datetime.now() - verified_at).days

    if days_old <= 7:
        return "fresh"      # Green badge
    elif days_old <= 30:
        return "current"    # No badge
    elif days_old <= 90:
        return "aging"      # Yellow badge
    else:
        return "stale"      # Red badge, trigger refresh
```

---

## Specific Tasks

### Phase 1: Database Schema
- [ ] Create vendors table with full schema
- [ ] Create ai_tools table for LLM/dev tools
- [ ] Create industry_benchmarks table
- [ ] Create opportunity_templates table
- [ ] Create pricing_history table
- [ ] Set up indexes for fast querying

### Phase 2: Initial Data Population

**Vendors (100+ total):**
- [ ] CRM category (10 vendors)
- [ ] Customer Support (10 vendors)
- [ ] Automation (10 vendors)
- [ ] AI Development (15 vendors/tools)
- [ ] Analytics (8 vendors)
- [ ] E-commerce (10 vendors)
- [ ] Project Management (10 vendors)
- [ ] Marketing (10 vendors)
- [ ] Finance (8 vendors)
- [ ] HR/Payroll (8 vendors)
- [ ] Dev Tools (10 vendors)

**AI Tools:**
- [ ] All Claude models with pricing
- [ ] All GPT models with pricing
- [ ] All Gemini models with pricing
- [ ] Cursor, Copilot, etc.
- [ ] Hosting platforms (Vercel, Railway, etc.)

**Benchmarks:**
- [ ] Tech/SaaS benchmarks (3 sizes)
- [ ] E-commerce benchmarks (3 sizes)
- [ ] Music/Studios benchmarks (3 sizes)
- [ ] Professional Services benchmarks (3 sizes)

**Opportunity Templates:**
- [ ] 20 templates for Tech/SaaS
- [ ] 15 templates for E-commerce
- [ ] 15 templates for Music/Studios
- [ ] 15 templates for Services

### Phase 3: Refresh Infrastructure
- [ ] Build vendor pricing scraper
- [ ] Build AI pricing extraction (Claude)
- [ ] Create refresh job scheduler
- [ ] Set up freshness monitoring
- [ ] Create manual review queue
- [ ] Build change detection alerts

### Phase 4: API Integration
- [ ] Vendor search/filter endpoints
- [ ] Vendor comparison endpoint
- [ ] Benchmark lookup endpoints
- [ ] Template matching logic
- [ ] Freshness status in responses

---

## Dependencies

**Needs from Agent 2 (Backend):**
- Database tables created
- API endpoints for CRUD
- Background job infrastructure

**Needs from Agent 3 (AI Engine):**
- Pricing extraction prompts
- Benchmark interpretation

**Provides to Agent 3 (AI Engine):**
- Vendor options for Three Options pattern
- Industry context for findings
- AI tool recommendations for custom builds

---

## Deliverables

1. **Vendor Database** - 100+ vendors with verified pricing
2. **AI Tool Database** - All major LLMs and dev tools
3. **Industry Benchmarks** - 4 industries × 3 sizes
4. **Opportunity Templates** - 65+ pre-built templates
5. **Refresh System** - Automated pricing updates
6. **Data Quality Dashboard** - Freshness monitoring

---

## Data Sources

**Vendor Pricing:**
- Official pricing pages (primary)
- G2, Capterra for ratings
- Product Hunt for new tools
- Twitter/LinkedIn for announcements

**Industry Benchmarks:**
- Gartner reports
- McKinsey studies
- Industry association reports
- SaaS Capital surveys
- Zendesk/HubSpot benchmark reports

**AI Tool Data:**
- Official API documentation
- Provider pricing pages
- AI leaderboards (LMSYS, etc.)

---

## Quality Criteria

- [ ] Every vendor has verified pricing < 30 days old
- [ ] Every benchmark cites a source with URL
- [ ] AI model pricing matches official docs
- [ ] No placeholder data in production
- [ ] Freshness badges accurate
- [ ] Comparison data is fair and balanced

---

## File Structure

```
backend/
├── src/
│   ├── knowledge/
│   │   ├── vendors/
│   │   │   ├── crm.json
│   │   │   ├── support.json
│   │   │   ├── automation.json
│   │   │   ├── ai_development.json
│   │   │   └── ...
│   │   ├── benchmarks/
│   │   │   ├── tech_saas.json
│   │   │   ├── ecommerce.json
│   │   │   ├── music_studios.json
│   │   │   └── ...
│   │   ├── opportunities/
│   │   │   ├── tech_saas.json
│   │   │   ├── ecommerce.json
│   │   │   └── ...
│   │   └── ai_tools/
│   │       ├── llm_providers.json
│   │       ├── dev_tools.json
│   │       └── hosting.json
│   └── services/
│       ├── vendor_service.py
│       ├── benchmark_service.py
│       └── refresh_service.py
```
