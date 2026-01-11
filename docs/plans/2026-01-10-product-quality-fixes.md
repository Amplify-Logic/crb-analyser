# CRB Analyser - Product Quality Fix Plan

> **Execute with:** `/execute docs/plans/2026-01-10-product-quality-fixes.md`
> **Total Issues:** 15 Critical, 25 Major, 40+ Minor
> **Estimated Effort:** 2-3 weeks full implementation

---

## Context

A comprehensive product quality audit identified critical security vulnerabilities, reliability gaps, and UX issues. This plan provides exact locations and fixes for all issues, prioritized by business impact.

**Tech Stack:** FastAPI + Python 3.12 (backend), React 18 + Vite + TypeScript (frontend), Supabase, Redis, Stripe, Claude API

---

## Phase 1: Critical Security Fixes (P0 - Do First)

### 1.1 Add Payment Verification to Public Report Endpoint

**File:** `backend/src/routes/reports.py`
**Lines:** 70-121
**Issue:** `/public/{report_id}` endpoint has NO authentication and NO payment verification. Anyone with a report_id can access full report data.

**Fix:**
```python
# In get_public_report function, add after fetching report:
@router.get("/public/{report_id}")
async def get_public_report(report_id: str):
    # ... existing report fetch logic ...

    # ADD THIS: Verify payment status
    if report_data:
        quiz_session_id = report_data.get("quiz_session_id")
        if quiz_session_id:
            session_result = supabase.table("quiz_sessions").select("status").eq("id", quiz_session_id).single().execute()
            if session_result.data:
                status = session_result.data.get("status")
                if status not in ["paid", "completed"]:
                    raise HTTPException(status_code=402, detail="Payment required to access this report")
```

**Verification:** `curl http://localhost:8383/api/reports/public/{unpaid-report-id}` should return 402

---

### 1.2 Add Authentication to Admin Research Routes

**File:** `backend/src/routes/admin_research.py`
**Lines:** 78-187
**Issue:** All endpoints (`/stale-count`, `/refresh`, `/discover`, `/apply-updates`, `/apply-discoveries`) have NO authentication.

**Fix:** Add `Depends(require_admin)` to all route handlers:

```python
from src.middleware.auth import require_admin

@router.get("/stale-count")
async def get_stale_vendor_count(current_user = Depends(require_admin)):
    # ... existing logic ...

@router.post("/refresh")
async def refresh_stale_vendors(current_user = Depends(require_admin)):
    # ... existing logic ...

@router.post("/discover")
async def discover_new_vendors(request: DiscoverRequest, current_user = Depends(require_admin)):
    # ... existing logic ...

@router.post("/apply-updates")
async def apply_vendor_updates(request: ApplyUpdatesRequest, current_user = Depends(require_admin)):
    # ... existing logic ...

@router.post("/apply-discoveries")
async def apply_vendor_discoveries(request: ApplyDiscoveriesRequest, current_user = Depends(require_admin)):
    # ... existing logic ...
```

---

### 1.3 Add Authentication to Admin QA Routes

**File:** `backend/src/routes/admin_qa.py`
**Lines:** 62-440
**Issue:** QA review system has NO authentication. Anyone can view customer PII, approve/reject reports.

**Fix:** Add `Depends(require_admin)` to ALL route handlers in this file:

```python
from src.middleware.auth import require_admin

# Apply to: /queue, /report/{id}, /review, /stats, /regenerate
# Example:
@router.get("/queue")
async def get_qa_queue(current_user = Depends(require_admin)):
    # ... existing logic ...
```

---

### 1.4 Fix Prompt Injection in Interview Skills

**File:** `backend/src/skills/interview/acknowledgment_generator.py`
**Lines:** 109-121
**Issue:** User answers directly interpolated into prompts without sanitization.

**Fix:** Create sanitization utility and apply:

```python
# Create new file: backend/src/utils/prompt_safety.py
import re

def sanitize_user_input(text: str) -> str:
    """Sanitize user input before including in LLM prompts."""
    if not text:
        return ""

    # Remove potential injection patterns
    dangerous_patterns = [
        r'ignore\s+(all\s+)?previous\s+instructions',
        r'ignore\s+(all\s+)?above',
        r'disregard\s+(all\s+)?previous',
        r'forget\s+(all\s+)?previous',
        r'system\s*prompt',
        r'you\s+are\s+now',
        r'new\s+instructions',
        r'</?(system|user|assistant)>',
    ]

    sanitized = text
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '[FILTERED]', sanitized, flags=re.IGNORECASE)

    # Escape XML-like tags
    sanitized = re.sub(r'<([^>]+)>', r'&lt;\1&gt;', sanitized)

    # Limit length to prevent context stuffing
    max_length = 5000
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "...[truncated]"

    return sanitized
```

