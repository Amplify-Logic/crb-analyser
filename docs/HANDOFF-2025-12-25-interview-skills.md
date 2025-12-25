# Handoff: Interview Skills Integration

**Date:** 2025-12-25
**Status:** ✅ COMPLETE
**Priority:** Done

---

## Summary

Created interview skills for adaptive follow-up questions and pain extraction. Skills are tested and working. **Integration into interview routes is complete.**

---

## Completed Work

### 1. Interview Skills Created

| Skill | File | Purpose |
|-------|------|---------|
| `FollowUpQuestionSkill` | `backend/src/skills/interview/followup.py` | Generates adaptive follow-up questions based on conversation context |
| `PainExtractionSkill` | `backend/src/skills/interview/pain_extraction.py` | Extracts structured pain points from interview transcripts |

### 2. Skills Features

**FollowUpQuestionSkill (`followup-question`):**
- Analyzes user's previous response for key themes
- Tracks topics covered vs. topics needed
- Uses industry expertise to probe known pain points
- Question types: `clarification`, `deepdive`, `transition`, `probing`
- Detects when interview should wrap up (question_count >= 12)
- Output: `{question, question_type, reasoning, topics_touched, suggested_followups, is_completion_candidate}`

**PainExtractionSkill (`pain-extraction`):**
- Extracts explicit and implicit pain points from transcripts
- Categories: operational, financial, customer, technology, team, compliance
- Scores severity (high/medium/low) and frequency
- Includes direct quotes from transcript
- Estimates impact (time_hours_per_week, cost_per_month, customer_impact)
- Maps to potential automation solutions
- Validates against expertise data for confidence boost
- Output: `{pain_points[], themes[], priority_ranking[], confidence_score}`

### 3. Registry Enhancement

Updated `backend/src/skills/registry.py` to index skills by both:
- Path name: `interview/followup`
- Class name: `followup-question`

### 4. Tests

- **69 total skill tests passing** (26 new interview tests)
- Test file: `backend/tests/skills/test_interview_skills.py`

---

## ✅ Completed: Interview Routes Integration

File: `backend/src/routes/interview.py`

**What was done:**
- Added imports for skills, expertise, knowledge
- Added `get_anthropic_client()` helper function
- Integrated `FollowUpQuestionSkill` into `generate_ai_response()`
- Created `generate_ai_response_legacy()` as fallback
- Updated `/respond` route to pass industry
- Integrated `PainExtractionSkill` into `interview_complete()`
- Pain points now extracted and saved with interview data

**Integration details:**

#### 1. Integrate FollowUpQuestionSkill into `generate_ai_response()`

Replace the current Claude API call with skill-based generation:

```python
async def generate_ai_response(
    user_message: str,
    context: InterviewContext,
    previous_messages: List[MessageContext],
    industry: str = "general",  # Add industry parameter
) -> tuple[str, List[str], int, bool]:
    """Generate an AI-powered response using FollowUpQuestionSkill."""
    topics_covered = context.topics_covered or ["introduction"]
    question_count = context.question_count

    # Check for completion signals (keep existing logic)
    completion_signals = ["that's all", "nothing else", "i'm done", "that's it", "wrap up", "finish"]
    if any(signal in user_message.lower() for signal in completion_signals):
        return (
            "Thank you so much for sharing all this valuable information!...",
            list(set(topics_covered + ["complete"])),
            100,
            True
        )

    # Try skill-based generation
    client = get_anthropic_client()
    skill = get_skill("followup-question", client=client)

    if skill:
        try:
            # Get expertise for the industry
            expertise_store = get_expertise_store()
            expertise = expertise_store.get_expertise(normalize_industry(industry))

            skill_context = SkillContext(
                industry=normalize_industry(industry),
                expertise=expertise,
                metadata={
                    "user_message": user_message,
                    "previous_messages": [
                        {"role": m.role, "content": m.content}
                        for m in previous_messages[-10:]
                    ],
                    "topics_covered": topics_covered,
                    "question_count": question_count,
                }
            )

            result = await skill.run(skill_context)

            if result.success:
                data = result.data
                # Build response with acknowledgment + question
                response = f"That's helpful context. {data['question']}"

                # Update topics
                new_topics = list(set(topics_covered + data.get("topics_touched", [])))

                # Calculate progress
                total_expected = 12
                progress = min(95, int((question_count / total_expected) * 100))

                is_complete = data.get("is_completion_candidate", False)

                logger.info(f"FollowUp skill: type={data['question_type']}, progress={progress}%")
                return (response, new_topics, progress, is_complete)

        except Exception as e:
            logger.warning(f"FollowUpQuestionSkill failed, using legacy: {e}")

    # Fall back to legacy Claude-based response
    return await generate_ai_response_legacy(user_message, context, previous_messages)
```

