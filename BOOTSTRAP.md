# CRB Analyser - Bootstrap Document

> **Use this document as your initial prompt in the new crb-analyser project**
> Repository: https://github.com/Amplify-Logic/crb-analyser

---

## What We're Building

**CRB Analyser** is an AI-powered business audit service that analyzes companies and provides:
- Cost/Risk/Benefit analysis for AI implementation
- Process automation recommendations
- Vendor comparisons with real pricing
- ROI projections with transparent assumptions
- Professional PDF reports

**Target Market:** Mid-market professional services (agencies, legal, accounting, recruitment) - companies with 20-200 employees, underserved by Big 4 consultants, too complex for DIY ChatGPT.

**Pricing Tiers:**
- Starter (€97-197): AI readiness score + top 3 recommendations
- Professional (€497-997): Full CRB report, 15-20 findings, PDF
- Enterprise (€2,997+): Deep audit, implementation roadmap, follow-up

---

## Source Project Reference

We're pulling proven infrastructure from **MMAI (Music Manager AI)** located at:
```
/Users/larsmusic/Music Manager AI/
├── mmai-backend/    # FastAPI backend
└── mmai-frontend/   # React + Vite frontend
```

**DO NOT modify MMAI files** - only read and adapt for CRB.

---

## Phase 1: Foundation Setup

### Step 1.1: Create Directory Structure

```bash
mkdir -p backend/src/{config,middleware,routes,agents,tools,services,models}
mkdir -p backend/src/services/knowledge
mkdir -p backend/supabase/migrations
mkdir -p frontend/src/{pages,components,contexts,services,hooks}
mkdir -p frontend/src/components/{ui,auth,intake,audit,findings,report}
mkdir -p frontend/public
```

### Step 1.2: Backend Dependencies

Create `backend/requirements.txt`:
```
# Core
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-socketio==5.11.0
python-multipart==0.0.6
httpx==0.27.0

# Database
supabase==2.11.0
pgvector==0.3.6
sqlalchemy==2.0.36
asyncpg==0.29.0
psycopg2-binary==2.9.10

# Memory/Cache
zep-cloud==3.4.0
redis==6.4.0

# AI/LLM
anthropic==0.43.0
openai==1.59.9

# Data Processing
pydantic==2.10.4
pydantic-settings==2.7.1
email-validator==2.2.0
pandas==2.1.4
numpy==1.26.3

# Utils
python-dotenv==1.0.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Email & Payments
sendgrid==6.11.0
stripe==11.4.1

# Monitoring
logfire==0.20.0

# DNS
dnspython==2.7.0

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
```

### Step 1.3: Frontend Dependencies

Create `frontend/package.json`:
```json
{
  "name": "crb-analyser",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext .js,.jsx,.ts,.tsx"
  },
  "dependencies": {
    "@headlessui/react": "^1.7.17",
    "@sentry/react": "^10.23.0",
    "@tanstack/react-query": "^5.90.5",
    "clsx": "latest",
    "date-fns": "^4.1.0",
    "framer-motion": "^11.5.4",
    "lucide-react": "^0.441.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-hook-form": "^7.48.2",
    "react-markdown": "^10.1.0",
    "react-router-dom": "^6.26.2",
    "recharts": "^2.12.0",
    "socket.io-client": "^4.8.1",
    "tailwind-merge": "latest",
    "zod": "^3.25.46"
  },
  "devDependencies": {
    "@types/node": "^20.19.0",
    "@types/react": "^18.3.1",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "latest",
    "eslint": "^8.50.0",
    "postcss": "latest",
    "tailwindcss": "3.4.17",
    "typescript": "^5.5.4",
    "vite": "^5.2.0"
  }
}
```

---

## Files to Copy from MMAI

### Backend - Copy Directly (adapt imports only)

