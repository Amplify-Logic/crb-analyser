"""
Report Generation Service

Generates CRB analysis reports from quiz session data.
Implements the two pillars methodology from FRAMEWORK.md.
"""

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, AsyncGenerator

from anthropic import Anthropic, RateLimitError, APIError, APIConnectionError


def clean_json_string(content: str) -> str:
    """Clean common JSON issues from LLM output."""
    # Remove markdown code blocks
    if "```" in content:
        # Find content between ``` markers
        match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
        if match:
            content = match.group(1)

    # Remove any leading/trailing whitespace
    content = content.strip()

    # Remove trailing commas before ] or }
    content = re.sub(r',\s*([}\]])', r'\1', content)

    # Remove JavaScript-style comments
    content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)

    return content


def safe_parse_json(content: str, fallback: Any = None) -> Any:
    """Safely parse JSON with cleaning and fallback."""
    try:
        cleaned = clean_json_string(content)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find a valid JSON array or object
        # Look for the outermost [ ] or { }
        try:
            # Find array
            arr_match = re.search(r'\[[\s\S]*\]', cleaned)
            if arr_match:
                return json.loads(arr_match.group())
        except json.JSONDecodeError:
            pass

        try:
            # Find object
            obj_match = re.search(r'\{[\s\S]*\}', cleaned)
            if obj_match:
                return json.loads(obj_match.group())
        except json.JSONDecodeError:
            pass

        return fallback

from src.config.settings import settings
from src.config.supabase_client import get_async_supabase
from src.config.ai_tools import get_ai_tools_prompt_context, get_build_it_yourself_context
from src.config.model_routing import get_model_for_task, TokenTracker
from src.config.system_prompt import get_full_system_prompt, get_analysis_system_prompt, get_recommendation_system_prompt
from src.knowledge import (
    get_industry_context,
    get_relevant_opportunities,
    get_vendor_recommendations,
    get_benchmarks_for_metrics,
    normalize_industry,
)
from src.expertise import get_self_improve_service, get_expertise_store
from src.skills import get_skill, SkillContext
from src.services.playbook_generator import PlaybookGenerator
from src.models.user_profile import UserProfile
from src.services.architecture_generator import ArchitectureGenerator
from src.services.insights_generator import InsightsGenerator
from src.services.review_service import ReviewService
from src.services.retrieval_service import get_retrieval_service
from src.models.generation_trace import TraceCollector

logger = logging.getLogger(__name__)

# Confidence-Adjusted ROI factors
# HIGH confidence: Full ROI estimate (100%)
# MEDIUM confidence: Moderate adjustment (85%)
# LOW confidence: Conservative adjustment (70%)
CONFIDENCE_FACTORS = {
    "high": 1.0,
    "medium": 0.85,
    "low": 0.70
}


