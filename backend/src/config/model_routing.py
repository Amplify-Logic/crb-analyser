"""
Model Routing Configuration

Routes different tasks to appropriate models based on:
- Task complexity
- Cost sensitivity
- Quality requirements
- Latency needs

Supported Providers:
- Anthropic: Haiku (fast), Sonnet (balanced), Opus (premium)
- Google: Gemini Flash (fast/cheap), Gemini Pro (premium)
- OpenAI: GPT-5.2 (balanced/premium)
- DeepSeek: V3.2 (budget)

Model tiers:
- Fast: Haiku, Gemini Flash - extraction, validation, simple classification
- Balanced: Sonnet, GPT-5.2 - fallback, cost-sensitive generation
- Premium: Opus 4.5, Gemini Pro - main generation, complex analysis
- Budget: DeepSeek V3.2 - high volume, cost-critical

Verified Pricing (December 2025):
- Sources: anthropic.com/pricing, ai.google.dev/gemini-api/docs/pricing,
           platform.openai.com/docs/models/gpt-5.2, api-docs.deepseek.com
- Last verified: December 2025

Benchmark Performance (December 2025):
- Claude Opus 4.5: 80.9% SWE-bench (leads), best for coding/reasoning
- Gemini 3 Pro: 1501 Elo LMArena (first ever 1500+), 1M context
- GPT-5.2: 100% AIME 2025, 187 tok/s inference, 400K context
- DeepSeek V3.2: 73.1% SWE-bench, 94% cheaper than Claude
"""

import logging
from typing import Optional, Literal

from src.config.settings import settings

logger = logging.getLogger(__name__)


# =============================================================================
# MODEL DEFINITIONS (Verified December 2025)
# =============================================================================

# =============================================================================
# ANTHROPIC CLAUDE 4.5 FAMILY
# Source: https://www.anthropic.com/pricing
# =============================================================================
# Opus 4.5:   $5/$25 per 1M tokens  - Complex reasoning, strategic analysis
# Sonnet 4.5: $3/$15 per 1M tokens  - Balanced, coding, analysis
# Haiku 4.5:  $1/$5 per 1M tokens   - Fast, matches Sonnet 4 quality
# Context: 200K tokens for all models
CLAUDE_MODELS = {
    "haiku": "claude-haiku-4-5-20251001",    # Fast extraction - $1/$5
    "sonnet": "claude-sonnet-4-5-20250929",  # Balanced - $3/$15
    "opus": "claude-opus-4-5-20251101",      # Premium reasoning - $5/$25
}

# =============================================================================
# GOOGLE GEMINI 3 FAMILY (December 2025)
# Source: https://ai.google.dev/gemini-api/docs/pricing
# =============================================================================
# Gemini 3 Flash: Fast, cost-effective (preview)
# Gemini 3 Pro:   Deep reasoning, premium quality (preview)
# Context: 1M+ tokens
GEMINI_MODELS = {
    "flash": "gemini-3-flash-preview",  # Gemini 3 Flash (preview)
    "pro": "gemini-3-pro-preview",      # Gemini 3 Pro (preview)
}

# =============================================================================
# OPENAI GPT-5.2 FAMILY (Released Dec 11, 2025)
# Source: https://platform.openai.com/docs/models/gpt-5.2
# =============================================================================
# GPT-5.2:      $1.75/$14 per 1M tokens - Balanced, 400K context
# GPT-5.2 Pro:  Higher cost, max reasoning compute
# Variants: Instant (fast), Thinking (reasoning dial), Pro (max compute)
# Context: 400K tokens, 128K max output
OPENAI_MODELS = {
    "gpt52": "gpt-5.2",               # Balanced - $1.75/$14, 400K context
    "gpt52_pro": "gpt-5.2-pro",       # Premium - max reasoning compute
}

# =============================================================================
# DEEPSEEK V3.2 (Budget Option)
# Source: https://api-docs.deepseek.com/quick_start/pricing
# =============================================================================
# DeepSeek V3.2: $0.28/$0.42 per 1M tokens (cache miss)
#                $0.028/$0.42 per 1M tokens (cache hit)
# 94% cheaper than Claude, 73.1% SWE-bench
DEEPSEEK_MODELS = {
    "v3": "deepseek-chat",            # Budget option - $0.28/$0.42
}

