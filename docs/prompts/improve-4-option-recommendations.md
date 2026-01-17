# Improve Quiz/Workshop for 4-Option Recommendations

## Context

**Current State:** Reports show 3 options (Off-the-shelf, Best-in-class, Custom build) without considering user's implementation capability.

**Desired State:** Reports show 4 actionable options based on user's ability to execute:

| Option | Icon | Example | Best When |
|--------|------|---------|-----------|
| **BUY** | 🛒 | Calendly €12/mo | User wants turnkey, no technical skills needed |
| **CONNECT** | 🔗 | Make + your CRM, 4hrs | User has existing tools, some automation comfort |
| **BUILD** | 🏗️ | Claude + Supabase, €5K | User has dev skills OR willing to learn AI coding tools |
| **HIRE** | 👥 | Agency €3K-8K, 2 weeks | User wants custom but lacks time/skills |

---

## Problem

The quiz and workshop don't capture implementation capability, so we can't personalize recommendations. We recommend "build custom" to people who can't code, and "buy SaaS" to people who could build something better.

---

## What We Need to Capture

### 1. Technical Capability (Required)

**Question:** "How would you describe your technical comfort level?"

| Answer | Score | Meaning |
|--------|-------|---------|
| "I avoid anything technical" | 0 | BUY or HIRE only |
| "I can follow tutorials and use no-code tools" | 1 | BUY, CONNECT, or HIRE |
| "I'm comfortable with automation tools like Zapier/Make" | 2 | CONNECT preferred |
| "I can code or am learning AI coding tools (Cursor, Claude Code)" | 3 | BUILD is viable |
| "I have developers on staff or easy access" | 4 | BUILD preferred |

### 2. Existing Stack (Required - already captured)

We already ask about existing software in the quiz. Use this to determine CONNECT viability:
- If they use tools with good APIs (api_openness_score >= 4), CONNECT is viable
- If they use closed systems, CONNECT is harder

### 3. Implementation Preference (Required)

**Question:** "When solving business problems with software, you prefer to..."

| Answer | Implication |
|--------|-------------|
| "Find a ready-made solution that just works" | BUY preference |
| "Customize and connect my existing tools" | CONNECT preference |
| "Build exactly what I need, even if it takes longer" | BUILD preference |
| "Hire someone to handle it for me" | HIRE preference |

### 4. Budget Context (Required)

**Question:** "For a tool that saves you 10+ hours/month, what's your comfort zone?"

| Answer | Budget Tier |
|--------|-------------|
| "Under €50/month" | Low - prioritize BUY (free/cheap tiers) |
| "€50-200/month" | Moderate - BUY or CONNECT viable |
| "€200-500/month" | Comfortable - all options open |
| "€500+/month or one-time €2K-10K" | High - BUILD or HIRE viable |

### 5. Time Urgency (Optional)

**Question:** "How soon do you need this working?"

| Answer | Implication |
|--------|-------------|
| "This week" | BUY only (no time for anything else) |
| "This month" | BUY or CONNECT |
| "This quarter" | All options open |
| "No rush, want it done right" | BUILD or HIRE preferred |

---

## Implementation: Quiz Changes

### Add to Quiz Flow (after industry selection)

```typescript
// New quiz step: Implementation Capability
{
  id: "implementation_capability",
  question: "How would you describe your technical comfort level?",
  type: "single_choice",
  options: [
    { value: "non_technical", label: "I avoid anything technical - just give me something that works" },
    { value: "tutorial_follower", label: "I can follow tutorials and use no-code tools like Notion or Airtable" },
    { value: "automation_user", label: "I'm comfortable with automation tools like Zapier or Make" },
    { value: "ai_coder", label: "I can code or am learning AI coding tools like Cursor" },
    { value: "has_developers", label: "I have developers on staff or easy access to technical help" }
  ],
  required: true
}

// New quiz step: Implementation Preference
{
  id: "implementation_preference",
  question: "When solving business problems with software, you prefer to...",
  type: "single_choice",
  options: [
    { value: "buy", label: "Find a ready-made solution that just works", icon: "🛒" },
    { value: "connect", label: "Customize and connect my existing tools", icon: "🔗" },
    { value: "build", label: "Build exactly what I need, even if it takes longer", icon: "🏗️" },
    { value: "hire", label: "Hire someone to handle it for me", icon: "👥" }
  ],
  required: true
}

// New quiz step: Budget Comfort
{
  id: "budget_comfort",
  question: "For a tool that saves you 10+ hours/month, what's your comfort zone?",
  type: "single_choice",
  options: [
    { value: "low", label: "Under €50/month" },
    { value: "moderate", label: "€50-200/month" },
    { value: "comfortable", label: "€200-500/month" },
    { value: "high", label: "€500+/month or one-time €2K-10K investment" }
  ],
  required: true
}
```

### Store in quiz_sessions table

Add columns or store in existing JSONB:
- `implementation_capability`: enum
- `implementation_preference`: enum
- `budget_comfort`: enum

---

## Implementation: Recommendation Logic

### Option Eligibility Matrix (Basic)

```python
def get_eligible_options(
    capability: str,
    preference: str,
    budget: str,
    existing_stack_api_ready: bool
) -> List[str]:
    """
    Returns list of eligible options: ['buy', 'connect', 'build', 'hire']
    """
    eligible = []

    # BUY is always eligible
    eligible.append('buy')

    # CONNECT requires:
    # - At least tutorial_follower capability
    # - Existing stack with API-ready tools
    if capability in ['tutorial_follower', 'automation_user', 'ai_coder', 'has_developers']:
        if existing_stack_api_ready:
            eligible.append('connect')

    # BUILD requires:
    # - ai_coder or has_developers capability
    # - moderate+ budget (unless they strongly prefer it)
    if capability in ['ai_coder', 'has_developers']:
        if budget in ['moderate', 'comfortable', 'high'] or preference == 'build':
            eligible.append('build')

    # HIRE requires:
    # - comfortable+ budget
    # - OR user explicitly prefers it
    if budget in ['comfortable', 'high'] or preference == 'hire':
        eligible.append('hire')

    return eligible
```

### Weighted Scoring System (Advanced)

Instead of binary eligibility, calculate a **match score (0-100%)** for each option:

```python
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class OptionScore:
    option: str                    # 'buy', 'connect', 'build', 'hire'
    score: float                   # 0-100
    breakdown: Dict[str, float]    # Individual factor scores
    match_reasons: List[str]       # Why this scores well
    concern_reasons: List[str]     # Why this loses points
    is_recommended: bool           # Highest score = recommended


SCORING_WEIGHTS = {
    'capability_match': 0.30,   # Can they actually execute this?
    'preference_match': 0.20,   # Does this align with what they want?
    'budget_fit': 0.20,         # Is this affordable for them?
    'time_fit': 0.15,           # Does it fit their urgency?
    'value_ratio': 0.15,        # ROI for this specific finding
}


def score_option(
    option: str,
    user_profile: 'UserProfile',
    finding: 'Finding',
    option_details: 'OptionDetails'
) -> OptionScore:
    """
    Calculate weighted match score for an option.
    Returns score 0-100 with breakdown and reasoning.
    """
    breakdown = {}
    match_reasons = []
    concern_reasons = []

    # 1. Capability Match (30%)
    capability_score = calculate_capability_match(option, user_profile.capability)
    breakdown['capability_match'] = capability_score
    if capability_score >= 80:
        match_reasons.append(CAPABILITY_MATCH_REASONS[option][user_profile.capability])
    elif capability_score < 50:
        concern_reasons.append(CAPABILITY_CONCERN_REASONS[option][user_profile.capability])

    # 2. Preference Match (20%)
    preference_score = 100 if user_profile.preference == option else 60
    breakdown['preference_match'] = preference_score
    if user_profile.preference == option:
        match_reasons.append(f"Matches your '{option}' preference")

    # 3. Budget Fit (20%)
    budget_score = calculate_budget_fit(option_details.cost, user_profile.budget)
    breakdown['budget_fit'] = budget_score
    if budget_score >= 80:
        match_reasons.append(f"Within your {user_profile.budget} budget")
    elif budget_score < 50:
        concern_reasons.append(f"May stretch your {user_profile.budget} budget")

    # 4. Time Fit (15%)
    time_score = calculate_time_fit(option_details.time_to_value, user_profile.urgency)
    breakdown['time_fit'] = time_score
    if time_score >= 80:
        match_reasons.append(f"Fits your {user_profile.urgency} timeline")
    elif time_score < 50:
        concern_reasons.append(f"May not meet your {user_profile.urgency} deadline")

    # 5. Value Ratio (15%)
    value_score = calculate_value_ratio(finding, option_details)
    breakdown['value_ratio'] = value_score
    if value_score >= 80:
        match_reasons.append("Excellent ROI for this specific problem")

    # Calculate weighted total
    total_score = sum(
        breakdown[factor] * weight
        for factor, weight in SCORING_WEIGHTS.items()
    )

    return OptionScore(
        option=option,
        score=round(total_score, 0),
        breakdown=breakdown,
        match_reasons=match_reasons[:3],  # Top 3 reasons
        concern_reasons=concern_reasons[:2],  # Top 2 concerns
        is_recommended=False  # Set later after comparing all options
    )


def calculate_capability_match(option: str, capability: str) -> float:
    """
    Score how well user's capability matches option requirements.
    """
    CAPABILITY_MATRIX = {
        'buy': {
            'non_technical': 100,
            'tutorial_follower': 100,
            'automation_user': 90,
            'ai_coder': 80,
            'has_developers': 70,  # Slightly low - they could do better
        },
        'connect': {
            'non_technical': 20,   # Can't do it
            'tutorial_follower': 60,
            'automation_user': 100,
            'ai_coder': 90,
            'has_developers': 85,
        },
        'build': {
            'non_technical': 10,
            'tutorial_follower': 30,
            'automation_user': 50,
            'ai_coder': 100,
            'has_developers': 100,
        },
        'hire': {
            'non_technical': 90,
            'tutorial_follower': 85,
            'automation_user': 80,
            'ai_coder': 70,        # They could do it themselves
            'has_developers': 50,  # Why hire when you have devs?
        },
    }
    return CAPABILITY_MATRIX[option].get(capability, 50)


def calculate_budget_fit(option_cost: 'CostEstimate', budget_tier: str) -> float:
    """
    Score how well option cost fits user's budget.
    """
    BUDGET_LIMITS = {
        'low': 600,         # €50/mo annual
        'moderate': 2400,   # €200/mo annual
        'comfortable': 6000,
        'high': 50000,
    }

    limit = BUDGET_LIMITS.get(budget_tier, 2400)
    annual_cost = option_cost.year_one_total

    if annual_cost <= limit * 0.5:
        return 100  # Well within budget
    elif annual_cost <= limit:
        return 80   # Fits budget
    elif annual_cost <= limit * 1.5:
        return 50   # Stretch
    else:
        return 20   # Out of budget


def calculate_time_fit(time_to_value: str, urgency: str) -> float:
    """
    Score how well option timeline fits user's urgency.
    """
    # Convert to days
    TIME_MAP = {
        '1 day': 1, '1 week': 7, '2 weeks': 14,
        '1 month': 30, '2-4 weeks': 21, '4-8 weeks': 42,
    }
    URGENCY_LIMITS = {
        'this_week': 7,
        'this_month': 30,
        'this_quarter': 90,
        'no_rush': 365,
    }

    days_needed = TIME_MAP.get(time_to_value, 14)
    days_available = URGENCY_LIMITS.get(urgency, 90)

    if days_needed <= days_available * 0.5:
        return 100
    elif days_needed <= days_available:
        return 80
    elif days_needed <= days_available * 1.5:
        return 50
    else:
        return 20


CAPABILITY_MATCH_REASONS = {
    'buy': {
        'non_technical': "No technical skills needed",
        'tutorial_follower': "Simple setup you can handle",
        'automation_user': "Quick win while you focus on bigger automations",
        'ai_coder': "Fast solution - save your coding time for custom needs",
        'has_developers': "Don't waste dev time on solved problems",
    },
    'connect': {
        'automation_user': "Perfect match for your automation skills",
        'ai_coder': "Quick integration using tools you know",
        'has_developers': "Your team can set this up quickly",
    },
    'build': {
        'ai_coder': "Your AI coding skills make this very achievable",
        'has_developers': "Your dev team can build exactly what you need",
    },
    'hire': {
        'non_technical': "Expert handles everything for you",
        'tutorial_follower': "Professional setup, you maintain",
    },
}

CAPABILITY_CONCERN_REASONS = {
    'connect': {
        'non_technical': "Requires automation tool comfort you don't have yet",
        'tutorial_follower': "May be challenging without automation experience",
    },
    'build': {
        'non_technical': "Requires technical skills",
        'tutorial_follower': "Would need significant learning curve",
        'automation_user': "Custom code is a step beyond automation tools",
    },
    'hire': {
        'ai_coder': "You could likely build this yourself for less",
        'has_developers': "Your team could handle this in-house",
    },
}
```

### Ranking and Recommendation

```python
def rank_options(eligible: List[str], preference: str) -> List[str]:
    """
    Rank eligible options by user preference.
    Returns ordered list with preferred option first.
    """
    if preference in eligible:
        # Move preference to front
        eligible.remove(preference)
        eligible.insert(0, preference)
    return eligible


def get_recommendations(
    user_profile: 'UserProfile',
    finding: 'Finding',
    all_option_details: Dict[str, 'OptionDetails']
) -> 'Recommendation':
    """
    Score all options and return ranked recommendations.
    """
    scores = []
    for option, details in all_option_details.items():
        score = score_option(option, user_profile, finding, details)
        scores.append(score)

    # Sort by score descending
    scores.sort(key=lambda x: x.score, reverse=True)

    # Mark highest as recommended
    scores[0].is_recommended = True

    return Recommendation(
        finding=finding,
        primary=scores[0],
        alternatives=[s for s in scores[1:] if s.score >= 50],
        not_recommended=[s for s in scores if s.score < 50],
    )
```