**Apply to:**
- `backend/src/skills/interview/acknowledgment_generator.py:109-121`
- `backend/src/skills/interview/followup.py:232-235`
- Any other skill that interpolates user input

```python
from src.utils.prompt_safety import sanitize_user_input

# Before interpolating user content:
safe_answer = sanitize_user_input(user_answer)
prompt = f"...{safe_answer}..."
```

---

### 1.5 Fix XSS via dangerouslySetInnerHTML

**Files:**
- `frontend/src/pages/Interview.tsx:485-488`
- `frontend/src/components/voice/VoiceQuizInterview.tsx:748`
- `frontend/src/components/WorkshopDeepDive.tsx:297`

**Issue:** AI-generated content rendered without sanitization.

**Fix:** Install DOMPurify and sanitize all dangerouslySetInnerHTML usage:

```bash
cd frontend && npm install dompurify @types/dompurify
```

```typescript
// Create: frontend/src/utils/sanitize.ts
import DOMPurify from 'dompurify';

export function sanitizeHtml(dirty: string): string {
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li'],
    ALLOWED_ATTR: []
  });
}
```

```typescript
// In each file with dangerouslySetInnerHTML:
import { sanitizeHtml } from '@/utils/sanitize';

// Replace:
<div dangerouslySetInnerHTML={{ __html: content }} />

// With:
<div dangerouslySetInnerHTML={{ __html: sanitizeHtml(content) }} />
```

---

### 1.6 Remove Dev Bypass from Production Checkout

**File:** `frontend/src/pages/Checkout.tsx`
**Lines:** 60-68

**Issue:** `?dev=bypass` query parameter allows skipping payment. Logic runs before DEV check.

**Fix:** Remove or properly gate the bypass:

```typescript
// REMOVE this entire block or wrap properly:
// Lines 60-68 - DELETE or change to:
if (import.meta.env.DEV && searchParams.get('dev') === 'bypass') {
  // Only in development
  console.log('Dev bypass enabled');
  // ... bypass logic
}

// Also remove console.log at lines 63-64
```

---

## Phase 2: Critical Path Fixes (P0)

### 2.1 Move Report Generation to Background Task

**File:** `backend/src/routes/payments.py`
**Lines:** 557-559
**Issue:** `generate_report_for_quiz()` called synchronously in webhook handler. Causes Stripe webhook timeout (>10s).

**Fix:** Use FastAPI BackgroundTasks:

```python
from fastapi import BackgroundTasks

@router.post("/webhook")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks):
    # ... existing webhook validation ...

    # In handle_guest_checkout_completed, replace:
    # report_id = await generate_report_for_quiz(quiz_session_id, tier)

    # With:
    background_tasks.add_task(generate_report_for_quiz, quiz_session_id, tier)

    # Update quiz session status to "generating" immediately
    supabase.table("quiz_sessions").update({"status": "generating"}).eq("id", quiz_session_id).execute()

    # Return success to Stripe immediately
    return {"status": "processing"}
```

**Also update:** The SSE endpoint at `reports.py:155` to poll for report completion.

---

### 2.2 Add Redis Lock for Report Generation

**File:** `backend/src/routes/reports.py`
**Lines:** 155-191
**Issue:** No mutex/lock. Multiple tabs = multiple report generations.

**Fix:**

```python
import redis
from src.config.settings import settings

redis_client = redis.from_url(settings.REDIS_URL)

@router.get("/stream/{quiz_session_id}")
async def stream_report_generation(quiz_session_id: str):
    lock_key = f"report_generation:{quiz_session_id}"

    # Try to acquire lock (expires in 5 minutes)
    lock_acquired = redis_client.set(lock_key, "1", nx=True, ex=300)

    if not lock_acquired:
        # Another generation in progress, just stream status
        return StreamingResponse(
            poll_existing_generation(quiz_session_id),
            media_type="text/event-stream"
        )

    try:
        # ... existing generation logic ...
    finally:
        redis_client.delete(lock_key)
```

---

### 2.3 Add Session Expiry Mechanism

**File:** `backend/src/routes/quiz.py`
**Issue:** Quiz sessions never expire. Stale data accumulates.

**Fix:** Add expiry check and background cleanup:

