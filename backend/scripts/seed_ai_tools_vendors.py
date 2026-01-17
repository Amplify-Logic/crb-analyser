"""
Seed script for AI tools vendors.

Run with: python -m scripts.seed_ai_tools_vendors

Adds 18 vetted AI tools to the vendor database:
- AI Coding Tools: Cursor, Windsurf, Claude Code, GitHub Copilot, Google Antigravity
- AI App Builders: v0.dev, bolt.new, Bubble, Lovable
- AI Voice: Deepgram, ElevenLabs, YourAtlas
- AI Video: Descript, Synthesia, HeyGen
- AI Image: MidJourney
- AI Productivity: Granola
- AI Knowledge: BuddyPro
- Data Scraping: Apify
"""

import asyncio
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


AI_TOOLS_VENDORS = [
    # =========================================================================
    # AI CODING TOOLS
    # =========================================================================
    {
        "slug": "cursor",
        "name": "Cursor",
        "category": "ai_coding_tools",
        "subcategory": "ai_native_ide",
        "website": "https://cursor.com",
        "pricing_url": "https://cursor.com/pricing",
        "description": "AI-native IDE built on VS Code that integrates AI deeply into the coding workflow. Market leader with 1M+ users and fastest-growing SaaS ever ($500M ARR in 16 months). Used by OpenAI, Midjourney, Shopify.",
        "tagline": "The AI-first Code Editor",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "tiers": [
                {"name": "Hobby", "price": 0, "per": "month", "features": ["Basic AI features", "Limited requests"]},
                {"name": "Pro", "price": 20, "per": "month", "features": ["500 fast agent requests/month", "Unlimited slow requests", "All AI features"]},
                {"name": "Pro+", "price": 60, "per": "month", "features": ["1,500 fast agent requests/month", "Priority support"]},
                {"name": "Ultra", "price": 200, "per": "month", "features": ["20x frontier model usage", "No compute caps"]},
                {"name": "Business", "price": 40, "per": "user/month", "features": ["Centralized billing", "Admin dashboard", "Enhanced privacy"]}
            ],
            "starting_price": 0,
            "free_tier": True,
            "free_trial_days": 14
        },
        "company_sizes": ["startup", "smb", "mid_market", "enterprise"],
        "industries": ["*"],
        "best_for": [
            "Developers wanting AI-assisted coding",
            "Teams building custom software",
            "Non-developers learning to code with AI",
            "Rapid prototyping and MVP development"
        ],
        "avoid_if": [
            "Prefer fully cloud-based IDE",
            "Need extensive offline support",
            "Require very specific legacy IDE features"
        ],
        "our_rating": 4.8,
        "our_notes": "Market leader in AI-native IDEs. 18% market share in just 18 months. $29B valuation (Nov 2025). Fastest 0-to-$500M ARR SaaS ever. Best for developers who want AI deeply integrated.",
        "g2_score": 4.6,
        "g2_reviews": 150,
        "implementation_weeks": 0,
        "implementation_complexity": "low",
        "requires_developer": False,
        "api_available": False,
        "competitors": ["windsurf", "github-copilot", "claude-code", "google-antigravity"],
        "key_capabilities": ["AI code generation", "Inline editing", "Chat-based coding", "Multi-file context", "Codebase understanding"],
        "verified_at": datetime.now(tz=timezone.utc).isoformat(),
        "verified_by": "claude-code",
        "source_url": "https://cursor.com/pricing",
        "status": "active"
    },
    {
        "slug": "windsurf",
        "name": "Windsurf",
        "category": "ai_coding_tools",
        "subcategory": "ai_native_ide",
        "website": "https://windsurf.com",
        "pricing_url": "https://windsurf.com/pricing",
        "description": "AI-native IDE from Codeium, positioned as 'the first agentic IDE'. Features Cascade AI assistant that plans multi-step edits and uses deep repo context. Cheaper than Cursor with self-hosting option.",
        "tagline": "The first agentic IDE",
        "pricing": {
            "model": "credits",
            "currency": "USD",
            "tiers": [
                {"name": "Free", "price": 0, "per": "month", "features": ["25 credits/month", "Basic features"]},
                {"name": "Pro", "price": 15, "per": "month", "features": ["500 credits/month", "Full Cascade access", "Priority execution"]},
                {"name": "Teams", "price": 30, "per": "user/month", "features": ["Team collaboration", "Shared workspaces", "Admin controls"]},
                {"name": "Enterprise", "price": 60, "per": "user/month", "features": ["SSO", "Self-hosting", "SOC 2 Type 2", "Zero data retention"]}
            ],
            "starting_price": 0,
            "free_tier": True
        },
        "company_sizes": ["startup", "smb", "mid_market", "enterprise"],
        "industries": ["*"],
        "best_for": [
            "Budget-conscious developers (cheaper than Cursor)",
            "Teams wanting self-hosted option",
            "Enterprise with security requirements",
            "Developers who prefer agentic workflows"
        ],
        "avoid_if": [
            "Want largest community/ecosystem",
            "Need specific niche features from Cursor"
        ],
        "our_rating": 4.5,
        "our_notes": "Best value AI IDE at $15/mo. SOC 2 Type 2 certified. Self-hosting option for enterprises. Cascade agent is genuinely good at multi-step edits.",
        "g2_score": 4.4,
        "g2_reviews": 80,
        "implementation_weeks": 0,
        "implementation_complexity": "low",
        "requires_developer": False,
        "api_available": False,
        "competitors": ["cursor", "github-copilot", "claude-code"],
        "key_capabilities": ["Cascade agentic AI", "Multi-file editing", "Terminal context", "Self-hosting", "Deep repo understanding"],
        "verified_at": datetime.now(tz=timezone.utc).isoformat(),
        "verified_by": "claude-code",
        "source_url": "https://windsurf.com/pricing",
        "status": "active"
    },
    {
        "slug": "claude-code",
        "name": "Claude Code",
        "category": "ai_coding_tools",
        "subcategory": "cli_coding_assistant",
        "website": "https://claude.ai/claude-code",
        "pricing_url": "https://claude.com/pricing",
        "description": "Anthropic's official CLI tool for AI-assisted coding. Terminal-native, works in any editor. Powered by Claude models with best-in-class coding accuracy (80%+ on SWE-bench). Part of Claude subscription.",
        "tagline": "AI coding in your terminal",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "tiers": [
                {"name": "Pro", "price": 20, "per": "month", "features": ["Claude Sonnet 4.5", "Standard usage limits"]},
                {"name": "Max 5x", "price": 100, "per": "month", "features": ["Claude Opus 4.5", "5x usage", "Priority"]},
                {"name": "Max 20x", "price": 200, "per": "month", "features": ["Claude Opus 4.5", "20x usage", "Highest priority"]},
                {"name": "Teams", "price": 150, "per": "user/month", "features": ["5 seat minimum", "Team features", "Admin controls"]}
            ],
            "starting_price": 20,
            "free_tier": False,
            "free_trial_days": 0
        },
        "company_sizes": ["startup", "smb", "mid_market", "enterprise"],
        "industries": ["*"],
        "best_for": [
            "Developers who prefer terminal workflows",
            "Those who want best coding accuracy",
            "Users already on Claude subscription",
            "Complex codebase navigation and editing"
        ],
        "avoid_if": [
            "Want visual IDE experience",
            "Prefer lower-cost options",
            "Need free tier for experimentation"
        ],
        "our_rating": 4.7,
        "our_notes": "Best coding accuracy (Claude Opus 4.5 at 80%+ SWE-bench). Terminal-native is unique. Requires Claude subscription. Best for experienced developers who live in the terminal.",
        "implementation_weeks": 0,
        "implementation_complexity": "low",
        "requires_developer": True,
        "api_available": True,
        "api_type": "CLI",
        "api_docs_url": "https://docs.anthropic.com/claude-code",
        "competitors": ["cursor", "windsurf", "github-copilot"],
        "key_capabilities": ["Terminal-native", "Best-in-class accuracy", "Multi-file editing", "Git integration", "Skill system"],
        "verified_at": datetime.now(tz=timezone.utc).isoformat(),
        "verified_by": "claude-code",
        "source_url": "https://claude.com/pricing",
        "status": "active"
    },
    {
        "slug": "github-copilot",
        "name": "GitHub Copilot",
        "category": "ai_coding_tools",
        "subcategory": "code_assistant",
        "website": "https://github.com/features/copilot",
        "pricing_url": "https://github.com/features/copilot/plans",
        "description": "Microsoft's AI coding assistant. Market leader with 20M+ users and 42% market share. Works as extension in VS Code, JetBrains, etc. Used by 90% of Fortune 100 companies.",
        "tagline": "Your AI pair programmer",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "tiers": [
                {"name": "Free", "price": 0, "per": "month", "features": ["2,000 completions/month", "50 premium requests/month"]},
                {"name": "Pro", "price": 10, "per": "month", "features": ["Unlimited completions", "Chat", "All features"]},
                {"name": "Pro+", "price": 39, "per": "month", "features": ["1,500 premium requests", "Claude Opus 4", "o3 access"]},
                {"name": "Business", "price": 19, "per": "user/month", "features": ["Team management", "Policy controls", "Audit logs"]},
                {"name": "Enterprise", "price": 39, "per": "user/month", "features": ["SSO", "Advanced security", "Custom models"]}
            ],
            "starting_price": 0,
            "free_tier": True,
            "startup_discount": "Free Pro for students and OSS maintainers"
        },
        "company_sizes": ["startup", "smb", "mid_market", "enterprise"],
        "industries": ["*"],
        "best_for": [
            "Teams already using GitHub",
            "Enterprise with security requirements",
            "Developers wanting proven, stable solution",
            "Those who prefer extension over new IDE"
        ],
        "avoid_if": [
            "Want AI-native IDE experience",
            "Prefer newer, more aggressive AI features",
            "Don't use VS Code or JetBrains"
        ],
        "our_rating": 4.6,
        "our_notes": "Market leader with 42% share. Most mature, stable option. Best for enterprises and GitHub-centric workflows. 55% faster task completion in studies.",
        "g2_score": 4.5,
        "g2_reviews": 500,
        "implementation_weeks": 0,
        "implementation_complexity": "low",
        "requires_developer": True,
        "api_available": False,
        "competitors": ["cursor", "windsurf", "claude-code"],
        "key_capabilities": ["Code completion", "Chat", "PR summaries", "Code review", "Enterprise security"],
        "verified_at": datetime.now(tz=timezone.utc).isoformat(),
        "verified_by": "claude-code",
        "source_url": "https://github.com/features/copilot/plans",
        "status": "active"
    },
    {
        "slug": "google-antigravity",
        "name": "Google Antigravity",
        "category": "ai_coding_tools",
        "subcategory": "ai_native_ide",
        "website": "https://antigravityai.org",
        "pricing_url": "https://antigravityai.org",
        "description": "Google's AI-powered IDE announced November 2025. Agent-first design with Manager view for orchestrating multiple AI agents. Supports Gemini 3, Claude, and open-source models. Currently free in preview.",
        "tagline": "Where we're going, we don't need chatbots",
        "pricing": {
            "model": "free_preview",
            "currency": "USD",
            "tiers": [
                {"name": "Preview", "price": 0, "per": "month", "features": ["All features", "Usage quotas apply", "Gemini 3 models"]}
            ],
            "starting_price": 0,
            "free_tier": True,
            "notes": "Free during preview. Paid tiers expected for enterprise/high-volume."
        },
        "company_sizes": ["startup", "smb", "mid_market", "enterprise"],
        "industries": ["*"],
        "best_for": [
            "Developers wanting to try latest Google AI",
            "Those who prefer multi-agent workflows",
            "Teams wanting free option during preview",
            "Google ecosystem users"
        ],
        "avoid_if": [
            "Need production-stable tool",
            "Want proven track record",
            "Require guaranteed pricing"
        ],
        "our_rating": 4.3,
        "our_notes": "Brand new (Nov 2025) but it's Google. Agent-first with Manager view is unique. Free during preview. Watch for enterprise pricing later.",
        "implementation_weeks": 0,
        "implementation_complexity": "low",
        "requires_developer": False,
        "api_available": False,
        "competitors": ["cursor", "windsurf", "claude-code"],
        "key_capabilities": ["Multi-agent orchestration", "Manager view", "Browser automation", "Artifacts verification", "Multiple model support"],
        "verified_at": datetime.now(tz=timezone.utc).isoformat(),
        "verified_by": "claude-code",
        "source_url": "https://developers.googleblog.com/build-with-google-antigravity-our-new-agentic-development-platform/",
        "status": "active"
    },

    # =========================================================================
    # AI APP BUILDERS
    # =========================================================================
    {
        "slug": "v0-dev",
        "name": "v0.dev",
        "category": "ai_app_builders",
        "subcategory": "ui_generator",
        "website": "https://v0.dev",
        "pricing_url": "https://v0.dev",
        "description": "Vercel's AI-powered UI generator. Converts natural language to production-ready React/Next.js code. 6M+ developers. Best for rapid UI prototyping and frontend development.",
        "tagline": "Build apps and websites with AI",
        "pricing": {
            "model": "credits",
            "currency": "USD",
            "tiers": [
                {"name": "Free", "price": 0, "per": "month", "features": ["$5 in credits/month", "Basic generation"]},
                {"name": "Premium", "price": 20, "per": "month", "features": ["$20 in credits/month", "Priority generation"]},
                {"name": "Team", "price": 30, "per": "user/month", "features": ["Shared credits", "Team chat", "API access"]}
            ],
            "starting_price": 0,
            "free_tier": True
        },
        "company_sizes": ["startup", "smb", "mid_market"],
        "industries": ["*"],
        "best_for": [
            "Rapid UI prototyping",
            "Frontend developers",
            "React/Next.js projects",
            "Design-to-code workflows"
        ],
        "avoid_if": [
            "Need full-stack backend",
            "Complex enterprise apps",
            "Non-React projects"
        ],
        "our_rating": 4.4,
        "our_notes": "Excellent for UI generation. Frontend-only - pair with Supabase/backend. Credit-based pricing can burn fast with iteration.",
        "implementation_weeks": 0,
        "implementation_complexity": "low",
        "requires_developer": False,
        "api_available": True,
        "competitors": ["bolt-new", "replit"],
        "key_capabilities": ["React code generation", "Tailwind CSS", "shadcn/ui", "One-click Vercel deploy", "Iterative refinement"],
        "verified_at": datetime.now(tz=timezone.utc).isoformat(),
        "verified_by": "claude-code",
        "source_url": "https://v0.dev",
        "status": "active"
    },
    {
        "slug": "bolt-new",
        "name": "bolt.new",
        "category": "ai_app_builders",
        "subcategory": "full_stack_builder",
        "website": "https://bolt.new",
        "pricing_url": "https://bolt.new/pricing",
        "description": "StackBlitz's AI-powered full-stack app builder. Runs entirely in browser using WebContainers. 1M+ websites built in 5 months. $40M ARR in 6 months. Best for complete apps, not just UI.",
        "tagline": "Prompt, run, edit, and deploy full-stack apps",
        "pricing": {
            "model": "tokens",
            "currency": "USD",
            "tiers": [
                {"name": "Free", "price": 0, "per": "month", "features": ["~100-200k tokens daily", "Public projects only"]},
                {"name": "Pro", "price": 20, "per": "month", "features": ["10M tokens", "Private projects"]},
                {"name": "Pro 50", "price": 50, "per": "month", "features": ["26M tokens"]},
                {"name": "Pro 100", "price": 100, "per": "month", "features": ["55M tokens"]},
                {"name": "Pro 200", "price": 200, "per": "month", "features": ["120M tokens"]}
            ],
            "starting_price": 0,
            "free_tier": True
        },
        "company_sizes": ["startup", "smb"],
        "industries": ["*"],
        "best_for": [
            "Full-stack app prototypes",
            "Non-developers building MVPs",
            "Rapid experimentation",
            "Simple to moderate complexity apps"
        ],
        "avoid_if": [
            "Complex enterprise apps (>15 components)",
            "Need advanced state management",
            "Production-grade reliability required"
        ],
        "our_rating": 4.3,
        "our_notes": "Full-stack in browser is impressive. Token costs add up. Best for prototypes and MVPs. Complexity ceiling around 15-20 components.",
        "g2_score": 4.2,
        "g2_reviews": 40,
        "implementation_weeks": 0,
        "implementation_complexity": "low",
        "requires_developer": False,
        "api_available": False,
        "competitors": ["v0-dev", "replit"],
        "key_capabilities": ["Browser-based dev", "Full-stack generation", "WebContainers", "Instant preview", "One-click deploy"],
        "verified_at": datetime.now(tz=timezone.utc).isoformat(),
        "verified_by": "claude-code",
        "source_url": "https://bolt.new/pricing",
        "status": "active"
    },
    {
        "slug": "bubble",
        "name": "Bubble",
        "category": "ai_app_builders",
        "subcategory": "no_code_platform",
        "website": "https://bubble.io",
        "pricing_url": "https://bubble.io/pricing",
        "description": "Leading no-code platform with 3M+ users. Build full web apps without code. 10+ years proven. Used by 60,000+ companies including HubSpot, Zendesk, VMware. 90% of Fortune 100 familiar.",
        "tagline": "Build apps without code",
        "pricing": {
            "model": "workload_units",
            "currency": "USD",
            "tiers": [
                {"name": "Free", "price": 0, "per": "month", "features": ["50K workload units", "Bubble branding", "Basic features"]},
                {"name": "Starter", "price": 32, "per": "month", "features": ["175K workload units", "Custom domain", "API access"]},
                {"name": "Growth", "price": 134, "per": "month", "features": ["50K+ workload units", "2 app editors", "Priority support"]},
                {"name": "Team", "price": 399, "per": "month", "features": ["Version control", "Multiple editors", "SSO"]},
                {"name": "Enterprise", "price": None, "per": "custom", "features": ["Dedicated infrastructure", "Custom compliance", "SLA"]}
            ],
            "starting_price": 0,
            "free_tier": True,
            "annual_discount_percent": 20
        },
        "company_sizes": ["startup", "smb", "mid_market", "enterprise"],
        "industries": ["*"],
        "best_for": [
            "Non-technical founders",
            "MVPs and prototypes",
            "Internal tools",
            "Marketplace and SaaS apps"
        ],
        "avoid_if": [
            "Need extreme performance",
            "Very complex custom logic",
            "Budget concerns with scaling (workload costs)"
        ],
        "our_rating": 4.4,
        "our_notes": "Most proven no-code platform. 10+ years. Workload pricing can surprise at scale. Best for MVPs through mid-scale apps.",
        "g2_score": 4.4,
        "g2_reviews": 300,
        "capterra_score": 4.5,
        "capterra_reviews": 400,
        "implementation_weeks": 2,
        "implementation_complexity": "medium",
        "requires_developer": False,
        "api_available": True,
        "api_type": "REST",
        "api_docs_url": "https://manual.bubble.io/core-resources/api",
        "api_openness_score": 4,
        "has_webhooks": True,
        "zapier_integration": True,
        "make_integration": True,
        "competitors": ["retool", "glide", "softr"],
        "key_capabilities": ["Visual app builder", "Database included", "User auth", "API integrations", "Responsive design"],
        "verified_at": datetime.now(tz=timezone.utc).isoformat(),
        "verified_by": "claude-code",
        "source_url": "https://bubble.io/pricing",
        "status": "active"
    },

    # =========================================================================
    # AI VOICE
    # =========================================================================
    {
        "slug": "deepgram",
        "name": "Deepgram",
        "category": "ai_voice",
        "subcategory": "speech_api",
        "website": "https://deepgram.com",
        "pricing_url": "https://deepgram.com/pricing",
        "description": "Enterprise voice AI platform with STT, TTS, and Voice Agent APIs. $200 free credits for new users. Used for transcription, voice bots, and real-time speech. 30+ languages.",
        "tagline": "Enterprise Voice AI",
        "pricing": {
            "model": "usage_based",
            "currency": "USD",
            "tiers": [
                {"name": "Pay-as-you-go", "price": None, "per": "usage", "features": ["$200 free credits", "STT: $0.0077/min", "TTS: $0.030/1k chars", "No minimum"]},
                {"name": "Growth", "price": None, "per": "usage", "features": ["Volume discounts", "STT: $0.0065/min", "Priority support"]},
                {"name": "Enterprise", "price": None, "per": "custom", "features": ["Custom pricing", "SLA", "Dedicated support"]}
            ],
            "starting_price": 0,
            "free_tier": True,
            "startup_discount": "$200 free credits"
        },
        "company_sizes": ["startup", "smb", "mid_market", "enterprise"],
        "industries": ["*"],
        "best_for": [
            "Voice bot development",
            "Transcription at scale",
            "Real-time speech apps",
            "Developers building voice AI"
        ],
        "avoid_if": [
            "Need consumer-ready voices (ElevenLabs better)",
            "Simple one-off transcription needs",
            "No developer resources"
        ],
        "our_rating": 4.5,
        "our_notes": "$200 free credits is generous. Best for developers building voice apps. STT is enterprise-grade. TTS is functional but ElevenLabs sounds better.",
        "implementation_weeks": 1,
        "implementation_complexity": "medium",
        "requires_developer": True,
        "api_available": True,
        "api_type": "REST",
        "api_docs_url": "https://developers.deepgram.com",
        "api_openness_score": 5,
        "has_webhooks": True,
        "has_oauth": False,
        "competitors": ["elevenlabs", "assembly-ai", "whisper"],
        "key_capabilities": ["Speech-to-text", "Text-to-speech", "Voice agents", "Real-time streaming", "30+ languages"],
        "verified_at": datetime.now(tz=timezone.utc).isoformat(),
        "verified_by": "claude-code",
        "source_url": "https://deepgram.com/pricing",
        "status": "active"
    },
    {
        "slug": "elevenlabs",
        "name": "ElevenLabs",
        "category": "ai_voice",
        "subcategory": "text_to_speech",
        "website": "https://elevenlabs.io",
        "pricing_url": "https://elevenlabs.io/pricing",
        "description": "Best-in-class AI voice generation. Known for most realistic, emotional voices. Voice cloning, 32+ languages. Used for content creation, audiobooks, games, voice agents.",
        "tagline": "AI Voice Generator",
        "pricing": {
            "model": "credits",
            "currency": "USD",
            "tiers": [
                {"name": "Free", "price": 0, "per": "month", "features": ["10,000 credits (20k chars)", "Pre-made voices", "Non-commercial"]},
                {"name": "Starter", "price": 5, "per": "month", "features": ["30,000 credits", "Voice cloning", "Commercial use"]},
                {"name": "Creator", "price": 22, "per": "month", "features": ["100,000 credits", "Professional voice cloning"]},
                {"name": "Pro", "price": 99, "per": "month", "features": ["500,000 credits", "Highest quality", "Priority support"]},
                {"name": "Scale", "price": 330, "per": "month", "features": ["2M credits", "Usage dashboard", "API priority"]}
            ],
            "starting_price": 0,
            "free_tier": True
        },
        "company_sizes": ["startup", "smb", "mid_market", "enterprise"],
        "industries": ["*"],
        "best_for": [
            "Content creators needing realistic voices",
            "Audiobook production",
            "Voice agents and chatbots",
            "Video voiceovers",
            "Game developers"
        ],
        "avoid_if": [
            "Just need basic TTS",
            "Very high volume (costs add up)",
            "Need STT (speech-to-text)"
        ],
        "our_rating": 4.7,
        "our_notes": "Best voice quality in the market. Emotional expression is remarkable. Credit-based pricing requires planning. Voice cloning is powerful.",
        "g2_score": 4.1,
        "g2_reviews": 126,
        "implementation_weeks": 1,
        "implementation_complexity": "low",
        "requires_developer": False,
        "api_available": True,
        "api_type": "REST",
        "api_docs_url": "https://elevenlabs.io/docs",
        "api_openness_score": 5,
        "has_webhooks": True,
        "has_oauth": False,
        "competitors": ["deepgram", "play-ht", "murf"],
        "key_capabilities": ["Text-to-speech", "Voice cloning", "70+ languages", "Emotional expression", "Real-time streaming"],
        "verified_at": datetime.now(tz=timezone.utc).isoformat(),
        "verified_by": "claude-code",
        "source_url": "https://elevenlabs.io/pricing",
        "status": "active"
    },

    # =========================================================================
    # AI VIDEO
    # =========================================================================
    {
        "slug": "descript",
        "name": "Descript",
        "category": "ai_video",
        "subcategory": "video_editing",
        "website": "https://www.descript.com",
        "pricing_url": "https://www.descript.com/pricing",
        "description": "AI-powered video and podcast editing. Edit video by editing text transcript. Features like filler word removal, Studio Sound, and AI actions. 95% transcription accuracy in 25+ languages.",
        "tagline": "Edit video like a doc",
        "pricing": {
            "model": "media_minutes",
            "currency": "USD",
            "tiers": [
                {"name": "Free", "price": 0, "per": "month", "features": ["60 media minutes/month", "100 AI credits (one-time)", "Basic editing"]},
                {"name": "Hobbyist", "price": 16, "per": "month", "features": ["10 hrs transcription", "1080p export", "Basic AI"]},
                {"name": "Creator", "price": 30, "per": "month", "features": ["1,800 media min", "800 AI credits", "Studio Sound"]},
                {"name": "Business", "price": 48, "per": "month", "features": ["More media min", "Advanced features", "Priority support"]}
            ],
            "starting_price": 0,
            "free_tier": True
        },
        "company_sizes": ["startup", "smb", "mid_market"],
        "industries": ["*"],
        "best_for": [
            "Podcasters",
            "YouTube creators",
            "Course creators",
            "Anyone editing talking-head video"
        ],
        "avoid_if": [
            "Need cinematic editing (color grading, VFX)",
            "Complex multi-layer timelines",
            "High-volume production at scale"
        ],
        "our_rating": 4.3,
        "our_notes": "Revolutionary for podcast/video editing. Transcript-based editing is game-changing. New pricing (Sept 2025) is more complex. Not for Hollywood production.",
        "g2_score": 4.4,
        "g2_reviews": 200,
        "implementation_weeks": 0,
        "implementation_complexity": "low",
        "requires_developer": False,
        "api_available": False,
        "competitors": ["adobe-premiere", "final-cut", "capcut"],
        "key_capabilities": ["Transcript editing", "Filler word removal", "Studio Sound", "AI actions", "Multi-track"],
        "verified_at": datetime.now(tz=timezone.utc).isoformat(),
        "verified_by": "claude-code",
        "source_url": "https://www.descript.com/pricing",
        "status": "active"
    },
    {
        "slug": "synthesia",
        "name": "Synthesia",
        "category": "ai_video",
        "subcategory": "ai_avatars",
        "website": "https://www.synthesia.io",
        "pricing_url": "https://www.synthesia.io/pricing",
        "description": "AI video platform with 230+ avatars in 140+ languages. Used by 60,000+ companies including 90% of Fortune 100. Create videos from text without cameras or actors.",
        "tagline": "#1 AI Video Platform for Business",
        "pricing": {
            "model": "video_minutes",
            "currency": "USD",
            "tiers": [
                {"name": "Free", "price": 0, "per": "month", "features": ["3 min video/month", "9 avatars", "Basic features"]},
                {"name": "Starter", "price": 18, "per": "month", "features": ["10 min/month (120/yr)", "125+ avatars", "3 personal avatars"], "billing": "annual"},
                {"name": "Creator", "price": 64, "per": "month", "features": ["30 min/month", "180+ avatars", "5 personal avatars"], "billing": "annual"},
                {"name": "Enterprise", "price": None, "per": "custom", "features": ["Unlimited video", "230+ avatars", "Custom avatars", "SOC 2"]}
            ],
            "starting_price": 0,
            "free_tier": True,
            "annual_discount_percent": 38
        },
        "company_sizes": ["smb", "mid_market", "enterprise"],
        "industries": ["*"],
        "best_for": [
            "Training and onboarding videos",
            "Marketing videos at scale",
            "Multi-language content",
            "Corporate communications"
        ],
        "avoid_if": [
            "Need highly creative/artistic video",
            "Real human connection required",
            "Very high volume without enterprise plan"
        ],
        "our_rating": 4.5,
        "our_notes": "Market leader in AI avatars. Express-2 avatars are convincing. Enterprise-focused pricing. Custom avatars are $1000/yr add-on. Great for training videos.",
        "g2_score": 4.6,
        "g2_reviews": 350,
        "implementation_weeks": 1,
        "implementation_complexity": "low",
        "requires_developer": False,
        "api_available": True,
        "api_type": "REST",
        "api_docs_url": "https://docs.synthesia.io",
        "api_openness_score": 4,
        "has_webhooks": True,
        "competitors": ["heygen", "colossyan", "hour-one"],
        "key_capabilities": ["AI avatars", "140+ languages", "Custom avatars", "Templates", "Brand kits"],
        "verified_at": datetime.now(tz=timezone.utc).isoformat(),
        "verified_by": "claude-code",
        "source_url": "https://www.synthesia.io/pricing",
        "status": "active"
    },
    {
        "slug": "heygen",
        "name": "HeyGen",
        "category": "ai_video",
        "subcategory": "ai_avatars",
        "website": "https://www.heygen.com",
        "pricing_url": "https://www.heygen.com/pricing",
        "description": "AI video platform with 230+ avatars. G2's #1 Fastest Growing Product 2025. Features video translation (175+ languages) and real-time interactive avatars. Used by 100,000+ businesses.",
        "tagline": "Free AI Video Generator",
        "pricing": {
            "model": "credits",
            "currency": "USD",
            "tiers": [
                {"name": "Free", "price": 0, "per": "month", "features": ["3 videos/month", "720p", "Basic avatars"]},
                {"name": "Creator", "price": 29, "per": "month", "features": ["Unlimited videos", "1080p", "175+ languages", "Voice cloning"]},
                {"name": "Team", "price": 39, "per": "seat/month", "features": ["4K export", "Custom avatars", "Collaboration", "Priority"]},
                {"name": "Enterprise", "price": None, "per": "custom", "features": ["API access", "SSO", "Custom workflows"]}
            ],
            "starting_price": 0,
            "free_tier": True
        },
        "company_sizes": ["startup", "smb", "mid_market", "enterprise"],
        "industries": ["*"],
        "best_for": [
            "Marketing videos",
            "Video translation/localization",
            "Social media content",
            "Personalized outreach"
        ],
        "avoid_if": [
            "Need enterprise compliance on lower tier",
            "Require very specific avatar control"
        ],
        "our_rating": 4.5,
        "our_notes": "Strong competitor to Synthesia. Faster growth. Video translation is standout feature. Avatar IV (Aug 2025) is impressively realistic.",
        "g2_score": 4.8,
        "g2_reviews": 630,
        "implementation_weeks": 0,
        "implementation_complexity": "low",
        "requires_developer": False,
        "api_available": True,
        "api_type": "REST",
        "api_openness_score": 4,
        "has_webhooks": True,
        "competitors": ["synthesia", "colossyan", "d-id"],
        "key_capabilities": ["AI avatars", "Video translation", "Real-time avatars", "Voice cloning", "175+ languages"],
        "verified_at": datetime.now(tz=timezone.utc).isoformat(),
        "verified_by": "claude-code",
        "source_url": "https://www.heygen.com/pricing",
        "status": "active"
    },

    # =========================================================================
    # DATA SCRAPING
    # =========================================================================
    {
        "slug": "apify",
        "name": "Apify",
        "category": "data_scraping",
        "subcategory": "web_scraping",
        "website": "https://apify.com",
        "pricing_url": "https://apify.com/pricing",
        "description": "Full-stack web scraping platform with 10,000+ ready-made scrapers (Actors). Used by Microsoft, Siemens, Accenture. SOC2, GDPR, CCPA compliant. Great for lead generation and data extraction.",
        "tagline": "Full-stack web scraping and data extraction platform",
        "pricing": {
            "model": "usage_based",
            "currency": "USD",
            "tiers": [
                {"name": "Free", "price": 0, "per": "month", "features": ["$5 platform credits", "Basic features"]},
                {"name": "Starter", "price": 49, "per": "month", "features": ["$49 platform credits", "Scheduling", "Webhooks"]},
                {"name": "Scale", "price": 199, "per": "month", "features": ["$199 platform credits", "Priority support", "Team features"]},
                {"name": "Business", "price": 999, "per": "month", "features": ["$999 platform credits", "Dedicated support", "SLA"]}
            ],
            "starting_price": 0,
            "free_tier": True
        },
        "company_sizes": ["startup", "smb", "mid_market", "enterprise"],
        "industries": ["*"],
        "best_for": [
            "Lead generation at scale",
            "Competitor monitoring",
            "E-commerce price tracking",
            "Data enrichment pipelines"
        ],
        "avoid_if": [
            "Simple one-off scraping (try free tools)",
            "No developer for custom scrapers",
            "Very limited budget"
        ],
        "our_rating": 4.4,
        "our_notes": "Most complete scraping platform. 10k+ ready Actors. Enterprise-grade. Credit pricing requires planning. Best for ongoing data needs vs one-off.",
        "g2_score": 4.5,
        "g2_reviews": 100,
        "implementation_weeks": 1,
        "implementation_complexity": "medium",
        "requires_developer": False,
        "api_available": True,
        "api_type": "REST",
        "api_docs_url": "https://docs.apify.com",
        "api_openness_score": 5,
        "has_webhooks": True,
        "has_oauth": True,
        "zapier_integration": True,
        "make_integration": True,
        "n8n_integration": True,
        "competitors": ["firecrawl", "browserbase", "scrapy"],
        "key_capabilities": ["10k+ scrapers", "Proxy management", "Browser automation", "Scheduling", "API integrations"],
        "verified_at": datetime.now(tz=timezone.utc).isoformat(),
        "verified_by": "claude-code",
        "source_url": "https://apify.com/pricing",
        "status": "active"
    },

    # =========================================================================
    # AI IMAGE GENERATION
    # =========================================================================
    {
        "slug": "midjourney",
        "name": "MidJourney",
        "category": "ai_content_creation",
        "subcategory": "image_generation",
        "website": "https://www.midjourney.com",
        "pricing_url": "https://docs.midjourney.com/hc/en-us/articles/27870484040333-Comparing-Midjourney-Plans",
        "description": "Leading AI image generation platform known for exceptionally high-quality, artistic outputs. Create stunning images from text prompts for marketing, branding, concept art, and creative projects. Known for cinematic, stylized aesthetic that sets it apart from competitors.",
        "tagline": "Explore new mediums of thought",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "tiers": [
                {"name": "Basic", "price": 10, "per": "month", "features": ["~200 generations/month", "3.3 Fast GPU hours", "Commercial usage"]},
                {"name": "Standard", "price": 30, "per": "month", "features": ["~900 generations/month", "15 Fast GPU hours", "Unlimited Relax Mode"]},
                {"name": "Pro", "price": 60, "per": "month", "features": ["~1,800 generations/month", "30 Fast GPU hours", "Stealth Mode"]},
                {"name": "Mega", "price": 120, "per": "month", "features": ["~3,600 generations/month", "60 Fast GPU hours", "Stealth Mode"]}
            ],
            "starting_price": 10,
            "free_tier": False
        },
        "company_sizes": ["individual", "startup", "smb", "mid_market"],
        "industries": ["Marketing", "Advertising", "Content Creation", "Gaming", "Architecture", "Fashion"],
        "best_for": [
            "Marketing teams creating visual content",
            "Social media managers needing graphics",
            "Designers exploring concepts quickly",
            "Small businesses without design resources"
        ],
        "avoid_if": [
            "Need precise control over outputs",
            "Require photorealistic product shots",
            "Companies >$1M revenue on Basic/Standard (TOS requires Pro)"
        ],
        "our_rating": 4.5,
        "our_notes": "Best-in-class image quality and artistic style. Standard plan at $30/mo is sweet spot with unlimited Relax Mode. No free tier. Pro required for larger businesses per TOS.",
        "g2_score": 4.4,
        "g2_reviews": 150,
        "implementation_weeks": 0,
        "implementation_complexity": "low",
        "requires_developer": False,
        "api_available": False,
        "competitors": ["dall-e-3", "stable-diffusion", "adobe-firefly", "leonardo-ai", "ideogram"],
        "key_capabilities": ["Text-to-image", "Image variations", "Style tuning", "Pan and zoom", "High-resolution outputs"],
        "verified_at": datetime.now(tz=timezone.utc).isoformat(),
        "verified_by": "claude-code",
        "source_url": "https://docs.midjourney.com",
        "status": "active"
    },

    # =========================================================================
    # AI PRODUCTIVITY
    # =========================================================================
    {
        "slug": "granola-ai",
        "name": "Granola",
        "category": "ai_productivity",
        "subcategory": "meeting_notes",
        "website": "https://www.granola.ai",
        "pricing_url": "https://www.granola.ai/pricing",
        "description": "AI meeting notes app that records on your device (not via bot) and generates transcripts, summaries, and action items. Works across Zoom, Google Meet, and Teams without other participants knowing. Features cross-meeting search and AI chat to query past conversations.",
        "tagline": "AI notepad for meetings",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "tiers": [
                {"name": "Free", "price": 0, "per": "month", "features": ["25 meetings total", "14-day history", "Basic AI notes"]},
                {"name": "Individual", "price": 18, "per": "user/month", "features": ["Unlimited meetings", "Full history", "Advanced AI notes"]},
                {"name": "Business", "price": 14, "per": "user/month", "features": ["All Individual features", "Team collaboration", "Admin controls"]},
                {"name": "Enterprise", "price": 35, "per": "user/month", "features": ["All Business features", "SSO", "Opt-out of AI training"]}
            ],
            "starting_price": 14,
            "free_tier": True
        },
        "company_sizes": ["individual", "startup", "smb", "mid_market", "enterprise"],
        "industries": ["Consulting", "Sales", "Professional Services", "Technology", "Finance", "Legal"],
        "best_for": [
            "Professionals in many meetings per day",
            "Consultants tracking client conversations",
            "Sales teams documenting prospect calls",
            "Privacy-conscious users"
        ],
        "avoid_if": [
            "Need shared recordings (Granola doesn't allow playback)",
            "Require compliance/audit trail of recordings",
            "Want participants to know they're being recorded"
        ],
        "our_rating": 4.7,
        "our_notes": "Top choice among technical AI users. Local recording approach is unique - no awkward bot joining calls. Raised $43M in May 2025 at $250M valuation.",
        "implementation_weeks": 0,
        "implementation_complexity": "low",
        "requires_developer": False,
        "api_available": False,
        "integrations": ["Zoom", "Google Meet", "Microsoft Teams", "Slack", "Notion", "HubSpot", "Salesforce"],
        "competitors": ["otter-ai", "fireflies-ai", "tl-dv", "fathom", "grain", "read-ai"],
        "key_capabilities": ["Local recording", "Automatic transcription", "AI summaries", "Action items", "Cross-meeting search", "AI chat"],
        "verified_at": datetime.now(tz=timezone.utc).isoformat(),
        "verified_by": "claude-code",
        "source_url": "https://www.granola.ai/pricing",
        "status": "active"
    },

    # =========================================================================
    # AI APP BUILDERS (additional)
    # =========================================================================
    {
        "slug": "lovable",
        "name": "Lovable",
        "category": "ai_app_builders",
        "subcategory": "no_code_app_builder",
        "website": "https://lovable.dev",
        "pricing_url": "https://lovable.dev/pricing",
        "description": "AI-powered no-code app builder that turns natural language prompts into production-ready full-stack applications. Generates React code with Supabase backend integration. Features Agent Mode for autonomous debugging. Used by Klarna, Uber, Zendesk for internal tools.",
        "tagline": "Build apps & websites with AI, fast",
        "pricing": {
            "model": "credits",
            "currency": "USD",
            "tiers": [
                {"name": "Free", "price": 0, "per": "month", "features": ["5 credits/day", "Public projects only"]},
                {"name": "Pro", "price": 25, "per": "month", "features": ["100 monthly credits + 5 daily", "Private projects", "Custom domains", "Code editing"]},
                {"name": "Business", "price": 50, "per": "month", "features": ["100 monthly credits", "SSO", "Opt out of data training"]}
            ],
            "starting_price": 25,
            "free_tier": True
        },
        "company_sizes": ["individual", "startup", "smb", "mid_market", "enterprise"],
        "industries": ["Startups", "Enterprise", "Agencies", "SaaS", "Operations"],
        "best_for": [
            "Non-technical founders building MVPs",
            "Internal tool development",
            "Rapid prototyping",
            "Agencies creating client apps quickly"
        ],
        "avoid_if": [
            "Need highly custom UI/UX",
            "Require complex backend logic beyond CRUD",
            "Need mobile-native apps (web-focused)"
        ],
        "our_rating": 4.5,
        "our_notes": "Leading AI app builder. $330M Series B at $6.6B valuation (Dec 2025). Export option avoids vendor lock-in. Credit-based system requires understanding consumption.",
        "implementation_weeks": 0,
        "implementation_complexity": "low",
        "requires_developer": False,
        "api_available": False,
        "integrations": ["Supabase", "GitHub", "Stripe", "Custom APIs"],
        "competitors": ["bolt-new", "v0-dev", "replit", "cursor", "retool"],
        "key_capabilities": ["Natural language to code", "Full-stack generation", "Supabase integration", "Agent Mode", "Code export", "Custom domains"],
        "verified_at": datetime.now(tz=timezone.utc).isoformat(),
        "verified_by": "claude-code",
        "source_url": "https://lovable.dev/pricing",
        "status": "active"
    },

    # =========================================================================
    # AI KNOWLEDGE / SUPPORT
    # =========================================================================
    {
        "slug": "buddypro-ai",
        "name": "BuddyPro",
        "category": "customer_support",
        "subcategory": "ai_knowledge_expert",
        "website": "https://buddypro.ai",
        "pricing_url": "https://buddypro.ai",
        "description": "AI knowledge expert platform that lets you create AI assistants trained on your specific content and expertise. Unlike typical chatbots, BuddyPro creates a premium AI service you can sell to clients. White-label solution with integrated Stripe payments for monetization.",
        "tagline": "Train your AI expert based on your knowledge",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "note": "Contact for pricing",
            "custom_pricing": True
        },
        "company_sizes": ["individual", "startup", "smb"],
        "industries": ["Consulting", "Coaching", "Education", "Professional Services", "Expert Services"],
        "best_for": [
            "Consultants scaling expertise",
            "Course creators extending value",
            "Experts monetizing knowledge 24/7",
            "Thought leaders building AI versions of themselves"
        ],
        "avoid_if": [
            "Need standard customer support deflection",
            "Don't have substantial existing content",
            "Need enterprise compliance features"
        ],
        "our_rating": 4.3,
        "our_notes": "Unique positioning as monetizable AI expert rather than cost-center chatbot. Good for consultants and coaches. No public pricing is a barrier.",
        "implementation_weeks": 2,
        "implementation_complexity": "low",
        "requires_developer": False,
        "api_available": False,
        "integrations": ["Stripe", "Website embed"],
        "competitors": ["coachvox", "delphi-ai", "chatbase", "customgpt"],
        "key_capabilities": ["Train on your content", "White-label branding", "Stripe payments", "Subscription management", "No-code setup"],
        "verified_at": datetime.now(tz=timezone.utc).isoformat(),
        "verified_by": "claude-code",
        "source_url": "https://buddypro.ai",
        "status": "active"
    },

    # =========================================================================
    # AI VOICE AGENTS
    # =========================================================================
    {
        "slug": "youratlas",
        "name": "YourAtlas",
        "category": "ai_sales_tools",
        "subcategory": "ai_voice_agents",
        "website": "https://youratlas.com",
        "pricing_url": "https://youratlas.com",
        "description": "AI sales agent platform that handles inbound and outbound calls, qualifies leads, and books appointments 24/7. Engages leads via Voice, SMS, or Chat within 60 seconds. White-glove onboarding builds your entire revenue engine. Backed by Dan Martell's Martell Ventures.",
        "tagline": "AI Sales Agents for Service Business Owners",
        "pricing": {
            "model": "custom",
            "currency": "USD",
            "note": "Consultation required - no public pricing",
            "guarantee": "90-day results guarantee",
            "custom_pricing": True
        },
        "company_sizes": ["smb", "mid_market"],
        "industries": ["Home Services", "Real Estate", "Legal", "Healthcare", "Insurance", "Automotive"],
        "best_for": [
            "Service businesses with high call volume",
            "Companies with ad spend driving inbound leads",
            "Businesses losing leads to slow response",
            "Teams wanting 24/7 phone coverage"
        ],
        "avoid_if": [
            "Low call volume",
            "No existing ad spend/lead flow",
            "Need transparent self-serve pricing"
        ],
        "our_rating": 4.4,
        "our_notes": "Portfolio company of Martell Ventures. White-glove approach reduces implementation burden. 90-day guarantee shows confidence. Best for service businesses with substantial lead flow.",
        "implementation_weeks": 2,
        "implementation_complexity": "low",
        "requires_developer": False,
        "api_available": False,
        "integrations": ["CRM systems", "Calendar tools", "Ad platforms"],
        "competitors": ["synthflow", "bland-ai", "air-ai", "vapi", "retell-ai"],
        "key_capabilities": ["AI voice agents", "Lead qualification", "Appointment booking", "SMS and chat", "60-second response", "Live call transfer"],
        "verified_at": datetime.now(tz=timezone.utc).isoformat(),
        "verified_by": "claude-code",
        "source_url": "https://youratlas.com",
        "status": "active"
    }
]


