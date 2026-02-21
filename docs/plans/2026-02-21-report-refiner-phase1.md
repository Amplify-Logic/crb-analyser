# Report Refiner Phase 1: Conversation — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an AI conversation sidebar to the report viewer where users can ask questions about their report and get contextual answers.

**Architecture:** Two new Supabase tables (conversations, messages), a FastAPI route module, a RefinerService that builds context from report data and calls Sonnet 4.6, and a React sidebar component integrated into ReportViewer.

**Tech Stack:** FastAPI, Supabase (PostgreSQL), Anthropic Claude API, React 18, TypeScript, Tailwind CSS

**Design doc:** `docs/plans/2026-02-21-report-refiner-design.md`

---

## Task 1: Database Migration

**Files:**
- Create: `backend/supabase/migrations/020_report_refiner.sql`

**Step 1: Write the migration**

```sql
-- Report Refiner: conversations and messages
-- Supports Phase 1 (conversation) and lays foundation for Phase 2+ (refinements, snapshots)

-- Conversations: persistent chat threads per report
CREATE TABLE IF NOT EXISTS report_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    title TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_message_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_report_conversations_report ON report_conversations(report_id);
CREATE INDEX idx_report_conversations_status ON report_conversations(report_id, status);

-- Messages: individual chat messages
CREATE TABLE IF NOT EXISTS report_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES report_conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    suggestions JSONB,
    model_used TEXT,
    tokens_used INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_report_messages_conversation ON report_messages(conversation_id);
CREATE INDEX idx_report_messages_created ON report_messages(conversation_id, created_at);

-- RLS
ALTER TABLE report_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_messages ENABLE ROW LEVEL SECURITY;

-- Service role (backend) can do everything
CREATE POLICY "report_conversations_service_all" ON report_conversations
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "report_messages_service_all" ON report_messages
    FOR ALL USING (true) WITH CHECK (true);

-- Users can read conversations for reports they have access to
CREATE POLICY "report_conversations_select" ON report_conversations
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM reports r
            JOIN quiz_sessions qs ON qs.id = r.quiz_session_id
            WHERE r.id = report_conversations.report_id
            AND qs.status IN ('paid', 'completed', 'generating', 'qa_pending', 'released')
        )
    );

CREATE POLICY "report_messages_select" ON report_messages
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM report_conversations rc
            WHERE rc.id = report_messages.conversation_id
        )
    );
```

**Step 2: Verify migration syntax**

Run: `cd backend && python -c "open('supabase/migrations/020_report_refiner.sql').read(); print('SQL file readable')"`
Expected: `SQL file readable`

**Step 3: Commit**

```bash
git add backend/supabase/migrations/020_report_refiner.sql
git commit -m "feat: add report_conversations and report_messages tables"
```

---

## Task 2: Refiner Service — Context Builder

**Files:**
- Create: `backend/src/services/refiner_service.py`
- Test: `backend/tests/services/test_refiner_service.py`

**Step 1: Write the failing test**

