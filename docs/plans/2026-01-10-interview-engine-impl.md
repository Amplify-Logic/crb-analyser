# SOTA Interview Engine Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform the voice interview from scripted Q&A into an adaptive conversation with signal detection, dynamic follow-ups, and warm expert acknowledgments.

**Architecture:** 3 anchor questions (Problem → Process → Priority) with signal-based follow-ups between them. Backend engine decides next question; frontend becomes thin display layer. LLM generates acknowledgments for anchor questions only.

**Tech Stack:** FastAPI, Pydantic, Anthropic Claude API, existing skill framework (`BaseSkill`, `LLMSkill`, `SyncSkill`)

---

## Phase 1: Data Layer

### Task 1: Create Follow-up Question Bank

**Files:**
- Create: `backend/src/expertise/data/interview/follow_ups.json`

**Step 1: Create directory and JSON file**

```json
{
  "signals": {
    "pain_intensity": {
      "patterns": ["nightmare", "killing us", "hours every day", "hate", "worst", "impossible", "drowning"],
      "follow_ups": [
        "That sounds really frustrating. Can you give me a recent example?",
        "When that happens, what's the ripple effect on your team?",
        "How long has this been going on?"
      ]
    },
    "manual_work": {
      "patterns": ["spreadsheet", "excel", "by hand", "copy paste", "manually", "paper", "write it down", "type it in"],
      "follow_ups": [
        "How long has it been that way? Has anyone tried to fix it before?",
        "Who on your team spends the most time on that?",
        "What would happen if that person was sick for a week?"
      ]
    },
    "customer_impact": {
      "patterns": ["clients complain", "lose customers", "reputation", "reviews", "angry", "waiting", "callback"],
      "follow_ups": [
        "When was the last time that actually cost you business?",
        "How do customers usually find out about those issues?",
        "What do you tell customers when that happens?"
      ]
    },
    "growth_blocker": {
      "patterns": ["can't scale", "hire more", "keeping up", "capacity", "bottleneck", "can't grow", "maxed out"],
      "follow_ups": [
        "What breaks first when you get busy?",
        "If you doubled your business tomorrow, what would fail?",
        "How many more jobs could you handle if this wasn't an issue?"
      ]
    },
    "tech_frustration": {
      "patterns": ["doesn't integrate", "old system", "clunky", "doesn't talk to", "manual entry", "two systems"],
      "follow_ups": [
        "What else does that need to talk to?",
        "How did you end up with that setup?",
        "What's the workaround your team uses?"
      ]
    },
    "vague_answer": {
      "patterns": [],
      "min_words": 5,
      "follow_ups": [
        "Let me ask that differently - what did you do yesterday that felt like a waste of time?",
        "Can you walk me through a specific example from the last week?",
        "What would your team say is the biggest headache?"
      ]
    }
  },
  "anchor_questions": {
    "problem": "What's the one thing in your business that costs you the most time or money right now?",
    "process": "Walk me through how that works today - what happens step by step?",
    "priority": "If we could fix that in the next 90 days, what would that be worth to your business?"
  }
}
```

**Step 2: Verify file is valid JSON**

Run: `python -c "import json; json.load(open('backend/src/expertise/data/interview/follow_ups.json'))"`
Expected: No output (success)

**Step 3: Commit**

```bash
git add backend/src/expertise/data/interview/follow_ups.json
git commit -m "feat(interview): add follow-up question bank with signal patterns"
```

---

### Task 2: Add Industry Interview Insights

**Files:**
- Modify: `backend/src/expertise/data/industries/dental.json`
- Modify: `backend/src/expertise/data/industries/plumbing.json` (if exists, else create)

**Step 1: Add interview_insights to dental.json**

Add this field to the JSON:

```json
{
  "interview_insights": {
    "common_pains": [
      "Insurance billing is the hidden time-killer in every practice I talk to",
      "Patient no-shows cost practices $200+ per slot",
      "Staff spend hours chasing down insurance pre-authorizations"
    ],
    "pain_vocabulary": ["insurance", "billing", "no-show", "scheduling", "pre-auth", "claims", "patients", "hygienist"],
    "process_hooks": {
      "scheduling": "Most practices I talk to lose 10-15 hours a week just on scheduling back-and-forth",
      "billing": "Insurance billing usually takes 2-3 touches per claim before it's resolved",
      "patient_communication": "Patient communication is usually scattered across phone, text, email, and portal"
    }
  }
}
```

**Step 2: Verify JSON is valid**

Run: `python -c "import json; json.load(open('backend/src/expertise/data/industries/dental.json'))"`
Expected: No output (success)

**Step 3: Commit**

```bash
git add backend/src/expertise/data/industries/dental.json
git commit -m "feat(interview): add dental industry interview insights"
```

---

## Phase 2: Interview Skills

### Task 3: Create Interview Signal Detector Skill

**Files:**
- Create: `backend/src/skills/interview/interview_signal_detector.py`
- Create: `backend/tests/skills/interview/test_interview_signal_detector.py`

**Step 1: Write the failing test**

