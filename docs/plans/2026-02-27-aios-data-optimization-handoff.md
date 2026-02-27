# AIOS Data Optimization — Handoff for Next Session

> Written: 2026-02-27
> Plan: `docs/plans/2026-02-27-aios-data-optimization-design.md`
> Status: **Batches 1-5 complete, Batches 6-7 remaining**

---

## What Was Done (Batches 1-5)

### Batch 1: Database Migrations ✅
Created 4 SQL migration files in `backend/supabase/migrations/`:
- `021_vendor_aios_fields.sql` — 7 new columns on vendors (mcp_server_slug, mcp_server_maturity, claude_code_compatible, agent_buildable, agent_patterns, data_portability, aios_readiness_score) + 3 indexes
- `022_vendor_integrations.sql` — New `vendor_integrations` table (connection graph between vendors) with RLS
- `023_workflow_templates.sql` — New `workflow_templates` table with GIN indexes + RLS
- `024_reports_aios_assessment.sql` — Added `aios_maturity` + `readiness_profile` JSONB columns to reports table
- **Note:** `system_architecture` column already existed (migration 007)
- **Migrations NOT yet run on Supabase** — just files created

### Batch 2: Vendor Enrichment Script ✅
- Created `backend/scripts/enrich_vendors_aios.py`
- Cross-references `knowledge/platforms/mcp_ecosystem.json` with vendor slugs
- Calculates `aios_readiness_score` (1-10) from API openness, webhooks, MCP, OAuth, integrations
- Derives `data_portability` from `api_openness_score`
- Run with: `python -m scripts.enrich_vendors_aios` (after migrations are applied)

### Batch 3: AIOS Knowledge Base ✅
Created `backend/src/knowledge/aios/` with 10 JSON files:
- `layers.json` — 7-layer AIOS framework definition + assessment criteria
- `maturity_model.json` — Assessment rubric with transition paths, gap templates
- `context_os_templates.json` — Per-industry templates (professional-services, dental, ecommerce, coaching)
- `skills_catalog.json` — 17 skill templates across 4 industries
- `dashboard_patterns.json` — 3 dashboard patterns (Notion, Claude Project, Custom Web App)
- `education/claude_code_guide.json` — Getting started with Claude Code
- `education/cowork_guide.json` — Using Claude Cowork
- `education/skills_creation.json` — Creating custom skills
- `education/context_os_setup.json` — Building your Context OS
- `education/mcp_setup_guides.json` — Per-vendor MCP setup instructions

### Batch 4: Workflow Template Sync ✅
Added to `backend/src/knowledge/__init__.py`:
- AIOS KB loading: `get_aios_layers()`, `get_aios_maturity_model()`, `get_context_os_template()`, `get_skills_catalog()`, `get_dashboard_patterns()`, `get_education_module()`, `get_education_modules_for_maturity()`
- `get_all_workflow_templates()` — loads 19 workflows from 4 industry dirs, enriches with AIOS layers
- `sync_workflow_templates()` — async upsert to DB with content hash change detection

### Batch 5: System Architecture Skill ✅
Created `backend/src/skills/report-generation/system_architecture.py`:
- 10 Pydantic models: `ArchNode`, `ArchitectureLayers`, `ArchitectureConnection`, `AIOSMaturity`, `BuildPhase`, `SkillRecommendation`, `ContextOSTemplate`, `EducationModule`, `SystemArchitecture`
- `SystemArchitectureSkill` (SyncSkill, name="system-architecture") generates full 7-layer AIOS blueprint
- Wired into `report_service.py._generate_system_architecture()` with fallback to legacy `ArchitectureGenerator`
- `aios_maturity` saved to DB alongside `system_architecture`
- Verified: auto-discovered by skill registry, test execution produces valid output

---

## What Remains (Batches 6-7)

### Batch 6: Education + Skills + Context OS in Report Flow
**Task:** Add education path, skill recommendations, and Context OS generation to report flow
1. Add education path generation to report flow — select education modules based on AIOS maturity from `get_education_modules_for_maturity()`
2. Add skill recommendation generation — match industry + pain points to `get_skills_catalog()` entries
3. Add Context OS template generation — select appropriate template via `get_context_os_template()`
4. Update playbook generator (`backend/src/skills/analysis/playbook_generator.py`) to include skill-building tasks

**Key files:**
- `backend/src/services/report_service.py` (line ~1113: Phase 6c where architecture is generated — add new phases after)
- `backend/src/skills/analysis/playbook_generator.py`
- `backend/src/knowledge/__init__.py` (AIOS loading functions already exist)

**Note:** The system_architecture skill already generates `education_path`, `recommended_skills`, and `context_os_template` as part of its output. Batch 6 is about ensuring these flow into the final report data and playbooks properly. The data is already computed — it just needs to be:
- Stored in the report's partial_data
- Included in the final report JSON sent to the frontend
- Referenced in playbook generation

### Batch 7: Readiness Profile + Adaptive Recommendations
**Task:** Build readiness profile and update recommendation options with AIOS enrichment
1. Check if `_build_readiness_profile()` already exists — look at `backend/src/services/readiness_profile.py` (it's already imported in `_get_skill_context()` at line 259)
2. Store `readiness_profile` on report using the new JSONB column from migration 024
3. Enrich `AIOSConnectOption` model in `backend/src/models/recommendation.py` with: `aios_layers_touched`, `skills_created`, `context_needed`, `education_prereq`, `cowork_tasks`
4. Update `backend/src/skills/report-generation/three_options.py` prompt with readiness context
5. Test with different client profiles

**Key files:**
- `backend/src/services/readiness_profile.py` (may already exist)
- `backend/src/models/recommendation.py` (AIOSConnectOption model)
- `backend/src/skills/report-generation/three_options.py`
- `backend/src/services/report_service.py`

### Batch 8: Frontend (DEFERRED)
The plan explicitly says Batch 8 is "Handled by visual workflow builder terminal prompt" — skip it.

---

## How to Continue

```
/execute docs/plans/2026-02-27-aios-data-optimization-design.md
```

Then tell the new session:
> "Batches 1-5 are complete. Continue with Batch 6 (Task #6), then Batch 7 (Task #7). Read the handoff at `docs/plans/2026-02-27-aios-data-optimization-handoff.md` for details."

---

## Important Notes

- `readiness_profile.py` is already imported in report_service.py line 259 — check if it exists before building from scratch
- The system_architecture skill output already includes education_path, recommended_skills, and context_os_template — reuse this data rather than re-computing
- `aios_maturity` is already extracted from system_architecture output and saved to DB (implemented in Batch 5)
- Migrations have NOT been run on Supabase yet — just SQL files created
- Frontend (Batch 8) is explicitly deferred
