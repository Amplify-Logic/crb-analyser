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
from src.middleware.error_handler import setup_error_handlers
from src.middleware.security import setup_security

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

    yield

    # Shutdown
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


# ============================================================================
# Health Check Routes
# ============================================================================

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "0.1.0"
    }


@app.get("/api/health")
async def api_health_check():
    """API health check with more details."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "0.1.0",
        "environment": settings.APP_ENV
    }


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
)

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(clients_router, prefix="/api/clients", tags=["Clients"])
app.include_router(audits_router, prefix="/api/audits", tags=["Audits"])
app.include_router(intake_router, prefix="/api/intake", tags=["Intake"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])
app.include_router(payments_router, prefix="/api/payments", tags=["Payments"])
app.include_router(research_router, prefix="/api/research", tags=["Research"])

# TODO: Add admin routes
# from src.routes import admin_router
# app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])


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
