"""
Source Validator Skill

Validates claims against knowledge base and flags unverified data.

This skill:
1. Analyzes claims in findings and recommendations
2. Checks against knowledge base sources
3. Flags unverified claims
4. Suggests confidence adjustments

Output Schema:
{
    "finding_id": "finding-001",
    "validated_claims": [
        {
            "claim": "35% of dental practices use AI scheduling",
            "verified": true,
            "source": "GoTu AI in Dentistry 2025",
            "source_url": "https://gotu.com/dental-practices/ai-in-dentistry-2025/",
            "confidence_boost": 0.1
        }
    ],
    "unverified_claims": [
        {
            "claim": "Most practices see 50% time savings",
            "reason": "No specific source found",
            "suggested_action": "Add 'estimated' qualifier"
        }
    ],
    "overall_confidence": "medium",
    "confidence_adjustment": -0.05,
    "verification_summary": "3 of 4 claims verified"
}
"""

import re
import logging
from typing import Dict, Any, List, Optional

from src.skills.base import LLMSkill, SkillContext, SkillError
from src.knowledge import (
    get_benchmarks_for_metrics,
    load_industry_data,
    normalize_industry,
)

logger = logging.getLogger(__name__)

# Patterns that suggest claims needing verification
CLAIM_PATTERNS = [
    r'\d+%',  # Percentages
    r'\$[\d,]+',  # Dollar amounts
    r'€[\d,]+',  # Euro amounts
    r'\d+ hours?',  # Time claims
    r'\d+ minutes?',
    r'most\s+\w+',  # "most companies"
    r'typically',
    r'on average',
    r'studies show',
    r'research indicates',
    r'according to',
]


