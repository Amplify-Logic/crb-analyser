# Four-Option Personalized Recommendations Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace 3-option recommendations with personalized 4-option (BUY/CONNECT/BUILD/HIRE) recommendations based on user capability, preference, and budget.

**Architecture:** Add 3 quiz questions to capture user profile, create weighted scoring algorithm to calculate match scores (0-100%) for each option, generate personalized recommendations with comparison tables and next steps.

**Tech Stack:** Python/FastAPI, Pydantic models, LLMSkill pattern, React/TypeScript frontend

**Spec Document:** `docs/prompts/improve-4-option-recommendations.md` (full design reference)

---

## CRB Context
- Affected user journey stage: Quiz + Report
- Industries impacted: All (with industry-specific defaults)
- Reference docs to load during execution: `.claude/reference/report-quality.md`

## Rollback Plan
If this fails, revert by:
1. Restore `three_options.py` as the active skill
2. Remove new questions from `questionnaire.py`
3. Keep old frontend components unchanged

---

## Phase 1: Quiz Changes

### Task 1: Add Quiz Questions to Questionnaire

**Files:**
- Modify: `backend/src/config/questionnaire.py`
- Test: Manual verification via quiz flow

**Step 1: Add implementation capability question**

Add after the "Technology & Tools" section (around line 200) in `questionnaire.py`:

```python
# Add this new section after section id=3 (Technology & Tools)
{
    "id": 4,
    "title": "Implementation Preferences",
    "description": "Help us understand how you prefer to solve problems",
    "questions": [
        {
            "id": "implementation_capability",
            "question": "How would you describe your technical comfort level?",
            "type": QuestionType.SELECT,
            "required": True,
            "options": [
                {"value": "non_technical", "label": "I avoid anything technical - just give me something that works"},
                {"value": "tutorial_follower", "label": "I can follow tutorials and use no-code tools like Notion or Airtable"},
                {"value": "automation_user", "label": "I'm comfortable with automation tools like Zapier or Make"},
                {"value": "ai_coder", "label": "I can code or am learning AI coding tools like Cursor"},
                {"value": "has_developers", "label": "I have developers on staff or easy access to technical help"},
            ],
        },
        {
            "id": "implementation_preference",
            "question": "When solving business problems with software, you prefer to...",
            "type": QuestionType.SELECT,
            "required": True,
            "options": [
                {"value": "buy", "label": "Find a ready-made solution that just works"},
                {"value": "connect", "label": "Customize and connect my existing tools"},
                {"value": "build", "label": "Build exactly what I need, even if it takes longer"},
                {"value": "hire", "label": "Hire someone to handle it for me"},
            ],
        },
        {
            "id": "budget_comfort",
            "question": "For a tool that saves you 10+ hours/month, what's your comfort zone?",
            "type": QuestionType.SELECT,
            "required": True,
            "options": [
                {"value": "low", "label": "Under \u20ac50/month"},
                {"value": "moderate", "label": "\u20ac50-200/month"},
                {"value": "comfortable", "label": "\u20ac200-500/month"},
                {"value": "high", "label": "\u20ac500+/month or one-time \u20ac2K-10K investment"},
            ],
        },
        {
            "id": "implementation_urgency",
            "question": "How soon do you need solutions working?",
            "type": QuestionType.SELECT,
            "required": False,
            "options": [
                {"value": "this_week", "label": "This week"},
                {"value": "this_month", "label": "This month"},
                {"value": "this_quarter", "label": "This quarter"},
                {"value": "no_rush", "label": "No rush, want it done right"},
            ],
        },
    ],
},
```

**Step 2: Update section IDs**

Renumber subsequent sections (Pain Points becomes id=5, AI Readiness becomes id=6).

**Step 3: Verify quiz renders correctly**

Run: `cd frontend && npm run dev`
Open: `http://localhost:5174/quiz`
Expected: New section "Implementation Preferences" appears with 4 questions

**Step 4: Commit**

```bash
git add backend/src/config/questionnaire.py
git commit -m "feat(quiz): add implementation capability questions for 4-option recommendations"
```

---

## Phase 2: Data Models

### Task 2: Create UserProfile Model

**Files:**
- Create: `backend/src/models/user_profile.py`
- Test: `backend/tests/models/test_user_profile.py`

**Step 1: Write the failing test**

Create `backend/tests/models/test_user_profile.py`:

```python
"""Tests for UserProfile model."""
import pytest
from src.models.user_profile import (
    UserProfile,
    CapabilityLevel,
    ImplementationPreference,
    BudgetTier,
    Urgency,
)


class TestUserProfile:
    """Test UserProfile model creation and validation."""

    def test_create_user_profile_minimal(self):
        """Test creating profile with required fields only."""
        profile = UserProfile(
            capability=CapabilityLevel.AUTOMATION_USER,
            preference=ImplementationPreference.CONNECT,
            budget=BudgetTier.MODERATE,
        )
        assert profile.capability == CapabilityLevel.AUTOMATION_USER
        assert profile.preference == ImplementationPreference.CONNECT
        assert profile.budget == BudgetTier.MODERATE
        assert profile.urgency is None
        assert profile.existing_stack_api_ready is False

    def test_create_user_profile_full(self):
        """Test creating profile with all fields."""
        profile = UserProfile(
            capability=CapabilityLevel.AI_CODER,
            preference=ImplementationPreference.BUILD,
            budget=BudgetTier.COMFORTABLE,
            urgency=Urgency.THIS_QUARTER,
            existing_stack_api_ready=True,
            industry="tech_startup",
        )
        assert profile.capability == CapabilityLevel.AI_CODER
        assert profile.urgency == Urgency.THIS_QUARTER
        assert profile.existing_stack_api_ready is True
        assert profile.industry == "tech_startup"

    def test_from_quiz_answers(self):
        """Test creating profile from quiz answers dict."""
        answers = {
            "implementation_capability": "automation_user",
            "implementation_preference": "connect",
            "budget_comfort": "moderate",
            "implementation_urgency": "this_month",
            "industry": "consulting",
        }
        profile = UserProfile.from_quiz_answers(answers)
        assert profile.capability == CapabilityLevel.AUTOMATION_USER
        assert profile.preference == ImplementationPreference.CONNECT
        assert profile.budget == BudgetTier.MODERATE
        assert profile.urgency == Urgency.THIS_MONTH

    def test_from_quiz_answers_with_defaults(self):
        """Test profile uses defaults when answers missing."""
        answers = {"industry": "dental"}
        profile = UserProfile.from_quiz_answers(answers)
        # Should use industry defaults for dental
        assert profile.capability == CapabilityLevel.NON_TECHNICAL
        assert profile.preference == ImplementationPreference.BUY
        assert profile.budget == BudgetTier.MODERATE
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/models/test_user_profile.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.models.user_profile'"

**Step 3: Write minimal implementation**

Create `backend/src/models/user_profile.py`:

```python
"""
User Profile Model

Captures implementation capability, preference, and budget
for personalized 4-option recommendations.
"""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class CapabilityLevel(str, Enum):
    """Technical capability levels for option scoring."""
    NON_TECHNICAL = "non_technical"
    TUTORIAL_FOLLOWER = "tutorial_follower"
    AUTOMATION_USER = "automation_user"
    AI_CODER = "ai_coder"
    HAS_DEVELOPERS = "has_developers"


