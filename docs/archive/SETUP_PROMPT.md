# CRB Analyser - Master Setup Prompt

> **INSTRUCTIONS: Copy this ENTIRE document as your first message in the crb-analyser repo**

---

## Step 1: Create Project Files

First, create these three essential files in the repo root:

### File 1: CLAUDE.md
Create `CLAUDE.md` with the contents from the CRB_CLAUDE.md file I'll provide.

### File 2: PRD.md
Create `PRD.md` with the contents from the CRB_PRD_FINAL.md file I'll provide.

### File 3: BOOTSTRAP.md
Create `BOOTSTRAP.md` with the contents from the CRB_ANALYSER_BOOTSTRAP.md file I'll provide.

---

## Step 2: Create Directory Structure

```bash
# Create all directories
mkdir -p backend/src/{config,middleware,routes,agents,tools,services,models}
mkdir -p backend/src/services/{knowledge,email}
mkdir -p backend/supabase/migrations
mkdir -p frontend/src/{pages,components,contexts,services,hooks}
mkdir -p frontend/src/components/{ui,auth,intake,audit,findings,report}
mkdir -p frontend/public

# Create __init__.py files for Python packages
touch backend/src/__init__.py
touch backend/src/config/__init__.py
touch backend/src/middleware/__init__.py
touch backend/src/routes/__init__.py
touch backend/src/agents/__init__.py
touch backend/src/tools/__init__.py
touch backend/src/services/__init__.py
touch backend/src/services/knowledge/__init__.py
touch backend/src/services/email/__init__.py
touch backend/src/models/__init__.py
```

---

## Step 3: Create Foundation Files

### 3.1 Backend requirements.txt

Create `backend/requirements.txt`:
```
# Core
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-socketio==5.11.0
python-multipart==0.0.6
httpx==0.27.0

# Database
supabase==2.11.0
pgvector==0.3.6
sqlalchemy==2.0.36
asyncpg==0.29.0
psycopg2-binary==2.9.10

# Memory/Cache
zep-cloud==3.4.0
redis==6.4.0

# AI/LLM
anthropic==0.43.0
openai==1.59.9

# Data Processing
pydantic==2.10.4
pydantic-settings==2.7.1
email-validator==2.2.0
pandas==2.1.4
numpy==1.26.3

# Utils
python-dotenv==1.0.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Email & Payments
sendgrid==6.11.0
stripe==11.4.1
apscheduler==3.10.4

# Monitoring
logfire==0.20.0

# PDF Generation
reportlab==4.0.0
weasyprint==60.0

# DNS
dnspython==2.7.0

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
```

### 3.2 Backend .env.example

