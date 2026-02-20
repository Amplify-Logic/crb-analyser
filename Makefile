.PHONY: test test-backend test-frontend lint typecheck dev generate-report

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
