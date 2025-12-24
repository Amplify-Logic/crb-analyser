# Quiz Flow - Faster, Smarter, Better

## Context
Read CLAUDE.md and docs/plans/2024-12-20-crb-philosophy-framework.md first for full project context.

The quiz is the free taster that converts visitors to paying customers. It must be fast, engaging, and demonstrate immediate value.

## Objective
Optimize the quiz flow for speed, smarter question generation, and better conversion while gathering quality data.

## Current State
- Quiz.tsx (80KB) - large component handling quiz flow
- Streaming research shows progress
- 5-10 dynamic questions generated
- AI Readiness Score at the end

## Deliverables

### 1. Speed Optimization
- Reduce time from URL entry to first insight
- Optimize research streaming for perceived speed
- Progressive reveal of findings during research
- Preload next question while current is answering

### 2. Smarter Questions
- More relevant questions based on research findings
- Skip questions if answer is obvious from research
- Adaptive depth (fewer questions for simple cases)
- Question priority based on impact on analysis

### 3. Better Question UX
- One question per screen (mobile-first)
- Progress indicator
- Skip option with "assume default"
- Voice input option (leverage existing Deepgram)

### 4. Value Demonstration
- Show insights discovered during research
- Mini-findings that tease full report value
- Competitor mentions found
- Industry context revealed

### 5. Conversion Optimization
- Clear value prop at score reveal
- Urgency/scarcity if appropriate
- Social proof (other businesses analyzed)
- Clear next step CTA

## Acceptance Criteria
- [ ] Time to first insight < 10 seconds
- [ ] 5-7 questions max for typical case
- [ ] Questions feel relevant to THIS business
- [ ] Score reveal feels earned and valuable
- [ ] Mobile experience is excellent
- [ ] Conversion rate trackable

## Files to Modify
- `frontend/src/pages/Quiz.tsx`
- `backend/src/routes/quiz.py`
- `backend/src/agents/pre_research_agent.py`
- `frontend/src/components/quiz/*.tsx` if they exist

## Metrics to Track
- Time to complete quiz
- Drop-off at each question
- Conversion to paid
- Score distribution