### Report Generation Changes

For each finding/recommendation, generate all 4 options but only show eligible ones:

```python
class FourOptionRecommendation:
    finding: str

    buy: Optional[BuyOption]      # SaaS product recommendation
    connect: Optional[ConnectOption]  # How to connect existing tools
    build: Optional[BuildOption]   # How to build custom
    hire: Optional[HireOption]     # Agency/freelancer estimate

    recommended: str  # Which option we recommend based on user profile
    reasoning: str    # Why this option fits them


@dataclass
class BuyOption:
    vendor_slug: str
    vendor_name: str
    price: str           # "€12/mo"
    setup_time: str      # "30 minutes"
    pros: List[str]
    cons: List[str]


@dataclass
class ConnectOption:
    integration_platform: str  # "Make", "n8n", "Zapier"
    connects_to: List[str]     # ["HubSpot", "Gmail", "Slack"]
    estimated_hours: int       # 4
    complexity: str            # "low", "medium", "high"
    template_url: Optional[str]  # Link to Make/n8n template if exists


@dataclass
class BuildOption:
    recommended_stack: List[str]  # ["Claude Code", "Supabase", "Vercel"]
    estimated_cost: str           # "€3K-5K"
    estimated_hours: str          # "20-40 hours"
    skills_needed: List[str]      # ["Python", "API integration"]
    ai_coding_viable: bool        # Can this be built with AI coding tools by non-dev?


@dataclass
class HireOption:
    service_type: str        # "Agency", "Freelancer", "Consultant"
    estimated_cost: str      # "€3K-8K"
    estimated_timeline: str  # "2-3 weeks"
    where_to_find: List[str] # ["Upwork", "Toptal", "local agencies"]
```

---

## Workshop Changes

### Add Implementation Capability Discovery

In workshop milestone questions, add probes for:

1. **Early (Discovery phase):**
   - "Do you have any technical team members or developers?"
   - "Have you used automation tools like Zapier or Make before?"
   - "Are you interested in AI coding tools that let non-developers build software?"

2. **Mid (Pain points phase):**
   - "For [pain point], would you prefer a ready solution or something custom?"
   - "What's your budget comfort for solving [pain point]?"

3. **Late (Solution exploration):**
   - "Would you be open to learning tools like Cursor or Claude Code to build this yourself?"
   - "Should we include agency/freelancer options in your recommendations?"

### Workshop Confidence Tracking

Track confidence on implementation capability:
- If user mentions "my developer", "our tech team" → high BUILD confidence
- If user mentions "I used Zapier", "we have Make" → high CONNECT confidence
- If user says "just want it to work", "no time to learn" → high BUY/HIRE confidence

---

## Data Requirements

### New Vendor Fields (already added)

Vendors already have:
- `api_openness_score` (1-5)
- `zapier_integration`, `make_integration`, `n8n_integration`
- `requires_developer` (bool)
- `implementation_complexity` (low/medium/high)

### New Knowledge Base Data Needed

1. **Agency/Freelancer Cost Data:**
   Create `backend/src/knowledge/implementation/agency_costs.json`:
   ```json
   {
     "automation_setup": {
       "freelancer": { "min": 500, "max": 2000, "timeline": "1-2 weeks" },
       "agency": { "min": 2000, "max": 8000, "timeline": "2-4 weeks" }
     },
     "custom_integration": {
       "freelancer": { "min": 1000, "max": 5000, "timeline": "2-4 weeks" },
       "agency": { "min": 5000, "max": 20000, "timeline": "4-8 weeks" }
     },
     "full_custom_app": {
       "freelancer": { "min": 5000, "max": 15000, "timeline": "4-8 weeks" },
       "agency": { "min": 15000, "max": 50000, "timeline": "8-16 weeks" }
     }
   }
   ```

2. **Connect Templates:**
   Create `backend/src/knowledge/implementation/connect_templates.json`:
   ```json
   {
     "crm_email_sync": {
       "platforms": ["Make", "n8n", "Zapier"],
       "estimated_hours": 2,
       "connects": ["HubSpot", "Salesforce", "Gmail", "Outlook"],
       "template_urls": {
         "make": "https://make.com/templates/...",
         "n8n": "https://n8n.io/workflows/..."
       }
     }
   }
   ```

3. **Build Stacks:**
   Create `backend/src/knowledge/implementation/build_stacks.json`:
   ```json
   {
     "simple_automation": {
       "stack": ["Claude Code", "Python", "Supabase"],
       "cost_range": { "min": 0, "max": 500 },
       "hours_range": { "min": 4, "max": 20 },
       "ai_coding_viable": true
     },
     "custom_app": {
       "stack": ["Cursor", "Next.js", "Supabase", "Vercel"],
       "cost_range": { "min": 500, "max": 5000 },
       "hours_range": { "min": 20, "max": 80 },
       "ai_coding_viable": true
     }
   }
   ```

---

## Migration Path

### Phase 1: Quiz Changes (This Sprint)
1. Add new quiz questions (capability, preference, budget)
2. Store responses in quiz_sessions
3. Pass to report generation

### Phase 2: Report Generation (Next Sprint)
1. Update `three_options.py` skill → `four_options.py`
2. Generate 4 options per finding
3. Filter to eligible options based on user profile
4. Highlight recommended option

### Phase 3: Knowledge Base (Parallel)
1. Add agency cost data
2. Add connect templates
3. Add build stack recommendations

### Phase 4: Workshop Integration (Later)
1. Add capability discovery questions
2. Track implementation confidence
3. Adjust recommendations based on workshop insights

---

## Files to Modify

### Backend
- `backend/src/routes/quiz.py` - Add new questions
- `backend/src/services/quiz_engine.py` - Process new responses
- `backend/src/skills/report-generation/three_options.py` → `four_options.py`
- `backend/src/skills/analysis/vendor_matching.py` - Add eligibility logic

### Frontend
- `frontend/src/pages/Quiz.tsx` - Render new questions
- `frontend/src/components/report/ThreeOptions.tsx` → `FourOptions.tsx`

### Database
- Migration to add columns to quiz_sessions (or use existing JSONB)

### Knowledge Base
- `backend/src/knowledge/implementation/` - New directory with cost/template data

---

## Success Metrics

1. **Recommendation Relevance:** Users click on recommended option 60%+ of time
2. **Report Usefulness:** Post-purchase satisfaction scores improve
3. **Conversion:** Quiz-to-purchase rate increases (better matching = more value perception)

---

## Path Visualization: Tradeoff Comparison

For each finding, show a clear comparison table that makes tradeoffs obvious:

### Comparison Table Format

