# Personalized Adaptive Quiz Design

**Date:** 2026-01-03
**Status:** Approved
**Goal:** Replace generic quiz with confidence-driven, research-aware adaptive interview

---

## Overview

The current quiz asks generic questions regardless of what we learned from research. The new system:

1. **Uses research as context** - Don't ask what we already know
2. **Fills gaps dynamically** - Ask only what's missing for a credible teaser
3. **Adapts in real-time** - Follow interesting threads, go off-script when needed
4. **Confidence-gated** - Quiz ends when thresholds are met, not after X questions

---

## User Journey

```
1. ENTRY
   └─→ User enters company website

2. RESEARCH (30-60 sec, runs in background)
   └─→ Scrape website, LinkedIn, news, job postings
   └─→ Build CompanyProfile with confidence scores
   └─→ Calculate "knowledge gaps" per category

3. QUIZ GENERATION
   └─→ AI generates question tree based on gaps
   └─→ Pre-loads branching paths for likely answers
   └─→ Prioritizes: HIGH gaps first, then MEDIUM

4. ADAPTIVE INTERVIEW
   └─→ Ask questions until confidence thresholds met
   └─→ Weave confirmations into discovery questions
   └─→ Go off-script when answers reveal new threads
   └─→ Track confidence in real-time

5. TEASER UNLOCK
   └─→ All categories hit minimum confidence
   └─→ Generate personalized teaser with real insights
   └─→ Paywall for full report
```

---

## Confidence Framework

The system tracks confidence across categories. Each has a **minimum threshold** that must be met before the teaser unlocks.

| Category | Minimum | How it's filled |
|----------|---------|-----------------|
| `company_basics` | 80% | Research: size, industry, business model, location |
| `tech_stack` | 60% | Research: detected tools. Quiz: confirm + expand |
| `pain_points` | 80% | Quiz only - can't find this publicly. Need 2+ specific |
| `operations` | 60% | Mix: research gives hints, quiz validates workflows |
| `goals_priorities` | 70% | Quiz only - what they want to achieve |
| `quantifiable_metrics` | 50% | Quiz: hours, volume, costs. Needed for ROI calculations |
| `industry_context` | 60% | Industry-specific questions (patient count, client count) |
| `buying_signals` | 40% | Quiz: budget, timeline, decision maker (lower bar) |

### How Confidence is Calculated

- Each answer contributes points to relevant categories
- Specific answers > vague answers (more points)
- Confirmed research findings boost confidence
- Contradictions flag for clarification

### Example Scenario

- Research fills `company_basics` to 75%, `tech_stack` to 40%
- Quiz needs to: boost basics to 80%, fill tech to 60%, and fill pain_points/goals from scratch
- Result: ~6-10 questions depending on answer quality

---

## Question Types

### 1. Woven Confirmations (structured input)
Use research as context, confirm + discover simultaneously.

> "How's HubSpot working for your sales pipeline?"

> "With 50 employees across 3 locations, what's your biggest coordination challenge?"

### 2. Gap Fillers (structured or voice)
Direct questions for missing data.

> "How many patients do you see per week?"

> "What tools do you use for scheduling?"

### 3. Discovery Probes (voice/text)
Open-ended, can't be researched.

> "What's the most frustrating part of your week?"

> "If you could fix one thing tomorrow, what would it be?"

### 4. Deep Dives (voice/text, triggered by answers)
Follow-up when answer reveals something interesting.

> User: "We lose leads because we can't answer calls"
> AI: "Tell me more - what happens to those missed calls?"

### 5. Industry-Specific (structured or voice)
Pulled from industry question bank.

> Dental: "What's your patient no-show rate?"
> Agency: "How many retainer vs project clients?"

---

## Adaptive Conversation Engine