```python
"""Tests for RefinerService context building."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.services.refiner_service import RefinerService


class TestBuildSystemPrompt:
    """Test system prompt construction from report data."""

    def test_includes_company_name(self):
        service = RefinerService(report_id="test-123")
        report_data = {
            "company_name": "Acme Store",
            "executive_summary": {"ai_readiness_score": 55},
            "findings": [],
            "recommendations": [],
        }
        prompt = service.build_system_prompt(report_data)
        assert "Acme Store" in prompt

    def test_includes_findings_summary(self):
        service = RefinerService(report_id="test-123")
        report_data = {
            "company_name": "Acme Store",
            "executive_summary": {"ai_readiness_score": 55},
            "findings": [
                {"id": "f-001", "title": "Customer Support Automation", "customer_value_score": 9},
                {"id": "f-002", "title": "Inventory Forecasting", "customer_value_score": 7},
            ],
            "recommendations": [],
        }
        prompt = service.build_system_prompt(report_data)
        assert "Customer Support Automation" in prompt
        assert "Inventory Forecasting" in prompt

    def test_includes_recommendations(self):
        service = RefinerService(report_id="test-123")
        report_data = {
            "company_name": "Acme Store",
            "executive_summary": {},
            "findings": [],
            "recommendations": [
                {"id": "rec-001", "title": "Implement Gorgias", "roi_percentage": 180},
            ],
        }
        prompt = service.build_system_prompt(report_data)
        assert "Gorgias" in prompt
        assert "180" in prompt

    def test_includes_behavioral_rules(self):
        service = RefinerService(report_id="test-123")
        report_data = {
            "company_name": "Test",
            "executive_summary": {},
            "findings": [],
            "recommendations": [],
        }
        prompt = service.build_system_prompt(report_data)
        assert "never apologize for the report" in prompt.lower() or "you authored this report" in prompt.lower()


class TestBuildMessages:
    """Test message history construction for Claude API."""

    def test_empty_history(self):
        service = RefinerService(report_id="test-123")
        messages = service.build_messages([], "Hello")
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"

    def test_includes_history(self):
        service = RefinerService(report_id="test-123")
        history = [
            {"role": "user", "content": "Why Gorgias?"},
            {"role": "assistant", "content": "Based on your support volume..."},
        ]
        messages = service.build_messages(history, "Tell me more")
        assert len(messages) == 3
        assert messages[0]["role"] == "user"
        assert messages[2]["content"] == "Tell me more"


class TestGenerateStarterPrompts:
    """Test dynamic starter prompt generation."""

    def test_returns_three_prompts(self):
        service = RefinerService(report_id="test-123")
        report_data = {
            "findings": [
                {"id": "f-001", "title": "Customer Support Automation", "customer_value_score": 9},
            ],
            "recommendations": [
                {"id": "rec-001", "title": "Implement Gorgias", "roi_percentage": 180},
            ],
            "value_summary": {"total_value_min": 100000, "total_value_max": 200000},
            "executive_summary": {"ai_readiness_score": 55},
        }
        prompts = service.generate_starter_prompts(report_data)
        assert len(prompts) == 3
        assert all(isinstance(p, str) for p in prompts)
        assert all(p.endswith("?") for p in prompts)
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/services/test_refiner_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.services.refiner_service'`

**Step 3: Write the implementation**

```python
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
```

**Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/services/test_refiner_service.py -v`
Expected: All 7 tests PASS

**Step 5: Commit**

```bash
git add backend/src/services/refiner_service.py backend/tests/services/test_refiner_service.py
git commit -m "feat: add RefinerService with context builder and conversation management"
```

---

## Task 3: API Routes

**Files:**
- Create: `backend/src/routes/refiner.py`
- Modify: `backend/src/main.py` (add router)
- Test: `backend/tests/routes/test_refiner_routes.py`

**Step 1: Write the failing test**

```python
"""Tests for refiner API routes."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient


class TestRefinerRoutes:
    """Test refiner conversation endpoints."""

    @pytest.fixture
    def mock_report(self):
        return {
            "id": "report-123",
            "status": "released",
            "quiz_session_id": "quiz-456",
            "executive_summary": {"ai_readiness_score": 55},
            "findings": [{"id": "f-001", "title": "Test Finding", "customer_value_score": 8}],
            "recommendations": [{"id": "rec-001", "title": "Test Rec", "roi_percentage": 150}],
            "value_summary": {},
            "company_name": "Test Co",
        }

    @pytest.mark.asyncio
    async def test_create_conversation_returns_id(self, mock_report):
        """Creating a conversation should return conversation ID."""
        from src.routes.refiner import router
        from fastapi import FastAPI
        from httpx import AsyncClient, ASGITransport

        app = FastAPI()
        app.include_router(router, prefix="/api/reports")

        with patch("src.routes.refiner.get_report_by_id", return_value=mock_report), \
             patch("src.routes.refiner.RefinerService") as MockService:

            mock_service = MockService.return_value
            mock_service.create_conversation = AsyncMock(return_value={
                "id": "conv-789",
                "report_id": "report-123",
                "status": "active",
            })
            mock_service.generate_starter_prompts = MagicMock(return_value=[
                "Why was this scored highest?",
                "Break down the value?",
                "What should I do first?",
            ])

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post("/api/reports/report-123/conversations")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "conv-789"
            assert len(data["starter_prompts"]) == 3

    @pytest.mark.asyncio
    async def test_send_message_returns_response(self, mock_report):
        """Sending a message should return assistant response."""
        from src.routes.refiner import router
        from fastapi import FastAPI
        from httpx import AsyncClient, ASGITransport

        app = FastAPI()
        app.include_router(router, prefix="/api/reports")

        with patch("src.routes.refiner.get_report_by_id", return_value=mock_report), \
             patch("src.routes.refiner.RefinerService") as MockService:

            mock_service = MockService.return_value
            mock_service.get_messages = AsyncMock(return_value=[])
            mock_service.save_message = AsyncMock(return_value={"id": "msg-1"})
            mock_service.send_message = AsyncMock(return_value={
                "content": "Based on your report...",
                "model_used": "claude-sonnet-4-6",
                "tokens_used": 500,
            })

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/reports/report-123/conversations/conv-789/messages",
                    json={"content": "Why Gorgias?"},
                )

            assert response.status_code == 200
            data = response.json()
            assert "Based on your report" in data["content"]
            assert data["model_used"] == "claude-sonnet-4-6"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/routes/test_refiner_routes.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.routes.refiner'`

**Step 3: Write the routes**

```python
"""
Refiner Routes

