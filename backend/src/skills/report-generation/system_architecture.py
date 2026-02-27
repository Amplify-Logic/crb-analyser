"""
System Architecture Skill — 7-Layer AIOS Blueprint

Generates a complete AI Operating System architecture for the client:
- 7-layer assessment (stack → connections → intelligence → data_os → skills → context_os → dashboard)
- AIOS maturity scoring per layer
- Build phases with progressive layer activation
- Recommended skills from catalog
- Context OS starter template
- Education path based on maturity

Input: Client stack, recommendations, quiz/workshop data, industry
Output: SystemArchitecture with full AIOS blueprint

Runs AFTER findings + recommendations, before roadmap.
"""

import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.knowledge import (
    get_aios_layers,
    get_aios_maturity_model,
    get_context_os_template,
    get_education_modules_for_maturity,
    get_mcp_servers,
    get_skills_catalog,
    normalize_industry,
)
from src.skills.base import SkillContext, SyncSkill

logger = logging.getLogger(__name__)


# =============================================================================
# PYDANTIC MODELS
# =============================================================================


class ArchNode(BaseModel):
    """A node in the AIOS architecture."""

    id: str
    name: str
    type: str  # existing_tool, mcp_server, claude_code, claude_cowork,
    # automation_platform, ai_agent, data_store, trigger,
    # skill, context_file, dashboard_view, output
    category: str
    status: str  # active, recommended, future
    linked_recommendation_id: Optional[str] = None


class ArchitectureLayers(BaseModel):
    """All 7 AIOS layers with their nodes."""

    stack: List[ArchNode] = Field(default_factory=list)
    connections: List[ArchNode] = Field(default_factory=list)
    intelligence: List[ArchNode] = Field(default_factory=list)
    data_os: List[ArchNode] = Field(default_factory=list)
    skills: List[ArchNode] = Field(default_factory=list)
    context_os: List[ArchNode] = Field(default_factory=list)
    dashboard: List[ArchNode] = Field(default_factory=list)


class ArchitectureConnection(BaseModel):
    """A connection between two nodes."""

    id: str
    from_node: str
    to_node: str
    data_flow: str
    connection_type: str  # mcp, api, webhook, native, zapier, make, n8n
    status: str  # active, recommended


class AIOSMaturity(BaseModel):
    """AIOS maturity assessment."""

    current_level: str  # disconnected, partially_connected, automated, ai_native
    target_level: str
    layer_scores: Dict[str, int]  # layer_id -> 1-10
    overall_score: int  # 1-100
    gaps: List[str]
    quick_wins: List[str]


class BuildPhase(BaseModel):
    """A phase in the AIOS build sequence."""

    phase: int
    title: str
    weeks: str
    focus_layers: List[str]
    actions: List[str]
    nodes_added: List[str] = Field(default_factory=list)
    connections_added: List[str] = Field(default_factory=list)
    estimated_value_unlocked: int = 0  # EUR/month


class SkillRecommendation(BaseModel):
    """A recommended Claude Code skill."""

    slug: str
    name: str
    description: str
    build_time_hours: int
    tools_needed: List[str]
    prerequisite_layers: List[str]
    estimated_time_saved_monthly: int  # hours


class ContextOSTemplate(BaseModel):
    """Context OS starter template for the client."""

    claude_md_sections: List[Dict[str, Any]]
    memory_structure: Dict[str, str]
    initial_context_prompts: List[str]


class EducationModule(BaseModel):
    """An education module recommended for the client."""

    title: str
    estimated_time: str
    outcome: str
    for_maturity: List[str]


class SystemArchitecture(BaseModel):
    """Complete AIOS blueprint for the client."""

    layers: ArchitectureLayers
    connections: List[ArchitectureConnection] = Field(default_factory=list)
    maturity: AIOSMaturity
    build_phases: List[BuildPhase] = Field(default_factory=list)
    education_path: List[EducationModule] = Field(default_factory=list)
    recommended_skills: List[SkillRecommendation] = Field(default_factory=list)
    context_os_template: Optional[ContextOSTemplate] = None