def extract_vendor_mentions(recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract vendor mentions from recommendations for partnership tracking.

    Tracks which vendors appear in off_the_shelf and best_in_class options
    to understand which vendors are recommended most frequently.

    Returns:
        Dict with vendor_mentions list and category breakdown
    """
    vendor_mentions = []
    category_counts: Dict[str, int] = {}

    for rec in recommendations:
        options = rec.get("options", {})
        rec_title = rec.get("title", "Unknown")

        # Track off_the_shelf vendor
        off_shelf = options.get("off_the_shelf", {})
        if off_shelf.get("vendor"):
            vendor_name = off_shelf["vendor"]
            vendor_mentions.append({
                "vendor": vendor_name,
                "option_type": "off_the_shelf",
                "recommendation": rec_title,
                "monthly_cost": off_shelf.get("monthly_cost"),
            })
            category_counts[vendor_name] = category_counts.get(vendor_name, 0) + 1

        # Track best_in_class vendor
        best_class = options.get("best_in_class", {})
        if best_class.get("vendor"):
            vendor_name = best_class["vendor"]
            vendor_mentions.append({
                "vendor": vendor_name,
                "option_type": "best_in_class",
                "recommendation": rec_title,
                "monthly_cost": best_class.get("monthly_cost"),
            })
            category_counts[vendor_name] = category_counts.get(vendor_name, 0) + 1

    return {
        "mentions": vendor_mentions,
        "unique_vendors": list(set(m["vendor"] for m in vendor_mentions)),
        "vendor_counts": category_counts,
        "total_mentions": len(vendor_mentions),
    }


class ReportGenerator:
    """
    Generates CRB analysis reports following the two pillars methodology.

    Report tiers:
    - quick: 10-15 findings, essential recommendations
    - full: 25-50 findings, comprehensive analysis with roadmap
    """

    # Use the centralized system prompt from config module
    SYSTEM_PROMPT = get_full_system_prompt()

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAYS = [1, 2, 4]  # Exponential backoff delays in seconds

    def __init__(self, quiz_session_id: str, tier: str = "quick", model_strategy: Optional[str] = None):
        self.quiz_session_id = quiz_session_id
        self.tier = tier
        self.model_strategy = model_strategy  # Optional strategy override for dev testing
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.context: Dict[str, Any] = {}
        self.report_id: Optional[str] = None
        self.token_tracker = TokenTracker()
        self._partial_data: Dict[str, Any] = {}  # Store partial results for recovery
        self.review_service = ReviewService(tier=tier)  # Multi-model review & refinement
        self.trace_collector: Optional[TraceCollector] = None  # Initialized when report_id is created

        # Apply model strategy overrides
        self._apply_model_strategy()

    def _apply_model_strategy(self):
        """
        Apply model strategy overrides for dev testing.

        Strategies map to tier overrides:
        - anthropic_quick: Use quick tier (Sonnet)
        - anthropic_full: Use full tier (Opus for all)
        - hybrid/gemini_primary/etc: Set as active multi-model strategy
        """
        if not self.model_strategy:
            logger.info(f"Using default model routing for tier: {self.tier}")
            return

        logger.info(f"Applying model strategy: {self.model_strategy}")

        # Map strategy to tier behavior
        if self.model_strategy == "anthropic_quick":
            self.tier = "quick"  # Force quick tier (Sonnet)
        elif self.model_strategy == "anthropic_full":
            self.tier = "full"  # Force full tier (Opus)
        elif self.model_strategy in ["hybrid", "gemini_primary", "cost_optimized", "multi_provider", "budget"]:
            # These are multi-model strategies defined in model_routing.py
            # They'll be picked up by get_strategy_models() in the review service
            from src.config import model_routing
            model_routing.ACTIVE_STRATEGY = self.model_strategy
            logger.info(f"Set active multi-model strategy to: {self.model_strategy}")

        # Store strategy info in context for tracing
        self.context["model_strategy"] = self.model_strategy
        self.context["effective_tier"] = self.tier

    def _get_skill_context(self) -> SkillContext:
        """
        Build SkillContext from current report context.

        Used by skill-based generation methods for consistent context passing.
        """
        industry = self.context.get("industry", "general")

        # Get expertise data for this industry
        try:
            store = get_expertise_store()
            expertise = store.get_all_expertise_context(industry)
        except Exception as e:
            logger.warning(f"Could not load expertise for {industry}: {e}")
            expertise = None

        # Build user profile from quiz answers for four-options scoring
        answers = self.context.get("answers", {})
        existing_stack = self.context.get("existing_stack", [])
        api_ready = any(
            tool.get("api_score", 0) >= 3.5
            for tool in existing_stack
            if isinstance(tool, dict)
        )

        try:
            user_profile = UserProfile.from_quiz_answers(answers, existing_stack_api_ready=api_ready)
        except Exception as e:
            logger.warning(f"Could not build user profile: {e}")
            user_profile = None

        return SkillContext(
            industry=industry,
            company_name=self.context.get("company_name"),
            company_size=self.context.get("company_size"),
            quiz_answers=answers,
            interview_data=self.context.get("interview_data"),
            expertise=expertise,
            knowledge=self.context.get("industry_knowledge"),
            report_data=self.context,
            existing_stack=existing_stack,
            user_profile=user_profile,
        )

    def _call_claude(self, task: str, prompt: str, max_tokens: int = 4000) -> str:
        """
        Call Claude with appropriate model routing, token tracking, and retry logic.

        Implements exponential backoff for rate limits and transient errors.

        Args:
            task: Task identifier for model routing
            prompt: The prompt to send
            max_tokens: Maximum tokens in response

        Returns:
            Response text

        Raises:
            APIError: After all retries exhausted
        """
        import time as time_module
        model = get_model_for_task(task, self.tier)
        last_error = None
        start_time = time_module.time()

        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=self.SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt}],
                )

                # Calculate duration
                duration_ms = (time_module.time() - start_time) * 1000
                response_text = response.content[0].text.strip()

                # Track token usage
                self.token_tracker.add_usage(
                    task=task,
                    model=model,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                )

                # Log to trace collector
                if self.trace_collector:
                    self.trace_collector.log_llm_call(
                        task=task,
                        model=model,
                        prompt=prompt,
                        response=response_text,
                        input_tokens=response.usage.input_tokens,
                        output_tokens=response.usage.output_tokens,
                        duration_ms=duration_ms,
                    )

                return response_text

            except RateLimitError as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAYS[attempt]
                    logger.warning(
                        f"Rate limit hit for task '{task}', retrying in {delay}s "
                        f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    time_module.sleep(delay)
                    continue
                logger.error(f"Rate limit exhausted for task '{task}' after {self.MAX_RETRIES} attempts")
                if self.trace_collector:
                    self.trace_collector.log_error(f"Rate limit exhausted for {task}")
                raise

            except APIConnectionError as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAYS[attempt]
                    logger.warning(
                        f"Connection error for task '{task}', retrying in {delay}s "
                        f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    time_module.sleep(delay)
                    continue
                logger.error(f"Connection failed for task '{task}' after {self.MAX_RETRIES} attempts")
                if self.trace_collector:
                    self.trace_collector.log_error(f"Connection failed for {task}")
                raise

            except APIError as e:
                # Don't retry other API errors (e.g., invalid request)
                logger.error(f"API error for task '{task}': {e}")
                if self.trace_collector:
                    self.trace_collector.log_error(f"API error for {task}: {str(e)}")
                raise

        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise APIError("Unknown error in _call_claude")

    async def _save_partial_report(self, supabase, error_message: str) -> None:
        """
        Save partial report data for recovery.

        If report generation fails mid-way, this saves whatever we have
        so it can be reviewed or retried.
        """
        if not self.report_id:
            return

        try:
            # Base update - always safe
            partial_report = {
                "status": "partial",
                "error_message": error_message,
            }

            # Update with whatever partial data we have
            if self._partial_data.get("executive_summary"):
                partial_report["executive_summary"] = self._partial_data["executive_summary"]
            if self._partial_data.get("findings"):
                partial_report["findings"] = self._partial_data["findings"]
            if self._partial_data.get("recommendations"):
                partial_report["recommendations"] = self._partial_data["recommendations"]

            # Try with optional columns first
            try:
                optional_fields = {
                    "error_at": datetime.utcnow().isoformat(),
                    "partial_data": self._partial_data,
                    "token_usage": self.token_tracker.to_dict(),
                }
                await supabase.table("reports").update({**partial_report, **optional_fields}).eq("id", self.report_id).execute()
            except Exception as optional_err:
                if "column" in str(optional_err).lower() and "schema cache" in str(optional_err).lower():
                    # Some columns don't exist, use minimal update
                    logger.warning(f"Some columns missing in partial save: {optional_err}")
                    await supabase.table("reports").update(partial_report).eq("id", self.report_id).execute()
                else:
                    raise

            logger.info(f"Saved partial report {self.report_id} with data: {list(self._partial_data.keys())}")
        except Exception as save_error:
            logger.error(f"Failed to save partial report: {save_error}")

    def _categorize_error(self, error: Exception) -> Dict[str, Any]:
        """Categorize error for frontend display."""
        if isinstance(error, RateLimitError):
            return {
                "type": "rate_limit",
                "message": "AI service is busy. Please try again in a few minutes.",
                "retryable": True,
                "retry_after_seconds": 60,
            }
        elif isinstance(error, APIConnectionError):
            return {
                "type": "connection",
                "message": "Connection to AI service failed. Please check your internet and try again.",
                "retryable": True,
                "retry_after_seconds": 30,
            }
        elif isinstance(error, APIError):
            return {
                "type": "api_error",
                "message": "AI service returned an error. Our team has been notified.",
                "retryable": False,
            }
        else:
            return {
                "type": "unknown",
                "message": f"An unexpected error occurred: {str(error)}",
                "retryable": False,
            }

    async def generate_report(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate a full CRB report from quiz session data.

        Yields progress updates during generation.
        """
        supabase = await get_async_supabase()

        try:
            # Phase 1: Load quiz data
            yield {"phase": "loading", "step": "Loading quiz data...", "progress": 5}

            quiz_result = await supabase.table("quiz_sessions").select("*").eq(
                "id", self.quiz_session_id
            ).single().execute()

            if not quiz_result.data:
                raise ValueError(f"Quiz session not found: {self.quiz_session_id}")

            quiz_data = quiz_result.data
            self.context["quiz"] = quiz_data
            self.context["email"] = quiz_data.get("email")
            self.context["answers"] = quiz_data.get("answers", {})
            self.context["results"] = quiz_data.get("results", {})

            # Load company profile (research scrape data)
            self.context["company_profile"] = quiz_data.get("company_profile", {})
            self.context["company_name"] = quiz_data.get("company_name", "")
            self.context["company_website"] = quiz_data.get("company_website", "")

            # Load existing software stack (Phase 2C - Connect vs Replace)
            self.context["existing_stack"] = quiz_data.get("existing_stack", [])
            if self.context["existing_stack"]:
                logger.info(
                    f"Report input - Existing stack: {len(self.context['existing_stack'])} tools"
                )
                # Log tools with API scores
                for tool in self.context["existing_stack"][:5]:
                    api_score = tool.get("api_score", "?")
                    logger.info(
                        f"  - {tool.get('name', tool.get('slug', 'Unknown'))}: API score {api_score}/5"
                    )

            # Log input data for debugging
            logger.info(f"Report input - Company: {self.context['company_name']}")
            logger.info(f"Report input - Industry: {self.context['answers'].get('industry', 'unknown')}")
            logger.info(f"Report input - Answers keys: {list(self.context['answers'].keys())}")
            if self.context["company_profile"]:
                logger.info(f"Report input - Company profile keys: {list(self.context['company_profile'].keys())}")

            # Load interview data if available
            interview_data = quiz_data.get("interview_data", {})
            interview_completed = quiz_data.get("interview_completed", False)
            self.context["interview"] = {
                "transcript": interview_data.get("messages", []),
                "topics_covered": interview_data.get("topics_covered", []),
                "completed": interview_completed,
            }
            if interview_completed:
                logger.info(f"Loaded interview data: {len(self.context['interview']['transcript'])} messages")

            # Load validated assumptions if validation session was completed
            validated_assumptions = quiz_data.get("validated_assumptions", [])
            corrected_values = quiz_data.get("corrected_values", {})

            if corrected_values:
                yield {"phase": "loading", "step": "Applying validated assumptions...", "progress": 7}
                # Apply corrections to answers
                self.context["answers"] = self._apply_validated_corrections(
                    self.context["answers"],
                    corrected_values
                )
                logger.info(f"Applied {len(corrected_values)} validated corrections to report")

            # Store assumption tracking info
            self.context["validated_assumptions"] = validated_assumptions
            self.context["corrected_values"] = corrected_values
            self.context["assumption_log"] = {
                "validated_count": len(validated_assumptions),
                "corrections_applied": list(corrected_values.keys()),
                "validation_completed": bool(validated_assumptions or corrected_values)
            }

            # Create report record
            yield {"phase": "loading", "step": "Creating report...", "progress": 10}

            report_result = await supabase.table("reports").insert({
                "quiz_session_id": self.quiz_session_id,
                "tier": self.tier,
                "status": "generating",
                "generation_started_at": datetime.utcnow().isoformat(),
            }).execute()

            self.report_id = report_result.data[0]["id"]

            # Initialize trace collector now that we have report_id
            self.trace_collector = TraceCollector(
                report_id=self.report_id,
                session_id=self.quiz_session_id,
                tier=self.tier,
            )
            self.trace_collector.set_input_summary(
                company_name=self.context.get("company_name", "Unknown"),
                industry=self.context.get("answers", {}).get("industry", "unknown"),
                answers_count=len(self.context.get("answers", {})),
                interview_messages=len(self.context.get("interview", {}).get("transcript", [])),
                has_company_profile=bool(self.context.get("company_profile")),
            )
            self.trace_collector.start_phase("loading")
            self.trace_collector.add_step("Created report record")

            # Update quiz session with report ID
            await supabase.table("quiz_sessions").update({
                "report_id": self.report_id,
            }).eq("id", self.quiz_session_id).execute()

            self.trace_collector.end_phase("loading", f"Loaded session data for {self.context.get('company_name', 'Unknown')}")

            # Phase 2: Load industry context
            self.trace_collector.start_phase("research")
            yield {"phase": "research", "step": "Loading industry knowledge...", "progress": 15}

            industry = self._extract_industry()
            self.context["industry"] = industry
            self.context["industry_knowledge"] = get_industry_context(industry)
            self.context["opportunities"] = get_relevant_opportunities(industry)
            self.context["vendors"] = get_vendor_recommendations(industry)
            self.context["benchmarks"] = get_benchmarks_for_metrics(industry)

            # Log knowledge base data loaded
            kb_knowledge = self.context["industry_knowledge"]
            kb_opps = self.context["opportunities"]
            kb_vendors = self.context["vendors"]
            kb_benchmarks = self.context["benchmarks"]
            logger.info(f"Knowledge base - Industry: {industry}")
            logger.info(f"Knowledge base - Is supported: {kb_knowledge.get('is_supported', False)}")
            logger.info(f"Knowledge base - Opportunities loaded: {len(kb_opps) if kb_opps else 0}")
            logger.info(f"Knowledge base - Vendors loaded: {len(kb_vendors) if kb_vendors else 0}")
            logger.info(f"Knowledge base - Benchmark categories: {list(kb_benchmarks.keys()) if kb_benchmarks else []}")

            # Trace knowledge retrievals
            self.trace_collector.log_knowledge_retrieval(
                source="industry_knowledge",
                results_count=1 if kb_knowledge.get("is_supported") else 0,
                results_preview=[f"{industry} industry context"],
            )
            if kb_opps:
                self.trace_collector.log_knowledge_retrieval(
                    source="opportunities",
                    results_count=len(kb_opps),
                    results_preview=[o.get("title", o.get("name", "Unknown")) for o in kb_opps[:5]],
                )
            if kb_vendors:
                self.trace_collector.log_knowledge_retrieval(
                    source="vendors",
                    results_count=len(kb_vendors),
                    results_preview=[v.get("name", "Unknown") for v in kb_vendors[:5]],
                )
            if kb_benchmarks:
                self.trace_collector.log_knowledge_retrieval(
                    source="benchmarks",
                    results_count=len(kb_benchmarks),
                    results_preview=list(kb_benchmarks.keys())[:5],
                )

            yield {"phase": "research", "step": f"Loaded {industry} context", "progress": 18}

            # Phase 2b: Semantic retrieval from vector database (RAG)
            yield {"phase": "research", "step": "Retrieving relevant knowledge (RAG)...", "progress": 19}

            try:
                retrieval_service = await get_retrieval_service()

                # Build search query from quiz answers
                answers = self.context.get("answers", {})
                interview = self.context.get("interview", {})

                pain_points = answers.get("pain_points", [])
                if isinstance(pain_points, list):
                    pain_points = " ".join(pain_points)

                biggest_challenge = answers.get("biggest_challenge", "")
                interview_text = " ".join([
                    msg.get("content", "")
                    for msg in interview.get("transcript", [])
                    if msg.get("role") == "user"
                ])

                search_query = f"{pain_points} {biggest_challenge} {interview_text}".strip()

                if search_query:
                    semantic_context = await retrieval_service.get_relevant_context(
                        query=search_query,
                        industry=industry,
                        vendors_limit=10,
                        opportunities_limit=10,
                        case_studies_limit=5,
                        patterns_limit=5
                    )

                    self.context["semantic_retrieval"] = {
                        "query": search_query,
                        "vendors": [r.model_dump() for r in semantic_context.vendors],
                        "opportunities": [r.model_dump() for r in semantic_context.opportunities],
                        "case_studies": [r.model_dump() for r in semantic_context.case_studies],
                        "patterns": [r.model_dump() for r in semantic_context.patterns],
                        "total_results": semantic_context.total_results,
                        "search_time_ms": semantic_context.search_time_ms,
                    }
                    self.context["semantic_prompt"] = semantic_context.to_prompt_context()

                    logger.info(
                        f"RAG retrieval: {semantic_context.total_results} results in {semantic_context.search_time_ms:.1f}ms"
                    )
                    logger.info(f"RAG - Vendors: {len(semantic_context.vendors)}, Opportunities: {len(semantic_context.opportunities)}")

                    # Trace semantic retrieval
                    self.trace_collector.log_knowledge_retrieval(
                        source="semantic_rag",
                        query=search_query[:200],
                        results_count=semantic_context.total_results,
                        results_preview=[
                            *[v.title for v in semantic_context.vendors[:3]],
                            *[o.title for o in semantic_context.opportunities[:3]],
                        ],
                        duration_ms=semantic_context.search_time_ms,
                    )
                else:
                    self.context["semantic_retrieval"] = {}
                    self.context["semantic_prompt"] = ""
                    logger.info("No query content for semantic retrieval")

            except Exception as e:
                # Semantic retrieval is enhancement - continue without it
                logger.warning(f"Semantic retrieval failed (non-critical): {e}")
                self.context["semantic_retrieval"] = {}
                self.context["semantic_prompt"] = ""
                self.trace_collector.log_error(f"Semantic retrieval failed: {str(e)}")

            self.trace_collector.end_phase("research", f"Loaded {industry} knowledge base with RAG")
            yield {"phase": "research", "step": f"Loaded {industry} context", "progress": 20}

            # Phase 3: Generate analysis
            self.trace_collector.start_phase("analysis")
            yield {"phase": "analysis", "step": "Analyzing business context...", "progress": 25}

            executive_summary = await self._generate_executive_summary()
            self._partial_data["executive_summary"] = executive_summary  # Track for recovery

            # Log decision about AI readiness score
            self.trace_collector.log_decision(
                decision_type="ai_readiness_score",
                input_factors={
                    "company_size": self.context.get("answers", {}).get("company_size"),
                    "current_tools": len(self.context.get("answers", {}).get("current_tools", [])),
                    "pain_points": len(self.context.get("answers", {}).get("pain_points", [])),
                    "interview_depth": len(self.context.get("interview", {}).get("transcript", [])),
                },
                outcome=f"Score: {executive_summary.get('ai_readiness_score', 'N/A')}",
                reasoning=executive_summary.get("key_insight", "Based on business maturity and automation potential"),
            )

            self.trace_collector.end_phase("analysis", f"AI Readiness: {executive_summary.get('ai_readiness_score', 'N/A')}/100")
            yield {"phase": "analysis", "step": "Executive summary complete", "progress": 35}

            # Save progress
            await supabase.table("reports").update({
                "executive_summary": executive_summary,
            }).eq("id", self.report_id).execute()

            # Phase 4: Generate findings
            self.trace_collector.start_phase("findings")
            yield {"phase": "findings", "step": "Generating findings...", "progress": 40}

            findings = await self._generate_findings()
            self._partial_data["findings"] = findings  # Track for recovery

            # Emit preview of each finding for real-time UI updates
            for i, finding in enumerate(findings):
                progress = 40 + int((i + 1) * 15 / max(len(findings), 1))
                yield {
                    "phase": "findings",
                    "step": f"Found: {finding.get('title', 'Finding')}",
                    "progress": progress,
                    "preview": {
                        "type": "finding",
                        "id": finding.get("id"),
                        "title": finding.get("title"),
                        "category": finding.get("category"),
                        "customer_value_score": finding.get("customer_value_score"),
                        "business_health_score": finding.get("business_health_score"),
                        "confidence": finding.get("confidence"),
                        "is_not_recommended": finding.get("is_not_recommended", False),
                    }
                }

            # Log decisions about findings
            for finding in findings[:3]:  # Log first 3 as examples
                self.trace_collector.log_decision(
                    decision_type="finding_generation",
                    input_factors={
                        "category": finding.get("category"),
                        "source": finding.get("source", "analysis"),
                    },
                    outcome=finding.get("title", "Unknown"),
                    reasoning=f"Confidence: {finding.get('confidence', 'N/A')}, Impact: {finding.get('impact', 'N/A')}",
                )

            self.trace_collector.end_phase("findings", f"Generated {len(findings)} findings")
            yield {"phase": "findings", "step": f"Generated {len(findings)} findings", "progress": 50}

            # Phase 4b: Review & Refine findings with multi-model validation
            self.trace_collector.start_phase("review")
            yield {"phase": "review", "step": "Validating findings with research...", "progress": 52}

            # Build original sources for review
            original_sources = {
                "quiz": self.context.get("answers", {}),
                "interview": self.context.get("interview", {}),
                "research": self.context.get("industry_knowledge", {}),
            }

            # Review and refine findings
            try:
                review_result = await self.review_service.review_and_refine(
                    content={"findings": findings},
                    content_type="findings",
                    original_sources=original_sources,
                    industry=self.context.get("industry", "general"),
                )

                # Use refined findings
                findings = review_result.get("content", findings)
                quality_scores = review_result.get("review_scores", {})
                findings_added = review_result.get("findings_added", 0)

                # Update executive summary if needed
                exec_updates = review_result.get("executive_summary_updates", {})
                if exec_updates:
                    executive_summary.update(exec_updates)

                yield {
                    "phase": "review",
                    "step": f"Validated: {quality_scores.get('overall', '?')}/10 quality, +{findings_added} findings",
                    "progress": 58,
                    "quality_scores": quality_scores,
                }

                logger.info(
                    f"Review complete - Quality: {quality_scores.get('overall', '?')}/10, "
                    f"Findings: {len(findings)}, Added: {findings_added}"
                )

            except Exception as review_error:
                logger.warning(f"Review step failed, using original findings: {review_error}")
                self.trace_collector.log_error(f"Review failed: {str(review_error)}")
                yield {"phase": "review", "step": "Review skipped (using original)", "progress": 58}

            self.trace_collector.end_phase("review", f"Quality score: {quality_scores.get('overall', 'N/A') if 'quality_scores' in dir() else 'skipped'}/10")
            self._partial_data["findings"] = findings  # Update with refined findings

            await supabase.table("reports").update({
                "findings": findings,
            }).eq("id", self.report_id).execute()

            # Phase 5: Generate recommendations
            self.trace_collector.start_phase("recommendations")
            yield {"phase": "recommendations", "step": "Generating recommendations...", "progress": 60}

            recommendations = await self._generate_recommendations(findings)
            self._partial_data["recommendations"] = recommendations  # Track for recovery

            # Emit preview of each recommendation
            for i, rec in enumerate(recommendations):
                progress = 60 + int((i + 1) * 15 / max(len(recommendations), 1))
                yield {
                    "phase": "recommendations",
                    "step": f"Recommendation: {rec.get('title', 'Recommendation')}",
                    "progress": progress,
                    "preview": {
                        "type": "recommendation",
                        "id": rec.get("id"),
                        "title": rec.get("title"),
                        "priority": rec.get("priority"),
                        "our_recommendation": rec.get("our_recommendation"),
                        "roi_percentage": rec.get("roi_percentage"),
                        "payback_months": rec.get("payback_months"),
                    }
                }

            self.trace_collector.end_phase("recommendations", f"Generated {len(recommendations)} recommendations")
            yield {"phase": "recommendations", "step": f"Generated {len(recommendations)} recommendations", "progress": 73}

            # Phase 5a: Validate math in findings and recommendations
            self.trace_collector.start_phase("validation")
            yield {"phase": "validation", "step": "Validating calculations...", "progress": 74}

            validation_results = await self._validate_math(findings, recommendations)
            self._partial_data["math_validation"] = validation_results

            # Trace validation results
            # confidence_adjustments may be an int count, convert to descriptive list
            adjustments = validation_results.get("confidence_adjustments", [])
            if isinstance(adjustments, int):
                adjustments = [f"{adjustments} confidence adjustment(s) applied"] if adjustments > 0 else []
            elif not isinstance(adjustments, list):
                adjustments = [str(adjustments)] if adjustments else []

            self.trace_collector.log_validation(
                validation_type="math_check",
                items_checked=len(findings) + len(recommendations),
                issues_found=validation_results.get("issues_found", 0),
                adjustments_made=adjustments,
            )

            if validation_results.get("issues_found", 0) > 0:
                yield {
                    "phase": "validation",
                    "step": f"⚠️ Found {validation_results['issues_found']} math issue(s) - adjusted confidence",
                    "progress": 75,
                    "preview": {
                        "type": "validation_warning",
                        "issues": validation_results.get("issues_found"),
                        "adjustments": validation_results.get("confidence_adjustments"),
                    }
                }
            else:
                yield {"phase": "validation", "step": "✓ All calculations verified", "progress": 75}

            self.trace_collector.end_phase("validation", f"Checked {len(findings) + len(recommendations)} items, {validation_results.get('issues_found', 0)} issues")

            # Update findings and recommendations - be resilient to missing columns
            try:
                await supabase.table("reports").update({
                    "recommendations": recommendations,
                    "findings": findings,
                    "math_validation": validation_results,
                }).eq("id", self.report_id).execute()
            except Exception as db_err:
                if "column" in str(db_err).lower() and "schema cache" in str(db_err).lower():
                    logger.warning(f"Some columns missing, saving without math_validation: {db_err}")
                    await supabase.table("reports").update({
                        "recommendations": recommendations,
                        "findings": findings,
                    }).eq("id", self.report_id).execute()
                else:
                    raise

            # Phase 5b: Identify quick wins
            yield {"phase": "quick_wins", "step": "Identifying quick wins...", "progress": 76}

            quick_wins = await self._identify_quick_wins(findings, recommendations)
            self._partial_data["quick_wins"] = quick_wins

            yield {"phase": "quick_wins", "step": f"Found {len(quick_wins.get('quick_wins', []))} quick wins", "progress": 78}

            # Phase 6: Generate roadmap and value summary
            yield {"phase": "roadmap", "step": "Building implementation roadmap...", "progress": 80}

            roadmap = await self._generate_roadmap(recommendations)
            roadmap["quick_wins"] = quick_wins.get("quick_wins", [])  # Add quick wins to roadmap

            value_summary = self._calculate_value_summary(findings, recommendations)
            methodology_notes = self._generate_methodology_notes()

            # Generate verdict - the honest consultant assessment
            verdict = await self._generate_verdict(executive_summary, findings, recommendations, value_summary)

            await supabase.table("reports").update({
                "roadmap": roadmap,
                "value_summary": value_summary,
                "methodology_notes": methodology_notes,
                "executive_summary": {**executive_summary, "verdict": verdict},
            }).eq("id", self.report_id).execute()

            yield {"phase": "roadmap", "step": "Roadmap complete", "progress": 80}

            # Phase 6b: Generate playbooks
            yield {"phase": "playbooks", "step": "Generating implementation playbooks...", "progress": 82}

            playbooks = await self._generate_playbooks(recommendations)
            self._partial_data["playbooks"] = playbooks

            yield {"phase": "playbooks", "step": f"Generated {len(playbooks)} playbooks", "progress": 86}

            # Phase 6c: Generate system architecture
            yield {"phase": "architecture", "step": "Building system architecture...", "progress": 88}

            system_architecture = self._generate_system_architecture(recommendations)
            self._partial_data["system_architecture"] = system_architecture

            yield {"phase": "architecture", "step": "System architecture complete", "progress": 90}

            # Phase 6d: Generate industry insights
            yield {"phase": "insights", "step": "Loading industry insights...", "progress": 92}

            industry_insights = await self._generate_industry_insights()
            self._partial_data["industry_insights"] = industry_insights

            yield {"phase": "insights", "step": "Industry insights complete", "progress": 92}

            # Phase 6e: Generate automation summary (Connect vs Replace roadmap)
            yield {"phase": "automation_summary", "step": "Building automation roadmap...", "progress": 93}

            automation_summary = await self._generate_automation_summary(findings)
            self._partial_data["automation_summary"] = automation_summary

            yield {"phase": "automation_summary", "step": "Automation roadmap complete", "progress": 93}

            # Phase 6f: Generate post-report metadata (follow-up, upsell)
            yield {"phase": "post_report", "step": "Preparing follow-up plan...", "progress": 93}

            post_report_data = await self._generate_post_report_metadata(
                report={
                    "findings": findings,
                    "recommendations": recommendations,
                    "verdict": verdict,
                },
                quick_wins=quick_wins.get("quick_wins", []),
            )
            self._partial_data["post_report_metadata"] = post_report_data

            yield {"phase": "post_report", "step": "Follow-up plan ready", "progress": 94}

            # Save all new enhanced report data - be resilient to missing columns
            try:
                await supabase.table("reports").update({
                    "playbooks": playbooks,
                    "system_architecture": system_architecture,
                    "industry_insights": industry_insights,
                    "automation_summary": automation_summary,
                    "follow_up_schedule": post_report_data.get("follow_up_schedule", {}),
                    "upsell_analysis": post_report_data.get("upsell_analysis", {}),
                }).eq("id", self.report_id).execute()
            except Exception as db_err:
                if "column" in str(db_err).lower() and "schema cache" in str(db_err).lower():
                    logger.warning(f"Some columns missing, saving core data only: {db_err}")
                    try:
                        await supabase.table("reports").update({
                            "playbooks": playbooks,
                            "system_architecture": system_architecture,
                            "industry_insights": industry_insights,
                            "automation_summary": automation_summary,
                        }).eq("id", self.report_id).execute()
                    except Exception:
                        # Last resort - save nothing extra
                        logger.warning("Could not save enhanced report data, continuing anyway")
                else:
                    raise

            # Phase 7: Finalize
            self.trace_collector.start_phase("finalization")
            logger.info(f"[FINALIZE] Starting finalize phase for report {self.report_id}")
            yield {"phase": "finalizing", "step": "Finalizing report...", "progress": 96}

            # Get token usage summary
            logger.info(f"[FINALIZE] Calculating token usage...")
            token_summary = self.token_tracker.get_summary()
            logger.info(f"[FINALIZE] Report {self.report_id} token usage: {token_summary['total_tokens']} tokens, ~${token_summary['estimated_cost_usd']}")

            # Finalize the generation trace
            generation_trace = self.trace_collector.finalize()
            logger.info(f"[FINALIZE] Generation trace: {generation_trace.total_llm_calls} LLM calls, {len(generation_trace.phases)} phases")

            # Update report status - goes to qa_pending for human review
            # Status flow: generating → qa_pending → (QA review) → released
            update_data = {
                "status": "qa_pending",
                "generation_completed_at": datetime.utcnow().isoformat(),
            }

            # Build comprehensive assumption log with RAG data
            assumption_log = self.context.get("assumption_log", {})
            assumption_log["semantic_retrieval"] = {
                "query": self.context.get("semantic_retrieval", {}).get("query", ""),
                "total_results": self.context.get("semantic_retrieval", {}).get("total_results", 0),
                "search_time_ms": self.context.get("semantic_retrieval", {}).get("search_time_ms", 0),
                "opportunities_retrieved": len(self.context.get("semantic_retrieval", {}).get("opportunities", [])),
                "vendors_retrieved": len(self.context.get("semantic_retrieval", {}).get("vendors", [])),
                "case_studies_retrieved": len(self.context.get("semantic_retrieval", {}).get("case_studies", [])),
            }

            # Track vendor mentions for partnership analytics
            # This helps identify which vendors appear most in recommendations
            vendor_tracking = extract_vendor_mentions(recommendations)
            assumption_log["vendor_mentions"] = vendor_tracking
            if vendor_tracking["total_mentions"] > 0:
                logger.info(f"[FINALIZE] Tracked {vendor_tracking['total_mentions']} vendor mentions: {vendor_tracking['unique_vendors']}")

            logger.info(f"[FINALIZE] Updating report status to qa_pending...")
            try:
                # Try with all fields first including generation trace
                await supabase.table("reports").update({
                    **update_data,
                    "token_usage": self.token_tracker.to_dict(),
                    "assumption_log": assumption_log,
                    "generation_trace": generation_trace.to_dict(),
                }).eq("id", self.report_id).execute()
                logger.info(f"[FINALIZE] Report status updated successfully with generation trace")
            except Exception as update_err:
                if "column" in str(update_err).lower() and "schema cache" in str(update_err).lower():
                    # Column doesn't exist, try without generation_trace
                    logger.warning(f"[FINALIZE] Some columns missing, trying without generation_trace: {update_err}")
                    try:
                        await supabase.table("reports").update({
                            **update_data,
                            "token_usage": self.token_tracker.to_dict(),
                            "assumption_log": assumption_log,
                        }).eq("id", self.report_id).execute()
                        logger.info(f"[FINALIZE] Report status updated without generation_trace")
                    except Exception:
                        await supabase.table("reports").update(update_data).eq("id", self.report_id).execute()
                        logger.info(f"[FINALIZE] Report status updated with minimal data")
                else:
                    raise

            # Update quiz session - pending QA review
            logger.info(f"[FINALIZE] Updating quiz session status to qa_pending...")
            await supabase.table("quiz_sessions").update({
                "status": "qa_pending",
                "report_generated_at": datetime.utcnow().isoformat(),
            }).eq("id", self.quiz_session_id).execute()
            logger.info(f"[FINALIZE] Quiz session status updated successfully")

            # Learn from this analysis to improve future reports
            logger.info(f"[FINALIZE] Starting expertise learning (may take a moment)...")
            try:
                expertise_service = get_self_improve_service()
                learning_context = {
                    "findings": findings,
                    "recommendations": [],  # Extracted from findings
                    "ai_readiness_score": executive_summary.get("ai_readiness_score", 50),
                    "total_potential_savings": executive_summary.get("total_value_potential", {}).get("max", 0),
                }
                execution_metrics = {
                    "tools_used": {},
                    "token_usage": self.token_tracker.to_dict(),
                    "phases_completed": ["executive_summary", "findings", "playbook", "architecture", "insights"],
                    "errors": [],
                }
                logger.info(f"[FINALIZE] Calling expertise_service.learn_from_analysis...")
                await expertise_service.learn_from_analysis(
                    audit_id=self.report_id,
                    industry=self.context.get("industry", "general"),
                    company_size=self.context.get("answers", {}).get("employee_count", "unknown"),
                    context=learning_context,
                    execution_metrics=execution_metrics,
                )
                logger.info(f"[FINALIZE] Expertise updated from report {self.report_id}")
            except Exception as learn_err:
                logger.warning(f"[FINALIZE] Expertise learning failed (non-critical): {learn_err}")

            logger.info(f"[FINALIZE] All finalize steps complete, yielding completion event for report {self.report_id}")
            yield {
                "phase": "complete",
                "step": "Report generation complete!",
                "progress": 100,
                "report_id": self.report_id,
                "executive_summary": executive_summary,
                "math_validation": {
                    "passed": validation_results.get("issues_found", 0) == 0,
                    "issues": validation_results.get("issues_found", 0),
                    "warnings": validation_results.get("warnings_found", 0),
                    "confidence_adjustments": validation_results.get("confidence_adjustments", 0),
                },
            }

        except Exception as e:
            logger.error(f"Report generation error: {e}", exc_info=True)

            # Categorize error for user-friendly display
            error_info = self._categorize_error(e)

            # Save partial report if we have any data
            if self.report_id and self._partial_data:
                await self._save_partial_report(supabase, str(e))
                logger.info(f"Partial report saved for {self.report_id}")
            elif self.report_id:
                # No partial data, just mark as failed - be resilient to missing columns
                try:
                    await supabase.table("reports").update({
                        "status": "failed",
                        "error_message": str(e),
                        "error_at": datetime.utcnow().isoformat(),
                        "token_usage": self.token_tracker.to_dict(),
                    }).eq("id", self.report_id).execute()
                except Exception as update_err:
                    if "column" in str(update_err).lower() and "schema cache" in str(update_err).lower():
                        # Minimal update without optional columns
                        await supabase.table("reports").update({
                            "status": "failed",
                            "error_message": str(e),
                        }).eq("id", self.report_id).execute()
                    else:
                        raise

            yield {
                "phase": "error",
                "step": error_info["message"],
                "progress": 0,
                "error": str(e),
                "error_info": error_info,
                "has_partial_data": bool(self._partial_data),
                "report_id": self.report_id,  # Include report_id for potential retry
            }

    def _apply_validated_corrections(
        self,
        answers: Dict[str, Any],
        corrections: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply validated corrections from assumption validation session.

        Maps assumption IDs to answer fields and updates values.
        """
        updated_answers = dict(answers)

        # Mapping of assumption IDs to answer fields
        assumption_to_field = {
            "assum-hourly-rate": "hourly_rate",
            "assum-team-size": "employee_count",
            "assum-manual-hours": "manual_hours",
            "assum-tech-budget": "monthly_tech_spend",
            "assum-revenue": "annual_revenue",
            "assum-timeline": "timeline",
        }

        for assumption_id, corrected_value in corrections.items():
            field = assumption_to_field.get(assumption_id)
            if field:
                updated_answers[field] = corrected_value
                logger.info(f"Applied correction: {field} = {corrected_value}")
            else:
                # Store unknown corrections in a special field
                if "validated_data" not in updated_answers:
                    updated_answers["validated_data"] = {}
                updated_answers["validated_data"][assumption_id] = corrected_value

        return updated_answers

    def _extract_industry(self) -> str:
        """Extract and normalize industry from quiz answers."""
        answers = self.context.get("answers", {})
        results = self.context.get("results", {})

        # Try to get industry from various sources
        industry = answers.get("industry") or results.get("industry") or "general"
        return normalize_industry(industry)

    async def _generate_executive_summary(self) -> Dict[str, Any]:
        """
        Generate executive summary using the ExecSummarySkill.

        Uses the skills framework for consistent output and expertise integration.
        Falls back to legacy method if skill fails.
        """
        # Try skill-based generation first
        skill = get_skill("exec-summary", client=self.client)

        if skill:
            try:
                context = self._get_skill_context()
                result = await skill.run(context)

                if result.success:
                    logger.info(
                        f"Executive summary generated via skill "
                        f"(expertise_applied={result.expertise_applied}, "
                        f"execution_time={result.execution_time_ms:.0f}ms)"
                    )
                    return result.data
                else:
                    logger.warning(
                        f"ExecSummarySkill failed, using legacy method: "
                        f"{result.warnings}"
                    )
            except Exception as e:
                logger.warning(f"Skill execution failed, using legacy: {e}")

        # Fall back to legacy method
        return await self._generate_executive_summary_legacy()

    async def _generate_executive_summary_legacy(self) -> Dict[str, Any]:
        """Generate executive summary using Claude (legacy method)."""
        answers = self.context.get("answers", {})
        results = self.context.get("results", {})
        industry_knowledge = self.context.get("industry_knowledge", {})

        prompt = f"""Based on the following quiz responses, generate an executive summary for a CRB Analysis report.

QUIZ ANSWERS:
{json.dumps(answers, indent=2)}

PRELIMINARY RESULTS:
{json.dumps(results, indent=2)}

INDUSTRY: {self.context.get('industry', 'general')}
INDUSTRY KNOWLEDGE AVAILABLE: {industry_knowledge.get('is_supported', False)}

Generate a JSON executive summary with this EXACT structure:
{{
    "shareable_summary": "<ONE sentence that captures the key finding AND top action. Format: 'You're [situation]. Priority: [action].' Example: 'You're leaving €47K/year on the table with manual invoicing. Priority: automate client billing this week.'>"
    "ai_readiness_score": <number 0-100>,
    "customer_value_score": <number 1-10>,
    "business_health_score": <number 1-10>,
    "key_insight": "<one sentence main insight>",
    "total_value_potential": {{
        "min": <number in euros>,
        "max": <number in euros>,
        "projection_years": 3
    }},
    "top_opportunities": [
        {{
            "title": "<opportunity name>",
            "value_potential": "<range like €10K-20K>",
            "time_horizon": "short|mid|long"
        }}
    ],
    "not_recommended": [
        {{
            "title": "<what NOT to do>",
            "reason": "<why not>"
        }}
    ],
    "recommended_investment": {{
        "year_1_min": <number>,
        "year_1_max": <number>
    }}
}}

CRITICAL: The "shareable_summary" must be ONE sentence that a busy executive can forward to their team. It should state the situation AND the priority action.

Be realistic and honest. Include at least one "not_recommended" item.
Return ONLY the JSON, no explanation."""

        default_summary = {
            "shareable_summary": "Analysis in progress. Priority: complete the assessment for personalized recommendations.",
            "ai_readiness_score": results.get("ai_readiness_score", 50),
            "customer_value_score": 5,
            "business_health_score": 5,
            "key_insight": "Analysis requires more data for accurate assessment.",
            "total_value_potential": {"min": 10000, "max": 50000, "projection_years": 3},
            "top_opportunities": [],
            "not_recommended": [],
            "recommended_investment": {"year_1_min": 2000, "year_1_max": 10000},
        }

        try:
            content = self._call_claude("generate_executive_summary", prompt, max_tokens=2000)
            summary = safe_parse_json(content, default_summary)
            if not isinstance(summary, dict):
                summary = default_summary

            # Add report date at the top
            summary["report_date"] = datetime.utcnow().strftime("%B %d, %Y")
            return summary
        except Exception as e:
            logger.error(f"Failed to parse executive summary: {e}")
            default_summary["report_date"] = datetime.utcnow().strftime("%B %d, %Y")
            return default_summary

    async def _generate_findings(self) -> List[Dict[str, Any]]:
        """
        Generate findings using the FindingGenerationSkill.

        Uses the skills framework for consistent output and expertise integration.
        Falls back to legacy method if skill fails.
        """
        # Try skill-based generation first
        skill = get_skill("finding-generation", client=self.client)

        if skill:
            try:
                context = self._get_skill_context()
                # Pass tier info for finding count
                context.metadata["tier"] = self.tier
                result = await skill.run(context)

                if result.success:
                    logger.info(
                        f"Findings generated via skill "
                        f"(count={len(result.data)}, "
                        f"expertise_applied={result.expertise_applied}, "
                        f"execution_time={result.execution_time_ms:.0f}ms)"
                    )
                    return result.data
                else:
                    logger.warning(
                        f"FindingGenerationSkill failed, using legacy method: "
                        f"{result.warnings}"
                    )
            except Exception as e:
                logger.warning(f"Skill execution failed, using legacy: {e}")

        # Fall back to legacy method
        return await self._generate_findings_legacy()

    async def _generate_findings_legacy(self) -> List[Dict[str, Any]]:
        """Generate findings using Claude (legacy method)."""
        answers = self.context.get("answers", {})
        opportunities = self.context.get("opportunities", [])
        benchmarks = self.context.get("benchmarks", {})
        semantic_prompt = self.context.get("semantic_prompt", "")
        semantic_retrieval = self.context.get("semantic_retrieval", {})

        # Request fewer findings for more reliable JSON output
        max_findings = 10 if self.tier == "quick" else 15
        min_not_recommended = 3

        # Build list of valid sources from retrieval
        valid_sources = []
        for opp in semantic_retrieval.get("opportunities", []):
            valid_sources.append(f"Opportunity: {opp.get('title')} (similarity: {opp.get('similarity', 0):.0%})")
        for vendor in semantic_retrieval.get("vendors", []):
            valid_sources.append(f"Vendor: {vendor.get('title')}")
        for cs in semantic_retrieval.get("case_studies", []):
            valid_sources.append(f"Case Study: {cs.get('title')}")

        prompt = f"""Analyze the quiz responses and generate findings for a CRB report.

QUIZ ANSWERS:
{json.dumps(answers, indent=2)}

INDUSTRY OPPORTUNITIES AVAILABLE:
{json.dumps(opportunities[:5], indent=2) if opportunities else "None specific"}

INDUSTRY BENCHMARKS:
{json.dumps(benchmarks, indent=2) if benchmarks else "Use general industry standards"}

═══════════════════════════════════════════════════════════════════════════════
SEMANTICALLY RETRIEVED KNOWLEDGE (RAG - USE THESE SOURCES!)
═══════════════════════════════════════════════════════════════════════════════

{semantic_prompt if semantic_prompt else "No semantic retrieval available - use industry opportunities and benchmarks above."}

VALID SOURCES FOR CITATION (you MUST cite from this list):
{chr(10).join(f"- {src}" for src in valid_sources[:20]) if valid_sources else "- Use quiz answers and benchmarks above"}

═══════════════════════════════════════════════════════════════════════════════
FINDING REQUIREMENTS
═══════════════════════════════════════════════════════════════════════════════

Generate {max_findings} findings total:
- At least {max_findings - min_not_recommended} RECOMMENDED findings (score 6+ on BOTH pillars)
- Exactly {min_not_recommended} NOT-RECOMMENDED findings (score below 6 on at least one pillar)

═══════════════════════════════════════════════════════════════════════════════
SOURCE CITATION REQUIREMENTS (CRITICAL)
═══════════════════════════════════════════════════════════════════════════════

Every finding MUST have at least one specific source. Valid source types:

1. Quiz response: "Based on your answer: '[quote from their answer]'"
2. Industry benchmark: "Industry average: X (Source: [benchmark name])"
3. Calculation: "Calculated: [formula with numbers]"
4. Industry pattern: "[Industry] businesses typically see [pattern]"

DO NOT use generic sources like "Industry benchmark" without specifics.

═══════════════════════════════════════════════════════════════════════════════
CONFIDENCE SCORING CRITERIA (REQUIRED)
═══════════════════════════════════════════════════════════════════════════════

Rate each finding's confidence based on evidence strength:

HIGH confidence (use for ~30% of findings):
- Quiz answer directly mentions this specific problem/need
- Multiple data points support the finding
- Calculation uses numbers provided by user
- Industry benchmark directly applies to their situation

MEDIUM confidence (use for ~50% of findings):
- Quiz answer implies this issue (reasonable inference)
- Industry pattern likely applies to their profile
- Calculation uses reasonable assumptions
- One strong supporting data point

LOW confidence (use for ~20% of findings):
- No direct quiz support, but industry pattern suggests this
- Significant assumptions required
- Hypothesis worth validating
- Limited data available

Distribution requirement: Include a mix - not all findings should be HIGH confidence.

═══════════════════════════════════════════════════════════════════════════════

Generate a JSON array with this structure:
{{
    "id": "finding-001",
    "title": "Short descriptive title",
    "description": "Clear description of the opportunity or issue",
    "category": "efficiency|growth|risk|compliance|customer_experience",
    "customer_value_score": <1-10>,
    "business_health_score": <1-10>,
    "current_state": "How they're doing this now (from quiz answers)",
    "value_saved": {{
        "hours_per_week": <REQUIRED: estimate hours saved 1-20>,
        "hourly_rate": 50,
        "annual_savings": <REQUIRED: hours * 50 * 52>
    }},
    "value_created": {{
        "description": "How this creates new value",
        "potential_revenue": <number or 0 if pure efficiency>
    }},
    "confidence": "high|medium|low",
    "sources": [
        "Based on your answer: '[specific quote]'",
        "Industry benchmark: [specific metric]"
    ],
    "time_horizon": "short|mid|long",
    "is_not_recommended": false,
    "why_not": null,
    "what_instead": null
}}

CRITICAL - VALUE_SAVED IS REQUIRED:
- EVERY finding MUST have value_saved.hours_per_week estimated (even if 1 hour)
- Use these guidelines for estimation:
  * Manual data entry tasks: 2-5 hours/week
  * Client communication: 3-8 hours/week
  * Scheduling/coordination: 2-4 hours/week
  * Reporting/admin: 2-6 hours/week
  * Research/lookup: 1-3 hours/week
- Calculate annual_savings = hours_per_week * 50 * 52

For NOT-RECOMMENDED findings, set:
- is_not_recommended: true
- customer_value_score or business_health_score below 6
- why_not: "Clear explanation of why this shouldn't be done"
- what_instead: "What they should do instead"

Example not-recommended finding:
{{
    "id": "finding-not-001",
    "title": "Full AI Customer Service Replacement",
    "description": "Completely replacing human support with AI chatbots",
    "category": "customer_experience",
    "customer_value_score": 3,
    "business_health_score": 4,
    "current_state": "You mentioned having a small support team",
    "confidence": "high",
    "sources": ["Studies show 40% customer satisfaction drop with full AI replacement"],
    "time_horizon": "short",
    "is_not_recommended": true,
    "why_not": "Customer satisfaction typically drops 40% with full AI replacement. Your customers expect human connection.",
    "what_instead": "Implement AI-assisted human support instead - AI handles tier 1, humans handle complex issues"
}}

IMPORTANT:
- Return ONLY a valid JSON array
- Every source must be specific and cite evidence
- Include exactly {min_not_recommended} not-recommended findings"""

        try:
            content = self._call_claude("generate_findings", prompt, max_tokens=10000)
            findings = safe_parse_json(content, [])

            if not isinstance(findings, list):
                logger.error(f"Findings is not a list: {type(findings)}")
                return []

            # Validate and enrich each finding
            validated_findings = []
            confidence_counts = {"high": 0, "medium": 0, "low": 0}
            not_recommended_count = 0

            for i, finding in enumerate(findings):
                if not isinstance(finding, dict):
                    continue

                # Ensure ID
                if "id" not in finding:
                    finding["id"] = f"finding-{i+1:03d}"

                # Ensure confidence is valid
                confidence = finding.get("confidence", "medium").lower()
                if confidence not in ["high", "medium", "low"]:
                    confidence = "medium"
                finding["confidence"] = confidence
                confidence_counts[confidence] += 1

                # Track not-recommended
                if finding.get("is_not_recommended"):
                    not_recommended_count += 1

                # Ensure sources exist
                if not finding.get("sources"):
                    finding["sources"] = ["Based on industry patterns"]
                    finding["confidence"] = "low"  # Downgrade confidence if no sources

                # Ensure value_saved has defaults
                if not isinstance(finding.get("value_saved"), dict):
                    finding["value_saved"] = {
                        "hours_per_week": 0,
                        "hourly_rate": 50,
                        "annual_savings": 0
                    }
                else:
                    vs = finding["value_saved"]
                    finding["value_saved"] = {
                        "hours_per_week": vs.get("hours_per_week", 0) or 0,
                        "hourly_rate": vs.get("hourly_rate", 50) or 50,
                        "annual_savings": vs.get("annual_savings", 0) or 0
                    }

                # Ensure value_created has defaults
                if not isinstance(finding.get("value_created"), dict):
                    finding["value_created"] = {
                        "description": "",
                        "potential_revenue": 0
                    }
                else:
                    vc = finding["value_created"]
                    finding["value_created"] = {
                        "description": vc.get("description", "") or "",
                        "potential_revenue": vc.get("potential_revenue", 0) or 0
                    }

                validated_findings.append(finding)

            # Log confidence distribution
            total = len(validated_findings)
            if total > 0:
                logger.info(
                    f"Finding confidence distribution: "
                    f"HIGH={confidence_counts['high']}/{total} ({confidence_counts['high']*100//total}%), "
                    f"MEDIUM={confidence_counts['medium']}/{total} ({confidence_counts['medium']*100//total}%), "
                    f"LOW={confidence_counts['low']}/{total} ({confidence_counts['low']*100//total}%)"
                )
                logger.info(f"Not-recommended findings: {not_recommended_count}/{total}")

            return validated_findings[:max_findings]
        except Exception as e:
            logger.error(f"Failed to parse findings: {e}")
            return []

    async def _generate_recommendations(self, findings: List[Dict]) -> List[Dict[str, Any]]:
        """
        Generate recommendations using the ThreeOptionsSkill.

        Uses the skills framework for consistent Three Options output.
        Falls back to legacy method if skill fails.
        """
        # Try skill-based generation first
        skill = get_skill("three-options", client=self.client)

        if skill:
            try:
                # Filter out not-recommended findings
                recommendable = [f for f in findings if not f.get("is_not_recommended")]

                # Group by priority
                high_priority = [f for f in recommendable if f.get("customer_value_score", 0) >= 8 or f.get("business_health_score", 0) >= 8]
                other = [f for f in recommendable if f not in high_priority]

                # Top findings for recommendations
                priority_findings = high_priority[:5] + other[:5]

                recommendations = []
                roi_skill = get_skill("roi-calculator", client=self.client)
                vendor_skill = get_skill("vendor-matching", client=self.client)

                for i, finding in enumerate(priority_findings):
                    try:
                        context = self._get_skill_context()
                        context.metadata["finding"] = finding

                        result = await skill.run(context)

                        if result.success:
                            rec = result.data
                            rec["id"] = f"rec-{i+1:03d}"

                            # Enrich with specific vendor matches
                            if vendor_skill:
                                try:
                                    vendor_context = self._get_skill_context()
                                    vendor_context.metadata["finding"] = finding
                                    vendor_context.metadata["company_context"] = self.context.get("company_profile", {})

                                    vendor_result = await vendor_skill.run(vendor_context)

                                    if vendor_result.success:
                                        vendor_data = vendor_result.data
                                        # Enhance options with specific vendor info
                                        if vendor_data.get("off_the_shelf") and rec.get("options", {}).get("off_the_shelf"):
                                            rec["options"]["off_the_shelf"]["matched_vendor"] = vendor_data["off_the_shelf"]
                                        if vendor_data.get("best_in_class") and rec.get("options", {}).get("best_in_class"):
                                            rec["options"]["best_in_class"]["matched_vendor"] = vendor_data["best_in_class"]
                                        rec["vendor_match"] = {
                                            "category": vendor_data.get("category"),
                                            "confidence": vendor_data.get("match_confidence"),
                                            "alternatives": vendor_data.get("alternatives", []),
                                        }
                                except Exception as vendor_e:
                                    logger.debug(f"Vendor matching skipped for {finding.get('id')}: {vendor_e}")

                            # Enrich with detailed ROI analysis
                            if roi_skill:
                                try:
                                    roi_context = self._get_skill_context()
                                    roi_context.metadata["finding"] = finding
                                    roi_context.metadata["recommendation"] = rec
                                    roi_context.metadata["company_context"] = self.context.get("company_profile", {})

                                    roi_result = await roi_skill.run(roi_context)

                                    if roi_result.success:
                                        # Add detailed ROI data
                                        rec["roi_detail"] = {
                                            "sensitivity": roi_result.data.get("sensitivity", {}),
                                            "assumptions": roi_result.data.get("assumptions", []),
                                            "calculation_breakdown": roi_result.data.get("calculation_breakdown", ""),
                                            "time_savings": roi_result.data.get("time_savings", {}),
                                            "financial_impact": roi_result.data.get("financial_impact", {}),
                                        }
                                        # Update main ROI if calculated
                                        if roi_result.data.get("roi_percentage"):
                                            rec["roi_percentage"] = roi_result.data["roi_percentage"]
                                            rec["roi_confidence_adjusted"] = roi_result.data.get("roi_confidence_adjusted")
                                            rec["payback_months"] = roi_result.data.get("payback_months")
                                except Exception as roi_e:
                                    logger.debug(f"ROI calculation skipped for {finding.get('id')}: {roi_e}")

                            # Cap unrealistic ROI values (max 500%)
                            roi = rec.get("roi_percentage", 0)
                            if roi > 500:
                                logger.info(f"Capping ROI from {roi}% to 500% for {rec.get('title')}")
                                rec["roi_percentage"] = 500
                                rec["roi_capped"] = True
                                assumptions = rec.get("assumptions", [])
                                assumptions.append(f"ROI capped at 500% (original estimate: {roi}%)")
                                rec["assumptions"] = assumptions

                            # Enrich with four-options personalized recommendations
                            four_options_skill = get_skill("four-options", client=self.client)
                            if four_options_skill and context.user_profile:
                                try:
                                    four_context = self._get_skill_context()
                                    four_context.finding = finding
                                    four_context.vendors = self.context.get("vendors", [])[:10]

                                    four_result = await four_options_skill.run(four_context)

                                    if four_result.success:
                                        rec["four_options"] = four_result.data
                                        logger.debug(f"Four-options generated for {finding.get('id')}")
                                except Exception as four_e:
                                    logger.debug(f"Four-options skipped for {finding.get('id')}: {four_e}")

                            recommendations.append(rec)
                        else:
                            logger.warning(f"ThreeOptionsSkill failed for finding {finding.get('id')}: {result.warnings}")
                    except Exception as e:
                        logger.warning(f"Skill failed for finding {finding.get('id')}: {e}")

                if recommendations:
                    logger.info(
                        f"Recommendations generated via skill "
                        f"(count={len(recommendations)}, "
                        f"with_vendor_match={sum(1 for r in recommendations if 'vendor_match' in r)}, "
                        f"with_roi_detail={sum(1 for r in recommendations if 'roi_detail' in r)})"
                    )
                    return recommendations

            except Exception as e:
                logger.warning(f"Skill execution failed, using legacy: {e}")

        # Fall back to legacy method
        return await self._generate_recommendations_legacy(findings)

    async def _generate_recommendations_legacy(self, findings: List[Dict]) -> List[Dict[str, Any]]:
        """Generate recommendations using Claude (legacy method)."""
        vendors = self.context.get("vendors", [])

        # Group findings by priority
        high_priority = [f for f in findings if f.get("customer_value_score", 0) >= 8 or f.get("business_health_score", 0) >= 8]
        other = [f for f in findings if f not in high_priority]

        priority_findings = high_priority[:5] + other[:5]  # Top 10 for recommendations

        # Get AI tools context for custom solution recommendations
        ai_tools_context = get_ai_tools_prompt_context()

        prompt = f"""Based on these findings, generate detailed recommendations with the THREE OPTIONS pattern.

TOP FINDINGS:
{json.dumps(priority_findings, indent=2)}

AVAILABLE VENDORS FOR THIS INDUSTRY:
{json.dumps(vendors[:15], indent=2) if vendors else "Use general market vendors"}

{ai_tools_context}

═══════════════════════════════════════════════════════════════════════════════
THREE OPTIONS PATTERN (REQUIRED)
═══════════════════════════════════════════════════════════════════════════════

For EACH recommendation, provide ALL THREE options:

Option A: OFF-THE-SHELF - Existing SaaS, plug and play, fastest to implement
Option B: BEST-IN-CLASS - Premium vendor solution, more features, better support
Option C: CUSTOM SOLUTION - Built with AI/APIs, perfect fit, competitive advantage

The custom_solution MUST include:
- Specific AI model recommendation (from the AI TOOL RECOMMENDATIONS above)
- build_tools list (e.g., ["Claude API", "Cursor", "Vercel", "Supabase"])
- skills_required list
- dev_hours_estimate range (e.g., "40-80 hours")
- model_recommendation with reasoning

═══════════════════════════════════════════════════════════════════════════════

For each recommendation, use this EXACT structure:
{{
    "id": "rec-001",
    "finding_id": "<id of related finding>",
    "title": "<recommendation title>",
    "description": "<what to do and why>",
    "why_it_matters": {{
        "customer_value": "<specific benefit to their customers>",
        "business_health": "<specific benefit to the business>"
    }},
    "priority": "high|medium|low",
    "crb_analysis": {{
        "cost": {{
            "short_term": {{ "software": <number>, "implementation": <number>, "training": <number> }},
            "mid_term": {{ "software": <number>, "maintenance": <number> }},
            "long_term": {{ "software": <number>, "upgrades": <number> }},
            "total": <sum of all costs>
        }},
        "risk": [
            {{
                "description": "<what could go wrong>",
                "probability": "low|medium|high",
                "impact": <cost if risk occurs>,
                "mitigation": "<how to reduce/avoid>",
                "time_horizon": "short|mid|long"
            }}
        ],
        "benefit": {{
            "short_term": {{ "value_saved": <number>, "value_created": <number> }},
            "mid_term": {{ "value_saved": <number>, "value_created": <number> }},
            "long_term": {{ "value_saved": <number>, "value_created": <number> }},
            "total": <sum of all benefits>
        }}
    }},
    "options": {{
        "off_the_shelf": {{
            "name": "<specific product name>",
            "vendor": "<company name>",
            "monthly_cost": <number in EUR>,
            "implementation_weeks": <number>,
            "implementation_cost": <one-time setup cost>,
            "pros": ["<pro1>", "<pro2>", "<pro3>"],
            "cons": ["<con1>", "<con2>"]
        }},
        "best_in_class": {{
            "name": "<specific product name>",
            "vendor": "<company name>",
            "monthly_cost": <number in EUR>,
            "implementation_weeks": <number>,
            "implementation_cost": <one-time setup cost>,
            "pros": ["<pro1>", "<pro2>", "<pro3>"],
            "cons": ["<con1>", "<con2>"]
        }},
        "custom_solution": {{
            "approach": "<description of custom solution approach>",
            "estimated_cost": {{ "min": <number>, "max": <number> }},
            "monthly_running_cost": <ongoing API/hosting costs>,
            "implementation_weeks": <number>,
            "pros": ["Perfect fit for your needs", "Competitive advantage", "Full control"],
            "cons": ["Higher upfront investment", "Requires maintenance"],
            "build_tools": ["<AI model>", "Cursor", "Vercel", "Supabase"],
            "model_recommendation": "<Specific model> because <reason>",
            "skills_required": ["<skill1>", "<skill2>"],
            "dev_hours_estimate": "<min>-<max> hours"
        }}
    }},
    "our_recommendation": "off_the_shelf|best_in_class|custom_solution",
    "recommendation_rationale": "<detailed explanation of why this option is best for THIS business based on their size, budget, tech comfort, and goals>",
    "roi_percentage": <calculated ROI>,
    "payback_months": <months until investment recovered>,
    "assumptions": [
        "<assumption 1 with specific numbers>",
        "<assumption 2 with specific numbers>",
        "<assumption 3>"
    ]
}}

CRITICAL REQUIREMENTS:
1. ALL THREE OPTIONS must be complete with real vendor names and pricing
2. CUSTOM SOLUTION must always include build_tools, model_recommendation, skills_required, dev_hours_estimate
3. ROI calculations must be transparent - show your math in assumptions
4. Recommendation rationale must be specific to THIS business context
5. Use real vendor names and current pricing (approximate if needed)

Generate 5-10 recommendations. Return ONLY the JSON array."""

        try:
            content = self._call_claude("generate_recommendations", prompt, max_tokens=12000)
            recommendations = safe_parse_json(content, [])

            if not isinstance(recommendations, list):
                logger.error(f"Recommendations is not a list: {type(recommendations)}")
                return []

            # Validate and enrich each recommendation
            validated_recommendations = []
            for i, rec in enumerate(recommendations):
                if not isinstance(rec, dict):
                    continue

                # Ensure ID
                if "id" not in rec:
                    rec["id"] = f"rec-{i+1:03d}"

                # Validate three options exist
                options = rec.get("options", {})
                if not all(k in options for k in ["off_the_shelf", "best_in_class", "custom_solution"]):
                    logger.warning(f"Recommendation {rec.get('id')} missing options, skipping")
                    continue

                # Ensure custom solution has required fields
                custom = options.get("custom_solution", {})
                if not custom.get("build_tools"):
                    custom["build_tools"] = ["Claude API", "Cursor", "Vercel", "Supabase"]
                if not custom.get("model_recommendation"):
                    custom["model_recommendation"] = "Claude Sonnet 4 for balanced quality and cost"
                if not custom.get("skills_required"):
                    custom["skills_required"] = ["Python or TypeScript", "Basic API integration"]
                if not custom.get("dev_hours_estimate"):
                    custom["dev_hours_estimate"] = "40-80 hours"

                # Enrich custom solution with Build It Yourself details
                custom = self._enrich_build_it_yourself(rec["title"], custom)
                options["custom_solution"] = custom

                # Cap unrealistic ROI values (max 500%)
                roi = rec.get("roi_percentage", 0)
                if roi > 500:
                    logger.info(f"Capping ROI from {roi}% to 500% for {rec.get('title')}")
                    rec["roi_percentage"] = 500
                    rec["roi_capped"] = True
                    assumptions = rec.get("assumptions", [])
                    assumptions.append(f"ROI capped at 500% (original estimate: {roi}%)")
                    rec["assumptions"] = assumptions

                validated_recommendations.append(rec)

            return validated_recommendations
        except Exception as e:
            logger.error(f"Failed to parse recommendations: {e}")
            return []

    def _enrich_build_it_yourself(self, recommendation_title: str, custom: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich custom solution with detailed Build It Yourself guidance.

        Adds recommended stack, resources, and implementation details.
        """
        # Determine use case from recommendation title
        title_lower = recommendation_title.lower()
        use_case = "automation"  # default

        if any(kw in title_lower for kw in ["chat", "support", "customer service", "bot"]):
            use_case = "chatbot"
        elif any(kw in title_lower for kw in ["document", "pdf", "contract", "invoice"]):
            use_case = "document_processing"
        elif any(kw in title_lower for kw in ["content", "write", "copy", "blog", "social"]):
            use_case = "content_generation"
        elif any(kw in title_lower for kw in ["email", "communication", "outreach"]):
            use_case = "email_assistant"
        elif any(kw in title_lower for kw in ["data", "analysis", "report", "dashboard"]):
            use_case = "data_analysis"
        elif any(kw in title_lower for kw in ["voice", "transcri", "meeting", "call"]):
            use_case = "voice_transcription"

        # Get context from ai_tools config
        biy_context = get_build_it_yourself_context(use_case)

        # Enrich the custom solution
        custom["use_case"] = use_case

        # Add recommended stack if not present
        if not custom.get("recommended_stack"):
            custom["recommended_stack"] = biy_context["recommended_stack"]

        # Add key APIs with pricing
        if not custom.get("key_apis"):
            ai_model = biy_context["ai_model"]
            custom["key_apis"] = [
                {
                    "name": ai_model["name"],
                    "purpose": "Core AI processing",
                    "pricing": ai_model.get("pricing", {}),
                    "docs": "https://docs.anthropic.com"
                },
                {
                    "name": "Supabase",
                    "purpose": "Database + Auth",
                    "pricing": {"free_tier": True, "pro": "$25/month"},
                    "docs": "https://supabase.com/docs"
                },
                {
                    "name": "Vercel",
                    "purpose": "Frontend hosting",
                    "pricing": {"free_tier": True, "pro": "$20/month"},
                    "docs": "https://vercel.com/docs"
                }
            ]

        # Add resources
        if not custom.get("resources"):
            custom["resources"] = {
                "documentation": [
                    "https://docs.anthropic.com - Claude API documentation",
                    "https://github.com/anthropics/anthropic-cookbook - Code examples",
                    "https://cursor.com/docs - Cursor IDE setup"
                ],
                "tutorials": [
                    f"Build a {use_case.replace('_', ' ')} with Claude - anthropic.com/cookbook",
                    "Deploying AI apps to Vercel - vercel.com/guides"
                ],
                "communities": [
                    "Anthropic Discord - discord.gg/anthropic",
                    "r/ClaudeAI - reddit.com/r/ClaudeAI"
                ]
            }

        # Add timeline estimates
        if not custom.get("timeline"):
            custom["timeline"] = biy_context["typical_timeline"]

        # Add implementation steps
        if not custom.get("implementation_steps"):
            custom["implementation_steps"] = [
                "1. Set up development environment (Cursor + Claude API key)",
                "2. Create project scaffolding (Next.js/FastAPI template)",
                "3. Implement core AI integration with Claude API",
                "4. Build user interface for interaction",
                "5. Add authentication with Supabase",
                "6. Deploy to Vercel (frontend) and Railway (backend)",
                "7. Test with real users and iterate"
            ]

        return custom

    async def _generate_roadmap(self, recommendations: List[Dict]) -> Dict[str, Any]:
        """Generate implementation roadmap from recommendations."""
        prompt = f"""Based on these recommendations, create an implementation roadmap.

RECOMMENDATIONS:
{json.dumps(recommendations[:10], indent=2)}

Generate a JSON roadmap with this structure:
{{
    "short_term": [
        {{
            "title": "<action item>",
            "description": "<details>",
            "timeline": "Week 1-4",
            "expected_outcome": "<what success looks like>",
            "related_recommendation_id": "<id>"
        }}
    ],
    "mid_term": [
        {{
            "title": "<action item>",
            "description": "<details>",
            "timeline": "Month 3-6",
            "expected_outcome": "<what success looks like>",
            "related_recommendation_id": "<id>"
        }}
    ],
    "long_term": [
        {{
            "title": "<action item>",
            "description": "<details>",
            "timeline": "Month 12-18",
            "expected_outcome": "<what success looks like>",
            "related_recommendation_id": "<id>"
        }}
    ]
}}

Put quick wins first. Be specific and actionable.
Return ONLY the JSON."""

        try:
            content = self._call_claude("generate_roadmap", prompt, max_tokens=3000)
            roadmap = safe_parse_json(content, {"short_term": [], "mid_term": [], "long_term": []})
            if not isinstance(roadmap, dict):
                return {"short_term": [], "mid_term": [], "long_term": []}
            return roadmap
        except Exception as e:
            logger.error(f"Failed to parse roadmap: {e}")
            return {"short_term": [], "mid_term": [], "long_term": []}

    def _calculate_value_summary(self, findings: List[Dict], recommendations: List[Dict]) -> Dict[str, Any]:
        """Calculate total value summary from findings and recommendations.

        Applies confidence-adjusted ROI (ROI-CA):
        - HIGH confidence: 100% of estimated value
        - MEDIUM confidence: 85% of estimated value
        - LOW confidence: 70% of estimated value
        """
        logger.info(f"[VALUE_CALC] Starting value_summary calculation with {len(findings)} findings and {len(recommendations)} recommendations")

        # Calculate confidence-adjusted hours saved
        total_hours_saved_raw = 0
        total_hours_saved_adjusted = 0
        for f in findings:
            hours = f.get("value_saved", {}).get("hours_per_week", 0) or 0
            if hours > 0:
                logger.info(f"[VALUE_CALC] Finding '{f.get('title', 'N/A')}' has {hours} hours/week saved")
            confidence = f.get("confidence", "medium").lower()
            factor = CONFIDENCE_FACTORS.get(confidence, 0.85)
            total_hours_saved_raw += hours
            total_hours_saved_adjusted += hours * factor

        hourly_rate = 50  # Default hourly rate
        time_savings_raw = total_hours_saved_raw * hourly_rate * 52  # Annual
        time_savings_adjusted = total_hours_saved_adjusted * hourly_rate * 52

        # Calculate confidence-adjusted value created from findings
        value_created_raw = 0
        value_created_adjusted = 0
        for f in findings:
            revenue = f.get("value_created", {}).get("potential_revenue", 0) or 0
            confidence = f.get("confidence", "medium").lower()
            factor = CONFIDENCE_FACTORS.get(confidence, 0.85)
            value_created_raw += revenue
            value_created_adjusted += revenue * factor

        # Calculate from recommendations
        # Note: Recommendations have roi_percentage and option costs, not crb_analysis.benefit.total
        # We derive benefit from: (investment * roi_percentage / 100) over 1 year
        total_benefit_from_recs = 0
        for rec in recommendations:
            # First try the legacy crb_analysis.benefit.total
            legacy_benefit = rec.get("crb_analysis", {}).get("benefit", {}).get("total", 0) or 0
            if legacy_benefit > 0:
                total_benefit_from_recs += legacy_benefit
                continue

            # Calculate from ROI and costs
            roi_pct = rec.get("roi_percentage", 0) or 0
            if roi_pct <= 0:
                continue

            # Get the recommended option's costs
            our_rec = rec.get("our_recommendation", "off_the_shelf")
            options = rec.get("options", {})
            chosen_option = options.get(our_rec, {})

            if our_rec == "custom_solution":
                # Custom solution: use estimated_cost range
                cost_range = chosen_option.get("estimated_cost", {})
                implementation_cost = (cost_range.get("min", 0) + cost_range.get("max", 0)) / 2
                monthly_cost = chosen_option.get("monthly_running_cost", 0) or 0
            else:
                implementation_cost = chosen_option.get("implementation_cost", 0) or 0
                monthly_cost = chosen_option.get("monthly_cost", 0) or 0

            # Total first year investment
            annual_cost = implementation_cost + (monthly_cost * 12)

            # Benefit = cost * roi_percentage / 100
            if annual_cost > 0:
                benefit = annual_cost * roi_pct / 100
                total_benefit_from_recs += benefit
                logger.info(f"[VALUE_CALC] Rec '{rec.get('title', 'N/A')}': cost={annual_cost}, ROI={roi_pct}%, benefit={benefit}")

        logger.info(f"[VALUE_CALC] Total benefit from recommendations: {total_benefit_from_recs}")

        # Apply average confidence factor to recommendations
        avg_confidence_factor = 0.85  # Default to medium
        if findings:
            confidence_factors_sum = sum(
                CONFIDENCE_FACTORS.get(f.get("confidence", "medium").lower(), 0.85)
                for f in findings
            )
            avg_confidence_factor = confidence_factors_sum / len(findings)
        total_benefit_adjusted = total_benefit_from_recs * avg_confidence_factor

        # Apply uncertainty ranges (±20%) on adjusted values
        time_savings_min = int(time_savings_adjusted * 0.8)
        time_savings_max = int(time_savings_adjusted * 1.2)

        value_created_total = value_created_adjusted + total_benefit_adjusted
        value_created_min = int(value_created_total * 0.7)
        value_created_max = int(value_created_total * 1.3)

        total_min = time_savings_min + value_created_min
        total_max = time_savings_max + value_created_max

        logger.info(f"[VALUE_CALC] Summary: hours_saved={total_hours_saved_adjusted}/week, time_savings={time_savings_adjusted}/year")
        logger.info(f"[VALUE_CALC] Summary: value_created_findings={value_created_adjusted}, value_created_recs={total_benefit_adjusted}")
        logger.info(f"[VALUE_CALC] Summary: TOTAL VALUE = {total_min} - {total_max}")

        return {
            "value_saved": {
                "hours_per_week": round(total_hours_saved_adjusted, 1),
                "hours_per_week_raw": total_hours_saved_raw,
                "hourly_rate": hourly_rate,
                "time_savings_annual": int(time_savings_adjusted),
                "time_savings_annual_raw": int(time_savings_raw),
                "subtotal": {"min": time_savings_min, "max": time_savings_max},
            },
            "value_created": {
                "from_findings": int(value_created_adjusted),
                "from_findings_raw": int(value_created_raw),
                "from_recommendations": int(total_benefit_adjusted),
                "from_recommendations_raw": int(total_benefit_from_recs),
                "subtotal": {"min": value_created_min, "max": value_created_max},
            },
            "total": {
                "min": total_min,
                "max": total_max,
            },
            "projection_years": 3,
            "confidence_adjustment_applied": True,
            "confidence_note": "Values are confidence-adjusted: HIGH=100%, MEDIUM=85%, LOW=70%",
        }

    def _generate_methodology_notes(self) -> Dict[str, Any]:
        """Generate methodology notes and disclaimers."""
        return {
            "data_sources": [
                "Quiz responses provided by business owner",
                "Industry benchmarks from our knowledge base",
                "Vendor pricing data (verified where possible)",
                "AI/automation adoption studies",
            ],
            "assumptions": [
                f"Hourly rate assumed at €50 unless specified",
                "3-year projection period for ROI calculations",
                "All estimates include ±20% uncertainty range",
                "Vendor pricing as of report generation date",
            ],
            "limitations": [
                "Estimates based on self-reported data",
                "Actual implementation results may vary",
                "Market conditions may affect vendor availability/pricing",
                "Recommendations should be validated with actual business data",
            ],
            "industry_benchmarks_used": list(self.context.get("benchmarks", {}).keys())[:5],
            "confidence_notes": "Findings marked as 'high' confidence have multiple supporting data points. "
                               "'Medium' confidence items are based on industry patterns. "
                               "'Low' confidence items are estimates requiring validation.",
            "confidence_adjusted_roi": {
                "explanation": "ROI estimates are confidence-adjusted to reflect uncertainty",
                "factors": {
                    "high": "100% of estimated value",
                    "medium": "85% of estimated value",
                    "low": "70% of estimated value"
                },
                "rationale": "This adjustment provides more realistic projections by weighting estimates "
                            "based on the strength of supporting evidence."
            },
        }

    # Industry-specific verdict adjustments
    INDUSTRY_VERDICT_ADJUSTMENTS = {
        "marketing-agencies": {
            "ai_readiness_boost": 5,  # Already using AI tools like Canva, ChatGPT
            "risk_tolerance": "medium",
            "quick_win_emphasis": True,
            "context_note": "Marketing agencies typically have higher AI familiarity"
        },
        "tech-companies": {
            "ai_readiness_boost": 10,  # High baseline tech literacy
            "risk_tolerance": "high",
            "quick_win_emphasis": False,  # Can handle complex implementations
            "context_note": "Tech companies can implement more sophisticated solutions"
        },
        "ecommerce": {
            "ai_readiness_boost": 3,
            "risk_tolerance": "medium",
            "quick_win_emphasis": True,
            "context_note": "E-commerce benefits from customer service and personalization AI"
        },
        "retail": {
            "ai_readiness_boost": 0,
            "risk_tolerance": "low",  # More conservative
            "quick_win_emphasis": True,
            "context_note": "Retail should focus on proven AI tools first"
        },
        "music-studios": {
            "ai_readiness_boost": 2,
            "risk_tolerance": "medium",
            "quick_win_emphasis": True,
            "context_note": "Creative industries benefit from AI augmentation, not replacement"
        },
        "general": {
            "ai_readiness_boost": 0,
            "risk_tolerance": "medium",
            "quick_win_emphasis": True,
            "context_note": "Start with quick wins to build confidence"
        }
    }

    async def _generate_verdict(
        self,
        executive_summary: Dict[str, Any],
        findings: List[Dict],
        recommendations: List[Dict],
        value_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate verdict using the VerdictSkill.

        Uses the skills framework for consistent Go/Caution/Wait/No verdicts.
        Falls back to legacy method if skill fails.
        """
        # Try skill-based generation first
        skill = get_skill("verdict", client=self.client)

        if skill:
            try:
                context = self._get_skill_context()
                # Provide report data for verdict generation
                context.report_data = {
                    "executive_summary": executive_summary,
                    "findings": findings,
                    "recommendations": recommendations,
                    "value_summary": value_summary,
                }

                result = await skill.run(context)

                if result.success:
                    logger.info(
                        f"Verdict generated via skill "
                        f"(recommendation={result.data.get('recommendation')}, "
                        f"execution_time={result.execution_time_ms:.0f}ms)"
                    )
                    return result.data
                else:
                    logger.warning(
                        f"VerdictSkill failed, using legacy method: "
                        f"{result.warnings}"
                    )
            except Exception as e:
                logger.warning(f"Skill execution failed, using legacy: {e}")

        # Fall back to legacy method
        return self._generate_verdict_legacy(executive_summary, findings, recommendations, value_summary)

    def _generate_verdict_legacy(
        self,
        executive_summary: Dict[str, Any],
        findings: List[Dict],
        recommendations: List[Dict],
        value_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate verdict using rule-based logic (legacy method).

        This is the 'brutally honest consultant' logic - we tell people the truth,
        including when AI is NOT the answer for them right now.
        """
        # Get industry adjustments
        industry = self.context.get("industry", "general")
        adjustments = self.INDUSTRY_VERDICT_ADJUSTMENTS.get(
            industry,
            self.INDUSTRY_VERDICT_ADJUSTMENTS["general"]
        )

        # Base scores
        raw_ai_score = executive_summary.get("ai_readiness_score", 0)
        cv_score = executive_summary.get("customer_value_score", 0)
        bh_score = executive_summary.get("business_health_score", 0)

        # Apply industry adjustment to AI score
        ai_score = raw_ai_score + adjustments["ai_readiness_boost"]
        ai_score = min(100, max(0, ai_score))  # Clamp to 0-100

        # Calculate confidence-weighted ROI (ROI-CA)
        # Apply average confidence factor from findings to ROI estimates
        avg_confidence_factor = 0.85  # Default to medium
        if findings:
            confidence_factors_sum = sum(
                CONFIDENCE_FACTORS.get(f.get("confidence", "medium").lower(), 0.85)
                for f in findings
            )
            avg_confidence_factor = confidence_factors_sum / len(findings)

        avg_roi_raw = 0
        avg_roi = 0  # Confidence-adjusted ROI
        if recommendations:
            roi_values = [r.get("roi_percentage", 0) or 0 for r in recommendations]
            avg_roi_raw = sum(roi_values) / len(roi_values) if roi_values else 0
            avg_roi = avg_roi_raw * avg_confidence_factor

        # Count high-risk recommendations
        high_risk_count = 0
        for rec in recommendations:
            risks = rec.get("crb_analysis", {}).get("risk", [])
            for risk in risks:
                if risk.get("probability") == "high":
                    high_risk_count += 1

        # Adjust risk threshold based on industry tolerance
        risk_thresholds = {"low": 2, "medium": 3, "high": 5}
        risk_threshold = risk_thresholds.get(adjustments["risk_tolerance"], 3)

        # Total value potential
        total_value_min = value_summary.get("total", {}).get("min", 0)
        total_value_max = value_summary.get("total", {}).get("max", 0)

        # Investment required (rough estimate from recommendations)
        total_cost = sum(
            rec.get("crb_analysis", {}).get("cost", {}).get("total", 0) or 0
            for rec in recommendations
        )

        # Log adjustments for debugging
        logger.info(
            f"Verdict calculation for {industry}: "
            f"raw_score={raw_ai_score}, adjusted_score={ai_score}, "
            f"boost={adjustments['ai_readiness_boost']}, "
            f"risk_tolerance={adjustments['risk_tolerance']}, "
            f"ROI_raw={avg_roi_raw:.0f}%, ROI_adjusted={avg_roi:.0f}% (factor={avg_confidence_factor:.2f})"
        )

        # Decision tree for verdict
        # NOT RECOMMENDED: Low scores, negative ROI, or human element is key
        if ai_score < 35 or (cv_score < 5 and bh_score < 5):
            return {
                "recommendation": "not_recommended",
                "headline": "AI is Not the Right Move Right Now",
                "subheadline": "Focus on fundamentals first",
                "reasoning": [
                    "Your current processes need standardization before AI can help",
                    "The potential ROI doesn't justify the investment at this stage",
                    "Basic automation would deliver better value than AI right now",
                    "Your competitive advantage likely comes from human expertise - protect it"
                ],
                "when_to_revisit": "Revisit AI in 12-18 months after standardizing core processes and building clean data foundations",
                "what_to_do_instead": [
                    "Document and standardize your current workflows",
                    "Implement basic automation tools (Zapier, simple scripts)",
                    "Build a data collection habit - structured, consistent data",
                    "Train your team on existing tools you're underutilizing"
                ],
                "confidence": "high",
                "color": "gray"
            }

        # WAIT: Borderline scores, cost exceeds near-term value
        elif ai_score < 50 or (avg_roi < 100 and total_cost > total_value_min * 0.5):
            return {
                "recommendation": "wait",
                "headline": "Not Yet - But AI is in Your Future",
                "subheadline": "The timing isn't right, but keep watching",
                "reasoning": [
                    "The numbers work, but margins are thin for early-stage AI adoption",
                    "Your processes show potential but need more maturity",
                    f"Estimated ROI ({int(avg_roi)}%, confidence-adjusted) is below our 150% threshold for confident recommendation",
                    "Implementation risks outweigh benefits at current scale"
                ],
                "when_to_revisit": "Check back in 6-12 months, or when your monthly revenue exceeds €50K consistently",
                "what_to_do_instead": [
                    "Start collecting the data AI will need (usage patterns, outcomes)",
                    "Pilot one small AI tool in a non-critical area",
                    "Build internal AI literacy - your team needs to understand what's possible",
                    "Watch competitors - if they start pulling ahead with AI, accelerate"
                ],
                "confidence": "medium",
                "color": "orange"
            }

        # PROCEED WITH CAUTION: Good scores but risks flagged (uses industry risk threshold)
        elif ai_score < 70 or high_risk_count >= risk_threshold or (cv_score < 7 and bh_score < 7):
            return {
                "recommendation": "proceed_cautiously",
                "headline": "Proceed with Caution",
                "subheadline": "Opportunity exists, but manage the risks",
                "reasoning": [
                    f"AI readiness score of {ai_score} shows solid foundation",
                    f"Projected value of €{total_value_min:,}-€{total_value_max:,} justifies exploration",
                    f"However, we identified {high_risk_count} high-risk factors to manage",
                    adjustments["context_note"]
                ],
                "when_to_revisit": "Re-evaluate after your first AI pilot (3-6 months)",
                "recommended_approach": [
                    "Start with ONE high-ROI, low-risk recommendation",
                    "Set clear success metrics before starting",
                    "Budget for iteration - first attempt rarely perfect",
                    "Have a rollback plan for each implementation"
                ],
                "industry_context": adjustments["context_note"],
                "confidence": "medium",
                "color": "yellow"
            }

        # PROCEED: Strong scores, clear ROI, manageable risk
        else:
            # Adjust approach based on industry quick_win_emphasis
            if adjustments["quick_win_emphasis"]:
                approach = [
                    "Start with the top quick-win recommendation",
                    "Build momentum with early successes",
                    "Expand to more complex implementations after proving ROI",
                    "Document wins to build internal buy-in"
                ]
            else:
                approach = [
                    "Implement top 2-3 recommendations in parallel",
                    "Assign an internal AI champion to drive adoption",
                    "Measure ROI monthly and share wins with the team",
                    "Plan for Phase 2 expansions once initial implementations succeed"
                ]

            return {
                "recommendation": "proceed",
                "headline": "Go For It - AI Will Accelerate Your Business",
                "subheadline": "Strong fundamentals, clear opportunity",
                "reasoning": [
                    f"AI readiness score of {ai_score} puts you in the top tier",
                    f"Projected 3-year value of €{total_value_min:,}-€{total_value_max:,}",
                    f"Estimated ROI of {int(avg_roi)}% (confidence-adjusted) across recommendations",
                    adjustments["context_note"]
                ],
                "when_to_revisit": "Quarterly check-ins to measure progress and adjust",
                "recommended_approach": approach,
                "industry_context": adjustments["context_note"],
                "confidence": "high",
                "color": "green"
            }

    async def _generate_playbooks(self, recommendations: List[Dict]) -> List[Dict[str, Any]]:
        """Generate playbooks for top recommendations."""
        playbook_gen = PlaybookGenerator()
        playbooks = []

        # Generate playbook for top 3 recommendations
        for rec in recommendations[:3]:
            try:
                # Generate for the recommended option
                our_rec = rec.get("our_recommendation", "off_the_shelf")
                playbook = await playbook_gen.generate_playbook(
                    recommendation=rec,
                    option_type=our_rec,
                    quiz_answers=self.context.get("answers", {}),
                    industry_context=self.context.get("industry_knowledge", {}),
                )
                playbooks.append(playbook.model_dump(mode='json'))
            except Exception as e:
                logger.warning(f"Failed to generate playbook for {rec.get('id')}: {e}")

        return playbooks

    async def _validate_math(
        self,
        findings: List[Dict],
        recommendations: List[Dict],
    ) -> Dict[str, Any]:
        """
        Validate mathematical claims in findings and recommendations.

        Uses the MathValidatorSkill to check:
        - Internal consistency (formulas add up)
        - Bounds (realistic values)
        - Source attribution (traceable numbers)
        - Cross-reference against company data

        Returns validation results and adjusts confidence levels.
        """
        skill = get_skill("math-validator")

        if not skill:
            logger.warning("MathValidatorSkill not found, skipping validation")
            return {"validated": False, "reason": "skill_not_found"}

        validation_results = []
        issues_found = 0
        warnings_found = 0
        confidence_adjustments = {}

        # Build recommendation lookup
        rec_by_finding = {r.get("finding_id"): r for r in recommendations}

        for finding in findings:
            try:
                context = self._get_skill_context()
                context.metadata["finding"] = finding
                context.metadata["recommendation"] = rec_by_finding.get(finding.get("id"))

                result = await skill.run(context)

                if result.success:
                    validation = result.data
                    validation_results.append(validation)

                    # Track issues
                    issues_found += len(validation.get("issues", []))
                    warnings_found += len(validation.get("warnings", []))

                    # Track confidence adjustments
                    finding_id = finding.get("id")
                    original_confidence = finding.get("confidence", "medium").lower()
                    new_confidence = validation.get("overall_confidence", original_confidence)

                    if new_confidence != original_confidence:
                        confidence_adjustments[finding_id] = {
                            "original": original_confidence,
                            "adjusted": new_confidence,
                            "reason": self._summarize_validation_issues(validation),
                        }

                        # Update the finding's confidence in place
                        finding["confidence"] = new_confidence
                        finding["confidence_adjusted_by_validation"] = True
                        finding["validation_issues"] = validation.get("issues", [])
                        finding["validation_warnings"] = validation.get("warnings", [])

            except Exception as e:
                logger.warning(f"Math validation failed for finding {finding.get('id')}: {e}")

        # Also update recommendations with adjusted confidence
        for rec in recommendations:
            finding_id = rec.get("finding_id")
            if finding_id in confidence_adjustments:
                adj = confidence_adjustments[finding_id]
                # Adjust ROI based on new confidence
                if "roi_percentage" in rec and adj["adjusted"] != adj["original"]:
                    original_roi = rec.get("roi_percentage", 0)
                    factor = CONFIDENCE_FACTORS.get(adj["adjusted"], 0.85) / CONFIDENCE_FACTORS.get(adj["original"], 0.85)
                    rec["roi_percentage_original"] = original_roi
                    rec["roi_percentage"] = round(original_roi * factor, 1)
                    rec["roi_adjusted_reason"] = f"Math validation: {adj['reason']}"

        return {
            "validated": True,
            "findings_checked": len(findings),
            "issues_found": issues_found,
            "warnings_found": warnings_found,
            "confidence_adjustments": len(confidence_adjustments),
            "details": validation_results,
        }

    def _summarize_validation_issues(self, validation: Dict[str, Any]) -> str:
        """Summarize validation issues for display."""
        issues = validation.get("issues", [])
        warnings = validation.get("warnings", [])

        if issues:
            return f"{len(issues)} math error(s): {issues[0].get('field', 'unknown')}"
        elif warnings:
            return f"{len(warnings)} warning(s): {warnings[0].get('concern', 'check values')}"
        elif validation.get("unverified_numbers"):
            return f"{len(validation['unverified_numbers'])} unverified number(s)"
        return "validation complete"

    async def _identify_quick_wins(
        self,
        findings: List[Dict],
        recommendations: List[Dict],
    ) -> Dict[str, Any]:
        """
        Identify quick wins using the QuickWinIdentifierSkill.

        Quick wins are low-effort, high-impact opportunities
        that can be implemented quickly.
        """
        skill = get_skill("quick-win-identifier", client=self.client)

        if skill:
            try:
                context = self._get_skill_context()
                context.metadata["findings"] = findings
                context.metadata["recommendations"] = recommendations

                result = await skill.run(context)

                if result.success:
                    logger.info(
                        f"Quick wins identified: {len(result.data.get('quick_wins', []))} "
                        f"from {result.data.get('total_findings_analyzed', 0)} findings"
                    )
                    return result.data

            except Exception as e:
                logger.warning(f"QuickWinIdentifierSkill failed: {e}")

        # Fallback: simple quick win detection
        quick_wins = []
        for finding in findings[:3]:
            if finding.get("confidence", "").lower() == "high":
                quick_wins.append({
                    "finding_id": finding.get("id"),
                    "title": finding.get("title"),
                    "why_quick": "High confidence finding",
                    "implementation_hours": 20,
                    "estimated_roi": 100,
                    "risk_level": "low",
                })

        return {
            "quick_wins": quick_wins,
            "total_findings_analyzed": len(findings),
            "quick_wins_found": len(quick_wins),
        }

    def _generate_system_architecture(self, recommendations: List[Dict]) -> Dict[str, Any]:
        """Generate system architecture diagram data."""
        arch_gen = ArchitectureGenerator()
        architecture = arch_gen.generate_architecture(
            recommendations=recommendations,
            quiz_answers=self.context.get("answers", {}),
        )
        return architecture.model_dump()

    async def _generate_industry_insights(self) -> Dict[str, Any]:
        """Generate industry insights, benchmarks, and competitor analysis."""
        insights_gen = InsightsGenerator()
        exec_summary = self._partial_data.get("executive_summary", {})
        ai_score = exec_summary.get("ai_readiness_score", 50)

        # Base insights
        insights = insights_gen.generate_insights(
            industry=self.context.get("industry", "general"),
            ai_readiness_score=ai_score,
        )
        result = insights.model_dump()

        # Enrich with competitor analysis
        competitor_skill = get_skill("competitor-analyzer", client=self.client)
        if competitor_skill:
            try:
                context = self._get_skill_context()
                context.metadata["findings"] = self._partial_data.get("findings", [])

                competitor_result = await competitor_skill.run(context)

                if competitor_result.success:
                    result["competitor_analysis"] = competitor_result.data
                    logger.info(
                        f"Competitor analysis: {competitor_result.data.get('ai_adoption_rate')} "
                        f"adoption, risk={competitor_result.data.get('risk_assessment', {}).get('risk_level')}"
                    )

            except Exception as e:
                logger.debug(f"Competitor analysis skipped: {e}")

        # Enrich with industry benchmarking
        benchmarker_skill = get_skill("industry-benchmarker", client=self.client)
        if benchmarker_skill:
            try:
                context = self._get_skill_context()
                benchmarker_result = await benchmarker_skill.run(context)

                if benchmarker_result.success:
                    result["company_benchmarks"] = benchmarker_result.data
                    logger.info(
                        f"Benchmarks: AI readiness {benchmarker_result.data.get('ai_readiness', {}).get('score')}/100, "
                        f"percentile={benchmarker_result.data.get('ai_readiness', {}).get('percentile')}"
                    )

            except Exception as e:
                logger.debug(f"Industry benchmarking skipped: {e}")

        return result

    async def _generate_automation_summary(
        self,
        findings: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate automation summary (Connect vs Replace roadmap) from findings.

        Uses the AutomationSummarySkill to aggregate automation opportunities
        and build the "Your Automation Roadmap" section.

        Args:
            findings: List of findings with Connect/Replace paths

        Returns:
            AutomationSummary dict with stack assessment, opportunities, and next steps
        """
        try:
            # Get the skill
            automation_skill = get_skill("automation-summary")
            if not automation_skill:
                logger.warning("AutomationSummarySkill not found, returning empty summary")
                return {}

            # Build context with findings and existing stack
            context = self._get_skill_context()
            context.report_data = {"findings": findings}
            context.metadata["tier"] = self.tier

            # Execute the skill
            result = await automation_skill.run(context)

            if result.success:
                # Convert Pydantic model to dict for JSON storage
                summary_data = result.data
                if hasattr(summary_data, "model_dump"):
                    summary_dict = summary_data.model_dump()
                else:
                    summary_dict = dict(summary_data) if summary_data else {}

                logger.info(
                    f"Automation summary: {summary_dict.get('connect_count', 0)} Connect, "
                    f"{summary_dict.get('replace_count', 0)} Replace opportunities, "
                    f"total impact €{summary_dict.get('total_monthly_impact', 0)}/mo"
                )
                return summary_dict
            else:
                logger.warning(f"AutomationSummarySkill failed: {result.warnings}")
                return {}

        except Exception as e:
            logger.warning(f"Automation summary generation failed: {e}")
            return {}

    async def _generate_post_report_metadata(
        self,
        report: Dict[str, Any],
        quick_wins: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate post-report metadata (follow-up schedule, upsell analysis).

        Uses the followup-scheduler and upsell-identifier skills to determine
        optimal follow-up timing and identify upsell opportunities.
        """
        result = {
            "follow_up_schedule": {},
            "upsell_analysis": {},
        }

        # Get the customer tier from context
        customer_tier = self.tier  # "quick", "full", or "human"

        # Generate follow-up schedule
        followup_skill = get_skill("followup-scheduler", client=self.client)
        if followup_skill:
            try:
                context = self._get_skill_context()
                context.metadata["report"] = report
                context.metadata["quick_wins"] = quick_wins
                context.metadata["customer_tier"] = customer_tier
                context.metadata["company_name"] = self.context.get("company_name", "")

                followup_result = await followup_skill.run(context)

                if followup_result.success:
                    result["follow_up_schedule"] = followup_result.data
                    logger.info(
                        f"Follow-up schedule: {followup_result.data.get('recommended_touchpoints')} touchpoints, "
                        f"complexity={followup_result.data.get('complexity')}"
                    )

            except Exception as e:
                logger.debug(f"Follow-up scheduler skipped: {e}")
                # Provide minimal fallback
                result["follow_up_schedule"] = {
                    "follow_up_schedule": [
                        {"timing": "1 week", "type": "first_check", "channel": "email"},
                        {"timing": "2 weeks", "type": "progress_review", "channel": "email"},
                    ],
                    "recommended_touchpoints": 2,
                }

        # Identify upsell opportunities (only if not already on human tier)
        if customer_tier != "human":
            upsell_skill = get_skill("upsell-identifier", client=self.client)
            if upsell_skill:
                try:
                    context = self._get_skill_context()
                    context.metadata["report"] = report
                    context.metadata["current_tier"] = customer_tier
                    context.metadata["company_context"] = {
                        "name": self.context.get("company_name", ""),
                        "employee_count": self.context.get("answers", {}).get("employee_count", 0),
                    }

                    upsell_result = await upsell_skill.run(context)

                    if upsell_result.success:
                        result["upsell_analysis"] = upsell_result.data
                        if upsell_result.data.get("upsell_recommended"):
                            logger.info(
                                f"Upsell recommended: confidence={upsell_result.data.get('recommendation', {}).get('confidence')}, "
                                f"reason={upsell_result.data.get('recommendation', {}).get('reason')}"
                            )
                        else:
                            logger.info("No upsell recommended for this customer")

                except Exception as e:
                    logger.debug(f"Upsell identifier skipped: {e}")
                    result["upsell_analysis"] = {
                        "upsell_recommended": False,
                        "reason": "Analysis not available",
                    }
        else:
            result["upsell_analysis"] = {
                "upsell_recommended": False,
                "reason": "Customer already on human tier",
            }

        return result


async def generate_report_for_quiz(quiz_session_id: str, tier: str = "quick") -> str:
    """
    Generate a report for a quiz session.

    Returns the report ID.
    """
    generator = ReportGenerator(quiz_session_id, tier)

    report_id = None
    async for update in generator.generate_report():
        logger.info(f"Report generation: {update.get('step')} ({update.get('progress')}%)")
        if update.get("report_id"):
            report_id = update["report_id"]

    return report_id


async def generate_report_streaming(
    quiz_session_id: str,
    tier: str = "quick",
    model_strategy: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Generate a report with SSE streaming updates.

    Args:
        quiz_session_id: The quiz session ID
        tier: Report tier ("quick" or "full")
        model_strategy: Optional model strategy override for testing
            - "anthropic_quick": Claude Sonnet for generation
            - "anthropic_full": Claude Opus for all generation
            - "hybrid": Haiku → Sonnet → Opus pipeline
            - "gemini_primary": Gemini Flash/Pro
            - "cost_optimized": Flash → Sonnet → Opus
            - "multi_provider": Cross-provider validation
            - "budget": DeepSeek V3 primary

    Yields SSE-formatted events.
    """
    generator = ReportGenerator(quiz_session_id, tier, model_strategy=model_strategy)

    async for update in generator.generate_report():
        yield f"data: {json.dumps(update)}\n\n"


async def get_report(report_id: str) -> Optional[Dict[str, Any]]:
    """Get a report by ID."""
    supabase = await get_async_supabase()

    result = await supabase.table("reports").select("*").eq(
        "id", report_id
    ).single().execute()

    return result.data if result.data else None


async def get_report_by_quiz_session(quiz_session_id: str) -> Optional[Dict[str, Any]]:
    """Get a report by quiz session ID."""
    supabase = await get_async_supabase()

    result = await supabase.table("reports").select("*").eq(
        "quiz_session_id", quiz_session_id
    ).single().execute()

    return result.data if result.data else None
