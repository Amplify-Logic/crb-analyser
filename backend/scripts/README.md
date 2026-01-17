# Backend Scripts

Admin scripts for managing CRB Analyser data and content.

## Quick Reference

```bash
# Always run from project root with backend virtualenv activated
cd /path/to/crb-analyser
source backend/venv/bin/activate
```

## Available Scripts

### extract_insights.py - Curated Insights Management

Extract and manage AI/industry insights from external content.

```bash
# Extract from a raw transcript file
python -m backend.scripts.extract_insights \
    --file backend/src/knowledge/insights/raw/2026-01-jeff-su-ai-trends.txt

# Extract with full metadata
python -m backend.scripts.extract_insights \
    --file path/to/content.txt \
    --title "Source Title" \
    --author "Author Name" \
    --date "2026-01-14" \
    --source-type youtube

# Paste content interactively
python -m backend.scripts.extract_insights --paste

# List all insights
python -m backend.scripts.extract_insights --list

# List by type
python -m backend.scripts.extract_insights --list --type trend

# Show statistics
python -m backend.scripts.extract_insights --stats

# Mark insight as reviewed
python -m backend.scripts.extract_insights --review <insight-id>

# Import from JSON
python -m backend.scripts.extract_insights --import edited_insights.json
```

### seed_ai_tools_vendors.py - Vendor Database Seeding

Seed the vendor database with AI tools and software.

```bash
python -m backend.scripts.seed_ai_tools_vendors
```

## Workflow: Adding New Insights

1. **Find great content** - YouTube video, research report, article

2. **Save raw content** (optional but recommended):
   ```bash
   # Save to raw folder for reference
   cp transcript.txt backend/src/knowledge/insights/raw/YYYY-MM-source-name.txt
   ```

3. **Extract insights**:
   ```bash
   python -m backend.scripts.extract_insights \
       --file backend/src/knowledge/insights/raw/YYYY-MM-source-name.txt \
       --title "Title" --author "Author" --date "YYYY-MM-DD"
   ```

4. **Review output** - AI extracts insights, you approve or edit

5. **Mark as reviewed** - After verifying quality:
   ```bash
   python -m backend.scripts.extract_insights --review <insight-id>
   ```

## Admin UI Alternative

You can also manage insights through the web admin:

- **Dashboard**: http://localhost:5174/admin
- **Insights**: http://localhost:5174/admin/insights
- **Extractor**: http://localhost:5174/admin/insights/extract