```
FINDING: Automate appointment reminders

                    🛒 BUY       🔗 CONNECT    🏗️ BUILD      👥 HIRE
────────────────────────────────────────────────────────────────────────
Time to Value       ⚡ 1 day      🕐 1 week     🕐 2-4 weeks   🕐 2-3 weeks
Upfront Cost        €0           €0-200        €2K-5K         €3K-8K
Year 1 Total        €144         €200          €2.5K-5.5K     €3K-8K
Year 3 Total        €432         €200          €3K-7K         €3K-8K
────────────────────────────────────────────────────────────────────────
Flexibility         ⭐⭐          ⭐⭐⭐         ⭐⭐⭐⭐⭐        ⭐⭐⭐⭐
Customization       Limited      Moderate      Full           Full
Maintenance         Vendor       You           You            Optional
Risk Level          Low          Medium        Medium         Low
Your Effort         None         4-8 hrs       20-40 hrs      2-3 hrs
────────────────────────────────────────────────────────────────────────
YOUR MATCH          72%          91% ⬅️        45%            68%
```

### Implementation

```python
@dataclass
class TradeoffTable:
    finding: str
    rows: List[TradeoffRow]
    winner: str  # option with highest match score

@dataclass
class TradeoffRow:
    metric: str                    # "Time to Value"
    buy: TradeoffCell
    connect: TradeoffCell
    build: TradeoffCell
    hire: TradeoffCell

@dataclass
class TradeoffCell:
    value: str                     # "€144" or "⚡ 1 day"
    is_best: bool                  # Highlight if best in row
    tooltip: Optional[str]         # Additional context on hover

TRADEOFF_METRICS = [
    {
        "metric": "Time to Value",
        "description": "How quickly you'll see results",
        "best_is": "lowest",
    },
    {
        "metric": "Upfront Cost",
        "description": "Initial investment required",
        "best_is": "lowest",
    },
    {
        "metric": "Year 1 Total",
        "description": "Total cost in first year",
        "best_is": "lowest",
    },
    {
        "metric": "Flexibility",
        "description": "Ability to customize and extend",
        "best_is": "highest",
    },
    {
        "metric": "Your Effort",
        "description": "Time you'll spend on implementation",
        "best_is": "lowest",
    },
    {
        "metric": "YOUR MATCH",
        "description": "How well this fits your profile",
        "best_is": "highest",
    },
]
```

---

## Growth Path: Option Evolution

Show users how their choice today can evolve over time. This reduces decision anxiety.

### Data Model

```python
@dataclass
class GrowthPath:
    start_with: str                    # 'buy', 'connect', 'build', 'hire'
    can_migrate_to: List[str]          # Options this naturally leads to
    migration_trigger: str             # When to consider switching
    migration_effort: str              # How hard is the switch
    data_portability: str              # "Easy", "Moderate", "Difficult"
    preserve_investment: bool          # Does prior work transfer?

GROWTH_PATHS = {
    'buy': GrowthPath(
        start_with='buy',
        can_migrate_to=['connect', 'build'],
        migration_trigger="When you hit feature limits or volume caps",
        migration_effort="Low - most SaaS tools export data cleanly",
        data_portability="Easy",
        preserve_investment=True,  # Your data transfers
    ),
    'connect': GrowthPath(
        start_with='connect',
        can_migrate_to=['build'],
        migration_trigger="When integration complexity outgrows Make/Zapier",
        migration_effort="Medium - automation logic is documented",
        data_portability="Moderate",
        preserve_investment=True,  # Logic patterns transfer
    ),
    'build': GrowthPath(
        start_with='build',
        can_migrate_to=[],  # Already at max flexibility
        migration_trigger="N/A - you own everything",
        migration_effort="N/A",
        data_portability="Full control",
        preserve_investment=True,
    ),
    'hire': GrowthPath(
        start_with='hire',
        can_migrate_to=['build'],  # You could take over maintenance
        migration_trigger="When you want to reduce ongoing costs",
        migration_effort="Low if well documented, High if not",
        data_portability="Depends on contract",
        preserve_investment=True,  # You own the deliverable
    ),
}
```

### Output Format

```markdown
### Your Path Forward

**Start with:** 🛒 Calendly (recommended)

**Growth Path:**
```
NOW                    6 MONTHS               12+ MONTHS
────────────────────────────────────────────────────────
🛒 Calendly     →     🔗 Make + CRM      →    🏗️ Custom
€12/mo                if you outgrow it       if you need full control
30 min setup          Your data exports       Your automation logic transfers
```

**When to upgrade:**
- Volume exceeds 500 appointments/month
- You need custom reminder logic per appointment type
- Integration with your specific dental workflow required

**Migration effort:** Low - Calendly exports all appointment data as CSV
```

---

## Total Cost of Ownership (TCO)

Show 1-year and 3-year costs to reveal the true cost picture:

### Data Model

```python
@dataclass
class CostEstimate:
    upfront: float                     # One-time costs
    monthly: float                     # Recurring monthly
    annual: float                      # Annual fees if different from monthly*12
    year_one_total: float              # Calculated
    year_three_total: float            # Calculated
    hidden_costs: List[HiddenCost]     # Often overlooked costs
    cost_trajectory: str               # "stable", "increasing", "decreasing"

@dataclass
class HiddenCost:
    name: str                          # "Learning curve"
    estimate: str                      # "4-8 hours"
    monetized: float                   # €200-400 if hourly rate €50
    applies_to: List[str]              # Which options this applies to

HIDDEN_COSTS = [
    HiddenCost(
        name="Learning curve",
        estimate="2-8 hours depending on complexity",
        monetized=100-400,  # At €50/hr
        applies_to=['connect', 'build'],
    ),
    HiddenCost(
        name="Maintenance time",
        estimate="1-2 hours/month",
        monetized=50-100,  # Monthly
        applies_to=['connect', 'build'],
    ),
    HiddenCost(
        name="Vendor lock-in risk",
        estimate="Migration cost if vendor changes",
        monetized=500-2000,  # Potential future cost
        applies_to=['buy'],
    ),
    HiddenCost(
        name="Integration debugging",
        estimate="2-4 hours when things break",
        monetized=100-200,
        applies_to=['connect'],
    ),
]
```

### TCO Comparison Output

```markdown
### 3-Year Total Cost of Ownership

**Finding:** Automate appointment reminders

| Cost Category      | 🛒 BUY      | 🔗 CONNECT  | 🏗️ BUILD    | 👥 HIRE     |
|--------------------|-------------|-------------|-------------|-------------|
| Upfront            | €0          | €200*       | €3,000      | €5,000      |
| Monthly ongoing    | €12         | €0          | €25         | €0          |
| **Year 1 Total**   | **€144**    | **€200**    | **€3,300**  | **€5,000**  |
| **Year 3 Total**   | **€432**    | **€200**    | **€3,900**  | **€5,000**  |

*Includes your time at €50/hr for 4 hours setup

**Cost Trajectory:**
- 🛒 BUY: Stable (€144/year forever, may increase with pricing changes)
- 🔗 CONNECT: Decreasing (one-time cost, minimal maintenance)
- 🏗️ BUILD: Decreasing (hosting costs only after build)
- 👥 HIRE: One-time (unless ongoing support contracted)

**Break-even Analysis:**
- CONNECT beats BUY after: Month 14
- BUILD beats BUY after: Year 8 (not worth it for this finding)
- BUILD beats CONNECT after: Never (CONNECT is better for this use case)

**Recommendation:** For appointment reminders specifically, **CONNECT** has the best
3-year TCO for your profile, with **BUY** as the simpler alternative.
```

