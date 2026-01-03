# Handoff: Adaptive Quiz System - Phases 1-5 Complete

**Date:** 2026-01-03
**Status:** All phases complete, ready for production testing
**Last updated:** Session 3

---

## Summary

We designed and implemented Phase 1 of a **personalized adaptive quiz system** that replaces the generic 25-question static quiz with a confidence-driven interview that adapts based on research findings.

### The Problem (Before)
- Quiz asked generic questions regardless of what research found
- "How many employees?" even when we already knew from LinkedIn
- No follow-up on interesting answers
- Fixed length (~25 questions) regardless of signal quality

### The Solution (After)
- Quiz adapts based on research gaps
- Weaves confirmations into discovery: "How's HubSpot working for your sales?"
- Deep dives when answers reveal interesting signals
- Ends when confidence thresholds are met (not fixed question count)

---

## What Was Built (Phase 1)

### 1. Models (`backend/src/models/quiz_confidence.py`)

```python
# Core types
ConfidenceCategory  # 8 categories we need confidence in
ConfidenceState     # Tracks scores, facts, gaps per category
AdaptiveQuestion    # Dynamically generated question with metadata
AnswerAnalysis      # Extracted insights from user answer
ExtractedFact       # A fact with value, confidence, source

# Key functions
create_initial_confidence_from_research(profile)  # Initialize from research
update_confidence_from_analysis(state, analysis)  # Update after answer
```

### 2. Confidence Categories & Thresholds

| Category | Threshold | Description |
|----------|-----------|-------------|
| `company_basics` | 80% | Size, industry, business model |
| `tech_stack` | 60% | Tools they use |
| `pain_points` | 80% | Challenges (quiz only) |
| `operations` | 60% | How they work |
| `goals_priorities` | 70% | What they want |
| `quantifiable_metrics` | 50% | Numbers for ROI |
| `industry_context` | 60% | Industry-specific |
| `buying_signals` | 40% | Budget, timeline |

### 3. Quiz Engine (`backend/src/services/quiz_engine.py`)

**AnswerAnalyzer** - Uses Haiku to extract:
- Explicit facts (numbers, tools, processes)
- Pain signals worth exploring
- Quantifiable metrics
- Sentiment and urgency
- Deep dive decisions

**QuestionGenerator** - Uses Sonnet to generate:
- Gap-filling questions (targeting lowest confidence categories)
- Deep dive follow-ups (when signals detected)
- Woven confirmations (confirm research + discover new info)
- Industry-specific questions (from question banks)

### 4. Database Migration (`backend/supabase/migrations/013_adaptive_quiz.sql`)

Added to `quiz_sessions`:
- `quiz_mode` - 'static' or 'adaptive'
- `confidence_state` - JSONB with scores, facts, gaps
- `adaptive_answers` - Array of Q&A with analysis
- `quiz_completed_at` - When thresholds were met
- `interview_data` - Voice interview messages
- `report_id` - Link to generated report

### 5. Tests (`backend/tests/test_quiz_confidence.py`)

22 unit tests covering:
- ConfidenceState operations
- Research → Confidence initialization
- Answer → Confidence updates
- Model validation

---

## Design Document

Full design saved at:
```
docs/plans/2026-01-03-personalized-adaptive-quiz-design.md
```

Contains:
- High-level flow diagrams
- Confidence framework details
- Question type taxonomy
- AI prompts for generation/analysis
- Full implementation architecture
- API endpoint specs

---

## What Was Built (Session 2)

### Phase 2: Industry Question Banks

Created 6 industry-specific question banks in `backend/src/knowledge/industry_questions/`:

| File | Questions | Deep Dives | Industry |
|------|-----------|------------|----------|
| `dental.json` | 15 | 3 | Dental Practices |
| `professional_services.json` | 14 | 3 | Law, Accounting, Consulting |
| `coaching.json` | 13 | 2 | Life/Business Coaches |
| `home_services.json` | 13 | 2 | HVAC, Plumbing, Cleaning |
| `veterinary.json` | 13 | 2 | Vet Clinics |
| `recruiting.json` | 14 | 2 | Staffing Agencies |

