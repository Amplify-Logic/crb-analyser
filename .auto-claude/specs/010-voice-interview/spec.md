# Voice Interview - Consultant-Quality Conversation

## Context
Read CLAUDE.md and docs/plans/2024-12-20-crb-philosophy-framework.md first for full project context.
Read docs/plans/2024-12-20-voice-first-quiz-workshop-design.md for voice design.

The 90-minute interview is where we extract the data that powers the report. It should feel like talking to a brilliant consultant.

## Objective
Create a voice interview experience that feels like a high-quality consulting conversation while extracting maximum useful information.

## Current State
- Interview.tsx and VoiceQuizInterview.tsx
- Deepgram Nova-2 for speech-to-text
- Claude Sonnet 4 for conversation
- Topic tracking (Team, Ops, Tech, Budget, etc.)
- Progress bar (0-100%)

## Deliverables

### 1. Conversation Quality
- Natural, consultant-like dialogue
- Follow-up questions that show understanding
- Acknowledge and build on previous answers
- Summarize and confirm understanding periodically

### 2. Data Extraction Excellence
- Extract specific numbers (team size, revenue, costs)
- Probe for pain points with "tell me more"
- Capture context behind answers
- Note emotional signals (frustration, excitement)

### 3. Topic Coverage
- Ensure all critical topics covered
- Smart topic transitions
- Don't ask what research already revealed
- Depth on high-impact areas, speed on low-impact

### 4. Voice UX Polish
- Clear recording state indicators
- Smooth transitions between speaking/listening
- Handle interruptions gracefully
- Visual feedback during processing

### 5. Session Management
- Save progress (resume if disconnected)
- Transcript available in real-time
- Key insights highlighted during conversation
- Estimated time remaining

## Acceptance Criteria
- [ ] Conversation feels natural and intelligent
- [ ] All critical topics covered by 100% progress
- [ ] Specific numbers captured for calculations
- [ ] Voice input/output works smoothly
- [ ] Session survives browser refresh
- [ ] Transcript captures full conversation

## Files to Modify
- `frontend/src/pages/Interview.tsx`
- `frontend/src/pages/VoiceQuizInterview.tsx`
- `frontend/src/components/voice/*.tsx`
- `backend/src/routes/interview.py`
- Interview system prompts

## Quality Markers
- Less than 2 clarifying re-asks per topic
- Specific numbers captured for 80%+ of quantifiable items
- Customer feels understood and heard
