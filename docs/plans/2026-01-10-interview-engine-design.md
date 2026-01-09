# SOTA Voice Interview Engine Design

> **Status:** Approved
> **Date:** 2026-01-10
> **Goal:** Transform the voice interview from scripted Q&A into a warm, adaptive conversation that uncovers deeper business intelligence.

---

## Problem Statement

Current interview experience:
- 5 pre-scripted questions asked sequentially
- Generic keyword-matching acknowledgments ("Time is definitely one of the biggest constraints")
- No follow-up on interesting threads
- Feels like a survey, not a consultation

## Design Decisions

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Structure | Hybrid (3 anchors + AI follow-ups) | Ensures required data while allowing natural flow |
| Anchor framework | Problem → Process → Priority | Starts with pain, gets detail, ends with value framing |
| Follow-up logic | Signal detection with template bank | Fast response, no API latency per follow-up |
| Acknowledgment generation | LLM-generated for anchors | Needs to feel genuinely responsive |
| Tone | Warm expert | Builds trust, shows industry knowledge |

---

## The 3 Anchor Questions

| # | Anchor | Question | Purpose |
|---|--------|----------|---------|
| 1 | **Problem** | "What's the one thing in your business that costs you the most time or money right now?" | Emotional hook, identifies primary pain |
| 2 | **Process** | "Walk me through how that works today - what happens step by step?" | Concrete operational detail for AI recommendations |
| 3 | **Priority** | "If we could fix that in the next 90 days, what would that be worth to your business?" | Value framing, primes for paid report |

**Flow:**
```
Intro → Anchor 1 → [0-2 follow-ups] → Anchor 2 → [0-2 follow-ups] → Anchor 3 → Summary
```

- **Target duration:** 4-6 minutes
- **Max questions:** 8 total (3 anchors + up to 5 follow-ups)

---

## Signal Detection System

After each answer, detect signals to decide: probe deeper or move on?

| Signal | Detection patterns | Follow-up direction |
|--------|-------------------|---------------------|
| **Pain intensity** | "nightmare", "killing us", "hours every day", "hate" | Quantify: "How many hours a week would you say?" |
| **Manual work** | "spreadsheets", "by hand", "copy/paste", "manually", "paper" | Map process: "What triggers that work?" |
| **Customer impact** | "clients complain", "lose customers", "reputation", "reviews" | Cost: "When was the last time that cost you a job?" |
| **Growth blocker** | "can't scale", "hire more", "keeping up", "capacity" | Constraint: "What breaks first when you get busy?" |
| **Tech frustration** | Software names, "doesn't integrate", "old system", "clunky" | Stack: "What else does that need to talk to?" |
| **Vague answer** | Short response, "I don't know", unclear | Reframe: "Let me ask differently - what did you do yesterday that felt like a waste?" |

### Follow-up Bank (per signal)

Each signal has 3-4 varied follow-ups:

```python
FOLLOW_UPS = {
    "pain_intensity": [
        "That sounds really frustrating. Can you give me a recent example?",
        "When that happens, what's the ripple effect on your team?",
        "How long has this been going on?",
    ],
    "manual_work": [
        "How long has it been that way? Has anyone tried to fix it before?",
        "Who on your team spends the most time on that?",
        "What would happen if that person was sick for a week?",
    ],
    "customer_impact": [
        "When was the last time that actually cost you business?",
        "How do customers usually find out about those issues?",
        "What do you tell customers when that happens?",
    ],
    # ... etc
}
```

---

## Warm Expert Acknowledgments

### The Formula

```
[Validate pain] + [Industry insight] + [Bridge to next]
```

### Examples by Industry

| Industry | User says | SOTA acknowledgment |
|----------|-----------|---------------------|
| Plumbing | "Scheduling is chaos" | "Scheduling in trades is brutal - one emergency call throws off the whole day, right? Walk me through what happens when that hits." |
| Dental | "Insurance claims take forever" | "Insurance billing is the hidden time-killer in every practice I talk to. Is your team doing that manually or through your PM system?" |
| Construction | "Quotes take too long" | "Slow quotes lose jobs - I've seen contractors leave $50K on the table because someone else replied first. What's your current turnaround?" |
| Generic | "We're drowning in emails" | "Email overload usually means information is scattered across too many places. Where else does important stuff come in?" |

### Generation Prompt

```
You are a warm, experienced business consultant conducting a voice interview.

Context:
- Industry: {industry}
- Company: {company_name}
- Their answer: {answer}
- Signals detected: {signals}
- Next question to ask: {next_question}

Generate a 1-2 sentence acknowledgment that:
1. Names their specific pain (use their actual words)
2. Adds a brief industry insight showing you've seen this before
3. Bridges naturally into the next question

Tone: Warm expert - knowledgeable but not condescending. Like a consultant who's solved this problem 100 times.

AVOID: "That's helpful", "Thanks for sharing", "I understand", "Great question"
USE: "Ah, [their problem]...", "That's really common in [industry]...", "I see this constantly..."

Keep it conversational. One breath, not a paragraph.
```

---

## Technical Architecture