class SourceValidatorSkill(LLMSkill[Dict[str, Any]]):
    """
    Validate claims against knowledge base sources.

    Ensures honest reporting by flagging unverified claims
    and suggesting confidence adjustments.
    """

    name = "source-validator"
    description = "Validate claims against knowledge base"
    version = "1.0.0"

    requires_llm = True
    requires_knowledge = True

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Validate claims in a finding.

        Args:
            context: SkillContext with:
                - metadata.finding: The finding to validate
                - metadata.recommendation: Optional recommendation
                - industry: For industry benchmarks

        Returns:
            Validation results with confidence adjustment
        """
        finding = context.metadata.get("finding", {})
        recommendation = context.metadata.get("recommendation")

        if not finding:
            raise SkillError(
                self.name,
                "No finding provided in context.metadata",
                recoverable=False
            )

        # Extract claims from finding
        claims = self._extract_claims(finding, recommendation)

        if not claims:
            return {
                "finding_id": finding.get("id"),
                "validated_claims": [],
                "unverified_claims": [],
                "overall_confidence": finding.get("confidence", "medium"),
                "confidence_adjustment": 0,
                "verification_summary": "No specific claims to verify",
            }

        # Get industry benchmarks for verification
        benchmarks = get_benchmarks_for_metrics(
            normalize_industry(context.industry),
            []  # Get all benchmarks
        )

        # Load industry data for additional sources
        industry_data = load_industry_data(
            normalize_industry(context.industry),
            "benchmarks"
        )

        # Validate each claim
        validated = []
        unverified = []

        for claim in claims:
            result = self._validate_claim(claim, benchmarks, industry_data)
            if result["verified"]:
                validated.append(result)
            else:
                unverified.append(result)

        # Use LLM for additional validation if needed
        if unverified and self.client:
            validated, unverified = await self._llm_validate_claims(
                validated=validated,
                unverified=unverified,
                industry=context.industry,
            )

        # Calculate confidence adjustment
        total_claims = len(validated) + len(unverified)
        if total_claims > 0:
            verified_ratio = len(validated) / total_claims
            if verified_ratio >= 0.8:
                adjustment = 0.05  # Boost
            elif verified_ratio >= 0.5:
                adjustment = 0
            else:
                adjustment = -0.1  # Penalty

            # Additional boost for having sources
            source_boost = sum(c.get("confidence_boost", 0) for c in validated)
            adjustment += min(0.1, source_boost)
        else:
            adjustment = 0

        # Determine overall confidence
        base_confidence = finding.get("confidence", "medium").lower()
        if adjustment > 0.05:
            overall = "high" if base_confidence != "low" else "medium"
        elif adjustment < -0.05:
            overall = "low" if base_confidence != "high" else "medium"
        else:
            overall = base_confidence

        return {
            "finding_id": finding.get("id"),
            "validated_claims": validated,
            "unverified_claims": unverified,
            "overall_confidence": overall,
            "confidence_adjustment": round(adjustment, 2),
            "verification_summary": f"{len(validated)} of {total_claims} claims verified",
        }

    def _extract_claims(
        self,
        finding: Dict[str, Any],
        recommendation: Optional[Dict[str, Any]],
    ) -> List[str]:
        """Extract verifiable claims from finding text."""
        claims = []

        # Combine text fields
        texts = [
            finding.get("title", ""),
            finding.get("description", ""),
            finding.get("impact", ""),
            finding.get("expected_outcome", ""),
        ]

        if recommendation:
            texts.extend([
                recommendation.get("description", ""),
                recommendation.get("recommendation_rationale", ""),
            ])

        full_text = " ".join(texts)

        # Find sentences with claim patterns
        sentences = re.split(r'[.!?]', full_text)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            for pattern in CLAIM_PATTERNS:
                if re.search(pattern, sentence, re.IGNORECASE):
                    claims.append(sentence)
                    break

        return list(set(claims))[:10]  # Limit to 10 unique claims

    def _validate_claim(
        self,
        claim: str,
        benchmarks: Dict[str, Any],
        industry_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Validate a single claim against knowledge base."""
        claim_lower = claim.lower()

        # Extract any numbers from claim
        numbers = re.findall(r'(\d+(?:\.\d+)?)\s*%', claim)
        dollar_amounts = re.findall(r'\$\s*([\d,]+)', claim)
        euro_amounts = re.findall(r'€\s*([\d,]+)', claim)

        # Check against benchmarks
        for category, data in benchmarks.items():
            if isinstance(data, dict):
                for key, value in data.items():
                    # Check if benchmark matches claim
                    if isinstance(value, (int, float)):
                        for num in numbers:
                            try:
                                claim_num = float(num)
                                # Allow 20% variance
                                if abs(claim_num - value) / max(value, 1) < 0.2:
                                    return {
                                        "claim": claim,
                                        "verified": True,
                                        "source": f"Industry benchmark: {category}",
                                        "source_url": None,
                                        "confidence_boost": 0.05,
                                    }
                            except ValueError:
                                pass

        # Check industry data for sources
        if industry_data:
            sources = industry_data.get("sources", [])
            for source in sources:
                source_text = str(source).lower()
                # Simple keyword matching
                claim_words = set(claim_lower.split())
                source_words = set(source_text.split())
                if len(claim_words & source_words) >= 3:
                    return {
                        "claim": claim,
                        "verified": True,
                        "source": source.get("name", "Industry data"),
                        "source_url": source.get("url"),
                        "confidence_boost": 0.05,
                    }

        # Check for common verified patterns
        if any(kw in claim_lower for kw in ["on average", "typically", "generally"]):
            return {
                "claim": claim,
                "verified": False,
                "reason": "Generalization without specific source",
                "suggested_action": "Add specific source or mark as estimate",
            }

        return {
            "claim": claim,
            "verified": False,
            "reason": "No matching source in knowledge base",
            "suggested_action": "Verify manually or add 'estimated' qualifier",
        }

    async def _llm_validate_claims(
        self,
        validated: List[Dict[str, Any]],
        unverified: List[Dict[str, Any]],
        industry: str,
    ) -> tuple:
        """Use LLM to help validate remaining claims."""
        if not unverified:
            return validated, unverified

        claims_to_check = [c["claim"] for c in unverified[:5]]

        prompt = f"""Review these claims for a {industry} business analysis report.

CLAIMS TO VERIFY:
{claims_to_check}

For each claim, determine:
1. Is this a reasonable industry claim based on your knowledge?
2. What source or basis would support it?
3. Should it be marked as verified, estimated, or unverified?

Return ONLY a JSON object:
{{
    "validations": [
        {{
            "claim": "exact claim text",
            "status": "verified|estimated|unverified",
            "basis": "why this is reasonable or not",
            "suggested_source": "type of source that would verify this"
        }}
    ]
}}"""

        try:
            result = await self.call_llm_json(
                prompt=prompt,
                system="You are a fact-checker for business analysis reports. Be conservative - only mark claims as verified if they are well-established facts."
            )

            validations = {
                v["claim"]: v
                for v in result.get("validations", [])
            }

            new_validated = list(validated)
            new_unverified = []

            for item in unverified:
                claim = item["claim"]
                if claim in validations:
                    v = validations[claim]
                    if v["status"] == "verified":
                        new_validated.append({
                            "claim": claim,
                            "verified": True,
                            "source": v.get("basis", "Industry knowledge"),
                            "source_url": None,
                            "confidence_boost": 0.02,
                        })
                    elif v["status"] == "estimated":
                        new_unverified.append({
                            "claim": claim,
                            "verified": False,
                            "reason": "Reasonable estimate, not verified fact",
                            "suggested_action": "Add 'estimated' or 'approximately' qualifier",
                        })
                    else:
                        new_unverified.append(item)
                else:
                    new_unverified.append(item)

            return new_validated, new_unverified

        except Exception as e:
            logger.warning(f"LLM validation failed: {e}")
            return validated, unverified


# For skill discovery
__all__ = ["SourceValidatorSkill"]
