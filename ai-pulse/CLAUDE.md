# AI Pulse - Development Guide

## Quick Start

```bash
# Backend (port 8484)
cd backend && source venv/bin/activate && uvicorn src.main:app --reload --port 8484

# Frontend (port 5175)
cd frontend && npm run dev

# Redis (required for caching)
brew services start redis
```

---

## What is AI Pulse?

AI Pulse is a micro-SaaS ($1/month) that monitors 50+ AI sources and delivers curated daily digests of the most important AI news, tools, and insights.

**Tagline:** "AI moves too fast. Get the signal, skip the noise."

**Business Model:**
- €1/month (EU) or $1/month (elsewhere) subscription via Stripe
- $10/year annual option (2 months free)
- Daily email digest of top 10 AI news items
- Web dashboard to browse content and manage preferences

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI + Python 3.12 |
| Frontend | React 18 + Vite + TypeScript + Tailwind |
| Database | Supabase (PostgreSQL + Auth) |
| Cache | Redis |
| AI Scoring | Google Gemini Flash (cheap) + Claude (summaries) |
| Email | Brevo (primary) + SendGrid (backup) |
| Payments | Stripe (multi-currency) |
| Deploy | Railway |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI PULSE                                  │
├─────────────────────────────────────────────────────────────────┤
│  Scrapers (every 4h)    Scorer              Digest Generator    │
│  • RSS feeds            • Rule-based        • Top 10 selection  │
│  • YouTube API          • Gemini Flash      • AI summaries      │
│  • Reddit JSON                                                   │
│  • Twitter API                                                   │
│         │                    │                     │            │
│         ▼                    ▼                     ▼            │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   Supabase   │     │    Redis     │     │ Brevo/SendGrid│    │
│  │  • articles  │     │  • cache     │     │  • digests    │    │
│  │  • users     │     │  • rate lim  │     │  • by timezone│    │
│  │  • digests   │     │              │     │              │     │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│         ▲                                                       │
│  ┌──────────────┐     ┌──────────────┐                         │
│  │   Frontend   │────▶│    Stripe    │                         │
│  │  • Landing   │     │  • €1 EUR    │                         │
│  │  • Dashboard │     │  • $1 USD    │                         │
│  └──────────────┘     └──────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Content Sources (50+)

### YouTube Channels
Cole Medin, Dave Shapiro, Liam Ottley, Matthew Berman, AI Explained, Wes Roth, AI Jason, Sam Witteveen, All About AI, WorldofAI, Prompt Engineering, Fireship, Two Minute Papers, Yannic Kilcher, NetworkChuck, Corbin Brown, Leon van Zyl, Greg Isenberg

### RSS Feeds
OpenAI Blog, Anthropic News, Google AI Blog, Hugging Face Blog, ArXiv AI, TechCrunch AI, The Verge AI, MIT Tech Review AI, LangChain Blog

### Reddit
r/MachineLearning, r/LocalLLaMA, r/ChatGPT, r/ClaudeAI, r/artificial

### Twitter/X
@sama, @AnthropicAI, @OpenAI, @GoogleDeepMind, @karpathy, @ylecun, @DrJimFan

---

## Database Schema

```sql
users
├── id, email, name
├── timezone, preferred_time ('morning'|'lunch'|'evening')
├── stripe_customer_id, subscription_status, currency
├── created_at, updated_at

sources
├── id, slug, name, source_type, url
├── category, priority (1-10), enabled
├── last_fetched_at

articles
├── id, source_id, external_id
├── content_type, title, description, url, thumbnail_url
├── published_at, fetched_at
├── views, likes, comments
├── score, novelty_score, impact_score
├── summary (AI-generated), categories
├── is_processed

digests
├── id, created_at, article_ids, subject_line, stats

digest_sends
├── id, digest_id, user_id, sent_at
├── opened_at, clicked_at, status
```

---

## API Routes

