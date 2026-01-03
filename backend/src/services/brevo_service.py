"""
Brevo (formerly Sendinblue) Email Marketing Service

Handles:
- Adding contacts after quiz completion
- Managing list memberships
- Triggering transactional emails
- Updating contact attributes

Docs: https://developers.brevo.com/reference/getting-started-1
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Optional

import httpx
from pydantic import BaseModel, EmailStr

from src.config.settings import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

BREVO_API_BASE = "https://api.brevo.com/v3"

# List IDs - Configure these in Brevo dashboard, then update here
class BrevoLists(int, Enum):
    """Brevo list IDs. Update these after creating lists in Brevo."""
    QUIZ_COMPLETERS = 1
    PAID_CUSTOMERS = 2
    # Industry-specific lists
    INDUSTRY_DENTAL = 10
    INDUSTRY_HOME_SERVICES = 11
    INDUSTRY_PROFESSIONAL = 12
    INDUSTRY_RECRUITING = 13
    INDUSTRY_COACHING = 14
    INDUSTRY_VETERINARY = 15


# Map industry slugs to list IDs
INDUSTRY_TO_LIST: dict[str, int] = {
    "dental": BrevoLists.INDUSTRY_DENTAL,
    "home-services": BrevoLists.INDUSTRY_HOME_SERVICES,
    "professional-services": BrevoLists.INDUSTRY_PROFESSIONAL,
    "recruiting": BrevoLists.INDUSTRY_RECRUITING,
    "coaching": BrevoLists.INDUSTRY_COACHING,
    "veterinary": BrevoLists.INDUSTRY_VETERINARY,
}


# =============================================================================
# Models
# =============================================================================

class QuizCompleterContact(BaseModel):
    """Data for a contact who completed the quiz."""
    email: EmailStr
    first_name: str
    company_name: str
    industry: str
    quiz_score: int
    ai_readiness_level: str  # "Low", "Medium", "High"
    report_id: str
    signup_source: str = "organic"  # "cold_email", "organic", "referral", "partner"


class ContactUpdateData(BaseModel):
    """Data for updating an existing contact."""
    email: EmailStr
    attributes: Optional[dict] = None
    list_ids_to_add: Optional[list[int]] = None
    list_ids_to_remove: Optional[list[int]] = None


class TransactionalEmailData(BaseModel):
    """Data for sending a transactional email."""
    to_email: EmailStr
    to_name: str
    template_id: int
    params: dict  # Template variables


# =============================================================================
# Service
# =============================================================================

class BrevoService:
    """
    Service for interacting with Brevo API.

    Usage:
        brevo = BrevoService()

        # Add quiz completer
        await brevo.add_quiz_completer(QuizCompleterContact(...))

        # Mark as paid customer
        await brevo.mark_as_paid_customer("user@example.com")

        # Send transactional email
        await brevo.send_transactional_email(TransactionalEmailData(...))
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.BREVO_API_KEY
        if not self.api_key:
            logger.warning("BREVO_API_KEY not set - Brevo service will be disabled")

        self.headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @property
    def is_configured(self) -> bool:
        """Check if Brevo is properly configured."""
        return bool(self.api_key)

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[dict] = None,
    ) -> dict:
        """Make authenticated request to Brevo API."""
        if not self.is_configured:
            logger.warning("Brevo not configured, skipping API call")
            return {"skipped": True}

        url = f"{BREVO_API_BASE}{endpoint}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=json_data,
                    timeout=30.0,
                )

                if response.status_code >= 400:
                    logger.error(
                        "brevo_api_error",
                        status=response.status_code,
                        endpoint=endpoint,
                        response=response.text,
                    )
                    response.raise_for_status()

                # Some endpoints return empty body on success
                if response.status_code == 204 or not response.text:
                    return {"success": True}

                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(
                    "brevo_request_failed",
                    endpoint=endpoint,
                    status=e.response.status_code,
                    error=str(e),
                )
                raise
            except Exception as e:
                logger.error(
                    "brevo_request_error",
                    endpoint=endpoint,
                    error=str(e),
                )
                raise

    # =========================================================================
    # Contact Management
    # =========================================================================

    async def add_quiz_completer(self, contact: QuizCompleterContact) -> dict:
        """
        Add or update a contact who completed the quiz.

        - Adds to quiz_completers list
        - Adds to industry-specific list
        - Sets all quiz-related attributes
        """
        # Determine industry list
        industry_list_id = INDUSTRY_TO_LIST.get(contact.industry.lower())
        list_ids = [BrevoLists.QUIZ_COMPLETERS]
        if industry_list_id:
            list_ids.append(industry_list_id)

        payload = {
            "email": contact.email,
            "attributes": {
                "FIRSTNAME": contact.first_name,
                "COMPANY_NAME": contact.company_name,
                "INDUSTRY": contact.industry,
                "QUIZ_SCORE": contact.quiz_score,
                "AI_READINESS_LEVEL": contact.ai_readiness_level,
                "REPORT_ID": contact.report_id,
                "SIGNUP_SOURCE": contact.signup_source,
                "SIGNUP_DATE": datetime.utcnow().isoformat(),
            },
            "listIds": list_ids,
            "updateEnabled": True,  # Update if contact exists
        }

        logger.info(
            "brevo_add_quiz_completer",
            email=contact.email,
            industry=contact.industry,
            score=contact.quiz_score,
        )

        return await self._request("POST", "/contacts", payload)

    async def get_contact(self, email: str) -> Optional[dict]:
        """Get contact details by email."""
        try:
            return await self._request("GET", f"/contacts/{email}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def update_contact(self, data: ContactUpdateData) -> dict:
        """
        Update an existing contact.

        - Update attributes
        - Add/remove from lists
        """
        payload = {}

        if data.attributes:
            payload["attributes"] = data.attributes

        if data.list_ids_to_add:
            payload["listIds"] = data.list_ids_to_add

        if data.list_ids_to_remove:
            payload["unlinkListIds"] = data.list_ids_to_remove

        logger.info(
            "brevo_update_contact",
            email=data.email,
            lists_add=data.list_ids_to_add,
            lists_remove=data.list_ids_to_remove,
        )

        return await self._request("PUT", f"/contacts/{data.email}", payload)

    async def mark_as_paid_customer(self, email: str) -> dict:
        """
        Move contact to paid_customers list.

        This triggers Brevo automation to stop upsell sequence.
        """
        payload = {
            "attributes": {
                "PAID_DATE": datetime.utcnow().isoformat(),
                "IS_PAID_CUSTOMER": True,
            },
            "listIds": [BrevoLists.PAID_CUSTOMERS],
        }

        logger.info("brevo_mark_paid_customer", email=email)

        return await self._request("PUT", f"/contacts/{email}", payload)

    async def delete_contact(self, email: str) -> dict:
        """
        Delete a contact (for GDPR compliance).
        """
        logger.info("brevo_delete_contact", email=email)
        return await self._request("DELETE", f"/contacts/{email}")

    # =========================================================================
    # List Management
    # =========================================================================

    async def get_lists(self) -> dict:
        """Get all contact lists."""
        return await self._request("GET", "/contacts/lists")

    async def add_to_list(self, list_id: int, emails: list[str]) -> dict:
        """Add contacts to a list."""
        payload = {"emails": emails}
        return await self._request("POST", f"/contacts/lists/{list_id}/contacts/add", payload)

    async def remove_from_list(self, list_id: int, emails: list[str]) -> dict:
        """Remove contacts from a list."""
        payload = {"emails": emails}
        return await self._request("POST", f"/contacts/lists/{list_id}/contacts/remove", payload)

    # =========================================================================
    # Transactional Emails
    # =========================================================================

    async def send_transactional_email(self, data: TransactionalEmailData) -> dict:
        """
        Send a transactional email using a Brevo template.

        Templates are created in Brevo dashboard.
        Use params to pass template variables.
        """
        payload = {
            "to": [{"email": data.to_email, "name": data.to_name}],
            "templateId": data.template_id,
            "params": data.params,
        }

        logger.info(
            "brevo_send_transactional",
            to=data.to_email,
            template_id=data.template_id,
        )

        return await self._request("POST", "/smtp/email", payload)

    async def send_report_delivered_email(
        self,
        email: str,
        first_name: str,
        company_name: str,
        quiz_score: int,
        industry_average: int,
        top_opportunity: str,
        report_link: str,
        template_id: int = 1,  # Set your template ID
    ) -> dict:
        """
        Convenience method to send the "Report Delivered" email.
        """
        return await self.send_transactional_email(
            TransactionalEmailData(
                to_email=email,
                to_name=first_name,
                template_id=template_id,
                params={
                    "first_name": first_name,
                    "company_name": company_name,
                    "quiz_score": quiz_score,
                    "industry_average": industry_average,
                    "top_opportunity": top_opportunity,
                    "report_link": report_link,
                },
            )
        )

    # =========================================================================
    # Campaign Stats (Optional - for monitoring)
    # =========================================================================

    async def get_email_stats(self, days: int = 7) -> dict:
        """Get aggregate email statistics."""
        return await self._request("GET", f"/smtp/statistics/aggregatedReport?days={days}")


# =============================================================================
# Factory Function
# =============================================================================

_brevo_service: Optional[BrevoService] = None


def get_brevo_service() -> BrevoService:
    """Get singleton Brevo service instance."""
    global _brevo_service
    if _brevo_service is None:
        _brevo_service = BrevoService()
    return _brevo_service


# =============================================================================
# FastAPI Dependency
# =============================================================================

async def get_brevo() -> BrevoService:
    """FastAPI dependency for Brevo service."""
    return get_brevo_service()