class ImplementationPreference(str, Enum):
    """User's preferred approach to solving problems."""
    BUY = "buy"
    CONNECT = "connect"
    BUILD = "build"
    HIRE = "hire"


class BudgetTier(str, Enum):
    """Budget comfort level for automation tools."""
    LOW = "low"              # Under 50/month
    MODERATE = "moderate"    # 50-200/month
    COMFORTABLE = "comfortable"  # 200-500/month
    HIGH = "high"            # 500+/month or 2K-10K one-time


class Urgency(str, Enum):
    """How soon user needs solution working."""
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    THIS_QUARTER = "this_quarter"
    NO_RUSH = "no_rush"


# Industry defaults when quiz answers are missing
INDUSTRY_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "dental": {
        "capability": CapabilityLevel.NON_TECHNICAL,
        "preference": ImplementationPreference.BUY,
        "budget": BudgetTier.MODERATE,
    },
    "legal": {
        "capability": CapabilityLevel.TUTORIAL_FOLLOWER,
        "preference": ImplementationPreference.BUY,
        "budget": BudgetTier.COMFORTABLE,
    },
    "tech_startup": {
        "capability": CapabilityLevel.HAS_DEVELOPERS,
        "preference": ImplementationPreference.BUILD,
        "budget": BudgetTier.LOW,
    },
    "ecommerce": {
        "capability": CapabilityLevel.AUTOMATION_USER,
        "preference": ImplementationPreference.CONNECT,
        "budget": BudgetTier.MODERATE,
    },
    "healthcare": {
        "capability": CapabilityLevel.NON_TECHNICAL,
        "preference": ImplementationPreference.HIRE,
        "budget": BudgetTier.COMFORTABLE,
    },
    "consulting": {
        "capability": CapabilityLevel.AUTOMATION_USER,
        "preference": ImplementationPreference.CONNECT,
        "budget": BudgetTier.MODERATE,
    },
    "real_estate": {
        "capability": CapabilityLevel.TUTORIAL_FOLLOWER,
        "preference": ImplementationPreference.BUY,
        "budget": BudgetTier.COMFORTABLE,
    },
}

# Fallback defaults
DEFAULT_PROFILE = {
    "capability": CapabilityLevel.TUTORIAL_FOLLOWER,
    "preference": ImplementationPreference.BUY,
    "budget": BudgetTier.MODERATE,
}


class UserProfile(BaseModel):
    """
    User's implementation profile for recommendation scoring.

    Captures capability, preference, budget, and urgency to
    calculate personalized match scores for BUY/CONNECT/BUILD/HIRE.
    """
    capability: CapabilityLevel = Field(
        ...,
        description="Technical capability level"
    )
    preference: ImplementationPreference = Field(
        ...,
        description="Preferred implementation approach"
    )
    budget: BudgetTier = Field(
        ...,
        description="Budget comfort level"
    )
    urgency: Optional[Urgency] = Field(
        default=None,
        description="How soon solution is needed"
    )
    existing_stack_api_ready: bool = Field(
        default=False,
        description="Whether existing tools have good API support"
    )
    industry: Optional[str] = Field(
        default=None,
        description="User's industry for context"
    )

    @classmethod
    def from_quiz_answers(
        cls,
        answers: Dict[str, Any],
        existing_stack_api_ready: bool = False,
    ) -> "UserProfile":
        """
        Create UserProfile from quiz answers dict.

        Falls back to industry defaults, then global defaults.
        """
        industry = answers.get("industry", "")
        industry_defaults = INDUSTRY_DEFAULTS.get(industry, DEFAULT_PROFILE)

        # Get capability with fallback
        capability_str = answers.get("implementation_capability")
        if capability_str:
            capability = CapabilityLevel(capability_str)
        else:
            capability = industry_defaults.get("capability", DEFAULT_PROFILE["capability"])

        # Get preference with fallback
        preference_str = answers.get("implementation_preference")
        if preference_str:
            preference = ImplementationPreference(preference_str)
        else:
            preference = industry_defaults.get("preference", DEFAULT_PROFILE["preference"])

        # Get budget with fallback
        budget_str = answers.get("budget_comfort")
        if budget_str:
            budget = BudgetTier(budget_str)
        else:
            budget = industry_defaults.get("budget", DEFAULT_PROFILE["budget"])

        # Get urgency (optional, no default)
        urgency_str = answers.get("implementation_urgency")
        urgency = Urgency(urgency_str) if urgency_str else None

        return cls(
            capability=capability,
            preference=preference,
            budget=budget,
            urgency=urgency,
            existing_stack_api_ready=existing_stack_api_ready,
            industry=industry if industry else None,
        )
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/models/test_user_profile.py -v`
Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add backend/src/models/user_profile.py backend/tests/models/test_user_profile.py
git commit -m "feat(models): add UserProfile model for 4-option scoring"
```

---

### Task 3: Create Four Option Models

**Files:**
- Create: `backend/src/models/four_options.py`
- Test: `backend/tests/models/test_four_options.py`

**Step 1: Write the failing test**

Create `backend/tests/models/test_four_options.py`:

```python
"""Tests for Four Options models."""
import pytest
from src.models.four_options import (
    OptionType,
    OptionScore,
    BuyOption,
    ConnectOption,
    BuildOption,
    HireOption,
    FourOptionRecommendation,
    CostEstimate,
)


class TestOptionScore:
    """Test OptionScore model."""

    def test_create_option_score(self):
        """Test creating an option score."""
        score = OptionScore(
            option=OptionType.BUY,
            score=85.0,
            breakdown={
                "capability_match": 100,
                "preference_match": 80,
                "budget_fit": 90,
                "time_fit": 70,
                "value_ratio": 85,
            },
            match_reasons=["No technical skills needed", "Within budget"],
            concern_reasons=[],
            is_recommended=True,
        )
        assert score.option == OptionType.BUY
        assert score.score == 85.0
        assert score.is_recommended is True
        assert len(score.match_reasons) == 2


class TestBuyOption:
    """Test BuyOption model."""

    def test_create_buy_option(self):
        """Test creating a BUY option."""
        option = BuyOption(
            vendor_slug="calendly",
            vendor_name="Calendly",
            price="12/mo",
            setup_time="30 minutes",
            pros=["Easy setup", "No technical skills"],
            cons=["Limited customization"],
            website="https://calendly.com",
        )
        assert option.vendor_name == "Calendly"
        assert option.price == "12/mo"


class TestFourOptionRecommendation:
    """Test FourOptionRecommendation model."""

    def test_create_recommendation_with_all_options(self):
        """Test creating recommendation with all 4 options."""
        rec = FourOptionRecommendation(
            finding_id="finding-001",
            finding_title="Automate appointment reminders",
            buy=BuyOption(
                vendor_slug="calendly",
                vendor_name="Calendly",
                price="12/mo",
                setup_time="30 minutes",
                pros=["Easy"],
                cons=["Basic"],
            ),
            connect=ConnectOption(
                integration_platform="Make",
                connects_to=["HubSpot", "Gmail"],
                estimated_hours=4,
                complexity="low",
            ),
            build=BuildOption(
                recommended_stack=["Claude Code", "Supabase"],
                estimated_cost="2K-5K",
                estimated_hours="20-40",
                skills_needed=["Python"],
                ai_coding_viable=True,
            ),
            hire=HireOption(
                service_type="Freelancer",
                estimated_cost="500-1K",
                estimated_timeline="1 week",
                where_to_find=["Upwork"],
            ),
            scores=[
                OptionScore(
                    option=OptionType.BUY,
                    score=92,
                    breakdown={},
                    match_reasons=["Easy"],
                    concern_reasons=[],
                    is_recommended=True,
                ),
            ],
            recommended=OptionType.BUY,
            recommendation_reasoning="Best match for your profile",
        )
        assert rec.recommended == OptionType.BUY
        assert rec.buy.vendor_name == "Calendly"
        assert len(rec.scores) == 1
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/models/test_four_options.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `backend/src/models/four_options.py`:

```python
"""
Four Options Models

Data models for BUY/CONNECT/BUILD/HIRE recommendation system.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class OptionType(str, Enum):
    """The four implementation options."""
    BUY = "buy"
    CONNECT = "connect"
    BUILD = "build"
    HIRE = "hire"


class CostEstimate(BaseModel):
    """Cost breakdown for TCO calculations."""
    upfront: float = Field(default=0, description="One-time costs")
    monthly: float = Field(default=0, description="Recurring monthly")
    year_one_total: float = Field(default=0, description="Total first year cost")
    year_three_total: float = Field(default=0, description="Total 3-year cost")


class OptionScore(BaseModel):
    """
    Weighted score for a single option.

    Score is 0-100 based on:
    - capability_match (30%)
    - preference_match (20%)
    - budget_fit (20%)
    - time_fit (15%)
    - value_ratio (15%)
    """
    option: OptionType
    score: float = Field(..., ge=0, le=100)
    breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Individual factor scores"
    )
    match_reasons: List[str] = Field(
        default_factory=list,
        description="Why this option scores well (max 3)"
    )
    concern_reasons: List[str] = Field(
        default_factory=list,
        description="Why this option loses points (max 2)"
    )
    is_recommended: bool = Field(
        default=False,
        description="True if this is the top-scoring option"
    )


class NextStep(BaseModel):
    """A single actionable step."""
    order: int
    action: str
    time_estimate: str
    help_link: Optional[str] = None


class BuyOption(BaseModel):
    """
    BUY option: Pre-built SaaS solution.

    Best when: User wants turnkey, no technical skills needed.
    """
    vendor_slug: str = Field(..., description="Vendor identifier")
    vendor_name: str = Field(..., description="Display name")
    price: str = Field(..., description="e.g., '12/mo' or '144/year'")
    setup_time: str = Field(..., description="e.g., '30 minutes'")
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    website: Optional[str] = None
    next_steps: List[NextStep] = Field(default_factory=list)
    cost: CostEstimate = Field(default_factory=CostEstimate)


class ConnectOption(BaseModel):
    """
    CONNECT option: Integrate existing tools via automation.

    Best when: User has existing tools with APIs, some automation comfort.
    """
    integration_platform: str = Field(
        ...,
        description="Make, n8n, Zapier, etc."
    )
    connects_to: List[str] = Field(
        default_factory=list,
        description="Tools being connected"
    )
    estimated_hours: int = Field(..., description="Setup hours")
    complexity: str = Field(default="medium", description="low/medium/high")
    template_url: Optional[str] = Field(
        None,
        description="Link to pre-built template if exists"
    )
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    next_steps: List[NextStep] = Field(default_factory=list)
    cost: CostEstimate = Field(default_factory=CostEstimate)


class BuildOption(BaseModel):
    """
    BUILD option: Custom solution with AI coding tools.

    Best when: User has dev skills OR willing to learn AI coding tools.
    """
    recommended_stack: List[str] = Field(
        default_factory=list,
        description="e.g., ['Claude Code', 'Supabase', 'Vercel']"
    )
    estimated_cost: str = Field(..., description="e.g., '2K-5K'")
    estimated_hours: str = Field(..., description="e.g., '20-40 hours'")
    skills_needed: List[str] = Field(default_factory=list)
    ai_coding_viable: bool = Field(
        default=True,
        description="Can non-dev build this with AI tools?"
    )
    approach: Optional[str] = Field(
        None,
        description="Brief description of what to build"
    )
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    next_steps: List[NextStep] = Field(default_factory=list)
    cost: CostEstimate = Field(default_factory=CostEstimate)


class HireOption(BaseModel):
    """
    HIRE option: Agency or freelancer builds it.

    Best when: User wants custom but lacks time/skills.
    """
    service_type: str = Field(
        ...,
        description="Agency, Freelancer, or Consultant"
    )
    estimated_cost: str = Field(..., description="e.g., '3K-8K'")
    estimated_timeline: str = Field(..., description="e.g., '2-3 weeks'")
    where_to_find: List[str] = Field(
        default_factory=list,
        description="Upwork, Toptal, etc."
    )
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    next_steps: List[NextStep] = Field(default_factory=list)
    cost: CostEstimate = Field(default_factory=CostEstimate)


class TradeoffRow(BaseModel):
    """Single row in comparison table."""
    metric: str
    buy: str
    connect: str
    build: str
    hire: str


class FourOptionRecommendation(BaseModel):
    """
    Complete 4-option recommendation for a finding.

    Includes all four options, scores, and the recommended path.
    """
    finding_id: str
    finding_title: str

    # The four options (all required, but may be marked as "not viable")
    buy: BuyOption
    connect: Optional[ConnectOption] = None
    build: Optional[BuildOption] = None
    hire: Optional[HireOption] = None

    # Scoring
    scores: List[OptionScore] = Field(default_factory=list)
    recommended: OptionType
    recommendation_reasoning: str

    # Comparison table data
    tradeoff_table: List[TradeoffRow] = Field(default_factory=list)

    # Growth path
    growth_path: Optional[str] = Field(
        None,
        description="How this option can evolve over time"
    )

    # Edge case handling
    no_good_match: bool = Field(
        default=False,
        description="True if all options score below 50%"
    )
    fallback_message: Optional[str] = Field(
        None,
        description="Guidance when no option fits well"
    )
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/models/test_four_options.py -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add backend/src/models/four_options.py backend/tests/models/test_four_options.py
git commit -m "feat(models): add FourOptionRecommendation models"
```

---

### Task 4: Create Scoring Algorithm

**Files:**
- Create: `backend/src/services/option_scoring.py`
- Test: `backend/tests/services/test_option_scoring.py`

**Step 1: Write the failing test**

Create `backend/tests/services/test_option_scoring.py`:

```python
"""Tests for option scoring algorithm."""
import pytest
from src.services.option_scoring import (
    score_option,
    calculate_capability_match,
    calculate_budget_fit,
    calculate_time_fit,
    get_recommendations,
    SCORING_WEIGHTS,
)
from src.models.user_profile import (
    UserProfile,
    CapabilityLevel,
    ImplementationPreference,
    BudgetTier,
    Urgency,
)
from src.models.four_options import OptionType, CostEstimate


class TestCapabilityMatch:
    """Test capability matching logic."""

    def test_non_technical_scores_high_for_buy(self):
        """Non-technical user should score 100 for BUY."""
        score = calculate_capability_match(
            OptionType.BUY,
            CapabilityLevel.NON_TECHNICAL
        )
        assert score == 100

    def test_non_technical_scores_low_for_build(self):
        """Non-technical user should score very low for BUILD."""
        score = calculate_capability_match(
            OptionType.BUILD,
            CapabilityLevel.NON_TECHNICAL
        )
        assert score <= 20

    def test_ai_coder_scores_high_for_build(self):
        """AI coder should score 100 for BUILD."""
        score = calculate_capability_match(
            OptionType.BUILD,
            CapabilityLevel.AI_CODER
        )
        assert score == 100

    def test_automation_user_scores_high_for_connect(self):
        """Automation user should score 100 for CONNECT."""
        score = calculate_capability_match(
            OptionType.CONNECT,
            CapabilityLevel.AUTOMATION_USER
        )
        assert score == 100


class TestBudgetFit:
    """Test budget fit scoring."""

    def test_low_budget_fits_cheap_option(self):
        """Low budget should fit option under 600/year."""
        cost = CostEstimate(year_one_total=144)  # 12/month
        score = calculate_budget_fit(cost, BudgetTier.LOW)
        assert score >= 80

    def test_low_budget_does_not_fit_expensive(self):
        """Low budget should not fit 5K option."""
        cost = CostEstimate(year_one_total=5000)
        score = calculate_budget_fit(cost, BudgetTier.LOW)
        assert score <= 30


class TestTimeFit:
    """Test time fit scoring."""

    def test_this_week_urgency_fits_1_day(self):
        """This week urgency should fit 1-day option."""
        score = calculate_time_fit("1 day", Urgency.THIS_WEEK)
        assert score == 100

    def test_this_week_urgency_does_not_fit_4_weeks(self):
        """This week urgency should not fit 4-week option."""
        score = calculate_time_fit("4 weeks", Urgency.THIS_WEEK)
        assert score <= 30


class TestFullScoring:
    """Test full option scoring."""

    def test_non_technical_low_budget_recommends_buy(self):
        """Non-technical user with low budget should get BUY recommended."""
        profile = UserProfile(
            capability=CapabilityLevel.NON_TECHNICAL,
            preference=ImplementationPreference.BUY,
            budget=BudgetTier.LOW,
            urgency=Urgency.THIS_MONTH,
        )

        # Mock option costs
        option_costs = {
            OptionType.BUY: CostEstimate(year_one_total=144),
            OptionType.CONNECT: CostEstimate(year_one_total=200),
            OptionType.BUILD: CostEstimate(year_one_total=3000),
            OptionType.HIRE: CostEstimate(year_one_total=5000),
        }
        option_times = {
            OptionType.BUY: "1 day",
            OptionType.CONNECT: "1 week",
            OptionType.BUILD: "3 weeks",
            OptionType.HIRE: "2 weeks",
        }

        recommendations = get_recommendations(
            profile, option_costs, option_times
        )

        assert recommendations[0].option == OptionType.BUY
        assert recommendations[0].is_recommended is True
        assert recommendations[0].score >= 80

    def test_ai_coder_comfortable_budget_considers_build(self):
        """AI coder with comfortable budget should have BUILD score highly."""
        profile = UserProfile(
            capability=CapabilityLevel.AI_CODER,
            preference=ImplementationPreference.BUILD,
            budget=BudgetTier.COMFORTABLE,
            urgency=Urgency.THIS_QUARTER,
        )

        option_costs = {
            OptionType.BUY: CostEstimate(year_one_total=144),
            OptionType.CONNECT: CostEstimate(year_one_total=200),
            OptionType.BUILD: CostEstimate(year_one_total=3000),
            OptionType.HIRE: CostEstimate(year_one_total=5000),
        }
        option_times = {
            OptionType.BUY: "1 day",
            OptionType.CONNECT: "1 week",
            OptionType.BUILD: "3 weeks",
            OptionType.HIRE: "2 weeks",
        }

        recommendations = get_recommendations(
            profile, option_costs, option_times
        )

        # BUILD should be recommended or score highly
        build_score = next(
            r for r in recommendations if r.option == OptionType.BUILD
        )
        assert build_score.score >= 70
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/services/test_option_scoring.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `backend/src/services/option_scoring.py`:

```python
"""
Option Scoring Service