```
# Public
GET  /health
GET  /api/preview              # Top 3 for landing page
GET  /api/sources              # All monitored sources

# Auth
POST /api/auth/signup
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me

# Subscribers
GET  /api/articles             # Paginated feed
GET  /api/articles/:id
GET  /api/digests              # Archive
GET  /api/digests/:id
GET  /api/user/preferences
PATCH /api/user/preferences

# Stripe
POST /api/checkout
POST /api/webhooks/stripe
POST /api/billing/portal

# Admin
GET  /api/admin/stats
POST /api/admin/trigger-digest
```

---

## Development Rules

### Code Quality
- **Read before edit** - Never modify code without reading it first
- **Type everything** - Use Pydantic models, TypeScript types
- **Test scrapers** - Each scraper needs unit tests with mocked responses

### Error Handling
```python
class APIError(Exception):
    def __init__(self, message: str, code: str, status: int = 500):
        self.message = message
        self.code = code
        self.status = status

# Routes return consistent format
{"data": {...}}
{"error": {"code": "...", "message": "...", "status": 400}}
```

### Logging
```python
import structlog
logger = structlog.get_logger()

logger.info("article_scraped", source=source_name, count=len(articles))
logger.error("scraper_failed", source=source_name, error=str(e))
```

### Security
- RLS on all Supabase tables
- Pydantic validation on all inputs
- Rate limit scrapers to respect APIs
- Never log API keys

---

## Scoring Algorithm

### Layer 1: Rules (Free)
- Filter out gaming, crypto, drama content
- Boost by source priority + engagement metrics
- Keep top 50-100 candidates

### Layer 2: Gemini Flash (~$0.10-0.20/day)
- Score top 50 for relevance/novelty (0-1)
- Quick classification

### Layer 3: Summaries (~$0.05-0.10/day)
- Generate 2-3 sentence summaries for top 10
- Write digest intro

### High-Signal Keywords (boost)
gpt-5, claude 4, gemini 2, opus, sonnet, agi, agents, agentic, multimodal, breakthrough, releases, announces

### Low-Value Patterns (filter)
gaming, crypto, NFT, sponsored, reaction video, drama, <60 second videos

---

## Digest Schedule

Users choose delivery time at signup:
- **Morning** (7 AM local) - "Start your day informed"
- **Lunchtime** (12 PM local) - "Midday reading" (default)
- **Evening** (6 PM local) - "Catch up after work"

Scheduler runs hourly, sends to users whose local time matches their preference.

---

## Git Workflow

### Branches
```
main              # Production
feat/xxx          # Features
fix/xxx           # Bug fixes
```

### Commits
```
feat: add YouTube scraper
fix: handle rate limit in Reddit scraper
refactor: extract scoring to separate module
```

---

## Testing

```bash
# Backend
cd backend && pytest
pytest -v tests/test_scrapers.py
pytest -k "test_rss"

# Frontend
cd frontend && npm test
```

### Scraper Testing Pattern
```python
def test_rss_scraper_parses_feed(mock_feedparser):
    mock_feedparser.return_value = SAMPLE_FEED
    scraper = RssScraper()
    articles = scraper.fetch("https://example.com/feed.xml")
    assert len(articles) == 5
    assert articles[0].title == "Expected Title"
```

---

## Key Files

| Area | File |
|------|------|
| **Config** | |
| Settings | `backend/src/config/settings.py` |
| Sources | `backend/src/config/sources.py` |
| **Scrapers** | |
| Base | `backend/src/scrapers/base.py` |
| RSS | `backend/src/scrapers/rss.py` |
| YouTube | `backend/src/scrapers/youtube.py` |
| Reddit | `backend/src/scrapers/reddit.py` |
| **Scoring** | |
| Rules | `backend/src/scoring/rules.py` |
| AI Scorer | `backend/src/scoring/ai_scorer.py` |
| **Services** | |
| Digest | `backend/src/services/digest_service.py` |
| Email | `backend/src/services/email/` |
| Scheduler | `backend/src/services/scheduler_service.py` |
| **Routes** | |
| Auth | `backend/src/routes/auth.py` |
| Articles | `backend/src/routes/articles.py` |
| Checkout | `backend/src/routes/checkout.py` |
| **Frontend** | |
| Auth Context | `frontend/src/contexts/AuthContext.tsx` |
| Landing | `frontend/src/pages/Landing.tsx` |
| Dashboard | `frontend/src/pages/Dashboard.tsx` |

