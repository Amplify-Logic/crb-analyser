"""
Import Professional Services Vendors to Supabase

Covers: Legal, Accounting/CPA, Consulting firms
Run: python -m src.scripts.import_professional_services_vendors
"""

import asyncio
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.config.supabase_client import get_async_supabase


PROFESSIONAL_SERVICES_VENDORS = [
    # ==========================================================================
    # TIER 1 - LEGAL PRACTICE MANAGEMENT
    # ==========================================================================
    {
        "slug": "clio",
        "name": "Clio",
        "category": "legal_practice_management",
        "website": "https://www.clio.com",
        "pricing_url": "https://www.clio.com/pricing/",
        "description": "Industry-leading legal practice management with built-in AI, used by 150,000+ lawyers. #1 ranked on G2.",
        "tagline": "#1 legal practice management",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 49,
            "free_tier": False,
            "free_trial_days": 7,
            "tiers": [
                {"name": "EasyStart", "price": 49, "per": "user/month"},
                {"name": "Essentials", "price": 89, "per": "user/month"},
                {"name": "Advanced", "price": 119, "per": "user/month"},
                {"name": "Expand", "price": 149, "per": "user/month"},
            ],
            "notes": "Add $10/mo for monthly billing. Clio Grow add-on +$49/user/mo."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["professional-services", "legal"],
        "best_for": ["law firms", "solo attorneys", "small-mid firms"],
        "key_capabilities": ["case management", "billing", "client portal", "document management", "AI features", "integrations"],
        "integrations": ["Lawmatics", "QuickBooks", "Dropbox", "Google Workspace", "200+ apps"],
        "g2_score": 4.4,
        "our_rating": 4.5,
        "our_notes": "#1 on G2 with most 5-star reviews. 150K+ lawyers. Separate modules increase cost.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    {
        "slug": "smokeball",
        "name": "Smokeball",
        "category": "legal_practice_management",
        "website": "https://www.smokeball.com",
        "description": "Cloud-based practice management with automatic time capture, document automation, and matter management.",
        "tagline": "Automatic time capture for law",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 39,
            "free_tier": False,
            "tiers": [
                {"name": "Bill", "price": 39, "per": "user/month"},
                {"name": "Boost", "price": 89, "per": "user/month"},
                {"name": "Grow", "price": 179, "per": "user/month"},
                {"name": "Prosper", "price": 219, "per": "user/month"},
            ],
            "notes": "Higher tiers needed for automation and advanced reporting."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["professional-services", "legal"],
        "best_for": ["small-mid law firms", "automatic time tracking", "document automation"],
        "key_capabilities": ["automatic time capture", "document automation", "matter management", "billing", "reporting"],
        "integrations": ["QuickBooks", "LawPay", "major legal tools"],
        "g2_score": 4.8,
        "our_rating": 4.6,
        "our_notes": "4.8/5 rating. Best automatic time capture. Some report slow performance with large docs.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    {
        "slug": "lawmatics",
        "name": "Lawmatics",
        "category": "legal_crm",
        "website": "https://www.lawmatics.com",
        "pricing_url": "https://www.lawmatics.com/pricing",
        "description": "#1 legal CRM with client intake, marketing automation, and pipeline management for law firms.",
        "tagline": "#1 CRM for law firms",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 99,
            "free_tier": False,
            "notes": "$99-199/mo depending on size. Custom quotes available."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["professional-services", "legal"],
        "best_for": ["client intake automation", "legal marketing", "lead management"],
        "key_capabilities": ["client intake", "CRM", "marketing automation", "pipeline management", "conflict checks", "e-signatures"],
        "integrations": ["Clio", "MyCase", "PracticePanther", "Smokeball", "Zapier", "CallRail"],
        "g2_score": 4.7,
        "our_rating": 4.5,
        "our_notes": "#1 legal CRM. Excellent intake automation. Setup can take time.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },

    # ==========================================================================
    # TIER 1 - ACCOUNTING PRACTICE MANAGEMENT
    # ==========================================================================
    {
        "slug": "karbon",
        "name": "Karbon",
        "category": "accounting_practice_management",
        "website": "https://karbonhq.com",
        "pricing_url": "https://karbonhq.com/pricing/",
        "description": "#1 ranked accounting practice management platform with workflow automation, team collaboration, and client management.",
        "tagline": "#1 accounting practice management",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 59,
            "free_tier": False,
            "free_trial_days": 14,
            "tiers": [
                {"name": "Team", "price": 59, "per": "user/month"},
                {"name": "Business", "price": 79, "per": "user/month"},
                {"name": "Enterprise", "price": None, "per": "user/month"},
            ],
            "notes": "5-user firm on Pro = ~$5,000/year. Extra costs for eSign, advanced reporting."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["professional-services", "accounting"],
        "best_for": ["accounting firms", "CPA firms", "bookkeeping practices"],
        "key_capabilities": ["workflow automation", "client management", "team collaboration", "email integration", "time tracking", "billing"],
        "integrations": ["QuickBooks", "Xero", "Gmail", "Outlook"],
        "g2_score": 4.8,
        "our_rating": 4.7,
        "our_notes": "#1 ranked. Business plan most popular. Extra costs for add-ons.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    {
        "slug": "taxdome",
        "name": "TaxDome",
        "category": "accounting_practice_management",
        "website": "https://taxdome.com",
        "pricing_url": "https://taxdome.com/pricing",
        "description": "All-in-one practice management for tax, bookkeeping, and accounting firms with client portal and workflow automation.",
        "tagline": "All-in-one for tax & accounting",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 58,
            "free_tier": False,
            "free_trial_days": 14,
            "tiers": [
                {"name": "Solo", "price": None, "per": "month"},
                {"name": "Pro", "price": 58, "per": "user/month"},
                {"name": "Business", "price": None, "per": "user/month"},
            ],
            "notes": "$58/user/mo on 3-year plan. $85/mo for seasonal staff. Annual billing required."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["professional-services", "accounting"],
        "best_for": ["tax firms", "bookkeeping firms", "client portal needs"],
        "key_capabilities": ["client portal", "workflow automation", "document management", "e-signatures", "IRS integration", "CRM"],
        "integrations": ["QuickBooks Online", "IRS", "major accounting tools"],
        "g2_score": 4.7,
        "our_rating": 4.5,
        "our_notes": "Excellent all-in-one value. Replaces multiple tools. Long-term commitment required.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    {
        "slug": "canopy",
        "name": "Canopy",
        "category": "accounting_practice_management",
        "website": "https://www.canopytax.com",
        "description": "Modular practice management for accounting firms - pay only for the features you need.",
        "tagline": "Modular accounting software",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 45,
            "free_tier": False,
            "notes": "~$45/user/month. Modular pricing - pay for what you need."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["professional-services", "accounting"],
        "best_for": ["firms wanting flexibility", "modular approach", "tax resolution"],
        "key_capabilities": ["CRM", "workflow", "document management", "tax tools", "client portal"],
        "integrations": ["QuickBooks", "Xero", "tax software"],
        "our_rating": 4.2,
        "our_notes": "Modular approach offers flexibility. Good for firms not needing everything.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },

    # ==========================================================================
    # TIER 1 - CONSULTING CRM
    # ==========================================================================
    {
        "slug": "hubspot-crm",
        "name": "HubSpot CRM",
        "category": "crm",
        "website": "https://www.hubspot.com",
        "description": "Leading CRM platform with marketing, sales, and service hubs. Free tier available with paid upgrades.",
        "tagline": "Grow better with HubSpot",
        "pricing": {
            "model": "freemium",
            "currency": "USD",
            "starting_price": 0,
            "free_tier": True,
            "tiers": [
                {"name": "Free", "price": 0, "per": "month"},
                {"name": "Starter", "price": 15, "per": "seat/month"},
                {"name": "Professional", "price": 890, "per": "month", "features": ["3 seats"]},
                {"name": "Enterprise", "price": 3600, "per": "month", "features": ["5 seats"]},
            ],
            "notes": "Professional requires $1,500-3,500 onboarding fee. Annual commitment required for Pro/Enterprise."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["professional-services", "consulting", "marketing"],
        "best_for": ["consulting firms", "marketing automation", "inbound marketing"],
        "key_capabilities": ["CRM", "marketing automation", "sales pipeline", "email marketing", "analytics", "reporting"],
        "integrations": ["Salesforce", "Slack", "Zapier", "1000+ apps"],
        "g2_score": 4.4,
        "our_rating": 4.3,
        "our_notes": "Free tier is generous. Pro/Enterprise gets expensive. Annual commitment lock-in.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },

    # ==========================================================================
    # TIER 2 - LEGAL
    # ==========================================================================
    {
        "slug": "mycase",
        "name": "MyCase",
        "category": "legal_practice_management",
        "website": "https://www.mycase.com",
        "description": "Centralized legal practice management with case files, client messaging, and invoicing in one place.",
        "tagline": "Simple legal practice management",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 39,
            "free_tier": False,
            "tiers": [
                {"name": "Basic", "price": 39, "per": "user/month"},
                {"name": "Pro", "price": 79, "per": "user/month"},
                {"name": "Advanced", "price": 99, "per": "user/month"},
            ],
            "notes": "Basic lacks key features. Pro recommended."
        },
        "company_sizes": ["small"],
        "industries": ["professional-services", "legal"],
        "best_for": ["solo practitioners", "small firms", "simple needs"],
        "key_capabilities": ["case management", "client portal", "billing", "document storage", "messaging"],
        "integrations": ["Lawmatics", "QuickBooks", "LawPay"],
        "g2_score": 4.4,
        "our_rating": 4.2,
        "our_notes": "Best customer service ratings. Good for smaller firms.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "practicepanther",
        "name": "PracticePanther",
        "category": "legal_practice_management",
        "website": "https://www.practicepanther.com",
        "description": "Legal practice management for solo to enterprise firms with case management, billing, and automation.",
        "tagline": "Practice management for all sizes",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 49,
            "free_tier": False,
            "tiers": [
                {"name": "Solo", "price": 49, "per": "user/month"},
                {"name": "Essential", "price": 79, "per": "user/month"},
                {"name": "Business", "price": 99, "per": "user/month"},
            ],
            "notes": "Good mid-tier option."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["professional-services", "legal"],
        "best_for": ["growing firms", "comprehensive case management", "automation"],
        "key_capabilities": ["case management", "billing", "time tracking", "automation", "client portal"],
        "integrations": ["Lawmatics", "QuickBooks", "LawPay", "Zapier"],
        "g2_score": 4.6,
        "our_rating": 4.3,
        "our_notes": "4.6/5 rating. Mobile app has some limitations.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "rocket-matter",
        "name": "Rocket Matter",
        "category": "legal_practice_management",
        "website": "https://www.rocketmatter.com",
        "description": "Legal practice management with time tracking, billing, and project management features.",
        "tagline": "Legal billing made easy",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 49,
            "free_tier": False,
            "tiers": [
                {"name": "Essentials", "price": 49, "per": "user/month"},
                {"name": "Premier", "price": 99, "per": "user/month"},
            ],
            "notes": "Premier for comprehensive features."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["professional-services", "legal"],
        "best_for": ["billing focus", "project management", "growing firms"],
        "key_capabilities": ["time tracking", "billing", "project management", "document management"],
        "integrations": ["QuickBooks", "LawPay", "Dropbox"],
        "our_rating": 4.0,
        "our_notes": "Good billing features. Entry plan may lack needed features.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "casepeer",
        "name": "CASEpeer",
        "category": "legal_practice_management",
        "subcategory": "personal_injury",
        "website": "https://www.casepeer.com",
        "description": "Practice management specifically designed for personal injury law firms.",
        "tagline": "Built for personal injury",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 79,
            "free_tier": False,
            "notes": "$79/mo. Specialized for PI firms."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["professional-services", "legal"],
        "best_for": ["personal injury firms", "PI-specific workflows"],
        "key_capabilities": ["case management", "PI workflows", "client communication", "settlement tracking"],
        "integrations": ["QuickBooks", "LawPay"],
        "our_rating": 4.3,
        "our_notes": "Best for personal injury niche. Not for general practice.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },

    # ==========================================================================
    # TIER 2 - ACCOUNTING
    # ==========================================================================
    {
        "slug": "financial-cents",
        "name": "Financial Cents",
        "category": "accounting_practice_management",
        "website": "https://financial-cents.com",
        "description": "Workflow and practice management for small to mid-sized accounting and bookkeeping firms.",
        "tagline": "Simple accounting workflow",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 39,
            "free_tier": False,
            "notes": "Starting ~$39/user/month. Good for small-mid firms."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["professional-services", "accounting"],
        "best_for": ["small-mid accounting firms", "workflow management", "recurring client work"],
        "key_capabilities": ["workflow management", "client management", "time tracking", "billing"],
        "integrations": ["QuickBooks", "Xero"],
        "our_rating": 4.1,
        "our_notes": "Good for firms moving beyond spreadsheets. Simpler than enterprise solutions.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "jetpack-workflow",
        "name": "Jetpack Workflow",
        "category": "accounting_practice_management",
        "website": "https://jetpackworkflow.com",
        "description": "Task management and workflow automation for accounting firms with recurring work.",
        "tagline": "Workflow for accountants",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 36,
            "free_tier": False,
            "notes": "Starting ~$36/user/month. Basic but effective."
        },
        "company_sizes": ["small"],
        "industries": ["professional-services", "accounting"],
        "best_for": ["small firms", "task management", "basic workflow needs"],
        "key_capabilities": ["task management", "workflow automation", "deadline tracking", "recurring tasks"],
        "integrations": ["limited integrations"],
        "our_rating": 3.8,
        "our_notes": "Good basic solution. May outgrow for larger needs.",
        "api_available": False,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "cone",
        "name": "Cone",
        "category": "accounting_practice_management",
        "website": "https://www.getcone.io",
        "description": "Affordable unified accounting practice management with CRM, proposals, projects, and billing.",
        "tagline": "Affordable all-in-one",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 5,
            "free_tier": False,
            "notes": "Starting at $5/user/month. Very affordable."
        },
        "company_sizes": ["small"],
        "industries": ["professional-services", "accounting"],
        "best_for": ["budget-conscious firms", "startups", "basic needs"],
        "key_capabilities": ["CRM", "proposals", "projects", "workflows", "billing", "invoicing"],
        "integrations": ["email"],
        "our_rating": 3.7,
        "our_notes": "Most affordable option. Good for very small firms.",
        "api_available": False,
        "requires_developer": False,
        "tier": 2,
    },

    # ==========================================================================
    # TIER 2 - CONSULTING/PSA
    # ==========================================================================
    {
        "slug": "salesforce",
        "name": "Salesforce",
        "category": "crm",
        "website": "https://www.salesforce.com",
        "description": "World's leading enterprise CRM with AI (Einstein), extensive customization, and ecosystem.",
        "tagline": "World's #1 CRM",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 25,
            "free_tier": False,
            "tiers": [
                {"name": "Essentials", "price": 25, "per": "user/month"},
                {"name": "Professional", "price": 80, "per": "user/month"},
                {"name": "Enterprise", "price": 165, "per": "user/month"},
                {"name": "Unlimited", "price": 330, "per": "user/month"},
            ],
            "notes": "Enterprise most common. Implementation can be costly."
        },
        "company_sizes": ["medium", "enterprise"],
        "industries": ["professional-services", "consulting"],
        "best_for": ["enterprises", "complex sales processes", "extensive customization"],
        "key_capabilities": ["CRM", "AI (Einstein)", "sales automation", "reporting", "customization", "AppExchange"],
        "integrations": ["thousands of apps via AppExchange"],
        "g2_score": 4.3,
        "our_rating": 4.2,
        "our_notes": "Industry standard for enterprise. Can be overkill for small firms.",
        "api_available": True,
        "requires_developer": True,
        "tier": 2,
    },
    {
        "slug": "insightly",
        "name": "Insightly",
        "category": "crm",
        "website": "https://www.insightly.com",
        "description": "CRM with project management features, ideal for consulting firms managing client projects.",
        "tagline": "CRM + project management",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 29,
            "free_tier": False,
            "tiers": [
                {"name": "Plus", "price": 29, "per": "user/month"},
                {"name": "Professional", "price": 49, "per": "user/month"},
                {"name": "Enterprise", "price": 99, "per": "user/month"},
            ],
            "notes": "Good for project-heavy consulting."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["professional-services", "consulting"],
        "best_for": ["project-heavy consulting", "client + project tracking"],
        "key_capabilities": ["CRM", "project management", "pipeline", "reporting"],
        "integrations": ["Google Workspace", "Microsoft 365", "QuickBooks"],
        "g2_score": 4.2,
        "our_rating": 4.0,
        "our_notes": "Good CRM + project combo. On pricier side.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "capsule-crm",
        "name": "Capsule CRM",
        "category": "crm",
        "website": "https://capsulecrm.com",
        "description": "Simple, affordable CRM for small consulting businesses and professional services.",
        "tagline": "Simple CRM for small business",
        "pricing": {
            "model": "freemium",
            "currency": "USD",
            "starting_price": 0,
            "free_tier": True,
            "tiers": [
                {"name": "Free", "price": 0, "per": "month", "features": ["250 contacts"]},
                {"name": "Starter", "price": 18, "per": "user/month"},
                {"name": "Growth", "price": 36, "per": "user/month"},
                {"name": "Advanced", "price": 54, "per": "user/month"},
            ],
            "notes": "Free tier for up to 250 contacts. Very affordable."
        },
        "company_sizes": ["small"],
        "industries": ["professional-services", "consulting"],
        "best_for": ["solo consultants", "small firms", "budget-conscious"],
        "key_capabilities": ["contact management", "sales pipeline", "task management", "integrations"],
        "integrations": ["Google Workspace", "Mailchimp", "Xero", "QuickBooks"],
        "g2_score": 4.4,
        "our_rating": 4.1,
        "our_notes": "Excellent value. Simple and effective. May lack advanced features.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "monday-crm",
        "name": "monday CRM",
        "category": "crm",
        "website": "https://monday.com",
        "description": "Flexible work OS with CRM capabilities, project management, and automation.",
        "tagline": "Work OS for everything",
        "pricing": {
            "model": "freemium",
            "currency": "USD",
            "starting_price": 0,
            "free_tier": True,
            "tiers": [
                {"name": "Free", "price": 0, "per": "month", "features": ["2 seats"]},
                {"name": "Basic", "price": 9, "per": "seat/month"},
                {"name": "Standard", "price": 12, "per": "seat/month"},
                {"name": "Pro", "price": 19, "per": "seat/month"},
            ],
            "notes": "Very flexible. Pro includes time tracking and automations."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["professional-services", "consulting"],
        "best_for": ["flexible workflows", "project + CRM combined", "visual teams"],
        "key_capabilities": ["CRM", "project management", "automation", "dashboards", "time tracking"],
        "integrations": ["Slack", "Google", "Microsoft", "100+ apps"],
        "g2_score": 4.6,
        "our_rating": 4.3,
        "our_notes": "Very flexible. Not specialized for legal/accounting but works well.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },

    # ==========================================================================
    # TIER 3 - NICHE/ENTERPRISE
    # ==========================================================================
    {
        "slug": "connectwise-psa",
        "name": "ConnectWise PSA",
        "category": "psa",
        "website": "https://www.connectwise.com",
        "description": "Enterprise PSA for MSPs and IT service providers with ticketing, billing, and project management.",
        "tagline": "Enterprise PSA for IT",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Custom pricing. Typically $100-200/user/month for full features."
        },
        "company_sizes": ["medium", "enterprise"],
        "industries": ["professional-services", "it-services"],
        "best_for": ["MSPs", "IT service providers", "enterprise PSA"],
        "key_capabilities": ["ticketing", "project management", "billing", "CRM", "workflow automation"],
        "integrations": ["ConnectWise ecosystem", "major RMM tools"],
        "our_rating": 3.8,
        "our_notes": "Industry standard for MSPs. Complex, not transparent pricing.",
        "api_available": True,
        "requires_developer": True,
        "tier": 3,
    },
    {
        "slug": "autotask-psa",
        "name": "Autotask PSA",
        "category": "psa",
        "website": "https://www.datto.com/products/autotask-psa",
        "description": "Cloud PSA for IT service providers with ticketing, contracts, and billing.",
        "tagline": "IT service PSA",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 50,
            "free_tier": False,
            "notes": "Starting ~$50/user/month. Custom quotes from sales."
        },
        "company_sizes": ["medium", "enterprise"],
        "industries": ["professional-services", "it-services"],
        "best_for": ["MSPs", "IT service providers", "Datto ecosystem"],
        "key_capabilities": ["ticketing", "contracts", "billing", "project management", "reporting"],
        "integrations": ["Datto RMM", "major IT tools"],
        "our_rating": 3.9,
        "our_notes": "Good customer support. Part of Datto ecosystem. Steep learning curve.",
        "api_available": True,
        "requires_developer": False,
        "tier": 3,
    },
    {
        "slug": "4degrees",
        "name": "4Degrees",
        "category": "crm",
        "subcategory": "relationship_intelligence",
        "website": "https://www.4degrees.ai",
        "description": "Relationship intelligence CRM for consulting, VC, and PE firms with automated data capture.",
        "tagline": "Relationship intelligence CRM",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Custom pricing for professional services firms."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["professional-services", "consulting", "finance"],
        "best_for": ["relationship-driven firms", "VC/PE", "consulting"],
        "key_capabilities": ["relationship intelligence", "automated data capture", "pipeline management", "integrations"],
        "integrations": ["Gmail", "Outlook", "LinkedIn", "calendar"],
        "our_rating": 4.0,
        "our_notes": "Good for relationship-heavy businesses. Niche positioning.",
        "api_available": True,
        "requires_developer": False,
        "tier": 3,
    },
    {
        "slug": "highlevel",
        "name": "HighLevel",
        "category": "crm",
        "subcategory": "agency",
        "website": "https://www.gohighlevel.com",
        "description": "All-in-one CRM and marketing platform for agencies with unlimited contacts and sub-accounts.",
        "tagline": "Agency marketing platform",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 97,
            "free_tier": False,
            "tiers": [
                {"name": "Starter", "price": 97, "per": "month"},
                {"name": "Unlimited", "price": 297, "per": "month"},
                {"name": "SaaS Pro", "price": 497, "per": "month"},
            ],
            "notes": "Unlimited contacts and sub-accounts. Good for agencies."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["professional-services", "marketing"],
        "best_for": ["agencies", "marketing automation", "white-label needs"],
        "key_capabilities": ["CRM", "marketing automation", "funnels", "SMS/email", "white-label"],
        "integrations": ["Twilio", "Stripe", "Zapier"],
        "our_rating": 4.0,
        "our_notes": "Great for agencies. Unlimited pricing is predictable. Learning curve.",
        "api_available": True,
        "requires_developer": False,
        "tier": 3,
    },
]


async def import_vendors():
    """Import all professional services vendors to Supabase."""
    supabase = await get_async_supabase()

    imported = 0
    skipped = 0
    failed = 0
    vendor_ids = {}

    print(f"\n{'='*60}")
    print("Importing Professional Services Vendors to Supabase")
    print(f"{'='*60}\n")

    for vendor_data in PROFESSIONAL_SERVICES_VENDORS:
        slug = vendor_data["slug"]
        tier = vendor_data.pop("tier", None)

        existing = await supabase.table("vendors").select("id").eq("slug", slug).execute()

        if existing.data:
            print(f"  SKIP: {slug} (already exists)")
            vendor_ids[slug] = existing.data[0]["id"]
            skipped += 1
            continue

        now = datetime.now(timezone.utc).isoformat()
        vendor_data["created_at"] = now
        vendor_data["updated_at"] = now
        vendor_data["verified_at"] = now
        vendor_data["verified_by"] = "claude-code"
        vendor_data["status"] = "active"

        try:
            result = await supabase.table("vendors").insert(vendor_data).execute()

            if result.data:
                vendor_ids[slug] = result.data[0]["id"]
                print(f"  OK: {slug}")
                imported += 1

                await supabase.table("vendor_audit_log").insert({
                    "vendor_id": result.data[0]["id"],
                    "vendor_slug": slug,
                    "action": "create",
                    "changed_by": "claude-code",
                    "changes": {"source": "professional-services-research-2026-01"},
                }).execute()
            else:
                print(f"  FAIL: {slug} (no data returned)")
                failed += 1

        except Exception as e:
            print(f"  FAIL: {slug} - {str(e)[:50]}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Import complete: {imported} imported, {skipped} skipped, {failed} failed")
    print(f"{'='*60}\n")

    return vendor_ids


async def set_professional_services_tiers(vendor_ids: dict):
    """Set industry tier assignments."""
    supabase = await get_async_supabase()

    tier_assignments = [
        # Tier 1 - Legal
        ("clio", 1, 10, "#1 legal practice management"),
        ("smokeball", 1, 9, "Best automatic time capture"),
        ("lawmatics", 1, 8, "#1 legal CRM"),
        # Tier 1 - Accounting
        ("karbon", 1, 10, "#1 accounting practice management"),
        ("taxdome", 1, 9, "Best all-in-one for tax/accounting"),
        ("canopy", 1, 7, "Modular flexibility"),
        # Tier 1 - Consulting
        ("hubspot-crm", 1, 8, "Free tier, great marketing automation"),
        # Tier 2 - Legal
        ("mycase", 2, 6, "Best customer service"),
        ("practicepanther", 2, 6, "Good for growing firms"),
        ("rocket-matter", 2, 5, "Billing focused"),
        ("casepeer", 2, 5, "PI specialty"),
        # Tier 2 - Accounting
        ("financial-cents", 2, 5, "Good for small-mid firms"),
        ("jetpack-workflow", 2, 4, "Basic workflow"),
        ("cone", 2, 3, "Most affordable"),
        # Tier 2 - Consulting
        ("salesforce", 2, 7, "Enterprise standard"),
        ("insightly", 2, 5, "CRM + project combo"),
        ("capsule-crm", 2, 5, "Simple and affordable"),
        ("monday-crm", 2, 6, "Flexible work OS"),
        # Tier 3 - Niche
        ("connectwise-psa", 3, 4, "MSP standard"),
        ("autotask-psa", 3, 4, "IT service PSA"),
        ("4degrees", 3, 3, "Relationship intelligence"),
        ("highlevel", 3, 4, "Agency marketing platform"),
    ]

    print(f"\n{'='*60}")
    print("Setting Professional Services Industry Tiers")
    print(f"{'='*60}\n")

    set_count = 0
    skip_count = 0

    for slug, tier, boost, notes in tier_assignments:
        vendor_id = vendor_ids.get(slug)

        if not vendor_id:
            print(f"  SKIP: {slug} (no vendor_id)")
            skip_count += 1
            continue

        try:
            await supabase.table("industry_vendor_tiers").upsert({
                "industry": "professional-services",
                "vendor_id": vendor_id,
                "tier": tier,
                "boost_score": boost,
                "notes": notes,
            }).execute()

            print(f"  OK: {slug} -> Tier {tier} (boost: {boost})")
            set_count += 1

        except Exception as e:
            print(f"  FAIL: {slug} - {str(e)[:50]}")

    print(f"\n{'='*60}")
    print(f"Tiers set: {set_count}, skipped: {skip_count}")
    print(f"{'='*60}\n")


async def main():
    print("\n" + "="*60)
    print("PROFESSIONAL SERVICES VENDOR IMPORT")
    print("="*60)

    vendor_ids = await import_vendors()
    await set_professional_services_tiers(vendor_ids)

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
