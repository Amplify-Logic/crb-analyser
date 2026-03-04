# Ecommerce Quiz & Workshop Optimization

> **Context**: CRB Analyser has pivoted to ecommerce-first but the quiz and workshop flows were built as generic/professional-services. This plan covers all changes needed to make the data collection pipeline ecommerce-native.

---

## Audit Summary

The report generation pipeline is solid — the bottleneck is **data collection quality**. If quiz and workshop collect generic professional-services data, the report inherits that weakness regardless of how good the ecommerce knowledge base is.

### What's Already Ecommerce-Aware
- `ecommerce.json` knowledge base: 15 ecommerce-specific questions (platform, order volume, cart abandonment, fulfillment, return rate, etc.)
- `question_skill.py` system prompt: has ecommerce-specific probes (returns, multi-channel inventory, fulfillment, CLV, attribution)
- `milestone_skill.py` system prompt: has ecommerce context (conversion benchmarks, WISMO, EU-specific framing)
- Software options endpoint: returns ecommerce-specific vendors when `industry=ecommerce`
- Frontend default industry: `'ecommerce'` in VoiceQuizInterview.tsx

### What's Still Generic (14 issues, priority-ordered)

---

## Task 1: Ecommerce Static Questionnaire [CRITICAL]

**File**: `backend/src/config/questionnaire.py`

**Problem**: The base questionnaire has professional-services placeholders ("partner reviews", "billable hours", "conflict checks", "law firm") across all 25 questions. No ecommerce branch exists.

**Fix**: Add an ecommerce questionnaire variant. When `industry=ecommerce`, return ecommerce-specific:

| Section | Generic Placeholder | Ecommerce Replacement |
|---------|--------------------|-----------------------|
| company_description | "commercial law firm" | "online store selling..." |
| main_processes | "client intake, document drafting, billing, research" | "order processing, inventory management, customer support, marketing campaigns" |
| repetitive_tasks | "time entry, document formatting, client updates, invoice follow-ups" | "order confirmations, shipping updates, return processing, product listing updates, inventory reconciliation" |
| biggest_bottlenecks | "partner reviews, document turnaround, client intake" | "cart abandonment recovery, returns processing, inventory forecasting, multi-channel sync" |
| biggest_challenge | "Partner time on admin, capturing billable hours" | "Cart abandonment is our biggest revenue leak — customers add items but don't complete checkout" |
| time_wasters | "Time entry, conflict checks, document formatting, chasing payments, scheduling" | "Manual order tracking updates, returns processing, inventory counting, product description writing, support ticket triage" |
| missed_opportunities | "Business development, responding to RFPs faster" | "Personalised product recommendations, abandoned cart recovery, repeat purchase campaigns, upsell/cross-sell at checkout" |

Also update **Section 3 `current_tools`** multiselect options for ecommerce:
- Replace `crm/project_management/accounting/email_marketing/social_media/ecommerce/spreadsheets/communication/analytics/other`
- With: `ecommerce_platform/email_marketing/helpdesk/reviews_ugc/analytics/ads_platform/inventory_management/shipping_fulfillment/returns_management/subscriptions/spreadsheets/other`

And update **Section 5 `cost_concerns`** multiselect for ecommerce:
- Replace `labor/software/marketing/overhead/inventory/outsourcing`
- With: `shipping_logistics/returns_processing/customer_acquisition/software_subscriptions/inventory_waste/marketing_spend/manual_labor/marketplace_fees`

---

## Task 2: Wire ecommerce.json Questions into Quiz Flow [CRITICAL]

**File**: `backend/src/routes/quiz.py` (dynamic questions generation)

**Problem**: The 15 rich ecommerce questions in `backend/src/knowledge/industry_questions/ecommerce.json` are never served to users. The quiz questions phase uses AI-generated questions from the pre-research agent instead.

**Fix**: When industry is `ecommerce`, inject key ecommerce.json questions into the dynamic question flow. At minimum, ensure these always get asked:
- `ecommerce_platform` (Shopify/WooCommerce/Magento/etc.)
- `monthly_order_volume`
- `cart_abandonment_rate`
- `sales_channels` (own site, Amazon, eBay, social, wholesale)
- `customer_service_volume`
- `fulfillment_method`
- `return_rate`

These are the high-signal questions that directly drive report quality. The AI can still generate additional discovery questions, but these should be guaranteed.

---

## Task 3: Pain Point Label Map for Ecommerce [CRITICAL]

**File**: `backend/src/routes/workshop.py` — `_get_pain_point_label()` function