Each question bank includes:
- **Questions**: Predefined questions with `input_type`, `target_categories`, `expected_boosts`, `priority`
- **Deep Dive Templates**: Follow-up questions triggered by specific answers (e.g., high no-show rate)
- **Woven Confirmation Templates**: Questions that confirm research + discover new info

### Phase 3: API Routes

Added adaptive quiz endpoints to `backend/src/routes/quiz.py`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/quiz/adaptive/start` | POST | Start adaptive quiz, returns first question |
| `/api/quiz/adaptive/answer` | POST | Submit answer, get next question or completion |
| `/api/quiz/adaptive/state/{id}` | GET | Get current confidence state |
| `/api/quiz/adaptive/industries` | GET | List industries with question banks |
| `/api/quiz/adaptive/questions/{ind}` | GET | Get question bank for industry |

### Phase 3: IndustryQuestionBank Class

Added `IndustryQuestionBank` dataclass to `quiz_engine.py`:

```python
@dataclass
class IndustryQuestionBank:
    industry: str
    display_name: str
    questions: List[Dict]
    deep_dive_templates: List[Dict]
    woven_confirmation_templates: List[Dict]

    @classmethod
    def load(cls, industry: str) -> "IndustryQuestionBank": ...

    def get_question_by_id(self, id: str) -> Optional[Dict]: ...
    def get_questions_for_category(self, cat, exclude_ids) -> List[Dict]: ...
    def get_deep_dive_for_answer(self, q_id, answer) -> Optional[Dict]: ...
```

### Tests Added

17 new tests in `test_quiz_confidence.py`:
- `TestIndustryQuestionBank`: 11 tests for loading, querying, filtering
- `TestGetAvailableIndustries`: 3 tests for industry listing
- `TestQuestionBankIntegration`: 3 tests for validation

All **39 tests passing**.

---

## What Was Built (Session 3)

### Phase 4: Frontend Components

Created 3 new frontend components:

| File | Purpose |
|------|---------|
| `frontend/src/components/quiz/StructuredInput.tsx` | Renders select, multi-select, number, scale, and text inputs |
| `frontend/src/components/quiz/ConfidenceProgress.tsx` | Visual progress bars for each confidence category |
| `frontend/src/pages/AdaptiveQuiz.tsx` | Main adaptive quiz page with full integration |

#### StructuredInput.tsx
- **Select**: Single choice with radio-style buttons, auto-submits on selection
- **MultiSelect**: Multiple choice with checkboxes, requires explicit submit
- **Number**: Numeric input with optional min/max/step/unit
- **Scale**: 1-5 or 1-10 rating scale, auto-submits on selection
- **Text**: Textarea with enter-to-submit support

#### ConfidenceProgress.tsx
- Shows progress bars for all 8 confidence categories
- Displays threshold markers and completion status
- **Compact mode**: Icon-based horizontal display for header
- **Full mode**: Detailed vertical list with labels
- **Mini mode**: Tiny vertical bars for inline use
- Color-coded by category and completion status

#### AdaptiveQuiz.tsx
Full quiz page with:
- **Phases**: loading → intro → conversation → complete
- **Voice input**: Uses existing VoiceRecorder component
- **Text input**: Fallback for voice questions
- **Structured input**: Auto-selects based on question type
- **Real-time confidence display**: Header mini-progress + sidebar full progress
- **TTS integration**: Speaks questions and acknowledgments
- **Error handling**: Displays errors with dismiss option
- **Skip option**: Users can skip to results early

#### Route Added
```tsx
<Route path="/quiz/adaptive" element={
  <AnonymousRoute>
    <AdaptiveQuiz />
  </AnonymousRoute>
} />
```

Access at: `http://localhost:5174/quiz/adaptive?session_id=<id>`

