"""
AI Tool Recommendations

Centralized recommendations for AI models, tools, and development resources.
Used by report generation to provide specific, actionable custom solution guidance.

Last updated: 2024-12
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Load DIY resources from JSON
_DIY_RESOURCES: Optional[Dict[str, Any]] = None


def _load_diy_resources() -> Dict[str, Any]:
    """Load DIY resources from JSON file."""
    global _DIY_RESOURCES
    if _DIY_RESOURCES is not None:
        return _DIY_RESOURCES

    resources_path = Path(__file__).parent.parent / "knowledge" / "diy_resources.json"
    try:
        with open(resources_path, "r") as f:
            _DIY_RESOURCES = json.load(f)
            logger.info(f"Loaded DIY resources from {resources_path}")
    except FileNotFoundError:
        logger.warning(f"DIY resources file not found at {resources_path}")
        _DIY_RESOURCES = {}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse DIY resources: {e}")
        _DIY_RESOURCES = {}

    return _DIY_RESOURCES


# =============================================================================
# AI MODEL RECOMMENDATIONS BY USE CASE
# =============================================================================

AI_TOOL_RECOMMENDATIONS: Dict[str, Dict[str, Any]] = {
    "chatbot": {
        "model": "Claude Sonnet 4 (claude-sonnet-4-20250514)",
        "model_id": "claude-sonnet-4-20250514",
        "why": "Best balance of quality and cost for conversational AI. Excellent at maintaining context and following instructions.",
        "alternatives": [
            {"model": "GPT-4o", "why": "Lower cost, good for simpler conversations"},
            {"model": "Gemini 2.0 Flash", "why": "Fast responses, good for high-volume"},
        ],
        "api_pricing": {
            "input_per_1m_tokens": 3.00,
            "output_per_1m_tokens": 15.00,
            "currency": "USD",
        },
        "typical_monthly_cost": "€50-200 for SMB volume",
        "cursor_compatible": True,
    },
    "document_processing": {
        "model": "Claude Opus 4.5 (claude-opus-4-5-20250514)",
        "model_id": "claude-opus-4-5-20250514",
        "why": "Best for complex document understanding, extraction, and analysis. Handles nuanced interpretation.",
        "alternatives": [
            {"model": "Claude Sonnet 4", "why": "Good enough for simpler docs, 5x cheaper"},
            {"model": "GPT-4 Turbo", "why": "Strong alternative, different strengths"},
        ],
        "api_pricing": {
            "input_per_1m_tokens": 15.00,
            "output_per_1m_tokens": 75.00,
            "currency": "USD",
        },
        "typical_monthly_cost": "€100-500 depending on volume",
        "cursor_compatible": True,
    },
    "code_generation": {
        "model": "Claude Sonnet 4 via Cursor",
        "model_id": "claude-sonnet-4-20250514",
        "why": "Cursor IDE provides best developer experience with Claude. Inline editing, tab completion, chat.",
        "alternatives": [
            {"model": "GitHub Copilot", "why": "Tighter IDE integration, subscription model"},
            {"model": "Codeium", "why": "Free tier available, good for individuals"},
        ],
        "api_pricing": {
            "cursor_pro": 20.00,
            "currency": "USD",
            "period": "month",
        },
        "typical_monthly_cost": "€20/developer",
        "cursor_compatible": True,
    },
    "data_analysis": {
        "model": "Gemini 2.5 Pro",
        "model_id": "gemini-2.5-pro",
        "why": "2M token context window handles large datasets. Good at pattern recognition and summarization.",
        "alternatives": [
            {"model": "Claude Sonnet 4", "why": "200K context, use pagination for larger data"},
            {"model": "GPT-4 Turbo", "why": "128K context, strong analytical capabilities"},
        ],
        "api_pricing": {
            "input_per_1m_tokens": 1.25,
            "output_per_1m_tokens": 5.00,
            "currency": "USD",
        },
        "typical_monthly_cost": "€30-150 depending on data volume",
        "cursor_compatible": False,
    },
    "automation": {
        "model": "Claude Haiku 3.5 (claude-3-5-haiku-20241022)",
        "model_id": "claude-3-5-haiku-20241022",
        "why": "Fast and cheap for high-volume automation tasks. Great for classification, extraction, routing.",
        "alternatives": [
            {"model": "GPT-4o-mini", "why": "Similar price/performance, OpenAI ecosystem"},
            {"model": "Gemini Flash", "why": "Very fast, good for real-time applications"},
        ],
        "api_pricing": {
            "input_per_1m_tokens": 0.80,
            "output_per_1m_tokens": 4.00,
            "currency": "USD",
        },
        "typical_monthly_cost": "€10-50 for moderate automation",
        "cursor_compatible": True,
    },
    "voice_transcription": {
        "model": "Deepgram Nova-2",
        "model_id": "nova-2",
        "why": "Best accuracy/cost ratio for real-time transcription. Low latency, good speaker diarization.",
        "alternatives": [
            {"model": "OpenAI Whisper API", "why": "Very accurate, higher latency"},
            {"model": "AssemblyAI", "why": "Good real-time, strong entity detection"},
        ],
        "api_pricing": {
            "per_minute": 0.0043,
            "currency": "USD",
        },
        "typical_monthly_cost": "€20-100 depending on audio volume",
        "cursor_compatible": False,
    },
    "image_generation": {
        "model": "DALL-E 3 or Midjourney",
        "model_id": "dall-e-3",
        "why": "DALL-E 3 for API integration, Midjourney for highest quality creative work.",
        "alternatives": [
            {"model": "Stable Diffusion XL", "why": "Self-hosted option, no per-image cost"},
            {"model": "Leonardo.ai", "why": "Good UI, consistent style"},
        ],
        "api_pricing": {
            "per_image_standard": 0.04,
            "per_image_hd": 0.08,
            "currency": "USD",
        },
        "typical_monthly_cost": "€20-200 depending on volume",
        "cursor_compatible": False,
    },
    "email_assistant": {
        "model": "Claude Haiku 3.5 or GPT-4o-mini",
        "model_id": "claude-3-5-haiku-20241022",
        "why": "Fast, cheap, perfect for drafting and summarizing emails. Low latency for real-time assist.",
        "alternatives": [
            {"model": "Claude Sonnet 4", "why": "Better quality for complex emails"},
            {"model": "Superhuman AI", "why": "Integrated solution if using Superhuman"},
        ],
        "api_pricing": {
            "input_per_1m_tokens": 0.80,
            "output_per_1m_tokens": 4.00,
            "currency": "USD",
        },
        "typical_monthly_cost": "€5-30 per user",
        "cursor_compatible": True,
    },
    "content_generation": {
        "model": "Claude Sonnet 4 (claude-sonnet-4-20250514)",
        "model_id": "claude-sonnet-4-20250514",
        "why": "Excellent writing quality, follows brand voice instructions well, good at long-form.",
        "alternatives": [
            {"model": "GPT-4o", "why": "Strong alternative, different writing style"},
            {"model": "Jasper/Copy.ai", "why": "Purpose-built UI for marketing teams"},
        ],
        "api_pricing": {
            "input_per_1m_tokens": 3.00,
            "output_per_1m_tokens": 15.00,
            "currency": "USD",
        },
        "typical_monthly_cost": "€50-300 for content teams",
        "cursor_compatible": True,
    },
    "customer_support": {
        "model": "Claude Sonnet 4 with RAG",
        "model_id": "claude-sonnet-4-20250514",
        "why": "Combine with knowledge base retrieval for accurate, on-brand support responses.",
        "alternatives": [
            {"model": "Intercom Fin", "why": "Turnkey solution, integrated ticketing"},
            {"model": "Zendesk AI", "why": "Enterprise-grade, existing Zendesk users"},
        ],
        "api_pricing": {
            "input_per_1m_tokens": 3.00,
            "output_per_1m_tokens": 15.00,
            "currency": "USD",
        },
        "typical_monthly_cost": "€100-500 + vector DB costs",
        "cursor_compatible": True,
    },
}


# =============================================================================
# DEVELOPMENT TOOLS & STACK RECOMMENDATIONS
# =============================================================================

DEV_TOOLS: Dict[str, Any] = {
    "ide": {
        "recommended": "Cursor",
        "why": "Best AI-assisted coding experience. Native Claude/GPT integration.",
        "pricing": {"pro": 20, "currency": "USD", "period": "month"},
        "url": "https://cursor.com",
        "alternatives": ["VS Code + Continue", "GitHub Copilot in VS Code"],
    },
    "version_control": {
        "recommended": "GitHub",
        "why": "Industry standard, best CI/CD integration, Copilot native.",
        "pricing": {"team": 4, "currency": "USD", "period": "user/month"},
        "url": "https://github.com",
    },
}

HOSTING_RECOMMENDATIONS: Dict[str, Dict[str, Any]] = {
    "frontend": {
        "recommended": "Vercel",
        "why": "Zero-config deployments, excellent DX, global CDN.",
        "pricing": {
            "hobby": 0,
            "pro": 20,
            "currency": "USD",
            "period": "month",
        },
        "url": "https://vercel.com",
        "best_for": ["React", "Next.js", "static sites"],
        "alternatives": ["Netlify", "Cloudflare Pages"],
    },
    "backend": {
        "recommended": "Railway",
        "why": "Simple deployments, good free tier, scales well.",
        "pricing": {
            "hobby": 5,
            "pro": 20,
            "currency": "USD",
            "period": "month",
        },
        "url": "https://railway.app",
        "best_for": ["Python", "Node.js", "Docker"],
        "alternatives": ["Render", "Fly.io", "AWS Lambda"],
    },
    "database": {
        "recommended": "Supabase",
        "why": "Postgres + Auth + Realtime + Storage. Great DX, generous free tier.",
        "pricing": {
            "free": 0,
            "pro": 25,
            "currency": "USD",
            "period": "month",
        },
        "url": "https://supabase.com",
        "best_for": ["Full-stack apps", "Real-time features", "Auth"],
        "alternatives": ["PlanetScale", "Neon", "Firebase"],
    },
    "vector_db": {
        "recommended": "Pinecone",
        "why": "Purpose-built for AI embeddings, serverless, fast.",
        "pricing": {
            "free": 0,
            "standard": 70,
            "currency": "USD",
            "period": "month",
        },
        "url": "https://pinecone.io",
        "best_for": ["RAG applications", "Semantic search"],
        "alternatives": ["Supabase pgvector", "Weaviate", "Qdrant"],
    },
}


# =============================================================================
# SKILLS REQUIREMENTS BY PROJECT TYPE
# =============================================================================

SKILLS_BY_PROJECT: Dict[str, List[str]] = {
    "chatbot": [
        "Python or TypeScript",
        "Basic API integration",
        "Prompt engineering fundamentals",
        "Simple frontend (React/HTML)",
    ],
    "document_processing": [
        "Python",
        "PDF/document parsing libraries",
        "Prompt engineering",
        "Data validation",
    ],
    "automation": [
        "Python or Node.js",
        "API integration",
        "Cron/scheduling",
        "Error handling patterns",
    ],
    "data_analysis": [
        "Python",
        "Pandas/data manipulation",
        "Basic statistics",
        "Visualization (optional)",
    ],
    "customer_support": [
        "Python or TypeScript",
        "RAG/vector search concepts",
        "API integration",
        "Basic frontend",
    ],
    "content_generation": [
        "Any programming language",
        "Prompt engineering",
        "API integration",
        "Content management basics",
    ],
}


# =============================================================================
# DOCUMENTATION & RESOURCES
# =============================================================================

AI_DOCUMENTATION: Dict[str, Dict[str, str]] = {
    "anthropic": {
        "api_docs": "https://docs.anthropic.com",
        "cookbook": "https://github.com/anthropics/anthropic-cookbook",
        "pricing": "https://anthropic.com/pricing",
        "sdk_python": "https://github.com/anthropics/anthropic-sdk-python",
        "sdk_typescript": "https://github.com/anthropics/anthropic-sdk-typescript",
    },
    "openai": {
        "api_docs": "https://platform.openai.com/docs",
        "cookbook": "https://cookbook.openai.com",
        "pricing": "https://openai.com/pricing",
    },
    "google": {
        "api_docs": "https://ai.google.dev/docs",
        "pricing": "https://ai.google.dev/pricing",
    },
}

DEV_RESOURCES: Dict[str, Dict[str, str]] = {
    "cursor": {
        "docs": "https://cursor.com/docs",
        "getting_started": "https://cursor.com/docs/get-started",
    },
    "vercel": {
        "docs": "https://vercel.com/docs",
        "templates": "https://vercel.com/templates",
    },
    "railway": {
        "docs": "https://docs.railway.app",
        "templates": "https://railway.app/templates",
    },
    "supabase": {
        "docs": "https://supabase.com/docs",
        "examples": "https://github.com/supabase/supabase/tree/master/examples",
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_ai_recommendation(use_case: str) -> Dict[str, Any]:
    """Get AI tool recommendation for a specific use case."""
    return AI_TOOL_RECOMMENDATIONS.get(use_case, AI_TOOL_RECOMMENDATIONS["automation"])


def get_recommended_stack(project_type: str = "general") -> Dict[str, Any]:
    """Get full recommended stack for a project type."""
    return {
        "ai_model": get_ai_recommendation(project_type),
        "ide": DEV_TOOLS["ide"],
        "hosting": {
            "frontend": HOSTING_RECOMMENDATIONS["frontend"],
            "backend": HOSTING_RECOMMENDATIONS["backend"],
            "database": HOSTING_RECOMMENDATIONS["database"],
        },
        "skills_required": SKILLS_BY_PROJECT.get(project_type, SKILLS_BY_PROJECT["automation"]),
        "documentation": AI_DOCUMENTATION,
        "resources": DEV_RESOURCES,
    }


def get_build_it_yourself_context(use_case: str) -> Dict[str, Any]:
    """
    Get complete context for Build It Yourself section generation.

    Returns all information needed for the custom solution option.
    """
    ai_rec = get_ai_recommendation(use_case)
    skills = SKILLS_BY_PROJECT.get(use_case, SKILLS_BY_PROJECT["automation"])

    return {
        "ai_model": {
            "name": ai_rec["model"],
            "model_id": ai_rec["model_id"],
            "why": ai_rec["why"],
            "pricing": ai_rec.get("api_pricing", {}),
            "typical_cost": ai_rec.get("typical_monthly_cost", "Varies"),
            "alternatives": ai_rec.get("alternatives", []),
        },
        "recommended_stack": {
            "ide": "Cursor with Claude integration",
            "frontend": "Vercel (React/Next.js)",
            "backend": "Railway (Python/FastAPI or Node.js)",
            "database": "Supabase (PostgreSQL + Auth)",
            "vector_db": "Pinecone or Supabase pgvector (if RAG needed)",
        },
        "skills_required": skills,
        "build_tools": [
            ai_rec["model"],
            "Cursor IDE",
            "Vercel",
            "Railway",
            "Supabase",
            "GitHub",
        ],
        "documentation": {
            "ai": AI_DOCUMENTATION.get("anthropic", {}),
            "hosting": DEV_RESOURCES,
        },
        "typical_timeline": {
            "experienced_developer": "40-80 hours",
            "learning_while_building": "80-160 hours",
        },
    }


# =============================================================================
# PROMPT CONTEXT GENERATOR
# =============================================================================

def get_ai_tools_prompt_context() -> str:
    """
    Generate context string for inclusion in recommendation prompts.

    This ensures the AI has accurate, current information about tools and pricing.
    """
    context = """
