# Onboarding Release Checklist (Go/No-Go)

Use this checklist before onboarding free clients to production.

## Release Decision Rules

- **GO** only when every `P0` item is checked and no `P1` item is red.
- **NO-GO** if checkout-to-report flow fails once in staging or smoke checks fail.
- **NO-GO** if any dev-only route or bypass is enabled in production config.
- **NO-GO** if CI gates are bypassed or failing (tests, type checks, lint, drift, artifact denylist).

## P0 - Critical Path (Must Pass)

- [ ] `checkout -> success -> workshop -> report` happy path succeeds in staging with a fresh session.
- [ ] Checkout calls `/api/payments/guest-checkout` and receives canonical `quiz_session_id`.
- [ ] Success page verifies payment via `/api/quiz/sessions/{quizSessionId}` and enters workshop.
- [ ] Workshop completion resolves to report by `report_id` (direct or via `/report/{quizSessionId}/progress`).
- [ ] Report progress consumes `/api/reports/stream/{quiz_session_id}` and completes without simulation fallback.

## P1 - Security & Data (Must Pass)

- [ ] `ENABLE_DEV_ROUTES=false` and `DEV_ADMIN_BYPASS=false` in production environment variables.
- [ ] No public access to `/api/quiz/dev/*` routes in production.
- [ ] Stripe webhook events are persisted and deduplicated (`stripe_webhook_events` table present).
- [ ] RLS hardening migrations are applied (`026_stripe_webhook_events.sql`, `027_rls_policy_hardening.sql`).
- [ ] Payment failures trigger webhook 5xx for retry (no swallowed handler exceptions).

## P1 - Repo Hygiene (Must Pass)

- [ ] `.gitignore` includes generated artifact paths (`test-results`, `.playwright-cli`, `backend/reports`, `backend/bonbon_*`, `screenshots`).
- [ ] Artifact denylist check passes: `python backend/src/scripts/check_tracked_artifacts.py`.
- [ ] No secrets or generated client artifacts are staged in release PR.

## CI Gates (Must Pass)

- [ ] Backend full tests + coverage threshold pass (`pytest ... --cov-fail-under=35`).
- [ ] Backend smoke suite passes (`test_auth`, `test_payments`, `test_workshop_routes`).
- [ ] Backend Ruff gate passes on critical backend payment/auth/config files.
- [ ] Backend mypy gate passes on critical backend payment/auth/config/quiz files.
- [ ] Migration drift check passes (`python -m src.scripts.check_migration_drift`).
- [ ] Frontend lint passes.
- [ ] Frontend coverage tests pass with thresholds.
- [ ] Frontend TypeScript check passes (`pnpm exec tsc --noEmit`).
- [ ] Frontend production build passes.

## Staging Validation (Must Pass)

- [ ] Deploy staging backend and frontend from `staging` branch.
- [ ] Post-deploy smoke endpoints pass:
  - [ ] `/health`
  - [ ] `/api/health/ready`
- [ ] Execute one manual onboarding run and store the resulting report link.
- [ ] Confirm transactional emails for payment/welcome are delivered.

## Production Readiness (Final Go/No-Go)

- [ ] Production deploy completed from `main`.
- [ ] Production post-deploy smoke endpoints pass:
  - [ ] `/health`
  - [ ] `/api/health/ready`
- [ ] First real onboarding session manually monitored end-to-end.
- [ ] Error monitoring (Sentry/BetterStack) shows no new P0/P1 alerts for 30 minutes.

## Rollback Criteria (Immediate)

Trigger rollback immediately if any occurs:

- Checkout success rate drops below 95% for 15 minutes.
- Webhook failures spike or duplicate payment processing appears.
- Report generation fails for two consecutive onboarding sessions.
- Authentication/authorization regression exposes admin/dev access.

## Rollback Actions

1. Pause onboarding traffic.
2. Redeploy previous known-good Railway release.
3. Re-run smoke checks and one internal end-to-end flow.
4. Open incident note with root-cause, user impact, and remediation owner.
