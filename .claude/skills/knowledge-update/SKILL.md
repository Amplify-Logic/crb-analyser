---
name: knowledge-update
description: Add or refresh industry benchmarks, trends, and curated insights in the knowledge base. Use for periodic knowledge maintenance, adding new research data, or updating stale benchmarks. Keywords - knowledge, benchmark, trends, insights, industry, data, refresh.
---

# Knowledge Base Update

## When to Use

- Adding new industry benchmarks or research data
- Refreshing stale benchmarks (source older than 6 months)
- Extracting insights from new content (articles, videos, reports)
- Adding data for a new industry vertical
- Periodic knowledge freshness maintenance

## Phase 1: Assess Current State

### Check Ecommerce Benchmark Freshness

```bash
cd backend && grep -r '"verified_date"\|"source_date"\|"date"' src/knowledge/ecommerce/ src/knowledge/benchmarks/ecommerce.json 2>/dev/null | head -30
```

### Check Insight Coverage

```bash
cd backend && python scripts/extract_insights.py --stats 2>/dev/null || echo "Run manually: check backend/src/knowledge/insights/curated/*.json"
```

### Check Industry Coverage

```bash
ls backend/src/knowledge/*/
```

Each industry should have: `benchmarks.json`, `processes.json`, `opportunities.json`, `vendors.json`, `workflows.json`

Present a summary of what's stale or missing.

## Phase 2: Update Benchmarks

### 2.1 Research New Data

For each stale benchmark, find updated sources:
- Use WebSearch for "ecommerce AI adoption statistics 2026"
- Use WebFetch to pull data from identified sources
- Prioritize: McKinsey, Gartner, Deloitte, industry associations, government stats

### 2.2 Update Benchmark Files

Edit `backend/src/knowledge/ecommerce/benchmarks.json` or `backend/src/knowledge/benchmarks/ecommerce.json`.

Every benchmark entry MUST include:

```json
{
  "metric": "AI-powered product recommendation conversion lift",
  "value": "15-25%",
  "source": "McKinsey Global Survey on AI, 2026",
  "source_url": "https://...",
  "verified_date": "2026-03",
  "confidence": "HIGH",
  "notes": "Survey of 1,200 firms globally"
}
```

### 2.3 Quality Rules

- [ ] Every stat has `source` and `verified_date`
- [ ] `verified_date` is YYYY-MM format
- [ ] `source_url` is a real, fetchable URL (not made up)
- [ ] `confidence` is HIGH/MEDIUM/LOW
- [ ] Values use ranges when source is imprecise ("30-40%" not "35%")
- [ ] Unverifiable data gets `"status": "UNVERIFIED"`

## Phase 3: Extract Insights from Content

When the user provides a new source (article, video transcript, report):

### 3.1 Save Raw Source

```bash
# Save to raw directory
cat > backend/src/knowledge/insights/raw/YYYY-MM-DD-source-name.txt << 'EOF'
[paste content here]
EOF
```

### 3.2 Extract Using CLI

```bash
cd backend && python scripts/extract_insights.py \
    --file src/knowledge/insights/raw/YYYY-MM-DD-source-name.txt \
    --title "Source Title" \
    --author "Author Name" \
    --date "YYYY-MM-DD"
```

### 3.3 Review Extractions

Read the output. For each extracted insight:
- Is it genuinely useful for reports? (not fluff)
- Is the attribution correct?
- Does it belong in the right category? (trend, framework, case_study, statistic, quote, prediction)

### 3.4 Manual Insight Addition

If the CLI isn't available or for targeted additions, edit the curated files directly:

```
backend/src/knowledge/insights/curated/
  trends.json        — Industry shifts backed by data
  frameworks.json    — Actionable methodologies
  case_studies.json  — Real-world examples with outcomes
  statistics.json    — Data-backed claims with sources
  quotes.json        — Memorable, quotable insights
  predictions.json   — Forward-looking forecasts
```

Each insight entry:

```json
{
  "id": "unique-kebab-case-id",
  "content": "The actual insight text",
  "source": "Author/Publication",
  "source_url": "https://...",
  "date": "2026-03",
  "industries": ["ecommerce"],
  "tags": ["ai-adoption", "roi"],
  "reviewed": true,
  "reviewer": "claude-code"
}
```

## Phase 4: Add Industry Knowledge

When adding data for a new or underserved industry:

### Required Files

Create `backend/src/knowledge/[industry-slug]/`:

1. **processes.json** — Common workflows and pain points
   - 5-10 core business processes
   - Time estimates for manual execution
   - Common tools currently used

2. **opportunities.json** — AI automation opportunities
   - Map to processes (which process does this improve?)
   - Estimated time savings
   - Implementation complexity (low/medium/high)

3. **benchmarks.json** — Industry metrics
   - Average revenue per employee
   - Common tech stack adoption rates
   - AI readiness indicators
   - All with sources

4. **vendors.json** — Industry-specific software
   - Top tools used in this industry
   - Pricing (verified)
   - API availability and quality

5. **workflows.json** — Detailed workflow breakdowns
   - Step-by-step for key processes
   - Where AI can intervene
   - Integration points between tools

### Register the Industry

Add to `backend/src/knowledge/__init__.py` if there's a registry.
Update `PRODUCT.md` industry list.

## Phase 5: Validation

After all updates:

- [ ] JSON files are valid (no syntax errors)
- [ ] Every data point has a source
- [ ] No placeholder text ("TODO", "TBD", "example.com")
- [ ] Industry-specific data is actually specific (not generic AI content)
- [ ] Dates are current (not inherited from old data)

```bash
cd backend && python -c "
import json, glob
for f in glob.glob('src/knowledge/**/*.json', recursive=True):
    try:
        json.load(open(f))
    except Exception as e:
        print(f'INVALID JSON: {f} — {e}')
print('JSON validation complete')
"
```

## Phase 6: Summary

```
Knowledge Base Update Summary
=============================
Benchmarks updated: X files
Insights added: X new entries
Industries touched: [list]
Sources used: [list of URLs]

Freshness after update:
- [industry]: all benchmarks current (2026-03)
- [industry]: 2 benchmarks still stale (source unavailable)

Next refresh recommended: [date]
```

## Rules

- **Never fabricate data** — if you can't find a source, mark as UNVERIFIED
- **Always include sources** — no stat without attribution
- **Use WebSearch/WebFetch** — don't rely on training data for current statistics
- **Load `.claude/reference/knowledge-base.md`** for full structure details
- **Validate JSON after editing** — broken JSON breaks report generation
- **Prefer ranges over false precision** — "30-40%" not "35%"
- **Focus on ecommerce** — this is our primary vertical. Key files: `backend/src/knowledge/ecommerce/`, `backend/src/knowledge/benchmarks/ecommerce.json`, `backend/src/knowledge/insights/curated/ecommerce.json`
