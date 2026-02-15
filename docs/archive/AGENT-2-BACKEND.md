# AGENT 2: Backend & API

> **Mission:** Build a robust, scalable API layer that powers instant quiz saves, real-time report generation, and vendor data freshness.

---

## Context

**Product:** CRB Analyser - AI-powered Cost/Risk/Benefit analysis
**Price Point:** €147 (one-time)
**Stack:** FastAPI + Python 3.12 + Supabase + Redis
**Port:** 8383 (avoid conflict with other services)

---

## Current State

```
backend/
├── src/
│   ├── main.py                    # FastAPI app
│   ├── config/
│   │   ├── settings.py            # Environment config
│   │   └── supabase_client.py     # DB client
│   ├── middleware/
│   │   └── auth.py                # JWT validation
│   ├── routes/
│   │   ├── quiz_routes.py         # Quiz sessions
│   │   ├── report_routes.py       # Report CRUD
│   │   ├── payment_routes.py      # Stripe
│   │   └── health_routes.py       # Health check
│   ├── services/
│   │   └── report_service.py      # Report generation (AI)
│   └── knowledge/                 # Industry data (JSON)
```

**What Works:**
- Quiz session creation and storage
- Report generation via Claude API
- Basic Stripe checkout flow
- Public report endpoint
- Supabase integration

**What Needs Work:**
- No SSE streaming for generation progress
- Quiz save/resume not implemented
- Vendor database needs auto-refresh capability
- No caching layer (Redis not utilized)
- Rate limiting not enforced
- No background job system for vendor updates

---

## Target State

### 1. API Endpoint Structure

```
/api
├── /health
│   └── GET /                    # Health check
│
├── /quiz
│   ├── POST /sessions           # Create new quiz session
│   ├── GET /sessions/:id        # Get session with progress
│   ├── PATCH /sessions/:id      # Save progress (partial update)
│   ├── POST /sessions/:id/complete  # Mark complete, trigger report
│   └── GET /questions/:industry     # Get industry-specific questions
│
├── /reports
│   ├── GET /public/:id          # Public report view (no auth)
│   ├── GET /:id/stream          # SSE stream for generation progress
│   ├── GET /:id/pdf             # Generate/download PDF
│   └── POST /:id/regenerate     # Regenerate with same inputs
│
├── /vendors
│   ├── GET /                    # List vendors (paginated, filterable)
│   ├── GET /:slug               # Single vendor detail
│   ├── GET /categories          # List categories
│   ├── POST /compare            # Compare multiple vendors
│   └── POST /refresh/:slug      # Trigger price refresh (admin)
│
├── /benchmarks
│   ├── GET /:industry           # Industry benchmarks
│   └── GET /:industry/:metric   # Specific metric
│
├── /payments
│   ├── POST /create-checkout    # Stripe checkout session
│   ├── POST /webhook            # Stripe webhook
│   └── GET /verify/:session_id  # Verify payment status
│
└── /admin (protected)
    ├── POST /vendors/refresh-all    # Refresh all vendor pricing
    ├── GET /reports/stats           # Report generation stats
    └── GET /cache/stats             # Cache hit rates
```

### 2. Quiz Save/Resume System

**Database Schema:**
```sql
-- Quiz sessions with progress tracking
CREATE TABLE quiz_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    tier TEXT NOT NULL CHECK (tier IN ('quick', 'full')),

    -- Progress tracking
    current_section INTEGER DEFAULT 0,
    current_question INTEGER DEFAULT 0,
    answers JSONB NOT NULL DEFAULT '{}',

    -- Computed fields
    completion_percent INTEGER GENERATED ALWAYS AS (
        CASE
            WHEN jsonb_array_length(answers->'completed_sections') >= 5 THEN 100
            ELSE (jsonb_array_length(answers->'completed_sections') * 20)
        END
    ) STORED,

    -- Status
    status TEXT NOT NULL DEFAULT 'in_progress'
        CHECK (status IN ('in_progress', 'completed', 'paid', 'generating', 'delivered')),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    -- Payment
    stripe_session_id TEXT,
    amount_paid DECIMAL(10, 2),

    -- Report link
    report_id UUID REFERENCES reports(id)
);

-- Index for resume by email
CREATE INDEX idx_quiz_sessions_email ON quiz_sessions(email, status);
```

