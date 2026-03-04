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

# Slug aliases for normalizing tool names from quiz answers
SLUG_ALIASES = {
    "google-analytics": "google_analytics",
    "ga4": "google_analytics",
    "google analytics": "google_analytics",
    "woocommerce": "woocommerce",
    "ship-station": "shipstation",
    "send-cloud": "sendcloud",
}

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

    # Ecommerce
    "shopify": {"name": "Shopify", "category": "existing", "monthly_cost": 36, "icon": "shopping-cart"},
    "klaviyo": {"name": "Klaviyo", "category": "existing", "monthly_cost": 45, "icon": "mail"},
    "gorgias": {"name": "Gorgias", "category": "existing", "monthly_cost": 60, "icon": "message"},
    "tidio": {"name": "Tidio", "category": "existing", "monthly_cost": 29, "icon": "message"},
    "shipstation": {"name": "ShipStation", "category": "existing", "monthly_cost": 30, "icon": "truck"},
    "sendcloud": {"name": "Sendcloud", "category": "existing", "monthly_cost": 25, "icon": "truck"},
    "woocommerce": {"name": "WooCommerce", "category": "existing", "monthly_cost": 0, "icon": "shopping-cart"},
    "inventory_planner": {"name": "Inventory Planner", "category": "existing", "monthly_cost": 100, "icon": "package"},
    "triple_whale": {"name": "Triple Whale", "category": "existing", "monthly_cost": 100, "icon": "bar-chart"},
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
# HELPER FUNCTIONS
# =============================================================================

def _derive_trigger(title: str, rec: Dict[str, Any]) -> str:
    """Derive a meaningful trigger from recommendation title and data."""
    title_lower = title.lower()

    if "order" in title_lower and ("rout" in title_lower or "track" in title_lower):
        return "New order placed in Shopify"
    if "cart" in title_lower and ("abandon" in title_lower or "recovery" in title_lower):
        return "Cart abandoned for 1+ hours"
    if "email" in title_lower or "klaviyo" in title_lower or "dormant" in title_lower:
        return "Subscriber inactive for 90+ days"
    if "support" in title_lower or "chatbot" in title_lower or "inquir" in title_lower:
        return "Customer support ticket received"
    if "inventory" in title_lower or "forecast" in title_lower or "restock" in title_lower:
        return "Stock level drops below threshold"
    if "product" in title_lower and ("description" in title_lower or "content" in title_lower):
        return "New product added to catalog"
    if "review" in title_lower:
        return "New product review posted"
    if "return" in title_lower:
        return "Return request submitted"
    if "segment" in title_lower or "personali" in title_lower:
        return "Customer behavior data updated"
    if "conversion" in title_lower or "analytics" in title_lower or "data" in title_lower:
        return "Weekly data sync triggered"
    if "recommend" in title_lower or "aov" in title_lower or "cross-sell" in title_lower:
        return "Customer views product page"
    if "fulfillment" in title_lower or "shipping" in title_lower:
        return "Order ready for fulfillment"

    # Generic but better than "When X occurs"
    return "Triggered by schedule or event"


def _parse_build_hours(build_time: str) -> float:
    """Parse build hours from strings like '8-12 hours' or '2-3 weeks'."""
    if not build_time:
        return 8  # Default
    build_time = build_time.lower()
    import re
    numbers = re.findall(r'(\d+(?:\.\d+)?)', build_time)
    if not numbers:
        return 8
    avg = sum(float(n) for n in numbers) / len(numbers)
    if "week" in build_time:
        return avg * 20  # 20 hours per week
    if "day" in build_time:
        return avg * 4  # 4 hours per day
    return avg  # Assume hours


def _parse_cost_from_range(cost_range: str, tool_name: str) -> Optional[float]:
    """Parse a monthly cost from a cost_range string for a specific tool."""
    if not cost_range:
        return None
    import re
    tool_lower = tool_name.lower()
    cost_lower = cost_range.lower()

    patterns = [
        rf'{re.escape(tool_lower)}[^€\d]*[€EUR]*\s*(\d+)',
        rf'(\d+)[^€\d]*{re.escape(tool_lower)}',
    ]
    for pattern in patterns:
        match = re.search(pattern, cost_lower)
        if match:
            return float(match.group(1))

    # Fallback: first number in the string
    match = re.search(r'[€EUR]\s*(\d+)', cost_range)
    if match:
        return float(match.group(1))

    return None


