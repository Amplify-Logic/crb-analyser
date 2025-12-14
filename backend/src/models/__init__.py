"""
Pydantic Models
"""

from .auth import (
    SignupRequest,
    LoginRequest,
    AuthResponse,
    UserResponse,
    UserProfile,
    UpdateProfileRequest,
    ChangePasswordRequest,
    ResetPasswordRequest,
    GoogleAuthRequest,
)
from .client import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientListResponse,
    INDUSTRIES,
    COMPANY_SIZES,
)
from .audit import (
    AuditCreate,
    AuditUpdate,
    AuditResponse,
    AuditListResponse,
    AuditWithClient,
    AuditProgress,
    AUDIT_STATUSES,
    AUDIT_TIERS,
    ANALYSIS_PHASES,
)
from .intake import (
    IntakeResponse,
    IntakeUpdate,
    IntakeComplete,
    IntakeWithAudit,
    QuestionnaireResponse,
    IntakeValidationResult,
)

__all__ = [
    # Auth
    "SignupRequest",
    "LoginRequest",
    "AuthResponse",
    "UserResponse",
    "UserProfile",
    "UpdateProfileRequest",
    "ChangePasswordRequest",
    "ResetPasswordRequest",
    "GoogleAuthRequest",
    # Client
    "ClientCreate",
    "ClientUpdate",
    "ClientResponse",
    "ClientListResponse",
    "INDUSTRIES",
    "COMPANY_SIZES",
    # Audit
    "AuditCreate",
    "AuditUpdate",
    "AuditResponse",
    "AuditListResponse",
    "AuditWithClient",
    "AuditProgress",
    "AUDIT_STATUSES",
    "AUDIT_TIERS",
    "ANALYSIS_PHASES",
    # Intake
    "IntakeResponse",
    "IntakeUpdate",
    "IntakeComplete",
    "IntakeWithAudit",
    "QuestionnaireResponse",
    "IntakeValidationResult",
]