**Problem**: Label map only has professional-services terms:
```python
labels = {
    "reporting": "Client Reporting",
    "lead_followup": "Lead Follow-up",
    "proposals": "Proposal Generation",
    "scheduling": "Scheduling & Coordination",
    "data_entry": "Data Entry",
    "customer_support": "Customer Support",
    "invoicing": "Invoicing & Billing",
    "onboarding": "Client Onboarding",
}
```

**Fix**: Add ecommerce pain point labels:
```python
ecommerce_labels = {
    "cart_abandonment": "Cart Abandonment Recovery",
    "returns": "Returns & Refund Processing",
    "inventory": "Inventory Management",
    "fulfillment": "Order Fulfillment & Shipping",
    "support": "Customer Support & WISMO",
    "product_content": "Product Content & Descriptions",
    "personalization": "Product Recommendations & Personalization",
    "marketing": "Marketing Automation & Attribution",
    "multi_channel": "Multi-Channel Management",
    "subscription_churn": "Subscription Churn Prevention",
    "pricing": "Dynamic Pricing & Promotions",
    "reviews": "Reviews & Social Proof",
    "customer_retention": "Customer Retention & Loyalty",
    "catalog": "Catalog & Data Quality",
}
```

Use industry-aware lookup: check `answers.get("industry")` and pick the right label map.

---

## Task 4: Ecommerce Tool Detection [CRITICAL]

**File**: `backend/src/routes/workshop.py` — milestone endpoint tool detection + confidence scoring

**Problem**: Only detects 9 generic tools: hubspot, salesforce, slack, excel, google, zapier, notion, asana, monday. An ecommerce store discussing Shopify, Klaviyo, and Gorgias scores 0 on tech confidence.

**Fix**: Add ecommerce tool detection:
```python
ecommerce_tools = [
    "shopify", "woocommerce", "magento", "bigcommerce", "squarespace",
    "klaviyo", "mailchimp", "omnisend", "drip",
    "gorgias", "zendesk", "freshdesk", "intercom",
    "yotpo", "okendo", "stamped", "loox",
    "recharge", "bold", "skio",
    "shipstation", "shipbob", "aftership", "easyship",
    "returnly", "loop", "narvar",
    "triple whale", "northbeam", "polar analytics",
    "channable", "feedonomics", "bazaarvoice",
    "algolia", "searchspring", "nosto",
    "loyaltylion", "smile.io",
]
```

Use industry-aware tool list: generic tools + ecommerce tools when `industry == "ecommerce"`.

---

## Task 5: Revenue-Based ROI Schema [CRITICAL]

**File**: `backend/src/skills/workshop/milestone_skill.py`

**Problem**: ROI calculation is always `hours_per_week × hourly_rate × 52`. For ecommerce, the biggest wins are revenue-based: recovered abandoned carts, prevented returns, increased AOV, improved LTV.

**Fix**: Add revenue-based ROI fields to the milestone schema:
```json
{
    "roi": {
        "hours_per_week": 5,
        "hourly_rate": 75,
        "annual_time_cost": 19500,
        "revenue_impact": {
            "metric": "cart_abandonment_recovery",
            "current_value": "72% abandonment, 3% recovery",
            "projected_value": "72% abandonment, 12% recovery",
            "monthly_revenue_gain": 8500,
            "annual_revenue_gain": 102000,
            "calculation": "850 abandoned carts/mo × 9% improvement × €65 AOV"
        },
        "total_annual_value": 121500,
        "savings_percentage": 65,
        "calculation_notes": "Combined time savings + revenue recovery"
    }
}
```

Update the milestone system prompt to calculate revenue impact when the pain point is revenue-related (cart abandonment, returns, personalization, marketing attribution) and time savings when it's operational (fulfillment, support, inventory management).

---

## Task 6: Vendor Category Map for Ecommerce [CRITICAL]

**File**: `backend/src/skills/workshop/milestone_skill.py` — `PAIN_TO_CATEGORY_MAP`

**Problem**: Missing ecommerce keywords. When a pain point is "cart abandonment", the vendor lookup returns nothing because `cart` isn't in the map.

**Fix**: Add ecommerce keyword mappings:
```python
# Ecommerce additions
"cart": "conversion_optimization",
"abandonment": "conversion_optimization",
"checkout": "conversion_optimization",
"conversion": "conversion_optimization",
"inventory": "inventory_management",
"stock": "inventory_management",
"warehouse": "inventory_management",
"fulfillment": "shipping_fulfillment",
"shipping": "shipping_fulfillment",
"logistics": "shipping_fulfillment",
"returns": "returns_management",
"refund": "returns_management",
"recommendations": "personalization",
"personalization": "personalization",
"upsell": "personalization",
"subscription": "subscription_management",
"churn": "subscription_management",
"retention": "customer_retention",
"loyalty": "customer_retention",
"marketplace": "marketplace_management",
"amazon": "marketplace_management",
"product": "content_management",
"description": "content_management",
"catalog": "content_management",
"wismo": "customer_support",
"tracking": "customer_support",
"review": "reviews_ugc",
```