```python
# backend/tests/skills/interview/test_interview_signal_detector.py
"""Tests for InterviewSignalDetectorSkill."""

import pytest
from src.skills.interview.interview_signal_detector import InterviewSignalDetectorSkill
from src.skills.base import SkillContext


class TestInterviewSignalDetector:
    """Test signal detection from interview answers."""

    def setup_method(self):
        self.skill = InterviewSignalDetectorSkill()

    @pytest.mark.asyncio
    async def test_detects_pain_intensity(self):
        """Should detect pain intensity signals."""
        context = SkillContext(
            industry="plumbing",
            metadata={"answer": "Scheduling is a nightmare, we're constantly double-booked"}
        )
        result = await self.skill.run(context)

        assert result.success
        assert "pain_intensity" in result.data["signals_detected"]

    @pytest.mark.asyncio
    async def test_detects_manual_work(self):
        """Should detect manual work signals."""
        context = SkillContext(
            industry="dental",
            metadata={"answer": "We track everything in spreadsheets and copy paste into the billing system"}
        )
        result = await self.skill.run(context)

        assert result.success
        assert "manual_work" in result.data["signals_detected"]

    @pytest.mark.asyncio
    async def test_detects_vague_answer(self):
        """Should detect vague/short answers."""
        context = SkillContext(
            industry="construction",
            metadata={"answer": "It's fine"}
        )
        result = await self.skill.run(context)

        assert result.success
        assert "vague_answer" in result.data["signals_detected"]

    @pytest.mark.asyncio
    async def test_returns_follow_up_suggestions(self):
        """Should return follow-up question suggestions."""
        context = SkillContext(
            industry="plumbing",
            metadata={"answer": "We're drowning in paperwork"}
        )
        result = await self.skill.run(context)

        assert result.success
        assert len(result.data["suggested_follow_ups"]) > 0

    @pytest.mark.asyncio
    async def test_multiple_signals(self):
        """Should detect multiple signals in one answer."""
        context = SkillContext(
            industry="dental",
            metadata={"answer": "The billing is a nightmare and we do it all in spreadsheets manually"}
        )
        result = await self.skill.run(context)

        assert result.success
        signals = result.data["signals_detected"]
        assert "pain_intensity" in signals
        assert "manual_work" in signals
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/skills/interview/test_interview_signal_detector.py -v`
Expected: FAIL with "ModuleNotFoundError" or "ImportError"

**Step 3: Create the __init__.py if needed**

```bash
mkdir -p backend/tests/skills/interview
touch backend/tests/skills/interview/__init__.py
```

**Step 4: Write minimal implementation**

```python
# backend/src/skills/interview/interview_signal_detector.py
"""
Interview Signal Detector Skill

Detects signals in user answers to determine:
- Pain intensity (frustration level)
- Manual work (automation opportunities)
- Customer impact (urgency)
- Growth blockers (scalability issues)
- Tech frustration (integration needs)
- Vague answers (need to probe deeper)

Returns detected signals and suggested follow-up questions.
"""

import json
import os
from typing import Any, Dict, List

from src.skills.base import SyncSkill, SkillContext


class InterviewSignalDetectorSkill(SyncSkill[Dict[str, Any]]):
    """
    Detect signals from interview answers to guide follow-up questions.
    """

    name = "interview-signal-detector"
    description = "Detect signals in interview answers for adaptive follow-ups"
    version = "1.0.0"

    requires_llm = False
    requires_expertise = False

    def __init__(self):
        super().__init__()
        self._follow_ups = self._load_follow_ups()

    def _load_follow_ups(self) -> Dict[str, Any]:
        """Load follow-up question bank."""
        path = os.path.join(
            os.path.dirname(__file__),
            "../../expertise/data/interview/follow_ups.json"
        )
        try:
            with open(path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # Return minimal default if file not found
            return {"signals": {}, "anchor_questions": {}}

    def execute_sync(self, context: SkillContext) -> Dict[str, Any]:
        """
        Detect signals in the given answer.

        Args:
            context: SkillContext with metadata containing:
                - answer: The user's answer text
                - current_topic: Optional topic being discussed

        Returns:
            Dict with:
                - signals_detected: List of signal names
                - signal_details: Dict of signal -> confidence
                - suggested_follow_ups: List of follow-up questions
                - should_probe_deeper: bool
        """
        answer = context.metadata.get("answer", "").lower()
        signals_config = self._follow_ups.get("signals", {})

        detected_signals: List[str] = []
        signal_details: Dict[str, Dict[str, Any]] = {}
        suggested_follow_ups: List[str] = []

        # Check each signal type
        for signal_name, config in signals_config.items():
            patterns = config.get("patterns", [])

            # Special handling for vague_answer (based on length)
            if signal_name == "vague_answer":
                min_words = config.get("min_words", 5)
                word_count = len(answer.split())
                if word_count < min_words:
                    detected_signals.append(signal_name)
                    signal_details[signal_name] = {
                        "reason": f"Short answer ({word_count} words)",
                        "confidence": 0.9
                    }
                    suggested_follow_ups.extend(config.get("follow_ups", [])[:1])
                continue

            # Pattern matching for other signals
            matched_patterns = [p for p in patterns if p in answer]
            if matched_patterns:
                detected_signals.append(signal_name)
                signal_details[signal_name] = {
                    "matched_patterns": matched_patterns,
                    "confidence": min(0.5 + 0.2 * len(matched_patterns), 1.0)
                }
                # Add one follow-up from this signal's bank
                follow_ups = config.get("follow_ups", [])
                if follow_ups:
                    suggested_follow_ups.append(follow_ups[0])

        # Determine if we should probe deeper
        should_probe = (
            "vague_answer" in detected_signals or
            len(detected_signals) == 0
        )

        return {
            "signals_detected": detected_signals,
            "signal_details": signal_details,
            "suggested_follow_ups": suggested_follow_ups[:2],  # Max 2 suggestions
            "should_probe_deeper": should_probe,
            "answer_word_count": len(answer.split())
        }
```

**Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/skills/interview/test_interview_signal_detector.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add backend/src/skills/interview/interview_signal_detector.py
git add backend/tests/skills/interview/
git commit -m "feat(interview): add signal detector skill with TDD"
```

---

### Task 4: Create Acknowledgment Generator Skill

**Files:**
- Create: `backend/src/skills/interview/acknowledgment_generator.py`
- Create: `backend/tests/skills/interview/test_acknowledgment_generator.py`

**Step 1: Write the failing test**

```python
# backend/tests/skills/interview/test_acknowledgment_generator.py
"""Tests for AcknowledgmentGeneratorSkill."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from src.skills.interview.acknowledgment_generator import AcknowledgmentGeneratorSkill
from src.skills.base import SkillContext


class TestAcknowledgmentGenerator:
    """Test warm expert acknowledgment generation."""

    def setup_method(self):
        # Create mock Anthropic client
        self.mock_client = MagicMock()
        self.skill = AcknowledgmentGeneratorSkill(client=self.mock_client)

    @pytest.mark.asyncio
    async def test_generates_acknowledgment(self):
        """Should generate acknowledgment using LLM."""
        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Scheduling in trades is brutal - one emergency throws off everything.")]
        self.mock_client.messages.create.return_value = mock_response

        context = SkillContext(
            industry="plumbing",
            company_name="Mount Eden Plumbing",
            metadata={
                "answer": "Scheduling is chaos, we're always double-booked",
                "signals_detected": ["pain_intensity"],
                "next_question": "Walk me through how that works today?"
            }
        )
        result = await self.skill.run(context)

        assert result.success
        assert "acknowledgment" in result.data
        assert len(result.data["acknowledgment"]) > 0

    @pytest.mark.asyncio
    async def test_includes_industry_context(self):
        """Should include industry in the prompt."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Insurance billing is the hidden time-killer.")]
        self.mock_client.messages.create.return_value = mock_response

        context = SkillContext(
            industry="dental",
            company_name="Smile Dental",
            metadata={
                "answer": "Insurance claims take forever",
                "signals_detected": ["pain_intensity"],
                "next_question": "How many hours a week?"
            }
        )
        await self.skill.run(context)

        # Verify the prompt included the industry
        call_args = self.mock_client.messages.create.call_args
        prompt = call_args.kwargs["messages"][0]["content"]
        assert "dental" in prompt.lower()

    @pytest.mark.asyncio
    async def test_fallback_on_error(self):
        """Should return fallback acknowledgment on LLM error."""
        self.mock_client.messages.create.side_effect = Exception("API Error")

        context = SkillContext(
            industry="construction",
            metadata={
                "answer": "Quotes take too long",
                "signals_detected": ["pain_intensity"],
                "next_question": "Walk me through the process?"
            }
        )
        result = await self.skill.run(context)

        assert result.success
        assert "acknowledgment" in result.data
        # Should have a fallback acknowledgment
        assert "construction" in result.data["acknowledgment"].lower() or len(result.data["acknowledgment"]) > 0
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/skills/interview/test_acknowledgment_generator.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# backend/src/skills/interview/acknowledgment_generator.py
"""
Acknowledgment Generator Skill

Generates warm expert acknowledgments that:
1. Name the user's specific pain (use their words)
2. Add industry insight showing expertise
3. Bridge naturally to the next question

Uses LLM for anchor questions, has fallback for errors.
"""

import json
import os
import logging
from typing import Any, Dict, Optional

from src.skills.base import LLMSkill, SkillContext, SkillError

logger = logging.getLogger(__name__)


ACKNOWLEDGMENT_SYSTEM_PROMPT = """You are a warm, experienced business consultant conducting a voice interview.

Your job is to generate a brief acknowledgment (1-2 sentences max) that:
1. Names their specific pain using their actual words
2. Adds a brief industry insight showing you've seen this before
3. Feels conversational and warm, not corporate

AVOID these phrases:
- "That's helpful"
- "Thanks for sharing"
- "I understand"
- "Great question"

USE phrases like:
- "Ah, [their problem]..."
- "That's really common in [industry]..."
- "I see this constantly..."
- "[Problem] in [industry] usually means..."

Keep it to ONE breath - not a paragraph. This will be spoken aloud."""


class AcknowledgmentGeneratorSkill(LLMSkill[Dict[str, Any]]):
    """
    Generate warm expert acknowledgments for interview answers.
    """

    name = "acknowledgment-generator"
    description = "Generate warm expert acknowledgments for interview answers"
    version = "1.0.0"

    requires_llm = True
    default_model = "claude-haiku-4-5-20251001"  # Fast model for quick responses
    default_max_tokens = 150

    def __init__(self, client=None):
        super().__init__(client)
        self._industry_insights = self._load_industry_insights()

    def _load_industry_insights(self) -> Dict[str, Any]:
        """Load industry-specific insights for acknowledgments."""
        insights = {}
        industries_path = os.path.join(
            os.path.dirname(__file__),
            "../../expertise/data/industries"
        )

        if os.path.exists(industries_path):
            for filename in os.listdir(industries_path):
                if filename.endswith(".json"):
                    industry = filename.replace(".json", "")
                    try:
                        with open(os.path.join(industries_path, filename)) as f:
                            data = json.load(f)
                            if "interview_insights" in data:
                                insights[industry] = data["interview_insights"]
                    except Exception as e:
                        logger.warning(f"Failed to load insights for {industry}: {e}")

        return insights

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Generate an acknowledgment for the user's answer.

        Args:
            context: SkillContext with metadata containing:
                - answer: The user's answer
                - signals_detected: List of detected signals
                - next_question: The next question to ask

        Returns:
            Dict with:
                - acknowledgment: The generated acknowledgment
                - used_llm: Whether LLM was used or fallback
        """
        answer = context.metadata.get("answer", "")
        signals = context.metadata.get("signals_detected", [])
        next_question = context.metadata.get("next_question", "")
        industry = context.industry
        company_name = context.company_name or "your company"

        # Get industry-specific insights if available
        industry_insights = self._industry_insights.get(industry, {})
        common_pains = industry_insights.get("common_pains", [])

        # Build the prompt
        prompt = f"""Generate an acknowledgment for this interview answer.

