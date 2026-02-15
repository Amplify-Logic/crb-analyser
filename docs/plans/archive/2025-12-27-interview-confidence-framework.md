# Interview Confidence Framework - Design Document

**Date:** 2025-12-27
**Status:** Implemented
**Author:** Claude Code

---

## Overview

The Interview Confidence Framework ensures high-quality report generation by measuring interview depth and triggering report generation only when sufficient context has been gathered. It integrates human QA review before reports are released to users.

## User Journey (Updated)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           COMPLETE USER FLOW                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  STEP 1: WEB RESEARCH                                                           │
│  └── User enters website → PreResearchAgent scrapes → CompanyProfile            │
│                                                                                 │
│  STEP 2: QUIZ                                                                   │
│  └── Dynamic questions from research → quiz_answers                             │
│                                                                                 │
│  STEP 3: TEASER (Free)                                                          │
│  └── KB-grounded insights → AI Readiness Score + 2 revealed findings            │
│                                                                                 │
│  ════════════════════ PAYWALL (€147) ════════════════════                       │
│                                                                                 │
│  STEP 4: AI INTERVIEW ("90-min Workshop")                                       │
│  └── AI conducts adaptive interview                                             │
│  └── Tracks topic coverage + depth + quality                                    │
│  └── Calculates CONFIDENCE SCORE in real-time                                   │
│  └── When confidence >= 0.60 AND hard gates pass → READY                        │
│                                                                                 │
│  STEP 5: REPORT GENERATION (Automatic Trigger)                                  │
│  └── Triggered when interview confidence threshold met                          │
│  └── Uses KB + RAG + Interview data                                             │
│  └── Status: generating → qa_pending                                            │
│                                                                                 │
│  STEP 6: HUMAN QA REVIEW (24-48 hours)                                          │
│  └── Admin reviews in QA queue                                                  │
│  └── Scores: accuracy, relevance, actionability                                 │
│  └── Approve → status: released → User notified                                 │
│  └── Reject → status: qa_rejected → May regenerate                              │
│                                                                                 │
│  STEP 7: REPORT DELIVERED                                                       │
│  └── User accesses full report                                                  │
│  └── PDF download available                                                     │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Confidence Framework Architecture

### Layer 1: Topic Confidence (Per-Topic Scoring)

Each of 5 interview topics is scored on 4 dimensions:

| Dimension | Max Score | Description |
|-----------|-----------|-------------|
| **Coverage** | 25 | Was the topic discussed at all? |
| **Depth** | 25 | How many substantive exchanges? |
| **Specificity** | 25 | Concrete examples, numbers, names? |
| **Actionability** | 25 | Can we make recommendations from this? |

**Topics:**
1. `current_challenges` (weight: 1.5) - Most important
2. `business_goals` (weight: 1.2) - Important for recommendations
3. `team_operations` (weight: 1.0) - Standard
4. `technology` (weight: 1.0) - Standard
5. `budget_timeline` (weight: 0.8) - Nice to have

### Layer 2: Quality Indicators

Quality multipliers applied to overall score:

| Indicator | Multiplier |
|-----------|------------|
| `pain_points >= 3` | ×1.10 |
| `quantifiable_impacts >= 2` | ×1.10 |
| `specific_tools >= 2` | ×1.05 |
| `budget_clarity` | ×1.05 |
| `timeline_clarity` | ×1.03 |
| `decision_maker` | ×1.02 |

### Layer 3: Overall Readiness

```
OVERALL_SCORE = (weighted_topic_avg) × (quality_multiplier)
```

**Thresholds:**
- `INSUFFICIENT` (0.0 - 0.59): Continue interviewing
- `ACCEPTABLE` (0.60 - 0.79): Can complete if user wants
- `EXCELLENT` (0.80 - 1.0): Ready for report generation

**Hard Gates (Must Pass):**
1. `current_challenges` confidence >= 0.5
2. At least 3 topics with confidence >= 0.4
3. At least 1 pain point extracted

### Layer 4: Trigger Decision

```python
if readiness >= ACCEPTABLE and hard_gates.passed:
    if readiness >= EXCELLENT:
        trigger_report()  # Automatic
    else:
        offer_completion()  # User chooses
else:
    continue_interview()  # Suggest questions
```

---

## Implementation Files