**Save Progress Endpoint:**
```python
@router.patch("/sessions/{session_id}")
async def save_quiz_progress(
    session_id: str,
    progress: QuizProgressUpdate,
    supabase: AsyncClient = Depends(get_supabase)
):
    """
    Save partial quiz progress. Called on every answer.

    Body:
    {
        "current_section": 2,
        "current_question": 3,
        "answers": {
            "industry": "tech_saas",
            "company_size": "20-50",
            ...
        }
    }
    """
    result = await supabase.table("quiz_sessions").update({
        "current_section": progress.current_section,
        "current_question": progress.current_question,
        "answers": progress.answers,
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", session_id).execute()

    return {"success": True, "completion_percent": calculate_completion(progress)}
```

**Resume Flow:**
```python
@router.get("/sessions/resume")
async def resume_quiz(
    email: str,
    supabase: AsyncClient = Depends(get_supabase)
):
    """
    Find in-progress quiz for email to allow resume.
    """
    result = await supabase.table("quiz_sessions")\
        .select("*")\
        .eq("email", email)\
        .eq("status", "in_progress")\
        .order("updated_at", desc=True)\
        .limit(1)\
        .execute()

    if result.data:
        return {"has_progress": True, "session": result.data[0]}
    return {"has_progress": False}
```

### 3. SSE Streaming for Report Generation

**Endpoint:**
```python
@router.get("/reports/{report_id}/stream")
async def stream_report_generation(
    report_id: str,
    supabase: AsyncClient = Depends(get_supabase)
):
    """
    Server-Sent Events stream for report generation progress.

    Events:
    - progress: {step: "analyzing", percent: 25, message: "Analyzing responses..."}
    - finding: {id: "...", title: "...", preview: "..."}
    - recommendation: {id: "...", title: "..."}
    - complete: {report_id: "...", status: "completed"}
    - error: {message: "...", recoverable: true}
    """
    async def event_generator():
        # Subscribe to report progress channel
        async for event in report_service.generate_with_progress(report_id):
            yield f"event: {event['type']}\n"
            yield f"data: {json.dumps(event['data'])}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
```

**Progress Events Structure:**
```python
GENERATION_STEPS = [
    {"step": "parsing", "percent": 10, "message": "Analyzing your responses..."},
    {"step": "benchmarks", "percent": 20, "message": "Researching industry benchmarks..."},
    {"step": "opportunities", "percent": 35, "message": "Identifying AI opportunities..."},
    {"step": "vendors", "percent": 50, "message": "Researching vendor solutions..."},
    {"step": "roi", "percent": 65, "message": "Calculating ROI projections..."},
    {"step": "recommendations", "percent": 80, "message": "Generating recommendations..."},
    {"step": "roadmap", "percent": 90, "message": "Building your roadmap..."},
    {"step": "finalizing", "percent": 95, "message": "Finalizing report..."},
    {"step": "complete", "percent": 100, "message": "Report ready!"}
]
```

### 4. Vendor Database with Auto-Refresh

**Schema:**
```sql
CREATE TABLE vendors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT,

    -- Pricing (JSONB for flexibility)
    pricing JSONB NOT NULL DEFAULT '{}'::jsonb,
    /*
    {
        "model": "per_seat",
        "currency": "USD",
        "tiers": [
            {"name": "Free", "price": 0, "limits": "1000 contacts"},
            {"name": "Starter", "price": 20, "per": "user/month", "features": [...]},
            {"name": "Pro", "price": 100, "per": "user/month", "features": [...]}
        ],
        "custom_pricing": true,
        "free_trial_days": 14
    }
    */

    -- Metadata
    website TEXT,
    description TEXT,
    logo_url TEXT,

    -- Use case matching
    best_for JSONB DEFAULT '[]',      -- ["small_teams", "agencies", "ecommerce"]
    industries JSONB DEFAULT '[]',     -- ["tech", "retail", "services"]
    avoid_if JSONB DEFAULT '[]',       -- ["enterprise", "complex_workflows"]

    -- Implementation
    avg_implementation_weeks INTEGER,
    implementation_cost_range JSONB,   -- {"min": 1000, "max": 5000}
    requires_developer BOOLEAN DEFAULT false,

    -- Ratings
    g2_rating DECIMAL(2,1),
    g2_reviews INTEGER,
    capterra_rating DECIMAL(2,1),
    our_rating DECIMAL(2,1),

    -- Integrations
    integrations JSONB DEFAULT '[]',
    api_available BOOLEAN DEFAULT true,

    -- Freshness
    pricing_verified_at TIMESTAMPTZ,
    pricing_source TEXT,              -- URL where pricing was found
    auto_refresh_enabled BOOLEAN DEFAULT true,
    last_refresh_attempt TIMESTAMPTZ,
    refresh_error TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Pricing history for tracking changes
CREATE TABLE vendor_pricing_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id UUID REFERENCES vendors(id),
    pricing JSONB NOT NULL,
    captured_at TIMESTAMPTZ DEFAULT NOW(),
    source TEXT
);

CREATE INDEX idx_vendors_category ON vendors(category);
CREATE INDEX idx_vendors_pricing_age ON vendors(pricing_verified_at);
```