Industry: {industry}
Company: {company_name}
Their answer: "{answer}"
Signals detected: {', '.join(signals) if signals else 'none'}
Next question we'll ask: "{next_question}"

Industry insights to potentially use:
{chr(10).join(f'- {p}' for p in common_pains[:3]) if common_pains else 'No specific insights available'}

Generate a 1-2 sentence acknowledgment that validates their pain and bridges to the next question.
Output ONLY the acknowledgment text, nothing else."""

        try:
            acknowledgment = await self.call_llm(
                prompt=prompt,
                system=ACKNOWLEDGMENT_SYSTEM_PROMPT,
            )
            return {
                "acknowledgment": acknowledgment.strip(),
                "used_llm": True
            }

        except Exception as e:
            logger.warning(f"LLM acknowledgment failed, using fallback: {e}")
            # Fallback acknowledgment
            fallback = self._get_fallback_acknowledgment(industry, signals)
            return {
                "acknowledgment": fallback,
                "used_llm": False,
                "fallback_reason": str(e)
            }

    def _get_fallback_acknowledgment(
        self,
        industry: str,
        signals: list
    ) -> str:
        """Generate a simple fallback acknowledgment."""
        if "pain_intensity" in signals:
            return f"That's a challenge I hear often in {industry}. Let me dig into that a bit more."
        elif "manual_work" in signals:
            return f"Manual processes like that are really common - and usually a great candidate for automation."
        elif "customer_impact" in signals:
            return "Customer experience issues like that can really add up. Let me understand the process better."
        else:
            return "Got it, that's helpful context. Let me ask a follow-up."
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/skills/interview/test_acknowledgment_generator.py -v`
Expected: All tests PASS

**Step 5: Update skills/interview/__init__.py**

```python
# backend/src/skills/interview/__init__.py
"""Interview skills for the voice interview experience."""

from src.skills.interview.interview_signal_detector import InterviewSignalDetectorSkill
from src.skills.interview.acknowledgment_generator import AcknowledgmentGeneratorSkill

__all__ = [
    "InterviewSignalDetectorSkill",
    "AcknowledgmentGeneratorSkill",
]
```

**Step 6: Commit**

```bash
git add backend/src/skills/interview/
git add backend/tests/skills/interview/
git commit -m "feat(interview): add acknowledgment generator skill with LLM"
```

---

## Phase 3: Interview Engine

### Task 5: Create Interview Engine Service

**Files:**
- Create: `backend/src/services/interview_engine.py`
- Create: `backend/tests/services/test_interview_engine.py`

**Step 1: Write the failing test**

```python
# backend/tests/services/test_interview_engine.py
"""Tests for InterviewEngine."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.services.interview_engine import InterviewEngine, InterviewState


class TestInterviewEngine:
    """Test the interview engine orchestration."""

    def setup_method(self):
        self.mock_client = MagicMock()
        self.engine = InterviewEngine(anthropic_client=self.mock_client)

    def test_initial_state(self):
        """Should start at anchor 1 (problem)."""
        state = InterviewState(industry="plumbing", company_name="Test Co")
        assert state.current_anchor == 1
        assert state.questions_asked == 0
        assert state.phase == "anchor"

    def test_get_anchor_question(self):
        """Should return correct anchor question."""
        q1 = self.engine.get_anchor_question(1)
        assert "time or money" in q1.lower()

        q2 = self.engine.get_anchor_question(2)
        assert "step by step" in q2.lower()

        q3 = self.engine.get_anchor_question(3)
        assert "90 days" in q3.lower()

    @pytest.mark.asyncio
    async def test_process_answer_detects_signals(self):
        """Should detect signals in answer."""
        state = InterviewState(industry="plumbing", company_name="Test")

        result = await self.engine.process_answer(
            state=state,
            answer="Scheduling is a nightmare, we do it all by hand"
        )

        assert "pain_intensity" in result.signals_detected or "manual_work" in result.signals_detected

    @pytest.mark.asyncio
    async def test_decides_follow_up_or_next_anchor(self):
        """Should decide whether to follow up or move to next anchor."""
        state = InterviewState(industry="dental", company_name="Test")

        # Short vague answer should trigger follow-up
        result = await self.engine.process_answer(
            state=state,
            answer="It's okay"
        )
        assert result.next_question_type == "follow_up"

    @pytest.mark.asyncio
    async def test_moves_to_next_anchor_on_rich_answer(self):
        """Should move to next anchor on detailed answer."""
        state = InterviewState(industry="plumbing", company_name="Test")
        state.current_anchor = 1
        state.follow_ups_for_current_anchor = 1  # Already asked one follow-up

        # Rich detailed answer
        result = await self.engine.process_answer(
            state=state,
            answer="We spend about 20 hours a week on scheduling. My wife handles calls, writes them on paper, then enters them in Google Calendar, then texts the crew. About 3 jobs a week get messed up."
        )

        # Should move to anchor 2 (process)
        assert result.next_question_type == "anchor"
        assert "step by step" in result.next_question.lower()

    @pytest.mark.asyncio
    async def test_completes_after_anchor_3(self):
        """Should complete interview after anchor 3."""
        state = InterviewState(industry="dental", company_name="Test")
        state.current_anchor = 3
        state.questions_asked = 6

        result = await self.engine.process_answer(
            state=state,
            answer="Probably worth $50K a year if we fixed it"
        )

        assert result.interview_complete == True
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/services/test_interview_engine.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write the implementation**

