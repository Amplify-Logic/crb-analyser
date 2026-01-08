"""
Observability configuration for CRB Analyser.
Integrates Logfire, Sentry, and BetterStack for logging/tracing and error tracking.

BetterStack provides:
- Centralized log aggregation with SQL querying
- Uptime monitoring
- Incident management
- Cost-effective alternative to Datadog (30x cheaper)

See docs/OBSERVABILITY.md for usage guide.
"""

import logging
from typing import Optional

from fastapi import FastAPI

from src.config.settings import settings

logger = logging.getLogger(__name__)


def setup_betterstack() -> None:
    """
    Configure BetterStack for centralized logging.

    BetterStack provides:
    - Centralized log aggregation
    - SQL-based log querying
    - Uptime monitoring
    - Alerting and incident management

    All Python logging will be forwarded to BetterStack when configured.
    """
    if not settings.BETTERSTACK_SOURCE_TOKEN:
        logger.info("BetterStack token not configured, skipping setup")
        return

    try:
        from logtail import LogtailHandler

        # Create the BetterStack handler
        betterstack_handler = LogtailHandler(
            source_token=settings.BETTERSTACK_SOURCE_TOKEN,
            host=settings.BETTERSTACK_HOST,
        )

        # Set format to include structured data
        betterstack_handler.setLevel(logging.INFO)

        # Add to root logger so all loggers forward to BetterStack
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
    """
    Configure Logfire for structured logging and tracing.

    Logfire provides:
    - Structured logging with context
    - Distributed tracing
    - FastAPI instrumentation
    - HTTP client instrumentation
    """
    if not settings.LOGFIRE_TOKEN:
        logger.info("Logfire token not configured, skipping setup")
        return

    try:
        import logfire

        logfire.configure(
            token=settings.LOGFIRE_TOKEN,
            service_name="crb-backend",
            service_version="0.1.0",
            environment=settings.APP_ENV,
        )

        # Instrument FastAPI
        logfire.instrument_fastapi(app)

        # Instrument HTTP clients
        logfire.instrument_httpx()

        # Instrument Redis if available
        try:
            logfire.instrument_redis()
        except Exception:
            pass  # Redis instrumentation optional

        logger.info("Logfire configured successfully")

    except ImportError:
        logger.warning("Logfire package not installed, skipping setup")
    except Exception as e:
        logger.error(f"Failed to configure Logfire: {e}")


def setup_sentry(app: FastAPI) -> None:
    """
    Configure Sentry for error tracking and performance monitoring.

    Sentry provides:
    - Error tracking with full context
    - Performance monitoring
    - Release tracking
    """
    sentry_dsn = getattr(settings, 'SENTRY_DSN', None)
    if not sentry_dsn:
        logger.info("Sentry DSN not configured, skipping setup")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        # Configure logging integration
        logging_integration = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR
        )

        # Try to add Redis integration if available
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
            release=f"crb-analyser@0.1.0",
            integrations=integrations,
            # Performance monitoring
            traces_sample_rate=0.1 if settings.is_production else 1.0,
            profiles_sample_rate=0.1 if settings.is_production else 0.5,
            # Privacy
            send_default_pii=False,
            # Filter out health checks
            before_send=_filter_health_checks,
        )

        logger.info("Sentry configured successfully")

    except ImportError:
        logger.warning("Sentry SDK not installed, skipping setup")
    except Exception as e:
        logger.error(f"Failed to configure Sentry: {e}")


def _filter_health_checks(event, hint):
    """Filter out health check transactions from Sentry."""
    if event.get("transaction") in ["/health", "/api/health", "/api/health/ready", "/api/health/live"]:
        return None
    return event


def setup_observability(app: FastAPI) -> None:
    """Set up all observability tools."""
    setup_betterstack()  # Set up logging first
    setup_logfire(app)
    setup_sentry(app)


# ============================================================================
# Logging Helpers for Business Metrics
# ============================================================================

def log_report_generation(
    report_id: str,
    quiz_session_id: str,
    duration_seconds: float,
    findings_count: int,
    recommendations_count: int,
    tier: str,
    success: bool,
    error: Optional[str] = None
) -> None:
    """Log report generation metrics."""
    try:
        import logfire

        if success:
            logfire.info(
                "report_generated",
                report_id=report_id,
                quiz_session_id=quiz_session_id,
                duration_seconds=duration_seconds,
                findings_count=findings_count,
                recommendations_count=recommendations_count,
                tier=tier,
            )
        else:
            logfire.error(
                "report_generation_failed",
                report_id=report_id,
                quiz_session_id=quiz_session_id,
                duration_seconds=duration_seconds,
                tier=tier,
                error=error,
            )
    except ImportError:
        # Fallback to standard logging
        if success:
            logger.info(f"Report generated: {report_id} in {duration_seconds:.2f}s")
        else:
            logger.error(f"Report generation failed: {report_id} - {error}")


def log_api_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
    operation: str
) -> None:
    """Log Claude API usage for cost tracking."""
    try:
        import logfire

        logfire.info(
            "claude_api_call",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            operation=operation,
        )
    except ImportError:
        logger.info(f"API call: {operation} - {input_tokens + output_tokens} tokens, ${cost_usd:.4f}")


def log_payment(
    quiz_session_id: str,
    amount_cents: int,
    tier: str,
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
                quiz_session_id=quiz_session_id,
                amount_cents=amount_cents,
                tier=tier,
                stripe_session_id=stripe_session_id,
            )
        else:
            logfire.warning(
                "payment_failed",
                quiz_session_id=quiz_session_id,
                amount_cents=amount_cents,
                tier=tier,
                error=error,
            )
    except ImportError:
        if success:
            logger.info(f"Payment completed: {quiz_session_id} - ${amount_cents/100:.2f}")
        else:
            logger.warning(f"Payment failed: {quiz_session_id} - {error}")
