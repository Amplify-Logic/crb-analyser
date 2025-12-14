"""
CRB Analyser Configuration Settings
"""

from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings


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

    # Security
    SECRET_KEY: str = "change-me-in-production-min-32-characters"
    CORS_ORIGINS: str = "http://localhost:5174,http://127.0.0.1:5174"

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_JWT_SECRET: Optional[str] = None

    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL_SECONDS: int = 3600

    # AI/LLM
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: Optional[str] = None
    DEFAULT_MODEL: str = "claude-sonnet-4-20250514"

    # Search APIs
    BRAVE_SEARCH_API_KEY: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None

    # Speech-to-Text (Deepgram)
    DEEPGRAM_API_KEY: Optional[str] = None

    # Payments (Stripe)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_PROFESSIONAL: Optional[str] = None
    STRIPE_PRICE_PROFESSIONAL_EARLY: Optional[str] = None

    # Email (SendGrid)
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: str = "reports@crb-analyser.com"
    SENDGRID_FROM_NAME: str = "CRB Analyser"

    # Monitoring
    LOGFIRE_TOKEN: Optional[str] = None
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

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string to list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