```python
# backend/src/services/interview_engine.py
"""
Interview Engine Service

Orchestrates the SOTA voice interview experience:
- Manages 3 anchor questions (Problem → Process → Priority)
- Detects signals to decide follow-ups vs next anchor
- Generates warm expert acknowledgments
- Tracks conversation state

Usage:
    engine = InterviewEngine(anthropic_client)
    state = InterviewState(industry="plumbing", company_name="Test Co")
    result = await engine.process_answer(state, "Scheduling is chaos")
"""

import json
import os
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Literal

from src.skills.interview.interview_signal_detector import InterviewSignalDetectorSkill
from src.skills.interview.acknowledgment_generator import AcknowledgmentGeneratorSkill
from src.skills.base import SkillContext

logger = logging.getLogger(__name__)


@dataclass
class InterviewState:
    """Tracks the state of an interview conversation."""

    industry: str
    company_name: str

    # Progress tracking
    current_anchor: int = 1  # 1, 2, or 3
    questions_asked: int = 0
    follow_ups_for_current_anchor: int = 0

    # Conversation data
    answers: List[Dict[str, Any]] = field(default_factory=list)
    all_signals: List[str] = field(default_factory=list)

    # Phase: "anchor" or "follow_up"
    phase: Literal["anchor", "follow_up"] = "anchor"

    # Configuration
    max_follow_ups_per_anchor: int = 2
    max_total_questions: int = 8


@dataclass
class ProcessAnswerResult:
    """Result from processing an answer."""

    # What was detected
    signals_detected: List[str]

    # Response to give
    acknowledgment: str
    next_question: str
    next_question_type: Literal["anchor", "follow_up", "summary"]
    next_topic: Optional[str] = None

    # State updates
    new_anchor: int = 1
    interview_complete: bool = False

    # Debug info
    decision_reason: str = ""


class InterviewEngine:
    """
    Orchestrates the adaptive voice interview.
    """

    def __init__(self, anthropic_client=None):
        self.client = anthropic_client
        self.signal_detector = InterviewSignalDetectorSkill()
        self.ack_generator = AcknowledgmentGeneratorSkill(client=anthropic_client)
        self._follow_ups = self._load_follow_ups()

    def _load_follow_ups(self) -> Dict[str, Any]:
        """Load the follow-up question bank."""
        path = os.path.join(
            os.path.dirname(__file__),
            "../expertise/data/interview/follow_ups.json"
        )
        try:
            with open(path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Follow-up bank not found, using defaults")
            return {
                "anchor_questions": {
                    "problem": "What's the one thing in your business that costs you the most time or money right now?",
                    "process": "Walk me through how that works today - what happens step by step?",
                    "priority": "If we could fix that in the next 90 days, what would that be worth to your business?"
                },
                "signals": {}
            }

    def get_anchor_question(self, anchor_num: int) -> str:
        """Get the anchor question for a given anchor number."""
        anchors = self._follow_ups.get("anchor_questions", {})
        if anchor_num == 1:
            return anchors.get("problem", "What costs you the most time or money?")
        elif anchor_num == 2:
            return anchors.get("process", "Walk me through how that works step by step?")
        elif anchor_num == 3:
            return anchors.get("priority", "What would fixing this be worth to your business?")
        else:
            return "Is there anything else you'd like to add?"

    def get_anchor_topic(self, anchor_num: int) -> str:
        """Get the topic name for an anchor."""
        topics = {1: "Problem", 2: "Process", 3: "Priority"}
        return topics.get(anchor_num, "Summary")

    async def process_answer(
        self,
        state: InterviewState,
        answer: str
    ) -> ProcessAnswerResult:
        """
        Process a user's answer and determine next steps.

        Args:
            state: Current interview state
            answer: The user's answer text

        Returns:
            ProcessAnswerResult with acknowledgment, next question, and state updates
        """
        # Step 1: Detect signals in the answer
        signal_context = SkillContext(
            industry=state.industry,
            metadata={"answer": answer}
        )
        signal_result = await self.signal_detector.run(signal_context)

        signals = signal_result.data.get("signals_detected", [])
        should_probe = signal_result.data.get("should_probe_deeper", False)
        suggested_follow_ups = signal_result.data.get("suggested_follow_ups", [])

        # Update state with detected signals
        state.all_signals.extend(signals)
        state.questions_asked += 1

        # Store the answer
        state.answers.append({
            "anchor": state.current_anchor,
            "question_type": state.phase,
            "answer": answer,
            "signals": signals
        })

        # Step 2: Decide next action
        decision = self._decide_next_action(state, signals, should_probe, suggested_follow_ups)

        # Step 3: Generate acknowledgment (only for anchors, use simpler for follow-ups)
        if state.phase == "anchor" and self.client:
            ack_context = SkillContext(
                industry=state.industry,
                company_name=state.company_name,
                metadata={
                    "answer": answer,
                    "signals_detected": signals,
                    "next_question": decision["next_question"]
                }
            )
            ack_result = await self.ack_generator.run(ack_context)
            acknowledgment = ack_result.data.get("acknowledgment", "Got it.")
        else:
            # Simple acknowledgment for follow-ups
            acknowledgment = self._get_simple_acknowledgment(signals)

        # Step 4: Update state based on decision
        if decision["type"] == "anchor":
            state.current_anchor = decision["new_anchor"]
            state.follow_ups_for_current_anchor = 0
            state.phase = "anchor"
        elif decision["type"] == "follow_up":
            state.follow_ups_for_current_anchor += 1
            state.phase = "follow_up"

        return ProcessAnswerResult(
            signals_detected=signals,
            acknowledgment=acknowledgment,
            next_question=decision["next_question"],
            next_question_type=decision["type"],
            next_topic=decision.get("topic"),
            new_anchor=state.current_anchor,
            interview_complete=decision.get("complete", False),
            decision_reason=decision.get("reason", "")
        )

    def _decide_next_action(
        self,
        state: InterviewState,
        signals: List[str],
        should_probe: bool,
        suggested_follow_ups: List[str]
    ) -> Dict[str, Any]:
        """Decide whether to follow up, move to next anchor, or complete."""

        # Check if we're at max questions
        if state.questions_asked >= state.max_total_questions:
            return {
                "type": "summary",
                "next_question": "Thanks for sharing all that. Is there anything else you'd like to add?",
                "complete": True,
                "reason": "Max questions reached"
            }

        # Check if we've completed anchor 3
        if state.current_anchor == 3 and state.phase == "anchor":
            return {
                "type": "summary",
                "next_question": "Thanks for sharing all that. Is there anything else you'd like to add?",
                "complete": True,
                "reason": "Completed all anchors"
            }

        # Decide: follow-up or next anchor?
        should_follow_up = (
            should_probe and
            state.follow_ups_for_current_anchor < state.max_follow_ups_per_anchor and
            len(suggested_follow_ups) > 0
        )

        if should_follow_up:
            return {
                "type": "follow_up",
                "next_question": suggested_follow_ups[0],
                "topic": self.get_anchor_topic(state.current_anchor),
                "reason": f"Probing deeper on signals: {signals}"
            }
        else:
            # Move to next anchor
            next_anchor = state.current_anchor + 1
            if next_anchor > 3:
                return {
                    "type": "summary",
                    "next_question": "Thanks for sharing all that. Is there anything else you'd like to add?",
                    "complete": True,
                    "reason": "Completed all anchors"
                }
            return {
                "type": "anchor",
                "next_question": self.get_anchor_question(next_anchor),
                "new_anchor": next_anchor,
                "topic": self.get_anchor_topic(next_anchor),
                "reason": f"Moving to anchor {next_anchor}"
            }

    def _get_simple_acknowledgment(self, signals: List[str]) -> str:
        """Get a simple acknowledgment for follow-up questions."""
        if "pain_intensity" in signals:
            return "I can see why that's frustrating."
        elif "manual_work" in signals:
            return "That's a lot of manual work."
        elif "customer_impact" in signals:
            return "That definitely affects the customer experience."
        elif "growth_blocker" in signals:
            return "Growth constraints like that are tough."
        else:
            return "Got it."

    def get_first_question(self, state: InterviewState) -> str:
        """Get the first question to start the interview."""
        return self.get_anchor_question(1)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/services/test_interview_engine.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add backend/src/services/interview_engine.py
git add backend/tests/services/test_interview_engine.py
git commit -m "feat(interview): add interview engine service with state management"
```