### New Components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| Interview Engine | `backend/src/services/interview_engine.py` | Orchestrates conversation flow, decides next question |
| Signal Detector | `backend/src/skills/interview/signal_detector.py` | Analyzes answers, extracts signals |
| Acknowledgment Skill | `backend/src/skills/interview/acknowledgment.py` | LLM skill for warm expert responses |
| Follow-up Bank | `backend/src/expertise/data/interview/follow_ups.json` | Signal → follow-up question mapping |
| Industry Insights | `backend/src/expertise/data/industries/{industry}.json` | Industry-specific pain points, language |

### API Design

**New endpoint:** `POST /api/interview/process-answer`

Request:
```json
{
  "session_id": "uuid",
  "audio": "base64 or multipart",
  "current_anchor": 1,
  "conversation_history": [...]
}
```

Response:
```json
{
  "transcription": "Scheduling is a nightmare, we're always double-booked",
  "signals_detected": ["pain_intensity", "manual_work"],
  "acknowledgment": "Scheduling in trades is brutal - one emergency throws off everything...",
  "next_question": {
    "type": "follow_up",  // or "anchor"
    "text": "How many hours a week would you say you spend fixing scheduling conflicts?",
    "topic": "Quantifying pain"
  },
  "progress": {
    "current_anchor": 1,
    "questions_asked": 2,
    "max_questions": 8
  }
}
```

### Frontend Changes

Current `VoiceQuizInterview.tsx` has hardcoded questions. Simplify to:

```tsx
// Frontend becomes a thin display layer
const { acknowledgment, next_question, progress } = await processAnswer(audio)

// Display acknowledgment in chat
// Update question card with next_question
// TTS speaks: acknowledgment + next_question.text
```

---

## Conversation Data Model

What gets stored for the report:

```typescript
interface InterviewData {
  session_id: string
  company_name: string
  industry: string

  // Per-answer data
  answers: Array<{
    question_type: 'anchor' | 'follow_up'
    question_text: string
    answer_text: string
    signals_detected: string[]
    acknowledgment_used: string
    duration_seconds: number
  }>

  // Derived insights
  primary_pain: string           // Most mentioned pain point
  pain_intensity: 'low' | 'medium' | 'high'
  tech_sophistication: 'low' | 'medium' | 'high'
  urgency_signals: string[]
  estimated_value: string        // From anchor 3

  // Meta
  total_duration_seconds: number
  questions_asked: number
  completed: boolean
}
```

---

## Implementation Tasks

### Phase 1: Backend Engine
1. Create `interview_engine.py` with anchor progression logic
2. Create `signal_detector.py` skill
3. Create `acknowledgment.py` LLM skill
4. Build follow-up question bank JSON
5. Create `/api/interview/process-answer` endpoint

### Phase 2: Industry Knowledge
6. Add interview insights to industry JSON files (dental, plumbing, construction, etc.)
7. Add industry-specific pain point vocabulary for signal detection

### Phase 3: Frontend Integration
8. Refactor `VoiceQuizInterview.tsx` to use new API
9. Remove hardcoded questions
10. Update TTS to speak acknowledgment + question

### Phase 4: Polish
11. Add conversation analytics/logging
12. Test with real users
13. Tune signal detection thresholds
14. Expand follow-up bank based on common answers

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Interview completion rate | ~70% | 85%+ |
| Avg interview duration | 5 min | 4-6 min |
| User satisfaction (if measured) | Unknown | 4.5/5 |
| Report quality (detail captured) | Basic | Rich operational detail |
| Conversion to paid report | X% | X+15% |

---

## Open Questions

1. **TTS voice** - Should acknowledgments sound different from questions? (Warmer tone for ack, clearer for question)
2. **Silence handling** - What if user pauses mid-answer? Wait or prompt?
3. **Interruption** - Can user interrupt the AI speaking to add more?

---

## Appendix: Full Conversation Example

**Plumber, "Mount Eden Plumbing"**

```
AI: "What's the one thing in your business that costs you the most time or money right now?"

User: "Honestly, scheduling. We're constantly double-booked or guys show up and the customer isn't home."

AI: "Scheduling in trades is brutal - one emergency call throws off the whole day. How are you tracking jobs right now - whiteboard, software, something else?"
[Signal: pain_intensity, manual_work → follow-up on process]

User: "We've got a shared Google Calendar but it's a mess. My wife updates it but then guys don't check it."

AI: "Ah, the calendar-that-nobody-checks problem. I hear that constantly. Walk me through what happens step by step when a new job comes in."
[Signal: tech_frustration → move to Anchor 2]

User: "Customer calls, my wife writes it down, tries to find a slot, calls them back, then adds it to the calendar, then texts the guys..."

AI: "That's a lot of handoffs - phone to paper to calendar to text. No wonder things slip through. If we could tighten that up in the next 90 days, what would that be worth to your business?"
[Signal: manual_work, detailed process → move to Anchor 3]

User: "I mean, we probably lose one or two jobs a week from confusion. That's maybe $500-1000 a week?"

AI: "So $25-50K a year just from scheduling friction - that's significant. I've got a clear picture of what's happening. Let me show you what AI opportunities we found..."
[Complete → Summary]
```

Total: 6 questions (3 anchors + 3 follow-ups), ~4 minutes