```python
from datetime import datetime, timedelta

async def check_session_expiry(session_id: str) -> bool:
    """Check if session is expired."""
    result = supabase.table("quiz_sessions").select("created_at, status").eq("id", session_id).single().execute()

    if not result.data:
        return True

    created_at = datetime.fromisoformat(result.data["created_at"].replace("Z", "+00:00"))
    status = result.data["status"]

    # Expire pending_payment after 24 hours
    if status == "pending_payment" and datetime.now(created_at.tzinfo) - created_at > timedelta(hours=24):
        supabase.table("quiz_sessions").update({"status": "expired"}).eq("id", session_id).execute()
        return True

    # Expire in_progress after 7 days
    if status == "in_progress" and datetime.now(created_at.tzinfo) - created_at > timedelta(days=7):
        supabase.table("quiz_sessions").update({"status": "expired"}).eq("id", session_id).execute()
        return True

    return False
```

---

## Phase 3: Reliability Fixes (P1)

### 3.1 Add Retry Logic to Supabase Client

**File:** `backend/src/config/supabase_client.py`
**Lines:** 39-51
**Issue:** No retry logic. Any Supabase issue crashes all endpoints.

**Fix:**

```python
import time
from functools import wraps

def with_retry(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for Supabase operations with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Supabase operation failed, retrying in {delay}s", error=str(e))
                        await asyncio.sleep(delay)
            raise last_exception
        return wrapper
    return decorator

# Apply to critical operations
```

---

### 3.2 Add Model Fallback Chain

**File:** `backend/src/config/model_routing.py`
**Lines:** 273-294
**Issue:** No fallback when preferred model unavailable.

**Fix:**

```python
MODEL_FALLBACK_CHAIN = {
    "claude-opus-4-5-20251101": ["claude-sonnet-4-5-20250929", "claude-haiku-4-5-20251001"],
    "claude-sonnet-4-5-20250929": ["claude-haiku-4-5-20251001"],
    "claude-haiku-4-5-20251001": [],
}

async def get_model_with_fallback(task: str, tier: str = "quick") -> str:
    """Get model for task with automatic fallback on failure."""
    primary_model = get_model_for_task(task, tier)

    async def try_model(model: str):
        try:
            # Quick health check
            response = await anthropic_client.messages.create(
                model=model,
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}]
            )
            return model
        except Exception:
            return None

    # Try primary
    if await try_model(primary_model):
        return primary_model

    # Try fallbacks
    for fallback in MODEL_FALLBACK_CHAIN.get(primary_model, []):
        if await try_model(fallback):
            logger.warning(f"Using fallback model {fallback} instead of {primary_model}")
            return fallback

    raise RuntimeError(f"No available models for task {task}")
```

---

### 3.3 Move Quiz State to Redis

**File:** `backend/src/routes/quiz.py`
**Line:** 1804
**Issue:** `_active_generators` in memory. Lost on restart, breaks with multiple workers.

**Fix:**

```python
# Replace in-memory dict with Redis
import json

class RedisQuizStateStore:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.prefix = "quiz_generator:"
        self.ttl = 3600  # 1 hour

    async def get(self, session_id: str) -> Optional[dict]:
        data = self.redis.get(f"{self.prefix}{session_id}")
        return json.loads(data) if data else None

    async def set(self, session_id: str, state: dict):
        self.redis.setex(
            f"{self.prefix}{session_id}",
            self.ttl,
            json.dumps(state)
        )

    async def delete(self, session_id: str):
        self.redis.delete(f"{self.prefix}{session_id}")

# Replace: _active_generators: Dict[str, QuestionGenerator] = {}
# With: quiz_state_store = RedisQuizStateStore(redis_client)
```

---

### 3.4 Wrap Account Creation in Transaction

**File:** `backend/src/routes/payments.py`
**Lines:** 61-151
**Issue:** Sequential operations without transaction. Partial failures leave orphaned records.

**Fix:**

```python
async def create_user_from_quiz_session(quiz_session_id: str, email: str, tier: str) -> dict:
    """Create user account with transaction-like rollback on failure."""
    created_resources = []

    try:
        # Create user
        user = await create_auth_user(email)
        created_resources.append(("auth_user", user.id))

        # Create workspace
        workspace = await create_workspace(user.id)
        created_resources.append(("workspace", workspace["id"]))

        # Create client
        client = await create_client(workspace["id"])
        created_resources.append(("client", client["id"]))

        # ... rest of creation logic ...

        return {"user_id": user.id, "workspace_id": workspace["id"]}

    except Exception as e:
        # Rollback in reverse order
        for resource_type, resource_id in reversed(created_resources):
            try:
                await rollback_resource(resource_type, resource_id)
            except Exception as rollback_error:
                logger.error(f"Failed to rollback {resource_type}:{resource_id}", error=str(rollback_error))
        raise
```

