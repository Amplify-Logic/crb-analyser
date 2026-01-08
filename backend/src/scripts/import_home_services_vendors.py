"""
Import Home Services Vendors to Supabase

Imports verified home services vendors (HVAC, plumbing, electrical, field service)
from research and sets industry tiers.

Run: python -m src.scripts.import_home_services_vendors
"""

import asyncio
from datetime import datetime
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config.supabase_client import get_async_supabase


# Verified home services vendors to import
HOME_SERVICES_VENDORS = [
    # Tier 1 - Market Leaders
    {
        "slug": "housecall-pro",
        "name": "Housecall Pro",
        "category": "field_service_management",
        "website": "https://www.housecallpro.com",
        "pricing_url": "https://www.housecallpro.com/pricing/",
        "description": "All-in-one business management software for home service professionals with scheduling, dispatching, invoicing, and customer communication.",
        "tagline": "Grow your home service business",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 59,
            "free_tier": False,
            "free_trial_days": 14,
            "tiers": [
                {"name": "Basic", "price": 59, "per": "month", "users": 1, "notes": "Billed annually, $79 monthly"},
                {"name": "Essentials", "price": 149, "per": "month", "users": 5, "notes": "Billed annually, $189 monthly"},
                {"name": "MAX", "price": 299, "per": "month", "users": 8, "notes": "Billed annually, $329 monthly"},
            ],
            "notes": "No long-term contracts required. Credit card processing: 2.59%+"
        },
        "company_sizes": ["small", "medium"],
        "industries": ["home-services"],
        "best_for": ["small to mid-size home service businesses", "HVAC contractors", "plumbers", "electricians", "cleaning services"],
        "key_capabilities": ["scheduling", "dispatching", "invoicing", "estimates", "payment processing", "customer communication", "GPS tracking", "marketing automation"],
        "integrations": ["QuickBooks", "Google Calendar", "Zapier", "Stripe", "Square"],
        "g2_score": 4.3,
        "g2_reviews": 190,
        "capterra_score": 4.7,
        "capterra_reviews": 2817,
        "our_rating": 4.5,
        "our_notes": "Best value for small teams. Easy to use, excellent mobile app. 80% of users are SMBs with <200 employees.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    {
        "slug": "jobber",
        "name": "Jobber",
        "category": "field_service_management",
        "website": "https://www.getjobber.com",
        "pricing_url": "https://www.getjobber.com/pricing/",
        "description": "Field service management software for home and commercial service businesses. Streamlines quoting, scheduling, invoicing, and client communication.",
        "tagline": "Run your service business like a pro",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 39,
            "free_tier": False,
            "free_trial_days": 14,
            "tiers": [
                {"name": "Core", "price": 39, "per": "month", "users": 1, "notes": "$29/mo billed annually"},
                {"name": "Connect", "price": 119, "per": "month", "users": 5, "notes": "$29/extra user"},
                {"name": "Grow", "price": 199, "per": "month", "users": 10, "notes": "$29/extra user"},
                {"name": "Connect Team", "price": 169, "per": "month", "users": 5},
                {"name": "Grow Team", "price": 349, "per": "month", "users": 10},
                {"name": "Plus", "price": 599, "per": "month", "users": 15, "notes": "AI Receptionist, Marketing Suite"},
            ],
            "notes": "Annual billing saves up to 40%. No credit card required for trial."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["home-services"],
        "best_for": ["landscaping", "HVAC", "plumbing", "electrical", "cleaning", "pest control", "owner-operators"],
        "key_capabilities": ["quoting", "scheduling", "invoicing", "CRM", "mobile app", "client hub", "payment processing", "automated follow-ups"],
        "integrations": ["QuickBooks", "Xero", "Stripe", "Square", "Mailchimp", "Zapier"],
        "g2_score": 4.5,
        "g2_reviews": 295,
        "capterra_score": 4.5,
        "capterra_reviews": 936,
        "our_rating": 4.6,
        "our_notes": "Excellent for owner-operators and small teams. Very intuitive interface. 50+ industries supported. Quick ROI.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    {
        "slug": "servicetitan",
        "name": "ServiceTitan",
        "category": "field_service_management",
        "website": "https://www.servicetitan.com",
        "pricing_url": "https://www.servicetitan.com/pricing",
        "description": "Enterprise-grade field service management platform for HVAC, plumbing, electrical, and water treatment companies with comprehensive operations automation.",
        "tagline": "The operating system for the trades",
        "pricing": {
            "model": "custom",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "tiers": [
                {"name": "Starter", "price": None, "per": "month"},
                {"name": "Essentials", "price": None, "per": "month"},
                {"name": "The Works", "price": None, "per": "month"},
            ],
            "notes": "Custom pricing per technician ($200-500+/tech/month typical). Implementation: $10,000-50,000+. 3-6 month onboarding."
        },
        "company_sizes": ["medium", "enterprise"],
        "industries": ["home-services"],
        "best_for": ["established trade businesses", "HVAC contractors", "plumbing companies", "electrical contractors", "11-200 employees"],
        "key_capabilities": ["dispatching", "scheduling", "pricebook", "marketing automation", "reporting", "inventory management", "call tracking", "memberships"],
        "integrations": ["QuickBooks", "Intuit", "Google Local Services", "major equipment suppliers"],
        "g2_score": 4.5,
        "g2_reviews": 317,
        "capterra_score": 4.4,
        "our_rating": 4.3,
        "our_notes": "Industry leader for mid-size to large contractors. Expensive but comprehensive. 76% of users have 11-200 employees. High implementation cost.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    # Tier 2 - Strong Alternatives
    {
        "slug": "service-fusion",
        "name": "Service Fusion",
        "category": "field_service_management",
        "website": "https://www.servicefusion.com",
        "pricing_url": "https://www.servicefusion.com/pricing",
        "description": "All-in-one field service management software with no per-user fees. Built for HVAC, plumbing, electrical, and appliance repair contractors.",
        "tagline": "Simplify operations and grow faster",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 165,
            "free_tier": False,
            "tiers": [
                {"name": "Starter", "price": 165, "per": "month", "notes": "Billed annually, $195 monthly"},
                {"name": "Plus", "price": 250, "per": "month"},
                {"name": "Pro", "price": 421, "per": "month"},
            ],
            "notes": "NO per-user fees - unique in market. Unlimited users on all plans."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["home-services"],
        "best_for": ["growing teams", "HVAC", "plumbing", "electrical", "garage door", "appliance repair"],
        "key_capabilities": ["scheduling", "dispatching", "invoicing", "customer communication", "GPS fleet tracking", "flat rate pricing", "inventory management"],
        "integrations": ["QuickBooks", "Stripe", "Authorize.net"],
        "capterra_score": 4.3,
        "our_rating": 4.2,
        "our_notes": "Best value for growing teams due to no per-user fees. GPS tracking in all plans. Some users report price increases.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "servicem8",
        "name": "ServiceM8",
        "category": "field_service_management",
        "website": "https://www.servicem8.com",
        "pricing_url": "https://www.servicem8.com/pricing",
        "description": "Smart field service software with job-based pricing model. Designed for trade contractors and service businesses with high job turnover.",
        "tagline": "Smart job management for trades",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 0,
            "free_tier": True,
            "free_trial_days": 14,
            "tiers": [
                {"name": "Free", "price": 0, "per": "month", "notes": "Limited jobs"},
                {"name": "Starter", "price": 29, "per": "month", "notes": "50 jobs/month, unlimited users"},
                {"name": "Growing", "price": 79, "per": "month", "notes": "150 jobs/month"},
                {"name": "Premium", "price": 149, "per": "month"},
                {"name": "Premium Plus", "price": 349, "per": "month"},
            ],
            "notes": "Unique job-based pricing, not per-user. Unlimited users and storage on all plans."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["home-services"],
        "best_for": ["sole traders", "small teams up to 20 staff", "high job turnover businesses", "plumbers", "electricians", "HVAC"],
        "key_capabilities": ["job management", "scheduling", "quoting", "invoicing", "client communication", "asset management", "forms", "AI assists"],
        "integrations": ["Xero", "QuickBooks", "MYOB", "Stripe", "Zapier"],
        "g2_score": 4.4,
        "capterra_score": 4.6,
        "our_rating": 4.4,
        "our_notes": "Unique job-based pricing is cost-effective for high-volume businesses. No lock-ins. Free 24/7 support. Strong in Australia/NZ.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "workiz",
        "name": "Workiz",
        "category": "field_service_management",
        "website": "https://www.workiz.com",
        "pricing_url": "https://www.workiz.com/pricing-plans/",
        "description": "Field service management software with built-in phone system for plumbing, HVAC, electrical, and locksmith businesses.",
        "tagline": "The smarter way to manage field service",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 0,
            "free_tier": True,
            "tiers": [
                {"name": "Free", "price": 0, "per": "month", "users": 2},
                {"name": "Standard", "price": 229, "per": "month", "users": 5, "notes": "$46/extra user"},
                {"name": "Pro", "price": None, "per": "month", "notes": "$54/extra user, custom pricing"},
            ],
            "notes": "Annual billing saves $400+. Built-in phone system included. Genius AI answering: $200/mo add-on."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["home-services"],
        "best_for": ["plumbing", "HVAC", "electrical", "locksmith", "appliance repair", "small to medium teams"],
        "key_capabilities": ["scheduling", "dispatching", "built-in phone system", "call tracking", "invoicing", "estimates", "mobile app", "Genius AI"],
        "integrations": ["QuickBooks", "Zapier", "Google Calendar", "Stripe"],
        "g2_score": 4.6,
        "capterra_score": 4.6,
        "our_rating": 4.3,
        "our_notes": "Unique built-in phone system with call tracking. Free plan for 2 users. Good for SMBs. Limited integrations compared to competitors.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "fieldpulse",
        "name": "FieldPulse",
        "category": "field_service_management",
        "website": "https://www.fieldpulse.com",
        "description": "All-in-one field service software with flat-rate pricebook, lead management, and inventory tracking for trade businesses.",
        "tagline": "The all-in-one solution for field service",
        "pricing": {
            "model": "custom",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "free_trial_days": 14,
            "custom_pricing": True,
            "notes": "Custom pricing based on team size (5-100+ users). No hidden fees. Contact for quote."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["home-services"],
        "best_for": ["HVAC", "plumbing", "electrical", "garage door", "locksmith", "septic", "glass repair", "5-100 person teams"],
        "key_capabilities": ["scheduling", "dispatching", "flat-rate pricebook", "lead management", "inventory management", "invoicing", "CRM", "mobile app"],
        "integrations": ["QuickBooks", "Xero", "Stripe", "Square", "Zapier"],
        "g2_score": 4.6,
        "capterra_score": 4.6,
        "our_rating": 4.4,
        "our_notes": "Strong flat-rate pricebook feature. Good for mid-size teams. Flexible pricing without hidden fees.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    # Tier 2 - Specialized/Enterprise
    {
        "slug": "fieldedge",
        "name": "FieldEdge",
        "category": "field_service_management",
        "website": "https://fieldedge.com",
        "pricing_url": "https://fieldedge.com/pricing/",
        "description": "Cloud-based field service management for HVAC, plumbing, electrical, and appliance repair with flat rate pricing software.",
        "tagline": "Field service management for contractors",
        "pricing": {
            "model": "custom",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Custom pricing based on business size. Onboarding: ~$1,500. Contact for quote."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["home-services"],
        "best_for": ["HVAC contractors", "plumbers", "electricians", "appliance repair", "established businesses"],
        "key_capabilities": ["scheduling", "dispatching", "flat rate pricing", "customer history", "invoicing", "reporting", "service agreements"],
        "integrations": ["QuickBooks", "major payment processors"],
        "capterra_score": 4.2,
        "our_rating": 4.0,
        "our_notes": "Solid HVAC-focused solution. Some users find it expensive. Hidden fees and price increases reported. Good flat rate module.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "zuper",
        "name": "Zuper",
        "category": "field_service_management",
        "website": "https://www.zuper.co",
        "description": "AI-powered field service management platform for mid-market and enterprise organizations with intelligent scheduling and automation.",
        "tagline": "Intelligent field service management",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 65,
            "free_tier": False,
            "tiers": [
                {"name": "Starter", "price": 65, "per": "user/month"},
                {"name": "Growth", "price": 85, "per": "user/month"},
                {"name": "Enterprise", "price": 105, "per": "user/month"},
            ],
            "notes": "Mid-range pricing. Contact for enterprise quotes."
        },
        "company_sizes": ["medium", "enterprise"],
        "industries": ["home-services"],
        "best_for": ["roofing", "HVAC", "plumbing", "electrical", "mid-market companies", "enterprise organizations"],
        "key_capabilities": ["AI scheduling", "dispatching", "work orders", "inventory management", "asset tracking", "route optimization", "analytics"],
        "integrations": ["Salesforce", "HubSpot", "Zendesk", "QuickBooks", "Zapier"],
        "g2_score": 4.7,
        "capterra_score": 4.6,
        "our_rating": 4.3,
        "our_notes": "Strong AI-based scheduling. Good for mid-market. Users note it's not cheap but a productivity multiplier.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    # Tier 3 - Budget/Niche Options
    {
        "slug": "mhelpdesk",
        "name": "mHelpDesk",
        "category": "field_service_management",
        "website": "https://www.mhelpdesk.com",
        "description": "Field service management software for HVAC, plumbers, electricians, and other trade businesses with job scheduling and invoicing.",
        "tagline": "Manage your business from anywhere",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 99,
            "free_tier": False,
            "free_trial_days": 7,
            "tiers": [
                {"name": "Starter", "price": 99, "per": "user/month"},
                {"name": "Pro", "price": 139, "per": "user/month"},
                {"name": "Enterprise", "price": None, "per": "user/month", "notes": "Custom pricing"},
            ],
            "notes": "Per-user pricing. Implementation: $500-5,000 depending on size."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["home-services"],
        "best_for": ["HVAC", "plumbers", "electricians", "pest control", "computer repair", "cleaning services", "up to 200 employees"],
        "key_capabilities": ["scheduling", "dispatching", "invoicing", "estimates", "customer management", "mobile app", "GPS tracking"],
        "integrations": ["QuickBooks", "Google Calendar"],
        "capterra_score": 4.3,
        "our_rating": 3.8,
        "our_notes": "Good for basic needs. Per-user pricing can add up. Teams under 8 should use Pro or Growth plans.",
        "api_available": True,
        "requires_developer": False,
        "tier": 3,
    },
    {
        "slug": "kickserv",
        "name": "Kickserv",
        "category": "field_service_management",
        "website": "https://www.kickserv.com",
        "pricing_url": "https://www.kickserv.com/pricing/",
        "description": "Simple, affordable field service management software for small businesses with essential job management features.",
        "tagline": "Simple job management for small businesses",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 47,
            "free_tier": True,
            "free_trial_days": 14,
            "tiers": [
                {"name": "Free", "price": 0, "per": "month", "users": 2},
                {"name": "Lite", "price": 47, "per": "month", "users": 5},
                {"name": "Standard", "price": 95, "per": "month", "users": 10},
                {"name": "Business", "price": 159, "per": "month", "users": 20},
                {"name": "Premium", "price": 239, "per": "month", "notes": "Unlimited users"},
            ],
            "notes": "Free plan includes 2 users. Very affordable for small teams."
        },
        "company_sizes": ["small"],
        "industries": ["home-services"],
        "best_for": ["small businesses", "startups", "budget-conscious contractors", "basic job management needs"],
        "key_capabilities": ["job scheduling", "estimates", "invoicing", "customer management", "mobile app", "payment processing"],
        "integrations": ["QuickBooks", "Xero", "Stripe", "Square"],
        "capterra_score": 4.4,
        "our_rating": 4.0,
        "our_notes": "Best budget option with free tier. Simple and easy to use. Good for businesses just starting out.",
        "api_available": True,
        "requires_developer": False,
        "tier": 3,
    },
    {
        "slug": "gorilladesk",
        "name": "GorillaDesk",
        "category": "field_service_management",
        "website": "https://www.gorilladesk.com",
        "pricing_url": "https://www.gorilladesk.com/pricing/",
        "description": "Field service software designed specifically for pest control, lawn care, and pool service businesses with route optimization.",
        "tagline": "Built for pest control & lawn care",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 49,
            "free_tier": False,
            "free_trial_days": 14,
            "tiers": [
                {"name": "Basic", "price": 49, "per": "month", "notes": "Single route"},
                {"name": "Pro", "price": 99, "per": "month", "notes": "Multiple routes"},
                {"name": "Growth", "price": 149, "per": "month"},
            ],
            "notes": "Route-based pricing unique to the industry."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["home-services"],
        "best_for": ["pest control", "lawn care", "pool service", "cleaning services", "route-based businesses"],
        "key_capabilities": ["route optimization", "scheduling", "customer portal", "invoicing", "chemical tracking", "mobile app", "automated reminders"],
        "integrations": ["QuickBooks", "Stripe", "Zapier"],
        "g2_score": 4.8,
        "capterra_score": 4.8,
        "our_rating": 4.5,
        "our_notes": "Excellent for route-based services. Top-rated in niche. Chemical tracking unique for pest control.",
        "api_available": True,
        "requires_developer": False,
        "tier": 3,
    },
    {
        "slug": "simpro",
        "name": "Simpro",
        "category": "field_service_management",
        "website": "https://www.simprogroup.com",
        "description": "Enterprise job management software for trade and field service businesses with advanced project management and asset tracking.",
        "tagline": "End-to-end job management",
        "pricing": {
            "model": "custom",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Enterprise pricing. Contact for quote. Implementation and training included."
        },
        "company_sizes": ["medium", "enterprise"],
        "industries": ["home-services"],
        "best_for": ["security and fire protection", "HVAC", "electrical", "plumbing", "mid-size to enterprise contractors"],
        "key_capabilities": ["project management", "job costing", "asset tracking", "inventory", "scheduling", "invoicing", "advanced reporting"],
        "integrations": ["QuickBooks", "Xero", "MYOB", "Sage"],
        "g2_score": 4.1,
        "capterra_score": 4.1,
        "our_rating": 4.0,
        "our_notes": "Strong for complex projects. Australian origin, global presence. Better for larger operations with project complexity.",
        "api_available": True,
        "requires_developer": False,
        "tier": 3,
    },
]


async def import_vendors():
    """Import all home services vendors to Supabase."""
    supabase = await get_async_supabase()

    imported = 0
    skipped = 0
    failed = 0
    vendor_ids = {}  # slug -> id mapping for tier assignment

    print(f"\n{'='*60}")
    print("Importing Home Services Vendors to Supabase")
    print(f"{'='*60}\n")

    for vendor_data in HOME_SERVICES_VENDORS:
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
                    "changes": {"source": "home-services-vendors-research-2026-01"},
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


async def set_home_services_tiers(vendor_ids: dict):
    """Set industry tier assignments for home services vendors."""
    supabase = await get_async_supabase()

    # Tier assignments based on research
    tier_assignments = [
        # Tier 1 - Market Leaders
        ("housecall-pro", 1, 9, "Best for SMBs, excellent mobile app"),
        ("jobber", 1, 10, "Top-rated, intuitive, 50+ industries"),
        ("servicetitan", 1, 8, "Enterprise leader, comprehensive"),
        # Tier 2 - Strong Alternatives
        ("service-fusion", 2, 7, "No per-user fees, growing teams"),
        ("servicem8", 2, 7, "Job-based pricing, cost-effective"),
        ("workiz", 2, 6, "Built-in phone system, free tier"),
        ("fieldpulse", 2, 7, "Great flat-rate pricebook"),
        ("fieldedge", 2, 5, "HVAC-focused, solid features"),
        ("zuper", 2, 6, "AI-powered, mid-market"),
        # Tier 3 - Budget/Niche
        ("mhelpdesk", 3, 4, "Basic needs, per-user pricing"),
        ("kickserv", 3, 5, "Budget-friendly, free tier"),
        ("gorilladesk", 3, 8, "Pest control & lawn care specialist"),
        ("simpro", 3, 5, "Enterprise projects, complex jobs"),
    ]

    print(f"\n{'='*60}")
    print("Setting Home Services Industry Tiers")
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
                "industry": "home-services",
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
    print("HOME SERVICES VENDOR IMPORT")
    print("="*60)

    # Import vendors
    vendor_ids = await import_vendors()

    # Set tiers
    await set_home_services_tiers(vendor_ids)

    print("\nDone! Verify at /admin/vendors or run:")
    print("  SELECT * FROM vendors WHERE industries @> '[\"home-services\"]'::jsonb;")
    print("  SELECT * FROM industry_vendor_tiers WHERE industry = 'home-services';")


if __name__ == "__main__":
    asyncio.run(main())
