"""
Pre-Research Agent

Researches a company before the questionnaire to:
1. Build a company profile from public sources
2. Generate tailored questions based on findings
"""

import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
from datetime import datetime
import uuid

from anthropic import Anthropic

from src.config.settings import settings
from src.config.supabase_client import get_async_supabase
from src.tools.research_scraper_tools import (
    RESEARCH_SCRAPER_TOOLS,
    execute_research_tool,
)
from src.models.research import (
    CompanyProfile,
    CompanyBasics,
    CompanySize,
    IndustryInfo,
    ProductsServices,
    TechStack,
    TeamLeadership,
    RecentActivity,
    ResearchedField,
    ConfidenceLevel,
    DynamicQuestion,
    DynamicQuestionnaire,
    QuestionPurpose,
)

logger = logging.getLogger(__name__)


class PreResearchAgent:
    """
    Pre-Research Agent

    Gathers public information about a company before asking questions.
    """

    SYSTEM_PROMPT = """You are a business research analyst. Your job is to gather comprehensive information about a company from public sources.

IMPORTANT GUIDELINES:
1. Use the provided tools to search and scrape information
2. Cross-reference multiple sources when possible
3. Note confidence levels for each finding
4. Don't make up information - only report what you find
5. Be thorough but efficient - gather key business information

Your goal is to build a complete company profile including:
- Basic info (name, description, founding year, headquarters)
- Size (employees, revenue estimates, funding)
- Industry and business model
- Products/services offered
- Technology stack (from job postings, website)
- Key people and team structure
- Recent news and activity

After research, you'll output a structured company profile."""

    def __init__(self, company_name: str, website_url: Optional[str] = None):
        self.company_name = company_name
        self.website_url = website_url
        self.research_id = str(uuid.uuid4())
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.gathered_data: Dict[str, Any] = {}

    async def run_research(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run company research and yield progress updates.
        """
        yield {
            "research_id": self.research_id,
            "status": "researching",
            "step": "Starting research...",
            "progress": 0,
        }

        try:
            # Phase 1: Gather data from multiple sources (with granular progress)
            profile_data = None
            async for update in self._run_research_phase_with_progress():
                if update.get("type") == "progress":
                    yield {
                        "status": "researching",
                        "step": update["step"],
                        "progress": update["progress"],
                    }
                elif update.get("type") == "result":
                    profile_data = update["data"]

            yield {
                "status": "researching",
                "step": "Processing research findings...",
                "progress": 65,
            }

            # Phase 2: Build structured profile
            company_profile = self._build_company_profile(profile_data or {})

            yield {
                "status": "generating_questions",
                "step": "Generating tailored questions...",
                "progress": 75,
            }

            # Phase 3: Generate tailored questionnaire
            questionnaire = await self._generate_questionnaire(company_profile)

            yield {
                "status": "ready",
                "step": "Research complete!",
                "progress": 100,
                "result": {
                    "company_profile": company_profile.model_dump(),
                    "questionnaire": questionnaire.model_dump(),
                },
            }

        except Exception as e:
            logger.error(f"Pre-research error: {e}")
            yield {
                "status": "failed",
                "step": f"Research failed: {str(e)}",
                "progress": 0,
                "error": str(e),
            }

    async def _run_research_phase_with_progress(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Run the research phase using Claude with tools, yielding progress updates."""

        # Tool name to user-friendly step mapping
        TOOL_STEP_NAMES = {
            "scrape_website": "Scanning website...",
            "web_search": "Searching the web...",
            "search_linkedin": "Searching LinkedIn...",
            "search_crunchbase": "Looking up company data...",
            "search_news": "Finding recent news...",
            "search_jobs": "Analyzing job postings...",
        }

        prompt = f"""Research the company: {self.company_name}
{f"Website: {self.website_url}" if self.website_url else ""}

Please gather comprehensive information using the available tools:

1. Start by scraping their website (if URL provided) or searching for it
2. Search for their LinkedIn company profile
3. Search for Crunchbase info (funding, investors)
4. Look for recent news
5. Search job postings to understand tech stack and growth areas

After gathering data, provide a structured summary of your findings in JSON format with these fields:
- basics: {{name, description, tagline, founded_year, headquarters}}
- size: {{employee_count, employee_range, revenue_estimate, funding_raised, funding_stage}}
- industry: {{primary_industry, sub_industry, business_model, target_market, competitors}}
- products: {{main_products, services, pricing_model, key_features}}
- tech_stack: {{technologies, platforms, infrastructure}}
- team: {{founders, executives, hiring_roles}}
- activity: {{recent_news, social_presence}}

For each field, also note your confidence level (high/medium/low) and source."""

        messages = [{"role": "user", "content": prompt}]

        # Run agent loop - progress from 10% to 60%
        max_iterations = 15
        iteration = 0
        base_progress = 10
        progress_per_iteration = 50 / max_iterations  # ~3.3% per iteration

        yield {"type": "progress", "step": "Starting company research...", "progress": base_progress}

        while iteration < max_iterations:
            iteration += 1
            current_progress = int(base_progress + (iteration * progress_per_iteration))

            try:
                response = self.client.messages.create(
                    model=settings.DEFAULT_MODEL,
                    max_tokens=4096,
                    system=self.SYSTEM_PROMPT,
                    tools=RESEARCH_SCRAPER_TOOLS,
                    messages=messages,
                )

                # Process response
                assistant_content = []
                tool_calls = []

                for block in response.content:
                    if block.type == "text":
                        assistant_content.append({"type": "text", "text": block.text})
                    elif block.type == "tool_use":
                        tool_calls.append(block)
                        assistant_content.append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        })

                messages.append({"role": "assistant", "content": assistant_content})

                # If no tool calls, extract final response
                if not tool_calls:
                    # Parse JSON from response
                    for block in response.content:
                        if block.type == "text":
                            result = self._extract_json_from_text(block.text)
                            yield {"type": "result", "data": result}
                            return
                    break

                # Execute tool calls
                tool_results = []
                for tool_call in tool_calls:
                    tool_name = tool_call.name
                    step_name = TOOL_STEP_NAMES.get(tool_name, f"Researching {tool_name}...")

                    yield {"type": "progress", "step": step_name, "progress": current_progress}

                    logger.info(f"Executing research tool: {tool_name}")

                    result = await execute_research_tool(
                        tool_name,
                        tool_call.input,
                    )

                    # Store gathered data
                    self.gathered_data[tool_name] = result

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": json.dumps(result, default=str),
                    })

                messages.append({"role": "user", "content": tool_results})

                if response.stop_reason == "end_turn":
                    break

            except Exception as e:
                logger.error(f"Research iteration error: {e}")
                break

        yield {"type": "result", "data": self.gathered_data}

    async def _run_research_phase(self) -> Dict[str, Any]:
        """Run the research phase using Claude with tools (non-streaming, for backwards compat)."""
        result = {}
        async for update in self._run_research_phase_with_progress():
            if update.get("type") == "result":
                result = update.get("data", {})
        return result

    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Extract JSON from Claude's response."""
        import re

        # Try to find JSON block
        json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find any JSON object
        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return {}

    def _build_company_profile(self, data: Dict[str, Any]) -> CompanyProfile:
        """Build a structured CompanyProfile from gathered data."""

        def make_field(value: Any, confidence: str = "medium", source: str = None) -> ResearchedField:
            conf_map = {
                "high": ConfidenceLevel.HIGH,
                "medium": ConfidenceLevel.MEDIUM,
                "low": ConfidenceLevel.LOW,
            }
            return ResearchedField(
                value=value,
                confidence=conf_map.get(confidence, ConfidenceLevel.MEDIUM),
                source=source,
            )

        def ensure_list(value: Any) -> list:
            """Ensure value is a list - handles LLM returning strings instead of arrays."""
            if value is None:
                return []
            if isinstance(value, list):
                return value
            if isinstance(value, str):
                # LLM returned a string instead of array - return empty
                return []
            return []

        # Extract from various data shapes
        basics_data = data.get("basics", {})
        size_data = data.get("size", {})
        industry_data = data.get("industry", {})
        products_data = data.get("products", {})
        tech_data = data.get("tech_stack", {})
        team_data = data.get("team", {})
        activity_data = data.get("activity", {})

        # Build profile
        profile = CompanyProfile(
            research_id=self.research_id,
            researched_at=datetime.utcnow(),
            sources_used=list(self.gathered_data.keys()),

            basics=CompanyBasics(
                name=make_field(self.company_name, "high"),
                website=self.website_url,
                description=make_field(basics_data.get("description")) if basics_data.get("description") else None,
                tagline=make_field(basics_data.get("tagline")) if basics_data.get("tagline") else None,
                founded_year=make_field(basics_data.get("founded_year")) if basics_data.get("founded_year") else None,
                headquarters=make_field(basics_data.get("headquarters")) if basics_data.get("headquarters") else None,
            ),

            size=CompanySize(
                employee_count=make_field(size_data.get("employee_count")) if size_data.get("employee_count") else None,
                employee_range=make_field(size_data.get("employee_range")) if size_data.get("employee_range") else None,
                revenue_estimate=make_field(size_data.get("revenue_estimate")) if size_data.get("revenue_estimate") else None,
                funding_raised=make_field(size_data.get("funding_raised")) if size_data.get("funding_raised") else None,
                funding_stage=make_field(size_data.get("funding_stage")) if size_data.get("funding_stage") else None,
            ) if size_data else None,

            industry=IndustryInfo(
                primary_industry=make_field(industry_data.get("primary_industry")) if industry_data.get("primary_industry") else None,
                sub_industry=make_field(industry_data.get("sub_industry")) if industry_data.get("sub_industry") else None,
                business_model=make_field(industry_data.get("business_model")) if industry_data.get("business_model") else None,
                target_market=make_field(industry_data.get("target_market")) if industry_data.get("target_market") else None,
            ) if industry_data else None,

            products=ProductsServices(
                main_products=[make_field(p) for p in ensure_list(products_data.get("main_products"))] or None,
                services=[make_field(s) for s in ensure_list(products_data.get("services"))] or None,
                pricing_model=make_field(products_data.get("pricing_model")) if products_data.get("pricing_model") else None,
                key_features=products_data.get("key_features"),
            ) if products_data else None,

            tech_stack=TechStack(
                technologies_detected=[make_field(t) for t in ensure_list(tech_data.get("technologies"))] or None,
                platforms_used=[make_field(p) for p in ensure_list(tech_data.get("platforms"))] or None,
            ) if tech_data else None,

            team=TeamLeadership(
                founders=[make_field(f) for f in ensure_list(team_data.get("founders"))] or None,
                key_executives=[make_field(e) for e in ensure_list(team_data.get("executives"))] or None,
                hiring_roles=team_data.get("hiring_roles"),
            ) if team_data else None,

            activity=RecentActivity(
                recent_news=[make_field(n) for n in ensure_list(activity_data.get("recent_news"))] or None,
                social_presence=activity_data.get("social_presence"),
            ) if activity_data else None,
        )

        # Calculate research quality score
        profile.research_quality_score = self._calculate_quality_score(profile)

        return profile

    def _calculate_quality_score(self, profile: CompanyProfile) -> int:
        """Calculate overall research quality score."""
        score = 0
        max_score = 100

        # Points for each section found
        if profile.basics.description:
            score += 15
        if profile.size and profile.size.employee_range:
            score += 15
        if profile.industry and profile.industry.primary_industry:
            score += 15
        if profile.products and profile.products.main_products:
            score += 15
        if profile.tech_stack and profile.tech_stack.technologies_detected:
            score += 10
        if profile.team and profile.team.founders:
            score += 10
        if profile.activity and profile.activity.recent_news:
            score += 10

        # Bonus for multiple sources
        if len(profile.sources_used) >= 3:
            score += 10

        return min(score, max_score)

    async def _generate_questionnaire(self, profile: CompanyProfile) -> DynamicQuestionnaire:
        """Generate a tailored questionnaire based on the company profile."""

        # Build context for question generation
        profile_summary = self._summarize_profile(profile)

        prompt = f"""Based on this company research, generate a SHORT qualifying questionnaire (3-5 questions MAX).

COMPANY PROFILE:
{profile_summary}

IMPORTANT: This is a FREE pre-qualification quiz. Generate only 3-5 essential questions that:
1. CONFIRM the most uncertain/important finding (1 question max)
2. DISCOVER their biggest pain point or challenge (1-2 questions)
3. UNDERSTAND their goals/timeline (1 question)
4. GAUGE their readiness/budget (1 question)

DO NOT ask about things we already know with high confidence.
DO NOT ask detailed operational questions - save those for the paid interview.

The goal is to:
- Qualify them as a good fit
- Understand their core need
- Give them a taste of personalized analysis

Output a JSON array of questions with this structure:
{{
  "questions": [
    {{
      "id": "unique_id",
      "question": "The question text",
      "type": "text|textarea|select|multi_select|scale|yes_no|number",
      "purpose": "confirm|clarify|discover|deep_dive",
      "rationale": "Why we're asking this",
      "prefilled_value": null or value,
      "required": true|false,
      "options": [for select/multi_select only],
      "section": "operations|technology|challenges|goals",
      "priority": 1-5
    }}
  ],
  "confirmed_facts": [
    {{"fact": "what we know", "confidence": "high|medium"}},
  ],
  "research_summary": "2-3 sentence summary of what we found"
}}

Generate 10-15 targeted questions. Focus on internal operations and pain points we can't find publicly."""

        try:
            response = self.client.messages.create(
                model=settings.DEFAULT_MODEL,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse response
            response_text = response.content[0].text
            questionnaire_data = self._extract_json_from_text(response_text)

            questions = [
                DynamicQuestion(
                    id=q.get("id", f"q_{i}"),
                    question=q.get("question", ""),
                    type=q.get("type", "text"),
                    purpose=QuestionPurpose(q.get("purpose", "discover")),
                    rationale=q.get("rationale", ""),
                    prefilled_value=q.get("prefilled_value"),
                    required=q.get("required", True),
                    options=q.get("options"),
                    section=q.get("section", "general"),
                    priority=q.get("priority", 3),
                )
                for i, q in enumerate(questionnaire_data.get("questions", []))
            ]

            # Sort by priority
            questions.sort(key=lambda x: x.priority)

            # Build sections
            sections = self._build_sections(questions)

            return DynamicQuestionnaire(
                company_name=self.company_name,
                research_summary=questionnaire_data.get("research_summary", f"We researched {self.company_name} and found public information about their business."),
                confirmed_facts=questionnaire_data.get("confirmed_facts", []),
                questions=questions,
                total_questions=len(questions),
                estimated_time_minutes=max(5, len(questions) * 1),  # ~1 min per question
                sections=sections,
            )

        except Exception as e:
            logger.error(f"Question generation error: {e}")
            # Return fallback questionnaire
            return self._generate_fallback_questionnaire(profile)

    def _summarize_profile(self, profile: CompanyProfile) -> str:
        """Create a text summary of the profile for the question generator."""
        lines = [f"Company: {self.company_name}"]

        if profile.basics.description:
            lines.append(f"Description: {profile.basics.description.value}")

        if profile.size:
            if profile.size.employee_range:
                lines.append(f"Size: {profile.size.employee_range.value} employees")
            if profile.size.funding_raised:
                lines.append(f"Funding: {profile.size.funding_raised.value}")

        if profile.industry:
            if profile.industry.primary_industry:
                lines.append(f"Industry: {profile.industry.primary_industry.value}")
            if profile.industry.business_model:
                lines.append(f"Business Model: {profile.industry.business_model.value}")

        if profile.products and profile.products.main_products:
            products = [p.value for p in profile.products.main_products[:3]]
            lines.append(f"Products: {', '.join(products)}")

        if profile.tech_stack and profile.tech_stack.technologies_detected:
            tech = [t.value for t in profile.tech_stack.technologies_detected[:5]]
            lines.append(f"Tech Stack: {', '.join(tech)}")

        lines.append(f"\nResearch Quality Score: {profile.research_quality_score}/100")
        lines.append(f"Sources Used: {', '.join(profile.sources_used)}")

        return "\n".join(lines)

    def _build_sections(self, questions: List[DynamicQuestion]) -> List[Dict[str, Any]]:
        """Group questions into sections."""
        section_map = {
            "operations": {"id": 1, "title": "Operations", "description": "How your business operates day-to-day"},
            "technology": {"id": 2, "title": "Technology", "description": "Your tools and tech stack"},
            "challenges": {"id": 3, "title": "Challenges", "description": "Pain points and bottlenecks"},
            "goals": {"id": 4, "title": "Goals", "description": "What you want to achieve"},
            "general": {"id": 5, "title": "General", "description": "Other information"},
        }

        sections = []
        for section_key, section_info in section_map.items():
            section_questions = [q.id for q in questions if q.section == section_key]
            if section_questions:
                sections.append({
                    **section_info,
                    "question_ids": section_questions,
                })

        return sections

    def _generate_fallback_questionnaire(self, profile: CompanyProfile) -> DynamicQuestionnaire:
        """Generate a fallback questionnaire if AI generation fails."""
        questions = [
            DynamicQuestion(
                id="main_processes",
                question="What are your main business processes that take the most time?",
                type="textarea",
                purpose=QuestionPurpose.DISCOVER,
                rationale="We need to understand your operations to identify automation opportunities.",
                section="operations",
                priority=1,
            ),
            DynamicQuestion(
                id="repetitive_tasks",
                question="What repetitive tasks does your team perform regularly?",
                type="textarea",
                purpose=QuestionPurpose.DISCOVER,
                rationale="Repetitive tasks are prime candidates for AI automation.",
                section="operations",
                priority=1,
            ),
            DynamicQuestion(
                id="biggest_bottlenecks",
                question="What are your biggest operational bottlenecks?",
                type="textarea",
                purpose=QuestionPurpose.DISCOVER,
                rationale="Understanding bottlenecks helps us prioritize solutions.",
                section="challenges",
                priority=1,
            ),
            DynamicQuestion(
                id="current_tools",
                question="What software tools does your business use?",
                type="multi_select",
                purpose=QuestionPurpose.CLARIFY,
                rationale="We want to confirm and expand on the tools we detected.",
                options=[
                    {"value": "crm", "label": "CRM (Salesforce, HubSpot, etc.)"},
                    {"value": "project_management", "label": "Project Management"},
                    {"value": "accounting", "label": "Accounting Software"},
                    {"value": "communication", "label": "Team Communication (Slack, Teams)"},
                    {"value": "analytics", "label": "Analytics Tools"},
                ],
                section="technology",
                priority=2,
            ),
            DynamicQuestion(
                id="ai_interest_areas",
                question="Which areas would you most like to automate or enhance with AI?",
                type="multi_select",
                purpose=QuestionPurpose.DISCOVER,
                rationale="This helps us focus our analysis on your priorities.",
                options=[
                    {"value": "customer_service", "label": "Customer service"},
                    {"value": "sales", "label": "Sales & marketing"},
                    {"value": "operations", "label": "Operations"},
                    {"value": "analytics", "label": "Data analysis"},
                    {"value": "content", "label": "Content creation"},
                ],
                section="goals",
                priority=2,
            ),
        ]

        return DynamicQuestionnaire(
            company_name=self.company_name,
            research_summary=f"We found some public information about {self.company_name}. Please answer these questions to help us provide better recommendations.",
            confirmed_facts=[],
            questions=questions,
            total_questions=len(questions),
            estimated_time_minutes=5,
            sections=self._build_sections(questions),
        )


def _json_serializer(obj):
    """Custom JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, 'value'):  # Handle Enum types
        return obj.value
    if hasattr(obj, '__dict__'):  # Handle Pydantic models or other objects
        return obj.__dict__
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


async def start_company_research(
    company_name: str,
    website_url: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """
    Start company research.

    Yields SSE-formatted events.
    """
    agent = PreResearchAgent(company_name, website_url)

    async for update in agent.run_research():
        yield f"data: {json.dumps(update, default=_json_serializer)}\n\n"
