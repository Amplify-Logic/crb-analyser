"""
CRB Analyser - Main Application

AI-powered Cost/Risk/Benefit Analysis for Business
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
from src.config.supabase_client import init_supabase, close_supabase
from src.config.redis_client import init_redis, close_redis
from src.config.observability import setup_observability
from src.middleware.error_handler import setup_error_handlers
from src.middleware.security import setup_security
from src.middleware.request_logger import setup_request_logging
from src.services.scheduler_service import setup_scheduler, start_scheduler, shutdown_scheduler

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info(f"Starting {settings.APP_NAME}...")

    # Startup
    try:
        await init_supabase()
        logger.info("Database connection established")
    except Exception as e:
        logger.warning(f"Could not connect to database: {e}")

    try:
        await init_redis()
        logger.info("Redis cache initialized")
    except Exception as e:
        logger.warning(f"Could not connect to Redis: {e}")

    # Start background scheduler (follow-up emails, cleanup jobs)
    try:
        setup_scheduler()
        start_scheduler()
        logger.info("Background scheduler started")
    except Exception as e:
        logger.warning(f"Could not start scheduler: {e}")

    yield

    # Shutdown
    shutdown_scheduler()
    await close_redis()
    await close_supabase()
    logger.info(f"Shutting down {settings.APP_NAME}...")


# Create app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered Cost/Risk/Benefit Analysis for Business",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
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

# Setup security middleware
setup_security(app)

# Setup request logging
setup_request_logging(app)

# Setup observability (Logfire + Sentry)
setup_observability(app)


# ============================================================================
# API Routes
# ============================================================================

from src.routes import (
    auth_router,
    clients_router,
    audits_router,
    intake_router,
    reports_router,
    payments_router,
    research_router,
    quiz_router,
    health_router,
    vendors_router,
    admin_router,
    interview_router,
    playbook_router,
)

# Health routes (no prefix - routes define their own paths)
app.include_router(health_router, tags=["Health"])

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(clients_router, prefix="/api/clients", tags=["Clients"])
app.include_router(audits_router, prefix="/api/audits", tags=["Audits"])
app.include_router(intake_router, prefix="/api/intake", tags=["Intake"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])
app.include_router(payments_router, prefix="/api/payments", tags=["Payments"])
app.include_router(research_router, prefix="/api/research", tags=["Research"])
app.include_router(quiz_router, prefix="/api/quiz", tags=["Quiz"])
app.include_router(vendors_router, prefix="/api/vendors", tags=["Vendors"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
app.include_router(interview_router, prefix="/api/interview", tags=["Interview"])
app.include_router(playbook_router, prefix="/api/playbook", tags=["Playbook"])


# ============================================================================
# Development Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_development
    )
