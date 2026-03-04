# Database Audit Handoff

## What's Done

### Industry Cleanup (COMPLETE)
- Deleted old industry files: knowledge/home-services/, expertise data, question banks, import scripts
- Updated ~50 backend/frontend/test files to remove general, home-services, marketing-agencies + all other non-primary industries
- Only 4 industries remain: `professional-services`, `dental`, `ecommerce`, `b2b-platforms`
- `normalize_industry()` now raises `ValueError` for unsupported industries
- All 866 backend tests pass

### DB Audit CLI (PARTIALLY COMPLETE)
- Created `backend/src/cli/db_audit.py` — audit + fix tool
- Added Makefile targets: `make db-audit`, `make db-audit-fix`
- Integrated into `auto_refresh all` pipeline as Step 4
- Fixed `knowledge_embeddings` column name bug (`source_id` → `source_file`)

## What's Left

### 1. Fix vendor normalization for `*` (cross-industry) vendors
The `fix_vendors()` function in `db_audit.py` needs the `*` case handled:
- Vendors with `industries: ["*"]` should become `industries: ["professional-services", "dental", "ecommerce", "b2b-platforms"]`
- Currently the `_normalize_vendor_industry("*")` returns `None` — the fix function needs to detect this and set all 4 industries
- Simple fix: in `fix_vendors()`, check if `current == ["*"]` and set `new_industries = SUPPORTED_INDUSTRIES`

### 2. Fix `industry_vendor_tiers` normalization
The `fix_industry_vendor_tiers()` currently deletes invalid rows. But 129/168 rows have display names like "SaaS", "E-commerce", "Financial Services" instead of slugs. Should normalize them using `_INDUSTRY_NORMALIZATION` map instead of deleting. Rows that can't be normalized should be deleted.

### 3. Run the fix
```bash
# Preview what will change
make db-audit-fix ARGS="--dry-run"

# Apply fixes
make db-audit-fix
```

### 4. Quiz sessions legacy data (31 rows)
- Quiz sessions with old industries (home-services, veterinary, recruiting, etc.) are historical data
- Decision needed: leave as-is (historical) or update the JSONB `answers.industry` field
- Recommendation: leave as-is, they're completed sessions

## Live Audit Results (2026-02-28)

| Table | Total | Clean | Dirty | Action |
|-------|-------|-------|-------|--------|
| supported_industries | 8 | 2 | 6 | DELETE 6 old, INSERT 2 missing (ecommerce, b2b-platforms) |
| vendors | 244 | 37 | 207 | Normalize display names → slugs |
| industry_vendor_tiers | 168 | 39 | 129 | Normalize display names → slugs |
| workflow_templates | 19 | 19 | 0 | Clean |
| knowledge_embeddings | ? | ? | ? | Re-run after column fix |
| quiz_sessions | 373 | 342 | 31 | Legacy data, leave as-is |
| reports | 107 | 107 | 0 | Clean |

## Key Files
- `backend/src/cli/db_audit.py` — the audit/fix CLI
- `backend/src/cli/auto_refresh.py` — now includes DB audit as Step 4
- `backend/src/knowledge/__init__.py` — source of truth for SUPPORTED_INDUSTRIES
- `Makefile` — `db-audit`, `db-audit-fix`, `data-refresh-cron` targets
