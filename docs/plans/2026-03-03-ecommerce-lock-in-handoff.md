# E-commerce Lock-In — Handoff for Remaining Work

**Date:** 2026-03-03
**Status:** Weeks 1-4 complete. Weeks 5-6 remain.
**Tests:** 936 passed, 0 failed (full backend suite)
**Source plan:** `docs/plans/2026-03-03-ecommerce-sales-lock-in.md`

---

## What's Done (Weeks 1-4)

### Week 1: Domain Locked, Defaults Fixed
- `frontend/src/pages/LandingHome.tsx` — Replaced 4-industry grid with `<Navigate to="/ecommerce" replace />`
- All 9 `"professional-services"` defaults flipped to `"ecommerce"` across 7 backend files + `VoiceQuizInterview.tsx`
- Hourly rate: EUR 35 → EUR 55 in `crb_calculation_service.py` (both `ecommerce` and `e-commerce` slugs)
- New quiz question `average_team_cost` added to `industry_questions/ecommerce.json` (after `team_size`)
- `get_effective_hourly_rate()` wired to read `average_team_cost` answer (step 2b, between salary and industry default)
- Verdict adjustments: `ai_readiness_boost` 3→5, `risk_tolerance` "medium"→"medium-high", context_note updated
- Admin UI: `KnowledgeEditor.tsx` and `KnowledgeStats.tsx` default to ecommerce

### Week 2: Knowledge Gaps Filled
- **Marketing Attribution** opportunity (`ai-marketing-attribution`) added to `ecommerce/opportunities.json` — full AIOS format
- **Subscription Management** opportunity (`ai-subscription-management`) added — churn, retention, personalization
- **14 EU tools** added to `existing_stack.py` ECOMMERCE_SOFTWARE: Sendcloud, Picqer, Mollie, Channable, Squarespace, Wix, Bol.com, Zalando, Kaufland, Lifetimely, Polar Analytics, Loop Returns, ReturnGO
- **5 vendor entries** added to `ecommerce/vendors.json`: Squarespace, Wix, Magento/Adobe Commerce (platforms), Recharge, Bold (new subscription-management category)
- **11 curated insights** created in new `insights/curated/ecommerce.json`: 4 trends, 2 case studies, 3 statistics, 2 quotes — all tagged `industries: ["ecommerce"]`

### Week 3: Pipeline Quality
- `competitor_analyzer.py` — ecommerce entry in `INDUSTRY_AI_ADOPTION` (52% adoption, Shopify/HubSpot 2025) + 3 new `AI_IMPLEMENTATION_AREAS` (product_descriptions, personalization, inventory_forecasting)
- `ai_readiness_calculator.py` — Platform-aware bonus in `_calculate_tech_stack_score()`: Shopify +4, WooCommerce/BigCommerce +3, Magento +2, Squarespace/Wix +0. Point budget rebalanced (16+10+4=30)
- `crb_analysis_v1.py` — Added "Marketing attribution" and "Subscription management and churn" to pain_points, EUR budget_range, EU compliance key_metric, EU logistics tools
- Curated insights filtering verified — already works via `industries` tag in `insight_service.py`

### Week 4: Tests
- `test_report_service.py` — 7 new ecommerce tests (hourly rate, user override, verdict adjustments, competitor analysis, curated insights existence/content/tagging)
- `test_e2e_verticals.py` — 14 new tests: opportunities cover landing page promises (chatbot, inventory, returns, attribution, subscriptions), EU tools in stack picker, quiz platforms in stack picker, vendor KB covers quiz platforms, hourly rate quiz answer midpoints
- `test_crb_calculation_service.py` — Updated ecommerce rate expectations (35→55)
- All existing tests updated for new hourly rate

---

## What Remains (Weeks 5-6)

### Week 5: Customer Experience Polish