### Models
- `src/models/interview_confidence.py`
  - `TopicConfidence` - Per-topic scoring
  - `QualityIndicators` - Quality multipliers
  - `OverallReadiness` - Aggregate calculation
  - `InterviewCompletionTrigger` - Decision logic
  - `ReportStatus` - Status enum for QA workflow
  - `QAReview` - Human review data

### Skills
- `src/skills/interview/confidence.py`
  - `InterviewConfidenceSkill` - LLM-powered transcript analysis
  - Extracts topic coverage, depth, quality indicators
  - Returns structured confidence data

### Routes
- `src/routes/interview.py` (updated)
  - `GET /confidence/{session_id}` - Calculate confidence
  - `POST /trigger-report` - Trigger generation if ready
  - `GET /readiness-summary/{session_id}` - Quick status check

- `src/routes/admin_qa.py` (new)
  - `GET /queue` - QA review queue
  - `GET /report/{id}` - Full report for QA
  - `POST /review` - Submit approval/rejection
  - `GET /stats` - Queue statistics
  - `POST /regenerate/{id}` - Regenerate rejected report

### Services
- `src/services/report_service.py` (updated)
  - Changed status flow: `generating → qa_pending → released`

---

## API Endpoints

### Interview Confidence

```bash
# Calculate current confidence
GET /api/interview/confidence/{session_id}

# Response:
{
  "session_id": "...",
  "topic_confidences": {
    "current_challenges": {
      "confidence": 0.72,
      "scores": {"coverage": 25, "depth": 18, "specificity": 15, "actionability": 14}
    },
    ...
  },
  "quality_indicators": {
    "pain_points_extracted": 3,
    "quantifiable_impacts": 2,
    "quality_multiplier": 1.21
  },
  "overall_readiness": {
    "final_score": 0.76,
    "level": "acceptable",
    "is_ready_for_report": true,
    "improvement_suggestions": ["Get budget clarity", ...]
  },
  "trigger_decision": {
    "trigger_report": false,
    "next_action": "offer_completion",
    "suggested_questions": [...]
  }
}
```

```bash
# Trigger report generation
POST /api/interview/trigger-report
{
  "session_id": "...",
  "force": false
}

# Response:
{
  "triggered": true,
  "readiness": {"level": "acceptable", "score": 0.76},
  "next_step": "/api/reports/stream/{session_id}"
}
```

### QA Admin

```bash
# Get QA queue
GET /api/admin/qa/queue?status=qa_pending

# Response:
{
  "queue": [
    {
      "report_id": "...",
      "company_name": "Acme Dental",
      "industry": "dental",
      "generated_at": "2025-12-27T10:00:00Z",
      "executive_summary_preview": "..."
    }
  ],
  "total_pending": 5
}
```

```bash
# Submit QA review
POST /api/admin/qa/review
{
  "report_id": "...",
  "approved": true,
  "notes": "Good quality report",
  "accuracy_score": 5,
  "relevance_score": 4,
  "actionability_score": 5
}

# Response:
{
  "success": true,
  "new_status": "released"
}
```

---

## Status Flow

```
quiz_session.status:
  in_progress → pending_payment → paid → interview_in_progress
    → generating → qa_pending → completed (or qa_rejected)

reports.status:
  generating → qa_pending → released (or qa_rejected)
```

---

## Frontend Integration Notes

1. **During Interview:**
   - Call `GET /api/interview/readiness-summary/{id}` periodically
   - Show confidence progress indicator
   - When `is_ready`, show "Generate Report" button

2. **After Interview Complete:**
   - Show "Report is being reviewed by our team"
   - Estimated wait: 24-48 hours
   - Provide preparation instructions

3. **Admin QA Dashboard:**
   - List of pending reports
   - Click to review full report
   - Approve/reject with feedback
   - Statistics on review volume

---

## Testing

```bash
# Test confidence calculation
curl -X GET http://localhost:8383/api/interview/confidence/{session_id}

# Test QA queue
curl -X GET http://localhost:8383/api/admin/qa/queue

# Test report trigger
curl -X POST http://localhost:8383/api/interview/trigger-report \
  -H "Content-Type: application/json" \
  -d '{"session_id": "...", "force": false}'
```

---

## Future Enhancements

1. **Email Notifications:**
   - Notify user when report is released
   - Notify admins when new report enters QA queue

2. **Auto-QA (ML-based):**
   - Train model on QA decisions
   - Auto-approve high-confidence reports
   - Flag edge cases for human review

3. **Feedback Loop:**
   - Track QA rejections by reason
   - Improve generation prompts based on patterns
   - Reduce rejection rate over time
