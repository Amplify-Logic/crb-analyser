# Product Audit Handoff - 2026-02-14

## What Was Done

Comprehensive 6-agent parallel audit of the entire CRB Analyser codebase covering:
- Backend services (report_service, quiz_engine, crb_calculation, vendor_service, etc.)
- Skills system (all skills under analysis/, interview/, workshop/, report-generation/)
- API routes (all route files + main.py registration)
- Frontend (landing pages, quiz, report viewer, admin, auth)
- Tests & knowledge base data quality
- Report generation pipeline (the core deliverable)

## Target Verticals (Confirmed by User)

**Professional Services, Dental, E-Commerce** - these are the 3 launch verticals.

---

## Critical Findings (Priority Order)

### P0: Launch Blockers

#### 1. E-Commerce Knowledge Base MISSING
- Frontend page exists at `/ecommerce` with full UI, messaging, sample findings
- **Backend has NO knowledge base** - no `backend/src/knowledge/ecommerce/` folder
- No quiz question bank (`ecommerce.json` missing from `industry_questions/`)
- Backend `PRIMARY_INDUSTRIES` in `knowledge/__init__.py` lists `home-services` instead of `ecommerce`
- E-commerce is marked as "DROPPED" in backend code comments
- **Users can start the quiz but will get generic/broken analysis**
- **Fix:** Create benchmarks.json, processes.json, opportunities.json, vendors.json for ecommerce + question bank + update PRIMARY_INDUSTRIES

#### 2. NET SCORE Formula Not Implemented
- PRODUCT.md defines: `NET SCORE = Benefit Score - Cost Score - (Risk Score / 10)`
- This formula exists NOWHERE in the code
- Three Options are generated without objective comparison scores
- The core CRB framework promise ("makes the best option obvious") is not delivered
- **Fix:** Implement as SyncSkill, apply to each of the three options

#### 3. Hardcoded €50/hr Rate for All Customers
- `crb_calculation_service.py:32`: `DEFAULT_HOURLY_RATE_EUR = 50`
- Every ROI calculation uses this regardless of customer industry/country
- A €150/hr lawyer and a €20/hr e-commerce support agent get same ROI numbers
- **Fix:** Source hourly rate from quiz answers or industry defaults, not hardcoded

### P1: Report Accuracy Issues

#### 4. LLM Can Hallucinate Vendor Pricing
- `four_options.py:122-126`: Prompt says "Use REAL vendors with REAL pricing"
- But NO knowledge base vendor data is passed into the prompt
- LLM makes up prices with no constraint
- Vendor validation happens AFTER generation, not before
- **Fix:** Inject KB vendor catalog + prices into LLM prompt context

#### 5. CONFIDENCE_FACTORS Defined But Unused in report_service.py
- `report_service.py:100-104`: Factors defined (HIGH=1.0, MEDIUM=0.85, LOW=0.70)
- These are correctly applied in `roi_calculator.py:392-394` (the skill)
- BUT report_service.py defines them separately and never uses them
- Potential for double-application or missed application depending on code path
- **Fix:** Remove duplicate definition, ensure single source of truth in roi_calculator

#### 6. Silent Exception Swallowing in Report Pipeline
- `report_service.py:1024`: `except Exception: pass` - NO logging after critical platform matching
- `report_service.py:1118`: `except Exception: pass` - NO logging after automation finding
- `review_service.py:534`: bare `except: pass` - catches even KeyboardInterrupt
- **Impact:** Report sections can fail silently, producing incomplete reports
- **Fix:** Add logging to all catch blocks, use specific exception types

#### 7. Professional Services Vendors All Unverified
- `knowledge/professional-services/vendors.json`: ALL vendors have `"verified": false`
- No `verified_date` fields present
- Using unverified pricing data in reports
- **Fix:** Verify vendor pricing against websites, add verified_date fields

#### 8. Negative ROI Silently Capped to 0%
- `roi_calculator.py:389`: `roi_raw = max(roi_raw, 0)`
- Bad recommendations appear "neutral" instead of flagged as "don't do this"
- **Fix:** Keep negative ROI, mark finding as `is_not_recommended` when ROI < 0

#### 9. Currency Hardcoded to EUR
- `roi_calculator.py:500`: Breakdown shows "€" symbol for all markets
- Should use currency from context (GBP for UK, AUD for Australia, USD for USA)
- `base.py:27-49`: CURRENCY_SYMBOLS dict exists but skills don't use it
- **Fix:** Pass currency through context, use symbol from CURRENCY_SYMBOLS

### P2: Missing Framework Components

#### 10. Only 4 of 6 Cost Dimensions Tracked
- Financial Cost: tracked
- Time Cost: implicit in hidden costs
- Opportunity Cost: NOT tracked
- Complexity Cost: NOT tracked
- Risk Cost: tracked separately, not in CostBreakdown
- Brand/Trust Cost: NOT tracked
- **Fix:** Extend CRB data model to include all 6 cost types

#### 11. Vendor Matching Double-Counts Boosts
- `vendor_matching.py:710`: Tag matching boost
- `vendor_matching.py:787-792`: Integration compatibility boost
- Vendors matching BOTH get double-boosted unfairly
- **Fix:** Separate scoring, or cap total boost

#### 12. Platform Consolidation Ignores Existing Category
- User has Hubspot (CRM) -> skill may recommend Salesforce (also CRM)
- Checks specific vendor names but not categories
- **Fix:** Check by category, not just vendor name

### P3: Code Quality (50+ Issues)

