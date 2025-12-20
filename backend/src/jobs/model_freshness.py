"""
Model Freshness Job

Weekly job that checks AI model pricing and benchmarks for updates.
Scrapes pricing pages and compares to knowledge base.
"""
import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

# Sources to scrape
PRICING_SOURCES = {
    "anthropic": {
        "url": "https://www.anthropic.com/pricing",
        "models": ["claude-opus-4.5", "claude-sonnet-4.5", "claude-haiku-4.5"]
    },
    "openai": {
        "url": "https://openai.com/api/pricing",
        "models": ["gpt-5", "gpt-5.1", "gpt-5.2"]
    },
    "google": {
        "url": "https://ai.google.dev/pricing",
        "models": ["gemini-3-pro", "gemini-3-flash"]
    }
}

# Current known pricing (Dec 2025) - fallback/comparison baseline
KNOWN_PRICING = {
    "claude-opus-4.5": {"input": 5.0, "output": 25.0, "per": "1M tokens"},
    "claude-sonnet-4.5": {"input": 3.0, "output": 15.0, "per": "1M tokens"},
    "gemini-3-pro": {"input": 2.0, "output": 12.0, "per": "1M tokens"},
    "gemini-3-flash": {"input": 0.5, "output": 3.0, "per": "1M tokens"},
    "gpt-5.2": {"input": 1.25, "output": 10.0, "per": "1M tokens"},
}


class ModelFreshnessChecker:
    """Check AI model pricing and benchmarks for updates."""

    def __init__(self):
        self.knowledge_base_path = Path(__file__).parent.parent / "knowledge" / "vendors" / "ai_assistants.json"
        self.changes: List[Dict[str, Any]] = []

    def load_current_knowledge(self) -> Dict[str, Any]:
        """Load current AI model data from knowledge base."""
        try:
            if self.knowledge_base_path.exists():
                with open(self.knowledge_base_path) as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")
        return {"vendors": [], "last_updated": None}

    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a webpage with error handling."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def extract_pricing_from_html(self, html: str, provider: str) -> Dict[str, Any]:
        """Extract pricing information from HTML (basic pattern matching)."""
        pricing = {}

        # Look for common pricing patterns like "$X.XX per 1M tokens"
        # This is a simplified approach - production would use more robust parsing
        patterns = [
            r'\$(\d+\.?\d*)\s*(?:per|/)\s*(?:1M|million)\s*(?:input)?\s*tokens?',
            r'input[:\s]+\$(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*(?:USD|$)\s*(?:per|/)\s*(?:1M|million)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                pricing["found_prices"] = matches[:5]  # First 5 matches
                break

        return pricing

    def compare_pricing(
        self,
        model_slug: str,
        current: Dict[str, Any],
        fetched: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Compare current vs fetched pricing, return change if significant."""
        # For now, compare against known baseline
        baseline = KNOWN_PRICING.get(model_slug)
        if not baseline:
            return None

        # Check if we found any pricing data
        found_prices = fetched.get("found_prices", [])
        if not found_prices:
            return None

        # Try to parse first found price
        try:
            found_price = float(found_prices[0])
            baseline_input = baseline.get("input", 0)

            # Check for >10% change
            if baseline_input > 0:
                change_pct = abs(found_price - baseline_input) / baseline_input * 100
                if change_pct > 10:
                    return {
                        "model_slug": model_slug,
                        "change_type": "price",
                        "old_value": {"input": baseline_input},
                        "new_value": {"input": found_price},
                        "change_percentage": round(change_pct, 1),
                    }
        except (ValueError, IndexError):
            pass

        return None

    async def check_provider(self, provider: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check a single provider for updates."""
        changes = []

        html = await self.fetch_page(config["url"])
        if not html:
            logger.warning(f"Could not fetch {provider} pricing page")
            return changes

        pricing_data = self.extract_pricing_from_html(html, provider)

        # Compare each model
        current_knowledge = self.load_current_knowledge()
        for model_slug in config["models"]:
            current_model = next(
                (v for v in current_knowledge.get("vendors", [])
                 if v.get("slug") == model_slug),
                {}
            )

            change = self.compare_pricing(model_slug, current_model, pricing_data)
            if change:
                change["provider"] = provider
                change["detected_at"] = datetime.utcnow().isoformat()
                changes.append(change)

        return changes

    async def run_check(self) -> Dict[str, Any]:
        """Run full freshness check across all providers."""
        logger.info("Starting model freshness check...")

        all_changes = []

        for provider, config in PRICING_SOURCES.items():
            try:
                changes = await self.check_provider(provider, config)
                all_changes.extend(changes)
                logger.info(f"Checked {provider}: {len(changes)} changes detected")
            except Exception as e:
                logger.error(f"Error checking {provider}: {e}")

        result = {
            "checked_at": datetime.utcnow().isoformat(),
            "providers_checked": list(PRICING_SOURCES.keys()),
            "total_changes": len(all_changes),
            "changes": all_changes,
        }

        if all_changes:
            logger.warning(f"Model freshness check found {len(all_changes)} changes!")
            # In production, this would save to database and send notification
        else:
            logger.info("No significant pricing changes detected")

        return result

    async def save_changes_to_db(self, changes: List[Dict[str, Any]]) -> None:
        """Save detected changes to database for admin review."""
        # Import here to avoid circular imports
        try:
            from src.config.supabase_client import get_async_supabase

            supabase = await get_async_supabase()

            for change in changes:
                await supabase.table("model_updates").insert({
                    "model_slug": change["model_slug"],
                    "change_type": change["change_type"],
                    "old_value": change.get("old_value"),
                    "new_value": change.get("new_value"),
                    "status": "pending",
                }).execute()

            logger.info(f"Saved {len(changes)} changes to model_updates table")
        except Exception as e:
            logger.error(f"Failed to save changes to database: {e}")


async def run_model_freshness_job() -> Dict[str, Any]:
    """Entry point for the model freshness job."""
    checker = ModelFreshnessChecker()
    result = await checker.run_check()

    if result["changes"]:
        await checker.save_changes_to_db(result["changes"])

    return result


# CLI entry point for manual runs
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = asyncio.run(run_model_freshness_job())
    print(json.dumps(result, indent=2))