## AI TOOL RECOMMENDATIONS (Use these for custom solutions)

### By Use Case:
"""
    for use_case, details in AI_TOOL_RECOMMENDATIONS.items():
        context += f"""
**{use_case.replace('_', ' ').title()}:**
- Model: {details['model']}
- Why: {details['why']}
- Typical cost: {details.get('typical_monthly_cost', 'Varies')}
- Alternatives: {', '.join([a['model'] for a in details.get('alternatives', [])])}
"""

    context += """
### Recommended Development Stack:
- IDE: Cursor with Claude ($20/month)
- Frontend hosting: Vercel (free tier available)
- Backend hosting: Railway ($5-20/month)
- Database: Supabase (free tier available)
- Vector DB (for RAG): Pinecone or Supabase pgvector

### Skills Typically Required:
- Python or TypeScript
- Basic API integration
- Prompt engineering fundamentals
- Frontend basics (React or simple HTML)

### Documentation Links:
- Claude API: https://docs.anthropic.com
- Cursor: https://cursor.com/docs
- Vercel: https://vercel.com/docs
- Supabase: https://supabase.com/docs
"""
    return context


# =============================================================================
# DIY RESOURCES HELPERS
# =============================================================================

def get_diy_resources() -> Dict[str, Any]:
    """Get full DIY resources dictionary."""
    return _load_diy_resources()


def get_tutorials_for_use_case(use_case: str) -> List[Dict[str, str]]:
    """Get relevant tutorials for a specific use case."""
    resources = _load_diy_resources()
    tutorials = resources.get("tutorials_by_use_case", {})
    return tutorials.get(use_case, [])


def get_recommended_stack(stack_type: str = "standard_saas") -> Dict[str, Any]:
    """
    Get a recommended technology stack.

    Args:
        stack_type: One of "minimal_mvp", "standard_saas", "enterprise"
    """
    resources = _load_diy_resources()
    stacks = resources.get("recommended_stacks", {})
    return stacks.get(stack_type, stacks.get("standard_saas", {}))


def get_skills_for_project(project_type: str) -> Dict[str, Any]:
    """Get required and optional skills for a project type."""
    resources = _load_diy_resources()
    skills = resources.get("skills_by_project", {})
    return skills.get(project_type, {
        "required": ["Python or TypeScript", "API integration"],
        "optional": [],
        "learning_time": "2-4 weeks"
    })


def get_hosting_recommendation(layer: str) -> Dict[str, Any]:
    """
    Get hosting recommendation for a specific layer.

    Args:
        layer: One of "frontend", "backend", "database", "vector_database"
    """
    resources = _load_diy_resources()
    hosting = resources.get("hosting", {})
    layer_options = hosting.get(layer, {})

    # Return the first/recommended option
    if layer_options:
        first_key = list(layer_options.keys())[0]
        return layer_options[first_key]
    return {}


def get_ai_provider_info(provider: str = "anthropic") -> Dict[str, Any]:
    """Get detailed info about an AI provider."""
    resources = _load_diy_resources()
    providers = resources.get("ai_providers", {})
    return providers.get(provider, {})


def get_specialized_ai(category: str, service: str) -> Dict[str, Any]:
    """
    Get info about specialized AI services.

    Args:
        category: One of "voice_transcription", "image_generation", "embeddings"
        service: Service name within the category
    """
    resources = _load_diy_resources()
    specialized = resources.get("specialized_ai", {})
    category_services = specialized.get(category, {})
    return category_services.get(service, {})


def enrich_custom_solution_with_resources(use_case: str, custom_solution: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich a custom solution dict with DIY resources.

    Adds tutorials, detailed documentation links, and skill requirements.
    """
    resources = _load_diy_resources()

    # Get tutorials
    tutorials = get_tutorials_for_use_case(use_case)

    # Get skills
    skills_info = get_skills_for_project(use_case)

    # Get provider info
    provider_info = get_ai_provider_info("anthropic")

    # Get recommended stack
    stack = get_recommended_stack("standard_saas")

    # Enrich the custom solution
    enriched = {**custom_solution}

    enriched["resources"] = {
        "tutorials": tutorials[:3],  # Top 3 tutorials
        "documentation": {
            "ai_api": provider_info.get("docs", "https://docs.anthropic.com"),
            "cookbook": provider_info.get("cookbook", ""),
            "pricing": provider_info.get("pricing_page", ""),
        },
        "communities": [
            "Anthropic Discord",
            "r/ClaudeAI",
            "Claude API Forum"
        ]
    }

    enriched["skills_detail"] = {
        "required": skills_info.get("required", []),
        "optional": skills_info.get("optional", []),
        "estimated_learning_time": skills_info.get("learning_time", "2-4 weeks")
    }

    enriched["recommended_stack_detail"] = {
        "description": stack.get("description", ""),
        "components": {
            "ai": stack.get("ai", "Claude Sonnet"),
            "frontend": stack.get("frontend", "Vercel"),
            "backend": stack.get("backend", "Railway + FastAPI"),
            "database": stack.get("database", "Supabase"),
        },
        "estimated_monthly_cost": stack.get("estimated_monthly_cost", "50-200"),
        "setup_time": stack.get("setup_time", "1 week")
    }

    return enriched
