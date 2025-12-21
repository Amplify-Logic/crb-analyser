"""
Report Validation Service

Validates generated reports against the schema and business rules.
Implements TICKET-016: Pydantic validation schema for full report.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from pydantic import ValidationError

from src.models.recommendation import (
    Report,
    Finding,
    Recommendation,
    RecommendationOptions,
    Verdict,
    ExecutiveSummary,
    Roadmap,
    ValueSummary,
    MethodologyNotes,
)

logger = logging.getLogger(__name__)


class ReportValidationError(Exception):
    """Raised when report validation fails."""

    def __init__(self, message: str, errors: List[Dict[str, Any]] = None):
        super().__init__(message)
        self.errors = errors or []


class ReportValidator:
    """
    Validates CRB analysis reports against schema and business rules.

    Validation levels:
    - Schema validation: Pydantic model validation
    - Business rules: Min findings, required sections, score ranges
    - Quality checks: Source citations, confidence distribution
    """

    # Business rule thresholds
    MIN_FINDINGS = 5
    MIN_RECOMMENDATIONS = 3
    MIN_NOT_RECOMMENDED = 3
    MIN_SOURCES_PER_FINDING = 1

    # Confidence distribution targets
    CONFIDENCE_TARGETS = {
        "high": (0.20, 0.40),    # 20-40% should be high confidence
        "medium": (0.40, 0.60),  # 40-60% should be medium confidence
        "low": (0.10, 0.30),     # 10-30% should be low confidence
    }

    @classmethod
    def validate_report(cls, report_data: Dict[str, Any], strict: bool = False) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate a report against schema and business rules.

        Args:
            report_data: Raw report data dictionary
            strict: If True, raise exception on validation failure

        Returns:
            Tuple of (is_valid, list of validation errors/warnings)
        """
        errors = []
        warnings = []

        # 1. Schema validation
        schema_errors = cls._validate_schema(report_data)
        errors.extend(schema_errors)

        # 2. Business rules validation
        rule_errors, rule_warnings = cls._validate_business_rules(report_data)
        errors.extend(rule_errors)
        warnings.extend(rule_warnings)

        # 3. Quality checks
        quality_warnings = cls._validate_quality(report_data)
        warnings.extend(quality_warnings)

        is_valid = len(errors) == 0

        if strict and not is_valid:
            raise ReportValidationError(
                f"Report validation failed with {len(errors)} errors",
                errors=errors
            )

        return is_valid, errors + warnings

    @classmethod
    def _validate_schema(cls, report_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate report structure against Pydantic models."""
        errors = []

        # Validate findings
        findings = report_data.get("findings", [])
        for i, finding in enumerate(findings):
            try:
                Finding(**finding)
            except ValidationError as e:
                for error in e.errors():
                    errors.append({
                        "type": "schema",
                        "severity": "error",
                        "location": f"findings[{i}].{'.'.join(str(x) for x in error['loc'])}",
                        "message": error["msg"],
                    })

        # Validate recommendations
        recommendations = report_data.get("recommendations", [])
        for i, rec in enumerate(recommendations):
            try:
                # Validate options structure
                options = rec.get("options", {})
                if options:
                    RecommendationOptions(**options)
            except ValidationError as e:
                for error in e.errors():
                    errors.append({
                        "type": "schema",
                        "severity": "error",
                        "location": f"recommendations[{i}].options.{'.'.join(str(x) for x in error['loc'])}",
                        "message": error["msg"],
                    })

        # Validate verdict
        verdict = report_data.get("executive_summary", {}).get("verdict")
        if verdict:
            try:
                Verdict(**verdict)
            except ValidationError as e:
                for error in e.errors():
                    errors.append({
                        "type": "schema",
                        "severity": "error",
                        "location": f"executive_summary.verdict.{'.'.join(str(x) for x in error['loc'])}",
                        "message": error["msg"],
                    })

        return errors

    @classmethod
    def _validate_business_rules(cls, report_data: Dict[str, Any]) -> Tuple[List[Dict], List[Dict]]:
        """Validate business rules."""
        errors = []
        warnings = []

        findings = report_data.get("findings", [])
        recommendations = report_data.get("recommendations", [])

        # Rule 1: Minimum findings
        if len(findings) < cls.MIN_FINDINGS:
            errors.append({
                "type": "business_rule",
                "severity": "error",
                "rule": "min_findings",
                "message": f"Report must have at least {cls.MIN_FINDINGS} findings, got {len(findings)}",
            })

        # Rule 2: Minimum recommendations
        if len(recommendations) < cls.MIN_RECOMMENDATIONS:
            errors.append({
                "type": "business_rule",
                "severity": "error",
                "rule": "min_recommendations",
                "message": f"Report must have at least {cls.MIN_RECOMMENDATIONS} recommendations, got {len(recommendations)}",
            })

        # Rule 3: Minimum not-recommended findings
        not_recommended_count = sum(1 for f in findings if f.get("is_not_recommended"))
        if not_recommended_count < cls.MIN_NOT_RECOMMENDED:
            errors.append({
                "type": "business_rule",
                "severity": "error",
                "rule": "min_not_recommended",
                "message": f"Report must have at least {cls.MIN_NOT_RECOMMENDED} not-recommended items, got {not_recommended_count}",
            })

        # Rule 4: All recommendations must have three options
        for i, rec in enumerate(recommendations):
            options = rec.get("options", {})
            required_options = ["off_the_shelf", "best_in_class", "custom_solution"]
            missing = [opt for opt in required_options if opt not in options]
            if missing:
                errors.append({
                    "type": "business_rule",
                    "severity": "error",
                    "rule": "three_options",
                    "message": f"Recommendation '{rec.get('title', i)}' missing options: {missing}",
                })

        # Rule 5: Score ranges
        for i, finding in enumerate(findings):
            cv_score = finding.get("customer_value_score", 0)
            bh_score = finding.get("business_health_score", 0)

            if not (1 <= cv_score <= 10):
                errors.append({
                    "type": "business_rule",
                    "severity": "error",
                    "rule": "score_range",
                    "message": f"Finding '{finding.get('title', i)}' has invalid customer_value_score: {cv_score}",
                })
            if not (1 <= bh_score <= 10):
                errors.append({
                    "type": "business_rule",
                    "severity": "error",
                    "rule": "score_range",
                    "message": f"Finding '{finding.get('title', i)}' has invalid business_health_score: {bh_score}",
                })

        # Rule 6: Not-recommended findings should have low scores
        for finding in findings:
            if finding.get("is_not_recommended"):
                cv_score = finding.get("customer_value_score", 10)
                bh_score = finding.get("business_health_score", 10)
                if cv_score >= 6 and bh_score >= 6:
                    warnings.append({
                        "type": "business_rule",
                        "severity": "warning",
                        "rule": "not_recommended_scores",
                        "message": f"Not-recommended finding '{finding.get('title')}' has high scores ({cv_score}, {bh_score})",
                    })

        # Rule 7: Custom solutions must have required fields
        for i, rec in enumerate(recommendations):
            custom = rec.get("options", {}).get("custom_solution", {})
            if custom:
                required_fields = ["build_tools", "model_recommendation", "skills_required"]
                missing = [f for f in required_fields if not custom.get(f)]
                if missing:
                    warnings.append({
                        "type": "business_rule",
                        "severity": "warning",
                        "rule": "custom_solution_fields",
                        "message": f"Recommendation '{rec.get('title', i)}' custom_solution missing: {missing}",
                    })

        return errors, warnings

    @classmethod
    def _validate_quality(cls, report_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate quality indicators."""
        warnings = []

        findings = report_data.get("findings", [])

        # Check 1: Source citations
        findings_without_sources = [
            f.get("title", f"Finding {i}")
            for i, f in enumerate(findings)
            if not f.get("sources") or len(f.get("sources", [])) < cls.MIN_SOURCES_PER_FINDING
        ]
        if findings_without_sources:
            warnings.append({
                "type": "quality",
                "severity": "warning",
                "check": "source_citations",
                "message": f"{len(findings_without_sources)} findings lack source citations",
                "affected": findings_without_sources[:5],  # Show first 5
            })

        # Check 2: Confidence distribution
        if findings:
            confidence_counts = {"high": 0, "medium": 0, "low": 0}
            for finding in findings:
                conf = finding.get("confidence", "medium").lower()
                if conf in confidence_counts:
                    confidence_counts[conf] += 1

            total = len(findings)
            for level, (min_pct, max_pct) in cls.CONFIDENCE_TARGETS.items():
                actual_pct = confidence_counts[level] / total
                if actual_pct < min_pct:
                    warnings.append({
                        "type": "quality",
                        "severity": "warning",
                        "check": "confidence_distribution",
                        "message": f"Low {level}-confidence findings: {actual_pct:.0%} (target: {min_pct:.0%}-{max_pct:.0%})",
                    })
                elif actual_pct > max_pct:
                    warnings.append({
                        "type": "quality",
                        "severity": "warning",
                        "check": "confidence_distribution",
                        "message": f"High {level}-confidence findings: {actual_pct:.0%} (target: {min_pct:.0%}-{max_pct:.0%})",
                    })

        # Check 3: Recommendation rationales
        recommendations = report_data.get("recommendations", [])
        weak_rationales = [
            rec.get("title", f"Rec {i}")
            for i, rec in enumerate(recommendations)
            if len(rec.get("recommendation_rationale", "")) < 50
        ]
        if weak_rationales:
            warnings.append({
                "type": "quality",
                "severity": "warning",
                "check": "rationale_quality",
                "message": f"{len(weak_rationales)} recommendations have weak rationales (<50 chars)",
                "affected": weak_rationales[:3],
            })

        # Check 4: Executive summary completeness
        exec_summary = report_data.get("executive_summary", {})
        missing_exec_fields = []
        required_exec_fields = [
            "ai_readiness_score", "customer_value_score", "business_health_score",
            "key_insight", "total_value_potential", "recommended_investment"
        ]
        for field in required_exec_fields:
            if not exec_summary.get(field):
                missing_exec_fields.append(field)
        if missing_exec_fields:
            warnings.append({
                "type": "quality",
                "severity": "warning",
                "check": "executive_summary_completeness",
                "message": f"Executive summary missing fields: {missing_exec_fields}",
            })

        return warnings

    @classmethod
    def get_validation_summary(cls, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of validation results for logging/debugging."""
        is_valid, issues = cls.validate_report(report_data)

        errors = [i for i in issues if i.get("severity") == "error"]
        warnings = [i for i in issues if i.get("severity") == "warning"]

        return {
            "is_valid": is_valid,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": errors,
            "warnings": warnings,
            "summary": {
                "findings_count": len(report_data.get("findings", [])),
                "recommendations_count": len(report_data.get("recommendations", [])),
                "not_recommended_count": sum(
                    1 for f in report_data.get("findings", [])
                    if f.get("is_not_recommended")
                ),
                "has_verdict": bool(
                    report_data.get("executive_summary", {}).get("verdict")
                ),
                "has_roadmap": bool(report_data.get("roadmap")),
            }
        }


# Convenience function
def validate_report(report_data: Dict[str, Any], strict: bool = False) -> Tuple[bool, List[Dict]]:
    """Validate a report - convenience wrapper."""
    return ReportValidator.validate_report(report_data, strict)
