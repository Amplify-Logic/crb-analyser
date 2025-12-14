# CRB Analyser - Development Guide

## Quick Start

```bash
# Backend (port 8383)
cd backend && source venv/bin/activate && uvicorn src.main:app --reload --port 8383

# Frontend (port 5174)
cd frontend && npm run dev

# Redis (required for caching)
brew services start redis
```

---

## Project Overview

**CRB Analyser** is an AI-powered business audit microservice delivering Cost/Risk/Benefit analysis for AI implementation.

| Component | Technology |
|-----------|------------|
| Backend | FastAPI + Python 3.12 |
| Frontend | React 18 + Vite + TypeScript |
| Database | Supabase (PostgreSQL) |
| Auth | Supabase Auth (JWT) |
| Cache | Redis |
| AI | Anthropic Claude API |
| Payments | Stripe |
| Email | SendGrid |
| Monitoring | Logfire + Langfuse |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CRB ANALYSER                           │
├─────────────────────────────────────────────────────────────┤
│  FRONTEND (React + Vite)          BACKEND (FastAPI)         │
│  ├── Landing                      ├── /api/auth             │
│  ├── Dashboard                    ├── /api/clients          │
│  ├── Intake Wizard                ├── /api/audits           │
│  ├── Progress View                ├── /api/findings         │
│  ├── Report Viewer                ├── /api/reports          │
│  └── Settings                     ├── /api/intake           │
│                                   ├── /api/vendors          │
│                                   ├── /api/payments         │
│                                   └── /api/health           │
├─────────────────────────────────────────────────────────────┤
│  CRB AGENT                                                  │
│  ├── Discovery Tools (analyze intake, map processes)        │
│  ├── Research Tools (benchmarks, vendors, web search)       │
│  ├── Analysis Tools (scoring, impact, risk)                 │
│  ├── Modeling Tools (ROI, comparison, timeline)             │
│  └── Report Tools (summary, full report, PDF)               │
├─────────────────────────────────────────────────────────────┤
│  DATA LAYER                                                 │
│  ├── Supabase: clients, audits, findings, recommendations   │
│  ├── Redis: caching, sessions, rate limiting                │
│  └── Vendor DB: pricing, benchmarks (our moat)              │
└─────────────────────────────────────────────────────────────┘
```

---

## Development Rules

### 1. Code Quality
- **Read before edit** - Never modify code you haven't read
- **No over-engineering** - Only build what's needed now
- **Type everything** - Full type hints in Python, TypeScript strict mode
- **Test critical paths** - Auth, payments, report generation

### 2. CRB-Specific Rules
- **Every claim needs a source** - No hallucinated data in reports
- **Transparent calculations** - Show assumptions in ROI math
- **Validate vendors** - Real pricing, verified dates
- **Confidence scores** - Rate certainty of each finding

### 3. Security
- **RLS everywhere** - All tables have Row Level Security
- **Validate inputs** - Pydantic models for all requests
- **Sanitize outputs** - No raw errors to users in production
- **Rate limit** - All endpoints rate-limited

### 4. Performance
- **Cache aggressively** - Tool results, LLM responses, benchmarks
- **Stream responses** - SSE for long-running operations
- **Lazy load** - Don't load all findings at once

---

## Key Files Reference

| Area | File | Purpose |
|------|------|---------|
| **Config** | `backend/src/config/settings.py` | Environment variables |
| **Supabase** | `backend/src/config/supabase_client.py` | DB client singleton |
| **Auth** | `backend/src/middleware/auth.py` | JWT validation |
| **Agent** | `backend/src/agents/crb_agent.py` | Main analysis agent |
| **Tools** | `backend/src/tools/tool_registry.py` | Tool definitions |
| **ROI** | `backend/src/services/roi_calculator.py` | ROI calculations |
| **Reports** | `backend/src/services/report_generator.py` | PDF generation |
| **Auth (FE)** | `frontend/src/contexts/AuthContext.tsx` | Auth state |
| **API Client** | `frontend/src/services/apiClient.ts` | HTTP client |

---

## Database Schema

### Core Tables

```sql
clients        -- Businesses being audited
audits         -- CRB analysis projects
findings       -- Discovered issues/opportunities
recommendations -- Proposed solutions with ROI
reports        -- Generated PDF reports
vendor_catalog -- Vendor pricing database (our moat)
industry_benchmarks -- Industry metrics (our moat)
```

### Key Relationships

```
workspace
    └── clients
            └── audits
                    ├── findings
                    │       └── recommendations
                    └── reports
```

---

## API Patterns

### Authentication
All protected routes use `Depends(get_current_user)`:
```python
@router.get("/audits")
async def list_audits(
    current_user: CurrentUser = Depends(get_current_user),
    supabase: AsyncClient = Depends(get_async_supabase)
):
    # current_user.workspace_id for multi-tenant isolation
```

### Response Format
```python
# Success
{"data": {...}, "message": "optional"}

# Error
{"error": {"type": "validation_error", "message": "...", "status_code": 400}}
```

### Streaming (SSE)
For long-running operations:
```python
@router.get("/audits/{id}/progress")
async def stream_progress(id: str):
    async def generate():
        async for update in agent.run_analysis(id):
            yield f"data: {json.dumps(update)}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## CRB Agent Tools

### Discovery (Phase 1)
| Tool | Purpose |
|------|---------|
| `analyze_intake_responses` | Parse questionnaire, extract pain points |
| `map_business_processes` | Create process flow from descriptions |
| `identify_tech_stack` | Detect current tools from intake |

### Research (Phase 2)
| Tool | Purpose |
|------|---------|
| `search_industry_benchmarks` | Find relevant metrics |
| `search_vendor_solutions` | Find matching vendors |
| `scrape_vendor_pricing` | Get current pricing |
| `validate_source_credibility` | Score source reliability |