Ensure corresponding vendor categories exist in the vendor database.

---

## Task 7: Ecommerce Quick-Reply Suggestions [HIGH]

**File**: `backend/src/routes/workshop.py` — `_get_stage_suggestions()`

**Problem**: Suggestions are generic professional-services language. "It's mostly manual — someone handles it each time" for cart abandonment.

**Fix**: Add ecommerce-specific suggestions per stage, keyed by pain point category:

**For cart_abandonment:**
| Stage | Suggestion |
|-------|-----------|
| current_state | "We have a basic Klaviyo flow but recovery is under 5%" |
| current_state | "We send one email 24hrs after — nothing else" |
| failed_attempts | "Tried SMS recovery but didn't see enough lift" |
| cost_impact | "At our AOV of €65, even 5% more recovery is huge" |
| ideal_state | "Multi-touch: email, SMS, dynamic discount ladder" |

**For returns:**
| Stage | Suggestion |
|-------|-----------|
| current_state | "Customer emails us, we send a label manually" |
| current_state | "Self-service portal but still manual restocking" |
| cost_impact | "Each return costs us €15-20 in shipping + handling" |
| ideal_state | "Automated exchanges instead of refunds" |

**For inventory:**
| Stage | Suggestion |
|-------|-----------|
| current_state | "We reorder based on gut feel and last year's numbers" |
| cost_impact | "Overstocked 30% on slow movers last quarter" |
| ideal_state | "Demand forecasting with seasonal patterns" |

Detect pain point category from label, then return category-specific suggestions. Fall back to generic if no match.

---

## Task 8: Ecommerce Interview Questions [HIGH]

**Files**:
- `frontend/src/pages/VoiceQuizInterview.tsx` — `generateQuestions()`
- `backend/src/routes/interview.py` — `INTERVIEW_TOPICS`

**Problem**: 5 hardcoded generic questions. Backend has 5 generic topic categories. No ecommerce-specific questions.

**Fix Frontend** — Replace `generateQuestions` with industry-aware version. When `industry === 'ecommerce'`:
1. "I've done some research on {company}. Tell me about your store — what do you sell and who's your typical customer?"
2. "Walk me through what happens from when a customer lands on your site to when they receive their order. Where do things break down?"
3. "What's your biggest revenue leak right now — cart abandonment, returns, low repeat purchases, something else?"
4. "How do you handle customer support? What percentage of tickets could be automated?"
5. "If you could fix one thing about your operations before {peak_season}, what would it be?"

**Fix Backend** — Add ecommerce interview topics:
```python
ECOMMERCE_INTERVIEW_TOPICS = {
    "store_operations": [
        "Walk me through a typical day managing your store",
        "What's your order volume and how do you handle fulfillment?",
        "How do you manage inventory across channels?",
    ],
    "revenue_leaks": [
        "What's your cart abandonment rate and what recovery do you have?",
        "What's your return rate and how does the process work?",
        "Where are you losing the most money right now?",
    ],
    "customer_experience": [
        "How do you handle customer support — what are the top ticket types?",
        "How do you personalize the shopping experience?",
        "What does your post-purchase experience look like?",
    ],
    "marketing_growth": [
        "What marketing channels drive your best customers?",
        "How do you measure marketing ROI after iOS changes?",
        "What's your repeat purchase rate and how do you drive retention?",
    ],
    "technology_readiness": [
        "What does your tech stack look like — platform, email, support, analytics?",
        "What integrations are working well and which are painful?",
        "Have you tried any AI tools for your store?",
    ],
}
```

---

## Task 9: Ecommerce Smart Acknowledgments [HIGH]

**File**: `frontend/src/pages/VoiceQuizInterview.tsx` — `getSmartAcknowledgment()`

**Problem**: Pattern-matches for generic terms (spreadsheet, CRM, manual). No ecommerce vocabulary.

**Fix**: Add ecommerce patterns:
```typescript
// Ecommerce patterns
if (/cart\s*abandon|abandoned\s*cart/i.test(text)) return "Cart abandonment is one of the biggest revenue leaks in e-commerce — great area to focus on."
if (/shopify/i.test(text)) return "Shopify has a strong app ecosystem we can leverage."
if (/klaviyo/i.test(text)) return "Klaviyo is powerful for email — the question is whether you're using its full potential."
if (/return|refund/i.test(text)) return "Returns are a margin killer. There's a lot of automation potential there."
if (/inventory|stock/i.test(text)) return "Inventory management is where AI forecasting can really shine."
if (/fulfillment|shipping/i.test(text)) return "Shipping and fulfillment is ripe for automation."
if (/wismo|where.*order/i.test(text)) return "'Where is my order' tickets are one of the easiest things to automate."
if (/subscription|recurring/i.test(text)) return "Subscription businesses have unique churn challenges — interesting area."
if (/aov|average.*order/i.test(text)) return "Increasing AOV is often the fastest path to profitability."
```

