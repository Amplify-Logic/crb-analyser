# AGENT 6: DevOps & Infrastructure

> **Mission:** Make CRB Analyser reliable, fast, and scalable. Zero-downtime deployments, instant rollbacks, comprehensive monitoring. The infrastructure should be invisible to users - it just works.

---

## Context

**Product:** CRB Analyser - AI-powered Cost/Risk/Benefit analysis
**Traffic Expectation:** 10-100 reports/day initially, scaling to 1000+
**SLA Target:** 99.9% uptime, <2s page loads, <2min report generation

**Stack:**
- Backend: FastAPI on Railway
- Frontend: React on Railway/Vercel
- Database: Supabase (PostgreSQL)
- Cache: Redis (Railway or Upstash)
- Storage: Supabase Storage
- Monitoring: Logfire + Sentry

---

## Current State

```
/
├── backend/
│   ├── Dockerfile
│   ├── railway.toml
│   └── requirements.txt
├── frontend/
│   ├── Dockerfile
│   ├── railway.json
│   └── package.json
└── docker-compose.yml (local dev)
```

**What Exists:**
- Basic Dockerfiles
- Railway config files
- Local development setup

**What's Missing:**
- CI/CD pipeline
- Proper health checks
- Monitoring and alerting
- Staging environment
- Database migrations system
- Secrets management
- Performance optimization
- Error tracking

---

## Target State

### 1. Environment Structure

```
ENVIRONMENTS:
├── local          # docker-compose, hot reload
├── staging        # Railway staging project
└── production     # Railway production project

SERVICES PER ENVIRONMENT:
├── crb-backend    # FastAPI API
├── crb-frontend   # React SPA
├── redis          # Cache layer
└── (supabase)     # External - separate staging/prod projects
```

**Environment Variables by Stage:**
```bash
# .env.local
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG
API_BASE_URL=http://localhost:8383
SUPABASE_URL=https://xxx-staging.supabase.co

# .env.staging
APP_ENV=staging
DEBUG=false
LOG_LEVEL=INFO
API_BASE_URL=https://staging-api.crb-analyser.com
SUPABASE_URL=https://xxx-staging.supabase.co

# .env.production
APP_ENV=production
DEBUG=false
LOG_LEVEL=WARNING
API_BASE_URL=https://api.crb-analyser.com
SUPABASE_URL=https://xxx-prod.supabase.co
```

### 2. Docker Configuration

**Backend Dockerfile (Optimized):**
```dockerfile
# backend/Dockerfile
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production image
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    # WeasyPrint dependencies for PDF
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY src/ ./src/
COPY templates/ ./templates/

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8383/api/health || exit 1

EXPOSE 8383

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8383", "--workers", "2"]
```

**Frontend Dockerfile:**
```dockerfile
# frontend/Dockerfile
FROM node:20-alpine as builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Build
COPY . .
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# Production image with nginx
FROM nginx:alpine

# Copy build
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**Nginx Config for SPA:**
```nginx
# frontend/nginx.conf
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA routing - serve index.html for all routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Health check endpoint
    location /health {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
```

**Docker Compose (Local Dev):**
```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "8383:8383"
    volumes:
      - ./backend/src:/app/src
    environment:
      - APP_ENV=development
      - DEBUG=true
      - REDIS_URL=redis://redis:6379
    env_file:
      - ./backend/.env
    depends_on:
      - redis
    command: uvicorn src.main:app --host 0.0.0.0 --port 8383 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "5174:5174"
    volumes:
      - ./frontend/src:/app/src
    environment:
      - VITE_API_BASE_URL=http://localhost:8383

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### 3. Railway Configuration

**Backend railway.toml:**
```toml
[build]
builder = "dockerfile"
dockerfilePath = "Dockerfile"

[deploy]
numReplicas = 2
healthcheckPath = "/api/health"
healthcheckTimeout = 10
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3

[deploy.resources]
memory = "1GB"
cpu = 1

[[services]]
name = "crb-backend"
port = 8383
```

**Frontend railway.json:**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "dockerfile",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "numReplicas": 1,
    "healthcheckPath": "/health",
    "restartPolicyType": "on_failure"
  }
}
```

### 4. CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main]

env:
  RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install backend dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio

      - name: Run backend tests
        run: |
          cd backend
          pytest tests/ -v
        env:
          APP_ENV: test

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install frontend dependencies
        run: |
          cd frontend
          npm ci

      - name: Run frontend tests
        run: |
          cd frontend
          npm run test:ci

      - name: Build frontend
        run: |
          cd frontend
          npm run build

  deploy-staging:
    needs: test
    if: github.ref == 'refs/heads/staging'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Install Railway CLI
        run: npm install -g @railway/cli

      - name: Deploy Backend to Staging
        run: |
          cd backend
          railway link ${{ secrets.RAILWAY_STAGING_PROJECT_ID }}
          railway up --service crb-backend

      - name: Deploy Frontend to Staging
        run: |
          cd frontend
          railway link ${{ secrets.RAILWAY_STAGING_PROJECT_ID }}
          railway up --service crb-frontend

  deploy-production:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Install Railway CLI
        run: npm install -g @railway/cli

      - name: Deploy Backend to Production
        run: |
          cd backend
          railway link ${{ secrets.RAILWAY_PROD_PROJECT_ID }}
          railway up --service crb-backend

      - name: Deploy Frontend to Production
        run: |
          cd frontend
          railway link ${{ secrets.RAILWAY_PROD_PROJECT_ID }}
          railway up --service crb-frontend

      - name: Notify Slack
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "CRB Analyser deployed to production :rocket:"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### 5. Database Migrations

```python
# backend/src/migrations/migrator.py

