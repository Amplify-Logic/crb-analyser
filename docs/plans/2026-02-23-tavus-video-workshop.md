# Tavus Video Workshop Integration

> **Status:** Parked — revisit when launching €497 tier (after 50+ reports delivered)
> **Date:** 2026-02-23
> **Effort:** ~2 days integration

---

## What is Tavus?

Real-time AI video avatar platform. You define a **Persona** (behavior/knowledge) + **Replica** (visual avatar) and get a WebRTC video conversation with ~600ms latency.

- React SDK: `@tavus/cvi-ui` (`CVIProvider`, `Conversation` components)
- 30+ languages, 100+ stock replicas
- Custom LLM integration supported (bring your own backend)
- Perception layer reads facial cues, gaze, body language
- Docs: https://docs.tavus.io

---

## Why

- 90 minutes of text chat is exhausting — video feels like a real consulting session
- Differentiator: nobody delivers AI business analysis via video avatar
- Perception layer detects confusion/engagement → better workshop outcomes
- Tavus is the **face**, our workshop engine stays the **brain**

---

## Integration Design

### Architecture

```
User (browser)
  ↕ WebRTC (Daily)
Tavus CVI Layer (avatar, TTS, STT, perception)
  ↕ Custom LLM webhook
Our Backend (workshop engine, milestones, knowledge base)
  ↓
Report Pipeline (transcript → analysis → report)
```

**Key principle:** Tavus handles video/audio/avatar. Our existing workshop logic (`workshop.py`, milestone skills, industry knowledge) handles all reasoning via custom LLM integration.

### Flow

1. User pays → workshop session created
2. Backend creates Tavus Conversation:
   ```
   POST https://tavusapi.com/v2/conversations
   Headers: { "x-api-key": TAVUS_API_KEY }
   Body: { "replica_id": "...", "persona_id": "..." }
   Response: { "conversation_url": "https://..." }
   ```
3. Frontend embeds via React SDK:
   ```tsx
   import { CVIProvider, Conversation } from '@tavus/cvi-ui';

   <CVIProvider>
     <Conversation conversationUrl={url} />
   </CVIProvider>
   ```
4. Tavus STT → our LLM endpoint → Tavus TTS + avatar
5. Full transcript captured → fed into report generation pipeline

### Backend Changes

| File | Change |
|------|--------|
| `backend/src/config/settings.py` | Add `TAVUS_API_KEY`, `TAVUS_REPLICA_ID` |
| `backend/src/services/tavus_service.py` | **New** — create personas, start/end conversations |
| `backend/src/routes/workshop.py` | Add video workshop mode (opt-in) |
| `backend/src/skills/workshop/` | No changes — skills stay the same |

### Frontend Changes

| File | Change |
|------|--------|
| `package.json` | Add `@tavus/cvi-ui` |
| `frontend/src/pages/Workshop.tsx` | Add video mode toggle + Tavus embed |
| `frontend/src/services/workshopApi.ts` | Add `startVideoWorkshop()` endpoint call |

### Persona Configuration

The Tavus Persona maps directly to our workshop system prompt:

```json
{
  "persona_name": "CRB Workshop Advisor",
  "system_prompt": "<existing workshop system prompt>",
  "context": "<industry knowledge + quiz answers>",
  "default_language": "en",
  "max_call_duration": 5400,
  "enable_recording": true,
  "llm_type": "custom",
  "custom_llm_url": "https://api.readypath.io/api/workshop/tavus-llm"
}
```

---

## Pricing

| Tavus Plan | Cost/min | 90-min session | % of €147 | % of €497 |
|------------|----------|----------------|-----------|-----------|
| Growth ($397/mo) | $0.32 | ~$29 | 20% | 6% |
| Starter ($59/mo) | $0.37 | ~$33 | 23% | 7% |

**Conclusion:** Not viable at €147 tier. Works at €497 tier (~6% of revenue).

### Free tier for prototyping
- 25 min/month conversational video — enough to build and demo

---

## Rollout Plan

### Phase 1: Prototype (1 day)
- [ ] Sign up for Tavus free tier
- [ ] Create test Persona with workshop system prompt
- [ ] Pick stock Replica
- [ ] Build minimal React embed page
- [ ] Test 10-minute conversation manually

### Phase 2: Integrate (1 day)
- [ ] Create `tavus_service.py` (create persona, start/end conversation)
- [ ] Add custom LLM webhook endpoint in `workshop.py`
- [ ] Wire transcript capture into report pipeline
- [ ] Add video mode toggle to Workshop.tsx

### Phase 3: Ship (with €497 tier launch)
- [ ] Upgrade to Growth plan
- [ ] Enable conversation recordings ($0.03/min)
- [ ] A/B test text vs video workshop completion rates
- [ ] Monitor transcript quality vs text chat quality

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Tavus latency spikes | Fallback to text workshop (already built) |
| Custom LLM integration complexity | Test with their sandbox first |
| Avatar feels uncanny | Use stock replicas — they're well-trained |
| Cost overruns on long sessions | Set `max_call_duration` + milestone-based pacing |
| Transcript quality < text input | Record + post-process with Whisper as backup |

---

## Decision Criteria (When to Build)

Build this when ALL are true:
- [ ] 50+ reports delivered via current flow
- [ ] Launching €497 "Report + Call" tier
- [ ] Workshop completion rate is a known bottleneck
- [ ] Tavus pricing hasn't increased significantly
