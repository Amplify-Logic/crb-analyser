"""
CRB Analyser Configuration Settings
"""

import logging
import re
from functools import lru_cache
from typing import List, Optional
from urllib.parse import urlparse

from pydantic import field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App Config
    APP_NAME: str = "CRB Analyser"
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8383
    WORKERS: int = 1  # Number of uvicorn workers (1 recommended for async)

    # Security
    SECRET_KEY: str = "change-me-in-production-min-32-characters"
    CORS_ORIGINS: str = "http://localhost:5174,http://127.0.0.1:5174"

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_JWT_SECRET: Optional[str] = None

    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_MAX_CONNECTIONS: int = 10
    REDIS_RETRY_ATTEMPTS: int = 3
    REDIS_RETRY_DELAY: float = 1.0  # seconds

    # Cache TTLs (seconds)
    CACHE_TTL_SECONDS: int = 3600  # Default 1 hour
    CACHE_TTL_VENDOR: int = 86400  # 24 hours
    CACHE_TTL_VENDOR_LIST: int = 3600  # 1 hour
    CACHE_TTL_BENCHMARK: int = 604800  # 7 days
    CACHE_TTL_REPORT: int = 3600  # 1 hour
    CACHE_TTL_QUIZ: int = 86400  # 24 hours

    # AI/LLM
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: Optional[str] = None
    DEFAULT_MODEL: str = "claude-sonnet-4-20250514"

    # Tool execution settings
    TOOL_TIMEOUT_DEFAULT: int = 30  # seconds
    TOOL_TIMEOUT_RESEARCH: int = 60  # seconds for web scraping
    TOOL_TIMEOUT_DISCOVERY: int = 30
    TOOL_TIMEOUT_ANALYSIS: int = 20
    TOOL_RETRY_ATTEMPTS: int = 3
    TOOL_RETRY_DELAY: float = 1.0  # seconds

    # Search APIs
    BRAVE_SEARCH_API_KEY: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None

    # Speech-to-Text (Deepgram)
    DEEPGRAM_API_KEY: Optional[str] = None

    # Payments (Stripe) - Fixed naming to match .env.production
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PROFESSIONAL_PRICE_ID: Optional[str] = None  # Fixed naming
    STRIPE_EARLY_ADOPTER_PRICE_ID: Optional[str] = None  # Fixed naming
    # Legacy aliases (for backwards compatibility)
    STRIPE_PRICE_PROFESSIONAL: Optional[str] = None
    STRIPE_PRICE_PROFESSIONAL_EARLY: Optional[str] = None

    # Email (SendGrid)
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: str = "reports@crb-analyser.com"
    SENDGRID_FROM_NAME: str = "CRB Analyser"

    # Monitoring
    LOGFIRE_TOKEN: Optional[str] = None
    SENTRY_DSN: Optional[str] = None
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # CRB Business Config - Pricing Tiers
    PRICE_QUICK_REPORT: int = 47  # Quick Report tier
    PRICE_FULL_ANALYSIS: int = 297  # Full Analysis tier
    PRICE_PROFESSIONAL: int = 697  # Legacy
    PRICE_PROFESSIONAL_EARLY: int = 497  # Legacy
    MAX_FINDINGS_FREE: int = 3
    MAX_FINDINGS_QUICK: int = 15
    MAX_FINDINGS_FULL: int = 50
    MAX_FINDINGS_PROFESSIONAL: int = 20  # Legacy
    REPORT_RETENTION_DAYS: int = 365

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_MAX_MEMORY_ENTRIES: int = 10000  # Max IPs to track in memory

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Validate SECRET_KEY is properly set in production."""
        # Get APP_ENV from the data being validated
        app_env = info.data.get("APP_ENV", "development")
        if app_env == "production":
            if "change-me" in v.lower() or len(v) < 32:
                raise ValueError(
                    "SECRET_KEY must be changed from default and be at least "
                    "32 characters in production"
                )
        return v

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v: str, info) -> str:
        """Validate CORS origins format and warn about localhost in production."""
        app_env = info.data.get("APP_ENV", "development")
        origins = [origin.strip() for origin in v.split(",")]

        for origin in origins:
            if origin:
                try:
                    parsed = urlparse(origin)
                    if not parsed.scheme or not parsed.netloc:
                        raise ValueError(f"Invalid CORS origin format: {origin}")
                except Exception:
                    raise ValueError(f"Invalid CORS origin: {origin}")

                # Warn about localhost in production
                if app_env == "production":
                    if "localhost" in origin or "127.0.0.1" in origin:
                        logger.warning(
                            f"CORS origin contains localhost in production: {origin}"
                        )
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string to list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def stripe_professional_price(self) -> Optional[str]:
        """Get professional price ID with fallback to legacy naming."""
        return self.STRIPE_PROFESSIONAL_PRICE_ID or self.STRIPE_PRICE_PROFESSIONAL

    @property
    def stripe_early_adopter_price(self) -> Optional[str]:
        """Get early adopter price ID with fallback to legacy naming."""
        return self.STRIPE_EARLY_ADOPTER_PRICE_ID or self.STRIPE_PRICE_PROFESSIONAL_EARLY

    def validate_critical_secrets(self) -> List[str]:
        """
        Validate all critical secrets are set.
        Returns list of missing/invalid secrets.
        """
        issues = []

        if not self.SUPABASE_URL:
            issues.append("SUPABASE_URL is not set")
        if not self.SUPABASE_SERVICE_KEY:
            issues.append("SUPABASE_SERVICE_KEY is not set")
        if not self.ANTHROPIC_API_KEY:
            issues.append("ANTHROPIC_API_KEY is not set")

        if self.is_production:
            if not self.STRIPE_SECRET_KEY:
                issues.append("STRIPE_SECRET_KEY is not set (required in production)")
            if not self.STRIPE_WEBHOOK_SECRET:
                issues.append("STRIPE_WEBHOOK_SECRET is not set (required in production)")
            if "change-me" in self.SECRET_KEY.lower():
                issues.append("SECRET_KEY is still set to default value")

        return issues

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()


def validate_startup_config() -> None:
    """
    Validate configuration on startup.
    Raises ValueError if critical issues found.
    """
    issues = settings.validate_critical_secrets()
    if issues:
        for issue in issues:
            logger.error(f"Configuration issue: {issue}")
        if settings.is_production:
            raise ValueError(
                f"Critical configuration issues in production: {', '.join(issues)}"
            )
