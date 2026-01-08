"""
AI Pulse Configuration Settings
"""

import logging
from functools import lru_cache
from typing import List, Optional
from urllib.parse import urlparse

from pydantic import field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App Config
    APP_NAME: str = "AI Pulse"
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8484
    WORKERS: int = 1

    # Security
    SECRET_KEY: str = "change-me-in-production-min-32-characters"
    CORS_ORIGINS: str = "http://localhost:5175,http://localhost:5176,http://127.0.0.1:5175,http://127.0.0.1:5176"

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_JWT_SECRET: Optional[str] = None

    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_MAX_CONNECTIONS: int = 10
    REDIS_RETRY_ATTEMPTS: int = 3
    REDIS_RETRY_DELAY: float = 1.0

    # Cache TTLs (seconds)
    CACHE_TTL_ARTICLE: int = 3600  # 1 hour
    CACHE_TTL_ARTICLE_LIST: int = 300  # 5 minutes
    CACHE_TTL_DIGEST: int = 86400  # 24 hours
    CACHE_TTL_SOURCES: int = 3600  # 1 hour

    # AI/LLM
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: Optional[str] = None  # For Gemini Flash
    DEFAULT_MODEL: str = "gemini-2.0-flash"  # Cheap scoring
    SUMMARY_MODEL: str = "claude-haiku-4-5-20251001"  # Quality summaries

    # Content Sources
    YOUTUBE_API_KEY: Optional[str] = None
    TWITTER_BEARER_TOKEN: Optional[str] = None  # $100/month Basic tier

    # Scraper Settings
    SCRAPER_TIMEOUT: int = 30
    SCRAPER_RATE_LIMIT_DELAY: float = 1.0  # seconds between requests
    MAX_ARTICLES_PER_SOURCE: int = 20
    ARTICLE_RETENTION_DAYS: int = 30

    # Digest Settings
    DIGEST_TOP_ITEMS: int = 10
    DIGEST_SCORE_THRESHOLD: float = 0.3  # Minimum score to include

    # Email (Brevo - Primary)
    BREVO_API_KEY: Optional[str] = None
    FROM_EMAIL: str = "digest@aipulse.dev"
    FROM_NAME: str = "AI Pulse"

    # Email (SendGrid - Backup)
    SENDGRID_API_KEY: Optional[str] = None

    # Payments (Stripe)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    # Monthly prices
    STRIPE_PRICE_MONTHLY_EUR: Optional[str] = None
    STRIPE_PRICE_MONTHLY_USD: Optional[str] = None
    # Annual prices
    STRIPE_PRICE_ANNUAL_EUR: Optional[str] = None
    STRIPE_PRICE_ANNUAL_USD: Optional[str] = None

    # Monitoring
    LOGFIRE_TOKEN: Optional[str] = None
    SENTRY_DSN: Optional[str] = None
    BETTERSTACK_SOURCE_TOKEN: Optional[str] = None
    BETTERSTACK_HOST: str = "https://in.logs.betterstack.com"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Validate SECRET_KEY is properly set in production."""
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
        """Validate CORS origins format."""
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

    def get_stripe_price(self, currency: str, annual: bool = False) -> Optional[str]:
        """Get Stripe price ID for currency and billing period."""
        if annual:
            return self.STRIPE_PRICE_ANNUAL_EUR if currency == "EUR" else self.STRIPE_PRICE_ANNUAL_USD
        return self.STRIPE_PRICE_MONTHLY_EUR if currency == "EUR" else self.STRIPE_PRICE_MONTHLY_USD

    def validate_critical_secrets(self) -> List[str]:
        """Validate all critical secrets are set."""
        issues = []

        if not self.SUPABASE_URL:
            issues.append("SUPABASE_URL is not set")
        if not self.SUPABASE_SERVICE_KEY:
            issues.append("SUPABASE_SERVICE_KEY is not set")

        if self.is_production:
            if not self.STRIPE_SECRET_KEY:
                issues.append("STRIPE_SECRET_KEY is not set (required in production)")
            if not self.STRIPE_WEBHOOK_SECRET:
                issues.append("STRIPE_WEBHOOK_SECRET is not set (required in production)")
            if not self.BREVO_API_KEY and not self.SENDGRID_API_KEY:
                issues.append("Email provider not configured (BREVO_API_KEY or SENDGRID_API_KEY)")
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
    """Validate configuration on startup."""
    issues = settings.validate_critical_secrets()
    if issues:
        for issue in issues:
            logger.error(f"Configuration issue: {issue}")
        if settings.is_production:
            raise ValueError(
                f"Critical configuration issues in production: {', '.join(issues)}"
            )
