"""
Model Routing Configuration

Routes different tasks to appropriate Claude models based on:
- Task complexity
- Cost sensitivity
- Quality requirements
- Latency needs

Model tiers:
- Haiku: Fast, cheap - extraction, validation, simple classification
- Sonnet: Balanced - main generation tasks, good quality/cost ratio
- Opus: Premium - complex synthesis, strategic analysis (reserved)
"""

import logging
from typing import Optional

from src.config.settings import settings

logger = logging.getLogger(__name__)


# =============================================================================
# MODEL DEFINITIONS
# =============================================================================

MODELS = {
    "haiku": "claude-3-5-haiku-20241022",
    "sonnet": "claude-sonnet-4-20250514",
    "opus": "claude-opus-4-5-20250514",
}


# =============================================================================
# TASK TO MODEL ROUTING
# =============================================================================

MODEL_ROUTING = {
    # -------------------------------------------------------------------------
    # FAST EXTRACTION TASKS (Haiku) - Speed and cost optimized
    # -------------------------------------------------------------------------
    "parse_quiz_responses": MODELS["haiku"],
    "extract_industry": MODELS["haiku"],
    "extract_pain_points": MODELS["haiku"],
    "validate_json": MODELS["haiku"],
    "classify_finding": MODELS["haiku"],
    "extract_metrics": MODELS["haiku"],

    # -------------------------------------------------------------------------
    # MAIN GENERATION TASKS (Sonnet) - Quality/cost balanced
    # -------------------------------------------------------------------------
    "generate_executive_summary": MODELS["sonnet"],
    "generate_findings": MODELS["sonnet"],
    "generate_recommendations": MODELS["sonnet"],
    "generate_roadmap": MODELS["sonnet"],
    "generate_verdict": MODELS["sonnet"],
    "generate_methodology": MODELS["sonnet"],

    # -------------------------------------------------------------------------
    # COMPLEX SYNTHESIS (Sonnet by default, Opus for premium tier)
    # -------------------------------------------------------------------------
    "synthesize_report": MODELS["sonnet"],
    "complex_analysis": MODELS["sonnet"],  # Upgrade to Opus for full tier

    # -------------------------------------------------------------------------
    # RESEARCH TASKS (Haiku for speed)
    # -------------------------------------------------------------------------
    "search_vendors": MODELS["haiku"],
    "search_benchmarks": MODELS["haiku"],
    "validate_sources": MODELS["haiku"],
}


# =============================================================================
# TIER-BASED OVERRIDES
# =============================================================================

# For premium/full tier reports, upgrade certain tasks to better models
TIER_OVERRIDES = {
    "full": {
        "generate_findings": MODELS["sonnet"],
        "generate_recommendations": MODELS["sonnet"],
        "synthesize_report": MODELS["sonnet"],
        "complex_analysis": MODELS["opus"],  # Only Opus usage
    },
    "quick": {
        # Keep defaults - optimize for speed/cost
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_model_for_task(task: str, tier: str = "quick") -> str:
    """
    Get the appropriate model for a given task and tier.

    Args:
        task: The task identifier (e.g., "generate_findings")
        tier: Report tier ("quick" or "full")

    Returns:
        Model ID string
    """
    # Check for tier-specific override first
    tier_overrides = TIER_OVERRIDES.get(tier, {})
    if task in tier_overrides:
        model = tier_overrides[task]
        logger.debug(f"Task '{task}' using tier override model: {model}")
        return model

    # Use default routing
    model = MODEL_ROUTING.get(task, settings.DEFAULT_MODEL)
    logger.debug(f"Task '{task}' using model: {model}")
    return model


def get_model_info(task: str, tier: str = "quick") -> dict:
    """
    Get model info including name and pricing tier for logging/tracking.
    """
    model_id = get_model_for_task(task, tier)

    # Determine tier name
    tier_name = "unknown"
    for name, mid in MODELS.items():
        if mid == model_id:
            tier_name = name
            break

    return {
        "model_id": model_id,
        "tier_name": tier_name,
        "task": task,
        "report_tier": tier,
    }


# =============================================================================
# TOKEN TRACKING
# =============================================================================

class TokenTracker:
    """
    Track token usage across a report generation session.

    Usage:
        tracker = TokenTracker()
        tracker.add_usage("generate_findings", model, input_tokens, output_tokens)
        print(tracker.get_summary())
    """

    # Approximate pricing per 1M tokens (USD)
    PRICING = {
        MODELS["haiku"]: {"input": 0.80, "output": 4.00},
        MODELS["sonnet"]: {"input": 3.00, "output": 15.00},
        MODELS["opus"]: {"input": 15.00, "output": 75.00},
    }

    def __init__(self):
        self.usage = []
        self.total_input = 0
        self.total_output = 0

    def add_usage(
        self,
        task: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ):
        """Record token usage for a task."""
        self.usage.append({
            "task": task,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        })
        self.total_input += input_tokens
        self.total_output += output_tokens

    def get_summary(self) -> dict:
        """Get usage summary with estimated cost."""
        by_model = {}
        for u in self.usage:
            model = u["model"]
            if model not in by_model:
                by_model[model] = {"input": 0, "output": 0, "tasks": []}
            by_model[model]["input"] += u["input_tokens"]
            by_model[model]["output"] += u["output_tokens"]
            by_model[model]["tasks"].append(u["task"])

        # Calculate estimated cost
        total_cost = 0.0
        for model, tokens in by_model.items():
            pricing = self.PRICING.get(model, {"input": 3.0, "output": 15.0})
            cost = (
                (tokens["input"] / 1_000_000) * pricing["input"] +
                (tokens["output"] / 1_000_000) * pricing["output"]
            )
            by_model[model]["estimated_cost_usd"] = round(cost, 4)
            total_cost += cost

        return {
            "total_input_tokens": self.total_input,
            "total_output_tokens": self.total_output,
            "total_tokens": self.total_input + self.total_output,
            "estimated_cost_usd": round(total_cost, 4),
            "by_model": by_model,
            "task_count": len(self.usage),
        }

    def to_dict(self) -> dict:
        """Export full usage data for storage."""
        return {
            "usage": self.usage,
            "summary": self.get_summary(),
        }
