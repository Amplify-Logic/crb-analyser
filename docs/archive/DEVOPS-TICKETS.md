# DevOps Tickets - Manual Actions Required

> Generated: 2024-12-17
> Status: Action required before production deployment

---

## Priority 1: Blocking Production

### TICKET-001: Create Railway Projects
**Status:** TODO
**Owner:** DevOps
**Effort:** 30 min

**Description:**
Create staging and production projects in Railway.

**Actions:**
1. Log into Railway dashboard
2. Create project: `crb-analyser-staging`
3. Create project: `crb-analyser-production`
4. Note down project IDs for GitHub secrets

**Acceptance Criteria:**
- [ ] Staging project created
- [ ] Production project created
- [ ] Project IDs documented

---

### TICKET-002: Configure GitHub Secrets
**Status:** TODO
**Owner:** DevOps
**Effort:** 15 min

**Description:**
Add required secrets to GitHub repository for CI/CD pipeline.

**Actions:**
1. Go to Repository → Settings → Secrets → Actions
2. Add the following secrets:
   - `RAILWAY_TOKEN` - Get from Railway account settings
   - `RAILWAY_STAGING_PROJECT_ID` - From TICKET-001
   - `RAILWAY_PROD_PROJECT_ID` - From TICKET-001
   - `SLACK_WEBHOOK_URL` (optional) - For deployment notifications

**Acceptance Criteria:**
- [ ] All secrets added
- [ ] CI/CD workflow runs successfully

---

### TICKET-003: Configure Railway Environment Variables
**Status:** TODO
**Owner:** DevOps
**Effort:** 45 min

**Description:**
Set environment variables in Railway for both staging and production.

**Actions:**
1. **Staging Project:**
   - Copy variables from `backend/.env.staging`
   - Set actual values (API keys, Supabase staging credentials)
   - Configure frontend build args

2. **Production Project:**
   - Copy variables from `backend/.env.production`
   - Set actual values (LIVE API keys, production Supabase)
   - Configure frontend build args

**Critical Variables:**
```
SUPABASE_URL
SUPABASE_SERVICE_KEY
ANTHROPIC_API_KEY
STRIPE_SECRET_KEY (test for staging, live for prod)
STRIPE_WEBHOOK_SECRET
REDIS_URL
SECRET_KEY (unique per environment)
```

**Acceptance Criteria:**
- [ ] Staging variables configured
- [ ] Production variables configured
- [ ] Health check passes on deployment

---

### TICKET-004: Create Supabase Projects
**Status:** TODO
**Owner:** DevOps
**Effort:** 1 hour

**Description:**
Create separate Supabase projects for staging and production.

**Actions:**
1. Create staging project in Supabase dashboard
2. Create production project in Supabase dashboard
3. Run initial migration on both:
   ```sql
   -- Create migrations tracking table
   CREATE TABLE schema_migrations (
     version VARCHAR(255) PRIMARY KEY,
     applied_at TIMESTAMPTZ DEFAULT NOW(),
     checksum VARCHAR(64)
   );
   ```
4. Run `001_initial_schema.sql` migration
5. Note credentials for Railway configuration

**Acceptance Criteria:**
- [ ] Staging Supabase project created
- [ ] Production Supabase project created
- [ ] Schema migrations table exists
- [ ] Initial schema deployed

---

### TICKET-005: Configure Custom Domains
**Status:** TODO
**Owner:** DevOps
**Effort:** 30 min

**Description:**
Set up custom domains for production.

**Actions:**
1. In Railway production project:
   - Backend: `api.crb-analyser.com`
   - Frontend: `crb-analyser.com` and `www.crb-analyser.com`
2. Configure DNS records:
   - CNAME for `api` → Railway backend URL
   - CNAME for `@` and `www` → Railway frontend URL
3. Enable SSL (automatic in Railway)

**Acceptance Criteria:**
- [ ] Custom domains configured
- [ ] SSL certificates active
- [ ] DNS propagated

---

## Priority 2: Production Readiness

### TICKET-006: Set Up Stripe Webhooks
**Status:** TODO
**Owner:** DevOps
**Effort:** 20 min

**Description:**
Configure Stripe webhook endpoints for payment processing.

**Actions:**
1. **Staging:**
   - Stripe Dashboard → Webhooks → Add endpoint
   - URL: `https://staging-api.crb-analyser.com/api/payments/webhook`
   - Events: `checkout.session.completed`, `payment_intent.succeeded`
   - Copy webhook secret to Railway

2. **Production:**
   - Same steps with production URL
   - URL: `https://api.crb-analyser.com/api/payments/webhook`

**Acceptance Criteria:**
- [ ] Staging webhook configured
- [ ] Production webhook configured
- [ ] Test payment flow works

---

### TICKET-007: Set Up Monitoring Services
**Status:** TODO
**Owner:** DevOps
**Effort:** 1 hour

**Description:**
Create accounts and configure monitoring services.