# =============================================================================
# SKILL IMPLEMENTATION
# =============================================================================


class SystemArchitectureSkill(SyncSkill[Dict[str, Any]]):
    """Generate a 7-layer AIOS blueprint from client data and recommendations."""

    name = "system-architecture"
    description = "Generate complete AIOS architecture blueprint"
    version = "2.0.0"  # v2: 7-layer model (v1 was 3-column)

    requires_llm = False
    requires_knowledge = True

    def execute_sync(self, context: SkillContext) -> Dict[str, Any]:
        """Generate the AIOS architecture."""
        industry = normalize_industry(context.industry)
        quiz_answers = context.quiz_answers or {}
        recommendations = context.report_data.get("recommendations", []) if context.report_data else []
        existing_stack = context.existing_stack or []

        # Build each component
        layers = self._build_layers(existing_stack, recommendations, industry)
        connections = self._build_connections(layers, existing_stack, industry)
        maturity = self._assess_maturity(existing_stack, quiz_answers, layers)
        build_phases = self._generate_build_phases(maturity, layers, recommendations)
        education_path = self._select_education(maturity.current_level)
        recommended_skills = self._recommend_skills(industry, existing_stack)
        context_os = self._build_context_os_template(industry)

        architecture = SystemArchitecture(
            layers=layers,
            connections=connections,
            maturity=maturity,
            build_phases=build_phases,
            education_path=education_path,
            recommended_skills=recommended_skills,
            context_os_template=context_os,
        )

        return architecture.model_dump()

    # =========================================================================
    # LAYER BUILDING
    # =========================================================================

    def _build_layers(
        self,
        existing_stack: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]],
        industry: str,
    ) -> ArchitectureLayers:
        """Build the 7-layer architecture from client data."""
        layers = ArchitectureLayers()

        # Layer 1: Stack — existing tools
        for i, tool in enumerate(existing_stack[:10]):
            layers.stack.append(ArchNode(
                id=f"stack-{i}",
                name=tool.get("name", tool.get("slug", f"tool-{i}")),
                type="existing_tool",
                category=tool.get("category", "general"),
                status="active",
            ))

        # Layer 2: Connections — MCP servers + recommended integrations
        mcp_servers = get_mcp_servers(industry=industry)
        for i, server in enumerate(mcp_servers[:8]):
            # Check if this MCP server matches an existing tool
            slug = server.get("slug", "")
            matches_existing = any(
                slug in (t.get("slug", "").lower())
                for t in existing_stack
            )
            layers.connections.append(ArchNode(
                id=f"conn-mcp-{i}",
                name=f"{server.get('name', slug)} MCP",
                type="mcp_server",
                category=server.get("name", "integration"),
                status="recommended" if matches_existing else "future",
            ))

        # Add non-MCP connections from recommendations
        for i, rec in enumerate(recommendations[:5]):
            options = rec.get("options", {})
            connect_opt = options.get("connect_and_automate") or options.get("aios_connect", {})
            if isinstance(connect_opt, dict):
                tools = connect_opt.get("tools_used", [])
                for tool in tools[:2]:
                    if isinstance(tool, str) and "mcp" not in tool.lower():
                        layers.connections.append(ArchNode(
                            id=f"conn-api-{i}",
                            name=f"{tool} API",
                            type="api",
                            category="integration",
                            status="recommended",
                            linked_recommendation_id=rec.get("id"),
                        ))

        # Layer 3: Intelligence — Claude Code + Cowork + automation platforms
        layers.intelligence = [
            ArchNode(
                id="intel-claude-code",
                name="Claude Code",
                type="claude_code",
                category="builder",
                status="recommended",
            ),
            ArchNode(
                id="intel-cowork",
                name="Claude Cowork",
                type="claude_cowork",
                category="operator",
                status="future",
            ),
        ]

        # Add automation platform if used in recommendations
        automation_platforms = {"make", "zapier", "n8n"}
        for rec in recommendations:
            options = rec.get("options", {})
            connect_opt = options.get("connect_and_automate") or options.get("aios_connect", {})
            if isinstance(connect_opt, dict):
                for tool in connect_opt.get("tools_used", []):
                    if isinstance(tool, str) and tool.lower() in automation_platforms:
                        layers.intelligence.append(ArchNode(
                            id=f"intel-{tool.lower()}",
                            name=tool,
                            type="automation_platform",
                            category="orchestrator",
                            status="recommended",
                        ))
                        break

        # Layer 4: Data OS — centralized data
        layers.data_os = [
            ArchNode(
                id="data-central",
                name="Centralized Business Data",
                type="data_store",
                category="data_hub",
                status="future",
            ),
        ]

        # Layer 5: Skills — recommended skills
        skills = get_skills_catalog(industry)
        for skill in skills[:5]:
            layers.skills.append(ArchNode(
                id=f"skill-{skill.get('slug', '')}",
                name=skill.get("name", ""),
                type="skill",
                category="automation",
                status="future",
            ))

        # Layer 6: Context OS
        layers.context_os = [
            ArchNode(
                id="ctx-claude-md",
                name="CLAUDE.md (Business Rules)",
                type="context_file",
                category="identity",
                status="future",
            ),
            ArchNode(
                id="ctx-memory",
                name="Client Memory Files",
                type="context_file",
                category="memory",
                status="future",
            ),
            ArchNode(
                id="ctx-processes",
                name="Process Documentation",
                type="context_file",
                category="processes",
                status="future",
            ),
        ]

        # Layer 7: Dashboard
        layers.dashboard = [
            ArchNode(
                id="dash-main",
                name="AIOS Command Center",
                type="dashboard_view",
                category="management",
                status="future",
            ),
        ]

        return layers

    # =========================================================================
    # CONNECTION BUILDING
    # =========================================================================

    def _build_connections(
        self,
        layers: ArchitectureLayers,
        existing_stack: List[Dict[str, Any]],
        industry: str,
    ) -> List[ArchitectureConnection]:
        """Build connections between layer nodes."""
        connections = []
        conn_id = 0

        # Connect existing tools → MCP servers
        for stack_node in layers.stack:
            for conn_node in layers.connections:
                if conn_node.type == "mcp_server":
                    # Match by name similarity
                    stack_name = stack_node.name.lower()
                    conn_name = conn_node.name.lower().replace(" mcp", "")
                    if conn_name in stack_name or stack_name in conn_name:
                        connections.append(ArchitectureConnection(
                            id=f"edge-{conn_id}",
                            from_node=stack_node.id,
                            to_node=conn_node.id,
                            data_flow="Tool data via MCP",
                            connection_type="mcp",
                            status="recommended",
                        ))
                        conn_id += 1

        # Connect MCP servers → Intelligence layer
        for conn_node in layers.connections:
            if conn_node.status == "recommended":
                connections.append(ArchitectureConnection(
                    id=f"edge-{conn_id}",
                    from_node=conn_node.id,
                    to_node="intel-claude-code",
                    data_flow="Connected data",
                    connection_type="mcp",
                    status="recommended",
                ))
                conn_id += 1

        # Intelligence → Skills
        for skill_node in layers.skills[:3]:
            connections.append(ArchitectureConnection(
                id=f"edge-{conn_id}",
                from_node="intel-claude-code",
                to_node=skill_node.id,
                data_flow="Skill execution",
                connection_type="native",
                status="future",
            ))
            conn_id += 1

        # Context OS → Intelligence
        connections.append(ArchitectureConnection(
            id=f"edge-{conn_id}",
            from_node="ctx-claude-md",
            to_node="intel-claude-code",
            data_flow="Business context",
            connection_type="native",
            status="future",
        ))

        return connections

    # =========================================================================
    # MATURITY ASSESSMENT
    # =========================================================================

    def _assess_maturity(
        self,
        existing_stack: List[Dict[str, Any]],
        quiz_answers: Dict[str, Any],
        layers: ArchitectureLayers,
    ) -> AIOSMaturity:
        """Assess AIOS maturity across all 7 layers."""
        maturity_data = get_aios_maturity_model()

        # Score each layer based on available data
        layer_scores: Dict[str, int] = {}

        # Layer 1: Stack — score based on API readiness of existing tools
        if existing_stack:
            avg_api = sum(
                t.get("api_openness_score", 0) or t.get("api_score", 0)
                for t in existing_stack
            ) / len(existing_stack)
            layer_scores["stack"] = min(10, max(1, round(avg_api * 2)))
        else:
            layer_scores["stack"] = 3  # Has tools but we don't know details

        # Layer 2: Connections — based on integration usage
        has_automations = any(
            quiz_answers.get(k) for k in ["uses_zapier", "uses_make", "uses_n8n", "automation_tools"]
        )
        layer_scores["connections"] = 4 if has_automations else 1

        # Layer 3: Intelligence — based on AI tool usage
        ai_usage = quiz_answers.get("ai_tools_used") or quiz_answers.get("ai_experience") or ""
        if isinstance(ai_usage, list) and len(ai_usage) > 2:
            layer_scores["intelligence"] = 5
        elif ai_usage:
            layer_scores["intelligence"] = 3
        else:
            layer_scores["intelligence"] = 1

        # Layers 4-7: Typically start at 1 for new clients
        layer_scores["data_os"] = 2 if len(existing_stack) > 3 else 1
        layer_scores["skills"] = 1
        layer_scores["context_os"] = 1
        layer_scores["dashboard"] = 2 if quiz_answers.get("uses_dashboards") else 1

        # Calculate overall score
        total = sum(layer_scores.values())
        overall_score = round((total / 70) * 100)

        # Determine current level
        if overall_score >= 76:
            current_level = "ai_native"
        elif overall_score >= 51:
            current_level = "automated"
        elif overall_score >= 26:
            current_level = "partially_connected"
        else:
            current_level = "disconnected"

        # Determine target (one level up)
        level_progression = {
            "disconnected": "partially_connected",
            "partially_connected": "automated",
            "automated": "ai_native",
            "ai_native": "ai_native",
        }
        target_level = level_progression[current_level]

        # Identify gaps
        gaps = []
        gap_templates = maturity_data.get("gap_templates", {}) if maturity_data else {}
        if layer_scores.get("connections", 0) <= 2:
            gaps.append(gap_templates.get("no_connections", "Tools are disconnected"))
        if layer_scores.get("intelligence", 0) <= 2:
            gaps.append(gap_templates.get("no_intelligence", "No AI intelligence layer"))
        if layer_scores.get("skills", 0) <= 2:
            gaps.append(gap_templates.get("no_skills", "No custom skills"))
        if layer_scores.get("context_os", 0) <= 2:
            gaps.append(gap_templates.get("no_context_os", "No Context OS"))
        if layer_scores.get("data_os", 0) <= 2:
            gaps.append(gap_templates.get("no_data_os", "No centralized data layer"))

        # Quick wins from maturity model
        quick_wins = []
        if maturity_data:
            transition_key = f"{current_level}_to_{target_level}"
            transition = maturity_data.get("transition_paths", {}).get(transition_key, {})
            quick_wins = transition.get("quick_wins", [])[:3]

        return AIOSMaturity(
            current_level=current_level,
            target_level=target_level,
            layer_scores=layer_scores,
            overall_score=overall_score,
            gaps=gaps,
            quick_wins=quick_wins,
        )

    # =========================================================================
    # BUILD PHASES
    # =========================================================================

    def _generate_build_phases(
        self,
        maturity: AIOSMaturity,
        layers: ArchitectureLayers,
        recommendations: List[Dict[str, Any]],
    ) -> List[BuildPhase]:
        """Generate phased build plan aligned to AIOS layers."""
        phases = []

        # Phase 1: Connect existing tools
        mcp_connections = [n for n in layers.connections if n.type == "mcp_server" and n.status == "recommended"]
        phase1_actions = ["Install Claude Code"]
        for conn in mcp_connections[:3]:
            phase1_actions.append(f"Connect {conn.name}")

        phases.append(BuildPhase(
            phase=1,
            title="Connect Your Stack",
            weeks="1-2",
            focus_layers=["connections", "intelligence"],
            actions=phase1_actions,
            nodes_added=[n.id for n in mcp_connections[:3]] + ["intel-claude-code"],
            estimated_value_unlocked=500,
        ))

        # Phase 2: Build first automations
        phase2_actions = []
        for rec in recommendations[:3]:
            phase2_actions.append(f"Implement: {rec.get('title', 'automation')[:40]}")

        phases.append(BuildPhase(
            phase=2,
            title="First Automations",
            weeks="3-4",
            focus_layers=["intelligence", "connections"],
            actions=phase2_actions or ["Build first automation workflow"],
            estimated_value_unlocked=1000,
        ))

        # Phase 3: Context OS + Skills
        skill_nodes = layers.skills[:3]
        phase3_actions = [
            "Create business CLAUDE.md",
            "Set up client memory files",
        ]
        for skill in skill_nodes:
            phase3_actions.append(f"Build {skill.name} skill")

        phases.append(BuildPhase(
            phase=3,
            title="Context OS + Core Skills",
            weeks="5-8",
            focus_layers=["context_os", "skills"],
            actions=phase3_actions,
            nodes_added=["ctx-claude-md", "ctx-memory"] + [s.id for s in skill_nodes],
            estimated_value_unlocked=2000,
        ))

        # Phase 4: Data OS + Dashboard
        phases.append(BuildPhase(
            phase=4,
            title="Data Centralization + Dashboard",
            weeks="9-12",
            focus_layers=["data_os", "dashboard"],
            actions=[
                "Centralize business data from connected tools",
                "Build operational dashboard",
                "Create reporting automations",
            ],
            nodes_added=["data-central", "dash-main"],
            estimated_value_unlocked=3000,
        ))

        return phases

    # =========================================================================
    # EDUCATION, SKILLS, CONTEXT OS
    # =========================================================================

    def _select_education(self, maturity_level: str) -> List[EducationModule]:
        """Select education modules based on maturity level."""
        modules = get_education_modules_for_maturity(maturity_level)
        return [
            EducationModule(
                title=m.get("title", ""),
                estimated_time=m.get("estimated_time", ""),
                outcome=m.get("outcome", ""),
                for_maturity=m.get("for_maturity", []),
            )
            for m in modules[:5]
        ]

    def _recommend_skills(
        self,
        industry: str,
        existing_stack: List[Dict[str, Any]],
    ) -> List[SkillRecommendation]:
        """Recommend skills from catalog based on industry and stack."""
        skills = get_skills_catalog(industry)
        stack_slugs = {t.get("slug", "").lower() for t in existing_stack}

        recommendations = []
        for skill in skills[:5]:
            # Check if prerequisite tools are in the stack
            tools_needed = skill.get("tools_needed", [])
            has_prereqs = len(tools_needed) == 0 or any(
                any(slug in tool.lower() for slug in stack_slugs)
                for tool in tools_needed
                if isinstance(tool, str)
            )

            recommendations.append(SkillRecommendation(
                slug=skill.get("slug", ""),
                name=skill.get("name", ""),
                description=skill.get("description", ""),
                build_time_hours=skill.get("build_time_hours", 4),
                tools_needed=tools_needed,
                prerequisite_layers=skill.get("prerequisite_layers", ["stack"]),
                estimated_time_saved_monthly=skill.get("estimated_time_saved_monthly_hours", 4),
            ))

        # Sort by time saved (most impactful first)
        recommendations.sort(key=lambda s: s.estimated_time_saved_monthly, reverse=True)
        return recommendations

    def _build_context_os_template(self, industry: str) -> Optional[ContextOSTemplate]:
        """Build a Context OS starter template for the industry."""
        template_data = get_context_os_template(industry)
        if not template_data:
            return None

        claude_md = template_data.get("claude_md_template", {})
        sections = claude_md.get("sections", [])
        memory_structure = claude_md.get("memory_structure", {})

        # Collect all prompts from sections
        all_prompts = []
        for section in sections:
            all_prompts.extend(section.get("prompts", []))

        return ContextOSTemplate(
            claude_md_sections=sections,
            memory_structure=memory_structure,
            initial_context_prompts=all_prompts[:10],
        )