---

## What Was Built (Session 3 continued)

### Phase 5: Polish

Added production-ready polish to the AdaptiveQuiz component:

#### 5.1 Resume Functionality
- **State persistence**: Quiz state saved to sessionStorage after each answer
- **Resume screen**: "Welcome back" screen when returning to interrupted quiz
- **Options**: Continue where left off or start fresh
- **Auto-expire**: Saved states expire after 30 minutes
- **Clear on completion**: Saved state cleared when quiz completes

#### 5.2 Retry Logic
- **fetchWithRetry()**: All API calls retry up to 3 times with exponential backoff
- **Error display**: Improved error UI with retry button
- **Graceful TTS**: Voice synthesis fails silently, doesn't block quiz

#### 5.3 Loading States
- **Skeleton loader**: Shows placeholder content during initial load
- **Processing indicators**: Clear feedback during API calls

#### 5.4 Mobile Responsiveness
- **Collapsible progress**: Mobile users can tap to expand/collapse progress
- **Mini progress bar**: Always visible in mobile header
- **Responsive buttons**: Stack vertically on small screens
- **Touch-friendly**: Larger tap targets for mobile

---

## Production Readiness Checklist

- [x] Backend API routes with error handling
- [x] Frontend components with TypeScript
- [x] Resume functionality for interrupted sessions
- [x] Retry logic for network failures
- [x] Loading skeletons for better perceived performance
- [x] Mobile-responsive design
- [x] Voice input with text fallback
- [x] TTS for spoken questions
- [ ] Database migration applied (run: `supabase db push`)
- [ ] End-to-end testing with real users
- [ ] TTS API key configured in production

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `backend/src/models/quiz_confidence.py` | Core models: ConfidenceState, AdaptiveQuestion, AnswerAnalysis |
| `backend/src/services/quiz_engine.py` | AnswerAnalyzer, QuestionGenerator, IndustryQuestionBank |
| `backend/src/routes/quiz.py` | Adaptive quiz API routes (lines 1504+) |
| `backend/src/knowledge/industry_questions/*.json` | 6 industry question banks |
| `backend/supabase/migrations/013_adaptive_quiz.sql` | DB schema for adaptive quiz |
| `backend/tests/test_quiz_confidence.py` | 39 passing tests |
| `frontend/src/pages/AdaptiveQuiz.tsx` | Main adaptive quiz page |
| `frontend/src/components/quiz/StructuredInput.tsx` | Select, multi-select, number, scale inputs |
| `frontend/src/components/quiz/ConfidenceProgress.tsx` | Category progress visualization |
| `docs/plans/2026-01-03-personalized-adaptive-quiz-design.md` | Full design doc |

---

## How to Continue

```bash
# Start services
cd backend && source venv/bin/activate && uvicorn src.main:app --reload --port 8383
cd frontend && npm run dev
brew services start redis

# Run tests
cd backend && pytest tests/test_quiz_confidence.py -v

# Apply migration (when ready)
supabase db push
```

### Next Session Prompt

```
The Adaptive Quiz System is feature-complete. All 5 phases implemented.

Read:
- docs/handoffs/2026-01-03-adaptive-quiz-phase1-complete.md

To test:
1. Start backend: cd backend && uvicorn src.main:app --reload --port 8383
2. Start frontend: cd frontend && npm run dev
3. Apply migration: supabase db push
4. Navigate to: http://localhost:5174/quiz/adaptive?session_id=<valid_session_id>

Remaining tasks:
- End-to-end testing with real users
- Configure TTS API key in production
- Monitor for edge cases
```

---

## Related Work

A separate session is working on improving the **90-minute paid workshop** with similar personalization.

---

## Tests Passing

```
Backend: 39 passed in 0.61s
Frontend: TypeScript compilation successful (no errors)
```

All Phase 1-5 functionality is implemented and compiles successfully.