async def seed_vendors():
    """Seed all AI tools vendors to Supabase."""
    from src.config.supabase_client import get_async_supabase

    supabase = await get_async_supabase()

    created = 0
    updated = 0
    errors = []

    for vendor_data in AI_TOOLS_VENDORS:
        slug = vendor_data["slug"]
        try:
            # Check if vendor exists (without .single() to avoid error on 0 rows)
            result = await supabase.table("vendors").select("id").eq("slug", slug).execute()
            existing = result.data[0] if result.data else None

            if existing:
                # Update existing vendor
                vendor_data["updated_at"] = datetime.now(tz=timezone.utc).isoformat()
                update_result = await supabase.table("vendors").update(vendor_data).eq("slug", slug).execute()
                if update_result.data:
                    updated += 1
                    logger.info(f"Updated vendor: {slug}")
                else:
                    errors.append(f"Failed to update {slug}")
            else:
                # Create new vendor
                vendor_data["created_at"] = datetime.now(tz=timezone.utc).isoformat()
                vendor_data["updated_at"] = datetime.now(tz=timezone.utc).isoformat()
                create_result = await supabase.table("vendors").insert(vendor_data).execute()
                if create_result.data:
                    created += 1
                    logger.info(f"Created vendor: {slug}")
                else:
                    errors.append(f"Failed to create {slug}")

        except Exception as e:
            errors.append(f"Error with {slug}: {str(e)}")
            logger.error(f"Error with {slug}: {e}")

    print("\n" + "=" * 50)
    print("SEED COMPLETE")
    print("=" * 50)
    print(f"Created: {created}")
    print(f"Updated: {updated}")
    print(f"Errors: {len(errors)}")
    if errors:
        print("\nErrors:")
        for err in errors:
            print(f"  - {err}")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed_vendors())
