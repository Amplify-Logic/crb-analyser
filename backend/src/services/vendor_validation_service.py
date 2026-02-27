"""
Vendor Validation Service

Validates that vendor recommendations from LLM output exist in the knowledge base.
Flags unverified vendors and optionally suggests alternatives from the KB.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from src.knowledge import (
    get_all_vendors,
    get_vendor_by_slug,
    load_industry_data,
    get_vendor_recommendations,
    VENDOR_CATEGORIES,
)

logger = logging.getLogger(__name__)


@dataclass
class VendorMatch:
    """Result of vendor lookup."""
    found: bool
    vendor_name: str
    matched_vendor: Optional[Dict[str, Any]] = None
    match_type: str = "none"  # "exact_slug", "exact_name", "fuzzy_name", "none"
    confidence: float = 0.0


@dataclass
class ValidationResult:
    """Result of validating a recommendation's vendors."""
    is_valid: bool
    off_the_shelf_match: Optional[VendorMatch] = None
    best_in_class_match: Optional[VendorMatch] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class VendorValidationService:
    """
    Validates vendor recommendations against the knowledge base.

    Usage:
        validator = VendorValidationService(industry="dental")
        result = validator.validate_recommendation(llm_output)
        validated_rec = validator.apply_validation(llm_output, result)
    """

    def __init__(self, industry: Optional[str] = None):
        """
        Initialize with optional industry context.

        Args:
            industry: Industry slug for industry-specific vendor lookup
        """
        self.industry = industry
        self._vendor_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._industry_vendor_cache: Optional[Dict[str, Dict[str, Any]]] = None

    def _build_vendor_cache(self) -> Dict[str, Dict[str, Any]]:
        """Build lookup cache of all vendors by name and slug."""
        if self._vendor_cache is not None:
            return self._vendor_cache

        self._vendor_cache = {}

        # Load category vendors (CRM, automation, etc.)
        all_vendors = get_all_vendors()
        for vendor in all_vendors:
            slug = vendor.get("slug", "").lower()
            name = vendor.get("name", "").lower()

            if slug:
                self._vendor_cache[slug] = vendor
            if name:
                self._vendor_cache[name] = vendor
                # Also add normalized version (no spaces, lowercase)
                normalized = name.replace(" ", "-").replace(".", "")
                self._vendor_cache[normalized] = vendor

        return self._vendor_cache

    def _build_industry_vendor_cache(self) -> Dict[str, Dict[str, Any]]:
        """Build lookup cache of industry-specific vendors."""
        if self._industry_vendor_cache is not None:
            return self._industry_vendor_cache

        self._industry_vendor_cache = {}

        if not self.industry:
            return self._industry_vendor_cache

        # Load industry-specific vendors
        industry_vendors = get_vendor_recommendations(self.industry)
        for vendor in industry_vendors:
            slug = vendor.get("slug", "").lower() if vendor.get("slug") else ""
            name = vendor.get("name", "").lower()

            if slug:
                self._industry_vendor_cache[slug] = vendor
            if name:
                self._industry_vendor_cache[name] = vendor
                # Normalized version
                normalized = name.replace(" ", "-").replace(".", "")
                self._industry_vendor_cache[normalized] = vendor

        return self._industry_vendor_cache

    def lookup_vendor(self, vendor_name: str) -> VendorMatch:
        """
        Look up a vendor by name or slug.

        Args:
            vendor_name: Vendor name or slug from LLM output

        Returns:
            VendorMatch with lookup results
        """
        if not vendor_name:
            return VendorMatch(found=False, vendor_name="", match_type="none")

        name_lower = vendor_name.lower().strip()
        normalized = name_lower.replace(" ", "-").replace(".", "")

        # Try industry-specific vendors first (higher priority)
        industry_cache = self._build_industry_vendor_cache()

        # Exact match in industry vendors
        if name_lower in industry_cache:
            return VendorMatch(
                found=True,
                vendor_name=vendor_name,
                matched_vendor=industry_cache[name_lower],
                match_type="exact_name",
                confidence=1.0
            )
        if normalized in industry_cache:
            return VendorMatch(
                found=True,
                vendor_name=vendor_name,
                matched_vendor=industry_cache[normalized],
                match_type="exact_slug",
                confidence=1.0
            )

        # Try category vendors
        category_cache = self._build_vendor_cache()

        if name_lower in category_cache:
            return VendorMatch(
                found=True,
                vendor_name=vendor_name,
                matched_vendor=category_cache[name_lower],
                match_type="exact_name",
                confidence=1.0
            )
        if normalized in category_cache:
            return VendorMatch(
                found=True,
                vendor_name=vendor_name,
                matched_vendor=category_cache[normalized],
                match_type="exact_slug",
                confidence=1.0
            )

        # Try fuzzy matching (contains)
        for key, vendor in {**industry_cache, **category_cache}.items():
            if name_lower in key or key in name_lower:
                return VendorMatch(
                    found=True,
                    vendor_name=vendor_name,
                    matched_vendor=vendor,
                    match_type="fuzzy_name",
                    confidence=0.7
                )

        # Not found
        return VendorMatch(
            found=False,
            vendor_name=vendor_name,
            match_type="none",
            confidence=0.0
        )

    def validate_recommendation(self, recommendation: Dict[str, Any]) -> ValidationResult:
        """
        Validate vendors in a recommendation.

        Args:
            recommendation: LLM-generated recommendation with options

        Returns:
            ValidationResult with match info and warnings
        """
        warnings = []
        options = recommendation.get("options", {})

        def _extract_vendor(option: Dict) -> str:
            """Extract vendor name from option dict (supports both legacy and AIOS formats)."""
            # AIOS format: matched_vendor dict with vendor/name
            mv = option.get("matched_vendor", {})
            if isinstance(mv, dict):
                v = mv.get("vendor", "") or mv.get("name", "")
                if v:
                    return v
            # Legacy format: vendor or name at top level
            return option.get("vendor", "") or option.get("name", "")

        # Support both legacy keys and AIOS keys
        # Legacy: off_the_shelf / best_in_class
        # AIOS: targeted_upgrade / enhance_with_ai
        ots = options.get("off_the_shelf", {}) or options.get("targeted_upgrade", {})
        ots_vendor = _extract_vendor(ots)
        ots_match = self.lookup_vendor(ots_vendor)

        if ots_vendor and not ots_match.found:
            warnings.append(f"Off-the-shelf vendor '{ots_vendor}' not in knowledge base")
        elif ots_match.match_type == "fuzzy_name":
            warnings.append(f"Off-the-shelf vendor '{ots_vendor}' matched via fuzzy match")

        # Validate best_in_class / enhance_with_ai
        bic = options.get("best_in_class", {}) or options.get("enhance_with_ai", {})
        bic_vendor = _extract_vendor(bic)
        bic_match = self.lookup_vendor(bic_vendor)

        if bic_vendor and not bic_match.found:
            warnings.append(f"Best-in-class vendor '{bic_vendor}' not in knowledge base")
        elif bic_match.match_type == "fuzzy_name":
            warnings.append(f"Best-in-class vendor '{bic_vendor}' matched via fuzzy match")

        # Overall validity - valid if we have no vendor warnings or if vendors matched
        is_valid = (not ots_vendor or ots_match.found) and (not bic_vendor or bic_match.found)

        return ValidationResult(
            is_valid=is_valid,
            off_the_shelf_match=ots_match,
            best_in_class_match=bic_match,
            warnings=warnings
        )

    def apply_validation(
        self,
        recommendation: Dict[str, Any],
        validation: ValidationResult
    ) -> Dict[str, Any]:
        """
        Apply validation results to recommendation.

        Adds verification flags to each option.

        Args:
            recommendation: Original recommendation
            validation: Validation results

        Returns:
            Recommendation with validation metadata
        """
        options = recommendation.get("options", {})

        # Add validation metadata to off_the_shelf
        if "off_the_shelf" in options:
            ots = options["off_the_shelf"]
            match = validation.off_the_shelf_match

            ots["vendor_verified"] = match.found if match else False
            ots["vendor_match_type"] = match.match_type if match else "none"
            ots["vendor_confidence"] = match.confidence if match else 0.0

            # Enrich with KB data if matched
            if match and match.found and match.matched_vendor:
                kb_vendor = match.matched_vendor
                # Add KB pricing if available and LLM price seems off
                kb_pricing = self._extract_kb_pricing(kb_vendor)
                if kb_pricing:
                    ots["kb_monthly_price"] = kb_pricing.get("monthly")
                    ots["kb_pricing_verified"] = kb_pricing.get("verified_date")

        # Add validation metadata to best_in_class
        if "best_in_class" in options:
            bic = options["best_in_class"]
            match = validation.best_in_class_match

            bic["vendor_verified"] = match.found if match else False
            bic["vendor_match_type"] = match.match_type if match else "none"
            bic["vendor_confidence"] = match.confidence if match else 0.0

            # Enrich with KB data if matched
            if match and match.found and match.matched_vendor:
                kb_vendor = match.matched_vendor
                kb_pricing = self._extract_kb_pricing(kb_vendor)
                if kb_pricing:
                    bic["kb_monthly_price"] = kb_pricing.get("monthly")
                    bic["kb_pricing_verified"] = kb_pricing.get("verified_date")

        # Custom solutions don't need vendor validation
        if "custom_solution" in options:
            options["custom_solution"]["vendor_verified"] = True  # N/A for custom
            options["custom_solution"]["vendor_match_type"] = "not_applicable"

        # Add overall validation status
        recommendation["vendor_validation"] = {
            "all_verified": validation.is_valid,
            "warnings": validation.warnings,
            "validated_at": "runtime"
        }

        return recommendation

    def _extract_kb_pricing(self, vendor: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract monthly pricing from KB vendor data."""
        pricing = vendor.get("pricing", {})

        # Handle different pricing structures

        # Structure 1: tiers array (category vendors like CRM)
        tiers = pricing.get("tiers", [])
        if tiers:
            # Find a reasonable starting tier (not free, not enterprise)
            for tier in tiers:
                price = tier.get("price")
                if price and price > 0:
                    return {
                        "monthly": price,
                        "tier_name": tier.get("name"),
                        "verified_date": vendor.get("verified_at", vendor.get("pricing_verified_date"))
                    }

        # Structure 2: named pricing tiers (industry vendors)
        for tier_name in ["standard", "essentials", "basic", "starter", "core", "hero"]:
            tier = pricing.get(tier_name, {})
            if isinstance(tier, dict) and tier.get("price"):
                price = tier.get("price")
                if isinstance(price, (int, float)):
                    return {
                        "monthly": price,
                        "tier_name": tier_name,
                        "verified_date": vendor.get("pricing_verified_date")
                    }

        # Structure 3: starting_price
        starting = pricing.get("starting_price")
        if starting and isinstance(starting, (int, float)):
            return {
                "monthly": starting,
                "tier_name": "starting",
                "verified_date": vendor.get("verified_at")
            }

        return None

    def suggest_alternatives(
        self,
        unverified_vendor: str,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Suggest alternative vendors from KB when LLM vendor isn't found.

        Args:
            unverified_vendor: Name of vendor not in KB
            category: Optional category to filter suggestions

        Returns:
            List of suggested vendors from KB
        """
        suggestions = []

        # Get industry vendors first
        if self.industry:
            industry_vendors = get_vendor_recommendations(self.industry, category)
            suggestions.extend(industry_vendors[:3])

        # If not enough, add category vendors
        if len(suggestions) < 3:
            all_vendors = get_all_vendors()
            for vendor in all_vendors:
                if len(suggestions) >= 5:
                    break
                # Avoid duplicates
                if vendor not in suggestions:
                    suggestions.append(vendor)

        return suggestions[:5]


def validate_recommendation(
    recommendation: Dict[str, Any],
    industry: Optional[str] = None
) -> Tuple[Dict[str, Any], ValidationResult]:
    """
    Convenience function to validate and apply in one call.

    Args:
        recommendation: LLM-generated recommendation
        industry: Optional industry for context

    Returns:
        Tuple of (validated_recommendation, validation_result)
    """
    validator = VendorValidationService(industry=industry)
    result = validator.validate_recommendation(recommendation)
    validated = validator.apply_validation(recommendation, result)
    return validated, result


def validate_all_recommendations(
    recommendations: List[Dict[str, Any]],
    industry: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Validate a list of recommendations.

    Args:
        recommendations: List of LLM-generated recommendations
        industry: Optional industry for context

    Returns:
        Tuple of (validated_recommendations, all_warnings)
    """
    validator = VendorValidationService(industry=industry)
    validated = []
    all_warnings = []

    for rec in recommendations:
        result = validator.validate_recommendation(rec)
        validated_rec = validator.apply_validation(rec, result)
        validated.append(validated_rec)
        all_warnings.extend(result.warnings)

    # Log summary
    unverified_count = sum(
        1 for w in all_warnings
        if "not in knowledge base" in w
    )
    if unverified_count > 0:
        logger.warning(
            f"Vendor validation: {unverified_count} vendors not in knowledge base",
            extra={"warnings": all_warnings}
        )

    return validated, all_warnings