| Source Path | Destination | Notes |
|-------------|-------------|-------|
| `mmai-backend/src/config/supabase_client.py` | `backend/src/config/supabase_client.py` | Copy as-is |
| `mmai-backend/src/config/logfire_config.py` | `backend/src/config/logfire_config.py` | Copy as-is |
| `mmai-backend/src/middleware/auth.py` | `backend/src/middleware/auth.py` | Copy as-is |
| `mmai-backend/src/middleware/security.py` | `backend/src/middleware/security.py` | Copy as-is (includes rate limiting) |
| `mmai-backend/src/middleware/error_handler.py` | `backend/src/middleware/error_handler.py` | Copy as-is |
| `mmai-backend/Dockerfile` | `backend/Dockerfile` | Update port to 8383 |
| `mmai-backend/railway.toml` | `backend/railway.toml` | Copy as-is |

### Backend - Additional Components (MISSED IN INITIAL AUDIT)

| Source Path | Destination | Notes |
|-------------|-------------|-------|
| `mmai-backend/src/services/cache_service.py` | `backend/src/services/cache_service.py` | Redis caching with fallback |
| `mmai-backend/src/services/tool_result_cache.py` | `backend/src/services/tool_result_cache.py` | Tool-specific caching (50-70% hit rate) |
| `mmai-backend/src/services/semantic_cache.py` | `backend/src/services/semantic_cache.py` | Embeddings-based LLM response caching |
| `mmai-backend/src/services/observability.py` | `backend/src/services/observability.py` | Langfuse tracing, cost tracking |
| `mmai-backend/src/services/email/sendgrid_service.py` | `backend/src/services/email/sendgrid_service.py` | Email delivery |
| `mmai-backend/src/services/email/email_scheduler.py` | `backend/src/services/email/email_scheduler.py` | Background job scheduling (APScheduler) |
| `mmai-backend/src/routes/stripe_routes.py` | `backend/src/routes/payments.py` | Full Stripe integration |
| `mmai-backend/src/routes/email_webhooks.py` | `backend/src/routes/webhooks.py` | Webhook patterns (verification, idempotency) |
| `mmai-backend/src/routes/assets.py` | `backend/src/routes/files.py` | File upload/storage patterns |
| `mmai-backend/src/routes/export_routes.py` | `backend/src/routes/export.py` | Data export (GDPR compliance) |

### Frontend - Additional Components (MISSED IN INITIAL AUDIT)

| Source Path | Destination | Notes |
|-------------|-------------|-------|
| `mmai-frontend/src/contexts/ToastContext.tsx` | `frontend/src/contexts/ToastContext.tsx` | Notification system |
| `mmai-frontend/src/contexts/ThemeContext.tsx` | `frontend/src/contexts/ThemeContext.tsx` | Dark/light mode |
| `mmai-frontend/src/hooks/useToolStream.ts` | `frontend/src/hooks/useToolStream.ts` | SSE streaming for real-time updates |
| `mmai-frontend/src/hooks/useWorkspaceId.ts` | `frontend/src/hooks/useWorkspaceId.ts` | Workspace context |
| `mmai-frontend/src/hooks/useSubscription.ts` | `frontend/src/hooks/useSubscription.ts` | Subscription status |
| `mmai-frontend/src/components/ui/ToastContainer.tsx` | `frontend/src/components/ui/ToastContainer.tsx` | Toast UI |
| `mmai-frontend/src/components/onboarding/OnboardingWizard.tsx` | `frontend/src/components/intake/IntakeWizard.tsx` | Multi-step form pattern |

### Backend - Copy and Adapt

| Source Path | Destination | Adaptations |
|-------------|-------------|-------------|
| `mmai-backend/src/config/settings.py` | `backend/src/config/settings.py` | Remove music APIs, add CRB config |
| `mmai-backend/src/main.py` | `backend/src/main.py` | Remove music routes, add CRB routes |
| `mmai-backend/src/agents/maestro_agent.py` | `backend/src/agents/crb_agent.py` | Rename, adapt tool set |
| `mmai-backend/src/agents/conservative_4tier_routing.py` | `backend/src/agents/model_routing.py` | Copy routing logic |
| `mmai-backend/src/services/knowledge/pipeline.py` | `backend/src/services/knowledge/pipeline.py` | Copy search/extract pattern |
| `mmai-backend/src/services/knowledge/quality_validation.py` | `backend/src/services/knowledge/quality_validation.py` | Copy as-is |
| `mmai-backend/src/tools/web_search_tools.py` | `backend/src/tools/research_tools.py` | Keep search, scraping tools |