Calculates weighted match scores (0-100) for BUY/CONNECT/BUILD/HIRE options
based on user profile (capability, preference, budget, urgency).
"""

from typing import Dict, List, Optional
from src.models.user_profile import (
    UserProfile,
    CapabilityLevel,
    ImplementationPreference,
    BudgetTier,
    Urgency,
)
from src.models.four_options import OptionType, OptionScore, CostEstimate


# Scoring weights (must sum to 1.0)
SCORING_WEIGHTS = {
    "capability_match": 0.30,
    "preference_match": 0.20,
    "budget_fit": 0.20,
    "time_fit": 0.15,
    "value_ratio": 0.15,
}

# Capability matrix: option -> capability -> score
CAPABILITY_MATRIX: Dict[OptionType, Dict[CapabilityLevel, int]] = {
    OptionType.BUY: {
        CapabilityLevel.NON_TECHNICAL: 100,
        CapabilityLevel.TUTORIAL_FOLLOWER: 100,
        CapabilityLevel.AUTOMATION_USER: 90,
        CapabilityLevel.AI_CODER: 80,
        CapabilityLevel.HAS_DEVELOPERS: 70,
    },
    OptionType.CONNECT: {
        CapabilityLevel.NON_TECHNICAL: 20,
        CapabilityLevel.TUTORIAL_FOLLOWER: 60,
        CapabilityLevel.AUTOMATION_USER: 100,
        CapabilityLevel.AI_CODER: 90,
        CapabilityLevel.HAS_DEVELOPERS: 85,
    },
    OptionType.BUILD: {
        CapabilityLevel.NON_TECHNICAL: 10,
        CapabilityLevel.TUTORIAL_FOLLOWER: 30,
        CapabilityLevel.AUTOMATION_USER: 50,
        CapabilityLevel.AI_CODER: 100,
        CapabilityLevel.HAS_DEVELOPERS: 100,
    },
    OptionType.HIRE: {
        CapabilityLevel.NON_TECHNICAL: 90,
        CapabilityLevel.TUTORIAL_FOLLOWER: 85,
        CapabilityLevel.AUTOMATION_USER: 80,
        CapabilityLevel.AI_CODER: 70,
        CapabilityLevel.HAS_DEVELOPERS: 50,
    },
}

# Budget limits in EUR (annual)
BUDGET_LIMITS = {
    BudgetTier.LOW: 600,           # 50/month
    BudgetTier.MODERATE: 2400,     # 200/month
    BudgetTier.COMFORTABLE: 6000,  # 500/month
    BudgetTier.HIGH: 50000,
}

# Time limits in days
URGENCY_LIMITS = {
    Urgency.THIS_WEEK: 7,
    Urgency.THIS_MONTH: 30,
    Urgency.THIS_QUARTER: 90,
    Urgency.NO_RUSH: 365,
}

# Time to value mappings
TIME_MAP = {
    "1 day": 1,
    "2 days": 2,
    "3 days": 3,
    "1 week": 7,
    "2 weeks": 14,
    "3 weeks": 21,
    "4 weeks": 28,
    "1 month": 30,
    "2-3 weeks": 18,
    "2-4 weeks": 21,
    "4-6 weeks": 35,
    "4-8 weeks": 42,
}

# Match reasons by option and capability
CAPABILITY_MATCH_REASONS: Dict[OptionType, Dict[CapabilityLevel, str]] = {
    OptionType.BUY: {
        CapabilityLevel.NON_TECHNICAL: "No technical skills needed",
        CapabilityLevel.TUTORIAL_FOLLOWER: "Simple setup you can handle",
        CapabilityLevel.AUTOMATION_USER: "Quick win - save your automation skills for bigger projects",
        CapabilityLevel.AI_CODER: "Fast solution - save your coding time for custom needs",
        CapabilityLevel.HAS_DEVELOPERS: "Don't waste dev time on solved problems",
    },
    OptionType.CONNECT: {
        CapabilityLevel.AUTOMATION_USER: "Perfect match for your automation skills",
        CapabilityLevel.AI_CODER: "Quick integration using tools you know",
        CapabilityLevel.HAS_DEVELOPERS: "Your team can set this up quickly",
    },
    OptionType.BUILD: {
        CapabilityLevel.AI_CODER: "Your AI coding skills make this very achievable",
        CapabilityLevel.HAS_DEVELOPERS: "Your dev team can build exactly what you need",
    },
    OptionType.HIRE: {
        CapabilityLevel.NON_TECHNICAL: "Expert handles everything for you",
        CapabilityLevel.TUTORIAL_FOLLOWER: "Professional setup, you maintain",
    },
}


def calculate_capability_match(
    option: OptionType,
    capability: CapabilityLevel
) -> int:
    """Score how well user's capability matches option requirements."""
    return CAPABILITY_MATRIX.get(option, {}).get(capability, 50)


