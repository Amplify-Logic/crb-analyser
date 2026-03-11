"""
Service for building, saving, and loading StoreProfiles.

Handles serialization to/from the store_profiles DB table.
"""

import structlog
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.config.supabase_client import get_async_supabase
from src.models.store_profile import (
    DataSource,
    StoreMetric,
    StoreProfile,
    _TIER1_FIELDS,
)

logger = structlog.get_logger()


class StoreProfileService:
    """Builds, persists, and retrieves StoreProfiles."""

    def build_profile(
        self,
        source: str,
        raw_answers: Dict[str, str],
        platform: str,
        currency: str,
        ecommerce_sub_type: str,
        sales_channels: List[str],
        monthly_orders: Optional[int] = None,
    ) -> StoreProfile:
        """Build a StoreProfile from quiz answers.

        source: 'manual_entry' or 'skip'
        raw_answers: dict of field_name -> string value from form
        """
        if source == "skip" or not raw_answers:
            return StoreProfile(
                platform=platform,
                currency=currency,
                ecommerce_sub_type=ecommerce_sub_type,
                sales_channels=sales_channels,
            )

        return StoreProfile.from_manual_entry(
            raw_answers=raw_answers,
            platform=platform,
            currency=currency,
            ecommerce_sub_type=ecommerce_sub_type,
            sales_channels=sales_channels,
            monthly_orders=monthly_orders,
        )

    def serialize_for_db(self, profile: StoreProfile) -> Dict[str, Any]:
        """Serialize StoreProfile for store_profiles table."""
        return {
            "source": profile.source.value,
            "completeness": profile.completeness,
            "currency": profile.currency,
            "metrics": profile.to_prompt_context(),
        }

    def deserialize_from_db(self, row: Dict[str, Any]) -> StoreProfile:
        """Reconstruct StoreProfile from DB row."""
        metrics = row.get("metrics", {})

        def _restore_metric(field_name: str) -> Optional[StoreMetric]:
            data = metrics.get(field_name)
            if data is None:
                return None
            return StoreMetric(
                value=Decimal(str(data["value"])) if isinstance(data["value"], (int, float)) else data["value"],
                source=DataSource(data["source"]),
                captured_at=datetime.fromisoformat(data["captured_at"]) if "captured_at" in data else datetime.now(timezone.utc),
            )

        kwargs: Dict[str, Any] = {
            "platform": metrics.get("platform", "unknown"),
            "currency": row.get("currency", "EUR"),
            "ecommerce_sub_type": metrics.get("ecommerce_sub_type", ""),
            "sales_channels": metrics.get("sales_channels", []),
        }
        for field_name in _TIER1_FIELDS:
            kwargs[field_name] = _restore_metric(field_name)

        return StoreProfile(**kwargs)

    async def save(self, session_id: str, profile: StoreProfile) -> None:
        """Upsert store profile for a quiz session."""
        supabase = await get_async_supabase()
        data = self.serialize_for_db(profile)
        data["quiz_session_id"] = session_id

        await (
            supabase.table("store_profiles")
            .upsert(data, on_conflict="quiz_session_id")
            .execute()
        )
        logger.info(
            "store_profile.saved",
            session_id=session_id,
            source=profile.source.value,
            completeness=profile.completeness,
        )

    async def load(self, session_id: str) -> Optional[StoreProfile]:
        """Load store profile for a quiz session, or None if not found."""
        supabase = await get_async_supabase()
        result = await (
            supabase.table("store_profiles")
            .select("*")
            .eq("quiz_session_id", session_id)
            .maybe_single()
            .execute()
        )
        if not result.data:
            return None
        return self.deserialize_from_db(result.data)
