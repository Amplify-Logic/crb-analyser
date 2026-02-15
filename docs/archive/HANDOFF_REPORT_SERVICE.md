# Handoff: Report Generation Service

## Context

CRB Analyser is an AI-powered Cost/Risk/Benefit analysis tool for SMBs. We've built:
- Landing page with free quiz CTA
- Quiz flow (5 questions → AI Readiness Score → opportunity previews)
- Stripe checkout for €47 Quick Report and €297 Full Analysis tiers
- Guest checkout flow (no auth required)

## Task: Build Report Generation Service

Create the service that generates the actual CRB report after payment.

### Report Structure (from FRAMEWORK.md)

The report must follow our methodology:

**Two Pillars Scoring:**
- Customer Value Score (1-10): Long-term customer lifetime value impact
- Business Health Score (1-10): Survival and thriving impact
- Only recommend if BOTH scores ≥ 6

**Value Types:**
- Value SAVED: Efficiency gains (time × hourly rate = € saved)
- Value CREATED: Growth opportunities (new revenue, better margins)

**Three Options Pattern (for each recommendation):**
1. Off-the-shelf: Existing SaaS tools
2. Best-in-class: Premium/specialized solutions
3. Custom AI solution: Tailored development

**Three Time Horizons:**
- Short-term (0-6 months): Quick wins
- Mid-term (6-18 months): Strategic initiatives
- Long-term (18+ months): Transformational changes

**Impartiality:**
- Agent should say "don't do this" when appropriate
- Include "not recommended" items with honest reasons

### Key Files to Reference

```
backend/src/agents/crb_agent.py          # Main CRB agent (already has methodology in prompts)
backend/src/knowledge/__init__.py        # Industry knowledge loader
backend/src/knowledge/*/opportunities.json # Industry-specific opportunities
backend/src/knowledge/*/processes.json   # Industry processes
backend/src/knowledge/*/benchmarks.json  # Industry benchmarks
backend/src/knowledge/*/vendors.json     # Vendor recommendations
docs/FRAMEWORK.md                        # Full methodology documentation
```

### Implementation Steps

1. **Create Report Service** (`backend/src/services/report_service.py`)
   - Take quiz_session_id as input
   - Load quiz answers and results from database
   - Initialize CRB agent with quiz context
   - Run full analysis pipeline
   - Store structured report in database

2. **Update Report Schema**
   - Create `reports` table structure for new format
   - Include sections: executive_summary, findings, recommendations, roadmap
   - Store both structured data and rendered HTML/PDF

3. **Report Output Format**
   ```python
   {
     "executive_summary": {
       "ai_readiness_score": 72,
       "key_insight": "...",
       "top_opportunities": [...],
       "not_recommended": [...]
     },
     "findings": [
       {
         "id": "...",
         "title": "...",
         "customer_value_score": 8,
         "business_health_score": 7,
         "value_saved": {"hours_per_week": 5, "hourly_rate": 50, "annual_savings": 13000},
         "value_created": {"description": "...", "potential_revenue": 20000},
         "options": {
           "off_the_shelf": {...},
           "best_in_class": {...},
           "custom_solution": {...}
         },
         "time_horizon": "short",
         "confidence": 0.85,
         "sources": [...]
       }
     ],
     "roadmap": {
       "short_term": [...],
       "mid_term": [...],
       "long_term": [...]
     },
     "methodology_notes": "..."
   }
   ```

4. **PDF Generation** (`backend/src/services/pdf_generator.py`)
   - Use WeasyPrint or similar
   - Professional template with branding
   - Charts/visualizations for scores

5. **Trigger from Webhook**
   - Update `handle_guest_checkout_completed()` in payments.py
   - Queue report generation job
   - Send email when complete

### Database Tables Needed

```sql
-- Update quiz_sessions to link to report
ALTER TABLE quiz_sessions ADD COLUMN report_id UUID REFERENCES reports(id);

-- Reports table
CREATE TABLE reports (
  id UUID PRIMARY KEY,
  quiz_session_id UUID REFERENCES quiz_sessions(id),
  tier TEXT NOT NULL,
  status TEXT DEFAULT 'generating',
  report_data JSONB,
  pdf_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);
```

### Frontend Updates Needed

- Report viewer page (`/report/:id`)
- PDF download button
- Interactive charts for scores
- Expandable sections for each finding

## Quick Start

```bash
# Backend
cd backend && source venv/bin/activate && uvicorn src.main:app --reload --port 8383

# Frontend
cd frontend && npm run dev
```

## Success Criteria

- [ ] Quiz completion triggers report generation
- [ ] Report follows two pillars methodology
- [ ] Each recommendation has three options
- [ ] PDF downloads correctly
- [ ] Email sent with report link