---

## Phase 4: Frontend UX Fixes (P1)

### 4.1 Add Keyboard Accessibility to Recommendations

**File:** `frontend/src/components/report/NumberedRecommendations.tsx`
**Lines:** 48-50
**Issue:** Cards use onClick on div without keyboard support.

**Fix:**

```typescript
// Replace the clickable div with proper button semantics:
<div
  role="button"
  tabIndex={0}
  onClick={() => toggleExpand(index)}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      toggleExpand(index);
    }
  }}
  aria-expanded={expanded}
  aria-controls={`recommendation-content-${index}`}
  className="cursor-pointer ..."
>
```

---

### 4.2 Add aria-labels to Checkout

**File:** `frontend/src/pages/Checkout.tsx`
**Lines:** 269-294

**Fix:**

```typescript
<button
  onClick={handleCheckout}
  disabled={isLoading}
  aria-label={`Complete purchase for ${formatPrice(selectedTier.price)}`}
  aria-busy={isLoading}
  className="..."
>
  {isLoading ? 'Processing...' : `Pay ${formatPrice(selectedTier.price)}`}
</button>
```

---

### 4.3 Add Focus Trap to Modal Dialogs

**File:** `frontend/src/pages/Workshop.tsx`
**Lines:** 418-448

**Fix:** Install and use focus-trap-react:

```bash
cd frontend && npm install focus-trap-react
```

```typescript
import FocusTrap from 'focus-trap-react';

// Wrap modal content:
{showModal && (
  <FocusTrap>
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div className="modal-content">
        <h2 id="modal-title">Upload Audio</h2>
        {/* ... modal content ... */}
        <button onClick={closeModal}>Close</button>
      </div>
    </div>
  </FocusTrap>
)}
```

---

### 4.4 Add Browser Support Check for Voice Recording

**File:** `frontend/src/components/voice/VoiceRecorder.tsx`
**Lines:** 87-153

**Fix:**

```typescript
const [browserSupported, setBrowserSupported] = useState(true);

useEffect(() => {
  // Check for getUserMedia support
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    setBrowserSupported(false);
    return;
  }
}, []);

if (!browserSupported) {
  return (
    <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
      <p className="text-yellow-800">
        Voice recording is not supported in your browser.
        Please use Chrome, Firefox, or Safari 14.5+ for the best experience.
      </p>
    </div>
  );
}
```

---

### 4.5 Add Form Validation on Blur

**File:** `frontend/src/pages/Checkout.tsx`
**Lines:** 96-104

**Fix:**

```typescript
const [emailError, setEmailError] = useState<string | null>(null);

const validateEmail = (email: string) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!email) {
    setEmailError('Email is required');
    return false;
  }
  if (!emailRegex.test(email)) {
    setEmailError('Please enter a valid email address');
    return false;
  }
  setEmailError(null);
  return true;
};

// In the input:
<input
  type="email"
  value={email}
  onChange={(e) => setEmail(e.target.value)}
  onBlur={(e) => validateEmail(e.target.value)}
  aria-invalid={!!emailError}
  aria-describedby={emailError ? "email-error" : undefined}
/>
{emailError && (
  <p id="email-error" className="text-red-500 text-sm mt-1">{emailError}</p>
)}
```

---

## Phase 5: Testing Infrastructure (P1)

### 5.1 Set Up Frontend Test Infrastructure

```bash
cd frontend
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

**Create:** `frontend/vitest.config.ts`
```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
  },
});
```

**Create:** `frontend/src/test/setup.ts`
```typescript
import '@testing-library/jest-dom';
```

**Update:** `frontend/package.json`
```json
{
  "scripts": {
    "test": "vitest",
    "test:coverage": "vitest run --coverage"
  }
}
```

---

### 5.2 Add Payment Route Tests

**Create:** `backend/tests/test_payments.py`

```python
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

class TestGuestCheckout:
    def test_guest_checkout_creates_session(self):
        """Test that guest checkout creates Stripe session."""
        with patch('src.routes.payments.stripe') as mock_stripe:
            mock_stripe.checkout.Session.create.return_value = MagicMock(
                id="cs_test_123",
                url="https://checkout.stripe.com/..."
            )

            response = client.post("/api/payments/guest-checkout", json={
                "quiz_session_id": "test-session-id",
                "tier": "quick",
                "email": "test@example.com"
            })

            assert response.status_code == 200
            assert "checkout_url" in response.json()

    def test_guest_checkout_validates_email(self):
        """Test that invalid email is rejected."""
        response = client.post("/api/payments/guest-checkout", json={
            "quiz_session_id": "test-session-id",
            "tier": "quick",
            "email": "invalid-email"
        })

        assert response.status_code == 422