def calculate_budget_fit(
    cost: CostEstimate,
    budget_tier: BudgetTier
) -> int:
    """Score how well option cost fits user's budget."""
    limit = BUDGET_LIMITS.get(budget_tier, 2400)
    annual_cost = cost.year_one_total

    if annual_cost <= limit * 0.5:
        return 100  # Well within budget
    elif annual_cost <= limit:
        return 80   # Fits budget
    elif annual_cost <= limit * 1.5:
        return 50   # Stretch
    else:
        return 20   # Out of budget


def calculate_time_fit(
    time_to_value: str,
    urgency: Optional[Urgency]
) -> int:
    """Score how well option timeline fits user's urgency."""
    if urgency is None:
        return 80  # No urgency specified, neutral score

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


def score_option(
    option: OptionType,
    profile: UserProfile,
    cost: CostEstimate,
    time_to_value: str,
    value_score: int = 80,  # Default good value
) -> OptionScore:
    """
    Calculate weighted match score for an option.

    Returns OptionScore with 0-100 score and reasoning.
    """
    breakdown = {}
    match_reasons = []
    concern_reasons = []

    # 1. Capability Match (30%)
    cap_score = calculate_capability_match(option, profile.capability)
    breakdown["capability_match"] = cap_score
    if cap_score >= 80:
        reason = CAPABILITY_MATCH_REASONS.get(option, {}).get(profile.capability)
        if reason:
            match_reasons.append(reason)
    elif cap_score < 50:
        if option == OptionType.BUILD:
            concern_reasons.append("Requires technical skills")
        elif option == OptionType.CONNECT:
            concern_reasons.append("Requires automation tool experience")

    # 2. Preference Match (20%)
    pref_map = {
        ImplementationPreference.BUY: OptionType.BUY,
        ImplementationPreference.CONNECT: OptionType.CONNECT,
        ImplementationPreference.BUILD: OptionType.BUILD,
        ImplementationPreference.HIRE: OptionType.HIRE,
    }
    pref_score = 100 if pref_map.get(profile.preference) == option else 60
    breakdown["preference_match"] = pref_score
    if pref_score == 100:
        match_reasons.append(f"Matches your '{option.value}' preference")

    # 3. Budget Fit (20%)
    budget_score = calculate_budget_fit(cost, profile.budget)
    breakdown["budget_fit"] = budget_score
    if budget_score >= 80:
        match_reasons.append(f"Within your {profile.budget.value} budget")
    elif budget_score < 50:
        concern_reasons.append(f"May stretch your {profile.budget.value} budget")

    # 4. Time Fit (15%)
    time_score = calculate_time_fit(time_to_value, profile.urgency)
    breakdown["time_fit"] = time_score
    if time_score >= 80 and profile.urgency:
        match_reasons.append(f"Fits your {profile.urgency.value.replace('_', ' ')} timeline")
    elif time_score < 50 and profile.urgency:
        concern_reasons.append(f"May not meet your {profile.urgency.value.replace('_', ' ')} deadline")

    # 5. Value Ratio (15%) - passed in, default 80
    breakdown["value_ratio"] = value_score
    if value_score >= 80:
        match_reasons.append("Good ROI for this specific problem")

    # Calculate weighted total
    total_score = sum(
        breakdown[factor] * weight
        for factor, weight in SCORING_WEIGHTS.items()
    )

    return OptionScore(
        option=option,
        score=round(total_score, 0),
        breakdown=breakdown,
        match_reasons=match_reasons[:3],  # Top 3
        concern_reasons=concern_reasons[:2],  # Top 2
        is_recommended=False,  # Set later
    )


def get_recommendations(
    profile: UserProfile,
    option_costs: Dict[OptionType, CostEstimate],
    option_times: Dict[OptionType, str],
    option_values: Optional[Dict[OptionType, int]] = None,
) -> List[OptionScore]:
    """
    Score all options and return ranked list.

    Highest scoring option is marked as recommended.
    """
    if option_values is None:
        option_values = {opt: 80 for opt in OptionType}

    scores = []
    for option in OptionType:
        cost = option_costs.get(option, CostEstimate())
        time = option_times.get(option, "2 weeks")
        value = option_values.get(option, 80)

        score = score_option(option, profile, cost, time, value)
        scores.append(score)

    # Sort by score descending
    scores.sort(key=lambda x: x.score, reverse=True)

    # Mark highest as recommended
    if scores:
        scores[0].is_recommended = True

    return scores
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/services/test_option_scoring.py -v`
Expected: All 8 tests PASS

**Step 5: Commit**

```bash
git add backend/src/services/option_scoring.py backend/tests/services/test_option_scoring.py
git commit -m "feat(services): add option scoring algorithm with weighted factors"
```

---

## Phase 3: Four Options Skill

### Task 5: Create Four Options Skill

**Files:**
- Create: `backend/src/skills/report-generation/four_options.py`
- Test: `backend/tests/skills/test_four_options.py`

**Step 1: Write the failing test**

Create `backend/tests/skills/test_four_options.py`:

```python
"""Tests for FourOptionsSkill."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.skills.report_generation.four_options import FourOptionsSkill
from src.skills.base import SkillContext
from src.models.user_profile import (
    UserProfile,
    CapabilityLevel,
    ImplementationPreference,
    BudgetTier,
)


class TestFourOptionsSkill:
    """Test FourOptionsSkill."""

    @pytest.fixture
    def skill(self):
        """Create skill instance."""
        return FourOptionsSkill()

    @pytest.fixture
    def mock_context(self):
        """Create mock skill context."""
        context = MagicMock(spec=SkillContext)
        context.finding = {
            "id": "finding-001",
            "title": "Automate appointment reminders",
            "description": "Send automatic reminders before appointments",
            "category": "efficiency",
        }
        context.user_profile = UserProfile(
            capability=CapabilityLevel.AUTOMATION_USER,
            preference=ImplementationPreference.CONNECT,
            budget=BudgetTier.MODERATE,
        )
        context.vendors = [
            {"slug": "calendly", "name": "Calendly", "monthly_price": 12},
        ]
        context.industry = "consulting"
        return context

    def test_skill_metadata(self, skill):
        """Test skill has correct metadata."""
        assert skill.name == "four-options"
        assert skill.requires_llm is True

    @pytest.mark.asyncio
    async def test_build_prompt_includes_user_profile(self, skill, mock_context):
        """Test prompt includes user profile context."""
        prompt = skill._build_prompt(mock_context)

        assert "automation_user" in prompt.lower() or "automation user" in prompt.lower()
        assert "connect" in prompt.lower()
        assert "moderate" in prompt.lower()

    @pytest.mark.asyncio
    async def test_build_prompt_includes_finding(self, skill, mock_context):
        """Test prompt includes finding details."""
        prompt = skill._build_prompt(mock_context)

        assert "appointment reminders" in prompt.lower()
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/skills/test_four_options.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `backend/src/skills/report-generation/four_options.py`:

```python
"""
Four Options Skill

