# Voice-First Quiz & Workshop Design

**Date:** 2024-12-20
**Status:** Approved

## Overview

Transform the CRB Analyser from form-based input to voice-first conversational experience.

## User Flow

```
┌──────────────────────────────────────────────────────────────┐
│                      PRE-PAYMENT                              │
├──────────────────────────────────────────────────────────────┤
│  1. Website Entry         → Enter company URL                 │
│  2. AI Research           → ~60 sec analysis                  │
│  3. Voice Quiz Interview  → ~5 min, voice-first conversation  │
│  4. Sales Preview         → Genuine insights, AI readiness    │
│  5. Payment               → Stripe checkout                   │
├──────────────────────────────────────────────────────────────┤
│                      POST-PAYMENT                             │
├──────────────────────────────────────────────────────────────┤
│  6. Full Workshop         → 90-min deep voice interview       │
│  7. Report Generation     → AI processes everything           │
│  8. Interactive Report    → Full web UI with all tabs         │
└──────────────────────────────────────────────────────────────┘
```

## Two Voice Experiences

| | Quiz Interview | Full Workshop |
|---|---|---|
| **Duration** | ~5 minutes | ~90 minutes |
| **Purpose** | Demonstrate value | Comprehensive discovery |
| **Depth** | Surface-level insights | Deep business analysis |
| **Output** | Sales preview | Full interactive report |
| **Input modes** | Voice / Text | Voice / Text / Upload recording |

## Voice Quiz Interview (~5 min)

### Entry Screen
- Clean, minimal design
- Large microphone button as primary CTA
- "Prefer to type?" link below
- "Upload a recording" and "Record a conversation" as secondary options

### Conversation Flow
1. **Warm-up prompt**: "Tell me about your business and what brought you here today"
2. **AI-led follow-ups**: 4-6 targeted questions based on response + research
3. **Gap-filling**: Specific questions for missed topics

### Input Modes
1. **Voice (primary)** - Tap to record, tap to stop
2. **Text (fallback)** - Type responses instead
3. **Upload recording** - Upload MP3/WAV of existing meeting
4. **Live recording** - Record a conversation with colleague/client

### UI States
- **Idle**: Large mic button, "Tap to talk"
- **Recording**: Red button, waveform animation, timer, "Tap to stop"
- **Transcribing**: Spinner, "Processing..."
- **AI Responding**: Typing indicator, then response appears

## Full Workshop (~90 min)

### Sections (~15 min each)
1. **Introduction** - Warm-up, confirm research findings
2. **Operations** - Day-to-day processes, pain points
3. **Technology** - Current tools, integrations, data
4. **Goals** - What success looks like, priorities
5. **Budget & Timeline** - Investment capacity, urgency
6. **Wrap-up** - Anything missed, final thoughts

### Features
- **Progress indicator** - Visual dots showing current section
- **Time estimate** - Updates based on conversation pace
- **Break button** - Pause and resume later
- **Upload mid-session** - Can upload recording at any point
- **Conversation history** - Scrollable chat-style view

### UI Layout
```
┌─────────────────────────────────────────────────────────────┐
│  Header: Logo + Section Progress + Time Remaining           │
├─────────────────────────────────────────────────────────────┤
│  Conversation Area (scrollable chat bubbles)                │
├─────────────────────────────────────────────────────────────┤
│  Input Area: Mic button + Type/Break/Upload options         │
└─────────────────────────────────────────────────────────────┘
```

## Technical Implementation

### Frontend Components
- `VoiceQuizInterview.tsx` - New component for quiz phase
- `Workshop.tsx` - Enhanced interview page for 90-min session
- `VoiceRecorder.tsx` - Shared mic button with waveform
- `AudioUploader.tsx` - Upload/record meeting component
- `ConversationView.tsx` - Chat-style message display

### Backend Endpoints
- `POST /api/interview/transcribe` - Already exists (Deepgram)
- `POST /api/interview/respond` - Already exists (Claude)
- `POST /api/interview/upload-recording` - NEW: Process uploaded audio
- `POST /api/workshop/section-complete` - NEW: Track workshop progress

### Audio Processing
- **Live voice**: Deepgram Nova-2 for real-time transcription
- **Uploaded files**: Same Deepgram endpoint, supports MP3/WAV/M4A
- **Long recordings**: Chunk and process, extract key insights

## Design Principles

1. **Voice-first, not voice-only** - Always provide text fallback
2. **Sleek and minimal** - No clutter, focus on conversation
3. **Progress visibility** - Users always know where they are
4. **Graceful degradation** - Works even if mic fails
5. **Mobile-friendly** - Large touch targets for mic button
