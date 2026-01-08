"""
Import Veterinary Vendors to Supabase

Imports verified veterinary practice management software
from research and sets industry tiers.

Run: python -m src.scripts.import_veterinary_vendors
"""

import asyncio
from datetime import datetime, timezone
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config.supabase_client import get_async_supabase


# Verified veterinary vendors to import
VETERINARY_VENDORS = [
    # Tier 1 - Market Leaders
    {
        "slug": "ezyvet",
        "name": "ezyVet",
        "category": "veterinary_practice_management",
        "website": "https://www.ezyvet.com",
        "pricing_url": "https://www.ezyvet.com/pricing/us",
        "description": "Cloud-based veterinary practice management software for primary care, emergency, specialty, and university settings. All features included in subscription.",
        "tagline": "Brilliantly simple veterinary software",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 245,
            "free_tier": False,
            "tiers": [
                {"name": "Standard", "price": 245, "per": "month", "notes": "All features included"},
            ],
            "notes": "6-month initial term, 3-month rolling after. Implementation scoped separately. 24/7 support, hosting, and updates included. Enterprise pricing available."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["veterinary"],
        "best_for": ["primary care clinics", "emergency hospitals", "specialty practices", "universities", "multi-location groups"],
        "key_capabilities": ["practice management", "electronic medical records", "scheduling", "billing", "inventory", "reporting", "integrations", "client portal"],
        "integrations": ["IDEXX", "Zoetis", "VetConnect", "Stripe", "QuickBooks"],
        "g2_score": 4.3,
        "capterra_score": 4.4,
        "our_rating": 4.5,
        "our_notes": "All features included at one price. No upgrade fees. Cloud-based with 24/7 support. Good for multi-location and specialty practices.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    {
        "slug": "shepherd-vet",
        "name": "Shepherd Veterinary Software",
        "category": "veterinary_practice_management",
        "website": "https://www.shepherd.vet",
        "description": "Cloud-based practice management with AI-powered features including TranscribeAI for SOAP notes and DiagnoseAI for treatment suggestions.",
        "tagline": "AI-powered veterinary software",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 299,
            "free_tier": False,
            "notes": "All-inclusive pricing. Support and training included. Low migration cost. Good value for multi-DVM practices."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["veterinary"],
        "best_for": ["AI-forward practices", "multi-DVM clinics", "practices wanting modern UX", "SOAP-focused workflows"],
        "key_capabilities": ["AI SOAP notes", "AI diagnosis suggestions", "scheduling", "billing", "inventory", "client communication", "SOAP-based interface"],
        "integrations": ["IDEXX", "Antech", "Zoetis", "payment processors"],
        "capterra_score": 4.7,
        "our_rating": 4.6,
        "our_notes": "Most AI-forward vet software. TranscribeAI and DiagnoseAI are differentiators. Good value for 7+ DVM practices. Simple pricing.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    {
        "slug": "digitail",
        "name": "Digitail",
        "category": "veterinary_practice_management",
        "website": "https://digitail.com",
        "pricing_url": "https://digitail.com/pricing/",
        "description": "AI-native all-in-one platform for veterinary clinics with 15+ AI workflows. Helps practices see up to 2x more patients per day.",
        "tagline": "AI-native veterinary platform",
        "pricing": {
            "model": "custom",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Contact for pricing. Trusted by 10,000+ vets in 20+ countries. Unlimited training, dedicated support included. Free consulting for new practices."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["veterinary"],
        "best_for": ["new practices", "AI-forward clinics", "high-volume practices", "practices wanting mobile client app"],
        "key_capabilities": ["AI-powered assistant", "SOAP notes automation", "scheduling", "billing", "inventory", "Pet Parent App", "treatment planning", "30+ integrations"],
        "integrations": ["IDEXX", "Antech", "Zoetis", "payment gateways", "lab integrations"],
        "g2_score": 4.6,
        "capterra_score": 4.7,
        "our_rating": 4.5,
        "our_notes": "Leading AI-native platform. 15+ AI workflows. Helps 3-4 new practices launch weekly. Pet Parent App is unique. 10,000+ users globally.",
        "api_available": True,
        "requires_developer": False,
        "tier": 1,
    },
    # Tier 2 - Strong Alternatives
    {
        "slug": "vetport",
        "name": "VetPort",
        "category": "veterinary_practice_management",
        "website": "https://www.vetport.com",
        "pricing_url": "https://www.vetport.com/pricing",
        "description": "Pioneer in cloud-based veterinary practice management with SOAP-based electronic medical records. Used by 12,500+ vets across 20+ countries.",
        "tagline": "Pioneer in cloud veterinary software",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 199,
            "free_tier": False,
            "free_trial_days": True,
            "tiers": [
                {"name": "Standard", "price": 199, "per": "month"},
                {"name": "Premium", "price": 229, "per": "month"},
            ],
            "notes": "Simple and affordable. Free support. Transparent pricing. Serves universities, hospitals, mobile clinics."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["veterinary"],
        "best_for": ["universities", "large hospitals", "group practices", "specialty clinics", "equine practices", "mobile clinics"],
        "key_capabilities": ["SOAP-based EMR", "scheduling", "billing", "inventory", "lab integrations", "client portal", "telemedicine"],
        "integrations": ["IDEXX", "Antech", "Zoetis", "VetConnect"],
        "g2_score": 4.1,
        "capterra_score": 4.2,
        "our_rating": 4.2,
        "our_notes": "Pioneer in cloud vet software. 12,500+ vets, 16M+ pets. Good for diverse practice types including equine. Affordable pricing.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "covetrus-pulse",
        "name": "Covetrus Pulse (eVetPractice)",
        "category": "veterinary_practice_management",
        "website": "https://www.covetrus.com/solutions/software/pulse/",
        "description": "Cloud-based veterinary practice management platform unifying workflows for productivity and patient care.",
        "tagline": "Unify your practice workflows",
        "pricing": {
            "model": "custom",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "free_trial_days": 30,
            "custom_pricing": True,
            "notes": "Custom pricing based on practice size and needs. 30-day free trial available."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["veterinary"],
        "best_for": ["single-location clinics", "multi-location groups", "practices wanting scalability"],
        "key_capabilities": ["practice management", "scheduling", "billing", "inventory", "EMR", "reporting", "integrations"],
        "integrations": ["Covetrus pharmacy", "lab systems", "payment processors"],
        "g2_score": 4.0,
        "capterra_score": 4.2,
        "our_rating": 4.0,
        "our_notes": "Part of Covetrus ecosystem. Good integration with Covetrus pharmacy. Custom pricing can vary. 30-day trial to evaluate.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "daysmart-vet",
        "name": "DaySmart Vet",
        "category": "veterinary_practice_management",
        "website": "https://www.daysmart.com/vet/",
        "pricing_url": "https://www.daysmart.com/vet/pricing/",
        "description": "Cloud-based practice management software to automate tasks, streamline workflows, and improve communication. Formerly Vetter Software.",
        "tagline": "Simplify your practice management",
        "pricing": {
            "model": "subscription",
            "currency": "USD",
            "starting_price": 116,
            "free_tier": False,
            "free_trial_days": 14,
            "notes": "Flexible pricing based on users. Add-ons for boarding, wellness plans, DICOM storage at extra cost. 14-day free trial."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["veterinary"],
        "best_for": ["small practices", "startups", "budget-conscious clinics", "scaling teams"],
        "key_capabilities": ["scheduling", "EMR", "billing", "inventory", "client communication", "boarding", "wellness plans", "reporting"],
        "integrations": ["IDEXX", "Antech", "payment processors"],
        "g2_score": 4.2,
        "capterra_score": 4.3,
        "our_rating": 4.1,
        "our_notes": "Most affordable starting price. Good for small/startup practices. Add-on costs for advanced features can add up. 14-day trial.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    {
        "slug": "instinct-science",
        "name": "Instinct Science",
        "category": "veterinary_practice_management",
        "website": "https://www.instinct.vet",
        "description": "Industry's first practice management software with natively integrated digital treatment sheets. Purpose-built for emergency and specialty practices.",
        "tagline": "Practice management for specialists",
        "pricing": {
            "model": "custom",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Custom pricing for emergency and specialty practices. Contact for quote."
        },
        "company_sizes": ["medium", "enterprise"],
        "industries": ["veterinary"],
        "best_for": ["emergency practices", "specialty hospitals", "24-hour clinics", "referral centers"],
        "key_capabilities": ["digital treatment sheets", "EMR", "scheduling", "billing", "ICU workflows", "specialty workflows"],
        "integrations": ["lab systems", "imaging systems", "payment processors"],
        "capterra_score": 4.5,
        "our_rating": 4.3,
        "our_notes": "Best for emergency/specialty. Unique digital treatment sheets. Not for general practice. Premium pricing for specialty workflows.",
        "api_available": True,
        "requires_developer": False,
        "tier": 2,
    },
    # Tier 3 - Legacy/Niche
    {
        "slug": "avimark",
        "name": "AVImark by Covetrus",
        "category": "veterinary_practice_management",
        "website": "https://www.covetrus.com/solutions/software/avimark/",
        "description": "Industry-leading on-premise practice management software used by 11,000+ veterinary hospitals. Powerful and scalable.",
        "tagline": "Industry-leading vet practice software",
        "pricing": {
            "model": "custom",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Custom pricing. No extra cost for additional workstations/users. On-premise installation. Some report high storage and support costs."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["veterinary"],
        "best_for": ["established practices", "practices preferring on-premise", "hospitals needing extensive features"],
        "key_capabilities": ["practice management", "EMR", "scheduling", "billing", "inventory", "reporting", "multi-location support"],
        "integrations": ["Covetrus pharmacy", "IDEXX", "Antech", "lab systems"],
        "capterra_score": 4.0,
        "our_rating": 3.8,
        "our_notes": "Legacy market leader (11,000+ hospitals). On-premise can be limiting. Some report hidden costs. Consider cloud alternatives for new practices.",
        "api_available": True,
        "requires_developer": False,
        "tier": 3,
    },
    {
        "slug": "cornerstone-idexx",
        "name": "Cornerstone by IDEXX",
        "category": "veterinary_practice_management",
        "website": "https://www.idexx.com/en/veterinary/software-services/cornerstone-software/",
        "description": "Comprehensive practice management system from IDEXX with deep lab integration and proven reliability.",
        "tagline": "Proven practice management from IDEXX",
        "pricing": {
            "model": "custom",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Custom pricing from IDEXX. Deep integration with IDEXX diagnostics. Contact for quote."
        },
        "company_sizes": ["small", "medium", "enterprise"],
        "industries": ["veterinary"],
        "best_for": ["IDEXX diagnostic users", "established practices", "practices valuing stability"],
        "key_capabilities": ["practice management", "EMR", "scheduling", "billing", "IDEXX lab integration", "imaging", "client communication"],
        "integrations": ["IDEXX diagnostics", "IDEXX lab systems", "VetConnect PLUS"],
        "capterra_score": 3.8,
        "our_rating": 3.7,
        "our_notes": "Best for heavy IDEXX diagnostic users. Proven and stable. Interface dated compared to newer cloud options. Premium pricing.",
        "api_available": True,
        "requires_developer": False,
        "tier": 3,
    },
    {
        "slug": "neo-idexx",
        "name": "Neo by IDEXX",
        "category": "veterinary_practice_management",
        "website": "https://software.idexx.com/neo/",
        "description": "Modern cloud-based veterinary software from IDEXX with flexibility and simplicity. Built for efficient practice management.",
        "tagline": "Brilliantly simple, cloud flexibility",
        "pricing": {
            "model": "custom",
            "currency": "USD",
            "starting_price": None,
            "free_tier": False,
            "custom_pricing": True,
            "notes": "Custom pricing from IDEXX. Cloud-based alternative to Cornerstone. Contact for quote."
        },
        "company_sizes": ["small", "medium"],
        "industries": ["veterinary"],
        "best_for": ["IDEXX ecosystem users", "practices wanting cloud", "modern practices"],
        "key_capabilities": ["cloud practice management", "scheduling", "billing", "EMR", "IDEXX integration", "mobile access"],
        "integrations": ["IDEXX diagnostics", "IDEXX lab systems", "VetConnect PLUS"],
        "our_rating": 4.0,
        "our_notes": "IDEXX's cloud offering. Good for practices in IDEXX ecosystem wanting cloud. Newer product, evolving feature set.",
        "api_available": True,
        "requires_developer": False,
        "tier": 3,
    },
]


async def import_vendors():
    """Import all veterinary vendors to Supabase."""
    supabase = await get_async_supabase()

    imported = 0
    skipped = 0
    failed = 0
    vendor_ids = {}  # slug -> id mapping for tier assignment

    print(f"\n{'='*60}")
    print("Importing Veterinary Vendors to Supabase")
    print(f"{'='*60}\n")

    for vendor_data in VETERINARY_VENDORS:
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
                    "changes": {"source": "veterinary-vendors-research-2026-01"},
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


async def set_veterinary_tiers(vendor_ids: dict):
    """Set industry tier assignments for veterinary vendors."""
    supabase = await get_async_supabase()

    # Tier assignments based on research
    tier_assignments = [
        # Tier 1 - Market Leaders
        ("ezyvet", 1, 10, "All features included, cloud-native"),
        ("shepherd-vet", 1, 9, "AI-powered, modern UX"),
        ("digitail", 1, 9, "AI-native, 10k+ users"),
        # Tier 2 - Strong Alternatives
        ("vetport", 2, 7, "Pioneer, 12.5k+ vets"),
        ("covetrus-pulse", 2, 6, "Covetrus ecosystem"),
        ("daysmart-vet", 2, 7, "Most affordable"),
        ("instinct-science", 2, 8, "Emergency/specialty focus"),
        # Tier 3 - Legacy/Niche
        ("avimark", 3, 5, "Legacy leader, on-premise"),
        ("cornerstone-idexx", 3, 4, "IDEXX ecosystem"),
        ("neo-idexx", 3, 5, "IDEXX cloud option"),
    ]

    # Also link Weave to veterinary if it exists
    weave_result = await supabase.table("vendors").select("id").eq("slug", "weave").execute()
    if weave_result.data:
        vendor_ids["weave"] = weave_result.data[0]["id"]
        tier_assignments.append(("weave", 2, 7, "Multi-industry communication"))

    print(f"\n{'='*60}")
    print("Setting Veterinary Industry Tiers")
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
                "industry": "veterinary",
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
    print("VETERINARY VENDOR IMPORT")
    print("="*60)

    # Import vendors
    vendor_ids = await import_vendors()

    # Set tiers
    await set_veterinary_tiers(vendor_ids)

    print("\nDone! Verify at /admin/vendors or run:")
    print("  SELECT * FROM vendors WHERE industries @> '[\"veterinary\"]'::jsonb;")
    print("  SELECT * FROM industry_vendor_tiers WHERE industry = 'veterinary';")


if __name__ == "__main__":
    asyncio.run(main())
