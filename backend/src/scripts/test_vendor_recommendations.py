"""
Test Vendor Recommendation Scenarios

Simulates different business contexts and verifies the recommendation engine
returns appropriate vendors.

Run: cd backend && source venv/bin/activate && python -m src.scripts.test_vendor_recommendations
"""

import asyncio
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.services.vendor_service import vendor_service


# Test scenarios
SCENARIOS = [
    {
        "name": "Dental: Reduce no-shows",
        "industry": "dental",
        "finding": {
            "title": "High patient no-show rate",
            "description": "Practice is losing $50K/year to no-shows. Need automated patient reminders and communication.",
            "category": "patient_communication",
        },
        "company_context": {
            "employee_count": 10,
            "budget": "moderate",
        },
        "expected_tier1": ["weave", "nexhealth", "revenuewell"],
        "should_not_include": [],
    },
    {
        "name": "Solo Coach: Client Management",
        "industry": "coaching",
        "finding": {
            "title": "Need client scheduling and payments",
            "description": "Solo executive coach needs simple client management, scheduling, and payment processing.",
            "category": "practice_management",
        },
        "company_context": {
            "employee_count": 1,
            "budget": "low",
        },
        "expected_tier1": ["paperbell", "coachaccountable", "honeybook"],
        "should_not_include": ["coachhub"],  # Enterprise solution, not for solos
    },
    {
        "name": "5-Location MedSpa: Unified Management",
        "industry": "medspa",
        "finding": {
            "title": "Need unified multi-location management",
            "description": "5-location medspa chain needs unified appointment booking, inventory, and reporting across all locations.",
            "category": "practice_management",
        },
        "company_context": {
            "employee_count": 50,
            "budget": "high",
        },
        "expected_tier1": ["mangomint", "boulevard", "zenoti"],
        "should_not_include": [],
    },
    {
        "name": "Small HVAC: Budget Field Service",
        "industry": "home-services",
        "finding": {
            "title": "Field service software for small team",
            "description": "Small HVAC company with 3 technicians needs scheduling and invoicing. Budget under $100/month.",
            "category": "field_service",
        },
        "company_context": {
            "employee_count": 5,
            "budget": "low",
        },
        "expected_tier1": ["jobber", "housecall-pro"],
        "should_not_include": ["servicetitan"],  # Too expensive for budget
    },
]


async def test_scenario(scenario: dict) -> dict:
    """Test a single recommendation scenario."""
    print(f"\n{'='*60}")
    print(f"SCENARIO: {scenario['name']}")
    print(f"{'='*60}")
    print(f"Industry: {scenario['industry']}")
    print(f"Finding: {scenario['finding']['title']}")
    print(f"Company Size: {scenario['company_context']['employee_count']} employees")
    print(f"Budget: {scenario['company_context']['budget']}")
    print()

    # Extract finding tags (simulating what vendor_matching.py does)
    finding_tags = []
    text = " ".join([
        scenario["finding"]["title"],
        scenario["finding"]["description"],
        scenario["finding"]["category"],
    ]).lower()

    tag_keywords = {
        "scheduling": ["schedule", "scheduling", "appointment", "booking"],
        "communication": ["reminder", "communication", "message", "text", "sms"],
        "payments": ["payment", "invoice", "billing"],
        "field_service": ["field", "technician", "service", "dispatch"],
        "multi_location": ["multi-location", "unified", "chain", "locations"],
    }
    for tag, keywords in tag_keywords.items():
        if any(kw in text for kw in keywords):
            finding_tags.append(tag)

    # Get vendors with tier boosts
    vendors = await vendor_service.get_vendors_with_tier_boost(
        industry=scenario["industry"],
        category=None,  # Let it search all categories
        finding_tags=finding_tags,
        company_context=scenario["company_context"],
    )

    # Show top 10 vendors
    print("TOP 10 VENDORS BY RECOMMENDATION SCORE:")
    print("-" * 60)
    for i, v in enumerate(vendors[:10]):
        tier = v.get("_tier", "N/A")
        boost = v.get("_tier_boost", 0)
        rec_score = v.get("_recommendation_score", 0)
        pricing = v.get("pricing", {}) or {}
        price = pricing.get("starting_price", "Custom")

        print(f"  {i+1}. {v['name']} ({v['slug']})")
        print(f"     Tier: {tier}, Boost: {boost}, Rec Score: {rec_score}, Price: ${price}")

    # Check expected vendors
    print()
    print("EXPECTED VENDORS CHECK:")
    print("-" * 60)

    results = {
        "scenario": scenario["name"],
        "passed": True,
        "issues": [],
    }

    # Check expected tier 1 vendors are in top results
    top_slugs = [v["slug"] for v in vendors[:10]]

    for expected in scenario["expected_tier1"]:
        if expected in top_slugs:
            print(f"  [PASS] {expected} found in top 10")
        else:
            # Check if it exists at all
            all_slugs = [v["slug"] for v in vendors]
            if expected in all_slugs:
                rank = all_slugs.index(expected) + 1
                print(f"  [WARN] {expected} found at rank {rank} (expected top 10)")
                results["issues"].append(f"{expected} ranked {rank} instead of top 10")
            else:
                print(f"  [FAIL] {expected} NOT FOUND in results")
                results["issues"].append(f"{expected} not found at all")
                results["passed"] = False

    # Check vendors that should NOT be recommended
    for excluded in scenario.get("should_not_include", []):
        if excluded in top_slugs[:5]:
            print(f"  [FAIL] {excluded} incorrectly in top 5 (should be excluded)")
            results["issues"].append(f"{excluded} incorrectly in top 5")
            results["passed"] = False
        else:
            print(f"  [PASS] {excluded} correctly excluded from top 5")

    return results


async def main():
    """Run all test scenarios."""
    print("\n" + "="*70)
    print("VENDOR RECOMMENDATION ENGINE TEST")
    print("="*70)

    all_results = []

    for scenario in SCENARIOS:
        result = await test_scenario(scenario)
        all_results.append(result)

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for r in all_results if r["passed"])
    total = len(all_results)

    for r in all_results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['scenario']}")
        for issue in r["issues"]:
            print(f"       - {issue}")

    print()
    print(f"RESULT: {passed}/{total} scenarios passed")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