---

## Task 10: Workshop Stage Guidance for Ecommerce [MEDIUM]

**File**: `backend/src/skills/workshop/question_skill.py` — stage guidance templates

**Problem**: Stage guidance is generic. For `cost_impact` it asks "Hours per week? Impact on revenue?" — should be more specific for ecommerce pain points.

**Fix**: Add ecommerce-aware stage guidance. When industry is ecommerce, detect pain point category and use targeted guidance:

**cart_abandonment + cost_impact**: "Quantify: What's your cart abandonment rate? Current recovery rate from existing flows? AOV? Monthly unique carts? Calculate: abandoned_carts × recovery_improvement × AOV = monthly revenue gain."

**returns + cost_impact**: "Quantify: What's your return rate? Cost per return (shipping + handling + restocking)? What % of returns are preventable (wrong size, wrong color, looked different)?"

**inventory + cost_impact**: "Quantify: What % of inventory becomes dead stock annually? Value of overstock write-downs last year? Cost of stockouts (lost sales)?"

---

## Task 11: Synthesis Form Ecommerce Questions [MEDIUM]

**File**: `frontend/src/components/workshop/SynthesisForm.tsx`

**Problem**: 3 generic final questions (stakeholders, timeline, additions).

**Fix**: For ecommerce, replace or augment with:
1. "Who else needs to be involved in this decision?" (keep)
2. "When are you looking to implement? Do you have a peak season deadline (e.g., BFCM, holiday)?"
3. "What's your biggest concern about implementing AI in your store — cost, complexity, or something else?"

---

## Task 12: Ecommerce Preliminary Results [MEDIUM]

**File**: `backend/src/routes/quiz.py` — `_calculate_preliminary_results()`

**Problem**: Value potential is same for all industries. An ecommerce store with €2M revenue and 72% cart abandonment has far higher potential than the generic €35K estimate for 11-50 employees.

**Fix**: When industry is ecommerce, adjust value potential based on:
- Revenue range → higher base potential (ecommerce has more automation surface)
- Cart abandonment severity → multiply potential
- Order volume → more orders = more automation value per unit
- Return rate → high returns = high recovery potential

Example: 11-50 employee ecommerce store with €2M-5M revenue → €55K-85K base (vs generic €35K).

---

## Task 13: Quiz Findings Display — Ecommerce Signals [MEDIUM]

**File**: `frontend/src/pages/Quiz.tsx` — findings display phase

**Problem**: Shows generic business fields after research. No ecommerce-specific signals highlighted.

**Fix**: When industry is ecommerce, add extracted signals:
- Detected Platform: Shopify Plus / WooCommerce / Magento
- Estimated Monthly Orders: (from traffic/alexa data if available)
- Sales Channels Detected: (from tech stack scraping)
- Payment Providers: (Stripe, Klarna, PayPal detected)

---

## Task 14: Frontend Quiz Copy — Always Ecommerce [LOW]

**File**: `frontend/src/pages/Quiz.tsx` — website entry phase

**Problem**: Ecommerce copy only shown when `?industry=ecommerce` URL param is set. Direct visitors to `/quiz` see generic copy.

**Fix**: Since we're ecommerce-first, default the copy to ecommerce. Change the condition from checking URL param to defaulting to ecommerce copy. Users from other verticals (dental, b2b) arriving via their industry page still get their copy from URL param.

---

## Execution Order

1. **Tasks 1-6** (Critical) — Do these first, they directly impact report data quality
2. **Tasks 7-9** (High) — These improve the real-time user experience during data collection
3. **Tasks 10-14** (Medium/Low) — Polish and optimization

**Estimated scope**: ~500-700 lines of code changes across 8-10 files. No schema migrations needed. No new dependencies.

---

## Files Touched

| File | Tasks |
|------|-------|
| `backend/src/config/questionnaire.py` | 1 |
| `backend/src/routes/quiz.py` | 2, 12 |
| `backend/src/routes/workshop.py` | 3, 4, 7 |
| `backend/src/skills/workshop/milestone_skill.py` | 5, 6 |
| `backend/src/skills/workshop/question_skill.py` | 10 |
| `backend/src/routes/interview.py` | 8 |
| `frontend/src/pages/VoiceQuizInterview.tsx` | 8, 9 |
| `frontend/src/pages/Quiz.tsx` | 13, 14 |
| `frontend/src/components/workshop/SynthesisForm.tsx` | 11 |