import os
from pathlib import Path
from supabase import AsyncClient

class Migrator:
    def __init__(self, supabase: AsyncClient):
        self.supabase = supabase
        self.migrations_dir = Path(__file__).parent / "versions"

    async def run_migrations(self):
        """Run all pending migrations."""

        # Get applied migrations
        result = await self.supabase.table("schema_migrations")\
            .select("version")\
            .execute()
        applied = {m["version"] for m in result.data}

        # Find and run pending migrations
        migration_files = sorted(self.migrations_dir.glob("*.sql"))

        for migration_file in migration_files:
            version = migration_file.stem  # e.g., "001_initial"

            if version not in applied:
                print(f"Running migration: {version}")

                sql = migration_file.read_text()
                await self.supabase.rpc("exec_sql", {"sql": sql}).execute()

                # Record migration
                await self.supabase.table("schema_migrations").insert({
                    "version": version,
                    "applied_at": datetime.utcnow().isoformat()
                }).execute()

                print(f"Migration {version} complete")

        print("All migrations complete")
```

**Migration Files:**
```
backend/src/migrations/versions/
├── 001_initial_schema.sql
├── 002_add_vendors_table.sql
├── 003_add_pricing_history.sql
└── ...
```

### 6. Monitoring & Observability

**Logfire Setup:**
```python
# backend/src/config/observability.py

import logfire
from opentelemetry import trace

def setup_observability():
    """Configure Logfire for monitoring."""

    logfire.configure(
        token=settings.LOGFIRE_TOKEN,
        service_name="crb-backend",
        service_version=settings.APP_VERSION,
        environment=settings.APP_ENV
    )

    # Instrument FastAPI
    logfire.instrument_fastapi(app)

    # Instrument httpx for API calls
    logfire.instrument_httpx()

    # Instrument Redis
    logfire.instrument_redis()

    return logfire
```

**Custom Metrics:**
```python
# Track report generation
with logfire.span("report_generation", report_id=report_id):
    logfire.info("Starting report generation", quiz_session_id=quiz_session_id)

    start_time = time.time()
    report = await generate_report(quiz_session_id)
    duration = time.time() - start_time

    logfire.info(
        "Report generated",
        duration_seconds=duration,
        findings_count=len(report.findings),
        recommendations_count=len(report.recommendations)
    )

# Track API costs
logfire.info(
    "claude_api_call",
    model=model,
    input_tokens=response.usage.input_tokens,
    output_tokens=response.usage.output_tokens,
    cost_usd=calculate_cost(response.usage)
)
```

**Sentry for Error Tracking:**
```python
# backend/src/config/sentry.py

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration

def setup_sentry():
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1 if settings.APP_ENV == "production" else 1.0,
        profiles_sample_rate=0.1,
        send_default_pii=False,
    )
```

### 7. Health Checks

```python
# backend/src/routes/health_routes.py

from datetime import datetime
import redis
from supabase import AsyncClient

@router.get("/health")
async def health_check():
    """Basic health check for load balancer."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@router.get("/health/detailed")
async def detailed_health_check(
    supabase: AsyncClient = Depends(get_supabase),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Detailed health check for monitoring."""

    checks = {}

    # Database check
    try:
        start = time.time()
        await supabase.table("health_check").select("1").limit(1).execute()
        checks["database"] = {
            "status": "healthy",
            "latency_ms": round((time.time() - start) * 1000, 2)
        }
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}

    # Redis check
    try:
        start = time.time()
        await redis_client.ping()
        checks["redis"] = {
            "status": "healthy",
            "latency_ms": round((time.time() - start) * 1000, 2)
        }
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}

    # Claude API check (just verify key is set)
    checks["claude_api"] = {
        "status": "healthy" if settings.ANTHROPIC_API_KEY else "unhealthy"
    }

    # Overall status
    overall = "healthy" if all(
        c.get("status") == "healthy" for c in checks.values()
    ) else "degraded"

    return {
        "status": overall,
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "checks": checks
    }