---

## Environment Variables

```bash
# Backend (required)
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
SECRET_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=           # For Gemini Flash
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
BREVO_API_KEY=

# Backend (optional)
REDIS_URL=redis://localhost:6379
YOUTUBE_API_KEY=
TWITTER_BEARER_TOKEN=     # $100/month for Basic tier
SENDGRID_API_KEY=         # Backup email
LOGFIRE_TOKEN=
BETTERSTACK_SOURCE_TOKEN=

# Frontend
VITE_API_BASE_URL=http://localhost:8484
VITE_STRIPE_PUBLISHABLE_KEY=
```

---

## Common Tasks

### Add a New Source
1. Add to `backend/src/config/sources.py`
2. Ensure appropriate scraper exists for source type
3. Test with: `python -m src.scrapers.rss "https://new-source.com/feed"`

### Add a New Scraper Type
1. Create `backend/src/scrapers/<type>.py`
2. Inherit from `BaseScraper`
3. Implement `fetch()` and `parse()` methods
4. Add tests in `backend/tests/test_scrapers.py`
5. Register in scraper factory

### Manual Digest Generation
```bash
# CLI
python -m src.jobs.send_digests --dry-run
python -m src.jobs.send_digests

# API (admin only)
curl -X POST http://localhost:8484/api/admin/trigger-digest
```

---

## Pricing (Stripe)

| Plan | EUR | USD | Stripe Price IDs |
|------|-----|-----|------------------|
| Monthly | €1 | $1 | `price_monthly_eur`, `price_monthly_usd` |
| Annual | €10 | $10 | `price_annual_eur`, `price_annual_usd` |

Detect user location via IP or country selection at checkout.

---

## Deployment (Railway)

```bash
# Deploy backend
railway up --service backend

# Deploy frontend
railway up --service frontend

# Set environment variables
railway variables set SUPABASE_URL=xxx
```

### Cron Jobs (Railway)
- Article fetch: `0 */4 * * *` (every 4 hours)
- Digest send: `0 * * * *` (every hour, filters by timezone)
- Cleanup: `0 0 * * 0` (weekly)

---

## Debugging

| Issue | Check |
|-------|-------|
| Scraper failing | API rate limits, network, parse errors |
| No articles | Source enabled? Last fetch time? |
| Email not sending | Brevo API key, sender verified? |
| Stripe webhook failing | Webhook secret, endpoint URL |

```bash
# Check Redis
redis-cli KEYS "*"

# Check recent articles
curl http://localhost:8484/api/preview

# Verbose logs
uvicorn src.main:app --reload --port 8484 --log-level debug
```

---

## Model Routing

| Task | Model | Cost |
|------|-------|------|
| Article scoring | Gemini Flash | ~$0.10/1M tokens |
| Summary generation | Claude Haiku | ~$0.25/1M tokens |
| Digest intro | Claude Haiku | ~$0.25/1M tokens |

**Daily cost estimate: $0.20-0.40**

---

## Anti-Patterns (Don't Do)

- ❌ Scraping without rate limits
- ❌ Storing full article content (just store URL + summary)
- ❌ Sending emails synchronously (use background jobs)
- ❌ Hardcoded API keys
- ❌ Ignoring scraper errors (log and continue)

---

## Shortcuts

| Short | Meaning |
|-------|---------|
| KB | Knowledge Base (sources) |
| FE/BE | Frontend/Backend |
| SSE | Server-Sent Events |
| PR | Pull Request |
