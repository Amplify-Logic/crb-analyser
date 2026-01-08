"""
Import Coaching Vendors to Supabase

Imports verified coaching platforms and software for business/executive/life coaches
from research and sets industry tiers.

Run: python -m src.scripts.import_coaching_vendors
"""

import asyncio
from datetime import datetime, timezone
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config.supabase_client import get_async_supabase


# Verified coaching vendors to import
COACHING_VENDORS = [
    # Tier 1 - Best for Solo Coaches
    {
        "slug": "coachaccountable",
        "name": "CoachAccountable",
        "category": "coaching_platform",
        "website": "https://www.coachaccountable.com",
        "pricing_url": "https://www.coachaccountable.com/pricing",
        "description": "Purpose-built coaching platform for client management, program delivery, and progress tracking. Reduces administrative overhead for solo practitioners and enterprises.",
        "tagline": "Deliver better coaching",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 20,
            "free_tier": False,
            "free_trial_days": 30,
            "tiers": [
                {"name": "2 Clients", "price": 20, "per": "month"},
                {"name": "5 Clients", "price": 40, "per": "month"},
                {"name": "10 Clients", "price": 70, "per": "month"},
                {"name": "25 Clients", "price": 120, "per": "month"},
                {"name": "100 Clients", "price": 400, "per": "month"},
                {"name": "1000 Clients", "price": 4000, "per": "month", "notes": "$4/client after 100"},
            ],
            "notes": "No setup fees. No cancellation fees. Unlimited coach accounts at no extra cost. Since 2012."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["coaching"],
        "best_for": ["solo coaches", "coaching practices", "enterprises with coaching programs", "accountability-focused coaches"],
        "key_capabilities": ["client management", "program delivery", "progress tracking", "session scheduling", "goal setting", "worksheets", "metrics tracking", "white-label"],
        "integrations": ["Zoom", "Google Calendar", "Stripe", "PayPal", "Zapier"],
        "g2_score": 4.7,
        "capterra_score": 4.9,
        "our_rating": 4.7,
        "our_notes": "Most established coaching-specific platform (since 2012). Per-client pricing scales well. Unlimited coach accounts. 30-day trial with no credit card.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    {
        "slug": "paperbell",
        "name": "Paperbell",
        "category": "coaching_platform",
        "website": "https://paperbell.com",
        "pricing_url": "https://paperbell.com/pricing/",
        "description": "All-in-one coaching platform handling payments, contracts, scheduling, and client admin. Supports any pricing structure coaches need.",
        "tagline": "All-in-one for coaches",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 47.5,
            "free_tier": False,
            "free_trial_days": 14,
            "tiers": [
                {"name": "Monthly", "price": 57, "per": "month"},
                {"name": "Annual", "price": 47.5, "per": "month", "notes": "Billed annually, save $114/year"},
            ],
            "notes": "Unlimited clients and packages. No transaction fees on payments (standard Stripe/PayPal fees apply)."
        },
        "company_sizes": ["small"],
        "industries": ["coaching"],
        "best_for": ["coaches wanting simplicity", "coaches selling packages", "group coaching", "discovery sessions", "digital products"],
        "key_capabilities": ["payment processing", "contract signing", "scheduling", "client portal", "packages", "subscriptions", "group programs", "digital downloads"],
        "integrations": ["Zoom", "Google Calendar", "Stripe", "PayPal"],
        "capterra_score": 4.8,
        "our_rating": 4.6,
        "our_notes": "Best value for unlimited clients. Simple, intuitive. Most coaches cover annual cost with one package sale. Supports complex pricing structures.",
        "api_available": False,
        "requires_developer": False,
        "tier": 1,
    },
    {
        "slug": "honeybook",
        "name": "HoneyBook",
        "category": "coaching_platform",
        "website": "https://www.honeybook.com",
        "pricing_url": "https://www.honeybook.com/pricing",
        "description": "Client management platform for freelancers and coaches with proposals, contracts, invoicing, and scheduling in one place.",
        "tagline": "Get clientflow moving",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 29,
            "free_tier": False,
            "free_trial_days": 7,
            "tiers": [
                {"name": "Starter", "price": 29, "per": "month", "notes": "Billed annually, $36 monthly"},
                {"name": "Essentials", "price": 49, "per": "month", "notes": "Billed annually, $59 monthly"},
                {"name": "Premium", "price": 109, "per": "month", "notes": "Billed annually, $129 monthly"},
            ],
            "notes": "USA/Canada only. 60-day money-back guarantee. ACH: 1.5%, Cards: 2.9% + 25¢."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["coaching"],
        "best_for": ["freelancers", "coaches selling packages", "creative professionals", "small teams needing automation"],
        "key_capabilities": ["proposals", "contracts", "invoicing", "scheduling", "client portal", "automations", "templates", "QuickBooks sync"],
        "integrations": ["Zoom", "Google Calendar", "QuickBooks", "Zapier"],
        "g2_score": 4.5,
        "capterra_score": 4.8,
        "our_rating": 4.4,
        "our_notes": "Great for coaches who also do creative work. Beautiful proposals. USA/Canada only is a limitation. Payment fees higher than some competitors.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    # Tier 2 - Strong Alternatives
    {
        "slug": "practice-do",
        "name": "Practice",
        "category": "coaching_platform",
        "website": "https://practice.do",
        "pricing_url": "https://practice.do/pricing",
        "description": "All-in-one coaching platform with mobile app, built for solopreneurs. Scheduling, client portal, forms, and file storage.",
        "tagline": "Your coaching business, organized",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 5,
            "free_tier": False,
            "free_trial_days": 7,
            "notes": "Flat fee starting at $5/month. 99% solo users. Enterprise plan coming."
        },
        "company_sizes": ["small"],
        "industries": ["coaching"],
        "best_for": ["solo coaches", "life coaches", "executive coaches", "wellness coaches", "mobile-first coaches"],
        "key_capabilities": ["scheduling", "client portal", "forms", "file storage", "mobile app", "session notes"],
        "integrations": ["Zoom", "Google Calendar", "Stripe"],
        "g2_score": 4.6,
        "capterra_score": 4.7,
        "our_rating": 4.5,
        "our_notes": "Most affordable coaching CRM. Only coaching platform with mobile app. Growing quickly. Best for solopreneurs who need essentials.",
        "api_available": False,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "satori-app",
        "name": "Satori",
        "category": "coaching_platform",
        "website": "https://satoriapp.com",
        "pricing_url": "https://satoriapp.com/pricing",
        "description": "Streamlined all-in-one coaching platform with client management, scheduling, packages, and business automation.",
        "tagline": "Run your coaching business with ease",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 33,
            "free_tier": True,
            "free_trial_days": 30,
            "tiers": [
                {"name": "Scholar", "price": 0, "per": "month", "notes": "Free for coaching students, unlimited pro-bono clients"},
                {"name": "Essentials", "price": 33, "per": "month", "notes": "Up to 10 active clients"},
                {"name": "Pro", "price": None, "per": "month", "notes": "For growing practices"},
                {"name": "Leader", "price": None, "per": "month", "notes": "CEO/scaling support"},
            ],
            "notes": "No setup fees. No cancellation fees. No contracts. 30-day trial, no credit card required."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["coaching"],
        "best_for": ["new coaches", "coaching students", "coaches scaling up", "certified coaches"],
        "key_capabilities": ["client management", "scheduling", "packages", "contracts", "invoicing", "client portal"],
        "integrations": ["Zoom", "Google Calendar", "Stripe", "PayPal"],
        "capterra_score": 4.8,
        "our_rating": 4.4,
        "our_notes": "Unique free Scholar plan for coaching students. Clean interface. Good for new coaches building their practice.",
        "api_available": False,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "simply-coach",
        "name": "Simply.Coach",
        "category": "coaching_platform",
        "website": "https://simply.coach",
        "pricing_url": "https://simply.coach/pricing-for-solopreneurs/",
        "description": "Digital coaching platform for coaches, consultants, therapists, and trainers with comprehensive practice management tools.",
        "tagline": "Your complete coaching platform",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 9,
            "free_tier": False,
            "free_trial_days": 14,
            "tiers": [
                {"name": "Starter", "price": 9, "per": "month"},
                {"name": "Essentials", "price": 29, "per": "month"},
                {"name": "Growth", "price": 39, "per": "month"},
                {"name": "Leap", "price": 59, "per": "month", "notes": "Custom domain included"},
                {"name": "CoCreate", "price": 69, "per": "month"},
                {"name": "Surge", "price": 129, "per": "month"},
            ],
            "notes": "Save up to 52% on annual plans. Available in English, Spanish, French."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["coaching"],
        "best_for": ["coaches", "consultants", "therapists", "trainers", "multi-coach practices"],
        "key_capabilities": ["scheduling", "client management", "program delivery", "invoicing", "custom domain", "multilingual"],
        "integrations": ["Zoom", "Google Meet", "Calendar", "Stripe"],
        "g2_score": 4.8,
        "capterra_score": 4.7,
        "our_rating": 4.3,
        "our_notes": "Most flexible tier structure (6 plans). Multilingual support. Good for international coaches. Starter plan limited to 1GB storage.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "coachingloft",
        "name": "CoachingLoft",
        "category": "coaching_platform",
        "website": "https://www.coachingloft.com",
        "pricing_url": "https://www.coachingloft.com/pricing",
        "description": "Professional coaching platform for scheduling, client progress tracking, and session record-keeping with central dashboard.",
        "tagline": "Manage your coaching practice",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 0,
            "free_tier": True,
            "tiers": [
                {"name": "Basic", "price": 0, "per": "month"},
                {"name": "Core", "price": 12, "per": "year", "notes": "Per user/year"},
                {"name": "Premium", "price": 25, "per": "month", "notes": "Unlimited clients"},
            ],
            "notes": "Every paid subscription plants trees. Eco-friendly platform."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["coaching"],
        "best_for": ["business coaches", "coaches needing central dashboard", "eco-conscious coaches"],
        "key_capabilities": ["scheduling", "client engagement", "progress tracking", "reporting", "virtual sessions", "client feedback"],
        "integrations": ["Zoom", "Google Calendar"],
        "g2_score": 4.8,
        "capterra_score": 4.7,
        "our_rating": 4.2,
        "our_notes": "Highest G2 rating (4.8). Free tier available. Unique eco-friendly mission. Good for coaches who want simple, ethical tools.",
        "api_available": False,
        "requires_developer": False,
        "tier": 2,
    },
    # Tier 3 - Enterprise/Premium
    {
        "slug": "coaches-console",
        "name": "Coaches Console",
        "category": "coaching_platform",
        "website": "https://coachesconsole.com",
        "pricing_url": "https://coachesconsole.com/pricing/",
        "description": "All-in-one coaching business platform with CRM, website builder, email marketing, course delivery, and billing.",
        "tagline": "Your complete coaching business system",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 197,
            "free_tier": False,
            "tiers": [
                {"name": "Core Console", "price": 197, "per": "month", "notes": "CRM, website, scheduling, email, billing"},
                {"name": "Total Console", "price": 297, "per": "month", "notes": "+ Shopping cart, courses, sales tracking"},
            ],
            "notes": "30-day money-back guarantee. No setup fees. No contracts. Instant access."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["coaching"],
        "best_for": ["life coaches", "health coaches", "business coaches", "coaches selling courses", "established practices"],
        "key_capabilities": ["CRM", "website builder", "scheduling", "email marketing", "billing", "course delivery", "shopping cart", "lead gen"],
        "integrations": ["Zoom", "Stripe", "PayPal"],
        "capterra_score": 4.6,
        "our_rating": 3.8,
        "our_notes": "Most comprehensive but expensive. Good for established coaches wanting all-in-one. May be overkill for new coaches. Paperbell is 1/4 the cost.",
        "api_available": False,
        "requires_developer": False,
        "tier": 3,
    },
    {
        "slug": "coachhub",
        "name": "CoachHub",
        "category": "coaching_platform",
        "website": "https://www.coachhub.com",
        "description": "Enterprise digital coaching platform for leadership development with global coach network. Serves Booking.com, Coca-Cola, Virgin Atlantic.",
        "tagline": "Digital coaching at scale",
        "pricing": {
            "model": "custom",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Enterprise pricing. Contact for quote. Serves 1000+ organizations globally."
        },
        "company_sizes": ["enterprise"],
        "industries": ["coaching"],
        "best_for": ["large enterprises", "leadership development", "executive coaching programs", "global organizations"],
        "key_capabilities": ["1:1 coaching", "executive coaching", "leadership development", "global coach network", "analytics", "ROI measurement"],
        "integrations": ["HRIS systems", "SSO", "LMS platforms"],
        "g2_score": 4.0,
        "our_rating": 4.0,
        "our_notes": "Enterprise-only. Top clients: Coca-Cola, Booking.com. Not for solo coaches. Best for organizations scaling coaching programs.",
        "api_available": True,
        "requires_developer": True,
        "tier": 3,
    },
    {
        "slug": "ezra-coaching",
        "name": "EZRA",
        "category": "coaching_platform",
        "website": "https://helloezra.com",
        "description": "Enterprise coaching platform providing 1:1 unlimited coaching for organizations. 2000+ certified coaches globally.",
        "tagline": "Coaching that transforms",
        "pricing": {
            "model": "custom",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Enterprise pricing. Contact for quote. Clients include Vodafone, Deloitte, Condé Nast."
        },
        "company_sizes": ["enterprise"],
        "industries": ["coaching"],
        "best_for": ["large enterprises", "executive leaders", "leadership development", "organizational transformation"],
        "key_capabilities": ["1:1 unlimited coaching", "executive coaching", "leadership assessment", "coach matching", "progress analytics", "EXRAX for executives"],
        "integrations": ["HRIS systems", "SSO"],
        "g2_score": 4.6,
        "our_rating": 4.2,
        "our_notes": "One of largest external coach providers (2000+ coaches). Focus on executives and leaders. Enterprise-only pricing.",
        "api_available": True,
        "requires_developer": True,
        "tier": 3,
    },
    {
        "slug": "trafft",
        "name": "Trafft",
        "category": "scheduling",
        "website": "https://trafft.com",
        "pricing_url": "https://trafft.com/pricing/",
        "description": "Smart scheduling and booking software for coaches and service businesses with automated reminders and payments.",
        "tagline": "Scheduling made simple",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 0,
            "free_tier": True,
            "tiers": [
                {"name": "Free", "price": 0, "per": "month", "notes": "1 location, 5 employees"},
                {"name": "Basic", "price": 19, "per": "month"},
                {"name": "Pro", "price": 49, "per": "month"},
                {"name": "Expert", "price": 99, "per": "month"},
            ],
            "notes": "Save 33% on annual billing."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["coaching"],
        "best_for": ["coaches needing scheduling focus", "service businesses", "multi-location practices"],
        "key_capabilities": ["online booking", "automated reminders", "payment processing", "calendar sync", "group bookings", "customizable pages"],
        "integrations": ["Zoom", "Google Calendar", "Stripe", "PayPal", "Zapier"],
        "g2_score": 4.7,
        "capterra_score": 5.0,
        "our_rating": 4.5,
        "our_notes": "Top-rated scheduling tool (5/5 Capterra). Free tier available. Great for coaches who need robust booking but have other tools for CRM.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
]


