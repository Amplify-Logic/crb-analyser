# Knowledge Base Reference

> Load this when working on the knowledge base, curated insights, or adding new industries.
> NOT here: vendor database (Supabase) → `vendor-management.md` | industry details → `PRODUCT.md`

---

## Knowledge Base Structure

```
backend/src/knowledge/
├── vendors/              # Vendor pricing (refresh monthly)
├── [industry]/           # Industry-specific data
│   ├── processes.json
│   ├── opportunities.json
│   ├── benchmarks.json
│   └── vendors.json
└── patterns/             # Cross-industry patterns
```

## Add a New Industry

1. Create folder: `backend/src/knowledge/<industry-slug>/`
2. Add required files:
   - `processes.json` - Common workflows, pain points
   - `opportunities.json` - AI automation opportunities
   - `benchmarks.json` - Industry metrics with sources
   - `vendors.json` - Relevant software for this industry
3. Register in `backend/src/knowledge/__init__.py`
4. Add to PRODUCT.md industry list

## Verify/Refresh Data

```bash
# Check what needs refresh
grep -r "verified_date" backend/src/knowledge/ | grep "2024"

# Update vendor pricing
python -m backend.src.services.vendor_refresh_service
```

## Data Quality Rules
- Every stat needs `"source"` and `"verified_date": "YYYY-MM"`
- Unverified data: `"status": "UNVERIFIED"` → shows warning in reports
- Pricing: verify against vendor website, not AI-generated

---

## Curated Insights System

Store and retrieve AI/industry insights from external content (YouTube, articles, reports).

### Structure
```
backend/src/knowledge/insights/
├── raw/                    # Original sources (transcripts, articles)
├── curated/                # Extracted, reviewed insights by type
│   ├── trends.json
│   ├── frameworks.json
│   ├── case_studies.json
│   ├── statistics.json
│   ├── quotes.json
│   └── predictions.json
└── embeddings/             # Vector embeddings (future)
```

### Insight Types

| Type | Description |
|------|-------------|
| `trend` | Industry shifts backed by data |
| `framework` | Actionable methodologies |
| `case_study` | Real-world examples with outcomes |
| `statistic` | Data-backed claims with sources |
| `quote` | Memorable, quotable insights |
| `prediction` | Forward-looking forecasts |

### CLI Commands
```bash
cd backend

# Extract from transcript/article
python scripts/extract_insights.py \
    --file src/knowledge/insights/raw/2026-01-source.txt \
    --title "Title" --author "Author" --date "2026-01-14"

# List all insights
python scripts/extract_insights.py --list

# Filter by type
python scripts/extract_insights.py --list --type trend

# Show stats
python scripts/extract_insights.py --stats

# Mark as reviewed
python scripts/extract_insights.py --review <insight-id>
```

### Admin UI
- **Dashboard**: http://localhost:5174/admin
- **List/Edit**: http://localhost:5174/admin/insights
- **Extract**: http://localhost:5174/admin/insights/extract

### Where Insights Are Surfaced
- **Reports**: Trends/stats in exec summary, case studies as social proof
- **Quiz results**: 1-2 relevant trend insights
- **Landing page**: Rotating stats, quotes, case studies

### API Endpoints
- `GET /api/admin/insights/list` - List with filters
- `POST /api/admin/insights/extract` - AI extraction
- `POST /api/admin/insights/save-extracted` - Save after review
- `PUT /api/admin/insights/{id}` - Update insight
- `POST /api/admin/insights/{id}/review` - Mark reviewed
