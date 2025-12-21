# AGENT-4: Data & Knowledge Base - Handoff Document

## Status: ~90% Complete

### Completed

| Component | Files | Status |
|-----------|-------|--------|
| **Pydantic Schemas** | `schemas.py` | Done |
| **Directory Structure** | `vendors/`, `ai_tools/`, `benchmarks/`, `opportunities/` | Done |
| **Vendor Database** | 11 JSON files, 65 vendors | Done |
| **LLM Providers** | `ai_tools/llm_providers.json` (5 providers, 18 models) | Done |
| **Knowledge Loaders** | `__init__.py` with search, compare, LLM cost estimation | Done |
| **Vendor Service** | `services/vendor_service.py` with KB functions | Done |
| **Research Tools** | `tools/research_tools.py` updated to use KB | Done |
| **Industry Benchmarks** | 4 files with source citations | Done |
| **Opportunity Templates** | `opportunities/` directory | **Pending** |

---

## File Inventory

### Vendors (`/backend/src/knowledge/vendors/`)
```
ai_assistants.json      (5 vendors: ChatGPT, Claude, Gemini, Perplexity, Poe)
analytics.json          (6 vendors: Mixpanel, Amplitude, PostHog, Heap, Pendo, Hotjar)
automation.json         (6 vendors: Zapier, Make, n8n, Workato, Tray.io, Activepieces)
crm.json               (6 vendors: HubSpot, Salesforce, Pipedrive, Close, Zoho, Attio)
customer_support.json   (6 vendors: Intercom, Zendesk, Freshdesk, Help Scout, Crisp, Ada)
dev_tools.json         (6 vendors: GitHub, GitLab, Vercel, Railway, Render, Supabase)
ecommerce.json         (6 vendors: Shopify, WooCommerce, BigCommerce, Medusa, Saleor, Magento)
finance.json           (6 vendors: QuickBooks, Xero, FreshBooks, Wave, Zoho Books, Sage)
hr_payroll.json        (6 vendors: Gusto, Rippling, BambooHR, Deel, Remote, Oyster)
marketing.json         (6 vendors: Mailchimp, Klaviyo, HubSpot Marketing, Brevo, ConvertKit, Drip)
project_management.json (6 vendors: Asana, Monday, ClickUp, Notion, Linear, Basecamp)
```

### AI Tools (`/backend/src/knowledge/ai_tools/`)
```
llm_providers.json     (Anthropic, OpenAI, Google, Mistral, Cohere - with model pricing)
```

### Benchmarks (`/backend/src/knowledge/benchmarks/`)
```
tech_saas.json              (~39KB, 3 company sizes, sourced metrics)
ecommerce.json              (~36KB, 3 revenue tiers, sourced metrics)
professional_services.json  (~55KB, 3 company sizes, sourced metrics)
music_studios.json          (~69KB, 3 company sizes, sourced metrics)
```

---

## Remaining Work

### 1. Opportunity Templates (Priority: High)
Create opportunity template files in `/backend/src/knowledge/opportunities/`:

- `tech_saas.json` - 20 templates
- `ecommerce.json` - 15 templates
- `professional_services.json` - 15 templates
- `music_studios.json` - 15 templates

**Template Schema:**
```json
{
  "id": "customer-support-automation",
  "title": "AI-Powered Customer Support",
  "category": "efficiency|growth|cost_reduction|customer_experience|risk",
  "typical_findings": {
    "hours_saved_weekly": {"min": 10, "max": 40},
    "cost_reduction_percent": {"min": 20, "max": 50}
  },
  "relevant_if": ["condition1", "condition2"],
  "recommended_solutions": {
    "off_the_shelf": {"tools": [], "cost_range": "", "pros": [], "cons": []},
    "best_in_class": {"tools": [], "cost_range": "", "pros": [], "cons": []},
    "custom": {"approach": "", "cost_range": "", "pros": [], "cons": []}
  },
  "implementation_notes": "",
  "quick_win": false
}
```

---

## Key Functions Available

### Knowledge Module (`src/knowledge/__init__.py`)
```python
# Vendor functions
search_vendors(query, category, company_size, max_price, has_free_tier)
get_vendor_by_slug(slug)
get_all_vendors(categories)
compare_vendors(slugs)
load_vendor_category(category)
list_vendor_categories()

# LLM functions
get_llm_providers()
get_llm_provider(slug)
estimate_llm_cost(provider_slug, model_id, input_tokens, output_tokens)

# Industry functions (backward compatible)
get_industry_context(industry)
get_relevant_opportunities(industry, pain_points)
get_benchmarks_for_metrics(industry, metric_category)
get_vendor_recommendations(industry, category)
normalize_industry(industry)
```

### Vendor Service (`src/services/vendor_service.py`)
```python
# File-based KB functions (use these)
search_vendors_kb(query, category, company_size, max_price, has_free_tier, limit)
get_vendor_kb(slug)
compare_vendors_kb(slugs)
get_vendors_for_use_case(use_case, budget_monthly, company_size, prefer_free, limit)
get_category_overview(category)
get_llm_recommendation(use_case, monthly_volume, priority)
get_knowledge_stats()
```

---

## Testing

```bash
cd backend

# Test knowledge module
python -c "from src.knowledge import get_all_vendors, get_llm_providers; print(f'Vendors: {len(get_all_vendors())}'); print(f'LLM providers: {len(get_llm_providers())}')"

# Test vendor service
python -c "from src.services.vendor_service import get_knowledge_stats; print(get_knowledge_stats())"

# Test research tools
python -c "
import asyncio
from src.tools.research_tools import search_vendor_solutions
result = asyncio.run(search_vendor_solutions({'category': 'automation'}, {}, 'test'))
print([v['name'] for v in result['vendors']])
"
```

---

## Notes

- All vendor pricing verified December 2025
- Currency: USD (EUR conversion can be added later)
- Backward compatibility maintained with existing industry folders
- `verified_at` timestamps on all vendor entries for freshness tracking
