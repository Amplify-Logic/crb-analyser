# CRB Analyser - Infrastructure

> This document describes HOW the system runs in production and how to operate it.
> For WHAT the product does, see [PRODUCT.md](./PRODUCT.md).
> For HOW to develop, see [CLAUDE.md](./CLAUDE.md).
> For WHY we're building this, see [STRATEGY.md](./STRATEGY.md).

---

## Environments

| Environment | Branch | Backend | Frontend | Auto-scale |
|-------------|--------|---------|----------|------------|
| **Production** | `main` | Railway, 2-5 replicas | Railway, 1 replica | CPU > 70% or memory > 80% |
| **Staging** | `staging` | Railway, 1 replica | Railway, 1 replica | No |
| **Development** | any | `localhost:8383` | `localhost:5174` | N/A |

**Deployment:** GitHub Actions → Railway. Rolling deploys, zero downtime.

```
Push to main → Tests (pytest + mypy + vitest + tsc) → Deploy backend → Deploy frontend → Slack notification
```

---

## Service Map

```
                    ┌─────────────────────┐
                    │   Frontend (Nginx)   │
                    │   React + Vite       │
                    │   Port 80 (prod)     │
                    │   Port 5174 (dev)    │
                    └──────────┬──────────┘
                               │ /api/*
                    ┌──────────▼──────────┐
                    │   Backend (FastAPI)  │
                    │   Uvicorn (async)    │
                    │   Port 8383          │
                    └──┬───┬───┬───┬──────┘
                       │   │   │   │
              ┌────────┘   │   │   └────────┐
              ▼            ▼   ▼            ▼
        ┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────────┐
        │ Supabase │ │ Redis  │ │ Stripe │ │ LLM APIs     │
        │ (Postgres│ │ Cache  │ │Payments│ │ Claude (pri)  │
        │  + RLS)  │ │ + Rate │ │        │ │ Gemini (sec)  │
        │          │ │ Limit  │ │        │ │ OpenAI (embed)│
        └──────────┘ └────────┘ └────────┘ └──────────────┘
```

---

## Dependencies & Their Roles

| Service | Role | Required | Degradation |
|---------|------|----------|-------------|
| **Supabase** | Database (PostgreSQL + RLS), auth | Yes | App won't start |
| **Redis** | Cache, rate limiting, payment locks | No | Falls back to in-memory LRU (bounded 10k entries) |
| **Anthropic Claude** | Primary LLM (analysis, reports) | Yes | No reports generated |
| **Google Gemini** | Secondary LLM (research, flash tasks) | No | Falls back to Claude |
| **Stripe** | Payments, webhooks | Yes (for paid flow) | Quiz still works, payment fails |
| **SendGrid** | Transactional email | No | Users don't get email notifications |
| **Brevo** | Marketing email sequences | No | No follow-up sequences |
| **BetterStack** | Centralized logging | No | Logs only local |
| **Logfire** | Structured tracing | No | No trace visualization |
| **Sentry** | Error tracking | No | Errors only in logs |

**Design principle:** Only Supabase and Claude are hard dependencies. Everything else degrades gracefully. This keeps the system running even when third-party services have outages.

---

## Environment Variables

### Required (app won't function without these)

```bash
SUPABASE_URL=                  # PostgreSQL via Supabase
SUPABASE_SERVICE_KEY=          # Service role key (bypasses RLS)
SECRET_KEY=                    # JWT signing (min 32 chars in production)
ANTHROPIC_API_KEY=             # Primary LLM
STRIPE_SECRET_KEY=             # Payment processing
STRIPE_WEBHOOK_SECRET=         # Webhook signature verification
```

### Optional (graceful degradation if missing)

```bash
# Cache
REDIS_URL=redis://localhost:6379
REDIS_MAX_CONNECTIONS=10

# Secondary LLMs
GOOGLE_API_KEY=                # Gemini (research, flash tasks)
OPENAI_API_KEY=                # Embeddings
DEEPSEEK_API_KEY=              # Budget model option

# Email
SENDGRID_API_KEY=              # Transactional email
BREVO_API_KEY=                 # Marketing sequences

# Search
BRAVE_SEARCH_API_KEY=          # Web search for research agents
TAVILY_API_KEY=                # Alternative search

# Monitoring
LOGFIRE_TOKEN=                 # Structured tracing
SENTRY_DSN=                    # Error tracking
BETTERSTACK_SOURCE_TOKEN=      # Centralized logging

# App config
APP_ENV=development            # development | production
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
FRONTEND_URL=http://localhost:5174
```

### Frontend (build-time, prefixed with VITE_)

```bash
VITE_API_BASE_URL=http://localhost:8383
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
VITE_STRIPE_PUBLISHABLE_KEY=
```

---

## Health Checks

| Endpoint | Purpose | What it checks |
|----------|---------|----------------|
| `/health` | Load balancer liveness | App is running |
| `/api/health` | Detailed status | App version, uptime |
| `/api/health/ready` | Readiness probe | Supabase + Redis + API keys all connected |
| `/api/health/live` | Kubernetes liveness | Process is healthy |

**Railway health check:** Backend polls `/health` every 30s. Frontend polls `/` every 10s.

---

## Caching Strategy

| Data Type | TTL | Why |
|-----------|-----|-----|
| Knowledge base | 1 hour | Rarely changes, expensive to recompute |
| Vendor pricing | 24 hours | Updated by research agents, not real-time |
| Benchmarks | 7 days | Quarterly refresh cycle |
| Quiz sessions | 24 hours | Active user sessions |
| Rate limits | Sliding window | Security-critical, always fresh |