**Auto-Refresh Service:**
```python
# backend/src/services/vendor_refresh_service.py

class VendorRefreshService:
    """
    Automatically refresh vendor pricing from their websites.
    Uses web scraping + AI extraction.
    """

    async def refresh_vendor(self, vendor_slug: str) -> RefreshResult:
        """
        Refresh pricing for a single vendor.

        1. Fetch pricing page
        2. Extract pricing with Claude
        3. Compare with current
        4. Update if changed
        5. Log history
        """
        vendor = await self.get_vendor(vendor_slug)

        # Fetch pricing page
        html = await self.fetch_page(vendor.pricing_source)

        # Extract with AI
        extracted = await self.extract_pricing_with_ai(html, vendor.name)

        # Compare and update
        if self.pricing_changed(vendor.pricing, extracted):
            await self.update_vendor_pricing(vendor.id, extracted)
            await self.log_pricing_history(vendor.id, extracted)
            return RefreshResult(changed=True, old=vendor.pricing, new=extracted)

        return RefreshResult(changed=False)

    async def extract_pricing_with_ai(self, html: str, vendor_name: str) -> dict:
        """Use Claude to extract structured pricing from HTML."""
        response = await anthropic.messages.create(
            model="claude-3-5-haiku-20241022",  # Fast + cheap for extraction
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"""Extract pricing information from this {vendor_name} pricing page.

Return JSON:
{{
    "model": "per_seat|flat|usage|custom",
    "currency": "USD|EUR|GBP",
    "tiers": [
        {{"name": "...", "price": 0, "per": "month|year|user/month", "features": [...]}}
    ],
    "free_trial_days": null|14|30,
    "custom_pricing": true|false
}}

HTML:
{html[:10000]}"""  # Truncate for token limits
            }]
        )
        return json.loads(response.content[0].text)

    async def refresh_all_vendors(self):
        """Background job to refresh all vendors."""
        vendors = await self.get_vendors_needing_refresh(
            older_than_days=7,
            limit=50
        )

        results = []
        for vendor in vendors:
            try:
                result = await self.refresh_vendor(vendor.slug)
                results.append({"vendor": vendor.slug, "success": True, **result})
            except Exception as e:
                results.append({"vendor": vendor.slug, "success": False, "error": str(e)})
                await self.mark_refresh_error(vendor.id, str(e))

        return results
```

### 5. Caching Layer (Redis)

```python
# backend/src/services/cache_service.py

class CacheService:
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)

    # Cache keys
    VENDOR_KEY = "vendor:{slug}"
    VENDOR_LIST_KEY = "vendors:list:{category}"
    BENCHMARK_KEY = "benchmark:{industry}:{size}"
    REPORT_KEY = "report:{id}"

    # TTLs
    VENDOR_TTL = 3600 * 24  # 24 hours
    BENCHMARK_TTL = 3600 * 24 * 7  # 7 days
    REPORT_TTL = 3600  # 1 hour

    async def get_vendor(self, slug: str) -> dict | None:
        cached = await self.redis.get(self.VENDOR_KEY.format(slug=slug))
        if cached:
            return json.loads(cached)
        return None

    async def set_vendor(self, slug: str, data: dict):
        await self.redis.setex(
            self.VENDOR_KEY.format(slug=slug),
            self.VENDOR_TTL,
            json.dumps(data)
        )

    async def invalidate_vendor(self, slug: str):
        """Called when vendor pricing is refreshed."""
        await self.redis.delete(self.VENDOR_KEY.format(slug=slug))
        # Also invalidate list caches
        keys = await self.redis.keys("vendors:list:*")
        if keys:
            await self.redis.delete(*keys)
```

