"""
Import Recruitment/Staffing Vendors to Supabase

Imports verified recruitment vendors from research and sets industry tiers.
Run: python -m src.scripts.import_recruitment_vendors
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config.supabase_client import get_async_supabase


# Verified recruitment vendors to import
RECRUITMENT_VENDORS = [
    # ==========================================================================
    # TIER 1 - Highly Recommended
    # ==========================================================================

    # ATS/CRM for Staffing Agencies
    {
        "slug": "bullhorn",
        "name": "Bullhorn",
        "category": "recruitment_ats",
        "subcategory": "staffing_agency",
        "website": "https://www.bullhorn.com",
        "pricing_url": "https://www.bullhorn.com/pricing/",
        "description": "Industry-leading ATS + CRM built specifically for staffing agencies with VMS integration, email sync, and AI-powered matching.",
        "tagline": "The staffing industry standard",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 99,
            "free_tier": False,
            "tiers": [
                {"name": "Team", "price": 99, "per": "user/month"},
                {"name": "Corporate", "price": 199, "per": "user/month"},
                {"name": "Enterprise", "price": None, "per": "user/month"},
            ],
            "notes": "Base plan lacks email add-ons and LinkedIn integration. Implementation $1K-15K+."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["recruitment", "staffing"],
        "best_for": ["staffing agencies", "high-volume recruiters", "agencies needing VMS integration"],
        "avoid_if": ["small team with tight budget", "need transparent pricing"],
        "key_capabilities": ["ATS", "CRM", "VMS integration", "email sync", "LinkedIn integration", "AI matching", "mobile app"],
        "integrations": ["LinkedIn", "Indeed", "VMS systems", "major job boards"],
        "g2_score": 4.0,
        "our_rating": 4.2,
        "our_notes": "Industry standard for staffing. Costs rise quickly with add-ons. AI assistant Amplify is powerful.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    {
        "slug": "ceipal",
        "name": "CEIPAL ATS",
        "category": "recruitment_ats",
        "subcategory": "staffing_agency",
        "website": "https://www.ceipal.com",
        "description": "AI-powered ATS with native VMS capabilities, popular with North American staffing firms. Excellent value vs competitors.",
        "tagline": "AI-powered staffing ATS",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 24,
            "free_tier": False,
            "free_trial_days": 14,
            "notes": "Starting at $24-25/user/month. Much cheaper than Bullhorn/JobDiva."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["recruitment", "staffing"],
        "best_for": ["cost-conscious agencies", "VMS workflow needs", "AI matching requirements"],
        "avoid_if": ["need fastest performance at scale"],
        "key_capabilities": ["ATS", "VMS integration", "AI matching", "resume parsing", "candidate ranking"],
        "integrations": ["major job boards", "VMS systems"],
        "g2_score": 4.8,
        "our_rating": 4.5,
        "our_notes": "92% user satisfaction. Best value vs Bullhorn/JobDiva. Some report lag with large datasets.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    {
        "slug": "manatal",
        "name": "Manatal",
        "category": "recruitment_ats",
        "website": "https://www.manatal.com",
        "description": "AI-powered ATS with built-in CRM, LinkedIn enrichment, and social media profile imports at an accessible price.",
        "tagline": "AI recruiting made affordable",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 15,
            "free_tier": False,
            "free_trial_days": 14,
            "tiers": [
                {"name": "Professional", "price": 15, "per": "user/month"},
                {"name": "Enterprise", "price": 35, "per": "user/month"},
                {"name": "Custom", "price": None, "per": "user/month"},
            ],
            "notes": "Billed annually. Most affordable AI-powered ATS."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["recruitment", "staffing", "hr"],
        "best_for": ["small agencies", "budget-conscious teams", "AI-first recruiting"],
        "key_capabilities": ["ATS", "CRM", "AI recommendations", "LinkedIn enrichment", "social media import", "duplicate detection"],
        "integrations": ["LinkedIn", "major job boards", "Google Calendar"],
        "g2_score": 4.8,
        "our_rating": 4.6,
        "our_notes": "Best value AI ATS on market. Great for small-medium agencies. Very generous feature set for price.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    {
        "slug": "recruit-crm",
        "name": "Recruit CRM",
        "category": "recruitment_ats",
        "website": "https://recruitcrm.io",
        "description": "User-friendly ATS + CRM designed for small and mid-sized recruitment agencies with visual pipelines and automation.",
        "tagline": "Simple recruiting for agencies",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 85,
            "free_tier": False,
            "free_trial_days": 14,
            "tiers": [
                {"name": "Pro", "price": 85, "per": "user/month"},
                {"name": "Business", "price": 125, "per": "user/month"},
                {"name": "Enterprise", "price": 165, "per": "user/month"},
            ],
            "notes": "Billed annually. No credit card required for trial."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["recruitment", "staffing"],
        "best_for": ["startup agencies", "small-mid sized firms", "visual pipeline lovers"],
        "key_capabilities": ["ATS", "CRM", "visual pipelines", "automation", "email sequences", "reporting"],
        "integrations": ["major job boards", "email providers", "Zapier"],
        "g2_score": 4.7,
        "our_rating": 4.4,
        "our_notes": "Very user-friendly for new agencies. Good support. Flexible pricing for startups.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },

    # Enterprise ATS
    {
        "slug": "greenhouse",
        "name": "Greenhouse",
        "category": "recruitment_ats",
        "subcategory": "enterprise",
        "website": "https://www.greenhouse.com",
        "pricing_url": "https://www.greenhouse.com/pricing",
        "description": "Top-rated enterprise ATS with structured hiring, DE&I tools, and 500+ integrations. Industry leader for mid-market and enterprise.",
        "tagline": "#1 rated enterprise ATS",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 6000,
            "free_tier": False,
            "tiers": [
                {"name": "Essential", "price": 6000, "per": "year"},
                {"name": "Advanced", "price": 13000, "per": "year"},
                {"name": "Expert", "price": 25000, "per": "year"},
            ],
            "notes": "Annual billing. Scales with employee count. Negotiation can reduce 20-40%."
        },
        "company_sizes": ["medium", "enterprise"],
        "industries": ["recruitment", "hr", "tech"],
        "best_for": ["mid-market companies", "enterprises", "structured hiring focus", "DE&I priorities"],
        "avoid_if": ["small team", "hiring < 20/year", "tight budget"],
        "key_capabilities": ["structured hiring", "DE&I tools", "interview scheduling", "scorecards", "500+ integrations", "advanced analytics"],
        "integrations": ["LinkedIn", "Slack", "Zoom", "500+ tools"],
        "g2_score": 4.4,
        "our_rating": 4.5,
        "our_notes": "#1 in 23 G2 reports. 98% satisfaction. Overkill for small teams. Watch for 8-15% annual increases.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },

    # AI Sourcing
    {
        "slug": "gem",
        "name": "Gem",
        "category": "recruitment_sourcing",
        "website": "https://www.gem.com",
        "description": "AI-first all-in-one recruiting platform with 800M+ profiles, CRM, sourcing, and analytics built into every workflow.",
        "tagline": "AI-first recruiting platform",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 99,
            "free_tier": True,
            "tiers": [
                {"name": "Startups (free)", "price": 0, "per": "month", "features": ["<30 employees"]},
                {"name": "Startups", "price": 135, "per": "month", "features": ["<100 employees", "after 6mo free"]},
                {"name": "Growth", "price": None, "per": "month", "features": ["101-1000 employees"]},
                {"name": "Enterprise", "price": None, "per": "month", "features": ["1000+ employees"]},
            ],
            "notes": "Startup program: 6 months free, then 50% off first year. Enterprise ~$3,600-4,000/seat/year."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["recruitment", "hr", "tech"],
        "best_for": ["sourcing-heavy teams", "passive candidate outreach", "data-driven recruiting"],
        "key_capabilities": ["AI sourcing", "800M+ profiles", "CRM", "outreach sequences", "analytics", "ATS integration"],
        "integrations": ["Greenhouse", "Lever", "Workday", "major ATS systems"],
        "g2_score": 4.6,
        "our_rating": 4.5,
        "our_notes": "Excellent startup program. Unlimited sourcing with no credit caps. Can be expensive for SMBs.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },

    # ==========================================================================
    # TIER 2 - Worth Considering
    # ==========================================================================

    {
        "slug": "jobdiva",
        "name": "JobDiva",
        "category": "recruitment_ats",
        "subcategory": "staffing_agency",
        "website": "https://www.jobdiva.com",
        "description": "Powerful ATS for staffing agencies with AI-driven candidate matching, resume harvesting, and VMS sync.",
        "tagline": "High-volume staffing ATS",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 99,
            "free_tier": False,
            "notes": "$99/user/month for small teams. Volume discounts for 100+ users (~$50-80/user). Implementation $5K-50K."
        },
        "company_sizes": ["medium", "enterprise"],
        "industries": ["recruitment", "staffing"],
        "best_for": ["high-volume staffing", "resume harvesting", "VMS workflows"],
        "avoid_if": ["small agency", "need simple onboarding"],
        "key_capabilities": ["ATS", "AI matching", "resume harvesting", "VMS sync", "candidate search"],
        "integrations": ["VMS systems", "major job boards"],
        "g2_score": 4.7,
        "our_rating": 4.0,
        "our_notes": "Powerful but complex. High implementation costs. Best for agencies doing 100+ placements/month.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "lever",
        "name": "Lever",
        "category": "recruitment_ats",
        "subcategory": "enterprise",
        "website": "https://www.lever.co",
        "pricing_url": "https://www.lever.co/pricing/",
        "description": "Combined ATS + CRM (LeverTRM) with intuitive UI, automation, and strong integrations for growing companies.",
        "tagline": "ATS + CRM in one",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 6000,
            "free_tier": False,
            "notes": "~$6-8/employee/month. Base ~$12K-18K/year, can reach $25K with add-ons."
        },
        "company_sizes": ["medium", "enterprise"],
        "industries": ["recruitment", "hr", "tech"],
        "best_for": ["companies hiring 20-100/year", "teams wanting ATS+CRM combined", "clean UI lovers"],
        "avoid_if": ["hiring < 20/year", "need deep analytics"],
        "key_capabilities": ["ATS", "CRM", "automation", "interview scheduling", "bulk actions", "integrations"],
        "integrations": ["Slack", "Zoom", "LinkedIn", "calendar apps"],
        "g2_score": 4.3,
        "our_rating": 4.2,
        "our_notes": "Shortest onboarding time. Beautiful UI. Reporting can feel limited. Used by Netflix, Spotify.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "workable",
        "name": "Workable",
        "category": "recruitment_ats",
        "website": "https://www.workable.com",
        "description": "All-in-one recruiting platform with AI screening, video interviews, and access to 400M+ candidate profiles.",
        "tagline": "All-in-one recruiting",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 169,
            "free_tier": False,
            "free_trial_days": 15,
            "tiers": [
                {"name": "Starter", "price": 169, "per": "month"},
                {"name": "Standard", "price": 360, "per": "month"},
                {"name": "Premier", "price": 599, "per": "month"},
            ],
            "notes": "Add-ons: texting +$79, video +$99, assessments +$59. Scales with headcount."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["recruitment", "hr"],
        "best_for": ["SMBs", "teams wanting all-in-one", "AI-powered screening"],
        "key_capabilities": ["ATS", "AI screening", "video interviews", "400M+ profiles", "200+ job boards", "self-scheduling"],
        "integrations": ["Slack", "major job boards", "HRIS systems"],
        "g2_score": 4.4,
        "our_rating": 4.2,
        "our_notes": "Good all-rounder. Headcount pricing can penalize larger companies with low hiring needs.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "recruiterflow",
        "name": "Recruiterflow",
        "category": "recruitment_ats",
        "subcategory": "staffing_agency",
        "website": "https://recruiterflow.com",
        "pricing_url": "https://recruiterflow.com/pricing",
        "description": "Complete ATS + CRM for staffing agencies with email sequences, automation, and built-in AI (RF GPT).",
        "tagline": "Modern agency recruiting OS",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 85,
            "free_tier": False,
            "free_trial_days": 14,
            "tiers": [
                {"name": "Advanced", "price": 85, "per": "user/month"},
                {"name": "Custom", "price": None, "per": "user/month"},
            ],
            "notes": "No contracts. Includes RF GPT for AI-generated content."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["recruitment", "staffing"],
        "best_for": ["modern agencies", "automation lovers", "email sequence users"],
        "key_capabilities": ["ATS", "CRM", "email sequences", "automation", "AI content generation", "career pages"],
        "integrations": ["major job boards", "email providers", "calendar"],
        "g2_score": 4.8,
        "capterra_score": 4.8,
        "our_rating": 4.4,
        "our_notes": "4.8/5 on Capterra. Great UI. RF GPT saves time on writing. Some report glitches.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "zoho-recruit",
        "name": "Zoho Recruit",
        "category": "recruitment_ats",
        "website": "https://www.zoho.com/recruit/",
        "description": "Comprehensive ATS with solutions for both in-house recruiters and staffing agencies, part of Zoho ecosystem.",
        "tagline": "Recruit smarter with Zoho",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 25,
            "free_tier": True,
            "tiers": [
                {"name": "Free", "price": 0, "per": "month", "features": ["1 active job"]},
                {"name": "Standard", "price": 25, "per": "user/month"},
                {"name": "Professional", "price": 50, "per": "user/month"},
                {"name": "Enterprise", "price": 75, "per": "user/month"},
            ],
            "notes": "Billed annually. Free tier available. Part of Zoho suite."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["recruitment", "staffing", "hr"],
        "best_for": ["Zoho users", "budget-conscious teams", "in-house + agency use"],
        "key_capabilities": ["ATS", "candidate sourcing", "resume parsing", "workflows", "analytics"],
        "integrations": ["Zoho suite", "major job boards", "Google Workspace"],
        "g2_score": 4.4,
        "our_rating": 4.0,
        "our_notes": "Great value with free tier. Best if already using Zoho. Solid for basics.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "hireez",
        "name": "hireEZ",
        "category": "recruitment_sourcing",
        "website": "https://hireez.com",
        "description": "AI-powered sourcing platform with access to 800M+ candidate profiles, agentic AI, and market intelligence.",
        "tagline": "Agentic AI recruiting",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 169,
            "free_tier": False,
            "free_trial_days": 7,
            "tiers": [
                {"name": "Starter", "price": 169, "per": "user/month"},
                {"name": "Professional", "price": 450, "per": "month"},
                {"name": "Enterprise", "price": 250, "per": "user/month"},
            ],
            "notes": "Annual billing. Professional ~$5,400/year with 4,000 monthly credits."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["recruitment", "staffing", "hr"],
        "best_for": ["sourcing teams", "passive candidate hunting", "market intelligence needs"],
        "key_capabilities": ["AI sourcing", "800M+ profiles", "agentic AI", "outreach automation", "market insights", "CRM"],
        "integrations": ["major ATS systems", "LinkedIn"],
        "g2_score": 4.6,
        "our_rating": 4.3,
        "our_notes": "Powerful AI sourcing. Credit-based model. Good for high-volume passive sourcing.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "fetcher",
        "name": "Fetcher",
        "category": "recruitment_sourcing",
        "website": "https://fetcher.ai",
        "pricing_url": "https://fetcher.ai/pricing",
        "description": "AI-powered candidate sourcing and outreach automation that can source talent autonomously or with expert assistance.",
        "tagline": "Your AI recruiter",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 379,
            "free_tier": False,
            "free_trial_days": 7,
            "tiers": [
                {"name": "Growth", "price": 149, "per": "user/month"},
                {"name": "Professional", "price": 249, "per": "user/month"},
                {"name": "Enterprise", "price": None, "per": "user/month"},
            ],
            "notes": "Annual commitment required. Can use AI self-serve or Fetcher's sourcing experts."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["recruitment", "hr", "tech"],
        "best_for": ["passive sourcing", "outreach automation", "teams wanting expert help option"],
        "key_capabilities": ["AI sourcing", "automated outreach", "sourcing experts option", "ATS integration"],
        "integrations": ["major ATS systems", "CRM", "email", "Slack"],
        "g2_score": 4.7,
        "our_rating": 4.3,
        "our_notes": "Users report 75% sourcing automation, 40% better response rates. Annual commitment required.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "loxo",
        "name": "Loxo",
        "category": "recruitment_ats",
        "website": "https://www.loxo.co",
        "pricing_url": "https://www.loxo.co/pricing",
        "description": "Talent intelligence platform combining ATS, CRM, and AI sourcing with a generous free tier.",
        "tagline": "Talent intelligence platform",
        "pricing": {
            "model": "freemium",
            "currency": "USD",
            "starting_price": 0,
            "free_tier": True,
            "free_trial_days": 7,
            "tiers": [
                {"name": "Free", "price": 0, "per": "month", "features": ["ATS/CRM forever free"]},
                {"name": "Professional", "price": None, "per": "user/month", "features": ["AI sourcing, automation"]},
                {"name": "Enterprise", "price": None, "per": "user/month"},
            ],
            "notes": "Free ATS/CRM forever. 7-day trial of Professional features. ~$6,000/year typical."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["recruitment", "staffing"],
        "best_for": ["agencies wanting free ATS", "AI sourcing needs", "budget-conscious teams"],
        "key_capabilities": ["ATS", "CRM", "AI sourcing", "automation", "outreach campaigns"],
        "integrations": ["major job boards", "email"],
        "g2_score": 4.6,
        "our_rating": 4.2,
        "our_notes": "Great free tier for ATS/CRM. AI sourcing in paid tiers. Good entry point.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "linkedin-recruiter",
        "name": "LinkedIn Recruiter",
        "category": "recruitment_sourcing",
        "website": "https://business.linkedin.com/talent-solutions/recruiter",
        "description": "Access to LinkedIn's 900M+ professional network with advanced search, InMail, and team collaboration.",
        "tagline": "The world's largest professional network",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 170,
            "free_tier": False,
            "tiers": [
                {"name": "Recruiter Lite", "price": 170, "per": "month"},
                {"name": "Recruiter Professional", "price": 800, "per": "month"},
                {"name": "Recruiter Corporate", "price": 1080, "per": "month"},
            ],
            "notes": "Lite: 30 InMails/mo. Corporate: 150 InMails/mo. Annual commitment typical. Extra InMails $10 each."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["recruitment", "staffing", "hr"],
        "best_for": ["passive candidate sourcing", "professional roles", "brand visibility"],
        "avoid_if": ["blue-collar recruiting", "tight budget"],
        "key_capabilities": ["advanced search", "InMail", "900M+ profiles", "team collaboration", "pipeline management"],
        "integrations": ["major ATS systems"],
        "g2_score": 4.4,
        "our_rating": 4.0,
        "our_notes": "Essential for professional recruiting. Expensive but unmatched network. TCO can be 20-40% higher than stated.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "crelate",
        "name": "Crelate",
        "category": "recruitment_ats",
        "subcategory": "staffing_agency",
        "website": "https://www.crelate.com",
        "description": "Modern ATS + CRM for recruiting and staffing firms with automation, reporting, and sales pipeline management.",
        "tagline": "Recruiting + sales in one",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 99,
            "free_tier": False,
            "tiers": [
                {"name": "Business", "price": 99, "per": "user/month"},
                {"name": "Business Plus", "price": 144, "per": "user/month"},
                {"name": "Custom", "price": None, "per": "user/month"},
            ],
            "notes": "Best for mid-size recruiting firms and staffing agencies."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["recruitment", "staffing"],
        "best_for": ["mid-size agencies", "sales-focused recruiters", "automation needs"],
        "key_capabilities": ["ATS", "CRM", "sales pipeline", "automation", "reporting", "candidate portal"],
        "integrations": ["major job boards", "email", "calendar"],
        "g2_score": 4.5,
        "our_rating": 4.1,
        "our_notes": "Good balance of ATS + CRM + sales. Popular with growth-stage agencies.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },

    # ==========================================================================
    # TIER 3 - Niche/Emerging
    # ==========================================================================

    {
        "slug": "avionyte",
        "name": "Avionté",
        "category": "recruitment_ats",
        "subcategory": "staffing_agency",
        "website": "https://www.avionte.com",
        "description": "All-in-one staffing platform with ATS, CRM, payroll, billing, and onboarding in a single solution.",
        "tagline": "Complete staffing platform",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 750,
            "free_tier": False,
            "notes": "Starting at $750/month. Includes ATS, CRM, payroll, billing, onboarding."
        },
        "company_sizes": ["medium", "enterprise"],
        "industries": ["recruitment", "staffing"],
        "best_for": ["staffing agencies wanting one platform", "payroll integration needs"],
        "avoid_if": ["small agency", "just need ATS"],
        "key_capabilities": ["ATS", "CRM", "payroll", "billing", "onboarding", "time tracking"],
        "integrations": ["job boards", "background check providers"],
        "our_rating": 3.8,
        "our_notes": "Good for all-in-one but expensive. Best for agencies doing payroll in-house.",
        "api_available": True,
        "requires_developer": False,
        "tier": 3,
    },
    {
        "slug": "paradox-olivia",
        "name": "Paradox (Olivia)",
        "category": "recruitment_automation",
        "website": "https://www.paradox.ai",
        "description": "Conversational AI assistant for high-volume hiring with 24/7 text/mobile interactions, screening, and scheduling.",
        "tagline": "Conversational recruiting AI",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Contact for pricing. Best for high-volume, hourly hiring."
        },
        "company_sizes": ["medium", "enterprise"],
        "industries": ["recruitment", "retail", "hospitality", "healthcare"],
        "best_for": ["high-volume hourly hiring", "retail/hospitality", "24/7 candidate engagement"],
        "key_capabilities": ["AI chatbot", "24/7 engagement", "screening", "scheduling", "text recruiting"],
        "integrations": ["major ATS systems", "HRIS"],
        "our_rating": 4.2,
        "our_notes": "Excellent for high-turnover industries. Olivia handles routine interactions automatically.",
        "api_available": True,
        "requires_developer": False,
        "tier": 3,
    },
    {
        "slug": "eightfold",
        "name": "Eightfold AI",
        "category": "recruitment_automation",
        "subcategory": "enterprise",
        "website": "https://eightfold.ai",
        "description": "Enterprise talent intelligence platform using deep learning for skills-based matching and career pathing.",
        "tagline": "Enterprise talent intelligence",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Enterprise pricing. Contact for quote."
        },
        "company_sizes": ["enterprise"],
        "industries": ["recruitment", "hr"],
        "best_for": ["large enterprises", "skills-based hiring", "internal mobility"],
        "avoid_if": ["SMB", "simple hiring needs"],
        "key_capabilities": ["deep learning matching", "skills taxonomy", "career pathing", "internal mobility", "talent intelligence"],
        "integrations": ["major enterprise ATS", "HRIS systems"],
        "our_rating": 4.0,
        "our_notes": "Enterprise-only. Powerful AI but complex implementation. Good for Fortune 500.",
        "api_available": True,
        "requires_developer": True,
        "tier": 3,
    },
    {
        "slug": "goodtime",
        "name": "GoodTime",
        "category": "recruitment_automation",
        "website": "https://www.goodtime.io",
        "description": "Interview scheduling automation platform for high-volume interviewing with smart coordination and analytics.",
        "tagline": "Intelligent interview scheduling",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Contact for pricing. Best for teams with 50+ interviews/month."
        },
        "company_sizes": ["medium", "enterprise"],
        "industries": ["recruitment", "hr", "tech"],
        "best_for": ["high-volume interviewing", "complex scheduling", "candidate experience focus"],
        "key_capabilities": ["automated scheduling", "interviewer coordination", "analytics", "candidate experience"],
        "integrations": ["Greenhouse", "Lever", "major ATS systems", "calendar apps"],
        "our_rating": 4.3,
        "our_notes": "Best for teams doing 50+ interviews monthly. Excellent at complex multi-round scheduling.",
        "api_available": True,
        "requires_developer": False,
        "tier": 3,
    },
    {
        "slug": "turbohire",
        "name": "TurboHire",
        "category": "recruitment_automation",
        "website": "https://www.turbohire.co",
        "description": "End-to-end AI recruitment automation covering sourcing, screening, interviewing, offers, and pre-onboarding.",
        "tagline": "End-to-end AI recruiting",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Contact for pricing. Targets enterprises seeking near-touchless hiring."
        },
        "company_sizes": ["medium", "enterprise"],
        "industries": ["recruitment", "hr"],
        "best_for": ["enterprises wanting full automation", "high-volume hiring", "near-touchless recruiting"],
        "key_capabilities": ["agentic AI", "semantic matching", "automated scheduling", "chatbot engagement", "offer management"],
        "integrations": ["major ATS systems", "HRIS"],
        "our_rating": 3.8,
        "our_notes": "Ambitious scope with end-to-end AI. Best for enterprises committed to AI transformation.",
        "api_available": True,
        "requires_developer": False,
        "tier": 3,
    },
]


async def import_vendors():
    """Import all recruitment vendors to Supabase."""
    supabase = await get_async_supabase()

    imported = 0
    skipped = 0
    failed = 0
    vendor_ids = {}  # slug -> id mapping for tier assignment

    print(f"\n{'='*60}")
    print("Importing Recruitment Vendors to Supabase")
    print(f"{'='*60}\n")

    for vendor_data in RECRUITMENT_VENDORS:
        slug = vendor_data["slug"]
        tier = vendor_data.pop("tier", None)  # Extract tier for later

        # Check if vendor already exists
        existing = await supabase.table("vendors").select("id").eq("slug", slug).execute()

        if existing.data:
            print(f"  SKIP: {slug} (already exists)")
            vendor_ids[slug] = existing.data[0]["id"]
            skipped += 1
            continue

        # Prepare data
        now = datetime.now(timezone.utc).isoformat()
        vendor_data["created_at"] = now
        vendor_data["updated_at"] = now
        vendor_data["verified_at"] = now
        vendor_data["verified_by"] = "claude-code"
        vendor_data["status"] = "active"

        try:
            # Insert vendor
            result = await supabase.table("vendors").insert(vendor_data).execute()

            if result.data:
                vendor_ids[slug] = result.data[0]["id"]
                print(f"  OK: {slug}")
                imported += 1

                # Log audit
                await supabase.table("vendor_audit_log").insert({
                    "vendor_id": result.data[0]["id"],
                    "vendor_slug": slug,
                    "action": "create",
                    "changed_by": "claude-code",
                    "changes": {"source": "recruitment-vendors-research-2026-01"},
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


async def set_recruitment_tiers(vendor_ids: dict):
    """Set industry tier assignments for recruitment vendors."""
    supabase = await get_async_supabase()

    # Tier assignments based on research
    tier_assignments = [
        # Tier 1 - Highly Recommended
        ("bullhorn", 1, 10, "Industry standard for staffing agencies"),
        ("ceipal", 1, 9, "Best value, 92% satisfaction, G2 4.8"),
        ("manatal", 1, 10, "Most affordable AI ATS, G2 4.8"),
        ("recruit-crm", 1, 8, "Best for small-mid agencies"),
        ("greenhouse", 1, 9, "#1 enterprise ATS, 98% satisfaction"),
        ("gem", 1, 8, "Best AI sourcing, great startup program"),
        # Tier 2 - Worth Considering
        ("jobdiva", 2, 6, "High-volume staffing"),
        ("lever", 2, 7, "Beautiful ATS+CRM combined"),
        ("workable", 2, 6, "Good all-rounder for SMBs"),
        ("recruiterflow", 2, 7, "Modern agency OS with AI"),
        ("zoho-recruit", 2, 5, "Great free tier, Zoho ecosystem"),
        ("hireez", 2, 7, "Powerful AI sourcing"),
        ("fetcher", 2, 6, "AI sourcing with expert option"),
        ("loxo", 2, 6, "Free ATS/CRM tier"),
        ("linkedin-recruiter", 2, 8, "Essential for professional roles"),
        ("crelate", 2, 5, "Good ATS+CRM+sales combo"),
        # Tier 3 - Niche/Emerging
        ("avionyte", 3, 4, "All-in-one with payroll"),
        ("paradox-olivia", 3, 5, "Conversational AI for high-volume"),
        ("eightfold", 3, 3, "Enterprise talent intelligence"),
        ("goodtime", 3, 4, "Interview scheduling automation"),
        ("turbohire", 3, 3, "End-to-end AI automation"),
    ]

    print(f"\n{'='*60}")
    print("Setting Recruitment Industry Tiers")
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
            # Upsert tier assignment
            await supabase.table("industry_vendor_tiers").upsert({
                "industry": "recruitment",
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
    """Main import function."""
    print("\n" + "="*60)
    print("RECRUITMENT VENDOR IMPORT")
    print("="*60)

    # Import vendors
    vendor_ids = await import_vendors()

    # Set tiers
    await set_recruitment_tiers(vendor_ids)

    print("\nDone! Verify at /admin/vendors or run:")
    print("  SELECT * FROM vendors WHERE industries @> '[\"recruitment\"]'::jsonb;")
    print("  SELECT * FROM industry_vendor_tiers WHERE industry = 'recruitment';")


if __name__ == "__main__":
    asyncio.run(main())