---

## Phase 4: API Endpoint

### Task 6: Create Process Answer Endpoint

**Files:**
- Modify: `backend/src/routes/interview.py`
- Create: `backend/tests/routes/test_interview_process.py`

**Step 1: Write the failing test**

```python
# backend/tests/routes/test_interview_process.py
"""Tests for /api/interview/process-answer endpoint."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


class TestProcessAnswerEndpoint:
    """Test the process-answer endpoint."""

    @patch("src.routes.interview.InterviewEngine")
    @patch("src.routes.interview.transcription_service")
    def test_process_answer_success(self, mock_transcription, mock_engine_class):
        """Should process answer and return next question."""
        # Mock transcription
        mock_transcription.transcribe = AsyncMock(return_value="Scheduling is chaos")

        # Mock engine
        mock_engine = MagicMock()
        mock_engine.process_answer = AsyncMock(return_value=MagicMock(
            signals_detected=["pain_intensity"],
            acknowledgment="Scheduling in trades is brutal.",
            next_question="How are you tracking jobs right now?",
            next_question_type="follow_up",
            next_topic="Problem",
            new_anchor=1,
            interview_complete=False
        ))
        mock_engine_class.return_value = mock_engine

        response = client.post(
            "/api/interview/process-answer",
            json={
                "session_id": "test-123",
                "answer_text": "Scheduling is chaos",
                "current_anchor": 1,
                "industry": "plumbing",
                "company_name": "Test Plumbing"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "acknowledgment" in data
        assert "next_question" in data
        assert "signals_detected" in data

    def test_process_answer_missing_fields(self):
        """Should return 422 for missing required fields."""
        response = client.post(
            "/api/interview/process-answer",
            json={"session_id": "test-123"}
        )
        assert response.status_code == 422
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/routes/test_interview_process.py -v`
Expected: FAIL (endpoint doesn't exist yet)

**Step 3: Add the endpoint to interview.py**

Add these models and endpoint to `backend/src/routes/interview.py`:

```python
# Add to imports at top
from src.services.interview_engine import InterviewEngine, InterviewState

# Add these new models after existing models
class ProcessAnswerRequest(BaseModel):
    """Request for processing an interview answer."""
    session_id: str
    answer_text: str
    current_anchor: int = 1
    follow_ups_asked: int = 0
    industry: str
    company_name: Optional[str] = None


class ProcessAnswerResponse(BaseModel):
    """Response from processing an interview answer."""
    transcription: Optional[str] = None
    signals_detected: List[str]
    acknowledgment: str
    next_question: str
    next_question_type: str  # "anchor", "follow_up", or "summary"
    next_topic: Optional[str] = None
    progress: dict
    interview_complete: bool = False


# Add this endpoint
@router.post("/process-answer", response_model=ProcessAnswerResponse)
async def process_interview_answer(request: ProcessAnswerRequest):
    """
    Process an interview answer and return the next question.

    This endpoint:
    1. Detects signals in the answer
    2. Generates a warm expert acknowledgment
    3. Decides: follow-up question or next anchor
    4. Returns everything needed for frontend
    """
    try:
        # Create engine and state
        client = get_anthropic_client()
        engine = InterviewEngine(anthropic_client=client)

        state = InterviewState(
            industry=request.industry,
            company_name=request.company_name or "your company",
            current_anchor=request.current_anchor,
            follow_ups_for_current_anchor=request.follow_ups_asked
        )

        # Process the answer
        result = await engine.process_answer(
            state=state,
            answer=request.answer_text
        )

        return ProcessAnswerResponse(
            signals_detected=result.signals_detected,
            acknowledgment=result.acknowledgment,
            next_question=result.next_question,
            next_question_type=result.next_question_type,
            next_topic=result.next_topic,
            progress={
                "current_anchor": result.new_anchor,
                "questions_asked": state.questions_asked,
                "max_questions": state.max_total_questions
            },
            interview_complete=result.interview_complete
        )

    except Exception as e:
        logger.error(f"Error processing answer: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process answer: {str(e)}"
        )


@router.get("/first-question")
async def get_first_question(industry: str, company_name: Optional[str] = None):
    """Get the first question to start the interview."""
    engine = InterviewEngine()
    state = InterviewState(industry=industry, company_name=company_name or "your company")

    return {
        "question": engine.get_first_question(state),
        "topic": "Problem",
        "anchor": 1
    }
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/routes/test_interview_process.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add backend/src/routes/interview.py
git add backend/tests/routes/test_interview_process.py
git commit -m "feat(interview): add process-answer API endpoint"
```

---

## Phase 5: Frontend Integration

### Task 7: Create Interview API Service

**Files:**
- Create: `frontend/src/services/interviewApi.ts`

**Step 1: Create the API service**

```typescript
// frontend/src/services/interviewApi.ts
/**
 * Interview API Service
 *
 * Handles communication with the SOTA interview engine backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8383'

export interface ProcessAnswerRequest {
  session_id: string
  answer_text: string
  current_anchor: number
  follow_ups_asked: number
  industry: string
  company_name?: string
}

export interface ProcessAnswerResponse {
  signals_detected: string[]
  acknowledgment: string
  next_question: string
  next_question_type: 'anchor' | 'follow_up' | 'summary'
  next_topic?: string
  progress: {
    current_anchor: number
    questions_asked: number
    max_questions: number
  }
  interview_complete: boolean
}

export interface FirstQuestionResponse {
  question: string
  topic: string
  anchor: number
}

/**
 * Process an interview answer and get the next question.
 */
export async function processAnswer(
  request: ProcessAnswerRequest
): Promise<ProcessAnswerResponse> {
  const response = await fetch(`${API_BASE_URL}/api/interview/process-answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || 'Failed to process answer')
  }

  return response.json()
}

