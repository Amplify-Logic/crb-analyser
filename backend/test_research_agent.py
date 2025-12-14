"""
Test the Pre-Research Agent with Aquablu
"""
import asyncio
import json
import sys
sys.path.insert(0, '/Users/larsmusic/CRB Analyser/crb-analyser/backend')

import logging
logging.basicConfig(level=logging.DEBUG)

from src.agents.pre_research_agent import PreResearchAgent


async def test_research():
    """Test the pre-research agent with Aquablu"""
    print("=" * 60)
    print("TESTING PRE-RESEARCH AGENT")
    print("=" * 60)

    # Test with Aquablu
    company_name = "Aquablu"
    website_url = "https://www.aquablu.com"

    print(f"\nResearching: {company_name}")
    print(f"Website: {website_url}")
    print("-" * 60)

    # Create agent
    agent = PreResearchAgent(
        company_name=company_name,
        website_url=website_url
    )

    # Run research and collect all updates
    profile = None
    questionnaire = None

    async for update in agent.run_research():
        status = update.get('status', 'unknown')
        step = update.get('step', '')
        message = update.get('message', '')
        phase = update.get('phase', '')

        print(f"\n[{status}] {phase} - {step or message}")

        if update.get('error'):
            print(f"  ERROR: {update.get('error')}")

        if status == 'complete':
            profile = update.get('company_profile')
            questionnaire = update.get('questionnaire')
            print(f"  Got profile: {profile is not None}")
            print(f"  Got questionnaire: {questionnaire is not None}")

    if not profile:
        print("\nERROR: No profile generated")
        return

    print("\n" + "=" * 60)
    print("COMPANY PROFILE")
    print("=" * 60)

    # Profile is a CompanyProfile object
    print(f"\nCompany: {profile.company_name}")
    print(f"Website: {profile.website}")

    if profile.basics:
        print(f"\nBasics:")
        print(f"  Industry: {profile.basics.industry if hasattr(profile.basics, 'industry') else 'N/A'}")
        print(f"  Description: {profile.basics.description[:200] if profile.basics.description else 'N/A'}...")

    if profile.size:
        print(f"\nSize:")
        print(f"  Employee Range: {profile.size.employee_range}")
        print(f"  Revenue Range: {profile.size.revenue_range}")

    if profile.products:
        offerings = profile.products.main_offerings if hasattr(profile.products, 'main_offerings') else []
        print(f"\nProducts/Services ({len(offerings or [])}):")
        for p in (offerings or [])[:5]:
            print(f"  - {p}")

    print(f"\nResearch Quality: {profile.research_quality_score}/100")

    if questionnaire:
        print("\n" + "=" * 60)
        print("GENERATED QUESTIONNAIRE")
        print("=" * 60)

        print(f"\nTotal Questions: {questionnaire.total_questions}")
        print(f"Estimated Time: {questionnaire.estimated_time_minutes} minutes")

        for q in questionnaire.questions[:5]:
            print(f"\n  {q.id}: {q.question}")
            print(f"    Type: {q.type}, Purpose: {q.purpose}")
            if q.prefilled_value:
                print(f"    [Pre-filled: {q.prefilled_value}]")

    print("\n" + "=" * 60)
    print("RESEARCH COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_research())