async def import_vendors():
    """Import all coaching vendors to Supabase."""
    supabase = await get_async_supabase()

    imported = 0
    skipped = 0
    failed = 0
    vendor_ids = {}  # slug -> id mapping for tier assignment

    print(f"\n{'='*60}")
    print("Importing Coaching Vendors to Supabase")
    print(f"{'='*60}\n")

    for vendor_data in COACHING_VENDORS:
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
                    "changes": {"source": "coaching-vendors-research-2026-01"},
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


async def set_coaching_tiers(vendor_ids: dict):
    """Set industry tier assignments for coaching vendors."""
    supabase = await get_async_supabase()

    # Tier assignments based on research
    tier_assignments = [
        # Tier 1 - Best for Solo Coaches
        ("coachaccountable", 1, 10, "Most established, since 2012"),
        ("paperbell", 1, 9, "Best value, unlimited clients"),
        ("honeybook", 1, 8, "Great UX, USA/Canada only"),
        # Tier 2 - Strong Alternatives
        ("practice-do", 2, 8, "Most affordable, mobile app"),
        ("satori-app", 2, 7, "Free Scholar plan"),
        ("simply-coach", 2, 7, "Multilingual, flexible tiers"),
        ("coachingloft", 2, 6, "Highest G2, eco-friendly"),
        ("trafft", 2, 8, "Top scheduling, free tier"),
        # Tier 3 - Enterprise/Premium
        ("coaches-console", 3, 5, "Comprehensive but expensive"),
        ("coachhub", 3, 6, "Enterprise leadership dev"),
        ("ezra-coaching", 3, 6, "2000+ coaches, enterprise"),
    ]

    print(f"\n{'='*60}")
    print("Setting Coaching Industry Tiers")
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
                "industry": "coaching",
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
    print("COACHING VENDOR IMPORT")
    print("="*60)

    # Import vendors
    vendor_ids = await import_vendors()

    # Set tiers
    await set_coaching_tiers(vendor_ids)

    print("\nDone! Verify at /admin/vendors or run:")
    print("  SELECT * FROM vendors WHERE industries @> '[\"coaching\"]'::jsonb;")
    print("  SELECT * FROM industry_vendor_tiers WHERE industry = 'coaching';")


if __name__ == "__main__":
    asyncio.run(main())
