# Vendor System Analysis Prompt

Run this prompt to get a comprehensive analysis of your vendor setup and recommendation system.

---

## Instructions

Copy everything below the line and paste it as a new conversation with Claude Code:

---

# Analyze Vendor System

Perform a comprehensive analysis of our vendor database and recommendation system. I need you to:

## 1. Database Health Check

Run these commands and analyze the results:

```bash
# Check vendor statistics
cd backend && python -c "
import asyncio
from src.services.vendor_service import VendorService

async def main():
    vs = VendorService()

    # Get all vendors
    result = await vs.list_vendors(limit=500)
    vendors = result.get('vendors', [])

    print(f'Total vendors: {len(vendors)}')

    # Status breakdown
    statuses = {}
    for v in vendors:
        s = v.get('status', 'unknown')
        statuses[s] = statuses.get(s, 0) + 1
    print(f'By status: {statuses}')

    # Category breakdown
    categories = {}
    for v in vendors:
        c = v.get('category', 'uncategorized')
        categories[c] = categories.get(c, 0) + 1
    print(f'By category: {dict(sorted(categories.items(), key=lambda x: -x[1]))}')

    # API openness scores
    api_scores = {'none': 0, '1': 0, '2': 0, '3': 0, '4': 0, '5': 0}
    for v in vendors:
        score = v.get('api_openness_score')
        if score:
            api_scores[str(score)] = api_scores.get(str(score), 0) + 1
        else:
            api_scores['none'] += 1
    print(f'API openness scores: {api_scores}')

    # Vendors missing key data
    missing_pricing = [v['slug'] for v in vendors if not v.get('pricing')]
    missing_ratings = [v['slug'] for v in vendors if not v.get('our_rating') and not v.get('g2_score')]
    missing_industries = [v['slug'] for v in vendors if not v.get('industries')]
    missing_sizes = [v['slug'] for v in vendors if not v.get('company_sizes')]

    print(f'\\nMissing pricing: {len(missing_pricing)} vendors')
    print(f'Missing ratings: {len(missing_ratings)} vendors')
    print(f'Missing industries: {len(missing_industries)} vendors')
    print(f'Missing company_sizes: {len(missing_sizes)} vendors')

    # Stale vendors
    stale = await vs.get_vendors_needing_refresh(days=90)
    print(f'\\nStale vendors (>90 days): {len(stale)}')

    # Vendors without embeddings
    no_embedding = [v['slug'] for v in vendors if not v.get('embedding')]
    print(f'Missing embeddings: {len(no_embedding)} vendors')

asyncio.run(main())
"
```

## 2. Industry Tier Coverage

Check if each supported industry has proper tier assignments:

```bash
cd backend && python -c "
import asyncio
from src.services.vendor_service import VendorService
from src.knowledge import SUPPORTED_INDUSTRIES

async def main():
    vs = VendorService()

    print('Industry Tier Coverage Analysis')
    print('=' * 50)

    for industry in SUPPORTED_INDUSTRIES:
        tiers = {1: [], 2: [], 3: []}

        for tier in [1, 2, 3]:
            vendors = await vs.get_tier_vendors(industry, tier)
            tiers[tier] = [v['slug'] for v in vendors]

        total = sum(len(v) for v in tiers.values())

        print(f'\\n{industry}:')
        print(f'  T1 (Top Pick): {len(tiers[1])} - {tiers[1][:3]}...' if tiers[1] else f'  T1 (Top Pick): 0 - MISSING!')
        print(f'  T2 (Recommended): {len(tiers[2])}')
        print(f'  T3 (Alternative): {len(tiers[3])}')

        if total < 5:
            print(f'  ⚠️  LOW COVERAGE: Only {total} vendors assigned')

asyncio.run(main())
"
```

## 3. Recommendation Quality Check

Test the vendor matching skill with sample findings:

```bash
cd backend && python -c "
import asyncio
from src.skills.analysis.vendor_matching import VendorMatchingSkill
from src.skills.base import SkillContext

async def main():
    skill = VendorMatchingSkill()

    test_findings = [
        {'id': 'test-1', 'title': 'Manual appointment scheduling', 'description': 'Staff spends 2 hours daily scheduling appointments by phone', 'category': 'scheduling'},
        {'id': 'test-2', 'title': 'No CRM system', 'description': 'Customer data tracked in spreadsheets', 'category': 'crm'},
        {'id': 'test-3', 'title': 'Manual invoice creation', 'description': 'Invoices created manually in Word', 'category': 'finance'},
        {'id': 'test-4', 'title': 'Website has no chat', 'description': 'Visitors cannot get instant answers', 'category': 'customer_support'},
    ]

    print('Vendor Matching Quality Test')
    print('=' * 50)

    for finding in test_findings:
        print(f'\\nFinding: {finding[\"title\"]}')

        context = SkillContext(
            finding=finding,
            industry='dental',
            company_size='smb',
            budget='moderate'
        )

        try:
            result = await skill.execute(context)
            print(f'  Off-the-shelf: {result.off_the_shelf.vendor} (fit: {result.off_the_shelf.fit_score})')
            print(f'  Best-in-class: {result.best_in_class.vendor} (fit: {result.best_in_class.fit_score})')
            print(f'  Confidence: {result.match_confidence}')
        except Exception as e:
            print(f'  ❌ ERROR: {e}')

asyncio.run(main())
"
```

## 4. Analyze and Report

After running the above, create a report answering:

### Data Quality Issues
- Which vendors are missing critical data (pricing, ratings, industries)?
- How many vendors are stale and need refresh?
- Are embeddings complete for semantic search?

### Coverage Gaps
- Which industries have low tier coverage?
- Which categories are under-represented?
- Are there common use cases without good vendor options?

### Recommendation Quality
- Did the matching skill return sensible vendors?
- Are fit scores reasonable (70+ for good matches)?
- Are there categories where matching fails?

### Improvement Recommendations
Based on your analysis, prioritize:

1. **Critical** (blocks recommendations)
   - Missing tier assignments for primary industries
   - Vendors without pricing data

2. **High** (degrades quality)
   - Stale vendors (>90 days)
   - Missing API openness scores
   - Low confidence matches

3. **Medium** (nice to have)
   - Missing embeddings
   - Incomplete ratings
   - Secondary industry coverage

### Action Items
Generate specific action items like:
- "Add tier assignments for [industry]: need at least 3 T1 vendors"
- "Refresh pricing for: [vendor-list]"
- "Add API openness scores for: [vendor-list]"
- "Research new vendors for [category] to improve coverage"

---

## Expected Output

Provide:
1. Summary table of database health metrics
2. List of industries with coverage issues
3. Vendor matching test results
4. Prioritized improvement recommendations
5. Specific action items with vendor names

---

## Optional: Run Vendor Refresh

If stale vendors are found:

```bash
# Dry run first
cd backend && python -m src.agents.research.cli refresh --stale --dry-run

# Then apply updates
cd backend && python -m src.agents.research.cli refresh --stale
```

## Optional: Discover New Vendors

If categories need more coverage:

```bash
cd backend && python -m src.agents.research.cli discover --category [category] --industry [industry]
```
