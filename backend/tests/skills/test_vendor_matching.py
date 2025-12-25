"""
Tests for Vendor Matching Skill
"""

import pytest
from unittest.mock import MagicMock

from src.skills import get_skill, SkillContext
from src.skills.analysis.vendor_matching import (
    VendorMatchingSkill,
    CATEGORY_KEYWORDS,
    SIZE_MAPPING,
)


class TestVendorMatchingSkill:
    """Tests for the VendorMatchingSkill."""

    def test_skill_discovery(self):
        """Test that the skill can be discovered by name."""
        from src.skills import registry
        registry._registry = None

        skill = get_skill("vendor-matching")
        assert skill is not None
        assert skill.name == "vendor-matching"

    def test_skill_metadata(self):
        """Test skill metadata is correct."""
        skill = VendorMatchingSkill()
        assert skill.name == "vendor-matching"
        assert skill.description == "Match findings to specific vendor solutions"
        assert skill.version == "1.0.0"
        assert skill.requires_llm is True
        assert skill.requires_knowledge is True

    def test_category_keywords_defined(self):
        """Test category keywords are properly defined."""
        assert "automation" in CATEGORY_KEYWORDS
        assert "crm" in CATEGORY_KEYWORDS
        assert "scheduling" in CATEGORY_KEYWORDS
        assert "customer_support" in CATEGORY_KEYWORDS

        # Check keywords are lists
        for category, keywords in CATEGORY_KEYWORDS.items():
            assert isinstance(keywords, list)
            assert len(keywords) > 0

    def test_size_mapping_defined(self):
        """Test company size mapping."""
        assert SIZE_MAPPING["1-10"] == "startup"
        assert SIZE_MAPPING["11-50"] == "smb"
        assert SIZE_MAPPING["51-200"] == "mid-market"
        assert SIZE_MAPPING["500+"] == "enterprise"

    def test_detect_category_automation(self):
        """Test category detection for automation findings."""
        skill = VendorMatchingSkill()

        finding = {
            "title": "Manual workflow processes",
            "description": "Staff spends hours manually transferring data between systems. Need to automate integration.",
        }

        category = skill._detect_category(finding)
        assert category == "automation"

    def test_detect_category_scheduling(self):
        """Test category detection for scheduling findings."""
        skill = VendorMatchingSkill()

        finding = {
            "title": "Inefficient appointment scheduling",
            "description": "Phone-based booking wastes staff time. Need online calendar booking system.",
        }

        category = skill._detect_category(finding)
        assert category == "scheduling"

    def test_detect_category_crm(self):
        """Test category detection for CRM findings."""
        skill = VendorMatchingSkill()

        finding = {
            "title": "No centralized customer tracking",
            "description": "Sales team lacks CRM system. Leads fall through cracks. Need salesforce alternative.",
        }

        category = skill._detect_category(finding)
        assert category == "crm"

    def test_detect_category_support(self):
        """Test category detection for support findings."""
        skill = VendorMatchingSkill()

        finding = {
            "title": "Customer support bottleneck",
            "description": "Support tickets pile up. Need helpdesk and chatbot solution.",
        }

        category = skill._detect_category(finding)
        assert category == "customer_support"

    def test_detect_category_unknown(self):
        """Test category detection returns None for unclear findings."""
        skill = VendorMatchingSkill()

        finding = {
            "title": "Generic business issue",
            "description": "Something is wrong with the business.",
        }

        category = skill._detect_category(finding)
        assert category is None

    def test_score_vendors_size_fit(self):
        """Test vendor scoring includes size fit."""
        skill = VendorMatchingSkill()

        vendors = [
            {
                "name": "Startup Tool",
                "slug": "startup-tool",
                "company_sizes": ["startup", "smb"],
                "ratings": {"our_rating": 4.5},
                "implementation": {"complexity": "low"},
                "pricing": {"free_tier": True},
            },
            {
                "name": "Enterprise Tool",
                "slug": "enterprise-tool",
                "company_sizes": ["enterprise"],
                "ratings": {"our_rating": 4.0},
                "implementation": {"complexity": "high"},
                "pricing": {"free_tier": False},
            },
        ]

        finding = {"title": "Test"}
        company_context = {"employee_count": "11-50"}  # SMB

        scored = skill._score_vendors(vendors, finding, company_context)

        # Startup Tool should score higher for SMB
        assert scored[0]["slug"] == "startup-tool"
        assert scored[0]["_fit_score"] > scored[1]["_fit_score"]

    def test_score_vendors_rating_impact(self):
        """Test vendor scoring considers ratings."""
        skill = VendorMatchingSkill()

        vendors = [
            {
                "name": "Highly Rated",
                "slug": "high-rated",
                "company_sizes": ["smb"],
                "ratings": {"our_rating": 4.8, "g2": {"score": 4.7, "reviews": 500}},
                "implementation": {"complexity": "medium"},
                "pricing": {},
            },
            {
                "name": "Low Rated",
                "slug": "low-rated",
                "company_sizes": ["smb"],
                "ratings": {"our_rating": 3.5},
                "implementation": {"complexity": "medium"},
                "pricing": {},
            },
        ]

        finding = {"title": "Test"}
        company_context = {"employee_count": "11-50"}

        scored = skill._score_vendors(vendors, finding, company_context)

        assert scored[0]["slug"] == "high-rated"
        assert "Highly rated" in scored[0]["_fit_reasons"]

    def test_score_vendors_implementation_complexity(self):
        """Test vendor scoring considers implementation complexity."""
        skill = VendorMatchingSkill()

        vendors = [
            {
                "name": "Easy Setup",
                "slug": "easy",
                "company_sizes": ["smb"],
                "ratings": {"our_rating": 4.0},
                "implementation": {"complexity": "low"},
                "pricing": {},
            },
            {
                "name": "Complex Setup",
                "slug": "complex",
                "company_sizes": ["smb"],
                "ratings": {"our_rating": 4.0},
                "implementation": {"complexity": "high"},
                "pricing": {},
            },
        ]

        finding = {"title": "Test"}
        company_context = {"employee_count": 25}  # Integer size

        scored = skill._score_vendors(vendors, finding, company_context)

        # Easy setup should score higher
        easy = next(v for v in scored if v["slug"] == "easy")
        complex_v = next(v for v in scored if v["slug"] == "complex")

        assert easy["_fit_score"] > complex_v["_fit_score"]
        assert "Easy to implement" in easy["_fit_reasons"]

    def test_format_vendor_output(self):
        """Test vendor formatting for output."""
        skill = VendorMatchingSkill()

        vendor = {
            "name": "TestVendor",
            "slug": "test-vendor",
            "pricing": {
                "starting_price": 0,
                "tiers": [
                    {"name": "Free", "price": 0, "features": ["Basic"]},
                    {"name": "Pro", "price": 29, "features": ["Advanced", "Support"]},
                ]
            },
            "implementation": {
                "avg_weeks": 2,
                "cost_range": {
                    "with_help": {"min": 500, "max": 1500}
                }
            },
            "_fit_score": 85,
            "_fit_reasons": ["Easy setup"],
            "_limitations": [],
        }

        formatted = skill._format_vendor(vendor)

        assert formatted["vendor"] == "TestVendor"
        assert formatted["slug"] == "test-vendor"
        assert formatted["monthly_cost"] == 29  # Pro tier
        assert formatted["implementation_cost"] == 1000  # Average of 500-1500
        assert formatted["implementation_weeks"] == 2
        assert formatted["fit_score"] == 85
        assert "Easy setup" in formatted["fit_reasons"]

    def test_select_tier_matches(self):
        """Test tier selection logic."""
        skill = VendorMatchingSkill()

        vendors = [
            {
                "name": "Budget Option",
                "slug": "budget",
                "_fit_score": 80,
                "_tier_recommendation": "off_the_shelf",
                "_fit_reasons": [],
                "_limitations": [],
                "pricing": {"starting_price": 10, "tiers": []},
                "implementation": {"avg_weeks": 1},
            },
            {
                "name": "Premium Option",
                "slug": "premium",
                "_fit_score": 75,
                "_tier_recommendation": "best_in_class",
                "_fit_reasons": [],
                "_limitations": [],
                "pricing": {"starting_price": 50, "tiers": []},
                "implementation": {"avg_weeks": 2},
            },
        ]

        finding = {"id": "finding-001", "title": "Test finding"}
        result = skill._select_tier_matches(vendors, finding)

        assert result["finding_id"] == "finding-001"
        assert result["off_the_shelf"]["vendor"] == "Budget Option"
        assert result["best_in_class"]["vendor"] == "Premium Option"
        assert result["match_confidence"] == "high"  # score >= 75

    @pytest.mark.asyncio
    async def test_skill_execution_success(self):
        """Test successful skill execution with mocked LLM."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{
            "matches": [
                {"slug": "zapier", "adjusted_score": 90, "tier_recommendation": "off_the_shelf", "reasoning": "Great for SMB automation"}
            ]
        }''')]
        mock_client.messages.create.return_value = mock_response

        skill = VendorMatchingSkill(client=mock_client)

        context = SkillContext(
            industry="dental",
            metadata={
                "finding": {
                    "id": "finding-001",
                    "title": "Manual data entry between systems",
                    "description": "Staff manually copies patient data. Need workflow automation.",
                },
                "company_context": {
                    "employee_count": 15,
                },
            }
        )

        result = await skill.run(context)

        assert result.success is True
        assert "finding_id" in result.data
        assert "off_the_shelf" in result.data or "best_in_class" in result.data
        assert "match_confidence" in result.data

    @pytest.mark.asyncio
    async def test_skill_requires_finding(self):
        """Test skill fails without finding."""
        from src.skills.base import SkillError

        mock_client = MagicMock()
        skill = VendorMatchingSkill(client=mock_client)

        context = SkillContext(
            industry="dental",
            metadata={
                # No finding
                "company_context": {},
            }
        )

        with pytest.raises(SkillError) as exc_info:
            await skill.execute(context)

        assert "finding" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_skill_handles_no_vendors(self):
        """Test skill handles case with no matching vendors."""
        mock_client = MagicMock()
        # LLM won't be called if no vendors
        skill = VendorMatchingSkill(client=mock_client)

        context = SkillContext(
            industry="unknown-industry",
            metadata={
                "finding": {
                    "id": "finding-001",
                    "title": "Very specific obscure requirement",
                    "description": "Something with no vendor matches",
                },
                "company_context": {},
            }
        )

        result = await skill.run(context)

        assert result.success is True
        # Should still return structure even if no vendors matched
        assert "match_confidence" in result.data


class TestVendorMatchingIntegration:
    """Integration tests for vendor matching."""

    def test_skill_without_client(self):
        """Test skill can be created without client."""
        skill = VendorMatchingSkill()
        assert skill.requires_llm is True

    @pytest.mark.asyncio
    async def test_automation_finding_matches_automation_vendors(self):
        """Test automation finding matches automation vendors."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{
            "matches": [
                {"slug": "zapier", "adjusted_score": 85, "tier_recommendation": "off_the_shelf", "reasoning": "Easy automation"},
                {"slug": "make", "adjusted_score": 80, "tier_recommendation": "best_in_class", "reasoning": "More powerful"}
            ]
        }''')]
        mock_client.messages.create.return_value = mock_response

        skill = VendorMatchingSkill(client=mock_client)

        context = SkillContext(
            industry="home-services",
            metadata={
                "finding": {
                    "id": "finding-001",
                    "title": "Manual workflow between job scheduling and invoicing",
                    "description": "Technicians finish jobs but invoices aren't automatically created. Need to automate the workflow integration.",
                },
                "company_context": {
                    "employee_count": 20,
                },
            }
        )

        result = await skill.run(context)

        assert result.success is True
        assert result.data["category"] == "automation"

    @pytest.mark.asyncio
    async def test_scheduling_finding_detection(self):
        """Test scheduling finding is correctly categorized."""
        skill = VendorMatchingSkill()

        finding = {
            "id": "finding-001",
            "title": "Phone-based appointment booking",
            "description": "All appointments are scheduled via phone. Patients want online booking.",
        }

        category = skill._detect_category(finding)
        assert category == "scheduling"