### 6. Rate Limiting

```python
# backend/src/middleware/rate_limit.py

from fastapi import Request, HTTPException
from redis import asyncio as aioredis

class RateLimiter:
    def __init__(self, redis: aioredis.Redis):
        self.redis = redis

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> bool:
        """
        Sliding window rate limiting.
        Returns True if request allowed, raises HTTPException if limited.
        """
        current = await self.redis.incr(key)

        if current == 1:
            await self.redis.expire(key, window_seconds)

        if current > limit:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limited",
                    "message": f"Too many requests. Limit: {limit} per {window_seconds}s",
                    "retry_after": await self.redis.ttl(key)
                }
            )

        return True

# Usage in routes
RATE_LIMITS = {
    "quiz_create": (10, 3600),      # 10 per hour
    "report_generate": (5, 3600),    # 5 per hour
    "vendor_refresh": (100, 86400),  # 100 per day (admin)
}
```

---

## Specific Tasks

### Phase 1: Core Fixes
- [ ] Fix any existing route errors
- [ ] Ensure Supabase connection is stable
- [ ] Add proper error handling middleware
- [ ] Set up request logging

### Phase 2: Quiz System
- [ ] Implement quiz progress save endpoint
- [ ] Implement quiz resume by email
- [ ] Add industry-specific question branching
- [ ] Test save/resume flow end-to-end

### Phase 3: SSE Streaming
- [ ] Create report generation SSE endpoint
- [ ] Integrate progress events into report_service
- [ ] Test with frontend EventSource
- [ ] Handle disconnection/reconnection

### Phase 4: Vendor System
- [ ] Create vendors table with full schema
- [ ] Build vendor CRUD endpoints
- [ ] Implement vendor comparison endpoint
- [ ] Create pricing extraction service (AI)
- [ ] Build auto-refresh background job
- [ ] Add pricing history tracking

### Phase 5: Caching
- [ ] Set up Redis connection
- [ ] Implement cache service
- [ ] Add caching to vendor endpoints
- [ ] Add caching to benchmark endpoints
- [ ] Monitor cache hit rates

### Phase 6: Rate Limiting & Security
- [ ] Implement rate limiter middleware
- [ ] Apply limits to all public endpoints
- [ ] Add request validation
- [ ] Security headers

---

## Dependencies

**Needs from Agent 3 (AI Engine):**
- Report generation function that yields progress events
- Pricing extraction prompt templates

**Needs from Agent 4 (Data):**
- Initial vendor data to seed database
- Industry benchmark data

**Needs from Agent 5 (Integrations):**
- Stripe webhook handling integration
- Email triggers on report completion

---

## Deliverables

1. Complete API with all endpoints documented
2. Quiz save/resume system working
3. SSE streaming for report generation
4. Vendor database with auto-refresh
5. Redis caching layer
6. Rate limiting middleware
7. OpenAPI documentation (`/docs`)

---

## Quality Criteria

- [ ] All endpoints return consistent response format
- [ ] Errors include helpful messages
- [ ] 95%+ uptime capability
- [ ] Response times < 200ms for cached data
- [ ] No N+1 query issues
- [ ] All sensitive data validated

---

## Tech Stack Reference

```
FastAPI 0.109+
Python 3.12
Supabase (PostgreSQL)
Redis for caching
httpx for async HTTP
Pydantic for validation
```

---

## File Locations

```
backend/src/
├── main.py
├── config/
│   ├── settings.py
│   ├── supabase_client.py
│   └── redis_client.py (new)
├── middleware/
│   ├── auth.py
│   ├── error_handler.py
│   └── rate_limit.py (new)
├── routes/
│   ├── quiz_routes.py (enhance)
│   ├── report_routes.py (enhance)
│   ├── vendor_routes.py (new)
│   ├── benchmark_routes.py (new)
│   └── admin_routes.py (new)
├── services/
│   ├── report_service.py (enhance)
│   ├── vendor_service.py (new)
│   ├── vendor_refresh_service.py (new)
│   ├── cache_service.py (new)
│   └── benchmark_service.py (new)
└── models/
    ├── quiz.py
    ├── report.py
    └── vendor.py (new)
```
