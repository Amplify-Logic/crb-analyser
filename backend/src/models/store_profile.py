"""
StoreProfile — normalized store metrics with source tracking.

Each metric knows whether it came from manual entry, OAuth, or benchmarks.
Completeness score drives report quality messaging.
"""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, computed_field


class DataSource(str, Enum):
    SHOPIFY_OAUTH = "shopify_oauth"
    MANUAL_ENTRY = "manual_entry"
    BENCHMARK = "benchmark"


class StoreMetric(BaseModel):
    """Individual metric with provenance tracking."""

    value: Decimal | float | int
    source: DataSource
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# The 6 tier-1 fields used for completeness calculation
_TIER1_FIELDS: list[str] = [
    "monthly_revenue",
    "monthly_orders",
    "average_order_value",
    "cart_abandonment_rate",
    "repeat_customer_rate",
    "email_list_size",
]


class StoreProfile(BaseModel):
    """Normalized store data from any source."""

    # Store context (from quiz, always available)
    platform: str
    currency: str = "EUR"
    ecommerce_sub_type: str = ""
    sales_channels: List[str] = Field(default_factory=list)

    # Tier 1: The 6 numbers that transform report quality
    monthly_revenue: Optional[StoreMetric] = None
    monthly_orders: Optional[StoreMetric] = None
    average_order_value: Optional[StoreMetric] = None
    cart_abandonment_rate: Optional[StoreMetric] = None
    repeat_customer_rate: Optional[StoreMetric] = None
    email_list_size: Optional[StoreMetric] = None

    # Tier 2: Sharper recommendations (OAuth or workshop)
    refund_rate: Optional[StoreMetric] = None
    product_count: Optional[StoreMetric] = None
    conversion_rate: Optional[StoreMetric] = None
    channel_breakdown: Optional[Dict[str, float]] = None
    support_ticket_volume: Optional[StoreMetric] = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def completeness(self) -> float:
        """Fraction of tier-1 metrics filled (0.0 - 1.0)."""
        filled = sum(1 for f in _TIER1_FIELDS if getattr(self, f) is not None)
        return filled / len(_TIER1_FIELDS)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def source(self) -> DataSource:
        """Primary data source based on what metrics are present."""
        sources = [
            getattr(self, f).source
            for f in _TIER1_FIELDS
            if getattr(self, f) is not None
        ]
        if not sources:
            return DataSource.BENCHMARK
        if DataSource.SHOPIFY_OAUTH in sources:
            return DataSource.SHOPIFY_OAUTH
        return DataSource.MANUAL_ENTRY

    @property
    def completeness_label(self) -> str:
        """Human-readable label for report display."""
        c = self.completeness
        if c >= 0.7:
            return "your actual business data"
        if c >= 0.3:
            return "your data + benchmarks"
        return "industry benchmarks"

    def to_prompt_context(self) -> Dict[str, Any]:
        """Serialize for inclusion in LLM prompt context."""
        result: Dict[str, Any] = {
            "platform": self.platform,
            "currency": self.currency,
            "ecommerce_sub_type": self.ecommerce_sub_type,
            "sales_channels": self.sales_channels,
            "completeness": self.completeness,
            "completeness_label": self.completeness_label,
            "source": self.source.value,
        }
        for field_name in _TIER1_FIELDS:
            metric: Optional[StoreMetric] = getattr(self, field_name)
            if metric is not None:
                result[field_name] = {
                    "value": float(metric.value) if isinstance(metric.value, Decimal) else metric.value,
                    "source": metric.source.value,
                }
            else:
                result[field_name] = None
        return result

    @classmethod
    def from_manual_entry(
        cls,
        raw_answers: Dict[str, str],
        platform: str,
        currency: str,
        ecommerce_sub_type: str,
        sales_channels: List[str],
        monthly_orders: Optional[int] = None,
    ) -> "StoreProfile":
        """Create profile from manual entry form answers.

        Blank or empty string values are treated as 'don't know' and left as None.
        """

        def _parse_decimal(val: str) -> Optional[StoreMetric]:
            if not val or not val.strip():
                return None
            try:
                return StoreMetric(value=Decimal(val.strip()), source=DataSource.MANUAL_ENTRY)
            except InvalidOperation:
                return None

        def _parse_float_pct(val: str) -> Optional[StoreMetric]:
            if not val or not val.strip():
                return None
            try:
                return StoreMetric(value=float(val.strip()) / 100, source=DataSource.MANUAL_ENTRY)
            except ValueError:
                return None

        def _parse_int(val: str) -> Optional[StoreMetric]:
            if not val or not val.strip():
                return None
            try:
                return StoreMetric(value=int(val.strip()), source=DataSource.MANUAL_ENTRY)
            except ValueError:
                return None

        orders_metric = (
            StoreMetric(value=monthly_orders, source=DataSource.MANUAL_ENTRY)
            if monthly_orders is not None
            else None
        )

        return cls(
            platform=platform,
            currency=currency,
            ecommerce_sub_type=ecommerce_sub_type,
            sales_channels=sales_channels,
            monthly_revenue=_parse_decimal(raw_answers.get("monthly_revenue", "")),
            monthly_orders=orders_metric,
            average_order_value=_parse_decimal(raw_answers.get("average_order_value", "")),
            cart_abandonment_rate=_parse_float_pct(raw_answers.get("cart_abandonment_rate", "")),
            repeat_customer_rate=_parse_float_pct(raw_answers.get("repeat_customer_rate", "")),
            email_list_size=_parse_int(raw_answers.get("email_list_size", "")),
        )
