# Workshop Overhaul — "Super Onto It + Engaging"

> **Status:** Ready for execution
> **Created:** 2026-02-28
> **Scope:** 21 improvements across 4 tiers, identified by 4-agent audit team
> **Execution:** `/execute docs/plans/2026-02-28-workshop-overhaul.md`

---

## CRB Context

- **Affected user journey:** Workshop (post-quiz, pre-report)
- **Industries impacted:** All
- **Reference docs to load:**
  - `.claude/reference/api-development.md` (backend routes/services)
  - `.claude/reference/frontend-development.md` (React components)
  - `.claude/reference/report-quality.md` (report generation)
  - `.claude/reference/vendor-management.md` (vendor DB queries)

## Rollback Plan

All changes are additive (new functions, new props, new components). No destructive changes to existing behavior. Revert by reverting the commits per batch.

---

## Batch 1: Wire What's Already Built (Showstoppers)

> **Goal:** Fix the 3 showstoppers that undermine the entire workshop value proposition.
> **Estimated effort:** 2-3 days

### Task 1.1: Wire Workshop Data into Report Generation

**Problem:** Users invest 90 minutes in the workshop. `report_service.py` has ZERO references to `workshop_data`. The report ignores everything discussed.

**Files to modify:**
- `backend/src/services/report_service.py` — lines 253-321 (`_get_skill_context`), lines 508-528 (data loading), line 1652 (`_generate_findings`)

**Implementation:**

1. **Load workshop data alongside quiz data** in `report_service.py` around line 515:

```python
# After loading quiz_data (line 515)
workshop_data = quiz_session.get("workshop_data", {})
self.workshop_data = workshop_data
```

2. **Inject workshop context into `_get_skill_context()`** around line 253:

```python
# Add to the skill context builder
workshop_findings = []
if self.workshop_data:
    for milestone in self.workshop_data.get("milestones", []):
        workshop_findings.append({
            "pain_point": milestone.get("pain_point_label"),
            "finding": milestone.get("finding"),
            "roi": milestone.get("roi"),
            "vendors": milestone.get("vendors"),
            "user_feedback": milestone.get("user_feedback"),
            "user_notes": milestone.get("user_notes"),
        })

    # Add deep-dive transcripts as enrichment
    for dd in self.workshop_data.get("deep_dives", []):
        workshop_findings.append({
            "pain_point": dd.get("pain_point_label"),
            "transcript_summary": dd.get("transcript", [])[-5:],  # Last 5 messages
            "finding": dd.get("finding"),
        })
```

3. **Pass workshop data to findings generation** in `_generate_findings()` around line 1652:

```python
# Include workshop milestones as pre-validated findings
# Workshop findings should be prioritized since user confirmed them
if self.workshop_data and self.workshop_data.get("milestones"):
    context["workshop_validated_findings"] = self.workshop_data["milestones"]
    context["workshop_confidence"] = self.workshop_data.get("confidence", {})
```

4. **Add workshop-enriched prompt section** to the findings generation prompt — instruct the LLM to use workshop data as primary source and fill gaps with analysis.

**Verification:**
- Generate a report for a session that has workshop_data — confirm findings reference workshop milestones
- Generate a report for a session WITHOUT workshop_data — confirm no regression
- Check that workshop ROI numbers appear in report ROI section

---

### Task 1.2: Restore Conversation on Resume

**Problem:** Transcripts ARE saved server-side in `workshop_data.deep_dives[i].transcript` but the frontend always starts fresh with a greeting message.

**Files to modify:**
- `frontend/src/components/workshop/WorkshopDeepDive.tsx` — lines 80-94 (useEffect initialization)
- `backend/src/routes/workshop.py` — need endpoint to return existing transcript

**Implementation:**

1. **Add API endpoint** to retrieve existing deep-dive state in `workshop.py`:

```python
@router.get("/deepdive/{session_id}/{pain_point_index}")
async def get_deepdive_state(session_id: str, pain_point_index: int):
    """Return existing conversation state for a deep-dive if it exists."""
    session = await get_session(session_id)
    workshop_data = session.get("workshop_data", {})
    deep_dives = workshop_data.get("deep_dives", [])

    for dd in deep_dives:
        if dd.get("pain_point_index") == pain_point_index:
            return {
                "exists": True,
                "transcript": dd.get("transcript", []),
                "conversation_stage": dd.get("conversation_stage", "current_state"),
                "confidence": dd.get("confidence"),
            }
    return {"exists": False}
```

2. **Modify WorkshopDeepDive useEffect** (line 80-94) to check for existing conversation:

