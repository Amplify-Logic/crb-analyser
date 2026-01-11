# API Development Reference

> Load this when working on backend routes, services, or API endpoints.

---

## Route Structure

```
backend/src/routes/
├── quiz.py           # Quiz flow (main conversion path)
├── interview.py      # Voice interview
├── workshop.py       # 90-minute workshop
├── reports.py        # Report generation/retrieval
├── payments.py       # Stripe integration
├── vendors.py        # Vendor database
├── admin_*.py        # Admin endpoints
└── health.py         # Health checks
```

## Creating a New Route

1. Create file: `backend/src/routes/<name>.py`
2. Define Pydantic models for request/response
3. Add auth: `current_user = Depends(get_current_user)`
4. Register in `main.py`: `app.include_router(router, prefix="/api/<name>")`
5. Add tests: `backend/tests/test_<name>.py`

## Response Patterns

```python
# Success
{"data": {...}, "message": "optional"}

# Error
{"error": {"code": "VENDOR_NOT_FOUND", "message": "...", "status": 404}}
```

## Error Handling

```python
from src.config.errors import CRBError

class CRBError(Exception):
    def __init__(self, message: str, code: str, status: int = 500):
        self.message = message
        self.code = code  # e.g., "VENDOR_NOT_FOUND"
        self.status = status

# In routes - catch specific errors, not bare Exception
@router.get("/vendors/{slug}")
async def get_vendor(slug: str):
    vendor = await vendor_service.get(slug)
    if not vendor:
        raise CRBError("Vendor not found", "VENDOR_NOT_FOUND", 404)
    return {"data": vendor}
```

## Auth Dependency

```python
@router.get("/audits")
async def list_audits(
    current_user: CurrentUser = Depends(get_current_user),
    supabase: AsyncClient = Depends(get_async_supabase)
):
    # current_user.workspace_id for multi-tenant isolation
    ...
```

## SSE Streaming (Long Operations)

```python
@router.get("/audits/{id}/progress")
async def stream_progress(id: str):
    async def generate():
        async for update in agent.run_analysis(id):
            yield f"data: {json.dumps(update)}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

## Validation Rules

- Pydantic validation on ALL inputs
- No raw SQL without parameterization
- Rate limit all endpoints
- Never log secrets or PII
- No raw errors to users in production

## Key Services

| Service | File | Purpose |
|---------|------|---------|
| Reports | `services/report_service.py` | Report generation |
| Quiz | `services/quiz_engine.py` | Adaptive question selection |
| Vendors | `services/vendor_service.py` | Vendor CRUD + caching |
| Teaser | `services/teaser_service.py` | Pre-payment preview |

## Logging

```python
import structlog
logger = structlog.get_logger()

# Always include context
logger.info("analysis_started", audit_id=audit_id, industry=industry)
logger.error("vendor_fetch_failed", vendor_id=vendor_id, error=str(e))
```

## Anti-Patterns

- Catching bare `Exception` - catch specific errors
- Business logic in route handlers - use services
- Direct Supabase calls outside repository layer
- Circular imports between modules
- `# type: ignore` without explanation comment
