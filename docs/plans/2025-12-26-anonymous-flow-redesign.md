# Anonymous Flow Redesign

**Date:** 2025-12-26
**Status:** Approved

## Overview

Redesign the user flow so research and quiz are fully anonymous. Account creation happens only at payment. Logged-in users cannot start new audits (cost per report).

## User Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        ANONYMOUS PHASE                          │
├─────────────────────────────────────────────────────────────────┤
│  /start or /quiz                                                │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────────┐   │
│  │ Company     │ → │ Research    │ → │ Quiz                │   │
│  │ Name + URL  │   │ Agent       │   │ (fill gaps)         │   │
│  └─────────────┘   └─────────────┘   └─────────────────────┘   │
│                                              ↓                  │
│                    ┌─────────────────────────────────────────┐  │
│                    │ Email Capture → Free Teaser Report      │  │
│                    │ (AI Score + 2 full findings + blurred)  │  │
│                    └─────────────────────────────────────────┘  │
│                                              ↓                  │
│                    ┌─────────────────────────────────────────┐  │
│                    │ CTA: €147 Report | €497 Report + Call   │  │
│                    └─────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                               ↓ Stripe Payment
┌─────────────────────────────────────────────────────────────────┐
│                      AUTHENTICATED PHASE                        │
├─────────────────────────────────────────────────────────────────┤
│  Account created → Email with login credentials                 │
│                                                                 │
│  /dashboard                                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Workshop (90 min, voice/text/meeting recording)         │   │
│  │ Pausable, resume anytime                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↓ Complete                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Report Generation → Expert Review (Lars & Lennard)      │   │
│  │ 24-48 hours                                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↓ Approved                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Interactive Web Report + Export                         │   │
│  │ €497 tier: Book Strategy Call                           │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Pricing Tiers

| Tier | Price | Includes |
|------|-------|----------|
| Free | €0 | AI Readiness Score + 2 full findings + blurred preview |
| Report Only | €147 | Full report (15-20 findings) via interactive webapp |
| Report + Call | €497 | Full report + 60 min strategy call with founders |

## Database Changes

### 1. Extend `quiz_sessions` table

```sql
-- Add research and teaser columns
ALTER TABLE quiz_sessions ADD COLUMN IF NOT EXISTS company_name TEXT;
ALTER TABLE quiz_sessions ADD COLUMN IF NOT EXISTS website_url TEXT;
ALTER TABLE quiz_sessions ADD COLUMN IF NOT EXISTS company_profile JSONB;
ALTER TABLE quiz_sessions ADD COLUMN IF NOT EXISTS research_completed_at TIMESTAMPTZ;
ALTER TABLE quiz_sessions ADD COLUMN IF NOT EXISTS teaser_report JSONB;
ALTER TABLE quiz_sessions ADD COLUMN IF NOT EXISTS teaser_sent_at TIMESTAMPTZ;

-- Add linking columns (populated after payment)
ALTER TABLE quiz_sessions ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);
ALTER TABLE quiz_sessions ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES workspaces(id);
ALTER TABLE quiz_sessions ADD COLUMN IF NOT EXISTS audit_id UUID REFERENCES audits(id);
ALTER TABLE quiz_sessions ADD COLUMN IF NOT EXISTS paid_at TIMESTAMPTZ;
ALTER TABLE quiz_sessions ADD COLUMN IF NOT EXISTS tier_purchased TEXT;  -- 'report_only' | 'report_plus_call'
```

### 2. Create `interview_responses` table

```sql
CREATE TABLE interview_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    audit_id UUID REFERENCES audits(id) NOT NULL,
    user_id UUID REFERENCES auth.users(id) NOT NULL,

    -- Progress tracking
    status TEXT DEFAULT 'not_started',  -- 'not_started' | 'in_progress' | 'completed'
    current_section INT DEFAULT 0,
    current_question INT DEFAULT 0,
    estimated_time_remaining INT,  -- minutes

    -- Responses
    responses JSONB DEFAULT '{}',  -- {question_id: {answer, mode, audio_url, transcript}}

    -- Audio recordings (Supabase Storage)
    recordings JSONB DEFAULT '[]',  -- [{url, duration, transcript, created_at}]

    -- Timestamps
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS
ALTER TABLE interview_responses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own interview responses"
    ON interview_responses FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Users can insert own interview responses"
    ON interview_responses FOR INSERT
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own interview responses"
    ON interview_responses FOR UPDATE
    USING (user_id = auth.uid());

CREATE POLICY "Service role full access"
    ON interview_responses FOR ALL
    USING (auth.role() = 'service_role');
```

### 3. Extend `audits` table

