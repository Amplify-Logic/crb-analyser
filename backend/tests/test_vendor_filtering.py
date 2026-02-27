"""Tests for industry-aware vendor filtering."""

import pytest
from src.skills.report_generation_utils import (
    load_kb_vendors_for_finding,
    _is_vendor_relevant_for_industry,
)


class TestVendorRelevanceFilter:
    """Unit tests for the _is_vendor_relevant_for_industry function."""

    def test_lawmatics_excluded_for_professional_services(self):
        assert _is_vendor_relevant_for_industry("Lawmatics", "professional-services") is False

    def test_lawmatics_allowed_for_legal(self):
        assert _is_vendor_relevant_for_industry("Lawmatics", "legal") is True

    def test_deepgram_excluded_for_professional_services(self):
        assert _is_vendor_relevant_for_industry("Deepgram", "professional-services") is False

    def test_apify_excluded_for_professional_services(self):
        assert _is_vendor_relevant_for_industry("Apify", "professional-services") is False

    def test_generic_vendor_allowed_for_professional_services(self):
        assert _is_vendor_relevant_for_industry("HubSpot", "professional-services") is True

    def test_dental_vendor_excluded_for_ecommerce(self):
        assert _is_vendor_relevant_for_industry("Dentrix", "ecommerce") is False

    def test_dental_vendor_allowed_for_dental(self):
        assert _is_vendor_relevant_for_industry("Dentrix", "dental") is True

    def test_ecommerce_vendor_excluded_for_dental(self):
        assert _is_vendor_relevant_for_industry("Gorgias", "dental") is False


class TestVendorFilterIntegration:
    """Integration tests using context_vendors to verify filtering."""

    def test_excluded_vendor_filtered_from_context(self):
        """Lawmatics passed as context_vendor should be filtered out for accounting."""
        finding = {
            "id": "finding-001",
            "title": "CRM Improvement",
            "description": "Need better CRM",
            "category": "customer_experience",
        }
        context_vendors = [
            {"name": "Lawmatics", "category": "crm", "description": "Legal CRM"},
            {"name": "HubSpot", "category": "crm", "description": "General CRM"},
        ]
        vendors = load_kb_vendors_for_finding(
            finding=finding,
            industry="professional-services",
            context_vendors=context_vendors,
        )
        vendor_names = [v.get("name", "").lower() for v in vendors]
        assert "lawmatics" not in vendor_names
        assert "hubspot" in vendor_names


class TestVendorIndustryFiltering:
    def test_legal_vendor_excluded_for_accounting(self):
        """Lawmatics (legal CRM) should not appear for accounting industry."""
        finding = {
            "id": "finding-001",
            "title": "Client Relationship Management",
            "description": "Need better CRM for client follow-up",
            "category": "customer_experience",
        }
        vendors = load_kb_vendors_for_finding(
            finding=finding,
            industry="professional-services",
        )
        vendor_names = [v.get("name", "").lower() for v in vendors]
        assert "lawmatics" not in vendor_names, "Legal CRM should not appear for accounting"

    def test_audio_vendor_excluded_for_accounting(self):
        """Deepgram (audio transcription) should not appear for accounting."""
        finding = {
            "id": "finding-002",
            "title": "Document Processing Automation",
            "description": "Automate document collection and processing",
            "category": "operations",
        }
        vendors = load_kb_vendors_for_finding(
            finding=finding,
            industry="professional-services",
        )
        vendor_names = [v.get("name", "").lower() for v in vendors]
        assert "deepgram" not in vendor_names, "Audio transcription vendor irrelevant for accounting"

    def test_scraping_vendor_excluded_for_accounting(self):
        """Apify (web scraping) should not appear for accounting."""
        finding = {
            "id": "finding-003",
            "title": "Regulatory Compliance Monitoring",
            "description": "Monitor regulatory changes automatically",
            "category": "compliance",
        }
        vendors = load_kb_vendors_for_finding(
            finding=finding,
            industry="professional-services",
        )
        vendor_names = [v.get("name", "").lower() for v in vendors]
        assert "apify" not in vendor_names, "Web scraping vendor irrelevant for accounting"