/**
 * Get the first question to start the interview.
 */
export async function getFirstQuestion(
  industry: string,
  companyName?: string
): Promise<FirstQuestionResponse> {
  const params = new URLSearchParams({ industry })
  if (companyName) params.append('company_name', companyName)

  const response = await fetch(
    `${API_BASE_URL}/api/interview/first-question?${params}`
  )

  if (!response.ok) {
    throw new Error('Failed to get first question')
  }

  return response.json()
}

/**
 * Transcribe audio and get text.
 */
export async function transcribeAudio(
  audioBlob: Blob,
  sessionId?: string
): Promise<string> {
  const formData = new FormData()
  formData.append('audio', audioBlob, 'recording.webm')
  if (sessionId) formData.append('session_id', sessionId)

  const response = await fetch(`${API_BASE_URL}/api/interview/transcribe`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error('Transcription failed')
  }

  const data = await response.json()
  return data.text
}
```

**Step 2: Commit**

```bash
git add frontend/src/services/interviewApi.ts
git commit -m "feat(interview): add interview API service"
```

---

### Task 8: Refactor VoiceQuizInterview Component

**Files:**
- Modify: `frontend/src/pages/VoiceQuizInterview.tsx`

**Step 1: Update imports**

Add to the imports section:

```typescript
import {
  processAnswer,
  getFirstQuestion,
  transcribeAudio,
  type ProcessAnswerResponse
} from '../services/interviewApi'
```

**Step 2: Update state to use engine-driven flow**

Replace the `questions` state and `generateQuestions` function with engine-driven state:

```typescript
// Replace these state variables:
// const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
// const [questions, setQuestions] = useState<QuizQuestion[]>([])

