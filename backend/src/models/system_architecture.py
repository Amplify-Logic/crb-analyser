# backend/src/models/system_architecture.py
"""
System Architecture models for visualizing integrated AI systems.
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


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
