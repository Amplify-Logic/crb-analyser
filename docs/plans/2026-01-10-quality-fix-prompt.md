# Product Quality Fix Execution Prompt

**Copy everything below the line and paste into a fresh Claude session:**

---

Execute the product quality fix plan at `docs/plans/2026-01-10-product-quality-fixes.md`

## Priority Order

Fix these in order, committing after each phase:

### Phase 1: Critical Security (DO FIRST)
1. Add payment verification to `backend/src/routes/reports.py` - `/public/{report_id}` endpoint must check quiz_session.status is "paid" or "completed"
2. Add `Depends(require_admin)` to ALL routes in `backend/src/routes/admin_research.py`
3. Add `Depends(require_admin)` to ALL routes in `backend/src/routes/admin_qa.py`
4. Create `backend/src/utils/prompt_safety.py` with `sanitize_user_input()` function, apply to `backend/src/skills/interview/acknowledgment_generator.py` and `followup.py`
5. Install DOMPurify in frontend, create `frontend/src/utils/sanitize.ts`, apply to all `dangerouslySetInnerHTML` in Interview.tsx, VoiceQuizInterview.tsx, WorkshopDeepDive.tsx
6. Remove dev bypass at `frontend/src/pages/Checkout.tsx:60-68` or properly gate with `import.meta.env.DEV`

### Phase 2: Critical Path
7. Move report generation to background task in `backend/src/routes/payments.py:557` using FastAPI BackgroundTasks
8. Add Redis lock in `backend/src/routes/reports.py:155` to prevent concurrent report generation
9. Add session expiry check in quiz routes

### Phase 3: Reliability
10. Add retry logic to `backend/src/config/supabase_client.py` (mirror Redis pattern)
11. Add model fallback chain in `backend/src/config/model_routing.py`
12. Move quiz state from memory to Redis (`backend/src/routes/quiz.py:1804`)
13. Wrap account creation in transaction-like rollback (`backend/src/routes/payments.py:61-151`)

### Phase 4: Frontend UX
14. Add keyboard accessibility to `frontend/src/components/report/NumberedRecommendations.tsx` (role="button", tabIndex, onKeyDown)
15. Add aria-labels to checkout button in `frontend/src/pages/Checkout.tsx:269`
16. Add focus trap to Workshop modal
17. Add browser support check to VoiceRecorder.tsx
18. Add email validation on blur in Checkout.tsx

### Phase 5: Testing
19. Set up Vitest in frontend with React Testing Library
20. Create `backend/tests/test_payments.py` with webhook and checkout tests
21. Create `backend/tests/test_auth.py` with signup/login tests

### Phase 6: Cleanup
22. Remove hardcoded localhost URLs
23. Remove console.log statements
24. Remove duplicate chart library (apexcharts or recharts)
25. Update outdated dependencies (FastAPI, python-jose)
26. Add CSP header

## Constraints

- Use TDD where practical
- Verify each fix before moving to next
- Commit after each phase with descriptive message
- Run `pytest` after backend changes
- Run `npm test` after frontend changes
- Do NOT skip security fixes for any reason

## Verification Commands

```bash
# After Phase 1
curl http://localhost:8383/api/reports/public/test-uuid  # Should 402
curl http://localhost:8383/api/admin/research/stale-count  # Should 401
curl http://localhost:8383/api/admin/qa/queue  # Should 401

# After all phases
cd backend && pytest -v
cd frontend && npm test
```

Start with Phase 1, task 1. Read the relevant files first, then implement the fix.