### Frontend - Copy Directly

| Source Path | Destination | Notes |
|-------------|-------------|-------|
| `mmai-frontend/src/contexts/AuthContext.tsx` | `frontend/src/contexts/AuthContext.tsx` | Copy as-is |
| `mmai-frontend/src/services/apiClient.ts` | `frontend/src/services/apiClient.ts` | Copy as-is |
| `mmai-frontend/vite.config.ts` | `frontend/vite.config.ts` | Update proxy port |
| `mmai-frontend/tailwind.config.js` | `frontend/tailwind.config.js` | Copy as-is |
| `mmai-frontend/postcss.config.js` | `frontend/postcss.config.js` | Copy as-is |
| `mmai-frontend/tsconfig.json` | `frontend/tsconfig.json` | Copy as-is |
| `mmai-frontend/Dockerfile` | `frontend/Dockerfile` | Copy as-is |
| `mmai-frontend/railway.json` | `frontend/railway.json` | Copy as-is |
| `mmai-frontend/build.sh` | `frontend/build.sh` | Copy as-is |

---

## Database Schema

Create `backend/supabase/migrations/001_initial_schema.sql`:

```sql
-- CRB Analyser Database Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Workspaces (multi-tenancy)
CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY,  -- Matches Supabase Auth user ID
    email TEXT UNIQUE NOT NULL,
    workspace_id UUID REFERENCES workspaces(id),
    role TEXT DEFAULT 'owner',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Subscriptions
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id),
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    plan TEXT DEFAULT 'free',  -- 'free', 'starter', 'professional', 'enterprise'
    status TEXT DEFAULT 'active',
    current_period_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Clients (businesses being audited)
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id),
    name TEXT NOT NULL,
    industry TEXT NOT NULL,
    company_size TEXT,  -- 'solo', '2-10', '11-50', '51-200', '201-500', '500+'
    revenue_range TEXT,  -- '<100k', '100k-500k', '500k-1m', '1m-5m', '5m-50m', '50m+'
    website TEXT,
    contact_email TEXT,
    intake_data JSONB,  -- Full questionnaire responses
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audits (CRB analysis projects)
CREATE TABLE audits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES clients(id),
    workspace_id UUID REFERENCES workspaces(id),
    title TEXT NOT NULL,
    audit_type TEXT NOT NULL,  -- 'ai_readiness', 'process_automation', 'cost_reduction', 'full_crb'
    status TEXT DEFAULT 'intake',  -- 'intake', 'discovery', 'analysis', 'modeling', 'report', 'delivered'
    tier TEXT NOT NULL,  -- 'starter', 'professional', 'enterprise'
    current_phase INTEGER DEFAULT 1,
    total_phases INTEGER DEFAULT 6,
    progress_percent INTEGER DEFAULT 0,
    price_paid DECIMAL(10,2),
    currency TEXT DEFAULT 'EUR',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Findings (discovered issues/opportunities)
CREATE TABLE findings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    audit_id UUID REFERENCES audits(id) ON DELETE CASCADE,
    category TEXT NOT NULL,  -- 'process', 'technology', 'cost', 'risk', 'opportunity'
    subcategory TEXT,
    severity TEXT NOT NULL,  -- 'critical', 'high', 'medium', 'low'
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    current_state TEXT,
    impact TEXT,
    estimated_annual_cost DECIMAL(12,2),
    confidence_score DECIMAL(3,2),
    sources JSONB,
    evidence JSONB,
    status TEXT DEFAULT 'draft',  -- 'draft', 'validated', 'approved', 'rejected'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Recommendations (proposed solutions)
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    finding_id UUID REFERENCES findings(id) ON DELETE CASCADE,
    audit_id UUID REFERENCES audits(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    implementation_steps JSONB,
    vendor_options JSONB,
    recommended_vendor TEXT,
    estimated_cost DECIMAL(12,2),
    estimated_annual_savings DECIMAL(12,2),
    estimated_one_time_benefit DECIMAL(12,2),
    payback_months DECIMAL(4,1),
    roi_percent DECIMAL(6,2),
    implementation_risk TEXT,  -- 'low', 'medium', 'high'
    risk_factors JSONB,
    priority INTEGER,
    effort_level TEXT,  -- 'quick_win', 'moderate', 'major_project'
    timeline_weeks INTEGER,
    assumptions JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Reports (generated deliverables)
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    audit_id UUID REFERENCES audits(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    executive_summary TEXT,
    full_content JSONB,
    pdf_storage_path TEXT,
    pdf_url TEXT,
    version INTEGER DEFAULT 1,
    status TEXT DEFAULT 'draft',  -- 'draft', 'final', 'delivered'
    delivered_at TIMESTAMPTZ,
    downloaded_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vendor Catalog (competitive advantage)
CREATE TABLE vendor_catalog (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,  -- 'crm', 'automation', 'analytics', 'ai_tool'
    subcategory TEXT,
    pricing_model TEXT,  -- 'per_seat', 'flat', 'usage', 'custom'
    pricing_tiers JSONB,
    pricing_last_verified TIMESTAMPTZ,
    website TEXT,
    description TEXT,
    best_for JSONB,
    avoid_if JSONB,
    g2_rating DECIMAL(2,1),
    capterra_rating DECIMAL(2,1),
    our_rating DECIMAL(2,1),
    avg_implementation_weeks INTEGER,
    avg_implementation_cost_smb DECIMAL(10,2),
    avg_implementation_cost_mid DECIMAL(10,2),
    integrations JSONB,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Industry Benchmarks (competitive advantage)
CREATE TABLE industry_benchmarks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    industry TEXT NOT NULL,
    company_size TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value DECIMAL(10,4),
    metric_unit TEXT,
    percentile_25 DECIMAL(10,4),
    percentile_50 DECIMAL(10,4),
    percentile_75 DECIMAL(10,4),
    source TEXT NOT NULL,
    source_url TEXT,
    source_date DATE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit Activity Log
CREATE TABLE audit_activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    audit_id UUID REFERENCES audits(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_clients_workspace ON clients(workspace_id);
CREATE INDEX idx_audits_workspace ON audits(workspace_id);
CREATE INDEX idx_audits_client ON audits(client_id);
CREATE INDEX idx_audits_status ON audits(status);
CREATE INDEX idx_findings_audit ON findings(audit_id);
CREATE INDEX idx_recommendations_audit ON recommendations(audit_id);
CREATE INDEX idx_reports_audit ON reports(audit_id);
CREATE INDEX idx_vendor_catalog_category ON vendor_catalog(category);
CREATE INDEX idx_industry_benchmarks_industry ON industry_benchmarks(industry, company_size);

-- Row Level Security (RLS)
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE audits ENABLE ROW LEVEL SECURITY;
ALTER TABLE findings ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- RLS Policies (workspace isolation)
CREATE POLICY workspace_isolation ON clients
    FOR ALL USING (workspace_id IN (
        SELECT workspace_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY workspace_isolation ON audits
    FOR ALL USING (workspace_id IN (
        SELECT workspace_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY workspace_isolation ON findings
    FOR ALL USING (audit_id IN (
        SELECT id FROM audits WHERE workspace_id IN (
            SELECT workspace_id FROM users WHERE id = auth.uid()
        )
    ));

CREATE POLICY workspace_isolation ON recommendations
    FOR ALL USING (audit_id IN (
        SELECT id FROM audits WHERE workspace_id IN (
            SELECT workspace_id FROM users WHERE id = auth.uid()
        )
    ));

CREATE POLICY workspace_isolation ON reports
    FOR ALL USING (audit_id IN (
        SELECT id FROM audits WHERE workspace_id IN (
            SELECT workspace_id FROM users WHERE id = auth.uid()
        )
    ));

-- Public read access for vendor catalog and benchmarks
CREATE POLICY public_read ON vendor_catalog FOR SELECT USING (true);
CREATE POLICY public_read ON industry_benchmarks FOR SELECT USING (true);
```