Create `backend/.env.example`:
```bash
# =============================================================================
# CRB ANALYSER - BACKEND CONFIGURATION
# =============================================================================

# Application
APP_NAME=CRB Analyser
APP_ENV=development
LOG_LEVEL=INFO
DEBUG=true

# =============================================================================
# DATABASE (Supabase)
# =============================================================================
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres

# =============================================================================
# AUTHENTICATION
# =============================================================================
SECRET_KEY=your-secret-key-minimum-32-characters-long
CORS_ORIGINS=http://localhost:5174,https://crb-analyser.com

# =============================================================================
# AI / LLM
# =============================================================================
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Optional: For embeddings
OPENAI_API_KEY=sk-...

# =============================================================================
# SEARCH APIs
# =============================================================================
BRAVE_API_KEY=BSA...
TAVILY_API_KEY=tvly-...

# =============================================================================
# CACHING
# =============================================================================
REDIS_URL=redis://localhost:6379

# =============================================================================
# MEMORY (Optional)
# =============================================================================
ZEP_API_KEY=z_...
ZEP_API_URL=https://api.getzep.com

# =============================================================================
# PAYMENTS (Stripe)
# =============================================================================
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PROFESSIONAL_PRICE_ID=price_...
STRIPE_EARLY_ADOPTER_PRICE_ID=price_...

# =============================================================================
# EMAIL (SendGrid)
# =============================================================================
SENDGRID_API_KEY=SG...
SENDGRID_FROM_EMAIL=reports@crb-analyser.com
SENDGRID_FROM_NAME=CRB Analyser

# =============================================================================
# MONITORING
# =============================================================================
LOGFIRE_TOKEN=...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 3.3 Frontend package.json

Create `frontend/package.json`:
```json
{
  "name": "crb-analyser",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --port 5174",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext .js,.jsx,.ts,.tsx",
    "test": "vitest"
  },
  "dependencies": {
    "@headlessui/react": "^1.7.17",
    "@sentry/react": "^10.23.0",
    "@tanstack/react-query": "^5.90.5",
    "clsx": "latest",
    "date-fns": "^4.1.0",
    "framer-motion": "^11.5.4",
    "lucide-react": "^0.441.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-hook-form": "^7.48.2",
    "react-markdown": "^10.1.0",
    "react-router-dom": "^6.26.2",
    "recharts": "^2.12.0",
    "socket.io-client": "^4.8.1",
    "tailwind-merge": "latest",
    "zod": "^3.25.46"
  },
  "devDependencies": {
    "@types/node": "^20.19.0",
    "@types/react": "^18.3.1",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.2.1",
    "@vitest/coverage-v8": "^1.6.0",
    "autoprefixer": "latest",
    "eslint": "^8.50.0",
    "postcss": "latest",
    "tailwindcss": "3.4.17",
    "typescript": "^5.5.4",
    "vite": "^5.2.0",
    "vitest": "^1.6.0"
  }
}
```

### 3.4 Frontend .env.example

Create `frontend/.env.example`:
```bash
VITE_API_BASE_URL=http://localhost:8383
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_...
VITE_SENTRY_DSN=https://...@sentry.io/...
VITE_SENTRY_ENVIRONMENT=development
```

### 3.5 Root .gitignore

Create `.gitignore`:
```
# Dependencies
node_modules/
venv/
.venv/
__pycache__/
*.pyc

# Environment
.env
.env.local
.env.*.local

# Build
dist/
build/
*.egg-info/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Testing
coverage/
.pytest_cache/
htmlcov/

# Misc
*.bak
*.tmp
```

### 3.6 docker-compose.yml

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8383:8383"
    environment:
      - PORT=8383
    env_file:
      - ./backend/.env
    depends_on:
      - redis
    networks:
      - crb-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5174:5174"
    environment:
      - PORT=5174
    env_file:
      - ./frontend/.env
    networks:
      - crb-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - crb-network

networks:
  crb-network:
    driver: bridge
```

---

## Step 4: Copy Infrastructure from MMAI

Now copy these files from MMAI (`/Users/larsmusic/Music Manager AI/`):

### Backend Config
```
mmai-backend/src/config/supabase_client.py → backend/src/config/supabase_client.py
mmai-backend/src/config/logfire_config.py → backend/src/config/logfire_config.py
```

### Backend Middleware
```
mmai-backend/src/middleware/auth.py → backend/src/middleware/auth.py
mmai-backend/src/middleware/security.py → backend/src/middleware/security.py
mmai-backend/src/middleware/error_handler.py → backend/src/middleware/error_handler.py
```

### Backend Services
```
mmai-backend/src/services/cache_service.py → backend/src/services/cache_service.py
mmai-backend/src/services/knowledge/pipeline.py → backend/src/services/knowledge/pipeline.py
mmai-backend/src/services/knowledge/quality_validation.py → backend/src/services/knowledge/quality_validation.py
```

### Frontend Core
```
mmai-frontend/src/contexts/AuthContext.tsx → frontend/src/contexts/AuthContext.tsx
mmai-frontend/src/services/apiClient.ts → frontend/src/services/apiClient.ts
mmai-frontend/src/hooks/useToolStream.ts → frontend/src/hooks/useToolStream.ts
mmai-frontend/vite.config.ts → frontend/vite.config.ts (update port to 8383)
mmai-frontend/tailwind.config.js → frontend/tailwind.config.js
mmai-frontend/postcss.config.js → frontend/postcss.config.js
mmai-frontend/tsconfig.json → frontend/tsconfig.json
```

