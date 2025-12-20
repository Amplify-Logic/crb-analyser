# backend/src/services/architecture_generator.py
"""
System Architecture Generator

Creates visual system architecture from recommendations and quiz data.
"""
import logging
from typing import Dict, Any, List, Optional, Literal, Union

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# INLINE MODELS (Stubs - will be replaced when models/system_architecture.py is created)
# =============================================================================

class NodeCRB(BaseModel):
    """CRB for a single tool/node in the architecture."""
    cost: str
    risk: str
    risk_level: Literal["low", "medium", "high"] = "low"
    benefit: str
    powers: List[str] = Field(default_factory=list, description="What automations this powers")


class Position(BaseModel):
    """Position for diagram layout."""
    x: int = 0
    y: int = 0
    column: Literal["existing", "ai_layer", "automations"] = "existing"


class ToolNode(BaseModel):
    """A tool or service in the architecture."""
    id: str
    name: str
    category: Literal["existing", "ai_brain", "automation", "database", "hosting"] = "existing"
    icon: Optional[str] = None
    monthly_cost: float = 0
    one_time_cost: float = 0
    crb: NodeCRB
    position: Position = Field(default_factory=Position)
    is_existing: bool = False  # True if user already has this tool


class Connection(BaseModel):
    """Connection between two nodes showing data flow."""
    id: str
    from_node: str
    to_node: str
    data_flow: str  # "Customer inquiries", "Lead data"
    integration_type: Literal["api", "webhook", "zapier", "native", "custom"] = "api"


class AutomationNode(BaseModel):
    """An automation/workflow output."""
    id: str
    name: str
    trigger: str
    action: str
    tools_used: List[str]
    output_type: str  # "notification", "report", "action"


class CostItem(BaseModel):
    """A single cost line item."""
    name: str
    monthly_cost: float
    one_time_cost: float = 0
    category: Literal["saas", "diy", "both"] = "saas"


class CostBreakdown(BaseModel):
    """Complete cost breakdown for a route."""
    items: List[CostItem]
    total_monthly: float
    total_one_time: float = 0


class CostComparison(BaseModel):
    """Compare SaaS vs DIY routes."""
    saas_route: CostBreakdown
    diy_route: CostBreakdown
    monthly_savings: float
    savings_percentage: float
    build_cost: float
    breakeven_months: float


class SystemArchitecture(BaseModel):
    """Complete system architecture for a report."""
    report_id: str
    existing_tools: List[ToolNode]
    ai_layer: List[ToolNode]
    automations: List[AutomationNode]
    connections: List[Connection]
    cost_comparison: CostComparison


# =============================================================================
# TOOL DATABASE
# =============================================================================

# Tool database with costs and categories
TOOL_DATABASE = {
    # AI Models
    "claude": {"name": "Claude Sonnet 4.5", "category": "ai_brain", "monthly_cost": 50, "icon": "brain"},
    "claude_opus": {"name": "Claude Opus 4.5", "category": "ai_brain", "monthly_cost": 150, "icon": "brain"},
    "gemini": {"name": "Gemini 3 Flash", "category": "ai_brain", "monthly_cost": 20, "icon": "brain"},
    "gpt": {"name": "GPT-5", "category": "ai_brain", "monthly_cost": 40, "icon": "brain"},
    "openai": {"name": "OpenAI GPT-4", "category": "ai_brain", "monthly_cost": 40, "icon": "brain"},

    # Automation
    "make": {"name": "Make.com", "category": "automation", "monthly_cost": 20, "icon": "zap"},
    "zapier": {"name": "Zapier", "category": "automation", "monthly_cost": 30, "icon": "zap"},
    "n8n": {"name": "n8n", "category": "automation", "monthly_cost": 0, "icon": "zap"},

    # CRM
    "hubspot": {"name": "HubSpot", "category": "existing", "monthly_cost": 50, "icon": "users"},
    "salesforce": {"name": "Salesforce", "category": "existing", "monthly_cost": 150, "icon": "users"},
    "pipedrive": {"name": "Pipedrive", "category": "existing", "monthly_cost": 30, "icon": "users"},

    # Communication
    "slack": {"name": "Slack", "category": "existing", "monthly_cost": 0, "icon": "message"},
    "intercom": {"name": "Intercom", "category": "existing", "monthly_cost": 89, "icon": "message"},
    "zendesk": {"name": "Zendesk", "category": "existing", "monthly_cost": 55, "icon": "message"},

    # Email
    "mailchimp": {"name": "Mailchimp", "category": "existing", "monthly_cost": 20, "icon": "mail"},
    "sendgrid": {"name": "SendGrid", "category": "existing", "monthly_cost": 20, "icon": "mail"},
    "gmail": {"name": "Gmail/Google Workspace", "category": "existing", "monthly_cost": 12, "icon": "mail"},

    # Database/Hosting
    "supabase": {"name": "Supabase", "category": "database", "monthly_cost": 0, "icon": "database"},
    "vercel": {"name": "Vercel", "category": "hosting", "monthly_cost": 0, "icon": "cloud"},
    "railway": {"name": "Railway", "category": "hosting", "monthly_cost": 5, "icon": "cloud"},

    # Billing
    "stripe": {"name": "Stripe", "category": "existing", "monthly_cost": 0, "icon": "credit-card"},

    # Project Management
    "notion": {"name": "Notion", "category": "existing", "monthly_cost": 10, "icon": "file-text"},
    "asana": {"name": "Asana", "category": "existing", "monthly_cost": 11, "icon": "list"},
    "trello": {"name": "Trello", "category": "existing", "monthly_cost": 0, "icon": "columns"},

    # Analytics
    "google_analytics": {"name": "Google Analytics", "category": "existing", "monthly_cost": 0, "icon": "bar-chart"},
    "mixpanel": {"name": "Mixpanel", "category": "existing", "monthly_cost": 89, "icon": "bar-chart"},
}

