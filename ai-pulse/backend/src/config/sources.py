"""
Content Sources Configuration

All 50+ sources that AI Pulse monitors for AI news and updates.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class SourceType(str, Enum):
    RSS = "rss"
    YOUTUBE = "youtube"
    REDDIT = "reddit"
    TWITTER = "twitter"


class Category(str, Enum):
    AI_NEWS = "ai_news"
    AI_AGENTS = "ai_agents"
    AI_TOOLS = "ai_tools"
    AI_RESEARCH = "ai_research"
    AI_BUSINESS = "ai_business"
    AUTOMATION = "automation"


@dataclass
class Source:
    """A content source to monitor."""
    slug: str
    name: str
    source_type: SourceType
    url: str
    category: Category
    priority: int  # 1-10, higher = more important
    enabled: bool = True
    description: Optional[str] = None
    # YouTube-specific
    channel_id: Optional[str] = None
    # Reddit-specific
    subreddit: Optional[str] = None
    # Twitter-specific
    twitter_handle: Optional[str] = None


# ============================================================================
# YouTube Channels (20+)
# ============================================================================

YOUTUBE_SOURCES: List[Source] = [
    Source(
        slug="cole-medin",
        name="Cole Medin",
        source_type=SourceType.YOUTUBE,
        url="https://www.youtube.com/@ColeMedin",
        channel_id="UCxxxxxxxx",  # Replace with actual channel ID
        category=Category.AI_AGENTS,
        priority=9,
        description="AI agents, n8n automation",
    ),
    Source(
        slug="dave-shapiro",
        name="Dave Shapiro",
        source_type=SourceType.YOUTUBE,
        url="https://www.youtube.com/@DaveShap",
        channel_id="UCxxxxxxxx",
        category=Category.AI_AGENTS,
        priority=9,
        description="AI architecture, autonomous agents",
    ),
    Source(
        slug="liam-ottley",
        name="Liam Ottley",
        source_type=SourceType.YOUTUBE,
        url="https://www.youtube.com/@LiamOttley",
        channel_id="UCxxxxxxxx",
        category=Category.AI_BUSINESS,
        priority=8,
        description="AI automation agencies",
    ),
    Source(
        slug="matthew-berman",
        name="Matthew Berman",
        source_type=SourceType.YOUTUBE,
        url="https://www.youtube.com/@MatthewBerman",
        channel_id="UCxxxxxxxx",
        category=Category.AI_NEWS,
        priority=9,
        description="AI news, model reviews",
    ),
    Source(
        slug="ai-explained",
        name="AI Explained",
        source_type=SourceType.YOUTUBE,
        url="https://www.youtube.com/@aiexplained-official",
        channel_id="UCxxxxxxxx",
        category=Category.AI_RESEARCH,
        priority=10,
        description="Deep dives on AI research",
    ),
    Source(
        slug="wes-roth",
        name="Wes Roth",
        source_type=SourceType.YOUTUBE,
        url="https://www.youtube.com/@WesRoth",
        channel_id="UCxxxxxxxx",
        category=Category.AI_NEWS,
        priority=8,
        description="AI news and analysis",
    ),
    Source(
        slug="ai-jason",
        name="AI Jason",
        source_type=SourceType.YOUTUBE,
        url="https://www.youtube.com/@AIJasonZ",
        channel_id="UCxxxxxxxx",
        category=Category.AI_AGENTS,
        priority=8,
        description="AI agents tutorials",
    ),
    Source(
        slug="sam-witteveen",
        name="Sam Witteveen",
        source_type=SourceType.YOUTUBE,
        url="https://www.youtube.com/@samwitteveenai",
        channel_id="UCxxxxxxxx",
        category=Category.AI_TOOLS,
        priority=8,
        description="LangChain, RAG tutorials",
    ),
    Source(
        slug="all-about-ai",
        name="All About AI",
        source_type=SourceType.YOUTUBE,
        url="https://www.youtube.com/@AllAboutAI",
        channel_id="UCxxxxxxxx",
        category=Category.AI_TOOLS,
        priority=7,
        description="AI tool reviews",
    ),
    Source(
        slug="worldofai",
        name="WorldofAI",
        source_type=SourceType.YOUTUBE,
        url="https://www.youtube.com/@intheworldofai",
        channel_id="UCxxxxxxxx",
        category=Category.AI_NEWS,
        priority=7,
        description="AI news roundups",
    ),
    Source(
        slug="fireship",
        name="Fireship",
        source_type=SourceType.YOUTUBE,
        url="https://www.youtube.com/@Fireship",
        channel_id="UCxxxxxxxx",
        category=Category.AI_NEWS,
        priority=9,
        description="Fast tech content, AI updates",
    ),
    Source(
        slug="two-minute-papers",
        name="Two Minute Papers",
        source_type=SourceType.YOUTUBE,
        url="https://www.youtube.com/@TwoMinutePapers",
        channel_id="UCxxxxxxxx",
        category=Category.AI_RESEARCH,
        priority=9,
        description="AI research paper summaries",
    ),
    Source(
        slug="yannic-kilcher",
        name="Yannic Kilcher",
        source_type=SourceType.YOUTUBE,
        url="https://www.youtube.com/@YannicKilcher",
        channel_id="UCxxxxxxxx",
        category=Category.AI_RESEARCH,
        priority=9,
        description="ML paper reviews",
    ),
    Source(
        slug="networkchuck",
        name="NetworkChuck",
        source_type=SourceType.YOUTUBE,
        url="https://www.youtube.com/@NetworkChuck",
        channel_id="UCxxxxxxxx",
        category=Category.AI_TOOLS,
        priority=6,
        description="Tech tutorials including AI",
    ),
    Source(
        slug="corbin-brown",
        name="Corbin Brown",
        source_type=SourceType.YOUTUBE,
        url="https://www.youtube.com/@CorbinBrown",
        channel_id="UCxxxxxxxx",
        category=Category.AUTOMATION,
        priority=7,
        description="AI automation tutorials",
    ),
    Source(
        slug="leon-van-zyl",
        name="Leon van Zyl",
        source_type=SourceType.YOUTUBE,
        url="https://www.youtube.com/@LeonvanZyl",
        channel_id="UCxxxxxxxx",
        category=Category.AI_AGENTS,
        priority=7,
        description="AI agents and automation",
    ),
    Source(
        slug="greg-isenberg",
        name="Greg Isenberg",
        source_type=SourceType.YOUTUBE,
        url="https://www.youtube.com/@GregIsenberg",
        channel_id="UCxxxxxxxx",
        category=Category.AI_BUSINESS,
        priority=8,
        description="AI business opportunities",
    ),
]

# ============================================================================
# RSS Feeds (15+)
# ============================================================================

RSS_SOURCES: List[Source] = [
    Source(
        slug="openai-blog",
        name="OpenAI Blog",
        source_type=SourceType.RSS,
        url="https://openai.com/blog/rss.xml",
        category=Category.AI_NEWS,
        priority=10,
        description="Official OpenAI announcements",
    ),
    Source(
        slug="anthropic-news",
        name="Anthropic News",
        source_type=SourceType.RSS,
        url="https://www.anthropic.com/feed.xml",
        category=Category.AI_NEWS,
        priority=10,
        description="Official Anthropic announcements",
    ),
    Source(
        slug="google-ai-blog",
        name="Google AI Blog",
        source_type=SourceType.RSS,
        url="https://blog.google/technology/ai/rss/",
        category=Category.AI_NEWS,
        priority=10,
        description="Google AI research and products",
    ),
    Source(
        slug="huggingface-blog",
        name="Hugging Face Blog",
        source_type=SourceType.RSS,
        url="https://huggingface.co/blog/feed.xml",
        category=Category.AI_TOOLS,
        priority=9,
        description="Open source AI models and tools",
    ),
    Source(
        slug="arxiv-ai",
        name="ArXiv AI",
        source_type=SourceType.RSS,
        url="https://rss.arxiv.org/rss/cs.AI",
        category=Category.AI_RESEARCH,
        priority=8,
        description="Latest AI research papers",
    ),
    Source(
        slug="arxiv-ml",
        name="ArXiv Machine Learning",
        source_type=SourceType.RSS,
        url="https://rss.arxiv.org/rss/cs.LG",
        category=Category.AI_RESEARCH,
        priority=8,
        description="Latest ML research papers",
    ),
    Source(
        slug="techcrunch-ai",
        name="TechCrunch AI",
        source_type=SourceType.RSS,
        url="https://techcrunch.com/category/artificial-intelligence/feed/",
        category=Category.AI_NEWS,
        priority=8,
        description="AI industry news",
    ),
    Source(
        slug="the-verge-ai",
        name="The Verge AI",
        source_type=SourceType.RSS,
        url="https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        category=Category.AI_NEWS,
        priority=7,
        description="AI news and analysis",
    ),
    Source(
        slug="mit-tech-review-ai",
        name="MIT Tech Review AI",
        source_type=SourceType.RSS,
        url="https://www.technologyreview.com/topic/artificial-intelligence/feed",
        category=Category.AI_NEWS,
        priority=8,
        description="AI technology analysis",
    ),
    Source(
        slug="langchain-blog",
        name="LangChain Blog",
        source_type=SourceType.RSS,
        url="https://blog.langchain.dev/rss/",
        category=Category.AI_TOOLS,
        priority=9,
        description="LangChain updates and tutorials",
    ),
    Source(
        slug="ars-technica-ai",
        name="Ars Technica AI",
        source_type=SourceType.RSS,
        url="https://feeds.arstechnica.com/arstechnica/technology-lab",
        category=Category.AI_NEWS,
        priority=6,
        description="Tech news including AI",
    ),
    Source(
        slug="mistral-blog",
        name="Mistral AI Blog",
        source_type=SourceType.RSS,
        url="https://mistral.ai/feed.xml",
        category=Category.AI_NEWS,
        priority=9,
        description="Mistral AI announcements",
    ),
    Source(
        slug="together-ai-blog",
        name="Together AI Blog",
        source_type=SourceType.RSS,
        url="https://www.together.ai/blog/rss.xml",
        category=Category.AI_TOOLS,
        priority=7,
        description="Together AI platform updates",
    ),
]

# ============================================================================
# Reddit Subreddits (5)
# ============================================================================

REDDIT_SOURCES: List[Source] = [
    Source(
        slug="r-machinelearning",
        name="r/MachineLearning",
        source_type=SourceType.REDDIT,
        url="https://www.reddit.com/r/MachineLearning/",
        subreddit="MachineLearning",
        category=Category.AI_RESEARCH,
        priority=9,
        description="ML research discussions",
    ),
    Source(
        slug="r-localllama",
        name="r/LocalLLaMA",
        source_type=SourceType.REDDIT,
        url="https://www.reddit.com/r/LocalLLaMA/",
        subreddit="LocalLLaMA",
        category=Category.AI_TOOLS,
        priority=9,
        description="Local LLM discussions",
    ),
    Source(
        slug="r-chatgpt",
        name="r/ChatGPT",
        source_type=SourceType.REDDIT,
        url="https://www.reddit.com/r/ChatGPT/",
        subreddit="ChatGPT",
        category=Category.AI_NEWS,
        priority=7,
        description="ChatGPT tips and news",
    ),
    Source(
        slug="r-claudeai",
        name="r/ClaudeAI",
        source_type=SourceType.REDDIT,
        url="https://www.reddit.com/r/ClaudeAI/",
        subreddit="ClaudeAI",
        category=Category.AI_NEWS,
        priority=8,
        description="Claude AI discussions",
    ),
    Source(
        slug="r-artificial",
        name="r/artificial",
        source_type=SourceType.REDDIT,
        url="https://www.reddit.com/r/artificial/",
        subreddit="artificial",
        category=Category.AI_NEWS,
        priority=6,
        description="General AI discussions",
    ),
]

# ============================================================================
# Twitter/X Accounts (10+)
# ============================================================================

TWITTER_SOURCES: List[Source] = [
    Source(
        slug="twitter-sama",
        name="Sam Altman",
        source_type=SourceType.TWITTER,
        url="https://twitter.com/sama",
        twitter_handle="sama",
        category=Category.AI_NEWS,
        priority=10,
        description="OpenAI CEO",
    ),
    Source(
        slug="twitter-anthropic",
        name="Anthropic",
        source_type=SourceType.TWITTER,
        url="https://twitter.com/AnthropicAI",
        twitter_handle="AnthropicAI",
        category=Category.AI_NEWS,
        priority=10,
        description="Official Anthropic account",
    ),
    Source(
        slug="twitter-openai",
        name="OpenAI",
        source_type=SourceType.TWITTER,
        url="https://twitter.com/OpenAI",
        twitter_handle="OpenAI",
        category=Category.AI_NEWS,
        priority=10,
        description="Official OpenAI account",
    ),
    Source(
        slug="twitter-deepmind",
        name="Google DeepMind",
        source_type=SourceType.TWITTER,
        url="https://twitter.com/GoogleDeepMind",
        twitter_handle="GoogleDeepMind",
        category=Category.AI_NEWS,
        priority=10,
        description="Official DeepMind account",
    ),
    Source(
        slug="twitter-karpathy",
        name="Andrej Karpathy",
        source_type=SourceType.TWITTER,
        url="https://twitter.com/karpathy",
        twitter_handle="karpathy",
        category=Category.AI_RESEARCH,
        priority=10,
        description="AI researcher, former Tesla/OpenAI",
    ),
    Source(
        slug="twitter-ylecun",
        name="Yann LeCun",
        source_type=SourceType.TWITTER,
        url="https://twitter.com/ylecun",
        twitter_handle="ylecun",
        category=Category.AI_RESEARCH,
        priority=9,
        description="Meta Chief AI Scientist",
    ),
    Source(
        slug="twitter-jimfan",
        name="Jim Fan",
        source_type=SourceType.TWITTER,
        url="https://twitter.com/DrJimFan",
        twitter_handle="DrJimFan",
        category=Category.AI_RESEARCH,
        priority=9,
        description="NVIDIA AI researcher",
    ),
    Source(
        slug="twitter-hwchase",
        name="Harrison Chase",
        source_type=SourceType.TWITTER,
        url="https://twitter.com/hwchase17",
        twitter_handle="hwchase17",
        category=Category.AI_TOOLS,
        priority=9,
        description="LangChain founder",
    ),
    Source(
        slug="twitter-rowancheung",
        name="Rowan Cheung",
        source_type=SourceType.TWITTER,
        url="https://twitter.com/rowancheung",
        twitter_handle="rowancheung",
        category=Category.AI_NEWS,
        priority=8,
        description="The Rundown AI newsletter",
    ),
]

# ============================================================================
# All Sources Combined
# ============================================================================

ALL_SOURCES: List[Source] = (
    YOUTUBE_SOURCES +
    RSS_SOURCES +
    REDDIT_SOURCES +
    TWITTER_SOURCES
)


def get_enabled_sources() -> List[Source]:
    """Get all enabled sources."""
    return [s for s in ALL_SOURCES if s.enabled]


def get_sources_by_type(source_type: SourceType) -> List[Source]:
    """Get sources by type."""
    return [s for s in ALL_SOURCES if s.source_type == source_type and s.enabled]


def get_source_by_slug(slug: str) -> Optional[Source]:
    """Get a source by its slug."""
    for source in ALL_SOURCES:
        if source.slug == slug:
            return source
    return None