### Analysis (Phase 3)
| Tool | Purpose |
|------|---------|
| `score_automation_potential` | Rate process (0-100) |
| `calculate_finding_impact` | Estimate cost/time |
| `identify_ai_opportunities` | Find AI use cases |
| `assess_implementation_risk` | Evaluate risk factors |

### Modeling (Phase 4)
| Tool | Purpose |
|------|---------|
| `calculate_roi` | Full ROI with assumptions |
| `compare_vendors` | Side-by-side comparison |
| `generate_timeline` | Implementation roadmap |

### Report (Phase 5)
| Tool | Purpose |
|------|---------|
| `generate_executive_summary` | Key findings synthesis |
| `generate_full_report` | Complete PDF artifact |

---

## Frontend Routes

```
/                   Landing (public)
/login              Login
/signup             Signup
/pricing            Pricing tiers

/dashboard          List audits
/new-audit          Start audit, select tier
/intake/:id         Multi-step questionnaire

/audit/:id          Audit detail
/audit/:id/progress Live progress view
/audit/:id/findings Review findings
/audit/:id/report   View/download report

/settings           Account settings
/settings/billing   Subscription management
```

---

## Design System

### Colors (Semantic)
| Color | Usage |
|-------|-------|
| **Blue** | Primary actions, links |
| **Green** | Success, savings, positive ROI |
| **Yellow** | Warnings, medium risk |
| **Red** | Errors, high risk, costs |
| **Purple** | AI/analysis related |
| **Gray** | Neutral, secondary text |

### Components
- `rounded-2xl` for cards
- `rounded-xl` for buttons
- `font-light` for body text
- `backdrop-blur-sm` for overlays

---

## Environment Variables

### Backend (.env)
```bash
# Required
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
SECRET_KEY=
ANTHROPIC_API_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

# Optional but recommended
REDIS_URL=redis://localhost:6379
BRAVE_API_KEY=
TAVILY_API_KEY=
SENDGRID_API_KEY=
LOGFIRE_TOKEN=
```

### Frontend (.env)
```bash
VITE_API_BASE_URL=http://localhost:8383
VITE_STRIPE_PUBLISHABLE_KEY=
```

---

## Testing

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test

# E2E (when ready)
npm run test:e2e
```

### Critical Test Coverage
- [ ] Auth flow (signup, login, logout)
- [ ] Payment flow (checkout, webhook)
- [ ] Audit creation and progress
- [ ] Report generation
- [ ] ROI calculations

---

## Deployment

### Railway (Production)
```bash
# Backend
railway link
railway up

# Frontend
railway link
railway up
```

### Health Checks
- Backend: `GET /health`
- Frontend: `GET /`

---

## Common Tasks

### Add a new tool
1. Define in `tools/tool_registry.py`
2. Implement in appropriate `tools/*_tools.py`
3. Register in agent tool list
4. Add tests

### Add a new API route
1. Create route file in `routes/`
2. Add Pydantic models
3. Register in `main.py`
4. Add auth dependency
5. Add tests

### Add a new frontend page
1. Create page in `pages/`
2. Add route in `App.tsx`
3. Create service functions if needed
4. Add to navigation if appropriate

---

## Debugging

### Backend logs
```bash
# Development
uvicorn src.main:app --reload --port 8383 --log-level debug

# Check Logfire dashboard for production
```

### Frontend
- React DevTools
- Network tab for API calls
- Check Sentry for errors

### Common Issues

| Issue | Solution |
|-------|----------|
| Auth not working | Check JWT token, Supabase config |
| Streaming not updating | Check SSE connection, CORS |
| Report not generating | Check Claude API key, tool errors |
| Payment failing | Check Stripe keys, webhook URL |

---

## Reference: MMAI Source Files

When adapting code, reference these MMAI files:

| Component | MMAI Path |
|-----------|-----------|
| Supabase client | `mmai-backend/src/config/supabase_client.py` |
| Auth middleware | `mmai-backend/src/middleware/auth.py` |
| Security middleware | `mmai-backend/src/middleware/security.py` |
| Error handler | `mmai-backend/src/middleware/error_handler.py` |
| Cache service | `mmai-backend/src/services/cache_service.py` |
| Knowledge pipeline | `mmai-backend/src/services/knowledge/pipeline.py` |
| Agent pattern | `mmai-backend/src/agents/maestro_agent.py` |
| Model routing | `mmai-backend/src/agents/conservative_4tier_routing.py` |
| Stripe routes | `mmai-backend/src/routes/stripe_routes.py` |
| Auth context | `mmai-frontend/src/contexts/AuthContext.tsx` |
| API client | `mmai-frontend/src/services/apiClient.ts` |
| Tool stream hook | `mmai-frontend/src/hooks/useToolStream.ts` |
| Wizard pattern | `mmai-frontend/src/components/onboarding/OnboardingWizard.tsx` |

---

## Checklist: MVP Ready

### Backend
- [ ] Auth working (signup, login, logout)
- [ ] Clients CRUD
- [ ] Audits CRUD with status tracking
- [ ] Intake submission and storage
- [ ] CRB agent runs analysis
- [ ] Findings generated
- [ ] Recommendations with ROI
- [ ] PDF report generation
- [ ] Stripe checkout works
- [ ] Webhook processes payments

### Frontend
- [ ] Landing page
- [ ] Auth flow complete
- [ ] Dashboard shows audits
- [ ] Intake wizard works
- [ ] Progress streaming
- [ ] Report viewer
- [ ] PDF download
- [ ] Payment flow

### Infrastructure
- [ ] Supabase tables with RLS
- [ ] Redis caching
- [ ] Railway deployment
- [ ] Environment variables set
- [ ] Health checks passing