# =============================================================================
# ARCHITECTURE GENERATOR
# =============================================================================

class ArchitectureGenerator:
    """Generate system architecture diagrams from recommendations."""

    def generate_architecture(
        self,
        recommendations: List[Dict[str, Any]],
        quiz_answers: Dict[str, Any],
        existing_stack: Optional[List[Dict[str, Any]]] = None,
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

        # Fallback: use existing_stack data if current_tools matching fails
        if not existing_tools and existing_stack:
            for i, stack_tool in enumerate(existing_stack[:6]):
                slug = stack_tool.get("slug", stack_tool.get("name", ""))
                tool_info = self._match_tool(slug)
                api_score = stack_tool.get("api_score", 0)
                tool_name = tool_info["name"] if tool_info else slug.replace("-", " ").title()
                existing_tools.append(ToolNode(
                    id=f"existing-{i}",
                    name=tool_name,
                    category="existing",
                    icon=tool_info.get("icon") if tool_info else None,
                    monthly_cost=0,
                    crb=NodeCRB(
                        cost="Already owned",
                        risk="Low" if api_score >= 3 else "Medium — limited API",
                        risk_level="low" if api_score >= 3 else "medium",
                        benefit=f"API score {api_score}/5 — {'strong' if api_score >= 3 else 'limited'} integration potential",
                        powers=[],
                    ),
                    position=Position(x=0, y=i * 100, column="existing"),
                    is_existing=True,
                ))

        # Build AI layer from what recommendations actually use
        ai_tools_seen: Dict[str, Dict[str, Any]] = {}  # deduplicate
        for rec in recommendations:
            connect = rec.get("options", {}).get("connect_and_automate", {})
            for tool_name in connect.get("tools_used", []):
                tool_lower = tool_name.lower()
                # Categorize
                if "claude" in tool_lower:
                    if "claude" not in ai_tools_seen:
                        model_name = "Claude Sonnet 4.5"
                        monthly = 50
                        if "haiku" in tool_lower:
                            model_name = "Claude Haiku 4.5"
                            monthly = 20
                        elif "opus" in tool_lower:
                            model_name = "Claude Opus 4.5"
                            monthly = 150
                        ai_tools_seen["claude"] = {
                            "name": model_name, "category": "ai_brain",
                            "monthly_cost": monthly, "icon": "brain",
                            "powers": [],
                        }
                elif "make" in tool_lower:
                    if "make" not in ai_tools_seen:
                        ai_tools_seen["make"] = {
                            "name": "Make.com", "category": "automation",
                            "monthly_cost": 20, "icon": "zap",
                            "powers": [],
                        }
                elif "supabase" in tool_lower:
                    if "supabase" not in ai_tools_seen:
                        ai_tools_seen["supabase"] = {
                            "name": "Supabase", "category": "database",
                            "monthly_cost": 0, "icon": "database",
                            "powers": [],
                        }
                elif "railway" in tool_lower or "vercel" in tool_lower:
                    key = "hosting"
                    if key not in ai_tools_seen:
                        ai_tools_seen[key] = {
                            "name": tool_name, "category": "hosting",
                            "monthly_cost": 5 if "railway" in tool_lower else 0,
                            "icon": "cloud",
                            "powers": [],
                        }

            # Track which recs each AI tool powers
            rec_title = rec.get("title", "")[:40]
            for key in ai_tools_seen:
                if key in ["claude", "make"]:  # These power most automations
                    if rec_title not in ai_tools_seen[key]["powers"]:
                        ai_tools_seen[key]["powers"].append(rec_title)

        # Fallback if nothing extracted
        if not ai_tools_seen:
            ai_tools_seen["claude"] = {
                "name": "Claude Sonnet 4.5", "category": "ai_brain",
                "monthly_cost": 50, "icon": "brain", "powers": [],
            }
            ai_tools_seen["make"] = {
                "name": "Make.com", "category": "automation",
                "monthly_cost": 20, "icon": "zap", "powers": [],
            }

        ai_layer = []
        for i, (key, tool_data) in enumerate(ai_tools_seen.items()):
            ai_layer.append(ToolNode(
                id=f"ai-{key}",
                name=tool_data["name"],
                category=tool_data["category"],
                icon=tool_data.get("icon"),
                monthly_cost=tool_data["monthly_cost"],
                crb=NodeCRB(
                    cost=f"~€{tool_data['monthly_cost']}/mo" if tool_data["monthly_cost"] > 0 else "Free tier",
                    risk="API dependency" if tool_data["category"] == "ai_brain" else "Low",
                    risk_level="low",
                    benefit=f"Powers {len(tool_data['powers'])} automations",
                    powers=tool_data["powers"][:5],
                ),
                position=Position(x=200, y=i * 100, column="ai_layer"),
            ))

        # Build automations from recommendations with real data
        automations = []
        for i, rec in enumerate(recommendations[:6]):
            title = rec.get("title", "Automation")

            # Extract real trigger from finding context
            connect = rec.get("options", {}).get("connect_and_automate", {})
            approach = connect.get("approach", "")

            # Derive trigger from the finding's category/context
            trigger = _derive_trigger(title, rec)
            action = approach[:80] if approach else rec.get("description", "Automated action")[:80]

            # Get tools from the selected/connect option
            tools = connect.get("tools_used", ["claude"])
            tool_keys = [t.lower().split()[0] for t in tools[:3]]

            automations.append(AutomationNode(
                id=f"auto-{i}",
                name=title,  # Full title — frontend handles overflow
                trigger=trigger,
                action=action,
                tools_used=tool_keys,
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
        # Check aliases first
        normalized = SLUG_ALIASES.get(tool_key, tool_key.replace("-", "_"))
        if normalized in TOOL_DATABASE:
            return TOOL_DATABASE[normalized]
        # Fuzzy fallback
        for key, info in TOOL_DATABASE.items():
            if key in tool_key or tool_key in info["name"].lower():
                return info
        return None

    def _calculate_costs(
        self,
        recommendations: List[Dict[str, Any]],
        ai_layer: List[ToolNode],
    ) -> CostComparison:
        """Calculate SaaS vs DIY cost comparison from actual recommendation data."""

        # === DIY ROUTE: from connect_and_automate options ===
        diy_items_seen: Dict[str, float] = {}
        total_build_hours = 0.0

        for node in ai_layer:
            if node.name not in diy_items_seen:
                diy_items_seen[node.name] = node.monthly_cost

        for rec in recommendations:
            connect = rec.get("options", {}).get("connect_and_automate", {})
            build_time = connect.get("build_time", "")
            hours = _parse_build_hours(build_time)
            total_build_hours += hours

        diy_items = [
            CostItem(name=name, monthly_cost=cost, category="diy")
            for name, cost in diy_items_seen.items()
        ]
        diy_total = sum(item.monthly_cost for item in diy_items)

        # Build cost = total hours x EUR 50/hr (freelancer rate)
        build_cost = max(total_build_hours * 50, 500)  # Minimum EUR 500

        # === SAAS ROUTE: from targeted_upgrade options ===
        saas_items_seen: Dict[str, float] = {}

        for rec in recommendations[:6]:
            tu = rec.get("options", {}).get("targeted_upgrade", {})
            tools = tu.get("tools", [])
            cost_range = tu.get("cost_range", "")

            matched = tu.get("matched_vendor", {})
            vendor_cost = matched.get("monthly_cost") if matched else None

            for tool_name in tools:
                if tool_name and tool_name not in saas_items_seen and "no matching" not in tool_name.lower():
                    tool_cost = _parse_cost_from_range(cost_range, tool_name)
                    if not tool_cost and vendor_cost:
                        tool_cost = float(vendor_cost)
                    if not tool_cost:
                        tool_cost = 50  # Conservative estimate
                    saas_items_seen[tool_name] = tool_cost

        saas_items = [
            CostItem(name=name, monthly_cost=cost, category="saas")
            for name, cost in saas_items_seen.items()
        ]
        saas_total = sum(item.monthly_cost for item in saas_items)

        # Ensure we have at least something
        if not saas_items:
            saas_total = diy_total * 3  # Rough 3x multiplier
            saas_items = [CostItem(name="Estimated SaaS equivalent", monthly_cost=saas_total, category="saas")]

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
