---
name: release-deploy
description: Pre-deploy verification checklist for CRB Analyser. Use before pushing to main or deploying to Railway. Runs tests, checks migrations, validates types, and confirms nothing is broken. Keywords - release, deploy, push, ship, checklist.
---

# Release & Deploy Checklist

## When to Use

Before pushing to `main` or deploying to production. Run this after completing a feature branch to verify everything is ship-ready.

## Phase 1: Pre-Flight Checks

### 1.1 Working Tree Status

```bash
cd "/Users/larsmusic/CRB Analyser/crb-analyser" && git status
```

Check for:
- Uncommitted changes that should be included
- Untracked files that should be gitignored
- Files that shouldn't be committed (`.env`, credentials, `node_modules/`)

### 1.2 Branch Status

```bash
git log --oneline main..HEAD  # What's being shipped
git diff --stat main..HEAD    # Files changed
```

Review the diff. Does every changed file belong in this release?

## Phase 2: Backend Verification

### 2.1 Tests

```bash
cd backend && pytest -v --tb=short 2>&1 | tail -40
```

**All tests must pass.** If any fail, fix before proceeding.

### 2.2 Type Checking

```bash
cd backend && python -m mypy src/ --strict --ignore-missing-imports 2>&1 | tail -30
```

Zero errors required. If `mypy` isn't configured, at minimum run:

```bash
cd backend && python -c "import src; print('Backend imports OK')"
```

### 2.3 Migration Check

```bash
ls -la backend/supabase/migrations/ | tail -5
```

If new migrations exist in this release:
- [ ] Migration has rollback comments
- [ ] Migration tested on local DB
- [ ] Migration number is sequential (currently up to 029)
- [ ] No destructive operations without deprecation period

### 2.4 Model Routing

```bash
cd backend && python -c "from src.config.model_routing import CLAUDE_MODELS; print('Models:', list(CLAUDE_MODELS.keys()))"
```

Verify no hardcoded model names were introduced:

```bash
cd backend && grep -r "claude-3-5\|gemini-2.0\|gemini-1.5" src/ --include="*.py" -l
```

If any files match, fix them to use `get_model_for_task()`.

## Phase 3: Frontend Verification

### 3.1 Build Check

```bash
cd frontend && pnpm build 2>&1 | tail -20
```

Must complete without errors. Warnings are OK but review them.

### 3.2 No Debug Artifacts

```bash
cd frontend && grep -r "console\.log\|debugger" src/ --include="*.ts" --include="*.tsx" -l
```

Remove any debug statements before shipping.

### 3.3 Frontend Tests (if available)

```bash
cd frontend && pnpm test --run 2>&1 | tail -20
```

## Phase 4: Security Scan

### 4.1 No Secrets in Code

```bash
grep -r "sk-\|supabase_key\|STRIPE_SECRET\|password.*=" backend/src/ frontend/src/ --include="*.py" --include="*.ts" --include="*.tsx" -l
```

If any matches, verify they're references to env vars, not actual secrets.

### 4.2 RLS Check

If any new tables were added, verify RLS policies exist:

```bash
grep -l "ENABLE ROW LEVEL SECURITY" backend/supabase/migrations/*.sql | tail -5
```

## Phase 5: Final Confirmation

Present a summary to the user:

```
Release Summary:
- Branch: [branch name]
- Commits: [count] new commits
- Backend tests: PASS/FAIL
- Type check: PASS/FAIL
- Frontend build: PASS/FAIL
- Migrations: [count] new (or none)
- Security: Clean / [issues found]

Ready to push? [y/n]
```

**Do NOT push without explicit user confirmation.**

## Phase 6: Push

Only after user confirms:

```bash
git push origin [branch-name]
```

If pushing to main directly (rare):

```bash
git push origin main
```

If creating a PR instead:

```bash
gh pr create --title "[title]" --body "$(cat <<'EOF'
## Summary
[bullet points]

## Verification
- [x] Backend tests pass
- [x] Type check passes
- [x] Frontend builds
- [x] No security issues
- [x] Migrations reviewed

EOF
)"
```

## Rules

- **Never skip tests** — even for "small" changes
- **Never push with failing tests** — fix them first
- **Always review the diff** — automated checks catch code issues, not logic errors
- **Confirm with user** — this skill never auto-pushes
- **If in doubt, PR** — prefer PR over direct push to main