### Inputs (evaluated after each answer)
- Current confidence scores per category
- Research findings (with confidence levels)
- Conversation history (what we've asked/learned)
- Last answer (analyzed for signals)
- Pre-generated question tree

### Decision Logic

```
IF answer contains unexpected signal
   → Generate follow-up deep dive (go off-script)

ELSE IF all categories >= thresholds
   → Wrap up → generate teaser

ELSE
   → Pick next question from tree:
     1. Lowest confidence category first
     2. Consider natural conversation flow
     3. Don't repeat topics too quickly
```

### Answer Analysis Extracts
- **Explicit facts:** "We have 12 employees" → company_basics +15%
- **Pain signals:** "waste hours on..." → pain_points +20%, flag for deep dive
- **Tool mentions:** "we use Slack and Notion" → tech_stack +10% each
- **Quantifiable data:** "50 leads per month" → quantifiable_metrics +25%
- **Sentiment:** frustration, urgency, skepticism → influences question tone

### Example Flow

```
Research: dental practice, 3 locations, ~20 employees (medium confidence)

Q1: "Running 3 dental locations is no small feat - what's the
     biggest headache in keeping them coordinated?"
A1: "Honestly, patient scheduling is a nightmare. We double-book
     constantly and have a 30% no-show rate."

     → Extracted: pain_point (scheduling), metric (30% no-show)
     → Signal detected: specific pain, go deep

Q2: "30% no-shows is brutal. Walk me through what happens when
     someone doesn't show - how does your team handle it?"
A2: "We try to call but honestly the front desk is swamped..."

     → Extracted: operations detail, secondary pain (staffing)
     → Confidence: pain_points 60%, operations 40%

Q3: [continues until thresholds met]
```

---

## AI Prompt (Question Generation)

```markdown
You are an expert business analyst conducting a personalized discovery
interview. Your goal is to fill knowledge gaps efficiently while building
rapport and uncovering real pain points.

## COMPANY RESEARCH (what we already know)
{{company_profile}}

## CONFIDENCE SCORES (current state)
{{confidence_scores}}
- company_basics: {{basics_score}}% (need 80%)
- tech_stack: {{tech_score}}% (need 60%)
- pain_points: {{pain_score}}% (need 80%)
- operations: {{ops_score}}% (need 60%)
- goals_priorities: {{goals_score}}% (need 70%)
- quantifiable_metrics: {{metrics_score}}% (need 50%)
- industry_context: {{industry_score}}% (need 60%)
- buying_signals: {{buying_score}}% (need 40%)

## CONVERSATION SO FAR
{{conversation_history}}

## LAST ANSWER
{{last_answer}}

## YOUR TASK
Generate the next question following these rules:

### QUESTION SELECTION LOGIC
1. First, analyze the last answer for:
   - Explicit facts (extract and log)
   - Pain signals worth exploring deeper
   - Quantifiable metrics mentioned
   - Emotional indicators (frustration, urgency)

2. If the answer reveals something worth exploring:
   - Generate a follow-up deep dive question
   - Use their exact words: "You mentioned X - tell me more about..."

3. Otherwise, select the next question based on:
   - Lowest confidence category that isn't blocked
   - Natural conversation flow (don't jump topics abruptly)
   - Weave in confirmations of medium-confidence research

### QUESTION STYLE RULES
- NEVER ask what we already know with high confidence
- WEAVE confirmations into discovery: "Since you're using {{tool}}, how's that working for {{use_case}}?"
- BE SPECIFIC to their business: "For a {{industry}} with {{size}} employees..."
- USE THEIR LANGUAGE from previous answers
- KEEP IT CONVERSATIONAL, not interrogative
- ONE QUESTION at a time (may have brief acknowledgment first)

### RESPONSE FORMAT
{
  "acknowledgment": "Brief, natural response to their last answer (optional)",
  "question": "The next question to ask",
  "question_type": "structured|voice",
  "input_type": "text|number|select|multi_select|scale|voice",
  "options": [...] // if select/multi_select
  "target_categories": ["pain_points", "operations"],
  "confidence_boosts": {"pain_points": 20, "operations": 15},
  "rationale": "Why asking this now"
}

### INDUSTRY QUESTION BANK (use when relevant)
{{industry_specific_questions}}

### END CONDITIONS
If all confidence scores meet thresholds, respond with:
{
  "complete": true,
  "wrap_up_message": "Personalized closing that references what you learned",
  "summary": "Key findings for teaser generation"
}
```

---

## Implementation Architecture

### Backend Components

```
backend/src/
├── services/
│   └── quiz_engine.py (NEW)
│       ├── ConfidenceTracker - tracks scores per category
│       ├── QuestionGenerator - calls AI, manages tree
│       └── AnswerAnalyzer - extracts facts, detects signals
│
├── models/
│   └── quiz_confidence.py (NEW)
│       ├── ConfidenceCategory enum
│       ├── ConfidenceState model
│       └── AdaptiveQuestion model
│
├── routes/
│   └── quiz.py (MODIFY)
│       ├── POST /quiz/adaptive/start
│       ├── POST /quiz/adaptive/answer
│       └── GET /quiz/adaptive/state/{session_id}
│
└── knowledge/
    └── industry_questions/ (NEW)
        ├── dental.json
        ├── marketing_agency.json
        ├── professional_services.json
        └── ... per industry
```

### Frontend Components

```
frontend/src/
├── pages/
│   └── AdaptiveQuiz.tsx (NEW)
│       ├── Confidence progress bar (shows all categories)
│       ├── Dynamic question renderer (structured vs voice)
│       └── Real-time "what we've learned" sidebar
│
└── components/quiz/
    ├── ConfidenceProgress.tsx (NEW)
    ├── StructuredInput.tsx (NEW)
    └── VoiceInput.tsx (existing, enhanced)
```

### API Endpoints

#### POST `/api/quiz/adaptive/start`
Start adaptive quiz after research completes.

**Request:**
```json
{ "session_id": "uuid" }
```

**Response:**
```json
{
  "session_id": "uuid",
  "question": { "id": "q_abc", "question": "...", "question_type": "voice", ... },
  "confidence": {
    "scores": { "company_basics": 75, "pain_points": 0, ... },
    "thresholds": { "company_basics": 80, ... },
    "gaps": ["company_basics", "pain_points", ...],
    "ready_for_teaser": false
  },
  "company_name": "Acme Corp"
}
```

#### POST `/api/quiz/adaptive/answer`
Submit answer and get next question.

**Request:**
```json
{
  "session_id": "uuid",
  "question_id": "q_abc",
  "answer": "We spend 20 hours a week on manual data entry",
  "answer_type": "voice"
}
```

**Response (continue):**
```json
{
  "complete": false,
  "question": { "id": "q_def", "acknowledgment": "That's a lot of manual work.", ... },
  "confidence": { "scores": {...}, "gaps": [...], ... },
  "analysis_hint": { "detected_signals": ["pain_signal", "quantifiable"], "is_deep_dive": true }
}
```

**Response (complete):**
```json
{
  "complete": true,
  "confidence": { "scores": {...}, "ready_for_teaser": true },
  "redirect": "/quiz/preview?session_id=uuid",
  "summary": { "pain_points": [...], "goals": [...], ... }
}
```

---

## Database Changes

Add to `quiz_sessions` table:

```sql
ALTER TABLE quiz_sessions ADD COLUMN quiz_mode TEXT DEFAULT 'static';
ALTER TABLE quiz_sessions ADD COLUMN confidence_state JSONB;
ALTER TABLE quiz_sessions ADD COLUMN adaptive_answers JSONB DEFAULT '[]';
ALTER TABLE quiz_sessions ADD COLUMN quiz_completed_at TIMESTAMPTZ;
```

---

## Industry Question Banks

Each industry has a JSON file with pre-defined questions that get mixed in.

### Example: `dental.json`

```json
{
  "industry": "dental",
  "questions": [
    {
      "id": "patient_volume",
      "question": "How many patients does your practice see per week?",
      "input_type": "number",
      "target_categories": ["quantifiable_metrics", "industry_context"],
      "expected_boosts": {"quantifiable_metrics": 20, "industry_context": 15}
    },
    {
      "id": "no_show_rate",
      "question": "What's your approximate patient no-show rate?",
      "input_type": "select",
      "options": [
        {"value": "under_10", "label": "Under 10%"},
        {"value": "10_20", "label": "10-20%"},
        {"value": "20_30", "label": "20-30%"},
        {"value": "over_30", "label": "Over 30%"}
      ],
      "target_categories": ["pain_points", "quantifiable_metrics"],
      "expected_boosts": {"pain_points": 15, "quantifiable_metrics": 15}
    },
    {
      "id": "insurance_handling",
      "question": "How do you currently handle insurance verification and claims?",
      "input_type": "voice",
      "target_categories": ["operations", "pain_points"],
      "expected_boosts": {"operations": 20, "pain_points": 10}
    }
  ]
}
```

---

## Success Metrics

1. **Quiz completion rate** - Should increase (more engaging)
2. **Average questions to threshold** - Target: 6-10 (down from 25 static)
3. **Teaser report quality** - More specific findings, fewer generic recommendations
4. **Time to teaser** - Target: 5-8 minutes total (research + quiz)
5. **Conversion to paid** - Higher quality leads should convert better

---

## Implementation Order

1. **Phase 1: Core Engine**
   - ConfidenceState model
   - ConfidenceTracker with threshold logic
   - AnswerAnalyzer with AI extraction

2. **Phase 2: Question Generation**
   - QuestionGenerator with AI prompt
   - Industry question banks (start with 3 industries)
   - Deep dive detection

3. **Phase 3: API Routes**
   - `/adaptive/start`, `/adaptive/answer`, `/adaptive/state`
   - Database schema updates
   - Session persistence

4. **Phase 4: Frontend**
   - AdaptiveQuiz page
   - ConfidenceProgress component
   - StructuredInput components

5. **Phase 5: Polish**
   - TTS integration
   - Error handling
   - Resume functionality
   - Analytics/logging

---

## Related Documents

- Workshop (90-min paid experience) will follow similar patterns with deeper thresholds
- See `docs/plans/2025-12-27-interview-confidence-framework.md` for earlier thinking