**Rules:**
- Never cache user-specific data without key isolation
- Redis unavailable = app continues with degraded caching (not an outage)
- Cache keys include industry vertical for data isolation

---

## Rate Limiting

| Scope | Limit | Algorithm |
|-------|-------|-----------|
| Global (per IP) | 60 req/min | Sliding window (Redis) |
| Sensitive endpoints | Lower, per-endpoint | Per-endpoint limiter |
| Email enumeration | Per-email | Prevents account probing |

**Fallback:** If Redis down, rate limiting uses bounded in-memory LRU (10k entries max). This prevents memory leaks while maintaining protection.

---

## Security

### Infrastructure Security
- **RLS on all Supabase tables** — no direct DB access without policy match
- **HTTPS everywhere** — Railway provides automatic SSL
- **HSTS** in production (31536000s, includeSubDomains)
- **Security headers:** X-Frame-Options (DENY), X-Content-Type-Options (nosniff), X-XSS-Protection, strict Referrer-Policy

### Application Security
- **Pydantic validation** on all API inputs
- **Stripe webhook signature verification** — prevents forged payment events
- **Payment locks** (5-min TTL in Redis) — prevents race conditions on double-payment
- **No raw errors to users** in production — all errors go through APIError handler
- **Secrets protection** — Claude Code hook blocks access to `.env` files

### CORS
- Development: `localhost:5173-5177`
- Production: configured via `CORS_ORIGINS` env var
- Credentials allowed, all methods, all headers

---

## Monitoring & Observability

### Three Layers

| Layer | Tool | What it captures |
|-------|------|-----------------|
| **Logs** | BetterStack + structlog | Structured events with context (user_id, session_id, industry) |
| **Traces** | Logfire | Request traces through FastAPI + httpx + Redis |
| **Errors** | Sentry | Exceptions with stack traces, release tracking, performance |

### Key Alerts (Production)

| Alert | Condition | Action |
|-------|-----------|--------|
| Report generation failure | 3+ failures in 5 minutes | Check Claude API rate limits, check Supabase |
| Payment webhook failure | Any failure | Check Stripe dashboard, verify webhook secret |
| Health check failure | /ready returns unhealthy | Check which dependency is down |
| High error rate | >5% of requests failing | Check Sentry for error grouping |

### Logging Best Practice
```python
import structlog
logger = structlog.get_logger()

# Always include context
logger.info("report_generated", session_id=session_id, industry=industry, duration_ms=elapsed)
```

---

## Scaling Considerations

### Current Capacity (2-5 replicas)
- Each backend replica: 2GB memory, 1 CPU, async Uvicorn
- Redis: 256MB (Docker) / managed (Railway)
- Supabase: managed PostgreSQL

### Scaling Triggers

| Metric | Threshold | Action |
|--------|-----------|--------|
| CPU | > 70% sustained | Railway auto-adds replica (up to 5) |
| Memory | > 80% sustained | Railway auto-adds replica |
| Report queue depth | > 10 concurrent | Consider background job queue (future) |
| Vendor DB size | > 10k vendors | Consider dedicated search index |

### What Scales Well (No Changes Needed)
- Quiz flow (stateless, fast)
- Report viewing (static data from Supabase)
- Webhook processing (idempotent)

### What Needs Attention at Scale
- **Report generation** — Long-running (30-120s), holds LLM connections. At 50+ concurrent reports, consider: background job queue (Celery/ARQ), dedicated worker pool, or streaming generation status via SSE.
- **Vendor research agents** — Playwright browser instances are memory-heavy. At scale, containerize scraping separately.
- **Knowledge base** — Currently JSON files in repo. At 500+ reports, consider migrating curated data to Supabase + pgvector for RAG.

---

## Database

### Schema Overview
```
quiz_sessions → reports → findings, recommendations, playbook
     ↓
  payments (Stripe)

vendors ← industry_vendor_tiers (T1/T2/T3 per industry)
     ↓
vendor_audit_log

knowledge_embeddings (pgvector for RAG)
```

### Migrations
Location: `backend/supabase/migrations/`

```bash
touch backend/supabase/migrations/XXX_description.sql   # Create
supabase db push                                         # Apply locally
supabase db push --linked                                # Apply to production
```

**Rules:** Migrations must be reversible. Never delete columns without deprecation. Test locally first. Backup before production.

---

## Docker (Development)

```bash
docker-compose up              # Start full stack (backend + frontend + Redis)
docker-compose up -d redis     # Just Redis
```

| Service | Memory Limit | CPU Limit | Notes |
|---------|-------------|-----------|-------|
| Backend | 2GB | 1 CPU | Depends on Redis |
| Frontend | 256MB | 0.5 CPU | Depends on Backend |
| Redis | 512MB | 0.5 CPU | LRU eviction, AOF persistence |

---

## Quick Start (Development)

```bash
# Option 1: Docker (all services)
docker-compose up

# Option 2: Manual
brew services start redis
cd backend && source venv/bin/activate && uvicorn src.main:app --reload --port 8383
cd frontend && pnpm dev
```

---

## Runbook: Common Operations

| Operation | Command |
|-----------|---------|
| Run all tests | `make test` |
| Type check | `make typecheck` |
| Lint | `make lint` |
| Generate test report | `make dev-report` |
| Refresh vendor data | `make vendor-refresh` |
| Audit knowledge base | `make kb-audit` |
| Check expertise health | `make expertise-health` |
| Full data refresh | `make data-refresh-cron` |
