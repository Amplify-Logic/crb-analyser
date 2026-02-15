"""
Quality Validator Service

Post-generation content quality checks for CRB reports.
Catches issues that structural/math validators miss:
- Banned buzzwords ("streamline", "leverage", etc.)
- Confidence distribution enforcement (30/50/20 target)
- User data quoting in findings
- Source citation presence
- ROI stuck at zero
- Vendor existence in knowledge base

Usage:
    from src.services.quality_validator import QualityValidator

    result = QualityValidator.validate(report_data)
    if not result.passed:
        logger.warning(f"Quality issues: {result.error_count} errors, {result.warning_count} warnings")
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


# =============================================================================
# Data Types
# =============================================================================


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class QualityIssue:
    """A single quality issue found in the report."""
    check: str
    severity: Severity
    location: str
    detail: str


@dataclass
class QualityResult:
    """Result of all quality checks."""
    issues: List[QualityIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.error_count == 0

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues": [
                {
                    "check": i.check,
                    "severity": i.severity.value,
                    "location": i.location,
                    "detail": i.detail,
                }
                for i in self.issues
            ],
        }


# =============================================================================
# Banned Phrases
# =============================================================================

BANNED_PHRASES = [
    "streamline",
    "leverage",
    "enhance efficiency",
    "transform your business",
    "unlock potential",
    "unlock value",
    "optimize workflows",
    "drive growth",
    "drive efficiency",
    "seamless integration",
    "seamless",
    "robust",
    "scalable",
    "enterprise-grade",
    "cutting-edge",
    "best-in-class solution",
    "empower",
    "synergy",
    "paradigm",
    "holistic approach",
    "game-changer",
    "next-generation",
    "world-class",
    "turnkey solution",
]

# Pre-compile patterns for performance
_BANNED_PATTERNS = [
    re.compile(re.escape(phrase), re.IGNORECASE)
    for phrase in BANNED_PHRASES
]


# =============================================================================
# User Data Reference Patterns
# =============================================================================

_USER_DATA_PATTERNS = [
    re.compile(r"based on your answer", re.IGNORECASE),
    re.compile(r"you mentioned", re.IGNORECASE),
    re.compile(r"you told us", re.IGNORECASE),
    re.compile(r"your response", re.IGNORECASE),
    re.compile(r"quiz q\d+", re.IGNORECASE),
    re.compile(r"you (said|indicated|reported|noted)", re.IGNORECASE),
    re.compile(r"according to your", re.IGNORECASE),
    re.compile(r"from your quiz", re.IGNORECASE),
    re.compile(r"your current", re.IGNORECASE),
    re.compile(r"your team", re.IGNORECASE),
    re.compile(r"your practice", re.IGNORECASE),
    re.compile(r"your business", re.IGNORECASE),
    re.compile(r"your staff", re.IGNORECASE),
    re.compile(r"you spend", re.IGNORECASE),
    re.compile(r"you currently", re.IGNORECASE),
]


# =============================================================================
# Confidence Distribution Targets
# =============================================================================

CONFIDENCE_TARGETS = {
    "high": (0.15, 0.40),    # 15-40%
    "medium": (0.35, 0.65),  # 35-65%
    "low": (0.05, 0.35),     # 5-35%
}

MIN_FINDINGS_FOR_DISTRIBUTION = 5


# =============================================================================
# Quality Validator
# =============================================================================


class QualityValidator:
    """
    Validates report content quality post-generation.

    All methods are classmethods returning lists of QualityIssue.
    Use validate() for the full suite.
    """

    @classmethod
    def validate(cls, report_data: Dict[str, Any]) -> QualityResult:
        """Run all quality checks and return combined result."""
        issues: List[QualityIssue] = []

        issues.extend(cls.check_buzzwords(report_data))
        issues.extend(cls.check_confidence_distribution(report_data))
        issues.extend(cls.check_user_data_quoting(report_data))
        issues.extend(cls.check_source_citations(report_data))
        issues.extend(cls.check_roi_values(report_data))
        issues.extend(cls.check_vendor_existence(report_data))

        result = QualityResult(issues=issues)

        if issues:
            logger.info(
                "quality_validation_complete",
                extra={
                    "error_count": result.error_count,
                    "warning_count": result.warning_count,
                    "checks": list({i.check for i in issues}),
                },
            )

        return result

    # -----------------------------------------------------------------
    # Check: Banned Buzzwords
    # -----------------------------------------------------------------

    @classmethod
    def check_buzzwords(cls, report_data: Dict[str, Any]) -> List[QualityIssue]:
        """Scan all text fields for banned phrases."""
        issues: List[QualityIssue] = []

        # Collect text fields to scan
        text_locations = cls._extract_text_fields(report_data)

        for location, text in text_locations:
            for pattern in _BANNED_PATTERNS:
                match = pattern.search(text)
                if match:
                    issues.append(QualityIssue(
                        check="buzzword",
                        severity=Severity.WARNING,
                        location=location,
                        detail=f"Banned phrase '{match.group()}' found in {location}",
                    ))

        return issues

    @classmethod
    def _extract_text_fields(cls, report_data: Dict[str, Any]) -> List[tuple]:
        """Extract all text fields from report for scanning."""
        fields = []

        # Executive summary
        exec_summary = report_data.get("executive_summary", {})
        if isinstance(exec_summary, dict):
            for key in ("key_insight", "summary", "headline"):
                val = exec_summary.get(key, "")
                if val:
                    fields.append((f"executive_summary.{key}", str(val)))

        # Findings
        for i, finding in enumerate(report_data.get("findings", [])):
            for key in ("title", "description", "recommendation_rationale"):
                val = finding.get(key, "")
                if val:
                    fields.append((f"findings[{i}].{key}", str(val)))

        # Recommendations
        for i, rec in enumerate(report_data.get("recommendations", [])):
            for key in ("title", "description", "recommendation_rationale"):
                val = rec.get(key, "")
                if val:
                    fields.append((f"recommendations[{i}].{key}", str(val)))

        return fields

    # -----------------------------------------------------------------
    # Check: Confidence Distribution
    # -----------------------------------------------------------------

    @classmethod
    def check_confidence_distribution(
        cls, report_data: Dict[str, Any]
    ) -> List[QualityIssue]:
        """Validate confidence levels follow target distribution."""
        issues: List[QualityIssue] = []

        findings = report_data.get("findings", [])
        if len(findings) < MIN_FINDINGS_FOR_DISTRIBUTION:
            return issues

        counts = {"high": 0, "medium": 0, "low": 0}
        for finding in findings:
            conf = finding.get("confidence", "medium").lower()
            if conf in counts:
                counts[conf] += 1

        total = len(findings)
        for level, (min_pct, max_pct) in CONFIDENCE_TARGETS.items():
            actual_pct = counts[level] / total
            if actual_pct < min_pct:
                issues.append(QualityIssue(
                    check="confidence_distribution",
                    severity=Severity.WARNING,
                    location="findings",
                    detail=(
                        f"Too few {level}-confidence findings: "
                        f"{counts[level]}/{total} ({actual_pct:.0%}), "
                        f"target: {min_pct:.0%}-{max_pct:.0%}"
                    ),
                ))
            elif actual_pct > max_pct:
                issues.append(QualityIssue(
                    check="confidence_distribution",
                    severity=Severity.WARNING,
                    location="findings",
                    detail=(
                        f"Too many {level}-confidence findings: "
                        f"{counts[level]}/{total} ({actual_pct:.0%}), "
                        f"target: {min_pct:.0%}-{max_pct:.0%}"
                    ),
                ))

        return issues

    # -----------------------------------------------------------------
    # Check: User Data Quoting
    # -----------------------------------------------------------------

    @classmethod
    def check_user_data_quoting(
        cls, report_data: Dict[str, Any]
    ) -> List[QualityIssue]:
        """Check that recommended findings reference user data."""
        issues: List[QualityIssue] = []

        for i, finding in enumerate(report_data.get("findings", [])):
            # Skip not-recommended findings
            if finding.get("is_not_recommended"):
                continue

            description = finding.get("description", "")
            if not description:
                continue

            # Check if any user-data pattern matches
            has_reference = any(
                pattern.search(description)
                for pattern in _USER_DATA_PATTERNS
            )

            if not has_reference:
                issues.append(QualityIssue(
                    check="user_data_quoting",
                    severity=Severity.WARNING,
                    location=f"findings[{i}]",
                    detail=(
                        f"Finding '{finding.get('title', i)}' doesn't reference user data. "
                        f"Add 'Based on your answer:' or 'You mentioned' to ground in quiz responses."
                    ),
                ))

        return issues

    # -----------------------------------------------------------------
    # Check: Source Citations
    # -----------------------------------------------------------------

    @classmethod
    def check_source_citations(
        cls, report_data: Dict[str, Any]
    ) -> List[QualityIssue]:
        """Check that recommended findings have source citations."""
        issues: List[QualityIssue] = []

        for i, finding in enumerate(report_data.get("findings", [])):
            if finding.get("is_not_recommended"):
                continue

            sources = finding.get("sources", [])
            if not sources:
                issues.append(QualityIssue(
                    check="source_citations",
                    severity=Severity.WARNING,
                    location=f"findings[{i}]",
                    detail=(
                        f"Finding '{finding.get('title', i)}' has no source citations. "
                        f"Add quiz references or benchmark sources."
                    ),
                ))

        return issues

    # -----------------------------------------------------------------
    # Check: ROI Values
    # -----------------------------------------------------------------

    @classmethod
    def check_roi_values(
        cls, report_data: Dict[str, Any]
    ) -> List[QualityIssue]:
        """Check for ROI values stuck at zero."""
        issues: List[QualityIssue] = []

        for i, rec in enumerate(report_data.get("recommendations", [])):
            roi = rec.get("roi_percentage", None)
            pending = rec.get("roi_pending_calculation", False)
            calc_failed = rec.get("roi_calculation_failed", False)

            if roi is not None and roi == 0 and pending:
                issues.append(QualityIssue(
                    check="roi_stuck_zero",
                    severity=Severity.ERROR,
                    location=f"recommendations[{i}]",
                    detail=(
                        f"Recommendation '{rec.get('title', i)}' has ROI=0% with "
                        f"roi_pending_calculation=True. ROI was never calculated."
                    ),
                ))
            elif roi is not None and roi == 0 and calc_failed:
                issues.append(QualityIssue(
                    check="roi_calculation_failed",
                    severity=Severity.WARNING,
                    location=f"recommendations[{i}]",
                    detail=(
                        f"Recommendation '{rec.get('title', i)}' has ROI=0%. "
                        f"ROI calculation was attempted but failed. Requires manual review."
                    ),
                ))
            elif roi is not None and roi == 0 and not pending:
                issues.append(QualityIssue(
                    check="roi_zero",
                    severity=Severity.WARNING,
                    location=f"recommendations[{i}]",
                    detail=(
                        f"Recommendation '{rec.get('title', i)}' has ROI=0%. "
                        f"Verify this is intentional."
                    ),
                ))
            # Negative ROI is allowed (not-recommended items)

        return issues

    # -----------------------------------------------------------------
    # Check: Vendor Existence
    # -----------------------------------------------------------------

    @classmethod
    def check_vendor_existence(
        cls, report_data: Dict[str, Any]
    ) -> List[QualityIssue]:
        """Check that vendor slugs in recommendations exist in KB."""
        issues: List[QualityIssue] = []

        # Lazy import to avoid circular dependencies
        from src.knowledge import get_vendor_by_slug

        for i, rec in enumerate(report_data.get("recommendations", [])):
            options = rec.get("options", {})
            for option_key, option_data in options.items():
                if not isinstance(option_data, dict):
                    continue

                vendor_slug = option_data.get("vendor_slug")
                if not vendor_slug:
                    continue

                vendor = get_vendor_by_slug(vendor_slug)
                if not vendor:
                    issues.append(QualityIssue(
                        check="vendor_existence",
                        severity=Severity.WARNING,
                        location=f"recommendations[{i}].options.{option_key}",
                        detail=(
                            f"Vendor '{vendor_slug}' not found in knowledge base. "
                            f"May be hallucinated by LLM."
                        ),
                    ))

        return issues
