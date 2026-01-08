"""
Observability configuration for AI Pulse.
Integrates Logfire, Sentry, and BetterStack for logging/tracing and error tracking.
"""

import logging
from typing import Optional

from fastapi import FastAPI

from src.config.settings import settings

logger = logging.getLogger(__name__)


def setup_betterstack() -> None:
    """Configure BetterStack for centralized logging."""
    if not settings.BETTERSTACK_SOURCE_TOKEN:
        logger.info("BetterStack token not configured, skipping setup")
        return

    try:
        from logtail import LogtailHandler

        betterstack_handler = LogtailHandler(
            source_token=settings.BETTERSTACK_SOURCE_TOKEN,
            host=settings.BETTERSTACK_HOST,
        )
        betterstack_handler.setLevel(logging.INFO)

        root_logger = logging.getLogger()
        root_logger.addHandler(betterstack_handler)

        logger.info("BetterStack configured successfully")

    except ImportError:
        logger.warning(
            "logtail-python package not installed, skipping BetterStack setup. "
            "Install with: pip install logtail-python"
        )
    except Exception as e:
        logger.error(f"Failed to configure BetterStack: {e}")


def setup_logfire(app: FastAPI) -> None:
    """Configure Logfire for structured logging and tracing."""
    if not settings.LOGFIRE_TOKEN:
        logger.info("Logfire token not configured, skipping setup")
        return

    try:
        import logfire

        logfire.configure(
            token=settings.LOGFIRE_TOKEN,
            service_name="ai-pulse-backend",
            service_version="0.1.0",
            environment=settings.APP_ENV,
        )

        logfire.instrument_fastapi(app)
        logfire.instrument_httpx()

        try:
            logfire.instrument_redis()
        except Exception:
            pass

        logger.info("Logfire configured successfully")

    except ImportError:
        logger.warning("Logfire package not installed, skipping setup")
    except Exception as e:
        logger.error(f"Failed to configure Logfire: {e}")


def setup_sentry(app: FastAPI) -> None:
    """Configure Sentry for error tracking."""
    sentry_dsn = getattr(settings, 'SENTRY_DSN', None)
    if not sentry_dsn:
        logger.info("Sentry DSN not configured, skipping setup")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        logging_integration = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR
        )

        integrations = [
            FastApiIntegration(transaction_style="endpoint"),
            logging_integration,
        ]

        try:
            from sentry_sdk.integrations.redis import RedisIntegration
            integrations.append(RedisIntegration())
        except ImportError:
            pass

        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=settings.APP_ENV,
            release="ai-pulse@0.1.0",
            integrations=integrations,
            traces_sample_rate=0.1 if settings.is_production else 1.0,
            profiles_sample_rate=0.1 if settings.is_production else 0.5,
            send_default_pii=False,
            before_send=_filter_health_checks,
        )

        logger.info("Sentry configured successfully")

    except ImportError:
        logger.warning("Sentry SDK not installed, skipping setup")
    except Exception as e:
        logger.error(f"Failed to configure Sentry: {e}")


def _filter_health_checks(event, hint):
    """Filter out health check transactions from Sentry."""
    if event.get("transaction") in ["/health", "/api/health"]:
        return None
    return event


def setup_observability(app: FastAPI) -> None:
    """Set up all observability tools."""
    setup_betterstack()
    setup_logfire(app)
    setup_sentry(app)


# ============================================================================
# Logging Helpers for Business Metrics
# ============================================================================

def log_digest_sent(
    digest_id: str,
    recipient_count: int,
    duration_seconds: float,
    success: bool,
    error: Optional[str] = None
) -> None:
    """Log digest send metrics."""
    try:
        import logfire

        if success:
            logfire.info(
                "digest_sent",
                digest_id=digest_id,
                recipient_count=recipient_count,
                duration_seconds=duration_seconds,
            )
        else:
            logfire.error(
                "digest_send_failed",
                digest_id=digest_id,
                recipient_count=recipient_count,
                duration_seconds=duration_seconds,
                error=error,
            )
    except ImportError:
        if success:
            logger.info(f"Digest sent: {digest_id} to {recipient_count} recipients")
        else:
            logger.error(f"Digest send failed: {digest_id} - {error}")


def log_scraper_run(
    source_name: str,
    articles_found: int,
    duration_seconds: float,
    success: bool,
    error: Optional[str] = None
) -> None:
    """Log scraper run metrics."""
    try:
        import logfire

        if success:
            logfire.info(
                "scraper_completed",
                source_name=source_name,
                articles_found=articles_found,
                duration_seconds=duration_seconds,
            )
        else:
            logfire.warning(
                "scraper_failed",
                source_name=source_name,
                duration_seconds=duration_seconds,
                error=error,
            )
    except ImportError:
        if success:
            logger.info(f"Scraper completed: {source_name} - {articles_found} articles")
        else:
            logger.warning(f"Scraper failed: {source_name} - {error}")


def log_payment(
    user_id: str,
    amount_cents: int,
    currency: str,
    plan: str,
    success: bool,
    stripe_session_id: Optional[str] = None,
    error: Optional[str] = None
) -> None:
    """Log payment events."""
    try:
        import logfire

        if success:
            logfire.info(
                "payment_completed",
                user_id=user_id,
                amount_cents=amount_cents,
                currency=currency,
                plan=plan,
                stripe_session_id=stripe_session_id,
            )
        else:
            logfire.warning(
                "payment_failed",
                user_id=user_id,
                amount_cents=amount_cents,
                currency=currency,
                plan=plan,
                error=error,
            )
    except ImportError:
        if success:
            logger.info(f"Payment completed: {user_id} - {amount_cents} {currency}")
        else:
            logger.warning(f"Payment failed: {user_id} - {error}")
