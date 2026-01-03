# Personalized 90-Minute Workshop Design

> **Status:** Design Complete
> **Date:** 2026-01-03
> **Goal:** Transform the post-payment workshop from generic questionnaire into a premium, deeply personalized consulting experience

---

## Table of Contents

1. [Overview](#overview)
2. [Design Principles](#design-principles)
3. [User Journey](#user-journey)
4. [Phase 1: Confirm & Calibrate](#phase-1-confirm--calibrate)
5. [Phase 2: Deep-Dive Conversations](#phase-2-deep-dive-conversations)
6. [Phase 3: Synthesis & Close](#phase-3-synthesis--close)
7. [Adaptive Branching Logic](#adaptive-branching-logic)
8. [Enhanced Confidence Framework](#enhanced-confidence-framework)
9. [Milestone Summary Format](#milestone-summary-format)
10. [Premium UX Details](#premium-ux-details)
11. [Technical Architecture](#technical-architecture)
12. [Data Models](#data-models)
13. [API Routes](#api-routes)
14. [Robustness & Recovery](#robustness--recovery)
15. [Performance Targets](#performance-targets)
16. [Implementation Notes](#implementation-notes)

---

## Overview

### The Problem

The current post-payment workshop:
- Ignores quiz data - starts with generic questions instead of building on what we know
- Uses 5 fixed questions - same for everyone regardless of context
- Goes wide when we need depth - we already have breadth from the quiz
- No user-type adaptation - technical vs non-technical treated the same
- No visible value building - user doesn't see their report forming

### The Solution

A premium workshop experience that:
- **Starts with what we know** - "Based on your quiz, your top 3 pain points are X, Y, Z"
- **Goes deep, not wide** - For each pain point: current process → failed solutions → cost/impact → ideal state → stakeholders
- **Adapts to user type** - Technical/non-technical, budget-ready/constrained, decision-maker/influencer
- **Shows value being built** - Milestone summaries every 15-20 min with draft findings
- **Respects user time** - Can complete faster if confidence thresholds met

### What We Have to Build On

From pre-paywall flow:
- `CompanyProfile` from research scrape (name, website, industry, size, tech stack, description)
- Quiz answers (pain points, goals, tools, budget range)
- Teaser report with AI readiness score
- Initial confidence scores

Existing infrastructure:
- `InterviewConfidenceSkill` with per-topic scoring
- `FollowUpQuestionSkill` for adaptive questions
- `PainExtractionSkill` for structured extraction
- Topic weights system (challenges weighted 1.5x, budget 0.8x)
- Knowledge base with vendors, benchmarks, industry data

---

## Design Principles

### Premium = Magic + Flow + Payoff

```
MAGIC moments ("They know me"):
├── Confirmation shows data they forgot they shared
├── Questions reference their specific tools by name
├── AI catches contradictions: "Earlier you said X, but..."
├── Milestone findings use their exact numbers
└── Vendor recommendations match their existing stack

FLOW moments ("Effortless"):
├── Never asked the same thing twice
├── Smooth transitions between phases (no jarring reloads)
├── Voice/text seamlessly interchangeable mid-conversation
├── Progress always visible but never distracting
└── Can pause, come back, resume exactly where left off

PAYOFF moments ("Worth every minute"):
├── First milestone summary: "This is already worth it"
├── ROI numbers feel real, not made up
├── Final preview makes them excited to receive report
└── They learn something about their business during workshop
```

### Key Constraints

- Duration: 60-90 minutes (adaptive based on confidence)
- Must feel pleasant, not overwhelming
- Quality over quantity - can end early if confident
- Every question must reference prior context

---

## User Journey

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: Confirm & Calibrate (~10 min)                        │
│  ├── Interactive summary of quiz + research data               │
│  ├── User rates accuracy (👍/👎/edit) per item                 │
│  └── System identifies: gaps, errors, deep-dive priorities     │
├─────────────────────────────────────────────────────────────────┤
│  PHASE 2: Deep-Dive Conversations (~50-70 min)                 │
│  ├── 3-4 focused conversations based on confirmed pain points  │
│  ├── Each conversation: current → failed → cost → ideal → who  │
│  ├── Adaptive branching (technical/budget/decision-maker)      │
│  └── Milestone summary after each deep-dive                    │
├─────────────────────────────────────────────────────────────────┤
│  PHASE 3: Synthesis & Close (~10 min)                          │
│  ├── Final report preview with key findings                    │
│  ├── Stakeholder/next-steps confirmation                       │
│  └── "Anything we missed?" catch-all                           │
└─────────────────────────────────────────────────────────────────┘
```

### Session Status Progression

```
paid → workshop_confirmation → workshop_deepdive →
workshop_synthesis → generating → qa_pending → released
```

---

## Phase 1: Confirm & Calibrate

### Purpose

Build trust by showing we listened, and identify where to focus deep-dives.

### Duration

~10 minutes

### UI Design

Card-based UI showing what we learned, organized into 4 categories:

```
┌─────────────────────────────────────────────────────────────────┐
│  "Here's what we learned about [Company Name]"                  │
├─────────────────────────────────────────────────────────────────┤
│  📍 YOUR BUSINESS                                    👍 👎 ✏️   │
│  • 15-person marketing agency in Amsterdam                      │
│  • B2B clients, primarily tech startups                         │
│  • Growing ~30% YoY                                             │
├─────────────────────────────────────────────────────────────────┤
│  😤 PAIN POINTS YOU MENTIONED                        👍 👎 ✏️   │
│  • Client reporting takes too long (8+ hrs/week)                │
│  • Lead follow-up falls through cracks                          │
│  • Team spends time on repetitive proposals                     │
├─────────────────────────────────────────────────────────────────┤
│  🛠️ YOUR CURRENT TOOLS                               👍 👎 ✏️   │
│  • HubSpot CRM, Google Workspace, Slack                         │
│  • No project management tool identified                        │
├─────────────────────────────────────────────────────────────────┤
│  🎯 WHAT SUCCESS LOOKS LIKE                          👍 👎 ✏️   │
│  • Save 10+ hours/week on admin work                            │
│  • Never miss a lead follow-up                                  │
└─────────────────────────────────────────────────────────────────┘
          [ Everything looks right → Start Deep-Dive ]
```

### Behavior

- Cards animate in sequentially (not all at once)
- Subtle "researched" badge: "Based on 12 data points"
- Edit mode: inline text field, not modal popup
- Accuracy rating: haptic/visual feedback on tap
- "Missing info" shown differently: dotted border, lighter color
- Transition to deep-dive: cards collapse into progress bar

### Backend Logic

- 👎 or ✏️ responses flag topics needing clarification in Phase 2
- Missing data (low quiz confidence) gets highlighted for exploration
- System prioritizes deep-dives based on: pain severity × confidence gap

### Signals Captured

- Role/title → technical vs. non-technical framing
- Company size + budget answer → implementation approach
- Who they mention → decision-maker or influencer

---

## Phase 2: Deep-Dive Conversations

### Purpose

Go deep on 3-4 confirmed pain points to gather implementation-ready details.

### Duration

~50-70 minutes (15-20 min per pain point)

### Conversation Arc (per pain point)

Each deep-dive follows a natural conversation arc, not a checklist:

```
┌─────────────────────────────────────────────────────────────────┐
│  PAIN POINT: "Client reporting takes too long"                 │
├─────────────────────────────────────────────────────────────────┤
│  1. CURRENT STATE (~5 min)                                      │
│     "Walk me through how reporting works today..."              │
│     → Who does it? How often? Which tools? How long?            │
│     → What data sources? Manual steps?                          │
│                                                                 │
│  2. FAILED ATTEMPTS (~3 min)                                    │
│     "What have you tried to fix this?"                          │
│     → Past tools? Workarounds? Why didn't they work?            │
│                                                                 │
│  3. COST & IMPACT (~5 min)                                      │
│     "Help me understand the real cost..."                       │
│     → Hours/week × hourly rate = €X                             │
│     → Delayed reports → client churn? Missed upsells?           │
│     → Team frustration? Turnover risk?                          │
│                                                                 │
│  4. IDEAL STATE (~3 min)                                        │
│     "If we solved this perfectly, what does it look like?"      │
│     → Automated? Real-time? Self-serve for clients?             │
│                                                                 │
│  5. STAKEHOLDERS (~2 min)                                       │
│     "Who else touches this process?"                            │
│     → Who approves changes? Who needs to adopt?                 │
├─────────────────────────────────────────────────────────────────┤
│  ✅ MILESTONE SUMMARY                                           │
│  "Based on this, here's what we're adding to your report..."    │
│  [Shows 2-3 draft findings/recommendations]                     │
│                                                                 │
│  "We have solid coverage here. Go deeper or move to next?"      │
└─────────────────────────────────────────────────────────────────┘
```

### Key Principles

- Questions feel like follow-ups, not topic switches
- Reference prior context: "You mentioned HubSpot - does the reporting data live there or somewhere else?"
- Never repeat questions from quiz
- Probe for specifics: numbers, names, examples

### UX Details

- Current pain point always visible in sticky header
- Question shows as "typing..." before appearing
- Smart suggestions: "Tap to answer: Yes / No / It's complex"
- Voice mode: waveform visualization while speaking
- AI acknowledgments reference their words
- Subtle confidence indicator fills as they provide depth

---

## Phase 3: Synthesis & Close

### Purpose

Bring it all together, confirm stakeholders and timeline, catch anything missed.

### Duration

~10 minutes

### UI Design

```
┌─────────────────────────────────────────────────────────────────┐
│  🎯 YOUR AI READINESS REPORT - PREVIEW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  "Here's what your full report will include based on our        │
│   conversation today..."                                        │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  EXECUTIVE SUMMARY                                        │  │
│  │                                                           │  │
│  │  [Company] has 3 high-impact AI opportunities with        │  │
│  │  combined potential savings of €67,400/year.              │  │
│  │                                                           │  │
│  │  Priority ranking:                                        │  │
│  │  1. Client Reporting Automation     €23,400  ⚡ Quick Win  │  │
│  │  2. Lead Follow-up Sequences        €28,000  🎯 High ROI  │  │
│  │  3. Proposal Generation             €16,000  📈 Strategic │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  REPORT SECTIONS (Confidence)                             │  │
│  │                                                           │  │
│  │  ✅ Executive Summary                           94%       │  │
│  │  ✅ Current State Analysis                      87%       │  │
│  │  ✅ AI Opportunities (3 detailed findings)      91%       │  │
│  │  ✅ Vendor Recommendations                      85%       │  │
│  │  ✅ Implementation Roadmap                      78%       │  │
│  │  ✅ ROI Projections                             88%       │  │
│  │  ⚠️  Risk Assessment                            62%       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  FINAL QUESTIONS                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Stakeholder Confirmation                                    │
│     "Who else should see this report?"                          │
│     [ Just me ]  [ + Partner ]  [ + Team leads ]  [ Other ]     │
│                                                                 │
│  2. Timeline Confirmation                                       │
│     "When are you looking to act on this?"                      │
│     [ ASAP ]  [ This quarter ]  [ 6 months ]  [ Exploring ]     │
│                                                                 │
│  3. Catch-All                                                   │
│     "Is there anything we didn't cover that you'd want          │
│      included in your report?"                                  │
│     [ Nothing, we covered it ]  [ Yes, let me add... ]          │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  NEXT STEPS                                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  "Your full report will be ready within 24 hours. You'll        │
│   receive an email with:"                                       │
│                                                                 │
│  📄 Full PDF Report (30-40 pages)                               │
│  📊 ROI Calculator (interactive)                                │
│  📋 Implementation Checklist                                    │
│  🤝 Optional: 30-min review call to discuss findings            │
│                                                                 │
│              [ Complete Workshop & Generate Report ]            │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│  Workshop Duration: 72 minutes                                  │
│  Confidence Score: 84% (Excellent)                              │
│  Pain Points Analyzed: 3                                        │
│  Quantified Savings: €67,400/year                               │
└─────────────────────────────────────────────────────────────────┘
```

### What Happens After "Complete"

- All captured data → Report generation pipeline
- Confidence scores determine how much AI fills in vs. flags for review
- High-confidence sections generated automatically
- Low-confidence sections (<70%) flagged for QA review before release

---

## Adaptive Branching Logic

### Three Signals, Different Paths

We detect signals from quiz data + Phase 1 confirmation, then adapt questions accordingly.

### Signal 1: Technical vs Non-Technical

**Detection:**
- Role contains: CTO, Developer, IT, Engineer → Technical
- Quiz mentioned: APIs, integrations, "we built" → Technical
- Otherwise → Non-technical

**Technical path:**
```
• "What APIs does HubSpot expose for this data?"
• "Is there a webhook or do you poll?"
• "Where does this live - cloud, on-prem, hybrid?"
```

**Non-technical path:**
```
• "Who would need to set this up - internal team or vendor?"
• "How does your team usually adopt new tools?"
• "What would make this easy vs. hard to roll out?"
```

### Signal 2: Budget-Ready vs Budget-Constrained

**Detection:**
- Quiz budget: €15K+ → Budget-ready
- Quiz budget: <€5K or "not sure" → Constrained
- Company size 50+ usually → More budget flexibility

**Budget-ready path:**
```
• "Would you prefer build vs. buy for this?"
• "Full implementation or phased rollout?"
• "What's your timeline for seeing ROI?"
```

**Constrained path:**
```
• "What's the quickest win we could show to get more budget?"
• "Are there free/low-cost tools already in your stack?"
• "Who would need to approve additional spend?"
```

### Signal 3: Decision-Maker vs Influencer

**Detection:**
- Role: CEO, Owner, Founder, Director → Decision-maker
- Company size 1-10 → Usually decision-maker
- Mentions "I need to check with..." → Influencer

**Decision-maker path:**
```
• "What would make you confident to move forward?"
• "What's your realistic timeline?"
• Focus on ROI and strategic fit
```

**Influencer path:**
```
• "Who else needs to be convinced?"
• "What does your [CEO/CFO] care most about?"
• "What would help you build the internal case?"
• Focus on giving them ammunition for internal sell
```

### Implementation Note

These aren't separate question banks - they're **framing adjustments** applied to the same conversation arc. The AI selects phrasing based on detected signals.

---

## Enhanced Confidence Framework

### From Teaser Confidence → Report Confidence

The current framework tracks 5 topics. For full reports, we add 4 depth dimensions.

### Core Topics (inherited from quiz, enhanced in workshop)

| Topic | Coverage | Depth | Specificity | Actionability | Weight |
|-------|----------|-------|-------------|---------------|--------|
| Challenges | 0-25 | 0-25 | 0-25 | 0-25 | 1.5x |
| Goals | 0-25 | 0-25 | 0-25 | 0-25 | 1.2x |
| Operations | 0-25 | 0-25 | 0-25 | 0-25 | 1.0x |
| Technology | 0-25 | 0-25 | 0-25 | 0-25 | 1.0x |
| Budget/Timeline | 0-25 | 0-25 | 0-25 | 0-25 | 0.8x |

### Depth Dimensions (unlocked in workshop deep-dives)

| Dimension | What We Need |
|-----------|--------------|
| Integration Depth | Tool connections mapped, data flows documented, manual handoffs identified |
| Cost Quantification | Hours/week quantified, € impact calculated, opportunity cost captured |
| Stakeholder Mapping | Decision-maker identified, approval process understood, change resistance anticipated |
| Implementation Readiness | Internal resources assessed, timeline constraints known, quick wins vs. big bets clear |

### Readiness Thresholds

**ACCEPTABLE (60%)** - Can generate report, some gaps:
- 2+ pain points with quantified cost
- Primary tools mapped
- At least 1 stakeholder identified

**EXCELLENT (80%)** - Comprehensive, consultant-grade:
- 3+ pain points with full cost/impact analysis
- Integration map complete
- Decision process understood
- Implementation approach discussed

**HARD GATES** (must pass regardless of score):
- ≥1 pain point with € or hours quantified
- Company size/industry confirmed
- At least 2 deep-dives completed

### Completion Logic

After each milestone summary, if confidence is "acceptable" (60%+), offer:
> "We have enough for a solid report on this area. Want to go deeper or move on?"

User chooses depth vs. speed. Quality floor maintained (can't skip if below acceptable).

---

## Milestone Summary Format

### The "Value Moment" After Each Deep-Dive

```
┌─────────────────────────────────────────────────────────────────┐
│  ✨ MILESTONE: Client Reporting Deep-Dive Complete              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  "Based on what you shared, here's what we're adding to         │
│   your report..."                                               │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  📊 FINDING #1                                            │  │
│  │  Client Reporting Automation Opportunity                  │  │
│  │                                                           │  │
│  │  Current: 8 hrs/week × €75/hr = €31,200/year              │  │
│  │  After:   2 hrs/week (75% reduction)                      │  │
│  │  Potential savings: €23,400/year                          │  │
│  │                                                           │  │
│  │  Confidence: ████████░░ 82%                               │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  🎯 RECOMMENDATION (Draft)                                │  │
│  │  Integrate HubSpot + Google Data Studio with automated    │  │
│  │  weekly report generation. Client portal for self-serve.  │  │
│  │                                                           │  │
│  │  Vendors to evaluate: Databox, Whatagraph, Custom build   │  │
│  │  Implementation: 2-4 weeks │ Investment: €3-8K            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  📝 CAPTURED CONTEXT                                      │  │
│  │  • Reports go to: Account managers → Client success       │  │
│  │  • Data sources: HubSpot, GA4, LinkedIn Ads, Meta Ads     │  │
│  │  • Tried before: Supermetrics (too complex for team)      │  │
│  │  • Decision-maker: You (CEO) ✓                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  💬 "Does this capture it correctly? Anything to add or fix?"   │
│                                                                 │
│  [  Looks good  ]    [  Let me add something  ]                 │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📈 Overall Progress                                            │
│  ═══════════════════════════░░░░░░░░░░░  58% → Report Ready    │
│                                                                 │
│  Pain Points: ██░░ 1/3 complete                                 │
│  Time elapsed: 25 min │ Est. remaining: 35-45 min               │
│                                                                 │
│  [  Go deeper on this  ]    [  Move to next pain point →  ]    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### What This Achieves

- **Immediate value** - They see real findings, not just "we're gathering data"
- **Correction opportunity** - Can fix misunderstandings before report is final
- **Progress visibility** - Clear sense of how far along they are
- **User agency** - They choose depth vs. speed
- **Trust building** - "They're actually listening and synthesizing"

### UX Details

- Appears with celebration micro-animation
- ROI number animates/counts up
- Finding card has "draft" watermark (shows it's being built)
- Vendor logos displayed (not just names)
- "Add a note" option: user can annotate the finding
- Expand/collapse for full recommendation details
- Screenshot/share button (they can show their team)

### Backend Logic

- Findings generated in real-time using pain point data + knowledge base
- ROI calculated from captured hours × inferred hourly rate
- Vendor recommendations pulled from industry-specific vendor DB
- Confidence score reflects depth dimensions captured

---

## Premium UX Details

### Confirmation Phase Polish

- Cards animate in sequentially (not all at once)
- Subtle "researched" badge: "Based on 12 data points"
- Edit mode: inline text field, not modal popup
- Accuracy rating: haptic/visual feedback on tap
- "Missing info" shown differently: dotted border, lighter color
- Transition to deep-dive: cards collapse into progress bar

### Deep-Dive Conversation Polish

- Current pain point always visible in sticky header
- Question shows as "typing..." before appearing
- Smart suggestions: "Tap to answer: Yes / No / It's complex"
- Voice mode: waveform visualization while speaking
- AI acknowledgments reference their words: "So the 8 hours you mentioned is mostly in the data gathering phase..."
- Subtle confidence indicator fills as they provide depth

### Milestone Summary Polish

- Appears with celebration micro-animation
- ROI number animates/counts up
- Finding card has "draft" watermark
- Vendor logos displayed (not just names)
- "Add a note" option for user annotations
- Expand/collapse for full details
- Screenshot/share button

### What Makes It Unique vs. Generic Forms

| Generic | Our Workshop |
|---------|--------------|
| Same questions for everyone | Every question references their specific context |
| Static progress bar | Dynamic: "20 min left for comprehensive report" |
| Submit at end, hope for best | Value delivered every 15-20 minutes (milestones) |
| One input modality | Voice/text/quick-tap seamlessly mixed |
| Form feels like work | Conversation feels like consulting session |
| Results come later | Report preview builds live in front of them |

---

## Technical Architecture

### Frontend Components

```
New Page: WorkshopInterview.tsx (replaces VoiceQuizInterview)
├── Phase1Confirmation/
│   ├── SummaryCard.tsx         # Renders each category
│   ├── AccuracyRating.tsx      # 👍/👎/✏️ controls
│   └── EditModal.tsx           # Inline corrections
│
├── Phase2DeepDive/
│   ├── ConversationView.tsx    # Voice/text chat interface
│   ├── ProgressIndicator.tsx   # Which pain point, % done
│   └── AdaptiveHints.tsx       # Shows detected signals
│
├── MilestoneSummary/
│   ├── FindingPreview.tsx      # Draft finding card
│   ├── ROICalculation.tsx      # Live savings display
│   ├── ConfidenceMeter.tsx     # Per-topic confidence
│   └── NextChoicePrompt.tsx    # Deeper vs. move on
│
└── Phase3Synthesis/
    ├── ReportPreview.tsx       # Section list with confidence
    ├── FinalQuestions.tsx      # Stakeholder, timeline, etc.
    └── CompletionSummary.tsx   # Stats and next steps
```

### Backend Skills

```
src/skills/workshop/
├── __init__.py
├── question_skill.py           # WorkshopQuestionSkill
├── milestone_skill.py          # MilestoneSynthesisSkill
├── confidence_skill.py         # WorkshopConfidenceSkill
└── signal_detector.py          # AdaptiveSignalDetector
```

#### WorkshopQuestionSkill

- **Input:** conversation history, current phase, user signals
- **Output:** next question with adaptive framing
- **Uses:** quiz data, company profile, confidence gaps
- **Extends:** FollowUpQuestionSkill

#### MilestoneSynthesisSkill (NEW)

- **Input:** deep-dive transcript, pain point, industry
- **Output:** draft finding, ROI calculation, recommendations
- **Uses:** knowledge base vendors, industry benchmarks
- **Called:** after each deep-dive completes
- **Model:** Sonnet/Opus (quality matters here)

#### WorkshopConfidenceSkill

- **Input:** full session data, all transcripts
- **Output:** enhanced confidence scores (5 topics + 4 depths)
- **Uses:** topic weights, hard gates, quality multipliers
- **Extends:** InterviewConfidenceSkill

#### AdaptiveSignalDetector (NEW)

- **Input:** quiz answers, company profile, role
- **Output:** `{ technical: bool, budgetReady: bool, decisionMaker: bool }`
- **Called:** once in Phase 1, used throughout Phase 2

### Integration Points

| Existing | Extends/Uses |
|----------|--------------|
| `pre_research_agent.py` | Workshop uses CompanyProfile directly |
| `quiz.py` routes | Workshop `/start` loads quiz answers |
| `interview.py` routes | Workshop routes replace these for paid flow |
| `InterviewConfidenceSkill` | Extended with 4 depth dimensions |
| `FollowUpQuestionSkill` | Extended with adaptive signals |
| `report_service.py` | Receives workshop_data for enhanced generation |
| `knowledge/` vendors & benchmarks | Used by MilestoneSynthesisSkill |

---

## Data Models

### Database Schema Extensions

```sql
-- quiz_sessions table additions
ALTER TABLE quiz_sessions ADD COLUMN IF NOT EXISTS
  workshop_phase TEXT CHECK (workshop_phase IN (
    'confirmation', 'deepdive', 'synthesis', 'complete'
  ));

ALTER TABLE quiz_sessions ADD COLUMN IF NOT EXISTS
  workshop_data JSONB DEFAULT '{}'::jsonb;

ALTER TABLE quiz_sessions ADD COLUMN IF NOT EXISTS
  workshop_confidence JSONB DEFAULT '{}'::jsonb;
```

### workshop_data Structure

```json
{
  "confirmation_ratings": {
    "business": "accurate",
    "pain_points": "edited",
    "tools": "accurate",
    "goals": "inaccurate"
  },
  "corrections": [
    {
      "field": "pain_points",
      "original": "Client reporting takes 8 hrs/week",
      "corrected": "Client reporting takes 12 hrs/week",
      "corrected_at": "2026-01-03T10:15:00Z"
    }
  ],
  "detected_signals": {
    "technical": false,
    "budget_ready": true,
    "decision_maker": true
  },
  "deep_dives": [
    {
      "pain_point_id": "reporting",
      "pain_point_label": "Client Reporting",
      "started_at": "2026-01-03T10:20:00Z",
      "completed_at": "2026-01-03T10:38:00Z",
      "transcript": [...],
      "finding": {
        "title": "Client Reporting Automation Opportunity",
        "current_cost": 31200,
        "potential_savings": 23400,
        "confidence": 0.82
      },
      "user_feedback": "looks_good"
    }
  ],
  "milestones": [
    {
      "pain_point_id": "reporting",
      "finding": {...},
      "roi": {...},
      "vendors": [...],
      "user_feedback": "looks_good",
      "user_notes": null
    }
  ],
  "final_answers": {
    "stakeholders": ["just_me"],
    "timeline": "this_quarter",
    "additions": null
  },
  "duration_minutes": 72,
  "completed_at": "2026-01-03T11:32:00Z"
}
```

### workshop_confidence Structure

```json
{
  "topics": {
    "current_challenges": {
      "coverage": 25,
      "depth": 22,
      "specificity": 20,
      "actionability": 18,
      "total": 85,
      "confidence": 0.85
    },
    "business_goals": {...},
    "team_operations": {...},
    "technology": {...},
    "budget_timeline": {...}
  },
  "depth_dimensions": {
    "integration_depth": 0.78,
    "cost_quantification": 0.92,
    "stakeholder_mapping": 0.65,
    "implementation_readiness": 0.71
  },
  "quality_indicators": {
    "pain_points_extracted": 3,
    "quantifiable_impacts": 4,
    "specific_tools_mentioned": 6,
    "budget_clarity": true,
    "timeline_clarity": true,
    "decision_maker_identified": true
  },
  "overall": {
    "weighted_average": 0.76,
    "quality_multiplier": 1.15,
    "final_score": 0.87,
    "level": "excellent",
    "is_ready_for_report": true
  },
  "hard_gates": {
    "passed": true,
    "failures": []
  }
}
```

---

## API Routes

### New Routes (src/routes/workshop.py)

```python
# Start workshop - returns confirmation data from quiz + research
POST /api/workshop/start
Request: { session_id: str }
Response: {
  company_profile: {...},
  quiz_answers: {...},
  confirmation_cards: [
    { category: "business", items: [...], source_count: 5 },
    { category: "pain_points", items: [...], source_count: 3 },
    ...
  ],
  detected_signals: { technical, budget_ready, decision_maker }
}

# Save confirmation ratings and corrections
POST /api/workshop/confirm
Request: {
  session_id: str,
  ratings: { category: "accurate"|"inaccurate"|"edited" },
  corrections: [ { field, original, corrected } ],
  priority_order: ["reporting", "leads", "proposals"]
}
Response: { success: true, deep_dive_order: [...] }

# Get next question in deep-dive (streaming supported)
POST /api/workshop/respond
Request: {
  session_id: str,
  message: str,
  current_pain_point: str
}
Response: {
  response: str,
  confidence_update: {...},
  should_show_milestone: bool,
  estimated_remaining: "15-20 min"
}

# Generate milestone summary after deep-dive
POST /api/workshop/milestone
Request: {
  session_id: str,
  pain_point_id: str,
  transcript: [...]
}
Response: {
  finding: {...},
  roi: { current_cost, potential_savings, formula },
  recommendations: [...],
  vendors: [...],
  confidence: 0.82
}

# Get current confidence breakdown
GET /api/workshop/confidence/{session_id}
Response: {
  topics: {...},
  depth_dimensions: {...},
  overall: {...},
  suggestions: [...]
}

# Complete workshop and trigger report generation
POST /api/workshop/complete
Request: {
  session_id: str,
  final_answers: {
    stakeholders: [...],
    timeline: str,
    additions: str|null
  }
}
Response: {
  success: true,
  report_eta: "24 hours",
  summary: {
    duration_minutes: 72,
    pain_points_analyzed: 3,
    total_savings: 67400,
    confidence_level: "excellent"
  }
}
```

---

## Robustness & Recovery

### Auto-Save

- Every answer saved within 500ms (debounced)
- Optimistic UI: show saved, retry silently on failure
- Conflict resolution: server wins, notify user if diverged

### Session Recovery

- Page refresh: restore exact position + scroll
- Browser close: email link to resume
- 24hr window to complete (then gentle reminder email)

### Error Handling

- AI timeout: graceful fallback question, retry in background
- TTS failure: seamless switch to text mode
- Network drop: queue messages, sync when reconnected

### Edge Cases

- User provides no data in deep-dive: prompt, then skip
- Conflicting answers: flag and ask for clarification
- Very long answers: chunked processing, no timeout

---

## Performance Targets

| Metric | Target | Approach |
|--------|--------|----------|
| Phase transition | <300ms | Preload next phase data |
| Question generation | <2s | Stream response, show typing indicator |
| Milestone synthesis | <5s | Background processing during last answer |
| Voice transcription | <3s | Optimized Whisper endpoint |
| Auto-save | <500ms | Debounced, background queue |

---

## Implementation Notes

### Priority Order

1. **Phase 1 Confirmation UI** - The "wow" moment, build trust early
2. **Deep-dive conversation with contextual questions** - Core value
3. **Milestone synthesis with real findings** - Proves value mid-workshop
4. **Adaptive signal detection and branching** - Premium personalization
5. **Phase 3 synthesis with report preview** - Strong close
6. **Voice UX polish** - Natural pauses, personality, smooth handoffs

### Model Selection

| Component | Model | Reason |
|-----------|-------|--------|
| Question generation | Haiku 4.5 | Speed matters, context is clear |
| Milestone synthesis | Sonnet 4.5 | Quality matters for findings |
| Confidence analysis | Haiku 4.5 | Structured output, speed |
| Final report preview | Sonnet 4.5 | User-facing summary quality |

### Dependencies

- Existing quiz flow must save CompanyProfile to session
- Knowledge base must have vendor data for top industries
- Report generation must accept workshop_data structure

### Testing Considerations

- Test with users who have varying technical levels
- Test session recovery across browser close/refresh
- Test milestone synthesis quality across industries
- Load test concurrent workshops

---

## Appendix: Key Decisions Made

| Question | Decision | Rationale |
|----------|----------|-----------|
| Additional topics for full report | All 4 (integration, costs, stakeholders, implementation) | Woven naturally, not overwhelming |
| Flow approach | Confirm then explore (hybrid) | Builds trust, prevents wasted deep-dives |
| Adaptation level | Moderate (3 signals) | Meaningful personalization without complexity |
| Visible value | Milestone summaries after each deep-dive | Natural breaks, shows progress, allows correction |
| Completion logic | Adaptive with user choice + quality floor | Respects time while ensuring quality |
| Opening phase | Interactive summary with accuracy ratings | Visual confirmation faster, catches errors early |