#### 5.1 Sharpen landing page copy
**File:** `frontend/src/pages/industries/Ecommerce.tsx`
- This is now the de facto landing page (LandingHome.tsx redirects to /ecommerce)
- Update hero to align with lock-in messaging: "Stop automating the wrong things"
- Add social proof section (even placeholder: "Built on analysis of X e-commerce operations")
- Ensure sample report links work and show strong ecommerce output
- Add EU credibility signals

#### 5.2 Ecommerce quiz copy
**File:** `frontend/src/pages/Quiz.tsx` lines 187-200 (`INDUSTRY_COPY`)
- Tighten ecommerce copy — progress step labels should use store language ("Your Store", "Your Operations", "Your Stack")
- Remove dental and professional-services from `INDUSTRY_COPY` and `industryHooks` (lines ~1212-1237)
- **Note:** Quiz.tsx is 2,400+ lines. Use offset/limit to read specific sections.

#### 5.3 Workshop question tuning
**Files:**
- `backend/src/skills/workshop/question_skill.py` — Ensure follow-up questions are ecommerce-specific ("Tell me about your return handling process", "How do you manage inventory across channels?")
- `backend/src/skills/workshop/milestone_skill.py` — Milestone templates should reference ecommerce deliverables

#### 5.4 Clean navigation
- `frontend/src/App.tsx` + any nav components — Remove all links to non-ecommerce vertical pages
- `frontend/src/pages/ReportViewer.tsx` — Keep `INDUSTRY_DISPLAY_NAMES` for backward compat (existing reports) but ensure new reports display ecommerce branding
- The "All Industries" link on each industry page points to `/` which already redirects to `/ecommerce`, so those are already handled

### Week 6: Beta Test & Sales Readiness

#### 6.1-6.3 Beta testing (manual)
- Run 3 beta reports with real e-commerce businesses
- Fix feedback (budget 10 hours)
- Create sanitized showcase report

#### 6.4 Update expertise data
**File:** `backend/src/expertise/data/industries/ecommerce.json`
- Update `total_analyses` and pain_point frequencies from internal + beta reports
- Move confidence from "medium" toward "high" where patterns confirmed

#### 6.5 Final smoke test checklist
- [ ] Root URL → ecommerce landing (**DONE**)
- [ ] Quiz defaults to ecommerce (**DONE**)
- [ ] Stack picker shows EU tools (**DONE**)
- [ ] Report uses correct hourly rate (**DONE**)
- [ ] Competitor analysis = ecommerce-specific (**DONE**)
- [ ] ROI numbers credible (needs manual audit)
- [ ] Zero "professional-services" defaults (**DONE**)
- [ ] Checkout works at EUR 147 (needs manual test)
- [ ] Report delivery email correct (needs manual test)
- [ ] Full test suite green: **936 passed** (**DONE**)

### Plan section 1.5 (skipped — docs updates)
- `PRODUCT.md` lines 131-269 — Replace "Parallel Launch Strategy" with e-commerce focus section
- `STRATEGY.md` lines 96-137 — Replace "Parallel Vertical Launch" with "E-commerce Lock-In" section

---

## Key Technical Details for Next Session

### Files that are large — use offset/limit:
- `report_service.py` — 4,000+ lines
- `Quiz.tsx` — 2,400+ lines
- `quiz.py` routes — 2,400+ lines

### What NOT to break:
- Routes for `/dental`, `/professional-services`, `/b2b-platforms` are alive (backward compat for existing sessions/bookmarks)
- Other vertical knowledge bases stay on disk (loaded dynamically, zero cost when unused)
- `INDUSTRY_VERDICT_ADJUSTMENTS` dict still has entries for all industries (fallback uses ecommerce now)

### Hourly rate resolution order:
1. Explicit `hourly_rate` from quiz → user-provided
2. `salary` from quiz → derived
3. `average_team_cost` from quiz → midpoint of range (NEW)
4. Industry default → EUR 55 for ecommerce
5. Global fallback → EUR 50

### Run tests with:
```bash
cd backend && pytest tests/ -v --ignore=tests/test_telegram_*.py --ignore=tests/test_rls_policy_hardening.py
```
