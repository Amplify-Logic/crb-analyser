"""
Test script for vendor refresh functionality.
Run with: python -m pytest tests/test_vendor_refresh.py -v
Or standalone: python tests/test_vendor_refresh.py
"""

import asyncio
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.vendor_refresh_service import VendorRefreshService


async def test_pricing_extraction():
    """Test AI pricing extraction with sample HTML."""
    service = VendorRefreshService()

    # Sample pricing page HTML (simplified)
    sample_html = """
    <html>
    <body>
        <div class="pricing">
            <div class="tier">
                <h3>Starter</h3>
                <p class="price">$29/month</p>
                <ul>
                    <li>5 users</li>
                    <li>Basic features</li>
                </ul>
            </div>
            <div class="tier">
                <h3>Professional</h3>
                <p class="price">$99/month</p>
                <ul>
                    <li>25 users</li>
                    <li>Advanced features</li>
                </ul>
            </div>
            <div class="tier">
                <h3>Enterprise</h3>
                <p class="price">Contact us</p>
                <ul>
                    <li>Unlimited users</li>
                    <li>All features</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """

    print("Testing AI pricing extraction...")
    result = await service._extract_pricing_with_ai(sample_html, "TestVendor")

    if result:
        print("SUCCESS: Pricing extracted")
        print(f"  Model: {result.get('model')}")
        print(f"  Currency: {result.get('currency')}")
        print(f"  Tiers: {len(result.get('tiers', []))}")
        for tier in result.get('tiers', []):
            print(f"    - {tier.get('name')}: ${tier.get('price')}/{tier.get('per')}")
        print(f"  Custom pricing: {result.get('custom_pricing')}")
        return True
    else:
        print("FAILED: Could not extract pricing")
        return False


async def test_pricing_comparison():
    """Test pricing change detection."""
    service = VendorRefreshService()

    old_pricing = {
        "model": "per_seat",
        "currency": "USD",
        "tiers": [
            {"name": "Basic", "price": 29},
            {"name": "Pro", "price": 99},
        ]
    }

    same_pricing = {
        "model": "per_seat",
        "currency": "USD",
        "tiers": [
            {"name": "Basic", "price": 29},
            {"name": "Pro", "price": 99},
        ]
    }

    different_pricing = {
        "model": "per_seat",
        "currency": "USD",
        "tiers": [
            {"name": "Basic", "price": 39},  # Price changed!
            {"name": "Pro", "price": 99},
        ]
    }

    print("\nTesting pricing comparison...")

    # Test same pricing
    if not service._pricing_changed(old_pricing, same_pricing):
        print("  PASS: Same pricing correctly detected as unchanged")
    else:
        print("  FAIL: Same pricing incorrectly marked as changed")
        return False

    # Test different pricing
    if service._pricing_changed(old_pricing, different_pricing):
        print("  PASS: Changed pricing correctly detected")
    else:
        print("  FAIL: Changed pricing not detected")
        return False

    return True


async def test_empty_pricing():
    """Test handling of empty/null pricing."""
    service = VendorRefreshService()

    print("\nTesting empty pricing handling...")

    new_pricing = {"model": "flat", "tiers": []}

    # Empty old pricing should always be "changed"
    if service._pricing_changed({}, new_pricing):
        print("  PASS: Empty old pricing correctly triggers update")
    else:
        print("  FAIL: Empty old pricing should trigger update")
        return False

    if service._pricing_changed(None, new_pricing):
        print("  PASS: None old pricing correctly triggers update")
    else:
        print("  FAIL: None old pricing should trigger update")
        return False

    return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("VENDOR REFRESH SERVICE TEST")
    print("=" * 60)

    results = []

    # Test 1: AI Extraction (requires API key)
    try:
        results.append(("AI Extraction", await test_pricing_extraction()))
    except Exception as e:
        print(f"AI Extraction test error: {e}")
        results.append(("AI Extraction", False))

    # Test 2: Pricing Comparison
    results.append(("Pricing Comparison", await test_pricing_comparison()))

    # Test 3: Empty Pricing
    results.append(("Empty Pricing", await test_empty_pricing()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
