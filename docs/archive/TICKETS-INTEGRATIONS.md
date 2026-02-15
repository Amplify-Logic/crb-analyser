# Integration Tickets - AGENT-5

> Tracking document for integration work. Updated: 2024-12-17

---

## Completed

### STRIPE-001: Webhook Handlers ✅
**Status:** Done
**Files:** `backend/src/routes/payments.py`
- [x] `checkout.session.completed` handler
- [x] `checkout.session.expired` handler
- [x] `charge.refunded` handler
- [x] `payment_intent.payment_failed` handler
- [x] Idempotency checks on both checkout flows

### EMAIL-001: Transactional Emails ✅
**Status:** Done
**Files:** `backend/src/services/email/__init__.py`
- [x] `send_payment_confirmation_email()` - sent after payment
- [x] `send_report_ready_email()` - sent when report completes
- [x] `send_report_failed_email()` - sent if generation fails

### STORAGE-001: Supabase Storage Service ✅
**Status:** Done
**Files:** `backend/src/services/storage_service.py`
- [x] `upload_pdf()` - upload to Supabase Storage
- [x] `get_signed_url()` - secure download URLs
- [x] `delete_pdf()` - remove files
- [x] `file_exists()` - check cache
- [x] `cleanup_old_files()` - purge old files (method exists)

### PDF-001: Storage Integration ✅
**Status:** Done
**Files:** `backend/src/routes/reports.py`
- [x] Check storage cache before generating
- [x] Cache PDF after first generation
- [x] Serve from signed URL when cached

### DB-001: Database Migration ✅
**Status:** Done
**Files:** `backend/MIGRATION_002_INTEGRATIONS.sql`
- [x] Updated `quiz_sessions` status constraint (added: generating, refunded, failed)
- [x] Updated `reports` status constraint (added: superseded)
- [x] Added `refund_amount` column to quiz_sessions and audits
- [x] Added `follow_up_sent_at` column to reports
- [x] Created storage bucket "reports" with RLS policies
- [x] Added index for follow-up email queries

---

## Pending - Infrastructure Required (Manual Steps)

### INFRA-001: Create Supabase Storage Bucket
**Status:** Included in MIGRATION_002
**Priority:** Critical (blocks storage)
**Action:** Run `MIGRATION_002_INTEGRATIONS.sql` - it includes bucket creation and RLS policies.

### INFRA-002: Stripe Webhook URL Configuration
**Status:** Pending
**Priority:** Critical (production)
**Action:**
1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://your-domain.com/api/payments/webhook`
3. Select events:
   - `checkout.session.completed`
   - `checkout.session.expired`
   - `charge.refunded`
   - `payment_intent.payment_failed`
4. Copy webhook secret to `STRIPE_WEBHOOK_SECRET` env var

### INFRA-003: SendGrid Configuration
**Status:** Pending
**Priority:** High
**Action:**
1. Create SendGrid account
2. Verify sender domain (`crb-analyser.com`)
3. Generate API key with Mail Send permission
4. Set env vars:
   - `SENDGRID_API_KEY`
   - `SENDGRID_FROM_EMAIL=reports@crb-analyser.com`
   - `SENDGRID_FROM_NAME=CRB Analyser`

---

## Pending - Development Required

### EMAIL-002: PDF Attachment in Report Ready Email ✅
**Status:** Done
**Files modified:**
- `backend/src/services/email/__init__.py` - Added `pdf_bytes` parameter and attachment logic
- `backend/src/routes/payments.py` - Generate PDF and pass to email function

### EMAIL-003: Follow-up Email Scheduler ✅
**Status:** Done
**Files created/modified:**
- `backend/src/services/email/__init__.py` - Added `send_follow_up_email()` function
- `backend/src/services/scheduler_service.py` - NEW: APScheduler-based job scheduler
- `backend/src/routes/admin.py` - NEW: Admin endpoints for manual job triggers
- `backend/src/main.py` - Integrated scheduler startup/shutdown

**Scheduled Jobs:**
- Follow-up emails: Daily at 10 AM UTC (7-day follow-up)
- Storage cleanup: Daily at 3 AM UTC (30-day retention)
- Quiz cleanup: Daily at 4 AM UTC (7-day expired sessions)

### STORAGE-002: Cleanup Cron Job ✅
**Status:** Done (included in EMAIL-003 scheduler)
**Implementation:** APScheduler in `scheduler_service.py`

### PDF-002: Advanced Chart Generation ✅
**Status:** Done
**Files created/modified:**
- `backend/src/services/chart_service.py` - NEW: Matplotlib chart generation
- `backend/src/services/pdf_generator.py` - Integrated charts into PDF template

**Charts Implemented:**
- AI Readiness Gauge (semi-circular)
- Two Pillars horizontal bar chart
- Value Timeline projection chart
- ROI Comparison bar chart
- Findings Breakdown pie chart

---

## Testing Required

### TEST-001: Full Payment Flow
**Status:** Pending
**Priority:** High
**Checklist:**
- [ ] Guest checkout creates quiz session
- [ ] Stripe redirect works
- [ ] Webhook processes payment
- [ ] Report generation triggers
- [ ] Emails send correctly
- [ ] PDF downloads work

### TEST-002: Error Scenarios
**Status:** Pending
**Priority:** High
**Checklist:**
- [ ] Expired checkout session handled
- [ ] Failed payment logged
- [ ] Refund updates status
- [ ] Report generation failure sends email
- [ ] Duplicate webhooks ignored (idempotency)

### TEST-003: Email Delivery
**Status:** Pending
**Priority:** Medium
**Checklist:**
- [ ] Payment confirmation arrives
- [ ] Report ready email arrives
- [ ] Links in emails work
- [ ] No spam folder issues
- [ ] Unsubscribe works (if applicable)

---

## Database Migrations

### DB-001: Migration 002 - Integrations ✅
**Status:** Ready to run
**File:** `backend/MIGRATION_002_INTEGRATIONS.sql`
**Includes:**
- `refund_amount` column on quiz_sessions and audits
- `follow_up_sent_at` column on reports
- Updated status constraints
- Storage bucket creation
- RLS policies

---

## Summary

| Category | Done | Pending |
|----------|------|---------|
| Stripe | 4/4 | 0 |
| Email | 5/5 | 0 |
| PDF | 3/3 | 0 |
| Storage | 6/6 | 0 |
| Scheduler | 3/3 | 0 |
| Database | 1/1 | 0 (migration ready) |
| Infrastructure | 0/3 | 3 (manual steps) |
| Testing | 0/3 | 3 |

**All Development Complete!**

**Next Actions (Manual/Infrastructure):**
1. Run `MIGRATION_002_INTEGRATIONS.sql` in Supabase SQL Editor
2. INFRA-002: Configure Stripe webhook URL in dashboard
3. INFRA-003: Set up SendGrid and verify domain
4. TEST-001: Full flow testing
