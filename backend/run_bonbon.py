"""
One-off script: Generate BonBon Boutique report through the full CRB pipeline.
Targets the specific seed by name instead of random pick.
"""
import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from src.cli.generate_report import load_seeds, generate_single_report


async def main():
    seeds_data = load_seeds("ecommerce")

    # Find BonBon Boutique specifically
    bonbon = None
    for seed in seeds_data["seeds"]:
        if seed["name"] == "BonBon Boutique":
            bonbon = seed
            break

    if not bonbon:
        print("ERROR: BonBon Boutique seed not found in ecommerce.json")
        sys.exit(1)

    print(f"Found seed: {bonbon['name']}")
    print(f"  Workshop transcript: {len(bonbon.get('workshop_transcript', []))} messages")
    print(f"  Tools: {bonbon['profile']['current_tools']}")
    print(f"  Pain points: {bonbon['profile']['pain_points']}")

    result = await generate_single_report(
        seed=bonbon,
        seeds_data=seeds_data,
        report_tier="quick",
        scrape=False,       # Skip scraping, seed data is rich enough
        skip_review=False,   # Keep review for quality
    )

    if result:
        print(f"\nReport generated successfully!")
        print(f"  Report ID: {result['report_id']}")
        print(f"  Session ID: {result['session_id']}")
        print(f"  Time: {result['elapsed']:.1f}s")

        # Save result reference
        with open("bonbon_result.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n  Result saved to bonbon_result.json")
    else:
        print("Report generation failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