Generates personalized recommendations in 4-option format:
- BUY: Pre-built SaaS (turnkey)
- CONNECT: Integrate existing tools (Make/Zapier)
- BUILD: Custom solution (AI coding tools)
- HIRE: Agency/freelancer

Uses weighted scoring based on user profile:
- Capability (30%)
- Preference (20%)
- Budget (20%)
- Time (15%)
- Value (15%)
"""

import json
import logging
from typing import Dict, Any, List, Optional

from src.skills.base import LLMSkill, SkillContext, SkillError
from src.models.user_profile import UserProfile, CapabilityLevel
from src.models.four_options import (
    OptionType,
    OptionScore,
    BuyOption,
    ConnectOption,
    BuildOption,
    HireOption,
    FourOptionRecommendation,
    CostEstimate,
)
from src.services.option_scoring import get_recommendations, score_option

logger = logging.getLogger(__name__)


class FourOptionsSkill(LLMSkill[Dict[str, Any]]):
    """
    Generate Four Options recommendations for findings.

    Creates personalized BUY/CONNECT/BUILD/HIRE options
    with weighted scoring based on user profile.
    """

    name = "four-options"
    description = "Generate personalized 4-option recommendations"
    version = "1.0.0"

    requires_llm = True
    requires_knowledge = True

    def _build_prompt(self, context: SkillContext) -> str:
        """Build LLM prompt with user profile and finding."""
        finding = context.finding
        profile: UserProfile = context.user_profile
        vendors = context.vendors or []
        industry = context.industry or "general"

        # Format vendor context
        vendor_context = ""
        if vendors:
            vendor_list = "\n".join([
                f"- {v.get('name', 'Unknown')}: ${v.get('monthly_price', 'N/A')}/mo"
                for v in vendors[:10]
            ])
            vendor_context = f"\n\nRELEVANT VENDORS:\n{vendor_list}"

        return f"""Generate a 4-option recommendation for this finding.

FINDING:
- Title: {finding.get('title', '')}
- Description: {finding.get('description', '')}
- Category: {finding.get('category', '')}

USER PROFILE:
- Technical Capability: {profile.capability.value}
- Implementation Preference: {profile.preference.value}
- Budget Tier: {profile.budget.value}
- Urgency: {profile.urgency.value if profile.urgency else 'not specified'}
- Industry: {industry}
- Existing Stack API-Ready: {profile.existing_stack_api_ready}
{vendor_context}

SCORING CONTEXT:
The user's profile determines which options are viable:
- Capability={profile.capability.value}: {'Can handle any option' if profile.capability in [CapabilityLevel.AI_CODER, CapabilityLevel.HAS_DEVELOPERS] else 'Limited to simpler options'}
- Preference={profile.preference.value}: User prefers {profile.preference.value.upper()} approach
- Budget={profile.budget.value}: {'Can afford all options' if profile.budget.value in ['comfortable', 'high'] else 'Budget constrained'}

Generate all 4 options with realistic details:

1. BUY: A specific SaaS product that solves this
   - Use real vendor from list if applicable
   - Include actual pricing
   - Setup time should be realistic (hours to days)

2. CONNECT: How to integrate their existing tools
   - Specify Make, n8n, or Zapier
   - Which tools would be connected
   - Estimated setup hours
   - Only viable if they have API-ready tools

3. BUILD: Custom solution with AI coding tools
   - Recommended tech stack
   - Realistic cost and time estimates
   - Skills needed
   - Whether AI coding tools (Cursor, Claude Code) make this achievable

4. HIRE: Agency/freelancer option
   - Type: Agency, Freelancer, or Consultant
   - Realistic cost range
   - Timeline
   - Where to find (Upwork, Toptal, etc.)

For each option include:
- 2-3 pros specific to this user's situation
- 1-2 cons specific to this user's situation
- Cost estimate (upfront + monthly)
- Time to value

OUTPUT FORMAT (JSON):
{{
    "buy": {{
        "vendor_slug": "calendly",
        "vendor_name": "Calendly",
        "price": "12/mo",
        "setup_time": "30 minutes",
        "pros": ["..."],
        "cons": ["..."],
        "year_one_cost": 144
    }},
    "connect": {{
        "integration_platform": "Make",
        "connects_to": ["HubSpot", "Gmail"],
        "estimated_hours": 4,
        "complexity": "low",
        "pros": ["..."],
        "cons": ["..."],
        "year_one_cost": 0
    }},
    "build": {{
        "recommended_stack": ["Claude Code", "Supabase", "Vercel"],
        "estimated_cost": "2K-5K",
        "estimated_hours": "20-40",
        "skills_needed": ["Python or TypeScript"],
        "ai_coding_viable": true,
        "approach": "Build custom reminder system...",
        "pros": ["..."],
        "cons": ["..."],
        "year_one_cost": 3000
    }},
    "hire": {{
        "service_type": "Freelancer",
        "estimated_cost": "500-2K",
        "estimated_timeline": "1-2 weeks",
        "where_to_find": ["Upwork", "Fiverr"],
        "pros": ["..."],
        "cons": ["..."],
        "year_one_cost": 1000
    }}
}}

IMPORTANT:
- Use REAL vendors with REAL pricing
- Be specific about what gets connected/built
- Pros/cons must reference user's specific situation
- If an option isn't viable for this user, still include it but note why in cons
"""

    def _build_system_prompt(self) -> str:
        """System prompt for consistent output."""
        return """You are a technical consultant generating implementation options.