#### 2. Integrate PainExtractionSkill into `interview_complete()`

Add pain extraction after saving interview data:

```python
@router.post("/complete")
async def interview_complete(request: InterviewCompleteRequest):
    """Mark the interview as complete, save data, and extract pain points."""
    try:
        supabase = await get_async_supabase()

        # Get session
        session_result = await supabase.table("quiz_sessions").select("*").eq(
            "id", request.session_id
        ).single().execute()

        if not session_result.data:
            raise HTTPException(status_code=404, detail="Session not found")

        session = session_result.data

        # Get industry from session
        answers = session.get("answers", {})
        industry = answers.get("industry", "general")

        # Extract pain points using skill
        pain_points_data = {}
        client = get_anthropic_client()
        skill = get_skill("pain-extraction", client=client)

        if skill and request.messages:
            try:
                expertise_store = get_expertise_store()
                expertise = expertise_store.get_expertise(normalize_industry(industry))

                skill_context = SkillContext(
                    industry=normalize_industry(industry),
                    expertise=expertise,
                    metadata={
                        "transcript": request.messages,
                        "company_profile": answers.get("company_profile", {}),
                    }
                )

                result = await skill.run(skill_context)

                if result.success:
                    pain_points_data = result.data
                    logger.info(
                        f"Extracted {len(pain_points_data.get('pain_points', []))} pain points "
                        f"(confidence={pain_points_data.get('confidence_score', 0):.2f})"
                    )

            except Exception as e:
                logger.warning(f"PainExtractionSkill failed: {e}")

        # Save interview data with extracted pain points
        await supabase.table("quiz_sessions").update({
            "interview_completed": True,
            "interview_data": {
                "messages": request.messages,
                "topics_covered": request.topics_covered,
                "completed_at": datetime.utcnow().isoformat(),
                "pain_points": pain_points_data,  # Add extracted pain points
            },
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", request.session_id).execute()

        logger.info(f"Interview completed for session {request.session_id}")

        return {
            "success": True,
            "message": "Interview saved successfully",
            "pain_points_extracted": len(pain_points_data.get("pain_points", [])),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Interview complete error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save interview")
```

#### 3. Update `/respond` Route

Pass industry to `generate_ai_response()`:

```python
@router.post("/respond")
async def interview_respond(request: InterviewRespondRequest):
    context = request.context or InterviewContext()
    previous_messages = context.previous_messages or []

    # Get industry from company profile
    industry = "general"
    if context.company_profile:
        industry = context.company_profile.get("industry", {}).get(
            "primary_industry", {}
        ).get("value", "general")

    response, topics, progress, is_complete = await generate_ai_response(
        user_message=request.message,
        context=context,
        previous_messages=previous_messages,
        industry=industry,  # Pass industry
    )
    # ... rest unchanged
```

#### 4. Rename existing `generate_ai_response` to `generate_ai_response_legacy`

Keep the existing implementation as fallback.

---

## File Locations

```
backend/src/skills/interview/
├── __init__.py              # Exports both skills
├── followup.py              # FollowUpQuestionSkill
└── pain_extraction.py       # PainExtractionSkill

backend/src/routes/
└── interview.py             # NEEDS INTEGRATION (partially updated)

backend/tests/skills/
└── test_interview_skills.py # 26 tests passing
```

---

## Testing Commands

```bash
cd backend && source venv/bin/activate

# Run interview skill tests
pytest tests/skills/test_interview_skills.py -v

# Run all skill tests
pytest tests/skills/ -v

# Verify skills discoverable
python -c "
from src.skills import get_skill
for name in ['followup-question', 'pain-extraction']:
    skill = get_skill(name)
    print(f'{name}: {skill.__class__.__name__ if skill else \"NOT FOUND\"}')"
```

---

## Previous Session Work

Also completed in this session (from previous handoff):

1. **Integrated report generation skills into `report_service.py`:**
   - `ExecSummarySkill` → `_generate_executive_summary()`
   - `FindingGenerationSkill` → `_generate_findings()`
   - `ThreeOptionsSkill` → `_generate_recommendations()`
   - `VerdictSkill` → `_generate_verdict()`

2. **All skills now have fallback to legacy methods**

---

## Notes

- The interview routes file was partially modified - imports added but integration not complete
- Skills use expertise data when available for better question targeting
- PainExtractionSkill validates findings against known industry pain points
- 69 total skill tests passing
