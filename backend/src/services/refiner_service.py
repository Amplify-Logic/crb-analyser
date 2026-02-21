"""
Refiner Service

AI conversation agent for report refinement.
Builds context from report data and manages Claude conversations.
"""

import json
import structlog
from typing import Dict, Any, List, Optional

from anthropic import Anthropic

from src.config.settings import settings
from src.config.model_routing import get_model_for_task
from src.config.supabase_client import get_async_supabase

logger = structlog.get_logger(__name__)


class RefinerService:
    """Service for report refiner conversations."""

    def __init__(self, report_id: str):
        self.report_id = report_id
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def build_system_prompt(self, report_data: Dict[str, Any]) -> str:
        """Build the agent system prompt from report data."""
        company = report_data.get("company_name", "this business")
        summary = report_data.get("executive_summary", {})
        findings = report_data.get("findings", [])
        recommendations = report_data.get("recommendations", [])

        # Build findings summary
        findings_text = ""
        for f in findings:
            score = f.get("customer_value_score", "?")
            findings_text += f"- {f.get('title', 'Untitled')} (score: {score}/10)\n"

        # Build recommendations summary
        recs_text = ""
        for r in recommendations:
            roi = r.get("roi_percentage", "?")
            recs_text += f"- {r.get('title', 'Untitled')} (ROI: {roi}%)\n"

        return f"""You are a CRB analyst who authored the report for {company}. You have deep knowledge of every finding, recommendation, and the data behind each decision.

## Your Role
- Answer questions confidently — you made these analytical decisions
- Explain reasoning by referencing specific data from the quiz, benchmarks, and industry knowledge
- Never apologize for the report or suggest it is incomplete
- Never propose changes to the report unprompted
- Be conversational but precise — cite specifics, not generalities

## Report Context

**Company:** {company}
**AI Readiness Score:** {summary.get('ai_readiness_score', 'N/A')}/100

### Findings
{findings_text or 'No findings available.'}

### Recommendations
{recs_text or 'No recommendations available.'}

### Full Report Data
```json
{json.dumps({
    "executive_summary": summary,
    "findings": findings,
    "recommendations": recommendations,
    "value_summary": report_data.get("value_summary", {}),
    "roadmap": report_data.get("roadmap", {}),
    "playbooks": report_data.get("playbooks", []),
    "automation_summary": report_data.get("automation_summary", {}),
    "company_profile": report_data.get("company_profile", {}),
}, indent=2, default=str)[:15000]}
```

## Behavioral Rules
1. When the user asks a question — explain clearly using report data
2. When the user explores a hypothetical ("what if...") — discuss tradeoffs without proposing changes
3. When the user shares NEW information not in the original analysis — acknowledge it and discuss how it might affect the findings
4. Keep responses concise (2-4 paragraphs). Use bullet points for comparisons.
5. Always ground answers in specific numbers, scores, or data from the report."""

    def build_messages(
        self,
        history: List[Dict[str, str]],
        new_message: str,
    ) -> List[Dict[str, str]]:
        """Build Claude message array from history + new message."""
        messages = []
        for msg in history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"],
            })
        messages.append({"role": "user", "content": new_message})
        return messages

    def generate_starter_prompts(self, report_data: Dict[str, Any]) -> List[str]:
        """Generate 3 dynamic starter prompts from report data."""
        findings = report_data.get("findings", [])
        recommendations = report_data.get("recommendations", [])
        value_summary = report_data.get("value_summary", {})
        summary = report_data.get("executive_summary", {})

        prompts = []

        # Prompt 1: Top finding
        if findings:
            top = sorted(findings, key=lambda f: f.get("customer_value_score", 0), reverse=True)
            if top:
                prompts.append(f"Why was \"{top[0].get('title', 'the top finding')}\" scored highest?")

        # Prompt 2: Value breakdown
        val_min = value_summary.get("total_value_min", 0)
        val_max = value_summary.get("total_value_max", 0)
        if val_max:
            prompts.append(f"Break down the ${val_min:,.0f}-${val_max:,.0f} value potential — what's realistic for year 1?")
        elif recommendations:
            top_rec = recommendations[0]
            prompts.append(f"How does the ROI for \"{top_rec.get('title', 'the top recommendation')}\" break down?")

        # Prompt 3: Implementation
        score = summary.get("ai_readiness_score", 0)
        if score:
            prompts.append(f"With a readiness score of {score}/100, what should I implement first?")
        else:
            prompts.append("What should I implement first?")

        # Ensure exactly 3
        defaults = [
            "What are the biggest risks in these recommendations?",
            "Which finding would have the fastest impact?",
            "How do the Connect vs Replace paths compare for my situation?",
        ]
        while len(prompts) < 3:
            prompts.append(defaults[len(prompts)])

        return prompts[:3]

    async def send_message(
        self,
        report_data: Dict[str, Any],
        history: List[Dict[str, str]],
        user_message: str,
    ) -> Dict[str, Any]:
        """
        Send a message to the refiner agent and get a response.

        Returns dict with: content, model_used, tokens_used
        """
        system = self.build_system_prompt(report_data)
        messages = self.build_messages(history, user_message)
        model = get_model_for_task("generate_findings", "quick")  # Sonnet 4.6

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=2000,
                system=system,
                messages=messages,
            )

            content = response.content[0].text
            tokens = response.usage.input_tokens + response.usage.output_tokens

            return {
                "content": content,
                "model_used": model,
                "tokens_used": tokens,
            }

        except Exception as e:
            logger.error("refiner_message_failed", error=str(e), report_id=self.report_id)
            raise

    async def create_conversation(self, report_id: str) -> Dict[str, Any]:
        """Create a new conversation for a report."""
        supabase = await get_async_supabase()
        result = await supabase.table("report_conversations").insert({
            "report_id": report_id,
            "status": "active",
        }).execute()
        return result.data[0]

    async def get_conversations(self, report_id: str) -> List[Dict[str, Any]]:
        """Get all conversations for a report."""
        supabase = await get_async_supabase()
        result = await supabase.table("report_conversations").select("*").eq(
            "report_id", report_id
        ).order("started_at", desc=True).execute()
        return result.data or []

    async def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a conversation."""
        supabase = await get_async_supabase()
        result = await supabase.table("report_messages").select("*").eq(
            "conversation_id", conversation_id
        ).order("created_at").execute()
        return result.data or []

    async def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        model_used: Optional[str] = None,
        tokens_used: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Save a message to the database."""
        supabase = await get_async_supabase()

        data: Dict[str, Any] = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
        }
        if model_used:
            data["model_used"] = model_used
        if tokens_used is not None:
            data["tokens_used"] = tokens_used

        result = await supabase.table("report_messages").insert(data).execute()

        # Update conversation last_message_at
        await supabase.table("report_conversations").update({
            "last_message_at": "now()",
        }).eq("id", conversation_id).execute()

        return result.data[0]