```typescript
useEffect(() => {
  const loadExistingConversation = async () => {
    try {
      const res = await fetch(
        `${API_BASE}/api/workshop/deepdive/${sessionId}/${currentIndex}`
      )
      const data = await res.json()

      if (data.exists && data.transcript.length > 0) {
        // Restore from server
        const restored: Message[] = data.transcript.map((msg: any, i: number) => ({
          id: `restored-${i}`,
          role: msg.role,
          content: msg.content,
        }))
        setMessages(restored)
        setConfidence(data.confidence)
        return
      }
    } catch {
      // Fall through to greeting
    }

    // Fresh start
    const greeting: Message = {
      id: `greeting-${currentIndex}`,
      role: 'assistant',
      content: `Great, let's talk about **${currentPainPoint?.label}**...`,
    }
    setMessages([greeting])
    setConfidence(null)
  }

  loadExistingConversation()
}, [currentIndex, currentPainPoint?.label, sessionId])
```

**Verification:**
- Start a deep-dive, send 3 messages, refresh the page — messages should restore
- Start a brand new deep-dive — should show greeting as before
- Resume from a different pain point — should load correct conversation

---

### Task 1.3: Wire Milestone "Needs Edit" to Re-enter Conversation

**Problem:** Backend generates followup questions when user says "needs_edit". Frontend calls `onContinue()` regardless of feedback type.

**Files to modify:**
- `frontend/src/components/workshop/WorkshopMilestone.tsx` — lines 134-159 (`handleContinue`)
- `frontend/src/pages/Workshop.tsx` — lines 216-230 (`handleMilestoneContinue`)

**Implementation:**

1. **Modify `handleContinue` in WorkshopMilestone.tsx** to pass feedback type:

```typescript
// Change onContinue prop type from () => void to (feedback: string) => void
const handleContinue = async () => {
  if (!feedback) return
  setIsSubmitting(true)

  try {
    const res = await fetch(`${API_BASE}/api/workshop/milestone/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        pain_point_id: painPointId,
        feedback,
        notes,
      }),
    })
    const data = await res.json()
    // Pass feedback type so parent can decide to re-enter deepdive
    onContinue(feedback)
  } catch (err) {
    console.error('Milestone feedback failed:', err)
    onContinue(feedback) // Continue even on failure
  } finally {
    setIsSubmitting(false)
  }
}
```

2. **Modify `handleMilestoneContinue` in Workshop.tsx** (line 216):

```typescript
const handleMilestoneContinue = (feedback: string) => {
  if (feedback === 'needs_edit') {
    // Re-enter deepdive for the SAME pain point (don't advance index)
    // Backend will generate followup questions targeting data gaps
    setPhase('deepdive')
    return
  }

  // Original logic: advance to next pain point or synthesis
  const nextIndex = state.currentPainPointIndex + 1
  if (nextIndex >= state.painPoints.length) {
    setPhase('synthesis')
  } else {
    setState(prev => ({ ...prev, currentPainPointIndex: nextIndex }))
    setPhase('deepdive')
  }
  setState(prev => ({ ...prev, milestonePainPointId: null }))
}
```

**Verification:**
- Click "Needs adjustments" on a milestone — should return to deep-dive for the SAME pain point
- Click "Looks good" — should advance to next pain point or synthesis
- After re-entering deep-dive from "needs edit", complete it — should show updated milestone

---

### Task 1.4: Make Data Gaps Actionable

**Problem:** Milestone shows data gaps as a static yellow box. Backend has followup question generation targeting gaps, but frontend doesn't use it.

**Files to modify:**
- `frontend/src/components/workshop/WorkshopMilestone.tsx` — lines 368-391 (data gaps display)

**Implementation:**

Replace static data gap display with interactive buttons:

```typescript
{/* Data Gaps - Make actionable */}
{dataGaps && dataGaps.length > 0 && (
  <motion.div variants={staggerItem} className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
    <h4 className="font-medium text-yellow-800 mb-2">
      Want to strengthen this analysis?
    </h4>
    <div className="space-y-2">
      {dataGaps.map((gap, i) => (
        <button
          key={i}
          onClick={() => {
            // Set feedback to needs_edit with specific gap context
            setFeedback('needs_edit')
            setNotes(`I want to provide more detail about: ${gap}`)
          }}
          className="w-full text-left px-3 py-2 bg-white rounded-lg border border-yellow-200
                     hover:border-yellow-400 hover:bg-yellow-50 transition-colors text-sm text-yellow-900"
        >
          Tell me more about: {gap}
        </button>
      ))}
    </div>
  </motion.div>
)}
```

**Verification:**
- Milestone with data gaps shows clickable buttons instead of static list
- Clicking a gap button sets feedback to "needs_edit" with gap context
- After submitting, deep-dive resumes targeting that specific gap

---

### Task 1.5: Add beforeunload Handler

**Problem:** No warning when user accidentally closes tab during 90-minute workshop.

**Files to modify:**
- `frontend/src/pages/Workshop.tsx` — add useEffect near top of component

**Implementation:**

```typescript
// Add near other useEffects
useEffect(() => {
  const activePhases: WorkshopPhase[] = ['confirmation', 'deepdive', 'milestone', 'synthesis']

  if (!activePhases.includes(phase)) return

  const handleBeforeUnload = (e: BeforeUnloadEvent) => {
    e.preventDefault()
    e.returnValue = '' // Chrome requires this
  }

  window.addEventListener('beforeunload', handleBeforeUnload)
  return () => window.removeEventListener('beforeunload', handleBeforeUnload)
}, [phase])
```

**Verification:**
- During active workshop phase, try closing tab — browser should show "Leave site?" dialog
- On welcome/complete phases, no dialog should appear

---

## Batch 2: Make It Feel Like Consulting (UX + Personality)

> **Goal:** Transform the workshop from a robotic Q&A into a premium consulting experience.
> **Estimated effort:** 1-2 weeks

### Task 2.1: Consultant Personality in Prompts

**Problem:** Current prompt says "be conversational and warm" — that's the entire personality guidance. No industry expertise signaling, no emotional intelligence, no consultant persona.

**Files to modify:**
- `backend/src/skills/workshop/question_skill.py` — lines 111-154 (system prompt template)
- `backend/src/skills/workshop/milestone_skill.py` — lines 287-293 (milestone prompt)

**Implementation:**

1. **Rewrite the question skill system prompt** (question_skill.py, replace lines 111-154):

```python
def _build_system_prompt(self, signals: Dict, stage: str, pain_label: str,
                         company_name: str, industry: str) -> str:
    prompt = f"""You are a senior technology strategist at a boutique consulting firm,
conducting a deep-dive discovery session with {company_name}.

YOUR PERSONA:
- You've consulted for 100+ {industry} businesses on technology transformation
- You're direct but empathetic — you genuinely care about their success
- You demonstrate expertise by connecting their situation to patterns you've seen
- You challenge assumptions when needed: "Many firms think X, but we find Y works better"
- You celebrate good insights: "That's a significant finding" / "Most firms miss this"

CONVERSATION RULES:
- Ask ONE question at a time
- Keep questions under 40 words (allow context that shows you listened)
- Reference specific details they shared — use their exact words and numbers
- When they share a number, validate it: "6 hours a week — that's over 300 hours a year"
- When you detect frustration, acknowledge it before asking more
- When you detect enthusiasm, build on it
- Inject industry context: "In {industry}, the benchmark for this is typically..."

WHAT MAKES YOU DIFFERENT FROM A CHATBOT:
- You proactively surface implications they haven't considered
- You challenge vague answers: "When you say 'a lot of time', can you estimate hours per week?"
- You connect dots across topics: "This reminds me of what you said about [earlier topic]..."
- You share relevant patterns: "I see this exact problem in about 70% of {industry} firms"
"""

    # Signal-based personality tuning
    if signals.get("technical"):
        prompt += """
TECHNICAL USER DETECTED:
- Use precise technical terminology (APIs, integrations, data flows, webhooks)
- Ask about system architecture and data model
- Probe about build vs. buy trade-offs
- Reference specific technologies and their limitations
"""
    else:
        prompt += """
BUSINESS-FOCUSED USER DETECTED:
- Focus on outcomes, not technology details
- Translate technical concepts to business impact
- Ask about team adoption and change management
- Use analogies to explain complex integrations
"""

    if signals.get("budget_ready"):
        prompt += """
BUDGET-READY USER:
- Discuss implementation timelines and phased rollouts
- Compare build vs. buy economics
- Explore ROI expectations and payback periods
- Ask about internal resources available for implementation
"""
    else:
        prompt += """
BUDGET-EXPLORING USER:
- Focus on quick wins with immediate ROI
- Emphasize free tiers and low-cost starting points
- Help them build the internal business case
- Ask what would unlock more budget: "If you could show your team that X saves Y hours..."
"""

    if signals.get("decision_maker"):
        prompt += """
DECISION-MAKER:
- Focus on strategic impact and competitive advantage
- Ask about board/partner priorities
- Discuss risk tolerance and change appetite
"""
    else:
        prompt += """
INFLUENCER (NOT FINAL DECISION-MAKER):
- Help them build the case for decision-makers
- Ask what their boss/partner would need to see
- Focus on measurable outcomes they can present
"""

    return prompt
```

2. **Rewrite the milestone synthesis prompt** (milestone_skill.py, replace lines 287-293):

```python
prompt = f"""You are a senior technology strategist synthesizing a discovery conversation
into an actionable insight for {company_name} ({industry}).

Write as if presenting to the client — use THEIR words, reference THEIR specific numbers
and examples. The finding should make them think "this consultant really understands my business."

When calculating ROI:
- Use their actual numbers when provided (quote them)
- If estimating, clearly state your assumptions
- Include a conservative and optimistic scenario
- Factor in the {industry} benchmark when relevant
- Consider both time savings AND revenue/quality impact

Your tone: confident, data-driven, but accessible. Not academic — practical.
"""
```

**Verification:**
- Run a test workshop conversation — AI should reference industry patterns, challenge vague answers, and use consultant language
- Compare tone before/after — should feel like talking to a person, not a form

---

### Task 2.2: Quick-Reply Suggestion Chips

**Problem:** After each AI question, users face a blank text input. The "blank page" problem causes hesitation and drop-off. Typeform data shows suggestion chips improve completion by 40%.

**Files to modify:**
- `backend/src/routes/workshop.py` — modify `/respond` endpoint to return suggestions
- `frontend/src/components/workshop/WorkshopDeepDive.tsx` — add chip UI below messages

**Implementation:**

1. **Backend: Return suggestions with each AI response** (workshop.py, in the respond endpoint around line 440):

```python
# After generating the question, generate 2-3 quick-reply options
suggestions = await self._generate_suggestions(
    question=ai_question,
    stage=conversation_stage,
    pain_label=pain_point_label,
    industry=industry,
)

return {
    "response": ai_question,
    "suggestions": suggestions,  # ["We use spreadsheets", "It's mostly manual", "We tried a tool but..."]
    "confidence_update": confidence,
    "estimated_remaining": remaining,
    "should_show_milestone": should_show,
}
```

Add helper method:

```python
async def _generate_suggestions(self, question: str, stage: str,
                                 pain_label: str, industry: str) -> List[str]:
    """Generate 2-3 contextual quick-reply suggestions for the current question."""
    stage_suggestions = {
        "current_state": [
            "We handle it manually",
            f"We use a basic tool for this",
            "It's spread across multiple systems",
        ],
        "failed_attempts": [
            "We haven't tried anything yet",
            "We tried a tool but it didn't work",
            "We looked into it but it seemed too complex",
        ],
        "cost_impact": [
            "A few hours per week",
            "It's more about errors than time",
            "Hard to quantify but it's significant",
        ],
        "ideal_state": [
            "Fully automated",
            "Just need it to be faster",
            "Better visibility and reporting",
        ],
        "stakeholders": [
            "Just me",
            "My team and I decide together",
            "Need buy-in from leadership",
        ],
    }
    return stage_suggestions.get(stage, [])[:3]
```

2. **Frontend: Render suggestion chips** in WorkshopDeepDive.tsx, below the messages and above the input:

```typescript
// Add state for suggestions
const [suggestions, setSuggestions] = useState<string[]>([])

// In processUserMessage, after parsing response:
setSuggestions(data.suggestions || [])

// Render chips between messages and input area
{suggestions.length > 0 && !isProcessing && (
  <div className="flex flex-wrap gap-2 px-4 pb-2">
    {suggestions.map((suggestion, i) => (
      <button
        key={i}
        onClick={() => {
          setTextInput(suggestion)
          setSuggestions([])
          processUserMessage(suggestion)
        }}
        className="px-3 py-1.5 text-sm bg-white border border-gray-200 rounded-full
                   hover:border-primary-400 hover:bg-primary-50 transition-colors
                   text-gray-700 hover:text-primary-700"
      >
        {suggestion}
      </button>
    ))}
  </div>
)}
```

**Verification:**
- Each AI question should display 2-3 suggestion chips below it
- Tapping a chip should send it as the user's response
- Chips should disappear when user starts typing manually
- Chips should be contextually appropriate per conversation stage

---

### Task 2.3: Streaming Responses (SSE)

**Problem:** AI responses load as a single block after full processing. Users see bouncing dots for 3-10 seconds. Every modern AI product streams responses.

**Files to modify:**
- `backend/src/routes/workshop.py` — add streaming endpoint
- `frontend/src/components/workshop/WorkshopDeepDive.tsx` — use EventSource

**Implementation:**

1. **Backend: Add streaming workshop respond endpoint** (workshop.py):

```python
from fastapi.responses import StreamingResponse

@router.post("/respond/stream")
async def respond_stream(request: WorkshopRespondRequest):
    """Stream the workshop AI response token by token."""
    # Same setup as /respond — load session, detect stage, etc.
    session = await get_session(request.session_id)
    # ... existing setup logic ...

    async def event_generator():
        # Stream the LLM response
        async for chunk in question_skill.execute_streaming(context):
            yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

        # After streaming complete, send metadata
        yield f"data: {json.dumps({
            'type': 'complete',
            'suggestions': suggestions,
            'confidence_update': confidence,
            'estimated_remaining': remaining,
            'should_show_milestone': should_show,
        })}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

2. **Frontend: Replace fetch with EventSource** in WorkshopDeepDive.tsx:

```typescript
const processUserMessage = async (text: string) => {
  // Create user message (same as before)
  const userMsg: Message = { id: `user-${Date.now()}`, role: 'user', content: text }
  setMessages(prev => [...prev, userMsg])
  setIsProcessing(true)
  setSuggestions([])

  // Create placeholder assistant message for streaming
  const assistantId = `assistant-${Date.now()}`
  setMessages(prev => [...prev, { id: assistantId, role: 'assistant', content: '' }])

  try {
    const res = await fetch(`${API_BASE}/api/workshop/respond/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        message: text,
        current_pain_point: currentPainPoint?.id,
      }),
    })

    const reader = res.body!.getReader()
    const decoder = new TextDecoder()
    let accumulated = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const data = JSON.parse(line.slice(6))

        if (data.type === 'token') {
          accumulated += data.content
          setMessages(prev => prev.map(m =>
            m.id === assistantId ? { ...m, content: accumulated } : m
          ))
        } else if (data.type === 'complete') {
          setSuggestions(data.suggestions || [])
          if (data.confidence_update) setConfidence(data.confidence_update)
          if (data.should_show_milestone) onMilestoneReady(currentPainPoint!.id)
        }
      }
    }
  } catch (err) {
    // Fallback to non-streaming endpoint
    // ... existing processUserMessage logic as fallback ...
  } finally {
    setIsProcessing(false)
  }
}
```

**Verification:**
- AI responses should appear word-by-word (streaming)
- If streaming fails, should fallback to non-streaming endpoint gracefully
- Suggestions and metadata should arrive after stream completes

---

### Task 2.4: Phase 3 Report Preview (Replace SynthesisForm)

**Problem:** After 60+ minutes of conversational deep-dive, users get a jarring 3-field HTML form. The design specified an elaborate report preview with combined savings, confidence per section, and a strong close.

**Files to modify:**
- `frontend/src/components/workshop/SynthesisForm.tsx` — full rewrite
- `backend/src/routes/workshop.py` — add endpoint to build report preview data

**Implementation:**

1. **Backend: Add report preview endpoint** (workshop.py):

```python
@router.get("/preview/{session_id}")
async def get_report_preview(session_id: str):
    """Build a preview of what the report will contain based on workshop data."""
    session = await get_session(session_id)
    workshop_data = session.get("workshop_data", {})
    milestones = workshop_data.get("milestones", [])
    confidence = workshop_data.get("confidence", {})

    # Calculate combined savings
    total_savings = sum(
        m.get("roi", {}).get("potential_savings", 0)
        for m in milestones
    )

    # Build findings summary
    findings = []
    for m in milestones:
        finding = m.get("finding", {})
        roi = m.get("roi", {})
        severity = finding.get("pain_severity", "medium")

        # Classify: quick_win (< 5hrs/wk, high savings%), high_roi (largest savings), strategic (rest)
        badge = "strategic"
        if roi.get("hours_per_week", 0) < 5 and roi.get("savings_percentage", 0) > 70:
            badge = "quick_win"
        elif roi.get("potential_savings", 0) == max(
            m2.get("roi", {}).get("potential_savings", 0) for m2 in milestones
        ):
            badge = "high_roi"

        findings.append({
            "title": finding.get("title", "Untitled"),
            "savings": roi.get("potential_savings", 0),
            "badge": badge,
            "severity": severity,
            "vendors": m.get("vendors", [])[:2],
        })

    # Report sections with confidence estimates
    sections = [
        {"name": "Executive Summary", "confidence": min(confidence.get("overall", 70), 95)},
        {"name": "Current State Analysis", "confidence": confidence.get("topics", {}).get("current_challenges", {}).get("coverage", 60)},
        {"name": "AI Opportunities", "confidence": confidence.get("topics", {}).get("business_goals", {}).get("coverage", 60), "finding_count": len(findings)},
        {"name": "Vendor Recommendations", "confidence": confidence.get("topics", {}).get("technology", {}).get("coverage", 50)},
        {"name": "Implementation Roadmap", "confidence": confidence.get("topics", {}).get("budget_timeline", {}).get("coverage", 50)},
        {"name": "ROI Projections", "confidence": confidence.get("overall", 60)},
    ]

    return {
        "company_name": session.get("company_name", "Your Company"),
        "total_savings": total_savings,
        "findings": findings,
        "sections": sections,
        "duration_minutes": workshop_data.get("duration_minutes"),
        "pain_points_analyzed": len(milestones),
    }
```

2. **Frontend: Rewrite SynthesisForm** as a rich report preview:

```typescript
// SynthesisForm.tsx — full rewrite
// Show report preview ABOVE the final questions
// Include: findings summary cards, combined ROI hero number,
// section confidence indicators, then final questions at bottom

// Structure:
// 1. Hero: "Your analysis is ready" + total savings with count-up
// 2. Findings grid: cards per pain point with badge (Quick Win / High ROI / Strategic)
// 3. Report sections: list with confidence bar per section
// 4. Workshop stats footer: duration, confidence, pain points
// 5. Final questions (same 3 fields but as conversational cards, not form)
// 6. CTA: "Generate My Report"
```

The full component implementation should:
- Fetch from `GET /api/workshop/preview/{sessionId}` on mount
- Display total savings as hero number
- Show each finding as a card with badge and vendor logos
- Show report sections with confidence bars
- Present final questions as individual animated cards (not a flat form)
- Show workshop stats footer (duration, confidence, pain points analyzed)

**Verification:**
- Synthesis phase shows rich report preview, not bare form
- Total savings number is correct sum of all milestone ROIs
- Confidence bars reflect actual workshop data quality
- Final questions still work and pass data to handleComplete

---

### Task 2.5: Overall Progress Indicator

**Problem:** No persistent sense of "where am I in this 90-minute workshop." Only per-pain-point confidence bar exists.

**Files to modify:**
- `frontend/src/pages/Workshop.tsx` — add persistent progress header
- Create `frontend/src/components/workshop/WorkshopProgress.tsx`

**Implementation:**

Create a persistent top bar showing:
- Current phase name (Confirmation / Deep-Dive / Synthesis)
- Phase progress dots (3 phases, current one highlighted)
- Overall completion percentage
- Estimated time remaining (rough)

```typescript
// WorkshopProgress.tsx
interface Props {
  phase: WorkshopPhase
  currentPainPointIndex: number
  totalPainPoints: number
  companyName: string
}

// Calculate overall progress:
// Confirmation = 0-15%
// DeepDive = 15-85% (distributed across pain points)
// Synthesis = 85-100%

// Render: fixed top bar with subtle background, phase dots, progress bar, company name
```

**Verification:**
- Progress bar visible during all active phases
- Progress updates as user moves through pain points
- Phase labels change correctly on transitions
- Doesn't overlap with existing component headers

---

## Batch 3: Adaptive Intelligence

> **Goal:** Make the AI genuinely smart — dynamic depth, continuous learning, cross-topic insights.
> **Estimated effort:** 2-3 weeks

### Task 3.1: Dynamic Conversation Depth

**Problem:** Every pain point gets exactly 5 questions. A minor scheduling annoyance gets the same depth as a mission-critical billing crisis.

**Files to modify:**
- `backend/src/skills/workshop/question_skill.py` — lines 92-101 (stage progression)
- `backend/src/routes/workshop.py` — conversation management

**Implementation:**

Replace the fixed 5-stage pipeline with a dynamic system:

1. After each user response, evaluate response quality (length, specificity, numbers mentioned)
2. If response is thin (< 20 words, no specifics), probe deeper on the same stage
3. If response is rich (> 100 words, specific numbers/names), consider skipping ahead
4. Allow stages to be revisited if new information surfaces
5. Cap at 8 exchanges per pain point, minimum 3

```python
# Replace fixed stage progression with:
async def _determine_next_stage(self, current_stage: str, user_response: str,
                                 message_count: int, pain_severity: str) -> str:
    """Dynamically determine next conversation stage based on response quality."""
    response_length = len(user_response.split())
    has_numbers = bool(re.search(r'\d+', user_response))
    has_specifics = response_length > 50 or has_numbers

    # Minimum 3 exchanges before completion
    if message_count < 3:
        # Standard progression but allow repeats for thin answers
        if response_length < 20 and not has_numbers:
            return current_stage  # Ask again, more specifically
        return self._next_standard_stage(current_stage)

    # After 3 exchanges, check if we have enough
    if message_count >= 3 and has_specifics and current_stage in ["cost_impact", "ideal_state"]:
        return "complete"  # We have enough for a solid milestone

    # High-severity pain points get more depth
    if pain_severity == "high" and message_count < 7:
        return self._next_standard_stage(current_stage)

    # Cap at 8 exchanges
    if message_count >= 8:
        return "complete"

    return self._next_standard_stage(current_stage)
```

**Verification:**
- Short, vague answers should trigger follow-up probes on the same topic
- Rich, detailed answers should accelerate the conversation
- No conversation should exceed 8 exchanges per pain point
- High-severity pain points should go deeper than low-severity ones

---

### Task 3.2: Continuous Signal Detection

**Problem:** Signals detected once at workshop start from quiz data. If a "non-technical" CEO starts discussing APIs, the system still treats them as non-technical.

**Files to modify:**
- `backend/src/skills/workshop/signal_detector.py` — lines 35-80
- `backend/src/routes/workshop.py` — inject updated signals per message

**Implementation:**

1. **Extend DetectedSignals with conversation-derived signals:**

```python
@dataclass
class DetectedSignals:
    technical: bool = False
    budget_ready: bool = False
    decision_maker: bool = False
    # NEW: conversation-derived signals
    urgency: str = "medium"        # low/medium/high — from language patterns
    detail_preference: str = "moderate"  # brief/moderate/detailed
    emotional_state: str = "neutral"     # frustrated/neutral/enthusiastic

    def update_from_response(self, response: str) -> None:
        """Update signals based on user's conversation response."""
        response_lower = response.lower()

        # Technical signal upgrade
        tech_terms = ["api", "webhook", "integration", "database", "endpoint", "oauth", "sdk"]
        if any(term in response_lower for term in tech_terms):
            self.technical = True

        # Urgency detection
        urgent_terms = ["asap", "immediately", "losing", "bleeding", "urgent", "can't wait"]
        if any(term in response_lower for term in urgent_terms):
            self.urgency = "high"

        # Frustration detection
        frustration_terms = ["frustrated", "waste", "hate", "terrible", "nightmare", "painful"]
        if any(term in response_lower for term in frustration_terms):
            self.emotional_state = "frustrated"

        # Enthusiasm detection
        enthusiasm_terms = ["excited", "love", "amazing", "great", "perfect", "exactly"]
        if any(term in response_lower for term in enthusiasm_terms):
            self.emotional_state = "enthusiastic"

        # Detail preference from response length
        word_count = len(response.split())
        if word_count > 100:
            self.detail_preference = "detailed"
        elif word_count < 20:
            self.detail_preference = "brief"
```

2. **Call `update_from_response` after each user message** in workshop.py's respond endpoint.

**Verification:**
- User who starts non-technical but mentions APIs should get technical questions next
- Frustrated user should get acknowledged ("I hear you — this is a common pain point")
- Brief responder should get more targeted, closed questions
- Detailed responder should get open-ended exploration questions

---

### Task 3.3: Cross-Pain-Point Insights

**Problem:** Each deep-dive is isolated. A great consultant connects patterns across topics.

**Files to modify:**
- `backend/src/skills/workshop/question_skill.py` — add previous milestones to context
- `backend/src/routes/workshop.py` — pass milestones to question generation

**Implementation:**

1. **Pass completed milestones to question skill** (workshop.py, in respond endpoint):

```python
# When generating questions for pain point N, include milestones from 1..N-1
completed_milestones = workshop_data.get("milestones", [])
metadata["previous_milestones"] = [
    {
        "pain_point": m.get("pain_point_label"),
        "finding_title": m.get("finding", {}).get("title"),
        "key_insight": m.get("finding", {}).get("summary"),
        "tools_mentioned": m.get("tools_mentioned", []),
    }
    for m in completed_milestones
]
```

2. **Add cross-reference instruction to question prompt** (question_skill.py):

```python
if previous_milestones:
    prev_context = "\n".join([
        f"- {m['pain_point']}: {m['finding_title']}"
        for m in previous_milestones
    ])
    prompt += f"""
PREVIOUS FINDINGS (reference these when relevant):
{prev_context}

If you spot a connection between the current topic and a previous finding,
mention it: "This seems related to what we found about [previous topic]..."
"""
```

**Verification:**
- When exploring pain point #2, AI should reference findings from pain point #1 when relevant
- Cross-references should feel natural, not forced
- If no connection exists, AI should not force one

---

### Task 3.4: LLM-Powered Confidence Assessment

**Problem:** Current confidence is `message_count / 10 * 100` — pure heuristic. 2 messages = 20% regardless of content quality.

**Files to modify:**
- Create `backend/src/skills/workshop/confidence_skill.py`
- `backend/src/routes/workshop.py` — replace heuristic with skill call

**Implementation:**

Create new skill `WorkshopConfidenceSkill`:

```python
class WorkshopConfidenceSkill(LLMSkill[Dict[str, Any]]):
    """Assess conversation quality and report-readiness using LLM."""

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        transcript = context.metadata.get("transcript", [])
        pain_label = context.metadata.get("pain_point_label", "")

        prompt = f"""Assess the quality of this discovery conversation about "{pain_label}".

CONVERSATION:
{self._format_transcript(transcript)}

Rate each dimension 0-100:
- coverage: How many aspects of the problem were explored?
- depth: How specific and detailed are the answers?
- specificity: Were concrete numbers, names, and examples provided?
- actionability: Is there enough info to make a specific recommendation?

Also identify data_gaps: What key information is still missing?

Return JSON:
{{
    "coverage": <0-100>,
    "depth": <0-100>,
    "specificity": <0-100>,
    "actionability": <0-100>,
    "overall": <0-100>,
    "data_gaps": ["<gap1>", "<gap2>"],
    "ready_for_milestone": <true/false>
}}
"""
        # Use fast model (haiku) for this assessment
        response = await self._call_llm(prompt, model_tier="fast")
        return self._parse_json_response(response)
```

**Verification:**
- A conversation with specific numbers and details should score higher than vague responses
- Data gaps should be specific and actionable
- `ready_for_milestone` should only be true when actionability > 60

---

### Task 3.5: Industry Benchmark Injection

**Problem:** Knowledge base has rich industry data (dental, ecommerce, professional services, recruiting, veterinary) but the workshop doesn't use any of it.

**Files to modify:**
- `backend/src/skills/workshop/question_skill.py` — load and inject benchmarks
- `backend/src/knowledge/__init__.py` — expose benchmark lookup function

**Implementation:**

1. **Create benchmark lookup utility:**

```python
# In knowledge/__init__.py or new file knowledge/benchmark_service.py
async def get_industry_benchmarks(industry: str, topic: str) -> Optional[Dict]:
    """Look up industry-specific benchmarks for a topic."""
    # Load from industry_questions/{industry}.json or benchmarks/
    # Return relevant benchmarks for the conversation topic
    pass
```

2. **Inject benchmarks into question prompts** (question_skill.py):

```python
# Look up benchmarks for current pain point + industry
benchmarks = await get_industry_benchmarks(industry, pain_label)
if benchmarks:
    prompt += f"""
INDUSTRY BENCHMARKS (reference these naturally):
{json.dumps(benchmarks, indent=2)}

Use these to ground your questions: "In {industry}, firms typically spend X on this..."
"""
```

**Verification:**
- Dental workshop should reference dental-specific benchmarks
- Ecommerce workshop should reference ecommerce benchmarks
- Unknown industries should gracefully skip benchmark injection

---

## Batch 4: Premium Polish

> **Goal:** Visual delight, micro-interactions, and polish that signals quality.
> **Estimated effort:** 1 week

### Task 4.1: ROI Count-Up Animation + Milestone Celebration

**Files to modify:**
- `frontend/src/components/workshop/WorkshopMilestone.tsx` — lines 300-335

**Implementation:**
- Use `framer-motion` `useMotionValue` + `useTransform` for count-up animation on ROI numbers
- Add a brief confetti/particle burst (use `canvas-confetti` library or CSS animation) when milestone first loads
- Lead with the savings number as the hero element: large font, green, prominent

---

### Task 4.2: Sequential Card Stagger + Data Points Badge

**Files to modify:**
- `frontend/src/components/workshop/WorkshopConfirmation.tsx`

**Implementation:**
- Use existing `staggerContainer` / `staggerItem` from `report/animations.ts` (lines 43-71)
- Add delay per card: `transition={{ delay: index * 0.15 }}`
- Add badge: `<span className="text-xs text-gray-500">Based on {dataPoints} data points</span>`

---

### Task 4.3: Phase Transition Animations

**Files to modify:**
- `frontend/src/pages/Workshop.tsx` — wrap phase rendering in AnimatePresence

**Implementation:**
- Wrap the phase switch/conditional rendering in `<AnimatePresence mode="wait">`
- Add `motion.div` with `fadeInUp` variant on each phase
- Use `key={phase}` to trigger exit/enter animations

---

### Task 4.4: Voice Waveform Visualization

**Files to modify:**
- `frontend/src/components/workshop/WorkshopDeepDive.tsx`

**Implementation:**
- During voice recording, render a simple waveform visualization using Web Audio API's `AnalyserNode`
- Create `VoiceWaveform.tsx` component that takes `mediaStream` and renders frequency bars
- Replace the static recording button with waveform during active recording

---

### Task 4.5: Company Name Throughout

**Files to modify:**
- `frontend/src/components/workshop/WorkshopMilestone.tsx`
- `frontend/src/components/workshop/SynthesisForm.tsx`
- `frontend/src/pages/Workshop.tsx` (completion screen)

**Implementation:**
- Milestone header: "Here's what we found for {companyName}"
- Synthesis: "{companyName}'s Technology Roadmap"
- Completion: "Your report for {companyName} is being generated"
- Pass `companyName` prop to all components that don't have it yet

---

### Task 4.6: Mid-Conversation Encouragement Toasts

**Files to modify:**
- `frontend/src/components/workshop/WorkshopDeepDive.tsx`
- Create `frontend/src/components/ui/Toast.tsx` (reusable)

**Implementation:**
- When confidence crosses 25%: "Good start — keep going"
- When confidence crosses 50%: "Halfway through this topic — great detail so far"
- When confidence crosses 75%: "Almost there — we have rich data for your report"
- Show as subtle toast that auto-dismisses after 3 seconds
- Use Framer Motion slide-in from top-right

---

## Execution Order Summary

| Batch | Tasks | Est. Effort | Dependencies |
|-------|-------|-------------|--------------|
| **Batch 1** | 1.1-1.5 (showstoppers) | 2-3 days | None |
| **Batch 2** | 2.1-2.5 (consulting feel) | 1-2 weeks | Batch 1 |
| **Batch 3** | 3.1-3.5 (adaptive AI) | 2-3 weeks | Batch 1 |
| **Batch 4** | 4.1-4.6 (polish) | 1 week | Batch 2 |

Batches 2 and 3 can run in parallel (backend AI work + frontend UX work).

---

## Testing Strategy

- **Backend:** Unit tests for each new skill, integration tests for workshop→report flow
- **Frontend:** Manual testing per component (frontend has ~2% test coverage)
- **E2E:** Run existing workshop UI test stories (`tests/ui/stories/workshop-*.yaml`) after each batch
- **Regression:** Verify non-workshop report generation still works (no workshop_data sessions)
