"""
Import MedSpa / Aesthetics Vendors to Supabase

Imports verified medical spa, aesthetics, and wellness software
from research and sets industry tiers.

Run: python -m src.scripts.import_medspa_vendors
"""

import asyncio
from datetime import datetime, timezone
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config.supabase_client import get_async_supabase


# Verified medspa vendors to import
MEDSPA_VENDORS = [
    # Tier 1 - Market Leaders
    {
        "slug": "mangomint",
        "name": "Mangomint",
        "category": "medspa_management",
        "website": "https://www.mangomint.com",
        "pricing_url": "https://www.mangomint.com/pricing/",
        "description": "Highest-rated salon and spa software. Smart automations, digital SOAP notes, and seamless scheduling. Ranked #1 for 4 consecutive years.",
        "tagline": "#1 rated salon and spa software",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 165,
            "free_tier": False,
            "tiers": [
                {"name": "Essentials", "price": 165, "per": "month"},
                {"name": "Standard", "price": 245, "per": "month"},
                {"name": "Unlimited", "price": 375, "per": "month"},
            ],
            "notes": "No setup fees, no contracts. Free data import. Only service providers count toward totals. Cancel anytime."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["medspa"],
        "best_for": ["med spas with teams", "high-end salons", "spas wanting automation", "practices valuing UX"],
        "key_capabilities": ["scheduling", "digital SOAP notes", "POS", "automations", "online booking", "Express Booking", "self checkout", "deposits"],
        "integrations": ["Mangomint Pay", "external processors", "marketing tools"],
        "g2_score": 4.8,
        "capterra_score": 4.9,
        "our_rating": 4.8,
        "our_notes": "Highest-rated for 4 years. Not for solopreneurs - teams only. 'Apple-level' UX. Higher entry price but exceptional support and ease of use.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    {
        "slug": "vagaro",
        "name": "Vagaro",
        "category": "medspa_management",
        "website": "https://www.vagaro.com",
        "pricing_url": "https://www.vagaro.com/pro/spa-software",
        "description": "All-in-one spa scheduling and management software with HIPAA-compliant charting, POS, marketing, and client marketplace.",
        "tagline": "All-in-one spa software",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 30,
            "free_tier": False,
            "free_trial_days": 30,
            "tiers": [
                {"name": "1 Calendar", "price": 30, "per": "month"},
                {"name": "2 Calendars", "price": 40, "per": "month"},
                {"name": "Additional", "price": 10, "per": "calendar/month"},
            ],
            "notes": "Add-ons: forms, SOAP notes, MySite, branded app, extra storage. 30-day free trial. Payment processing varies by type."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["medspa"],
        "best_for": ["small to growing med spas", "budget-conscious practices", "spas wanting marketplace exposure", "solopreneurs"],
        "key_capabilities": ["HIPAA charting", "scheduling", "POS", "loyalty programs", "email/text campaigns", "Vagaro Marketplace", "credit card processing"],
        "integrations": ["QuickBooks", "Xero", "Data Lake", "marketing tools"],
        "g2_score": 4.3,
        "capterra_score": 4.7,
        "our_rating": 4.5,
        "our_notes": "Best value for small med spas. $30 start is unbeatable. A la carte pricing - costs can add up with add-ons. Strong marketplace for client discovery.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    {
        "slug": "boulevard",
        "name": "Boulevard",
        "category": "medspa_management",
        "website": "https://www.joinblvd.com",
        "pricing_url": "https://www.joinblvd.com/pricing",
        "description": "Premium client experience platform for self-care businesses. Precision Scheduling, luxury client experiences, and enterprise-grade features.",
        "tagline": "Apple-level spa software",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 176,
            "free_tier": False,
            "tiers": [
                {"name": "Essentials", "price": 176, "per": "month"},
                {"name": "Premier", "price": 293, "per": "month"},
                {"name": "Enterprise", "price": None, "per": "month", "notes": "Custom pricing"},
            ],
            "notes": "Onboarding: $495 for single location. Boulevard Duo POS: $149. Processing: 2.65-3.65% + 15¢. Full price per location."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["medspa"],
        "best_for": ["luxury spas", "high-end med spas", "client experience focus", "multi-location businesses"],
        "key_capabilities": ["Precision Scheduling", "Duo POS", "check-in management", "purchase orders", "luxury client portal", "online booking"],
        "integrations": ["payment processors", "marketing tools", "accounting software"],
        "g2_score": 4.7,
        "capterra_score": 4.8,
        "our_rating": 4.6,
        "our_notes": "'Apple-level' luxury experience. Premium pricing. Best for high-end spas. Full price per location can make scaling expensive.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    # Tier 2 - Strong Alternatives
    {
        "slug": "zenoti",
        "name": "Zenoti",
        "category": "medspa_management",
        "website": "https://www.zenoti.com",
        "pricing_url": "https://www.zenoti.com/pricing-zenoti/",
        "description": "Enterprise cloud platform for multi-location med spas, wellness centers, and aesthetic clinics. Serves 50+ countries.",
        "tagline": "Enterprise med spa platform",
        "pricing": {
            "model": "custom",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "tiers": [
                {"name": "Growth", "price": None, "per": "month", "notes": "Full-featured, no add-ons needed"},
                {"name": "Hypergrowth", "price": None, "per": "month", "notes": "Outcomes, compliance focus"},
                {"name": "Complete", "price": None, "per": "month", "notes": "Enterprise, custom"},
            ],
            "notes": "Pricing based on locations, providers, and data usage. Negotiable. Enterprise-focused."
        },
        "company_sizes": ["medium", "enterprise"],
        "industries": ["medspa"],
        "best_for": ["multi-location med spas", "fast-scaling aesthetic clinics", "enterprise wellness centers", "global organizations"],
        "key_capabilities": ["multi-location management", "scheduling", "POS", "room assignment", "provider utilization", "memberships", "reporting", "marketing automation"],
        "integrations": ["CRM systems", "accounting software", "marketing platforms"],
        "g2_score": 4.3,
        "capterra_score": 4.5,
        "our_rating": 4.3,
        "our_notes": "Best for multi-location enterprises. 50+ countries. Pricing is high but negotiable. Not for small solo practices.",
        "api_available": True,
        "requires_developer": True,
        "tier": 2,
    },
    {
        "slug": "aestheticspro",
        "name": "AestheticsPro",
        "category": "medspa_management",
        "website": "https://www.aestheticspro.com",
        "pricing_url": "https://www.aestheticspro.com/Software-Pricing/",
        "description": "All-in-one HIPAA-compliant software for medical spas and aesthetic clinics. EMR, booking, CRM, marketing, POS, and inventory.",
        "tagline": "All-in-one medspa software",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 59,
            "free_tier": False,
            "tiers": [
                {"name": "Starter", "price": 59, "per": "month"},
                {"name": "Professional", "price": 75, "per": "month"},
                {"name": "Executive", "price": 275, "per": "month"},
                {"name": "Enterprise", "price": None, "per": "month", "notes": "Custom pricing"},
            ],
            "notes": "HIPAA-compliant. Trusted by 35,000+ med spas. Scalable for solo to franchise."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["medspa"],
        "best_for": ["med spas of all sizes", "aesthetic clinics", "franchises", "HIPAA-focused practices"],
        "key_capabilities": ["EMR", "online booking", "scheduling", "CRM", "marketing", "POS", "inventory", "telehealth", "e-prescribing"],
        "integrations": ["payment processors", "lab systems", "marketing tools"],
        "g2_score": 4.1,
        "capterra_score": 4.4,
        "our_rating": 4.3,
        "our_notes": "35,000+ med spas. Affordable starting at $59. HIPAA-compliant with e-prescribing. Good value for comprehensive features.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "aesthetic-record",
        "name": "Aesthetic Record",
        "category": "medspa_management",
        "website": "https://www.aestheticrecord.com",
        "description": "Cloud-based EMR designed specifically for aesthetics and medspas. Before-and-after photos, treatment mapping, and HIPAA-compliant charting.",
        "tagline": "EMR built for aesthetics",
        "pricing": {
            "model": "custom",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Per-user pricing. Essentials package with add-on fees for upgrades. 9,000+ aesthetic clinics."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["medspa"],
        "best_for": ["aesthetic clinics", "solo providers", "startups", "practices prioritizing clinical documentation"],
        "key_capabilities": ["before-and-after photos", "treatment mapping", "HIPAA charting", "telehealth", "scheduling", "payments"],
        "integrations": ["payment processors", "telehealth"],
        "capterra_score": 4.6,
        "our_rating": 4.2,
        "our_notes": "9,000+ clinics. Great for clinical documentation and photos. Per-user pricing with add-on fees. Best for documentation-focused practices.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "glossgenius",
        "name": "GlossGenius",
        "category": "medspa_management",
        "website": "https://glossgenius.com",
        "pricing_url": "https://glossgenius.com/pricing",
        "description": "Salon, spa, and medspa software with beautiful booking websites, POS, and marketing. Lowest payment processing in industry at 2.6%.",
        "tagline": "Beautiful software for beauty pros",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 24,
            "free_tier": False,
            "free_trial_days": 14,
            "tiers": [
                {"name": "Standard", "price": 24, "per": "month", "users": 2, "notes": "2.6% flat processing"},
                {"name": "Gold", "price": 48, "per": "month", "users": 10, "notes": "Google booking, waitlist"},
                {"name": "Platinum", "price": None, "per": "month", "notes": "10+ employees, team management"},
            ],
            "notes": "14-day free trial. 2.6% flat payment processing - lowest in industry. No Tap to Pay fees."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["medspa"],
        "best_for": ["solo providers", "small salons", "new businesses", "budget-conscious spas"],
        "key_capabilities": ["booking website", "POS", "SMS/email marketing", "social media booking", "client discovery", "waitlist", "Google booking"],
        "integrations": ["Google Business", "social media", "payment processors"],
        "g2_score": 4.5,
        "capterra_score": 4.8,
        "our_rating": 4.5,
        "our_notes": "Most affordable at $24. Lowest payment processing (2.6%). Beautiful booking sites. Great for solopreneurs and small teams.",
        "api_available": False,
        "requires_developer": False,
        "tier": 2,
    },
    # Tier 3 - Niche/Specialized
    {
        "slug": "fresha",
        "name": "Fresha",
        "category": "medspa_management",
        "website": "https://www.fresha.com",
        "description": "Free booking and business management software for beauty and wellness. No subscription fees - only pay for optional add-ons.",
        "tagline": "Free salon and spa software",
        "pricing": {
            "model": "freemium",
            "currency": "USD",
            "starting_price": 0,
            "free_tier": True,
            "notes": "Core features free. Payment processing and optional add-ons have fees. Fresha marketplace for client discovery."
        },
        "company_sizes": ["small"],
        "industries": ["medspa"],
        "best_for": ["startups", "budget-conscious", "solo providers", "spas wanting free software"],
        "key_capabilities": ["online booking", "POS", "client management", "marketing", "Fresha marketplace", "inventory"],
        "integrations": ["payment processors", "marketplace"],
        "g2_score": 4.8,
        "capterra_score": 4.9,
        "our_rating": 4.4,
        "our_notes": "Truly free core features. 4.8 on G2. Transaction fees apply. Great for startups. Fresha marketplace drives new clients.",
        "api_available": False,
        "requires_developer": False,
        "tier": 3,
    },
    {
        "slug": "pabau",
        "name": "Pabau",
        "category": "medspa_management",
        "website": "https://pabau.com",
        "description": "Practice management software for aesthetics and medical clinics. European market leader with GDPR compliance.",
        "tagline": "Practice management for aesthetics",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Custom pricing based on practice size. Strong in European market. GDPR compliant."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["medspa"],
        "best_for": ["European clinics", "aesthetic practices", "GDPR-focused businesses", "medical clinics"],
        "key_capabilities": ["EMR", "scheduling", "billing", "consent forms", "before-after photos", "marketing", "GDPR compliance"],
        "integrations": ["payment processors", "accounting software"],
        "capterra_score": 4.7,
        "our_rating": 4.2,
        "our_notes": "Strong in Europe. GDPR-compliant. Good for international clinics or those serving European clients.",
        "api_available": True,
        "requires_developer": False,
        "tier": 3,
    },
    {
        "slug": "meevo",
        "name": "Meevo",
        "category": "medspa_management",
        "website": "https://www.meevo.com",
        "description": "All-in-one salon and spa software with scheduling, POS, marketing, and business intelligence for multi-location businesses.",
        "tagline": "All-in-one spa business platform",
        "pricing": {
            "model": "custom",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Custom pricing. Enterprise focus. Multi-location capabilities."
        },
        "company_sizes": ["medium", "enterprise"],
        "industries": ["medspa"],
        "best_for": ["multi-location spas", "franchise operations", "enterprise spa businesses"],
        "key_capabilities": ["scheduling", "POS", "marketing", "business intelligence", "inventory", "multi-location management"],
        "integrations": ["accounting software", "marketing platforms"],
        "capterra_score": 4.3,
        "our_rating": 4.0,
        "our_notes": "Enterprise focus. Good for multi-location and franchise. Custom pricing for larger operations.",
        "api_available": True,
        "requires_developer": False,
        "tier": 3,
    },
    {
        "slug": "square-appointments",
        "name": "Square Appointments",
        "category": "medspa_management",
        "website": "https://squareup.com/appointments",
        "description": "Free appointment scheduling and POS from Square. Simple booking, payments, and client management.",
        "tagline": "Free scheduling from Square",
        "pricing": {
            "model": "freemium",
            "currency": "USD",
            "starting_price": 0,
            "free_tier": True,
            "tiers": [
                {"name": "Free", "price": 0, "per": "month", "notes": "1 location, basic features"},
                {"name": "Plus", "price": 29, "per": "month", "per_location": True},
                {"name": "Premium", "price": 69, "per": "month", "per_location": True},
            ],
            "notes": "Free for single location. Processing: 2.6% + 10¢ in-person. Part of Square ecosystem."
        },
        "company_sizes": ["small"],
        "industries": ["medspa"],
        "best_for": ["startups", "solo providers", "small spas", "Square ecosystem users"],
        "key_capabilities": ["online booking", "POS", "client management", "calendar sync", "automated reminders", "Square payments"],
        "integrations": ["Square ecosystem", "Google Calendar", "QuickBooks"],
        "g2_score": 4.7,
        "capterra_score": 4.8,
        "our_rating": 4.3,
        "our_notes": "Free tier excellent for starters. Part of powerful Square ecosystem. Limited medspa-specific features. Best for simple needs.",
        "api_available": True,
        "requires_developer": False,
        "tier": 3,
    },
]


async def import_vendors():
    """Import all medspa vendors to Supabase."""
    supabase = await get_async_supabase()

    imported = 0
    skipped = 0
    failed = 0
    vendor_ids = {}  # slug -> id mapping for tier assignment

    print(f"\n{'='*60}")
    print("Importing MedSpa Vendors to Supabase")
    print(f"{'='*60}\n")

    for vendor_data in MEDSPA_VENDORS:
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
                    "changes": {"source": "medspa-vendors-research-2026-01"},
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


async def set_medspa_tiers(vendor_ids: dict):
    """Set industry tier assignments for medspa vendors."""
    supabase = await get_async_supabase()

    # Tier assignments based on research
    tier_assignments = [
        # Tier 1 - Market Leaders
        ("mangomint", 1, 10, "#1 rated 4 years, teams"),
        ("vagaro", 1, 9, "Best value, $30 start"),
        ("boulevard", 1, 8, "Luxury, Apple-level UX"),
        # Tier 2 - Strong Alternatives
        ("zenoti", 2, 7, "Enterprise multi-location"),
        ("aestheticspro", 2, 8, "35k+ spas, $59 start"),
        ("aesthetic-record", 2, 6, "9k+ clinics, EMR focus"),
        ("glossgenius", 2, 8, "Most affordable, 2.6% fees"),
        # Tier 3 - Niche/Specialized
        ("fresha", 3, 7, "Free core features"),
        ("pabau", 3, 5, "European, GDPR"),
        ("meevo", 3, 5, "Enterprise, franchise"),
        ("square-appointments", 3, 6, "Free tier, Square ecosystem"),
    ]

    print(f"\n{'='*60}")
    print("Setting MedSpa Industry Tiers")
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
                "industry": "medspa",
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
    print("MEDSPA VENDOR IMPORT")
    print("="*60)

    # Import vendors
    vendor_ids = await import_vendors()

    # Set tiers
    await set_medspa_tiers(vendor_ids)

    print("\nDone! Verify at /admin/vendors or run:")
    print("  SELECT * FROM vendors WHERE industries @> '[\"medspa\"]'::jsonb;")
    print("  SELECT * FROM industry_vendor_tiers WHERE industry = 'medspa';")


if __name__ == "__main__":
    asyncio.run(main())