---

## Environment Variables

Create `backend/.env.example`:
```bash
# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
DATABASE_URL=postgresql://...

# Auth
SECRET_KEY=your-secret-key-min-32-chars
CORS_ORIGINS=http://localhost:5173,https://crb-analyser.com

# LLM
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Search APIs
BRAVE_API_KEY=...
TAVILY_API_KEY=...

# Cache
REDIS_URL=redis://localhost:6379

# Memory (optional)
ZEP_API_KEY=...
ZEP_API_URL=https://api.getzep.com

# Payments
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email
SENDGRID_API_KEY=SG...
SENDGRID_FROM_EMAIL=reports@crb-analyser.com

# Monitoring
LOGFIRE_TOKEN=...

# App Config
APP_NAME=CRB Analyser
APP_ENV=development
LOG_LEVEL=INFO
```

Create `frontend/.env.example`:
```bash
VITE_API_BASE_URL=http://localhost:8383
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_...
VITE_SENTRY_DSN=https://...
```

---

## API Endpoints Reference

```
/api
├── /auth
│   ├── POST /signup
│   ├── POST /login
│   ├── POST /logout
│   └── GET  /me
│
├── /clients
│   ├── POST /
│   ├── GET  /
│   ├── GET  /:id
│   └── PUT  /:id
│
├── /audits
│   ├── POST /
│   ├── GET  /
│   ├── GET  /:id
│   ├── PUT  /:id
│   ├── POST /:id/start
│   ├── GET  /:id/progress (SSE)
│   └── POST /:id/generate-report
│
├── /findings
│   ├── GET  /audit/:audit_id
│   ├── POST /
│   ├── PUT  /:id
│   └── DELETE /:id
│
├── /recommendations
│   ├── GET  /audit/:audit_id
│   ├── PUT  /:id
│   └── POST /:id/recalculate
│
├── /reports
│   ├── GET  /audit/:audit_id
│   ├── POST /:id/regenerate
│   └── GET  /:id/download
│
├── /intake
│   ├── GET  /questionnaire/:type
│   └── POST /submit
│
├── /vendors
│   ├── GET  /
│   ├── GET  /:slug
│   └── GET  /compare
│
├── /benchmarks
│   └── GET  /:industry
│
├── /payments
│   ├── POST /create-checkout
│   ├── POST /webhook
│   └── GET  /status/:audit_id
│
└── /health
    └── GET  /
```