RULES:
- Use ONLY real vendors and real pricing (2024-2025 data)
- Be specific, not vague - name actual tools and platforms
- Pros/cons must be specific to THIS user's profile
- Never use buzzwords: seamless, robust, scalable, leverage, unlock
- All costs in EUR
- Be honest about limitations and requirements
- Output valid JSON only"""

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Generate 4-option recommendation with scoring.

        1. Call LLM to generate option details
        2. Calculate weighted scores based on user profile
        3. Determine recommended option
        4. Return complete FourOptionRecommendation
        """
        # Get LLM-generated options
        prompt = self._build_prompt(context)
        system = self._build_system_prompt()

        try:
            response = await self._call_llm(prompt, system_prompt=system)
            options_data = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise SkillError(f"Invalid JSON from LLM: {e}")

        # Build option models
        buy = BuyOption(
            vendor_slug=options_data["buy"].get("vendor_slug", "unknown"),
            vendor_name=options_data["buy"].get("vendor_name", "Unknown"),
            price=options_data["buy"].get("price", "N/A"),
            setup_time=options_data["buy"].get("setup_time", "Unknown"),
            pros=options_data["buy"].get("pros", []),
            cons=options_data["buy"].get("cons", []),
            cost=CostEstimate(
                year_one_total=options_data["buy"].get("year_one_cost", 0)
            ),
        )

        connect = ConnectOption(
            integration_platform=options_data["connect"].get("integration_platform", "Make"),
            connects_to=options_data["connect"].get("connects_to", []),
            estimated_hours=options_data["connect"].get("estimated_hours", 4),
            complexity=options_data["connect"].get("complexity", "medium"),
            pros=options_data["connect"].get("pros", []),
            cons=options_data["connect"].get("cons", []),
            cost=CostEstimate(
                year_one_total=options_data["connect"].get("year_one_cost", 0)
            ),
        )

        build = BuildOption(
            recommended_stack=options_data["build"].get("recommended_stack", []),
            estimated_cost=options_data["build"].get("estimated_cost", "N/A"),
            estimated_hours=options_data["build"].get("estimated_hours", "N/A"),
            skills_needed=options_data["build"].get("skills_needed", []),
            ai_coding_viable=options_data["build"].get("ai_coding_viable", True),
            approach=options_data["build"].get("approach", ""),
            pros=options_data["build"].get("pros", []),
            cons=options_data["build"].get("cons", []),
            cost=CostEstimate(
                year_one_total=options_data["build"].get("year_one_cost", 0)
            ),
        )

        hire = HireOption(
            service_type=options_data["hire"].get("service_type", "Freelancer"),
            estimated_cost=options_data["hire"].get("estimated_cost", "N/A"),
            estimated_timeline=options_data["hire"].get("estimated_timeline", "N/A"),
            where_to_find=options_data["hire"].get("where_to_find", []),
            pros=options_data["hire"].get("pros", []),
            cons=options_data["hire"].get("cons", []),
            cost=CostEstimate(
                year_one_total=options_data["hire"].get("year_one_cost", 0)
            ),
        )

        # Calculate scores
        profile: UserProfile = context.user_profile
        option_costs = {
            OptionType.BUY: buy.cost,
            OptionType.CONNECT: connect.cost,
            OptionType.BUILD: build.cost,
            OptionType.HIRE: hire.cost,
        }
        option_times = {
            OptionType.BUY: buy.setup_time,
            OptionType.CONNECT: f"{connect.estimated_hours} hours",
            OptionType.BUILD: build.estimated_hours,
            OptionType.HIRE: hire.estimated_timeline,
        }

        scores = get_recommendations(profile, option_costs, option_times)
        recommended = scores[0].option if scores else OptionType.BUY

        # Check for no good match
        no_good_match = all(s.score < 50 for s in scores)
        fallback_message = None
        if no_good_match:
            fallback_message = self._generate_fallback_message(scores, profile)

        # Build recommendation reasoning
        top_score = scores[0] if scores else None
        reasoning = self._build_reasoning(top_score, profile) if top_score else ""

        return FourOptionRecommendation(
            finding_id=context.finding.get("id", ""),
            finding_title=context.finding.get("title", ""),
            buy=buy,
            connect=connect,
            build=build,
            hire=hire,
            scores=scores,
            recommended=recommended,
            recommendation_reasoning=reasoning,
            no_good_match=no_good_match,
            fallback_message=fallback_message,
        ).model_dump()

    def _build_reasoning(
        self,
        top_score: OptionScore,
        profile: UserProfile
    ) -> str:
        """Build recommendation reasoning from score."""
        reasons = top_score.match_reasons[:3]
        if not reasons:
            return f"{top_score.option.value.upper()} is the best match for your profile."
        return f"{top_score.option.value.upper()} is recommended because: {'; '.join(reasons)}."

    def _generate_fallback_message(
        self,
        scores: List[OptionScore],
        profile: UserProfile
    ) -> str:
        """Generate message when no option scores well."""
        # Find the limiting factor
        if profile.budget.value == "low":
            return (
                "Your current budget limits the options for this finding. "
                "Consider prioritizing other findings first, or look for "
                "free/freemium tiers of BUY options."
            )
        if profile.capability == CapabilityLevel.NON_TECHNICAL:
            return (
                "This automation requires technical skills beyond your current level. "
                "Consider the HIRE option if budget allows, or start with simpler "
                "findings to build confidence."
            )
        return (
            "This is a complex automation that doesn't fit standard patterns. "
            "Consider booking a consultation to discuss custom approaches."
        )
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/skills/test_four_options.py -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add backend/src/skills/report-generation/four_options.py backend/tests/skills/test_four_options.py
git commit -m "feat(skills): add FourOptionsSkill with weighted scoring"
```

---

### Task 6: Register Four Options Skill

**Files:**
- Modify: `backend/src/skills/registry.py`

**Step 1: Import and register the skill**

Add to `backend/src/skills/registry.py`:

```python
# Add import at top
from src.skills.report_generation.four_options import FourOptionsSkill