```sql
ALTER TABLE audits ADD COLUMN IF NOT EXISTS workshop_status TEXT DEFAULT 'pending';
-- Values: 'pending' | 'in_progress' | 'completed'
ALTER TABLE audits ADD COLUMN IF NOT EXISTS workshop_completed_at TIMESTAMPTZ;
ALTER TABLE audits ADD COLUMN IF NOT EXISTS strategy_call_included BOOLEAN DEFAULT FALSE;
ALTER TABLE audits ADD COLUMN IF NOT EXISTS strategy_call_scheduled_at TIMESTAMPTZ;
```

### 4. Extend `reports` table

```sql
ALTER TABLE reports ADD COLUMN IF NOT EXISTS review_status TEXT DEFAULT 'pending';
-- Values: 'pending' | 'in_review' | 'approved' | 'needs_changes'
ALTER TABLE reports ADD COLUMN IF NOT EXISTS reviewer_id UUID;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS reviewer_notes TEXT;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS published_at TIMESTAMPTZ;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS generation_started_at TIMESTAMPTZ;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS generation_completed_at TIMESTAMPTZ;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS generation_error TEXT;
```

## Backend Changes

### 1. Make Research Routes Anonymous

Update `backend/src/routes/research.py`:
- Remove `require_workspace` dependency
- Accept `session_id` parameter instead of auth
- Store research results in `quiz_sessions` table

### 2. Update Quiz Routes

Update `backend/src/routes/quiz.py`:
- Add research step before questions
- Generate teaser report after quiz completion
- Email teaser report to captured email

### 3. Update Payment Webhook

Update `backend/src/routes/payments.py`:
- On successful payment:
  1. Create user account with generated password
  2. Create workspace
  3. Link quiz_session to user
  4. Create audit with `workshop_status: 'pending'`
  5. Send welcome email with credentials

### 4. Add Interview Routes

Create `backend/src/routes/interview.py`:
- `GET /interview/{audit_id}` - Get interview questions and progress
- `POST /interview/{audit_id}/response` - Save response (text/audio)
- `POST /interview/{audit_id}/recording` - Upload meeting recording
- `POST /interview/{audit_id}/complete` - Mark workshop complete, trigger report generation

### 5. Add Admin Review Routes

Update `backend/src/routes/admin.py`:
- `GET /admin/reports/pending` - List reports pending review
- `POST /admin/reports/{id}/approve` - Approve and publish report
- `POST /admin/reports/{id}/reject` - Request changes (internal only)

## Frontend Changes

### 1. Route Protection Updates

```typescript
// Routes that redirect logged-in users away
const anonymousOnlyRoutes = ['/', '/start', '/quiz', '/new-audit'];

// In App.tsx or route guards
if (isAuthenticated && anonymousOnlyRoutes.includes(currentPath)) {
  redirect('/dashboard');
}
```

### 2. Update Quiz Flow

Modify `/quiz` page:
1. Step 1: Company name + website URL
2. Step 2: Research agent (streaming progress)
3. Step 3: Dynamic quiz questions
4. Step 4: Email capture
5. Step 5: Teaser report display + email sent
6. Step 6: Payment CTA

### 3. Dashboard States

```typescript
// Dashboard shows different content based on audit status
if (!audit) {
  // No purchase yet - shouldn't happen if logged in
  redirect('/');
}

if (audit.workshop_status === 'pending' || audit.workshop_status === 'in_progress') {
  // Show workshop CTA
  <WorkshopProgress audit={audit} />
}

if (audit.workshop_status === 'completed' && report.review_status !== 'approved') {
  // Show "pending review" message
  <PendingReview expectedTime="24-48 hours" />
}

if (report.review_status === 'approved') {
  // Show full report
  <InteractiveReport report={report} />
  {audit.strategy_call_included && !audit.strategy_call_scheduled_at && (
    <BookStrategyCall />
  )}
}
```

### 4. Workshop/Interview Page

New `/workshop` page:
- Question list with progress
- Mode selector per question (voice/text)
- Meeting recording option
- Pause/resume functionality
- Completion triggers report generation

## Teaser Report Content

The free teaser report includes:
- **AI Readiness Score** (0-100 with breakdown)
- **2 Full Findings** (complete detail, actionable)
- **Remaining Findings Preview** (titles only, blurred/locked)
- **CTA** to unlock full report

## Email Notifications

| Trigger | Recipient | Content |
|---------|-----------|---------|
| Teaser generated | User | AI score + 2 findings + CTA |
| Payment success | User | Welcome + credentials + workshop link |
| Workshop complete | Lars & Lennard | Review request + admin link |
| Report approved | User | Report ready notification |
| Strategy call (€497) | User | Booking link for call |

## Implementation Order

1. Database migrations
2. Make research routes anonymous (session-based)
3. Update quiz flow with research integration
4. Teaser report generation
5. Payment webhook updates (account creation)
6. Interview/workshop routes and UI
7. Admin review panel
8. Email notifications
9. Route protection updates

## Open Questions

None - design approved.
