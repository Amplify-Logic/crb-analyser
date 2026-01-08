"""
Import Dental Vendors to Supabase

Imports verified dental vendors from research and sets industry tiers.
Run: python -m src.scripts.import_dental_vendors
"""

import asyncio
from datetime import datetime
from typing import Optional
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config.supabase_client import get_async_supabase


# Verified dental vendors to import
DENTAL_VENDORS = [
    # Tier 1 - Practice Management
    {
        "slug": "open-dental",
        "name": "Open Dental",
        "category": "dental_practice_management",
        "website": "https://www.opendental.com",
        "pricing_url": "https://www.opendental.com/site/fees.html",
        "description": "Open-source practice management software created by a dentist, offering comprehensive features at lower cost than competitors.",
        "tagline": "Open source dental practice management",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 179,
            "free_tier": False,
            "free_trial_days": None,
            "tiers": [
                {"name": "Monthly (Year 1)", "price": 179, "per": "month"},
                {"name": "Monthly (After Year 1)", "price": 129, "per": "month"},
            ],
            "notes": "12-month contract, includes all computers up to 3 dentists per location"
        },
        "company_sizes": ["small", "medium"],
        "industries": ["dental"],
        "best_for": ["budget-conscious practices", "tech-savvy offices", "practices wanting customization"],
        "key_capabilities": ["scheduling", "clinical charting", "billing", "patient portal", "eReminders", "imaging"],
        "integrations": ["Pearl AI", "NexHealth", "Weave", "Dental Intelligence"],
        "g2_score": 4.5,
        "capterra_score": 4.5,
        "our_rating": 4.5,
        "our_notes": "41% less expensive than average. Strong community, regular updates.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    {
        "slug": "carestack",
        "name": "CareStack",
        "category": "dental_practice_management",
        "website": "https://carestack.com",
        "pricing_url": "https://carestack.com/pricing",
        "description": "Cloud-based all-in-one dental software for scheduling, clinical, billing, patient engagement, and analytics.",
        "tagline": "All-in-one cloud dental platform",
        "pricing": {
            "model": "custom",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Custom pricing based on locations, chairs, providers. No per-user licenses."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["dental"],
        "best_for": ["multi-location practices", "DSOs", "practices wanting all-in-one solution"],
        "key_capabilities": ["scheduling", "clinical notes", "billing", "patient engagement", "teledentistry", "reputation management"],
        "integrations": ["Pearl AI", "major imaging systems"],
        "g2_score": 4.7,
        "our_rating": 4.7,
        "our_notes": "Top-rated on G2. True all-in-one platform with modern cloud architecture.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    {
        "slug": "curve-dental",
        "name": "Curve Dental",
        "category": "dental_practice_management",
        "website": "https://www.curvedental.com",
        "pricing_url": "https://www.curvedental.com/pricing",
        "description": "Leading cloud-based all-in-one dental practice management software trusted by 80,000+ dental professionals.",
        "tagline": "Most adopted cloud dental software",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 299,
            "free_tier": False,
            "notes": "One login, one monthly price. Special startup pricing available."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["dental"],
        "best_for": ["startups", "single-location practices", "multi-location groups"],
        "key_capabilities": ["cloud storage", "unified workflows", "scheduling", "clinical", "billing", "imaging"],
        "integrations": ["NexHealth", "Pearl AI"],
        "g2_score": 4.4,
        "our_rating": 4.4,
        "our_notes": "Most adopted cloud solution in North America. Good startup support.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    # Tier 1 - Patient Communication
    {
        "slug": "weave",
        "name": "Weave",
        "category": "patient_communication",
        "website": "https://www.getweave.com",
        "pricing_url": "https://www.getweave.com/pricing/",
        "description": "All-in-one communication platform combining VoIP phones, texting, scheduling, payments, and reviews.",
        "tagline": "Unified patient communication platform",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 250,
            "free_tier": False,
            "tiers": [
                {"name": "Pro", "price": 250, "per": "month"},
                {"name": "Elite", "price": None, "per": "month"},
                {"name": "Ultimate", "price": None, "per": "month"},
            ],
            "notes": "Setup fee $750. Free Yealink VoIP phones with some plans."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["dental", "healthcare"],
        "best_for": ["small-medium practices", "offices wanting unified communications"],
        "key_capabilities": ["VoIP phones", "two-way texting", "appointment reminders", "online scheduling", "payments", "reviews", "AI assistant"],
        "integrations": ["Open Dental", "Dentrix", "Eaglesoft", "Curve Dental"],
        "g2_score": 4.5,
        "capterra_score": 4.5,
        "g2_reviews": 605,
        "our_rating": 4.3,
        "our_notes": "Market leader. Added AI assistant in 2024. Some report frequent price increases.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    {
        "slug": "nexhealth",
        "name": "NexHealth",
        "category": "patient_communication",
        "website": "https://www.nexhealth.com",
        "pricing_url": "https://www.nexhealth.com/pricing",
        "description": "Patient engagement platform with real-time online scheduling, digital forms, reminders, and payments.",
        "tagline": "Real-time patient engagement",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 299,
            "free_tier": False,
            "notes": "Four subscription plans. Monthly or annual billing, no cancellation fees."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["dental", "healthcare"],
        "best_for": ["practices wanting modern patient experience", "real-time sync requirements"],
        "key_capabilities": ["real-time online scheduling", "digital forms", "appointment reminders", "payments", "video consultations", "two-way messaging"],
        "integrations": ["Open Dental", "Dentrix", "Dentrix Ascend", "Dentrix Enterprise", "Denticon", "Curve Dental", "Eaglesoft"],
        "g2_score": 4.6,
        "our_rating": 4.5,
        "our_notes": "Real-time EHR sync sets it apart. 25,000+ dental providers. No cancellation fees.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    {
        "slug": "revenuewell",
        "name": "RevenueWell",
        "category": "dental_marketing",
        "website": "https://www.revenuewell.com",
        "description": "All-in-one dental marketing platform for patient communication, scheduling, forms, and reputation management.",
        "tagline": "Dental marketing automation",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 189,
            "free_tier": False,
            "notes": "Three subscription tiers. Bundle discounts available."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["dental"],
        "best_for": ["marketing-focused practices", "patient retention", "reputation management"],
        "key_capabilities": ["appointment reminders", "social media management", "online scheduling", "paperless forms", "reputation management"],
        "integrations": ["Eaglesoft", "Dentrix", "Open Dental"],
        "our_rating": 4.4,
        "our_notes": "92% user satisfaction. Strong marketing features. 11,500+ practices.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    # Tier 2 - Practice Management
    {
        "slug": "dentrix",
        "name": "Dentrix",
        "category": "dental_practice_management",
        "website": "https://www.dentrix.com",
        "pricing_url": "https://www.dentrix.com/how-to-purchase",
        "description": "Industry-standard dental practice management system that automates the entire patient journey.",
        "tagline": "Industry standard dental software",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 500,
            "free_tier": False,
            "notes": "Premium pricing - 32% more expensive than average. Dentrix Ascend (cloud) starts ~$248-399/mo."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["dental"],
        "best_for": ["established practices", "practices needing extensive features", "Henry Schein customers"],
        "key_capabilities": ["comprehensive charting", "scheduling", "billing", "treatment planning", "imaging", "extensive reporting"],
        "integrations": ["Pearl AI", "NexHealth", "Weave"],
        "g2_score": 3.9,
        "our_rating": 3.8,
        "our_notes": "Industry standard with massive install base. Some report outdated UI and high support costs.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "eaglesoft",
        "name": "Eaglesoft",
        "category": "dental_practice_management",
        "website": "https://www.pattersondental.com/cp/Software/dental-practice-management-software/eaglesoft",
        "description": "Complete dental practice management solution from Patterson Dental with scheduling, billing, charting, and imaging.",
        "tagline": "Patterson Dental practice management",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 200,
            "free_tier": False,
            "free_trial_days": 14,
            "notes": "~$200/mo single user, scales to ~$1,500/mo for 10 users."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["dental"],
        "best_for": ["Patterson Dental customers", "practices wanting on-premise option"],
        "key_capabilities": ["scheduling", "insurance claims", "paperless charting", "digital imaging", "treatment planning"],
        "integrations": ["RevenueWell", "Patterson imaging products"],
        "our_rating": 3.5,
        "our_notes": "Solid Patterson-backed solution. On-premise installation can be a drawback vs cloud.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "adit",
        "name": "Adit",
        "category": "dental_practice_management",
        "website": "https://adit.com",
        "pricing_url": "https://adit.com/pricing",
        "description": "AI-powered all-in-one dental practice management consolidating communications, scheduling, payments, and analytics.",
        "tagline": "AI-powered dental practice management",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Claims 60% cost savings. No binding contracts."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["dental"],
        "best_for": ["practices seeking AI features", "unified platform seekers", "cost-conscious practices"],
        "key_capabilities": ["AI scheduling", "VoIP phones", "texting", "online scheduling", "patient forms", "practice analytics", "call tracking"],
        "our_rating": 4.0,
        "our_notes": "AI-first approach. Case study: Lynnwood Dental generated $227K, cut no-shows 40%.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    # Tier 2 - Patient Communication
    {
        "slug": "solutionreach",
        "name": "Solutionreach",
        "category": "patient_communication",
        "website": "https://www.solutionreach.com",
        "description": "Patient engagement platform with secure messaging, online scheduling, and insurance eligibility checking.",
        "tagline": "Patient engagement at scale",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 329,
            "free_tier": False,
            "notes": "Pro and Enterprise plans. Flexible packages with unlimited texting in some tiers."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["dental", "healthcare"],
        "best_for": ["multi-specialty practices", "practices needing extensive integrations"],
        "key_capabilities": ["secure texting", "bulk messaging", "online scheduling", "insurance eligibility", "appointment reminders"],
        "integrations": ["400+ PMS and EHR systems"],
        "our_rating": 4.0,
        "our_notes": "Integrates with 400+ systems - widest integration network.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "emitrr",
        "name": "Emitrr",
        "category": "patient_communication",
        "website": "https://emitrr.com",
        "description": "Affordable patient communication platform with AI automation, texting, and call features.",
        "tagline": "Affordable patient communication",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 149,
            "free_tier": False,
            "tiers": [
                {"name": "Standard", "price": 149, "per": "month"},
                {"name": "Pro", "price": None, "per": "month"},
                {"name": "Enterprise", "price": None, "per": "month"},
            ],
            "notes": "Pay-as-you-go messaging (500-100,000+ credits). No setup fees mentioned."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["dental", "healthcare"],
        "best_for": ["budget-conscious practices", "practices wanting flexible messaging", "Weave alternatives"],
        "key_capabilities": ["AI automation", "auto-responses", "message translation", "missed-call auto-text", "call transcription"],
        "our_rating": 4.0,
        "our_notes": "Most affordable at $149/mo. Pay-as-you-go messaging gives cost control.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "tab32",
        "name": "tab32",
        "category": "dental_practice_management",
        "website": "https://tab32.com",
        "pricing_url": "https://tab32.com/pricing/",
        "description": "Cloud-based dental practice management with intuitive interface and anywhere access.",
        "tagline": "Cloud dental management made simple",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 199,
            "free_tier": False,
            "tiers": [
                {"name": "1 user", "price": 199, "per": "month"},
                {"name": "10 users", "price": 999, "per": "month"},
            ],
            "notes": "Implementation $500-2,000."
        },
        "company_sizes": ["small"],
        "industries": ["dental"],
        "best_for": ["smaller practices", "new practices", "cloud-first offices"],
        "key_capabilities": ["appointment scheduling", "clinical charting", "automated reminders", "two-way texting", "anywhere access"],
        "our_rating": 3.8,
        "our_notes": "87% user satisfaction. Good for basic needs. Some x-ray quality issues reported.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    # Tier 2 - AI & Specialty
    {
        "slug": "pearl-ai",
        "name": "Pearl",
        "category": "ai_dental",
        "website": "https://www.hellopearl.com",
        "description": "FDA-cleared AI platform for dental x-ray analysis, detecting caries, bone loss, and other pathologies.",
        "tagline": "FDA-cleared dental AI diagnostics",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 250,
            "free_tier": False,
            "notes": "$250-500/mo typical quote. ~$6,000/year."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["dental"],
        "best_for": ["practices focused on case acceptance", "patient education", "comprehensive diagnostics"],
        "key_capabilities": ["AI x-ray analysis", "caries detection", "bone loss detection", "calculus identification", "patient communication overlays"],
        "integrations": ["Open Dental", "Dentrix", "Dentrix Ascend", "CareStack", "Curve Dental", "Carestream"],
        "our_rating": 4.2,
        "our_notes": "First FDA-cleared dental AI (2021). 92% sensitivity for caries. 30% increase in treatment acceptance.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "dental-intelligence",
        "name": "Dental Intelligence",
        "category": "dental_analytics",
        "website": "https://www.dentalintel.com",
        "description": "Practice performance analytics platform for KPIs, treatment tracking, and actionable insights.",
        "tagline": "Dental practice analytics",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 499,
            "free_tier": False,
            "notes": "$1,000 setup fee, $499/mo subscription. Auto-renewing yearly contracts."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["dental"],
        "best_for": ["data-driven practices", "production optimization", "treatment follow-up"],
        "key_capabilities": ["KPI tracking", "production analytics", "treatment scheduling follow-up", "goal tracking", "automated insights"],
        "integrations": ["Dentrix", "Eaglesoft", "Open Dental"],
        "g2_score": 3.7,
        "g2_reviews": 14,
        "our_rating": 3.5,
        "our_notes": "Expensive with contract lock-in. Some find alternatives offer better value.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "truelark",
        "name": "TrueLark",
        "category": "ai_receptionist",
        "website": "https://truelark.com",
        "description": "AI-powered virtual receptionist for call handling, appointment scheduling, and patient communication 24/7.",
        "tagline": "AI virtual receptionist",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Contact for pricing. Designed for practices and DSOs of all sizes."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["dental", "healthcare"],
        "best_for": ["practices with high call volume", "after-hours coverage", "DSOs"],
        "key_capabilities": ["AI call handling", "24/7 scheduling", "patient recall", "ASAP list management", "treatment plan follow-ups", "lead nurturing"],
        "our_rating": 4.0,
        "our_notes": "Automates entire front-desk workflow. Captures leads after hours. HIPAA compliant.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    # Tier 3 - Niche/Emerging
    {
        "slug": "oryx-dental",
        "name": "Oryx Dental Software",
        "category": "dental_practice_management",
        "website": "https://www.oryxdentalsoftware.com",
        "description": "Cloud-based dental platform built by dentists with patient-first mindset and deep clinical intelligence.",
        "tagline": "Built by dentists for dentists",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Contact for pricing. Serves startups to DSOs."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["dental"],
        "best_for": ["clinically-focused practices", "dentist-designed workflow seekers"],
        "key_capabilities": ["clinical charting", "scheduling", "patient management", "specialty case management"],
        "our_rating": 3.8,
        "our_notes": "Built by dentists. Strong clinical focus. Newer entrant.",
        "api_available": True,
        "requires_developer": False,
        "tier": 3,
    },
    {
        "slug": "greaten-ai",
        "name": "Greaten AI",
        "category": "ai_receptionist",
        "website": "https://www.greaten.ai",
        "description": "Fully automated AI staff for scheduling, billing, and insurance claim handling with no human intervention.",
        "tagline": "Fully automated AI staff",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Contact for pricing."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["dental", "healthcare"],
        "best_for": ["practices seeking full automation", "insurance claim automation"],
        "key_capabilities": ["24/7 AI scheduling", "billing automation", "insurance claim handling"],
        "our_rating": 3.5,
        "our_notes": "Newer/emerging player. Claims full automation including insurance claims.",
        "api_available": False,
        "requires_developer": False,
        "tier": 3,
    },
]


async def import_vendors():
    """Import all dental vendors to Supabase."""
    supabase = await get_async_supabase()

    imported = 0
    skipped = 0
    failed = 0
    vendor_ids = {}  # slug -> id mapping for tier assignment

    print(f"\n{'='*60}")
    print("Importing Dental Vendors to Supabase")
    print(f"{'='*60}\n")

    for vendor_data in DENTAL_VENDORS:
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
        vendor_data["created_at"] = datetime.utcnow().isoformat()
        vendor_data["updated_at"] = datetime.utcnow().isoformat()
        vendor_data["verified_at"] = datetime.utcnow().isoformat()
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
                    "changes": {"source": "dental-vendors-research-2026-01"},
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


async def set_dental_tiers(vendor_ids: dict):
    """Set industry tier assignments for dental vendors."""
    supabase = await get_async_supabase()

    # Tier assignments based on research
    tier_assignments = [
        # Tier 1
        ("open-dental", 1, 10, "Best value, open-source"),
        ("carestack", 1, 8, "Top G2 rating, all-in-one"),
        ("curve-dental", 1, 7, "Most adopted cloud solution"),
        ("weave", 1, 9, "Market leader in communication"),
        ("nexhealth", 1, 8, "Real-time sync"),
        ("revenuewell", 1, 6, "Strong marketing features"),
        # Tier 2
        ("dentrix", 2, 5, "Industry standard, expensive"),
        ("eaglesoft", 2, 4, "Patterson backed"),
        ("adit", 2, 6, "AI-first approach"),
        ("solutionreach", 2, 5, "Wide integrations"),
        ("emitrr", 2, 7, "Budget-friendly Weave alternative"),
        ("tab32", 2, 3, "Simple cloud solution"),
        ("pearl-ai", 2, 8, "FDA-cleared AI diagnostics"),
        ("dental-intelligence", 2, 4, "Analytics, expensive"),
        ("truelark", 2, 6, "AI receptionist"),
        # Tier 3
        ("oryx-dental", 3, 3, "Emerging, dentist-built"),
        ("greaten-ai", 3, 2, "Emerging AI automation"),
    ]

    print(f"\n{'='*60}")
    print("Setting Dental Industry Tiers")
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
                "industry": "dental",
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
    print("DENTAL VENDOR IMPORT")
    print("="*60)

    # Import vendors
    vendor_ids = await import_vendors()

    # Set tiers
    await set_dental_tiers(vendor_ids)

    print("\nDone! Verify at /admin/vendors or run:")
    print("  SELECT * FROM vendors WHERE industries @> '[\"dental\"]'::jsonb;")
    print("  SELECT * FROM industry_vendor_tiers WHERE industry = 'dental';")


if __name__ == "__main__":
    asyncio.run(main())