# Active provider: "anthropic" or "google"
# Can be overridden via settings.MODEL_PROVIDER
ACTIVE_PROVIDER = getattr(settings, "MODEL_PROVIDER", "anthropic")

# Unified model mapping based on provider
def get_models():
    """Get model mapping based on active provider."""
    if ACTIVE_PROVIDER == "google":
        return {
            "fast": GEMINI_MODELS["flash"],
            "balanced": GEMINI_MODELS["flash"],  # Flash is good enough for balanced
            "premium": GEMINI_MODELS["pro"],
            "provider": "google",
        }
    else:  # anthropic (default)
        return {
            "fast": CLAUDE_MODELS["haiku"],
            "balanced": CLAUDE_MODELS["sonnet"],
            "premium": CLAUDE_MODELS["opus"],
            "provider": "anthropic",
        }

MODELS = get_models()


# =============================================================================
# TASK TO MODEL ROUTING
# =============================================================================

MODEL_ROUTING = {
    # -------------------------------------------------------------------------
    # FAST EXTRACTION TASKS - Speed and cost optimized
    # -------------------------------------------------------------------------
    "parse_quiz_responses": MODELS["fast"],
    "extract_industry": MODELS["fast"],
    "extract_pain_points": MODELS["fast"],
    "validate_json": MODELS["fast"],
    "classify_finding": MODELS["fast"],
    "extract_metrics": MODELS["fast"],

    # -------------------------------------------------------------------------
    # MAIN GENERATION TASKS - Use premium (Opus 4.5) for best quality
    # -------------------------------------------------------------------------
    "generate_executive_summary": MODELS["premium"],
    "generate_findings": MODELS["premium"],
    "generate_recommendations": MODELS["premium"],
    "generate_roadmap": MODELS["premium"],
    "generate_verdict": MODELS["premium"],
    "generate_methodology": MODELS["premium"],
    "generate_playbook": MODELS["premium"],

    # -------------------------------------------------------------------------
    # COMPLEX SYNTHESIS - Always premium
    # -------------------------------------------------------------------------
    "synthesize_report": MODELS["premium"],
    "complex_analysis": MODELS["premium"],

    # -------------------------------------------------------------------------
    # RESEARCH TASKS - Fast for speed
    # -------------------------------------------------------------------------
    "search_vendors": MODELS["fast"],
    "search_benchmarks": MODELS["fast"],
    "validate_sources": MODELS["fast"],
}


# =============================================================================
# TIER-BASED OVERRIDES
# =============================================================================

# For premium/full tier reports, all main tasks use premium (Opus 4.5)
# For quick tier, use balanced (Sonnet) for cost savings
TIER_OVERRIDES = {
    "full": {
        # Full tier uses premium for everything - already set in MODEL_ROUTING
    },
    "quick": {
        # Quick tier downgrades generation tasks to balanced for cost savings
        "generate_executive_summary": MODELS["balanced"],
        "generate_findings": MODELS["balanced"],
        "generate_recommendations": MODELS["balanced"],
        "generate_roadmap": MODELS["balanced"],
        "generate_playbook": MODELS["balanced"],
    },
}


# =============================================================================
# MULTI-MODEL STRATEGY (For Testing & Cross-Checking)
# =============================================================================
# Strategy: Use cheaper models for initial generation, premium for aggregation
# Optional: Cross-check critical sections with multiple models

