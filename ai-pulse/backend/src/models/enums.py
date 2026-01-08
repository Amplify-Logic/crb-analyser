"""
Enums for AI Pulse
"""

from enum import Enum


class SourceType(str, Enum):
    """Type of content source."""
    RSS = "rss"
    YOUTUBE = "youtube"
    REDDIT = "reddit"
    TWITTER = "twitter"


class ContentType(str, Enum):
    """Type of content item."""
    ARTICLE = "article"
    VIDEO = "video"
    POST = "post"
    PAPER = "paper"
    TWEET = "tweet"


class Category(str, Enum):
    """Content category."""
    AI_NEWS = "ai_news"
    AI_AGENTS = "ai_agents"
    AI_TOOLS = "ai_tools"
    AI_RESEARCH = "ai_research"
    AI_BUSINESS = "ai_business"
    AUTOMATION = "automation"


class SubscriptionStatus(str, Enum):
    """User subscription status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    TRIALING = "trialing"


class PreferredTime(str, Enum):
    """Preferred digest delivery time."""
    MORNING = "morning"    # 7 AM local
    LUNCH = "lunch"        # 12 PM local (default)
    EVENING = "evening"    # 6 PM local


class DigestSendStatus(str, Enum):
    """Status of a digest send."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    FAILED = "failed"