---

## Actionable Next Steps

Each option must end with concrete, clickable actions:

### Data Model

```python
@dataclass
class NextSteps:
    option: str
    immediate_action: str              # First thing to do
    action_url: Optional[str]          # Direct link if available
    steps: List[ActionStep]            # Numbered steps
    time_to_first_win: str             # "15 minutes to first reminder"
    success_criteria: str              # How they'll know it worked

@dataclass
class ActionStep:
    order: int
    action: str
    time_estimate: str
    help_link: Optional[str]           # Tutorial or guide

# Example for BUY option
NextSteps(
    option='buy',
    immediate_action="Start Calendly free trial",
    action_url="https://calendly.com/signup",
    steps=[
        ActionStep(1, "Create Calendly account (free trial)", "2 min", None),
        ActionStep(2, "Connect your Google/Outlook calendar", "2 min", "https://help.calendly.com/..."),
        ActionStep(3, "Create your first event type", "5 min", None),
        ActionStep(4, "Enable reminder emails in settings", "1 min", None),
        ActionStep(5, "Share booking link with first client", "1 min", None),
    ],
    time_to_first_win="15 minutes to first automated reminder scheduled",
    success_criteria="Client receives reminder email 24hr before appointment",
)
```

### Output Format

```markdown
### Next Steps: 🛒 BUY Calendly

**Start now:** [Create free Calendly account →](https://calendly.com/signup)

1. **Create account** (2 min)
   - Use your business email for professional booking links

2. **Connect your calendar** (2 min)
   - Links: [Google Calendar](https://help.calendly.com/google) | [Outlook](https://help.calendly.com/outlook)

3. **Create event type** (5 min)
   - "30-minute consultation" or "Initial appointment"

4. **Enable reminders** (1 min)
   - Settings → Notifications → Enable 24hr and 1hr reminders

5. **Share and test** (1 min)
   - Book a test appointment to verify reminders work

**⏱️ Time to first win:** 15 minutes
**✅ Success:** Client receives automatic reminder 24hr before appointment
```

---

## Industry-Specific Defaults

Different industries have different default preferences based on compliance, culture, and typical technical capability:

```python
INDUSTRY_DEFAULTS = {
    "dental": {
        "default_preference": "buy",
        "capability_assumption": "non_technical",
        "budget_assumption": "moderate",
        "preferred_options": ["buy", "hire"],
        "avoid_unless_explicit": ["build"],
        "reasoning": "Dental practices prioritize compliance and simplicity. Most don't have IT staff.",
        "compliance_note": "Ensure any tool is HIPAA/GDPR compliant for patient data.",
        "typical_stack": ["Dentrix", "Eaglesoft", "Open Dental"],
    },
    "legal": {
        "default_preference": "buy",
        "capability_assumption": "tutorial_follower",
        "budget_assumption": "comfortable",
        "preferred_options": ["buy", "hire"],
        "avoid_unless_explicit": ["build"],
        "reasoning": "Law firms bill by the hour - time spent on tech is lost revenue.",
        "compliance_note": "Client confidentiality is paramount. Verify data handling.",
        "typical_stack": ["Clio", "MyCase", "PracticePanther"],
    },
    "tech_startup": {
        "default_preference": "build",
        "capability_assumption": "has_developers",
        "budget_assumption": "low",  # Bootstrapped often
        "preferred_options": ["build", "connect"],
        "avoid_unless_explicit": ["hire"],  # They can do it themselves
        "reasoning": "Tech startups have dev resources and prefer owning their stack.",
        "compliance_note": None,
        "typical_stack": ["Custom", "Open source"],
    },
    "ecommerce": {
        "default_preference": "connect",
        "capability_assumption": "automation_user",
        "budget_assumption": "moderate",
        "preferred_options": ["connect", "buy"],
        "avoid_unless_explicit": [],
        "reasoning": "E-commerce operators are typically comfortable with integrations.",
        "compliance_note": "PCI compliance for payment data.",
        "typical_stack": ["Shopify", "WooCommerce", "Klaviyo", "Gorgias"],
    },
    "healthcare": {
        "default_preference": "hire",
        "capability_assumption": "non_technical",
        "budget_assumption": "comfortable",
        "preferred_options": ["buy", "hire"],
        "avoid_unless_explicit": ["build", "connect"],
        "reasoning": "HIPAA compliance makes DIY risky. Professional implementation preferred.",
        "compliance_note": "HIPAA compliance is mandatory. Verify BAA with any vendor.",
        "typical_stack": ["Epic", "Cerner", "athenahealth"],
    },
    "consulting": {
        "default_preference": "connect",
        "capability_assumption": "automation_user",
        "budget_assumption": "moderate",
        "preferred_options": ["connect", "buy"],
        "avoid_unless_explicit": [],
        "reasoning": "Consultants value flexibility and often have tech-adjacent skills.",
        "compliance_note": "Client data confidentiality varies by engagement.",
        "typical_stack": ["HubSpot", "Notion", "Calendly", "Loom"],
    },
    "real_estate": {
        "default_preference": "buy",
        "capability_assumption": "tutorial_follower",
        "budget_assumption": "comfortable",
        "preferred_options": ["buy", "hire"],
        "avoid_unless_explicit": ["build"],
        "reasoning": "Real estate agents prefer turnkey solutions that work on mobile.",
        "compliance_note": "Fair housing compliance for automated communications.",
        "typical_stack": ["Follow Up Boss", "kvCORE", "BoomTown"],
    },
}

def adjust_for_industry(
    user_profile: 'UserProfile',
    industry: str
) -> 'UserProfile':
    """
    Apply industry defaults to fill gaps in user profile.
    User's explicit answers always override industry defaults.
    """
    defaults = INDUSTRY_DEFAULTS.get(industry, {})

    if not user_profile.capability:
        user_profile.capability = defaults.get('capability_assumption', 'tutorial_follower')

    if not user_profile.preference:
        user_profile.preference = defaults.get('default_preference', 'buy')

    if not user_profile.budget:
        user_profile.budget = defaults.get('budget_assumption', 'moderate')

    user_profile.compliance_notes = defaults.get('compliance_note')
    user_profile.industry_context = defaults.get('reasoning')

    return user_profile
```

---

## Recommendation Presentation Guidelines

How to display recommendations in the report:

### Visual Hierarchy