**Actions:**
1. **Logfire:**
   - Create account at logfire.pydantic.dev
   - Create project for CRB Analyser
   - Get token, add to Railway env vars

2. **Sentry:**
   - Create account at sentry.io
   - Create project (Python/FastAPI)
   - Create project (JavaScript/React)
   - Get DSNs, add to Railway env vars

3. **Langfuse (optional):**
   - Create account at langfuse.com
   - Create project for LLM tracing
   - Get keys, add to Railway env vars

**Acceptance Criteria:**
- [ ] Logfire receiving logs
- [ ] Sentry receiving errors
- [ ] Dashboards accessible

---

### TICKET-008: Configure SendGrid
**Status:** TODO
**Owner:** DevOps
**Effort:** 30 min

**Description:**
Set up SendGrid for transactional emails.

**Actions:**
1. Create SendGrid account
2. Verify sender domain (`crb-analyser.com`)
3. Create API key with Mail Send permissions
4. Add to Railway env vars
5. Create email templates for:
   - Report ready notification
   - Payment confirmation

**Acceptance Criteria:**
- [ ] Domain verified
- [ ] API key configured
- [ ] Test email sends successfully

---

## Priority 3: Operations

### TICKET-009: Create Staging Branch
**Status:** TODO
**Owner:** DevOps
**Effort:** 5 min

**Description:**
Create `staging` branch for staging deployments.

**Actions:**
```bash
git checkout main
git checkout -b staging
git push -u origin staging
```

**Workflow:**
- `main` → Production deployments
- `staging` → Staging deployments
- Feature branches → PR to staging first

**Acceptance Criteria:**
- [ ] Staging branch exists
- [ ] CI/CD triggers on staging push

---

### TICKET-010: Set Up Redis
**Status:** TODO
**Owner:** DevOps
**Effort:** 15 min

**Description:**
Add Redis service to Railway projects.

**Actions:**
1. In Railway staging project:
   - Add service → Redis
   - Note internal URL
   - Set `REDIS_URL` env var

2. In Railway production project:
   - Same steps
   - Or use Upstash for serverless Redis

**Acceptance Criteria:**
- [ ] Staging Redis running
- [ ] Production Redis running
- [ ] Health check shows Redis healthy

---

### TICKET-011: Document Runbooks
**Status:** TODO
**Owner:** DevOps
**Effort:** 2 hours

**Description:**
Create operational runbooks for common tasks.

**Runbooks Needed:**
1. **Deployment Rollback** - How to rollback a bad deployment
2. **Database Migration** - How to run migrations
3. **Cache Clear** - How to clear Redis cache
4. **Log Investigation** - How to find and analyze logs
5. **Incident Response** - Steps for production incidents

**Acceptance Criteria:**
- [ ] Runbooks created in `/docs/runbooks/`
- [ ] Team reviewed and understands procedures

---

## Priority 4: Nice to Have

### TICKET-012: Load Testing
**Status:** TODO
**Owner:** DevOps
**Effort:** 4 hours

**Description:**
Perform load testing to validate performance targets.

**Targets:**
- 100 concurrent users
- <2s page load times
- <2min report generation

**Actions:**
1. Set up k6 or Locust
2. Create test scenarios
3. Run against staging
4. Document baseline metrics
5. Identify bottlenecks

**Acceptance Criteria:**
- [ ] Load test scripts created
- [ ] Baseline documented
- [ ] Performance meets targets

---

### TICKET-013: Set Up Uptime Monitoring
**Status:** TODO
**Owner:** DevOps
**Effort:** 30 min

**Description:**
Configure external uptime monitoring.

**Options:**
- UptimeRobot (free tier)
- Better Uptime
- Pingdom

**Monitors:**
- `https://api.crb-analyser.com/health`
- `https://crb-analyser.com`

**Acceptance Criteria:**
- [ ] Monitors configured
- [ ] Alert notifications set up
- [ ] Status page created (optional)

---

## Summary

| Priority | Tickets | Estimated Effort |
|----------|---------|------------------|
| P1 - Blocking | 5 tickets | ~3 hours |
| P2 - Production Ready | 3 tickets | ~2 hours |
| P3 - Operations | 3 tickets | ~2.5 hours |
| P4 - Nice to Have | 2 tickets | ~4.5 hours |

**Total:** 13 tickets, ~12 hours of work

---

## Quick Start Checklist

For fastest path to production:

1. [ ] TICKET-001: Create Railway projects
2. [ ] TICKET-004: Create Supabase projects
3. [ ] TICKET-002: Configure GitHub secrets
4. [ ] TICKET-003: Configure Railway env vars
5. [ ] TICKET-009: Create staging branch
6. [ ] TICKET-010: Set up Redis
7. [ ] Deploy to staging, test
8. [ ] TICKET-005: Configure custom domains
9. [ ] TICKET-006: Set up Stripe webhooks
10. [ ] Deploy to production
