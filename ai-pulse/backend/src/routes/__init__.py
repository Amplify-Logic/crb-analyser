"""Routes module for AI Pulse."""

from .auth import router as auth_router
from .articles import router as articles_router
from .digests import router as digests_router
from .checkout import router as checkout_router
from .webhooks import router as webhooks_router
from .sources import router as sources_router
from .admin import router as admin_router

__all__ = [
    "auth_router",
    "articles_router",
    "digests_router",
    "checkout_router",
    "webhooks_router",
    "sources_router",
    "admin_router",
]