---

## CRB Tools to Implement

```python
CRB_TOOLS = {
    # Discovery (3)
    "analyze_intake_responses": "Parse questionnaire, identify pain points",
    "map_business_processes": "Create process flow from descriptions",
    "identify_tech_stack": "Detect current tools from intake + research",

    # Research (4)
    "search_industry_benchmarks": "Find relevant benchmarks",
    "search_vendor_solutions": "Find vendors matching requirements",
    "scrape_vendor_pricing": "Get current pricing from vendor sites",
    "validate_source_credibility": "Score source reliability",

    # Analysis (4)
    "score_automation_potential": "Rate process for automation (0-100)",
    "calculate_finding_impact": "Estimate cost/time impact",
    "identify_ai_opportunities": "Find AI use cases for processes",
    "assess_implementation_risk": "Evaluate risk factors",

    # Modeling (3)
    "calculate_roi": "Full ROI calculation with assumptions",
    "compare_vendors": "Side-by-side vendor comparison",
    "generate_timeline": "Create implementation roadmap",

    # Report (2)
    "generate_executive_summary": "Synthesize key findings",
    "generate_full_report": "Create structured report artifact"
}
```

---

## Frontend Pages

```
/                       # Landing (public)
/login                  # Login
/signup                 # Signup
/pricing                # Pricing tiers

/dashboard              # List audits
/new-audit              # Start new audit
/intake/:audit_id       # Multi-step questionnaire

/audit/:id              # Audit detail
/audit/:id/progress     # Live progress
/audit/:id/findings     # Review findings
/audit/:id/report       # View/download report

/settings               # Account
/settings/billing       # Subscription
```

---

## Target Directory Structure

