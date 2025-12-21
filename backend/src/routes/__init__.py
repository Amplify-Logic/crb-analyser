"""
API Routes
"""

from .auth import router as auth_router
from .clients import router as clients_router
from .audits import router as audits_router
from .intake import router as intake_router
from .reports import router as reports_router
from .payments import router as payments_router
from .research import router as research_router
from .quiz import router as quiz_router
from .health import router as health_router
from .vendors import router as vendors_router
from .admin import router as admin_router
from .interview import router as interview_router
from .playbook import router as playbook_router
from .expertise import router as expertise_router
from .validation import router as validation_router

__all__ = [
    "auth_router",
    "clients_router",
    "audits_router",
    "intake_router",
    "reports_router",
    "payments_router",
    "research_router",
    "quiz_router",
    "health_router",
    "vendors_router",
    "admin_router",
    "interview_router",
    "playbook_router",
    "expertise_router",
    "validation_router",
]
