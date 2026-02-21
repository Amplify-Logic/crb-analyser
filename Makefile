.PHONY: test test-backend test-frontend lint typecheck dev generate-report ui-test ui-test-headed playwright-install generate-report-playwright research-vendor test-all

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

# Browser automation
playwright-install:
	cd backend && playwright install chromium

# UI testing
ui-test:
	@echo "Run: /ui-test in Claude Code to execute agentic UI tests"
	@echo "Or manually: cd backend && python -m pytest tests/ui/ -v"

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