# SaaS alternatives with costs
SAAS_ALTERNATIVES = {
    "customer_support": {"name": "Intercom", "monthly_cost": 89},
    "content_generation": {"name": "Jasper", "monthly_cost": 49},
    "lead_scoring": {"name": "Salesforce Einstein", "monthly_cost": 150},
    "analytics": {"name": "Mixpanel", "monthly_cost": 89},
    "email_automation": {"name": "Mailchimp Pro", "monthly_cost": 50},
    "social_media": {"name": "Hootsuite", "monthly_cost": 99},
    "seo": {"name": "Semrush", "monthly_cost": 130},
    "reporting": {"name": "Databox", "monthly_cost": 72},
}


# =============================================================================
# ARCHITECTURE GENERATOR
# =============================================================================

class ArchitectureGenerator:
    """Generate system architecture diagrams from recommendations."""

    def generate_architecture(
        self,
        recommendations: List[Dict[str, Any]],
        quiz_answers: Dict[str, Any],
    ) -> SystemArchitecture:
        """Generate complete system architecture."""

        # Extract existing tools from quiz
        existing_tools_raw = quiz_answers.get("current_tools", [])
        if isinstance(existing_tools_raw, str):
            existing_tools_raw = [t.strip().lower() for t in existing_tools_raw.split(",")]
        elif isinstance(existing_tools_raw, list):
            existing_tools_raw = [str(t).strip().lower() for t in existing_tools_raw]
        else:
            existing_tools_raw = []

        # Build existing tools nodes
        existing_tools = []
        for i, tool_key in enumerate(existing_tools_raw[:6]):  # Max 6 existing tools
            tool_info = self._match_tool(tool_key)
            if tool_info:
                existing_tools.append(ToolNode(
                    id=f"existing-{i}",
                    name=tool_info["name"],
                    category="existing",
                    icon=tool_info.get("icon"),
                    monthly_cost=0,  # Already paying for it
                    crb=NodeCRB(
                        cost="Already owned",
                        risk="None",
                        risk_level="low",
                        benefit="Foundation for integrations",
                        powers=[],
                    ),
                    position=Position(x=0, y=i * 100, column="existing"),
                    is_existing=True,
                ))

        # Build AI layer from recommendations
        ai_layer = [
            ToolNode(
                id="ai-claude",
                name="Claude Sonnet 4.5",
                category="ai_brain",
                icon="brain",
                monthly_cost=50,
                crb=NodeCRB(
                    cost="~€50/mo at typical usage",
                    risk="API dependency",
                    risk_level="low",
                    benefit="Powers all AI automations",
                    powers=["Lead scoring", "Content generation", "Support responses"],
                ),
                position=Position(x=200, y=0, column="ai_layer"),
            ),
            ToolNode(
                id="ai-automation",
                name="Make.com",
                category="automation",
                icon="zap",
                monthly_cost=20,
                crb=NodeCRB(
                    cost="€20/mo",
                    risk="Workflow complexity",
                    risk_level="low",
                    benefit="Connects all tools",
                    powers=["Workflows", "Triggers", "Scheduling"],
                ),
                position=Position(x=200, y=100, column="ai_layer"),
            ),
        ]

        # Build automations from recommendations
        automations = []
        for i, rec in enumerate(recommendations[:5]):
            title = rec.get("title", "Automation")
            automations.append(AutomationNode(
                id=f"auto-{i}",
                name=title[:30] if len(title) > 30 else title,
                trigger=f"When {title.lower().split()[0] if title else 'event'} occurs",
                action=rec.get("description", "")[:50] if rec.get("description") else "Automated action",
                tools_used=["claude", "make"],
                output_type="action",
            ))

        # Build connections
        connections = []
        for i, existing in enumerate(existing_tools):
            connections.append(Connection(
                id=f"conn-{i}",
                from_node=existing.id,
                to_node="ai-claude",
                data_flow="Data sync",
                integration_type="api",
            ))

        # Add connections from AI layer to automations
        for i, auto in enumerate(automations[:3]):
            connections.append(Connection(
                id=f"conn-ai-{i}",
                from_node="ai-claude",
                to_node=auto.id,
                data_flow="AI processing",
                integration_type="api",
            ))

        # Calculate costs
        cost_comparison = self._calculate_costs(recommendations, ai_layer)

        return SystemArchitecture(
            report_id="",  # Set by caller
            existing_tools=existing_tools,
            ai_layer=ai_layer,
            automations=automations,
            connections=connections,
            cost_comparison=cost_comparison,
        )

    def _match_tool(self, tool_key: str) -> Optional[Dict[str, Any]]:
        """Match a tool key to our database."""
        tool_key = tool_key.lower().strip()
        for key, info in TOOL_DATABASE.items():
            if key in tool_key or tool_key in info["name"].lower():
                return info
        return None

    def _calculate_costs(
        self,
        recommendations: List[Dict[str, Any]],
        ai_layer: List[ToolNode],
    ) -> CostComparison:
        """Calculate SaaS vs DIY cost comparison."""

        # DIY costs
        diy_items = [
            CostItem(name=node.name, monthly_cost=node.monthly_cost, category="diy")
            for node in ai_layer
        ]
        diy_items.append(CostItem(name="Supabase", monthly_cost=0, category="diy"))
        diy_items.append(CostItem(name="Vercel", monthly_cost=0, category="diy"))

        diy_total = sum(item.monthly_cost for item in diy_items)
        build_cost = 2400  # Typical freelancer cost for initial setup

        # SaaS costs (what they'd pay for equivalent functionality)
        saas_items = []
        saas_total = 0
        matched_categories = set()

        for rec in recommendations[:5]:
            title_lower = rec.get("title", "").lower()
            for key, saas in SAAS_ALTERNATIVES.items():
                if key not in matched_categories:
                    if key.replace("_", " ") in title_lower or key.replace("_", "") in title_lower:
                        saas_items.append(CostItem(
                            name=saas["name"],
                            monthly_cost=saas["monthly_cost"],
                            category="saas",
                        ))
                        saas_total += saas["monthly_cost"]
                        matched_categories.add(key)
                        break

        # Ensure minimum SaaS cost for comparison
        if saas_total < 200:
            saas_total = 400
            saas_items = [
                CostItem(name="Multiple SaaS tools", monthly_cost=400, category="saas")
            ]

        monthly_savings = saas_total - diy_total
        savings_pct = (monthly_savings / saas_total * 100) if saas_total > 0 else 0
        breakeven = build_cost / monthly_savings if monthly_savings > 0 else 999

        return CostComparison(
            saas_route=CostBreakdown(items=saas_items, total_monthly=saas_total),
            diy_route=CostBreakdown(items=diy_items, total_monthly=diy_total, total_one_time=build_cost),
            monthly_savings=monthly_savings,
            savings_percentage=savings_pct,
            build_cost=build_cost,
            breakeven_months=round(breakeven, 1),
        )