class TestWebhook:
    def test_webhook_validates_signature(self):
        """Test that invalid webhook signature is rejected."""
        response = client.post(
            "/api/payments/webhook",
            content=b"{}",
            headers={"stripe-signature": "invalid"}
        )

        assert response.status_code == 400

    def test_webhook_handles_checkout_completed(self):
        """Test successful checkout completion."""
        # ... webhook test implementation
```

---

### 5.3 Add Auth Route Tests

**Create:** `backend/tests/test_auth.py`

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

class TestSignup:
    def test_signup_creates_user(self):
        """Test user signup flow."""
        response = client.post("/api/auth/signup", json={
            "email": "newuser@test.com",
            "password": "SecurePass123!"
        })

        assert response.status_code in [200, 201]
        assert "access_token" in response.json()

    def test_signup_rejects_weak_password(self):
        """Test that weak passwords are rejected."""
        response = client.post("/api/auth/signup", json={
            "email": "newuser@test.com",
            "password": "123"
        })

        assert response.status_code == 400

class TestLogin:
    def test_login_returns_token(self):
        """Test login returns JWT."""
        # ... implementation

    def test_login_rejects_invalid_credentials(self):
        """Test invalid credentials rejected."""
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "wrong"
        })

        assert response.status_code == 401
```

---

## Phase 6: Minor Fixes (P2)

### 6.1 Remove Hardcoded localhost URL

**File:** `backend/src/routes/payments.py:195`

```python
# Replace:
base_url = "http://localhost:5174"

# With:
from src.config.settings import settings
base_url = settings.FRONTEND_URL  # Add to settings.py
```

---

### 6.2 Remove Console.log Statements

**Files to clean:**
- `frontend/src/pages/Checkout.tsx:63-64`
- Search: `grep -r "console.log" frontend/src/`

---

### 6.3 Remove Duplicate Chart Library

**File:** `frontend/package.json`

```bash
# Keep recharts, remove apexcharts (or vice versa)
cd frontend && npm uninstall apexcharts react-apexcharts
```

---

### 6.4 Update Outdated Dependencies

**File:** `backend/requirements.txt`

```bash
# Update FastAPI
pip install --upgrade fastapi

# Replace python-jose with PyJWT
pip uninstall python-jose
pip install PyJWT

# Update requirements.txt
pip freeze > requirements.txt
```

---

### 6.5 Add CSP Header

**File:** `backend/src/middleware/security.py`

```python
# Add to security headers middleware:
response.headers["Content-Security-Policy"] = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://js.stripe.com; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "connect-src 'self' https://api.stripe.com https://api.anthropic.com; "
    "frame-src https://js.stripe.com; "
)
```

---

## Verification Checklist

After completing all fixes, verify:

```bash
# 1. Security fixes
curl -X GET "http://localhost:8383/api/reports/public/random-uuid"  # Should return 402
curl -X GET "http://localhost:8383/api/admin/research/stale-count"  # Should return 401
curl -X GET "http://localhost:8383/api/admin/qa/queue"  # Should return 401

# 2. Run all backend tests
cd backend && pytest -v

# 3. Run frontend tests
cd frontend && npm test

# 4. Type checking
cd backend && mypy --strict src/
cd frontend && npm run typecheck

# 5. Verify no console.log in production
grep -r "console.log" frontend/src/ | grep -v test | grep -v ".d.ts"

# 6. Check for hardcoded URLs
grep -r "localhost" backend/src/ --include="*.py" | grep -v test | grep -v "#"
```

---

## Execution Order

1. **Day 1-2:** Phase 1 (Critical Security) - All 6 tasks
2. **Day 3:** Phase 2.1-2.2 (Background tasks, Redis lock)
3. **Day 4:** Phase 2.3, 3.1-3.2 (Session expiry, Supabase retry, model fallback)
4. **Day 5:** Phase 3.3-3.4 (Redis quiz state, transaction wrapper)
5. **Day 6-7:** Phase 4 (Frontend UX fixes)
6. **Day 8-10:** Phase 5 (Testing infrastructure)
7. **Day 11-12:** Phase 6 (Minor fixes)

---

## Success Metrics

| Metric | Before | After |
|--------|--------|-------|
| Critical security issues | 5 | 0 |
| Public endpoints without auth | 7 | 0 |
| Backend test coverage | ~20% | 60%+ |
| Frontend test files | 0 | 15+ |
| Console.log in production | 12+ | 0 |
| Hardcoded URLs | 5+ | 0 |