#### 13. Bare `except Exception:` Throughout Codebase
- 50+ instances across all services
- report_service.py alone has 30+ bare exception catches
- **Fix:** Replace with specific exception types (ValueError, KeyError, etc.)

#### 14. datetime.now() vs datetime.utcnow() Mixing
- `teaser_service.py:103`: Uses `datetime.now()` (LOCAL time)
- Most other services use `datetime.utcnow()`
- Causes stale data calculations to be wrong across timezones
- **Fix:** Use `datetime.utcnow()` consistently everywhere

#### 15. Model IDs Hardcoded in Skills
- `base.py:354`: Hardcoded `claude-sonnet-4-5-20250929`
- `insight_extraction.py:60`: Hardcoded model
- `workshop/question_skill.py:42`: Hardcoded model
- Should use `get_model_for_task()` from `model_routing.py`

### P4: Security

#### 16. Admin Routes Use `require_workspace` Instead of `require_admin`
- `admin.py:42-99`: Any logged-in user can access admin routes
- `admin_vendors.py`, `knowledge_admin.py`: Same issue
- **Fix:** Use `require_admin` dependency on all admin routes

#### 17. Quiz Email Lookup Has No Per-Email Rate Limiting
- `quiz.py:567`: `/sessions/resume` allows email enumeration
- Global rate limiting exists but not per-email
- **Fix:** Add per-email rate limiting

### P5: Frontend

#### 18. `/report/sample` Link Likely Broken
- All landing pages link to `/report/sample`
- No report with ID "sample" likely exists
- **Fix:** Create sample report or update links

#### 19. Console.log Statements in Production
- 10+ `console.error` / `console.warn` calls across pages
- Dashboard.tsx, Checkout.tsx, Workshop.tsx, ReportViewer.tsx, Quiz.tsx
- **Fix:** Remove or gate behind development check

#### 20. CheckoutSuccess Masks Verification Errors
- `CheckoutSuccess.tsx:38-42`: On error, sets `isVerified(true)` anyway
- User shown success even when verification fails
- **Fix:** Show error state, offer retry

### P6: Tests

#### 21. Weak Test Assertions in Auth/Payments
- Tests use `assert response.status_code in [200, 201, 400, 500]`
- Tests pass even on 500 errors
- **Fix:** Assert specific expected status codes

#### 22. CRB Calculation Service Has No Tests
- The core math producing financial figures for reports
- Most critical untested code
- **Fix:** Write comprehensive unit tests for all ROI/payback calculations

---

## Recommended Execution Order

### Phase 1: Make E-Commerce Launch-Ready (Day 1)
1. Create `backend/src/knowledge/ecommerce/` with all 4 required JSON files
2. Create `backend/src/knowledge/industry_questions/ecommerce.json`
3. Update `PRIMARY_INDUSTRIES` in `knowledge/__init__.py` to include ecommerce
4. Verify the quiz flow works end-to-end for ecommerce

### Phase 2: Fix Report Accuracy (Day 1-2)
5. Implement NET SCORE formula as SyncSkill
6. Make hourly rate customer-specific (from quiz data)
7. Inject KB vendor data into LLM prompts
8. Fix silent exception swallowing in report pipeline
9. Handle negative ROI properly (mark as not-recommended)
10. Fix currency handling for multi-market

### Phase 3: Data Quality (Day 2)
11. Verify professional-services vendor pricing
12. Verify dental vendor pricing
13. Create/verify ecommerce vendor data

### Phase 4: Tests for Critical Paths (Day 3)
14. Write tests for crb_calculation_service.py
15. Tighten auth/payments test assertions
16. Write tests for validation_service.py

### Phase 5: Code Quality & Security (Day 3-4)
17. Fix admin route authorization
18. Replace bare except blocks (start with report_service.py)
19. Fix datetime consistency
20. Fix model routing in skills

---

## Files Most Needing Attention

| File | Issues | Priority |
|------|--------|----------|
| `backend/src/knowledge/__init__.py` | PRIMARY_INDUSTRIES wrong | P0 |
| `backend/src/knowledge/ecommerce/` | Doesn't exist | P0 |
| `backend/src/services/crb_calculation_service.py` | Hardcoded rate, no NET SCORE | P0 |
| `backend/src/services/report_service.py` | 30+ bare exceptions, silent failures | P1 |
| `backend/src/skills/report-generation/three_options.py` | No NET SCORE, hallucination risk | P1 |
| `backend/src/skills/report-generation/four_options.py` | No KB context in prompts | P1 |
| `backend/src/skills/analysis/roi_calculator.py` | Negative ROI capped, EUR hardcoded | P1 |
| `backend/src/knowledge/professional-services/vendors.json` | All unverified | P1 |
| `backend/src/skills/analysis/vendor_matching.py` | Double-counting boosts | P2 |
| `backend/src/models/crb.py` | Missing 3 of 6 cost dimensions | P2 |
| `backend/src/routes/admin.py` | Wrong auth dependency | P4 |

---

## What NOT to Touch

- Three Options structure (correctly implemented)
- Connect vs Replace logic (correctly implemented)
- Confidence factors in roi_calculator.py (correctly applied)
- AI readiness formula calculation (correctly formula-based)
- Verdict thresholds and logic (correctly implemented)
- Automation summary aggregation (correct)
- Workshop/interview skills (working)

## Context

- Brand: **ReadyPath** by Amplify Logic AI
- Price: **€147** for quiz + 90-min workshop + human-reviewed report
- Landing: `LandingHome.tsx` (active), `Landing.tsx` (legacy/unused)
- User confirmed verticals: **Professional Services, Dental, E-Commerce**