# Add to SKILL_REGISTRY dict
"four-options": FourOptionsSkill,
```

**Step 2: Verify registration**

Run: `cd backend && python -c "from src.skills.registry import get_skill; print(get_skill('four-options'))"`
Expected: `<class 'src.skills.report_generation.four_options.FourOptionsSkill'>`

**Step 3: Commit**

```bash
git add backend/src/skills/registry.py
git commit -m "feat(skills): register four-options skill"
```

---

### Task 7: Integrate with Report Generation

**Files:**
- Modify: `backend/src/services/report_service.py`
- Test: Integration test via API

**Step 1: Update `_generate_recommendations` to use four-options**

In `report_service.py`, find the `_generate_recommendations` method and update:

```python
async def _generate_recommendations(
    self,
    findings: List[Dict[str, Any]],
    context: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Generate recommendations using four-options skill."""
    recommendations = []

    # Build user profile from quiz answers
    from src.models.user_profile import UserProfile
    answers = context.get("answers", {})
    existing_stack = context.get("existing_stack", [])

    # Check if existing stack has API-ready tools
    api_ready = any(
        tool.get("api_score", 0) >= 3.5
        for tool in existing_stack
        if isinstance(tool, dict)
    )

    user_profile = UserProfile.from_quiz_answers(
        answers,
        existing_stack_api_ready=api_ready,
    )

    # Get skill
    skill = get_skill("four-options", client=self.client)

    # Filter findings
    eligible_findings = [
        f for f in findings
        if not f.get("is_not_recommended", False)
    ]

    # Sort by priority (high scores first)
    eligible_findings.sort(
        key=lambda f: (
            f.get("customer_value_score", 0) +
            f.get("business_health_score", 0)
        ),
        reverse=True
    )

    # Generate for top 10 findings
    for finding in eligible_findings[:10]:
        try:
            # Build skill context
            skill_context = SkillContext(
                finding=finding,
                user_profile=user_profile,
                vendors=self._get_relevant_vendors(finding),
                industry=answers.get("industry", ""),
            )

            result = await skill.execute(skill_context)
            recommendations.append(result)

        except Exception as e:
            logger.error(f"Failed to generate recommendation for {finding.get('id')}: {e}")
            # Fall back to three-options if four-options fails
            try:
                fallback_skill = get_skill("three-options", client=self.client)
                result = await fallback_skill.execute(skill_context)
                recommendations.append(result)
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")

    return recommendations
```

**Step 2: Test via API**

Start server: `cd backend && uvicorn src.main:app --reload --port 8383`
Create a quiz session with the new questions answered
Generate report and verify 4-option format appears

**Step 3: Commit**

```bash
git add backend/src/services/report_service.py
git commit -m "feat(reports): integrate four-options skill into report generation"
```

---

## Phase 4: Frontend Updates

### Task 8: Create FourOptions Component

**Files:**
- Create: `frontend/src/components/report/FourOptions.tsx`
- Modify: `frontend/src/pages/ReportViewer.tsx`

**Step 1: Create the component**

Create `frontend/src/components/report/FourOptions.tsx`:

```tsx
import React from 'react';

interface OptionScore {
  option: 'buy' | 'connect' | 'build' | 'hire';
  score: number;
  match_reasons: string[];
  concern_reasons: string[];
  is_recommended: boolean;
}

interface BuyOption {
  vendor_name: string;
  price: string;
  setup_time: string;
  pros: string[];
  cons: string[];
}

interface ConnectOption {
  integration_platform: string;
  connects_to: string[];
  estimated_hours: number;
  pros: string[];
  cons: string[];
}

interface BuildOption {
  recommended_stack: string[];
  estimated_cost: string;
  estimated_hours: string;
  ai_coding_viable: boolean;
  pros: string[];
  cons: string[];
}

interface HireOption {
  service_type: string;
  estimated_cost: string;
  estimated_timeline: string;
  pros: string[];
  cons: string[];
}

interface FourOptionRecommendation {
  finding_id: string;
  finding_title: string;
  buy: BuyOption;
  connect?: ConnectOption;
  build?: BuildOption;
  hire?: HireOption;
  scores: OptionScore[];
  recommended: 'buy' | 'connect' | 'build' | 'hire';
  recommendation_reasoning: string;
  no_good_match: boolean;
  fallback_message?: string;
}

interface FourOptionsProps {
  recommendation: FourOptionRecommendation;
}

const OPTION_ICONS = {
  buy: '🛒',
  connect: '🔗',
  build: '🏗️',
  hire: '👥',
};

const OPTION_LABELS = {
  buy: 'BUY',
  connect: 'CONNECT',
  build: 'BUILD',
  hire: 'HIRE',
};

export const FourOptions: React.FC<FourOptionsProps> = ({ recommendation }) => {
  const { scores, recommended, buy, connect, build, hire } = recommendation;

  // Sort scores by value descending
  const sortedScores = [...scores].sort((a, b) => b.score - a.score);
  const topScore = sortedScores[0];

  return (
    <div className="four-options">
      {/* Recommended Option - Prominent */}
      <div className="recommended-option">
        <div className="option-header">
          <span className="option-icon">{OPTION_ICONS[recommended]}</span>
          <span className="option-label">{OPTION_LABELS[recommended]}</span>
          <span className="match-score">{topScore?.score}% MATCH</span>
        </div>

        {/* Option Details */}
        {recommended === 'buy' && buy && (
          <div className="option-details">
            <h4>{buy.vendor_name}</h4>
            <p className="price">{buy.price}</p>
            <p className="setup">Setup: {buy.setup_time}</p>
          </div>
        )}

        {recommended === 'connect' && connect && (
          <div className="option-details">
            <h4>{connect.integration_platform}</h4>
            <p>Connects: {connect.connects_to.join(', ')}</p>
            <p>Setup: ~{connect.estimated_hours} hours</p>
          </div>
        )}

        {recommended === 'build' && build && (
          <div className="option-details">
            <h4>Custom Solution</h4>
            <p>Stack: {build.recommended_stack.join(', ')}</p>
            <p>Cost: €{build.estimated_cost}</p>
            <p>Time: {build.estimated_hours}</p>
          </div>
        )}

        {recommended === 'hire' && hire && (
          <div className="option-details">
            <h4>{hire.service_type}</h4>
            <p>Cost: €{hire.estimated_cost}</p>
            <p>Timeline: {hire.estimated_timeline}</p>
          </div>
        )}

        {/* Match Reasons */}
        <div className="match-reasons">
          <h5>Why this fits you:</h5>
          <ul>
            {topScore?.match_reasons.map((reason, i) => (
              <li key={i}>✓ {reason}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* Comparison Table */}
      <div className="comparison-table">
        <h4>All Options</h4>
        <table>
          <thead>
            <tr>
              <th>Option</th>
              <th>Match</th>
              <th>Cost</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {sortedScores.map((score) => (
              <tr
                key={score.option}
                className={score.is_recommended ? 'recommended' : ''}
              >
                <td>
                  {OPTION_ICONS[score.option]} {OPTION_LABELS[score.option]}
                </td>
                <td>{score.score}%</td>
                <td>
                  {score.option === 'buy' && buy?.price}
                  {score.option === 'connect' && '€0'}
                  {score.option === 'build' && build && `€${build.estimated_cost}`}
                  {score.option === 'hire' && hire && `€${hire.estimated_cost}`}
                </td>
                <td>
                  {score.option === 'buy' && buy?.setup_time}
                  {score.option === 'connect' && connect && `${connect.estimated_hours}h`}
                  {score.option === 'build' && build?.estimated_hours}
                  {score.option === 'hire' && hire?.estimated_timeline}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Fallback Message */}
      {recommendation.no_good_match && recommendation.fallback_message && (
        <div className="fallback-message">
          <p>⚠️ {recommendation.fallback_message}</p>
        </div>
      )}
    </div>
  );
};

export default FourOptions;
```

**Step 2: Add styles**

Add to appropriate CSS file or use Tailwind classes.

**Step 3: Integrate into ReportViewer**

In `ReportViewer.tsx`, import and use the new component:

```tsx
import { FourOptions } from '../components/report/FourOptions';

// In the recommendations section, replace ThreeOptions with FourOptions
{recommendations.map((rec) => (
  <FourOptions key={rec.finding_id} recommendation={rec} />
))}
```

**Step 4: Commit**

```bash
git add frontend/src/components/report/FourOptions.tsx frontend/src/pages/ReportViewer.tsx
git commit -m "feat(frontend): add FourOptions component for recommendations"
```

---

## Final Verification

### Task 9: End-to-End Test

**Step 1: Start services**

```bash
# Terminal 1
cd backend && uvicorn src.main:app --reload --port 8383

# Terminal 2
cd frontend && npm run dev
```

**Step 2: Complete quiz flow**

1. Go to `http://localhost:5174/quiz`
2. Answer all questions including new implementation preference questions
3. Complete payment (test mode)
4. View report

**Step 3: Verify**

- [ ] New questions appear in quiz
- [ ] Report shows 4 options with match percentages
- [ ] Recommended option is highlighted
- [ ] Match reasons are specific to user profile
- [ ] Comparison table shows all options

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete 4-option recommendation system (Phase 1+2)"
```

---

## Summary

| Task | Files | Tests |
|------|-------|-------|
| 1. Quiz Questions | `questionnaire.py` | Manual |
| 2. UserProfile Model | `user_profile.py` | 4 tests |
| 3. Four Option Models | `four_options.py` | 3 tests |
| 4. Scoring Algorithm | `option_scoring.py` | 8 tests |
| 5. Four Options Skill | `four_options.py` | 3 tests |
| 6. Register Skill | `registry.py` | Manual |
| 7. Report Integration | `report_service.py` | Integration |
| 8. Frontend Component | `FourOptions.tsx` | Manual |
| 9. E2E Verification | - | Manual |

**Total: 9 tasks, 18+ automated tests**