```markdown
## 🎯 Your Recommended Path

### Primary Recommendation

┌─────────────────────────────────────────────────────────────────┐
│  🔗 CONNECT: Make + HubSpot                        91% MATCH    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Why this fits you:                                             │
│  ✓ Perfect match for your automation skills                     │
│  ✓ Uses your existing HubSpot data                              │
│  ✓ Within your €50-200/month budget                             │
│                                                                 │
│  Investment: €200 one-time (4 hours setup)                      │
│  Time to value: 1 week                                          │
│                                                                 │
│  [Get Started →]                                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

### Alternatives to Consider

┌──────────────────────────────┐  ┌──────────────────────────────┐
│  🛒 BUY: Calendly   72%      │  │  👥 HIRE: Agency    68%      │
├──────────────────────────────┤  ├──────────────────────────────┤
│  Simpler but less flexible   │  │  Hands-off but higher cost   │
│  €144/year                   │  │  €3-5K one-time              │
│  Best if: You want zero      │  │  Best if: You'd rather pay   │
│  setup effort                │  │  than learn                  │
└──────────────────────────────┘  └──────────────────────────────┘

### Not Recommended for You

┌──────────────────────────────────────────────────────────────────┐
│  🏗️ BUILD: Custom Solution                            45%        │
│  ─────────────────────────────────────────────────────────────── │
│  ⚠️ Requires coding skills you indicated you don't have          │
│  ⚠️ Overkill for appointment reminders specifically              │
│                                                                  │
│  This option would make sense if:                                │
│  • You learn AI coding tools like Cursor or Claude Code          │
│  • You need features no existing tool provides                   │
│  • You want to integrate with custom internal systems            │
└──────────────────────────────────────────────────────────────────┘
```

### Content Rules

1. **Primary recommendation gets 3x the space** of alternatives
2. **Always show match percentage** - makes recommendation objective
3. **List exactly 3 "why this fits" reasons** - not 2, not 5
4. **Include one clear CTA** - "Get Started" or "Learn More"
5. **Alternatives show "Best if" scenarios** - helps user self-select
6. **Not Recommended explains why** - prevents "why didn't you suggest X"
7. **Not Recommended shows path to eligibility** - "would make sense if..."

---

## Edge Cases and Fallback Logic

### When All Options Score Below 50%

```python
def handle_low_scores(scores: List[OptionScore], finding: Finding) -> Recommendation:
    """
    When no option is a good fit, provide alternative guidance.
    """
    if all(s.score < 50 for s in scores):
        return Recommendation(
            finding=finding,
            primary=None,
            alternatives=[],
            not_recommended=scores,
            fallback_message=generate_fallback_message(scores, finding),
        )

def generate_fallback_message(scores: List[OptionScore], finding: Finding) -> str:
    # Analyze why everything scored low
    reasons = analyze_low_score_reasons(scores)

    if 'budget' in reasons:
        return f"""
        **No strong match for: {finding.title}**

        Your current budget (under €50/mo) limits the options for this finding.

        **Suggestions:**
        1. Prioritize other findings first - build revenue, then revisit
        2. Look for free/freemium tiers of BUY options
        3. Consider this finding a "Phase 2" item

        **Simplest path forward:** Skip this for now, focus on findings #2 and #3
        which have better matches for your profile.
        """

    if 'capability' in reasons:
        return f"""
        **No strong match for: {finding.title}**

        This automation requires technical skills beyond your current level.

        **Suggestions:**
        1. Start simpler - implement findings #4 and #5 first to build confidence
        2. Consider HIRE option if budget allows (€3-5K)
        3. Learn basics of Make.com (free) to unlock CONNECT options

        **Recommended learning path:**
        Week 1-2: Make.com basics (free course)
        Week 3-4: Build simple automation for finding #5
        Then: Revisit this finding with new CONNECT skills
        """

    return f"""
    **No strong match for: {finding.title}**

    This is a complex automation that doesn't fit standard patterns.

    **Suggestions:**
    1. Book a consultation call to discuss custom approaches
    2. Break this into smaller sub-tasks that might have clearer solutions
    3. Consider if this automation is truly necessary vs. nice-to-have
    """
```

### When Multiple Options Tie

```python
def break_tie(tied_options: List[OptionScore], user_profile: 'UserProfile') -> OptionScore:
    """
    When 2+ options have the same score, use tiebreakers.
    """
    # Tiebreaker 1: User's explicit preference
    for option in tied_options:
        if option.option == user_profile.preference:
            return option

    # Tiebreaker 2: Lower risk option
    RISK_ORDER = ['buy', 'hire', 'connect', 'build']  # Lowest to highest risk
    tied_options.sort(key=lambda x: RISK_ORDER.index(x.option))

    return tied_options[0]
```

### When Capability/Budget Mismatch

User wants BUILD but can't code and has low budget:

```python
def handle_aspiration_mismatch(
    user_profile: 'UserProfile',
    desired_option: str
) -> str:
    """
    Generate helpful message when user wants option they can't currently do.
    """
    if desired_option == 'build' and user_profile.capability in ['non_technical', 'tutorial_follower']:
        return f"""
        **You selected BUILD as your preference**

        We love the ambition! Custom solutions give you full control.
        Here's how to get there:

        **Your path to BUILD capability:**

        1. **Start with BUY** (now)
           - Get the problem solved immediately with Calendly
           - Free up mental space to learn

        2. **Learn automation basics** (Month 1-2)
           - Free course: Make.com Academy
           - Build confidence with no-code tools
           - Your profile will unlock CONNECT options

        3. **Explore AI coding tools** (Month 3-4)
           - Try Cursor or Claude Code
           - Build a simple personal project
           - These tools make coding accessible to non-devs

        4. **Revisit BUILD** (Month 6+)
           - With new skills, BUILD options become viable
           - Your BUY solution data exports cleanly
           - You'll know exactly what custom features you need

        **For now:** We recommend 🛒 BUY as your starting point.
        """

    if desired_option == 'hire' and user_profile.budget == 'low':
        return f"""
        **You selected HIRE as your preference**

        Having an expert handle it is smart! The constraint is budget.

        **Options within your budget:**

        1. **Freelancer on Fiverr/Upwork** (€200-500)
           - Simpler scope than full agency
           - Good for single integrations

        2. **Done-with-you coaching** (€150-300)
           - Expert guides you through setup
           - You do the clicking, they advise

        3. **Template + setup service** (€100-200)
           - Pre-built automation template
           - Quick customization for your tools

        **For this finding:** We recommend 🛒 BUY as the most
        budget-friendly path, with HIRE for higher-value findings later.
        """
```

### When Existing Stack Has Poor API Support