```
crb-analyser/
├── backend/
│   ├── src/
│   │   ├── main.py
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   ├── settings.py
│   │   │   ├── supabase_client.py
│   │   │   └── logfire_config.py
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── security.py
│   │   │   └── error_handler.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── clients.py
│   │   │   ├── audits.py
│   │   │   ├── findings.py
│   │   │   ├── recommendations.py
│   │   │   ├── reports.py
│   │   │   ├── intake.py
│   │   │   ├── vendors.py
│   │   │   ├── benchmarks.py
│   │   │   ├── payments.py
│   │   │   └── health.py
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── crb_agent.py
│   │   │   └── model_routing.py
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── tool_registry.py
│   │   │   ├── discovery_tools.py
│   │   │   ├── research_tools.py
│   │   │   ├── analysis_tools.py
│   │   │   ├── modeling_tools.py
│   │   │   └── report_tools.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── knowledge/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── pipeline.py
│   │   │   │   └── quality_validation.py
│   │   │   ├── roi_calculator.py
│   │   │   ├── report_generator.py
│   │   │   ├── vendor_service.py
│   │   │   └── benchmark_service.py
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── client.py
│   │       ├── audit.py
│   │       ├── finding.py
│   │       ├── recommendation.py
│   │       └── report.py
│   ├── supabase/
│   │   └── migrations/
│   │       └── 001_initial_schema.sql
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── railway.toml
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── index.css
│   │   ├── pages/
│   │   │   ├── Landing.tsx
│   │   │   ├── Login.tsx
│   │   │   ├── Signup.tsx
│   │   │   ├── Pricing.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── NewAudit.tsx
│   │   │   ├── Intake.tsx
│   │   │   ├── AuditDetail.tsx
│   │   │   ├── AuditProgress.tsx
│   │   │   ├── Findings.tsx
│   │   │   ├── Report.tsx
│   │   │   └── Settings.tsx
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   ├── auth/
│   │   │   ├── intake/
│   │   │   ├── audit/
│   │   │   ├── findings/
│   │   │   └── report/
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx
│   │   ├── services/
│   │   │   ├── apiClient.ts
│   │   │   ├── auditService.ts
│   │   │   ├── intakeService.ts
│   │   │   └── reportService.ts
│   │   └── hooks/
│   │       ├── useAuth.ts
│   │       └── useAudit.ts
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── tsconfig.json
│   ├── Dockerfile
│   ├── railway.json
│   ├── build.sh
│   └── .env.example
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## Implementation Order

### Phase 1: Foundation (This Session)
1. Create directory structure
2. Copy infrastructure files from MMAI
3. Adapt settings.py for CRB
4. Create main.py with health route
5. Create database migrations
6. Set up Docker + env files
7. Verify backend starts

### Phase 2: Auth & Core Routes
1. Copy auth middleware
2. Implement auth routes
3. Implement clients CRUD
4. Implement audits CRUD
5. Set up frontend auth context

### Phase 3: Intake System
1. Design questionnaire schema
2. Implement intake routes
3. Build frontend intake wizard
4. Store intake responses

### Phase 4: CRB Agent
1. Copy agent pattern from maestro
2. Implement CRB-specific tools
3. Set up knowledge pipeline
4. Integrate model routing

### Phase 5: Analysis & Reporting
1. Implement findings generation
2. Implement recommendations
3. Build ROI calculator
4. Create report generator

### Phase 6: Frontend & Polish
1. Build all pages
2. Implement report viewer
3. Add Stripe payments
4. Deploy to Railway

---

## Differentiators to Build

1. **Vendor Intelligence Database** - Real, verified pricing (not hallucinated)
2. **Industry Benchmarks** - Curated data by industry/size
3. **Transparent Assumptions** - Every ROI calculation shows its math
4. **Source Validation** - Every claim is cited
5. **Structured Methodology** - Not vibes, repeatable framework

---

## Quick Start Commands

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
uvicorn src.main:app --reload --port 8383

# Frontend
cd frontend
npm install
cp .env.example .env
npm run dev
```

---

## Notes

- Backend port: **8383** (to avoid conflict with MMAI's 8282)
- Frontend port: **5174** (to avoid conflict with MMAI's 5173)
- Use `crb_` prefix for all database tables if sharing Supabase instance
- Keep MMAI and CRB in separate Supabase projects for production
