"""
AI Pulse - FastAPI Application

Main entry point for the backend API.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings, validate_startup_config
from src.config.supabase_client import init_supabase, close_supabase
from src.config.redis_client import init_redis, close_redis
from src.config.observability import setup_observability
from src.middleware.error_handler import setup_error_handlers
from src.middleware.request_logger import setup_request_logging
from src.services.scheduler_service import (
    setup_scheduler,
    start_scheduler,
    shutdown_scheduler,
)
from src.routes import (
    auth_router,
    articles_router,
    digests_router,
    checkout_router,
    webhooks_router,
    sources_router,
    admin_router,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME}...")

    # Validate config
    validate_startup_config()

    # Initialize clients
    await init_supabase()
    await init_redis()

    # Setup scheduler
    setup_scheduler()
    start_scheduler()

    logger.info(f"{settings.APP_NAME} started successfully")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}...")

    shutdown_scheduler()
    await close_redis()
    await close_supabase()

    logger.info(f"{settings.APP_NAME} shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI news aggregation and daily digest service",
    version="0.1.0",
    lifespan=lifespan,
)

# Setup observability
setup_observability(app)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup middleware
setup_request_logging(app)
setup_error_handlers(app)

# Register routes
app.include_router(auth_router, prefix="/api")
app.include_router(articles_router, prefix="/api")
app.include_router(digests_router, prefix="/api")
app.include_router(sources_router, prefix="/api")
app.include_router(checkout_router, prefix="/api")
app.include_router(webhooks_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from src.config.redis_client import get_redis_status

    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "redis": get_redis_status(),
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs",
        "health": "/health",
    }


# CLI runner
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_development,
    )