```python
def handle_poor_api_stack(
    user_profile: 'UserProfile',
    finding: Finding
) -> str:
    """
    When CONNECT isn't viable due to closed systems.
    """
    closed_tools = [t for t in user_profile.existing_stack if t.api_openness_score < 3]

    if closed_tools and user_profile.preference == 'connect':
        tool_names = ", ".join([t.name for t in closed_tools])
        return f"""
        **CONNECT limitation detected**

        Your current tools ({tool_names}) have limited API access,
        which makes integration difficult.

        **Options:**

        1. **Work around it** (short-term)
           - Use email/webhook triggers instead of direct API
           - Manual CSV export/import for data sync
           - Zapier/Make may have limited connectors

        2. **Replace the blocker** (medium-term)
           - {closed_tools[0].name} alternatives with better APIs:
             {get_api_friendly_alternatives(closed_tools[0])}
           - Migration effort: typically 2-4 weeks

        3. **Accept BUY option** (pragmatic)
           - Standalone tool that doesn't need to integrate
           - Manages this workflow independently

        **Our recommendation:** For {finding.title}, go with 🛒 BUY
        since CONNECT isn't viable with your current stack.
        """
```

---

## Example Output (Enhanced Format)

Below are complete examples showing the new recommendation format with all improvements.

---

### Example 1: Non-Technical User, Low Budget (Dental Practice)

**User Profile:**
- Industry: Dental
- Capability: Non-technical
- Preference: Buy
- Budget: Low (under €50/mo)
- Urgency: This month
- Existing Stack: Dentrix (low API openness)

**Finding:** "Automate appointment reminders"

#### Comparison Table

```
                    🛒 BUY       🔗 CONNECT    🏗️ BUILD      👥 HIRE
────────────────────────────────────────────────────────────────────────
Time to Value       ⚡ 1 day      🕐 1 week     🕐 3-4 weeks   🕐 2-3 weeks
Upfront Cost        €0           €200          €3,000         €4,000
Year 1 Total        €144         €200          €3,300         €4,000
Year 3 Total        €432         €200          €3,900         €4,000
────────────────────────────────────────────────────────────────────────
Flexibility         ⭐⭐          ⭐⭐⭐         ⭐⭐⭐⭐⭐        ⭐⭐⭐⭐
Your Effort         None         4-8 hrs       30-40 hrs      2-3 hrs
Risk Level          Low          Medium        High           Low
────────────────────────────────────────────────────────────────────────
YOUR MATCH          92% ⬅️       35%           15%            48%
```

#### Your Recommended Path