// With:
const [currentQuestion, setCurrentQuestion] = useState<string>('')
const [currentTopic, setCurrentTopic] = useState<string>('Problem')
const [currentAnchor, setCurrentAnchor] = useState(1)
const [followUpsAsked, setFollowUpsAsked] = useState(0)
const [questionsAsked, setQuestionsAsked] = useState(0)
const [maxQuestions] = useState(8)
const [industry, setIndustry] = useState('')
```

**Step 3: Update startConversation**

```typescript
const startConversation = useCallback(async () => {
  setPhase('conversation')

  try {
    // Get first question from engine
    const { question, topic } = await getFirstQuestion(industry, displayName)
    setCurrentQuestion(question)
    setCurrentTopic(topic)

    // Speak the question
    await speakText(question)
  } catch (error) {
    console.error('Failed to start conversation:', error)
    // Fallback to hardcoded first question
    const fallbackQuestion = "What's the one thing in your business that costs you the most time or money right now?"
    setCurrentQuestion(fallbackQuestion)
    await speakText(fallbackQuestion)
  }
}, [industry, displayName, speakText])
```

**Step 4: Update processUserAnswer**

```typescript
const processUserAnswer = async (text: string) => {
  // Add user message to chat
  const userMessage: Message = {
    id: `user-${Date.now()}`,
    role: 'user',
    content: text,
    timestamp: new Date(),
  }
  setMessages(prev => [...prev, userMessage])
  setIsProcessing(true)

  try {
    // Process through engine
    const result = await processAnswer({
      session_id: sessionId || '',
      answer_text: text,
      current_anchor: currentAnchor,
      follow_ups_asked: followUpsAsked,
      industry,
      company_name: displayName,
    })

    // Update state from engine response
    setCurrentAnchor(result.progress.current_anchor)
    setQuestionsAsked(result.progress.questions_asked)

    if (result.next_question_type === 'follow_up') {
      setFollowUpsAsked(prev => prev + 1)
    } else {
      setFollowUpsAsked(0)
    }

    // Check if complete
    if (result.interview_complete) {
      setPhase('summary')
      const summaryAck = result.acknowledgment
      setMessages(prev => [...prev, {
        id: `ack-${Date.now()}`,
        role: 'assistant',
        content: summaryAck,
        timestamp: new Date(),
      }])
      await speakText(`${summaryAck} Is there anything else you'd like to add?`)
      return
    }

    // Update question and show acknowledgment
    setCurrentQuestion(result.next_question)
    setCurrentTopic(result.next_topic || currentTopic)

    // Add acknowledgment to chat
    setMessages(prev => [...prev, {
      id: `ack-${Date.now()}`,
      role: 'assistant',
      content: result.acknowledgment,
      timestamp: new Date(),
    }])

    // Speak acknowledgment + next question
    await speakText(`${result.acknowledgment} ${result.next_question}`)

  } catch (error) {
    console.error('Error processing answer:', error)
    // Fallback behavior
    setMessages(prev => [...prev, {
      id: `error-${Date.now()}`,
      role: 'assistant',
      content: "Got it. Let me ask another question.",
      timestamp: new Date(),
    }])
  } finally {
    setIsProcessing(false)
  }
}
```

**Step 5: Update progress calculation**

```typescript
const progress = maxQuestions > 0
  ? (questionsAsked / maxQuestions) * 100
  : 0
```

**Step 6: Update question card display**

In the JSX, update the question card:

```tsx
<h2 className="text-2xl font-semibold text-gray-900 leading-relaxed">
  {phase === 'summary'
    ? "Is there anything else you'd like to add about your situation or goals?"
    : currentQuestion}
</h2>
```

**Step 7: Load industry from session storage**

In the useEffect:

```typescript
useEffect(() => {
  const name = sessionStorage.getItem('companyName')
  const profileStr = sessionStorage.getItem('companyProfile')
  const storedIndustry = sessionStorage.getItem('quizIndustry') || 'general'

  if (name) setCompanyName(name)
  setIndustry(storedIndustry)

  // ... rest of profile parsing
}, [])
```

**Step 8: Commit**

```bash
git add frontend/src/pages/VoiceQuizInterview.tsx
git commit -m "refactor(interview): integrate with SOTA interview engine API"
```

---

## Phase 6: Integration Testing

### Task 9: End-to-End Test

**Files:**
- Create: `backend/tests/integration/test_interview_flow.py`

**Step 1: Write integration test**

```python
# backend/tests/integration/test_interview_flow.py
"""Integration tests for the full interview flow."""

import pytest
from unittest.mock import MagicMock, patch
from src.services.interview_engine import InterviewEngine, InterviewState


class TestInterviewFlow:
    """Test complete interview conversation flow."""

    @pytest.mark.asyncio
    async def test_complete_interview_flow(self):
        """Should complete a full 3-anchor interview."""
        # Mock the LLM client for acknowledgments
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="That's a common challenge.")]
        mock_client.messages.create.return_value = mock_response

        engine = InterviewEngine(anthropic_client=mock_client)
        state = InterviewState(
            industry="plumbing",
            company_name="Test Plumbing Co"
        )

        # Simulate conversation
        answers = [
            "Scheduling is a nightmare, we lose jobs every week",  # Anchor 1
            "About 10 hours a week dealing with it",  # Follow-up
            "Customer calls, wife writes it down, enters in calendar, texts the crew",  # Anchor 2
            "Maybe $50K a year if we fixed it",  # Anchor 3
        ]

        for i, answer in enumerate(answers):
            result = await engine.process_answer(state, answer)

            # Verify we got a response
            assert result.acknowledgment
            assert result.next_question

            if i < len(answers) - 1:
                assert not result.interview_complete

        # Final answer should complete
        assert result.interview_complete or state.questions_asked >= state.max_total_questions

    @pytest.mark.asyncio
    async def test_signal_detection_affects_flow(self):
        """Vague answers should trigger follow-ups."""
        engine = InterviewEngine()  # No LLM needed for signal detection
        state = InterviewState(industry="dental", company_name="Test")

        # Vague answer should trigger follow-up
        result = await engine.process_answer(state, "It's fine I guess")

        assert "vague_answer" in result.signals_detected
        assert result.next_question_type == "follow_up"
```

**Step 2: Run integration tests**

Run: `cd backend && pytest tests/integration/test_interview_flow.py -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add backend/tests/integration/
git commit -m "test(interview): add integration tests for interview flow"
```

---

## Summary

**Total tasks:** 9
**Estimated commits:** 9

**What we built:**
1. Follow-up question bank (JSON data)
2. Industry interview insights
3. Signal detector skill (SyncSkill)
4. Acknowledgment generator skill (LLMSkill)
5. Interview engine service
6. Process-answer API endpoint
7. Frontend API service
8. Refactored VoiceQuizInterview component
9. Integration tests

**Key patterns used:**
- TDD: Tests first, then implementation
- Skill framework: Extends existing `BaseSkill`, `LLMSkill`, `SyncSkill`
- State management: `InterviewState` dataclass tracks conversation
- Fallbacks: LLM failures gracefully degrade to template responses
