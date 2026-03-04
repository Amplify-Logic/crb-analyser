# Database Reference

> Load this when working on database schema, migrations, or Supabase queries.
> NOT here: vendor-specific tables → `vendor-management.md` | API route patterns → `api-development.md` | env vars, deployment, infra → [INFRASTRUCTURE.md](../../INFRASTRUCTURE.md)

---

## Database Schema

```
# Core Flow
quiz_sessions → reports → findings, recommendations, playbook
     ↓
  payments (Stripe)

# Vendor System (Supabase)
vendors ← industry_vendor_tiers (T1/T2/T3 per industry)
    ↓
vendor_audit_log

# Knowledge (Vector)
knowledge_embeddings (pgvector for RAG)

# Legacy (being deprecated)
workspace → clients → audits
```

### Key Tables

| Table | Purpose |
|-------|---------|
| `quiz_sessions` | Anonymous quiz responses, industry, scores |
| `reports` | Generated reports with token_usage, generation trace |
| `vendors` | Vendor catalog with pricing, features, ratings |
| `industry_vendor_tiers` | Which vendors are T1/T2/T3 for each industry |
| `knowledge_embeddings` | Vector embeddings for RAG retrieval |

---

## Migrations

### Location
```
backend/supabase/migrations/
├── 001_initial_schema.sql      # Core tables
├── 002_company_research.sql    # Research data
├── 003_quiz_sessions.sql       # Anonymous quiz
├── 004_reports.sql             # Report storage
├── 007_add_missing_report_columns.sql
├── 008_vector_embeddings.sql   # pgvector for RAG
├── 009_anonymous_flow.sql      # Anonymous user support
├── 010_update_report_status_constraint.sql
├── 011_add_generation_trace.sql
├── 012_vendor_database.sql     # Vendor tables
├── 013_adaptive_quiz.sql       # Adaptive quiz confidence
├── 014_workshop_columns.sql    # Workshop support
├── 015_vendor_api_openness.sql # Vendor API/integration scores
├── 016_existing_stack.sql      # User's current tech stack
└── 017_automation_summary.sql  # Automation roadmap data
```

### Create Migration
```bash
# Create new migration file
touch backend/supabase/migrations/XXX_description.sql

# Apply locally
supabase db push

# Apply to production
supabase db push --linked
```

### Rules
- Migrations must be reversible (include rollback comments)
- Never delete columns in production without deprecation period
- Test migration on local DB first
- Backup before applying to production

---

## Environment Variables & Debugging

> See [INFRASTRUCTURE.md](../../INFRASTRUCTURE.md) for full env var reference, health checks, and operational runbook.
