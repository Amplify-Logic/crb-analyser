# Curated Insights System

**Date**: 2026-01-14
**Status**: Approved
**Purpose**: Store curated AI/industry insights and intelligently surface them in reports, quiz results, and landing page

---

## Problem

We find great content (YouTube transcripts, research reports, analyst insights) but have no structured way to:
1. Store these insights in a reusable format
2. Automatically surface relevant insights based on user context

## Solution

A hybrid system combining:
- **Manual tags** for high-level filtering (where insights can appear)
- **Semantic search** for context-specific matching (which insights are most relevant)
- **AI-assisted extraction** to turn raw content into structured insights

---

## Data Model

Each insight stored as:

```json
{
  "id": "trend-2026-models-commoditized",
  "type": "trend",
  "title": "AI Models Are Becoming Commoditized",
  "content": "The gap between AI models keeps shrinking. No single model has a clear lead anymore.",
  "supporting_data": [
    {
      "claim": "Models clustering in top-right corner of quality benchmarks",
      "source": "Artificial Analysis",
      "date": "2025-12",
      "credibility": "industry_data"
    }
  ],
  "actionable_insight": "Stop obsessing over technical scores. Focus on how AI fits your workflow.",
  "tags": {
    "topics": ["model-selection", "ai-strategy"],
    "industries": ["all"],
    "use_in": ["report", "landing", "quiz_results"],
    "user_stage": ["considering", "early_adopter"]
  },
  "source": {
    "title": "Top 6 AI Trends That Will Define 2026",
    "author": "Jeff Su",
    "url": "https://youtube.com/...",
    "date": "2026-01-06"
  },
  "extracted_at": "2026-01-14",
  "reviewed": true
}
```

**Content types**: `trend`, `framework`, `quote`, `case_study`, `statistic`, `prediction`

**Credibility levels**: `peer_reviewed`, `academic`, `industry_research`, `industry_data`, `analyst`, `anecdotal`

---

## Storage Structure

```
backend/src/knowledge/
├── insights/
│   ├── raw/                    # Original sources (transcripts, articles)
│   │   └── 2026-01-jeff-su-trends.txt
│   ├── curated/                # Extracted, reviewed insights
│   │   ├── trends.json
│   │   ├── frameworks.json
│   │   ├── case_studies.json
│   │   ├── statistics.json
│   │   └── quotes.json
│   └── embeddings/             # Vector embeddings for semantic search
│       └── insights_index.json
```

---

## Retrieval Flow

1. **Tag filter first** - Filter by `use_in`, `industries`, `topics`
2. **Semantic search second** - Within filtered set, rank by relevance to user context
3. **Freshness weight** - Recent insights ranked higher for trends; evergreen for frameworks

---

## Integration Points

| Surface | Insight Types | How Used |
|---------|---------------|----------|
| **Report - Executive Summary** | Trends, Statistics | Context-setting, credibility |
| **Report - Findings** | Case Studies, Statistics | Social proof for recommendations |
| **Report - Recommendations** | Frameworks | Best practice references |
| **Quiz Results** | Trends (1-2) | Show market awareness before teaser |
| **Landing Page** | Statistics, Quotes, Case Studies | Rotating credibility builders |

---

## Admin Interface

**Routes**:
```
/admin                    → Dashboard home (overview, quick actions)
/admin/vendors            → Existing VendorAdmin
/admin/knowledge          → Existing KnowledgeBase
/admin/insights           → Curated Insights manager
/admin/insights/extract   → AI extraction workflow
```

**Dashboard home** shows:
- Quick stats (vendors, insights, stale data alerts)
- Recent activity
- Quick actions (Extract insights, Refresh vendors)

**Insights Admin** features:
- List view with filters (type, tag, source, reviewed status)
- Extract view (paste content → AI extracts → review/approve)
- Edit view (modify tags, content, mark reviewed)

---

## CLI Commands

Location: `backend/scripts/`

```bash
# Extract insights from content
python -m backend.scripts.extract_insights --file path/to/transcript.txt
python -m backend.scripts.extract_insights --url "https://..."
python -m backend.scripts.extract_insights --paste  # Opens editor

# List insights
python -m backend.scripts.extract_insights --list --type trend

# Generate embeddings
python -m backend.scripts.extract_insights --embed
```

---

## Extraction Workflow

1. **Capture** - CLI or Admin UI, paste raw content
2. **Extract** - AI identifies trends, frameworks, case studies, statistics, quotes
3. **Review** - Human approves/rejects each insight, adjusts tags
4. **Save** - Approved insights saved to type files, embeddings generated

---

## New Files to Create

### Backend
- `backend/src/knowledge/insights/` - Directory structure
- `backend/src/services/insight_service.py` - Retrieval logic
- `backend/src/skills/extraction/insight_extraction.py` - AI extraction skill
- `backend/src/routes/admin_insights.py` - API routes
- `backend/scripts/extract_insights.py` - CLI tool

### Frontend
- `frontend/src/pages/admin/AdminDashboard.tsx` - Dashboard home
- `frontend/src/pages/admin/InsightsAdmin.tsx` - Insights manager
- `frontend/src/pages/admin/InsightExtractor.tsx` - Extraction workflow

---

## Sample Content to Extract

First source: Jeff Su "Top 6 AI Trends That Will Define 2026"

Expected extractions:
1. **Trend**: Models commoditizing (Artificial Analysis data)
2. **Trend**: Year of workflows, not agents (McKinsey: 10% scaling agents)
3. **Trend**: End of technical divide (OpenAI: 75% doing new tasks)
4. **Framework**: Context > Prompting (file management matters)
5. **Statistic**: $3T value from workflow redesign by 2030 (McKinsey)
6. **Quote**: "You don't ask who provides the best electricity"
7. **Case Study**: Pharma - 60% less prep time, 50% fewer errors
8. **Case Study**: Utility call center - 50% cost reduction
9. **Case Study**: Bank code migration - 50% fewer human hours