### Deployment
```
mmai-backend/Dockerfile → backend/Dockerfile (update port to 8383)
mmai-backend/railway.toml → backend/railway.toml
mmai-frontend/Dockerfile → frontend/Dockerfile
mmai-frontend/railway.json → frontend/railway.json
mmai-frontend/build.sh → frontend/build.sh
```

---

## Step 5: Create settings.py

Create `backend/src/config/settings.py`:
```python
"""CRB Analyser Configuration"""
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Application
    app_name: str = "CRB Analyser"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # Database
    supabase_url: str
    supabase_service_key: str
    supabase_service_role_key: Optional[str] = None
    database_url: Optional[str] = None

    # Auth
    secret_key: str
    cors_origins: str = "http://localhost:5174"

    # AI
    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-4-20250514"
    openai_api_key: Optional[str] = None

    # Search
    brave_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None

    # Cache
    redis_url: str = "redis://localhost:6379"

    # Memory
    zep_api_key: Optional[str] = None
    zep_api_url: Optional[str] = None

    # Payments
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_professional_price_id: Optional[str] = None
    stripe_early_adopter_price_id: Optional[str] = None

    # Email
    sendgrid_api_key: Optional[str] = None
    sendgrid_from_email: str = "reports@crb-analyser.com"
    sendgrid_from_name: str = "CRB Analyser"

    # Monitoring
    logfire_token: Optional[str] = None
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "https://cloud.langfuse.com"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
```

---

## Step 6: Create main.py

Create `backend/src/main.py`:
```python
"""CRB Analyser - Main Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from src.config.settings import settings
from src.config.logfire_config import configure_logfire
from src.middleware.error_handler import setup_error_handlers

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info(f"Starting {settings.app_name}...")
    # Startup
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.app_name}...")

# Create app
app = FastAPI(
    title=settings.app_name,
    description="AI-powered Cost/Risk/Benefit Analysis for Business",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup error handlers
setup_error_handlers(app)

# Configure observability
if settings.logfire_token:
    configure_logfire(app)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.app_name}

@app.get("/api/health")
async def api_health_check():
    return {"status": "healthy", "service": settings.app_name}

# Import and register routes (add as you build them)
# from src.routes import auth, clients, audits, findings, reports, intake, payments
# app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
# app.include_router(clients.router, prefix="/api/clients", tags=["clients"])
# app.include_router(audits.router, prefix="/api/audits", tags=["audits"])
# etc.

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8383)
```

---

## Step 7: Create Database Migration

Create `backend/supabase/migrations/001_initial_schema.sql` with the full schema from BOOTSTRAP.md.

---

## Step 8: Verify Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
uvicorn src.main:app --reload --port 8383

# Should see: "Starting CRB Analyser..."
# Health check: curl http://localhost:8383/health

# Frontend
cd frontend
npm install
cp .env.example .env
npm run dev

# Should start on http://localhost:5174
```

---

## Step 9: Build Order

Follow this order to build the complete system:

```
✅ Phase 1: Foundation (Steps 1-8 above)

⬜ Phase 2: Auth & Core Routes
   - Copy auth.py from MMAI, adapt for CRB
   - Create clients.py route
   - Create audits.py route
   - Create frontend auth flow

⬜ Phase 3: Intake System
   - Create intake questionnaire schema
   - Create intake.py route
   - Build frontend IntakeWizard component

⬜ Phase 4: CRB Agent
   - Create crb_agent.py (adapt from maestro_agent.py)
   - Create tool_registry.py
   - Implement 16 CRB tools
   - Create model_routing.py

⬜ Phase 5: Analysis & Output
   - Create findings generation
   - Create recommendations engine
   - Create roi_calculator.py
   - Create report_generator.py (PDF)

⬜ Phase 6: Frontend Pages
   - Landing page
   - Dashboard
   - Intake flow
   - Progress view
   - Report viewer

⬜ Phase 7: Payments & Polish
   - Stripe integration
   - Email notifications
   - Error handling
   - Testing
   - Deployment
```

---

## Ready to Build

You now have everything needed. Start by verifying the foundation works, then proceed phase by phase.

**When you need code from MMAI**, reference the file paths in BOOTSTRAP.md or ask and I'll provide the content.

Let's build CRB Analyser.
