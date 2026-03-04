.PHONY: test test-backend test-frontend lint typecheck dev generate-report dev-report dev-report-all ui-test ui-test-headed playwright-install playwright-cli-install generate-report-playwright research-vendor test-all data-refresh vendor-refresh kb-audit expertise-health vendor-discover data-refresh-cron db-audit db-audit-fix migration-drift-check artifact-denylist-check gen-ecommerce gen-dental gen-professional-services gen-b2b-platforms review-ecommerce review-dental review-professional-services review-b2b-platforms review-report

test: test-backend test-frontend

test-backend:
	cd backend && python -m pytest tests/ -v

test-frontend:
	cd frontend && npx vitest run

lint:
	cd backend && python -m ruff check src/
	cd frontend && npm run lint

typecheck:
	cd backend && python -m mypy src/ --ignore-missing-imports
	cd frontend && npx tsc --noEmit

dev:
	@echo "Start backend: cd backend && source venv/bin/activate && uvicorn src.main:app --reload --port 8383"
	@echo "Start frontend: cd frontend && npm run dev"
	@echo "Start Redis: brew services start redis"

generate-report:
	cd backend && python -m src.cli.generate_report $(ARGS)

# Dev mode report generation (multi-industry)
dev-report:
	@echo "Generating $(or $(INDUSTRY),ecommerce) report..."
	cd backend && python -m src.cli.generate_report --industry $(or $(INDUSTRY),ecommerce) $(ARGS)

dev-report-all:
	@echo "Generating one report per industry..."
	cd backend && python -m src.cli.generate_report --batch --all-industries $(ARGS)

# =============================================================================
# Per-Industry: Generate
# =============================================================================

gen-ecommerce:
	cd backend && python generate_and_review.py --industry ecommerce $(ARGS)

gen-dental:
	cd backend && python generate_and_review.py --industry dental $(ARGS)

gen-professional-services:
	cd backend && python generate_and_review.py --industry professional-services $(ARGS)

gen-b2b-platforms:
	cd backend && python generate_and_review.py --industry b2b-platforms $(ARGS)

# =============================================================================
# Per-Industry: Review (latest report)
# =============================================================================

review-ecommerce:
	cd backend && python -m src.cli.review_report --industry ecommerce $(ARGS)

review-dental:
	cd backend && python -m src.cli.review_report --industry dental $(ARGS)

review-professional-services:
	cd backend && python -m src.cli.review_report --industry professional-services $(ARGS)

review-b2b-platforms:
	cd backend && python -m src.cli.review_report --industry b2b-platforms $(ARGS)

# Review any industry (generic)
review-report:
	cd backend && python -m src.cli.review_report $(ARGS)

# Browser automation
playwright-install:
	cd backend && playwright install chromium

playwright-cli-install:
	pnpm add -g @playwright/cli@latest
	playwright-cli install

# UI testing (Bowser QA agent via /ui-test command)
ui-test:
	@echo "Run: /ui-test in Claude Code to execute Bowser QA agent tests"
	@echo "Stories: tests/ui/stories/*.yaml"
	@echo "Screenshots: screenshots/bowser-qa/"

ui-test-headed:
	@echo "Run: /ui-test --headed in Claude Code"

# Enhanced report generation
generate-report-playwright:
	cd backend && python -m src.cli.generate_report --playwright $(ARGS)

# Vendor research
research-vendor:
	@echo "Use /research-vendor in Claude Code"
	@echo "Category: $(CATEGORY), Industry: $(INDUSTRY)"

# Full test suite (including UI)
test-all: test ui-test

# =============================================================================
# Data Intelligence Pipeline
# =============================================================================

# Full refresh: vendors + KB audit + expertise health
data-refresh:
	cd backend && python -m src.cli.auto_refresh all $(ARGS)

# Refresh stale vendors (auto-approve non-significant changes)
vendor-refresh:
	cd backend && python -m src.cli.auto_refresh vendors --auto-approve $(ARGS)

# Audit knowledge base freshness
kb-audit:
	cd backend && python -m src.cli.auto_refresh kb-audit $(ARGS)

# Check expertise store health
expertise-health:
	cd backend && python -m src.cli.auto_refresh expertise-health $(ARGS)

# Vendor discovery (find new vendors for a category)
vendor-discover:
	cd backend && python -m src.agents.research.cli discover --category $(CATEGORY) $(ARGS)

# Database hygiene audit
db-audit:
	cd backend && python -m src.cli.db_audit $(ARGS)

# Database audit + fix invalid data
db-audit-fix:
	cd backend && python -m src.cli.db_audit --fix $(ARGS)

# Schema/migration drift guardrail
migration-drift-check:
	cd backend && python -m src.scripts.check_migration_drift

artifact-denylist-check:
	python backend/src/scripts/check_tracked_artifacts.py

# Full data pipeline (JSON output for cron)
data-refresh-cron:
	cd backend && python -m src.cli.auto_refresh all --auto-approve --output json && python -m src.cli.db_audit --output json