┌─────────────────────────────────────────────────────────────────┐
│  🛒 BUY: Calendly                                   92% MATCH   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Why this fits you:                                             │
│  ✓ No technical skills needed - perfect for your comfort level  │
│  ✓ Within your under-€50/mo budget at €12/month                 │
│  ✓ Ready in 1 day - meets your "this month" timeline            │
│                                                                 │
│  Investment: €12/month (€144/year)                              │
│  Time to value: Same day                                        │
│                                                                 │
│  [Start Free Trial →](https://calendly.com)                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

**Alternatives:**

┌──────────────────────────────┐
│  👥 HIRE: Agency    48%      │
├──────────────────────────────┤
│  Hands-off, but €4K upfront  │
│  Best if: Budget increases   │
│  and you want custom         │
└──────────────────────────────┘

**Not Recommended for You:**

```
🔗 CONNECT (35%): Requires automation skills + your Dentrix has limited API
🏗️ BUILD (15%): Requires coding skills you don't have
```

#### Next Steps

**Start now:** [Create free Calendly account →](https://calendly.com/signup)

1. **Create account** (2 min) - Use your practice email
2. **Connect Google/Outlook calendar** (2 min)
3. **Create "Patient Appointment" event type** (5 min)
4. **Enable 24hr + 1hr reminder emails** (1 min)
5. **Test with a sample booking** (5 min)

**⏱️ Time to first win:** 15 minutes
**✅ Success:** Patient receives automatic reminder 24hr before appointment

#### Growth Path

```
NOW                    6+ MONTHS (if needed)
────────────────────────────────────────────
🛒 Calendly     →     👥 HIRE custom solution
€12/mo                if you outgrow Calendly's features
15 min setup          Your appointment data exports as CSV
```

---

### Example 2: Automation-Savvy User with HubSpot (Consulting)

**User Profile:**
- Industry: Consulting
- Capability: Automation user
- Preference: Connect
- Budget: Moderate (€50-200/mo)
- Urgency: This quarter
- Existing Stack: HubSpot (high API openness), Gmail, Notion

**Finding:** "Automate appointment reminders"

#### Comparison Table

```
                    🛒 BUY       🔗 CONNECT    🏗️ BUILD      👥 HIRE
────────────────────────────────────────────────────────────────────────
Time to Value       ⚡ 1 day      🕐 4-6 hrs    🕐 2-3 weeks   🕐 1-2 weeks
Upfront Cost        €0           €0            €2,000         €2,500
Year 1 Total        €144         €0            €2,300         €2,500
Year 3 Total        €432         €0            €2,900         €2,500
────────────────────────────────────────────────────────────────────────
Flexibility         ⭐⭐          ⭐⭐⭐⭐        ⭐⭐⭐⭐⭐        ⭐⭐⭐⭐
Your Effort         None         4-6 hrs       20-30 hrs      2 hrs
Risk Level          Low          Low           Medium         Low
────────────────────────────────────────────────────────────────────────
YOUR MATCH          68%          94% ⬅️        52%            61%
```

#### Your Recommended Path

┌─────────────────────────────────────────────────────────────────┐
│  🔗 CONNECT: Make + HubSpot                         94% MATCH   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Why this fits you:                                             │
│  ✓ Perfect match for your automation skills                     │
│  ✓ Uses your existing HubSpot data - personalized reminders     │
│  ✓ €0 ongoing cost - one-time 4-6 hour setup                    │
│                                                                 │
│  Investment: €0 (your time: ~5 hours)                           │
│  Time to value: This week                                       │
│                                                                 │
│  [Get Make Template →](https://make.com/templates/hubspot)      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

**Alternatives:**

┌──────────────────────────────┐  ┌──────────────────────────────┐
│  🛒 BUY: Calendly   68%      │  │  👥 HIRE: Freelancer 61%     │
├──────────────────────────────┤  ├──────────────────────────────┤
│  Simpler but another tool    │  │  Someone else builds it      │
│  €144/year                   │  │  €500-1K one-time            │
│  Best if: You want zero      │  │  Best if: Too busy to        │
│  setup effort                │  │  build yourself              │
└──────────────────────────────┘  └──────────────────────────────┘

**Not Recommended for You:**

```
🏗️ BUILD (52%): Overkill for appointment reminders. Your automation
    skills make CONNECT just as powerful with 1/5th the effort.
```

#### 3-Year TCO Analysis

| Option      | Year 1  | Year 3  | Winner? |
|-------------|---------|---------|---------|
| 🔗 CONNECT  | €0      | €0      | ✅ Best |
| 🛒 BUY      | €144    | €432    | Simple  |
| 👥 HIRE     | €2,500  | €2,500  | -       |
| 🏗️ BUILD   | €2,300  | €2,900  | -       |

**CONNECT wins** - €0 total cost, and you'll learn patterns reusable for other automations.

#### Next Steps

**Start now:** [Open Make.com →](https://make.com)

1. **Create Make account** (free tier works) (2 min)
2. **Connect HubSpot** (OAuth flow) (3 min)
3. **Import template:** "HubSpot Meeting Reminder" (1 min)
4. **Customize reminder timing** (24hr, 1hr before) (10 min)
5. **Add personalization** (client name, meeting topic) (15 min)
6. **Test with real meeting** (5 min)

**⏱️ Time to first win:** 4-6 hours spread over 1-2 evenings
**✅ Success:** Personalized reminder pulls client name + context from HubSpot

#### Growth Path

```
NOW                    6 MONTHS               12+ MONTHS
────────────────────────────────────────────────────────────
🔗 Make + HubSpot →   🔗 Advanced flows   →   🏗️ Custom (if needed)
€0, 5 hours           Add SMS, AI follow-up   Only if Make limits you
                      Your Make flows export  Your automation logic transfers
```

---

### Example 3: Developer/AI Coder (Tech Startup)

**User Profile:**
- Industry: Tech startup
- Capability: AI coder (uses Cursor)
- Preference: Build
- Budget: Comfortable (€200-500/mo capacity)
- Urgency: No rush
- Existing Stack: Custom CRM (Supabase), Slack, Linear

**Finding:** "Automate appointment reminders"

#### Comparison Table

```
                    🛒 BUY       🔗 CONNECT    🏗️ BUILD      👥 HIRE
────────────────────────────────────────────────────────────────────────
Time to Value       ⚡ 1 day      🕐 4 hrs      🕐 8-12 hrs    🕐 2 weeks
Upfront Cost        €0           €0            €0-100         €3,000
Year 1 Total        €144         €0            €300           €3,000
Year 3 Total        €432         €0            €900           €3,000
────────────────────────────────────────────────────────────────────────
Flexibility         ⭐⭐          ⭐⭐⭐         ⭐⭐⭐⭐⭐        ⭐⭐⭐⭐
Your Effort         None         4 hrs         8-12 hrs       2 hrs
Customization       Limited      Moderate      Unlimited      High
────────────────────────────────────────────────────────────────────────
YOUR MATCH          58%          72%           91% ⬅️        38%
```

#### Your Recommended Path

┌─────────────────────────────────────────────────────────────────┐
│  🏗️ BUILD: Claude Code + Supabase                   91% MATCH   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Why this fits you:                                             │
│  ✓ Your AI coding skills make this very achievable (8-12 hrs)   │
│  ✓ Full control - integrate directly with your Supabase CRM     │
│  ✓ No recurring cost - just ~€25/mo hosting on Vercel           │
│                                                                 │
│  Investment: ~€100 one-time + €25/mo hosting                    │
│  Time to value: 1-2 weekends                                    │
│                                                                 │
│  Stack: Claude Code → Supabase Edge Functions → Resend          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

**Alternatives:**

┌──────────────────────────────┐  ┌──────────────────────────────┐
│  🔗 CONNECT: Make   72%      │  │  🛒 BUY: Calendly   58%      │
├──────────────────────────────┤  ├──────────────────────────────┤
│  Faster, but less control    │  │  Quick, but doesn't          │
│  €0, 4 hours                 │  │  integrate with your CRM     │
│  Best if: You're short       │  │  Best if: You need it        │
│  on time this sprint         │  │  working TODAY               │
└──────────────────────────────┘  └──────────────────────────────┘

**Not Recommended for You:**

```
👥 HIRE (38%): You can build this yourself faster and cheaper.
    Your team would spend more time specifying requirements than
    the actual build would take you.
```

#### Build Specification

```typescript
// What you'll build (Claude Code can generate this in ~4 hours)

// 1. Supabase Edge Function: reminder-scheduler
//    - Runs daily at 9am
//    - Queries meetings happening in 24hr and 1hr
//    - Queues reminder emails

// 2. Supabase Edge Function: send-reminder
//    - Triggered by queue
//    - Pulls meeting + attendee details
//    - Sends via Resend API
//    - Logs to reminder_logs table

// 3. Database tables
//    - meetings (you have this)
//    - reminder_logs (new)
//    - reminder_templates (new)

// Estimated tokens: ~15K with Claude Code
// Estimated cost: ~€3 in API calls
```

#### Next Steps

**Start now:** Open your IDE with Claude Code

1. **Create `reminder_logs` table** in Supabase (5 min)
2. **Scaffold Edge Function** with Claude Code (30 min)
   - Prompt: "Create a Supabase Edge Function that sends email reminders
     24hr and 1hr before meetings in my `meetings` table"
3. **Set up Resend** for email delivery (10 min)
4. **Test with tomorrow's meeting** (15 min)
5. **Deploy to production** (5 min)

**⏱️ Time to first win:** ~8 hours (1 focused weekend)
**✅ Success:** Custom reminder pulls rich context from your Supabase CRM

#### Why BUILD wins for you

```
3-Year Comparison:
─────────────────────────────────────────────
🛒 BUY (Calendly):  €432 + doesn't integrate with your CRM
🔗 CONNECT (Make):  €0 but limited customization
🏗️ BUILD (Custom): €900 + unlimited flexibility + you learn

BUILD cost is higher, but you get:
✓ Direct CRM integration (no sync issues)
✓ Custom reminder logic (meeting type aware)
✓ Foundation for other automations
✓ Skills that transfer to bigger projects
```

---

### Example 4: Edge Case - No Good Options (Budget Mismatch)

**User Profile:**
- Industry: Healthcare clinic
- Capability: Non-technical
- Preference: Hire
- Budget: Low (under €50/mo)
- Urgency: This month
- Existing Stack: Epic (closed system)

**Finding:** "Build custom patient intake automation"

#### Recommendation

```
⚠️ NO STRONG MATCH FOR THIS FINDING

All options score below 50% for your profile:

| Option      | Score | Blocker                           |
|-------------|-------|-----------------------------------|
| 🛒 BUY      | 42%   | No HIPAA-compliant tool under €50 |
| 🔗 CONNECT  | 18%   | Epic has no API access            |
| 🏗️ BUILD   | 12%   | Requires technical skills         |
| 👥 HIRE     | 35%   | €5K+ minimum, outside budget      |
```

#### What We Recommend Instead

**Option A: Defer this finding**
- Focus on findings #2 and #4 which have 75%+ matches
- Revisit when budget allows €100+/mo for compliant tools

**Option B: Simplify the scope**
- Instead of "custom patient intake automation"
- Start with "digital intake forms" (simpler)
- JotForm HIPAA: €99/mo (stretch budget slightly)

**Option C: Budget path to HIRE**
```
Phase 1: Implement findings #2, #4, #5 (high-match, low-cost)
Phase 2: ROI from those funds budget increase
Phase 3: Revisit this finding with €200+/mo capacity
         → HIRE becomes viable at 65% match
```

**Our recommendation:** Go with **Option A** - this finding isn't urgent
and your resources are better spent on higher-match opportunities first.