MULTI_MODEL_STRATEGIES = {
    # Strategy 1: Cost-optimized (use Flash for drafts, Opus for final)
    "cost_optimized": {
        "draft_model": GEMINI_MODELS["flash"],      # $0.50/$3 - initial drafts
        "review_model": CLAUDE_MODELS["sonnet"],    # $3/$15 - review & refine
        "final_model": CLAUDE_MODELS["opus"],       # $5/$25 - final aggregation
        "cross_check": False,
    },

    # Strategy 2: Quality-first (Opus throughout, Gemini for validation)
    "quality_first": {
        "draft_model": CLAUDE_MODELS["opus"],       # $5/$25 - premium drafts
        "review_model": CLAUDE_MODELS["opus"],      # $5/$25 - premium review
        "final_model": CLAUDE_MODELS["opus"],       # $5/$25 - premium final
        "cross_check": True,
        "cross_check_model": GEMINI_MODELS["pro"],  # Different perspective
    },

    # Strategy 3: Hybrid (Best of both worlds) - RECOMMENDED
    "hybrid": {
        # Phase 1: Fast extraction with Haiku
        "extract_model": CLAUDE_MODELS["haiku"],    # $1/$5 - fast extraction

        # Phase 2: Generation with Sonnet
        "generate_model": CLAUDE_MODELS["sonnet"],  # $3/$15 - good quality

        # Phase 3: Final synthesis with Opus
        "synthesize_model": CLAUDE_MODELS["opus"],  # $5/$25 - best reasoning

        # Cross-check findings with Gemini Flash (cheap validation)
        "cross_check": True,
        "cross_check_model": GEMINI_MODELS["flash"],  # $0.50/$3 - cheap validation
    },

    # Strategy 4: Gemini-primary (Cost-focused, strong quality)
    "gemini_primary": {
        "draft_model": GEMINI_MODELS["flash"],      # $0.50/$3 - ultra-cheap
        "review_model": GEMINI_MODELS["flash"],     # $0.50/$3 - still cheap
        "final_model": GEMINI_MODELS["pro"],        # $2/$12 - Gemini premium (1501 Elo!)
        "cross_check": True,
        "cross_check_model": CLAUDE_MODELS["sonnet"],  # Claude perspective
    },

    # Strategy 5: OpenAI-primary (GPT-5.2 ecosystem)
    "openai_primary": {
        "draft_model": OPENAI_MODELS["gpt52"],      # $1.75/$14 - fast inference
        "review_model": OPENAI_MODELS["gpt52"],     # $1.75/$14 - consistent
        "final_model": OPENAI_MODELS["gpt52_pro"],  # Higher reasoning compute
        "cross_check": True,
        "cross_check_model": CLAUDE_MODELS["opus"], # Claude validation
    },

    # Strategy 6: Budget (DeepSeek-primary, 94% cost savings)
    "budget": {
        "draft_model": DEEPSEEK_MODELS["v3"],       # $0.28/$0.42 - ultra-cheap
        "review_model": GEMINI_MODELS["flash"],     # $0.50/$3 - cheap review
        "final_model": CLAUDE_MODELS["sonnet"],     # $3/$15 - quality final
        "cross_check": False,  # Skip cross-check to save cost
    },

    # Strategy 7: Multi-provider validation (highest quality)
    "multi_provider": {
        "draft_model": CLAUDE_MODELS["opus"],       # $5/$25 - Claude draft
        "review_model": GEMINI_MODELS["pro"],       # $2/$12 - Gemini review
        "final_model": CLAUDE_MODELS["opus"],       # $5/$25 - Claude final
        "cross_check": True,
        "cross_check_model": OPENAI_MODELS["gpt52"],  # GPT-5.2 validation
        "triple_check": True,  # Enable 3-way validation for critical sections
    },
}

# Active multi-model strategy (set via settings.MULTI_MODEL_STRATEGY)
ACTIVE_STRATEGY = getattr(settings, "MULTI_MODEL_STRATEGY", "hybrid")


def get_strategy_models() -> dict:
    """Get the models for the active multi-model strategy."""
    return MULTI_MODEL_STRATEGIES.get(ACTIVE_STRATEGY, MULTI_MODEL_STRATEGIES["hybrid"])


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

    # Pricing per 1M tokens (USD) - Verified December 2025
    # Sources: anthropic.com/pricing, ai.google.dev, platform.openai.com, api-docs.deepseek.com
    PRICING = {
        # Anthropic Claude 4.5 Family
        CLAUDE_MODELS["haiku"]: {"input": 1.00, "output": 5.00},
        CLAUDE_MODELS["sonnet"]: {"input": 3.00, "output": 15.00},
        CLAUDE_MODELS["opus"]: {"input": 5.00, "output": 25.00},
        # Google Gemini 3 Family
        GEMINI_MODELS["flash"]: {"input": 0.50, "output": 3.00},
        GEMINI_MODELS["pro"]: {"input": 2.00, "output": 12.00},  # $4/$18 for >200K
        # OpenAI GPT-5.2 Family
        OPENAI_MODELS["gpt52"]: {"input": 1.75, "output": 14.00},
        OPENAI_MODELS["gpt52_pro"]: {"input": 3.50, "output": 28.00},  # Estimated 2x
        # DeepSeek V3.2 (Budget)
        DEEPSEEK_MODELS["v3"]: {"input": 0.28, "output": 0.42},  # 94% cheaper!
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
