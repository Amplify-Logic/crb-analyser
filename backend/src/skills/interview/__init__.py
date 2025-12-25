"""
Interview Skills

Skills for adaptive interview flow in CRB analysis.

Available Skills:
- FollowUpQuestionSkill: Generate adaptive follow-up questions
- PainExtractionSkill: Extract structured pain points from transcript

Usage:
    from src.skills import get_skill, SkillContext

    # Generate follow-up question
    skill = get_skill("followup-question", client=anthropic_client)
    context = SkillContext(
        industry="dental",
        metadata={
            "user_message": "We spend too much time on scheduling...",
            "topics_covered": ["Current Challenges"],
            "question_count": 3,
        }
    )
    result = await skill.run(context)
    print(result.data["question"])

    # Extract pain points from transcript
    skill = get_skill("pain-extraction", client=anthropic_client)
    context = SkillContext(
        industry="dental",
        metadata={
            "transcript": [
                {"role": "assistant", "content": "What challenges do you face?"},
                {"role": "user", "content": "Scheduling is a nightmare..."},
            ]
        }
    )
    result = await skill.run(context)
    print(result.data["pain_points"])
"""

from .followup import FollowUpQuestionSkill
from .pain_extraction import PainExtractionSkill

__all__ = [
    "FollowUpQuestionSkill",
    "PainExtractionSkill",
]