API endpoints for report refiner conversations.
"""

import structlog
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.config.supabase_client import get_async_supabase
from src.services.report_service import get_report as get_report_by_id
from src.services.refiner_service import RefinerService

logger = structlog.get_logger(__name__)

router = APIRouter()


class SendMessageRequest(BaseModel):
    content: str


class SendMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None


@router.post("/{report_id}/conversations")
async def create_conversation(report_id: str):
    """Start a new conversation for a report."""
    report = await get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    service = RefinerService(report_id=report_id)
    conversation = await service.create_conversation(report_id)

    # Generate starter prompts from report data
    starter_prompts = service.generate_starter_prompts(report)

    return {
        "id": conversation["id"],
        "report_id": report_id,
        "status": conversation["status"],
        "starter_prompts": starter_prompts,
    }


@router.get("/{report_id}/conversations")
async def list_conversations(report_id: str):
    """List all conversations for a report."""
    report = await get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    service = RefinerService(report_id=report_id)
    conversations = await service.get_conversations(report_id)
    return {"conversations": conversations}


@router.get("/{report_id}/conversations/{conversation_id}/messages")
async def get_messages(report_id: str, conversation_id: str):
    """Get message history for a conversation."""
    service = RefinerService(report_id=report_id)
    messages = await service.get_messages(conversation_id)
    return {"messages": messages}


@router.post("/{report_id}/conversations/{conversation_id}/messages")
async def send_message(
    report_id: str,
    conversation_id: str,
    request: SendMessageRequest,
):
    """Send a message and get an AI response."""
    report = await get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    service = RefinerService(report_id=report_id)

    # Get conversation history
    history = await service.get_messages(conversation_id)
    history_for_llm = [{"role": m["role"], "content": m["content"]} for m in history]

    # Save user message
    await service.save_message(conversation_id, "user", request.content)

    # Get AI response
    try:
        result = await service.send_message(report, history_for_llm, request.content)
    except Exception as e:
        logger.error("refiner_send_failed", error=str(e), report_id=report_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate response",
        )

    # Save assistant message
    saved = await service.save_message(
        conversation_id,
        "assistant",
        result["content"],
        model_used=result.get("model_used"),
        tokens_used=result.get("tokens_used"),
    )

    return {
        "id": saved["id"],
        "role": "assistant",
        "content": result["content"],
        "model_used": result.get("model_used"),
        "tokens_used": result.get("tokens_used"),
    }
```

**Step 4: Register the router in main.py**

Find the router registration section in `backend/src/main.py` and add:

```python
from src.routes.refiner import router as refiner_router

app.include_router(refiner_router, prefix="/api/reports", tags=["refiner"])
```

**Step 5: Run tests to verify they pass**

Run: `cd backend && pytest tests/routes/test_refiner_routes.py -v`
Expected: All 2 tests PASS

**Step 6: Commit**

```bash
git add backend/src/routes/refiner.py backend/tests/routes/test_refiner_routes.py backend/src/main.py
git commit -m "feat: add refiner API routes for conversations and messages"
```

---

## Task 4: Frontend API Service

**Files:**
- Create: `frontend/src/services/refinerApi.ts`

**Step 1: Write the API service**

```typescript
/**
 * Refiner API Service
 * Handles report refiner conversations and messages.
 */

import apiClient from './apiClient'

// --- Types ---

export interface StarterPrompt {
  text: string
}

export interface Conversation {
  id: string
  report_id: string
  status: 'active' | 'archived'
  title?: string
  started_at: string
  last_message_at?: string
  starter_prompts?: string[]
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  suggestions?: Suggestion[]
  model_used?: string
  tokens_used?: number
  created_at: string
}

export interface Suggestion {
  id: string
  refinement_type: string
  impact_level: 'minor' | 'moderate' | 'major'
  energy_cost: number
  target_section: string
  target_ids: string[]
  change_summary: string
  preview?: {
    before: Record<string, unknown>
    after: Record<string, unknown>
  }
}

export interface CreateConversationResponse {
  id: string
  report_id: string
  status: string
  starter_prompts: string[]
}

export interface SendMessageResponse {
  id: string
  role: 'assistant'
  content: string
  model_used?: string
  tokens_used?: number
}

// --- API ---

export const refinerApi = {
  async createConversation(reportId: string): Promise<CreateConversationResponse> {
    const { data } = await apiClient.post<CreateConversationResponse>(
      `/api/reports/${reportId}/conversations`
    )
    return data
  },

  async listConversations(reportId: string): Promise<Conversation[]> {
    const { data } = await apiClient.get<{ conversations: Conversation[] }>(
      `/api/reports/${reportId}/conversations`
    )
    return data.conversations
  },

  async getMessages(reportId: string, conversationId: string): Promise<Message[]> {
    const { data } = await apiClient.get<{ messages: Message[] }>(
      `/api/reports/${reportId}/conversations/${conversationId}/messages`
    )
    return data.messages
  },

  async sendMessage(
    reportId: string,
    conversationId: string,
    content: string
  ): Promise<SendMessageResponse> {
    const { data } = await apiClient.post<SendMessageResponse>(
      `/api/reports/${reportId}/conversations/${conversationId}/messages`,
      { content },
      { timeout: 60000 } // 60s timeout for LLM calls
    )
    return data
  },
}
```

**Step 2: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit src/services/refinerApi.ts 2>&1 | head -5`
Expected: No errors (or only unrelated warnings)

**Step 3: Commit**

```bash
git add frontend/src/services/refinerApi.ts
git commit -m "feat: add refiner API service for frontend"
```

---

## Task 5: RefinerButton Component

**Files:**
- Create: `frontend/src/components/report/Refiner/RefinerButton.tsx`

**Step 1: Write the component**

```tsx
import { useState } from 'react'
import { MessageCircle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface RefinerButtonProps {
  onClick: () => void
  isOpen: boolean
  hasUnread?: boolean
}

export default function RefinerButton({ onClick, isOpen, hasUnread }: RefinerButtonProps) {
  if (isOpen) return null

  return (
    <motion.button
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
      onClick={onClick}
      className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-full shadow-lg transition-colors print:hidden"
      title="Ask your report"
    >
      <MessageCircle className="w-5 h-5" />
      <span className="text-sm font-medium">Ask your report</span>
      {hasUnread && (
        <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full" />
      )}
    </motion.button>
  )
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/report/Refiner/RefinerButton.tsx
git commit -m "feat: add RefinerButton floating trigger component"
```

---

## Task 6: MessageInput Component

**Files:**
- Create: `frontend/src/components/report/Refiner/MessageInput.tsx`

**Step 1: Write the component**

```tsx
import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'

interface MessageInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

export default function MessageInput({ onSend, disabled, placeholder }: MessageInputProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current
    if (el) {
      el.style.height = 'auto'
      el.style.height = Math.min(el.scrollHeight, 120) + 'px'
    }
  }, [value])

  const handleSubmit = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 p-3 bg-white dark:bg-gray-800">
      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder || "Ask about your report..."}
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 px-3 py-2 text-sm text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:opacity-50"
        />
        <button
          onClick={handleSubmit}
          disabled={disabled || !value.trim()}
          className="p-2 rounded-lg bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/report/Refiner/MessageInput.tsx
git commit -m "feat: add MessageInput component with auto-resize"
```

---

## Task 7: MessageList Component

**Files:**
- Create: `frontend/src/components/report/Refiner/MessageList.tsx`

**Step 1: Write the component**

```tsx
import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import type { Message } from '../../../services/refinerApi'

interface StarterPromptsProps {
  prompts: string[]
  onSelect: (prompt: string) => void
}

function StarterPrompts({ prompts, onSelect }: StarterPromptsProps) {
  return (
    <div className="space-y-2 px-4 py-3">
      {prompts.map((prompt, i) => (
        <button
          key={i}
          onClick={() => onSelect(prompt)}
          className="w-full text-left px-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 transition-colors"
        >
          {prompt}
        </button>
      ))}
    </div>
  )
}

interface MessageBubbleProps {
  message: Message
}

function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
          isUser
            ? 'bg-primary-600 text-white'
            : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white'
        }`}
      >
        <div className="whitespace-pre-wrap">{message.content}</div>
      </div>
    </motion.div>
  )
}

interface MessageListProps {
  messages: Message[]
  starterPrompts: string[]
  onStarterSelect: (prompt: string) => void
  isLoading?: boolean
}

export default function MessageList({
  messages,
  starterPrompts,
  onStarterSelect,
  isLoading,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, isLoading])

  const showStarters = messages.length === 0 && starterPrompts.length > 0

  return (
    <div className="flex-1 overflow-y-auto">
      {/* Greeting */}
      <div className="px-4 py-4">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          I have full context on your analysis. Ask me anything.
        </p>
      </div>

      {/* Starter prompts or messages */}
      {showStarters ? (
        <StarterPrompts prompts={starterPrompts} onSelect={onStarterSelect} />
      ) : (
        <div className="space-y-3 px-4 pb-4">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-start"
            >
              <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-3 py-2 text-sm text-gray-500">
                <span className="inline-flex gap-1">
                  <span className="animate-bounce" style={{ animationDelay: '0ms' }}>.</span>
                  <span className="animate-bounce" style={{ animationDelay: '150ms' }}>.</span>
                  <span className="animate-bounce" style={{ animationDelay: '300ms' }}>.</span>
                </span>
              </div>
            </motion.div>
          )}
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/report/Refiner/MessageList.tsx
git commit -m "feat: add MessageList with starter prompts and auto-scroll"
```

---

## Task 8: RefinerSidebar Component

**Files:**
- Create: `frontend/src/components/report/Refiner/RefinerSidebar.tsx`
- Create: `frontend/src/components/report/Refiner/index.ts`

**Step 1: Write the sidebar**

```tsx
import { useState, useEffect, useCallback } from 'react'
import { X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import MessageList from './MessageList'
import MessageInput from './MessageInput'
import { refinerApi } from '../../../services/refinerApi'
import type { Message } from '../../../services/refinerApi'

interface RefinerSidebarProps {
  reportId: string
  isOpen: boolean
  onClose: () => void
}

export default function RefinerSidebar({ reportId, isOpen, onClose }: RefinerSidebarProps) {
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [starterPrompts, setStarterPrompts] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Initialize: create or load conversation
  useEffect(() => {
    if (!isOpen || conversationId) return

    const init = async () => {
      try {
        // Check for existing conversations
        const existing = await refinerApi.listConversations(reportId)
        if (existing.length > 0) {
          const conv = existing[0]
          setConversationId(conv.id)
          const msgs = await refinerApi.getMessages(reportId, conv.id)
          setMessages(msgs)
          if (conv.starter_prompts) {
            setStarterPrompts(conv.starter_prompts)
          }
        } else {
          // Create new conversation
          const conv = await refinerApi.createConversation(reportId)
          setConversationId(conv.id)
          setStarterPrompts(conv.starter_prompts || [])
        }
      } catch (err: any) {
        setError(err.message || 'Failed to start conversation')
      }
    }

    init()
  }, [isOpen, reportId, conversationId])

  const sendMessage = useCallback(async (content: string) => {
    if (!conversationId || isLoading) return

    // Optimistic: add user message
    const userMsg: Message = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])
    setIsLoading(true)
    setError(null)

    try {
      const response = await refinerApi.sendMessage(reportId, conversationId, content)
      // Replace temp + add assistant response
      setMessages(prev => [
        ...prev.filter(m => m.id !== userMsg.id),
        { ...userMsg, id: `user-${Date.now()}` },
        {
          id: response.id,
          role: 'assistant',
          content: response.content,
          model_used: response.model_used,
          tokens_used: response.tokens_used,
          created_at: new Date().toISOString(),
        },
      ])
    } catch (err: any) {
      setError(err.message || 'Failed to send message')
      // Remove optimistic user message on error
      setMessages(prev => prev.filter(m => m.id !== userMsg.id))
    } finally {
      setIsLoading(false)
    }
  }, [conversationId, reportId, isLoading])

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.aside
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="fixed right-0 top-0 h-full w-[400px] max-w-full z-40 bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-700 shadow-xl flex flex-col print:hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-sm font-semibold text-gray-900 dark:text-white">
              Report Refiner
            </h2>
            <button
              onClick={onClose}
              className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Error banner */}
          {error && (
            <div className="px-4 py-2 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-xs">
              {error}
            </div>
          )}

          {/* Messages */}
          <MessageList
            messages={messages}
            starterPrompts={starterPrompts}
            onStarterSelect={sendMessage}
            isLoading={isLoading}
          />

          {/* Input */}
          <MessageInput
            onSend={sendMessage}
            disabled={isLoading || !conversationId}
          />
        </motion.aside>
      )}
    </AnimatePresence>
  )
}
```

**Step 2: Write the barrel export**

```typescript
// frontend/src/components/report/Refiner/index.ts
export { default as RefinerButton } from './RefinerButton'
export { default as RefinerSidebar } from './RefinerSidebar'
export { default as MessageInput } from './MessageInput'
export { default as MessageList } from './MessageList'
```

**Step 3: Commit**

```bash
git add frontend/src/components/report/Refiner/
git commit -m "feat: add RefinerSidebar with conversation management"
```

---

## Task 9: Integrate into ReportViewer

**Files:**
- Modify: `frontend/src/pages/ReportViewer.tsx`

**Step 1: Add imports and state**

At the top of ReportViewer.tsx, add:

```typescript
import { RefinerButton, RefinerSidebar } from '../components/report/Refiner'
```

Add state near the other `useState` calls:

```typescript
const [refinerOpen, setRefinerOpen] = useState(false)
```

**Step 2: Add components to the render**

Inside the main return, after the closing `</div>` of the two-panel layout and before the final closing `</div>`:

```tsx
{/* Report Refiner */}
{report && (
  <>
    <RefinerButton
      onClick={() => setRefinerOpen(true)}
      isOpen={refinerOpen}
    />
    <RefinerSidebar
      reportId={report.id}
      isOpen={refinerOpen}
      onClose={() => setRefinerOpen(false)}
    />
  </>
)}
```

**Step 3: Verify frontend compiles**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -10`
Expected: No new errors

**Step 4: Commit**

```bash
git add frontend/src/pages/ReportViewer.tsx
git commit -m "feat: integrate Report Refiner into ReportViewer"
```

---

## Task 10: Verify End-to-End

**Step 1: Run all backend tests**

Run: `cd backend && pytest tests/ -q`
Expected: All tests pass, no regressions

**Step 2: Run frontend type check**

Run: `cd frontend && npx tsc --noEmit`
Expected: No type errors in Refiner components

**Step 3: Manual smoke test**

1. Start backend: `cd backend && uvicorn src.main:app --reload --port 8383`
2. Start frontend: `cd frontend && pnpm dev`
3. Open a report: `http://localhost:5174/report/579e62bd-139d-4e58-b3df-442425c427e9`
4. Verify "Ask your report" button appears bottom-right
5. Click it — sidebar should slide in
6. Verify 3 starter prompts appear
7. Click a starter prompt or type a question
8. Verify response comes back from the agent

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat: Report Refiner Phase 1 complete — AI conversation sidebar"
```

---

## Summary

| Task | Description | Files | Estimated |
|------|-------------|-------|-----------|
| 1 | Database migration | 1 new | 5 min |
| 2 | RefinerService + tests | 2 new | 15 min |
| 3 | API routes + tests | 3 new/modified | 15 min |
| 4 | Frontend API service | 1 new | 5 min |
| 5 | RefinerButton component | 1 new | 5 min |
| 6 | MessageInput component | 1 new | 5 min |
| 7 | MessageList component | 1 new | 10 min |
| 8 | RefinerSidebar component | 2 new | 15 min |
| 9 | ReportViewer integration | 1 modified | 5 min |
| 10 | End-to-end verification | 0 | 10 min |