```

### 8. Performance Optimization

**Backend Optimization:**
```python
# Connection pooling
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.supabase_pool = create_supabase_pool(max_size=20)
    app.state.redis_pool = create_redis_pool(max_connections=50)

    yield

    # Shutdown
    await app.state.supabase_pool.close()
    await app.state.redis_pool.close()

# Response compression
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS optimization
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    max_age=86400,  # Cache preflight for 24h
)
```

**Frontend Optimization:**
```javascript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'charts': ['recharts'],
          'motion': ['framer-motion'],
        }
      }
    },
    // Enable minification
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
      }
    }
  },
  // Enable dependency pre-bundling
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', 'recharts']
  }
})
```

---

## Specific Tasks

### Phase 1: Local Dev Environment
- [ ] Finalize docker-compose.yml
- [ ] Create Dockerfile.dev for hot reload
- [ ] Document local setup in README
- [ ] Test full stack locally

### Phase 2: CI/CD Pipeline
- [ ] Set up GitHub Actions workflow
- [ ] Configure test job
- [ ] Configure staging deployment
- [ ] Configure production deployment
- [ ] Add Slack notifications

### Phase 3: Railway Setup
- [ ] Create staging project
- [ ] Create production project
- [ ] Configure environment variables
- [ ] Set up custom domains
- [ ] Configure health checks

### Phase 4: Database Migrations
- [ ] Create migrations table
- [ ] Implement migrator class
- [ ] Create initial migration
- [ ] Test migration flow

### Phase 5: Monitoring
- [ ] Set up Logfire
- [ ] Set up Sentry
- [ ] Create custom dashboards
- [ ] Configure alerting rules
- [ ] Document runbooks

### Phase 6: Performance
- [ ] Optimize Docker images
- [ ] Configure caching headers
- [ ] Enable compression
- [ ] Load test (target: 100 concurrent users)
- [ ] Document performance baselines

---

## Dependencies

**Needs from All Agents:**
- Final code to deploy
- Environment variable requirements
- External service dependencies

**Provides to All Agents:**
- Deployment infrastructure
- Environment URLs
- Monitoring dashboards

---

## Deliverables

1. **Docker Configuration** - Optimized multi-stage builds
2. **CI/CD Pipeline** - GitHub Actions with test, stage, prod
3. **Railway Setup** - Staging + Production environments
4. **Migration System** - Database version control
5. **Monitoring** - Logfire + Sentry dashboards
6. **Documentation** - Runbooks, architecture diagrams

---

## Environment Variables (Complete List)

```bash
# App
APP_ENV=production
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=WARNING
SECRET_KEY=your-32-char-secret

# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
DATABASE_URL=postgresql://...

# Cache
REDIS_URL=redis://...

# AI
ANTHROPIC_API_KEY=sk-ant-...

# Payments
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PUBLISHABLE_KEY=pk_live_...

# Email
SENDGRID_API_KEY=SG...
SENDGRID_FROM_EMAIL=reports@crb-analyser.com

# Monitoring
LOGFIRE_TOKEN=...
SENTRY_DSN=https://...

# Search (optional)
BRAVE_API_KEY=...
TAVILY_API_KEY=...
```

---

## Quality Criteria

- [ ] Zero-downtime deployments
- [ ] Rollback capability < 2 minutes
- [ ] Health checks pass before traffic
- [ ] 99.9% uptime SLA achievable
- [ ] All errors logged to Sentry
- [ ] Performance metrics in Logfire
- [ ] < 2s page load times
- [ ] < 2min report generation

---

## Runbook: Common Operations

**Deploy to Production:**
```bash
git checkout main
git pull
git merge staging  # After QA on staging
git push origin main
# GitHub Actions handles the rest
```

**Rollback:**
```bash
railway rollback --service crb-backend
railway rollback --service crb-frontend
```

**Check Logs:**
```bash
railway logs --service crb-backend
railway logs --service crb-frontend
```

**Run Migration:**
```bash
railway run --service crb-backend python -m src.migrations.run
```

**Clear Cache:**
```bash
railway run --service crb-backend python -c "from src.services.cache import clear_all; clear_all()"
```
