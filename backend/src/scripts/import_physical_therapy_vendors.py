"""
Import Physical Therapy / Chiropractic Vendors to Supabase

Imports verified PT, OT, SLP, and chiropractic practice management software
from research and sets industry tiers.

Run: python -m src.scripts.import_physical_therapy_vendors
"""

import asyncio
from datetime import datetime, timezone
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config.supabase_client import get_async_supabase


# Verified physical therapy vendors to import
PHYSICAL_THERAPY_VENDORS = [
    # Tier 1 - Market Leaders
    {
        "slug": "webpt",
        "name": "WebPT",
        "category": "pt_practice_management",
        "website": "https://www.webpt.com",
        "pricing_url": "https://www.webpt.com/pricing",
        "description": "Leading physical therapy software platform for rehab therapists. Web-based EMR, billing, and practice management for PT, OT, and SLP.",
        "tagline": "The leading rehab therapy platform",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 99,
            "free_tier": False,
            "tiers": [
                {"name": "Starter", "price": 99, "per": "user/month"},
                {"name": "Professional", "price": None, "per": "user/month"},
                {"name": "Ultimate", "price": None, "per": "user/month"},
            ],
            "notes": "Per-provider pricing. RCM available at 6.5% of collections. Add-ons are ala carte."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["physical-therapy"],
        "best_for": ["physical therapists", "occupational therapists", "speech-language pathologists", "rehab practices"],
        "key_capabilities": ["EMR", "scheduling", "billing", "documentation", "patient engagement", "analytics", "telehealth", "RCM"],
        "integrations": ["Clinicient", "various clearinghouses", "payment processors"],
        "g2_score": 4.3,
        "capterra_score": 4.3,
        "our_rating": 4.3,
        "our_notes": "Market leader in rehab therapy. Comprehensive but can be expensive with add-ons. Some find it pricier than alternatives. Owns Clinicient.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    {
        "slug": "jane-app",
        "name": "Jane App",
        "category": "pt_practice_management",
        "website": "https://jane.app",
        "pricing_url": "https://jane.app/pricing",
        "description": "Practice management software for health and wellness practitioners. Simple booking, charting, scheduling, and billing for interdisciplinary clinics.",
        "tagline": "Practice management made simple",
        "pricing": {
            "model": "subscription",
            "currency": "CAD",
            "starting_price": 54,
            "free_tier": False,
            "tiers": [
                {"name": "Balance", "price": 54, "per": "month", "notes": "1 practitioner, 20 appointments/month"},
                {"name": "Practice", "price": None, "per": "month"},
                {"name": "Thrive", "price": None, "per": "month"},
            ],
            "notes": "CAD pricing. No long-term contracts. AI Scribe feature launched 2025. Available in Canada, US, UK, Australia."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["physical-therapy"],
        "best_for": ["solo practitioners", "interdisciplinary clinics", "physios", "massage therapists", "counsellors", "wellness practices"],
        "key_capabilities": ["scheduling", "charting", "billing", "client portal", "online booking", "AI Scribe", "telehealth", "waitlist"],
        "integrations": ["Stripe", "Square", "Mailchimp", "Zoom"],
        "g2_score": 4.8,
        "capterra_score": 4.8,
        "our_rating": 4.7,
        "our_notes": "Highest-rated PT software. Beautiful UX. AI Scribe is new differentiator. Best for smaller practices and interdisciplinary clinics. Canadian company.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    {
        "slug": "prompt-health",
        "name": "Prompt Health (Prompt EMR)",
        "category": "pt_practice_management",
        "website": "https://www.prompthealth.com",
        "description": "AI-powered EMR and practice management platform for PT, OT, chiropractic, and rehab therapy. Unified documentation, scheduling, billing, and analytics.",
        "tagline": "AI-powered rehab therapy EMR",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 100,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Typically $100-500/provider/month based on practice size. Custom quotes. 20-25 more visits per provider per month reported."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["physical-therapy"],
        "best_for": ["physical therapy clinics", "occupational therapy", "chiropractic", "multi-clinic enterprises", "AI-forward practices"],
        "key_capabilities": ["AI documentation", "scheduling", "billing", "patient engagement", "analytics", "RCM", "telehealth"],
        "integrations": ["major clearinghouses", "payment processors"],
        "g2_score": 4.8,
        "capterra_score": 4.9,
        "our_rating": 4.6,
        "our_notes": "Leading AI-powered EMR. 100% user satisfaction. Claims 20-25 more visits/provider/month. Best for practices wanting AI efficiency gains.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    # Tier 1 - Chiropractic
    {
        "slug": "chirotouch",
        "name": "ChiroTouch",
        "category": "chiropractic_practice_management",
        "website": "https://www.chirotouch.com",
        "pricing_url": "https://www.chirotouch.com/pricing",
        "description": "Chiropractic EHR and practice management software with AI assistant Rheo. Cuts documentation time by up to 92% with AI Scribe.",
        "tagline": "The chiropractic software leader",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 159,
            "free_tier": False,
            "tiers": [
                {"name": "Core", "price": 159, "per": "provider/month", "notes": "+$49/additional provider. Paper-billing/cash practices"},
                {"name": "Advanced", "price": 299, "per": "provider/month", "notes": "+$99/additional provider. Electronic billing/insurance"},
            ],
            "notes": "Rheo AI assistant included at no extra cost. CT Launch for new practices with special pricing."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["physical-therapy"],
        "best_for": ["chiropractic practices", "cash practices", "insurance-billing practices", "AI-forward chiropractors"],
        "key_capabilities": ["EHR", "scheduling", "billing", "AI Scribe", "AI Intake", "electronic claims", "patient portal", "SOAP notes"],
        "integrations": ["clearinghouses", "payment processors", "x-ray systems"],
        "capterra_score": 4.1,
        "our_rating": 4.4,
        "our_notes": "Market leader in chiropractic. Rheo AI cuts documentation 92%. Core vs Advanced based on billing type. New practice discounts available.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    # Tier 2 - Strong Alternatives
    {
        "slug": "simplepractice",
        "name": "SimplePractice",
        "category": "pt_practice_management",
        "website": "https://www.simplepractice.com",
        "pricing_url": "https://www.simplepractice.com/pricing/",
        "description": "Practice management platform trusted by 100,000+ health and wellness professionals. EHR, telehealth, billing, and client portal.",
        "tagline": "Run your practice with ease",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 49,
            "free_tier": False,
            "free_trial_days": 30,
            "tiers": [
                {"name": "Starter", "price": 49, "per": "month"},
                {"name": "Essential", "price": 79, "per": "month"},
                {"name": "Plus", "price": 99, "per": "month"},
            ],
            "notes": "30-day free trial. ePrescribe add-on: $49/month + $89 setup. Feb 2025 pricing update."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["physical-therapy"],
        "best_for": ["solo practitioners", "mental health", "therapists", "small practices", "telehealth-focused practices"],
        "key_capabilities": ["EHR", "telehealth", "scheduling", "billing", "client portal", "website builder", "Monarch directory", "insurance claims"],
        "integrations": ["Stripe", "clearinghouses", "labs"],
        "g2_score": 4.5,
        "capterra_score": 4.6,
        "our_rating": 4.4,
        "our_notes": "100,000+ users. Great for solo/small practices. Recent price increases have frustrated some users. Essential features now require higher tiers.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "practice-better",
        "name": "Practice Better",
        "category": "pt_practice_management",
        "website": "https://practicebetter.io",
        "pricing_url": "https://practicebetter.io/pricing",
        "description": "EHR and practice growth platform for health and wellness practitioners including nutritionists, naturopaths, functional medicine, and PT.",
        "tagline": "The all-in-one practice platform",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 25,
            "free_tier": False,
            "free_trial_days": 14,
            "tiers": [
                {"name": "Starter", "price": 25, "per": "month"},
                {"name": "Professional", "price": 59, "per": "month"},
                {"name": "Plus", "price": 89, "per": "month"},
                {"name": "Team", "price": 145, "per": "month"},
            ],
            "notes": "14-day free trial. Oct 2025 price increase. Now includes 3 Practice Admins free and unlimited storage."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["physical-therapy"],
        "best_for": ["nutritionists", "naturopaths", "functional medicine", "dieticians", "health coaches", "chiropractors"],
        "key_capabilities": ["EHR", "scheduling", "billing", "client portal", "meal planning", "protocols", "programs", "telehealth"],
        "integrations": ["Zoom", "Stripe", "Fullscript", "labs"],
        "g2_score": 4.7,
        "capterra_score": 4.8,
        "our_rating": 4.5,
        "our_notes": "Best value starting at $25. Strong for functional medicine and nutrition. Oct 2025 price increase but added features. 14-day trial.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "theraoffice",
        "name": "TheraOffice",
        "category": "pt_practice_management",
        "website": "https://www.ntst.com/solutions/specialty-practices/theraoffice",
        "description": "Physical therapy EMR software from Netsmart. Reduces documentation time by up to 80% with intake, scheduling, documentation, and billing.",
        "tagline": "Reduce documentation time by 80%",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 99,
            "free_tier": False,
            "tiers": [
                {"name": "1 User", "price": 99, "per": "month"},
                {"name": "10 Users", "price": 499, "per": "month"},
                {"name": "Enterprise", "price": None, "per": "month", "notes": "Custom pricing"},
            ],
            "notes": "Monthly or annual plans. Startup, Growth, and Enterprise tiers. Part of Netsmart."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["physical-therapy"],
        "best_for": ["physical therapy clinics", "startup PT practices", "growing clinics", "enterprise PT organizations"],
        "key_capabilities": ["EMR", "scheduling", "documentation", "billing", "accounting", "reporting", "intake"],
        "integrations": ["clearinghouses", "Netsmart ecosystem"],
        "capterra_score": 4.2,
        "our_rating": 4.1,
        "our_notes": "Part of Netsmart. Good for all sizes. Claims 80% documentation reduction. Scaling pricing from $99-$499 based on users.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "clinicient-insight",
        "name": "Clinicient Insight EMR",
        "category": "pt_practice_management",
        "website": "https://www.clinicient.com",
        "description": "Voice-enabled documentation EMR for outpatient rehab. Reduces charting time by 50%. Now part of WebPT family.",
        "tagline": "Voice-enabled rehab documentation",
        "pricing": {
            "model": "custom",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Custom pricing based on practice size. Part of WebPT. Enterprise-level pricing typically $150-300/provider/month."
        },
        "company_sizes": ["medium", "enterprise"],
        "industries": ["physical-therapy"],
        "best_for": ["outpatient rehab", "PT clinics wanting voice documentation", "WebPT ecosystem users", "larger practices"],
        "key_capabilities": ["voice documentation", "EMR", "billing", "scheduling", "coding automation", "practice management"],
        "integrations": ["WebPT ecosystem", "clearinghouses"],
        "capterra_score": 4.0,
        "our_rating": 4.0,
        "our_notes": "Voice-enabled documentation is differentiator. 50% charting reduction. Part of WebPT now. Best for larger practices.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    # Tier 3 - Niche/Specialized
    {
        "slug": "raintree-systems",
        "name": "Raintree Systems",
        "category": "pt_practice_management",
        "website": "https://www.raintreeinc.com",
        "description": "Customizable, template-driven EMR for rehab therapy practices. Enterprise-grade scheduling, billing, and documentation.",
        "tagline": "Enterprise rehab therapy EMR",
        "pricing": {
            "model": "custom",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Enterprise pricing. Contact for quote. Designed for larger multi-location practices."
        },
        "company_sizes": ["medium", "enterprise"],
        "industries": ["physical-therapy"],
        "best_for": ["enterprise PT organizations", "multi-location practices", "practices needing customization"],
        "key_capabilities": ["EMR", "scheduling", "billing", "documentation", "reporting", "customizable templates", "multi-location"],
        "integrations": ["clearinghouses", "labs", "imaging"],
        "g2_score": 4.1,
        "our_rating": 3.9,
        "our_notes": "Enterprise-focused. Highly customizable templates. Best for larger organizations needing flexibility. Not for small practices.",
        "api_available": True,
        "requires_developer": True,
        "tier": 3,
    },
    {
        "slug": "spry-pt",
        "name": "SPRY",
        "category": "pt_practice_management",
        "website": "https://sprypt.com",
        "description": "Fastest-growing AI-powered EMR and billing platform for rehab therapy. Modern interface with AI documentation.",
        "tagline": "AI-powered rehab therapy platform",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Custom pricing. Fast-growing platform. AI-first approach."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["physical-therapy"],
        "best_for": ["AI-forward practices", "modern PT clinics", "practices wanting latest technology"],
        "key_capabilities": ["AI documentation", "EMR", "billing", "scheduling", "patient engagement", "telehealth"],
        "integrations": ["major clearinghouses", "payment processors"],
        "g2_score": 4.5,
        "our_rating": 4.2,
        "our_notes": "Fastest-growing in category per G2. AI-first. Modern UX. Newer entrant but gaining traction. Watch this space.",
        "api_available": True,
        "requires_developer": False,
        "tier": 3,
    },
    {
        "slug": "juvonno",
        "name": "Juvonno",
        "category": "pt_practice_management",
        "website": "https://juvonno.com",
        "description": "Flexible, scalable practice management for physical therapy clinics. Streamlines workflows and supports growth.",
        "tagline": "Scalable PT practice management",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Custom pricing based on practice size. Scalable plans."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["physical-therapy"],
        "best_for": ["growing PT clinics", "multi-disciplinary practices", "scalable operations"],
        "key_capabilities": ["scheduling", "EMR", "billing", "reporting", "patient portal", "online booking"],
        "integrations": ["payment processors", "insurance systems"],
        "capterra_score": 4.6,
        "our_rating": 4.0,
        "our_notes": "Good for growing practices. Scalable tools. Less market presence than leaders but solid reviews.",
        "api_available": True,
        "requires_developer": False,
        "tier": 3,
    },
    {
        "slug": "zanda",
        "name": "Zanda (formerly Power Diary)",
        "category": "pt_practice_management",
        "website": "https://www.zandahealth.com",
        "description": "Complete practice management platform with optional AI assistant for healthcare providers. Scheduling, billing, and client management.",
        "tagline": "Practice management with AI",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 15,
            "free_tier": False,
            "free_trial_days": 14,
            "tiers": [
                {"name": "Solo", "price": 15, "per": "practitioner/month"},
                {"name": "Team", "price": None, "per": "month"},
                {"name": "Enterprise", "price": None, "per": "month"},
            ],
            "notes": "14-day free trial. Formerly Power Diary. Optional AI assistant."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["physical-therapy"],
        "best_for": ["solo practitioners", "allied health", "psychologists", "physios", "budget-conscious practices"],
        "key_capabilities": ["scheduling", "billing", "client management", "AI assistant", "online booking", "telehealth"],
        "integrations": ["Stripe", "Zoom", "Xero"],
        "capterra_score": 4.7,
        "our_rating": 4.2,
        "our_notes": "Most affordable at $15/practitioner. Formerly Power Diary. Optional AI. Good for budget-conscious solo practitioners.",
        "api_available": True,
        "requires_developer": False,
        "tier": 3,
    },
]


async def import_vendors():
    """Import all physical therapy vendors to Supabase."""
    supabase = await get_async_supabase()

    imported = 0
    skipped = 0
    failed = 0
    vendor_ids = {}  # slug -> id mapping for tier assignment

    print(f"\n{'='*60}")
    print("Importing Physical Therapy Vendors to Supabase")
    print(f"{'='*60}\n")

    for vendor_data in PHYSICAL_THERAPY_VENDORS:
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
                    "changes": {"source": "physical-therapy-vendors-research-2026-01"},
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


async def set_physical_therapy_tiers(vendor_ids: dict):
    """Set industry tier assignments for physical therapy vendors."""
    supabase = await get_async_supabase()

    # Tier assignments based on research
    tier_assignments = [
        # Tier 1 - Market Leaders
        ("webpt", 1, 9, "Market leader, comprehensive"),
        ("jane-app", 1, 10, "Highest-rated, beautiful UX"),
        ("prompt-health", 1, 9, "AI-powered, 100% satisfaction"),
        ("chirotouch", 1, 8, "Chiro leader, Rheo AI"),
        # Tier 2 - Strong Alternatives
        ("simplepractice", 2, 7, "100k+ users, solo-friendly"),
        ("practice-better", 2, 8, "Best value, $25 start"),
        ("theraoffice", 2, 6, "Netsmart, 80% doc reduction"),
        ("clinicient-insight", 2, 6, "Voice documentation"),
        # Tier 3 - Niche/Specialized
        ("raintree-systems", 3, 5, "Enterprise, customizable"),
        ("spry-pt", 3, 6, "Fastest-growing, AI-first"),
        ("juvonno", 3, 5, "Scalable, growing"),
        ("zanda", 3, 7, "Most affordable, $15 start"),
    ]

    print(f"\n{'='*60}")
    print("Setting Physical Therapy Industry Tiers")
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
                "industry": "physical-therapy",
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
    print("PHYSICAL THERAPY VENDOR IMPORT")
    print("="*60)

    # Import vendors
    vendor_ids = await import_vendors()

    # Set tiers
    await set_physical_therapy_tiers(vendor_ids)

    print("\nDone! Verify at /admin/vendors or run:")
    print("  SELECT * FROM vendors WHERE industries @> '[\"physical-therapy\"]'::jsonb;")
    print("  SELECT * FROM industry_vendor_tiers WHERE industry = 'physical-therapy';")


if __name__ == "__main__":
    asyncio.run(main())
